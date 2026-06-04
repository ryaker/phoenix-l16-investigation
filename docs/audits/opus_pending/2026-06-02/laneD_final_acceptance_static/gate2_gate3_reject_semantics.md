<!-- provenance: orchestrator static disasm of libcp.dylib 0x216f60 accept-gate, region 0x217a40..0x217b20, 2026-06-03 -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, STATIC disasm; gate1 separately OBSERVED live in
`accept_reject_gate_located.md`; gate2/gate3 were "present but untriggered" at runtime — now characterized
statically). Binary: `libcp.dylib` (Mach-O x86_64, __TEXT fileVA==offset).

# Lane D — accept/reject gate2 + gate3 reject semantics (the CalibDataProcessor::State acceptance triad)

Advances `accept_reject_gate_located.md`: that packet proved **gate1** live (0.25 ceiling) but left gate2 and
gate3 "present but untriggered this run." Static disasm of `0x217a68..0x217af9` now decodes all three. The
acceptance test is a TRIAD: one ABSOLUTE quality floor + two MUST-BEAT-REFERENCE comparisons.

## Two arrays + a reference index (decoded from the disasm)
- **Array A** = primary per-candidate SCORE array, `[rbp-0x3f0]` (begin) .. `[rbp-0x3e8]` (end); element = f32.
  **Lower A = better** (the selector takes the argMIN, below).
- **Array B** = per-candidate THRESHOLD-EXCEED-FRACTION array, base `[rbp-0x410]`; element = f32. (This is the
  fraction whose 0.25 ceiling is gate1.)
- **`ebx` = reference/incumbent candidate index** into A and B (the thing the winner must beat). Nearest defs
  reaching the gate: `0x21765d mov ebx,r15d`, with loop-body candidates `0x217451 lea ebx,[r13+r13]` (=2·r13)
  and `0x217583 lea ebx,[r12+r12+1]` (=2·r12+1). Exact CFG-selected provenance = residual (needs full
  candidate-build CFG trace); the gate *uses* B[ebx]/A[ebx] as the incumbent baseline.
- **`r12d` (gate3 guard)** = `[rbp-0x60c]`, stored from a candidate-count r12d at `0x2173fe`.

## Selector = argMIN of A (0x217a68..0x217aa4)
Walks A; `0x217a9d ucomiss xmm0,[rcx]; 0x217aa0 jae (keep)` ⇒ tracks the **smallest** A element. `rcx` ends at
the min-A pointer; `sub rcx,rax` → byte offset; `>>2` → **selected index** = argMIN_A. (rdx holds 4·selected
as a byte offset for A/B indexing.) ⇒ **the selected candidate is the lowest-score one**, then it must pass:

## GATE 1 — absolute ceiling on exceed-fraction (0x217ab9..0x217ac9) [matches live finding]
```
movss xmm0,[rsi+rdx]      ; xmm0 = B[selected]
movss xmm1,[0x5a8200]     ; 0.25 (confirmed: bytes @0x5a8200 = 0.25f)
ucomiss xmm1,xmm0 ; jb 0x217bf8(REJECT)   ; REJECT if 0.25 < B[selected]
```
⇒ **REJECT when B[selected] > 0.25** (absolute disagreement ceiling). Consistent with the OBSERVED 70mm run
(5 rejected frac>0.25 / 3 accepted ≤0.25).

## GATE 2 — winner must be no worse than incumbent on exceed-fraction (0x217acf..0x217ad6) [NEW]
```
movsxd rdx,ebx            ; rdx = reference index ebx
ucomiss xmm0,[rsi+4*rdx]  ; xmm0 (=B[selected]) vs B[ebx]
ja 0x217bf8(REJECT)       ; REJECT if B[selected] > B[ebx]
```
⇒ **REJECT when B[selected] > B[ebx]** — the selected candidate's exceed-fraction must be ≤ the
reference/incumbent's. A RELATIVE gate (no constant).

## GATE 3 — winner must beat incumbent score by ≥20% (0x217ae3..0x217af9) [NEW]
```
test r12d,r12d ; jle 0x217aff      ; SKIP gate3 if guard r12d <= 0
movss xmm0,[rax+4*rdx]             ; A[ebx]  (rdx still = ref index ebx)
mulss xmm0,[0x5d5350]              ; * 0.8   (confirmed: bytes @0x5d5350 = 0.8f)
ucomiss xmm0,[rax+4*rcx]           ; 0.8*A[ebx]  vs  A[selected]  (rcx = selected index)
jb 0x217bf8(REJECT)                ; REJECT if 0.8*A[ebx] < A[selected]
```
⇒ **REJECT when A[selected] > 0.8 · A[ebx]** — since lower-A is better, the winner's score must be at most 80%
of the incumbent's, i.e. a **≥20% improvement** over the reference. Guarded: only enforced when `r12d>0`
(a positive candidate-count). A RELATIVE gate with a 0.8 margin constant.

## Acceptance (fall-through 0x217aff+) and clean-room meaning
Pass all three ⇒ load the winning candidate's record: `rax=[rbp-0x430]`, `rcx=3*selected` (`lea rcx,[rcx+2*rcx]`),
read `movsd [rax+8*rcx]` (double) + two `movss` at `+0x8`/`+0xc` ⇒ 24-byte records, fed to the `0xf33d0`
CalibStage writer (see `accept_reject_gate_located.md`).

**Clean-room reimplementation of the accept rule (reimplemented algorithm, not copied bytes — Rule #0 OK):**
> select the candidate with the lowest score A; accept the per-render calibration update **iff**
> `B[sel] ≤ 0.25` **AND** `B[sel] ≤ B[incumbent]` **AND** (`no prior candidates` **OR** `A[sel] ≤ 0.8·A[incumbent]`).
This is "absolute-quality floor + must-clearly-beat-the-incumbent," confirming the de-conflation thesis:
acceptance = a conservative per-render CALIBRATION UPDATE (only when distinctly better than factory/current),
NOT pixel-merge inclusion. Constants 0.25 and 0.8 are libcp's; a clean-room impl derives/justifies its own
thresholds rather than copying these two floats.

## Residuals (NEEDS_CODEX_VALIDATION)
- Exact CFG-selected definition of `ebx` (incumbent index) reaching the gate — 3 candidate defs listed above.
- Whether `r12d` guard means "≥1 prior accepted candidate" vs "≥1 candidate of a class" — count provenance at
  `0x2173fe` not fully traced.
- gate2/gate3 still UNTRIGGERED at runtime (only gate1 fired in the 70mm run); static-only for gate2/gate3.
- Meaning of the 3-field 24-byte winning record (1 double + 2 float) — likely (score, 2× transform params).
