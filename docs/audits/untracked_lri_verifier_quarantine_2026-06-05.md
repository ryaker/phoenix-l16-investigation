# Untracked LRI Verifier Quarantine, 2026-06-05

## Scope

After committing `6d2c5a2 Validate index-5 origin classification`, six loose
untracked Python scripts remained under `tools/`.

Codex inspected the file headers and representative bodies, classified them as
LRI/protobuf claim-verification or diagnostic utilities, and moved them into:

`tools/quarantine/lri_field_verifiers_2026-06-05/`

This cleanup preserves possible deterministic repro value while preventing
untracked scratch from being mistaken for admitted evidence.

## Quarantined Files

- `block6_f28_decode.py`
- `focal_map_corpus_verify.py`
- `focal_map_corpus_verify2.py`
- `focal_map_diag.py`
- `spectral_corpus_verify.py`
- `verify_block3_claims.py`

## Admission Boundary

This audit action admits no new LRI field semantics.

The scripts may contain useful candidate checks, corrections, diagnostics, or
stale claims. Their output is not canonical unless a later validation reruns the
script or independently reimplements the check against the real LRIs, writes a
durable evidence document under `docs/evidence/`, and updates
`docs/canonical/CLAIM_LEDGER.md`.

## Initial Classification

- `block6_f28_decode.py`: candidate spectral-field parser for the canonical
  `28mm` seed; one listed claim is explicitly interpretive / non-verifiable by
  parse alone.
- `focal_map_corpus_verify.py`: likely superseded first pass. It carries claim
  paths later corrected by `focal_map_corpus_verify2.py`.
- `focal_map_corpus_verify2.py`: corrected candidate focal-map verifier. It is
  still not evidence until rerun and reviewed.
- `focal_map_diag.py`: diagnostic script, not a proof artifact.
- `spectral_corpus_verify.py`: candidate spectral-block corpus verifier across
  Unit-1 and Unit-2 seed paths.
- `verify_block3_claims.py`: candidate one-seed block-3 calibration /
  distortion verifier.

## Next Validation Path

When these candidates become relevant to a blocker, validate them like any
other Opus/quarantine material:

1. Rerun the candidate against the real LRI paths.
2. Save raw outputs under ignored `runs/<topic>/`.
3. Independently inspect or reimplement any load-bearing parse.
4. Promote only reproduced facts into `docs/evidence/`.
5. Update the claim ledger only from admitted evidence.
