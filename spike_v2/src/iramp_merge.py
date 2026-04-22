"""
iramp_merge.py — Cross-camera N→1 merge per TRUTH §2.1 (v2.1.4).

Runtime signature per TRUTH M2 (still correct):
  (dst, src1, src2, srcs[5], warps[5], scale, roi)
  = 2 anchor wrappers (same cam) + 5 contributors + 5 × 80 B WarpField structs
    28mm: srcs = B1..B5 (cam_ids 5..9), anchor = A1 (M13 corrected v2.1.4)
    70mm: srcs = C1..C5 (cam_ids 10..14), anchor = B4
  NOTE v2.1.4: "composite" in M13 means "pyramid-tier wrapper" not
  "blended-from-5-cams" — see composite_anchor.py docstring.

**v2.1.4 NEW INPUT: WarpField byte layout decoded (§2.1 M2.1).**
Each of 5 WarpFields (80 B each) contains:
  +0x00..+0x0F : vec4f homography col 0 (coef of dst_x × sample)
  +0x10..+0x1F : vec4f homography col 1 (coef of dst_y × sample)
  +0x20..+0x2F : vec4f homography col 2 (coef of sample)
  +0x30..+0x3F : vec4f homography col 3 (constant; slot-3 = +1.0 homogeneous)
  +0x40        : ptr to SHARED aux-image (one for all 5 warps per render)
                 aux.stride@+0x18, aux.data@+0x20
  +0x48        : float X sampling scale (dst_x → aux-sampling coord)
  +0x4C        : float Y sampling scale (dst_y → aux-sampling coord)

Per-pixel warp math:
  sample = aux.data[ int(dst_y × sy) × aux.stride + int(dst_x × sx) ]
  out    = sample·col2 + col3 + (dst_x·sample)·col0 + (dst_y·sample)·col1
  (src_u, src_v) = round(out[0..1] / out[2])   # perspective divide

**Spike blocker: aux-image construction is NOT decoded.** aux is a canvas-space
depth/disparity buffer at stride=4160 populated upstream (likely by a
depth-cache or ref-image stage). Phoenix must produce an equivalent buffer
from LRI depth hints or camera-geometry before this merge can run cleanly.
Pending that, the spike keeps contributor merge OFF and returns anchor-only.

Kept TRUTH references:
  - M6: 16-entry LUT per-pixel separable — applies to IRAMP's own filter, NOT
        to libcp+0x2b3410 (see v2.1.4 M14.1 supersession).
  - M7: CDF 9/7 lifting super-res constants (bit-exact JPEG2000).
  - M14: per-contributor pre-norm `out = sqrt(max(0, in × FOV_ratio))`; FOV_ratio
         written at closure+0x10 by libcp+0xe67c0.
  - C3/C18: per-tile CCM in chromaticity space `M @ (R/G, 1, B/G)`; kernel
            at libcp+0x350c56 appears to row-normalize M (v2.1.3 spike finding
            →  OPEN-CCM-NORMALIZATION).

For the spike's visual smoke test the critical things are:
  (a) don't invert R/B channels                  — fixed via rownorm CCM in utils
  (b) blend contributors w/o phantom edges       — REQUIRES WarpField + aux-image
  (c) apply CCM in the right space               — rownorm workaround in place
"""

import numpy as np

from utils import apply_ccm_chromaticity, finite


# TRUTH §2.1 M7: JPEG2000 CDF 9/7 lifting constants (bit-exact public values)
CDF97_ALPHA = np.float32(-1.5861343)
CDF97_BETA  = np.float32(-0.05298011)
CDF97_GAMMA = np.float32( 0.8829110)
CDF97_DELTA = np.float32( 0.4435068)
CDF97_K     = np.float32( 1.1496044)


# TRUTH C17 FOV ratios (typical — OPEN-PER-CAM-FOV for byte-exact values)
FOV_RATIO_28MM_B = 0.50    # 28mm B-cams relative to A anchor
FOV_RATIO_70MM_C = 0.80    # mid-range of 70mm C-cams (0.75-0.84)


def per_contributor_prenorm(rgb: np.ndarray, fov_ratio: float) -> np.ndarray:
    """TRUTH §2.1 M14: out = sqrt(max(0, in × FOV_ratio)) per-channel."""
    return np.sqrt(np.maximum(rgb * np.float32(fov_ratio), 0.0)).astype(np.float32)


def merge_iramp(anchor_rgb: np.ndarray,
                contributor_rgbs,
                contributor_ccms,
                anchor_ccm,
                fov_ratio: float,
                include_contributors: bool = False) -> np.ndarray:
    """
    Simplified IRAMP merge: anchor composite + photometric-normed contributors
    post-CCM (applied in chromaticity space).

    IMPORTANT (spike v2.0 known limit):
    Contributor registration via WarpField (TRUTH M2 — 80B struct, per-cam
    projection into anchor coordinate frame) is NOT decoded in this spike.
    Each contributor camera covers a DIFFERENT FOV slice of the scene (e.g.
    B1 covers left-third, B3 covers center-third, etc.). Merging contributors
    without warp registration produces 5-stripe phantom overlays in the
    output. For the initial visual smoke test we default to anchor-only.

    When `include_contributors=True`, contributors are averaged-in using FOV
    ratio as a scalar weight. This is incorrect (missing WarpField) but is
    kept as a toggle for future validation once WarpField decode completes.

    Args:
        anchor_rgb:        (H, W, 3) composite anchor from composite_anchor.py
        contributor_rgbs:  list of (H_c, W_c, 3) per-contributor outputs
        contributor_ccms:  list of 3x3 CCM per contributor (same count as above)
        anchor_ccm:        3x3 CCM for anchor (typically A1's CCM)
        fov_ratio:         contributor FOV ratio vs anchor (TRUTH C17)

    Returns:
        merged: (H_out, W_out, 3) float32 — in the 4160×3120 per-cam space.
    """
    H, W = anchor_rgb.shape[:2]

    # Apply anchor CCM (per TRUTH C18: single consolidated M per pass)
    anchor_ccm_applied = (apply_ccm_chromaticity(anchor_rgb, anchor_ccm)
                          if anchor_ccm is not None else anchor_rgb)

    if not include_contributors:
        return finite(anchor_ccm_applied).astype(np.float32)

    merged_acc = anchor_ccm_applied.copy()
    weight_acc = np.float32(1.0)
    for c_rgb, c_ccm in zip(contributor_rgbs, contributor_ccms):
        if c_rgb is None:
            continue
        if c_rgb.shape[:2] != (H, W):
            continue
        normed = per_contributor_prenorm(c_rgb, fov_ratio)
        normed = normed * normed
        M = c_ccm if c_ccm is not None else anchor_ccm
        c_applied = (apply_ccm_chromaticity(normed, M)
                     if M is not None else normed)
        merged_acc = merged_acc + c_applied
        weight_acc += np.float32(fov_ratio)

    merged = merged_acc / weight_acc
    return finite(merged).astype(np.float32)
