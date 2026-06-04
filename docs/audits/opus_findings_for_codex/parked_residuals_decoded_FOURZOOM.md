<!-- GRADUATED finding. provenance: orchestrator (coverage-sentinel) + decode-residuals agent (a73011d379ece6576), deterministic static disasm of libcp b38dc4b3, orchestrator-spot-verified (strings/rodata/RTTI), 2026-06-04. Decodes the sub-mechanisms that were parked in SUBSUMPTION_RESIDUALS.md instead of investigated. -->
**Status:** NEEDS_CODEX_VALIDATION — **GRADUATED to STATIC-DETERMINISTIC verified** (Tier 1). These six
mechanisms were initially parked as "residuals/LEADs" during the subsumption pass; that was a deferral, not
a resolution. They are decoded here byte-exact (static disasm, zoom-invariant). Load-bearing claims
orchestrator-re-verified: "wrong CalibStage…" + "State machine" strings present; `0x5a886c`=0.5; RTTI
`lt::BilateralUpsample<f,h>` present. **Two parked claims were WRONG and are corrected below.**

# Parked residuals — decoded (no longer punted)

## 1. Merge contributor-SELECTION gate `0x36930f` (the reducer's "N-accept" prong)
Per (contributor, output-position): contributor stride `rcx×640` (`leaq (rcx,rcx,4); shl $7`); pixel index
`= stride·row + col` (`0x3692f8 movl 0x28(rdi,rdx); imull r13d; addl r8d`); the contributor's index-map ptr
is field `+0x30` (`0x369306 movq 0x30(rdi,rdx),r12`), 8-byte entries `[int32 index, int32 paired]`.
**`0x36930f cmpl $0x80000000,%eax; jne 0x369320`** — if `indexmap[pos] == 0x80000000` (the "no-coverage"
sentinel) the (contributor,position) is SKIPPED (`jmp 0x369f0b`); else it is accepted and its `+4` paired
value + counts (`+0xe8`,`+0xd0`) are set up for accumulation. ⇒ **contributor c contributes to output pixel
p iff its index-map[p] ≠ 0x80000000.** This is the coverage/selection prong the `terminal_merge` REDUCER
VERDICT left OPEN — now decoded statically (the gate is a sentinel compare, not a score threshold).

## 2. Calibration State-machine driver `0x22f0f0` (next-state at `0x22f3fd`)
A **timed** state loop (constructs `std::string "State machine"`, wraps the body in mach_absolute_time →
ms via `×1000.0`/timebase). `this+0x6c` = current-state int; `this+0x58` = intrusive ordered tree of
per-state records (node key at `+0x20`, NOT libc++ `__tree`). Each iteration: completion predicate via the
`this+0x90` std::function (vtable+0x30 at `0x22f286`); if not done, descend the state tree to the current
state's node, load its **per-state action functor at node+0x50**, invoke it (vtable+0x30 at `0x22f3fd`), and
**store its int return to `[this+0x6c]` (`0x22f3ff`) = the next state.** ⇒ next-state is produced by calling
a **per-state functor**, not a switch/jump-table. **CORRECTION:** the parked claim conflated two vtable+0x30
calls — the next-state producer is node+0x50 (`0x22f3fd`); `0x22f286` is a separate completion predicate.
(Runtime-only: the concrete state-enum integer values + which functors register, bound at population time.)

## 3. Accepted-contributor → CalibStage bank store `0xf33d0`
`(rdi=State*, rsi=A, rdx=B, rcx=C, r8d=selector)`. **r8d==1 → CURRENT bank**, **r8d==0 → FACTORY bank**,
else throw `"wrong CalibStage, must be factory or current"` (string-confirmed). A and B are each a **36-byte
(9×4) block** (2× movups + trailing movl = 8 floats + 1 int); C = 3 separate 4-byte fields.
| field | current(r8d=1) | factory(r8d=0) |
|---|---|---|
| A[0..7]/A[8] | +0x12c / +0x14c | +0x180 / +0x1a0 |
| B[0..7]/B[8] | +0x150 / +0x170 | +0x1a4 / +0x1c4 |
| C0/C1/C2 | +0x174/+0x178/+0x17c | +0x1c8/+0x1cc/+0x1d0 |
Helper `0xf34e0` = the bank-base selector (`esi==1 ? +0x12c : +0x180`). Confirms the lane-D accept path
writes the accepted calibration into the current-vs-factory bank.

## 4. `0x1f0a00` — intrusive walk + per-record constructors (parked "RB-tree" = WRONG)
Walks an **intrusive list/threaded structure** (next-link `+0x10`, back-edge `(rbx)==rax` test, fixed
sentinel `this+0xb0`), selecting nodes with flag bytes `+0x1c8`≠0 && `+0x1c0`≠0. Per matched node it
constructs two heap records via shared_ptr: **`0x1f08a0` (operator new 0xe8)** — vtable'd, seeds two `1.0`
doubles at +0x90/+0xa8, `cvtps2pd` a float-pair→double2 from node+0xe0; and **`0x1f0530` (operator new
0x220)** — `cvtps2pd 0x28/0x30(%r12)` → +0x110/+0x120, int discriminator at `(%r12)`. **CORRECTION: NOT an
RB-tree/map** (no color byte, no __tree node layout — consistent with this binary's zero `__tree` symbols);
it is an intrusive walk promoting float32 geometry pairs → float64 calibration-math records.

## 5. Depth guided upsampler `0x29ed90` = `lt::BilateralUpsample<f,h>` (RTTI-confirmed)
RTTI present: `lt::BilateralUpsample<f,h>(lt::Image<f>&, Image<f> const&, Image<half> const&, f)` +
`BilateralUpsampleFromCollapse<2,f,vec4x8ui>`, tile-parallel (`std::function` over `lt::Rectangle<i>`).
Entry computes the **Gaussian range-weight coefficient `0.5/σ²`** (`movss [0x5a886c]=0.5; divss σ²`,
σ²=`mulss xmm1,xmm1`) and a small **`{1.0, 1/3}` tent spatial stencil** (`0x3f800000`/`0x3eaaaaab`), then
fans the kernel out per-tile. ⇒ a **joint-bilateral guided upsample** (range weight on the `half` guide ×
tent spatial) — the low-res-depth → full-res guided-by-image upsampler. (Runtime-only: the per-tile kernel
body — exact range form exp vs rational, neighbor footprint — is in the `0x5dcf40` lambda.)

## 6. `{flow_x, flow_y, score}` per-pixel store `0x369e7e/8b/91` (inside terminal merge `0x3661b0`)
Output image header at `[rbp-0x42f0]+[rbp-0x4300]`: stride `+0x58`, data ptr `+0x60`. Linear index
`stride·Y + X` (`imull r13d; addl r8d; cltq`), element = **×3 floats = 12-byte stride** (`leaq (rax,rax,2)`).
Stores `[idx*12+0]=flow_x` (`[rbp-0x4310]`), `[+4]=flow_y` (`[rbp-0x4320]`), `[+8]=score` (live xmm0). ⇒ a
per-output-pixel **3-channel {flow_x, flow_y, score}** record — the motion-vector + confidence map. (Runtime-
only: where fx/fy are produced + whether this map is consumed by the accumulator vs emitted as an aux buffer.)

## What this answers
These were findable static decodes, not blockers — parking them was a deferral. Decoding them advances the
merge SELECTION prong (#1), corrected two wrong claims (#2 conflation, #4 "RB-tree"), and read #3/#5/#6. **None
of this is "truth" — it is candidate disassembly at investigation-rigor, all `NEEDS_CODEX_VALIDATION`. The
orchestrator is not the verdict on truth; Codex validates.**

## CORRECTIONS + new candidate decodes (2nd pass, 2026-06-04) — and an OPEN contradiction
A second static pass (`decode-remainders`) refined items the first pass got wrong and surfaced a discrepancy
that proves these are candidates, not verdicts:
- **State machine `0x22f0f0` — RESOLVED (candidate); both prior passes were each HALF right.** RTTI-proven
  `lt::StateMachine<lt::CalibDataProcessor::State>` running inside `CalibDataProcessor::runReferenceGroupCams()`
  (typeinfo at `0x6675a0`; per-state functors `runReferenceGroupCams()::$_0..$_6` at `0x6583a0..`). The two
  passes described DIFFERENT co-existing fields of the same object — neither wrong: **`+0x58`** = root of an
  intrusive RB-tree `{state_int(+0x20) → node}`, node `+0x50` = per-state action functor `function<State()>`
  (Pass-1 ✓; the `node+0x50→vtable+0x30` call at `0x22f3fd` produces the next state → `[+0x6c]`); **`+0x90`** =
  the guard functor `function<bool()>` (Pass-2 ✓; `(*0x90)→vtable+0x30` at `0x22f286`, early-abort); **`+0xa0`**
  = the `std::vector<{state_int, elapsed_double}>` profiling log (Pass-2 ✓ but it MISLOCATED this at `+0x58` —
  the vector is `+0xa0`, distinct from the state tree at `+0x58`). `+0x68`=terminal state **9**, `+0x6c`=current
  (init **0**). **Live-adjudicated** (render `--profile 3`, BP set MODULE-RELATIVE): two State instances ran;
  state-int sequences `0→2→3→6→4→7→8→9` and `0→1→3→6→5→8→9`; the profiling vector grew **+1 per iteration**
  (confirms push-back log, not a tree walk); 14 distinct live action-functor VAs (`0x229df0..0x22e1d0`). Enum
  ints 0..9, terminal 9. **Action-functor semantics DECODED (candidate, static):** 13 distinct functor types
  ($_0..$_12, vtable blocks `0x6583a0` stride 0x80), each returns its next-state in `eax`. Roles: transition
  stubs (`0x229df0`→2, `0x22bdf0`→1, byte-verified `mov $imm,eax`); per-camera calib-record accumulators
  (`0x22a0e0`→3/6 calls the record-chain `0x23faf0`×2 + RB-tree insert, inits weight `0x58=1.0f`; `0x22c350`
  →3/6 on the `0x78` list); iterator/loop-control (`0x22a9b0`, `0x22cd00`); **geometry-apply** (`0x22aaf0`,
  `0x22d250` call the geometry builders `0x216f50`/`0x216eb0`/`0x216f60` with per-cam score `0x108`);
  mode/init (`0x229ec0`, `0x22bee0`); cleanup/finalize (`0x22ae60`, `0x22af80`, `0x22e1d0`). ⇒ the state
  machine IS the **per-camera calibration/geometry refinement loop** (accumulate records → apply geometry
  builders → finalize), driving the same `0x216f60`/`0x23faf0` kernels other lanes mapped. (Residual: the
  exact State-enum→vtable-index binding in `runReferenceGroupCams()`'s table init not yet disassembled.)
- **Folded-optics mirror model role DECODED (candidate, static).** `MirrorSysParam`/`MirrorActuatorMapping`
  (`ltpb.MirrorActuatorMapping` protobuf: `QuadraticModel` + `ActuatorAnglePair` + `actuator_angle_pair_vec`,
  strings confirmed) built by `0x1f0a00` are consumed in the **per-camera calibration/geometry path**:
  `0x1f0a00`'s callers `0x210ccb` (in `0x210c10`, reached from state functor `0x22bee0`) and `0x217145` (in
  the geometry builder `0x216f60`) both do `f3360`(cam handle)→`0x1f0a00`→`0x1c1860`→`0x1ed4d0` = a piecewise
  **actuator↔angle lookup** (sorted `vector<double>`, `ucomisd` threshold select) yielding a per-camera
  **mirror-deflection scalar** that feeds the geometry-record builders `0x216f60`/`0x218390`/`0x264440`. ⇒ the
  mirror model supplies per-camera ray geometry via mirror deflection (NOT a separate undistort LUT).
  (Residual: whether the deflection reaches per-pixel warp at render = geometry-record→pixel-warp, not traced.)
- **Flow `{fx,fy,score}` buffer (`0x369e7e`) — RESOLVED by render (candidate); the first pass was right, the
  second refuted.** Module-relative BP (nlocs=1, exact-pc stop, worker thread) under bridge profile-3/--no-lris:
  the store **FIRES**; the data ptr is loaded from the **object field `+0x60`** (`0x369e6d movq 0x60(%rcx,%rdx),
  %rcx`; runtime obj+0x60 == dataptr 0x7fbce0860640, in an 8 MB rw HEAP region — NOT rbp), so it writes a real
  **heap {flow_x,flow_y,score} map** (stride field `+0x58`=28; 12-byte/3-float records; first-hit fx=fy=19.2256,
  score=0). It is **read back**: intra-merge at `0x36a803`/`0x36a814` (`addss (%rbx,%rcx,4)` — the SAME
  weight/normalization block decoded in `merge_magnitudes` §1b, so the flow/score map FEEDS the per-contributor
  weighting) plus a `0x2ec6xx` weighted-accumulation consumer. ⇒ persistent heap flow/score map, written AND
  consumed in the bridge path; the prior "rbp stack-local / no reader" reading was wrong. (Residual: the score
  `+8` slot's specific reader and the `0x2ec6xx` consumer semantics not yet decoded — single 28mm U1 sample.)
- **CalibStage bank census (`0xf33d0`, 10 static call sites, r8d all immediate):** 9 sites pass **r8d=1 =
  current bank** (`+0x12c`); exactly ONE — `0x1f1328` — passes **r8d=0 = factory bank** (`+0x180`), immediately
  paired with a current read at `0x1f134b` (a factory-vs-current comparison in one function).
- **Merge `0x3661b0` is named `ImageResolutionAmp` / `processLevel0` (naming enrichment, NOT a contradiction).**
  A trace of `0x3661b0`'s only caller `0x365960` found it = `ImageResolutionAmp` (error string "ImageResolutionAmp
  did not create image of correct size!") inside `PipelineCache::processLevel0` ("Requested processLevel0
  before initResamp()!"), and read `0x3661b0`'s entry as a tiled ROI-resample — raising "is `0x3661b0` the
  merge or a resampler?" **Resolved deterministically:** `0x3661b0` (extent +0..+21155) **calls the score
  kernel `0x36cde0` at `+0x369e3f` (+15503) and computes 1/Σscore `rcpss 0x36a938` (+18312) IN-BODY** — it IS
  the score-weighted merge; the ROI rect is its per-tile (512×512) input and `ImageResolutionAmp` is the
  super-resolution-merge STAGE NAME. Its output is consumed by `0xd76a0` which **squares every channel**
  (`mulps %xmm0,%xmm0`) — a per-pixel energy/magnitude op downstream (candidate role).
- **METHOD CORRECTION (supersedes the "python callbacks drop hits" claim).** The earlier "L2-4=0 / gate2/3
  untriggered" 0-counts were a **breakpoint-binding artifact, not python**: BPs set on raw **file VAs** never
  bound through the ASLR slide (lldb "unresolved, hit count 0"). Set **module-relative** (`breakpoint set
  --shlib libcp.dylib --address 0xVA`), the same python in-frame callback captured all 40 loop iterations with
  ZERO drops. ⇒ the reusable lesson is **always set BPs module-relative so they bind through ASLR** — a raw
  `--address` on this PIE dylib silently fails and looks like "doesn't fire." Python-callback-vs-native is NOT
  the proven discriminator. (The positive corrections — L2-4 fires, gate2/3 fire, the native tallies — STAND;
  only their EXPLANATION changes from "python drops" to "earlier BPs were unbound.")
- **Bilateral kernel (real body `0x29f070`, NOT `0x5dcf40` which is `__const`):** range weight =
  **Gaussian `exp(−1.5·d²/σ²)`** via inline branchless `exp2f` (4th-order minimax `2^x` poly coeffs
  `0x5dae2c..` ≈ {0.078,0.226,0.696,0.99993}; `pslld $0x17` exponent pack; clamp ±126/128) — NOT a rational
  `1/(1+d²k)`. Bilinear-weighted taps, scale 1/3.
- **Flow producers (`0x369ce4/0x369cf8`, the store `0x369e7e` was the OUT not the producer):** {fx,fy} =
  **sub-pixel registration offsets from a 2×2 Cramer's-rule quadratic peak-fit** of the `0x36cde0` score
  field (validity-clamped to 0), ×tile-scale, then used as **Q16.16 (65536) warp coordinates** — registration
  vectors, NOT dense optical flow.
- **Flow buffer:** a **caller-provided output image** (assembled in caller `0x365960` at `0x365e9c`, passed as
  a pointer field into the single caller `0x365f4b`) — survives the call ⇒ consumed downstream (exact reader
  one frame up, not chased). Candidate, not confirmed.
- **`0xf33d0` (10 call sites):** A/B = 36-byte **9-field calibration-refinement blocks** (8 float + 1 int),
  C = 3 ints; representative caller `0x217bbe` passes `r8d=1` (current bank) after the accept gate (floor
  `0.25` + must-beat-incumbent × `0.8`). Not a full 3×3 CCM — per-camera refinement deltas.
- **`0x1f0a00` record identity (RTTI-resolved) — NEW:** the two records are
  **`std::shared_ptr<MirrorSysParam<double>>`** (0xe8) and **`std::shared_ptr<MirrorActuatorMapping<double>>`**
  (0x220, transform-type 1/2 else "Unrecognized Variable Transform Type!"). ⇒ the L16 **folded-optics
  moving-mirror system parameters + actuator-position→deflection mapping** — a calibration object class not
  previously surfaced (the L16 folded-optics moving-mirror calibration). Candidate; the mirror-model's role in
  the pipeline is still to decode (mine to do).
