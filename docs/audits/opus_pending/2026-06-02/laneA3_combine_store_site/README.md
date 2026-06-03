# Lane A3 — src1/src2 cross-camera combine/store site

**Status:** `NEEDS_CODEX_VALIDATION` (nothing here is truth; Opus has no ledger authority).
**Blocker:** `CLM-PREFUSION-002` (the #1 WSJF parity blocker — pre-fusion src1/src2 merge/reduction mechanism).
**Branch:** `research/opus-quarantine-2026-06-02`. **Binary:** `libcp.dylib` sha256 `b38dc4b3…` (VA == file offset).

## One-line summary

> ⚠ **See `CORRECTION.md`** — the first commit's mechanism narrative was self-caught as wrong and
> corrected. Read `observations.md` (corrected) and `CORRECTION.md` together; this summary is corrected.
> ⚠ **See `LEDGER_RECONCILIATION.md`** — this packet does NOT contradict the PROVEN `CLM-MERGE-002`
> accumulator claim; "cross-tile overlap-add, not cross-camera" is a placement note, not a denial of
> the ledger's "multi-source weighted accumulator." The ledger wins.

Machine-verified loop nest in `0x3661b0`: **tile-X `0x369140` → tile-Y `0x369160` → contributor loop
`0x3692f0..0x369f24` (sentinel-gated `0x80000000` per-tile coverage) → single Hann overlap-add
`0x369f80` into a shared, loop-invariant output base `-0x1710(%rbp)`** (3 accesses only). The
cross-camera combination happens **inside** the contributor-loop body `0x369320..0x369ec4` (one pass
per tile); the `addps/movaps` RMW is **cross-tile Hann overlap-add**, not cross-camera summation.
Whether the inner body **sums** valid contributors (H-REDUCE) or **selects** one (H-SELECT) is **OPEN**
and now localized to `0x369320..0x369ec4`.

## The distinction this packet attacks

The entry-side input count is already proven four-zoom elsewhere (5-element contributor + 5-element
warp vectors, `lldb_iramp_entry_signature_four_zoom.md`). That proves 5 contributors are *passed in*.
It does NOT prove how they reduce to one output. This packet localizes that to the per-tile inner body
`0x369320..0x369ec4` and reframes the open question:

- **H-REDUCE** — the inner body sums all valid (coverage-passing) contributors into the per-tile result.
- **H-SELECT** — the inner body selects one contributor (e.g. last/best valid) per tile.

This packet does NOT resolve H-REDUCE vs H-SELECT — the inner body was not traced. What it DOES
establish (machine-verified): the nest shape, the per-tile sentinel `0x80000000` coverage gate
(a tile-level acceptance mechanism), and the shared loop-invariant output base. See
`proof_or_disproof_plan.md` for the experiment that resolves sum-vs-select.

## FINAL frame (`step0_reconciliation.md`) — read this last

A pre-task check against Codex's committed `iramp_*` lane reframes and partly RETRACTS the sum-vs-select
question. `0x36cde0(-0x4240,-0x11a0)` returns a per-contributor **match SCORE** (Codex's
`bundle_lldb_iramp_36cde0_scalar.md`), so `-0x4240` is a compared patch, NOT a pixel accumulator. The
inner body emits a per-contributor `(flow_x, flow_y, score)` tuple; the real pixel reduction is
downstream and already traced by Codex as a **reciprocal-weighted add**
(`bundle_lldb_iramp_tuple_post_reciprocal_weighted_add.md`). **Converged answer:** the merge is a
score-weighted N→1 reduction (motion-aligned + quality-weighted), not a naive sum and not a hard select.
The `-0x4240` runtime watchpoint task is retracted. See `step0_reconciliation.md`.

## Step 0 update (`step0_inner_body.md`)

Tracing the inner body added a machine-verified mechanism finding and refined the open question:
- **NEW (deterministic):** the inner body does **per-contributor SAD block-match motion search**
  (`mpsadbw` ×16 + `phminposuw` argmin, `0x3694b1..0x369643`) — each contributor is aligned before
  combine. The merge is motion-compensated per contributor.
- **Confirmed:** the Hann accumulate `0x369f80` runs once per tile (after the contributor loop), reading
  per-contributor scratch `-0x4240` via `0x36e530`.
- **Still OPEN (sum vs select):** whether `-0x4240` is accumulated (H-REDUCE) or overwritten
  (H-SELECT, last-valid-wins) across contributors is **unresolved statically**; two automated traces
  erred on this loop re-entry, so the arbiter is a **runtime watchpoint** (see `step0_inner_body.md`).

## Files

- `observations.md`     — OBSERVED-from-disasm structure, exact VAs + quoted instruction lines.
- `non_claims.md`       — what this packet explicitly does NOT establish.
- `proof_or_disproof_plan.md` — the cheap runtime experiment Codex (or this branch, Codex offline) runs.
- `commands.txt`        — exact extraction commands (reproducible).
- `manifest.json`       — machine-readable summary.

## Discipline note

All VAs/instructions below are LLM-read from machine-extracted `otool` disasm. Per project rule,
LLM-read disassembly is **not fact** until independently re-extracted by Codex. Labels are
`OBSERVED-from-disasm` / `LEAD` / `CANDIDATE` only.
