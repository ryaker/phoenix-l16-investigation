# Phoenix Metric-Claim Sweep (2026-08-08)

**Status:** complete adversarial pass over the live Phoenix metric narrative at
commit `d3bb82c` plus the three corrective working-tree edits described below.

**Scope:** implementation validation only. This audit neither proves nor
changes an installed Lumen mechanism.

## Surfaces Swept

- Phoenix `BURNDOWN.md`
- Phoenix `PARITY_DIVERGENCE_LEDGER.md`
- Phoenix `ENGINE_RECONCILIATION.md`
- Phoenix `tools/parity/wired_status.py`
- Phoenix `tools/parity/score_depth_controlled.py`

The four prose/status surfaces contain `304` token occurrences of Pearson,
within-N, flip retention, shuffle, or null terminology. This is an occurrence
count, not a claim count. Each current conclusion was traced to the latest
correction entry rather than treating the chronological notebook as flat
authority.

## Findings

### 1. The `53.1%` retraction used the wrong bound

Truth indices `1..40` on a global `1464`-entry ladder can exceed a per-pixel
local upper bound such as `14` or `19`. The supposed contradiction is refuted.
The original percentage remains unverified because its raw band dump, exact
comparison script, and intermediate Phoenix source state were not retained.
See `tele_band_53pct_reconciliation_2026-08-08.md`.

### 2. `out_of_ladder()` did not inspect a ladder

The function compared Phoenix output to Lumen's maximum **selected output**.
It did not inspect Lumen's global lookup bound or local `Range map`. The `1.44%`
tail remains a valid Pearson-leverage diagnostic, but it does not prove that
Phoenix searched hypotheses Lumen never entered. The function is now named
`output_range_tail()` and its comments/output state the narrower meaning.

### 3. The current tele candidate has no overall controlled pass

For repeatable Unit-2 `70mm` seed `L16_00010`, both Lumen draws give the same
result class:

| Statistic | Current result |
|---|---|
| raw Pearson | fails mirror control |
| detrended Pearson | passes |
| Spearman | fails mirror control (`93-97%` retained) |
| within-4 | fails mirror/shuffle control |
| within-16 | fails mirror control |

Therefore the ledger phrase "strong spatial agreement" is withdrawn. A strong
monotone association exists, but it is not spatially discriminating under this
test. The affine fit `ours = 0.3471*truth + 13.444`, quadrant offsets, and tail
size remain descriptive measurements only; none localizes a Lumen stage.

### 4. The Lumen tele reference really is repeatable

The old label used only a fixed `90% within-4` threshold. Re-testing the two raw
Lumen hypothesis-index maps with controls gives:

- identical: `52.88%`
- within-4: `94.36%`
- best mirror within-4: `55.07%`
- shuffled within-4: `44.23%`
- flip retention above chance: `21.6%`
- MAE: `1.10` index units

This reference survives the adversarial test. The scorer now applies the same
shuffle and mirror controls on every repeatability screen. A missing repeat is
`UNKNOWN` and yields a nonzero `CONTROL-INAPPLICABLE` result rather than being
silently scoreable as evidence.

### 5. The local candidate corpus was mixed-generation and is now normalized

Before regeneration, the scorer's shape guard correctly found:

- `campaign/u2_70mm_a`: canonical `390x520` final candidate;
- `unit1_28mm`: stale `49x65` level-0 candidate;
- `l16_06689`: stale `49x65` level-0 candidate.

The stale Unit-1 and `L16_06689` candidates were regenerated on the Mac with
the same `d3bb82c` binary and exact canonical recipe
`--pyramid on --maxlevel 3 --colormatch on --avgsrc on`. The mislabeled
`L16_06689` level-0 products were preserved under `legacy_maxlevel0/`.

The normalized three-capture pass now reports:

| Capture | Reference | Controlled result |
|---|---|---|
| Unit-1 28mm `L16_02130` | repeatable | within-4 `16.28%` fails; within-16 and detrended Pearson pass |
| Unit-1 `L16_06689` | unscreened | all rows fail; run is non-admissible without a repeat |
| Unit-2 70mm `L16_00010` | repeatable | all except detrended Pearson fail |

This removes the local 49x65/390x520 generation collision. It does not create
a complete cross-focal/two-body candidate corpus; `35mm`, `150mm`, and the
remaining exact-focal/body combinations still need canonical candidates and
repeat-screened references.

### 6. Historical within-N and Pearson lines are measurements, not authority

`BURNDOWN.md` is a chronological notebook containing many superseded recipes,
injected-input experiments, mixed reference draws, and pre-control scores. A
banner now says that Pearson conclusions are retired and that a within-N claim
lacking repeatability, shuffle, mirror, perfect-map, grid, and provenance
controls is historical only.

Direct byte equality, exact formula replay, dimensions, hashes, and installed-
binary receipts are unaffected by this statistical downgrade. In particular,
the G-42 byte-exact local-curve evidence is not a Pearson/within-N claim.

## Live Code Corrections

Phoenix working tree changes:

1. `score_depth_controlled.py`: rename and narrow `output_range_tail()`;
   controlled repeatability; unscreened references become non-admissible.
2. `PARITY_DIVERGENCE_LEDGER.md`: append the global-vs-local bound correction,
   withdraw "strong spatial agreement," and retain only scoped measurements.
3. `BURNDOWN.md`: add a top-level statistical custody warning.

Verification:

- scorer self-test: `53/53` passed;
- controlled tele run: reference `REPEATABLE`, candidate `FAILED-CONTROL`;
- pre-regeneration full local corpus run: `NOT-SCORED` because two candidates
  were wrong-recipe `49x65` products;
- post-regeneration three-capture run: Unit-1 28mm and Unit-2 70mm references
  are controlled/repeatable, `L16_06689` is unscreened, and no capture achieves
  an all-row controlled pass.

## Consequence For Investigation Priority

The tele range builder is not cleared and not localized as the root cause. The
new repeatable Unit-1 28mm failure also refutes treating the current build's
depth defect as tele-only. The
highest-value discriminator is a direct, same-generation per-level comparison
of Lumen and Phoenix `Range map`, normalized local Cost volume, aggregated SGM
cost, and selected Depth-map index. Correlation of final maps cannot replace
that stage boundary.
