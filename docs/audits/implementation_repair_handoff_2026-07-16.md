# Phoenix Implementation Repair Handoff

**Truth snapshot:** `docs/TRUTH.md` v3.0.331  
**Authority:** `docs/canonical/CLAIM_LEDGER.md`  
**External implementation reviewed:** `/Users/ryaker/L16_Phoenix` as present
on 2026-07-16

## Purpose

This is an implementation-reconciliation audit, not a new pipeline spec and
not a source of new truth. It maps the failed Phoenix build's documented
divergences to claims and formulas already admitted after the build's working
spec became stale.

When this audit and the claim ledger differ, the ledger wins.

## 2026-07-17 Stereo Correction Addendum

The five depth questions raised after the original audit are now admitted.
They remove the remaining fitted stereo behavior from the parity path:

| Builder substitute or uncertainty | Admitted replacement | Evidence |
|---|---|---|
| Per-level `H_L = D_L H D_L^-1` projection scaling | Delete it. Every `Image` and projection record remains in the fixed `2080 x 1560` domain at all six levels. Lift a level coordinate with `full = min(step * level_coord + floor(step/2), extent-1)`, where `step = StereoLayer+0x1c = 32,16,8,4,2,1`, then apply the unchanged full-domain `H`. Live record scales are `(1,1)` at every level. | TRUTH v3.0.328; `bundle_static_runtime_index5_perlevel_projection_scale_two_body_four_zoom.md` |
| Radius-2 prior-depth min/max fitted around `0x298ff0`, with Skip mask ignored | Replace it with the exact clamped `4 x 4` footprint using offsets `{-1,0,+1,+2}` on both axes. Include only prior pixels whose Skip-mask byte is nonzero. Emit empty `(low,high)=(65535,0)` when none qualify; the later range builder applies its separate one-hypothesis padding. | TRUTH v3.0.329; `bundle_static_runtime_index5_range_pool_skip_policy.md` |
| Per-pixel band-min pedestal before SGM | Delete it. G-42's raw four-source `u16` sum is converted in place as `trunc_u16(f32(raw) * f32((1/27)/source_count))`; profile 3 has four projected sources, so the factor is `0.0092592593282461166f`. G-43 reads those exact normalized values. Its subtraction of the prior path minimum is internal to the SGM recurrence, not unary normalization. | TRUTH v3.0.330; `bundle_static_runtime_index5_sgm_cost_input_normalization.md` |
| Guided or nearest-neighbor filling of pattern-2 Skip-mask holes | Delete it. Mask `0` computes the normalized G-42 unary vector; a nonzero mask writes an all-zero unary vector. Both pixels then run all eight SGM paths, receive ordinary Cost-volume records, and use the same first-minimum argmin. The later guided 2x stage consumes an already-complete depth map. | TRUTH v3.0.331; `bundle_static_runtime_index5_skip_consumption_two_body.md` |
| Approximate `d-1/d/d+1` P1 lane assignment | Use the admitted order: the current `d` lane is unpenalized, `d-1` is the farther/lower-inverse-depth neighbor plus `P1`, and `d+1` is the nearer/higher-inverse-depth neighbor plus `P1`. Hypothesis lanes increase from far to near. | `bundle_static_runtime_index5_disparity_lane_convention_four_zoom.md` |

The implementation should remove all five substitutes together before using a
depth-map comparison as a parity diagnostic. In particular, a pedestal can
hide an incorrect coarse-level projection or range footprint, while hole fill
can hide incorrect Skip-mask semantics. The admitted chain is now complete
from level-coordinate lift through unary normalization, eight-path SGM, and
per-pixel argmin.

Pinned external-source SHA-256 values for the concrete line references:

```text
fcc9e114e504c978d2984f5095b050b398c3cc5d53ac592929ced8d2b95ce799  phoenix_arm/tools/phoenix_depth.cpp
689cb9f17fc39956e32ec329c58dd73df85985ac45c450fb8e311723a0ef0c2d  phoenix_arm/tools/phoenix_fuse.cpp
4507a875e2ce0fd4f0c3f572b8d060c9b6bdf31d2895bcde7398b76afb8ab3ff  phoenix_arm/engine/depth/cost_sgm.cpp
45d8a2e4cf10b4b25e6f56af0303e1f325de734ba30ac04e30f4fbdb185dc574  phoenix_arm/engine/merge/iramp.cpp
f467efe25acad9fdc0f38ec769bdb9bc3c3bc46bb44cfe12f7720e8e0f30dc81  phoenix_arm/engine/edit/phoenix_project.cpp
```

Recheck that exact external snapshot with:

```bash
python3 tools/validation/verify_implementation_repair_snapshot.py
```

## Executive Finding

The failed build does not demonstrate that the canonical profile-3 mechanism
is still broadly unknown. It implements several old gaps with clean-room
heuristics even though those gaps were later closed by installed-bundle and
runtime evidence. Those substitutions are large enough to dominate parity:

1. dense NCC flow and confidence gates replace Lumen's calibrated warp plus
   exact IRAMP candidate/score/reconstruction path;
2. scene-percentile depth confinement and post-hoc depth scaling replace the
   exact per-level Range-map construction;
3. a neutral-forcing von-Kries adjustment modifies the admitted CCM;
4. the CCM uses a proxy rg/bg alpha and an unconditional neutral-forcing
   row scale instead of the admitted fixed-point/Robertson path;
5. older four-path/default stereo and incomplete guidance/source preparation
   assumptions predate the G-40/G-42/G-43 and Guidance closures;
6. the build still labels exact profile-3 MonoFusion mode-0 algebra as an
   open Wiener stub even though the wavelet, noise, Wiener, overlap, blend,
   and confidence formulas are admitted.

The correct repair is to rebuild from the current admitted mechanism and use
the stage artifacts as oracles. Tuning the existing heuristics cannot validate
Lumen parity because their algorithms are different.

## Required Deletions

| Current implementation behavior | Verdict | Current authority |
|---|---|---|
| Dense coarse-to-fine block-NCC `flow_reg`, subpixel Jacobian gather, flow-confidence rejection, and contrast/detail transfer | Remove from the parity path. No admitted merge stage uses this algorithm. | `CLM-WARP-003`, `CLM-MERGE-003..006`; exact calibrated pair grids, five warp records, local SAD/WTA/refinement, score, reconstruction, and accumulation are closed. |
| `accept_min_ncc=0.75` or any NCC/absolute-difference anti-ghost gate | Remove. It replaces the now-closed local candidate policy. | [IRAMP candidate policy](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_iramp_candidate_policy_four_zoom.md): exhaustive sentinel/rejection census; no post-score threshold for non-sentinel `t`. |
| Coarse `p2/p92` (formerly p2/p89) or similar scene-percentile global depth window | Remove from the parity path. The build itself records that Lumen's `+0x238/+0x23c` are full-span. | `CLM-STEREO-001`; [G-40 hypothesis policy](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_index5_g40_hypothesis_policy.md). |
| NCC-derived whole-depth scale, including the `0.5` floor | Remove. Depth is selected directly from the reciprocal mm lookup; there is no post-hoc scale. | `CLM-WARP-003`; TRUTH v3.0.291 and the index-to-mm/GDepth custody bundles. |
| Neutral-forcing von-Kries row scaling after the admitted CCM | Remove. It mutates the exact selected matrix. | `CLM-CCM-002`; [public scene-chromaticity origin](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_ccm_chromaticity_public_origin_four_zoom.md). |
| Direct rg/bg-ratio average for CCM interpolation alpha | Replace with the admitted fixed-point scene-xy solve, Robertson round trip, and reciprocal-temperature interpolation. | `CLM-CCM-002`; [public scene-chromaticity origin](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_ccm_chromaticity_public_origin_four_zoom.md). |
| Optional fitted `lumenLook` | Keep explicitly non-parity/product-only. Current `phoenix_fuse` already defaults `no_look=true`; do not use `--look` as a parity comparison. | `CLM-OUTPUT-002`; [tagged linear-ProPhoto TIFF](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_independent_tagged_linear_prophoto_float_tiff.md); [slot-15 classification](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_pipeline_linear_prophoto_stage_four_zoom.md). |
| Per-level P2 scaling knobs or four-direction SGM substitution | Remove. | `CLM-STEREO-001`; [G-43 direction policy](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_index5_g43_direction_policy.md). |
| Fixed or captured per-level hypothesis-count tables | Remove. Counts are generated per input. | TRUTH v3.0.291; [G-40 hypothesis policy](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_index5_g40_hypothesis_policy.md). |

## Concrete Source Map

These locations refer to the external implementation snapshot named above.
They are repair targets, not Phoenix truth sources.

| Current source location | Observed divergence | Required repair / truth anchor |
|---|---|---|
| `phoenix_arm/tools/phoenix_depth.cpp:1315-1402` | G-42 defaults to per-patch-pixel reprojection (`g_contigPatch=false`), one universal weight vector, and saturating cross-source accumulation. | Use one projected source-patch center against the fixed anchor patch, retain the per-source weight table including the wide source-1 intensity-only row, and add each source cost modulo `u16`. See TRUTH v3.0.289 and the G-42 bundle. |
| `phoenix_arm/tools/phoenix_depth.cpp:1817-1835` | Banded SGM runs four cardinal paths by default; diagonals require `PHX_SGM8`. | Execute the exact eight signed paths unconditionally in the admitted route, with positive group before negative group. See TRUTH v3.0.290 / G-43. |
| `phoenix_arm/engine/depth/cost_sgm.cpp:113-183` | The reusable dense SGM helper is also cardinal-only and still labels G-43 a gap. | Bring the library helper into the same exact eight-path policy; do not repair only the CLI-local duplicate. |
| `phoenix_arm/tools/phoenix_depth.cpp:3725-3736` | Optional resolution/level P2 overrides remain wired into the production depth body. | Remove them from the parity route; use admitted `P1=1`, nominal `P2/P1=500`, and guide decay without resolution tuning. |
| `phoenix_arm/tools/phoenix_depth.cpp:3747-3810` | Default-on p2/p92 coarse-argmin confinement explicitly compensates for the implementation's noisy cost. | Delete from parity. Level 0 uses the full lookup; higher levels derive per-pixel `(lower,count)` from previous Depth map and Skip mask. See TRUTH v3.0.291 / G-40. |
| `phoenix_arm/tools/phoenix_fuse.cpp:2031-2098` | NCC-derived global depth multiplier, clamped to `[0.5,3]`. | Delete. Consume lookup-selected mm depth directly. |
| `phoenix_arm/tools/phoenix_fuse.cpp:2100-2238` | Per-contributor NCC depth maps replace the admitted shared depth/warp consequence. | Delete. Build the five exact terminal whole-State calibrated warp records and use the admitted depth map. |
| `phoenix_arm/tools/phoenix_fuse.cpp:2240-2315`; `engine/merge/flow_reg.*`; `engine/merge/CMakeLists.txt:24` | Dense coarse-to-fine block-NCC flow is default-on and linked into the merge library. | Remove from the parity target and from `WarpRecord`; calibrated projection plus the exact local IRAMP refinement supplies registration. |
| `phoenix_arm/tools/phoenix_fuse.cpp:2716-2740`; `engine/merge/iramp.cpp:109-121,304-321,398-416`; `engine/merge/iramp.h:76-92` | Narrow depth ladder, `accept_min_ncc=0.75`, Jacobian/flow controls, and duplicate NCC candidate gates alter contributor survival. | Replace with the admitted IRAMP sentinel policy, G-49 refinement, continuous score weighting, and `0x36e530` reconstruction. |
| `phoenix_arm/tools/phoenix_fuse.cpp:3022-3256` | Default-on flow-aligned detail transfer selects `use_sr` and bypasses `merge::runIramp`; the admitted IRAMP path runs only in the `else` arm. | Delete this branch from parity. The default path must execute the exact seven-input IRAMP score/candidate/reconstruction chain. |
| `phoenix_arm/tools/phoenix_fuse.cpp:1462-1510`; `engine/edit/phoenix_project.cpp:789-809` | CCM alpha is a direct average of rg/bg record-space fractions with a `0.245` fallback. | Implement exact public neutral -> fixed-point scene xy -> 31-row Robertson round trip -> clamped reciprocal-temperature A/D65 interpolation from `CLM-CCM-002`. |
| `phoenix_arm/tools/phoenix_fuse.cpp:3271-3302`; `engine/edit/phoenix_project.cpp:810-817` | Both render and edit paths row-scale the selected CCM to force neutral. | Delete the extra matrix mutation. Apply the admitted interpolated matrix unchanged. |
| `phoenix_arm/tools/phoenix_fuse.cpp:3542-3570` | Default-on post-CCM sRGB-linear chroma denoise writes back into the ProPhoto master and clamps channels nonnegative. | Remove from parity. Use the admitted pre-CCM CNR/NLM placement and preserve negative/HDR float output. |
| `phoenix_arm/tools/phoenix_fuse.cpp:1353-1357,3664-3680,3793-3806` | The fitted `lumenLook` remains available, but current default is straight output. | Preserve `no_look=true` for parity or remove the option from parity builds. It is not an active default divergence in this snapshot. |

The most consequential depth defect is upstream of the merge: the code itself
says the p2/p92 window is compensating for a noisy cost volume. Keeping that
regularizer while tuning IRAMP would hide, not repair, the G-42/G-43 mismatch.

The most consequential merge defect is similarly structural: with current
defaults, flow enables `use_sr`, the detail-transfer branch runs, and
`merge::runIramp` is skipped. A result produced by that default cannot validate
the admitted IRAMP implementation even if `engine/merge/iramp.cpp` itself is
later corrected.

## Stale Audit Dispositions

The external audit set was useful research direction, but several of its
"OPEN" labels predate later Codex admissions and must not be copied into a new
spec or implementation plan:

| External disposition | Current authority |
|---|---|
| `ENGINE_RECONCILIATION` reopens colored Guidance as a Codex formula problem. | The same document later identifies its Bayer-phase/application bug. `CLM-STEREO-001` now closes Guidance as exact `[R,0.5*(G1+G2),B,1]` with default hot-pixel/native configuration. |
| `DEPTH_AUDIT` / `PROVENANCE_LEDGER` call G-42 caps, weights, and accumulation unproven. | TRUTH v3.0.289 closes source-to-anchor pairing, per-source weights, rounding, per-source clamp, and cross-source modulo-u16 addition. |
| Four-path SGM is retained while eight paths are described as optional. | TRUTH v3.0.290 closes eight signed paths and their positive/negative group order. |
| G-40 per-level counts and the range builder are treated as captured tables or open policy. | TRUTH v3.0.291 closes generated per-input counts and the exact previous-depth/Skip-mask `(lower,count)` policy. |
| `GEOMETRY_AUDIT` calls movable-mirror frame/sign convention unverified. | TRUTH v3.0.297 closes the public movable-mirror constructor formula and selected convention with two-body evidence. |
| `MERGE_AUDIT` calls the sentinel predicate, `0x36e530`, and MonoFusion Wiener algebra open. | `CLM-MERGE-005/006` and `CLM-PREFUSION-002` now close candidate policy, score/reconstruction consequence, and profile-3 MonoFusion mode 0. |
| CalibStage `factory/current` bank names are listed unknown. | `CLM-WARP-003` addenda close selector `0=factory`, `1=current`, plus transferred K/R/t public origins. |

Use those audits as provenance for why a probe was run, not as a live gap list.

## Rebuild From Current Truth

### 1. Input and camera image preparation

Implement the exact public LRI contract and pixel stages before evaluating
depth or merge quality:

- `CLM-LRI-001`, `CLM-INPUT-001`: record merge, raw offsets, dimensions,
  stride, little-endian 10-bit unpacking, Bayer/mono phase.
- `CLM-DEMOSAIC-002`: exact four-phase `DemosaickLightV1`, border and SSE
  reciprocal behavior.
- `CLM-AWB-001`: public reciprocal AWB source and two live consumers.
- `CLM-CORRECTION-001`: public vignetting selection/interpolation/shaping;
  tested profile-3 cross-talk exclusion.
- `CLM-PIPELINE-001`: fixed payload callback order. Do not move all
  correction/denoise/sharpen work to an arbitrary post-merge phase.

The depth build's historical “colored guidance mystery” is not an open color
matrix. Current `CLM-STEREO-001` proves Guidance as default-hot-pixel,
native/no-output-color-conversion `collapse2`:

```text
[R, 0.5*(G1+G2), B, 1]
```

Use the exact Bayer phase and normalization. The external reconciliation
itself later found that its apparent grayscale/color contradiction came from
its own phase/application path, not from a missing Guidance CCM.

### 2. Stereo images, color match, and geometry

Use the admitted source order and preparation:

- wide: anchor/source order `A1,A5,A2,A3,A4`;
- tele: `B4,B2,B5,B1,B3`;
- `Images[0]` and Guidance are the tier anchor;
- non-anchor `CreateStereoImage` products use the admitted per-image affine
  fit `A=chol(cov_target)*inverse(chol(cov_source))`,
  `b=mean_target-A*mean_source`, with the exact sample gate and fallback in
  TRUTH v3.0.298.

Geometry must use the admitted composed records, not raw K/R/t plus an NCC
pose refinement:

- `CLM-WARP-003`, `CLM-STATE-001`: focus-evaluated K, anchor-relative pose,
  derived envelope scale/origin, distortion record, and terminal whole-State
  publication into `PipelineCache+0x258`.
- TRUTH v3.0.293: exact focus-K pair selection and float32 interpolation.
- TRUTH v3.0.294: exact undistort-envelope construction.
- TRUTH v3.0.297: public movable-mirror pose formula, including the installed
  reflection/frame convention.

Do not infer a camera-body or firmware correction from capture date. The
formula is public-field driven; targeted Unit-2 discriminators already span
the second physical calibration signature.

### 3. Plane sweep and SGM

Replace the stale open-item dispositions in `03_STEREO_DEPTH.md` with current
admissions:

- TRUTH v3.0.289 / G-42: exact source-to-anchor 3x3 byte-patch pairing,
  `(2,6,6,0)` caps, source weights, rounding, u16 behavior, and OOB policy.
- TRUTH v3.0.290 / G-43: eight paths, exact signed directions, positive then
  negative task groups, `2000` initialization, and saturating aggregation.
- `CLM-STEREO-001`: exact P1/P2/guide decay, far/current/near polarity,
  Skip-mask generator, Guidance, and hot-pixel formula.
- TRUTH v3.0.291 / G-40: level-0 full lookup range; higher-level per-pixel
  `(lower,count)` from prior Depth map and Skip mask; committed active extent
  `ceil(max_upper/8)*8`. Observed focal sequences are examples, not constants.

No p2/p89 window, global confidence clamp, P2 resolution knob, or final depth
scale belongs in the parity path.

### 4. Wide anchor MonoFusion

The external “G-58 Wiener algebra” stub is superseded. Canonical profile-3
wide uses A1 target plus A2 mono in mode 0; tele uses direct B4.

Implement from:

- [mode-0 wavelet formula](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_prefusion_monofusion_wavelet_formula_two_body.md): public exposure/VST inputs, installed panchromatic table, frame-scale formula, 16x16/step-8 flow-aligned patches, normalized 5/3 lifting, exact 256-value coefficient table, patch-noise law, coefficient Wiener law, half-Hann overlap-add, and final scalar blend;
- [transform edge schedule](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_installed_prefusion_monofusion_transform_edges.md): complete forward/inverse boundaries and packing;
- [secondary confidence callback](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_prefusion_monofusion_confidence_callback_two_body.md): exact confidence-map formula.

Do not replace this with an ordinary DCT, generic Wiener denoiser, or guessed
lifting schedule. MonoFusion mode 1 is only a profiles-1/2 compatibility gap;
it is not a profile-3 stub.

### 5. IRAMP merge

Use the actual seven-input contract:

```text
src1 = A1 wide / B4 tele ReferenceImageCache guide
src2 = A1+A2 MonoFusion wide / direct B4 tele baseline
srcs = B1..B5 wide / C1..C5 tele candidates
warps = five terminal whole-State records
```

Then implement the admitted formulas in order:

1. calibrated projection/pair-grid and candidate patch preparation;
2. exact RGB-to-I1/I2/I3 transform (TRUTH v3.0.295);
3. coarse SAD/WTA plus coupled two-variable subpixel refinement
   (TRUTH v3.0.292);
4. exact `0x36cde0` structural score;
5. exhaustive sentinel/rejection policy, with no invented NCC threshold;
6. baseline `0.2f` seed and surviving-candidate continuous weights;
7. exact `0x36e530` inverse CDF 9/7 reconstruction;
8. shaping, inverse opponent transform, square/post-square scale, half cache,
   and selected-cache resample.

Primary formula bundles:

- [score](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_iramp_score_formula_four_zoom.md)
- [candidate policy](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_iramp_candidate_policy_four_zoom.md)
- [reconstruction](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_iramp_accumulator_reconstruction_four_zoom.md)
- [final consequence](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_final_iramp_score_image_effect_wide_tele.md)

Dense flow may make one JPEG look sharper, but it cannot validate this
mechanism and must not remain in the parity code path.

### 6. Color, denoise, sharpen, clarity, and output

- `CLM-CCM-002`: public AUTO AWB neutral, fixed-point scene xy, Robertson
  round trip, reciprocal-temperature A/D65 interpolation. Apply the admitted
  matrix without a neutral-forcing rewrite.
- `CLM-DENOISE-002`: selected CNR formulas and public/generated vector origins.
- `CLM-DENOISE-001`: exact PatchNLM L1/max/tent/`rcpps` formula and generated
  `range_scale`; do not substitute an exponential NLM.
- `CLM-SHARPEN-001`: Lab-L-only unsharp formula, public packet, exact sigma
  and 3/5/7-tap policy.
- `CLM-SHARPEN-002`: exact Laplacian clarity pyramid and transfer.
- `CLM-PIPELINE-001`: clarity is index 13; index 15 is conditional
  linear-ProPhoto/D50 materialization, not a look curve.
- `CLM-OUTPUT-002`: top-left contiguous RGB float32 TIFF with embedded
  linear-ProPhoto ICC is the independent modern output contract. Keep HDR and
  negative values unclamped.

JPEG/sRGB display rendering may be offered as a separately labeled product
operation. It is not the parity oracle and must not be used to judge the
linear pipeline.

## Validation Order

Do not validate only the final JPEG. Compare in this order so an early error
cannot be hidden by later tuning:

1. unpacked raw and Bayer phase;
2. demosaic/collapse2 Guidance and non-anchor affine outputs;
3. undistorted/envelope-mapped camera planes;
4. per-level Range maps, Skip mask, hypothesis-index map, and lookup identity;
5. guided-upsample depth;
6. MonoFusion wide baseline or direct tele baseline;
7. five calibrated candidate projections and IRAMP score/reconstruction
   fixtures;
8. linear-ProPhoto float output before any display transform.

Use `CLM-VALIDATION-001` correctly: depth repeats are nondeterministic in
class, so validate in-range indices, bit-exact index-to-lookup coupling,
finite mm bounds, dimensions, and admitted stage fixtures. Do not require one
golden depth hash across repeated tele renders.

## Genuine Remaining Investigation Scope

For the requested profile-3 LRI-to-modern-linear-image target, no current
ledger claim is `OPEN` or `PARTIAL`. The remaining ledger scopes are:

- profiles `1/2` MonoFusion mode 1 and GUI/editing surfaces
  (`CLM-COMPAT-001`), outside the target;
- `DepthCache` and `DepthEditor` liveness generalization, outside the base
  profile-3 merge (`CLM-DEPTH-001/002`);
- generic slot-15 unequal color-selector formulas outside the admitted route.
  The destination and matching-config formula close at v3.0.305, and tested
  profile-3 incidence closes as exact copy at v3.0.306 across the Unit-1
  quartet plus targeted Unit-2 controls;
- a Lumen display/JPEG look curve, intentionally outside the admitted modern
  linear output contract.

More two-body photographs are useful for adversarial validation and rare
supported-input discovery. They should be partitioned by per-file calibration
digest, focal/reference/firing topology, and public settings. They are not a
license to attribute a discrepancy to camera body or firmware without a
controlled discriminator.

## Handoff Rule

The implementation team should consume `docs/TRUTH.md` v3.0.307 and the live
claim ledger, not the older numbered spec's inline GAP list. Any proposed
replacement algorithm must first be traced to an admitted claim/evidence
bundle. If it cannot be, label it non-parity and keep it out of the validation
path.
