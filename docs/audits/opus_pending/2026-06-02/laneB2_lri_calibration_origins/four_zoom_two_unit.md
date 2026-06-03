# Lane B2 addendum — intrinsics block across four zooms + both units (OBSERVED)

**Status:** `NEEDS_CODEX_VALIDATION`. Deterministic LRI-parse over all 8 canonical seeds (4 zooms × 2
units). Byte-verified; no render; collision-free (LRI-input side). Extends the single-file B2 README to
the four-zoom + two-unit rigor.

## Result (all 8 seeds, `tools/lri_field_inspect.py`)

| seed | block | payload | unit sig | tier fx (cam0 / cam5 / cam10) |
|---|---|---:|---|---|
| 28mm U1 | blk3 | 32832 | `722a6e72…` | 3376 / 8283 / 18795 |
| 35mm U1 | blk3 | 32832 | `722a6e72…` | 3376 / 8283 / 18795 |
| 70mm U1 | blk4 | 32832 | `722a6e72…` | 3376 / 8283 / 18795 |
| 150mm U1 | blk4 | 32832 | `722a6e72…` | 3376 / 8283 / 18795 |
| 28mm U2 | blk3 | 32833 | `223961c6…` | 3373 / 8281 / 18684 |
| 35mm U2 | blk4 | 32833 | `223961c6…` | 3373 / 8281 / 18684 |
| 70mm U2 | blk4 | 32833 | `223961c6…` | 3373 / 8281 / 18684 |
| 150mm U2 | blk4 | 32833 | `223961c6…` | 3373 / 8281 / 18684 |

## OBSERVED facts

1. **All 8 seeds carry a 16×field-13 intrinsics block** with the L16 5+5+6 focal-tier layout — the B2
   structure holds **four-zoom AND two-unit**, not just the 28mm Unit-1 seed.
2. **Intrinsics are per-body constants.** Within a unit, the block payload, unit signature, and tier fx
   are **identical across all four zoom captures** (28/35/70/150mm). So each LRI from a body carries that
   body's full, fixed 16-camera intrinsics — independent of the shot's focal tier. (Consistent with the
   distribution model: every LRI is self-contained calibration.)
3. **The two units differ.** Unit-1 fx `[3376, 8283, 18795]` vs Unit-2 `[3373, 8281, 18684]`; payload
   32832 vs 32833 B. The per-file unit-hash difference (from the two-unit proof) is therefore a **real
   per-body intrinsics divergence** (different lens calibration), not noise.
4. **The intrinsics block index varies** (blk3 or blk4 depending on the file) — confirming the
   two-unit partition's "smallest 16-field-13 block" selection heuristic is necessary (a fixed index
   would mis-select).

## Non-claims
- Only the block-level structure + tier fx were re-verified across the 8 seeds; the per-sub-field K /
  distortion / LUT / date labels remain CANDIDATE (README) and were re-verified only on 28mm Unit-1.
- "Per-body constant" is shown for the 4 zoom captures per unit; not exhaustively over all of a unit's
  thousands of LRIs (4 samples each).
- LRI-input side only; how libcp consumes these is Codex's `0x23faf0` thread, untouched.
- `commands.txt` (parent README) + this table reproduce the OBSERVED items.
