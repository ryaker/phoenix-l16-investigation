# Runtime Evidence: ColorFusion source-plane registration is an INTEGER active-window crop (no warp)

## Scope

Resolves the long-standing "source-plane per-camera warp" blocker. The
ColorFusion SOURCE half-res planes (`owner+0x100`, packed
`source_vec4_f16_0k`) are built by the SAME per-camera route the (already
bit-exact) REFERENCE plane uses, differing only by:

1. the source camera's own calibration (black / vignette / scene-neutral gain), and
2. an INTEGER active-window crop = `anchor_rect ∩ source_rect`.

There is **no projective H, no radial LUT, no sub-pixel resample** in the
ColorFusion source-plane construction. The `ImageWarpClamped<filter=2>` worker
`0x3ed2e0` belongs to the depth `PipelineCache::processLevel1` src2 path, NOT to
`ColorFusionBayer::initialize`; the ColorFusion reference plane is already
bit-exact WITHOUT it, which is the proof it is not on this path.

## Static custody (already attested)

`tools/verifiers/verify_colorfusion_source_plane_static.py` pins the build chain
inside `ColorFusionBayer::initialize` (0x1ab2d0). Per source (loop
0x1ab764..0x1abb58) and for the reference:

```
0x1ac010  construct native plane  (RAW10 -> hotpixel -> RestoreHighlightsBayer(c,black,white) -> f32(u16)-black)
0x1ad390  normalize+compact window  (out[i] = window[i] * scale ; tight-strided copy, NO interpolation)
0x19bd20  PackBayerImageProtoType<vec4x16f,float>  (half-res, lane [TR,TL,BL,BR], f16 truncation)
          -> stored at owner+0x100[k]
```

Reference uses the same pair at 0x1AB4B7/0x1AB4C7; each source at 0x1ABA80/0x1ABA8F.

## Runtime operands (u1_28, A1 target key 0, sources [4,2,3])

Probe `tools/lldb_probes/colorfusion_source_planes/operand_probe.py`
(+`run_operand.sh`), breakpoints 0x1ab813 (rect intersection), 0x1aba80
(0x1ad390 in), 0x1aba8f (0x19bd20 in). Captured:

| src | cam | anchor_rect (TL..BR) | source_rect | crop = ∩ (x0,y0,w,h) | pack in |
|----:|----:|----------------------|-------------|----------------------|---------|
| 0 | 4 | (1,1)..(4159,3119) | (0,0)..(4160,3120) | (1,1, 4158,3118) | 4158×3118 |
| 1 | 2 | (0,0)..(4160,3120) | (0,0)..(4160,3120) | (0,0, 4160,3120) | 4160×3120 |
| 2 | 3 | (0,0)..(4160,3120) | (0,0)..(4160,3120) | (0,0, 4160,3120) | 4160×3120 |

The crop is a pure integer sub-rectangle of the source's OWN native
(4160×3120) plane. Even-extent: the odd inset (1,1)/4158×3118 halves to the
captured 2079×1559 `source_vec4_f16_00` (25,929,288 B); (0,0)/4160×3120 halves
to 2080×1560 (25,958,400 B) — matches every captured descriptor across 2u/4f.

`0x1ad390` output descriptor is the window pixels multiplied by `scale`
(≈1/(white−black), per-camera ~980.6–981) written to a tight buffer; the input
window has stride 4160 and the output stride == width, i.e. a normalize+compact
COPY. No fractional addressing / interpolation weights are computed — confirming
crop, not warp.

NOTE (RESOLVED 2026-08-12): the per-camera `scale` for cam4 that read 981.00 in
one run and 979.83 in a repeat is NOT instability -- it is unsolved-black-42.0
(981 = 1/(1023-42)) vs over-refined-black-43.17 (979.83). The runtime refines
black (`solveBlackLevel`) only for the SUBSET of source modules its keyed cache
helper `0x1bdc80` (internal solve `0x1bdd86`, gate `0x1bdd19`; `0xe78e0` count
always 1, lazy builder `0x1be270` zero-hit) sees FRESH at ColorFusion time -- a
module is refined iff ColorFusion is the first stage to request its key; the
pre-CF flow/reference/depth passes pre-empt the rest, which keep 42.0. cam4 in
u1_28 is one such never-refined source -> black 42.0 -> scale 981. `solve.json`
(runs/normalization_black_level/u1_28) confirms only cam2/cam3 are solved (to
42.39/42.36), not cam4. This membership is emergent runtime request-order state,
NOT an LRI constant; Phoenix consumes it as a captured input
(`colorFusionSourcePlaneRegistered(refined_black=...)`, provenance in
engine/merge/colorfusion_black_membership.md). With cam4 black=42.0 the pre-pack
plane matches `bd20_input_src0` at the 1-ULP floor (maxULP 3).

NOTE (open): POST-PACK bit-exactness of the SOURCE planes (source_vec4_f16) is
NOT yet reached. Two non-black residuals remain: (1) highlight-restore CLIPPED-
kernel bright-region scatter (u1_28 cam2 0.14% / cam3 0.075%; also the u2_35
anchor 16396) -- needs the CFA-phase clipped kernels 0x30b9f0/0x30dcc0/0x30ff60/
0x3121f0 ported; (2) the cropped ODD-Bayer-phase source cam4 (red_override (0,1))
-- un-packing source_vec4_00 to native shows the even-column channel matches
(~1.05x) but the odd-column channel is ~1.33x brighter than the monochrome
bd20/packer-input, a phase-dependent per-channel step present in the final plane
but absent from bd20. cam2/cam3 (red_override (1,0), crop (0,0)) do not show it.
So the earlier "pack = plain 2x2 truncation of the cropped native plane, proven
against source_vec4_00" holds for the even-phase uncropped sources but NOT for
the odd-phase cropped cam4 -- the cropped-source registration/pack for an odd
anchor offset needs the phase-aware per-channel step identified.

## Consequence / port

Source plane[k] = `colorFusionAnchorPlane` pipeline (route + HighlightRestore +
normalize + per-pixel vignette + f16-truncation half-res pack, lane [TR,TL,BL,BR])
run for camera k with k's own calib_index / solved black / scene-neutral gain c_k
(c_k from the SHARED neutral temp/tint + camera k's ColorCalibration), then
cropped to the integer anchor∩source window before the half-res pack. All pieces
already exist and are bit-exact for the reference; this is a wiring + per-camera
parameter task, validated against runs/colorfusion_source_planes/*/source_vec4_f16_00.bin.
