# Evidence: Two-Unit Corpus Identification (Static, Per-File, Machine-Verified)

**Date:** 2026-05-30
**Status:** VERIFIED (deterministic per-file byte facts).
**Scope:** Full `/Volumes/Base Photos/Light/*/*.lri` corpus. Static only — intrinsics calibration-block
SHA-256 per file via `tools/lri_field_inspect.py`. No render, no lldb.
**Method note:** The corpus is organized by **shot date**, NOT by unit (per Rich). So units cannot be
inferred from folders — each LRI was hashed individually; the distinct hashes ARE the units. Reproduced
in local ignored script `runs/two_unit_corpus/per_file_unit_partition.py`.

## FACT 1 — Exactly two physical units (per-file calibration SHA-256)

Hashing the intrinsics calibration block (16 per-camera records) of **every** LRI:

| Unit signature (intrinsics sha256, first 16) | files |
|---|---|
| `722a6e721636c9c4` (Unit-1) | 5724 |
| `223961c6bce6153e` (Unit-2) | 3484 |

Total scanned: 9390. Exactly two distinct signatures — no third. (182 files had no parseable intrinsics
block under the current parser and are unassigned; see caveat.)

## FACT 2 — Folders are date-organized, not unit-organized (13 mixed folders)

**13 date-folders contain BOTH units' files** — direct proof that organization is by shot date, not by
camera. These are the days both cameras were used:

```
2018-01-29, 2018-01-30, 2018-02-01, 2018-02-05, 2018-02-12, 2018-02-20,
2018-03-01, 2018-05-03, 2018-07-04, 2018-07-07, 2018-07-26, 2018-10-12, 2018-10-24
```

This is exactly the structure Rich described: two cameras, same per-camera filename counter, files landed
in date folders — so the same filename recurs on different dates (different bodies), and some single dates
hold both bodies' captures. Unit identity therefore must come from the per-file calibration hash, never
from the folder.

## FACT 3 — All four canonical seeds are Unit-1; their same-name twins are Unit-2

Independently verified earlier (`runs/two_unit_corpus/twin_compare.py`) and consistent with the
partition. Each canonical seed has a same-name, same-focal-length twin on a different date that belongs to
the **other** unit:

| name | focal | Unit-1 (`722a6e72`) | Unit-2 (`223961c6`) |
|---|---|---|---|
| L16_02130 | 28mm  | 2018-07-23 | 2018-07-04 |
| L16_03041 | 35mm  | 2018-12-26 | 2018-10-28 |
| L16_03434 | 70mm  | 2019-05-18 | 2020-07-14 |
| L16_02285 | 150mm | 2018-07-29 | 2018-07-07 |

All four twin pairs had differing calibration hashes (SAME=False). These eight files are the **true
cross-unit four-zoom test set**: Unit-1 four-zoom AND Unit-2 four-zoom = the real unit-invariance test.

## FACT 4 — Independent corroboration: per-unit filename sequence is monotonic by date

A **second, independent** confirmation of the partition, using a different data source than the
calibration hash: the LRI filename number (`L16_NNNNN`). Each physical camera has its own capture counter
that ticks up over time, so within one unit the filename number should rise with shot date, and the two
units' counters should be independent of each other. Both predictions hold
(`runs/two_unit_corpus/unit_sequence_monotonicity.py`):

| Unit | files | filename-number monotonic by date |
|---|---|---|
| `722a6e72` | 5724 | **99.91%** (5718 increasing, 5 decreasing) |
| `223961c6` | 3484 | **99.83%** (3477 increasing, 6 decreasing) |

- `722a6e72` runs `2 → 5708` across 2018-01-19 … 2021-03-06.
- `223961c6` runs `1 → 3500` across 2017-12-01 … 2021-03-14.

**Independent across units** — on the 13 shared (mixed) dates the two counters sit at unrelated
positions, e.g. 2018-01-29: `223961c6`[1536-1614] vs `722a6e72`[386-401]; 2018-07-04:
`223961c6`[2032-2259] vs `722a6e72`[1461-1527]. Two cameras, two independent counters, each internally
ordered, not aligned with each other.

Because the calibration-hash partition (FACT 1) and this filename-sequence partition are independent
measurements that agree, the two-unit split is a physical fact, not a parsing artifact.

**Observed, not explained (scope-bound):** ~5-6 date-boundary number *drops* per unit (e.g. `722a6e72`
reads 509-529 on 2018-02-05, then 75-90 on 2018-02-12). Counter-reset-shaped (card reformat / DCIM
reset), recorded as observation only — ~0.1% of boundaries, not explained here.

## FACT 5 — The LRI-format facts hold on BOTH units (cross-unit confirmed)

The Lane B LRI-format facts (`bundle_proof_lri_calibration_origin_static.md`) were originally proven on
Unit-1's four canonical seeds only. Re-running the same render-free checks on the four **Unit-2** twin
seeds confirms they hold across both physical bodies
(`runs/two_unit_corpus/crossunit_v2.py`):

| seed | intrinsics block | 16 records distinct | ROI 4160×3120 | intr sig |
|---|---|---|---|---|
| U1 28/35/70/150mm | 32832 B | 16/16 | ✓ | `722a6e72…` |
| U2 28/35/70/150mm | 32833 B | 16/16 | ✓ | `223961c6…` |

All eight seeds pass: each carries 16 pairwise-distinct per-camera intrinsics records and the
4160×3120 sensor ROI in `CameraModule.f9.f2`. So the **LRI-format / per-camera-calibration structure is
unit-invariant** (the *values* differ per body, as expected; the *format* is identical). This discharges
the universality gap **for the LRI-format facts specifically** — they are now two-unit verified, not
Unit-1-only.

> Method note: a first pass mis-selected the block (both the ~32 KB intrinsics block and the ~263 KB
> distortion block parse to 16 field-13 records, so "first 16-record block" was ambiguous). The fixed
> check pins to the **smallest** 16-record block (the intrinsics block); the bug was caught and corrected
> before this fact was admitted.

Scope limit: this discharges only the *LRI-format* claims. The **runtime merge/pipeline** "four-zoom
verified" claims remain Unit-1-only — they need an actual cross-unit render, which is separate work.

## Consequence for the ledger (flagged, not auto-applied)

The prior `CLAUDE.md` "Unit A = L16_02130+L16_03434; Unit B = L16_03041+L16_02285" labeling is **REFUTED** —
those are not two units; all four are **Unit-1** at four focal lengths. Therefore every claim marked
"four-zoom VERIFIED" in the ledger was verified on **one physical body across four focals**, NOT across two
bodies. **Unit-invariance (universality) is unproven** for those claims; they are unit-bound until re-run
on the Unit-2 twins above. This scopes, does not retract, those claims — flagged for human decision before
any ledger edit.

## Owner identity (out of scope)

Which physical unit belongs to which owner is external knowledge, not a bytes-verifiable fact, and gates
no parity work — so it is deliberately not investigated here. The two units are identified by their
calibration signatures (`722a6e72`, `223961c6`); that is all this proof asserts.

## Caveat (scope-bound, not hidden)

182 of 9390 files did not expose a 16-record intrinsics block under the current `lri_field_inspect`
heuristic (e.g. `2017-12-08/L16_00696.lri`). They are **unassigned**, not a third unit — the parser
coverage gap is a known limitation, not evidence of more bodies. Assigning them needs a parser fix
(tracked as future work), not a new claim.

## Artifacts (reproduction, local ignored `runs/`)

- `runs/two_unit_corpus/per_file_unit_partition.py` — per-file hash + mixed-folder detection (this proof)
- `runs/two_unit_corpus/twin_compare.py` — canonical-seed vs twin calibration comparison
- raw report: `/Volumes/Dev/lumen-phoenix-scratch/per_file_unit_partition_report.txt`

Codex audit note, 2026-06-01: these `runs/` scripts are present locally and reproduced the numbers above,
but `runs/` is gitignored and the scripts are not git-tracked. The embedded facts above are therefore the
durable committed evidence; promoting the verifier scripts into a tracked harness path is a separate
custody hardening step.
