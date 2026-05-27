# Quarantine Index

This folder is the boundary for contradictory, stale, partial, or over-broad material.

The goal is not to erase those docs. The goal is to stop them from silently outranking proof.

## Quarantine Rule

Anything listed here may be used only:

- for traceability
- for contradiction tracking
- for claim discovery

Anything listed here may not be used:

- as direct spec input
- as canonical truth
- as the final word on a merge-critical topic

## External Quarantine Targets

### AI-generated patent research intake

- `docs/quarantine/PATENT_RESEARCH_HANDOFF.md`
  User-provided, AI-generated patent research handoff. Generation provenance
  stated by the user: Google Gemini 3.1 Pro performed patent search; Claude
  Sonnet 4.6 analyzed the research report. Use only for claim discovery,
  verification planning, and contradiction tracking. It admits zero claims and
  may not be cited as project truth.

### Transient artifact references

- `/tmp/*` and `/private/tmp/*` references are never canonical evidence
  locations. If an older doc cites one, treat it as historical provenance only
  unless the verified facts are embedded in a repo proof doc or can be
  reproduced by a repo-local harness.

### Use only as contamination maps

- `/Volumes/Dev/lumen-phoenix-scratch/backward_audit_2026-04-16.md`
- `/Volumes/Dev/lumen-phoenix-scratch/critique_audit.md`

### Use only with claim-level filtering

- `/Volumes/Dev/lumen-phoenix-scratch/c6_destination_and_depthcache.md`
- `/Volumes/Dev/lumen-phoenix-scratch/depth_editor_and_iramp_depth.md`
- `/Volumes/Dev/lumen-phoenix-scratch/merge_canvas_writes.md`
- `/Volumes/Dev/lumen-phoenix-scratch/anchor_prefusion_and_c6.md`

### Quarantine specific conclusions

- `/Volumes/Dev/lumen-phoenix-scratch/merge_function_reconciliation.md`
  Keep its refutations of stale merge-site theories. Quarantine the stronger conclusion that the cross-camera merge does not live in `libcp`.

## Repo-Local Legacy Docs

The current repo-root `docs/TRUTH.md` is rebuilt from admitted claims and is not quarantined.

Superseded root-truth narratives are preserved by git history. Use `docs/canonical/TRUTH_RECONCILIATION.md` when you need the audit trail from the old v2 root truth into the current canonical structure.
