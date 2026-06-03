# Lane A3 — src1/src2 cross-camera combine/store site

**Status:** `NEEDS_CODEX_VALIDATION` (nothing here is truth; Opus has no ledger authority).
**Blocker:** `CLM-PREFUSION-002` (the #1 WSJF parity blocker — pre-fusion src1/src2 merge/reduction mechanism).
**Branch:** `research/opus-quarantine-2026-06-02`. **Binary:** `libcp.dylib` sha256 `b38dc4b3…` (VA == file offset).

## One-line summary

OBSERVED-from-disasm + CANDIDATE: the IRAMP merge (`0x365960` → `0x3661b0`) iterates its
contributor vector in ONE outer loop (top `0x366b00`, induction `rbx`, back-branch `0x368bb5`,
trip = `(this->_vec18.end-begin)/16`) and every contributor **read-modify-writes the SAME
persistent accumulation buffer** (base = `-0x1710(%rbp)`, member-derived from `this->0x8`,
loop-invariant) via `addps (%rdx,%rcx,4); movaps %xmm1,(%rdx,%rcx,4)` at `0x369fa4/0x369fa8`.
This favors **H-REDUCE (true N→1 reduction)** over **H-MOSAIC (disjoint per-contributor tiles)**.

## The distinction this packet attacks

The entry-side input count is already proven four-zoom elsewhere (5-element contributor + 5-element
warp vectors, `lldb_iramp_entry_signature_four_zoom.md`). That proves 5 contributors are *passed in*.
It does NOT prove how they reduce to one output. This packet narrows that:

- **H-REDUCE** — all contributors accumulate into the same output elements (overlapping warped
  contributions summed). The merge is a real reduction.
- **H-MOSAIC** — each contributor writes a disjoint output region; "merge" is tiling/selection.

Static structure favors H-REDUCE (see `observations.md`). The unresolved ambiguity: the `addps`-RMW
proves the *capability* to sum overlapping contributions; it does NOT prove the per-contributor warp
offsets actually overlap at runtime. Only a runtime observation of one output element receiving writes
from ≥2 distinct contributors settles it. See `proof_or_disproof_plan.md`.

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
