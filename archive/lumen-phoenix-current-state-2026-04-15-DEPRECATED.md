# Lumen Phoenix — Investigation Current State
**Last updated:** 2026-04-13 (All unknowns closed — AWB order, CRA algorithm, CCM interpolation, Cauchy a, 35mm crop, BJPG format confirmed)  
**Purpose:** Briefing for the investigation agent. Read this first, then the full log if needed.  
**Full log:** `/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lumen-phoenix-investigation.md`

---

## Status: ALL OPEN QUESTIONS CLOSED (2026-04-13)

All named OQs (A/B/C/D/E/F) and Lumen-side questions (Q1 fusion, Q2 AWB, Q3 demosaic) are closed. **Phoenix spec writing and POC implementation are now unblocked.**

Next phase: write the Phoenix reimplementation spec covering the full pipeline from LRI decode → demosaic → calibration → depth → fusion → tone mapping. All required facts are in the solid table below. Full investigation log has source details.

Full agent instructions — WSJF, model selection, spike rules, finding format — are in the full log, Agent Instructions section.

---

## Reference paths

| Resource | Path |
|---|---|
| **Phoenix spec facts (start here for implementation)** | `/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/phoenix-pipeline-facts.md` |
| Full investigation log | `/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lumen-phoenix-investigation.md` |
| C++ bridge | `/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process.cpp` |
| Build script | `/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/build.sh` |
| libcp.dylib | `find /Users/ryaker/Dev/L16_Lumen_ReverseEngineering/Lumen -name "libcp.dylib"` |
| LRI archive | `/Volumes/Base Photos/Light/` — `YYYY-MM-DD/` subdirectories |
| Test capture | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` + `.lris` |
| Ground truth TIFF | `/Volumes/Dev/Light_Spike/ground_truth.tiff` |
| Depth map | `/Volumes/Dev/Light_Spike/depth_map.npy` |
| LRI catalog | `/Volumes/Dev/lumen-phoenix-scratch/lri_catalog.db` |

**Before any spike:** confirm libcp.dylib is present and LRI volume is mounted. If either is missing, stop.

---

## L16 hardware architecture — verified

### Zoom mode firing rules

| Zoom | Cameras that fire | Count |
|---|---|---|
| 28mm | 5A (A1/A2/A3/A4/A5) + 5B (B1/B2/B3/B4/B5) | 10 |
| 35mm | 5B + computational synthesis | — |
| 70mm | 5B (B1/B2/B3/B4/B5) + 6C (C1/C2/C3/C4/C5/C6) | 11 |
| 150mm | 6C (C1/C2/C3/C4/C5/C6) only | 6 |

C cameras do NOT fire at 28mm. A2 IS active at 28mm. C6 (ID15) IS active at 70mm and 150mm — verified from L16_03434.lri (zoom=70, 2019-05-18) and L16_02285.lri (zoom≈149, 2018-07-29). C6 pixel data is 99.83% non-zero across 4×1MB samples in both captures. The 5B+6C=11 camera count at 70mm is confirmed. CCM block absence of C6 (42=14×3 records) is a factory unit calibration decision, NOT an indicator of hardware absence — the geometric cal block (32,832 bytes, 16 records) covers all 16 cameras including C6.

### Camera roles

- **A cameras (28mm, direct-fire):** stereo depth baseline + wide-angle canvas
- **B4 (fixed mirror, 70mm):** telephoto center — always forward-pointing
- **B1/B2/B3/B5 (movable mirrors, 70mm):** telephoto corners — fixed azimuth ±38°/±144° factory quadrants. At 28mm they DO contribute to the canvas despite their optical axis at 38° exceeding the canvas half-FOV of 31.67°. Their inner-edge FOV overlap (from ~28°–31.67°) falls within the canvas boundary — they contribute to the corner regions at ~40–100% of B4's photometric weight. At 70mm they are the primary capture pointing forward. See OQ-F finding (verified 2026-04-12).
- **C1/C2/C3/C4 (movable mirrors, 150mm):** same quadrant pairing as movable B cameras. Fire at 70mm and 150mm.
- **C5 (glued mirror, 150mm):** fixed pointing, active.

### Movable mirror key finding (verified 2026-04-12)

Each movable camera has exactly ONE R_fold — a fixed pointing direction. The 4 encoder configs per camera control **focal position (zoom level) only**, not pointing direction. Azimuth is permanently fixed at factory calibration.

### Canvas geometry (verified)

10432×7824 output, fx=8457.2px, hFOV=63.33°, vFOV=49.65°.

---

## What is solid — do not re-investigate

| Finding | Status |
|---|---|
| libcp.dylib callable via C++ bridge, no GUI needed | ✅ Verified |
| Bridge produces ground truth at 10432×7824, MAD=0.067% vs Lumen GUI | ✅ Verified |
| QA: multiple A-cameras independently drive depth | ✅ Verified |
| QB-1: A-camera stereo matches Lumen depth, percentile r=0.954 | ✅ Verified |
| QB-2: Warp geometry math correct, round-trip <0.030px | ✅ Verified |
| QC: Bridge is valid ground truth source | ✅ Verified |
| Canvas: 10432×7824, fx=8457.2px, hFOV=63.33°, vFOV=49.65° | ✅ Verified |
| Movable camera azimuth fixed at factory — encoder configs = focal position only | ✅ Verified |
| At 28mm: 10 cameras fire (5A+5B). C cameras absent. A2 active. | ✅ Verified |
| At 70mm: 11 cameras fire (5B+6C) | ✅ Verified |
| At 150mm: 6C cameras fire only | ✅ Verified |
| At 28mm: movable B cameras (B1/B2/B3/B5) contribute to canvas corners | ✅ Verified (OQ-F, 2026-04-12) | Corruption experiment: MAD 0.12–0.16% vs ground truth, 0.8–1.9% pixels changed >1%. Calibrated against B4 (center mirror, 0.166%/1.8%) and A1 (primary, 15.6%/90.1%). B cameras contribute via inner-edge FOV overlap (28°–31.67°) even though their optical axis is at 38°. |
| All 16 ISP stage names confirmed via C++ RTTI | ✅ Verified |
| ISP two-tier: base pipeline (bridge-accessible) vs GUI-only editing pipeline | ✅ Verified |
| Fusion entry point: FusionCacheBayer::vfunc[3], tile-parallel | ✅ Verified |
| Tile processor: 661 GP + 610 non-GP, split by resolution test at 0x3D070C | ✅ Verified |
| Bicubic renderer: project_roi_to_camera (0x3e2e90), Catmull-Rom, float32 RGBA | ✅ Verified |
| LRI formats: 2017-era, 2018-normal, WDR — all three confirmed | ✅ Verified |
| UNKNOWN LRI format (0.1.x firmware, 515-file main cluster): stride=10,485,764 bytes/camera, 8 cameras/chunk, W=4160 bpr=5200 H_int=2016 rows, same 10-bit MIPI decode as 2018-normal. 2018-normal correction: H_int=1950 rows (not 2473). Full findings: oqe_unknown_format.md. | ✅ Verified (OQ-E, 2026-04-13) |
| Per-capture zoom config: LightHeader.field_12.field_4, argmin vs factory nominals | ✅ Verified |
| Ceres: 3 independent `Problem` lifecycles in libcp. **5** AutoDiff cost functors total (not 18). Pass A = LabCostFunction<25,9> single-block L2 HSV/Lab calibration, max_iter=2000 (`0x11749a`). Pass B = LightBA full BA — CameraProjection<2,1,1,2,3,3,3> (per-observation loop) + EntrancePupilCost<3,3,3> + IntrinsicsCost<3,1,2> in one Problem with 6 AddParameterBlock + 6 SetConstant/Variable toggle pairs (coarse-to-fine schedule), no loss, no bounds (`0x201a4f`). Pass C = **ReProjectionCost<2,1> per-point bounded 1-DOF depth refinement** with stack-constructed **CauchyLoss** robust loss, Lower/UpperBound set per-point, single scalar depth parameter, N residuals per point (one per observing camera), outer loop over all feature points — this is `lt::Triangulator::refine3dPoints` (`0x20d1ac`). Runtime 183/347 aggregate counts are per-capture, not static. | ✅ Verified (OQ-D, 2026-04-13) |
| Black level=42.0, white level=1023.0, sensor AR1335 | ✅ Verified |
| AWB gains stored in LRI Block 8 f19.f15 as [R_gain, 1.0, 1.0, B_gain] (green unity). Also recomputed at render time via SoftISP::Stats&. Phoenix should read stored gains directly — no per-frame AWB reimplementation needed. 9 AWB preset modes (AUTO/DAYLIGHT/SHADE/CLOUDY/TUNGSTEN/FLUORESCENT/FLASH/CUSTOM/KELVIN). Dual-illuminant CCM interpolation by CCT, PCS=D50. | ✅ Verified (Q2, 2026-04-13) |
| 4 tone curves embedded in libcp: acr, light_v1, light_v1_lowlight, light_v2 | ✅ Verified |
| Tone curves = 1024-entry float32 LUTs + fixed piecewise pre-shaper + exp2f EV scalar. All 4 LUTs extracted from libcp.dylib. ACR y(0.18)=0.379, light_v1 y(0.18)=0.203, light_v1_lowlight y(0.18)=0.377, light_v2 y(0.18)=0.201. Pre-shaper: u=0 if x≤0.0025; (x−0.0025)²·100.50251 if 0.0025<x<0.0075; (x−0.005)·1.0050251 if x≥0.0075; LUT idx=clip(u·1024,0,1023). Factory table @ vaddr 0x659c70, LUT pointers 0x5e31b0/5e41b4/5e51b8/5e61bc in __TEXT __const. Output: `/Volumes/Dev/lumen-phoenix-scratch/tmo_*.npy` + `tmo_characterization.json`. | ✅ Verified (OQ-A, 2026-04-13) |
| Bayer pattern: BGGR (value 3) for all 16 cameras — sensor-wide constant, confirmed via cv2.COLOR_BayerBG2RGB POC (MAD=1.70% vs ground truth) | ✅ Verified-indirect |
| Vignetting grids: 16 cameras × 4 channels × (17,13) float32. Center=1.0 normalized, corners 2.0–3.8×. Field path: rec.f4.f2[ch].f2.f3 = 884 bytes = 221 float32. Block B payload ~262,969 bytes @ L16_02130 file offset 162,324,576. | ✅ Verified |
| CRA grids: 16 cameras × (13,17,4,4) float32. Center diagonal [1.0000,1.0034,0.9966,1.0000]. Field path: rec.f4.f1.f4 = 14,144 bytes = 3,536 float32. Same Block B as vignetting. | ✅ Verified |
| CCM matrices: 14 cameras × 3 illuminants × (3,3) float32. A2 (ID 1) and C6 (ID 15) absent (42 records = 14×3). Illuminants: TungstenA=0, D65=2, F11=6. Block C payload ~35,266 bytes @ file offset 162,589,394. A1 D65: [[0.900,0.132,−0.067],[0.310,1.074,−0.384],[−0.057,−0.430,1.313]]. CCM absence of A2/C6 = factory unit cal decision, NOT hardware absence. | ✅ Verified |
| C6 (ID15) active at 70mm and 150mm: 5B+6C=11 cameras verified. L16_03434.lri (zoom=70): Block 3 LightHeader lists C1/C3/C4/C6 (chunk 3 of 3), C6 pixel data 99.83% non-zero across 4×1MB samples (file offset 162,291,720, 16,228,344 bytes). L16_02285.lri (zoom≈149): same block structure, C6 pixel data 99.82% non-zero. Geo cal block (32,832 bytes, 16 records) covers all 16 cameras including C6 in every LRI. Source: spike_c6_verification (2026-04-13), c6_verification.md. | ✅ Verified (2026-04-13) |
| **Cross-camera fusion operator = ≤3-tap weighted aggregation with depth-aware warp, NOT a Laplacian pyramid blend.** Inner kernel at 0x36fd30 has 3 distinct source-base registers (rbx/rsi/r9), Catmull-Rom cubic weight LUT built at 0x36f890–0x36fa9d, per-pixel `rcpss` on `depth+offset` → perspective divide → `mulps` weights → accumulate. Per-tile gating via PyramidAlignment + ComputeFlowField + GetSkippingMaskGrid (the "3-6 pyramid levels" string 330047 is alignment, not blend). `CreateAndBlendLaplacianPyramids` exists but its protobuf parameters carry the prefix `tone_adjust.lpyr_*` (strings 330460–330545) → Laplacian belongs to the tone-adjust stage (stage 14), NOT to cross-camera fusion. `ExposureFusion` takes a single source → intra-source HDR bracket merge, not cross-camera. This reconciles the 2026-04-12 LLDB observation that `blend_lambda` had zero fires during fusion. Source: `/Volumes/Dev/lumen-phoenix-scratch/lumen_side_analysis.md` §Q1, disasm_full.txt 0x36f800–0x36fffc, strings_all.txt 324238/324256/330047/330460–545. | ✅ Verified (Q1, 2026-04-13) |
| **AWB pipeline order confirmed: pre-demosaic (Bayer), then demosaic, then CCM.** Stage 8=AWB (multiply R-cells by R_gain, B-cells by B_gain on packed float Bayer), Stage 10=Demosaic (Bayer→RGB), Stage 12=CCM (3×3 matrix on RGB). Confirmed via LLDB stage trace (lambda_5=AWB, lambda_6=CCM). L16_02130 gains: R=1.717839, B=1.588839 (from LRI Block 8 offset 162,624,758+32, f19→f15→field1/field4 as LE float32). **Do NOT apply AWB gains post-demosaic — causes double-application with CCM.** | ✅ Verified (2026-04-13) |
| **CRA correction algorithm confirmed.** Class `lt::LensUndistortCRA`, applied pre-demosaic at tile-fetch time in `SourceImageCache` via `ImageWarp<Bicubic, vec4x8ui, LensUndistortCRA>`. Operation: spatially-varying 4×4 Bayer channel mixing matrix (channels: R, Gr, Gb, B) bilinear-interpolated from 13×17 grid. Center matrix ≈ identity; corners: diagonal ~0.95, off-diagonals ~0.02 (optical chief-ray-angle cross-talk). Separate from electronic cross-talk (`RemoveCrossTalkGeneric`, numbered stages 14–19). cra_grids npz shape: (16, 13, 17, 4, 4). Phoenix: apply 4×4 mix to each Bayer quad pre-demosaic. | ✅ Verified (2026-04-13) |
| **CCM illuminant interpolation formula confirmed.** CCT NOT stored in LRI — computed at pipeline time from AWB B/R gain ratio. Blend between nearest two illuminants: w_D65=(CCT−4000)/2500, w_F11=1−w_D65 for 4000K<CCT<6500K; pure TungstenA below 4000K, pure D65 above 6500K. L16_02130 at ~5000K: w_F11=0.60, w_D65=0.40. npz illuminant index order: [0]=TungstenA, [1]=D65, [2]=F11 (regardless of protobuf enum values 0/2/6). | ✅ Verified (2026-04-13) |
| **CauchyLoss scale a=1.0 confirmed.** At VA 0x5c3580 (RIP 0x20beb6 + disp 0x3b76ca): b_=a²=1.0, c_=1/a²=1.0 stored as float64. Phoenix: `scipy.optimize.least_squares(loss='cauchy', f_scale=1.0)`. Quadratic-to-log transition at ≥1px reprojection residual. | ✅ Verified (2026-04-13) |
| **35mm = 28mm pipeline + canvas center-crop. No synthesis pass.** No 35mm-specific functions, symbols, or strings exist in libcp. B cameras at 35mm use encoder config 2 (same as 28mm wide park). 35mm crop on 10432×7824 base canvas: left=1043, top=782, right=9389, bottom=7042 → output 8346×6260 px. hFOV=52.52°, vFOV=40.62°. | ✅ Verified (2026-04-13) |
| **244 outlier LRI files = BJPG (Burst JPEG) format, NOT non-standard stride.** LELR data blocks contain `BJPG` magic at byte +32. Structure: 1,576-byte index + 80 concatenated JFIF JPEGs (variable-length, quality 68–84, tile 1024×512). Confirmed on L16_01951.lri (243.6MB). Total ~302 files post-2018-06-26, firmware v0.2+. Phoenix: skip BJPG files for 2018-normal decode path; decompress via libjpeg per camera if needed. | ✅ Verified (2026-04-13) |
| **AWB = hybrid capture-time + stats-driven render-time, NOT grey-world.** `Pipeline::setWhiteBalance(AWB)::$_20..$_23` (4 overloads) all consume `SoftISP::Stats&`, not raw pixels (strings 324585–324592). Preset enum full: AWB_MODE_{AUTO,DAYLIGHT,SHADE,CLOUDY,TUNGSTEN,FLUORESCENT,FLASH,CUSTOM,KELVIN} (strings 318460–318469). Dual-illuminant CCM interpolation by CCT, PCS=D50 (strings 329930–933, 330818). Capture-time side: LRI Block 8 f19.f15 stores `[R_gain, 1.0, 1.0, B_gain]` with green unity. `Pipeline::setColorCorrection::$_58..$_63` same stats-driven pattern. Phoenix can read stored gains directly; no per-frame auto-WB reimplementation required. Source: `/Volumes/Dev/lumen-phoenix-scratch/lumen_side_analysis.md` §Q2, corroborates prior 2026-04-12 AWB entry. | ✅ Verified (Q2, 2026-04-13) |
| **Demosaic V1 vs V2 are algorithmically distinct; V2 is Phoenix target.** Template families: `DemosaickLightV1<offX,offY>(Image<vec4x32f>&, Image<float>&, Vec3<float> gains)` × 4 Bayer phases vs `DemosaickLightV2<offX,offY>(Image<vec4x32f>&, Image<float>&, float)` × 4 phases (strings 324317–332). V1 takes Vec3 RGB gains, V2 takes a scalar — different input contracts, not just different parameters. `Pipeline::setDemosaicking::$_24` has 2 sub-overloads (Bayer/BayerFloat payload, V2 path); `$_25..$_31` take `(vec4x32f&,float&,Vec2<int>&,Vec3<float>&)` (V1 path × 7 variants) (strings 324593–609). `ImageDemosaickFilter<DemosaickFilter::{0,2,3},float,offX,offY>` (12 instantiations, strings 314533–556) including Malvar is the editing-pipeline tier only, not on bridge/GT codepath. Profile-indexed dispatch via `ApplyTuning` 0x3cbc10 / jump table 0x3cd290. Profile 0 (bridge default) → light_v2. Phoenix only needs V2 for ground-truth parity. Source: `/Volumes/Dev/lumen-phoenix-scratch/lumen_side_analysis.md` §Q3, corroborates prior 2026-04-12 DEMOSAICK V1 vs V2 entry. | ✅ Verified (Q3, 2026-04-13) |

---

## What is wrong — do not use these

| Claim | Correct understanding |
|---|---|
| Slot→camera mapping (S00=A5, S02=A1 etc.) | ⚠️ SUPERSEDED — warp block ≠ image sub-block order |
| Stride=10,616,832, 8 sub-blocks/chunk | ⚠️ SUPERSEDED — correct: 5 cameras/chunk, sensor W=4160 H=3120 |
| QA slot corruption results (slot identities) | ⚠️ SUPERSEDED — camera attribution unreliable, re-run needed |
| S07 = A3 primary stereo reference | ⚠️ SUPERSEDED — slot identity was wrong |
| Zero-depth slots = B/C cameras | ⚠️ SUPERSEDED — slot identity was wrong |
| A2 (ID1) permanently absent | ❌ Wrong — A2 IS active at 28mm |
| C6 (ID15) permanently absent | ❌ Wrong — C6 IS active at 70mm and 150mm (verified 2026-04-13). CCM block absence is unit-level color cal, not capture-level absence. |
| CCM absence of C6 = C6 hardware failure | ❌ Wrong — CCM block (14 cams × 3 illuminants) is a factory cal snapshot. Geo cal block covers all 16 cameras including C6. |
| Active cameras = 14 (4A+5B+5C) at 28mm | ❌ Wrong — at 28mm it is 10 (5A+5B), C cameras don't fire |
| Movable cameras are sideways stereo depth sensors | ❌ Retracted — fabricated architecture, no source |
| Forward canvas = 6 cameras | ❌ Retracted — based on wrong canvas bounds |
| 18 cost function types in libcp | ❌ Wrong — exactly 5 AutoDiffCostFunction types: LabCostFunction, CameraProjection, EntrancePupilCost, IntrinsicsCost, ReProjectionCost. The "18" figure came from double-counting RTTI pairs. |
| Pipeline::setToneMapping is callable from C++ bridge | ❌ Wrong — NOT exported in macOS libcp.dylib or Android libcp.so. OQ-A was closed by static LUT extraction from __TEXT __const, not dynamic invocation. |
| Android libcp.so has more debug symbols than macOS dylib | ❌ Wrong — Android is equally stripped. The ~300-symbol delta is Halide runtime (statically linked in macOS, separate .so in Android). No additional Pipeline:: methods exported. |
| AWB gains not stored in LRI — only computed at render time | ❌ Wrong — gains ARE stored in LRI Block 8 f19.f15 as [R_gain, 1.0, 1.0, B_gain]. |
| Cross-camera fusion uses Laplacian pyramid blending | ❌ Wrong — CreateAndBlendLaplacianPyramids belongs to tone-adjust stage (stage 14, tone_adjust.lpyr_* protobuf params). Fusion is ≤3-tap weighted aggregation with depth-aware warp. |
| 244 outlier LRI files have non-standard strides | ❌ Wrong — they are BJPG (Burst JPEG) format. LELR data blocks contain `BJPG` magic at byte +32, followed by 80 concatenated JFIF JPEGs with a 1,576-byte index. Variable-length per camera; no fixed stride. Firmware v0.2+. |
| AWB gains should be applied post-demosaic to RGB channels | ❌ Wrong — AWB is applied pre-demosaic to the packed Bayer float image (stage 8 per LLDB trace), before demosaic (stage 10), before CCM (stage 12). Apply R_gain to R-cells and B_gain to B-cells in the Bayer array. |

---

## Open questions — work these, in this order

~~**OQ-F — CLOSED 2026-04-12.** All 4 movable B cameras contribute to 28mm canvas. See solid table.~~

~~**OQ-C — CLOSED 2026-04-12.** Per-camera calibration extracted from L16_02130.lri. Bayer=BGGR (all cameras, indirect). Vignetting 16×4×(17,13), CRA 16×(13,17,4,4), CCM 14×3×(3,3) — A2/C6 absent. Output: `/Volumes/Dev/lumen-phoenix-scratch/cal_color_l16_02130.npz`. Source: spike_oqc_cal_extract.py. See solid table.~~

~~**OQ-A — CLOSED 2026-04-13.** All 4 tone curves = 1024-entry float32 LUT + fixed piecewise pre-shaper + exp2f EV scalar. Extracted statically from libcp.dylib (Pipeline::setToneMapping is NOT exported — pivoted from dynamic to pure static extraction). Pre-shaper formula decoded instruction-by-instruction from TMO_ACR::process at 0x2d8150. Factory table at vaddr 0x659c70 holds 4 LUT pointers. Outputs saved to `/Volumes/Dev/lumen-phoenix-scratch/tmo_*.npy`. Source: `spike_oqa_tone_mapping.py`. See solid table.~~

~~**OQ-D — CLOSED 2026-04-13.** All 3 Ceres passes characterized statically. **Pass A** = LabCostFunction 25/[9], offline color calibration, skip at runtime. **Pass B** = LightBA full bundle adjustment (CameraProjection + EntrancePupilCost + IntrinsicsCost, 6-stage Set*Constant/Variable schedule), offline calibration, skip at runtime — Phoenix uses baked factory intrinsics/extrinsics from OQ-C. **Pass C** = `lt::Triangulator::refine3dPoints` — per-point bounded 1-DOF Cauchy-weighted depth optimization with 1 scalar param (depth), N reprojection residuals (one per observing camera), Lower/UpperBound set per point. Reimplementable with `scipy.optimize.least_squares(loss='cauchy', bounds=(lo,hi))`. Only 5 AutoDiffCostFunction types total in libcp (not 18 — that figure was wrong and is corrected in solid table). Source: `/Volumes/Dev/lumen-phoenix-scratch/spike_oqd_ceres.py`, `/Volumes/Dev/lumen-phoenix-scratch/ceres_analysis.md`. See solid table.~~

~~**OQ-B — CLOSED 2026-04-12.** Config selection: argmin(|encoder − nominal[i]|). Config 2 = wide-angle park position (28mm/35mm). Config 3 = telephoto park position (70mm/150mm). Batch-verified across 10 files per zoom level. See solid table.~~

~~**OQ-E — CLOSED 2026-04-13.** UNKNOWN LRI format (transitional firmware 0.1.x). Main cluster (515 files, 2018-03-30 to 2018-06-26): **stride = 10,485,764 bytes/camera**, 8 cameras per chunk, W=4160, bpr=5200, H_int=2016 rows. Same 10-bit MIPI packing as 2018-normal. 3-LELR-chunk structure (chunk0: cameras 0-7, chunk1: ~1MB interstitial, chunk2: cameras 8-15). chunk_len = off12 + off20 = total including 32-byte LELR header. 244 outlier files (post-2018-06-26) have non-standard strides — uncharacterized, low priority. CORRECTION: 2018-normal row count is H_int=1950 (not 2473 as claimed by spike_qb_2018normal.py) — both formats use bpr=5200. Source: inline spike on L16_01806.lri, lri_catalog.db. Full findings: `/Volumes/Dev/lumen-phoenix-scratch/oqe_unknown_format.md`.~~

---

## What a finding looks like

Every finding written back to the full log must include: what was observed (specific, numerical where possible) + confidence (Verified / Hypothesis / Unknown) + source (which spike, file, tool) + what it unblocks. "Looks correct" is not a finding.
