# PHOENIX TRUTH SOURCE 2026-04-17

**Status:** Canonical truth doc for the L16 Phoenix reimplementation.
**Replaces:** `lumen-phoenix-current-state.md` and `phoenix-pipeline-facts.md` as source-of-truth. **Those docs contain refuted claims; do not read them for current architecture.** Refer to them only when this doc explicitly cites a row by quoting them.
**Do read alongside:** `LIBRARY_INVENTORY.md` (411-symbol public API + DepthEditor surface — still accurate, no refutations).
**Investigation window covered:** through 2026-04-17 (40+ KMS entries, ~25 agent reports under `/Volumes/Dev/lumen-phoenix-scratch/`).
**Discipline rule (Rich):** every finding cites a VA + disasm range, an LLDB transcript, an LRI binary offset, or RTTI/string evidence. Hypotheses are tagged. Rich's "X is the merge / X is the reducer" claims require **signature AND body** — both must be cited.
**Reproducibility:** all VAs are file-relative offsets into `libcp.dylib` (x86_64). LLDB reads use `process continue` semantics with **no auto-continue** (auto-continue returns stale registers — see Replication Recipes §7.0).

---

## 1. TL;DR architecture (one page)

```
                LRI file (.lri / .lris)
                          │
            ┌─────────────┴───────────────┐
            ▼                             ▼
      LightHeader parse             Calibration parse
      • zoom_val (field[4])         • Block 3: geometric (16 cams)
      • per-cam: cam_id (f2),       • Block 4: vignetting + CRA (16 cams)
        bayer_red_override (f13),   • Block 6: CCM 14×3×9 (A2/C6 absent)
        bytes_per_row (f9.f4),      • Block 8 f19.f15: AWB gains [R,1,1,B]
        data_offset  (f9.f5)          (PRE-multiply gains; render kernel uses RECIPROCALS)
                          │
                          ▼
       10-bit MIPI BGGR/RGGB/GRBG/GBRG unpack (per-camera Bayer pattern)
                          │
                          ▼
   ┌─────────  Per-camera ISP inside lt::ReferenceImageCache  ────────┐
   │  RIC is a SHARED orchestrator (1 instance, 10 image-buffers).    │
   │  Worker dispatches per-camera BayerPipelinePayload via r14.      │
   │  Stage order on bridge HDR (LLDB-verified):                       │
   │    SourceImageCache  ImageWarp<Bicubic, vec4x8ui,                │
   │                      LensUndistortCRA>  @ libcp 0x261940         │
   │       (radial 4096-LUT undistort, geometric only)                │
   │    STAGE0  LinearizeAndColorScale<uint16>      0x340b00          │
   │            (BL subtract + color-scale matrix)                    │
   │    STAGE1  LinearizeAndColorScale<float>       0x340bf0          │
   │    STAGE2  ImageCorrectBayerPhaseAR1335        0x340cc0          │
   │            (sensor-specific Bayer-phase fix)                     │
   │    STAGE5  Pipeline::setWhiteBalance::$_5      0x340f70          │
   │            (Bayer-cell  ×  1/stored_gain)                        │
   │    DemosaickLightV1<offX,offY> driver          0x2eb560          │
   │            (V2 driver 0x2eba10 + V2 kernel 0x2f0df0 = DEAD CODE) │
   │    STAGE6  Pipeline::setColorCorrection::$_6   0x341040          │
   │            (per-camera CCM blend SETUP only – tile apply runs    │
   │             inside IRAMP via 0xbf4a0; see C18 + Open Q-9..Q-12)  │
   │    Vignetting:                                                   │
   │      RemoveVignettingGeneric<vec4x32f, true>   0x108080          │
   │            (mulps pixel × interpolated grid; per-tile invoke     │
   │             dispatcher 0x345f30 fires 348× across 10 cam threads,│
   │             A2 IS in set; closure scale 0.7373 uniform — see I5) │
   │    Tone curve:                                                   │
   │      LinearTMO::process driver                 0x2d7780          │
   │      Per-tile LUT-apply lambda                  0x2d7a30          │
   │            (light_v1 LUT @ 0x5e41b4, EV mul = exp2f(Settings.exposure))│
   └─────────────────────────────────────────────────────────────────┘
                          │
   Output: per-camera Image<vec4x32f> 4-ch RGBA float32 working buffer,
           cached as Tile<Vec3<Float16>> (3-ch f16 packed RGB, 6 B/px)
                          │
                          ▼
        ┌───── IRAMP-side calibration dispatcher 0x3f6170 ─────┐
        │  Filters cam_ids that don't have CCM entries.        │
        │  At 28mm, passes [0,5,6,7,8,9] = A1+B1..B5 (6 cams). │
        │  At 70mm, passes [8,10,11,12,13,14]= B4+C1..C5 (6).  │
        │  No fallback – throws std::out_of_range otherwise.   │
        │  A2-A5 (28mm) and B1/B2/B3/B5 (70mm) = depth-only.   │
        └──────────────────────────────────────────────────────┘
                          │
                          ▼
   ┌────── lt::ImageResolutionAmp ("IRAMP") — cross-camera merge ──────┐
   │  Setup func 0x365960..0x366082                                    │
   │    builds 64-entry weight LUT, allocates Image<vec4x32f> sized to │
   │    ROI, packs 7 ImageGenerator args + WarpField vector + LUT      │
   │    into stack closure, dispatches Halide kernel.                  │
   │  Halide AOT body 0x3661b0..0x36ae41 (19,601 B)                    │
   │    Per source: warp coords → mpsadbw cost (sub 0x36b920) →        │
   │    bicubic resample → weighted accumulate.                        │
   │    Inner accumulator at 0x369fa1 (SMOKING GUN):                   │
   │      mulps (%rdi),%xmm1                                           │
   │      addps (%rdx,%rcx,4),%xmm1                                    │
   │      movaps %xmm1,(%rdx,%rcx,4)                                   │
   │    Outer ÷5 magic constant -0x3333333333333333 at 0x369f18.       │
   │  Inputs (per-call signature, LLDB-verified):                      │
   │    (Image<vec4x32f>& dst, ImageGenerator& src1, ImageGenerator&   │
   │     src2, vector<shared_ptr<ImageGenerator>>& srcs (size=5),       │
   │     vector<WarpField>& warps (size=5), float scale,               │
   │     Rectangle<int>& roi)                                          │
   │  src1/src2 = anchor IG wrappers (vtables 0x65f668/0x65f6e8) over │
   │     SAME single anchor camera (A1@28mm, B4@70mm), via PC+0x170 = │
   │     lt::ReferenceImageCache (M13/I8). NOT pre-fused composites.   │
   │     Per-tile op @ vt[+0x30] = 0x3ecc10 / 0x3ecd80 (vt[+0x18]      │
   │     never fires). 13 lambdas at 0x229ec0..0x247380 = REFUTED      │
   │     R16/R17 (CalibDataProcessor setup callbacks, NOT reducers).   │
   │  Per-contributor pre-norm @ libcp+0x3eced0 (M14, dispatched from │
   │     IRAMP body 0x366f1c → 0x374ac0 → vt[+0x30] indirect):         │
   │     out = sqrt(max(0, in × IG+0x10)) per channel,                 │
   │     IG+0x10 = effective-FOV ratio (writer 0xe67c0, see C17).      │
   │  5 contributor inputs come from lt::SourceImageCache RB-tree at  │
   │     RIC+0x30 (I9): node+0x20 = cam_id, node+0x28 = SIC*.          │
   │     SIC vtable libcp+0x65f490, init libcp+0x3e0330 from initResAmp.│
   │  Per-tile CCM is APPLIED HERE (not in per-camera ISP):            │
   │     ImageConvertColorSpace::$_0 @ libcp+0xbf4a0 (vt slot 6 of     │
   │     0x6527c0), 370 hits, 2 distinct CCM matrices (C18).           │
   │     Per-camera CCM blend = SETUP via CCMInterpBetweenCalib        │
   │     0x350bc0 (5 hits, single overwrite buffer → one consolidated  │
   │     M for all tiles in this pass).                                │
   │  Wavelet-domain super-res sub-stages:                             │
   │     0x36cde0 = patch stats + CDF 9/7 match-score                  │
   │     0x36e530 = inverse-DWT synthesis + 5-band byte-LUT weighting  │
   │     0x36f800 = Catmull-Rom 64-LUT setup                           │
   │     CDF 9/7 lifting constants @ rodata 0x5cbfd0..0x5cc040         │
   │     (1.5861343, 3.1722686, -0.05298011, -0.10596023, -0.8829110,  │
   │      -1.7658221, 1.1496044, 0.8698644) — JPEG2000-spec exact.    │
   │  Per-pyramid level dispatch via lt::PipelineCache::processLevel:  │
   │     L0 (eax=0) → IRAMP 0x365960              (300 hits at 28mm)   │
   │     L1 (eax=1) → 0x3ebb80 single-source reshape (348 hits)        │
   │     eax∈{2,3,4} → 0x3d0650 single-source resample (370 hits, all  │
   │                   from L1 or post-IRAMP cleanup)                  │
   │     L0 is the only level delivered to the encoder.                │
   └───────────────────────────────────────────────────────────────────┘
                          │
                          ▼
   Output canvas Image<vec4x32f>:
     • L0 dims: 10432×7824 (28mm, 70mm base) or 8848×6624 (70mm tile-tier)
     • Crop applied BEFORE IRAMP via libcp+0xe6d90 + zoom-tier table
       libcp+0xe7020 (Tier 0 ref=28mm, Tier 1 ref=70mm)
                          │
                          ▼
   exportImage::$_3 (1 call/render)
                          │
                          ▼
   CIAPI::Renderer::writeImage(...) → DNGWriter / TIFF / PNG / JPEG
   Bridge tool `lri_process` hardcodes Point<int>{10432,7824} so cropped
   FOVs are upsampled to match (NOT a Lumen GUI behavior).

   Depth pipeline = GUI ONLY in bridge lri_process (profile=2).
   Profile=3 (DESKTOP) activates depth: see D7/D9/D10/D11.

   Depth dispatch chain (profile=3, verified):
     RendererPrivate vt20 @ 0x3b1d20
     → gate 0x3b2fa3 ([imageStorageObj+0] & 0xf == 0x3)
     → StereoAsyncAPI C1 0x3f46d0 → C2 0x3f2c40
     → DepthCache 0x3d8780
     → Triangulator::refine3dPoints 0x20ca00

   Path A cost chain (static-verified, 2 upstream paths):
     ISP Renderer 0x406960 → 0x1ab2d0 → 0x1ac010 → 0x1ac1ac ┐
     Demosaicking 0x27b7a0 → 0x31b470 → 0x3403f0 → 0x343ef8 ┘
       → 0x30b770 [Path A builder]
         → 0xf540 [alloc output buffer]
         → 2×2 dispatch at 0x30b801 → one of {0x30b9f0, 0x30dcc0, 0x30ff60, 0x3121f0}
         → 0x5440 [Halide AOT tile dispatcher] (same as depth StereoAsyncAPI path)

   IRAMP outputs RGB only on bridge HDR. See §2.6 (D7–D11).
```

5-level pyramid table (LLDB-verified at 28mm L16_02130):

| Level | Dims | Ratio | Notes |
|---|---|---|---|
| L0 | 10432 × 7824 | 1.0× | full canvas, only level delivered to encoder |
| L1 | 4160 × 3120 | 2.508× | NON-power-of-2; matches AR1335 native sensor dims |
| L2 | 2080 × 1560 | ×2 from L1 | scratch |
| L3 | 1040 × 780 | ×2 from L2 | scratch |
| L4 | 520 × 390 | ×2 from L3 | scratch |

Pyramid-dims vector lives at `PipelineCache+0x8` (begin pointer of embedded `std::vector<Vec2<int32>>`), written once by `PipelineCache` ctor (0x3ea7d0/0x3eaf00) via `std::vector::operator=` 0x292070 from sub-init 0x3cfd80. **It is NOT a composite buffer.**

---

## 2. Verified Findings

### 2.1 Cross-camera merge / IRAMP

| # | Finding | Evidence (VA + source) | Confidence |
|---|---|---|---|
| M1 | The cross-camera merge function is **`lt::ImageResolutionAmp`** ("IRAMP") at `libcp+0x365960` (setup) + `libcp+0x3661b0..0x36ae41` (Halide body, 19,601 B, 0x4498 stack frame, 120 internal calls). It is the UNIQUE multi-source combine on the bridge HDR path. | Setup signature LLDB-verified across 10 ROIs; smoking-gun N→1 accumulator at `0x369fa1`: `mulps (%rdi),%xmm1 ; addps (%rdx,%rcx,4),%xmm1 ; movaps %xmm1,(%rdx,%rcx,4)`. Outer ÷5 magic `-0x3333333333333333` at `0x369f18`. Source: `iramp_kernel_body.md`, `/tmp/lldb_iramp_kernel_trace*.txt`, `/tmp/libcp_disasm_intel.txt` lines 835314..839523. | **Verified** |
| M2 | IRAMP runtime signature: `(Image<vec4x32f>& dst, ImageGenerator& src1, ImageGenerator& src2, vector<shared_ptr<ImageGenerator>>& srcs[size=5], vector<WarpField>& warps[size=5], float scale, Rectangle<int>& roi)`. **7 ImageGenerator inputs per invocation = 2 anchors + 5 contributors.** WarpField struct = 80 B (verified by `0xCCCCCCCCCCCCCCCD>>SAR4` divide magic). | LLDB BP at setup 0x365960, captured args across 10 ROIs at L16_02130 28mm; 300 invocations per render at 28mm. Source: `image_resolution_amp_verification.md`, `iramp_camera_identity.md`. | **Verified** |
| M3 | Per-camera identity at IRAMP runtime (read of `*(IG+0x08)+0x90` int64 cam_id field). **28mm L16_02130:** `vec[0..4] = {5,6,7,8,9}` = B1..B5; `src1+src2` = composite anchor wrappers (cam_id=0). **70mm L16_03434:** `vec[0..4] = {10,11,12,13,14}` = C1..C5; same anchor pattern. **B-as-A architecture: same C++ vtables, same operator architecture, only input stream differs.** | Direct memory read at IRAMP entry; same vtables 0x1092d9668/0x1092d96e8 at both zooms. Source: `iramp_camera_identity.md`. | **Verified** |
| M4 | **IRAMP-side calibration dispatcher at `libcp+0x3f6170` filters cameras lacking CCM entries.** At 28mm, dispatcher passes only `cam_ids = [0,5,6,7,8,9]` = A1+B1..B5 (6 cams). At 70mm, `[8,10,11,12,13,14]` = B4+C1..C5 (6 cams). A2 + C6 are **dropped**. A3-A5 (at 28mm) and B1/B2/B3/B5 (at 70mm) are RIC-processed but dropped at this dispatcher → **depth-only contributors** (likely feed depth-from-parallax). No fallback: `__cxa_throw std::out_of_range("map::at: key not found")` at `0x3f6866`. | LLDB BP at 0x3f6170, 7 hits at 28mm, all cam_ids enumerated. Source: `a2_destination.md`, `c6_destination_and_depthcache.md`. | **Verified** |
| M5 | **Refined B-as-A model (single canvas anchor):** at 28mm = A1 (canvas anchor) + B1..B5 (5 high-res contributors); at 70mm = B4 (canvas anchor) + C1..C5 (5 high-res contributors). **Effective IRAMP fusion = 6 cameras at BOTH zooms** (not 10/11). | Combined finding from M2+M3+M4. Anchor pyramid descriptor at 28mm encodes 20×15 = 300 tile-cells, exactly matching IRAMP's 300 invocations. Visual confirmation via per-camera puzzle-piece thumbnails at `/Volumes/Dev/lumen-phoenix-scratch/puzzle_pieces/L16_03434_70mm_<CAM>.png`: B4 = full FOV anchor, C5/C1 = zoomed sub-region inserts. Source: `puzzle_pieces.md`, `iramp_camera_identity.md`, `a2_destination.md`. | **Verified** |
| M6 | IRAMP's per-source weighting: 16-entry LUT applied per-pixel as **separable spatial kernel** — same LUT multiplied with each of 5 sources. **NO separate weight/coverage buffer; NO per-camera radiometric weight at the IRAMP body.** Per-source contributions accumulate additively into per-tile scratch within ONE IRAMP call (5× addps+movaps on same buffer). | `iramp_kernel_body.md`. Per-camera radiometric is upstream (AWB+CCM+vignetting per camera). | **Verified** |
| M7 | **IRAMP wavelet-domain super-resolution.** Sub-stages `0x36cde0` (patch stats + CDF 9/7 match-score) and `0x36e530` (inverse-DWT synthesis + 5-band byte-LUT weighting) use **CDF 9/7 biorthogonal wavelet** (JPEG2000 spec). Lifting constants at `.rodata 0x5cbfd0..0x5cc040`: `(1.5861343, 3.1722686, −0.05298011, −0.10596023, −0.8829110, −1.7658221, 1.1496044, 0.8698644)` — bit-exact JPEG2000 spec values (uniquely identifying). Hit counts at ~6% partial run: `0x36cde0` = 15,890; `0x36e530` = 16,629; `0x36f800` = 87. | `sub_stages_36cde0_36e530_36f800.md`. Sub-stage 0x36f800 = Catmull-Rom 64-entry LUT setup, dispatches to inner uint8 luma-grid kernel at `0x36fd30` (which is **NOT** the cross-camera merge — see refuted §3). | **Verified** |
| M8 | **Pyramid-level dispatch:** `lt::PipelineCache::processLevel(int)` arg `eax` is a render-stage code (NOT a pyramid index). Runtime distribution on bridge HDR: `eax==0` → IRAMP `0x365960` (300 hits at 28mm); `eax==1` → `0x3ebb80` single-source bicubic post-IRAMP reshape (paired with `0x3edb80` sqrt kernel; 348 hits = 48 from L1 dispatcher + 300 post-IRAMP via `initResAmp_1` lambda `0x3ecda8`); `eax∈{2,3,4}` arm never fires on bridge. `0x3d0650` = single-source pyramid-level resample primitive (370 hits, signature `f(this,outImage*,Rect*,targetVec2i*,level_int)`). | LLDB hit-count traces. Source: `merge_function_reconciliation.md`. | **Verified** |
| M9 | `lt::StackFusion` at `libcp+0x1b7d80` fires **ZERO times** on bridge HDR despite multi-source signature. Alternative codepath (probably stack-LRI captures or Lumen GUI editing pipeline). | LLDB BP, 0 hits across L16_02130 28mm AND L16_03434 70mm full renders. Source: `stackfusion_characterization.md`, `merge_string_inventory.md`. | **Verified** |
| M10 | `lt::FusionCacheBayer::process` (vfunc 3) fires N=1 always on bridge HDR (269 hits at 70mm, all single-source). It is **NOT** the cross-camera merge. The orphaned "where does multi-camera fusion happen" question in `lumen-phoenix-investigation.md` line 1332 is now answered by IRAMP (M1). | LLDB hit counts; `merge_function_reconciliation.md`, `merge_string_inventory.md`. | **Verified** |
| M11 | **`initResAmp` at `libcp+0x3eb3c0` is the src1/src2 IG construction site** (two `_Znwm(0x60)` allocations; inner vtables `0x65f668`/`0x65f6e8`). Word "composite" was retired 2026-04-17 (M13): the IGs wrap the **single anchor camera's** pyramid cache, not multi-source composites. `lt::PipelineCache::initFusion` (`libcp+0x3eb200`) is NOT a producer — its FusionCacheBayer dispatch leaves PC+0x238/+0x248 funcdata pointers identical pre/post. | `anchor_prefusion_and_c6.md`, `runreferencegroupcams_body.md`, `composite_producer.md`. | **Verified** |
| M12 | ~~13 lambdas as N→1 reducer candidates~~ — see **R17**. The 13 `runReferenceGroupCams/runHigherGroupCams` lambda VAs (libcp+0x229ec0..+0x247380) are `lt::CalibDataProcessor` per-camera **calibration setup callbacks**, NOT pixel reducers. Hit counts per render: 1–28 each on a single dispatch thread, vs IRAMP's 300 per-tile fires on 5+ worker threads. | `composite_anchor_n1_reducer.md` (2026-04-17). | **REFUTED** |
| M13 | **There is NO separate anchor pre-fusion N→1 stage.** L16 has exactly ONE multi-camera reduce: IRAMP itself. src1/src2 IGs do NOT wrap pre-fused composites — they are **two ImageGenerator views over the SAME single anchor camera's pyramid cache** (A1 at 28mm, B4 at 70mm). Both wrap data ultimately rooted at `PipelineCache+0x170` (= `lt::ReferenceImageCache`, see I8). The two views differ only in vtable (`0x65f668` vs `0x65f6e8`) controlling sibling pyramid-tier lookup paths. The actual operator() that fires per-tile is at vt[+0x30] = `libcp+0x3ecc10` / `0x3ecd80` (NOT vt[+0x18] which never fires). | `composite_anchor_n1_reducer.md` (2026-04-17). LLDB on L16_02130 28mm + L16_00010 70mm: src1/src2 op vt[+0x30] hit 300/221 = tile count; vt[+0x18] hit 0; lambda hit pattern identical at both zooms; threading split (lambdas single-thread, ops multi-thread) confirms setup-vs-pixel boundary. | **Verified** |
| M14 | **Per-contributor photometric pre-normalization runs INSIDE IRAMP's dispatch chain** at `libcp+0x3eced0`. Operation: `out = sqrt(max(0, in × fov_ratio))` per-channel SIMD (4-wide via `mulps`+`maxps`+`sqrtps`), with alpha lane left as 1.0 (broadcast `{s,s,s,1.0}` constructed via 3× `insertps` at 0x3ecf2d–0x3ecf39, alpha=1.0 from const-pool `0x5a8128`). `fov_ratio` is read from IG+0x10 (= effective-FOV ratio per C17/I9). Dispatch chain: IRAMP body `0x366f1c` → helper `0x374ac0` → vtable[+0x30] indirect → `0x3eced0`. Hit count: **1 per camera per pipeline invocation** on 28mm L16_02130. | `ig_offset10_consumer.md` (2026-04-17). LLDB read watchpoint on closure+0x30 (the FOV scalar written by PropertyAccessor::transform at `0x3eb85b`) fired at runtime VA `0x109066ee9` = file VA `0x3ecee9`, inside function `0x3eced0`. Backtrace verified: frames #2/#3 inside IRAMP body range. | **Verified** |

### 2.2 Per-camera ISP

| # | Finding | Evidence (VA + source) | Confidence |
|---|---|---|---|
| I1 | **`lt::ReferenceImageCache` is a SHARED orchestrator** (1 instance), not 10 per-camera instances. 10 distinct level-0 `Image&` buffers + 4 level-1 buffers at 28mm; same shape at 70mm. Per-camera state is in `r14` `BayerPipelinePayload` register (NOT in dispatcher closure). | LLDB at 70mm L16_03434: 48 `processLevel` hits / 10 worker threads, ALL share `this*` = `0x7f7db5025200`. Closure pointer at `LinearizeAndColorScale 0x340b00` is `0x7fb1b70b7620` for all 31 LIN hits with `[rbx+0x16b0]=[1.0,0,0,1.0]` constant. Source: `refcache_per_camera_isp.md`, **CORRECTED** in `c6_destination_and_depthcache.md` (per-image-buffer not per-physical-camera). | **Verified** |
| I2 | **Per-camera ISP stage order** on bridge HDR (LLDB BP-ordering at 28mm L16_02130): SourceImageCache `ImageWarp<Bicubic,vec4x8ui,LensUndistortCRA>` (CRA undistort, tile-fetch) → STAGE0 `LinearizeAndColorScale<uint16> 0x340b00` (BL subtract + color-scale) → STAGE1 `<float> 0x340bf0` → STAGE2 `ImageCorrectBayerPhaseAR1335 0x340cc0` → STAGE5 `Pipeline::setWhiteBalance::$_5 0x340f70` → **`DemosaickLightV1`** Halide AOT kernel (driver `0x2eb560`) → STAGE6 `Pipeline::setColorCorrection::$_6 0x341040`. RIC emits per-pyramid-level `Image<vec4x32f>` 4-ch f32 + caches `Tile<Vec3<Float16>>` 3-ch f16 packed RGB (6 B/px) via `$_4` lambda for IRAMP. | `refcache_per_camera_isp.md`, `color_pipeline_audit.md`. | **Verified** |
| I3 | **`DemosaickLightV1` fires; `DemosaickLightV2` is DEAD CODE on bridge HDR.** V1 driver `0x2eb560` = 889 hits; V2 driver `0x2eba10` = 0 hits; V2 kernel `0x2f0df0` = 0 hits across full L16_02130 28mm render. Per-camera dispatcher override at `libcp+0x40b370` selects V1. | `color_pipeline_audit.md`. **REFUTES** prior `current-state.md` row 110 ("Profile 0 → light_v2") at the demosaic level. (Tone curve "light_v1" at 0x5e41b4 is a separate naming-collision — see Refuted §3, item R7.) | **Verified** |
| I4 | **Bayer pattern is per-camera, NOT a sensor-wide constant.** `LightHeader.cam[i].field[13]` = `sensor_bayer_red_override` of type `.ltpb.Point2I` per protobuf descriptor at `libcp 0x5c8380`. At L16_02130: A1/A3/A4 = `(1,0)` GRBG; A5 = `(0,1)` GBRG; B1/B5 = `(0,0)` RGGB; B2/B3/B4 = `(1,1)` BGGR. **At least 3 distinct patterns across 10 cameras.** The 4 V1 template variants `<offX,offY>` correspond directly to the 4 Point2I values. **Phoenix MUST dispatch DemosaickLightV1 to the correct phase variant per camera.** `BayerPhaseFix lambda $_76` at `0x34af10` + inner kernel `0x315b30` fired 0 times — confirms per-camera Bayer-phase variation handled by V1's 4-variant dispatch, not by a separate fix-up stage. | `calibration_audit.md`. **REFUTES** prior `current-state.md` row 97 + KMS entry "BGGR for all 16" (was indirectly verified via cv2 demosaic with MAD≈1.7%, but that was a coincidence of choice; correct decode is per-camera). | **Verified** |
| I5 | **Vignetting application: `RemoveVignettingGeneric<vec4x32f, true>` at `libcp 0x108080`** is multiply-by-grid (compensates fall-off). Inner loop at `0x10824e`: `mulps xmm0, xmm3` against bilinearly-interpolated grid value (xmm0 = grid factor broadcast, xmm3 = pixel vec4x32f). Grid values normalized 1.0 (brightest reference) to 3.9 (corners). Per-camera channel-0 min == 1.0 across all 16 cameras in NPZ. **Grid shape: `(camera, channel, x_index_17, y_index_13)`** confirmed by cell-aspect physics (4160/17=244.7 ≈ 3120/13=240). **Per-tile invoke dispatcher at `libcp+0x345f30`** (runtime-confirmed): 348 hits across 10 distinct camera threads (28-41 tiles each) on L16_02130 28mm bridge run. Closure carries uniform global scale `0.7373` at `[closure+0x1618]`; per-camera LUT lookup via BST keyed on lens-type at `[CapturedImage+0x60]`. **A2 IS in the 10-camera vignetting set** — A2/C6 filter at `0x3f6170` (M4) is IRAMP-stage only; upstream ISP stages (vignetting, demosaic) are NOT filtered. | `calibration_audit.md`, `zoom_tier_and_vignetting.md`, `vignetting_runtime_corroboration.md` (2026-04-17). | **Verified** |
| I6 | **CRA undistort is a pure radial geometric warp**, NOT a 4×4 channel mix. `LensUndistortCRA::operator()` at `libcp 0x261940`: 3×3 homography → perspective divide → radial-distance index into 4096-entry float LUT → undistorted (u,v). Applied pre-demosaic at tile-fetch via `ImageWarp<Bicubic,vec4x8ui,LensUndistortCRA>` from `lt::SourceImageCache::ctor::$_0`. | `calibration_audit.md`. **REFUTES** prior `current-state.md` row 104 ("4×4 Bayer channel mixing matrix") — that row conflated CRA with electronic cross-talk. | **Verified** |
| I7 | The 13×17×4×4 `cra_grids` calibration data **DOES exist in LRI** (Block 4 / `f4.f1.f4` = 14,144 B = 3,536 f32 = 221 grid points × 16 mat entries) but is consumed by a **separate stage**, most likely `RemoveCrossTalkGeneric` at `libcp 0x101830-region` (electronic cross-talk correction). Verified center diagonal ≈ identity, corners ~0.95 diag / ~0.02 off-diag. **Phoenix must extract and route correctly: the 4×4 grid feeds RemoveCrossTalkGeneric, not LensUndistortCRA.** | `calibration_audit.md`. | **Verified** |
| I8 | **`PipelineCache+0x170` = `shared_ptr<lt::ReferenceImageCache>` (RIC, anchor camera).** Writer: `libcp+0x3ea83d` (`mov %rax, 0x170(%r14)`). RTTI verified via Itanium-mangled name `N2lt19ReferenceImageCacheE` resolved through vtable+typeinfo walk. Constructor signature includes `lt::CapturedImage::Camera` enum + `std::shared_ptr<lt::StereoAsyncAPI>` → strictly per-camera, stereo-pair model. Pyramid dims at `[RIC+0x40]` = `(4160, 3120)` = AR1335 sensor full-res. Tile pixel format = `lt::Vec3<Float16>` (matches IG consumer side). Halide step name embedded in object (key=0): `"hot_pixel_leakage_removal\0"`. Error strings: `"Cannot init source image caches without a stereo object!"`, `"ReferenceImageCache not implemented for mono camera!"`. Vtable at file offset `0x66b200`. | `sourceimagecache_writer.md` (2026-04-17). | **Verified** |
| I9 | **5-contributor `lt::SourceImageCache` (SIC) objects live in an RB-tree at `RIC+0x30`**, NOT at a flat PC offset. Tree node layout (48 B): `+0x00/+0x08/+0x10/+0x18` = std::map node ptrs; `+0x20` = `cam_id` (int32, key); `+0x28` = `SourceImageCache*` (496 B = 0x1f0). RIC tree fields: `+0x28` sentinel, `+0x30` root, `+0x38` node count. Init function: `libcp+0x3e0330`, called from `initResAmp` at `libcp+0x3eb5c6`. **5 SICs verified** at runtime on L16_02130 28mm for cam_ids `{5,6,7,8,9}` = B1..B5; SIC vtable = `libcp+0x65f490`. IRAMP→SIC access path: IRAMP reads IGs from `PC+0x258..0x268` vector, IGs read pixels from SIC tree via cam_id key. | `sourceimagecache_location.md` (2026-04-17). LLDB BP at `libcp+0x3e0735` ctor-call site captured 5 distinct SIC ptrs with cam_ids 5,6,7,8,9; vtable `0x1092d9490` − base `0x108c7a000` = file offset `0x65f490` exact. | **Verified** |

### 2.3 Color (AWB / CCM / tone curve)

| # | Finding | Evidence (VA + source) | Confidence |
|---|---|---|---|
| C1 | **AWB direction = MULTIPLY BY RECIPROCAL of stored gain.** Color audit BP at AWB stage `Pipeline::setWhiteBalance::$_5 (libcp 0x340f70)` on bridge HDR run of L16_02130 captured `context_ptr[0..3] = (0.5821, 1.0, 0.6294, 0.3630)` at runtime. **0.5821 = 1/1.7178** (matches Block 8 stored R_gain reciprocal); **0.6294 = 1/1.5888** (Block 8 B_gain reciprocal). The kernel multiplies Bayer cells by `1/stored_gain`. | `color_pipeline_audit.md`. **REFUTES** `current-state.md` row 103 ("multiply R-cells × R_gain"). The 2026-04-13 spike-failure inventory's "1/stored_gain" was correct. | **Verified** |
| C2 | LRI Block 8 `f19.f15` stores `[R_gain, 1.0, 1.0, B_gain]` (green unity). At L16_02130, file offset `0x09b189d8`: `{R=1.648295, G1=1.0, G2=1.0, B=1.778951}`. Reciprocals match runtime context to 5+ decimal places. The `divss` is computed **once at pipeline setup**, not per-pixel. | LLDB Session 2 + LRI binary inspect; `color_pipeline_audit.md`, KMS f4284bc2 lineage. | **Verified** |
| C3 | **CCM application runs in CHROMATICITY space**, NOT standard 3×3 RGB→RGB. Per-pixel kernel at `libcp 0x350c56`: `out = M_blend @ (R/G, 1.0, B/G)` with output `(out[0], 1.0, out[2])`. **Green is forcibly written 1.0** via disasm `350cdd: mov dword ptr [r14+0x4], 0x3f800000`. **Phoenix CCM stage must be `(R/G,1,B/G) → 3×3 → (out0, 1.0, out2)`, not RGB→RGB.** | `ccm_factory_to_runtime_transformation.md`. | **Verified** |
| C4 | **CCM lerp is mired-space between two illuminants.** `MatLerpClamped` at `libcp 0xab720`: `M_out = M_B + α·(M_A − M_B)` with `α = clip((1/T − 1/T_B)/(1/T_A − 1/T_B), 0, 1)`. Endpoints loaded by `CCMInterpBetweenCalib` at `libcp 0x350bc0`. NO extrapolation; clamp at endpoints. | `ccm_factory_to_runtime_transformation.md`, KMS f99bc8a7. | **Verified** |
| C5 | **CCM source field is `color_matrix` (Block C field 3), NOT `forward_matrix` (field 2).** Bit-exact match between Block C field 3 and runtime `ctx[+0xdc]` (max_abs_diff = 0.000). The 0.7954 max_abs_diff bug was comparing the wrong field. **Phoenix calibration parser MUST extract field 3** (color_matrix); field 2 (forward_matrix, DNG cam→XYZ_D50) is optional, only useful for DNG export. Both are stored per-camera per-illuminant. | `ccm_factory_to_runtime_transformation.md`. | **Verified** |
| C6 | **Calibration block layout** (verified on L16_02586 + L16_02500 + L16_02130): Block 3 @ offset 162,291,712 (32,832 B, 16 records) = geometric/Bayer; Block 4 @ 162,324,576 (~262,969 B, 16 records) = vignetting + CRA; Block 6 @ 162,589,394 (~35,266 B, 42 records = 14 cams × 3 illuminants) = CCM. **A2 (cam_id 1) and C6 (cam_id 15) NaN entries** — 14 cams × 3 illum total. Field paths: vignetting `rec.f4.f2[ch].f2.f3` = 884 B = 221 f32 → (17,13); CRA `rec.f4.f1.f4` = 14,144 B = 3,536 f32 → (13,17,4,4); CCM `f2.f2` = 45 B (9 fields × 5 B), illuminant_id at `f2.f1`; CCM disambiguation: `n13 ≥ 36` distinguishes Block 6 from Block 3. | KMS 91839eb8, `cal_color_l16_02130.npz`. | **Verified** |
| C7 | **CCT computation = Robertson (1968) isotemperature-line search, NOT gain-ratio interpolation.** `CCTFromChromaticity(Vec2 xy) @ 0xab2e0` runs 30-iteration Robertson search over 31-entry `(u,v,slope)` table at `0x66d410` (bss, runtime-populated). Constants: 175, 0.20525, 0.31647, −0.84901 (uv' transform), 1e6 (mired→K). Input `(x,y)` is `auto_white_balance.neutral_color` protobuf field parsed at `0x13eda0`, NOT computed from AWB gains. **libcp NEVER computes CCT from pixels.** | KMS f99bc8a7. | **Verified** |
| C8 | **Forward direction (CCT→xy) used at render time** via `ChromaticityFromCCT_Tint @ 0xab130` from `setWhiteBalance::$_20 @ 0x342a80`. Walks 28-entry × 16-byte Robertson FORWARD table at `libcp 0x66d420` (different from 0x66d410 reverse table). Reads `(CCT, tint)` from `Pipeline+0x15d0/+0x15d4`. Source of CCT input: `Pipeline::fromProtoConfig @ 0x3184d0` setter at `0x33ead0` from protobuf parser at `0x318847`, gated by `Pipeline[0x1530] == 3` (AWB type=manual_temp). Source fields: `auto_white_balance.neutral_temp` and `.neutral_tint`. **Default CCT = 4300 K (constructor default)** when not set. The previously documented `(CCT−4000)/2500` formula is FABRICATED — refuted. | KMS ed20c8aa. | **Verified** |
| C9 | **CCT effective state on this corpus:** observed `ctx[0x0c]=0.36895, ctx[0x10]=0.21384` at runtime on L16_02130 — these are `(x,y)` chromaticity from Kim's Planckian polynomial for T≈4280K. The earlier "always D65" conclusion (from a 9438-LRI scan finding `neutral_color` never-persisted) was wrong: libcp computes a non-trivial CCT blend even when `neutral_color` is absent, falling back to the 4300K constructor default. | KMS ce2c73e3 (Session 4 misinterpretation) → KMS ed20c8aa (Session 5 correction). | **Verified** |
| C10 | **Tone curve kernel VA = `libcp+0x2d7a30`** = per-tile LUT-apply lambda body, invoked by `LinearTMO::process(Image<vec4x32f>&, Image<vec4x32f>&, ColorSpace&)` driver at `libcp+0x2d7780` (vtable slot 2 of TMO base at `libcp+0x659b30`). Buffer type = `Image<vec4x32f>` = **post-demosaic 4-ch RGBA float32** (16 B/px). Tile-parallel via Halide block dispatcher at `libcp+0x5440`. | KMS ef06bd6a. | **Verified** |
| C11 | **Tone curve pre-shaper (bit-exact, 0x2d7c90..0x2d7f44)** uses constants at `0x5e3140-0x5e3180`: `{0.0025, 0.0075, -0.005, 1.0050251, 100.50251, 1024.0}`. Pre-shaper formula: `u=0` if `x≤0.0025`; `(x−0.0025)²·100.50251` if `0.0025<x<0.0075`; `(x−0.005)·1.0050251` if `x≥0.0075`; `LUT_idx = clip(u·1024, 0, 1023)`. LUT linear interpolation: `movss (rbx,rcx,4); movss 0x4(rbx,rcx,4); subss; mulss; addss`. Alpha preservation via `blendps $0x8, %xmm10`. | KMS ef06bd6a, KMS 9408f4cd. | **Verified** |
| C12 | **EV multiply at tone curve:** `mulps %xmm15, %xmm1` where `xmm15 = exp2f(TMO+0x20)` via `__exp2f` at libsystem stub `0x555f7e`, broadcast-4-lane via `shufps $0`. Source = `Settings.exposure` protobuf → `TMO_obj+0x20`. Default 0.0 → `exp2f(0)=1.0×`. | KMS ef06bd6a. | **Verified** |
| C13 | **Bridge default tone curve = `light_v1`** at `libcp 0x5e41b4` (HIGH confidence). LUT pointer loaded via `movq 0x10(%r14), %rbx` at `0x2d7c94`, written by TMO ctor at `0x2d76b0` from static factory table `libcp+0x659c70[curve_enum*8]`. 4 named curves: `acr 0x5e31b0`, `light_v1 0x5e41b4`, `light_v1_lowlight 0x5e51b8`, `light_v2 0x5e61bc`. Defaults function at `0x3c7860` selects via `isLowLight()` flag. | KMS ef06bd6a, KMS 9408f4cd, KMS e24fa9ce (naming-collision warning). | **Verified** |
| C14 | **Tone curve spatial location: per-camera POST-DEMOSAIC, PRE-IRAMP** (MEDIUM confidence, structural inference): buffer type `Image<vec4x32f>` = post-demosaic per-camera tile, runs between `DemosaickLightV1` and IRAMP merge. `setToneMapping @ libcp+0x319369` is a CONFIG SETTER (reads `tone_mapping.*` protobuf, stores into Pipeline-state offsets), NOT the kernel. | KMS ef06bd6a; structural inference flagged MEDIUM. | **Verified-Structural** |
| C15 | **Tone curve LUT y(0.18) values** (extracted statically from libcp): `acr y(0.18)=0.379, light_v1 y(0.18)=0.203, light_v1_lowlight y(0.18)=0.377, light_v2 y(0.18)=0.201`. Saved to `/Volumes/Dev/lumen-phoenix-scratch/tmo_*.npy` + `tmo_characterization.json`. | KMS 9408f4cd, prior OQ-A close-out. | **Verified** |
| C16 | **Per-camera radiometric weighting is distributed**, not a separate stage: combines (a) AWB pre-demosaic Bayer multiply by `1/stored_gain` (per-channel reciprocal — see C1), (b) CCM 3×3 chromaticity-space mired-space lerp via `MatLerpClamped` (per-camera `color_matrix(A)` and `color_matrix(D65)` endpoints from Block C field 3 — see C3-C5), (c) per-camera vignetting 17×13 LUT multiply (see I5), (d) **per-contributor sqrt-weighted FOV pre-norm at `libcp+0x3eced0`** (M14): `out = sqrt(max(0, in × IG+0x10))` per-channel, applied during IRAMP dispatch. The IG+0x10 hypothesis "geometric warp-scale, not radiometric, never read in IRAMP" was REVISED 2026-04-17 — it IS the effective-FOV ratio (writer `libcp+0xe67c0`) AND it IS read by the IRAMP-dispatched 0x3eced0 (M14, C17). | `per_camera_radiometric_weight.md`, `ig_offset10_scalar.md`, `ig_offset10_consumer.md` (2026-04-17). | **Verified** |
| C17 | **IG+0x10 = effective-FOV ratio per contributor camera.** Writer: `libcp+0xe67c0` called from `PropertyAccessor::transform` at `~libcp+0x3eb836`. Formula: `(ref_dim × ref_scale) / (this_dim × this_scale) × optional_exposure_adjustment`, where camera struct fields `+0x38` (int64 sensor dim) and `+0x40` (float angular scale) are read via accessor functions at `libcp+0xf32d0`/`+0xf32c0`. Captured values: 28mm B-cams ~0.50 (B-cam covers ~half of canvas vs A-anchor); 70mm C-cams ~0.75-0.84 (longer focal → wider canvas swath). src1/src2 IG+0x10 = 0.0 (anchor self-ratio sentinel). Consumed by `0x3eced0` (M14) as the per-contributor multiplier before sqrt. | `ig_offset10_scalar.md` + `ig_offset10_consumer.md` (2026-04-17). Disasm-verified write site + LLDB watchpoint-verified read site. | **Verified** |
| C18 | **Per-tile CCM kernel is `ImageConvertColorSpace::$_0` at `libcp+0xbf4a0`** (vtable slot 6 of `0x6527c0`), dispatched via `ImageConvertColorSpace` at `libcp+0xa9f20` (Halide dispatcher `0x5440`). 370 tile-level hits on L16_02130 28mm. Closure capture[3] at `[closure+0x20]` = CCM matrix ptr. **Only 2 distinct CCM matrices applied across all 370 tile invocations**: Matrix A (70 hits) ≈ D65-adapted XYZ→sRGB; Matrix B (300 hits) = different transform. **Per-camera CCM differentiation is at SETUP, not per-tile.** `CCMInterpBetweenCalib` (`libcp+0x350bc0`) fires 5× (once per active contributing camera) — each call uses per-camera calibration CCM at `[camera_struct+0xa8]` and **all 5 outputs OVERWRITE the same buffer** (rdi `0x304748f58`), consolidating into a single blended matrix that then feeds the per-tile kernel. Helper wrapper at `libcp+0x342a80` is the per-camera loop body. `ImageApplyColorMatrix_3x3_mask` @ `0x300570` and `setColorCorrection_58_Color` @ `0x3466d0` are NOT active on bridge HDR (0 hits). | `imageapplycolormatrix_va.md` (2026-04-17). LLDB Python event-listener probe; 370 ICS hits, 5 CCMInterp hits, 0 hits at refuted candidates. | **Verified** |

### 2.4 Calibration

| # | Finding | Evidence | Confidence |
|---|---|---|---|
| K1 | Black level = 42.0, white level = 1023.0 (sensor AR1335, global). | KMS ac60e123, `current-state.md` row preserved (still valid). | **Verified** |
| K2 | Vignetting grids: 16 cameras × 4 channels × (17,13) f32. Center=1.0 normalized; corners 2.0–3.8×. Two profile families: 1-channel (wide-angle: A1,A2,A5,B3,B4,C2,C3,C5) corners 1.4–3.9, and 4-channel (telephoto-like: A3,A4,B1,B2,B5,C1,C4,C6) corners 1.1–2.0. Field path `rec.f4.f2[ch].f2.f3`. Direction: multiply (compensates fall-off). | KMS 91839eb8, KMS aee26802, `cal_color_l16_02130.npz`. Application VA = `RemoveVignettingGeneric 0x108080`. | **Verified** |
| K3 | CRA grids: 16 cameras × (13,17,4,4) f32. Center mixer diagonal ≈ identity `[1.0, ~1.003, ~0.997, 1.0]`. Field path `rec.f4.f1.f4`. **Consumed by `RemoveCrossTalkGeneric` (electronic cross-talk), NOT by `LensUndistortCRA` (which is pure radial — see I6).** | KMS 91839eb8, `calibration_audit.md`. | **Verified** |
| K4 | CCM matrices: 14 cameras × 3 illuminants × (3,3) f32. **A2 (cam_id 1) and C6 (cam_id 15) absent — NaN entries.** Illuminant order in NPZ: `[0]=TungstenA, [1]=D65, [2]=F11`. Block 6 detection: `n13≥36` (distinguishes from Block 3). A1 D65 example: `[[0.900,0.132,−0.067],[0.310,1.074,−0.384],[−0.057,−0.430,1.313]]`. | KMS 91839eb8. | **Verified** |
| K5 | **Per-LRI calibration parser is a REQUIRED Phoenix pipeline stage.** Each LRI is self-contained; calibration is per-device factory data baked into every LRI. Phoenix MUST parse Blocks 3/4/6/8 from each input LRI at render time. The `cal_color_l16_02130.npz` in handoff is a REFERENCE EXTRACT of one device, NOT a runtime input. | KMS 5e9c43f8, KMS 5e7bd5fe (Rule #0). | **Verified** |

### 2.5 Firing rules / camera config

| # | Finding | Evidence | Confidence |
|---|---|---|---|
| F1 | **Empirical firing scan across 9390 LRIs (full archive):** 28mm = 2424 LRIs, dominant 5A+5B (10 cams) at 98.5%. 35mm = 3240 LRIs, dominant 5A+5B (10 cams) at 99.5% — **IDENTICAL firing set to 28mm**. 70mm = 1915 LRIs, dominant 5B+6C (11 cams) at 74.2% (98.4% by raw `zoom_val ∈ [70,79]`). 150mm = 1797 LRIs, dominant 5B+6C (11 cams) at 96.0%. **Sharp empirical transition at `zoom_val=70`**: all `<70` → 5A+5B; all `≥70` → 5B+6C. **Across the entire archive, ZERO LRIs fire C cameras alone at any zoom** — every B+C capture also fires the full 5B set. | `lightheader_camera_scan.md`, `lightheader_scan_raw.csv` (9390 rows). DB integrated into `lri_catalog.db` with new columns `zoom_val`, `zoom_class`, `n_image_chunks`, `fired_count`, `fired_ids`, `fired_names`. **REFUTES** two `current-state.md` "Verified" claims — see R3, R4. | **Verified** |
| F2 | **Only 2 firing modes exist**: (wide=5A+5B) and (tele=5B+6C). B is constant across zoom modes; the partner group changes (A at wide, C at tele). **Phoenix needs ONE merge function parameterized by `(anchor_group, partner_group)`**, not three per-zoom merge implementations. | `lightheader_camera_scan.md`. Direct visual confirmation in `puzzle_pieces.md` (B4 = canvas anchor at 70mm; C5/C1 = zoomed sub-region inserts). | **Verified** |
| F3 | **C6 IS active hardware-wise at 70mm and 150mm.** L16_03434 (zoom=70): C6 pixel data 99.83% non-zero across 4×1MB samples (file offset 162,291,720, 16,228,344 B). L16_02285 (zoom≈149): 99.82% non-zero. Geometric cal block (32,832 B, 16 records) covers all 16 cameras INCLUDING C6 in every LRI. **C6's exclusion from CCM block (14 cam) is a factory unit-cal decision, NOT hardware absence.** C6 is then dropped at IRAMP-side dispatcher (M4) because no CCM map entry exists. | `c6_verification.md`, `c6_destination_and_depthcache.md`. | **Verified** |
| F4 | **Camera ID mapping** (varint in `LightHeader.field_12[*].field_2`): A1=0, A2=1, A3=2, A4=3, A5=4, B1=5, B2=6, B3=7, B4=8, B5=9, C1=10, C2=11, C3=12, C4=13, C5=14, C6=15. Per-camera record fields: `f9.f4`=bytes_per_row (5200 for W=4160 PACKED_10BPP), `f9.f5`=data_offset within chunk, `f13`=`sensor_bayer_red_override` Point2I (see I4). | KMS ac60e123, `calibration_audit.md`. | **Verified** |
| F5 | Movable mirror key finding: each movable camera has exactly ONE `R_fold` — a fixed pointing direction. The 4 encoder configs per camera control **focal position (zoom level) only**, not pointing direction. Azimuth is permanently fixed at factory calibration. Config selection: `argmin(|encoder − nominal[i]|)`. (Config 2/3 do NOT have shared "wide park"/"tele park" semantics — see R5.) | Closed OQ-B 2026-04-12, batch-verified across 10 files per zoom level. | **Verified** |

### 2.6 Depth

| # | Finding | Evidence | Confidence |
|---|---|---|---|
| D1 | **REVISED-AGAIN 2026-04-18 — depth FIRES on bridge profile=3 (any fmt).** Earlier "0 hits" findings were a wrong-VA artifact: probes targeted `shared_ptr_emplace<DepthCache>` wrapper at libcp+0x3c2160. The verification agent's "DepthCache fires 1×" claim was ALSO mislabeled — `libcp+0x3eaf00` is actually a 4-byte thunk to **PipelineCache** ctor at libcp+0x3ea7d0 (PipelineCache fires 1× per render unconditionally; not a depth indicator). The **real** `lt::DepthCache::C2` ctor body is at **`libcp+0x3d8780`** (C1 thunk: `libcp+0x3d8b70`) per the 28mm depth populator agent's verified disasm. **True depth pipeline indicators on bridge profile=3**: `StereoAsyncAPI::C1` ctor (libcp+0x3f46d0) fires 1×, `lt::Triangulator::refine3dPoints` (libcp+0x20ca00) fires **10×**. Verified across 4 scenarios (with/without prior `--depth` flag, with/without `.lris`) — all identical. **What WAS verified zero**: `CIAPI::DepthEditor::*` 14-method GUI-edit surface (0 hits — that's the depth-EDIT API, not depth-COMPUTE). The original D1 framing "depth GUI only" was wrong. | `depth_unlock_verification.md`, `profile2_camera_characterization.md` 2026-04-18, 28mm depth populator agent VA correction. Refutes prior `depth_editor_and_iramp_depth.md` D1 framing. | **Verified (corrected ×2)** |
| D2 | **`ImageDecodeBayerJPEG` is in libcp.so (Android), NOT in liblricompression.** Phase 2 RE redirect: the previously assumed "decompress lives in liblricompression" was wrong — investigation.md line 12 reveals it's in libcp. liblricompression's `libceres` link is ornamental (not used). | `depth_editor_and_iramp_depth.md`, `LIBRARY_INVENTORY.md` cross-ref, `backward_audit_2026-04-16.md`. | **Verified** |
| D3 | **Ceres usage characterized statically (still valid, from OQ-D 2026-04-13):** 3 distinct `Problem` lifecycles with **5 (not 18)** `AutoDiffCostFunction` types: `LabCostFunction<25,9>` (Pass A, factory color cal, skip at runtime), `CameraProjection<2,1,1,2,3,3,3>` + `EntrancePupilCost<3,3,3>` + `IntrinsicsCost<3,1,2>` (Pass B, LightBA full bundle adjustment, factory cal, skip at runtime — Phoenix uses baked factory intrinsics), `ReProjectionCost<2,1>` (Pass C = `lt::Triangulator::refine3dPoints` at `0x20d1ac` — per-point bounded 1-DOF Cauchy-weighted depth refinement, scale `a=1.0` at `libcp 0x5c3580`). Reimplementable with `scipy.optimize.least_squares(loss='cauchy', f_scale=1.0, bounds=(lo,hi))`. | `ceres_analysis.md`, KMS a2cc8b7b. | **Verified** |
| D4 | **Two-gate filter at SIC init (libcp+0x3e0330) prevents `SourceImageCache` creation for cameras IRAMP will not consume.** Gate 1 (`libcp+0x3e0412`): `cmp byte ptr [rax+0x30], 0; je 0x3e0880` skips SIC if camera_struct+0x30 active/CCM flag = 0 (no CCM cal for this zoom). Gate 2 (`libcp+0x3e044a/0x3e0450`): class-match filter skips cameras whose class equals the anchor class (class mapper at `libcp+0xf6c60`: `0xfc00`→C, `0x001f`→A, else B). Per-zoom result: 28mm SIC tree = {B1-B5}; 35mm SIC tree = {A1+B1-B5}; 70mm/150mm SIC tree = {C1-C5}. Cameras failing either gate still go through per-camera ISP and have RIC level-0 buffers populated, but cannot be consumed via the SIC RB-tree. **A cameras are not fired at all at 70mm/150mm** (sensor activation, not just filtering). | `depth_fate_cross_zoom.md` (synthesis of 4 parallel probes 2026-04-18). | **Verified** |
| D5 | **NARROW finding (do NOT extrapolate to "orphaned"):** Across all 4 zoom tiers on bridge HDR, the sole caller of SIC `vtable[+0x30]` body (`libcp+0x3ecc10`/`0x3ecd80`) and per-contributor prenorm body (`libcp+0x3eced0`) is `libcp+0x374cf3` (IRAMP dispatch helper, child of `0x374ac0`). No other caller observed AT THESE TWO PROBE POINTS. **Scope limitation (critical)**: the probes did NOT instrument (a) other SIC vtable slots, (b) direct (non-vtable) reads of RIC level-0 image buffers, (c) the AWB path, (d) HDR exposure-bracket fusion, (e) any noise/SNR averaging stage, (f) the Lumen.app GUI path. Light Inc shipped 16 cameras and marketed all 16 as contributing to image quality — dropped cams' RIC level-0 buffers must have a consumer somewhere in the pipeline. **Q-DROPPED-CONSUMER (open):** find where dropped cams' RIC level-0 buffers are actually read. Method: hardware watchpoint on the RIC level-0 buffer pointer for a known dropped cam (e.g., A2 at 28mm) — log every PC that touches it during a full render. **Phoenix MUST NOT skip per-camera ISP for dropped cams until Q-DROPPED-CONSUMER is closed.** | `depth_fate_cross_zoom.md`, agent reports 2026-04-18, Rich correction 2026-04-18. | **Verified scope-bound; conclusion deliberately narrowed** |
| D6 | **Bridge `lri_process` is a CLAUDE-WRITTEN test harness, NOT Lumen.app.** It calls `Renderer::render` + `writeImage` only — a SUBSET of libcp's invocation surface. Anything libcp can do that's not reachable from those entry points has been invisible to LLDB probes. The bridge's color-output validity (L2: MAD 0.067% vs Lumen GUI) only validates color, not depth. The "DepthCache 0 hits on bridge" finding (D1) was correct but scope-limited to bridge's invocation pattern, NOT proof that depth code is dead. The depth code IS in libcp; bridge just never reached it. | `lumen_app_vs_bridge_delta.md` 2026-04-18 (54-symbol delta between Lumen.app and bridge libcp imports). Rich correction 2026-04-18. | **Verified** |
| D7 | **REVISED-AGAIN 2026-04-18 — depth gate is profile-driven + image-storage-byte check.** The actual gate is at libcp+0x3b2fa3: `[imageStorageObj+0] & 0xf == 0x3` via `call libcp+0x40b010`. Profile=3 (DESKTOP) sets the byte to 0x3 → depth fires. Profile=2 (CAMERA) does NOT set 0x3 → depth skipped (StereoAsyncAPI 0 hits, Triangulator 0 hits — verified). The `RendererPrivate+0x774` field (setMode write target) is read for a different render-property update at libcp+0x3b0874, NOT depth gating. **Real depth pipeline call chain (verified live, bridge profile=3)**: `RendererPrivate` vtable slot 20 @ libcp+0x3b1d20 → gate @ libcp+0x3b2fa3 → `StereoAsyncAPI` C1 ctor @ libcp+0x3f46d0 (call site libcp+0x3b3011) → C2 ctor @ libcp+0x3f2c40 → `DepthCache` ctor @ **libcp+0x3d8780** (C1 thunk libcp+0x3d8b70) → `Triangulator::refine3dPoints` @ libcp+0x20ca00 fires **10× per render**. PipelineCache (libcp+0x3ea7d0, thunk at 0x3eaf00) fires 1× per render unconditionally — NOT a depth indicator. **SGM as the algorithm = REFUTED-AS-DISPATCH 2026-04-18.** String at libcp+0x632901 is an ERROR GUARD inside function libcp+0x267e80: throws `runtime_error` if SGM stereo pair is added after upsampled depth. Function 0x267e80 fires 0× on bridge profile=3. The 7 "state machine handlers" at libcp+0x229d80..0x22aee0 are 4-instruction push/pop/ret STUBS (dead vtable entries). **Real depth dispatch chain (verified)**: StereoAsyncAPI C2 → libcp+0x3d01b0 → Halide AOT tile dispatcher at libcp+0x5440 with closure vtable at libcp+0x66a618 ("stereo cost evaluator"). **Algorithm class is in the Halide-generated machine code body — NO named C++ matcher class exists in libcp strings** (zero hits for PatchMatch/Census/SGBM/NCC/GraphCut/PMVS/planeSweep). Identifying the algorithm requires disassembling the Halide kernel body (out of scope). **Triangulator hit semantics (corrected)**: outer entry libcp+0x20ca00 fires 1× (28mm) or 2× (70mm parallel threads), NOT 10×. Inner loop libcp+0x20cab0 fires 4-5× = partner-camera count + thread duplicates. **Verified 5A/5B parallax structure (matches Light's tech doc)**: 28mm pair vector = {A2,A3,A4,A5} with A1 anchor (excluded from vector); 70mm = {B1,B2,B3,B5} with B4 anchor. Cross-zoom rule: depth uses 5 same-row cams (anchor + 4 partners). DepthCache `[+0x90]=0xa` is max-pair CAPACITY (not active count). | `depth_unlock_verification.md`, `profile2_camera_characterization.md` 2026-04-18, 28mm depth populator agent VAs. | **Verified live; algorithm decode pending** |
| D8 | **Cam_id field offset = `[per_cam+0x60]` (uint32).** Verified via getter `libcp+0xf2720` (`movl 0x60(%rdi), %eax; retq`) called from a "find-by-cam_id" lookup function at `libcp+0xdf8d0`. Used across 7+ call sites. This was the missing piece for cross-zoom CCMInterp cam_id attribution at libcp+0x350bc0. | `q10_ccminterp_70mm_v6_live.log` 2026-04-18, `libcp_disasm_intel.txt` lines 219934-219968. | **Verified** |
| D9 | **`libcp+0x30b770` = Path A cost functor builder.** This 3-stage setup function (a) allocates output image buffer via `libcp+0xf540`, (b) selects one of 4 cost function pointers via a 2-bit dispatch at `0x30b801` (`flag_a=[rdx]`, `flag_b=[rdx+4]`), (c) builds a 0x38-byte closure (vtable `0x65aca0`, fields: out-buf, image-desc, cost-fn-ptr, 4th-arg, 2 float params), (d) calls `libcp+0x5440` (Halide AOT tile dispatcher, per D7) to execute the closure across all tiles. Has **3 call sites** in anonymous `__text`: `libcp+0x1ac1ac` (inside `0x1ac010`), `libcp+0x1b934c` (inside `0x1b92d0`), `libcp+0x343ef8` (inside `0x3403f0`). Static analysis only. | `path_a_call_chain_round3.md` 2026-04-19. callgraph DB query + disasm read. | **Static-verified** |
| D10 | **Path A 2×2 cost-variant dispatch at `libcp+0x30b801`.** Flags from `[rdx]`/`[rdx+4]` (both binary 0/1; validation: OR≥2 → bail). Flag source at call site `0x343ef8`: `0xf2750([rbx+8])` = `[rbx+8]+0x58` (field-accessor getter). Dispatch table: (flag_b=0,flag_a=0)→`0x30b9f0` (confirmed "Laplacian SAD + chromatic L2"); (0,1)→`0x30dcc0`; (1,0)→`0x30ff60`; (1,1)→`0x3121f0`. All 4 variants share identical L2-normalize prologue: load 3 per-channel scale factors from `[r9]`/`[r9+8]`, compute `1.0/each`, compute `1.0/(xmm1-xmm0)` (inverse range), 3D `sqrtss` normalization, per-channel `mulss` with rodata constants `0x5f3e20`/`0x5e7420`. Variants diverge beyond line ~60 of body. Semantic meaning of flags (projection model? channel count?) not decoded. | `path_a_call_chain_round3.md` 2026-04-19. | **Static-verified; flag semantics pending** |
| D11 | **Path A upstream callers via static call-chain trace (2 confirmed chains).** Chain 1: ISP Pipeline Renderer/Configurator (`libcp+0x406960`, string evidence: `light_v1/v2`, `demosaicking.type`, `collapse2/4/8`, `tone_mapping.*`, `denoising.*`, `lens_shading.*`, `pipeline.parameter_scale`, `Invalid Renderer profile!`) → `0x1ab2d0` → `0x1ac010` → (at `0x1ac1ac`) → `0x30b770`. Chain 2: Demosaicking (`libcp+0x27b7a0`, strings: `demosaicking.type`, `collapse2`, `expect an empty reference image.`) → (at `0x27daf0`) → `0x31b470` → `0x3403f0` → (at `0x343ef8`) → `0x30b770`. Output of Chain 2 stored at `[rbx+0x100]` (tile rect) in per-tile object; clipped against `[rbx+0x30..0x3c]`; metadata at `[rbx+0x110]` (width), `[rbx+0x114]` (height), `[rbx+0x120]` (pixel ptr). Scope: static disasm only; not LLDB-live; function identities are anonymous (no named C++ evidence). | `path_a_call_chain_round3.md` 2026-04-19. | **Static-verified (not LLDB-live)** |

### 2.7 Outliers / variant formats

| # | Finding | Evidence | Confidence |
|---|---|---|---|
| O1 | **~180 LRIs (1.8% of archive) are a distinct file format**, NOT firmware bugs. Empirical signature: LELR offset-6 byte = `0x10` (10/10 sampled, all bridge-rejected with "Corrupted record#1/2 header"). NOT BJPG. Patterns: `B1\|B2\|B3\|B4\|B5\|C2\|C5` (86 LRIs, 7-cam tele variant), `A1\|A5\|B2\|B4\|B5` (59 LRIs, 5-cam variant), `B2\|B4\|B5\|C5` (23 LRIs, 4-cam tele variant). Persist 2017-12-09 → 2021-03-06; temporally interleaved with canonical captures (rules out deprecated-firmware explanation). B4+B2+B5 present in EVERY outlier pattern (the B-tele core). The 4-cam pattern's set IS exactly chunk-1 of the 7-cam pattern (shared firmware mode). | `zoom_35mm_and_outliers.md`. **Phoenix can ignore variant-0x10 LRIs (1.8% niche) per Rich's outlier-deprioritization rule, OR add a separate parser later.** | **Verified** |
| O2 | **244-file BJPG (Burst JPEG) cluster is a SEPARATE phenomenon from variant-0x10.** LELR data blocks contain `BJPG` magic at byte +32. Structure: 1,576-byte index + 80 concatenated JFIF JPEGs (variable-length, quality 68–84, tile 1024×512). Confirmed on L16_01951.lri. ~302 files post-2018-06-26, firmware v0.2+. **Phoenix should skip BJPG files for 2018-normal decode path; decompress via libjpeg per camera if needed.** | Closed OQ-E 2026-04-13. KMS lineage in pipeline-facts. | **Verified** |
| O3 | **L16_01853 (zoom=96) operates in a special 4-frames-per-camera mode** with `bpr=0` and ~5.4 MB per-frame stride. Distinct from single-frame high-zoom. | KMS ce238bd9. | **Verified** |
| O4 | UNKNOWN LRI format (transitional firmware 0.1.x): main cluster (515 files, 2018-03-30 → 2018-06-26): stride = 10,485,764 B/camera, 8 cameras per chunk, W=4160, bpr=5200, H_int=2016 rows. Same 10-bit MIPI packing as 2018-normal. 3-LELR-chunk structure. CORRECTION to prior claim: 2018-normal H_int = 1950 (not 2473). | Closed OQ-E, `oqe_unknown_format.md`. | **Verified** |

### 2.8 Zoom / crop / canvas

| # | Finding | Evidence | Confidence |
|---|---|---|---|
| Z1 | **Two-tier focal-length canvas architecture.** Reference focal length is NOT a fixed 28mm — it's a zoom-mode-tier table read at `libcp+0xe7020` via `*(int*)0x44(image)` enum cases 0/1/2. **Tier 0 (28mm-anchor):** ref=28mm. Used at 28mm (no crop, RectF=(0,0,1,1), full 10432×7824 canvas, 300 tiles 20×15) and 35mm (RectF=(0.0957, 0.1045, 0.8957, 0.9045), **8345×6259 internal canvas**, 234 tiles). **Tier 1 (70mm-anchor):** ref=70mm. Used at 70mm (no crop, RectF=(0,0,1,1), ~8848×6624 base canvas, 221 tiles 17×13) and 150mm (RectF=(0.2668, 0.2673, 0.7332, 0.7327), **4865×3641 internal canvas**, 63 tiles 9×7 — ratio 70/150=0.466). | `35mm_renderer_mechanism.md`, `tone_curve_location_and_zoom_crop.md`, `zoom_tier_and_vignetting.md`. | **Verified** |
| Z2 | **Focal-length crop computer at `libcp+0xe6d90`** reads `image_focal_length` from `lcp::Image at 0x40(rsi)`, divides reference focal by image focal, writes centered normalized RectF to renderer's internal Transform. `Renderer::render` invoked with same `ROI=(0,0,65536,65536)` at all focal lengths — crop lives on renderer's internal Transform, NOT in ROI argument. | `35mm_renderer_mechanism.md`. | **Verified** |
| Z3 | IRAMP iteration count tracks tile-grid dimensions (NOT a simple `(28/focal)²` formula): 28mm=300, 35mm=234, 70mm=221, 150mm=63. (35mm/28mm ratio 234/300 = 0.78 ≈ (28/35)² = 0.64 from progress callbacks 193/301 = 0.6412.) | LLDB hit counts. | **Verified** |
| Z4 | **Bridge `lri_process` upsamples cropped FOV to hardcoded `Point<int> outsize = {10432, 7824}` (lri_process.cpp:640).** Lumen GUI presumably calls `writeImage` with focal-aware Point<int> and gets the correct cropped resolution. **Phoenix output should match internal cropped resolution OR provide focal-aware outsize control.** | `35mm_renderer_mechanism.md`. | **Verified** |
| Z5 | **35mm = 28mm pipeline + crop** (no separate synthesis pass). No 35mm-specific functions, symbols, or strings exist in libcp. B cameras at 35mm use encoder config 2 (same as 28mm wide park). | F1 + Z1 + libcp string scan. | **Verified** |

### 2.9 Container / library inventory (still-valid carryover)

| # | Finding | Evidence | Confidence |
|---|---|---|---|
| L1 | Canvas geometry: 10432×7824 output, fx=8457.2px, hFOV=63.33°, vFOV=49.65°. (Pre-crop base; see Z1.) | OQ-closed 2026-04-12. | **Verified** |
| L2 | Bridge `lri_process.cpp` reproduces ground truth at 10432×7824 with **MAD = 0.067% vs Lumen GUI**. Bridge IS valid ground-truth source. | OQ-closed; `current-state.md` rows preserved. | **Verified** |
| L3 | LRI formats: 2017-era, 2018-normal, WDR — all three confirmed. 2018-normal: stride 10,616,832; W=4160; H=3120 (full sensor). | OQ-E close-out. | **Verified** |
| L4 | All 16 ISP stage names confirmed via C++ RTTI; ISP two-tier: base pipeline (bridge-accessible) vs GUI-only editing pipeline. | `current-state.md` rows preserved (still valid). | **Verified** |
| L5 | Stages NOT in RIC at bridge HDR (verified 0 hits): `RemoveCrossTalkGeneric`, lens shading, hot-pixel — only fire under specific tunings/profiles (GUI editing pipeline, not bridge). **REFUTES** prior `current-state.md` claims that put these on the bridge HDR path. | `refcache_per_camera_isp.md`. | **Verified** |
| L6 | Phase B ("L16 mono-path final render") is a parallel sibling pipeline producing grayscale TIFF (`MonoFusion::initialize`, `MonoMerge` at `0x3596e0` reading 2 f32 canvases, writing uint16). **Phoenix should skip Phase B entirely** — install only lambda_0/1/2/5/6 (color path), skip `$_7`/`$_8` from PipelineC1 defaults. Phoenix does not emit mono. | KMS 6e7523df. | **Verified** |
| L7 | Public API (411 symbols) + `CIAPI::DepthEditor` 11-method surface in `LIBRARY_INVENTORY.md` is **STILL VALID** (no refutations). Useful for future ctypes/dlopen wrappers, but Phoenix is clean-room (Rule #0) so this is reference-only. | `LIBRARY_INVENTORY.md`. | **Verified** |

---

## 3. Refuted Claims

Each row quotes the wrong claim, then cites the refutation.

| # | Old claim (where) | Refutation evidence (VA + source) |
|---|---|---|
| R1 | `current-state.md` row 102: "**Cross-camera fusion operator = ≤3-tap weighted aggregation with depth-aware warp.** Inner kernel at `0x36fd30` has 3 distinct source-base registers (rbx/rsi/r9), Catmull-Rom cubic weight LUT built at 0x36f890–0x36fa9d…" | **REFUTED.** `0x36fd30` is a uint8 luma-grid generator that bypasses the IRAMP canvas and feeds `PyramidAlignment` + `GetSkippingMaskGrid`, NOT a cross-camera reducer. Real cross-camera merge is IRAMP at `0x365960` (setup) + `0x3661b0..0x36ae41` (Halide body). Smoking-gun N→1 accumulator at `0x369fa1` (M1, M7). Source: `iramp_kernel_body.md`, `sub_stages_36cde0_36e530_36f800.md`. |
| R2 | `current-state.md` row 86: "**Fusion entry point: FusionCacheBayer::vfunc[3], tile-parallel.**" | **REFUTED.** FCB::vfunc[3] fires N=1 always on bridge HDR (269 hits at 70mm, all single-source). FCB is per-source, not the cross-camera merge (M10). The orphaned "where does upstream multi-camera fusion happen" question in `lumen-phoenix-investigation.md` line 1332 is now answered by IRAMP. |
| R3 | `current-state.md` row 82: "**At 150mm: 6C cameras fire only.**" | **REFUTED.** 9390-LRI archive scan: 96.0% of 150mm captures fire 5B+6C (11 cams). ZERO captures fire C cameras alone at any zoom. F1, `lightheader_camera_scan.md`. |
| R4 | `current-state.md` row 45-46: "**35mm: 5B + computational synthesis.**" | **REFUTED.** 35mm fires 5A+5B identical to 28mm (99.5%). 35mm-specific behavior is downstream of capture: 28mm pipeline + canvas center-crop (Z1, Z5, F1). |
| R5 | Spike-failure inventory KMS 8ddbe013 cites prior claim: "**B camera Config 2 = wide park, Config 3 = tele park.**" | **REFUTED.** Configs are per-camera focus brackets with NO shared azimuth meaning. Movable cameras have one fixed `R_fold` (azimuth permanently set at factory cal); encoder configs control focal position only (F5). Applying assumed shared semantics caused 0% B coverage in early spikes. |
| R6 | Spike-failure inventory cites prior claim: "**Movable camera set = `{B1,B2,B3,B5,C1,C4,C5,C6}`.**" | **REFUTED.** Correct set: `{B1,B2,B3,B5,C1,C2,C3,C4}` (KMS 8ddbe013). Two cameras swapped. |
| R7 | `current-state.md` row 110: "**Profile 0 (bridge default) → light_v2.**" | **REFUTED at the demosaic level.** `DemosaickLightV1` driver `0x2eb560` = 889 hits; V2 driver `0x2eba10` = 0 hits; V2 kernel `0x2f0df0` = 0 hits on bridge HDR. Per-camera dispatcher override at `libcp+0x40b370` selects V1 (I3, `color_pipeline_audit.md`). NOTE: tone curve "light_v1" at LUT `0x5e41b4` is a SEPARATE naming-collision (KMS e24fa9ce); both default to V1-named entities but they are unrelated systems. |
| R8 | `current-state.md` row 103: "**Apply R_gain to R-cells and B_gain to B-cells in the Bayer array.**" | **REFUTED.** Direction is RECIPROCAL. Runtime `context_ptr[0..2] = (1/R_gain, 1.0, 1/B_gain)` exactly matches Block 8 stored gains' reciprocals to 5+ decimals. Multiply Bayer cells by `1/stored_gain`. C1, C2, `color_pipeline_audit.md`. |
| R9 | `current-state.md` row 104: "**CRA correction algorithm = spatially-varying 4×4 Bayer channel mixing matrix.**" | **REFUTED.** `LensUndistortCRA::operator()` at `libcp 0x261940` is a pure radial geometric warp (3×3 homography → perspective divide → 4096-LUT). The 13×17×4×4 cra_grids data exists and IS used, but by `RemoveCrossTalkGeneric` (electronic cross-talk), a DIFFERENT stage. I6, I7, `calibration_audit.md`. |
| R10 | `current-state.md` row 97: "**Bayer pattern: BGGR (value 3) for all 16 cameras — sensor-wide constant.**" | **REFUTED.** Per-camera; at L16_02130 there are at least 3 distinct patterns across 10 cameras (A1/A3/A4=GRBG, A5=GBRG, B1/B5=RGGB, B2/B3/B4=BGGR). Source = `LightHeader.cam[i].field[13]` Point2I `sensor_bayer_red_override`. The cv2 BGGR demosaic giving MAD≈1.7% was a coincidence (one of the patterns in the camera set is BGGR). I4, `calibration_audit.md`. |
| R11 | `current-state.md` row 105: "**CCM illuminant interpolation formula confirmed: w_D65=(CCT−4000)/2500, w_F11=1−w_D65 for 4000K<CCT<6500K.**" | **REFUTED — fabricated.** Real implementation: mired-space lerp via `MatLerpClamped` (C4) between TungstenA (~2855K) and D65 (~6502K) endpoints; F11 illuminant exists in cal block but is not blended pairwise with that formula. Default CCT = 4300K constructor default when not set (KMS ed20c8aa). C7, C8, C9, `ccm_factory_to_runtime_transformation.md`. |
| R12 | Earlier draft claim: "**`PipelineCache+0x8` = composite buffer pointer that initResAmp wraps into IRAMP src1/src2 anchor IGs.**" (`anchor_prefusion_and_c6.md` 2026-04-16) | **REFUTED 2026-04-17.** PC+0x8 is the begin-pointer of an embedded `std::vector<Vec2<int32>>` containing 5 packed (W,H) pairs = the 5-level pyramid-dims table. Written ONCE at PipelineCache construction (`std::vector::operator=` at `libcp+0x292070` from sub-init `0x3cfd80`), never mutated thereafter. Just metadata. The actual composite anchor content lives in src1/src2 funcdata (heap-allocated, pointer at `PipelineCache+0x238`/`+0x248`) — producer pending (Open Q-1). `composite_producer.md`. |
| R13 | Earlier RIC framing: "**RIC fires on EXACTLY 10 worker threads = 10 cameras (48 BP hits ≈ 5 pyramid levels per camera).**" | **REFUTED-AS-MISLEADING.** RIC is a SHARED orchestrator (1 instance, 10 image-buffers + 4 level-1). Per-camera state lives in `r14` BayerPipelinePayload register, NOT in 10 separate RIC instances. I1, KMS 5b87df33, `c6_destination_and_depthcache.md`. |
| R14 | RefCache agent claim: "**STAGE6 = per-camera CCM matmul at libcp 0x341040.**" | **REFUTED.** Empirically: 418 hits / 10 RIC threads / **only 2 distinct lambda funcdata pointers + 2 distinct payloads** (NOT 10). Payload+0x16b0 = `(1.0, 0, 1, 0.5)` and `(0.9, 0.5, 1, 1)` — these are not 3×3 CCMs. Slot 16 B too small for 3×3 CCM. The actual per-camera CCM matmul site is OPEN (likely `lt::CCMInterpBetweenCalib 0x350bc0` / chromaticity kernel `0x350c56` — those are downstream of dispatcher 0x3f6170 lookup). `a2_destination.md`, Open Q-3. |
| R15 | `current-state.md` "all 16 ISP stage names confirmed via C++ RTTI" then footnote: "Stage 7 LensShading hot-pixel cross-talk fire on bridge." | **REFUTED-IN-PART.** `RemoveCrossTalkGeneric`, lens shading, hot-pixel ISP stages fire 0 times on bridge HDR. They only fire in GUI editing-pipeline tunings. The 16-stage RTTI list is correct; their bridge-activation status was wrong. L5, `refcache_per_camera_isp.md`. |
| R16 | Truth doc M12 (prior version): "13 lambda VAs `runReferenceGroupCams::$_0..$_6` + `runHigherGroupCams::$_7..$_12` are the strongest candidates for the actual N→1 anchor pre-fusion reducer." | **REFUTED 2026-04-17.** All 13 lambdas fire only 1–28 times per render on a single dispatch thread (sequential, identical pattern at 28mm vs 70mm), while per-tile pipeline (IRAMP setup, src1/src2 op, post-reshape) fires 300×/221× across 5 worker threads. Lambdas execute at pipeline-setup time, not per-tile, and cannot be the N→1 pixel reducer. They are `lt::CalibDataProcessor` per-camera calibration setup callbacks (warp/ROI/cam-id RB-tree builders), confirmed by static body inspection ($_0 + $_12) showing int-only / RB-tree-walking bodies with no SIMD pixel arithmetic. `composite_anchor_n1_reducer.md`. |
| R17 | Q1 hypothesis: "The composite anchor wrappers src1/src2 carry pre-fused multi-camera content; some upstream reducer produces it." | **REFUTED 2026-04-17.** src1/src2 IGs both wrap the SAME single anchor camera's pyramid cache (A1 at 28mm, B4 at 70mm), rooted at `PipelineCache+0x170` = `lt::ReferenceImageCache` (M13, I8). There is no upstream multi-camera reduce. The 5 contributor cameras flow through the parallel `lt::SourceImageCache` (SIC) tree at `RIC+0x30` (I9) and feed IRAMP separately. L16 has exactly ONE multi-camera reduce: IRAMP itself. `composite_anchor_n1_reducer.md`, `sourceimagecache_writer.md`. |
| R18 | Old candidate VA for per-pixel CCM matmul: "`ImageApplyColorMatrix_3x3_mask` at `libcp+0x300570`" (RTTI-based hypothesis). | **REFUTED 2026-04-17.** `0x300570` and `0x304170` (nomask variant) both fire 0 times across full L16_02130 28mm bridge HDR render. Active per-tile CCM kernel is `ImageConvertColorSpace::$_0` at `libcp+0xbf4a0` (370 hits), and per-camera CCM differentiation happens once at SETUP via `CCMInterpBetweenCalib` (5 hits, blended into single buffer) — see C18. `imageapplycolormatrix_va.md`. |
| R19 | C16 (prior version): "Per-IG +0x10 float scalar is per-camera GEOMETRIC warp-scale (~0.5 = L0→L1 downsample), not radiometric — never read inside IRAMP body." | **REVISED 2026-04-17.** IG+0x10 IS the effective-FOV ratio (writer `libcp+0xe67c0`, formula `(ref_dim×ref_scale)/(this_dim×this_scale)×optional_exposure`), AND it IS read by `libcp+0x3eced0` which is dispatched from IRAMP body (`0x366f1c → 0x374ac0 → vt[+0x30] → 0x3eced0`). Operation: `out = sqrt(max(0, in × IG+0x10))` per-channel. The "never read in IRAMP body" claim was scope-limited to the inline 0x3661b0..0x36ae41 range and missed the dispatched indirect call. C16 (revised), C17, M14. |

---

## 4. Open Questions (verified-still-unknown)

| # | Question | Why important | Investigation path | Source |
|---|---|---|---|---|
| ~~Q1~~ | **CLOSED 2026-04-17 — REFUTED.** No separate anchor pre-fusion stage exists. See M13, R16, R17. | — | — | `composite_anchor_n1_reducer.md`. |
| ~~Q2~~ | **CLOSED 2026-04-17 — VERIFIED.** Vignetting per-tile invoke at `libcp+0x345f30` (348 hits across 10 camera threads on L16_02130 28mm). Direction = multiply (`<vec4x32f, true>`). Order: per-camera ISP, fires for full 10-cam set including A2 (filter at 0x3f6170 is IRAMP-stage only). See I5 (revised). | — | — | `vignetting_runtime_corroboration.md`. |
| ~~Q3~~ | **CLOSED 2026-04-17 — VERIFIED-with-revision.** Per-tile CCM kernel = `ImageConvertColorSpace::$_0` at `libcp+0xbf4a0` (370 hits), NOT the prior chromaticity hypothesis. Per-camera selection happens at SETUP via `CCMInterpBetweenCalib` (5×, blended into single buffer). See C18, R18. | — | — | `imageapplycolormatrix_va.md`. |
| ~~Q4~~ | **CLOSED 2026-04-17 — VERIFIED.** IG+0x10 = effective-FOV ratio. Writer `libcp+0xe67c0`. Consumer `libcp+0x3eced0` (dispatched from IRAMP body). Operation `out = sqrt(max(0, in × FOV_ratio))` per-channel. See M14, C17, R19. | — | — | `ig_offset10_scalar.md`, `ig_offset10_consumer.md`. |
| Q5 | **`RemoveCrossTalkGeneric` exact VA + invocation path.** I7 says it's the consumer of the 13×17×4×4 cra_grids; "libcp 0x101830-region" was given as candidate. Needs precise VA + verification it fires on bridge HDR. | Needed to wire up CRA grids correctly. If it doesn't fire on bridge but only in editing-pipeline (per L5), Phoenix can omit it from the bridge-parity path. | RTTI scan for `RemoveCrossTalkGeneric`; LLDB BP each candidate VA on bridge HDR. | `calibration_audit.md`. |
| ~~Q6~~ | **CLOSED 2026-04-17 — MOOT.** Renderer-orchestrator at `0x3b5c00` was a Q1 alternative branch. Q1 closed via M13 (no separate pre-fusion stage exists), so Q6 is no longer relevant. | — | — | — |
| Q7 | **`auto_white_balance.neutral_color` source on captures where it IS persisted.** Most archive captures don't persist this protobuf field (so they fall to default 4300K, C8). But what about edge cases that DO have it set? Path: protobuf parse at `libcp 0x13eda0`. | Affects color accuracy for the subset of captures with explicit WB settings. | LRI archive scan for captures with non-empty `auto_white_balance.neutral_color`; LLDB at `0x13eda0` + watch what writer sets it. | KMS f99bc8a7. |
| ~~Q8~~ | **CLOSED 2026-04-17 — DUPLICATE of Q2 (now closed).** | — | — | — |
| Q9 | **Which of the 7 callers of `ImageConvertColorSpace` (`libcp+0xa9f20`) actually fires on bridge HDR?** Static caller list: `0xaa238, 0x2d7287, 0x2d8013, 0x3467ba, 0x34698f, 0x3470b9, 0x347318`. The 370-hit fire count + 2-distinct-CCM-matrix split (70+300) suggests at least 2 callers are active in different pipeline stages, but the per-caller breakdown is unobserved. | Helps localize where in the stage order CCM applies (pre-IRAMP per-camera vs post-IRAMP global). | LLDB BP at each of the 7 callers on bridge HDR L16_02130; tally hits per caller. | `imageapplycolormatrix_va.md`. |
| Q10 | **Why does `CCMInterpBetweenCalib` fire only 5× on L16_02130 28mm?** Expected 10 cameras (A1-A5+B1-B5) per the vignetting fire pattern (Q2-closed) and 6 cameras per the IRAMP dispatcher pattern (M4). The 5-camera fire suggests an additional culling stage between AWB/vignetting and CCM blending — or the 5 IRAMP contributors only (B1-B5, NOT the A1 anchor). | Affects whether Phoenix needs per-camera CCM for all firing cams or only contributors. | LLDB BP at `0x350bc0` capturing `[camera_struct+0xa8]` ptr and resolving to cam_id; verify whether 5 = {B1..B5} contributors or some other subset. | `imageapplycolormatrix_va.md`. |
| Q11 | **CCM 2-matrix split (70 hits Matrix A vs 300 hits Matrix B) attribution.** The two distinct matrices passed via closure capture[3] are likely from different pipeline passes (e.g., one for the per-tile pre-IRAMP per-camera path, one for post-IRAMP color-space conversion). 300 = IRAMP tile count match → Matrix B likely IS the per-camera pre-IRAMP CCM; 70 hits could be a downstream pass. | Confirms the architectural placement of the CCM step. Phoenix needs to know whether it's one CCM pass or two. | Add closure-capture tracing on `0xbf4a0` correlating which calling pipeline stage produced each matrix. Tied to Q9. | `imageapplycolormatrix_va.md`. |
| Q12 | **70mm/150mm CCM behavior verification.** All 2026-04-17 CCM findings (C18, R18) tested only on L16_02130 28mm. Need to confirm `ImageConvertColorSpace::$_0` is the active kernel at 70mm/150mm too, and whether the 5-camera CCMInterpBetweenCalib pattern holds. | Without it Phoenix could miss zoom-tier-specific CCM behavior. | LLDB BP at `0xbf4a0` + `0x350bc0` on L16_03434 70mm and L16_02285 150mm. | `imageapplycolormatrix_va.md`. |

---

## 5. Phase 2 / Out of Scope (deferred items)

| Topic | Status | Notes |
|---|---|---|
| Variant-0x10 outlier LRIs (~180 files, 1.8%) | **DEFERRED** per Rich's outlier-deprioritization rule. Phoenix can ignore or add later. Algorithm derives from canonical 98%; outliers are validation. | O1, `zoom_35mm_and_outliers.md`. |
| 244-file BJPG cluster | **DEFERRED.** Skip on 2018-normal decode path. Decompress via libjpeg per camera if Phase 2 wants to handle. | O2. |
| L16_01853-class 4-frames-per-camera mode (zoom=96) | **DEFERRED.** Special handling needed. | O3. |
| `DepthEditor` GUI surface (11 methods including push*Edit, quickSelectMask, enableFaceMatting) | **OUT OF SCOPE for Phoenix base render.** GUI-only (D1). `LIBRARY_INVENTORY.md` documents the surface for any future ctypes wrapper, but Phoenix is clean-room (Rule #0). |
| `lt::StackFusion` at `libcp+0x1b7d80` | **OUT OF SCOPE.** Fires 0 times on bridge HDR (M9). Likely stack-LRI captures or GUI editing pipeline. |
| Phase B mono-path (`MonoFusion` / `MonoMerge`) | **OUT OF SCOPE.** Phoenix does not emit mono output (L6). Skip lambdas `$_7`/`$_8`. |
| GUI editing-pipeline ISP stages (`RemoveCrossTalkGeneric`, lens-shading, hot-pixel, NLM, Adjust*, ImageCircleFilter, RestoreHighlights, ColorNoiseReduction, HSVMap 3D LUT) | **OUT OF SCOPE.** All fire 0 times on bridge HDR (L5). Phoenix only needs bridge-parity. |
| Ceres Pass A (`LabCostFunction<25,9>`) — offline color cal | **SKIP at runtime.** D3. |
| Ceres Pass B (`LightBA`: CameraProjection + EntrancePupilCost + IntrinsicsCost) — offline factory cal | **SKIP at runtime.** Phoenix uses baked factory intrinsics/extrinsics from cal blocks. D3. |
| Ceres Pass C (`Triangulator::refine3dPoints`) — per-point bounded depth refinement | **REIMPLEMENT** with `scipy.optimize.least_squares(loss='cauchy', f_scale=1.0, bounds=(lo,hi))`. D3. |
| Halide kernel byte extraction (tone curve LUTs, Robertson forward table) | **FORBIDDEN** per Rule #0 (KMS 5e7bd5fe). Reimplement from formulas / Wyszecki-Stiles / CIE-standard. Tone curve = recompute from filmic/ACR formula whose midgray response matches; OR fit splines from observed input/output behavior. KMS 8c2bc067. |
| Distribution legal review for shipping LUT bytes | **SUPERSEDED** by clean-room decision (KMS 8c2bc067). No legal blocker; Phoenix is dcraw-style standalone. |
| Preview-quality per-camera puzzle-piece extraction (no per-camera vignetting/CCM applied) | **DONE (not needed for Phoenix).** Used for visual confirmation of B-as-A architecture only. Files at `/Volumes/Dev/lumen-phoenix-scratch/puzzle_pieces/`. |

---

## 6. Replication Recipes

These recipes assume libcp.dylib is loadable into LLDB (x86_64 macOS, Rosetta if on Apple Silicon). Slide is per-process; compute via `image list libcp.dylib`. All VAs in this doc are FILE offsets — add slide to get RIP.

### 7.0 LLDB tooling discipline (mandatory)

Pitfall (KMS df9a908b, 2026-04-16): **DO NOT use `breakpoint command add ... --auto-continue true`.** The script reads stale or garbage register values when the BP fires under auto-continue. Two valid alternatives:

1. **Manual stop and inspect:** Plain `breakpoint set` + `process continue`; when it stops, run `register read` + `memory read` interactively. Slowest but always correct.
2. **Frame-context register reads inside BP script:** Inside `breakpoint command add` use the SBFrame API explicitly:
   ```
   frame = thread.GetSelectedFrame()
   rip = frame.FindRegister("rip").GetValueAsUnsigned()
   rdi = frame.FindRegister("rdi").GetValueAsUnsigned()
   # then read memory or follow pointer
   ```
   This reads live registers at the BP stop, NOT the convenience-wrapped (potentially stale) globals.

Always use `process continue` between hits, never auto-continue.

### 7.1 Reproduce IRAMP smoking-gun accumulator (M1, M6)

```
(lldb) target create lri_process
(lldb) br set -n CIAPI::Renderer::render
(lldb) run --in /Volumes/Base\ Photos/Light/2018-07-23/L16_02130.lri --out /tmp/phx_test.tiff
# At first hit:
(lldb) image list libcp.dylib   # note slide S
(lldb) br set -a $(printf "0x%x" $((S + 0x369fa1)))
(lldb) c
# At hit:
(lldb) di -s $rip -c 5
# Expect:
#   mulps  (%rdi),%xmm1
#   addps  (%rdx,%rcx,4),%xmm1
#   movaps %xmm1,(%rdx,%rcx,4)
```

To verify outer ÷5: `di -a $(printf "0x%x" $((S + 0x369f18))) -c 4` and look for `imul $-0x3333333333333333`.

### 7.2 Verify IRAMP runtime signature + camera identity (M2, M3)

```
(lldb) br set -a $(printf "0x%x" $((S + 0x365960)))
(lldb) br command add -F py_capture_iramp_args.py
# In script (frame-context reads):
def func(frame, bp_loc, dict):
    rdi = frame.FindRegister("rdi").GetValueAsUnsigned()  # &dst
    rsi = frame.FindRegister("rsi").GetValueAsUnsigned()  # &src1
    rdx = frame.FindRegister("rdx").GetValueAsUnsigned()  # &src2
    rcx = frame.FindRegister("rcx").GetValueAsUnsigned()  # &srcs vector
    r8  = frame.FindRegister("r8").GetValueAsUnsigned()   # &warps vector
    # vector layout: begin* at +0, end* at +8, capacity_end* at +16
    proc = frame.GetThread().GetProcess()
    err  = lldb.SBError()
    srcs_begin = proc.ReadPointerFromMemory(rcx, err)
    srcs_end   = proc.ReadPointerFromMemory(rcx + 8, err)
    n_srcs = (srcs_end - srcs_begin) // 8
    for i in range(n_srcs):
        ig = proc.ReadPointerFromMemory(srcs_begin + 8*i, err)
        # cam_id = *(*(IG+0x08)+0x90) int64
        funcdata = proc.ReadPointerFromMemory(ig + 0x08, err)
        cam_id = proc.ReadUnsignedFromMemory(funcdata + 0x90, 8, err)
        print("src[%d] cam_id=%d" % (i, cam_id))
    return False  # do not auto-continue
(lldb) c
# Expect at 28mm L16_02130: vec[0..4] = {5,6,7,8,9} = B1..B5
```

### 7.3 Verify IRAMP-side dispatcher cam-id filtering (M4)

```
(lldb) br set -a $(printf "0x%x" $((S + 0x3f6170)))
(lldb) br command add -F py_capture_dispatcher.py
# Capture cam_id arg passed in; expect at 28mm: {0,5,6,7,8,9} = A1+B1..B5
# At 70mm L16_03434 expect: {8,10,11,12,13,14} = B4+C1..C5
```

### 7.4 Verify DemosaickLightV1 vs V2 dead-code (I3)

```
(lldb) br set -a $(printf "0x%x" $((S + 0x2eb560)))   # V1 driver
(lldb) br set -a $(printf "0x%x" $((S + 0x2eba10)))   # V2 driver
(lldb) br set -a $(printf "0x%x" $((S + 0x2f0df0)))   # V2 kernel
# Run full L16_02130 28mm export. Expect: V1=889, V2 driver=0, V2 kernel=0.
```

### 7.5 Verify AWB reciprocal direction (C1)

```
(lldb) br set -a $(printf "0x%x" $((S + 0x340f70)))   # setWhiteBalance::$_5
(lldb) br command add -F py_dump_context.py
# In script: read context_ptr (typically rcx or rdx depending on calling state)
# Read 4 floats. Expect (0.5821, 1.0, 0.6294, 0.3630) on L16_02130
# Verify 0.5821 == 1/1.7178 (Block 8 R_gain) and 0.6294 == 1/1.5888 (B_gain)
```

LRI extraction of Block 8 stored gains:

```
import struct
data = open('L16_02130.lri', 'rb').read()
# Block 8 f19.f15 is at offset 0x09b189d8 + 32 (LELR header)
# Read 4 LE float32: [R, G1, G2, B]
gains = struct.unpack('<4f', data[0x09b189d8 + 32 : 0x09b189d8 + 32 + 16])
# Expect: (1.648295, 1.0, 1.0, 1.778951)
```

### 7.6 Verify CCM chromaticity kernel (C3)

```
(lldb) br set -a $(printf "0x%x" $((S + 0x350cdd)))  # green-write-1.0 instruction
(lldb) di -s $rip -c 1
# Expect: mov dword ptr [r14+0x4], 0x3f800000     ; 0x3f800000 = float 1.0
```

### 7.7 Verify tone curve kernel (C10–C13)

```
(lldb) br set -a $(printf "0x%x" $((S + 0x2d7780)))   # LinearTMO::process driver
(lldb) br command add -F py_dump_tmo.py
# In script:
#   Read TMO_obj+0x10 -> LUT pointer (expect light_v1 LUT @ 0x5e41b4)
#   Read TMO_obj+0x20 -> EV float (expect 0.0 by default → exp2f(0)=1.0×)
# Confirm pre-shaper constants by reading 6 f32 at libcp+0x5e3140:
#   Expect (0.0025, 0.0075, -0.005, 1.0050251, 100.50251, 1024.0)
```

### 7.8 Verify CDF 9/7 wavelet constants (M7)

```
(lldb) memory read -f f32 -c 8 $(printf "0x%x" $((S + 0x5cbfd0)))
# Expect:
#   1.5861343  3.1722686  -0.05298011  -0.10596023
#   -0.8829110 -1.7658221  1.1496044    0.8698644
# These are JPEG2000 CDF 9/7 lifting coefficients.
```

### 7.9 Verify zoom-tier table (Z1)

```
(lldb) memory read -f int32 -c 3 $(printf "0x%x" $((S + 0xe7020)))
# Tier table cases for enum 0/1/2 mapping to ref-focal length lookup
# Combine with BP at libcp+0xe6d90 (focal-length crop computer) to capture
# image_focal_length read from lcp::Image at 0x40(rsi).
```

### 7.10 Verify pyramid-dims vector at PipelineCache+0x8 (R12 refutation)

```
(lldb) wp set expression -- "*(uint64*)($PipelineCache + 0x8)"
# Run full export. Expect: 4 hits (2 at construction, 2 at process-exit free)
# Read the begin pointer; deref as 5 packed Vec2<int32>:
#   {(10432,7824), (4160,3120), (2080,1560), (1040,780), (520,390)}
```

### 7.11 Verify per-camera Bayer pattern in LightHeader (I4)

```python
# Pseudocode for LightHeader scan:
# For each camera record in field[12]:
#   parse field[13] as ltpb.Point2I -> (x, y)
#   map (0,0)->RGGB, (1,0)->GRBG, (0,1)->GBRG, (1,1)->BGGR
# Expect at L16_02130: A1/A3/A4=GRBG, A5=GBRG, B1/B5=RGGB, B2/B3/B4=BGGR
```

### 7.12 Verify firing rules from full archive (F1, F2)

```python
# Use lri_catalog.db (post-2026-04-16 schema):
# SELECT zoom_class, fired_names, COUNT(*)
#   FROM lri_catalog
#   WHERE zoom_val IS NOT NULL
#   GROUP BY zoom_class, fired_names
#   ORDER BY zoom_class, COUNT(*) DESC;
# Expect dominant patterns:
#   28mm/35mm: A1|A2|A3|A4|A5|B1|B2|B3|B4|B5
#   70mm/150mm: B1|B2|B3|B4|B5|C1|C2|C3|C4|C5|C6
```

---

## 7. References

### 7.1 Scratch agent reports (`/Volumes/Dev/lumen-phoenix-scratch/`)

Primary 2026-04-16/17 reports cited in this doc:

- `iramp_kernel_body.md` — IRAMP smoking-gun mulps+addps+movaps at 0x369fa1; full disasm citations of body 0x3661b0..0x36ae41.
- `iramp_camera_identity.md` — Per-camera IDs at IRAMP, B-as-A architecture verified.
- `image_resolution_amp_verification.md` — IRAMP runtime signature capture across 10 ROIs.
- `pyramid_levels_characterization.md` — 5-level pyramid table.
- `merge_canvas_writes.md` — Canvas write semantics.
- `merge_function_reconciliation.md` — Corrected merge attribution; 0x3ebb80 / 0x3d0650 / processLevel hit counts.
- `merge_string_inventory.md` — `lt::ImageResolutionAmp` + StackFusion RTTI inventory.
- `merge_tile_geometry.md` — Tile geometry.
- `refcache_per_camera_isp.md` — Per-camera ISP chain VAs (Stage0–6); CRA undistort tile-fetch.
- `composite_producer.md` — PC+0x8 = pyramid metadata refutation; runReferenceGroupCams VAs resolved.
- `anchor_prefusion_and_c6.md` — initResAmp = src1/src2 construction site; initFusion vfunc REFUTED as composite producer.
- `runreferencegroupcams_body.md` — Body characterization of FCB::process inner.
- `c6_destination_and_depthcache.md` — C6 filtered at 0x3f6170; DepthCache GUI-only.
- `a2_destination.md` — A2 filtered at 0x3f6170; refined single-anchor model; STAGE6 0x341040 refuted as CCM.
- `color_pipeline_audit.md` — AWB direction reciprocal; CCM 2-illuminant; V1 fires.
- `ccm_factory_to_runtime_transformation.md` — CCM chromaticity-space; field 3 color_matrix.
- `35mm_renderer_mechanism.md` — Focal-length crop @ 0xe6d90; 35mm RectF; bridge upsample.
- `tone_curve_location_and_zoom_crop.md` — Zoom-tier table libcp+0xe7020; tone curve location.
- `tone_curve_kernel_location.md` — Tone curve kernel VA libcp+0x2d7a30; pre-shaper bit-exact.
- `calibration_audit.md` — Per-camera Bayer pattern; CRA radial; vignetting direction.
- `zoom_tier_and_vignetting.md` — Tier table values + vignetting kernel VA.
- `depth_editor_and_iramp_depth.md` — DepthEditor GUI-only; ImageDecodeBayerJPEG location.
- `stackfusion_characterization.md` — StackFusion not on bridge.
- `per_camera_radiometric_weight.md` — 4 candidates probed; no per-camera weight at IRAMP.
- `puzzle_pieces.md` — Per-camera visual extraction; B-as-A confirmation.
- `lightheader_camera_scan.md` + `lightheader_scan_raw.csv` — 9390-LRI fired-camera scan.
- `sub_stages_36cde0_36e530_36f800.md` — CDF 9/7 sub-stages.
- `zoom_35mm_and_outliers.md` — Variant-0x10 outlier characterization.
- `critique_audit.md` — Agent 5's 28-item audit, 7 verified.
- `backward_audit_2026-04-16.md` — Full backward audit, 19 STILL-VALID / 8 SUPERSEDED / 11 REFUTED / 6 NEW.

2026-04-17 PM batch (closes Q1, Q2, Q3, Q4, Q6, Q8; opens Q9–Q12):

- `composite_anchor_n1_reducer.md` — REFUTES the 13-lambda hypothesis; proves no separate anchor pre-fusion stage exists; src1/src2 IGs both wrap single anchor camera.
- `ig_offset10_scalar.md` — IG+0x10 writer = `libcp+0xe67c0`; formula = `(ref_dim×ref_scale)/(this_dim×this_scale)×optional_exposure`.
- `ig_offset10_consumer.md` — IG+0x10 consumer = `libcp+0x3eced0` (LLDB watchpoint verified); operation `out = sqrt(max(0, in × FOV_ratio))`; dispatched from IRAMP body.
- `vignetting_runtime_corroboration.md` — Vignetting per-tile invoke @ `libcp+0x345f30`; 348 hits across 10 camera threads; A2 IS in vignetting set (filter is IRAMP-stage only).
- `sourceimagecache_writer.md` — `PipelineCache+0x170` = `lt::ReferenceImageCache` (RTTI-verified); writer @ `libcp+0x3ea83d`; tile format `lt::Vec3<Float16>`.
- `sourceimagecache_location.md` — 5 contributor SICs in RB-tree at `RIC+0x30`; SIC vtable `libcp+0x65f490`; init function `libcp+0x3e0330` from `initResAmp` @ `libcp+0x3eb5c6`.
- `imageapplycolormatrix_va.md` — Per-tile CCM kernel = `ImageConvertColorSpace::$_0` @ `libcp+0xbf4a0` (370 hits, 2 distinct matrices); CCMInterpBetweenCalib = SETUP-time per-camera blend (5 hits → single buffer); REFUTES `ImageApplyColorMatrix_3x3_mask` and `setColorCorrection_58_Color` as candidates.

### 7.2 Reference data & ground truth

- `/Volumes/Dev/lumen-phoenix-scratch/cal_color_l16_02130.npz` — REFERENCE EXTRACT only (Rule #0 forbids runtime use).
- `/Volumes/Dev/lumen-phoenix-scratch/cal_color_l16_02500.npz`, `cal_color_l16_02586.npz` — additional sample units.
- `/Volumes/Dev/lumen-phoenix-scratch/lri_catalog.db` — 9390-LRI catalog with fired-camera + zoom data.
- `/Volumes/Dev/Light_Spike/ground_truth.tiff` — Bridge-rendered ground truth on L16_02130 (10432×7824, MAD 0.067% vs Lumen GUI).
- `/Volumes/Dev/Light_Spike/depth_map.npy` — Companion depth (GUI-derived; not a bridge product).
- `/Volumes/Dev/lumen-phoenix-scratch/tmo_*.npy` + `tmo_characterization.json` — Tone curve LUT extracts (REFERENCE only; clean-room re-derive per Rule #0).
- LRI archive: `/Volumes/Base Photos/Light/YYYY-MM-DD/`. Test capture: `L16_02130.lri` (28mm, 2018-07-23). 70mm test: `L16_03434.lri` (2019-05-18). 150mm test: `L16_02285.lri` (zoom≈149, 2018-07-29). 35mm tests: from 9390-row scan.

### 7.3 KMS entry IDs (selected — full grouping above)

Merge / IRAMP: `5dab2d99` (rev), `ab919f01` (smoking gun), `30277490` (architecture), `94f16536` (cam identity), `456fc305` (CDF 9/7), `12b1a423` (backward audit), `82ec7c61` (C6 destination), `3c000e4a` (A2 destination + 6-cam revision), `5b87df33` (RIC framing correction), `8f145e78` (radiometric weight resolved), `7c87890f` (35mm crop), `8475c34d` (zoom-tier table), `7867497b` (firing scan), `60180309` (initResAmp construction), `02e7ed36` (PC+0x8 refutation + runReferenceGroupCams VAs), `8affaced` (B-as-A visual), `45148e2e` (puzzle pieces).

Color pipeline: `ad9dcad6` (AWB reciprocal), `4a5a9459` (AWB context decode), `f99bc8a7` (Robertson CCT), `ed20c8aa` (CCT chromaticity correction), `f687f433` (CCM chromaticity-space transformation), `0a403698` (V1 vs V2 dispatch), `91839eb8` (calibration extraction), `e50b0758` (AWB stats-driven), `ef06bd6a` (tone curve kernel), `9408f4cd` (ISP VA map), `e24fa9ce` (light_v2 naming gotcha), `d9b842f4` (per-camera Bayer + vignetting + CRA correction).

Discipline / process: `df9a908b` (LLDB auto-continue pitfall), `5e7bd5fe` (clean-room Rule #0), `8c2bc067` (standalone distribution), `5e9c43f8` (per-LRI calibration parser required), `b44626c8` (audit-before-acting), `c3029e6e` (sweep-before-investigate), `b72814a7` (validate-doc-before-spec), `8ddbe013` (8-spike-failure inventory), `a0acb5b6` (backward-audit gap noted), `dac3f29d` (parallel WSJF investigation).

Container / library: `eafa5c3b` (spec-writing ready), `a2cc8b7b` (Ceres static analysis), `9d3bd76d` (handoff complete), `f40e099c` (handoff procedure), `90903ff4` (rev 2 corrections), `fc7f26c1` (two-artifact discipline), `82a0e2f6` (Halide table at 0x1cd40).

Outliers / variants: `d0ff99ba` (variant-0x10), `ce238bd9` (zoom=96 4-frames mode), `8475c34d` (two-tier canvas — also under merge).

Depth: `d4efb901` (depth GUI-only), `9e47405e` (DepthEditor + DepthCache zero hits).

### 7.4 Rules / invariants carried forward

1. **Rule #0 (clean-room, KMS 5e7bd5fe):** Phoenix does NOT link, dlopen, or bundle bytes from libcp/Lumen.app. Every constant is parsed from LRI at render time, derived from CIE/published references, or reimplemented from a documented algorithm in this doc.
2. **Two-artifact discipline (KMS fc7f26c1):** Investigation doc and spike implementation are separate. Spike outputs (MAD, coverage %) are tests of the investigation, NEVER edited into the doc.
3. **Signature-AND-body criterion (Rich):** Any "X is the merge / X is the reducer" claim requires both a signature match AND a verified body. Setup-only matches stay CANDIDATE until body is read.
4. **Outlier-deprioritization rule (Rich):** Don't drive architecture investigation with outliers; algorithm derives from canonical 98%; outliers are later validation.
5. **LLDB no-auto-continue (KMS df9a908b):** Always use frame-context register reads. Never `--auto-continue true`. See Replication §7.0.
6. **Standalone distribution (KMS 8c2bc067):** Phoenix is fully standalone (eBay 2030 use case). No legal review blocker; tone curves reimplemented from formula or fitted spline.
7. **Per-LRI calibration parser is a required pipeline stage (KMS 5e9c43f8):** Every LRI is self-contained. The .npz files in handoffs are reference extracts only.

---

*End of PHOENIX TRUTH SOURCE 2026-04-17. Direct successor to `lumen-phoenix-current-state.md` (rev 2026-04-13) and `phoenix-pipeline-facts.md` (rev 6, 2026-04-13). Companion: `LIBRARY_INVENTORY.md` (still valid; no refutations). For pre-2026-04-13 history, see `lumen-phoenix-investigation.md` (281K full log) — but that log contains stale conclusions; cross-check every claim against this doc before relying on it.*
