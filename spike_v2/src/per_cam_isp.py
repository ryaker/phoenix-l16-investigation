"""
per_cam_isp.py — Per-camera ISP stages per TRUTH §2.2.

Pipeline (TRUTH §2.2 I2):
  raw MIPI10 uint16 (H, W)
    → LensUndistortCRA radial warp (I6)         [we approximate as identity]
    → BLC (K1): (raw - 42) / 981                [TRUTH K1 linear formula]
    → AWB (C1): multiply by 1/stored_gain       [reciprocal per-channel]
    → Demosaic (I3): Hamilton-Adams 5x5 family  [algorithm parity, not byte]
    → Per-cam CCM setup                         [stored; applied INSIDE IRAMP]
    → Vignetting (I5): multiply by grid × 0.7373 scale

Input:  uint16 (H, W) Bayer mosaic, CameraRecord, Calibration
Output: float32 (H, W, 3) RGB + CCM matrix for IRAMP stage

Clean-room: BLC constants 42/981 are documented TRUTH values, AWB direction is
documented, Hamilton-Adams is public algorithm, CCM lerp is mired-space
MatLerpClamped per TRUTH C4, vignetting scale 0.7373 is TRUTH I5.
"""

import numpy as np
from scipy.ndimage import zoom as ndi_zoom

from utils import (
    demosaic_hamilton_adams, BAYER_LAYOUTS, mat_lerp_mired,
    finite,
)


# TRUTH K1 black level and white level
BL = np.float32(42.0)
WL = np.float32(1023.0)
BLC_SCALE = np.float32(1.0 / (WL - BL))  # = 1/981

# TRUTH I5 vignetting scale (closure scale uniform across cams)
VIG_SCALE = np.float32(0.7373)

# TRUTH C9 default CCT when protobuf `neutral_temp` absent
DEFAULT_CCT = 4300.0

# CCT endpoints per calibration illuminant (approximate, Wyszecki-Stiles)
#   TungstenA ~ 2856 K
#   D65       ~ 6504 K
#   F11       ~ 4000 K
CCT_TungstenA = 2856.0
CCT_D65 = 6504.0
CCT_F11 = 4000.0


def blc(raw_u16: np.ndarray) -> np.ndarray:
    """Black-level + white-level linearization per TRUTH K1.

    out = (raw - 42) / 981 → linearly scaled to ~[0, 1] with clamp at 0.
    """
    out = (raw_u16.astype(np.float32) - BL) * BLC_SCALE
    np.clip(out, 0.0, None, out=out)
    return out


def awb_bayer(mosaic_f32: np.ndarray, bayer_pattern: int,
              R_gain: float, B_gain: float) -> np.ndarray:
    """
    TRUTH §2.3 C1: AWB = multiply by RECIPROCAL of stored gain, applied per
    Bayer cell BEFORE demosaic. Combined with row-normalized CCM downstream
    this produces a near-neutral output.

    The stored Block 8 gains for 28mm L16_00007 are (1.616, 1.853) with
    G1=G2=1.0. We multiply R cells by 1/1.616 = 0.619 and B cells by
    1/1.853 = 0.540, leaving G cells unchanged.
    """
    out = mosaic_f32.copy()
    tl, tr, bl, br = BAYER_LAYOUTS[bayer_pattern & 3]

    invR = np.float32(1.0 / R_gain)
    invB = np.float32(1.0 / B_gain)

    def mul_for(ch):
        if ch == 'R':
            return invR
        if ch == 'B':
            return invB
        return np.float32(1.0)

    out[0::2, 0::2] *= mul_for(tl)
    out[0::2, 1::2] *= mul_for(tr)
    out[1::2, 0::2] *= mul_for(bl)
    out[1::2, 1::2] *= mul_for(br)
    return out


def lens_undistort_approx(bayer_linear: np.ndarray) -> np.ndarray:
    """TRUTH §2.2 I6: LensUndistortCRA is a pure radial 3x3 homography +
    4096-LUT warp. We don't have the per-cam homography coefficients decoded
    in this spike — approximate as identity (no warp).

    If we don't warp, the dominant visual artifact will be slight residual
    radial distortion. For 28mm-tier where all contributors are A/B cams
    with similar optical axes, ghosting should still be manageable.
    """
    return bayer_linear


def demosaic(bayer_linear: np.ndarray, bayer_pattern: int) -> np.ndarray:
    """Hamilton-Adams demosaic — algorithm parity per TRUTH §2.2 I3."""
    return demosaic_hamilton_adams(bayer_linear, bayer_pattern)


def upsample_vignetting_grid(grid: np.ndarray, H: int, W: int) -> np.ndarray:
    """Bilinearly upsample (13, 17) to (H, W)."""
    # scipy.ndimage.zoom with order=1
    gh, gw = grid.shape
    zoom_y = H / gh
    zoom_x = W / gw
    return ndi_zoom(grid, (zoom_y, zoom_x), order=1, mode='nearest').astype(np.float32)


def vignetting_apply(rgb: np.ndarray, grid: np.ndarray) -> np.ndarray:
    """TRUTH §2.2 I5: multiply pixel × interpolated grid × uniform scale 0.7373.

    Vignetting grid max > 1 at corners (per TRUTH K2 corners 1.4–3.9).
    Multiplying increases corner brightness to compensate.
    """
    H, W = rgb.shape[:2]
    g_full = upsample_vignetting_grid(grid, H, W)
    g_scaled = (g_full * VIG_SCALE)[..., None]
    return rgb * g_scaled


def select_ccm_for_cct(ccm_by_illum: dict, cct: float) -> np.ndarray:
    """Mired-space lerp between calibration CCMs (TRUTH §2.3 C4).

    Three illuminants available: TungstenA, D65, F11.
    If cct <= D65: lerp between F11 and D65 (or TungstenA and F11 if very low).
    Otherwise: lerp between D65 and extrapolation cap (clamped).

    TRUTH C4: no extrapolation — clamp at endpoints.
    """
    M_T = ccm_by_illum.get('TungstenA')
    M_D = ccm_by_illum.get('D65')
    M_F = ccm_by_illum.get('F11')

    # Identify two closest illuminants and lerp between them in mired space.
    # Mireds: 1e6 / K.  Tungsten=350, F11=250, D65=154.
    if cct <= CCT_TungstenA:
        return M_T if M_T is not None else M_D
    if cct >= CCT_D65:
        return M_D if M_D is not None else M_F
    if cct <= CCT_F11:
        # between TungstenA and F11
        if M_T is None or M_F is None:
            return M_D
        return mat_lerp_mired(M_T, CCT_TungstenA, M_F, CCT_F11, cct)
    # between F11 and D65
    if M_F is None or M_D is None:
        return M_D if M_D is not None else (M_T if M_T is not None else np.eye(3, dtype=np.float32))
    return mat_lerp_mired(M_F, CCT_F11, M_D, CCT_D65, cct)


def run_per_cam_isp(raw_u16: np.ndarray, cam_record, cal, cct: float = DEFAULT_CCT):
    """
    Run the full per-camera ISP for one camera.

    Returns:
      rgb_linear: (H, W, 3) float32 RGB, BLC+AWB+demosaiced+vignetting-corrected,
                  PRE-CCM (CCM applies INSIDE IRAMP per TRUTH §2.3 C3).
      M_ccm:      (3, 3) float32 — per-cam CCM selected at this CCT; for cams
                  without CCM calibration (A2, C6), we return None.
    """
    cid = cam_record.cam_id
    # Stage 1: LensUndistortCRA (approximate identity for this spike)
    raw_warped = lens_undistort_approx(raw_u16)

    # Stage 2: BLC
    linear = blc(raw_warped)

    # Stage 3: AWB (reciprocal multiply per Bayer cell)
    R_gain, B_gain = cal.awb_gains.get(cid, (1.6, 1.8))
    linear = awb_bayer(linear, cam_record.bayer_pattern, R_gain, B_gain)

    # Stage 4: Demosaic
    rgb = demosaic(linear, cam_record.bayer_pattern)

    # Stage 5: Vignetting
    if cid in cal.vignetting:
        rgb = vignetting_apply(rgb, cal.vignetting[cid])
    # else: no vignetting data (rare) — leave unchanged

    # Stage 6: CCM lookup (applied downstream inside IRAMP per TRUTH C3)
    ccm_illums = cal.ccm_by_cam.get(cid)
    M_ccm = select_ccm_for_cct(ccm_illums, cct) if ccm_illums else None

    rgb = finite(rgb)
    return rgb, M_ccm
