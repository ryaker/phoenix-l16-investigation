"""
composite_anchor.py — Anchor IG pair wrapping per TRUTH v2.1.4 M13 (corrected).

**v2.1.4 CORRECTION (2026-04-21 runtime LLDB probe):**

The prior v2.1 M14.1 claim that `libcp+0x2b3410` is a "4-way SIMD weighted blend
that fuses A1..A5 RIC L0 buffers into src1/src2" was DISCONFIRMED. Runtime
closure-string probe captured Halide's self-reported function name
`"color_denoise_multiplier"` at that VA — the kernel is a cubic B-spline
separable 4-tap resampler, not a multi-camera blender. TRUTH v2.1.4 supersedes
the composite-anchor-combiner story.

**Corrected architecture:**

M13 still stands structurally: IRAMP body takes `src1, src2` as its first two
ImageGenerator args at `libcp+0x365960`. Both wrap the SAME anchor camera's
pyramid (A1 at 28/35mm tier, B4 at 70/150mm tier) via two sibling vtables
(`0x65f668` and `0x65f6e8`) that control different pyramid-tier lookup paths.
"Composite" in M13 means "pyramid-tier wrapper", NOT "blended from 5 cameras".

**Phoenix/spike posture:**

- No explicit A1..A5 pre-fusion combiner has been located. Session 1's
  watchpoint evidence (dropped cams A2..A5 buffers DO get read) is consistent
  with downstream pyramid resampling consumption, not a dedicated blender.
- For the visual-gate spike we return src1 = src2 = the anchor camera's RGB
  (post-ISP) directly. No blend, no mean, no averaging.
- Phoenix must still run ISP for A2..A5 — their pyramids may be read by
  `color_denoise_multiplier` or other pyramid-level ops further downstream.

**OPEN-COMPOSITE-COMBINER (new in TRUTH v2.1.4 §8.4):** whether a dedicated
multi-cam combiner exists (unlocated kernel, or a stage described in scratch
files that hasn't been VA-pinned) is the current open item. Spike assumes NO
explicit combiner pending re-audit.
"""

import numpy as np
from utils import finite


def build_anchor_views(anchor_rgb: np.ndarray):
    """
    Return (src1, src2) as sibling pyramid-tier views of the anchor camera's
    post-ISP RGB. For the spike these are identical; in libcp they would be
    two IG wrappers with different vtable dispatch for pyramid-level lookup.

    Args:
        anchor_rgb: (H, W, 3) float32 — anchor camera post-ISP output.
                    At 28/35mm = A1 (cam_id 0).
                    At 70/150mm = B4 (cam_id 8).

    Returns:
        (src1, src2) — both = anchor_rgb (copy for src2 to allow independent
        downstream mutation without aliasing).
    """
    if anchor_rgb is None:
        raise ValueError("anchor_rgb required")
    src1 = finite(anchor_rgb).astype(np.float32)
    src2 = src1.copy()
    return src1, src2


def build_composite_anchor(anchor_rgbs):
    """
    SUPERSEDED (v2.1.4): the "composite from A1..A5 average" story was wrong.

    Kept as a named entry point for any existing callers; now delegates to
    `build_anchor_views(anchor_rgbs[0])` — the first entry (= A1 at 28mm,
    B4 at 70mm) is the anchor; the rest (A2..A5 / B1..B3/B5) are dropped
    from the src1/src2 path entirely.

    If caller needs a combined aggregate for diagnostic purposes, use
    np.mean(np.stack(anchor_rgbs), axis=0) directly. But do NOT feed it into
    IRAMP — that path does not exist in libcp.
    """
    if not anchor_rgbs:
        raise ValueError("no anchor cams")
    return build_anchor_views(anchor_rgbs[0])
