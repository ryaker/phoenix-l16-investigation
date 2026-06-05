# LRI Field Verifier Quarantine, 2026-06-05

These scripts were found as loose untracked files in `tools/` after the
Opus-quarantine validation checkpoint.

They are preserved here to avoid evidence loss, but they are not canonical
evidence and do not admit any claim into `docs/TRUTH.md` or
`docs/canonical/CLAIM_LEDGER.md`.

Use this folder as a holding area only:

- rerun a script against the real LRIs before citing its output;
- write durable accepted results under `docs/evidence/`;
- record broader audit status under `docs/audits/`;
- update the claim ledger only after independent reproduction;
- do not cite these scripts directly as proof of LRI field semantics.

## File Classification

- `block6_f28_decode.py` — candidate independent parser for one `28mm`
  block-6 spectral-field claim set; includes an explicitly interpretive
  non-verifiable lead.
- `focal_map_corpus_verify.py` — original candidate 8-seed focal-map verifier;
  appears superseded by the corrected v2 script below.
- `focal_map_corpus_verify2.py` — corrected candidate focal-map verifier with
  block-index/path corrections and one out-of-scope Unit-2 seed note.
- `focal_map_diag.py` — diagnostic exploration script, not a verifier to cite.
- `spectral_corpus_verify.py` — candidate spectral-block corpus verifier across
  Unit-1 and Unit-2 seed paths.
- `verify_block3_claims.py` — candidate one-seed block-3 calibration /
  distortion verifier for `2018-07-23/L16_02130.lri`.

## Current Status

Quarantined only. No script in this folder has been admitted as truth by this
quarantine move.
