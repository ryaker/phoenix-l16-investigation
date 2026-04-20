# Phoenix Spec Writer Prompt
**Paste this into your spec-writing agent (Gemini 3.1 Pro, Sonnet 4.6, Opus 4.6, etc.). Self-contained.**

---

## Your task

Write the complete **coding specification** for Phoenix — a clean-room reimplementation of Lumen's L16 LRI bridge renderer, combined with a SwiftUI photo editor. Your output is a set of markdown documents that an implementer (different person, weeks later) can use to build Phoenix without asking clarifying questions.

## Your inputs (everything you need is in this folder)

1. **`phoenix-pipeline-facts.md`** — canonical investigation document for the **rendering pipeline**. Every stage, algorithm, VA, and caveat. This is your source of truth for the image processing layer.
2. **`ui_spec/`** — 12 markdown files defining the **SwiftUI app**: screens, navigation, controls, design system, and the **Swift Pipeline API contract** (`ui_spec/10_pipeline_api_contract.md`) that your spec must satisfy.
3. **`lri_header_camera_config.md`** — LRI file format reference with standalone Python decoder. Cite this for input parsing.
4. **`tmo_characterization.json`** — tone curve metadata (names, midgray responses, pre-shaper formula). No LUT bytes — see Rule #0.

## Required reading order (stay within context budget)

You don't need to read every file. Start with these sections in this order:

1. **`phoenix-pipeline-facts.md`** — read the **Rule #0 / Clean-room** box at the top, the **Rev 5 / Rev 6 architecture box**, and the **Honest Approximations** section. Skim the stage sections on demand as you write each spec chapter. Skip the Open Items list unless you hit something ambiguous.
2. **`ui_spec/10_pipeline_api_contract.md`** — read the full file. This is the Swift protocol your pipeline must implement.
3. **`ui_spec/README.md`** + **`ui_spec/01_overview.md`** — for product context and design decisions (platform, non-destructive editing, .lrp sidecar format).
4. **`ui_spec/07_export.md`** — for export format requirements (JPEG/TIFF/DNG/HDR, color spaces, embedded depth).
5. **Everything else** — on-demand only.

## Rule #0 — Clean-room constraint (ABSOLUTE)

**Phoenix does NOT link against, `dlopen`, bundle bytes from, or otherwise depend on `libcp.dylib`, `Lumen.app`, or any other Light Inc. proprietary binary.**

All VAs in `phoenix-pipeline-facts.md` are **reverse-engineering references only**. They tell you where to read the reference algorithm in a disassembler, NOT which bytes to copy into Phoenix.

Every constant Phoenix needs comes from:
1. **Parsed from the input LRI at render time** (calibration blocks, AWB gains, LightHeader metadata)
2. **Published / CIE-standard values** (Wyszecki-Stiles Robertson tables, sRGB math)
3. **Reimplemented from a documented algorithm** in `phoenix-pipeline-facts.md`

**Things that MUST NOT be referenced as runtime sources in your spec:**
- Tone curve LUT bytes at `libcp:0x5e31b0/0x5e41b4/...` — these are RE references, not inputs
- Any pre-extracted `.npz` archive — `cal_color_l16_02130.npz` in the handoff is a REFERENCE SAMPLE, not a runtime input
- Any function at a libcp VA as a runtime call target

The phrase "port verbatim" must not appear in your spec. Use "reimplement from the algorithm described in [section X of phoenix-pipeline-facts.md]" instead.

## What the spec must contain

### Part 1 — Pipeline layer (the Phoenix render engine)

For each of these stages, write a dedicated section with: algorithm description in prose, pseudocode (not real code), references to the relevant section of `phoenix-pipeline-facts.md`, edge cases, and explicit approximation flags where Phoenix deviates from Lumen exact parity.

1. **LRI input parsing** — LELR block structure, LightHeader.field_12 per-capture fired cameras + encoder readings, LightHeader.field_4 zoom focal length, union-across-chunks = fired set. Cite `lri_header_camera_config.md` for protobuf paths. Handle all zoom levels (28mm/35mm/70mm/150mm) and all firmware variants (2018-normal 28/35mm, 2018-normal 70/150mm, 0.1.x transitional, BJPG). WDR is not a real format — do not add a WDR parser.
2. **Calibration block parser** — Phoenix parses Blocks 3/4/5/6 from every LRI to produce per-camera `black_level`, `white_level`, `vignetting_grid`, `cra_grid`, `ccm_matrices`, `R_fold`, `virtual_pos`, `encoder_nominals`, and geometric intrinsics. Some protobuf paths are documented in `phoenix-pipeline-facts.md` Calibration Fields section; black/white level and Block 3 paths are flagged as OPEN ITEM #26 — your spec must note this gap and direct the implementer to reverse whatever tool produced `cal_color_l16_02130.npz` (likely `spike_oqc_cal_extract.py`).
3. **Per-camera raw decode** — uint16 → float32 1:1 bit-cast (no normalization). Data enters in [0, 1023] range.
4. **Per-camera vignetting correction** — bilinear-interpolated 17×13 grid, multiply direction. Both pre-demosaic Bayer (<float,true>) AND post-demosaic RGBA (<vec4x32f,*>) per Session 3 finding.
5. **Per-camera CRA correction** — 4×4 Bayer channel mixing matrix, bilinear-interpolated from 13×17 grid.
6. **Per-camera demosaic** — Hamilton-Adams family edge-aware green interpolation, Vec3 gain-scaled epsilon for adaptive noise floor, writes float32 RGBA into shared canvas. ONE runtime-parameterized kernel handling all 4 Bayer-phase offsets (`tile_x mod 2`, `tile_y mod 2`).
7. **Cross-camera merge** — emergent behavior: each camera's demosaic writes into the shared canvas. Not a separate stage. Warp parameters come from R_fold + virtual_pos + per-camera distortion grid per camera.
8. **Linearize + color scale** — `(rgba − black_level[cam]) / (white_level[cam] − black_level[cam])` using per-camera values parsed at render time.
9. **AWB** — multiply by `1/stored_gain` where stored_gain comes from Block 8 f19.f15. Pre-compute reciprocals once per render.
10. **CCM** — interpolate between two factory matrices (illuminant A at ~2855K + D65 at ~6502K, from Block 6) using CCT-driven chromaticity. Default CCT = 4300K when `neutral_temp` not present in LRI. See Honest Approximations for MVP hardcoded value.
11. **Tone mapping** — apply equivalent of `light_v1` curve (see Honest Approximations for shipping strategy) with pre-shaper from `tmo_characterization.json` and `exp2f(EV)` where EV comes from `Settings.exposure` protobuf field.
12. **Depth output (optional)** — decode .lris Section 3 (magic `0x51E8E000`) as `depth_mm = 3460 + (116930−3460) × arr / 16383`. Shape (3120, 4160).

### Part 2 — Swift Pipeline API bindings

Match the protocols in `ui_spec/10_pipeline_api_contract.md` exactly:
- `LRILibraryProtocol` (metadata + embeddedPreview)
- `LRIRendererProtocol` (render + cancel + rerender + isCached, AsyncThrowingStream<RenderResult, Error>)
- `DepthProtocol` (depthAtPoint, computeQuickSelectMask, applyDepthEdit, detectFaces)
- `RefocusProtocol` (focusDistanceAtPoint, validateRefocusParams)
- `ExportProtocol` (export, cancelExport)
- `ToneParams`, `WhiteBalanceParams`, `CropParams`, `EditState`, `DepthEdit`, `RenderResult`, `RenderLevel`

Core types follow the Swift definitions in that file. Pixel output goes through `MTLTexture` (Metal). All operations are `async`.

### Part 3 — Processing layer bridge

Describe how the Swift Pipeline API bridges to the underlying processing layer (Rust or Python + Metal per `ui_spec/02_app_architecture.md`). This is where the Phoenix render engine from Part 1 plugs in. Define:
- Object lifetime (who owns `MTLTexture`s, who cancels background work)
- Thread model (all async, results delivered on main actor)
- Progress reporting via AsyncThrowingStream
- Memory management for 81.6 MP float32 canvases (~1.3 GB per render — cache policy)

### Part 4 — Non-destructive edit state + `.lrp` sidecar format

Define the `.lrp` (Lumen Phoenix) sidecar file format. Non-destructive: original LRI never modified. Sidecar stores full `EditState` (white balance, tone params, crop, depth edits, focus/aperture/bokeh, face matting flag). Format: prefer JSON for human-readable + versionable + mergeable. Must round-trip without loss.

### Part 5 — Validation strategy

How Phoenix's output is validated against Lumen's reference:
- `ground_truth.tiff` is a **Linear Raw DNG** (not a rendered TIFF) with embedded `ProfileToneCurve`. Spec describes unwrapping the DNG, applying the embedded tone curve, and comparing Phoenix's tone-mapped output against that.
- Pixel-level MAD tolerance: <5% mean absolute deviation is "passing" for MVP (demosaic + tone curve approximations prevent tighter parity).
- Functional validation: 100% canvas coverage, no seam artifacts, correct zoom level handling, AWB channel ratios within 1 ΔE of Lumen on neutral scenes.

### Part 6 — Honest Approximations section (REQUIRED — mirror from phoenix-pipeline-facts.md §Honest Approximations)

Every approximation must be called out explicitly. The spec must contain a top-level "Honest Approximations" section listing each of these with the same headings used in `phoenix-pipeline-facts.md`:

1. **Demosaic — Hamilton-Adams algorithm class, not byte parity.** VNG or AHD are acceptable substitutes with flagged deviation.
2. **Tone curve — shipped LUT vs. reimplemented formula.** Legal decision blocks shipping. Spec must describe both paths.
3. **CCT blend weight — hardcoded MVP vs. runtime-derived v1.0.** MVP hardcodes chromaticity `(0.36895, 0.21384)` for CCT ≈ 4300K with <1 ΔE error on neutral scenes.
4. **Linearize + color_scale — Halide-JIT, semantic equivalent only.** Not statically extractable, reimplemented from formula.
5. **Bundle adjustment — NOT reimplemented (out of scope).** Phoenix reads baked factory calibration from LRI. Only the per-point depth refinement Ceres pass is reimplemented via `scipy.optimize.least_squares(loss='cauchy')`.
6. **Cross-camera merge — inferred from closure-level accumulation.** Seam-level geometric parity depends on distortion grid interpolation matching Lumen's bicubic implementation.
7. **Phase B (Lumen's mono output) — intentionally SKIPPED.** Phoenix is color-only.
8. **HDR bracket fusion — NOT implemented.** No multi-exposure LRIs exist in corpus. Phoenix returns `PipelineError.unsupportedFormat` if encountered.

Each approximation entry must state: the deviation from Lumen, the typical magnitude (<1 ΔE, <5% pixels, etc.), and the mitigation or v1.0 upgrade path.

## Format conventions

- Every stage section has: **Algorithm** (prose), **Pseudocode** (not real code), **Sources** (citations to phoenix-pipeline-facts.md section), **Edge cases**, **Approximation flags** if applicable.
- Cite VAs as `libcp:0x34XXXX (reverse-engineering reference)` to make clear they are RE refs, not Phoenix runtime state.
- Use SI units and explicit ranges. "float32 in [0, 1]" is good; "normalized float" is not.
- Every `Phoenix action:` directive in `phoenix-pipeline-facts.md` must have a corresponding spec directive.

## Output structure

Write these files under `phoenix-spec-writing/spec/`:

```
spec/
├── 00_overview.md                    # Purpose, scope, product context
├── 01_clean_room_rule.md             # Rule #0 restated
├── 02_pipeline_architecture.md       # 12-stage render pipeline (Part 1 above)
├── 03_swift_api.md                   # Swift protocols matching ui_spec/10
├── 04_bridge_layer.md                # Swift → Rust/Python/Metal bridge
├── 05_edit_state_sidecar.md          # .lrp format + non-destructive edit model
├── 06_validation.md                  # Ground-truth comparison strategy
├── 07_honest_approximations.md       # REQUIRED — all 8 approximations flagged
├── 08_stage_details/
│   ├── 01_lri_parser.md
│   ├── 02_calibration_parser.md
│   ├── 03_raw_decode.md
│   ├── 04_vignetting.md
│   ├── 05_cra.md
│   ├── 06_demosaic.md
│   ├── 07_merge.md
│   ├── 08_linearize.md
│   ├── 09_awb.md
│   ├── 10_ccm.md
│   ├── 11_tone_mapping.md
│   └── 12_depth.md
└── README.md                         # Index + how to read this spec
```

## Discipline (absolute)

**The spec describes what Lumen does, not what any Phoenix implementation attempt has done.** Do NOT reference:
- MAD values, coverage percentages, per-camera spike results
- "We observed X in the test implementation"
- Any hypothesis derived from running experimental code

Every claim must be traceable to `phoenix-pipeline-facts.md` which in turn cites a VA / file offset / LLDB trace / calibration extract from a real LRI. If you can't cite a claim back, delete it.

## Done criteria

- Every pipeline stage has a dedicated section in `08_stage_details/`
- Part 6 Honest Approximations section is complete with all 8 entries
- Every Swift protocol in `ui_spec/10_pipeline_api_contract.md` has a matching spec directive in `03_swift_api.md`
- Every `Phoenix action:` line in `phoenix-pipeline-facts.md` has a corresponding directive in the spec
- All 8 honest-approximation flags are in place
- Zero mention of any spike, test harness, MAD value, or numerical parity measurement
- No "port verbatim" language
- No cited `.npz` or libcp VA as a runtime source
- A reader unfamiliar with Lumen can produce working Swift + Rust/Python code for ≥1 pipeline stage per day without asking clarifying questions

---

## If your context budget is tight

`phoenix-pipeline-facts.md` is ~70 KB. `ui_spec/` total is ~120 KB. If you can't hold both + your output, **read phoenix-pipeline-facts.md's Rule #0 + Rev 5 architecture box + Honest Approximations section first** (together < 15 KB), write the spec framework + clean-room section + approximations section + honest approximations using just that, then load stage sections on demand as you write `08_stage_details/NN_*.md` files one at a time. You do NOT need to hold the entire source document in context while writing.
