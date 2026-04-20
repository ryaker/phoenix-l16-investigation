# Session 4 — Phase B Purpose Investigation (closes #18)

**Date:** 2026-04-13
**Scope:** Static-disasm + cross-reference of existing runtime logs. NO new LLDB spike.
**Goal:** Determine whether Phase B (lambda_0 + lambda_7 ColorPost + lambda_8 MonoMerge, t=289..672) produces intermediate state that Phase D reads, or a separable preview/output.

---

## TL;DR

**Phase B is the Mono-path final render stage, NOT a preview and NOT a stats pre-pass.**

- lambda_7 is slot `$_7` in `PipelineC1`'s default lambda table, typed `ColorPipelinePayload` — it drives the Halide-generated exposure-normalized color post-processing kernel that emits **uint16 merged output tiles**.
- lambda_8 is slot `$_8`, typed `MonoPipelinePayload` — it merges the **two buffers** of a `MonoPipelinePayload` (primary canvas at `+0xd0..+0xf0`, secondary canvas at `+0x130..+0x158`) into a third output buffer.
- Phase B runs on **merged final-canvas tile coordinates** (260×260 and 256×256 tiles on a 10432×7824 canvas) — NOT per-camera pipeline coordinates like lambdas 1/2/5/6. The 192 hits = 12 merged output tiles × 16 cameras.
- lambda_7/8 writes a **uint16 output buffer** (stride×2) rather than the float32 canvas (stride×4) that Phase D writes. The strides observed in disasm of `0x350d00` (real ColorPost body) confirm: `leaq (%r8,%rax,2), %rax` for dest vs `leaq (%r8,%rax,4), %rax` for src.

**Phase B's output is the L16 Mono-path image.** Phase D's Color Bayer ISP (lambdas 0/1/2/5/6) runs **afterward**, producing a separate color-path output. The two paths are independent parallel renders feeding the final composite.

---

## Key evidence

### 1. Architectural separation — MonoFusion is a first-class module

libcp strings contain symbols for three sibling fusion modules:
- `lt::MonoFusion::initialize(const bool*)` — mono-path camera fusion
- `lt::ColorFusionBayer::initialize(const bool*, const Vec2<f>&)` — color-path Bayer fusion
- `lt::StackFusion(...)` — HDR stack fusion

The presence of `MonoFusion` as a dedicated class, with its own `operator()` lambdas and a guard string `"Called MonoFusion::initialize() twice!"`, proves that the L16 ISP has a **dedicated mono image path** separate from the color path. Phase B's `lambda_8 : MonoPipelinePayload` is the execution of that mono path.

### 2. lambda_7/8 write uint16, Phase D writes float32

From the disasm of the real `ColorPost` body (`0x350d00`, tail-called from the `0x341130` thunk):
- Source read: `movq 0x120(%rbx), %r8; ... leaq (%r8,%rax,4), %rax` — source stride ×4 = **float32 RGBA** canvas at payload `+0x120`.
- Destination read: `movq 0x100(%rbx), %xmm0; ... leaq (%r8,%rax,2), %rax` — destination stride ×2 = **uint16** output at payload `+0x100`.
- Exposure normalization: `movss 0x4(%rax), %xmm0; movss 0x8(%rax), %xmm2; subss %xmm0, %xmm2; divss %xmm2, %xmm1` — reads `[min, max]` from context+0x198, computes `1.0 / (max - min)` = exposure normalization scale.

Phase D lambdas write **float32 stride×4** canvases. Phase B's output buffer is uint16, meaning it's the **quantized/displayable output** for the mono path — a final deliverable, not a float preview.

### 3. MonoMerge reads TWO input canvases

Disasm of `0x3596e0` (real MonoMerge body, called from `0x341220` thunk):
- Reads primary canvas at `0xd0(%r14) .. 0xf8(%r14)` — stride×4 (float32).
- Reads a **second** canvas at `0x130(%r14) .. 0x158(%r14)` — also stride×4 (float32).
- Merges them (per-pixel blend inside the Halide kernel at `0x3596e0`+inner) to produce the final mono output buffer referenced via the `rsi` payload arg.

Two-input merge = "merge color-path canvas with highlight/shadow canvas" into a mono-path final image. This is the classic L16 algorithm: fuse color Bayer canvas with mono-sensor canvas to preserve detail in highlights.

### 4. Tile coordinates are on the final canvas, not per-camera

From `lldb_isp_findings.txt` PART 4 and the session 3 hit-count analysis:
- lambdas 1/2/5/6 (Phase D): tile sizes 226×234 to 242×250, 16 cameras × ~20 tiles = 330 hits. These are **per-camera** tiles with shrinking guard-band borders.
- lambdas 7/8 (Phase B): tile sizes 260×260, 260×304, 320×260 / 256×256, 256×304, 320×256, 192 hits = 12 merged tiles × 16 cameras. These are **final canvas** tiles — strictly larger than per-camera tiles.

lambda_7 tile origins: `[252, 516]`, `[1020, 1284]`, `[3580, 3844]` — these are pixel coordinates on the 10432×7824 full canvas, not per-camera coordinates. Phase B is operating on the merged canvas.

### 5. Phase B and Phase D share the same Pipeline object (but different payload offsets)

From `session2_probe_log.json`:
- `lambda_0` Phase A: `rsi_payload = 0x304be5b48`
- `lambda_8` Phase B: `rsi_payload = 0x304be5b50` (same base, +8 byte offset)

These are **adjacent payload fields inside the same Pipeline instance**. Phase B doesn't read from Phase A's canvas — it reads from its own `Mono*` payload slot in the same Pipeline. Phase D's Bayer lambdas similarly have their own `Bayer*` payload slot.

**The Phase A/B/C/D ordering reflects the installation order of lambdas in the `0x33f042` dispatcher**, not a data-flow chain. Each phase is an independent render of a different output image. The shared Pipeline instance coordinates them but they produce **different outputs**.

### 6. No stats/AWB feedback strings in the dispatcher area

Searched `strings_all.txt` for `preview`, `luminance`, `pre_pass`, `coarse`, `stats_pass`, `two_pass`, `prepass`: zero hits near the pipeline dispatcher. The only "stats" strings are error messages for `ISPStats` / `histogram` objects, which are configured at pipeline setup time (not produced during Phase B).

---

## Data dependencies — does Phase D read Phase B output?

**No.** The buffers are structurally segregated:

| Buffer | Written by | Read by | Type |
|---|---|---|---|
| BayerPipelinePayload.main_buf (+0x90) | lambda_0, lambda_1, lambda_2, lambda_5, lambda_6 (Phase A/C/D) | lambda_6 CCM → next stage | float32 RGBA canvas |
| ColorPipelinePayload extended buffers (+0xd0..+0x100..+0x120) | Phase B ColorPost | Phase B MonoMerge only | float32 src → uint16 dest |
| MonoPipelinePayload dual canvases (+0xd0, +0x130) | Upstream mono-path code (not in Phase B lambdas) | Phase B MonoMerge | float32 → uint16 final |

Phase D lambdas **do not** dereference any buffer at offsets `+0xd0`, `+0x100`, `+0x120`, `+0x130` on any payload. They only touch `+0x90` / `+0x98` (main_buf / src_buf). Buffer layout is disjoint.

**UNVERIFIED:** I did not run an LLDB probe to confirm the physical memory of the Phase B uint16 buffer is distinct from any Phase D canvas — the conclusion rests on static analysis of payload struct offsets and the disjoint stride arithmetic. A single LLDB verification would be: break at `0x350e14` (ColorPost call to Halide at `0x352950`), record `[rbx+0x120]` as the dest addr; break at lambda_6 entry (`0x341040`) anywhere in Phase D, record `[rdi+0x90]`; confirm the two addresses are in different mmap regions. Low priority — the structural evidence is already strong.

---

## Phoenix action

**SKIP Phase B entirely.**

Phoenix is reverse-engineering the **color-path final output** (the 77 MB TIFF that Lumen writes via `session3_out.tif`). Phase B produces the **mono-path final output**, which is a separate image deliverable that Phoenix can re-implement later if/when a mono render target is added to the Phoenix spec.

Phase D (lambdas 0/1/2/5/6) is the color path. Phase A/C are color-path canvas seeding. Phase B is a parallel mono-path render that does not feed Phase D.

Concretely for Phoenix:
1. Do NOT replicate `ColorPost` (lambda_7) — it normalizes a float canvas into a uint16 mono output, which Phoenix doesn't emit.
2. Do NOT replicate `MonoMerge` (lambda_8) — it fuses two mono-path canvases into a final uint16 mono image.
3. Phoenix's render loop should install ONLY the Phase A/C/D lambdas (lambda_0, lambda_1, lambda_2, lambda_5, lambda_6) and skip slots $_7, $_8 in the `PipelineC1` default table.
4. If Phoenix later adds a "write mono TIFF" feature, revisit Phase B and install the mono-path lambdas at that time. The existing disasm at `0x350d00` (ColorPost) and `0x3596e0` (MonoMerge) is ready for translation.

---

## UNVERIFIED / open items

1. **The secondary canvas at MonoMerge payload +0x130**: I know it exists and is read by lambda_8, but I did not trace who populates it. Candidates are an unnamed default lambda (slot `$_9` MonoPipelinePayload, which was observed as 0 hits in Session 2 — so not slot 9) or an upstream setter-installed lambda that fires in Phase A before t=289. If Phoenix ever needs the mono output, this secondary canvas must be traced.
2. **Whether lri_process ever actually consumes the Phase B uint16 output**: The lri_process binary might write the mono image to a separate TIFF plane, or it might discard it entirely for the CLI path. Phoenix's scope (color TIFF out) is unaffected either way.
3. **Why Phase B uses exposure normalization min/max from context+0x198**: these `min_exposure`/`max_exposure` floats are likely from the LRI's capture metadata (per-capture HDR range). Not needed for Phoenix's color path.
4. **Phase C (lambda_0 only, 96 tiles)**: still slightly ambiguous. Session 3 labeled it "refinement/continuation" of Phase A. Likely it's the last 96 per-camera canvas-seed tiles that didn't fit in the first 288 of Phase A due to tile ordering, not a distinct architectural phase. No Phase-B impact.
5. **Static-only analysis**: I did NOT run any LLDB probes this session. All conclusions are static (disasm + prior session logs). If a single confirmation probe is wanted, see item in "Data dependencies" above — 10 minutes of LLDB would close it.

---

## Artifacts consulted

- `/Volumes/Dev/lumen-phoenix-scratch/q123/disasm_full.txt` — libcp disasm (1.33M lines); read bodies at `0x33ede0` (pipeline stage dispatcher parent function), `0x33f180` (inner tile-loop w/ vtable dispatch at `0x33f3e8`), `0x341130` (lambda_7 thunk → `0x350d00`), `0x341200`/`0x341220` (lambda_8 thunk → `0x3596e0`), `0x350d00` (ColorPost body), `0x3596e0` (MonoMerge body).
- `/Volumes/Dev/lumen-phoenix-scratch/q123/strings_all.txt` — confirmed `MonoFusion`, `ColorFusionBayer`, `StackFusion` class symbols; confirmed absence of `preview`/`pre_pass`/`stats_pass` strings in dispatcher region; confirmed `PipelineC1EvE3$_7` uses `ColorPipelinePayload` and `$_8` uses `MonoPipelinePayload`.
- `/Volumes/Dev/lumen-phoenix-scratch/lldb_isp_findings.txt` — PART 4/5/6/7/8 confirmed lambda_7 tile sizes (260×260 merged canvas), lambda_8 final output tile sizes, ColorPipelinePayload struct layout at +0x90/+0x98, and the exposure-normalize / Halide dispatch at `0x350e14 → 0x352950`.
- `/Volumes/Dev/lumen-phoenix-scratch/session2_probe_log.json` — confirmed lambda_7 inline-float closure `[255.0, 22.0]`, lambda_8 shared rdi_this across all 192 hits, and payload offset delta `b48` vs `b50` (= +8 bytes) between lambda_0 and lambda_8 on the same Pipeline instance.
- `/Volumes/Dev/lumen-phoenix-scratch/session3_upstream_probe.md` — Big finding #6 (Phase architecture) + the explicit UNVERIFIED on Phase B purpose that this session resolves.
