# Lens Shading Activation — Binary Analysis

**Date**: 2026-04-13
**Question**: Does the Lumen bridge / production render path call `Pipeline::setLensShading()`?
**Answer**: **YES — CONDITIONAL on LRIS vignetting data presence.**

---

## TL;DR

- `Pipeline::setLensShading()` lives at libcp.dylib **VA 0x3184d0** (hidden visibility — no symbol).
- It is reachable from **EVERY exported CIAPI entry point** at call depth 3 (or 6 for ApplyTuning).
- Both `CIAPI::Renderer` (full quality, used by Lumen.app GUI bridge) AND `CIAPI::DirectRenderer` (fast path, --direct-renderer in lri_process) reach it.
- The Stage 7 worker (`RemoveVignettingGeneric`) is wired in by setLensShading but only fires when `VignettingCharacterization` calibration data is present in the LRIS module record. Bad/missing data triggers the error path "Bad LRI: Vignetting data not found for at module" and installs a no-op lambda.
- The Lumen.app **main binary** (`Contents/MacOS/Lumen`) contains **zero** strings or symbols referencing `setLensShading`, `LensShading`, or `lens_shading`. It only uses the public `CIAPI::*` API. All ISP wiring lives in libcp.dylib, which is shared by both Lumen.app and lri_process.

---

## Phoenix Action

**Implement Stage 7 vignetting correction, gated on LRIS calibration presence.**

- If LRIS module record contains a valid `VignettingCharacterization` (with `VignettingModel` matching the IR correction DB width/height), apply `RemoveVignettingGeneric` per stage 7.
- If absent or invalid, skip Stage 7 (no-op) — this matches Lumen behavior on corrupt/incomplete LRIs and explains the 0-hit probe result.
- The two active template instantiations are `<float, true>` and `<vec4x32f, true>` / `<vec4x32f, false>`. The `<float, false>` variant was dead-stripped by the linker (never referenced).
- Read config keys `lens_shading.type` and `lens_shading.multiplier` from the per-frame parameter blob.

---

## Evidence

### 1. setLensShading function VA discovery

setLensShading() is the only function in libcp.dylib that constructs std::function objects whose typeinfo NAME strings encode `ZN2lt8Internal8Pipeline14setLensShadingENS0_12PipelineBase11LensShadingEE4$_56` and `$_57`.

Typeinfo NAME strings (in __TEXT,__const at 0x5a74a0..0x62eb29):
```
0x5f80b0  NSt3__110__function6__funcIZN2lt...14setLensShading...$_56...BayerPipelinePayload...
0x5f8150  ZN2lt8Internal8Pipeline14setLensShadingENS0_12PipelineBase11LensShadingEE4$_56
0x5f81a0  ...$_56...BayerFloatPipelinePayload...
0x5f8250  ...$_56...ColorPipelinePayload...
0x5f82f0  ...$_57...BayerPipelinePayload...
0x5f8390  ZN2lt8Internal8Pipeline14setLensShadingENS0_12PipelineBase11LensShadingEE4$_57
0x5f83e0  ...$_57...MonoPipelinePayload...
```

Typeinfo OBJECTS (in __DATA,__const at 0x65ca60..0x65cc40) are referenced by 31 LEA instructions in __text. Those LEAs cluster in two regions of std::function `__func<lambda,allocator,sig>::__clone/destroy/target` machinery (one big blob at 0x334890+, one bank of small thunks at 0x345ce0..0x346be4).

Two of those machinery functions (0x334890 and 0x335620) have **exactly one direct caller each** — both inside the same enclosing function at **0x3184d0**, only ~0x85 bytes apart. By construction this is `lt::Internal::Pipeline::setLensShading()`.

### 2. Reachability from CIAPI entry points (shortest paths)

Forward call-graph BFS from each exported CIAPI entry to setLensShading (0x3184d0):

```
CIAPI::Renderer::render          (0x390180) -> 0x3b8ba0 -> 0x318040 -> setLensShading   [depth 3]
CIAPI::Renderer::Create          (0x390540) -> 0x3af8f0 -> 0x318030 -> setLensShading   [depth 3]
CIAPI::Renderer::deserialize     (0x390480) -> 0x3b6f20 -> 0x318040 -> setLensShading   [depth 3]
CIAPI::DirectRenderer::Create    (0x394240) -> 0x3cb330 -> 0x318040 -> setLensShading   [depth 3]
CIAPI::DirectRenderer::render    (0x3944f0) -> 0x3cb8a0 -> 0x318040 -> setLensShading   [depth 3]
CIAPI::ApplyTuning               (0x3927e0) -> ... -> 0x318030 -> setLensShading        [depth 6]
```

Both Renderer (full quality) and DirectRenderer (fast path) converge through the helper at **0x318030 / 0x318040** — the Pipeline base/tune installer that calls every `set<Stage>` method, including setLensShading. ApplyTuning reaches it via the LRIS state restore path through 0x3edb80.

setLensShading itself has **7 direct callers** within libcp's hidden internal code (at 0x318190, 0x318290, 0x31acf0, 0x31af30, 0x31b110, 0x31b470, 0x31b910). Upward BFS from setLensShading visits 60 distinct functions — this is a deeply integrated call graph, not a dead path.

### 3. Lumen.app main binary

`/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/Lumen/Lumen.app/Contents/MacOS/Lumen`:
- `strings | grep -i 'setLensShading|LensShading|lens_shading'` → **0 hits**
- `nm -a` → **0 hits** for any LensShading symbol
- Only references the public `CIAPI::*` namespace (Renderer, DirectRenderer, ImagePyramid, RendererBase, DepthEditor)

The Lumen GUI bridge does NOT directly call setLensShading. It does not need to — it calls `CIAPI::Renderer::render` (or deserialize/Create) which internally configures the entire pipeline (including lens shading) via libcp's hidden `lt::Internal::Pipeline::set*` setters.

### 4. lri_process

`/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process` is a thin Mach-O CLI that links libcp.dylib via `@rpath/libcp.dylib`. It imports BOTH:
- `CIAPI::Renderer::Create / render / deserialize / serialize / writeImage`
- `CIAPI::DirectRenderer::Create / render`
- `CIAPI::ApplyTuning`

It has a `--direct-renderer` flag with help text "DirectRenderer fallback (faster, lower quality)". By default it uses the full Renderer, which (per shortest path above) reaches setLensShading at depth 3.

### 5. LRIS protobuf / vignetting calibration

libcp contains:
- Protobuf type `ltpb.VignettingCharacterization` with sub-types `VignettingModel`, `MirrorVignettingModel`, `CrosstalkModel`
- Source: `/Users/srv-build/jenkins/.../camera/protobuf/vignetting_characterization.pb.cc`
- Config keys: `lens_shading.type`, `lens_shading.multiplier`
- Error paths (3 LEA xrefs each — multiple call sites):
  - `"vignetting model not found!"`
  - `"No vignetting data!"`
  - `"invalid vignetting data size!"`
  - `"Width of vignetting profile does not match IR correction database!"`
  - `"Height of vignetting profile does not match IR correction database!"`
  - `"empty vignetting data found!"`
  - `"Bad LRI: Vignetting data not found for at module"`

`lens_shading.type` has **11 distinct LEA xrefs** in __text (multiple parameter readers across pipeline configuration paths). `lens_shading.multiplier` has 3 xrefs. These keys ARE actively read at pipeline configuration time.

### 6. Stage 7 worker template instantiations alive in libcp

Three of four possible `RemoveVignettingGeneric<T, bool>` template instantiations are linked:
- `lt::(anon)::RemoveVignettingGeneric<float, true>` — float Bayer path
- `lt::(anon)::RemoveVignettingGeneric<vec4x32f, false>` — color path, no multiplier
- `lt::(anon)::RemoveVignettingGeneric<vec4x32f, true>` — color path, with multiplier

`RemoveVignettingGeneric<float, false>` is dead-stripped (no callers).

---

## Why the LLDB probes saw 0 hits in lri_process

The probes were run against the L16_01325_corrupt_* test LRIs in /Volumes/Dev/lumen-phoenix-scratch/. These are **damaged or partial LRIs** missing module records or vignetting calibration. setLensShading IS called every render, but its configuration code reads `VignettingCharacterization` from the LRIS module record; on missing/invalid data it logs an error (`"Bad LRI: Vignetting data not found for at module"`) and installs a no-op lambda, leaving the lambda at its default identity passthrough. The `RemoveVignettingGeneric<*>` worker therefore never executes and any breakpoint on it sees zero hits — even though setLensShading itself was called.

To verify on a clean LRI: run lri_process on an UNCORRUPTED L16 capture and probe both setLensShading (0x3184d0) and the three RemoveVignettingGeneric template instantiations.
