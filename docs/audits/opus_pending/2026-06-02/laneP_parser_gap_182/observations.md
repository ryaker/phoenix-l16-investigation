# Lane P — Observations (deterministic)

Corpus: 9390 `/Volumes/Base Photos/Light/*/*.lri`. Method: reuse `tools/lri_field_inspect.py`
(`scan_lri_blocks`, `parse_proto_fields`). Reproducible — see `commands.txt`. No render, no disasm.

## O1 — 182 unassigned, reproduced

Files with no LELR block containing exactly 16 field-13 records: **182** (matches the two-unit proof's
count). Split: **4** with no LELR blocks at all; **178** with ≥1 block but none being the 16-camera
intrinsics block.

## O2 — block-count distribution (unassigned vs assigned)

Unassigned LELR-block counts: `{0:4, 1:10, 2:26, 3:77, 4:65}` (all ≤4).
Assigned example `L16_02130`: **12** `LELR` blocks, chaining cleanly (`blk0 total_len=81143279` → next
`LELR` magic at offset `81143279`; 12 magics total). The intrinsics block is one of those 12.

## O3 — walk-termination mechanism (magic count vs walked)

For each unassigned file, raw `LELR` magic count in the bytes vs blocks the `total_len`-chained walker
returned:
- `walked_all_present_blocks` (magic == walked): **92** (incl. the 4 zero-block).
- `walk_terminated_early` (magic > walked): **90** (e.g. `L16_00101`: 6 magics, 3 walked).

## O4 — robust re-parse assigns NONE; no third signature

Exhaustive re-parse: for every `LELR` magic offset in each of the 182, read `msg_offset`(@+12)/
`msg_len`(@+20), parse the payload, and if any block has 16 field-13 records, hash it. Result:
```
still_unassigned: 182
NOW_UNIT1: 0   NOW_UNIT2: 0   NEW_THIRD_SIG: 0
```
No 16×field-13 block exists in any of the 182 even under magic-scan; **no third calibration signature**.

## O5 — verified single-block example

`2017-12-09/L16_00795.lri`: size 170,203,529 B; exactly **one** `LELR` occurrence in the whole file
(offset 0); `blk0`: `total_len=84934688`, `msg_off=83886112`, `msg_len=1497`; byte at `+total_len` is
`fd ff ff e9` (not `LELR`). The 1497-byte payload parses to **no** recognized proto fields. A genuinely
different/reduced container layout, not a truncation (file is full-size).

## O6 — date spread

Unassigned span 2017-12-08 … 2021-03-06 (by year: 2017≈6, 2018≈94, 2019≈68, 2020≈9, 2021≈5). Not an
early-firmware-only artifact.

## Interpretation

Deterministic conclusion: the 182 unassigned contain no 16-camera intrinsics block in any parseable form,
yield no calibration signature, and surface no third unit. The two-unit "exactly two, no third" claim is
not threatened. The gap is a container-format / parser-coverage difference (≤4 blocks vs ~12; 90 with
early walk-termination that a robust walker still couldn't assign; 92 genuinely lacking the block).
