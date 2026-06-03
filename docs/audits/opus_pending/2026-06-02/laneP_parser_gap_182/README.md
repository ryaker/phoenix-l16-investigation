# Lane P — the 182 unassigned LRIs (parser-gap characterization)

**Status:** `NEEDS_CODEX_VALIDATION`. Deterministic data analysis (no disasm, no render).
**Branch:** `research/opus-quarantine-2026-06-02`. Corpus: `/Volumes/Base Photos/Light/*/*.lri` (9390 files).

## Question

The two-unit corpus proof (`docs/evidence/bundle_proof_two_unit_corpus_static.md`) assigns each LRI to a
unit by the SHA-256 of its 16-camera intrinsics block (the LELR block with exactly 16 field-13 records);
**182 files were unassigned** ("no parseable intrinsics block"). Rich's no-assumptions rule: do those 182
hide a **third unit**, or otherwise threaten "exactly two units, no third"?

## Answer (deterministic)

**No third unit. The two-unit claim is not threatened by the 182.** Even an exhaustive `LELR`-magic-scan
re-parse (parsing *every* block in each file, not just the cleanly-walked ones) assigns **0 of 182** and
surfaces **0 third signatures**. None of the 182 contains a 16×field-13 intrinsics block in any
parseable form, so none yields any calibration signature at all. The gap is **structural/format**, not a
distinct camera.

## What the 182 actually are (machine-verified)

- **4 files:** zero `LELR` blocks (truncated / non-LELR / unreadable as a block container).
- **178 files:** 1–4 `LELR` blocks, but **none** is the 16-camera intrinsics block. (Assigned files have
  ~12 blocks — e.g. `L16_02130` has 12 `LELR` blocks that chain cleanly.)
- **Mechanism split of the 182:**
  - **90 = parser walk terminated early** (raw `LELR` magic count > blocks the `total_len`-chained
    walker found; e.g. `L16_00101`: 6 magics, 3 walked). A robustness gap — BUT the extra blocks reached
    by magic-scan still contain no 16×field-13 intrinsics, so even a fixed walker would not assign them.
  - **92 = walker found all present blocks** (magic count == walked, incl. the 4 zero-block files), so
    these genuinely have few blocks and no intrinsics block.
- **Verified example:** `2017-12-09/L16_00795.lri` is a 170 MB full-size capture with **exactly one
  `LELR` occurrence in the entire file**; its single 1497-byte block payload parses to **no** recognized
  proto fields. A genuinely different/reduced container layout, not a truncation.
- **Date spread:** 2017-12 … 2021-03 (94 in 2018, 68 in 2019) — **not** an early-firmware-only artifact.

## Why it matters

Completes the open completeness caveat on the two-unit corpus: the 182 unassigned are a **format/parser
coverage gap, deterministically shown to contain no third-unit signature.** Universality claims that rely
on "exactly two units" are not undermined by the unassigned set.

## Open (not closed here)

These 182 cannot be unit-fingerprinted by the field-13 intrinsics method. Whether they carry per-camera
calibration under a *different* proto field/structure (and could be assigned by an extended parser) is
NOT resolved — but that is an assignment-coverage question, not a third-unit risk. See `non_claims.md`.

## Files

- `characterize_unassigned.py` — identifies the 182 + record-count/signature/date histograms.
- `observations.md` — the deterministic numbers + the robust re-parse result.
- `non_claims.md` — what is NOT established.
- `commands.txt` — exact reproduction.
Raw reports (gitignored `runs/laneP_parser_gap_182/`): `characterize_report.txt`.
