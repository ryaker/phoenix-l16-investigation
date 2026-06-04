# Lane P residual — the 182 use a structurally different LELR layout

**Status:** `NEEDS_CODEX_VALIDATION`. Bounded structural characterization + one explicit HYPOTHESIS.
This does NOT assign the 182; it scopes WHY they can't be assigned by the current parser and what an
extended-parser effort would face. The integrity result (no third unit, `README.md`/`observations.md`)
is unaffected and already settled.

## OBSERVED (deterministic)

Comparing a representative unassigned file to an assigned one (first 32 header bytes + whole-file `LELR`
scan):

- **Assigned `L16_02130`** (`2018-07-23`): header `LELR`, `total_len@4 = 0x04d625ef = 81,143,279`;
  there IS a `LELR` magic at exactly offset `81,143,279`; **11** `LELR` blocks total (deterministic
  `scan_lri_blocks` re-count 2026-06-04 — corrects the earlier "12"; wide-tier=11, tele-tier=12); chain walks.
- **Unassigned `L16_00795`** (`2017-12-09`): header `LELR`, `total_len@4 = 0x05100020 = 84,934,688`
  (≈ half the 170,203,529-byte file); there is **no** `LELR` magic at `84,934,688`; **only 1 `LELR` in
  the entire file**. First block's `msg_len = 1497`, payload parses to no recognized proto fields.

So both are `LELR`-headed, but the unassigned file's first-block `total_len` does not point to a
subsequent `LELR` block — the multi-block chain that exposes the 16×field-13 intrinsics block in assigned
files is absent. (Class-wide: the 182 have 0–4 `LELR` blocks vs ~12 for assigned; see `observations.md`.)

## HYPOTHESIS (NOT asserted — needs verification)

The 182 may be a **different LRI container generation/firmware-format version**. Weak supporting signal:
the 4-byte ascii data tags differ by suffix between the two files (assigned: `*AD` family e.g.
`AXAD/DXAD/BTAD`; unassigned: `*AE`/`*QE` family e.g. `MTAE/UTAE/JPQE`). This is a **hypothesis only** —
the tags could be coincidental ascii in binary image data; their structural role was NOT verified. Per
discipline this is recorded as a hypothesis, not a finding.

## What an extended-parser assignment would require (scoping, not done)

To unit-assign the 182 one would have to reverse-engineer the alternate container layout: locate where
per-camera intrinsics calibration lives in these files (it is not a 16×field-13 LELR block), then hash it
and test against Unit-1 `722a6e72` / Unit-2 `223961c6`. This is a multi-step format RE task, deferred.

## Why this is not blocking

The merge/parity blockers do not depend on assigning these 182 (the canonical four-zoom seeds and their
Unit-2 twins are all assigned). The only open value is corpus-coverage completeness, and the integrity
question it could have threatened (a hidden third unit) is already deterministically closed in
`README.md`/`observations.md` (0/182 yield any signature under exhaustive magic-scan re-parse).
