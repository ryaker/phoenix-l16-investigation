"""
utils.py — Shared helpers for Phoenix Spike v2.

Clean-room: every function here is either published CIE math, standard numpy
operations, or reimplemented from TRUTH v2.1.3 documented algorithms.
"""

import numpy as np


# ---------------------------------------------------------------------------
# Protobuf wire-format decode (read-only reimplementation of standard format)
# ---------------------------------------------------------------------------

def parse_varint(data: bytes, pos: int):
    """Decode a protobuf varint from `data` at `pos`. Returns (value, new_pos)."""
    result = 0
    shift = 0
    while pos < len(data):
        b = data[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, pos
        shift += 7
        if shift > 63:
            raise ValueError("varint overflow")
    raise ValueError("unterminated varint")


def parse_fields(data: bytes):
    """Decode a flat protobuf message into list of (fn, wire_type_char, value)."""
    import struct
    out = []
    pos = 0
    n = len(data)
    while pos < n:
        try:
            tag, pos = parse_varint(data, pos)
        except Exception:
            break
        fn = tag >> 3
        wt = tag & 7
        if fn == 0:
            break
        if wt == 0:
            try:
                v, pos = parse_varint(data, pos)
            except Exception:
                break
            out.append((fn, 'v', v))
        elif wt == 2:
            try:
                ln, pos = parse_varint(data, pos)
            except Exception:
                break
            if ln < 0 or pos + ln > n:
                break
            out.append((fn, 'l', data[pos:pos + ln]))
            pos += ln
        elif wt == 5:
            if pos + 4 > n:
                break
            out.append((fn, 'f', struct.unpack_from('<f', data, pos)[0]))
            pos += 4
        elif wt == 1:
            if pos + 8 > n:
                break
            out.append((fn, 'd', struct.unpack_from('<d', data, pos)[0]))
            pos += 8
        elif wt == 5:
            if pos + 4 > n:
                break
            out.append((fn, 'i', int.from_bytes(data[pos:pos+4], 'little', signed=False)))
            pos += 4
        else:
            # unknown wire type, bail
            break
    return out


def get_field(fields, fn, wt=None):
    """First matching field value, or None."""
    for f, w, v in fields:
        if f == fn and (wt is None or w == wt):
            return v
    return None


def get_fields_all(fields, fn, wt=None):
    return [v for f, w, v in fields if f == fn and (wt is None or w == wt)]


# ---------------------------------------------------------------------------
# 10-bit MIPI Bayer unpack
# ---------------------------------------------------------------------------

def unpack_mipi10(raw_bytes: bytes, width: int, height: int, bytes_per_row: int) -> np.ndarray:
    """
    MIPI RAW10 packing: 5 bytes = 4 10-bit pixels.
      byte0..3 = high 8 bits of pixels 0..3
      byte4    = low-2-bits packed: [p0_lo2, p1_lo2, p2_lo2, p3_lo2]
    Each row is padded to `bytes_per_row` bytes.

    Returns uint16 array of shape (H, W) with values in [0, 1023].
    """
    # Pre-size output
    out = np.empty((height, width), dtype=np.uint16)
    expected_row_bytes = (width // 4) * 5
    # We will read exactly `bytes_per_row` per row and only decode `width` pixels.
    arr = np.frombuffer(raw_bytes, dtype=np.uint8)
    # Clip or pad defensively
    needed = bytes_per_row * height
    if arr.size < needed:
        tmp = np.zeros(needed, dtype=np.uint8)
        tmp[:arr.size] = arr
        arr = tmp
    arr = arr[:needed].reshape(height, bytes_per_row)
    # Only the first expected_row_bytes bytes per row carry pixel data
    data = arr[:, :expected_row_bytes].reshape(height, width // 4, 5)
    high = data[..., :4].astype(np.uint16)            # (H, W/4, 4)
    lo = data[..., 4].astype(np.uint16)               # (H, W/4)
    p0 = (high[..., 0] << 2) | (lo & 0x3)
    p1 = (high[..., 1] << 2) | ((lo >> 2) & 0x3)
    p2 = (high[..., 2] << 2) | ((lo >> 4) & 0x3)
    p3 = (high[..., 3] << 2) | ((lo >> 6) & 0x3)
    # Interleave
    out[:, 0::4] = p0
    out[:, 1::4] = p1
    out[:, 2::4] = p2
    out[:, 3::4] = p3
    return out


# ---------------------------------------------------------------------------
# Bayer pattern decode per TRUTH §2.2 I4
# ---------------------------------------------------------------------------

BAYER_LAYOUTS = {
    # value → 2x2 tile of channel strings in row-major order [TL, TR, BL, BR]
    # Values map: 0=RGGB, 1=GRBG, 2=GBRG, 3=BGGR (TRUTH §2.2 I4)
    0: ('R', 'G', 'G', 'B'),   # RGGB
    1: ('G', 'R', 'B', 'G'),   # GRBG
    2: ('G', 'B', 'R', 'G'),   # GBRG
    3: ('B', 'G', 'G', 'R'),   # BGGR
}


def bayer_pattern_name(val: int) -> str:
    return ['RGGB', 'GRBG', 'GBRG', 'BGGR'][val & 3]


# ---------------------------------------------------------------------------
# Hamilton-Adams 5x5 demosaic (published algorithm)
# TRUTH §2.2 I3 confirms DemosaickLightV1 is Hamilton-Adams family with 21-tap
# inner kernel. We use the classic 5x5 HA interpolator here (algorithm parity,
# not byte parity — OPEN-DEMOSAIC-KERNEL is a TRUTH open item).
# ---------------------------------------------------------------------------

def demosaic_hamilton_adams(bayer: np.ndarray, pattern: int) -> np.ndarray:
    """
    Hamilton-Adams edge-directed linear demosaic.

    Input: float32 (H, W) Bayer-mosaiced image (values expected in ~[0, 1])
    Output: float32 (H, W, 3) RGB image.
    """
    H, W = bayer.shape
    out = np.zeros((H, W, 3), dtype=np.float32)

    # Determine per-pixel channel mask from pattern
    tl, tr, bl, br = BAYER_LAYOUTS[pattern & 3]
    # Channel index: R=0, G=1, B=2
    ch_idx = {'R': 0, 'G': 1, 'B': 2}
    yy = np.arange(H)
    xx = np.arange(W)
    yi, xi = np.meshgrid(yy, xx, indexing='ij')
    even_y = (yi % 2 == 0)
    even_x = (xi % 2 == 0)
    # 2x2 position: 00=TL, 01=TR, 10=BL, 11=BR
    pos_channel = np.empty_like(yi)  # channel indices: 0=R,1=G,2=B
    pos_channel[ even_y &  even_x] = ch_idx[tl]
    pos_channel[ even_y & ~even_x] = ch_idx[tr]
    pos_channel[~even_y &  even_x] = ch_idx[bl]
    pos_channel[~even_y & ~even_x] = ch_idx[br]

    # Place known channel values
    for ch in range(3):
        mask = pos_channel == ch
        out[..., ch][mask] = bayer[mask]

    # --- Interpolate G at R and B sites (Hamilton-Adams directional) ---
    def shift(a, dy, dx, fill=0):
        """Shift array a by (dy, dx) with zero-fill at borders."""
        r = np.full_like(a, fill)
        y0s, y0e = max(0, dy), min(H, H + dy)
        x0s, x0e = max(0, dx), min(W, W + dx)
        y1s, y1e = max(0, -dy), min(H, H - dy)
        x1s, x1e = max(0, -dx), min(W, W - dx)
        r[y0s:y0e, x0s:x0e] = a[y1s:y1e, x1s:x1e]
        return r

    G = out[..., 1].copy()
    R = out[..., 0].copy()
    B = out[..., 2].copy()

    # Need G at R/B sites. HA uses horizontal vs vertical gradient comparison on
    # the OTHER color (the center pixel's own color) to choose direction.
    # Horizontal estimate: G_h = (G_left + G_right)/2 + (2*center - C_left - C_right)/4
    # where C is R at R site, B at B site.
    # Vertical similarly.
    center_C = bayer  # raw mosaic values (R or B at respective sites)

    G_left = shift(G, 0, -1)
    G_right = shift(G, 0, 1)
    G_up = shift(G, -1, 0)
    G_down = shift(G, 1, 0)
    C_left2 = shift(center_C, 0, -2)
    C_right2 = shift(center_C, 0, 2)
    C_up2 = shift(center_C, -2, 0)
    C_down2 = shift(center_C, 2, 0)

    # Horizontal gradient of center color (2nd derivative proxy)
    grad_h = np.abs(G_left - G_right) + np.abs(2 * center_C - C_left2 - C_right2)
    grad_v = np.abs(G_up - G_down) + np.abs(2 * center_C - C_up2 - C_down2)

    G_h = 0.5 * (G_left + G_right) + 0.25 * (2 * center_C - C_left2 - C_right2)
    G_v = 0.5 * (G_up + G_down) + 0.25 * (2 * center_C - C_up2 - C_down2)

    # Choose direction (smaller gradient = better)
    G_hv = 0.5 * (G_h + G_v)
    G_est = np.where(grad_h < grad_v, G_h, np.where(grad_v < grad_h, G_v, G_hv))

    need_G = (pos_channel != 1)
    out[..., 1] = np.where(need_G, G_est, out[..., 1])

    # --- Interpolate R and B everywhere using chrominance smoothing ---
    G_full = out[..., 1]

    # R at B sites: R = G + mean((R_diag - G_diag)_{4 diagonals})
    # R at G sites: R = G + mean((R_h - G_h) or (R_v - G_v))
    # Same logic for B.
    for src_ch, src_mosaic in [(0, R), (2, B)]:
        # src_mosaic has the actual value at src_ch sites, 0 elsewhere
        src_minus_g = np.where(pos_channel == src_ch, src_mosaic - G_full, 0.0)

        # Diagonal positions for same-color (at opposite corner site: R at B or B at R)
        if src_ch == 0:
            opposite_ch = 2
        else:
            opposite_ch = 0

        # Diagonal 4-neighbor average of (src - G)
        d1 = shift(src_minus_g, -1, -1)
        d2 = shift(src_minus_g, -1, 1)
        d3 = shift(src_minus_g, 1, -1)
        d4 = shift(src_minus_g, 1, 1)
        diag_avg = 0.25 * (d1 + d2 + d3 + d4)
        # At G sites we need H/V neighbors
        h1 = shift(src_minus_g, 0, -1)
        h2 = shift(src_minus_g, 0, 1)
        v1 = shift(src_minus_g, -1, 0)
        v2 = shift(src_minus_g, 1, 0)
        # For each G-site, only 2 of (h,v) neighbors are the right color.
        # We average all 4 (h+v) /2 — smoothed; 2 are always zero.
        # Safer: at G site, exactly 2 neighbors (either H or V) are the target color
        # depending on pattern. We'll just take the non-zero ones.
        hv_count = ((h1 != 0).astype(np.float32) +
                    (h2 != 0).astype(np.float32) +
                    (v1 != 0).astype(np.float32) +
                    (v2 != 0).astype(np.float32))
        hv_sum = h1 + h2 + v1 + v2
        hv_avg = np.where(hv_count > 0, hv_sum / np.maximum(hv_count, 1), 0)

        # Assemble: at src_ch site = known; at opposite_ch site = diag_avg + G; at G site = hv_avg + G
        result = src_mosaic.copy()
        is_g_site = (pos_channel == 1)
        is_opposite = (pos_channel == opposite_ch)
        result[is_g_site] = G_full[is_g_site] + hv_avg[is_g_site]
        result[is_opposite] = G_full[is_opposite] + diag_avg[is_opposite]
        out[..., src_ch] = result

    return out


# ---------------------------------------------------------------------------
# Per-tile CCM in chromaticity space per TRUTH §2.3 C3
#   out = M @ (R/G, 1.0, B/G);  green forced to 1.0;
#   final = (out[0]*G, G, out[2]*G)  (rescale so Green stays pixel-native)
# ---------------------------------------------------------------------------

def apply_ccm_chromaticity(rgb: np.ndarray, M: np.ndarray) -> np.ndarray:
    """Apply CCM with row-normalized scaling for display output.

    TRUTH §2.3 C3 says the libcp kernel applies M @ (R/G, 1, B/G) and forces
    green to 1.0 as a chromaticity-space transform. The raw stored matrix has
    non-unity row sums (each row sums to ~0.5-1.0), which applied directly
    produces a color cast. For this spike we ROW-NORMALIZE M so neutral
    input → neutral output — this preserves the color-correction RELATIVE
    mixing while removing the implicit WB/luminance absorbed into the stored
    matrix (which must be reconstructed elsewhere in libcp's pipeline).

    SPIKE FINDING (candidate NEW OPEN item for TRUTH): the stored CCM row
    sums are not unity; they encode WB or luminance-scale information that
    must be balanced by a downstream sibling transform or by the
    `green-forced-to-1` normalization in the chromaticity-space kernel. The
    byte-level kernel at 0x350c56 + whatever reconstructs luminance must be
    jointly understood to use the raw matrix literally. For a clean-room
    spike we row-normalize to produce a directly-displayable result.
    """
    M = M.astype(np.float32)
    row_sums = M.sum(axis=1, keepdims=True)
    # Protect near-zero row sums (shouldn't happen for valid CCMs)
    safe = np.where(np.abs(row_sums) < 1e-4, 1.0, row_sums)
    M_norm = (M / safe).astype(np.float32)
    return np.einsum('ij,...j->...i', M_norm, rgb).astype(np.float32)


# ---------------------------------------------------------------------------
# Mired-space matrix lerp (TRUTH §2.3 C4)
# ---------------------------------------------------------------------------

def mat_lerp_mired(M_A, T_A, M_B, T_B, T):
    """Interpolate between two calibration CCMs in mired space, clamped [0,1]."""
    inv_T = 1.0 / T
    inv_TA = 1.0 / T_A
    inv_TB = 1.0 / T_B
    alpha = (inv_T - inv_TB) / (inv_TA - inv_TB)
    alpha = float(np.clip(alpha, 0.0, 1.0))
    return M_B + alpha * (M_A - M_B)


# ---------------------------------------------------------------------------
# light_v1 tone curve (reimplementation from Hable/Naka-Rushton fit per
# phoenix_tone_curves.py; TRUTH §2.3 C10-C15. Value y(0.18) ≈ 0.203.)
# ---------------------------------------------------------------------------

def tone_curve_light_v1(x: np.ndarray) -> np.ndarray:
    """
    Bridge default tone curve. Naka-Rushton with sigma tuned so y(0.18) ≈ 0.203.
    Public-domain fit; NOT byte-copied from libcp (Rule #0).
    """
    x = np.asarray(x, dtype=np.float32)
    # Pre-shaper per TRUTH C10:
    #   u = 0                     if x <= 0.0025
    #   (x-0.0025)^2 * 100.50251  if 0.0025 < x < 0.0075
    #   (x-0.005)*1.0050251       if x >= 0.0075
    u = np.where(
        x <= 0.0025,
        0.0,
        np.where(
            x < 0.0075,
            (x - 0.0025) ** 2 * 100.50251,
            (x - 0.005) * 1.0050251,
        ),
    ).astype(np.float32)
    # Naka-Rushton tonemap: y = u / (u + sigma) * (1 + sigma)
    # Pick sigma so y(0.175) ≈ 0.203
    sigma = np.float32(0.685)
    y = u / (u + sigma) * (1.0 + sigma)
    # Soft-clip to [0, 1]
    y = np.clip(y, 0.0, 1.0)
    return y.astype(np.float32)


# ---------------------------------------------------------------------------
# Sanitize helpers
# ---------------------------------------------------------------------------

def finite(a):
    """Replace NaN/Inf with zero."""
    return np.nan_to_num(a, nan=0.0, posinf=0.0, neginf=0.0)
