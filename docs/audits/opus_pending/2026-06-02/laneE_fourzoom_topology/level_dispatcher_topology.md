<!-- provenance: workflow wf_d596de8b-90c (l16-unfenced-w10), 2026-06-03; finder + verifier; reliable=None -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, weak-labeled, static disasm).
**Verifier reliability:** verifier stage did not run; ORCHESTRATOR independently re-verified the level dispatcher branch logic (0x3ec9dc movl 0x18(rax); levels 2-4->0x3d0650, level0->0x3ec770, level1->0x3ebb80, else 'Level not supported') — PASS. Cross-level recombine site = runtime (indirect dispatch).

## Lane E: four-zoom merge TOPOLOGY — processLevel functions and cross-level combine (STATIC)

Binary: `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
Method: `arch -x86_64 lldb --batch -o 'target create <lib>' -o 'disassemble ...'` ; `strings -a -t x`; `otool -tV`. All VAs re-extractable.

### PREDICTION (pre-verification)
Coarse tier upsampled + detail-added per level (Laplacian collapse / addps across levels). **PARTIALLY REFUTED** — see verdict.

### Q1 — The other level functions (OBSERVED, static)

| Level | Function VA | What it does | Evidence |
|---|---|---|---|
| 0 | `processLevel0` = `0x3ec770` | calls `0x365960` (builds cosf window/kernel tables) then IRAMP `0x3661b0` (multi-source merge) | string `"Requested PipelineCache::processLevel0 before initResamp()!"` at code ref `0x3ec837`; `0x3ec7da` callq `0x365960`; `0x365f4b` callq `0x3661b0` |
| 1 | `processLevel1` = `0x3ebb80` | single-source `ImageWarpClamped<ResamplerFilter=2, vec4x32f>` resample over `PipelineCache+0x1e0` resample-state object; builds a 0x58-byte callback (vtable typeinfo `void(*)(double const*,double*)`) and copies a 5-elem record vector | RTTI lambda `...lt::PipelineCache::processLevel1...ImageWarpClamped...` at `0x608bb0`/`0x608cc0`; body reads `0x1e0(%r14)` at `0x3ebbab` |
| 2,3,4 | `0x3d0650` (shared) | plain selected-cache level/ROI read (`0x3d01b0`) + rescale (`0x36f800`); NO merge | dispatcher branch `0x3ec9e7 -> 0x3d0650`; `0x3d072d` callq `0x3d01b0` |

**Level DISPATCHER** = `0x3ec960` = vtable slot `0x65f5e0 + 0x30` (memory read of `0x65f5e0` shows `+0x30 = 0x3ec960`). It is ONE virtual method taking a level argument, NOT separate per-level vtable slots. Branch logic at `0x3ec9dc`: `eax = level field *(tileDesc+0x18)`; `ecx = eax-2`; `cmpl $0x3,ecx; jae 0x3eca1c` → if level in {2,3,4} go to `0x3d0650`; else at `0x3eca1c` `testl eax,eax; je`→level0 (`0x3ec770` at `0x3eca46`); `cmpl $1; jne`→`"Level not supported by PipelineCache!"` (string ref `0x3ecaee`); else level1 (`0x3ebb80` at `0x3eca34`).

### Q2 — How the tiers/levels are organized (OBSERVED + LEAD)
- `PipelineCache+0x8` is a **5-entry dimension pyramid** (committed evidence `lldb_pipelinecache_level_vector_four_zoom.md`): entry0 tiered `10432x7824`(28/35) / `8896x6672`(70/150), then `(4160,3120),(2080,1560),(1040,780),(520,390)` for all zooms. So "levels" = Gaussian octaves of the render. OBSERVED.
- Class is `lt::PipelineCache`, constructed from `vector<Vec2<int>>` (= the dimension pyramid), `TileStorage`, `ImageCaches`, `StereoAsyncAPI`, `RendererProfileConfig`; its constructor lambda emits `vector<Tile<Vec3<Float16>>>` (RTTI `0x6088a0`). OBSERVED.
- **Only level 0 runs the IRAMP N→1 multi-camera merge.** Levels 1..4 are single-source resample/reads. So the focal-tier multi-camera fusion is a level-0 phenomenon; coarser levels are resolution support, not where cameras combine. OBSERVED (static body classification).

### Q3 — Where per-level outputs recombine (NOT FOUND statically)
- A generic `lt::Internal` **Gaussian/Laplacian collapse-and-blend** utility EXISTS: `CreateAndBlendLaplacianPyramids` (RTTI `0x5f11b0`), `LaplacianPyramidConfig`, `BilateralUpsampleFromCollapse` (RTTI `0x5dd060`), collapse body ~`0x136c0` (strings `"gaussian/laplacian pyramid size mismatch!"` at code refs `0x138d3`/`0x13b03`, `"empty input!"` at `0x13894`). **LEAD** — this is a SEPARATE subsystem from `PipelineCache::processLevelN`; I did NOT prove it runs on the bridge HDR path. Committed C6 evidence shows the tele `ImagePyramid` geometry route was zero-filled / inert, so do not assume this collapse drives the bridge output.
- The actual upsample+add SITE that fuses the 5 level outputs into the final image was **not located** — the dispatcher `0x3ec960` is invoked indirectly (vtable `0x65f5e0+0x30`) with a per-tile level arg, so static cannot cross to the level-loop driver. **This is a hard indirect-dispatch wall for static.**

### Scope-bound disclaimers
- I did NOT run the bridge; no runtime confirmation of which levels fire per zoom, nor of any cross-level addps/collapse on the bridge path.
- I did NOT prove IRAMP is the reducer here (that is owned by other lanes; existing evidence has it CANDIDATE/bounded).
- "processLevel1 = single-source resample" is from its visible body + RTTI; not a full trace.
- Negative "no Laplacian collapse on bridge path" is NOT claimed — only "collapse utility is a separate subsystem, bridge use unproven."