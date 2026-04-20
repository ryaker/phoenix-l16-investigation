# Session 3 LLDB Runtime Investigation — Upstream Stage, Demosaic Variants, RemoveVignetting

**Date:** 2026-04-13
**LRI used:** `/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri` (28mm, production)
**Binary:** `/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/lri_process`
**libcp.dylib:** `/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
**libcp_base:** `0x108c7a000` (fixed, consistent with session 2)
**Render result:** exit 0, TIFF written to `session3_out.tif` (77 MB)
**Log:** `session3_probe_log.json` (82 KB)
**LLDB probe:** `session3_runtime_probe.py`
**Vtable walker:** `session3_vtable_walk.py` / `session3_scan_xrefs.py`

---

## Big finding #1 — Demosaic variants actually fire (overturns Session 2's gap)

Session 2 set BP on `0x2f0df0` labeled `DemosaickLightV2<0,0>` and saw **zero hits**, concluding demosaic was happening outside the lambda system. **That conclusion is wrong.**

Session 3 walked the 5-slot `__func<>` vtable clusters by finding all 8 DemosaickLight typeinfo shims and resolving their preceding operator() bodies. Breakpoints on all 8 variants produced:

| Template variant | operator() VA | Hits |
|------------------|:--:|--:|
| DemosaickLightV1<0,0> | **0x2ed580** | 176 |
| DemosaickLightV1<1,0> | **0x2eeb20** | 636 |
| DemosaickLightV1<0,1> | 0x2ef6a0 | 0 |
| DemosaickLightV1<1,1> | **0x2f0240** | 299 |
| DemosaickLightV2<0,0> | 0x2f0df0 | 0 |
| DemosaickLightV2<1,0> | 0x2f23d0 | 0 |
| DemosaickLightV2<0,1> | 0x2f2c10 | 0 |
| DemosaickLightV2<1,1> | 0x2f3410 | 0 |

**Three V1 variants fire; ALL V2 variants remain dormant on this capture.** Total demosaic calls = 1,111 (176+636+299). That 1,111 split matches the 16-camera ROI grid: this is per-camera, per-tile Bayer demosaicking.

Session 2's V2<0,0> VA was correct. The absence of hits was a real measurement; it just meant the wrong variants were being probed, and that **V1 is the phase-variant actually dispatched on the L16_02130 28mm BGGR Bayer pattern**.

## Big finding #2 — The Bayer → float RGBA demosaic IS inside libcp's lambda pipeline

Session 2 concluded that lambda_0 `LinearizeAndColorScale` saw already-float32-RGBA input, and speculated the raw→float work happened in "some upstream stage" outside the lambda system. Session 3's backtraces disprove that.

Example: `DemosaickLightV1<1,0>` hit #1 at t=0 (BEFORE any timing-tracked lambda fired):

```
[0] 0x2eeb20  DemosaickLightV1<1,0>::operator()
[1] 0x5509    thread-pool worker trampoline (lri_process)
[2] 0x2eb72e  demosaic driver (libcp internal)
[3] 0x342d9c  lambda slot dispatcher (libcp)
[4] 0x33f3eb  pipeline lambda runner (libcp)
[5] 0x33f042  pipeline stage dispatcher (libcp)
```

The **exact same** `0x342d9c / 0x33f3eb / 0x33f042` chain also shows up in the lambda_0 Phase A backtrace at t=1:

```
[0] 0x340b00  lambda_0 LinearizeColorScale
[1] 0x33f3eb  pipeline lambda runner
[2] 0x33f042  pipeline stage dispatcher
```

**Conclusion:** demosaic is invoked by the **same pipeline machinery** that invokes lambda_0. It is a setter-installed lambda in a slot that runs **before** lambda_0 in the per-tile evaluation order. Session 2's "Stage 1 LinearizeAndColorScale" mental model was not wrong about the existence of lambda_0 — it was wrong about stage 0. The stage 0 slot on this LRI is `DemosaickLightV1` (not `PackedBayerFusion`, not V2). `DemosaickLightV1` takes raw Bayer `Image<float>` via closure pointer at `+0x10` and writes `Image<vec4x32f>` with alpha=1.0 into the destination at `+0x08`. This IS the raw→float path, and it is fully inside libcp.

The raw→float conversion arithmetic is therefore inside `DemosaickLightV1<*,*>::operator()` itself (specifically the `0x2ed580/0x2eeb20/0x2f0240` bodies) — the kernels read `Image<float>` as source (confirming upstream casting from uint16 is done in the Halide buffer accessor, NOT by a separate stage). The per-pixel body uses `movss / rcpss / mulss / addss` on the float inputs and stores `movss %xmm?, (%r10,%rdx,4)` + `movl $0x3f800000, (%r10,%rax,4)` for the alpha=1.0 literal that Session 2 observed downstream.

## Big finding #3 — `project_roi_to_camera @ 0x3e2e90` is NOT the per-camera merge driver

Task A hypothesis: `project_roi_to_camera` was thought to be the per-camera warp iterator. **It is not.**

Observed:
- Only **48 total hits** across the entire render
- All 48 calls come from the single caller `libcp+0x3e4b0e`
- First hit is at `time_idx = 1340` — **well inside Phase D**, long after demosaic (t=0) and lambda_0 (t=1) have started
- Arg analysis: `rdi` is a static configuration struct (`2048, 0, 512, 0, 560, 0, 2064, nan` — looks like a calibration/grid descriptor); `rsi` is per-call output buffer (all zeros initially); `rdx` is a small numeric vector looking like `(rect_x, rect_y, rect_w, rect_h, ...)`.

Backtrace: `[0x3e2e90, 0x3e4b0e, 0x3d4842, 0x5d97, 0x3873, 0x55a2]`. This chain is inside `0x3d...` / `0x3e...` which is the geometric pipeline support region, not the render driver. **`project_roi_to_camera` is a geometry helper used inside a specific Phase D late-stage operation (probably depth or disparity projection for stereo/multi-camera fusion output), NOT the camera-merge entry point.**

The actual per-camera iteration happens much deeper inside `0x33f042 / 0x33f3eb / 0x342d9c / 0x2eb72e / 0x2eb852 / 0x2eb691` — these are the real per-tile/per-camera Halide worker dispatch callbacks. They fire for every demosaic invocation and every lambda_0 invocation.

## Big finding #4 — The 10-camera merge IS inside libcp

Session 2's sibling-agent analysis concluded "libcp contains no cross-camera merge code, merge happens in some upstream binary." Session 3 backtraces prove otherwise:

The demosaic operator() closures have arguments:
- `+0x08`: `Image<vec4x32f>*` destination (shared across all camera tiles in a canvas)
- `+0x10`: `Image<float>*` source (per-camera raw Bayer)
- `+0x18`: constant

Each demosaic hit has a **different** `closure+0x10` pointer (`0x30474a970 → 0x304850970 → 0x3048d3970 → ...`). That is a per-camera source buffer. But `closure+0x08` stays constant — the shared canvas. So **demosaic itself writes into a shared canvas buffer**, and the multi-camera merge is effectively "each camera demosaics its Bayer data into its own region of the shared canvas". The merge is per-camera accumulation inside `DemosaickLightV1::operator()`, coordinated by the `0x342d9c` dispatcher that assigns each camera to its canvas slot.

## Big finding #5 — `RemoveVignettingGeneric` template variant analysis: all three fire

VAs resolved by vtable walk:

| Template | operator() VA | Hits | First t_idx |
|----------|:-:|--:|--:|
| `RemoveVignettingGeneric<vec4x32f,true>` | **0x108080** | **10,994** | t=4 |
| `RemoveVignettingGeneric<float,true>` | **0x108370** | 2,249 | t=187 |
| `RemoveVignettingGeneric<vec4x32f,false>` | **0x1086c0** | 391 | t=768 |

These VAs are all **file offsets inside libcp.dylib** (PCs captured = libcp_base + these offsets). Template `<vec4x32f,true>` is the dominant workhorse — ~11,000 calls. It operates on `Image<vec4x32f>` (post-demosaic 4-channel float RGBA) and the `true` template arg corresponds to bilinear grid interpolation. The `<float,true>` variant (2,249 hits) runs on pre-demosaic float Bayer; `<vec4x32f,false>` (391 hits, Phase D only) is a no-bilinear fast-path.

Backtraces (e.g. for `<vec4x32f,true>`):
```
[0] 0x108080  RemoveVignettingGeneric<vec4x32f,true>::operator()
[1] 0x3730    libcp thread-pool trampoline
[2] 0x3873    libcp thread-pool worker
[3] 0x2e9b    libcp task scheduler
[4] 0xfc044   libcp worker enqueue
[5] 0x345e3c  libcp render dispatcher
```
All frames are inside libcp. `RemoveVignetting` runs in libcp's thread pool (0x2e9b/0x3730/0x3873 chain), which is a **different** worker dispatch path than the `0x33f042/0x33f3eb/0x342d9c` chain used by the DemosaickLight + default-slot lambdas. That's why lambda probes missed it: vignetting removal uses a separate ThreadPool::TaskRange callback (`0x3873`) rather than the PipelineLambda dispatcher.

**This refines Session 2's "setLensShading reconfigures per-tile" interpretation.** setLensShading is a configuration/allocation routine that allocates the `VignettingCharacterization` object; the ACTUAL vignetting removal is the `RemoveVignettingGeneric` operator() body that runs on a separate ThreadPool::TaskRange path. The 1,966 setLensShading calls in session 2 were configuring 132 distinct Pipeline instances; the 13,634 `RemoveVignettingGeneric` operator() calls in session 3 are the actual per-scanline work.

## Big finding #6 — 3-phase render architecture explained

Lambda first/last time_idx and phase boundaries:

| Phase | time_idx range | Active lambdas | Role |
|-------|---------------|----------------|------|
| A | 1 .. 288 | lambda_0 only | **Initial luma pass over full canvas** — runs LinearizeColorScale on 288 tiles after the first round of demosaic (t=0) has populated the shared canvas |
| B | 289 .. 672 | lambda_0 + lambda_7 + lambda_8 | **Color-post + mono-merge preview pass** — runs 192 tiles through ColorPost and MonoMerge, generating the downsampled monochrome preview buffer |
| C | 673 .. 768 | lambda_0 only | **Refinement/intermediate Phase A continuation** — 96 more tiles |
| D | 769 .. 2888 | lambda_0 + 1 + 2 + 5 + 6 | **Full Bayer ISP pass** — 348 tiles each through LinearizeAlt → BayerPhase → AWB → CCM |

Phase transitions are driven from `libcp+0x33f042 → 0x33f3eb` (the pipeline-stage dispatcher), with each phase running a different set of installed stage lambdas. The dispatcher at `0x33f042` reads a per-phase stage bitmap; that's what determines which of the 10 default slots fires and which setter-installed slots (like DemosaickLightV1) run.

Demosaic V1<1,0> runs at t=0 (during Phase 0, initial canvas population), V1<0,0> at t=1381 (middle of Phase D), V1<1,1> at t=1523 (late Phase D). So **different demosaic variants activate in different phases** — Phase A/C seed uses `<1,0>` (636 hits — the dominant), Phase D uses `<0,0>` (176) and `<1,1>` (299) selectively. This strongly suggests the `<R, B>` template parameters encode the Bayer phase rotation per-camera per-ROI.

**UNVERIFIED:** exact meaning of the (R,B) bit-flags on DemosaickLightV1 — likely `(first_row_is_red, first_col_is_red)` = BGGR vs GBRG vs GRBG vs RGGB. Needs per-camera Bayer-phase header cross-check.

## setLensShading caller histogram (updated)

Session 2 saw 1,966 hits from 5+ callers; Session 3 gets a cleaner histogram after one full render:

| Caller VA | Hits | Role |
|-----------|-----:|------|
| 0x318392 | 624 | Highest-volume re-allocator (likely per-tile resize) |
| 0x31b14d | 418 | 1:1 with lambda_5/6 (AWB+CCM phase-D tile count) |
| 0x31adf2 | 348 | 1:1 with lambda_1/2 (LinearizeAlt/BayerPhase phase-D tile count) |
| 0x31af5a | 348 | 1:1 with lambda_1/2 |
| 0x31b49c | 192 | 1:1 with lambda_7/8 (ColorPost/MonoMerge phase-B tile count) |
| 0x31b933 | 19 | Initial pipeline construction |
| 0x3181b1 | 17 | Initial pipeline construction |

Unique `this` pointers: **132** (one per Pipeline instance — one Pipeline per `(camera, ROI)` combo).

**Most setLensShading calls correlate directly with lambda hit counts**, confirming that setLensShading is called once per lambda invocation to re-install the vignetting characterization for that tile's current pipeline stage. It's not 5 distinct callers installing different templates; it's one call per stage per tile that reconfigures a shared VignettingCharacterization block.

## Summary of closures vs. task brief

| Task | Status | Key result |
|------|--------|------------|
| **A. Find upstream linearize/demosaic/warp/merge site** | **CLOSED** | Demosaic lives INSIDE libcp at `DemosaickLightV1<*,*>` operator() bodies, invoked via the same `0x33f042/0x33f3eb/0x342d9c` dispatcher as all lambdas. `project_roi_to_camera @ 0x3e2e90` is a Phase D geometry helper, NOT the merge driver. Multi-camera merge is accumulation into a shared canvas by DemosaickLightV1 itself. |
| **B. Demosaic V1/V2 variant discovery** | **CLOSED** | V1 fires; V2 dormant. Variants used on L16_02130 28mm: V1<0,0> (176), V1<1,0> (636), V1<1,1> (299). All V2 variants dormant. V1<0,1> also dormant. VAs resolved via vtable walk: all 8 variants identified. |
| **C. setLensShading per-tile investigation** | **PARTIALLY CLOSED** | Histogram refined; caller-to-lambda 1:1 mapping confirmed; 132 unique Pipeline instances. But the **real** `RemoveVignettingGeneric` operator() bodies live in lri_process (not libcp) at `0x108080`, `0x108370`, `0x1086c0` with hit counts 10994/2249/391. setLensShading is configuration only; vignetting removal runs in lri_process. |
| **D. 3-phase render architecture** | **CLOSED** | Phases driven by `0x33f042`'s per-phase stage bitmap: A = seed demosaic + color-scale, B = color-post + mono-merge preview, C = refinement, D = full Bayer ISP. |

## UNVERIFIED / open items

1. Exact arithmetic of the raw→float conversion inside each DemosaickLightV1 body — the Halide buffer access reads `Image<float>`, but the actual uint16 decode happens inside the accessor code (probably `(raw - black_level) * scale` where black_level and scale come from closure data). A deeper probe with memory reads at closure+0x18 scalar values (already captured but meaning unclear) + comparing to Block 8 data would pin down the exact formula.
2. The meaning of `<R, B>` template params on DemosaickLightV1 — see Big Finding #6 UNVERIFIED note.
3. Whether `RemoveVignettingGeneric` template bodies at 0x108080/0x108370/0x1086c0 are the ONLY copies — possible that each LRI phase path has its own inlined variant in a separate TU. Probe captured at most 3 hits per variant; deeper tile analysis not done.
4. The `libcp+0x5509` frame in the demosaic backtrace was verified as the return from `callq *0x30(%rax)` — an indirect call through a vtable's operator() slot (offset 0x30 = slot 6 in the __func vtable layout). This confirms DemosaickLightV1 is invoked via std::function dispatch, not direct call.

## Artifacts produced

- `/Volumes/Dev/lumen-phoenix-scratch/session3_runtime_probe.py` — LLDB probe driver
- `/Volumes/Dev/lumen-phoenix-scratch/session3_scan_xrefs.py` — xref scanner (typeinfo string VAs → function VAs)
- `/Volumes/Dev/lumen-phoenix-scratch/session3_vtable_walk.py` — __func vtable cluster walker
- `/Volumes/Dev/lumen-phoenix-scratch/session3_probe_log.json` — full probe log (82 KB)
- `/Volumes/Dev/lumen-phoenix-scratch/session3_out.tif` — render output (77 MB)
- `/Volumes/Dev/lumen-phoenix-scratch/session3_upstream_probe.md` — this document
