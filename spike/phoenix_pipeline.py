#!/usr/bin/env python3
"""
phoenix_pipeline.py — L16 Lumen → 52MP clean-room pipeline skeleton
====================================================================

Implements all verified ISP stages. Raw image loading is stubbed (TODO).

Pipeline (per camera):
  raw uint16 → BLC+AWB normalize → [BayerPhaseCorrect stub] →
  HA demosaic → CCM (chromaticity-space, mired lerp) →
  vignette multiply → tone curve (light_v1 Hable)

Then: reproject each contributor → anchor frame via H = K2·R·K1⁻¹ (Z-divide)
      → weighted average blend → 52MP output TIFF

Verified facts:
  BL = 42.0, WL = 1023.0 (AR1335, hardcoded)
  BLC+AWB: output_C = (raw - BL) / (981.0 * wb_C)   [libcp+0x352ce0]
  CCM: simple matmul out=M@[R,G,B] (ImageApplyColorMatrix libcp+0xaa260)  [C3]
  CCM lerp: mired-space MatLerpClamped TungstenA↔D65, default 4300K (α≈0.401) [C4]
  Vignetting: 17×13 per-channel multiply grid  [I5]
  Tone curve: light_v1 Hable fit (phoenix_tone_curves.py, no LUT bytes)
  Canvas: 28mm=10432×7824, 70mm≈8848×6624  [Z1]
  Firing: 28/35mm=5A+5B, 70/150mm=5B+6C  [F1]
  IRAMP warp: H = K2·(R|t)·K1⁻¹, per-pixel Z-divide  [libcp+0x366d1c]
"""

import sys
import struct
import math
import numpy as np
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "phoenix-handoff" / "decoders"))
sys.path.insert(0, str(REPO_ROOT / "phoenix-handoff" / "phoenix_modules"))

from phoenix_tone_curves import light_v1

# ── Constants ────────────────────────────────────────────────────────────────

BL = 42.0
WL = 1023.0
RANGE = WL - BL  # 981.0

# All tiers output 10432×7824. 35mm/150mm use internal crops upsampled to this.
# Crop formula: r = ref_focal/image_focal; RectF = ((1-r)/2, (1-r)/2, (1+r)/2, (1+r)/2)
#   35mm:  r=28/35=0.800 → internal crop ~8345×6259, then upsampled
#   150mm: r=70/150=0.467 → internal crop ~4865×3641, then upsampled
# [Verified: LLDB BPs at libcp+0xe6d90 and libcp+0x3b2313]
CANVAS = {
    "28mm":  (10432, 7824),
    "35mm":  (10432, 7824),
    "70mm":  (10432, 7824),
    "150mm": (10432, 7824),
}

CROP_RECT = {
    "28mm":  (0.000, 0.000, 1.000, 1.000),
    "35mm":  (0.100, 0.100, 0.900, 0.900),  # r=0.8
    "70mm":  (0.000, 0.000, 1.000, 1.000),
    "150mm": (0.267, 0.267, 0.733, 0.733),  # r=70/150
}

# Camera IDs: A1-A5=0-4, B1-B5=5-9, C1-C6=10-15
FIRING_RULES = {
    "28mm":  list(range(0, 5)) + list(range(5, 10)),   # 5A + 5B
    "35mm":  list(range(0, 5)) + list(range(5, 10)),   # 5A + 5B
    "70mm":  list(range(5, 10)) + list(range(10, 16)), # 5B + 6C
    "150mm": list(range(5, 10)) + list(range(10, 16)), # 5B + 6C
}

ANCHOR_CAM = {
    "28mm": 0,   # A1
    "35mm": 0,   # A1
    "70mm": 5,   # B1
    "150mm": 5,  # B1
}

# CCM illuminant CCTs (K) — CIE defined values, not extracted from libcp
_CCT_TUNGSTEN_A = 2856.0   # CIE illuminant A
_CCT_D65        = 6504.0   # CIE D65

# Robertson (1968) Table 1 (W&S "Color Science" §3.11) — CIE 1960 UCS isotemperature lines
# (mired, u, v, slope) — 31 entries 0..600 mired.
# Confirmed vs libcp: constant at VA 0x5ab180 = (175.0, 0.20525, 0.31647, -0.84901) ✓
# Clean-room source: Robertson A.R. 1968, JOSA 58(11):1528-1535.
_ROBERTSON_TABLE = [
    (  0, 0.18006, 0.26352, -0.24341),
    ( 10, 0.18066, 0.26589, -0.25479),
    ( 20, 0.18133, 0.26846, -0.26876),
    ( 30, 0.18208, 0.27119, -0.28539),
    ( 40, 0.18293, 0.27407, -0.30470),
    ( 50, 0.18388, 0.27709, -0.32675),
    ( 60, 0.18494, 0.28021, -0.35156),
    ( 70, 0.18611, 0.28342, -0.37915),
    ( 80, 0.18740, 0.28668, -0.40955),
    ( 90, 0.18880, 0.28997, -0.44278),
    (100, 0.19032, 0.29326, -0.47888),
    (125, 0.19462, 0.30141, -0.58204),
    (150, 0.19962, 0.30921, -0.70471),
    (175, 0.20525, 0.31647, -0.84901),
    (200, 0.21142, 0.32312, -1.0182 ),
    (225, 0.21807, 0.32909, -1.2168 ),
    (250, 0.22511, 0.33439, -1.4512 ),
    (275, 0.23247, 0.33904, -1.7298 ),
    (300, 0.24010, 0.34308, -2.0637 ),
    (325, 0.24792, 0.34655, -2.4681 ),
    (350, 0.25591, 0.34951, -2.9641 ),
    (375, 0.26400, 0.35200, -3.5814 ),
    (400, 0.27218, 0.35407, -4.3633 ),
    (425, 0.28039, 0.35577, -5.3762 ),
    (450, 0.28863, 0.35714, -6.7262 ),
    (475, 0.29685, 0.35823, -8.5955 ),
    (500, 0.30505, 0.35907, -11.324 ),
    (525, 0.31320, 0.35968, -15.628 ),
    (550, 0.32129, 0.36011, -23.325 ),
    (575, 0.32931, 0.36038, -40.770 ),
    (600, 0.33724, 0.36051, -116.45 ),
]


# ── LRI parsing ──────────────────────────────────────────────────────────────

def _read_varint(data, off):
    r = s = 0
    while off < len(data):
        b = data[off]; off += 1
        r |= (b & 0x7f) << s
        if not (b & 0x80): break
        s += 7
    return r, off

def _parse_fields(data):
    out = []; off = 0
    while off < len(data):
        try: tag, off = _read_varint(data, off)
        except Exception: break
        wt = tag & 7; fn = tag >> 3
        if fn == 0: break
        if wt == 2:
            try: n, off = _read_varint(data, off)
            except Exception: break
            if off + n > len(data): break
            out.append((fn, 'len', data[off:off+n])); off += n
        elif wt == 0:
            try: v, off = _read_varint(data, off)
            except Exception: break
            out.append((fn, 'varint', v))
        elif wt == 5:
            if off + 4 > len(data): break
            out.append((fn, 'f32', struct.unpack_from('<f', data, off)[0])); off += 4
        elif wt == 1:
            if off + 8 > len(data): break
            out.append((fn, 'd64', struct.unpack_from('<d', data, off)[0])); off += 8
        else: break
    return out

def _scan_lelr(file_bytes):
    blocks = []; pos = 0
    while pos + 32 <= len(file_bytes) and file_bytes[pos:pos+4] == b'LELR':
        blen  = struct.unpack_from('<Q', file_bytes, pos+4)[0]
        moff  = struct.unpack_from('<Q', file_bytes, pos+12)[0]
        mlen  = struct.unpack_from('<I', file_bytes, pos+20)[0]
        mtype = file_bytes[pos+24]
        pstart = pos + moff
        blocks.append({'type': mtype, 'start': pstart, 'len': mlen,
                       'payload': file_bytes[pstart:pstart+mlen]})
        if blen == 0: break
        pos += blen
    return blocks

def _f32_mat(data):
    """Parse repeated f32 fields as float list."""
    return [v for _, wt, v in _parse_fields(data) if wt == 'f32']

def _mat3(data):
    """Parse a Matrix3x3F submessage → 3×3 numpy array (row-major).

    Handles two encodings:
    - 9 individual f32 fields (f1..f9) as used in intrinsics/rotation
    - Nested len-delimited rows each containing f32 elements
    """
    vals = [v for _, wt, v in _parse_fields(data) if wt == 'f32']
    if not vals:
        for _, wt, v in _parse_fields(data):
            if wt == 'len':
                vals.extend(_f32_mat(v))
    arr = np.array(vals[:9], dtype=np.float64)
    return arr.reshape(3, 3) if arr.size == 9 else None

def parse_lri(path):
    """
    Parse LRI and return:
      focal_mm (int), tier (str), cam_modules (dict cam_id→{wb_R,wb_Gr,wb_Gb,wb_B}),
      factory_cals (dict cam_id→{K, R, t, vignette_grid, ccm_list}),
      awb_gains (dict {R,Gr,Gb,B})
    """
    data = Path(path).read_bytes()
    blocks = _scan_lelr(data)

    # Find LightHeader block (msg_type=0, largest small block)
    lh_block = next((b for b in blocks if b['type'] == 0), None)
    if not lh_block:
        raise ValueError("No LightHeader block found")

    lh_fields = _group_fields(_parse_fields(lh_block['payload']))

    # Field 4: focal length
    focal_mm = lh_fields.get(4, [('', 'varint', 28)])[0][2]
    tier = _focal_tier(focal_mm)

    # Field 19: ViewPreferences → AWB gains (scan all type-0 blocks)
    awb_gains = {'R': 1.0, 'Gr': 1.0, 'Gb': 1.0, 'B': 1.0}
    for blk in blocks:
        if blk['type'] != 0: continue
        bf = _group_fields(_parse_fields(blk['payload']))
        if 19 not in bf: continue
        vp_data = bf[19][0][2]
        for fn2, wt2, v2 in _parse_fields(vp_data):
            if fn2 == 15 and wt2 == 'len':
                cg = _parse_fields(v2)
                cg_map = {fn3: v3 for fn3, wt3, v3 in cg if wt3 == 'f32'}
                awb_gains = {
                    'R':  cg_map.get(1, 1.0),
                    'Gr': cg_map.get(2, 1.0),
                    'Gb': cg_map.get(3, 1.0),
                    'B':  cg_map.get(4, 1.0),
                }
        break

    # Field 13: FactoryModuleCalibration[] — spread across multiple type-0 blocks
    factory_cals = {}
    for blk in blocks:
        if blk['type'] != 0: continue
        bf = _group_fields(_parse_fields(blk['payload']))
        if 13 not in bf: continue
        for _, wt, fmc_data in bf[13]:
            if wt != 'len': continue
            fmc = _group_fields(_parse_fields(fmc_data))
            if 1 not in fmc: continue
            cam_id = fmc[1][0][2]
            # FMC for one camera is split across multiple blocks — merge into one cal
            if cam_id not in factory_cals:
                factory_cals[cam_id] = {'K': None, 'R': None, 't': None,
                                        'vignette_grid': None, 'ccm_list': [], 'k_bundles': []}
            cal = factory_cals[cam_id]

            # f3 = GeometricCalibration → f2[] CalibrationFocusBundle (repeated)
            # Each bundle is either a K-bundle (f2=Intrinsics, f6=focus_hall_code)
            # or an extrinsics bundle (f3=Extrinsics, f4=0, no K).
            if 3 in fmc:
                gc_data = fmc[3][0][2]
                for _, wt2, cfb_data in _parse_fields(gc_data):
                    if wt2 != 'len': continue
                    cfb = _group_fields(_parse_fields(cfb_data))
                    if 2 in cfb and cfb[2][0][1] == 'len':
                        # K-bundle: has Intrinsics (f2) + focus_hall_code (f6)
                        K = None
                        for _, wt3, km_data in _parse_fields(cfb[2][0][2]):
                            if wt3 == 'len':
                                K = _mat3(km_data)
                                break
                        hall_code = None
                        if 6 in cfb:
                            hc = cfb[6][0]
                            hall_code = hc[2] if hc[1] in ('f32', 'varint') else None
                        if K is not None:
                            cal['k_bundles'].append({'hall_code': hall_code, 'K': K})
                            if cal['K'] is None:
                                cal['K'] = K  # fallback: first K bundle
                    elif 3 in cfb:
                        # Extrinsics bundle: has R and t (canonical or movable_mirror)
                        ext = cfb[3][0][2]
                        for fn4, wt4, can_data in _parse_fields(ext):
                            if fn4 == 1 and wt4 == 'len':
                                # canonical: f1=rotation, f2=translation
                                can = _group_fields(_parse_fields(can_data))
                                if 1 in can: cal['R'] = _mat3(can[1][0][2])
                                if 2 in can:
                                    t_vals = _f32_mat(can[2][0][2])
                                    cal['t'] = np.array(t_vals[:3], dtype=np.float64) if t_vals else None
                            elif fn4 == 2 and wt4 == 'len':
                                # movable_mirror: f1=MirrorSystem
                                mm = _group_fields(_parse_fields(can_data))
                                if 1 in mm:
                                    ms = _group_fields(_parse_fields(mm[1][0][2]))
                                    if 1 in ms:
                                        t_vals = _f32_mat(ms[1][0][2])
                                        cal['t'] = np.array(t_vals[:3], dtype=np.float64) if t_vals else None
                                    if 2 in ms:
                                        cal['R'] = _mat3(ms[2][0][2])

            # f4 = photometric: f2 = per-focus vignette entries
            # Structure: phot.f2 → {f1: hall_code, f2: {f1: w, f2: h, f3: raw_f32_blob}}
            if 4 in fmc:
                phot_data = fmc[4][0][2]
                for fn4, wt4, v4 in _parse_fields(phot_data):
                    if fn4 == 2 and wt4 == 'len':
                        for fn5, wt5, v5 in _parse_fields(v4):
                            if fn5 == 2 and wt5 == 'len':
                                for fn6, wt6, v6 in _parse_fields(v5):
                                    if fn6 == 3 and wt6 == 'len' and len(v6) == 884:
                                        floats = np.frombuffer(v6, dtype='<f4')
                                        cal['vignette_grid'] = floats.reshape(13, 17)
                        break  # use first focus bundle's vignetting

            # f2 = ColorCalibration[]
            if 2 in fmc:
                for _, wt2, cc_data in fmc[2]:
                    if wt2 != 'len': continue
                    cc = _group_fields(_parse_fields(cc_data))
                    mode = cc[1][0][2] if 1 in cc else -1
                    fwd_ccm = _mat3(cc[2][0][2]) if 2 in cc else None  # forward CCM: sensor→display
                    inv_ccm = _mat3(cc[3][0][2]) if 3 in cc else None  # inverse CCM: display→sensor
                    cal['ccm_list'].append({'mode': mode, 'ccm': inv_ccm, 'fwd_ccm': fwd_ccm})

            factory_cals[cam_id] = cal

    # Field 12: CameraModule[] — from per-shot LightHeader (block 0)
    cam_modules = {}
    for _, wt, cm_data in lh_fields.get(12, []):
        if wt != 'len': continue
        cm = _group_fields(_parse_fields(cm_data))
        if 2 not in cm: continue
        cam_id = cm[2][0][2]
        lens_pos = cm[5][0][2] if 5 in cm else None
        cam_modules[cam_id] = {'wb_R': awb_gains['R'], 'wb_Gr': awb_gains['Gr'],
                                'wb_Gb': awb_gains['Gb'], 'wb_B': awb_gains['B'],
                                'lens_position_hall': lens_pos}

    # Select best K per camera by argmin(|lens_position_hall - focus_hall_code|)
    # R/t come from the extrinsics bundle (already set directly during parsing)
    for cam_id, cal in factory_cals.items():
        valid = [b for b in cal.get('k_bundles', [])
                 if b['hall_code'] is not None and b['K'] is not None]
        if len(valid) <= 1:
            continue
        lens_pos = cam_modules.get(cam_id, {}).get('lens_position_hall')
        if lens_pos is None:
            continue
        best = min(valid, key=lambda b: abs(b['hall_code'] - lens_pos))
        cal['K'] = best['K']

    # neutral_xy: (x,y) chromaticity from LRI Field 19 auto_white_balance.neutral_color
    # TODO: parse from Field 19 sub-message (field number not yet decoded; needs RE)
    return {'focal_mm': focal_mm, 'tier': tier,
            'cam_modules': cam_modules, 'factory_cals': factory_cals,
            'awb_gains': awb_gains, 'neutral_xy': None}

def _group_fields(fields):
    out = {}
    for fn, wt, v in fields:
        out.setdefault(fn, []).append((fn, wt, v))
    return out

def _focal_tier(mm):
    if mm <= 31:  return "28mm"
    if mm <= 52:  return "35mm"
    if mm <= 110: return "70mm"
    return "150mm"


# ── Raw image loading ─────────────────────────────────────────────────────────

def _parse_camera_surfaces(lri_path):
    """
    Read per-camera Surface metadata from ALL type-0 LELR blocks.

    Returns dict: cam_id → {data_offset, row_stride, width, height, format}

    Surface.format=7 means RAW_PACKED_10BPP (MIPI RAW10).
    data_offset is a FILE-ABSOLUTE byte offset (= block_start + surface.data_offset,
    since each block stores data_offset relative to its own block start).
    """
    surfaces = {}
    with open(lri_path, 'rb') as f:
        raw = f.read()

    pos = 0
    while pos + 32 <= len(raw) and raw[pos:pos+4] == b'LELR':
        blen  = struct.unpack_from('<Q', raw, pos+4)[0]
        moff  = struct.unpack_from('<Q', raw, pos+12)[0]
        mlen  = struct.unpack_from('<I', raw, pos+20)[0]
        mtype = raw[pos+24]
        block_start = pos  # absolute file position of this LELR block

        if mtype == 0:
            proto = raw[pos + moff : pos + moff + mlen]
            for fn, wt, val in _parse_fields(proto):
                if fn != 12 or wt != 'len':
                    continue
                cam_id = None
                surf = {}
                for cfn, cwt, cv in _parse_fields(val):
                    if cfn == 2 and cwt == 'varint':
                        cam_id = cv
                    elif cfn == 9 and cwt == 'len':
                        for sfn, swt, sv in _parse_fields(cv):
                            if sfn == 1 and swt == 'len':   # bayer_phase: Point2I {f1:x, f2:y}
                                bpts = [v2 for f2, t2, v2 in _parse_fields(sv) if t2 == 'varint']
                                if len(bpts) >= 2:
                                    surf['bayer_phase'] = (bpts[0], bpts[1])
                            elif sfn == 2 and swt == 'len':   # size: Point2I
                                pts = [(f2, v2) for f2, t2, v2 in _parse_fields(sv) if t2 == 'varint']
                                if len(pts) >= 2:
                                    surf['width']  = pts[0][1]
                                    surf['height'] = pts[1][1]
                            elif sfn == 3 and swt == 'varint':
                                surf['format'] = sv          # 7 = RAW_PACKED_10BPP
                            elif sfn == 4 and swt == 'varint':
                                surf['row_stride'] = sv
                            elif sfn == 5 and swt == 'varint':
                                # data_offset is block-relative; make file-absolute
                                surf['data_offset'] = block_start + sv
                if cam_id is not None and surf:
                    surfaces.setdefault(cam_id, {}).update(surf)

        if blen == 0:
            break
        pos += blen
    return surfaces


def _unpack_mipi_raw10(raw_bytes, width, height, stride):
    """
    Unpack MIPI RAW10: 4 pixels per 5 bytes (CSI-2 packing).
      B0=px0[9:2], B1=px1[9:2], B2=px2[9:2], B3=px3[9:2]
      B4={px3[1:0], px2[1:0], px1[1:0], px0[1:0]}
    Returns uint16 array (height, width).
    """
    n_groups = width // 4
    row_len = n_groups * 5
    data = np.frombuffer(raw_bytes, dtype=np.uint8)
    B = np.zeros((height, n_groups, 5), dtype=np.uint8)
    for row in range(height):
        B[row] = data[row * stride : row * stride + row_len].reshape(n_groups, 5)
    out = np.empty((height, width), dtype=np.uint16)
    out[:, 0::4] = (B[:, :, 0].astype(np.uint16) << 2) | (B[:, :, 4] & 0x03)
    out[:, 1::4] = (B[:, :, 1].astype(np.uint16) << 2) | ((B[:, :, 4] >> 2) & 0x03)
    out[:, 2::4] = (B[:, :, 2].astype(np.uint16) << 2) | ((B[:, :, 4] >> 4) & 0x03)
    out[:, 3::4] = (B[:, :, 3].astype(np.uint16) << 2) | ((B[:, :, 4] >> 6) & 0x03)
    return out


def load_raw_bayer(lri_path, camera_id):
    """
    Extract raw uint16 Bayer frame for camera_id from LRI MIPI RAW10 gap data.

    Returns (float32 array (H, W) with values in [0, 1023], bayer_phase tuple).
    bayer_phase = (red_x, red_y) from Surface.f1; defaults to (0, 0) = RGGB.
    Raises KeyError if camera_id not found in the LRI.
    """
    surfaces = _parse_camera_surfaces(lri_path)
    if camera_id not in surfaces:
        raise KeyError(f"camera_id {camera_id} not in LRI (available: {sorted(surfaces)})")

    s = surfaces[camera_id]
    width       = s['width']
    height      = s['height']
    stride      = s['row_stride']
    data_offset = s['data_offset']
    fmt         = s.get('format', 7)

    if fmt != 7:
        raise NotImplementedError(f"Surface.format={fmt} not RAW_PACKED_10BPP (7); unsupported")

    nbytes = height * stride
    with open(lri_path, 'rb') as f:
        f.seek(data_offset)
        raw_bytes = f.read(nbytes)

    if len(raw_bytes) < nbytes:
        raise IOError(f"Short read: expected {nbytes} bytes, got {len(raw_bytes)}")

    pixels = _unpack_mipi_raw10(raw_bytes, width, height, stride)
    bayer_phase = s.get('bayer_phase', (0, 0))  # default RGGB
    return pixels.astype(np.float32), bayer_phase


# ── ISP stages ───────────────────────────────────────────────────────────────

def blc_awb_normalize(raw_f32, wb_R, wb_Gr, wb_Gb, wb_B, bayer_phase=(0, 0)):
    """
    Combined BLC + AWB normalization.
    Field 19 ChannelGain values are stored boost factors (e.g. R=1.7178).
    libcp [libcp+0x352ce0] pre-computes reciprocals and multiplies — equivalent to
    dividing by the stored gain: output_C = (raw - BL) / wb_C / RANGE.
    LLDB-verified: context_ptr[0]=0.5821 = 1/1.7178 (color_pipeline_audit.md).
    bayer_phase = (red_x, red_y).
    Returns float32 (H, W) with values ~[0, 1].
    """
    out = np.empty_like(raw_f32)
    rx, ry = bayer_phase
    wb_G = (wb_Gr + wb_Gb) * 0.5

    gains = np.ones((2, 2), dtype=np.float64)
    gains[ry,     rx]     = wb_R
    gains[ry,     1-rx]   = wb_G
    gains[1-ry,   rx]     = wb_G
    gains[1-ry,   1-rx]   = wb_B

    sub = (raw_f32 - BL).clip(0)
    for row in range(2):
        for col in range(2):
            out[row::2, col::2] = sub[row::2, col::2] / gains[row, col] / RANGE
    return out.clip(0, 1)


def bayer_phase_correct(bayer_f32):
    """
    BayerPhaseCorrect (ImageCorrectBayerPhaseAR1335, libcp+0x340cc0).
    Halide inner kernel 0x3589c0: anisotropic 2nd-order gradient equalization.

    Per-pixel: computes horizontal and vertical 2nd-order differences (stride-2
    neighbors), selects the minimum-gradient direction, applies a fixed-point
    scaled correction. Scale factor = int(min(inv_g1x, inv_g1y, inv_b) * 0.9 * 1024).

    arg1=rbx+0x1670, arg2=rbx+0x1674 — both initialized to 1.0f at VA 0x329b96
    and never overridden on the bridge codepath.

    With arg1=arg2=1.0: gain_range=0 → scale=0 → all corrections zero.
    Pass-through is CORRECT for all normal L16 bridge renders.
    Only activates when channel gains differ (non-bridge/custom pipeline paths).
    """
    return bayer_f32


def demosaic_ha(bayer_f32, bayer_phase=(0, 0)):
    """
    Hamilton-Adams inverse-gradient-weighted demosaic.
    Approximates DemosaickLightV1 Phase B (single-scale) without pyramid.
    Returns float32 (H, W, 3) in RGB order.
    bayer_phase = (red_x, red_y).
    """
    try:
        import colour_demosaicing as cd
        # colour_demosaicing pattern strings: RGGB, GRBG, GBRG, BGGR
        patterns = {(0,0):'RGGB', (1,0):'GRBG', (0,1):'GBRG', (1,1):'BGGR'}
        pat = patterns.get(bayer_phase, 'BGGR')
        rgb = cd.demosaicing_CFA_Bayer_Malvar2004(bayer_f32, pat)
        return rgb.astype(np.float32)
    except ImportError:
        # Fallback: simple bilinear via OpenCV
        try:
            import cv2
            patterns_cv = {(0,0): cv2.COLOR_BAYER_RG2RGB,
                           (1,0): cv2.COLOR_BAYER_GR2RGB,
                           (0,1): cv2.COLOR_BAYER_GB2RGB,
                           (1,1): cv2.COLOR_BAYER_BG2RGB}
            u16 = (bayer_f32 * 1023).clip(0, 1023).astype(np.uint16)
            rgb = cv2.cvtColor(u16, patterns_cv.get(bayer_phase, cv2.COLOR_BAYER_BG2RGB))
            return (rgb / 1023.0).astype(np.float32)
        except ImportError:
            # Bare numpy bilinear (BGGR assumed)
            H, W = bayer_f32.shape
            rgb = np.zeros((H, W, 3), dtype=np.float32)
            rx, ry = bayer_phase
            rgb[:, :, 0] = bayer_f32   # placeholder; real bilinear omitted for brevity
            rgb[:, :, 1] = bayer_f32
            rgb[:, :, 2] = bayer_f32
            return rgb


def _robertson_cct(x, y):
    """
    Robertson (1968) CCT from CIE xy chromaticity.
    Matches libcp CCTFromChromaticity at VA 0xab2e0.
    Returns K, or 0.0 if xy is off the Robertson locus.
    """
    denom = -2*x + 12*y + 3
    if abs(denom) < 1e-10:
        return 0.0
    u = 4*x / denom
    v = 6*y / denom
    prev_cross = None
    for i in range(1, 31):
        mi, ui, vi, ti = _ROBERTSON_TABLE[i]
        norm = math.sqrt(1.0 + ti*ti)
        cross = ((v - vi) - ti*(u - ui)) / norm
        if prev_cross is not None and (prev_cross > 0 >= cross or prev_cross < 0 <= cross):
            alpha = prev_cross / (prev_cross - cross)
            mr_prev = _ROBERTSON_TABLE[i-1][0]
            mired = mr_prev + alpha * (mi - mr_prev)
            return 1e6 / mired if mired > 0 else float('inf')
        prev_cross = cross
    return 0.0


def select_ccm(ccm_list, neutral_xy=None):
    """
    Select CCM for the capture's illuminant.

    Doc 23 (23_CCM_COLOR_DIAGNOSIS.md): awb_mode=0 → mode 2 (D65) directly.
    neutral_color (neutral_xy) is NEVER present in real L16 LRIs, so mode 2
    is always the correct choice. Mired interpolation was incorrect.

    Uses mode 0 (TungstenA, 2856K) and mode 2 (D65, 6504K) from ccm_list.
    Mode 6 (F11) is stored in LRI but NOT loaded at runtime (LLDB-verified).
    """
    ccm_by_mode = {e['mode']: e['fwd_ccm'] for e in ccm_list if e.get('fwd_ccm') is not None}
    M_D = ccm_by_mode.get(2)   # D65 — always selected for awb_mode=0
    M_A = ccm_by_mode.get(0)   # TungstenA — fallback only

    if M_D is not None:
        return M_D
    if M_A is not None:
        return M_A
    return np.eye(3, dtype=np.float64)


def apply_ccm(rgb, ccm3x3):
    """
    Apply forward CCM (fwd_ccm, sensor→display) to image.
    lt::(anon)::ImageApplyColorMatrix at libcp+0xaa260; per-pixel SSE kernel at 0xab940.
    Formula: rgb @ M  (no transpose — forward CCM is already in row-vector form).
    Diagnostic-verified: fwd_ccm without transpose produces neutral R≈G≈B output;
    inv_ccm@.T was wrong (extreme green cast G=0.449, R=0.155 pre-tone).
    """
    h, w, _ = rgb.shape
    out = (rgb.reshape(-1, 3) @ ccm3x3).reshape(h, w, 3)
    return out.clip(0, 1).astype(np.float32)


def apply_vignette(rgb, grid_13x17):
    """
    Multiply vignette correction: 17×13 per-channel flat-gain grid.
    grid_13x17 shape: (13, 17) — single channel (assumed same across RGB).
    [I5]
    """
    H, W = rgb.shape[:2]
    from scipy.ndimage import zoom
    scale = zoom(grid_13x17, (H / 13.0, W / 17.0), order=1)
    return (rgb * scale[:, :, None]).clip(0, 1).astype(np.float32)


def apply_tone_curve(rgb):
    """
    light_v1 Hable tone curve from phoenix_tone_curves.py.
    Input: linear scene-radiance [0, ~1]. Output: tone-mapped [0, ~1].
    """
    return light_v1(rgb).astype(np.float32)


def isp_camera(raw_f32, cam_id, wb_gains, factory_cal, bayer_phase=(0, 0), neutral_xy=None):
    """Full per-camera ISP: BLC+AWB → BayerPhaseCorrect → demosaic → CCM → vignette → tone."""
    wb_R  = wb_gains.get('R', 1.0)
    wb_Gr = wb_gains.get('Gr', 1.0)
    wb_Gb = wb_gains.get('Gb', 1.0)
    wb_B  = wb_gains.get('B', 1.0)

    bayer = blc_awb_normalize(raw_f32, wb_R, wb_Gr, wb_Gb, wb_B, bayer_phase)
    bayer = bayer_phase_correct(bayer)
    rgb   = demosaic_ha(bayer, bayer_phase)

    ccm_list = factory_cal.get('ccm_list', []) if factory_cal else []
    ccm = select_ccm(ccm_list, neutral_xy) if ccm_list else None
    if ccm is not None:
        rgb = apply_ccm(rgb, ccm)

    vig = factory_cal.get('vignette_grid') if factory_cal else None
    if vig is not None:
        rgb = apply_vignette(rgb, vig)

    rgb = apply_tone_curve(rgb)
    return rgb


# ── Reprojection ─────────────────────────────────────────────────────────────

def build_homography(K_anchor, R_contrib, t_contrib, K_contrib, R_anchor=None):
    """
    Rotation-only homography for planar/far-field scenes.
    R convention: world→camera (R_cw) as stored in LRI real_camera_orientation.

    H = K_anchor · R_anchor · R_contrib^T · K_contrib⁻¹

    R_anchor defaults to eye(3) when anchor is the world reference frame.
    Translation t is dropped (zero-row trick; valid when scene depth >> baseline).
    Returns 3×3 float64.
    """
    if R_anchor is None:
        R_anchor = np.eye(3, dtype=np.float64)
    R_rel = R_anchor @ R_contrib.T
    return K_anchor @ R_rel @ np.linalg.inv(K_contrib)


def reproject(rgb_contrib, H, canvas_hw):
    """
    Reproject rgb_contrib (H_src × W_src × 3) into canvas_hw using homography H.
    Returns float32 (canvas_H × canvas_W × 3), zeros where out-of-bounds.
    """
    try:
        import cv2
        canvas_H, canvas_W = canvas_hw
        H3x3 = H[:3, :3]
        warped = cv2.warpPerspective(rgb_contrib, H3x3, (canvas_W, canvas_H),
                                     flags=cv2.INTER_CUBIC,
                                     borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        return warped.astype(np.float32)
    except ImportError:
        # Fallback: return zeros with correct shape
        canvas_H, canvas_W = canvas_hw
        return np.zeros((canvas_H, canvas_W, 3), dtype=np.float32)


# ── Main pipeline ─────────────────────────────────────────────────────────────

def process_lri(lri_path, out_path=None):
    """
    LRI → 52MP merged image.
    Returns numpy array (H, W, 3) float32 or saves TIFF if out_path given.
    """
    print(f"Parsing {lri_path} ...")
    meta = parse_lri(lri_path)
    tier = meta['tier']
    canvas_hw = CANVAS[tier]
    cam_ids   = FIRING_RULES[tier]
    anchor_id = ANCHOR_CAM[tier]
    awb       = meta['awb_gains']

    print(f"  tier={tier}, canvas={canvas_hw}, cameras={cam_ids}, anchor={anchor_id}")

    anchor_cal = meta['factory_cals'].get(anchor_id, {})
    K_anchor   = anchor_cal.get('K')
    R_anchor   = anchor_cal.get('R')  # world→camera; None → treated as eye(3)

    canvas = np.zeros((*canvas_hw, 3), dtype=np.float32)
    weight = np.zeros(canvas_hw, dtype=np.float32)

    # Load anchor raw first to get sensor dimensions for K scaling.
    # K from LRI is in sensor pixel coords; homography output must be in canvas coords.
    print(f"  Processing cam {anchor_id} (anchor) ...")
    anchor_raw, anchor_bp = load_raw_bayer(lri_path, anchor_id)
    anchor_H, anchor_W = anchor_raw.shape[:2]
    anchor_rgb = isp_camera(anchor_raw, anchor_id, awb, anchor_cal, anchor_bp,
                            neutral_xy=meta.get('neutral_xy'))
    try:
        import cv2
        resized = cv2.resize(anchor_rgb, (canvas_hw[1], canvas_hw[0]),
                             interpolation=cv2.INTER_LANCZOS4)
    except ImportError:
        resized = anchor_rgb
    canvas += resized
    weight += 1.0

    # Scale K_anchor from sensor space (e.g. 4160×3120) to canvas space (e.g. 10432×7824).
    # Without this, H maps contributors into only the upper-left ~16% of the canvas.
    if K_anchor is not None:
        sx = canvas_hw[1] / anchor_W
        sy = canvas_hw[0] / anchor_H
        S  = np.array([[sx, 0, 0], [0, sy, 0], [0, 0, 1]], dtype=np.float64)
        K_anchor_canvas = S @ K_anchor
        print(f"  K scaling: sensor {anchor_W}×{anchor_H} → canvas {canvas_hw[1]}×{canvas_hw[0]}"
              f" (sx={sx:.3f}, sy={sy:.3f})")
    else:
        K_anchor_canvas = None

    for cam_id in cam_ids:
        if cam_id == anchor_id:
            continue  # already processed above

        print(f"  Processing cam {cam_id} ...")
        raw, bayer_phase = load_raw_bayer(lri_path, cam_id)
        cal = meta['factory_cals'].get(cam_id, {})

        rgb = isp_camera(raw, cam_id, awb, cal, bayer_phase, neutral_xy=meta.get('neutral_xy'))

        R = cal.get('R')
        t = cal.get('t')
        K = cal.get('K')
        if K_anchor_canvas is not None and R is not None and t is not None and K is not None:
            H = build_homography(K_anchor_canvas, R, t, K, R_anchor=R_anchor)
            warped = reproject(rgb, H, canvas_hw)
            mask = (warped.sum(axis=2) > 0).astype(np.float32)
            canvas += warped
            weight += mask
        else:
            print(f"    WARNING: cam {cam_id} missing R/t/K or K_anchor, skipping reproject")

    # Normalize
    w = weight[:, :, None].clip(1)
    merged = (canvas / w).clip(0, 1)

    if out_path:
        _save_tiff(merged, out_path)
        print(f"Saved {out_path}")

    return merged


def _save_tiff(rgb_f32, path):
    """Save float32 RGB as 16-bit TIFF."""
    try:
        import tifffile
        u16 = (rgb_f32 * 65535).clip(0, 65535).astype(np.uint16)
        tifffile.imwrite(path, u16, photometric='rgb')
    except ImportError:
        try:
            import cv2
            u16 = (rgb_f32 * 65535).clip(0, 65535).astype(np.uint16)
            cv2.imwrite(str(path), cv2.cvtColor(u16, cv2.COLOR_RGB2BGR))
        except ImportError:
            print("WARNING: no tifffile or cv2 — output not saved")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: phoenix_pipeline.py <input.lri> [output.tiff]")
        sys.exit(1)
    lri = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else lri.replace('.lri', '_phoenix.tiff')
    process_lri(lri, out)
