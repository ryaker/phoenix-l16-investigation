# Phoenix L16 — TRUTH

**Version**: 2.1.2
**Status**: Canonical truth doc for the L16 Phoenix reimplementation.
**Git is authoritative for history.** Commit hash + log = "when was this true."
**File has no date in its name** — versioning lives inside; the previous version is preserved at `archive/TRUTH-v1-phoenix-truth-2026-04-17.md`.

**What v2.1.1 adds / changes vs v2.1 (2026-04-20, doc hygiene pass):**
- **Doc hygiene (OPEN-UNCITED closure):** added 12 load-bearing citations to §2.1–§2.9 Evidence cells + §4 OPEN-* rows + §7.2 authoritative-scratch list. Files now integrated: `pyramid_levels_characterization.md`, `laplacian_pyramid_kernels.md`, `laplacian_collapse_and_lab_layout.md`, `nlm_bm3d_denoiser.md`, `per_iso_anscombe_consumer.md`, `q12_ics_kernel_28mm.md`, `q12_ics_kernel_35mm.md`, `demosaicv1_details_cleanup.md`, `demosaicv1_sub_kernels.md`, `blc_correction_OVERRIDE.md` (already in §7.2 — expanded §2.4 K1 citation), `dual_cost_fusion_site.md`, `depth_cost_algorithm_classified.md`, plus external `l16-tech-part-1-3.md`. Closes 2026-04-20 audit action #17 OPEN-UNCITED (see `/tmp/l16_open_audit/_FINDINGS.md` §17). No finding rows rewritten — Evidence cells appended only.
- **§1 pyramid dims table** now cites `pyramid_levels_characterization.md` for full per-level resolution + operator-role map.
- **§2.1 M8** Evidence expanded to cite pyramid-level operator decode (0x3ebb80 cubic resample + 0x3d0650 pyramid read primitive).
- **§2.2 I3** Evidence expanded to cite DemosaicV1 21-tap coefficient decode + 5-sub-kernel buffer-allocator identification.
- **§2.3 C18** Evidence expanded with 28mm re-verify (324 hits / 2 CCM values).
- **§2.4 K1** Evidence expanded with `blc_correction_OVERRIDE.md` Round-4 late-revision scope-bound conditions.
- **§2.6 D3** Evidence expanded with LabCostFunction Evaluate VA (0x11ae40) + CIEDE2000 helper (0x1273c0).
- **§2.6 D9-D11** Evidence expanded with Path A algorithm classification + fusion-site hypothesis.
- **§4 Q12 / OPEN-NLM4 / OPEN-DARKCURRENT / OPEN-DEMOSAIC-KERNEL / OPEN-LAPLACIAN-TAPS / OPEN-PATH-B2** rows updated with static-disasm partial closures; runtime/LLDB verification still required for each.

**What v2.1 added / changed vs v2 (2026-04-20, Session 1 LLDB closure):**
- **#15 Q-DROPPED-CONSUMER CLOSED.** HW read-watchpoints on 4 dropped-cam RIC L0 buffers at 28mm bridge HDR captured 102,361 trips; 100% trace through IRAMP-family code. Dropped cams consumed via composite-anchor pre-fusion kernel (new VA below). See §2.1 M14.1 + §4 for evidence.
- **NEW VA added to §2.1 IRAMP**: `libcp+0x2b3410..0x2b3448` composite-anchor 4-way SIMD weighted-blend kernel. Called from IRAMP body `0x365f50`; consumes A1-A5 RIC L0 buffers at 28mm to build `src1`/`src2` composite IGs.
- **§4 updated**: OPEN-DROPPED-CONSUMER row removed (resolved). OPEN-DARKCURRENT row updated — Session 1 reconfirmed `0x3048b0`/`0x2f3b90` fire 0× on bridge HDR profile=3; formula extraction deferred to different render profile.
- **Session 1 deliverables**: `/tmp/l16_open_audit/session1_findings.md`, `session1_transcript.md`, `session1/phase2_watchpoints.log` (66 MB, 102K trips), `session1/reclassified.txt` ("TRULY NOVEL: (none)").
- **Spike gate**: 28mm bridge HDR spike is UNBLOCKED. 70/150mm spike still gated by #16 (non-blocking for 28mm).

**What v2 added / changed vs v1:**
- Integrates the 4 April-19 cleanup rounds (10 SUPERSEDED corrections + 16 Round-2 verifications + 6 Round-3 banner refutations + 34 Round-4 scope-bands across 9 files) which explicitly skipped TRUTH in v1
- Integrates 3 post-v1 scratch files (`va_registry.md`, `hwinfo_field_18.md`, `pyramid_range_seeding.md`)
- Applies Round-4 precision rule to v1's absolutes ("GUI-only" / "0 hits" / "NEVER fires" → scope-bound to tested LRI + focal + mode)
- Expands Open Questions with items that were silent in v1 (BLC kernel VA, Path B2, dark-current stage, Demosaic inner kernel, IRAMP 28mm short-circuit)
- Flags two unresolved internal conflicts that v1 papered over: f_scale and BLC kernel identity

**Discipline (carried from v1, made explicit):**
- Every finding cites VA + LLDB transcript | LRI binary offset | RTTI/string evidence
- Absolutes get scope-bands (Rich's rule: "if your paraphrase sounds like an absolute thats a problem")
- Static-disasm ≠ LLDB-live ≠ structural-inference; confidence label on every row
- Spike is validation-only; spike NEVER writes to TRUTH; spike doesn't run until TRUTH is closed
- Open questions stay Open — no silent resolution
- Every test-scope claim carries its explicit (LRI + focal + profile) axis and enumerates untested axes

Confidence key: ✅ LLDB-live  📐 Static-disasm  🔤 String/RTTI  ⚠️ Candidate/unverified  🟡 Structural-inference

---

## 1. TL;DR architecture

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
        data_offset  (f9.f5)          (PRE-multiply gains; kernel uses RECIPROCALS)
                          │
                          ▼
   10-bit MIPI BGGR/RGGB/GRBG/GBRG unpack — per-camera pattern from f13
                          │
                          ▼
   ┌────── Per-camera ISP inside lt::ReferenceImageCache ──────┐
   │  RIC is a SHARED orchestrator (1 instance, 10 buffers).    │
   │  Stage order (bridge HDR, LLDB-verified on L16_02130 28mm +│
   │  L16_03434 70mm only — NOT verified at 35mm/150mm):        │
   │   SourceImageCache ImageWarp<Bicubic,vec4x8ui,             │
   │     LensUndistortCRA> @ 0x261940 (radial 4096-LUT undist)  │
   │   STAGE0 LinearizeAndColorScale<uint16> @ 0x340b00         │
   │     ⚠ OPEN-BLC: whether this is BLC kernel or color-scale  │
   │       ONLY is DISPUTED. See §4 OPEN-BLC.                   │
   │   STAGE1 LinearizeAndColorScale<float>  @ 0x340bf0         │
   │   STAGE2 ImageCorrectBayerPhaseAR1335   @ 0x340cc0         │
   │   STAGE5 setWhiteBalance::$_5           @ 0x340f70         │
   │     (Bayer cells × 1/stored_gain — reciprocal verified)    │
   │   DemosaickLightV1 driver               @ 0x2eb560         │
   │     Inner kernel = STATIC SSE2 @ 0x2eef80 (not JIT — the   │
   │     "JIT wall" was phantom per Round 2)                    │
   │   STAGE6 setColorCorrection::$_6        @ 0x341040         │
   │     (per-camera CCM SETUP; tile apply at 0xbf4a0 inside    │
   │      IRAMP — per-tile, not per-camera)                     │
   │   Vignetting (parallel worker path, multiply):             │
   │     <vec4x32f, true> @ 0x108080 (post-demosaic)            │
   │     Per-tile dispatcher @ 0x345f30 (348 hits / 10 cams)    │
   │   Tone curve (per-tile post-demosaic):                     │
   │     LinearTMO::process driver @ 0x2d7780                   │
   │     LUT-apply lambda          @ 0x2d7a30                   │
   │     Default = light_v1 @ 0x5e41b4 (bridge; ground-truth    │
   │       LUT match). Pre-shaper @ 0x2d7c90..0x2d7f44 with     │
   │       bilinear LUT interp.                                 │
   │   ⚠ OPEN: dark-current correction separate from BLC lives  │
   │     at libcp+0x66d670 (28-record per-ISO table). Whether it│
   │     fires on bridge HDR is unverified.                     │
   │   ⚠ OPEN: denoiser = NLM-4 with 4 novel modifications      │
   │     (Round 3 banner, refutes BM3D hypothesis). Bridge-path │
   │     activation status unverified.                          │
   └────────────────────────────────────────────────────────────┘
                          │
   Output: per-camera Image<vec4x32f> + cached Tile<Vec3<Float16>>
                          │
                          ▼
        ┌── IRAMP-side calibration dispatcher @ 0x3f6170 ──┐
        │  Filters cam_ids without CCM entries.             │
        │  28mm: passes [0,5,6,7,8,9] = A1+B1..B5  (6 cams) │
        │  70mm: passes [8,10,11,12,13,14]=B4+C1..C5 (6 cams)│
        │  No fallback — std::out_of_range at 0x3f6866.     │
        │  A2-A5 (28mm) and B1/B2/B3/B5 (70mm) = consumed   │
        │  via composite-anchor pre-fusion, NOT depth-only. │
        │  ✅ D5/Q-DROPPED CLOSED 2026-04-20: dropped cams  │
        │    consumed by IRAMP body's composite-anchor      │
        │    kernel at libcp+0x2b3410 (4-way SIMD blend).   │
        │    See §2.1 M14.1. Phoenix MUST run full per-cam  │
        │    ISP for all fired cams (dropped ISP = corrupt  │
        │    src1/src2 → corrupt merge).                    │
        └──────────────────────────────────────────────────┘
                          │
                          ▼
   ┌── lt::ImageResolutionAmp (IRAMP) — cross-camera merge ──┐
   │  Setup @ 0x365960..0x366082                              │
   │  Halide body @ 0x3661b0..0x36ae41 (19,601 B)             │
   │  Smoking-gun N→1 accumulator @ 0x369fa1:                 │
   │    mulps (%rdi),%xmm1                                    │
   │    addps (%rdx,%rcx,4),%xmm1                             │
   │    movaps %xmm1,(%rdx,%rcx,4)                            │
   │  Outer ÷5 magic -0x3333333333333333 @ 0x369f18           │
   │  Signature (LLDB-captured on L16_02130 28mm +            │
   │             L16_03434 70mm only):                        │
   │    (Image<vec4x32f>& dst,                                │
   │     ImageGenerator& src1,                                │
   │     ImageGenerator& src2,                                │
   │     vector<shared_ptr<ImageGenerator>>& srcs[size=5],    │
   │     vector<WarpField>& warps[size=5],                    │
   │     float scale,                                         │
   │     Rectangle<int>& roi)                                 │
   │  = 2 anchor wrappers + 5 contributors, NOT 10 cams       │
   │                                                          │
   │  src1/src2 wrap the SAME single anchor camera (A1 at     │
   │  28mm, B4 at 70mm) via PipelineCache+0x170 =             │
   │  lt::ReferenceImageCache. Per-tile op fires at           │
   │  vt[+0x30] = 0x3ecc10 / 0x3ecd80. vt[+0x18] never fires. │
   │                                                          │
   │  Per-contributor pre-norm @ 0x3eced0 (M14):              │
   │    out = sqrt(max(0, in × IG+0x10)) per-channel          │
   │    IG+0x10 = effective-FOV ratio (writer @ 0xe67c0)      │
   │                                                          │
   │  Per-tile CCM @ ImageConvertColorSpace::$_0 @ 0xbf4a0    │
   │    370 hits at 28mm, 2 distinct matrices (70 + 300).     │
   │    Per-camera CCMInterpBetweenCalib @ 0x350bc0 fires 5×, │
   │    all 5 OVERWRITE the same buffer → single consolidated │
   │    M for all tiles in this pass.                         │
   │  ⚠ Q10/Q11 open: why 5× not 10×? which of the 2 matrices │
   │    is per-camera vs post-IRAMP? Unresolved.              │
   │                                                          │
   │  Wavelet super-res sub-stages:                           │
   │    0x36cde0 = patch stats + CDF 9/7 match-score          │
   │    0x36e530 = inverse-DWT synthesis + 5-band byte-LUT    │
   │    0x36f800 = Catmull-Rom 64-LUT setup                   │
   │    Lifting constants @ 0x5cbfd0..0x5cc040 (JPEG2000 spec)│
   │  Inner resample: BILINEAR (4 samples), NOT bicubic.      │
   │    True Catmull-Rom bicubic only at 0x3e2e90 elsewhere.  │
   │                                                          │
   │  ⚠ 28mm IRAMP short-circuits through a single-anchor     │
   │  path that hides inner SAD/WTA stages; 70mm fires the    │
   │  full chain with 25+ hits at each VA. Spike-blocker:     │
   │  28mm-only validation will hide bugs that only surface   │
   │  at 70mm.                                                │
   └──────────────────────────────────────────────────────────┘
                          │
                          ▼
   Output canvas Image<vec4x32f>:
     L0: 10432×7824 (28mm, 70mm base) or 8848×6624 (70mm tier)
     Crop BEFORE IRAMP via 0xe6d90 + zoom-tier table 0xe7020
     (Tier 0 ref=28mm, Tier 1 ref=70mm)
                          │
                          ▼
   exportImage::$_3 → Renderer::writeImage → DNG/TIFF/PNG/JPEG
   Bridge lri_process hardcodes outsize {10432,7824} — cropped
   FOVs upsampled to this. (Not a Lumen.app GUI behavior.)

   Depth (profile=3 DESKTOP only; profile=2 CAMERA skips):
     Gate @ 0x3b2fa3 (image-storage byte & 0xf == 0x3)
     → StereoAsyncAPI C1 @ 0x3f46d0 → C2 @ 0x3f2c40
     → DepthCache ctor @ 0x3d8780 (NOT 0x3eaf00 — that's a thunk)
     → Triangulator::refine3dPoints @ 0x20ca00 (1-2 hits)
     → ReProjectionCost<2,1> @ 0x20d1ac (Ceres Pass C)
     → Halide AOT tile dispatcher @ 0x5440 (shared with IRAMP/CCM)
     Path A cost builder @ 0x30b770 with 4 variants at
       0x30b9f0 / 0x30dcc0 / 0x30ff60 / 0x3121f0.
     ⚠ Path B2 @ 0x2732f0 also fires (Round 3 banner).
       0x2730c0 is a count==4 specialization that NEVER fires
       on L16 (count>4 always at the single tested 70mm LRI).
     SGM "identified" was REFUTED-AS-DISPATCH: 0x267e80 fires 0×
     on bridge profile=3 at the single tested LRI pair. Real
     algorithm class lives in Halide kernel body at 0x3d01b0
     with closure vtable 0x66a618 — NOT named in libcp strings.
```

5-level pyramid dims (LLDB-verified at 28mm L16_02130 only):

| Level | Dims | Notes |
|---|---|---|
| L0 | 10432 × 7824 | only level delivered to encoder |
| L1 | 4160 × 3120 | matches AR1335 native sensor dims |
| L2 | 2080 × 1560 | scratch |
| L3 | 1040 × 780 | scratch |
| L4 | 520 × 390 | scratch |

Stored at `PipelineCache+0x8` (embedded `vector<Vec2<int32>>`), written once by PC ctor (0x3ea7d0/0x3eaf00) — NOT a composite buffer. See `pyramid_levels_characterization.md` for full per-level dims + role-map (0x3ebb80 single-source cubic resample; 0x3d0650 pyramid-level read primitive).

---

## 2. Verified Findings

**Test-condition scope guard (universal to this section):** every "Verified" row in §2.1–§2.9 was established on specific LRI(s) + focal length(s) + profile(s). Unless a row explicitly says "empirical archive scan (9390 LRIs)", assume the scope is **ONLY the LRIs listed in the Evidence cell**. Untested axes: other LRIs, other zooms, profile=2 CAMERA, Lumen.app GUI, single-shot LRIs.

### 2.1 Cross-camera merge / IRAMP

| # | Finding | Evidence (VA + source) | Confidence |
|---|---|---|---|
| M1 | Cross-camera merge = `lt::ImageResolutionAmp` at `libcp+0x365960` (setup) + `0x3661b0..0x36ae41` (Halide body, 19,601 B, 0x4498 stack frame, 120 internal calls). Smoking-gun N→1 accumulator at `0x369fa1`: `mulps (%rdi),%xmm1 ; addps (%rdx,%rcx,4),%xmm1 ; movaps %xmm1,(%rdx,%rcx,4)`. ÷5 magic `-0x3333333333333333` at `0x369f18`. | LLDB across 10 ROIs on L16_02130 28mm + L16_03434 70mm. `iramp_kernel_body.md`. | ✅ |
| M2 | IRAMP runtime signature: `(dst, src1, src2, srcs[5], warps[5], float scale, roi)`. 7 IG inputs = 2 anchors + 5 contributors. WarpField = 80 B (verified via `0xCCCCCCCCCCCCCCCD>>SAR4` divide magic). 300 invocations per 28mm render on L16_02130; 221 per 70mm on L16_03434. | `image_resolution_amp_verification.md`, `iramp_camera_identity.md`. | ✅ (L16_02130 28mm + L16_03434 70mm only) |
| M3 | Per-camera identity at IRAMP runtime (via `*(IG+0x08)+0x90` int64 cam_id field): **28mm L16_02130** `vec[0..4] = {5,6,7,8,9}` = B1..B5; src1+src2 wrap A1. **70mm L16_03434** `vec[0..4] = {10,11,12,13,14}` = C1..C5; src1+src2 wrap B4. B-as-A architecture: same vtables, only input stream differs. | `iramp_camera_identity.md`. | ✅ (2 LRIs only) |
| M4 | IRAMP-side calibration dispatcher at `libcp+0x3f6170` filters cameras lacking CCM. **28mm L16_02130** passes cam_ids `[0,5,6,7,8,9]` = A1+B1..B5. **70mm L16_03434** passes `[8,10,11,12,13,14]` = B4+C1..C5. No fallback: `__cxa_throw std::out_of_range` at `0x3f6866`. A2+C6 dropped (no CCM). A3-A5 (28mm), B1/B2/B3/B5 (70mm) = RIC-processed but dropped at dispatcher. | LLDB BP at 0x3f6170. `a2_destination.md`, `c6_destination_and_depthcache.md`. | ✅ (2 LRIs only) |
| M5 | Refined B-as-A model (single canvas anchor, 6-cam fusion both zooms): 28mm = A1 anchor + B1..B5 contributors; 70mm = B4 anchor + C1..C5. Anchor pyramid descriptor at 28mm encodes 20×15 = 300 tile-cells = IRAMP invocation count. Visual confirmation in `puzzle_pieces/L16_03434_70mm_<CAM>.png`: B4 = full FOV, C5/C1 = zoomed sub-region inserts. | Combined M2+M3+M4. `puzzle_pieces.md`. | ✅ |
| M6 | IRAMP per-source weighting: 16-entry LUT applied per-pixel as separable spatial kernel — same LUT multiplied with each of 5 sources. No separate weight/coverage buffer. Per-source additive accumulation into per-tile scratch (5× addps+movaps on same buffer) within ONE IRAMP call. | `iramp_kernel_body.md`. | ✅ |
| M7 | IRAMP wavelet-domain super-resolution. Sub-stages `0x36cde0` (patch stats + CDF 9/7 match-score) and `0x36e530` (inverse-DWT synthesis + 5-band byte-LUT weighting). CDF 9/7 biorthogonal wavelet (JPEG2000 spec). Lifting constants at `.rodata 0x5cbfd0..0x5cc040`: `(1.5861343, 3.1722686, −0.05298011, −0.10596023, −0.8829110, −1.7658221, 1.1496044, 0.8698644)` — bit-exact JPEG2000 values. Hit counts (~6% partial run): `0x36cde0`=15,890; `0x36e530`=16,629; `0x36f800`=87. `0x36f800` = Catmull-Rom 64-LUT setup → dispatches uint8 luma-grid kernel at `0x36fd30` (NOT cross-camera merge — feeds PyramidAlignment/GetSkippingMaskGrid). | `sub_stages_36cde0_36e530_36f800.md`, `iramp_kernel_body.md` (v2 correction per Round 1). | ✅📐 |
| M7.1 | **IRAMP inner resample is BILINEAR (4 samples), NOT bicubic** — v1 naming of "bicubic resample at 0x369d70..0x369e2b" corrected per Round 1 cleanup. True Catmull-Rom bicubic is at `project_roi_to_camera @ 0x3e2e90` (separate path). | Round 1 banner on `iramp_kernel_body.md` + `iramp_integration_e2e.md`. | 📐 (correction of v1) |
| M7.2 | **28mm IRAMP takes single-anchor short-circuit path** that hides inner SAD/WTA/SubPixel/Bilinear stages (0 hits at those VAs). 70mm L16_03434 fires the full chain with 25+ hits at each VA. **Spike-blocker**: validation on 28mm only will miss bugs that only surface at 70mm. | Round 1/2 banners on `iramp_substages_verified.md`, `iramp_integration_e2e.md`, `iramp_28mm_short_circuit_gate.md`. | ✅ |
| M8 | Pyramid-level dispatch `PipelineCache::processLevel(int)` arg `eax` is render-stage code, NOT pyramid index. 28mm bridge HDR runtime distribution: `eax==0` → IRAMP `0x365960` (300 hits); `eax==1` → `0x3ebb80` single-source post-IRAMP reshape (348 hits = 48 L1 dispatch + 300 post-IRAMP via `initResAmp_1` lambda); `eax∈{2,3,4}` arm never fires at L16_02130 28mm bridge. `0x3d0650` = single-source pyramid-level resample primitive (370 hits). | `merge_function_reconciliation.md`, `pyramid_levels_characterization.md` (full bodies + per-level dims + RTTI-verified operator types: 0x3ebb80 = cubic B-spline/Mitchell-Netravali 64-entry LUT + single-source Halide dispatch; 0x3d0650 = pyramid read/resample primitive using `vec<Vec2i>` at cache+0x8/+0x10). | ✅ (L16_02130 28mm only) |
| M9 | **Scope-bound**: `lt::StackFusion` at `libcp+0x1b7d80` fires 0× on bridge HDR at L16_02130 28mm + L16_03434 70mm. Alternative codepath unverified (likely stack-LRI captures or Lumen GUI editing pipeline — NOT proven to be dead code globally). | `stackfusion_characterization.md`, `merge_string_inventory.md`. | ✅ scope-bound |
| M10 | **Scope-bound**: `lt::FusionCacheBayer::process` (vfunc 3) fires N=1 always on bridge HDR at the 2 tested LRIs (269 hits at 70mm). NOT the cross-camera merge for those tests. Not proven dead globally. | LLDB hit counts on L16_02130 + L16_03434. `merge_function_reconciliation.md`. | ✅ scope-bound |
| M11 | `initResAmp` at `libcp+0x3eb3c0` is src1/src2 IG construction site (two `Znwm(0x60)` allocations; vtables `0x65f668`/`0x65f6e8`). `PipelineCache::initFusion` (`libcp+0x3eb200`) is NOT a producer — FCB funcdata pointers at PC+0x238/+0x248 identical pre/post. | `anchor_prefusion_and_c6.md`, `composite_producer.md`. | ✅ |
| M13 | No separate anchor pre-fusion N→1 stage. L16 has exactly ONE multi-camera reduce: IRAMP. src1/src2 IGs = two views over the SAME single anchor camera's pyramid cache (A1 at 28mm, B4 at 70mm), rooted at `PipelineCache+0x170` = `lt::ReferenceImageCache`. Two vtables (`0x65f668` vs `0x65f6e8`) control sibling pyramid-tier lookup paths. Per-tile op at vt[+0x30] = `0x3ecc10`/`0x3ecd80`; vt[+0x18] never fires. | `composite_anchor_n1_reducer.md`. LLDB L16_02130 28mm + L16_00010 70mm. | ✅ (2 LRIs only) |
| M14 | Per-contributor photometric pre-norm INSIDE IRAMP at `libcp+0x3eced0`. `out = sqrt(max(0, in × IG+0x10))` per-channel SIMD (`mulps+maxps+sqrtps`). Alpha lane = 1.0 via 3× `insertps` with const from `0x5a8128`. IG+0x10 = effective-FOV ratio per C17. Dispatch chain: IRAMP body `0x366f1c` → `0x374ac0` → vt[+0x30] indirect → `0x3eced0`. Hit count: 1 per camera per pipeline invocation at 28mm L16_02130. | `ig_offset10_consumer.md`. LLDB read watchpoint on closure+0x30. | ✅ (L16_02130 28mm only) |
| M14.1 | **Composite-anchor pre-fusion kernel at `libcp+0x2b3410..0x2b3448`** — 4-input × weight SIMD accumulator (classic `movaps + mulps + addps + movaps` 4-way weighted blend). Consumes the 5 A-cam RIC L0 buffers (A1..A5 at 28mm) to build the `src1`/`src2` composite IGs that the IRAMP body at `0x365960` takes as its first two ImageGenerator inputs. Called from IRAMP body at offset `+0x5f0` (`libcp+0x365f50`). **This is the kernel that consumes "dropped" cams** (A2-A5 at 28mm) — they are NOT depth-only; they feed the composite anchor src1/src2 pre-fusion upstream of IRAMP. Hottest PC `0x2b341e` logged 20,351 watchpoint trips on dropped-cam RIC L0 buffers in 30% of a render; 100% of the 46 unique trip PCs trace through IRAMP-family code (zero non-IRAMP consumers). Refines M13 (`composite_anchor_n1_reducer.md` said src1/src2 wrap composite anchors; this locates the assembly kernel that does the pre-fusion). | Session 1 LLDB 2026-04-20 on L16_02130 28mm bridge HDR profile=3: `/tmp/l16_open_audit/session1/phase2_watchpoints.log` (102,361 trips), `session1/reclassified.txt` ("TRULY NOVEL: (none)"). Closes §4 OPEN-DROPPED-CONSUMER. | ✅ (L16_02130 28mm only; 70mm/150mm extension optional, see §4 open items) |

### 2.2 Per-camera ISP

| # | Finding | Evidence | Confidence |
|---|---|---|---|
| I1 | `lt::ReferenceImageCache` is a SHARED orchestrator (1 instance, 10 level-0 + 4 level-1 image buffers at 28mm; same at 70mm). Per-camera state in `r14` BayerPipelinePayload register, NOT in 10 RIC instances. Closure pointer at `LinearizeAndColorScale 0x340b00` is same across all LIN hits. | LLDB 70mm L16_03434: 48 processLevel hits / 10 worker threads, all `this*=0x7f7db5025200`. 31 LIN hits all closure `0x7fb1b70b7620`. `refcache_per_camera_isp.md`. | ✅ (2 LRIs only) |
| I2 | Per-camera ISP stage order (bridge HDR, LLDB BP-order at 28mm L16_02130): SourceImageCache ImageWarp<Bicubic,vec4x8ui,LensUndistortCRA> (0x261940) → STAGE0 LinearizeAndColorScale<uint16> (0x340b00) → STAGE1 <float> (0x340bf0) → STAGE2 ImageCorrectBayerPhaseAR1335 (0x340cc0) → STAGE5 setWhiteBalance::$_5 (0x340f70) → DemosaickLightV1 driver (0x2eb560) → STAGE6 setColorCorrection::$_6 (0x341040). RIC emits per-pyramid-level `Image<vec4x32f>` 4-ch f32 + caches `Tile<Vec3<Float16>>` 3-ch f16 packed (6 B/px) via `$_4` lambda for IRAMP. | `refcache_per_camera_isp.md`, `color_pipeline_audit.md`. | ✅ (L16_02130 28mm only) |
| I3 | `DemosaickLightV1` is the ACTIVE demosaic on bridge HDR. Driver `0x2eb560` = 889 hits at 28mm L16_02130. Three phase variants: V1<0,0> @ 0x2ed580 (176 hits), V1<1,0> @ 0x2eeb20 (636 hits dominant), V1<1,1> @ 0x2f0240 (299 hits). Template `<offX,offY>` encodes tile-origin Bayer parity. Phoenix needs ONE runtime-parameterized kernel, not 4 specializations. **Inner kernel is STATICALLY compiled SSE2 at `libcp+0x2eef80`** (Round 2 correction — JIT-wall was phantom; see `demosaicv1_jit_kernel.md`). V2 driver `0x2eba10` and V2 kernel `0x2f0df0` fire 0× on bridge HDR at L16_02130 + L16_03434 (scope-bound dead code). Inner kernel taps = 21-tap (NOT 9-tap) with verified coefficient pool `{+56, +6, -4, -2, 1/64 divisor}` at `__const` VAs `0x5f18c8/0x5aae70/0x5a8878/0x5a8874/0x5abed4`; scope = Bayer-row-phase-select parity at `0x2ec4f4`; 8 pointers in `0x2eef80` = 4-level pyramid × 2 row-cache views per level (NOT 7 / NOT channel-separator). | `color_pipeline_audit.md`, `session4_v1_linearize.md`, `demosaicv1_jit_kernel.md`, `demosaicv1_sub_kernels.md` (5 sub-kernels 2ebe90/2ebff0/2ec150/2ee070/2ee1e0 = buffer allocators, NOT channel separators), `demosaicv1_details_cleanup.md` (21-tap filter + parity select + 8-pointer map), Round 2 banner. | ✅ scope-bound |
| I4 | **Per-camera Bayer pattern** from `LightHeader.cam[i].field[13]` Point2I `sensor_bayer_red_override`. Value 0-3 → RGGB/GRBG/GBRG/BGGR. At L16_02130 there are at least 3 distinct patterns across 10 cameras: A1/A3/A4=GRBG, A5=GBRG, B1/B5=RGGB, B2/B3/B4=BGGR. Hardcoded "BGGR for all" in v1-prior was REFUTED. `BayerPhaseFix $_76 @ 0x34af10` + inner kernel `0x315b30` fire 0× at 28mm (Bayer-phase handled by V1 dispatch). | `calibration_audit.md` (with unit-bound banner per Round 1 L1). | ✅ (L16_02130 only; verify on other LRIs) |
| I5 | Vignetting runs on parallel `ThreadPool::TaskRange` worker path, NOT inline with Pipeline lambda dispatcher. `RemoveVignettingGeneric<vec4x32f, true>` @ `libcp+0x108080` fires with `mulps pixel × interpolated grid`. Per-tile dispatcher `0x345f30` fires 348× across 10 camera threads at 28mm L16_02130. Closure scale 0.7373 uniform across cameras. Direction = multiply. Three template variants: `<float,true>` @ 0x108370 (2249 hits pre-demosaic Bayer), `<vec4x32f,true>` @ 0x108080 (10,994 hits post-demosaic RGBA — dominant), `<vec4x32f,false>` @ 0x1086c0 (391 hits). Fires for full 10-cam set including A2 (the IRAMP-stage filter at 0x3f6170 does NOT apply here). | `vignetting_runtime_corroboration.md`, `refcache_per_camera_isp.md`. | ✅ (L16_02130 28mm only) |
| I6 | `LensUndistortCRA::operator()` at `libcp 0x261940` is a pure radial geometric warp (3×3 homography → perspective divide → 4096-LUT), NOT a Bayer channel mixer. The 13×17×4×4 cra_grids data goes to a different stage. | `calibration_audit.md`. | 📐 |
| I7 | 13×17×4×4 cra_grids consumed by `RemoveCrossTalkGeneric` (electronic cross-talk), NOT by LensUndistortCRA. **Scope-bound dead**: on bridge HDR at L16_02130 + L16_03434 this stage fires 0× (per L5). May fire in GUI-editing-pipeline tunings — that path untested. | `calibration_audit.md`, `cross_talk_correction.md`. | 📐 + ✅(0-scope-bound) |
| I8 | `PipelineCache+0x170` = `shared_ptr<lt::ReferenceImageCache>`. Writer at `0x3ea83d` inside PC ctor `0x3ea7d0`. `lt::ReferenceImageCache` vtable at `0x66b200`. | `refcache_per_camera_isp.md`. | ✅ |
| I9 | `lt::SourceImageCache` (SIC) tree at `RIC+0x30` holds 5 contributor IGs. Node+0x20 = cam_id, node+0x28 = SIC*. SIC vtable `0x65f490`, init `0x3e0330`. LLDB BP at 0x3e0735 captured 5 SIC ptrs with cam_ids {5,6,7,8,9} at 28mm L16_02130. | `sourceimagecache_writer.md`. | ✅ (L16_02130 28mm only) |

### 2.3 Color (AWB / CCM / tone curve)

| # | Finding | Evidence | Confidence |
|---|---|---|---|
| C1 | **AWB direction = MULTIPLY BY RECIPROCAL of stored gain.** Runtime `context_ptr[0..3] = (0.5821, 1.0, 0.6294, 0.3630)` at AWB stage `0x340f70` for L16_02130. `0.5821 = 1/1.7178`, `0.6294 = 1/1.5888` — exact reciprocals of Block 8 stored gains. | `color_pipeline_audit.md`. | ✅ (L16_02130 only) |
| C2 | LRI Block 8 `f19.f15` = `[R_gain, 1.0, 1.0, B_gain]`. L16_02130 file offset `0x09b189d8`: `{R=1.648295, G1=1.0, G2=1.0, B=1.778951}`. Reciprocals match runtime to 5+ decimals. `divss` computed ONCE at pipeline setup, not per-pixel. | LLDB + LRI binary inspect. `color_pipeline_audit.md`. KMS f4284bc2. | ✅ |
| C3 | **CCM application in CHROMATICITY space**, NOT RGB→RGB. Per-pixel kernel at `libcp 0x350c56`: `out = M_blend @ (R/G, 1.0, B/G)`, output `(out[0], 1.0, out[2])`. Green forcibly 1.0 via `350cdd: mov [r14+0x4], 0x3f800000`. Phoenix CCM must be `(R/G,1,B/G) → 3×3 → (out0, 1.0, out2)`. | `ccm_factory_to_runtime_transformation.md`. | 📐 |
| C4 | **CCM lerp = mired-space MatLerpClamped** at `libcp 0xab720`: `M_out = M_B + α·(M_A − M_B)` with `α = clip((1/T − 1/T_B)/(1/T_A − 1/T_B), 0, 1)`. Endpoints via `CCMInterpBetweenCalib` at `0x350bc0`. NO extrapolation; clamp at endpoints. | `ccm_factory_to_runtime_transformation.md`. | 📐 |
| C5 | **CCM source = Block C field 3 `color_matrix`**, NOT field 2 `forward_matrix`. Bit-exact match between Block C field 3 and runtime `ctx[+0xdc]` (max_abs_diff=0.000). The 0.7954 max_abs_diff bug was comparing wrong field. | `ccm_factory_to_runtime_transformation.md`. | ✅ |
| C6 | Calibration block layout (L16_02586 + L16_02500 + L16_02130): Block 3 @ 162,291,712 (32,832 B, 16 records) = geometric+Bayer; Block 4 @ 162,324,576 (262,969 B, 16 records) = vignetting+CRA; Block 6 @ 162,589,394 (35,266 B, 42 records = 14×3 cams×illums) = CCM. Field paths: vignetting `rec.f4.f2[ch].f2.f3` = 884 B = 221 f32 → (17,13); CRA `rec.f4.f1.f4` = 14,144 B = 3,536 f32 → (13,17,4,4); CCM `f2.f2` = 45 B per entry. Block 6 detection: `n13 ≥ 36`. | KMS 91839eb8, `cal_color_l16_02130.npz`. | ✅ |
| C7 | CCT reverse computation `CCTFromChromaticity(Vec2 xy) @ 0xab2e0` runs 30-iteration Robertson search over 31-entry `(u,v,slope)` table at `0x66d410` (bss, runtime-populated). Constants: 175, 0.20525, 0.31647, −0.84901 (uv' transform), 1e6 (mired→K). Input `(x,y) = auto_white_balance.neutral_color` protobuf at `0x13eda0`, NOT computed from AWB gains. libcp NEVER computes CCT from pixels. | KMS f99bc8a7. | 📐 |
| C8 | CCT forward `ChromaticityFromCCT_Tint @ 0xab130` from `setWhiteBalance::$_20 @ 0x342a80`. Walks 28-entry × 16-byte forward table at `0x66d420` (different from 0x66d410). Reads `(CCT, tint)` from `Pipeline+0x15d0/+0x15d4`. Writer: `0x33ead0` from `0x318847` inside `fromProtoConfig @ 0x3184d0`, gated by `Pipeline[0x1530]==3` (AWB type=manual_temp). Sources: `auto_white_balance.neutral_temp`, `.neutral_tint`. Default **CCT = 4300 K** when not set. The previously documented `(CCT−4000)/2500` formula was FABRICATED. | KMS ed20c8aa. | 📐 |
| C9 | CCT effective state on this corpus: observed `ctx[0x0c]=0.36895, ctx[0x10]=0.21384` at runtime on L16_02130 — `(x,y)` chromaticity from Kim's Planckian polynomial for T≈4280K. The earlier "always D65" conclusion from the 9438-LRI scan was wrong: libcp computes a non-trivial blend even when `neutral_color` absent, falling back to 4300K default. | `session5_cct_derivation.md`. | ✅ (L16_02130) |
| C10-C15 | Tone curve mechanics: LUT-apply lambda at `0x2d7a30` (per-tile post-demosaic, vec4x32f in/out). Driver `LinearTMO::process @ 0x2d7780`. Pre-shaper body `0x2d7c90..0x2d7f44`: `u=0` if `x≤0.0025`; `(x−0.0025)²·100.50251` if `0.0025<x<0.0075`; `(x−0.005)·1.0050251` if `x≥0.0075`; `LUT_idx = clip(u·1024, 0, 1023)`. Alpha preserve via `blendps $0x8, %xmm10`. EV multiply: `mulps %xmm15, %xmm1` with `xmm15 = exp2f(TMO+0x20)` (= exp2f(Settings.exposure)). LUT linear interpolation: `movss (rbx,rcx,4); movss 0x4(rbx,rcx,4); subss; mulss; addss`. Bridge default = `light_v1 @ 0x5e41b4` (verified via ground_truth.tiff ProfileToneCurve match). 4 LUTs: `acr 0x5e31b0`, `light_v1 0x5e41b4`, `light_v1_lowlight 0x5e51b8`, `light_v2 0x5e61bc`. Defaults function at `0x3c7860` via `isLowLight()`. y(0.18) values: acr=0.379, light_v1=0.203, light_v1_lowlight=0.377, light_v2=0.201. | KMS ef06bd6a, 9408f4cd, e24fa9ce. | ✅📐 |
| C16 | Per-camera radiometric is distributed across: (a) AWB reciprocal (C1), (b) CCM mired-lerp (C3-C5), (c) vignetting multiply (I5), (d) per-contributor FOV pre-norm `sqrt(max(0, in × FOV_ratio))` at 0x3eced0 (M14). NOT a single radiometric stage. | `per_camera_radiometric_weight.md`, `ig_offset10_consumer.md`. | ✅ |
| C17 | IG+0x10 = effective-FOV ratio per contributor camera. Writer `libcp+0xe67c0` called from `PropertyAccessor::transform ~0x3eb836`. Formula: `(ref_dim×ref_scale)/(this_dim×this_scale)×optional_exposure`. Captured: 28mm B-cams ~0.50; 70mm C-cams ~0.75-0.84. src1/src2 IG+0x10 = 0.0 (anchor self-ratio sentinel). | `ig_offset10_scalar.md`. | ✅ |
| C18 | Per-tile CCM kernel = `ImageConvertColorSpace::$_0` at `libcp+0xbf4a0` (vtable slot 6 of `0x6527c0`), dispatched via `ImageConvertColorSpace` at `0xa9f20` (Halide dispatcher 0x5440). 370 tile-level hits on L16_02130 28mm. Closure capture[3] at `[closure+0x20]` = CCM matrix ptr. **Only 2 distinct CCM matrices** applied across 370 invocations (70 + 300 split). `CCMInterpBetweenCalib` at `0x350bc0` fires 5×, all overwrite the same buffer → single consolidated M per pass. `ImageApplyColorMatrix_3x3_mask` @ 0x300570 and `setColorCorrection_58_Color` @ 0x3466d0 fire 0× on bridge HDR at tested LRIs. | `imageapplycolormatrix_va.md`, `q12_ics_kernel_28mm.md` (manual-BP re-verify 2026-04-18 on L16_02130: 324 hits / 3 ptr-distinct / **2 value-distinct** CCMs; hit-count delta vs 370 attributed to thread-scheduler serialization under manual stop-continue). | ✅ (L16_02130 28mm only) |

### 2.4 Calibration

| # | Finding | Evidence | Confidence |
|---|---|---|---|
| K1 | **Black level = 42.0, white level = 1023.0** (sensor AR1335, global per K1 per v1). ⚠ The BLC KERNEL VA and FORMULA are OPEN — see §4 OPEN-BLC. | KMS ac60e123. Binary constants 42.0f/1023.0f appear exactly once each in libcp (provable absolute), both at `libcp+0xdf6d2` inside the `0xdf5d0` per-cam-id BL/WL allocator. `1/981 = 0x3a85bb38` is ABSENT from libcp static disasm. `blc_correction_OVERRIDE.md` (Round 4 late-revision, 2026-04-19): strong hypothesis is linear `(raw_uint16 − 42.0f) × (1/981.0f)` computed LIVE via `subss+divss` at `0x2d051f` inside `0x2cffd0` (stats kernel) — but 0x2cffd0 registered 0 hits under tested HDR profile=3 conditions (untested: profile=2 LDR, GUI path). | ✅ value; ⚠ OPEN kernel+formula |
| K2 | Vignetting: 16 cams × 4 ch × (17,13) f32. Center=1.0; corners 2.0–3.8×. Two profile families: 1-channel (A1,A2,A5,B3,B4,C2,C3,C5) corners 1.4–3.9; 4-channel (A3,A4,B1,B2,B5,C1,C4,C6) corners 1.1–2.0. Path `rec.f4.f2[ch].f2.f3`. Multiply direction. Application: `RemoveVignettingGeneric 0x108080`. | KMS 91839eb8, `cal_color_l16_02130.npz`. Unit-bound: L16_02130 / Unit A per Round 1. | ✅ (L16_02130 only; per-unit variance likely) |
| K3 | CRA grids: 16 cams × (13,17,4,4) f32. Center diagonal ≈ [1.0, 1.003, 0.997, 1.0]. Path `rec.f4.f1.f4`. Consumed by `RemoveCrossTalkGeneric` (I7) — NOT by `LensUndistortCRA` (I6). | KMS 91839eb8, `calibration_audit.md`. | ✅ |
| K4 | CCM matrices: 14 cams × 3 illuminants × (3,3) f32. **A2 (cam_id 1) + C6 (cam_id 15) absent — NaN entries.** Illuminant order NPZ: [0]=TungstenA, [1]=D65, [2]=F11. Block 6 detection: `n13≥36`. A1 D65 example: `[[0.900,0.132,−0.067],[0.310,1.074,−0.384],[−0.057,−0.430,1.313]]`. Unit-bound: L16_02130 / Unit A per Round 1 L2. Per-unit CCM variance highly likely. | KMS 91839eb8. | ✅ (unit-bound) |
| K5 | Per-LRI calibration parser is a REQUIRED Phoenix stage. Every LRI is self-contained; cal is per-device factory baked per LRI. Phoenix MUST parse Blocks 3/4/6/8 from each input at render time. `cal_color_l16_02130.npz` = reference extract, NOT runtime input. | KMS 5e9c43f8 + Rule #0. | ✅ |
| K6 | **LightHeader field-identification corrections** (from `lightheader_field16_23.md` + `hwinfo_field_18.md`, post-v1): Field 16 = `sensor_data: ltpb.SensorData` (universal per-ISO AR1335 noise model, lives in OWN LELR block — NOT in per-shot LightHeader). Field 18 = `hw_info: ltpb.HwInfo` (per-shot, 48–54 B, 4-5 sub-byte-fields with 2 small varints — sub-schema NOT decoded). Field 23 = `imu_data: ltpb.IMUData` (per-shot rolling-shutter 18-19 accel+gyro samples; NOT proto2-groups, NOT per-focus black-level, NOT spectral calibration). The earlier "Field 16 = focus-distance LUT" and "Field 23 = spectral or per-focus calibration" from legacy doc 09 were REFUTED. Phoenix MVP can safely ignore Field 18 HwInfo. | `lightheader_field16_23.md`, `hwinfo_field_18.md` (2026-04-19). | ✅ identified; sub-schema ⚠ |

### 2.5 Firing rules / camera config

| # | Finding | Evidence | Confidence |
|---|---|---|---|
| F1 | **Empirical firing scan across 9390 LRIs** (full archive): 28mm=2424 LRIs, dominant 5A+5B @ 98.5%; 35mm=3240, dominant 5A+5B @ 99.5% (IDENTICAL to 28mm); 70mm=1915, dominant 5B+6C (11 cams) @ 74.2%; 150mm=1797, dominant 5B+6C @ 96.0%. Sharp transition at `zoom_val=70`: <70 → 5A+5B; ≥70 → 5B+6C. ZERO LRIs fire C alone at any zoom. | `lightheader_camera_scan.md`. DB integrated in `lri_catalog.db`. | ✅ archive-scan |
| F2 | Only 2 firing modes: wide = 5A+5B, tele = 5B+6C. B is constant across zooms. Phoenix needs ONE merge function parameterized by `(anchor_group, partner_group)`. | F1 + `puzzle_pieces.md`. | ✅ |
| F3 | C6 IS active at 70mm/150mm. L16_03434: C6 pixel data 99.83% non-zero. L16_02285: 99.82%. Geometric cal covers all 16 including C6. C6's exclusion from CCM block (14 cams) is a factory unit-cal decision, NOT hardware absence. C6 then dropped at IRAMP dispatcher (M4) because no CCM. | `c6_verification.md`, `c6_destination_and_depthcache.md`. | ✅ |
| F4 | Camera ID mapping: A1=0..A5=4, B1=5..B5=9, C1=10..C6=15. Per-cam record fields: `f9.f4`=bpr (5200 for W=4160 PACKED_10BPP), `f9.f5`=data_offset, `f13`=`sensor_bayer_red_override` Point2I. | KMS ac60e123, `calibration_audit.md`. | ✅ |
| F5 | Movable-mirror cameras: each has exactly ONE `R_fold` — fixed pointing. 4 encoder configs per camera control **focal position only**, not pointing. Azimuth permanently fixed at factory cal. Config selection: `argmin(|encoder − nominal[i]|)`. (Config 2/3 do NOT have "wide park"/"tele park" semantics.) | Closed OQ-B 2026-04-12, batch-verified 10 files per zoom. | ✅ |

### 2.6 Depth

| # | Finding | Evidence | Confidence |
|---|---|---|---|
| D1 | **Scope-bound**: depth FIRES on bridge profile=3 (verified across 4 scenarios on L16_02130 28mm + L16_03434 70mm — with/without prior `--depth` flag, with/without `.lris`). Real DepthCache ctor body at `libcp+0x3d8780` (NOT `0x3eaf00` — that's a PipelineCache thunk). StereoAsyncAPI C1 @ 0x3f46d0 fires 1×; `Triangulator::refine3dPoints` @ 0x20ca00 fires 1-2× (outer) / 4-5× (inner = partner-cam count). Profile=2 CAMERA does NOT fire depth (0 hits at tested LRIs). CIAPI::DepthEditor 14-method GUI surface fires 0× on bridge (that's depth-EDIT API, not depth-COMPUTE). | `depth_unlock_verification.md`, `profile2_camera_characterization.md`, 28mm depth populator agent. | ✅ scope-bound (2 LRIs + profile=3; untested: 35mm, 150mm, profile=2 depth behavior beyond the 0-hits, GUI live-preview) |
| D2 | `ImageDecodeBayerJPEG` is in libcp (NOT liblricompression). liblricompression's `libceres` link is ornamental. | `depth_editor_and_iramp_depth.md`, `LIBRARY_INVENTORY.md`. | ✅ |
| D3 | Ceres = **5 distinct AutoDiffCostFunction types** (NOT 18 — the 347 runtime AddResidualBlock count was loop-driven instantiation per Round 2). Pass A: `LabCostFunction<25,9>` @ 0x11749a — factory color cal; Phoenix skips. Pass B: `CameraProjection<2,1,1,2,3,3,3> + EntrancePupilCost<3,3,3> + IntrinsicsCost<3,1,2>` @ 0x201a4f — factory bundle adjustment; Phoenix skips. **Pass C: `ReProjectionCost<2,1>` @ 0x20d1ac** = `lt::Triangulator::refine3dPoints` = per-point bounded 1-DOF Cauchy-weighted depth refinement. Phoenix reimplements with `scipy.optimize.least_squares(loss='cauchy', f_scale=?, bounds=(lo,hi))`. ⚠ **`f_scale` value is OPEN** — see §4 OPEN-FSCALE. LabCostFunction Evaluate body located at `libcp+0x11ae40` (vtable[2] at `0x6534a0`): 25 patches × 1 scalar residual each = `sqrt(weight) * CIEDE2000(predicted_Lab, target_Lab)`; CIEDE2000 helper at `libcp+0x1273c0` (constants 25^7, 7.0, π, 2π, 500, 200 present). | `ceres_analysis.md`, `ceres_evaluate_bodies.md`, `ceres_residual_bodies.md`, `laplacian_collapse_and_lab_layout.md` §B (LabCostFunction Evaluate VA + 25-residual layout + CIEDE2000 helper), Round 1/2. | ✅ classes; ⚠ f_scale open |
| D4 | Two-gate filter at SIC init `libcp+0x3e0330` prevents `SourceImageCache` creation for cameras IRAMP won't consume. Gate 1 (`0x3e0412`): `[rax+0x30]` active/CCM flag. Gate 2 (`0x3e044a`): class-match filter (skip if cam-class == anchor-class via mapper `0xf6c60`). Per-zoom SIC-tree: 28mm={B1..B5}; 35mm={A1+B1..B5}; 70mm/150mm={C1..C5}. Cameras failing either gate still go through per-camera ISP and have RIC L0 buffers populated but cannot be consumed via SIC tree. A cameras are NOT fired at all at 70mm/150mm (sensor activation, not just filtering). | `depth_fate_cross_zoom.md`. | ✅ (structural verified 2026-04-18) |
| D5 | **NARROW finding — scope-critical**: Across bridge HDR at the 4 zoom tiers tested, the sole caller of SIC `vt[+0x30]` bodies (`0x3ecc10`/`0x3ecd80`) and per-contributor prenorm body (`0x3eced0`) is `libcp+0x374cf3` (IRAMP dispatch helper). **Scope limitation (critical)**: probes did NOT instrument (a) other SIC vtable slots, (b) direct (non-vtable) reads of RIC L0 buffers, (c) AWB path, (d) HDR exposure-bracket fusion, (e) noise/SNR averaging, (f) Lumen.app GUI path. Light Inc marketed all 16 cameras as contributing to image quality — dropped cams' RIC L0 buffers MUST have a consumer somewhere. **Q-DROPPED-CONSUMER (open)**: find where dropped cams' L0 buffers are actually read via hardware watchpoint. **Phoenix MUST NOT skip per-camera ISP for dropped cams until Q-DROPPED-CONSUMER closes.** | `depth_fate_cross_zoom.md`. Rich correction 2026-04-18. | ✅ scope-bound; conclusion deliberately narrowed |
| D6 | Bridge `lri_process` is a Claude-written test harness, NOT Lumen.app. Calls `Renderer::render` + `writeImage` only — SUBSET of libcp's invocation surface. Bridge color-output MAD=0.067% vs Lumen GUI validates COLOR only, not depth. "DepthCache 0 hits on bridge" findings in prior sessions were scope-bound to bridge's invocation pattern, not proof of dead code. Depth IS in libcp; bridge just never reached it before profile=3 path was identified. | `lumen_app_vs_bridge_delta.md`. Rich correction 2026-04-18. | ✅ |
| D7 | Depth gate at `libcp+0x3b2fa3`: `[imageStorageObj+0] & 0xf == 0x3` via `call libcp+0x40b010`. Profile=3 DESKTOP → depth fires. RendererPrivate+0x774 (setMode target) is a different render-property, NOT depth gate. Call chain: RendererPrivate vtable slot 20 @ 0x3b1d20 → gate 0x3b2fa3 → StereoAsyncAPI C1 @ 0x3f46d0 (site 0x3b3011) → C2 @ 0x3f2c40 → DepthCache ctor @ 0x3d8780 → Triangulator::refine3dPoints @ 0x20ca00. **SGM-as-algorithm = REFUTED-AS-DISPATCH**: string at `libcp+0x632901` is ERROR GUARD inside function `0x267e80` that throws runtime_error; 0x267e80 fires 0× on bridge profile=3 at tested LRIs. The 7 "state machine handlers" at 0x229d80..0x22aee0 are 4-instruction push/pop/ret STUBS (dead vtable entries). Real dispatch: StereoAsyncAPI C2 → `0x3d01b0` → Halide AOT dispatcher `0x5440` with closure vtable `0x66a618` ("stereo cost evaluator"). Algorithm class lives in Halide-generated machine code body — NO named C++ matcher class exists in libcp strings (0 hits for PatchMatch/Census/SGBM/NCC/GraphCut/PMVS/planeSweep). Identifying the algorithm requires disassembling the Halide kernel body (out of scope for current investigation). DepthCache `[+0x90]=0xa` is max-pair CAPACITY, not active count. | `depth_unlock_verification.md`, Round 4 precision banners. | ✅ algorithm-class pending |
| D8 | cam_id field offset = `[per_cam+0x60]` uint32. Getter `libcp+0xf2720`: `movl 0x60(%rdi), %eax; retq`. Used across 7+ sites; enables cross-zoom CCMInterp cam_id attribution. | `q10_ccminterp_70mm_v6_live.log` 2026-04-18. | ✅ |
| D9-D11 | **Path A cost functor** builder at `libcp+0x30b770` (4-stage setup: alloc buffer → 2-bit dispatch → build 0x38 closure → 0x5440 tile dispatch). 2×2 variant dispatch at 0x30b801 (flags from `[rdx]`/`[rdx+4]`; OR≥2 → bail): (0,0)→`0x30b9f0` (Laplacian SAD + chromatic L2), (0,1)→`0x30dcc0`, (1,0)→`0x30ff60`, (1,1)→`0x3121f0`. 3 static call chains: (A) ISP renderer `0x406960` → `0x1ab2d0` → `0x1ac010` → `0x1ac1ac → 0x30b770`; (B) `0x1b92d0` @ 0x1b934c; (C) Demosaicking `0x27b7a0` → `0x31b470` → `0x3403f0` → `0x343ef8 → 0x30b770`. All static. **Variant flag semantics NOT decoded.** ⚠ **Path B2 @ 0x2732f0 also fires on depth path** (Round 3: 0x2730c0 is count==4 specialization that NEVER fires on L16; 0x2732f0 fires instead). TRUTH v1 only covered Path A; v2 flags Path B2 as additional active depth cost — invocation count + relationship to Path A unclear. Path A classification: derivative-domain integer SAD with WTA + rsqrtps-based chromatic L2 normalize — NOT raw SAD / Census / NCC (`depth_cost_algorithm_classified.md` LLDB 2026-04-18 on L16_03434 70mm, superseded-banner preserves dual-path framing). Fusion-site investigation for Path A vs Path B2 outputs is UNLOCATED within 25-min budget (`dual_cost_fusion_site.md`, 2026-04-18); hypothesis = confidence-weighted MIN reduction, candidate site = `libcp+0x3bcf20` startRendering::$_8 case-4 handler — NOT verified. | `path_a_call_chain_round3.md`, `do_work_lambda_decode.md` (Round 3 banner), `dual_cost_path_classifier.md`, `depth_cost_algorithm_classified.md`, `dual_cost_fusion_site.md`. | 📐 Path A; ⚠ Path B2 needs LLDB; ⚠ fusion unlocated |

### 2.7 Outliers / variant formats

| # | Finding | Evidence | Confidence |
|---|---|---|---|
| O1 | ~180 LRIs (1.8% of archive) = distinct file format (LELR offset-6 byte = `0x10`). Patterns: `B1-B5, C2, C5` (86 files, 7-cam tele), `A1, A5, B2, B4, B5` (59 files, 5-cam), `B2, B4, B5, C5` (23 files, 4-cam tele). 2017-12-09 to 2021-03-06; temporally interleaved. Every outlier has B4+B2+B5 (B-tele core). Phoenix can ignore per outlier-deprioritization rule. | `zoom_35mm_and_outliers.md`. | ✅ |
| O2 | 244-file BJPG cluster (Burst JPEG): LELR data blocks contain `BJPG` magic at +32. Structure: 1,576 B index + 80 concatenated JFIF JPEGs. Quality 68–84, tile 1024×512. ~302 files post-2018-06-26, firmware v0.2+. Phoenix skips on 2018-normal decode. | OQ-E close. | ✅ |
| O3 | L16_01853 (zoom=96) = special 4-frames-per-camera mode, `bpr=0`, ~5.4 MB per-frame stride. | KMS ce238bd9. | ✅ |
| O4 | Unknown format (transitional firmware 0.1.x): 515 files 2018-03-30 to 2018-06-26. Stride 10,485,764 B/cam, 8 cam/chunk, W=4160, bpr=5200, H_int=2016. Same 10-bit MIPI. 3-LELR-chunk. CORRECTION: 2018-normal H_int=1950 (not 2473). | OQ-E close. | ✅ |

### 2.8 Zoom / crop / canvas

| # | Finding | Evidence | Confidence |
|---|---|---|---|
| Z1 | **Two-tier focal-length canvas architecture.** Reference focal is tier-table-driven at `libcp+0xe7020` via `*(int*)0x44(image)` enum cases 0/1/2. Tier 0 (28mm-anchor): used at 28mm (RectF=(0,0,1,1), 10432×7824, 300 tiles 20×15) + 35mm (RectF=(0.0957,0.1045,0.8957,0.9045), 8345×6259 internal, 234 tiles). Tier 1 (70mm-anchor): used at 70mm (RectF=(0,0,1,1), ~8848×6624, 221 tiles 17×13) + 150mm (RectF=(0.2668,0.2673,0.7332,0.7327), 4865×3641 internal, 63 tiles 9×7 — ratio 70/150=0.466). | `35mm_renderer_mechanism.md`, `tone_curve_location_and_zoom_crop.md`. | ✅ |
| Z2 | Focal-length crop computer `libcp+0xe6d90` reads `image_focal_length` at `Image+0x40(rsi)`, divides reference_focal/image_focal, writes centered normalized RectF to Transform. `Renderer::render` invoked with same `ROI=(0,0,65536,65536)` at all focal lengths — crop on internal Transform. | `35mm_renderer_mechanism.md`. | ✅ |
| Z3 | IRAMP iteration counts: 28mm=300, 35mm=234, 70mm=221, 150mm=63. (Tracks tile-grid dims, not a simple `(28/focal)²` formula.) | LLDB hit counts. | ✅ |
| Z4 | Bridge `lri_process` upsamples cropped FOV to hardcoded `Point<int> outsize={10432,7824}` (lri_process.cpp:640). Lumen GUI likely calls `writeImage` with focal-aware Point<int>. Phoenix should match internal cropped resolution OR provide focal-aware outsize. | `35mm_renderer_mechanism.md`. | ✅ |
| Z5 | 35mm = 28mm pipeline + crop. No 35mm-specific functions/symbols/strings in libcp. B cameras at 35mm use encoder config 2 (same as 28mm wide park). | F1 + Z1 + string scan. | ✅ |

### 2.9 Container / library inventory

| # | Finding | Evidence | Confidence |
|---|---|---|---|
| L1 | Canvas geometry: 10432×7824 base, fx=8457.2px, hFOV=63.33°, vFOV=49.65° (pre-crop; see Z1). | OQ-closed 2026-04-12. | ✅ |
| L2 | Bridge `lri_process.cpp` reproduces ground truth at 10432×7824 with **MAD = 0.067% vs Lumen GUI**. Bridge IS valid ground-truth source. | OQ-closed. | ✅ |
| L3 | LRI formats: 2017-era, 2018-normal, WDR confirmed. 2018-normal: stride 10,616,832, W=4160, H=3120. | OQ-E close. | ✅ |
| L4 | 16 ISP stage names confirmed via C++ RTTI. Two tiers: base (bridge-accessible) + GUI-only editing. | From prior. | ✅ |
| L5 | **Scope-bound**: stages `RemoveCrossTalkGeneric`, lens shading, hot-pixel fire 0× on bridge HDR at L16_02130 + L16_03434. Fire in specific tunings (GUI editing) — that path untested. NOT proven dead globally. | `refcache_per_camera_isp.md`. | ✅ scope-bound |
| L6 | **Scope-bound**: Phase B (MonoFusion/MonoMerge grayscale path) does not emit on bridge HDR color-output path at tested LRIs. Phoenix skips lambdas `$_7`/`$_8`. NOT claimed dead globally. | KMS 6e7523df. | ✅ scope-bound |
| L7 | Public API (411 symbols) + `CIAPI::DepthEditor` 11-method surface in `LIBRARY_INVENTORY.md` still valid. | Reference-only per Rule #0. | ✅ |

---

## 3. Refuted Claims (v1 R1-R19 + cleanup-round additions R20+)

Carries v1 rows R1-R19 intact (see `archive/TRUTH-v1-phoenix-truth-2026-04-17.md` §3). Additional rows from April-19 cleanup rounds:

| # | Old claim | Refutation |
|---|---|---|
| R20 | "IRAMP inner resample is bicubic at 0x369d70..0x369e2b" (v1 M7 phrasing) | **REFUTED Round 1.** BILINEAR (4 samples). True Catmull-Rom bicubic at `project_roi_to_camera @ 0x3e2e90` is a distinct path. `iramp_kernel_body.md` SUPERSEDED banner. |
| R21 | "Denoiser is BM3D-flavored" (`vst_consumer_chain.md` prior claim) | **REFUTED Round 3.** NLM-4 with 4 novel modifications per `nlm_bm3d_denoiser.md`. |
| R22 | "DOF row-thunks contain per-pixel disc gather" (`disc_far_halide_blob.md` prior) | **REFUTED Round 3.** Row-thunks = pipeline glue only per `dof_leaf_kernels.md`. |
| R23 | "Path B at libcp+0x2730c0 is active cost kernel" (`do_work_lambda_decode.md` prior) | **REFUTED Round 3.** 0x2730c0 is count==4 specialization that NEVER fires on L16 (count > 4 always at the tested LRI). Active Path B2 = `libcp+0x2732f0`. |
| R24 | "3-boolean toggle = Gray-code 2³=8 pass-type traversal" (`disparity_search_loop.md` prior) | **REFUTED Round 3.** Actual = 2-state lock-step XOR alternation. |
| R25 | "libcp+0x275630 = unknown intermediate / candidate range-seeder" | **REFUTED Round 3.** PerTileState in-place constructor; all 4 candidate roles rejected. `x275630_and_3bool_toggle.md`. |
| R26 | "Field 23 IMU samples stored as raw float bytes in consumer heap" | **REFUTED Round 3.** Raw bytes NOT in heap; consumer transforms eagerly at parse OR parses lazily on demand. `imu_consumer_va.md`. |
| R27 | "SGM identified per lumen_depth_algorithm.md" (Round 2 interim acceptance) | **REFUTED Round 4.** SGM-as-algorithm = REFUTED-AS-DISPATCH. 0x267e80 fires 0× on bridge profile=3 at tested LRIs; string is ERROR GUARD, not active dispatcher. Real algorithm class is in Halide kernel body at `0x3d01b0` with closure vtable `0x66a618` — NOT a named C++ matcher class. |
| R28 | "BLC uses Anscombe/VST per-ISO LUT at libcp+0x5ad26c" (Round 1 hypothesis) | **REFUTED Round 2 LATE REVISION.** `0.375 (= 3/8 signature)` appears 0× in libcp. "vst invalid!" strings belong to SEPARATE dark-current correction stage. 28-record per-ISO table at `libcp+0x66d670` is dark-current correction, NOT BLC. `blc_correction_OVERRIDE.md`. ⚠ BLC kernel identity reverted to LINEAR `(raw-42)/981` hypothesis — see §4 OPEN-BLC. |
| R29 | "JIT wall blocks DemosaicV1 kernel" | **REFUTED Round 2.** DemosaicV1 inner kernel is STATIC SSE2 at `libcp+0x2eef80`. Prior agents misread `std::function::operator()` indirect dispatch as JIT mmap. `demosaicv1_jit_kernel.md`. |
| R30 | "18 distinct Ceres cost function pointers" (v1 D3 phrasing prior to cleanup) | **REFUTED Round 1/2.** Only **5 distinct classes** statically (LabCostFunction, CameraProjection, IntrinsicsCost, EntrancePupilCost, ReProjectionCost). 347 AddResidualBlock count was loop-driven instantiation. |
| R31 | "Bayer pattern: BGGR (value 3) for all 16 cameras — sensor-wide constant" | **REFUTED (v1 I4 already caught this but worth restating).** Per-camera from `LightHeader.cam[i].field[13]` Point2I `sensor_bayer_red_override`. At L16_02130: A1/A3/A4=GRBG, A5=GBRG, B1/B5=RGGB, B2/B3/B4=BGGR. |
| R32 | v1 absolute-language in D1/D5/L5/L6 ("depth is GUI-only", "0 hits means dead code") | **SCOPE-BANDED v2** per Rich's Round 4 rule ("if your paraphrase sounds like an absolute that's a problem"). All 0-hits claims now scope-bound to (LRI + focal + profile) with untested axes enumerated. TRUTH was explicitly OFF-LIMITS during Round 4; v2 finally applies it. |

---

## 4. Open Questions (verified-still-unknown) — MUST close before spike

v1 carried Q5, Q7, Q9, Q10, Q11, Q12. v2 expands:

| # | Question | Why blocks spike | Path |
|---|---|---|---|
| Q5 | `RemoveCrossTalkGeneric` exact VA + bridge activation | If fires on bridge and consumes cra_grids, Phoenix must wire up; if GUI-only (L5 scope-bound), Phoenix omits. | RTTI scan for `RemoveCrossTalkGeneric`; LLDB BP each candidate (0x101830-region) on bridge HDR. |
| Q7 | `auto_white_balance.neutral_color` on captures that DO persist it | Affects color accuracy for non-default captures. | LRI scan for non-empty `neutral_color`; LLDB 0x13eda0 + write-watch. |
| Q9 | Which of 7 callers of `ImageConvertColorSpace` (`0xa9f20`) fires on bridge HDR? | Localizes CCM in stage order (pre-IRAMP per-cam vs post-IRAMP global). | LLDB BP at each caller (0xaa238, 0x2d7287, 0x2d8013, 0x3467ba, 0x34698f, 0x3470b9, 0x347318); tally per-caller. |
| Q10 | Why `CCMInterpBetweenCalib` fires 5× on L16_02130 28mm (not 10 vignetting / not 6 IRAMP)? | Determines per-camera CCM subset Phoenix must compute. | LLDB at 0x350bc0 capture `[camera_struct+0xa8]` → cam_id. |
| Q11 | CCM 2-matrix split (70 vs 300 hits) attribution — which matrix is per-camera pre-IRAMP vs post-IRAMP global? | Places CCM in pipeline correctly. | Closure-capture tracing on 0xbf4a0 with per-caller correlation (tied to Q9). |
| ~~Q12~~ | **CLOSED 2026-04-20 Sessions 2+3.** 70mm L16_03434 Phase 1: CCMInterp `libcp+0x350bc0` fires 12× with **3 distinct dest-rdi values** (0x304125d68, 0x3046c5f58, 0x3046c69f8) vs 28mm's 1. ICS CCM matmul `libcp+0xbf4a0` fires 444× (28mm ref: 370×). 150mm L16_02285 Phase 1: dispatcher cam_ids match 70mm exactly ({8,10,11,12,13,14} = B4+C1..C5); CCMInterp + ICS_CCM + BLC all fire before instrumentation-induced crash (Rich 2026-04-20: Lumen.app ships working 150mm → crash is ours not libcp's). 150mm uses 70mm-tier CCM by extension. | — | — |
| **OPEN-BLC** | **BLC kernel VA + formula.** v1 pipeline diagram implies `0x340b00 = LinearizeAndColorScale<uint16> = BL subtract + color-scale`. Round 1 said `0x340b00` is color-scale only, not BLC. Round 2 LATE REVISION said BLC is linear `(raw-42)/981` via `libcp+0x2cffd0` (subps+mulps; scale `1/981` computed LIVE via `subss+divss` at `0x2d051f` — which is why `0x3a85bb38 = 1/981` doesn't appear in static disasm). The intermediate Anscombe/VST hypothesis was refuted (R28). **Per-image BLC kernel VA is still TBD.** | Spike-blocker: wrong VA → wrong black subtraction → wrong everything downstream. | LLDB BP at 0x340b00 + 0x2cffd0 on bridge HDR; trace per-pixel in/out for known input. Determine: which VA reads raw pixels? Which subtracts 42? Which divides by 981 (or runs the scale factor)? Is there a per-Bayer-channel `color_scale` coefficient? |
| **OPEN-FSCALE** | **Ceres Cauchy `f_scale` value.** v1 D3 said "verified a=1.0 at libcp 0x5c3580". Round 2 `cleanup_actions_log_round2.md` confirms verified via LLDB. BUT `legacy_doc_audit_round2.md` SUPERSEDED banner says UNVERIFIED: first 4 floats at 0x5c3580 decode as `(42.0, 1023.0, 0.000547, -0.0000204)` which is NOT standard Ceres `(a, a²)` doubles layout. **Internal conflict unresolved.** | Spike-blocker for depth: wrong f_scale → wrong Cauchy robustness → wrong depth refinement. | LLDB dump 16 bytes at 0x5c3580; interpret as 2 doubles vs 4 floats; correlate with Ceres Evaluate body observed behavior. |
| **OPEN-PATH-B2** | **Depth cost Path B2 at `libcp+0x2732f0`** — Round 3 says it fires on L16 (0x2730c0 is a count==4 spec that never fires). v2 §2.6 D9-D11 only covers Path A. Fire rate + relationship to Path A + flag semantics unknown. Fusion site for Path A × Path B2 outputs UNLOCATED (`dual_cost_fusion_site.md` 2026-04-18: candidate = `0x3bcf20` case-4 handler, but not verified; strongest hypothesis = confidence-weighted MIN reduction). Path A algorithm class = derivative-SAD + chromatic-L2 (`depth_cost_algorithm_classified.md` 2026-04-18). | Spike-blocker for depth: incomplete depth cost path → wrong disparity. | LLDB BP at 0x2732f0 on bridge profile=3; tally hits; inspect arguments + closure. Once Path B2 characterized, re-run `dual_cost_fusion_site.md` probe with Path A + Path B2 write-watchpoints to localize fusion site. |
| **OPEN-DARKCURRENT** | **Dark-current correction stage at `libcp+0x66d670` (28-record per-ISO table)** — identified by Round 2 as SEPARATE from BLC. **Session 1 2026-04-20 RECONFIRMED INACTIVE on bridge HDR profile=3**: BPs at `0x3048b0` (VST applier) and `0x2f3b90` (F1 wrapper) fire **0×** on full L16_02130 28mm render. The 28-record table is loaded once at dyld init (`0xe1210`) and is dead during render. `f2_worker 0x2f4470` + `f3_top 0x2f53d0` fire 648× each (live YCoCg variance projection per `vst_per_pixel_lldb.md`). **Does NOT block 28mm bridge HDR spike.** Formula extraction requires different render profile (e.g. `--direct-renderer --dr-profile 2`). Table layout per `per_iso_anscombe_consumer.md` F-1 (init signature at `libcp+0xe1xxx`): vector begin=`0x66d670` / end=`0x66d678` / cap_end=`0x66d680` spans 0x700 B = 28×64-byte records = Block 5 ISO record count; sibling vectors at `0x66d688/0x66d6a0/0x66d6b8`. The file's "per-pixel Anscombe" interpretation is superseded by `vst_per_pixel_lldb.md` YCoCg-variance finding but the layout + static consumer-hunt evidence remains valid. | Deferred — not spike-blocking. | For formula extraction (outside bridge HDR spike scope): switch invocation to `--direct-renderer` or `--export-fmt 4`; BP `0x3048b0` once live; capture α/β/γ register loads. |
| **OPEN-NLM4** | **NLM-4 denoiser** (4 novel modifications per `nlm_bm3d_denoiser.md`) — bridge activation + kernel VA + formula unverified. Static disasm (2026-04-18): RTTI string at `libcp+0x5f3720` demangles to `lt::Internal::ImageDenoisePatchNLM<4>::$_0`; vtable at `libcp+0x668920`; `operator()` body at `libcp+0x3070e0` (trampoline at `0x3070a0`); outer dispatcher at `libcp+0x3066d0` invokes 4 phases with phase counter at `[rbp-0x174]`. Body performs 4×4 patch L1-distance (andps-abs + sum, NOT L2) with LCG-PRNG stochastic search-window sampling, weighted by F2 per-pixel YCoCg variance `rcp(variance*16)` at `[rbp-0x290]`. BM3D REFUTED (no DCT/3D-transform; no hard-threshold). | If fires on bridge, Phoenix needs it; if GUI-only, Phoenix omits. | NLM RTTI scan done; LLDB BP at `0x3066d0` on bridge HDR profile=3 to confirm activation + capture per-phase closure args. |
| **OPEN-DEMOSAIC-KERNEL** | **DemosaicV1 inner kernel body at `libcp+0x2eef80`** is static SSE2 per Round 2 — but full taps + interpolation formula not decoded. Partial decode per `demosaicv1_details_cleanup.md` (2026-04-18, static disasm): inner filter is **21-tap** (NOT 9-tap) summing to +64 with `/64` divisor (i.e. `= 1.0` normalized); coefficient pool `{+56 center, +6 cardinal, −4 inner 3×3 ring, −2 inner 5×5 ring, 1/64 divisor}` at `__const` VAs `0x5f18c8 / 0x5aae70 / 0x5a8878 / 0x5a8874 / 0x5abed4`; Bayer-row-phase select at `0x2ec4f4..0x2ec4fc` (NOT a sign-flip); 8 pointers in kernel = 4 pyramid levels × 2 row-cache views per level. Sub-kernel inventory: `2ebe90/2ebff0/2ec150` = identical buffer allocator variant A (8-byte align); `2ee070/2ee1e0` = variant B (4-byte align, 1 channel). `2ec2b0` = per-row pyramid-level row-builder (5-tap convolution with `[1,−2,−4,6,56,6,−4,−2,1]/64` weights); `2ee350` = outer recursion entry. "Tile mirror" at `0x2eedd0..0x2eee79` = sliding row-cache addressing `slot = (y/inner_dim) mod num_slots`, NOT geometric mirror. | For byte-parity demosaic, Phoenix needs the exact taps; for algorithm-class parity, published Hamilton-Adams suffices. Decide based on quality target. | Static disasm of 0x2eef80 inner kernel body (4-5 per-pixel-block instructions for the phase-specific interpolations) + cross-check vs `demosaicv1_sub_kernels.md` + `demosaicv1_details_cleanup.md`. |
| **OPEN-LAPLACIAN-TAPS** | **Laplacian pyramid kernel taps** — 4 verified VAs (`libcp+0x2e4cf0, 0x12c50, 0x133d0, 0x134d0`) per legacy audit Round 2, but tap coefficients + down/upsample formula not extracted. **CLOSED static-disasm** per `laplacian_pyramid_kernels.md` (2026-04-18): pyrDown = **5-tap separable Burt-Adelson Gaussian `[0.05, 0.25, 0.40, 0.25, 0.05]`** (a=0.4 maximum-stopband form); constants bit-exact in `__const` at `0x5a8200/0x5a8204/0x5a8208/0x5a81d0/0x5a81e0/0x5a8190/0x5a8850..0x5a8864`. Laplacian residual formula = `L = upsample_burt(low) − high` (NEGATIVE of textbook). Level count = `clamp(floor(log2(min(W,H))−2.0), 2, 6)`. 17-stop EV synthesis table at `0x5f0ff0..0x5f1040` → Mertens-style multi-exposure fusion synthesized from single HDR input (NOT multi-capture). RTTI-verified: `0x12c50 = lt::ImageGaussianFilterAndSubSample<float>`, `0x12e10 = <vec4x32f>`, `0x133d0 = lt::ImageGaussianUpscaleAndSubtract<float>`, `0x134d0 = <vec4x32f>`, `0x2e4cf0 = lt::(anon)::CreateAndBlendLaplacianPyramids`. **Laplacian COLLAPSE kernel** = `lt::ImageGaussianSubtractUpscaleAndAdd<vec4x32f>` at `libcp+0x16e70` (trampoline `0x16e30`; vtable `0x665258`; typeinfo `0x6652b0`; name at `0x5a8730`) per `laplacian_collapse_and_lab_layout.md`; collapse sign = `output = upsample_burt(low) + residual` (ADDED — sign flip happens during BLENDING, not collapse). | Directly drives output sharpness/halo; needed for tone/color blend fidelity. | Static disasm of the 4 VAs DONE. Remaining: LLDB BP on bridge HDR to verify activation + hit count; confirm sign-flip happens in blending stage, not collapse. |
| **OPEN-IRAMP-BODY** | **IRAMP SAD→WTA→SubPixel→Accumulate→Hann body** — v1 M7 characterizes sub-stages as "CDF 9/7 wavelet + 5-band LUT" but the per-tile SAD/WTA/SubPixel math is not decoded. Round 2 confirmed 70mm L16_03434 fires the full chain 25+ times at each VA. | Core merge fidelity gated on this. | Static disasm of 0x3661b0..0x36ae41 inner bodies at identified sub-stage VAs. |
| ~~**OPEN-DROPPED-CONSUMER** (D5)~~ | **CLOSED 2026-04-20 Session 1.** HW read-watchpoints on A2/A3/A4/A5 RIC L0 buffers at 28mm bridge HDR profile=3 captured 102,361 trips; all 46 unique trip PCs trace through IRAMP-family code. Dropped cams consumed via composite-anchor kernel at `libcp+0x2b3410` (see §2.1 M14.1). 28mm spike UNBLOCKED. Non-blocking optional: re-run script at 70mm (B1/B2/B3/B5/C6 dropped) and 150mm to confirm universal across zoom tiers. | — | — |
| ~~**OPEN-SCOPE-VERIFY**~~ | **CLOSED 2026-04-20 Sessions 2+3 (70mm FULL, 150mm ARCHITECTURAL).** 70mm L16_03434: all 4 target kernels (BLC 0x340b00, CCMInterp 0x350bc0, ICS_CCM 0xbf4a0, IRAMP 0x365960) fire with counts + arg patterns consistent with 28mm; dispatcher cam_ids `[8,10..14]` = B4+C1..C5 match TRUTH M4 exactly; IRAMP body signature (2 composite anchors + 5 contributors) matches B-as-A architecture. 150mm L16_02285: dispatcher cam_ids + IRAMP body first-hits match 70mm (confirms 150mm takes 70mm tier via `outer_enum=1` per `zoom_tier_and_vignetting.md`); full kernel counts BLOCKED by instrumentation-induced crash at `libcp+0x2e945d` (Rich 2026-04-20: Lumen.app ships working 150mm → our BPs perturb timing; not a libcp bug). Remaining untested axes: profile=2 CAMERA, DirectRenderer, other LRIs in each tier (scope-bounded as `untested` not `unverifiable`). **70mm + 150mm bridge HDR spike architecturally UNBLOCKED.** | — | — |
| **OPEN-TRIAGE-99-SCRATCH** | 99 of 136 scratch md files are NOT cited by v1 TRUTH (73% coverage gap). v2 integrated cleanup-log findings + 3 post-TRUTH files but did NOT audit the full 99. Unknown what findings remain. | Unknown-unknowns risk. | Structured diff: for each uncited scratch file, classify as (agrees, fills gap, contradicts, irrelevant) vs v2 claims. |

---

## 5. Phase 2 / Out of Scope (deferred items)

Unchanged from v1 except:

- **Variant-0x10 outliers** (~180 files, 1.8%) — deferred per outlier-deprioritization rule
- **244-file BJPG cluster** — deferred
- **L16_01853 zoom=96 mode** — deferred
- **CIAPI::DepthEditor GUI surface** (11 methods) — out of scope for base render
- **lt::StackFusion** — scope-bound-zero; out of scope unless surfaces elsewhere
- **Phase B mono-path** — Phoenix does not emit mono
- **GUI-editing-pipeline ISP stages** (L5 scope-bound zero) — Phoenix skips for bridge-parity; revisit if Phoenix adds GUI editing later
- **Ceres Pass A + Pass B** — skip at runtime (factory data)
- **Ceres Pass C** — reimplement with scipy (pending OPEN-FSCALE close)
- **Halide kernel byte extraction (tone curve LUTs, Robertson forward table)** — FORBIDDEN per Rule #0. Reimplement from fitted formulas. `phoenix_tone_curves.py` is clean-room Hable/Naka-Rushton fit at ≤0.5% RMS.
- **Distribution legal review** — DISSOLVED by clean-room decision (KMS 8c2bc067).
- **Variant flag semantics (Path A variants 1/2/3 at 0x30dcc0 / 0x30ff60 / 0x3121f0)** — decoded structurally, role unknown. Deferred unless depth accuracy requires.

---

## 6. Replication Recipes

(Unchanged from v1; see `archive/TRUTH-v1-phoenix-truth-2026-04-17.md` §6 recipes 7.0–7.12.)

New recipes needed for OPEN-* items in §4 — left as investigation tickets once path prioritized.

---

## 7. References

### 7.1 Evidence base (in-repo)
- `evidence/phoenix-handoff_traceability/*.md` — 23 session reports
- `evidence/README.md` — pointer to full scratch at `/Volumes/Dev/lumen-phoenix-scratch/`

### 7.2 Authoritative scratch files (cited from v2)

**Core architecture:**
- `iramp_kernel_body.md`, `image_resolution_amp_verification.md`, `iramp_camera_identity.md`
- `iramp_substages_verified.md`, `iramp_integration_e2e.md`, `iramp_28mm_short_circuit_gate.md`
- `sub_stages_36cde0_36e530_36f800.md`, `merge_function_reconciliation.md`
- `composite_anchor_n1_reducer.md`, `anchor_prefusion_and_c6.md`
- `refcache_per_camera_isp.md`, `color_pipeline_audit.md`, `calibration_audit.md`
- `a2_destination.md`, `c6_destination_and_depthcache.md`, `c6_verification.md`
- `ig_offset10_scalar.md`, `ig_offset10_consumer.md`, `per_camera_radiometric_weight.md`
- `ccm_factory_to_runtime_transformation.md`, `imageapplycolormatrix_va.md`
- `session4_v1_linearize.md`, `demosaicv1_jit_kernel.md`, `demosaicv1_per_camera_dispatch.md`, `demosaicv1_sub_kernels.md`, `demosaicv1_details_cleanup.md`
- `vignetting_runtime_corroboration.md`, `sourceimagecache_writer.md`
- `35mm_renderer_mechanism.md`, `tone_curve_location_and_zoom_crop.md`, `zoom_tier_and_vignetting.md`
- `lightheader_camera_scan.md`, `zoom_35mm_and_outliers.md`
- `depth_fate_cross_zoom.md`, `depth_unlock_verification.md`, `profile2_camera_characterization.md`
- `path_a_call_chain_round3.md`, `dual_cost_path_classifier.md`, `do_work_lambda_decode.md`, `depth_cost_algorithm_classified.md`, `dual_cost_fusion_site.md`
- `ceres_analysis.md`, `ceres_residual_bodies.md`, `ceres_evaluate_bodies.md`
- `lightheader_field16_23.md`, `hwinfo_field_18.md`
- `lumen_app_vs_bridge_delta.md`, `blc_correction_OVERRIDE.md`, `blc_formula_final.md`
- `pyramid_levels_characterization.md` (0x3ebb80 / 0x3d0650 operator decode + pyramid-level resolution table)
- `laplacian_pyramid_kernels.md` (5-tap Burt-Adelson pyrDown + Laplacian residual identity + 17-stop EV table for Mertens fusion)
- `laplacian_collapse_and_lab_layout.md` (collapse kernel 0x16e70 + LabCostFunction Evaluate 0x11ae40 + CIEDE2000 helper 0x1273c0)
- `nlm_bm3d_denoiser.md` (NLM-4 denoiser identification at 0x3066d0 + vtable 0x668920 + body 0x3070e0; BM3D refuted)
- `per_iso_anscombe_consumer.md` (28-record per-ISO table layout at 0x66d670; 2 SUPERSEDED banners — layout valid, VST-as-Anscombe refuted)
- `q12_ics_kernel_28mm.md` (C18 re-verify at 28mm: 324 hits / 2 distinct CCM values — confirms C18 at value level)
- `q12_ics_kernel_35mm.md` (C18 topology extension to 35mm: 270 hits / 2 distinct CCM values)

**External L16 architecture reference (non-repo):**
- `/Users/ryaker/Documents/Light_Work/l16-tech-part-1-3.md` — Light Inc.'s own public L16 technology explainer (Wayback Machine capture of support.light.co/l16-photography/l16-tech-part-1-3). Layman-level overview of how 16-camera capture + fusion works. Not byte-authoritative; useful for naming / architecture intuition only.

**Audit / cleanup chain (2026-04-19):**
- `cleanup_actions_log.md`, `cleanup_actions_log_round2.md`, `cleanup_actions_log_round3.md`, `cleanup_actions_log_round4_precision.md`
- `legacy_doc_audit.md`, `legacy_doc_audit_round2.md`
- `va_registry.md` (comprehensive VA table — more complete than scattered VAs in v1)

### 7.3 Comprehensive VA registry

`va_registry.md` (post-v1, 2026-04-19) catalogs 120+ VAs across 11 sections with confidence annotations (✅📐🔤⚠️). Treat as the authoritative index when cross-referencing VAs between sections of this doc.

### 7.4 Reference data (gitignored, on-disk only)
- `spike/reference/ground_truth.tiff` (232 MB)
- `spike/reference/depth_map.npy` (326 MB)
- `spike/sample_extracts/cal_color_l16_02130.npz`

### 7.5 Rules / invariants carried forward
- **Rule #0 (clean-room)**: Phoenix does not link, dlopen, bundle bytes, or depend on libcp/Lumen at build OR runtime. All VAs here are references; every constant Phoenix needs comes from parsed LRI / published CIE tables / reimplemented formulas.
- **Rule 4 (absolutes)**: Every "X doesn't fire" / "GUI-only" / "NEVER" carries explicit (LRI + focal + profile) scope + enumerates untested axes.
- **Rule (spike-is-validation)**: Spike never writes to TRUTH. Spike doesn't run until TRUTH is closed (no unresolved OPEN items in its test path).

---

## 8. v1 → v2 changelog summary (for audit)

| Category | v1 state | v2 action |
|---|---|---|
| Internal conflicts | f_scale contradicted between v1 D3 and `legacy_doc_audit_round2.md`; v1 silently picked "verified" | **Flagged OPEN-FSCALE** — both sides cited; LLDB verification required |
| Silent outdated claims | v1 implied `0x340b00` = BLC kernel; Round 2 said color-scale only | **Flagged OPEN-BLC** — all 3 hypotheses (0x340b00, 0x2cffd0, Anscombe-refuted) cited with verdict trail |
| Silent omissions | IRAMP bilinear, Path B2, NLM-4, dark-current, Demosaic-inner-VA, LightHeader-field-corrections, short-circuit | **Integrated as M7.1, M7.2, D9-D11 Path-B2 note, §4 OPEN-* items, K6, R28-R32** |
| Absolutes not scope-banded | v1 D1/D5/L5/L6 used "GUI-only", "NEVER", "0 hits" unqualified | **Scope-banded** per Rich's Round 4 rule — now "fires 0× at L16_02130 28mm + L16_03434 70mm on bridge HDR profile=3; untested axes enumerated" |
| Coverage gap (99 uncited scratch) | v1 cited 48 of 136 scratch files | **Flagged OPEN-TRIAGE-99-SCRATCH** — not closed in v2; next work item |
| v1 Refuted rows R1-R19 | Preserved | Carried forward via archive reference; added R20-R32 for cleanup-round refutations |
| Post-v1 scratch (hwinfo, pyramid_seeding, va_registry) | Not integrated | **Integrated as K6, §4 OPEN-*, §7.3 authoritative VA index** |

## 8.1 v2 → v2.1 changelog (2026-04-20 Session 1)

| Category | v2 state | v2.1 action |
|---|---|---|
| OPEN-DROPPED-CONSUMER (spike blocker) | Open — "consumer of dropped-cam RIC L0 buffers unknown; Phoenix MUST NOT skip per-cam ISP" | **CLOSED** via HW read-watchpoints on A2/A3/A4/A5 at 28mm bridge HDR. 102,361 trips; 100% IRAMP-family. Dropped cams consumed via composite-anchor pre-fusion. 28mm spike UNBLOCKED. |
| Composite-anchor kernel VA | Hypothesized in `iramp_camera_identity.md`/`composite_anchor_n1_reducer.md` ("src1/src2 wrap composite anchors") but assembly kernel not located | **NEW §2.1 M14.1**: kernel at `libcp+0x2b3410..0x2b3448` (4-way SIMD weighted blend), called from IRAMP body `0x365f50`. Cited to Session 1 artifact `/tmp/l16_open_audit/session1/phase2_watchpoints.log`. |
| OPEN-DARKCURRENT | "Whether it fires on bridge HDR + its kernel VA is unverified" | Reconfirmed: `0x3048b0` / `0x2f3b90` fire **0×** on bridge HDR profile=3 (Session 1 Phase 1). 28-record table dead during render. Formula extraction moved out of bridge HDR spike scope. Row in §4 updated. |
| Phoenix dropped-cam posture | Conservative ("run ISP for all 16 until closed") | Positive-evidence-grounded ("must run ISP for all fired cams because dropped cams feed composite anchor; skipping = corrupt src1/src2 = corrupt merge"). Same behavior, different justification. |
| Session artifacts | — | Added `/tmp/l16_open_audit/session1/` (10 files, incl. 66 MB watchpoint log, 552-line unique-PC dedup, reclassifier script, 2 render outputs). `/tmp/l16_open_audit/_FINDINGS.md` SYNTHESIS block count bumped 13→14 RESOLVED, #15 status flipped TRULY-OPEN → RESOLVED. |
| Open items state | 13 RESOLVED / 3 PARTIAL / 1 TRULY OPEN | **14 RESOLVED / 3 PARTIAL / 0 TRULY OPEN.** 28mm bridge HDR spike is UNBLOCKED per Rich's gate. 70/150mm spike still gated by #16 (non-blocking for 28mm). |

## 8.2 v2.1 → v2.1.1 changelog (2026-04-20 doc hygiene pass)

| Category | v2.1 state | v2.1.1 action |
|---|---|---|
| Doc hygiene: added 12 citations to §2.1–§2.9 Evidence cells + §7.2 authoritative list + §4 OPEN-* rows, closing OPEN-UNCITED action from 2026-04-20 audit (`/tmp/l16_open_audit/_FINDINGS.md` §17). | 107 scratch files uncited; 12 identified as load-bearing | 12 scratch files + 1 external tech-doc now cited; each citation is scope-bound (reflects narrower static-disasm / manual-BP evidence rather than full-coverage LLDB). No finding rows rewritten — Evidence cells appended only. |
| Files integrated | — | `pyramid_levels_characterization.md`, `laplacian_pyramid_kernels.md`, `laplacian_collapse_and_lab_layout.md`, `nlm_bm3d_denoiser.md`, `per_iso_anscombe_consumer.md`, `q12_ics_kernel_28mm.md`, `q12_ics_kernel_35mm.md`, `demosaicv1_details_cleanup.md`, `demosaicv1_sub_kernels.md`, `blc_correction_OVERRIDE.md` (expanded, already listed), `dual_cost_fusion_site.md`, `depth_cost_algorithm_classified.md`, `/Users/ryaker/Documents/Light_Work/l16-tech-part-1-3.md` |
| OPEN-UNCITED status (2026-04-20 audit #17) | 99 uncited scratch files flagged | **RESOLVED** for the 12 load-bearing files; remaining ~95 scratch files = per-session scratch or superseded per audit classification, not load-bearing. |

## 8.3 v2.1.1 → v2.1.2 changelog (2026-04-20 Sessions 2+3 LLDB on 70mm + 150mm)

| Category | v2.1.1 state | v2.1.2 action |
|---|---|---|
| Q12 ZOOM_CCM | PARTIAL (35mm✓, 70mm partial, 150mm UNTESTED) | **CLOSED.** 70mm L16_03434: CCMInterp fires 12× with 3 distinct dest-rdis (vs 28mm's 1); ICS_CCM matmul 444 hits; BLC 932 hits; IRAMP body 63 hits; dispatcher 7 hits with cam_ids `[8,10..14]` = B4+C1..C5 matching TRUTH M4 exactly. 150mm L16_02285: first-hit data for all targeted kernels matches 70mm; architectural extension rather than direct count due to instrumentation crash. |
| OPEN-SCOPE-VERIFY | all PARTIAL | **CLOSED** for 70mm FULL + 150mm ARCHITECTURAL. 70mm/150mm bridge HDR spike architecturally UNBLOCKED. |
| #15 cross-zoom extension | not-attempted | **DEFERRED (non-blocking).** Direct BP at composite-anchor kernel `libcp+0x2b3410` causes deterministic render crash at both 70mm and 150mm (Halide-JIT hot-loop + BP perturbation incompatible). Cross-zoom universality inferred architecturally from IRAMP body arg signature (src1/src2 composite anchors present at all 3 zoom tiers). Direct confirmation via HW read-watchpoints on 70mm/150mm dropped-cam buffers remains possible future work. |
| Instrumentation caveat added | — | Documented that LLDB BPs at `libcp+0x2b3410` deterministically crash HDR render; at 150mm, even S2's proven probe triggers `EXC_BAD_ACCESS` at `libcp+0x2e945d` under instrumentation. Rich's verdict (2026-04-20): "Lumen.app ships working 150mm renders — crash has to be ours." Not a libcp bug; our BP-induced timing perturbation surfaces a race in Halide's lock-free path. |
| Open items state | 14 RESOLVED / 3 PARTIAL / 0 TRULY OPEN | **16 RESOLVED / 1 PARTIAL (#10) / 0 TRULY OPEN.** All 28/70/150mm bridge HDR spikes architecturally UNBLOCKED. #10 OPEN-DARKCURRENT remains deferred (not HDR-relevant). |
| Session 2+3 artifacts | — | `/tmp/l16_open_audit/session2_and_3_findings.md` (synthesis), `/tmp/l16_open_audit/session2/phase1_processlevel.log` (11 KB full 70mm render), `/tmp/l16_open_audit/session3/phase1_probe.log` (14 KB partial 150mm before crash), `/tmp/l16_open_audit/minimal_{70,150}mm.log` (0x2b3410 BP experiments — documented crash mode). |
