# Lane A (quarantine) — static disassembly of the src1/src2 pre-fusion reducer

**Blocker:** `CLM-PREFUSION-002` (ledger status **OPEN / BLOCKER** — the #1 parity wall: the exact upstream
`src1`/`src2` merge/reduction math). **NOT solved by anyone**; this packet is independent quarantine
investigation, complementary to Codex's runtime-watchpoint frontier.

**Status of every claim here:** `NEEDS_CODEX_VALIDATION`. Method = `arch -x86_64 lldb --batch ...
disassemble` only (static, no runtime). Labels: **OBSERVED** = raw disasm re-extractable; **LEAD** =
inferred from structure. Nothing here is PROVEN. Scope-bound to static disasm of the named VAs.

Binary: `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
(Mach-O x86_64, `__TEXT` file-offset == VA).

## Why this is the right target (per Rich, 2026-06-03)
"Codex owns validation ... but that doesn't mean investigation into any corner is owned by Codex."
Investigation territory is not owned; only ledger validation is. The pre-fusion reducer is the highest
cost-of-delay OPEN item ⇒ top WSJF investigation target. Findings go to quarantine with weak labels;
Codex validates on return (2026-06-07).

## Findings (detail in `static_reducer_roles.md`)

1. **Arg correction (OBSERVED).** Sole caller `PipelineCache::processLevel0` at `0x3ec770`; sole
   `call 0x365960` at `0x3ec7da`. Arg loads `0x3ec7ac..`: `src1 = arg1 = cache+0x238`,
   `src2 = arg2 = cache+0x248`, scale `+0x1e8`, warpfield-vector `&cache+0x270` (arg3), source-image
   vector `&cache+0x258` (arg4), ROI/dest (arg5). ⇒ **src1/src2 are NOT the contributor/warp vectors**
   (those are separate cache-embedded args). Corrects the earlier Opus scaffolding.

2. **0x365960 = window-table + dispatch (OBSERVED).** Builds a `cosf` weight table from `scale`
   (`0x3659ed..0x365e1c`), packs args into a stack descriptor at `-0x158(rbp)`
   (`+0x08=src1, +0x10=src2, +0x18=warpvec, +0x20=srcvec, +0x38=output`), then `call 0x3661b0`.
   src1/src2 pass through untouched. All real work is in `0x3661b0`.

3. **Role asymmetry (LEAD).** In `0x3661b0` (r15=descriptor): **src1 (`0x8(r15)`)** = geometry anchor —
   per-pixel warped coords validated against src1 w/h `0x30/0x34(r13)` at `0x366c77`, output extent
   clamped by src1 dims at `0x36a004`. **src2 (`0x10(r15)`)** read once at `0x366915` to build a
   *separate* ROI box with a different kernel half-width (pad `0x8` vs src1 box pad `0x18`). Roles differ;
   src2 may be a lower-res / differently-padded source (LEAD).

4. **Reduction operator = weighted ADDITIVE accumulation (OBSERVED — strongest).** The N→1 pixel combine:
   ```
   0x369fa1  mulps  (%rdi), %xmm1        ; patch * separable weight
   0x369fa4  addps  (%rdx,%rcx,4), %xmm1 ; accumulate into output
   0x369fa8  movaps %xmm1, (%rdx,%rcx,4) ; store back to same buffer
   ```
   Accumulator base `-0x1710(rbp)`, zeroed once at `0x366356`, advanced at `0x36640c`. Exhaustive grep of
   the ~4000-insn body for select-style ops: **no `maxps/minps/blendvps/cmpps` in the pixel path** (only
   one unrelated `maxss` at `0x36a860` in post-loop bbox finalize). ⇒ static LEAD that the merge is
   **SUM, not select/max** — directly addresses the long-standing "sum-vs-select OPEN" question. Matches
   Codex's prior Hann-accumulator anchor at `0x369fa1` (`CLM-MERGE-002`).

## What remains UNKNOWN (do not overstate)
- **Which buffer feeds each accumulate** (src1 vs src2 vs a source-image-vector entry) is NOT established:
  the inner gather reads patch data from `-0x1770(rbp)` and warped coords from `-0x1740(rbp)`; their
  per-source assignment was not traced back. So "which source is summed each iteration" is OPEN.
- Whether **src2 supplies pixel values** to the accumulator or only geometry/ROI — UNKNOWN (its only
  observed deref is geometry).
- **N (number of sources summed)** is data-driven (`-0x1750`/`-0x1748` counts); whether N=5 contributor
  vector flows here is a LEAD only.
- Static only — additive path not confirmed executed for any specific zoom/LRI at runtime; alternate
  small-ROI fallback (`0x365f55`) and clamp branch (`0x36a01f`) not exercised.

## Next deterministic steps (WSJF, collision-tolerant)
- Trace `-0x1770(rbp)` (patch-source base) and `-0x1740(rbp)` (coord base) back to their per-iteration
  assignment in `0x3661b0` to resolve "which source feeds each accumulate." Pure static, high value.
- Decode the `0x366915` src2 ROI-box build to test the "src2 = lower-res second source" LEAD.
- Confirm vs Codex's runtime frontier on return (he can watchpoint the accumulator to settle SUM).
