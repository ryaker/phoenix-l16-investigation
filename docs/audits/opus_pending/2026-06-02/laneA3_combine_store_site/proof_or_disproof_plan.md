# Lane A3 — Proof / disproof plan (CORRECTED)

> Superseded the original collision-counting plan (which assumed the wrong loop structure — see
> `CORRECTION.md`). The real open question is sum-vs-select inside the per-tile contributor body.

## Decisive question

Inside the per-tile contributor loop `0x3692f0..0x369f24`, for tiles where **≥2 contributors pass the
`0x80000000` coverage gate**, does the body **SUM** their contributions (H-REDUCE) or keep only **ONE**
(H-SELECT)?

## Step 0 — static (no render): trace the inner body `0x369320..0x369ec4`

Extract and read `0x369320..0x369ec4`. Look for:
- An accumulation into a per-tile working buffer that is **added** across contributor iterations
  (`addps`/`addss` into the same stack/temp slot keyed by position, not by contributor) ⇒ H-REDUCE.
- A plain overwrite / `cmov`/max-select / last-writer-wins into that slot ⇒ H-SELECT.
- The role of `0x369ed0 movabsq $0x8000000080000000 ; movq %rax,(%r12,%rcx,8)` (writes a sentinel pair)
  and the `(%r12,%rsi,8)` map — is the per-tile temp indexed by output position (shared across
  contributors → can accumulate) or by contributor (disjoint → cannot)?

This may resolve the question without a render. Do it first.

## Step 1 — runtime confirmation (render; Codex offline only; sequential)

If static is ambiguous, instrument at runtime:
- Break at `0x36930f` (the coverage compare) or `0x369314`; per tile, count how many contributors pass
  the gate (`eax != 0x80000000`). Confirms multi-contributor tiles exist (expected near image center).
- Break at the inner accumulation site found in Step 0; on a chosen multi-contributor tile, read the
  per-tile temp slot **before vs after** each valid contributor. Monotonic add across ≥2 contributors
  ⇒ H-REDUCE; single change then stable ⇒ H-SELECT.
- Auto-continue + Python tally; early-terminate once one multi-contributor tile is fully characterized.

### Scope discipline
- Four-zoom (28/35/70/150mm Unit-1 seeds); merge topology is zoom-bound.
- Renders sequential only (documented 150mm thread-timing crash); only while Codex confirmed offline.
- Report scope-bound: "OBSERVED on tested tiles," never "all pixels / NEVER."
- Resolving sum-vs-select does NOT alone close `CLM-PREFUSION-002` (semantic src1/src2 payload + the
  full acceptance/rejection surface remain separate open items).

## Disjointness from Codex's live thread

This stays on the IRAMP accumulator VAs (`0x3661b0` interior: `0x3692f0`, `0x369320`, `0x369f80`). It
must NOT instrument the `0x23c5f0`/`0x23faf0` State-helper chain of Codex's uncommitted
`state_helper_23faf0_record_chain` thread. Disjoint VAs by construction.
