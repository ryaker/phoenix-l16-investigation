# Runtime Evidence: Unit-2 70mm B4 CreateStereoImage Stage Vector

**Date:** 2026-08-10
**Route:** deterministic boundary comparison follow-up (audit Next-Investigation #3)
**Input:** `/Volumes/Base Photos/Light/2018-02-08/L16_00010.lri` (full LRI, no staging)
**Camera:** key 8 (B4, u2_70 tier anchor)
**Probe:** `tools/lldb_probes/create_stereo_color_public_reconstruction/stage_vector_probe.py`
with `camera_key=8`, `terminate_on_complete=True` (single-camera staging is NOT
usable here: a B4-only staged LRI fails `setInputDataStream: map::at: key not
found`; capture on the full LRI with closure key-filtering instead).
**Run:** `runs/create_stereo_color_public_reconstruction/unit2_70mm_b4_full/`

## Result

Complete: 7 ordered stage calls, same active set and order as the wide-body
bundle (`bundle_static_runtime_create_stereo_color_normalization_vignetting_
two_body.md`):

| Index | Stage | u2_70 B4 payload observation |
|---:|---|---|
| 1 | hot-pixel | captured |
| 3 | Bayer normalization | captured |
| 5 | cross-talk | LIVE; Bayer payload transformed (payload also shrinks a border: 1097728 -> 1089536 bytes) |
| 6 | demosaic | LIVE; produces the full-res RGBA image payload |
| 11 | sharpen | FULL-PLANE byte-exact pass-through: stage-11 input slot_70 sha256 `cd22dd7f...` == stage-12 input slot_70 |
| 12 | lens shading | LIVE; image payload changes (`cd22dd7f...` -> `75cc24a1...`) |
| 15 | tone map / conditional materialization | input captured (`75cc24a1...`); OUTPUT NOT captured -- next open boundary |

Bayer payload custody after demosaic is inert: slot_d0 sha256 `aa375c8d...`
identical at stages 6, 11, 12, 15.

## Bearing on the stage-A plane divergence

This extends the wide-body stage-order proof to the u2_70 tele route and
narrows the unmeasured chain between proven stages and the captured stereo
`Images[0..4]` (2080x1560 RGBA8) to:

1. stage-15 output (tone map / conditional materialization),
2. RGBA -> YUV conversion for source planes, and
3. the full-res -> 2080x1560 half-res reduction.

Phoenix implication (code-vs-spec): the depth tool builds ALL five planes with
a raw 2x2 Bayer collapse (`collapse2FromRaw` / float-YUV path) and never calls
the engine's PROVEN bit-exact cross-talk (`engine/depth/cross_talk.cpp`) or
demosaic stages, although both are live on this route. The sharpen no-op means
no sharpen port is needed. A licensed byte-exact source-plane port requires
closing boundaries 1-3 above by measurement before wiring.

## Not claimed

Stage-15 output semantics; YUV/half-res reduction custody; other cameras of
this render; formula closure for cross-talk on THIS route (the existing
crosstalk bundles prove the formula on two bodies at four zooms; liveness here
is consistent with them).

## Addendum (same date): stage-15 OUTPUT captured

`final_slot_probe.py` binds the unbound stage-return site `0x33f3eb` and
captured the post-stage-15 payload
(`runs/create_stereo_color_public_reconstruction/unit2_70mm_b4_stage15/`):

- After stage 15 the payload's `0x70` (RGBA image) and `0xd0` (Bayer) slots
  are GONE; only the u16 storage slot `0x100` remains (274,432 values -- the
  same storage count the wide normalization bundle proved).
- Stage 15 REWRITES that u16 storage: before `[51,1023]` mean 286.4 (raw
  scale); after `[46,647]` mean 86.0; only 1,270/274,432 values unchanged;
  median after/before ratio 0.3745 with max ratio ~0.63 -- a NONLINEAR global
  tone transform, not a pure scale.
- This is the missing global photometric transform between the proven
  lens-shaded RGBA and the stereo `Images[]` bytes implicated by the stage-A
  boundary comparison. Formula closure (static worker analysis of the
  `0x34a610` stage + operand capture) is the next investigation item; only
  after closure is a Phoenix port licensed.
