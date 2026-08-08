# Tele Band 53.1% Reconciliation (2026-08-08)

**Status:** historical percentage not reproducible; a fresh same-generation
replacement now localizes the current divergence before range propagation.

**Scope:** Phoenix implementation audit for Unit-2 `70mm` seed
`/Volumes/Base Photos/Light/2017-12-01/L16_00010.lri`. This is not installed-
bundle evidence and does not change a canonical Lumen claim.

## Question

Phoenix's July notebook said its finest local search band excluded Lumen's
truth above the band's upper bound for `53.1%` of cells. The August retraction
called that incompatible with the same Lumen map spanning only indices `1..40`
on a `1464`-entry ladder.

Those facts are not incompatible. `1464` is the global lookup count. The dumped
upper value is a different, per-pixel coarse-to-fine search ceiling. A truth
index of `20` is globally valid and is still unreachable where a local band
ends at `18`.

The July prose itself made this distinction explicit: it quoted mean local
upper bounds `14.2` and `18.9` for truth bins `[15,20)` and `[20,25)`. Therefore
the August sentence "nowhere near any upper bound of mine" compared the truth
to the wrong upper bound.

## Custody

The retained Lumen inputs are:

- `index5_depth.f32le` SHA-256
  `8b4b7ada9c88f8419aa96d0340064f64c0b632c3575a2dcb1172a71bfa1f4d80`.
- `lookup.f32le` SHA-256
  `9ef636b7142f20a8742b6d5e9e7f50bfdc11f915f05edc2091c07cbc76aa881a`,
  `1464` descending float32 values.
- The depth map converts to exactly `40` rounded indices, `1..40`, with maximum
  continuous-index residual `1.32e-5`.

No July `PHX_DUMPBAND` raw file or comparison script was retained. Git history
first adds the tool and the whole prior notebook together at Phoenix commit
`65cf9bd`; it does not preserve the intermediate source state that produced
the `53.1%` line.

## Independent Replays

`tools/validation/verify_tele_band_coverage.py` binds one depth map, lookup, and
band dump and reports both correct half-open semantics and the historical
closed-bound reading.

Two full `--maxlevel 5` runs were captured under
`runs/tele_band_reconciliation_2026-08-08/`:

| Phoenix source | Band SHA-256 | Half-open inside / above / below |
|---|---|---|
| historical commit `65cf9bd` | `49999694...40bfaf` | `2.56% / 5.40% / 92.04%` |
| current commit `d3bb82c` | `764a621b...1ddef` | `13.73% / 17.65% / 68.62%` |

Neither replay reproduces `53.1%`. The historical commit is already later than
the missing intermediate run, and the current path has changed further. The
large change between these two addressable source states confirms that a band
percentage without a source commit, exact flags, raw dump, and comparison
semantics is not reusable evidence.

## Verdict

1. The `53.1%` value is **UNVERIFIABLE**, not disproven. Its load-bearing raw
   artifact and exact producing source state are absent.
2. The alleged logical contradiction with truth indices `1..40` is **REFUTED**.
   It confused the global lookup range with each pixel's local search range.
3. The value cannot support the current claim that the range builder is the
   tele root cause. That localization remains unsupported pending a fresh,
   same-generation band capture and a stage-matched Lumen reference.
4. The independently observed `1.44%` Phoenix output tail above Lumen's observed
   output maximum does not by itself prove non-overlapping search bands. Lumen
   may have searched a wider band and selected a lower minimum. A direct range-
   map comparison is required.

## Required Next Test

For one repeatable tele seed, retain in one run bundle:

- Lumen per-level `Range map` and pre-argmin `Cost volume`/Depth-map output;
- Phoenix per-level `(lower, lower+count)` dump and pre-argmin output;
- exact LRI SHA, binary/source SHA, dimensions, flags, and upper-bound semantics.

Compare the first diverging level. This distinguishes range construction from
cost/SGM selection without relying on a final-map correlation statistic.

## Fresh Resolution (TRUTH 3.0.348)

That required test is now complete. Evidence bundle
`bundle_runtime_unit2_70mm_range_generation_localization.md` retains two fresh
instrumented Lumen captures and one current Phoenix render of the same
Unit-2 `70mm` LRI.

The admitted asymmetric-4x4/Skip-mask pool reproduces every captured Lumen
low/high word at all five transitions in both draws (`4,322,500` total), and
each Lumen next-level winner is inside its own band in `100%` of controlled
cells. Current Phoenix band dumps likewise exactly equal the admitted formula
applied to Phoenix's own prior maps.

The first mismatch occurs at level 0, where both engines search the complete
1,464-entry lookup and no range propagation has run. Phoenix is only
`25.5259%` / `28.1947%` within four of the two Lumen draws there, versus
`63.2653%` Lumen-repeat within four. Subsequent Lumen-winner coverage in
Phoenix bands falls to `46.2088/19.2170/16.9246%` for draw one and
`49.8587/28.5503/25.5251%` for draw two.

Therefore the fresh causal verdict is: **range construction amplifies an
upstream level-0 argmin mismatch but does not originate it**. The historical
`53.1%` remains unverified and unnecessary. Next work moves to same-render
level-0 Guidance/source planes, composed records, G-42 cost, and G-43
accumulation/argmin.
