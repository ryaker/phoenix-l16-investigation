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
- **⚠ OPEN CONTRADICTION — State machine `0x22f0f0` structure.** Pass-1 (#2 above) read the next-state functor
  at tree-node `+0x50` (`0x22f3fd`). Pass-2 reads the current functor at **`this+0x90`** (invoked
  `(*0x90)→vtable+0x30`), with `+0x6c`=current-state int, `+0x68`=terminal, and `+0x58`/`+0xa0` a
  `std::vector<{state_int, elapsed_double}>` PROFILING log (the "tree insert" = its push_back grow), plus an
  "state function has not been registered" throw. **The two passes disagree on the functor location and on
  whether `+0x58` is a functor tree or a profiling vector. NOT resolved by these two static passes — I am
  resolving it now (decode the State registration/construction + a live state-sequence trace), not leaving
  it.** Both agree the next-state binding is populated at State construction time.
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
