# Evidence: Lane B Cross-Unit Public LRI Carrier Check

**Date:** 2026-06-20
**Status:** VERIFIED for static public LRI carrier schema. No runtime Unit-2
index-5 custody is admitted by this note.
**Scope:** Unit-1 canonical four focal tiers plus Unit-2 exact-focal static
representatives. Render-free LRI parsing only.

## Why This Exists

The index-5 public-meaning audit uses public LRI carrier paths such as
`LightHeader.field_12`, the compact intrinsics `field_13` block, the large
warp/calibration `field_13` block, and the per-camera `4160 x 3120` ROI. The
canonical runtime evidence for the index-5 path remains Unit-1 only, so this
probe checks whether the public LRI carrier schema itself is body-specific.

This is a risk-based body check. It is not a substitute for rerunning the full
runtime index-5 path on Unit-2.

## Tracked Verifier

Verifier:

```text
tools/lane_b_crossunit_lri_public_carriers.py
```

Run:

```text
python3 -m py_compile tools/lane_b_crossunit_lri_public_carriers.py
python3 tools/lane_b_crossunit_lri_public_carriers.py --json-out runs/lane_b_crossunit_lri_public_carriers/report.json
```

The verifier reuses the tracked parser helpers in
`tools/lane_b_index5_public_meaning_audit.py` and asserts:

- Unit identity by smallest 16-record intrinsics-block SHA-256.
- Header focal value.
- Fired-camera set in `LightHeader.field_12`.
- Required public module carrier fields:
  `field_2`, `field_3`, `field_5`, `field_8`, `field_10`, `field_15`, and
  `field_16`, with optional `field_4`.
- Per-camera ROI path:
  `LightHeader.field_12[].field_9.field_2.field_1/field_2 = 4160/3120`.
- Intrinsics block: 16 camera-keyed `field_13` entries, camera IDs `0..15`,
  16 pairwise-distinct records.
- Warp block: 16 camera-keyed `field_13` entries; each camera has a public
  nominal-table path at `field_4.field_2[j].field_1` with either one or four
  entries.
- Public proto value walk includes `4160` and `3120` and does not expose the
  libcp-computed pyramid/output dimensions checked by the Lane B audit.

## Exact-Focal Static Set

The passing exact-focal set is:

| Role | Tier | LRI | Header focal | Fired set | Intrinsics |
|---|---|---|---:|---|---|
| Unit-1 canonical | `28mm` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` | `28` | `A1..A5,B1..B5` | `32832B / 722a6e721636c9c4` |
| Unit-1 canonical | `35mm` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` | `35` | `A1..A5,B1..B5` | `32832B / 722a6e721636c9c4` |
| Unit-1 canonical | `70mm` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` | `70` | `B1..B5,C1..C6` | `32832B / 722a6e721636c9c4` |
| Unit-1 canonical | `150mm` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` | `149` | `B1..B5,C1..C6` | `32832B / 722a6e721636c9c4` |
| Unit-2 representative | `28mm` | `/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri` | `28` | `A1..A5,B1..B5` | `32833B / 223961c6bce6153e` |
| Unit-2 representative | `35mm` | `/Volumes/Base Photos/Light/2018-07-02/L16_01956.lri` | `35` | `A1..A5,B1..B5` | `32833B / 223961c6bce6153e` |
| Unit-2 representative | `70mm` | `/Volumes/Base Photos/Light/2018-10-25/L16_02894.lri` | `70` | `B1..B5,C1..C6` | `32833B / 223961c6bce6153e` |
| Unit-2 representative | `150mm` | `/Volumes/Base Photos/Light/2018-07-07/L16_02285.lri` | `149` | `B1..B5,C1..C6` | `32833B / 223961c6bce6153e` |

The Unit-2 warp block is `262969B / 4ed37b69a473f7c5`; the Unit-1 canonical
warp block is `262968B / f0c34433f9cf9b07`.

## Body-Specific Calibration Values Are Real

The public carrier schema is stable across both physical bodies, but the
calibration payloads are not byte-identical and some per-camera nominal-table
cardinality assignments differ by body.

Observed one-entry nominal groups:

| Unit | One-entry nominal cameras | Four-entry nominal cameras |
|---|---|---|
| Unit-1 canonical | `A1,A2,A3,A4,A5,B4,C2,C3` | `B1,B2,B3,B5,C1,C4,C5,C6` |
| Unit-2 representatives | `A1,A2,A5,B3,B4,C2,C3,C5` | `A3,A4,B1,B2,B5,C1,C4,C6` |

This matters for implementation: Phoenix should parse these public per-LRI
tables instead of hardcoding Unit-1's camera grouping.

## Same-Name Scope Correction

The earlier same-name Unit-2 list is useful for body identity, but it is not a
true exact-focal four-tier runtime set:

| Same-name candidate | Actual header focal | Fired set | Scope |
|---|---:|---|---|
| `/Volumes/Base Photos/Light/2018-10-28/L16_03041.lri` | `74` | `B1..B5,C1..C6` | not an exact `35mm` representative |
| `/Volumes/Base Photos/Light/2020-07-14/L16_03434.lri` | `149` | `B1..B5,C1..C6` | not an exact `70mm` representative |

Therefore future cross-unit runtime work should use exact-focal Unit-2
representatives, or another explicitly verified exact-focal Unit-2 set, rather
than assuming same filename implies same focal tier.

## Conclusion

Admitted:

- The public LRI carrier schema used by the Lane B public-meaning audit is
  verified on both physical bodies for exact-focal static representatives.
- Public fired-camera sets remain AB for `28mm` / `35mm` and BC for `70mm` /
  `150mm` on the checked Unit-2 representatives.
- The `4160 x 3120` full-sensor ROI path and the intrinsics/warp `field_13`
  carrier paths are schema-stable across the checked bodies.
- Body-specific calibration values and nominal-table assignments exist and
  should be parsed per LRI.

Not admitted:

- Any Unit-2 runtime custody for `state+0xe0`, `state+0x448`, `record+0x40`,
  `StereoLayer<false>+0xe0`, `StereoLayer<false>+0xf8`, `0x299c70`, `0x267010`,
  or `0x29ed90`.
- Any public semantic names for the full internal State records or the
  index-5 ray-depth grid.
- Any canonical blocker or ledger status upgrade.
