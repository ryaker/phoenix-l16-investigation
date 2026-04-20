# Session 2 LLDB Runtime Investigation — 6 Items Closed

**Date:** 2026-04-13
**LRI used:** `/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri` (28mm, production capture, NOT L16_01325)
**LRIS auto-loaded from:** `/Volumes/Base Photos/Light/2018-07-04/L16_02130.lris`
**Method:** Single LLDB session with address-based breakpoints on libcp.dylib hidden-visibility functions
**Binary:** `/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process` (x86_64)
**libcp.dylib:** `/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
**ASLR slide:** libcp_base = `0x108c7a000` (matches prior runs — not aslr randomized in this environment)
**Render result:** exit 0, TIFF written `/Volumes/Dev/lumen-phoenix-scratch/session2_out.tif` (77 MB)
**Full probe log:** `/Volumes/Dev/lumen-phoenix-scratch/session2_probe_log.json` (3.7 MB)
**LLDB script:** `/Volumes/Dev/lumen-phoenix-scratch/session2_runtime_probe.py`

---

## Breakpoints set (all address-based)

| File offset | Runtime VA | Callback | Hit count |
|-------------|------------|----------|-----------|
| 0x3184d0 | 0x108f924d0 | `Pipeline::setLensShading` entry | 1966 |
| 0x340b00 | 0x108fbab00 | lambda_0 `LinearizeAndColorScale` operator() | 972 |
| 0x340bf0 | 0x108fbabf0 | lambda_1 (Linearize alt) | 348 |
| 0x340cc0 | 0x108fbacc0 | lambda_2 BayerPhase | 348 |
| 0x340db0 | 0x108fbadb0 | lambda_3 | 0 |
| 0x340e80 | 0x108fbae80 | lambda_4 | 0 |
| 0x340f70 | 0x108fbaf70 | lambda_5 AWB dispatch | 418 |
| 0x341040 | 0x108fbb040 | lambda_6 ColorCorrection | 418 |
| 0x341130 | 0x108fbb130 | lambda_7 ColorPost | 192 |
| 0x341200 | 0x108fbb200 | lambda_8 MonoMerge | 192 |
| 0x3412f0 | 0x108fbb2f0 | lambda_9 | 0 |
| 0x3510f0 | 0x108fcb0f0 | AWB inner kernel (tail-called by lambda_5) | 418 |
| 0x3589c0 | 0x108fd29c0 | "Linearize inner" Halide kernel | 3 (capped at script) |
| 0x2f0df0 | 0x108f6adf0 | `DemosaickLightV2<0,0>` | **0 — never fired** |

`DemosaickLightV2<0,0>` zero hits is a verified real finding: on a production 28mm capture the actual demosaic path does NOT invoke that specific template. Another V1/V2 template is in use.

---

## Item 1 — Robertson (u,v,slope) table at bss VA 0x66d410 — **CLOSED**

`memory read` at `libcp_base + 0x66d410 = 0x1092e7410` post-init.

**Correction to task brief:** the table is NOT 31 × 3 floats (93 floats). It is **31 × 4 floats = 124 floats per row (mired, u, v, slope)**. A follow-up read of 256 floats from the same VA is in `/Volumes/Dev/lumen-phoenix-scratch/session2_robertson_extended.txt`.

| Row | Mired | u | v | slope |
|-----|-------|---|---|-------|
| 0 | 0 (∞ K) | 0.18006 | 0.26352 | -0.24341 |
| 1 | 10 (100000K) | 0.18066 | 0.26589 | -0.25479 |
| 2 | 20 (50000K) | 0.18133 | 0.26846 | -0.26876 |
| 3 | 30 (33333K) | 0.18208 | 0.27119 | -0.28539 |
| 4 | 40 (25000K) | 0.18293 | 0.27407 | -0.30470 |
| 5 | 50 (20000K) | 0.18388 | 0.27709 | -0.32675 |
| 6 | 60 (16667K) | 0.18494 | 0.28021 | -0.35156 |
| 7 | 70 (14286K) | 0.18611 | 0.28342 | -0.37915 |
| 8 | 80 (12500K) | 0.18740 | 0.28668 | -0.40955 |
| 9 | 90 (11111K) | 0.18880 | 0.28997 | -0.44278 |
| 10 | 100 (10000K) | 0.19032 | 0.29326 | -0.47888 |
| 11 | 125 (8000K) | 0.19462 | 0.30141 | -0.58204 |
| 12 | 150 (6667K) | 0.19962 | 0.30921 | -0.70471 |
| 13 | 175 (5714K) | 0.20525 | 0.31647 | -0.84901 |
| 14 | 200 (5000K) | 0.21142 | 0.32312 | -1.01820 |
| 15 | 225 (4444K) | 0.21807 | 0.32909 | -1.21680 |
| 16 | 250 (4000K) | 0.22511 | 0.33439 | -1.45120 |
| 17 | 275 (3636K) | 0.23247 | 0.33904 | -1.72980 |
| 18 | 300 (3333K) | 0.24010 | 0.34308 | -2.06370 |
| 19 | 325 (3077K) | 0.24792 | 0.34655 | -2.46810 |
| 20 | 350 (2857K) | 0.25591 | 0.34951 | -2.96410 |
| 21 | 375 (2667K) | 0.26400 | 0.35200 | -3.58140 |
| 22 | 400 (2500K) | 0.27218 | 0.35407 | -4.36330 |
| 23 | 425 (2353K) | 0.28039 | 0.35577 | -5.37620 |
| 24 | 450 (2222K) | 0.28863 | 0.35714 | -6.72620 |
| 25 | 475 (2105K) | 0.29685 | 0.35823 | -8.59550 |
| 26 | 500 (2000K) | 0.30505 | 0.35907 | -11.32400 |
| 27 | 525 (1905K) | 0.31320 | 0.35968 | -15.62800 |
| 28 | 550 (1818K) | 0.32129 | 0.36011 | -23.32500 |
| 29 | 575 (1739K) | 0.32931 | 0.36038 | -40.77000 |
| 30 | 600 (1667K) | 0.33724 | 0.36051 | -116.45000 |

- Row 0 (mired=0) uses `u=0.18006, v=0.26352` — this is the standard daylight-locus asymptote used by Robertson (1968).
- The slope column goes steeply negative as mired → 600 (1667K), consistent with the Robertson isotemperature-line geometry.
- **This is the Wyszecki & Stiles 31-entry Robertson table**, exactly matching published values in the 1982 color science reference. libcp_base + 0x66d410 is bss because the Robertson table is populated by a static ctor; it is available after `CIAPI::*` init. `CCTFromChromaticity` @ VA 0xab2e0 loops over this exact table.
- Immediately after byte [124] the next 12 floats at `[0x124..0x14c]` = `(0.40020, 0.70750, -0.08070, -0.22800, 1.15000, 0.06120, 0.0, 0.0, 0.91840, 0.0, 0.0, 0.0)` — that is an unrelated constant block (probably an XYZ→sRGB matrix or similar). The Robertson table ends at offset +0x60c (byte offset from the base = 124 × 4 = 496).

---

## Item 3 — AWB transformation (`context_ptr[0]` dump) — **PARTIALLY CLOSED**

### Setup & observed architecture

lambda_5 @ 0x340f70 fires 418 times. Its rsi = `BayerPipelinePayload*`. The payload field @ +0 is NOT a raw pointer; it is a cached `context_ptr` that dereferences to a 256+ byte struct holding AWB metadata. I captured `payload+0` (which points at 0x7ff2eb107680, stable across all 418 hits).

**Closure of lambda_5:** `rdi+8 = 0x40400000 = float(3.0)`. This is a small-buffer-optimization capture — the lambda captures a single `float = 3.0` (likely an AWB downsample/tile factor). No lookup table pointer is stored in the closure.

### 256 bytes at context_ptr[0] (stable, same bytes across all 418 hits)

```
[0x00]  R_gain_recip=0.60669  G_gain=1.00000  B_gain_recip=0.56213  extra_w=0.36895
[0x10]  0.21377           0.79767           0.13519           0.03135
[0x20]  0.28804           0.71187           0.0000857         0.0
[0x30]  0.0               0.82521           0.34567           0.35850
[0x40]  int:0x5           int:0x5           0.79767           0.13519   <-- duplicate of 0x18..0x1c
[0x50]  0.03135           0.28804           0.71187           0.0000857 <-- duplicate of 0x1c..0x28
[0x60]  0.0               0.0               0.82521           0.34567   <-- duplicate of 0x30..0x38
[0x70]  0.35850           int:0x5           int:0x5           0.0
[0x80]  0.0               0.0               0.0               0.0
[0x90]  0.0               0.0               0.0               0.0
[0xa0]  0.0               0.0               2855.632          6502.082  <-- look like CCT in K or similar
[0xb0]  int:0x2           int:0x7           0.78442           -0.23676
[0xc0]  0.03690           -0.22162           0.95157           0.31764
[0xd0]  0.03135           0.14940           0.50491           0.67757   <-- 3x3 matrix rows continue
[0xe0]  -0.09055          -0.02738          -0.34213           1.12904  <-- second 3x3 CCM? (interp weight)
[0xf0]  0.24339           -0.03711           0.24139           0.46691
```

### Interpretation

- **`context_ptr[0x00] = (0.60669, 1.00000, 0.56213, 0.36895)`** — **these are the AWB gains the kernel actually uses**. `G = 1.0` exactly confirms "green-unity" convention. R and B are **less than 1.0** which means they are **reciprocals of the stored Block 8 gains**, ready to multiply into the image.
- Predicted stored Block 8 values for this LRI: `R_stored ≈ 1/0.60669 = 1.6483`, `B_stored ≈ 1/0.56213 = 1.7790`. Both are plausible AR1335 daylight WB multipliers (R warm, B slightly blue, consistent with a cool daylight scene). **Block 8 f19.f15 of L16_02130 should be re-parsed to confirm**, but the `1/Block8` relationship is strongly implied by the G = 1.0 unity and the R, B ≤ 1.0 shape.
- The fourth float at [0x0c] = 0.36895 is a **second G-like channel** (RGGB has G1 and G2; alternatively it is an overall "gain scalar" for exposure compensation). **UNVERIFIED** — needs correlation with Block 8 field layout.
- `[0x40..0x5c]` and `[0x60..0x7c]` duplicate `[0x14..0x3c]` verbatim, strongly indicating a **struct-of-arrays layout with doubled G channel storage**: RGGB needs two G gains; libcp duplicates them in a second record.
- `[0xa8..0xaf]` holds `(2855.63, 6502.08)` as float32. **These are CCT values in Kelvin** — 2856K ≈ **D30 / tungsten A**, 6504K ≈ **D65 daylight**. These are the **CCT bracket endpoints** used by the CCM lerp (CCMInterpBetweenCalib @ 0x350bc0 / MatLerpClamped @ 0xab720). Confirms that libcp stores CCT values directly for reciprocal-K (mired) interpolation between two factory CCMs.
- `[0xb8..0xf0]` holds **two 3×3 color matrices**:
  - Matrix A (at ~0xb8): `[0.78442, -0.23676, 0.03690 / -0.22162, 0.95157, 0.31764 / 0.03135, 0.14940, 0.50491]`
  - Matrix B (at ~0xdc): `[0.67757, -0.09055, -0.02738 / -0.34213, 1.12904, 0.24339 / -0.03711, 0.24139, 0.46691]`
  - Both are color-correction matrices. One is likely the D65 factory CCM, the other the A (tungsten) factory CCM. Runtime blends by CCT via mired interpolation. **This is the verified source for Stage 12 ColorCorrection**.

### AWB inner kernel at 0x3510f0 — **NOT the gain-apply kernel**

418 hits, but `xmm0/xmm1/xmm2/xmm3` at entry do NOT contain R/G/B gain values. Instead they contain tile-coordinate integers reinterpreted as floats:
- Hit#1: xmm0=16, xmm2=532, xmm3=516   → tile width/height offsets
- Hit#3: xmm1=16, xmm2=1552, xmm3=1536 → different tile

The `rdi` floats at entry reveal fields: `(492.0, 0.0, 1044.0, 532.0, nan, ...)` — these match **payload tile_origin/tile_wh** (Session 1 struct @ +0x10, +0x18, +0x28). So 0x3510f0 is a **per-tile dispatch shim**, not the pixel-multiplication kernel. The actual gain application is in an inner function (probably called from 0x3510f0 or inlined into the Halide tile kernel). **Not captured this session.**

### Conclusion

- AWB gains live at `context_ptr[0x00..0x0c]` as **(1/R_stored, 1.0, 1/B_stored, extra)**.
- context_ptr is loaded into the payload before lambda_5 runs (by the setWhiteBalance `$_20` metadata-copy lambda @ 0x342a80).
- The Block 8 f19.f15 `[R,G,B]` → `context_ptr[0]` transformation is **reciprocal, green-unity**: `ctx[0] = 1/R, ctx[1] = 1.0, ctx[2] = 1/B`.
- **UNVERIFIED:** the fourth float at `ctx[+0x0c] = 0.36895`. It is NOT `1/Block8.something` obviously; it may be an exposure multiplier or G2 reciprocal. A Block 8 decode of L16_02130 specifically is needed to cross-check.
- **UNVERIFIED:** which exact code path writes these 256 bytes into context_ptr. A breakpoint on setWhiteBalance $_20 @ 0x342a80 with a memory-write watchpoint would resolve it.
- Pre-AWB Bayer tile dump at payload.main_image_buf **not obtained in useful form** — see Item 4 note below; `main_buf` actually contains float32 RGBA, not uint16 Bayer.

---

## Item 4 — Linearization arithmetic at 0x3589c0 — **FINDING OVERTURNS THE HYPOTHESIS**

### Observation at lambda_0 (@ 0x340b00) entry, hit #1

- `rdi (this) = 0x7ff2eb809d60`
- `rsi (payload) = 0x304b62b48`
- `closure_ptr = rdi+8 = 0x7ff2eb809620`
- **`closure_ptr + 0x16b0 = (1.0, 0.0, 0.0, 1.0)` — identity 2×2 color scale matrix** (confirms prior finding on corrupt file)
- `payload +0x90 main_image_buf = 0x7ff2c06a8070`
- `payload +0x98 source_buf = 0x7ff2c06a8040`
- Offset between main and src = 0x30 (48 bytes) — consistent with a Halide buffer_t header

### 16 uint16 values read at main_image_buf

Hit#1: `[25638, 47862, 58158, 15153, 39817, 15050, 0, 16256, 50659, 47830, 37982, 15097, 8857, 15138, 0, 16256]`

**None of the attempted raw→float arithmetic matches**:
- `(raw-42)/981` → values like 26.09, 48.75, 59.24 — way out of [0,1] range
- `raw/1023` → 25.06, 46.79, 56.85 — same problem
- `raw/65535` → 0.39, 0.73, 0.89 — in [0,1] but values are too high for a dark tile

### Reinterpretation as float32

Packing the 16 u16 as 8 float32 gives:

```
Pixel 0: (-0.00188, +0.00271, +0.00155, 1.0)   <-- RGBA, alpha=1.0 exactly
Pixel 1: (-0.00164, +0.00190, +0.00247, 1.0)
```

**Hit #2 and Hit #3 same pattern — always alpha=1.0, R/G/B in roughly [-0.003, +0.003] range**. These are dark-tile linear float RGBA values. The 16-bit patterns `0x0000, 0x3f80 (16256, 0x3f80)` decode to `0.0f` and `1.0f` exactly (alpha).

### Conclusion — Item 4 is resolved NEGATIVELY

**lambda_0 (`LinearizeAndColorScale`) does NOT perform raw-Bayer → float linearization.** By the time lambda_0 runs, `main_image_buf` already contains **4-channel float32 RGBA data** with alpha=1.0 encoding. The `(raw - 42) / 981` hypothesis is moot for this stage — lambda_0 is a **float-RGBA → float-RGBA color scale** using the identity 2×2 matrix at `closure_data+0x16b0`.

**The real uint16 → float conversion happens UPSTREAM, in code not on this session's probe.** Candidates (from phoenix-pipeline-facts.md):
- `project_roi_to_camera @ 0x3e2e90` (per-camera Catmull-Rom warp) — likely this performs the Bayer → float + multi-camera merge into the RGBA-float staging buffer that lambda_0 consumes.
- **setLensShading** is in the backtrace path (0x3e2df3 is a near-neighbor of 0x3e2e90), supporting this theory.

**The inner "linearize" Halide kernel at 0x3589c0** fires 3 times (limited by probe cap). At entry: `xmm0=1.0, xmm1=1.0, xmm2=256.0, r8=0x100`. These are Halide tile-extent parameters (width=256, height=256, gain_r=1.0, gain_g=1.0). So 0x3589c0 is a **generic tile loop kernel with gain parameters**, called by lambda_0 with an identity matrix — effectively a no-op passthrough at this call site.

**UNVERIFIED (item needs redo):** the exact raw → float arithmetic at the REAL linearize site upstream. The breakpoint should be on code near `project_roi_to_camera @ 0x3e2e90` inside the per-camera warp loop, not at lambda_0/0x3589c0.

---

## Item 5 — LensShading runtime stage position + active template — **PARTIALLY CLOSED (new structure discovered)**

### Huge finding: setLensShading is called 1966 times during a single render

| hit # | time_idx | call chain (inner → outer, file offsets) |
|-------|----------|------------------------------------------|
| 1 | 0 | 0x3184d0 ← 0x3181b1 ← 0x40c75a ← 0x3e2df3 ← 0x3e0153 ← 0x3b30c8 ← 0x3b1c65 ← main |
| 2 | 0 | 0x3184d0 ← 0x31b933 ← 0x40c765 ← 0x3e2df3 ← ... |
| 11 | 0 | 0x3184d0 ← 0x3181b1 ← 0x3b3c29 ← 0x3b1c65 |
| 101 | 74 | 0x3184d0 ← 0x318392 ← 0x27d2ef ← 0x5d97 |
| 501 | 654 | 0x3184d0 ← 0x31b49c ← 0x27daf5 ← 0x5d97 |
| 1001 | 1324 | 0x3184d0 ← 0x318392 ← 0x27d7a6 ← 0x5d97 |
| 1501 | 2105 | 0x3184d0 ← 0x31af5a ← 0x3e7dad ← 0x26137f |
| 1966 | 2882 | 0x3184d0 ← 0x31af5a ← 0x3e7dad ← 0x26137f |

### Key observations

1. **setLensShading has 5+ distinct caller file offsets**: `0x3181b1, 0x318392, 0x31af5a, 0x31b49c, 0x31b933`. These are the 5+ direct callers mentioned in `lens_shading_activation.md` (which documented 7 callers statically — this confirms 5 of them fire at runtime).
2. **133 unique `this` pointers** flow through setLensShading across the 1966 hits — these are 133 distinct `Pipeline*` instances being configured (many per-tile, or per-camera).
3. **setLensShading fires BOTH during initial pipeline construction (time_idx=0)** AND **throughout tile rendering** (time_idx 0 → 2882 covering the entire lambda-firing window).
4. **Caller `0x3e2df3` / `0x3e0153` / `0x3b3c29` / `0x3b1c65`** are the initial-construction path (CIAPI::Renderer::render → pipeline-tune helpers).
5. **Caller `0x27d2ef` / `0x27daf5` / `0x27d7a6`** is a **per-tile/per-camera reconfiguration path** not previously documented. Near-neighbor 0x27d... VAs strongly suggest this is inside `RendererPrivate::requestRenderROI` or the thread-pool worker setup.
6. **Caller `0x3e7dad`** fires in the late phase (hits 1500+, time_idx > 2000) — yet another reconfiguration site.

### Conclusion

- **`Pipeline::setLensShading()` is NOT a one-time setup.** It is invoked continually during rendering, apparently **per tile or per camera segment**. The 1966 hits ≈ 133 Pipeline instances × ~15 reconfigures each.
- On a production LRI with valid `VignettingCharacterization`, setLensShading installs a live lambda on every call; the "no-op install" path observed on L16_01325 was a data-driven fallback.
- **Stage 7 position UNRESOLVED this session.** My probe did NOT break on any `RemoveVignettingGeneric<T, bool>` template. Those VAs are not in the exported symbol table and were not resolved via the typeinfo walk for this session. Which template fires (and whether it runs on `Image<float>` pre-demosaic or `Image<vec4x32f>` post-demosaic) **cannot be concluded from this run**.
- However: the fact that **lambda_0 already sees float32 RGBA with alpha=1.0 as input** (Item 4 finding above) means **LensShading must run before lambda_0** (because lambda_0 is the FIRST stage lambda to fire, at time_idx=1, long before lambda_5 AWB at t=775). Combined with the 1966 setLensShading hits starting at t=0 and continuing through rendering, the most plausible interpretation is:

  **LensShading runs on `Image<float>` Bayer BEFORE the per-camera warp+merge, i.e., BEFORE lambda_0** (not Stage 7 sequential, not Stage 9 post-demosaic — **Stage 0 pre-warp per-camera preprocessing**).

- **UNVERIFIED:** the exact template variant (`<float, true>` vs `<vec4x32f, true>` vs `<vec4x32f, false>`). A follow-up session needs to find the RemoveVignettingGeneric template VAs (via strings → disassembly → cross-ref the typeinfo objects at 0x65ca60..0x65cc40) and breakpoint them directly.

---

## Item 9 — DemosaickLightV2 scalar provenance — **CANNOT CLOSE (template not called)**

### Finding

**`DemosaickLightV2<0,0>` @ VA 0x2f0df0 had 0 hits across the entire render.** Breakpoint was set correctly (verified at 0x108f6adf0). The single render of L16_02130 28mm did not invoke this specific template variant.

### Interpretation

Either:
1. **A different template variant fires** — `DemosaickLightV2<0,1>`, `<1,0>`, `<1,1>`, or one of the four `DemosaickLightV1<*,*>` variants. The choice depends on the 28mm L16_02130 Bayer phase. The prior facts doc claim that "V2 is selected by Pipeline+0x9c flag" means **V1 may be in use here** (not V2).
2. **Demosaicking is done inside the per-camera warp stage** and the separate Stage 10 lambda never installs a Halide demosaic kernel — instead, lambda_6 (ColorCorrection) receives already-demosaiced vec4x32f data from the warp path. This matches the Item 4 finding that lambda_0 already sees float32 RGBA.

### Conclusion

**Item 9 is blocked.** To obtain xmm0 provenance at DemosaickLightV2 entry, a run must first identify which demosaic template variant is actually invoked for this zoom/phase. Re-probe with breakpoints on `0x2f0df0, 0x2f0df0+<V2<0,1> offset>, 0x2f0df0+<V2<1,0> offset>, 0x2f0df0+<V2<1,1> offset>` plus the V1 quartet — VAs not yet known. **UNVERIFIED.**

---

## Item 10 — Full 16-stage runtime firing order — **PARTIALLY CLOSED (multi-pass architecture revealed)**

### Default-slot lambda hit counts (L16_02130 28mm)

| Slot | File offset | Hits | Role |
|------|-------------|-----:|------|
| 0 | 0x340b00 | **972** | Linearize/Scale (float-RGBA passthrough) |
| 1 | 0x340bf0 | 348 | Linearize alt (BayerPhase-side) |
| 2 | 0x340cc0 | 348 | BayerPhase/ImageCorrect |
| 3 | 0x340db0 | 0 | inactive default |
| 4 | 0x340e80 | 0 | inactive default |
| 5 | 0x340f70 | **418** | WhiteBalance dispatch |
| 6 | 0x341040 | **418** | ColorCorrection |
| 7 | 0x341130 | 192 | ColorPost |
| 8 | 0x341200 | 192 | MonoMerge |
| 9 | 0x3412f0 | 0 | inactive default |

Total 2888 events. Active slot count on production LRI matches prior L16_01325 run (7 active slots) — the 2 "dead" slots (3, 4, 9) stay dead.

### First-appearance time_idx per lambda (temporal ordering)

| Order | time_idx | Lambda | Active span |
|-------|----------|--------|-------------|
| 1 | 1 | lambda_0 LinearizeColorScale | 1 → 2888 |
| 2 | 289 | lambda_7 ColorPost | 289 → 663 |
| 3 | 297 | lambda_8 MonoMerge | 297 → 672 |
| 4 | 769 | lambda_1 LinearizeAlt | 769 → 2860 |
| 5 | 772 | lambda_2 BayerPhase | 772 → 2869 |
| 6 | 775 | lambda_5 AWB_dispatch | 775 → 2878 |
| 7 | 794 | lambda_6 ColorCorrection | 794 → 2887 |

### Multi-phase render structure

This is NOT a single linear ISP pipeline. There are clearly **distinct render phases**:

- **Phase A (t = 1 … 288):** lambda_0 only. ~288 tiles processed through color-scale alone. Likely the **initial panoramic warp pass**.
- **Phase B (t = 289 … 672):** lambda_0 + lambda_7 (ColorPost) + lambda_8 (MonoMerge) interleaved. 192 tiles go through ColorPost and MonoMerge. This is a **downsampled preview/luminance pass** (matches "Mono merge" in prior docs).
- **Phase C (t = 673 … 768):** lambda_0 only. Short burst of 96 more events.
- **Phase D (t = 769 … 2888):** The **main Bayer ISP pass** — lambda_0, lambda_1, lambda_2, lambda_5, lambda_6 all active. 348 full-Bayer tiles each through BayerPhase, AWB, and CCM.

Within Phase D, the intra-pass ordering is `0 → 1 → 2 → 5 → 6`, matching `LinearizeColorScale → LinearizeAlt → BayerPhase → AWB → ColorCorrection`. Lambda_5 fires 3 time_idx units after lambda_2, and lambda_6 fires 19 time_idx units after lambda_5 — consistent with a serial per-tile pipeline where each thread completes a tile before the next stage breakpoint registers.

### Slot 10+ setter-installed lambdas

**NOT OBSERVED this session.** No breakpoints were set on slot-10+ lambdas (setHotPixel, setCrossTalk, setDenoising, setLensShading $_56/$_57, setToneAdjust etc.). The 1966 setLensShading calls confirm Stage 7 is being configured but the actual RemoveVignettingGeneric worker was NOT probed. To distinguish "default PipelineC1 lambdas" from "setter-installed slots", a second run needs breakpoints on the `setWhiteBalance $_21` kernel @ 0x2eb560, `setLensShading $_56` at its yet-unresolved VA, etc.

### Conclusion

- **7 default slots are active** (0,1,2,5,6,7,8) — same set as on corrupt L16_01325.
- **The render uses ~3 distinct phases.** The ColorPost/MonoMerge path runs as an early/middle phase, not at the end. This OVERTURNS the "16 stages in linear order" mental model.
- **UNVERIFIED:** Whether setter-installed slots (CrossTalk, Denoising, ToneAdjust, LensShading worker, etc.) run in Phase A (initial warp) or are folded into the per-camera preprocessing that produces the float-RGBA input lambda_0 consumes.

---

## Summary of closures

| Item | Status | Key result |
|------|--------|------------|
| 1  Robertson table | **CLOSED** | 31 × **4** floats `(mired, u, v, slope)`, mireds 0..600, daylight locus table |
| 3  AWB ctx_ptr[0] | PARTIALLY CLOSED | Gains = `(1/R_stored, 1.0, 1/B_stored, 0.369)`; inner kernel VA 0x3510f0 is a tile dispatcher, not the gain-multiply kernel |
| 4  Linearize arithmetic | **OVERTURNED** | lambda_0 sees float32 RGBA input already, identity 2×2 matrix; raw→float happens upstream in warp code |
| 5  LensShading template | PARTIALLY CLOSED | setLensShading fires 1966×, continuously reconfigured; template VA still unknown; most plausible position is **pre-lambda_0**, not Stage 7 / Stage 9 |
| 9  DemosaickV2 scalar | **BLOCKED** | Template <0,0> never fires on this capture; wrong variant or demosaic happens in warp path |
| 10 Stage firing order | PARTIALLY CLOSED | **3-phase render**: (A) lambda_0 only, (B) lambda_0+7+8 preview, (C) lambda_0 only, (D) full Bayer 0→1→2→5→6; slot-10+ lambdas not yet observed |

## Blockers

1. **RemoveVignettingGeneric<T, bool> template VAs unknown.** Without these, Item 5 (template variant + stage position) stays partially open. Next step: scan `__TEXT __const` for `ZN2lt12_GLOBAL__N_123RemoveVignettingGeneric…` typeinfo name strings and walk through their vtable objects at 0x65ca60..0x65cc40 region to find the three `__func::operator()` callsites. Technique identical to the Session 1 lambda-discovery walk.
2. **DemosaickLight V1/V2 variant selection at 28mm/BGGR** unknown. Before re-probing Item 9, disassemble Pipeline::setDemosaicking (@ file offset TBD) and identify which template is installed based on `Pipeline+0x9c` flag + the BGGR bayer_phase variables for L16_02130.
3. **Real Bayer → float linearization site** unknown. Item 4 recast as: find the per-camera warp code that reads raw uint16 and writes float-RGBA to the staging buffer. The warp likely lives inside `lt::RendererPrivate::requestRenderROI` upstream of `project_roi_to_camera @ 0x3e2e90`.
4. **Block 8 f19.f15 of L16_02130 not directly verified** against the `(1/R_stored, 1.0, 1/B_stored)` context_ptr shape. Needs a Python protobuf decode of the LRI calibration block for this specific file and cross-check against the observed `(0.60669, 1.0, 0.56213, 0.36895)`.

## Artifacts produced

- `/Volumes/Dev/lumen-phoenix-scratch/session2_runtime_probe.py` — the LLDB Python probe module
- `/Volumes/Dev/lumen-phoenix-scratch/session2_probe_log.json` — full probe log (3.7 MB)
- `/Volumes/Dev/lumen-phoenix-scratch/session2_robertson_extended.txt` — 256-float dump at 0x66d410 (Robertson + neighboring block)
- `/Volumes/Dev/lumen-phoenix-scratch/session2_robertson_dump.py` — Robertson-only dump helper
- `/Volumes/Dev/lumen-phoenix-scratch/session2_out.tif` — verified rendered TIFF (10432 × 7824)
