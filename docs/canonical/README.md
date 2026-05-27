# Canonical Zone

This folder is the clean boundary for documentation that is allowed to drive:

- clean-room implementation
- parity validation
- merge-quality investigation
- future enhancement work

This folder exists because older root-truth narratives and the external scratch corpus contained contradiction drift, stale narrative, and tested-scope overclaims.

The current repo-root `docs/TRUTH.md` is the rebuilt human-readable entrypoint, synthesized from admitted claims only.

## Boundary Rule

Nothing enters `docs/canonical/` unless it satisfies all of the following:

1. The claim has a clear verdict:
   - `PROVEN`
   - `PARTIAL`
   - `OPEN`
   - `REFUTED`
   - `SUPERSEDED`
2. The scope is explicit:
   - exact binary or bundle
   - exact LRI(s) or corpus slice
   - exact profile or render path
   - exact zoom coverage: `28mm`, `35mm`, `70mm`, `150mm`
3. The evidence is named:
   - file path
   - VA / symbol / bytes / LLDB / trace
   - stable artifact location
4. The implementation consequence is explicit:
   - `SPEC_READY`
   - `BLOCKER`
   - `REFERENCE_ONLY`

Evidence may not depend on live `/tmp` or `/private/tmp` paths. If a historical
probe wrote raw output there, the canonical claim must rely on embedded packet
facts, a repo-local proof document, or a rerunnable repo-local probe harness.
Use `docs/audits/` for durable audit registers and `runs/<topic>/` for ignored,
rerunnable local outputs.

## Canonical Files

- `../TRUTH.md`
  Canonical root summary for humans. Git history carries superseded root-truth narratives.
- `CLAIM_LEDGER.md`
  Claim-by-claim authority. This is the primary source of truth for future docs.
- `TRUTH_RECONCILIATION.md`
  Audit note showing how the superseded v2 root truth was reconciled into the current canonical structure.
- `MERGE_CRITICAL_TRUTH.md`
  Narrow set of facts needed to achieve a ghost-free merge.
- `PARITY_BLOCKERS.md`
  Exact unknowns that still block a clean parity-grade Lumen replacement.
- `ENDGOAL_UNKNOWNS.md`
  End-goal-oriented map of what is still unknown, what is blocking, and what is not the current critical path.
- `BLOCKER_PATHS.md`
  Recorded investigation paths for resolving the current blocker set.
- `WSJF_PRIORITY.md`
  Planning-only prioritization of the current blocker set, including dependency-adjusted order and parallelization lanes.
- `LUMEN_PARITY_SPEC.md`
  Clean-room implementation spec. May only cite `SPEC_READY` claim IDs from the ledger.
- `PARITY_SPEC/`
  Section rules and templates for future spec chapters.
- `../audits/`
  Repo-owned home for durable audit registers and artifact-boundary notes.

## Four-Zoom Rule

No merge-critical topic is considered fully closed unless its zoom scope is explicit.

Every canonical claim must carry a verdict for:

- `28mm`
- `35mm`
- `70mm`
- `150mm`

Allowed per-zoom statuses:

- `VERIFIED`
- `VERIFIED_SAME_MECHANISM`
- `PARTIAL`
- `OPEN`
- `REFUTED`
- `N/A`

`N/A` is allowed only for claims that are truly zoom-irrelevant static facts, such as a binary constant or a helper's fixed instruction behavior.

## Precedence

Canonical precedence for new work:

1. `docs/canonical/CLAIM_LEDGER.md`
2. `docs/TRUTH.md`
3. other files in `docs/canonical/`
4. `docs/evidence/`
5. repo-root proof docs not yet migrated
6. `docs/quarantine/` and external scratch docs, claim-level only

## Historical Note

These root-level docs remain important inputs into the canonical system:

- `docs/LUMEN_APP_PROOF_ONLY_AUDIT.md`
- `docs/SCRATCH_CORPUS_CONTAMINATION_AUDIT.md`
- `docs/TECHDOC_ALIGNED_TRUTH.md`

The current `docs/TRUTH.md` is now rebuilt from the canonical zone.

Older root-truth narratives are preserved by git history, not by keeping stale truth in the main path.
