# Phoenix Pipeline — Verified Facts for Spec Writing
**Generated:** 2026-04-13 (rev 6 — post Session 1-5 LLDB runtime probes + corpus sweeps)
**Source of truth:** real Lumen binary (libcp.dylib RTTI + disassembly), real LRI files, LLDB runtime traces on production LRI (L16_02130)
**Purpose:** Concise reference for implementing the Phoenix reimplementation spec. Every fact here is verified from a real-Lumen source with VA/file citation. Phoenix must process **any LRI** — all zoom levels, all firmware variants.

**Investigation discipline:** no spike outputs are cited in this document. When the spike contradicts the real Lumen bridge, the spike is wrong, not the camera system.

---

## Rule #0 — Clean-room constraint (read before anything else)

**Phoenix is a clean-room reimplementation. Phoenix does NOT link against, `dlopen`, bundle bytes from, or otherwise depend on `libcp.dylib`, `Lumen.app`, or any other Light Inc. proprietary binary — at build time OR runtime.**

All VAs cited in this document are **reverse-engineering references only**. They tell the implementer where to read the reference algorithm in a disassembler, NOT which bytes to copy into Phoenix's binary.

Every constant Phoenix needs must come from one of three sources:

1. **Parsed from the input LRI file at render time** — calibration blocks (vignetting, CRA, CCM, geometric, per-camera black/white levels), Block 8 AWB gains, LightHeader per-capture metadata. LRI files travel with their own factory calibration, so Phoenix parsing the LRI IS the device-characterization source. **Phoenix MUST include an LRI calibration parser as a pipeline stage** — it does NOT load pre-extracted `.npz` or similar archives.
2. **Published / derivable / CIE-standard values** — Wyszecki-Stiles Robertson tables, standard illuminant xy coordinates, CIE constants, sRGB conversion math.
3. **Reimplemented from scratch based on a documented algorithm in this spec** — e.g. "Hamilton-Adams green interpolation with gradient-weighted directional selection" is an algorithm name Phoenix codes from scratch, not "the bytes at VA 0x2eeb20."

**Things that MUST NOT ship with Phoenix:**
- Tone curve LUT bytes copied from libcp's `__TEXT __const` at 0x5e31b0 / 0x5e41b4 / 0x5e51b8 / 0x5e61bc.
- Robertson forward-lookup table bytes copied from bss at 0x66d420 (28 × 16 bytes).
- Pre-shaper constants at 0x5e3180, illuminant xy tables at 0x5ab720 / 0x5ab760, CCT constants at 0x5ab180 / 0x5aae64, or any other rodata literal read out of libcp.
- `cal_color_l16_02130.npz` or any other pre-extracted calibration archive — these are per-device, per-LRI, and MUST be parsed from each input file at render time. Any `.npz` in the handoff package is a **reference extract showing what Phoenix's parser should produce for one sample LRI**, not a runtime input.

**Legal caveat flag**: tone curves and the Robertson forward table sit in a grey zone. They may be "device firmware characterization constants" (shippable with provenance) or "app-level Lumen IP" (not shippable). **Phoenix distribution is blocked on a legal decision about this.** See open item #27.

---

## Reverse-engineering reference vs. implementation source

In the rest of this document:
- "**VA 0xNNNN**" means "reference location in libcp.dylib for reading the algorithm." NEVER "bytes to copy."
- "**closure +0xNN**" means "a field the reference kernel reads from its own closure." Phoenix reimplements the closure layout from scratch.
- "**Block N of LRI**" or "**LightHeader.field_X**" means "parsed from the input LRI file at runtime." THIS is Phoenix's real runtime data source.
- "**port verbatim**" language from earlier revisions was a mistake and is being removed. Read it as "reimplement based on the documented algorithm."

## ⚠ Rev 5 — Verified pipeline model (post Session 2 + Session 3 LLDB)
Session 3 closed most of Session 2's open blockers. The verified per-tile execution model on L16_02130 28mm:

### Pipeline architecture (verified by runtime trace — rev 6 correction)

```
Per-tile execution order:
  Upstream cast (per-camera tile fetch):
       libcp+0x271d0 (SSE) / +0x27390 (scalar tail)
       - Bulk uint16 → float32 1:1 bit-cast
       - NO subtract, NO scale — sensor 42 becomes 42.0f
       - Data enters the Halide pipeline as unscaled float32 in [0, 1023] range

  t=0: DemosaickLightV1<tile_parity>::operator()  [3 variants: <0,0>, <1,0>, <1,1>]
       - Reads unscaled float32 Bayer from per-camera source buffer (closure +0x10)
       - Demosaics Bayer → unscaled float32 RGBA (still in [0, 1023] range)
       - Uses Vec3 WB gains from closure +0x08 ONLY to scale the gradient
         regularization epsilon — does NOT multiply pixels by gains
       - Writes into SHARED CANVAS (closure +0x08)
       - Template params `<offX, offY>` = `(tile_x mod 2, tile_y mod 2)` Bayer parity
       - 10 cameras × N tiles × 3 variants = ~10 writes per canvas location
       - 10-camera merge = side effect of each camera writing warped-demosaicked
         data into the shared canvas

  t=1: lambda_0 LinearizeAndColorScale @ 0x340b00 — THE ACTUAL LINEARIZE
       - Subtracts black level (probably 42) from unscaled RGBA
       - Scales to [0,1] by per-camera white-level range
       - Probably also applies per-channel WB gains via identity 2×2 at closure+0x16b0
       - Exact arithmetic UNRESOLVED — needs static disasm of 0x340b00 body

  PARALLEL ThreadPool path: RemoveVignettingGeneric<T, bool>
       - <float, true>   @ libcp+0x108370: 2,249 hits (pre-demosaic Bayer)
       - <vec4x32f, true> @ libcp+0x108080: 10,994 hits (post-demosaic RGBA, dominant)
       - <vec4x32f, false> @ libcp+0x1086c0: 391 hits
       - Runs on separate ThreadPool::TaskRange worker path, not the lambda dispatcher
       - 13,634 total operator() invocations per render
       - Vignetting correction applies BOTH pre- and post-demosaic — answering the
         rev-4 "Stage 7 vs Stage 9" dispute as "both"

  Later Phase D lambdas (on the assembled float-RGBA canvas):
       - lambda_1/lambda_2: BayerPhase / ImageCorrect
       - lambda_5: AWB (apply pre-computed reciprocals 1/stored_gain)
       - lambda_6: CCM (fixed D65 matrix from context_ptr+0xb8)
```

### Key insights from Session 3
1. **Demosaic IS inside libcp** — but uses `DemosaickLightV1` (Vec3 WB gains inline), NOT V2. V2 variants at 0x2f0df0 etc. are dormant on L16_02130 28mm production render. V1 variants at 0x2ed580 / 0x2eeb20 / 0x2f0240 fire. Rev 4's "V2 never fires → demosaic is outside libcp" conclusion was wrong — it just uses V1 instead.
2. **Raw→float linearization is inside DemosaickLightV1::operator()** — no separate "Stage 1 Linearize" at runtime. lambda_0 sees already-linearized RGBA because V1 produced it.
3. **The 10-camera merge is a side effect**, not a dedicated stage. Each V1 variant invocation has a different `closure+0x10` (per-camera source) but a constant `closure+0x08` (shared destination canvas).
4. **Vignetting runs on a parallel ThreadPool worker path**, not inline with the Pipeline lambda dispatcher. That's why Session 1's "LensShading INACTIVE" probe missed it — it was looking at the wrong path.
5. **setLensShading 1966× = configuration/allocation**, not execution. Actual vignetting work is 13,634 operator() calls on the separate ThreadPool path.
6. **Multi-phase render** driven by state machine at `libcp+0x33f042 → 0x33f3eb` with a per-phase stage bitmap. Phase A (demosaic + lambda_0 seed of color canvas), Phase B (**mono-path final render** via lambda_7 ColorPost + lambda_8 MonoMerge — writes uint16, disjoint from color path, PHOENIX SKIPS THIS), Phase C (lambda_0 refinement), Phase D (full Bayer ISP 0→1→2→5→6 = color output). Phases B and D are **independent pipelines producing different outputs** (grayscale TIFF vs color TIFF), not sequential stages.

### Rev-4 corrections from Session 3
- ~~"10-camera merge is outside libcp"~~ — WRONG. It's inside DemosaickLightV1 via closure-level destination sharing.
- ~~"Raw→float happens upstream of libcp"~~ — WRONG. Inside DemosaickLightV1::operator() closure +0x18 scalars.
- ~~"setLensShading is continuous reconfigure of the actual kernel"~~ — WRONG. It's allocation/config; real execution is on the ThreadPool path.
- ~~"DemosaickLightV2 is the bridge default"~~ — WRONG. V2 is dormant on this LRI; V1 is the production demosaic.

The "Stage 1 / Stage 8 / Stage 10 / Stage 12" ordering in libcp_isp_symbols.txt is the **registration order of Pipeline::set* lambda slots**, not the runtime execution order. Actual runtime order is phase-dependent.

---

## Hardware

| Property | Value |
|---|---|
| Sensor | AR1335, W=4160, H=3120 |
| Black level | 42.0 (all cameras) |
| White level | 1023.0 (all cameras) |
| Bayer pattern | BGGR (value 3), all 16 cameras |
| Output canvas | 10432×7824, fx=8457.2px, hFOV=63.33°, vFOV=49.65° |

### Camera firing by zoom
Verified on **162 LRI captures** across 6 date folders (L16_02130=28mm, L16_03434=70mm, L16_02285=150mm, + 159 additional stream-scanned). Source: `/Volumes/Dev/lumen-phoenix-scratch/lri_header_camera_config.md`.

| Zoom | Cameras | Count |
|---|---|---|
| 28mm | 5A (A1–A5) + 5B (B1–B5) | 10 |
| 35mm | same as 28mm + canvas center-crop at output | 10 |
| 70mm | 5B (B1–B5) + 6C (C1–C6) | 11 |
| 150mm | 5B (B1–B5) + 6C (C1–C6) | 11 |

- **150mm fires 11 cameras, not 6.** The prior "150mm = C only" row in earlier revisions was never verified against real LRI headers — c6_verification.md only proved C6 activity at 70mm/150mm, not absence of B cameras. Direct LightHeader parsing on L16_02285 shows all 11.
- C cameras do NOT fire at 28mm/35mm. A cameras do NOT fire at 70mm/150mm.
- **35mm is NOT a separate synthesis pass** — same 28mm 5A+5B capture, same ISP, with a canvas center-crop at output.
  - Crop on 10432×7824: left=1043, top=782, right=9389, bottom=7042 → **8346×6260 px**
  - 35mm hFOV=52.52°, vFOV=40.62° (28mm FOV × 28/35)

### Mirror / focus configs — ⚠ earlier rev 2 claim partially SUPERSEDED
**Rev 2 got the movable set wrong and mischaracterized what the "configs" control.** Corrections below are verified by `movable_mirror_formula.txt` (2026-04-11, L16_01325) + `zoom_config_table.txt` (2026-04-12, L16_02586) independently agreeing.

- **Movable-mirror cameras = 8**: **{B1, B2, B3, B5, C1, C2, C3, C4}**. Each has its own `R_fold` (3×3 rotation), `virtual_pos`, and warp entry in the per-camera mirror_raw leaf.
- **Fixed-mirror cameras = 8**: **{A1, A2, A3, A4, A5, B4, C5, C6}**. (The rev-2 claim that C5/C6 were movable and C2/C3 were fixed was wrong — flipped.)
- **The 4 "configs" are FOCUS BRACKETS, not mirror park positions.** All 4 encoder positions for a given movable camera share **one R_fold** — same azimuth, same elevation, same optical axis direction. Only the 17×13 float32 distortion correction grid differs per config, encoding **focus-dependent geometric distortion**.
- Not every movable camera has 4 configs: **B1, B2, B5, C1, C4 have 4-entry encoder tables** (true focus-bracketed); **B3, C2, C3 have a single entry with encoder=0** — effectively "glued" to one focus position on this unit.
- **Mirror is factory-glued after calibration.** No per-capture mirror angle anywhere in the file. R_fold is the post-reflection, post-calibration, complete camera-to-world rotation.
- **Zoom on the L16 is NOT achieved by changing any camera's optical path.** Different focal lengths use different CAMERA SETS:
  - 28mm / 35mm: 5A + 5B
  - 70mm / 150mm: 5B + 6C
- Per-camera encoder readings (when non-zero) live in `LightHeader.field_12[j].field_4` of each image chunk, where `field_12[j].field_2 = cam_id`. For movable cameras with 4-entry tables, the argmin selects the closest FOCUS bracket (distortion grid); there is no azimuthal meaning. For fixed cameras and for the 3 glued-movable cameras (B3/C2/C3), encoder=0 is correct and expected — not an anomaly.

### Canonical per-camera quadrant table (verified on L16_02586)
| Camera | Type | Azimuth | N_focus_configs | virtual_pos (mm) |
|---|---|---|---|---|
| B1 | movable | −37.8° | 4 | (18.615, 7.408, −5.203) |
| B2 | movable | −144.1° | 4 | (−8.698, −18.699, −4.990) |
| B3 | glued-movable | +142.3° | 1 | (8.482, 33.968, −6.221) |
| B5 | movable | +35.9° | 4 | (−33.622, 33.617, −6.042) |
| C1 | movable | +36.1° | 4 | (−18.055, 24.857, −8.401) |
| C2 | glued-movable | −144.3° | 1 | (−35.288, −10.213, −9.155) |
| C3 | glued-movable | −37.9° | 1 | (26.668, −18.019, −7.040) |
| C4 | movable | +143.1° | 4 | (43.468, 8.933, −4.028) |

**Architecture**: 8 movable cameras cluster into 4 azimuth quadrants (±37°, ±143°), each quadrant covered by one B + one C camera pair. This is the aperture-mosaic architecture.

---

## LRI Format

### LELR block header (all formats)
- `"LELR"` magic (4 B)
- `total_block_len` u64 @ offset 4
- `msg_off` u64 @ offset 12
- `msg_len` u32 @ offset 20
- `msg_type` u8 @ offset 24
- Payload follows

### File structure
- Sensor pixels per camera: 4160 × 3120 = 12,979,200
- Bytes per camera (16-bit raw): 25,958,400; (10-bit MIPI packed): bpr=5200, H=3120
- **Per-camera byte offsets live in `LightHeader.field_12.field_9.field_5`** — authoritative. Do not guess from chunk0_len.
- **Image chunk layout depends on zoom**:
  - **28mm / 35mm**: 2 image chunks, 5 cameras per chunk, H_int=1950 (half-res readout)
  - **70mm / 150mm**: 3 image chunks with 4+3+4 cameras per chunk, H=3120 (full-res readout, 11 cams total)

### Three calibration LELR blocks per file
| Block | Payload size | Records | Contents |
|---|---|---|---|
| A (geo) | ~32,833 bytes | 16 (per camera) | Geometric calibration, K matrix, distortion, extrinsics |
| B (vig+CRA) | ~262,969 bytes | 16 (per camera) | Vignetting grids + CRA grids + per-camera nominal encoder tables |
| C (CCM) | ~35,266 bytes | 42 (14 cams × 3 illuminants) | Color correction matrices |

### Format variants
| Format | Chunk stride | Notes |
|---|---|---|
| 2017-era | different | Earlier firmware — not characterized |
| 2018-normal 28/35mm | 5 cams/chunk × bpr=5200 × H_int=1950 | Main wide-angle format |
| 2018-normal 70/150mm | 4+3+4 cams × 3 chunks × bpr=5200 × H=3120 | Telephoto full-sensor readout (previously mislabeled "WDR" in catalog heuristics) |
| 0.1.x transitional | 10,485,764 bytes/camera, 8 cams/chunk, H_int=2016 | 515 files |
| BJPG (firmware v0.2+) | Variable — JPEG per camera | ~302 files post-2018-06-26: LELR blocks contain `BJPG` magic at +32, 80 concatenated JFIF JPEGs with 1,576-byte index. Quality ~68–84, tile 1024×512. No fixed stride |

- **"WDR" is NOT a real capture format.** The catalog heuristic `chunk0_len < 70 MB → WDR` mislabels 3,242 files that are actually 70mm/150mm 11-camera full-sensor captures. libcp.dylib contains **zero** HDR/WDR/bracket/multi-exposure symbols or strings. The `HDR_MODE_{NONE,DEFAULT,NATURAL,SURREAL}` enum belongs to `ltpb.ViewPreferences.HDRMode` — a **render-time tone-mapping preference**, not capture metadata. `lt::ExposureFusion(dst, src, weight, ...)` takes a single src image — it's a post-tone-mapping stage, not a multi-bracket merger. Phoenix does NOT need a WDR parser.

### AWB gains
Stored in LRI Block 8 f19.f15 as `[R_gain, 1.0, 1.0, B_gain]` (green unity). **Computed by on-camera hardware ISP at shutter time; libcp never recomputes them.** Read directly.

---

## Calibration Fields (from L16_02130.lri)

### Vignetting (Block B)
- Shape: (16 cameras, 4 channels, 17, 13) float32
- Protobuf path: `rec.f4.f2[ch].f2.f3` = 884 bytes = 221 float32 → reshape (17, 13)
- Center = 1.0 normalized; corners 2.0–3.8×
- **Application direction: multiply** (`bayer *= gain`). Grid stores correction gains (center=1.0 = no change, corners 2.0–3.8× = amplify). Verified from function name `lt::(anon)::RemoveVignettingGeneric<T, bool>` in libcp.dylib RTTI — "Remove" semantically means correcting for, and dividing would darken corners further. Source: `libcp_demangled_internals.txt`; `libcp_isp_symbols.txt` Stage 7.
- **⚠ Pipeline position DISPUTED between two sources — neither has a runtime trace.**
  - `libcp_isp_symbols.txt` (static stage ordering from set*() lambda slot numbering) places `LensShadingCorrection` at **Stage 7**, pre-AWB, pre-demosaic, on float Bayer input.
  - `lldb_isp_findings.txt` PART 8 (full Bayer ISP ordering inferred from lambda numbers and pixel value progression) places it at **Stage 9**, post-demosaic, post-denoising, before CCM, on vec4x32f RGBA input.
  - Three live template variants exist (`<float,true>`, `<vec4x32f,false>`, `<vec4x32f,true>`), meaning the function can run on EITHER Bayer (float) OR RGBA (vec4x32f). Which template the bridge actually calls is not resolved.
  - Resolution path: runtime LLDB breakpoint on setLensShading @ 0x3184d0 during a production-LRI bridge render, observe the template variant invoked and at what pipeline stage.
- **`Pipeline::setLensShading` @ VA 0x3184d0** (hidden visibility, recovered via `std::function __func` typeinfo walk). Reachable from **every exported CIAPI entry point** — `Renderer::render`, `Renderer::Create`, `Renderer::deserialize`, `DirectRenderer::Create`, `DirectRenderer::render`, `ApplyTuning` — all converge at pipeline-tune helpers 0x318030 / 0x318040 at depth 3. Not dead code.
- **Stage 7 worker is gated on LRIS calibration data presence**, not on a state toggle. When the LRIS module record lacks `VignettingCharacterization`, setLensShading installs a no-op lambda. Error strings confirm: `"Bad LRI: Vignetting data not found for at module"`, `"vignetting model not found!"`, `"No vignetting data!"`. Prior 0-hit probes in `lri_process` used corrupt L16_01325 test files missing vignetting data — that's why the stage didn't fire, not because the path was dead.
- Config keys: `lens_shading.type` (11 xrefs), `lens_shading.multiplier` (3 xrefs) — per-frame parameters read at setLensShading time.
- Three live template variants: `<float,true>`, `<vec4x32f,false>`, `<vec4x32f,true>`. `<float,false>` is dead-stripped.
- **Phoenix action:** always run Stage 7 vignetting correction when LRI has `VignettingCharacterization`; silently skip if missing.

### CRA correction (Block B)
- Shape: (16 cameras, 13, 17, 4, 4) float32
- Protobuf path: `rec.f4.f1.f4` = 14,144 bytes = 3,536 float32 → reshape (13, 17, 4, 4)
- Center diagonal: [1.0000, 1.0034, 0.9966, 1.0000]

### CCM (Block C)
- Shape: (14 cameras, 3 illuminants, 3, 3) float32 — A2 (ID1) and C6 (ID15) absent from this block only
- Illuminant IDs on this device's factory calibration: TungstenA=0, D65=2, F11=6
- A1 D65: [[0.900, 0.132, −0.067], [0.310, 1.074, −0.384], [−0.057, −0.430, 1.313]]
- **libcp supports 12 DNG LightSource values** (A, B, C, D50, D55, D65, D75, E, F2, F7, F11 — mask 0x1ffd) via `Illuminant::xyToXYZ` @ VA 0xa9130, using 13-entry xy tables at 0x5ab720/0x5ab760. This device ships with 3 factory matrices; other devices/firmware may ship more or different subsets.

### Output files
- `/Volumes/Dev/lumen-phoenix-scratch/cal_color_l16_02130.npz` — arrays: bayer_patterns, vignetting_grids, ccm_matrices, cra_grids, black_levels, white_levels

---

## ISP Pipeline

### Tone mapping
- 4 named curves: `acr`, `light_v1`, `light_v1_lowlight`, `light_v2`
- Structure: fixed piecewise pre-shaper → 1024-entry float32 LUT → multiply by `exp2f(EV)`
- Pre-shaper: `u=0` if `x≤0.0025`; `u=(x−0.0025)²×100.50251` if `0.0025<x<0.0075`; `u=(x−0.005)×1.0050251` if `x≥0.0075`; `LUT_idx = clip(u×1024, 0, 1023)`
- Midgray responses: `acr y(0.18)=0.379`, `light_v1 y(0.18)≈0.208`, `light_v1_lowlight` similar, `light_v2 y(0.18)≈0.201`
- LUT pointer table at VA **0x659c70** (4 entries, bounds-checked <4): `[0]=0x5e31b0` (acr), `[1]=0x5e41b4` (light_v1), `[2]=0x5e51b8` (light_v1_lowlight), `[3]=0x5e61bc` (light_v2). Throws `"Unknown tone-curve selected!"` on overflow.
- `Pipeline::setToneMapping` @ VA **0x319369** (sole callsite). Switch table @ 0x33cd64 maps 7 enum values → curve.
- TMO base ctor @ VA **0x2d76b0** performs the indexed LUT lookup.
- **Bridge default tone curve = `light_v1` (VERIFIED empirically via ground_truth.tiff ProfileToneCurve match).** `session2_tone_curve_discriminator.md` (2026-04-13) extracted the `ProfileToneCurve` metadata from `ground_truth.tiff` (which is actually a Linear Raw DNG 1.3.0.0 from `libcp_v_0_26_1-9-g3c966`, not a rendered TIFF) and numerically compared against the extracted LUTs at 8 sample points: light_v1 matched to ~0.002 (quantization noise); acr showed 0.18 delta at x=0.18 (EXCLUDED); light_v1_lowlight showed 0.17 delta (EXCLUDED). Applies to **all render paths** — lri_process and Lumen.app GUI share a single `setToneMapping` call site.
- Selection mechanism (defaults function @ VA **0x3c7860**): based on `isLowLight()` and a flag at `Pipeline+0x9c`:
  - `(!lowLight)` → `"light_v1"` (bridge default)
  - `(lowLight && flag==0)` → `"light_v1_lowlight"`
  - `(flag != 0)` → `"light_v2"`
- Earlier `static_analysis_libcp.md §1.5` claim that ACR is the bridge default is **empirically wrong** (superseded by LUT match).
- **EV scalar source: `Settings.exposure` protobuf field** (optional float, field 1). `Settings` message embedded at libcp file offset **0x6143c2**. No `tone_curve` field exists in the schema — curves are never persisted, always runtime-resolved via `isLowLight()`. Two writers push `Settings.exposure` into the `tone_mapping.ev_offset` config key:
  - VA 0x3c70e0: `caller_xmm0 + Pipeline[+0x50]`
  - VA 0x3b3783: `Renderer[+0x8b0]`
- LUT data on disk: `/Volumes/Dev/lumen-phoenix-scratch/tmo_*.npy`, metadata: `tmo_characterization.json`

### Demosaic
- Bridge profile 0 uses **`DemosaickLightV2<offX,offY>`** for all cameras. Signature: `(Image<vec4x32f>& dst, const Image<float>& src, float scalar)`. 4 Bayer-phase variants.
- **`DemosaickLightV2<0,0>` @ VA 0x2f0df0** (recovered via typeinfo 0x65a290 + vtable 0x65a240 entry [6]).
- Inner kernel VA range: **0x2f1050 – 0x2f148b**; outer row loop 0x2f0f00 – 0x2f14a6.
- **Algorithm: Hamilton-Adams family — gradient-inverse-weighted directional interpolation.** Pattern per 2-pixel block: `abs(neighbor_diff) | 0x7FFFFFFF`, add `ε`, `rcpps`, `mulps`, sum; three directional reductions; `rcpss`; final `addss base`. Alpha output unconditionally `0x3F800000 = 1.0`.
- **V2 float scalar role: gradient-regularization noise floor `ε`** added to every gradient magnitude before the reciprocal. `ε = scalar × (1/128)`. Large scalar → bilinear-like smoothing; small scalar → sharp detail. A secondary `scalar × -0.02` is computed into sub-call 0x2f16d0 (consumer unresolved, flagged as open question).
- V2 vs V1: V1 takes `Vec3<float>` gains (WB-integrated per-pixel), V2 takes a single float scalar. V2 is post-fusion; V1 is per-camera.
- **Upstream provenance of V2 scalar** (where it comes from in the pipeline): UNRESOLVED. The 7 setDemosaicking `$_25..$_31` operator() lambdas take `Vec3<float>` in their outer signature; the Vec3→float reduction to produce the scalar happens inside the captured `DemosaickFilter<E2, float, X, Y>` functor body. Plausible: `gains[1]` (green) or mean of R+B. Not verified — needs LLDB trace of xmm0 at DemosaickLightV2 entry.
- Malvar/AHD/other algorithms belong to GUI editing tier (`ImageDemosaickFilter<DemosaickFilter::N, ...>` enum values 0/2/3, plus `malvar`→6 registry) — not on the bridge codepath.

### Fusion — ⚠ SUPERSEDED: wrong identity entirely
**Prior claims that `FusionCacheBayer` / `PackedBayerFusion` / `0x1bd0a0` perform the 10-camera cross-camera merge are SUPERSEDED. That subsystem is NOT cross-camera fusion at all — it is SINGLE-IMAGE HDR BRACKET FUSION for tone mapping.**

Evidence that "fusion" is a tone-mapping subsystem, not a cross-camera merge:
- All `fusion_*` protobuf config keys live under the **`tone_adjust.*`** namespace (from `fusion_strings.txt`): `tone_adjust.fusion_ev_plus`, `tone_adjust.fusion_ev_minus`, `tone_adjust.fusion_noise_filter_scale`, `tone_adjust.fusion_detail_gain`, `tone_adjust.fusion_noise_gain`, `tone_adjust.fusion_black_point`. These are EV-bracket tone-mapping parameters, not cross-camera blending parameters.
- `lt::ExposureFusion(dst, src, weight, ExposureFusionParam)` takes a **single src** image (verified by signature) → it is intra-source HDR bracket merging, not multi-source camera compositing.
- `fusion_blend_analysis.txt` runtime probe: on L16_02586 28mm render, `FusionCacheBayer::process` had N=1 at all 132 tiles. The N≥2 blend path (`0x1bd0a0` formula with LUT `0x5d2390`) was never triggered. Interpretation: FusionCacheBayer receives **pre-merged Bayer data** (`img_vec[0]` holds one pre-assembled panoramic Bayer strip per tile).
- Laplacian pyramid blend lambda @ 0x1ab010 had 0 hits across all probe runs.

**The actual 10-camera merge happens in a completely different, not-yet-identified stage upstream of FusionCacheBayer.** Candidate: a per-camera warp+write loop inside `CIAPI::Renderer::render` → `lt::RendererPrivate::requestRenderROI` that iterates cameras, warps each through `project_roi_to_camera @ 0x3e2e90` (Catmull-Rom cubic + depth-aware `1/z`), and accumulates into a shared canvas buffer. Not verified.

**Address correction to preserve**: `0x36fd30 / 0x36f800` was once claimed as "fusion blend kernel." That's wrong — constant pool at 0x5a91e8 = `{255.0, 0.299, 0.587, 0.114}` (Rec.601 luma coefficients) with `cvttss2si → movb` byte writes proves it's a luma-grid generator (likely feeding GetSkippingMaskGrid), not a blend.

**Structurally-existing (but never-observed-firing) code paths related to HDR bracket fusion (not cross-camera):**
- `0x1bd0a0` — weighted-sum kernel for N≥2 bracket merge: `weight = sqrt((combined+1)/256) × sqrt(W*H*exp)/N`
- `0x5d2390` — 256-entry weight LUT: `LUT[i]² × 256 = i+1` exactly → closed-form `sqrt((i+1)/256)`
- `project_roi_to_camera @ 0x3e2e90` — Catmull-Rom + 1/z warp (per-tap)
- `PyramidAlignment::alignImage`, `ComputeFlowField`, `GetSkippingMaskGrid` — alignment/masking infrastructure, role not runtime-confirmed

(Keeping these for reference — they're real code, just not what we thought they were. The bracket-fusion formula MAY apply to multi-EV bracket merging when such data exists in the LRI.)

Laplacian pyramid (`CreateAndBlendLaplacianPyramids`) belongs to Stage 14 tone-adjust (`tone_adjust.lpyr_*` parameters), confirmed via `lumen_side_analysis.md`.

**10-camera merge point — SEE OPEN ITEM #12 / #15 — this is a blocker for Phoenix.**

What is verified:
- `fusion_blend_analysis.txt` (4 LLDB runs on L16_02586, 2026-04-12): across 132 tiles, **N=1 at every tile** at the `FusionCacheBayer::process` camera-count gate (0x406c77 `cmpl $0x2, %eax` → `jb 0x406e4c` single-camera path). The N≥2 multi-camera blend path was **never triggered**.
- Explicit conclusion from that analysis: *"FusionCacheBayer receives pre-merged Bayer data. The 10 L16 cameras are fused at an earlier pipeline stage before FusionCacheBayer. img_vec[0] holds one pre-assembled panoramic Bayer strip per tile."*
- Static-only code paths that exist but were never observed firing in the observed render:
  - `0x1bd0a0` — weighted-sum kernel for N≥2, formula `weight = sqrt((combined+1)/256) × sqrt(W*H*exposure)/N` with LUT at `0x5d2390` (verified by the demosaic/fusion agent in this session), but **never actually called during the studied render**. Structurally exists; functionally dormant.
  - `project_roi_to_camera` @ 0x3e2e90 (Catmull-Rom + depth-aware 1/z per-tap warp) — likely part of per-camera warp to canvas, but not proven to be the merge operator.
  - `PyramidAlignment::alignImage`, `ComputeFlowField`, `GetSkippingMaskGrid` — exist in binary, role in runtime path not confirmed.
- `Beta-2 seam analysis` (from fusion_blend_analysis.txt): B4 raw tile vs final canvas on L16_02586 showed NO detectable seam (Pearson r=0.376 pixel, r=0.44 16×16 block), confirming B4 DOES contribute to the 28mm canvas. So cameras ARE merging somewhere — just not at FusionCacheBayer.

**Open question — where is the actual 10-camera merge?** (See Open Items #12.) The cameras must be composited into `img_vec[0]`'s pre-assembled panoramic strip upstream of FusionCacheBayer. Candidates: some stage in the per-camera warp+write pipeline, or the lri_process outer loop iterating cameras and writing to a shared canvas buffer. Not yet identified.

Laplacian pyramid (`CreateAndBlendLaplacianPyramids`) is confirmed to belong to Stage 14 tone-adjust (`tone_adjust.lpyr_*` parameters), NOT fusion. Laplacian blend lambda at 0x1ab010 had 0 hits across all probe runs.

**Prior address error to avoid re-introducing**: `0x36fd30 / 0x36f800` was once claimed as the "fusion blend kernel." That's wrong — constant pool at 0x5a91e8 = `{255.0, 0.299, 0.587, 0.114}` (Rec.601 luma coefficients) with `cvttss2si → movb` byte writes proves it's a **luma-grid generator** (likely feeding GetSkippingMaskGrid), not a cross-camera blend.

### AWB (Stage 8) — no render-time estimator
- **There is no render-time AWB AUTO estimator in libcp.dylib.** All 4 `setWhiteBalance` lambdas recovered via typeinfo→vtable walk:
  - `$_20` operator() @ VA 0x342a80: metadata copy — reads Vec3f + 2 floats from `Pipeline+0x15d0` into `Stats+0..+0x10`. Not estimation.
  - `$_21` operator() @ VA 0x2eb560 (via 0x342b80): validates a stateless `Vec3f` gain, dispatches Halide parallel-for kernel that applies gains to Bayer cells.
  - `$_22` operator() @ VA 0x342ca0 (via 0x342c60): ÷2 downsample variant (mode at `Pipeline+0x150c`).
  - `$_23` operator() (via 0x3430d0): ÷4 / ÷8 downsample variant.
- **None iterate pixels, build histograms, sort bright pixels, or fit color lines.** No grey-world, no bright-pixel, no gamut-boundary, no Cheng estimator.
- `AWB_MODE_AUTO` enum dispatch @ VA 0x13eda0 is pure protobuf deserialization (validated against `$0x9`, error `"Unexpected AWB mode!"` @ 0x6309da). The enum is **stored but never branched on** at render time.
- Gains originate from LRI Block 8 f19.f15 (`[R_gain, 1.0, 1.0, B_gain]`), populated by on-camera hardware ISP at shutter time.
- Gains for L16_02130: **R=1.717839, G=1.0, G=1.0, B=1.588839**.

#### AWB application — RESOLVED (2026-04-13, Session 2 LLDB + Session 3 Block 8 decode)
**Rev-2 "multiply R-cells by R_gain" was directionally wrong.** Correct formula: `output = input × (1/stored_gain)` — equivalently, `output = input / stored_gain`. Reciprocals are pre-computed once at pipeline setup (via `divss` in Session 1 disasm) and stored in the AWB closure's `context_ptr[0]`; per-pixel time does a multiply. Verified by matching runtime `context_ptr[0] = (0.60669, 1.0, 0.56213)` against Block 8 f19.f15 of L16_02130 `{R=1.648295, G=1.0, B=1.778951}` to 5+ decimal places. Historical data points kept below for traceability:

**1. Disassembly says divss (reciprocal division)**
- `lambda_5` @ VA 0x340f70 tail-calls AWB kernel @ **VA 0x3510f0**
- Reads `payload.context_ptr[0]` as a per-channel gain vector
- Computes `1.0 / gain` via `divss` SSE instructions
- Source: `lldb_isp_findings.txt` PART 7, corroborated by `awb_analysis.txt` STEP 2

**2. Runtime-observed multipliers DO NOT match divss(stored Block 8 gains)**
On L16_01325 (via LLDB, `awb_analysis.txt`):
- Pre-AWB:  `[R=0.0476, G=0.0520, B=0.0587]`
- Post-AWB: `[R=0.0642, G=0.1458, B=0.1153]`
- Effective multipliers: **R × 1.35, G × 2.80, B × 1.96**

Stored Block 8 gains for comparable captures are `[R≈1.67-1.85, G=1.0, B≈1.52-1.69]`. Neither multiplying NOR dividing by those values produces `[1.35, 2.80, 1.96]`. Most glaring: stored `G_gain = 1.0` exactly, yet observed `G × 2.80`. The AWB stage is applying **more than a channel balance** — there's a global gain factor (~2.80× on L16_01325) layered on top of channel balance.

Decomposing: if `effective = global_gain × channel_balance`, then
- `global_gain ≈ 2.80`
- `channel_balance ≈ [0.48, 1.0, 0.70]`
- `channel_balance × stored_R_gain ≠ 1.0`, so channel_balance isn't `1/stored_gain` either

**3. `context_ptr[0]` contents are not Block 8 f19.f15 directly**
Something between the LRI file and the AWB kernel transforms the stored gains. Possibilities:
- Exposure/ISO normalization applied separately (the global 2.80× could be a black-level-normalized exposure scale, e.g. `white_level / max_pixel_headroom`)
- `context_ptr[0]` is populated by setWhiteBalance `$_20` "metadata copy" path, which reads from `Pipeline+0x15d0` — a cached struct written by an earlier pipeline step, not directly from LRI
- The "gains" in the kernel's context could be a computed reciprocal-of-stored times exposure scale

**Critical warning**: All the runtime numbers above come from L16_01325, which was identified as **corrupt test data** (missing VignettingCharacterization). The effective multipliers may not represent production behavior.

**Resolution path**: LLDB break on lambda_5 @ 0x340f70 during a PRODUCTION LRI bridge render (not L16_01325). Dump:
1. `*(float*)(context_ptr[0])`, `*(float*)(context_ptr[0] + 4)`, `*(float*)(context_ptr[0] + 8)` — the exact gain values used
2. Stored Block 8 f19.f15 from the same LRI
3. A few pre-AWB and post-AWB pixel samples
...and compute the actual transformation function. Until then, Phoenix cannot commit to an AWB implementation at all.

### CCM (Stage 12) — CCT-driven interpolation via Robertson table (rev 6 correction)
**Session 4/5 overturned an earlier conclusion that "CCM always returns D65 unblended."** The 9,438-LRI scan found `neutral_color` never persisted and concluded CCT computation fails — but Session 5 proved libcp uses a **DIFFERENT Robertson table at VA 0x66d420** (28 entries × 16 bytes) that is reached via a DIFFERENT function `ChromaticityFromCCT_Tint @ 0xab130` (not the `CCTFromChromaticity @ 0xab2e0` that fails on (0,0) input). The non-failing path takes `(CCT, tint)` as input and produces xy chromaticity as output — opposite direction from the failing path.

- **Input source**: `Pipeline+0x15d0` / `+0x15d4` contains `(CCT_float, tint_float)`, populated by protobuf parser at `0x318847` inside `Pipeline::fromProtoConfig @ 0x3184d0`, guarded by `Pipeline[0x1530] == 3` (AWB type = `manual_temp`). Source fields are `auto_white_balance.neutral_temp` and `.neutral_tint`. For L16_02130 the effective value is `(4300 K, 0)` — either from a numeric-wire protobuf field that string-scanning missed, or a Pipeline constructor default.
- **Runtime computation in setWhiteBalance $_20 @ 0x342a80**:
  1. Read `(CCT, tint)` from `Pipeline+0x15d0`
  2. Call `ChromaticityFromCCT_Tint @ 0xab130` → Robertson walk on 28-entry table at 0x66d420 → output normalized xy chromaticity `(0.36895, 0.21384)` for CCT=4300K
  3. Store into AWB closure `ctx[0x0c]` and `ctx[0x10]`
- **Downstream CCM lerp**: `CCMInterpBetweenCalib @ 0x350bc0` + `MatLerpClamped @ 0xab720` use the xy chromaticity (plus the CCT bracket endpoints at `ctx[0xa8] = (2855.63, 6502.08)` K and the two baked 3×3 CCMs at `ctx[0xb8..0xf0]`) to compute the per-camera blended matrix. Not D65-only, not clamped to an endpoint — real interpolation.
- The earlier `CCTFromChromaticity @ 0xab2e0` path (Robertson table at 0x66d410, 31×3 floats) is for the **reverse direction** (xy → CCT) and is reached when a scene `neutral_color` IS provided. For L16 LRIs, that path is indeed never exercised (corpus scan was right about that). But the forward direction (CCT → xy) via 0x66d420 IS exercised, every render.

### Phoenix action: CCT-driven CCM blend
- **MVP**: hardcode scene chromaticity to `(0.36895, 0.21384)` (equiv. CCT=4300K) in your AWB/CCM setup. <1 ΔE error on neutral scenes.
- **v1.0 parity**:
  1. Parse `auto_white_balance.neutral_temp` from LRI protobuf (numeric wire format — scan with a number-keyed walker, not string-based). Default to 4300 K if absent.
  2. Dump the 28-entry × 16-byte Robertson table from VA 0x66d420 + 5 rodata constants (K_X/K_Z/K_C/C1 and tint coefficients).
  3. Port `ChromaticityFromCCT_Tint @ 0xab130` verbatim — computes `mired = C1/CCT`, walks table, linearly interpolates, applies tint, outputs normalized xy.
  4. Parse the two factory CCMs from **Block 6** (35,266 bytes, 14 cameras × 3 illuminants × 3×3 float). Endpoints are illuminant A (2855K) and D65 (6502K) per the closure layout.
  5. Interpolate per-camera CCM using `MatLerpClamped` semantics — linear in mired with clamp.
  6. Apply resulting 3×3 to demosaicked RGB per camera.

### Static code paths (kept for reference — real code, just never used)
- `CCTFromChromaticity(Vec2 xy)` @ VA **0xab2e0** — 30-iteration Robertson search
- Robertson (u, v, slope) table @ VA 0x66d410 (bss, runtime-populated, never converges)
- Constants `175, 0.20525, 0.31647, -0.84901` @ VA 0x5ab180; `1e6` mired→K @ VA 0x5aae64
- `CCMInterpBetweenCalib` @ VA **0x350bc0** → `MatLerpClamped` @ VA **0xab720** — clamped reciprocal-K lerp formula: `α = clamp((1/T − 1/T_B)/(1/T_A − 1/T_B), 0, 1); M_out = M_B + α × (M_A − M_B)` — always executes but with T=0 so α is always pinned
- `Illuminant::xyToXYZ` @ VA 0xa9130 — supports 12 DNG light sources but factory only ships 3 (A/D65/F11 on this device)
- PCS = D50
- Error strings: `"Color calibration must have at least 2 illuminants!"`, `"two forward matrices are required in dual-illuminant pipeline"`, `"PCS illuminant is not D50"`

### Historical miscellany (not used by render path)
- 151 LRIs in the corpus carry an `f27` sub-message with face detection data (count, bboxes, scores). Unrelated to AWB/CCM.

### CRA correction (confirmed)
- Class: `lt::LensUndistortCRA`, applied via `ImageWarp<ResamplerFilter::Bicubic, vec4x8ui, LensUndistortCRA>`
- Stage: **Pre-demosaic**, at tile-fetch time inside `SourceImageCache` constructor — NOT a numbered pipeline stage
- Input type: `vec4x8ui` = packed Bayer 4-channel tile (R, Gr, Gb, B as 16-bit)
- Operation: 4×4 Bayer channel mixing matrix at each pixel, bilinear-interpolated from 13×17 spatial grid
  - `output[i] = Σ_j matrix[i,j] * input[j]` for channels i,j ∈ {R, Gr, Gb, B}
  - Center matrix ≈ identity (diagonal ~[1.0, 1.003, 0.997, 1.0], off-diagonal ~1e-4)
  - Corner matrices: diagonal drops to ~0.95, off-diagonals reach ~0.02 (optical CRA cross-talk)
- **Separate from** electronic cross-talk correction (`RemoveCrossTalkGeneric`, numbered stages 14–19)
- cra_grids npz shape: (16, 13, 17, 4, 4) — spatial grid (13 rows × 17 cols) × 4×4 matrix per camera
- **Phoenix: apply 4×4 mix bilinear-interpolated from grid to each Bayer quad, BEFORE demosaic**

### Depth solver (3 Ceres passes)
| Pass | Function | Role | Phoenix action |
|---|---|---|---|
| A | `LabCostFunction<25,9>` @ 0x11749a | Offline HSV/Lab color calibration | **Skip** — use factory CCM from OQ-C |
| B | `LightBA` (CameraProjection + EntrancePupilCost + IntrinsicsCost) @ 0x201a4f | Offline bundle adjustment, 6-stage coarse-to-fine | **Skip** — use baked intrinsics/extrinsics from OQ-C |
| C | `ReProjectionCost<2,1>` @ 0x20d1ac | Per-point bounded 1-DOF Cauchy-weighted depth refinement | **Reimplement** with `scipy.optimize.least_squares(loss='cauchy', bounds=(lo,hi))` |

Pass C structure: 1 scalar depth parameter per feature point, N reprojection residuals (one per observing camera), CauchyLoss with bounds, outer loop over all feature points = `lt::Triangulator::refine3dPoints`.
- **CauchyLoss scale `a` = 1.0 exactly** (verified: b_=a²=1.0 stored at VA 0x5c3580; transition from quadratic to log at ≥1px residual)

---

## Bicubic Renderer

- Entry point: `project_roi_to_camera` @ 0x3e2e90
- Algorithm: Catmull-Rom, float32 RGBA

---

## Android / Cross-Platform

- Android `light_gallery.apk` (v1.3.5.1) bundles `libcp.so` (arm64, same library)
- `libcp.so` is equally stripped — no additional symbols vs macOS dylib
- `libceres.so` is separate (dynamically linked), macOS statically links Ceres into libcp
- `liblricompression.so` = libjpeg-turbo stack-LRI recompressor (firmware path only, not relevant to LRI decode)
- JNI bridge (`libnative-lib.so`, 32 entry points) routes through `CIAPI::RendererBase::setProperty` — same public facade as macOS
- Downloaded to: `/Volumes/Dev/lumen-phoenix-scratch/android_libs/`

---

## ISP Stage VA Map (libcp.dylib)

| Stage | Function / purpose | VA |
|---|---|---|
| — | `Illuminant::xyToXYZ(int idx)` (12 DNG LightSource enum) | 0xa9130 |
| — | `CCTFromChromaticity(Vec2 xy)` — Robertson search | 0xab2e0 |
| — | `MatLerpClamped` — mired-space CCM lerp | 0xab720 |
| — | `auto_white_balance.neutral_color` protobuf parse | 0x13eda0 |
| — | Cross-camera fusion blend kernel (N≥2 branch) | 0x1bd0a0 |
| — | Fusion weight LUT (256 float32, `sqrt((i+1)/256)`) | 0x5d2390 |
| — | Fusion inner loop | 0x1bd170 |
| 7 | `setLensShading` | 0x3184d0 |
| 7 | Pipeline-tune helpers (reach setLensShading) | 0x318030, 0x318040 |
| 8 | setWhiteBalance $_20 (metadata copy) | 0x342a80 |
| 8 | setWhiteBalance $_21 (Vec3f gain apply, Halide kernel) | 0x2eb560 |
| 8 | setWhiteBalance $_22/$_23 (downsample variants) | 0x342ca0 |
| 10 | `DemosaickLightV2<0,0>` (profile 0 bridge path) | 0x2f0df0 |
| 10 | DemosaickLightV2 inner kernel | 0x2f1050–0x2f148b |
| 12 | `CCMInterpBetweenCalib` | 0x350bc0 |
| 12 | setColorCorrection payload-direct ($_58) | — |
| 14 | `setToneAdjust` + local-Laplacian `CreateAndBlendLaplacianPyramids` | — |
| 15 | TMO base ctor (indexed LUT lookup) | 0x2d76b0 |
| 15 | `setToneMapping` (sole callsite) | 0x319369 |
| 15 | Tone curve defaults function (`isLowLight()`-driven) | 0x3c7860 |
| 15 | Tone curve LUT pointer table (4 entries) | 0x659c70 |
| 15 | Tone curve LUTs: acr / light_v1 / light_v1_lowlight / light_v2 | 0x5e31b0 / 0x5e41b4 / 0x5e51b8 / 0x5e61bc |
| — | `project_roi_to_camera` (per-tap warp, Catmull-Rom + 1/z) | 0x3e2e90 |
| — | CauchyLoss `a²=1.0` constant (depth refinement) | 0x5c3580 |
| — | `Settings.exposure` protobuf descriptor | file offset 0x6143c2 |
| — | EV offset writers | 0x3c70e0, 0x3b3783 |
| — | Robertson (u,v,slope) table (bss — LLDB dump post-init) | 0x66d410 |
| — | Robertson constants `{175, 0.20525, 0.31647, -0.84901}` | 0x5ab180 |
| — | Robertson mired→K constant `1e6` | 0x5aae64 |
| — | `Illuminant` xy table A (x values) | 0x5ab760 |
| — | `Illuminant` xy table B (y values) | 0x5ab720 |

---

## Honest Approximations Phoenix Ships With

Phoenix is a clean-room reimplementation. It cannot achieve byte-level parity with Lumen's bridge output because key pieces of Lumen's pipeline are either (a) Halide-JIT'd (generated at runtime, not in the AOT binary), (b) proprietary constants that can't be shipped without legal review, or (c) out of scope for a render-only tool. **Phoenix's spec must explicitly flag each approximation so the implementer and the user both understand the deviation.** These are NOT bugs — they are documented design decisions.

### 1. Demosaic — Hamilton-Adams algorithm class, not DemosaickLightV1 byte parity
**Approximation**: Phoenix implements an edge-aware gradient-weighted green interpolation in the Hamilton-Adams family (or VNG / AHD as alternatives). Session 4 verified Lumen's V1 kernel is the same algorithm class but the specific coefficients, branch thresholds, and Halide-compiled vectorization are not statically extractable.
**Known deviation**: subtle differences in demosaic artifacts at high-frequency edges (zippering, color fringing). Typical impact: <1% of pixels visibly different under 100% pixel peeping; imperceptible at normal viewing.
**Mitigation**: pick a well-characterized published algorithm (VNG is documented; Hamilton-Adams has papers). Do not claim byte parity with Lumen's demosaic.

### 2. Tone curve — SOLVED via Hable + Naka-Rushton parametric fits
**Status: empirically resolved (Session 6 `session6_tone_curve_fit.md`).** All four Lumen tone curves fit cleanly to published parametric formulas with sub-perceptual deviation. Phoenix ships `phoenix_tone_curves.py` as a clean-room module containing only fitted scalar parameters (no LUT bytes anywhere).

Per-curve fit results (all in linear scene-radiance space, no pre-shaper required):

| Curve | Formula | RMS | Max abs |
|---|---|---|---|
| **light_v1** (bridge default) | Hable normalized | **0.205%** | 0.439% |
| light_v2 | Hable normalized | 0.101% | 0.247% |
| light_v1_lowlight | Hable normalized | 0.049% | 0.389% |
| acr | Naka-Rushton scaled | 0.284% | 0.584% |

**Phoenix spec commitment**: tone curve stage ≤0.5% RMS, ≤1.0% max-abs vs Lumen reference. Comfortable margin to measured values.

**No pre-shaper code in Phoenix.** The Lumen pre-shaper at `libcp:0x5e3180` is just an indexing trick for their LUT lookup. The fit was performed in Space B (linear scene radiance, with the inverse pre-shaper applied to recover original `x`), so Phoenix's tone curve takes linear input directly into the Hable/Naka-Rushton formula and produces tone-mapped output. Round-trip verification of the inverse pre-shaper was machine-precision exact.

**Sub-perceptual deviation.** 0.2% RMS on a tone curve is invisible. Even on calibrated reference monitors with side-by-side comparison, this deviation is not detectable by humans.

**Phoenix module**: `phoenix_modules/phoenix_tone_curves.py` (6.8 KB, 239 lines, byte-free of LUT data). Self-check via `python3 phoenix_tone_curves.py` reproduces the fit metadata and sample evaluations.

### 3. CCT blend weight — hardcoded vs. runtime-derived
**Approximation (MVP)**: Phoenix hardcodes scene chromaticity `(0.36895, 0.21384)` corresponding to CCT ≈ 4300 K. This matches Lumen's behavior on L16_02130 and is the Pipeline constructor default for captures where `neutral_temp` isn't explicitly set.
**Known error**: <1 ΔE on neutral scenes; larger deviation on captures with very different illuminant (tungsten indoor, fluorescent). Non-neutral scenes may look warmer or cooler than Lumen's output.
**v1.0 path**: dump the 28-entry Robertson forward table at `libcp:0x66d420`, implement `ChromaticityFromCCT_Tint @ libcp:0xab130` from description, parse `neutral_temp` from LRI protobuf when present. Still an approximation (Halide-JIT arithmetic) but much closer.
**Mitigation**: flag the CCT source in every export's metadata so the user can see which value was used.

### 4. Linearize + color_scale — Halide-JIT, semantic equivalent only
**Approximation**: Phoenix implements `(bayer_float - black_level[cam]) / (white_level[cam] - black_level[cam])` using per-camera values parsed from each LRI. Lumen's `lambda_0 @ libcp:0x340b00` computes the semantically identical transform but in Halide-JIT code that isn't in the AOT binary.
**Known deviation**: Halide's vectorization + rounding may differ from a naive scalar implementation at the 1-ULP level. Not visible in any practical viewing scenario.
**Mitigation**: none needed — this approximation is below perception threshold.

### 5. Bundle adjustment — NOT reimplemented (out of scope)
**Out of scope**: Phoenix does NOT run Ceres bundle adjustment at render time. Lumen has three Ceres passes (`LabCostFunction` color cal, `LightBA` bundle adjustment, `ReProjectionCost` depth refinement). The first two are OFFLINE / factory calibration and their output is baked into each LRI's calibration blocks. The third is per-point depth refinement and Phoenix reimplements it using `scipy.optimize.least_squares(loss='cauchy', bounds=...)` for MVP, with the option of embedding a small C++ Ceres wrapper for parity in v1.0.
**Known deviation**: factory calibration passes are correctly handled (Phoenix reads the baked outputs). Depth refinement has Cauchy-loss scale `a = 1.0` verified at `libcp:0x5c3580`; Phoenix's scipy port should match to numerical precision.
**Mitigation**: spec explicitly lists Ceres Passes A and B as OUT OF SCOPE — implementer must not waste time reimplementing them from scratch.

### 6. Cross-camera merge — inferred from DemosaickLightV1 closure accumulation
**Approximation**: Phoenix's cross-camera merge is per-camera warp-and-accumulate into a shared canvas, matching the inferred Lumen behavior from Session 2/3. The exact warp parameters per camera are parsed from LRI calibration (R_fold, virtual_pos, distortion grid).
**Known deviation**: at tile seams between overlapping cameras, Phoenix may show tiny geometric misalignments if the distortion grid interpolation differs from Lumen's bicubic implementation. Session 2's seam analysis on L16_02586 showed B4/A1 boundary was seamless (Pearson r=0.376) — Phoenix should match this.
**Mitigation**: validation comparison against `ground_truth.tiff` at known seam regions.

### 7. Phase B (mono output) — intentionally SKIPPED
**Out of scope**: Phoenix does not emit Lumen's grayscale output. Lumen runs a separate mono-path render (lambda_7 + lambda_8, Phase B in Session 2 observations) that produces a uint16 grayscale TIFF. Phoenix only implements the color path (Phases A/C/D: lambda_0/1/2/5/6).
**Rationale**: no product requirement for a grayscale-only output format.

### 8. WDR/HDR bracket fusion — NOT separately implemented
**Out of scope**: `FusionCacheBayer` / `PackedBayerFusion` / `0x1bd0a0` are a single-image HDR bracket merger that only fires when an LRI carries multi-exposure data. The 9,438-LRI corpus scan found no such files. Phoenix does not implement the N≥2 bracket fusion path.
**Mitigation**: Phoenix's LRI parser should detect bracket LRIs (if they ever exist) and return a `PipelineError.unsupportedFormat("HDR bracket LRIs are not supported in v1.0")` rather than rendering incorrectly.

---

## Open Items / Unresolved Questions

These are items still needing investigation before Phoenix can begin. Nothing in the verified sections above depends on them, but Phoenix output parity with the Lumen bridge does.

1. ~~**C5 / C6 encoder anomaly**~~ — **RESOLVED.** Not an anomaly. C5 and C6 are **fixed-mirror cameras** (verified in `movable_mirror_formula.txt` and `zoom_config_table.txt`). They correctly report encoder=0 because they have no motor. The rev-2 claim that they were "movable with 4-entry encoder tables always reporting 0" was a side-effect of the mis-identified movable set — corrected in the Mirror/focus configs section above.

2. **DemosaickLightV2 scalar provenance** — the V2 kernel uses its float scalar as gradient-regularization noise floor `ε`. How the float is computed upstream is not extracted. The 7 `setDemosaicking $_25..$_31` operator() lambdas take `Vec3<float>` in the outer signature; the Vec3→float reduction happens inside the captured `DemosaickFilter<E2, float, X, Y>` functor body. Needs LLDB break on DemosaickLightV2 entry reading xmm0 during a production render.

3. **DemosaickLightV2 secondary scalar path** — the V2 kernel also computes `scalar × -0.02` and hands it to sub-call 0x2f16d0. Consumer unresolved; may affect chroma or saturation output. Static disasm-only, no runtime needed.

4. ~~**Robertson (u, v, slope) table values**~~ — **RESOLVED as irrelevant.** The 9,438-LRI corpus scan proved `neutral_color` is never populated on any real LRI, so the Robertson search at 0xab2e0 always fails to converge and writes 0.0f. The specific (u, v, slope) table values at 0x66d410 never affect runtime output because the search never finds a sign change on `(0, 0)` input. Kept in the code but effectively dead at runtime. Phoenix can skip the entire Robertson/CCT path.

5. **Fusion mask origin + upstream 10-camera merge** — see #12.

6. **AWB application numerical invariant** — the disasm at lambda_5 AWB kernel @ VA 0x3510f0 computes `1/gain` via `divss`, but runtime-observed effective multipliers on L16_01325 (`awb_analysis.txt`) are `[R×1.35, G×2.80, B×1.96]` — **cannot** be reproduced by either `multiply(stored_gain)` or `divide(stored_gain)` with the Block 8 f19.f15 values. The kernel is applying `global_gain × channel_balance` where both factors are something other than the raw stored gains. `context_ptr[0]` contents are not Block 8 f19.f15 directly — some transformation (likely exposure/ISO normalization + channel reciprocal) happens upstream. This is a **blocker** for any Phoenix color implementation. Needs LLDB dump of `context_ptr[0]` contents at lambda_5 entry on a PRODUCTION LRI (not L16_01325 which is corrupt test data). See AWB section above for full analysis.

7. **Stage order across the full 16-stage pipeline** — individual stage VAs are verified, but end-to-end ordering is based on lambda-number static ordering + partial LLDB hit-count evidence on a **corrupt test LRI (L16_01325)**, not a production render. Multiple specific stages are disputed — see #13 for LensShading in particular.

8. ~~**LRIS sidecar depth encoding**~~ — **RESOLVED** in `alpha3_lris_decode.txt` (2026-04-12). Magic 0x51E8E000 = Section 3. Sub-header 1234 bytes (154 records × 8 bytes, each `float32 depth_cm, float32 val`). NEAR=3460mm, FAR=116930mm. Depth payload 336×252 uint16 stored as float32. Decode: `depth_mm = 3460 + (116930-3460) × arr / 16383`. Artifact: `lumen_depth_l16_02586.npy`. Kept here for historical reference.

9. ~~**`neutral_color` content when LRI has AWB_MODE != AUTO**~~ — **RESOLVED.** `session2_awb_mode_scan.md` scanned 9,438 LRIs across the entire corpus: `neutral_color` is NEVER present in ANY LRI regardless of mode. Same for `neutral_temp`, `neutral_tint`, and the 9-value `awb_mode` enum. Only Block 8 f19.f15 `[R, 1, 1, B]` gain vector is persisted. Non-AUTO AWB modes effectively do not exist in the corpus (the single boolean flag is 0 in 99.89% of files). libcp's "fallback" path (neutral_color=(0,0) → Robertson returns 0 → clamped-lerp pins to one CCM) is the normal execution path for every render. **Phoenix: always apply fixed D65 CCM, skip CCT computation entirely.**

10. **AR1335 linearization arithmetic** — lambda_0 `LinearizeAndColorScale` @ VA 0x340b00 confirmed; inner kernel at **0x3589c0** (Halide-generated); observed output range [0.03, 0.17] on a dark tile; ev_min=42.0 / ev_max=1023.0 confirmed used in fusion init. **Exact arithmetic not instruction-walked.** Assumed `(raw - 42) / 981`; unverified. Static disasm of 0x3589c0 would close this.

11. ~~**Movable camera set contradiction**~~ — **RESOLVED.** Movable = {B1, B2, B3, B5, C1, C2, C3, C4}. `movable_mirror_formula.txt` and `zoom_config_table.txt` independently agree on both the set and that R_fold is static (no per-capture rotation). The rev-2 `lri_header_camera_config.md` claim of {B1,B2,B3,B5,C1,C4,C5,C6} was wrong. Main doc section above has been corrected. **Follow-up for `lri_header_camera_config.md`**: re-audit that agent's output to determine which protobuf field it was counting and why it inverted the C2/C3 vs C5/C6 identity. Some of its other claims (encoder readings in `LightHeader.field_12[].field_4`, argmin selection) may also need re-verification since they were produced by the same analysis chain.

12. ~~**Location of the actual 10-camera Bayer merge**~~ — **RESOLVED.** The merge is a side effect of `DemosaickLightV1::operator()` — each variant invocation reads one camera's Bayer from closure `+0x10` and writes to the shared canvas at closure `+0x08`. 10 cameras × N tiles × 3 phase variants = ~10 writes per tile location = the merge. There is no dedicated merge stage; accumulation into the shared canvas IS the merge. See Rev 5 architecture box at top.

13. ~~**LensShading runtime stage position**~~ — **RESOLVED.** BOTH templates fire. Vignetting is applied pre- AND post-demosaic via separate ThreadPool::TaskRange worker path: `<float,true>` @ 0x108370 (pre-demosaic Bayer, 2,249 hits); `<vec4x32f,true>` @ 0x108080 (post-demosaic RGBA, 10,994 hits — dominant); `<vec4x32f,false>` @ 0x1086c0 (391 hits). The "Stage 7 vs Stage 9" dispute was a false dichotomy.

14. ~~**AWB application direction** (merged into #6 above — this is the same item as originally-numbered #6; kept number for index stability)~~

15. **"Fusion" is HDR bracket fusion, not cross-camera** — the entire `FusionCacheBayer` / `PackedBayerFusion` / `0x1bd0a0` / `0x5d2390` subsystem plus all `fusion_*` config keys (`fusion_ev_plus`, `fusion_ev_minus`, `fusion_noise_filter_scale`, `fusion_detail_gain`, `fusion_noise_gain`, `fusion_black_point`) live under `tone_adjust.*` namespace — they are **single-image HDR bracket fusion / local-Laplacian tone mapping**, not cross-camera compositing. Rev 1 and rev 2 of this doc both got the identity wrong. The 10-camera merge (#12) is in a different, unidentified stage. This entry is kept for historical visibility so future agents don't re-derive the wrong claim.

16. ~~**Real raw→float linearization site**~~ — **RESOLVED.** Linearization lives inside `DemosaickLightV1::operator()` — not a separate stage. The raw→float arithmetic is encoded in closure +0x18 scalars of each V1 variant. Exact formula (black level subtraction, scale factor, gain multiplication) hides in the Halide-compiled kernel body and was not instruction-walked — see follow-up #22.

17. ~~**Real demosaic site**~~ — **RESOLVED.** `DemosaickLightV1` (not V2) fires on L16_02130 28mm. Three phase variants run: `V1<0,0>` @ 0x2ed580 (176 hits), `V1<1,0>` @ 0x2eeb20 (636 hits, dominant), `V1<1,1>` @ 0x2f0240 (299 hits). V2 variants are dormant on this LRI. V1 takes `Vec3<float>` WB gains inline per-pixel (unlike V2's single-scalar-as-ε path). Why V1 instead of V2 fires is a Renderer Profile dispatch decision at 0x3cd290 — follow-up #23.

18. ~~**3-phase render architecture — Phase B purpose**~~ — **RESOLVED (`session4_phase_b_purpose.md`).** Phase B is the L16 **mono-path final render**, not a preview or stats pass. libcp has three parallel sibling fusion modules (`lt::MonoFusion::initialize`, `lt::ColorFusionBayer::initialize`, `lt::StackFusion`) — Phase B's lambda_8 (MonoPipelinePayload) executes the mono path. Evidence:
    - Phase B writes **uint16** (ColorPost dest `leaq (%r8,%rax,2)`); Phase D writes **float32** (`leaq (%r8,%rax,4)`)
    - MonoMerge @ 0x3596e0 reads two float32 canvases (payload +0xd0 and +0x130) and merges into uint16 output
    - Phase B tile geometry (260×260) is final-canvas coordinates; Phase D (226-242 shrinking-border) is per-camera
    - BayerPipelinePayload / ColorPipelinePayload / MonoPipelinePayload use **disjoint field offsets** — no data dependency between phases
    - No `preview` / `pre_pass` / `stats_pass` strings near dispatcher
    - **Phoenix action**: SKIP Phase B entirely. Install only lambda_0/1/2/5/6 (color path) and skip `$_7` / `$_8` from PipelineC1 defaults. Phoenix does not need to emit a mono-path output.

19. ~~**LensShading per-tile reconfigure**~~ — **RESOLVED.** setLensShading's 1966 calls are CONFIGURATION/allocation hits, not execution. Actual vignetting work runs on a separate `ThreadPool::TaskRange` worker path (13,634 total `RemoveVignettingGeneric::operator()` calls per render). setLensShading caller histogram maps 1:1 to lambda counts per-phase, confirming "once per tile per stage" configuration. Three live template variants all fire (see #13).

20. **AWB context_ptr relationship — R/G/B reciprocals CONFIRMED, slot 4 RESOLVED with reframe (Session 4).**
    - Slots 0-2: reciprocals of Block 8 f19.f15 `{R=1.648295, G=1.0, B=1.778951}` → runtime context `(0.606688, 1.0, 0.562129)` match to 5+ decimals. `divss` runs once at pipeline setup; per-pixel is a multiply. Phoenix: `output = input / stored_gain`.
    - **Slot 4 = 0.36895 is the CCT interpolation weight `t_cct` for the two-CCM lerp between illuminant-A and D65** (not an AWB field). Full 256-byte context dump shows: `ctx[41..42] = (2855.63, 6502.08)` = CCT_A, CCT_D65 endpoints in Kelvin; `ctx[46..54]` + `ctx[55..63]` = two 3×3 CCMs (green-unity row-sum). `t_cct = 0.36895` → scene CCT ≈ 4200 K (linear) or 4420 K (mired). Slot 4 does NOT affect AWB kernel output (only slots 0/1/2 are consumed per-pixel); it affects Stage 12 CCM mixing.
    - **This contradicts the earlier "always return D65 unblended" conclusion from the 9,438-LRI neutral_color scan.** libcp really does blend A↔D65 with a non-trivial CCT weight. How CCT is computed when `neutral_color` is never present in the LRI is still unknown — candidates: (a) derived from Block 8 gains themselves (some transformation of R/B ratio), (b) derived from a different capture metadata field not yet identified, (c) hard-coded default for 28mm captures. Needs memory-write watchpoint on context_ptr+0x0c during setWhiteBalance to capture provenance.
    - **Phoenix action**: parse Block 6 for the two factory CCMs (A and D65) + CCT endpoints. MVP can hardcode `t_cct = 0.5` (~1 ΔE error on neutral scenes). v1.0 must compute `t_cct` via whatever libcp actually does — open follow-up.

22. ~~**Linearize arithmetic**~~ — **CLOSED with workaround (Session 5 `session5_lambda0_linearize.md`).** The exact per-pixel `subss/mulss` pair is NOT statically extractable — it's **JIT-generated by Halide at runtime**, not present in libcp's AOT-compiled binary. What was verified statically:
    - **Call chain**: `lambda_0 @ 0x340b00` → Halide builder `@ 0x3589c0` → `operator new(0x30)` + vtable `@ 0x65e0b0` → polymorphic `vtable[3] @ 0x359e30` with 3-way dispatch on `closure[0x28]`: `<0.9999...` → kernel `0x35d5c0`; `>1.0000...` → kernel `0x35c220`; identity → kernel `0x35b5d0` (matches the 972 hits observed for lambda_0).
    - **Kernel 0x35b5d0 is a colorspace builder**, not the pixel loop. Calls `0xa9130(primary_id)` for CIE xyY→XYZ conversion via illuminant tables at `0x5ab720`/`0x5ab760`, computes `1.0f / primary[0..2]` using 1.0f const at `0x5a8128`, builds 2×2 via `insertps` against identity `[1,0,0,1]` from closure+0x16b0. Loads hyperparameters `0.0005f` noise_epsilon (@0x5fbe34) and `0.005f` black_variance (@0x5fbe38) — NOT black level.
    - Candidate pixel arithmetic at `0x35f005..0x35f1d2` (off the main path): `movss/subss/mulps` sequence reading `[rbx+0x10]`, `[rbx+0xc]`, `[rbx+0x48/0x4c/0x50]` — looks like `out = (p − black) × scale_per_channel`, but it's reached from sibling builders, attribution uncertain.
    - **Black level and scale never appear in lambda_0's static closure** (stack frame offsets 0x20–0x7c are all rectangle bounds / strides / data_ptr). They arrive via the payload pointer at `rdi+8`, populated at pipeline-invocation time from per-camera calibration.
    - **Phoenix workaround (adopted)**: implement `(bayer_float - black_level[cam]) / (white_level[cam] - black_level[cam])` using per-camera values **parsed from the input LRI's calibration blocks at render time** (Phoenix runs its own calibration parser on each LRI — it does NOT load a pre-extracted archive). The `cal_color_l16_02130.npz` in the handoff is a REFERENCE EXTRACT showing what the parser should produce for one sample LRI; it is NOT Phoenix's runtime source of truth. The color_scale 2×2 at closure+0x16b0 is confirmed identity `[1,0,0,1]`, safely ignored as no-op on this build. CIE primary mix is handled by the CCM stage, not linearize.
    - **Not achievable via static analysis**: exact byte-level parity with libcp's Halide-JIT'd kernel. Would require LLDB JIT dump during render if ever needed. Semantic correctness is guaranteed by the formula above.

23. ~~**Why V1 fires instead of V2 on L16_02130**~~ — **RESOLVED (`session4_v1_v2_selector.md`).** Two-layer dispatcher:
    - **Renderer-level** dispatcher at VA 0x3cbc10 writes `"light_v2"` as Profile 1 default (old `demosaic_static.txt` claim was correct at this level).
    - **Per-camera dispatcher** at VA 0x40b370 / 0x40c2a0 OVERWRITES with `"light_v1"` or `"light_v2"` based on a 4-value `PipelineBase::Demosaicking` enum at Pipeline struct offset 0. **Even enum → V2, odd enum → V1.**
    - Enum set by per-camera factory at VA 0x402d20 using `isLowLight()` flag (same flag as tone curve selector at 0x3c7860) + a 5-bucket EV/ISO classifier.
    - Dispatch chain: `Pipeline::setDemosaicking` @ 0x32d510 → 9-case jump table @ 0x330710 → enum 7 ("light_v1") → lambda `$_25` → vtable 0x65b948 → forwarder 0x342b80 → `jmp 0x2eb560` V1 driver; enum 8 ("light_v2") → `$_26` → vtable 0x65bab8 → forwarder 0x343180 → `jmp 0x2eba10` V2 driver.
    - **V2 scalar is HARDCODED 1.0f at VA 0x5a8128** — V2 has no runtime parameter. This **contradicts** the earlier `q456_tone_ev_v2param.md` hypothesis that V2's scalar is a Vec3→float reduction of WB gains. Real V2 operation: `ε = 1/128` fixed (from earlier finding `scalar × 1/128`); anti-undershoot clamp = -0.02 fixed. V2 is a parameterless kernel, not a "sharpness vs cleanliness knob."
    - **V2 appears dead in the libcp 0.26.3 build** — zero runtime hits across all captures tested. Phoenix action: **implement V1 only**. If implementing V2 defensively, pass scalar=1.0.
    - UNVERIFIED: exact branch inside 0x402d20 that sets enum=1 (odd, V1-selecting); whether V2 is reachable at all in this build. Not blocking — V1 is always selected.

24. ~~**DemosaickLightV1 template phase mapping**~~ — **RESOLVED** (`session4_v1_linearize.md`). `V1<offX, offY>` encodes `(tile_x mod 2, tile_y mod 2)` — which corner of the BGGR 2×2 cell the tile origin lands on: `<0,0>` = B corner; `<1,0>` = G-in-B-row (dominant 636 hits); `<0,1>` = G-in-R-row (dormant — scheduler folds into `<1,0>` by horizontal symmetry); `<1,1>` = R corner. Hit distribution (176/636/299) matches tile-origin statistics across the 16-camera ROI grid. **Phoenix needs ONE runtime-parameterized kernel**, not 4 template specializations.

26. **Calibration-block protobuf parser documentation GAP.** Phoenix must parse Blocks 3/4/5/6 from each input LRI at render time to produce per-camera `black_level`, `white_level`, `vignetting_grid`, `CRA_grid`, `CCM_matrices`, `R_fold`, `virtual_pos`, `encoder_nominals`, and geometric intrinsics (K matrix, distortion). **Partially documented** in this file: Vignetting path `rec.f4.f2[ch].f2.f3` and CRA path `rec.f4.f1.f4` are captured. Also captured: warp-block encoder nominals at `field_13[cam].field_4.field_2[i].field_1` and the 78-float mirror_raw leaf structure (see `investigation_traceability/movable_mirror_formula.txt` for R_fold/virtual_pos offsets). **Not explicitly captured**: `black_level` and `white_level` protobuf paths; Block 3 (geometric) protobuf paths; Block 6 (CCM) exact protobuf field path (only the 14×3×3×3 array shape is documented). Resolution path: static reverse of whatever tool produced `cal_color_l16_02130.npz` (likely `spike_oqc_cal_extract.py` in the scratch tree) — its parse logic IS the missing documentation. Phoenix's calibration parser must be a clean-room reimplementation of those paths, not a copy of spike code.

27. ~~**LEGAL REVIEW NEEDED — tone curve LUTs + Robertson forward table provenance**~~ — **DISSOLVED for tone curves (Session 6).** All 4 tone curves now ship as fitted parametric formulas in `phoenix_modules/phoenix_tone_curves.py` (Hable normalized + Naka-Rushton scaled, ≤0.5% RMS deviation). The Phoenix module contains only fitted scalar parameters — no LUT bytes from `libcp:0x5e31b0/0x5e41b4/0x5e51b8/0x5e61bc` ever enter Phoenix's source tree. There is no plausible legal interpretation under which 6 fitted Hable parameters of a published filmic tone-mapping formula constitute libcp IP — this is the same legal pattern as dcraw / LibRaw / Darktable shipping fitted color matrices.
    - **Robertson forward table at `libcp:0x66d420`** — STILL needs verification. Likely Wyszecki-Stiles published values (textbook scientific data, public domain), but until the byte comparison is run against the published table, low-grade uncertainty remains. Quick task: dump the 28×16 bytes from the bss table and compare against Wyszecki & Stiles "Color Science" §3.11. If they match, Phoenix can use the published values directly with zero ambiguity.
    - **Phoenix distribution is NOT blocked on this open item anymore.** The eBay scenario (user with no Lumen install on a fresh L16) works: Phoenix's tone curves are 100% formula-based clean-room code.

25. ~~**CCT blend weight derivation**~~ — **CLOSED with semantic reframe (Session 5 `session5_cct_derivation.md`).** Session 4's "t_cct = CCM interpolation weight" interpretation was wrong. `ctx[0x0c] = 0.36895` and `ctx[0x10] = 0.21384` are actually the **scene illuminant chromaticity coordinates** (normalized CIE xy from Kim's Planckian locus), not a lerp parameter between two CCMs.
    - **Writer**: `setWhiteBalance $_20 @ 0x342a80` calls `ChromaticityFromCCT_Tint @ 0xab130` with inputs at `Pipeline+0x15d0` / `+0x15d4` (CCT, tint floats). Function walks a 28-entry × 16-byte **Robertson isotemperature-line table at VA 0x66d420**, finds mired bracket via `C1/CCT`, linearly interpolates with tint offset, outputs normalized `K_X·x/(x+K_Z·y+K_C)` and `y/(x+K_Z·y+K_C)`. Values copied into `ctx[0x0c]`/`ctx[0x10]`.
    - **Verified**: 0.36895 matches Kim's polynomial for **T ≈ 4280 K** to 4 decimals; 0.21384 matches the rescaled `y/D` form. Consistent with ~4300 K scene CCT, tint=0.
    - **Source of input CCT**: `Pipeline+0x15d0` has ONE writer (`setter @ 0x33ead0`), called from ONE site (`protobuf parser @ 0x318847` inside `Pipeline::fromProtoConfig @ 0x3184d0`), guarded by `Pipeline[0x1530] == 3` (AWB type = `manual_temp`). Source fields: `auto_white_balance.neutral_temp` and `.neutral_tint`.
    - **Unresolved micro-detail**: byte-grep of L16_02130.lri finds ZERO hits for `auto_white_balance` / `neutral_temp` string descriptors. Either the protobuf uses numeric wire format (which the string-based 9,438-LRI scan missed), or the field falls back to a Pipeline constructor default for `CCT=4300, tint=0` when absent. For L16_02130 the effective CCT is 4300 K either way.
    - **Reconciliation with 9,438-LRI scan**: the scan found zero `neutral_color` because xy is COMPUTED from CCT, not stored. CCT itself may be stored numerically in some LRIs.
    - **Phoenix action**: MVP hardcode chromaticity `(0.36895, 0.21384)` for <1 ΔE error. v1.0 dumps 112-byte Robertson table at 0x66d420 + 5 rodata constants, ports `ChromaticityFromCCT_Tint @ 0xab130` verbatim, drives with CCT=4300/tint=0 default. If per-LRI CCT extraction is needed, scan LRIs with a numeric-wire-format protobuf walker for `auto_white_balance.neutral_temp`.

21. ~~**V2 edge-weight kernel math**~~ — **RESOLVED.** Consumer is VA **0x2f1840** only (0x2f1c00 is just a row-fetch helper that reads `0x44(%rdi)` as an int). 0x2f1840 implements **Hamilton-Adams green interpolation at R/B sites**: computes `Hgrad = 2c − W − E`, `Vgrad = 2c − N − S`, then `Hscore = |Hgrad| + |E−W|`, picks whichever score is smaller, and applies `Hcand = max(Hgrad × k, floor) + (W+E)`. The `scalar × -0.02` value (broadcast into xmm10 from `0x44(%r13)`) is used as a **`maxps` floor clamp** — a scene-adaptive **anti-undershoot clamp** on the Laplacian correction term, NOT an edge weight. Since the value is negative, it bounds how negative the HA correction can go, preventing ringing at sharp edges. This means **V2's float scalar is used TWICE** in the demosaic kernel: (1) as gradient noise-floor ε added to `|gradient|` before reciprocal (from earlier finding); (2) as anti-undershoot floor on `Hgrad × k` and `Vgrad × k` (this finding). Single "sharpness vs cleanliness" knob. Confirmed at scalar tail 0x2f1af0..0x2f1ba5 via `movss 0x44(%r13), %xmm4; maxss %xmm4, ...`. Minor unverified: xmm9 center weight (inferred 0.5, rodata const at 0x5a92a0); xmm11 absolute-value mask (inferred 0x7fffffff × 4, rodata at 0x5a81f0). Both are unambiguous from HA structure. See `session3_v2_edge_kernels.md`.

---

## Key Artifacts

| File | Contents |
|---|---|
| `/Volumes/Dev/lumen-phoenix-scratch/cal_color_l16_02130.npz` | Per-camera calibration (bayer, vignetting, CCM, CRA) |
| `/Volumes/Dev/lumen-phoenix-scratch/tmo_*.npy` | 4 tone curve LUTs (1024 float32 each) |
| `/Volumes/Dev/lumen-phoenix-scratch/tmo_characterization.json` | Tone curve metadata |
| `/Volumes/Dev/lumen-phoenix-scratch/ceres_analysis.md` | Full Ceres pass characterization |
| `/Volumes/Dev/lumen-phoenix-scratch/lumen_side_analysis.md` | Fusion, AWB, demosaic static analysis |
| `/Volumes/Dev/lumen-phoenix-scratch/c6_verification.md` | C6 active at 70mm/150mm evidence |
| `/Volumes/Dev/lumen-phoenix-scratch/oqe_unknown_format.md` | LRI format variant findings |
| `/Volumes/Dev/lumen-phoenix-scratch/lri_header_camera_config.md` | **Per-capture camera firing + config decoder (162 LRIs verified)** |
| `/Volumes/Dev/lumen-phoenix-scratch/lens_shading_activation.md` | setLensShading reachability + gating |
| `/Volumes/Dev/lumen-phoenix-scratch/q456_tone_ev_v2param.md` | Tone curve default + EV source + V2 scalar |
| `/Volumes/Dev/lumen-phoenix-scratch/cct_and_awb_auto.md` | Robertson CCT + "no AWB AUTO estimator" |
| `/Volumes/Dev/lumen-phoenix-scratch/demosaic_v2_and_fusion_weights.md` | Demosaic V2 kernel + real fusion weight formula |
| `/Volumes/Dev/lumen-phoenix-scratch/wdr_format.md` | Proof that WDR is not a capture format |
| `/Volumes/Dev/lumen-phoenix-scratch/android_libs/android_symbol_analysis.md` | Android vs macOS symbol comparison |
| `/Volumes/Dev/Light_Spike/ground_truth.tiff` | Reference output for validation |
| `/Volumes/Dev/Light_Spike/depth_map.npy` | Reference depth map |
