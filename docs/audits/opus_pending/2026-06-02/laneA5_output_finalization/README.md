# Lane A5 — IRAMP post-merge output finalization (`0x3661b0` tail)

**Status:** `NEEDS_CODEX_VALIDATION`. **Branch:** `research/opus-quarantine-2026-06-02`.
**Binary:** `libcp.dylib` sha256 `b38dc4b3…` (VA == file offset).

## One-line summary

After the IRAMP merge tile-loops finish, the function tail `0x369ff2..0x36ae41` does **bounds-clamp →
edge-pad → cubic resample into the output**, NOT a quality/acceptance gate. Two derived views of the
merged buffer are **border-replicated** by `0x3750a0` (extend amount = 2 px), then **cubic-kernel
resampled** into the downstream image by `0x2b2be0` and its sibling `0x36f800` (separable cubic weight
LUT + recursive spatial-subdivision driver `0x5440`). The only rejection is a **degenerate-rect skip**
(`jle 0x36a15b` → zero-filled descriptor → no-op resample) when the clamped dst∩src is empty.

## Why this matters for the blockers

`CLM-MERGE-002`'s evidence explicitly leaves "final merge acceptance/rejection logic" open. This packet
is a bounded **negative-shaped** result for that question at THIS site: the post-merge finalization in
`0x3661b0` contains **no score/quality acceptance gate** — only geometric clamping and a degenerate-rect
skip. Any acceptance/rejection logic, if it exists, is NOT here; it would be upstream (the per-tile
contributor scoring of Lane A3) or in a different function. Scope-bound to `0x369ff2..0x36ae41`.

## Machine-verified anchors (deterministic — not LLM interpretation)

- **Edge-extend helper identity:** `strings libcp.dylib` contains `"Amount to extend must be positive"`,
  `"ROI must be within image!"`, `"ROI start must be non-negative!"` — the asserts inside `0x3750a0`.
- **Call sites (grep-confirmed VAs):** `0x36a072 callq 0x3750a0`, `0x36a08a callq 0x3750a0`,
  `0x36a200 callq 0x2b2be0`, `0x36a273 callq 0x36f800`.
- **Geometric gate:** `0x36a0eb jle 0x36a15b`, `0x36a0ef jle 0x36a15b` (degenerate-rect → zero-fill).
- **Resampler shape:** `0x2b2be0` has a 64-entry weight-LUT loop (`cmpq $0x40`), `__Znwm` functor
  alloc, and `callq 0x5440` (subdivision driver). `0x36f800` is its byte-sibling with different kernel
  constants.

## Files

- `observations.md` — step-by-step finalization with VAs; helper roles.
- `non_claims.md` — what is NOT established (the cubic-coefficient values, the runtime output identity).
- `commands.txt` — reproducible extraction + the deterministic `strings`/grep checks.
- `manifest.json` — machine-readable summary.

Raw dumps (gitignored `runs/laneA5_output_finalization/`): `finalization_369ff2.txt`,
`resampler_2b2be0.txt`.

## Discipline

LLM-read disasm interpretation is LEAD/CANDIDATE only; the `strings` asserts and grep-confirmed VAs are
deterministic. Does not touch any canonical doc. Consistent with PROVEN `CLM-MERGE-002` (see Lane A3's
`LEDGER_RECONCILIATION.md`): this is the resample-to-output stage after the weighted accumulator.
