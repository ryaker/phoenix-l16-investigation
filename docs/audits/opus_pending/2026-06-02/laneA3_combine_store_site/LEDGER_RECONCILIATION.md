# Lane A3 — reconciliation with the ledger (authority)

**Authority rule (CLAUDE.md):** if any doc disagrees with `docs/canonical/CLAIM_LEDGER.md`, the ledger
wins. This note ensures nothing in the Lane A3 packet is read as contradicting the ledger.

## CLM-MERGE-002 (PROVEN / SPEC_READY) vs this packet

The ledger row `CLM-MERGE-002` (four-zoom `VERIFIED`, `PROVEN`, `SPEC_READY`) states: *"IRAMP contains a
real multi-source weighted accumulator in `libcp`, with the accumulator at `0x369fa1..0x369fa8`."*
Evidence: `docs/evidence/lldb_iramp_wrapper_accumulator_four_zoom.md`.

That evidence is explicitly scope-bounded. It proves **four-zoom runtime participation** of the
weighted accumulator instruction `0x369fa1`, and it **explicitly disclaims**:
- "does not prove the exact pre-fusion merge/reduction mechanism behind `src1`/`src2`,"
- "does not prove final merge acceptance/rejection logic,"
- "does not prove that the captured `rbp-0xa0` stack window is a closed-form weight formula."

## How this packet relates (no contradiction)

This packet's claims about `0x369fa1..0x369fa8` are **consistent** with CLM-MERGE-002:
- Both agree `0x369fa1..0x369fa8` is a **weighted accumulator** (this packet identifies the weights as
  the 16×16 separable Hann window at `rbp-0xa0`; the ledger records the stack window as observed bytes,
  not a proven closed-form — so the Hann identification remains a quarantine LEAD, not a strengthening
  of the ledger).
- Neither claims `0x369fa1` is the cross-camera `src1`/`src2` reducer. This packet's phrase
  "cross-tile overlap-add, **not** cross-camera summation" is a *placement* observation (the accumulate
  runs once per tile after the contributor loop), NOT a denial of the ledger's "multi-source weighted
  accumulator" label. "Multi-source" is satisfied because the per-tile source `-0x4240` is itself the
  combined product of multiple contributors (contributor loop + downstream reciprocal-weighted add).

## Corrections to avoid over-reading this packet

- Do **not** read Lane A3 as weakening or contradicting CLM-MERGE-002. It does neither.
- The Hann-window weight identification is a quarantine LEAD; the ledger deliberately keeps the weight
  window as observed bytes. Do not promote "Hann" into the ledger from this packet.
- The src1/src2 reduction characterization (score-weighted, reciprocal-weighted add) targets the
  still-OPEN `CLM-PREFUSION-002`, and remains `NEEDS_CODEX_VALIDATION` — it does not touch the already
  PROVEN CLM-MERGE-002 accumulator-participation claim.
