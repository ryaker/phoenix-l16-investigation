# Opus Quarantine Research — 2026-06-02

**Role:** Opus acts ONLY as a quarantine research manager. It has NO authority over truth.
**Branch:** `research/opus-quarantine-2026-06-02` (isolated git worktree at `/Volumes/Dev/L16-opus-quarantine`).
**Validator:** Codex. Nothing here is truth until Codex independently re-runs/re-extracts and integrates.

## Hard rules (every packet, every subagent)

1. **Do NOT modify any canonical / truth doc.** Off-limits: `docs/TRUTH.md`,
   `docs/canonical/CLAIM_LEDGER.md`, `docs/canonical/PARITY_BLOCKERS.md`,
   `docs/canonical/WSJF_PRIORITY.md`, `docs/canonical/MERGE_CRITICAL_TRUTH.md`,
   `docs/canonical/BLOCKER_PATHS.md`, `docs/canonical/ENDGOAL_UNKNOWNS.md`, `docs/evidence/INDEX.md`.
   (This branch was cut from committed `dbf9a04`; Codex's in-progress canonical edits live only in the
   main worktree and must never be touched from here.)
2. **Weak language only.** Use `OBSERVED`, `LEAD`, `CANDIDATE`, `NEEDS_CODEX_VALIDATION`.
   NEVER use `PROVEN`, `TRUTH`, `RESOLVED`, `CLOSED`, `UNBLOCKED`, `VERIFIED` for findings.
3. **No cross-citation of unvetted work.** One packet may not cite another Opus packet as fact.
4. **Reproducible or it doesn't exist.** Every packet ships exact commands, exact paths, and raw output
   locations so Codex can re-run from scratch.
5. **Investigation only.** Real Lumen binary / LRI bytes / LLDB traces. No spike code, no spike outputs.
6. **Renders are sequential.** Never run two instrumented `libcp` renders concurrently (thread-timing
   race; documented 150mm crash). Only run renders while Codex is confirmed offline.
7. Commit to this quarantine branch only. Never push to `main`. Never `git add` from the main worktree.

## Packet layout

```
docs/audits/opus_pending/2026-06-02/<topic>/
  README.md                 # what this packet is, status label, one-line summary
  manifest.json             # topic, lane, binaries+SHAs, LRIs used, status, created
  commands.txt              # exact commands run (copy-paste reproducible)
  observations.md           # OBSERVED facts only, scope-bound, with verbatim excerpts
  non_claims.md             # what this packet does NOT establish (explicit)
  proof_or_disproof_plan.md # the experiment Codex should run to validate/refute
tools/lldb_probes/opus_pending/<topic>/   # probe scripts (.lldb / .py / run_*.sh)
runs/<topic>/                              # raw outputs (gitignored; reproducible)
```

## Status vocabulary (per packet)

- `OBSERVED` — directly seen in a deterministic run (byte-search, disasm, register read). Still
  needs Codex re-extraction before it is fact.
- `LEAD` — a plausible direction with partial support; not yet observed end-to-end.
- `CANDIDATE` — a specific VA/structure proposed as the answer, unconfirmed.
- `NEEDS_CODEX_VALIDATION` — terminal state for every packet: hand-off marker.

## Lanes this campaign

- **Lane A1** — post-node consumers: `0x23c5f0 → 0x23faf0 → local tree node` outputs after `0x23d025`;
  who reads node `+0x28..+0xa0`.
- **Lane A2** — reducer/body search: consumers of those derived records; look for image/source effect,
  do NOT assume an N-to-1 reducer exists.
- **Lane B** — corpus validation: repeat key four-zoom probes on **Unit-2 twins only**, keeping Unit-1
  vs Unit-2 strictly separated. (Renders — sequential.)
- **Lane C** — C6 tele odd-camera: alias/filter/terminal-route proof; bounded observations only.
- **Contamination audit** — final pass: scan all packets for overclaims / banned language / cross-citation.

## Verified environment (2026-06-02)

- `lri_process`: `/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lri_process` (Mach-O x86_64)
- `libcp.dylib`: `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- LRIs: `/Volumes/Base Photos/Light/<date>/<name>.lri` (external volume — confirm mounted).
- Two physical units by intrinsics calib SHA-256: Unit-1 `722a6e72…`, Unit-2 `223961c6…`.
  Unit-2 four-zoom twins: 28mm `2018-07-04/L16_02130`, 35mm `2018-10-28/L16_03041`,
  70mm `2020-07-14/L16_03434`, 150mm `2018-07-07/L16_02285`.
</content>
