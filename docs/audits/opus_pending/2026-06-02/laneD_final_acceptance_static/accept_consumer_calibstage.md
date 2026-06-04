<!-- provenance: orchestrator static disasm of 0xf33d0, 2026-06-03 -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, static disasm; orchestrator re-extracted directly).

# Lane D — what ACCEPT does: 0xf33d0 = CalibStage writer (acceptance = a CALIBRATION update)

## OBSERVED (disasm of 0xf33d0, the accept-path consumer)
`0xf33d0(rdi=State, rsi, rdx, rcx, r8d=stage)` copies **three records** into the State object. Each source
(rsi, rdx, rcx) supplies a 36-byte record = `movups (src)` + `movups 0x10(src)` (two 16-byte vec4s) +
`movl 0x20(src)` (one int). `r8d` selects which field bank:
- **r8d==0 (CalibStage "factory")** → State `+0x180/+0x190/+0x1a0`, `+0x1a4/+0x1b4/+0x1c4`, `+0x1c8/+0x1cc/+0x1d0`.
- **r8d==1 (CalibStage "current")** → State `+0x12c/+0x13c/+0x14c`, `+0x150/+0x160/+0x170`, `+0x174/+0x178/+0x17c`.
- else → throws **"wrong CalibStage, must be factory or current"** (string @ `0xf34ac`, +44 bytes).

So the accept body writes the accepted candidate's **3-part calibration/transform** (2×vec4 + int each)
into the State's **current** (or factory) **CalibStage** bank.

## Interpretation (reframes the 0x216f60 cluster)
**Acceptance = a per-render CALIBRATION / ALIGNMENT UPDATE, NOT inclusion in the pixel merge.** The
`0x216f60` / `0x218b30` / `0x218e20` / `0x23faf0` cluster is the **per-render calibration-candidate
refinement subsystem** (`CalibDataProcessor::State`): build alignment candidates (geometry/transform
records) → parallel-score per-pair (`0x218b30` mean-score + threshold-exceed fraction) → argmax → accept/
reject gate (`0x217ab9`, **reject if exceed-fraction > 0.25** + 2 more gates) → on accept, `0xf33d0` writes
the winning candidate into the State's current CalibStage. The **pixel merge** (`0x3661b0`, level 0) is a
SEPARATE downstream subsystem that CONSUMES the resulting calibration/warp.

This cleanly separates the two subsystems that earlier packets partly conflated:
- **Calibration/alignment refinement** = the `0x23faf0`/`0x216f60` State cluster (this lane).
- **Pixel N→1 merge** = IRAMP `0x3661b0` (laneA / MERGE_MECHANISM_SYNTHESIS).

## Clean-room relevance
The "factory" vs "current" CalibStage split = the LRI's baked factory calibration vs a per-render refined
calibration. Phoenix's parser already has the factory calibration (LRI Block 3/6); the "current" stage is
a runtime per-render refinement of it, gated by the 0.25 exceed-fraction ceiling.

## Open
- The exact meaning of the 3 records (2×vec4+int) — a 3-row transform? per-axis alignment? (LEAD).
- The factory(0)/current(1) tag is named from the string; not traced to who reads each bank downstream.
- Whether the pixel merge reads the "current" CalibStage (the link calib→merge) — not yet traced.
