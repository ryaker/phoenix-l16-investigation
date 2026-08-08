# Unit-2 70mm Range-Generation Localization

**Date:** 2026-08-08  
**Claims:** `CLM-STEREO-001` full-map addendum; Phoenix parity localization  
**Result:** `PROVEN` at the scope below

## Purpose

This bundle replaces an unretained historical claim that Phoenix's local band
excluded Lumen's truth in `53.1%` of cells. It captures both engines under one
current recipe on the same Unit-2 tele LRI and asks three separate questions:

1. Does the admitted Lumen `0x298ff0` range-pool formula reproduce complete
   runtime low/high maps, not only samples?
2. Does current Phoenix execute the same formula on its own prior index maps?
3. At what level does Phoenix first diverge enough to exclude Lumen's next
   winner?

## Pinned Inputs

```text
LRI
/Volumes/Base Photos/Light/2017-12-01/L16_00010.lri
SHA-256 bfcd916c34d3a5c1307f602490f6b7d6179eb67cba9d98b107b831d546dc973a

installed libcp.dylib
SHA-256 b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9

Phoenix source
/Users/ryaker/L16_Phoenix/phoenix
commit d3bb82c

Phoenix executable
build/tools/phoenix_depth_tool
SHA-256 19fed003a7d0199d874a6c4b262fae85abb7f91b6bc15c0b1c7efb7542fd494a
```

The Phoenix working-tree changes at capture time were confined to the parity
scorer and its two notebooks; the depth source was unchanged from the pinned
commit.

## Reproduction

Lumen full-map capture, repeated twice:

```bash
bash tools/lldb_probes/index5_range_pool_policy/run_lri.sh \
  "/Volumes/Base Photos/Light/2017-12-01/L16_00010.lri" \
  "Unit-2 70mm L16_00010 controlled tele range maps" \
  unit2_70mm_l16_00010_fresh

bash tools/lldb_probes/index5_range_pool_policy/run_lri.sh \
  "/Volumes/Base Photos/Light/2017-12-01/L16_00010.lri" \
  "Unit-2 70mm L16_00010 controlled tele range maps repeat" \
  unit2_70mm_l16_00010_fresh_repeat
```

The extended callback writes packed prior Depth, prior Skip mask, range-low,
and range-high arrays for all five transitions. Each report records size and
SHA-256 for every file.

Phoenix command:

```bash
PHX_DUMPBAND=.../phoenix/band PHX_DUMPIDX=.../phoenix/index \
  /Users/ryaker/L16_Phoenix/phoenix/build/tools/phoenix_depth_tool \
  "/Volumes/Base Photos/Light/2017-12-01/L16_00010.lri" OUTPUT \
  --pyramid on --maxlevel 3 --colormatch on --avgsrc on
```

The ignored raw outputs are retained under:

```text
runs/index5_range_pool_policy/unit2_70mm_l16_00010_fresh/
runs/index5_range_pool_policy/unit2_70mm_l16_00010_fresh_repeat/
runs/tele_range_generation_unit2_70mm_2026-08-08/phoenix/
```

Verifier:

```bash
python3 tools/validation/verify_tele_range_generation.py \
  --lumen-repeat runs/index5_range_pool_policy/unit2_70mm_l16_00010_fresh_repeat \
  --phoenix-index-prefix runs/tele_range_generation_unit2_70mm_2026-08-08/phoenix/index \
  --phoenix-band-prefix runs/tele_range_generation_unit2_70mm_2026-08-08/phoenix/band
```

Run the same command with `--lumen` pointing to the repeat directory to obtain
the second-draw Phoenix coverage figures below.

## Complete Lumen Pool Replay

For each source cell, the verifier independently applies the admitted clamped
`4x4` footprint `dx,dy in {-1,0,1,2}`, includes only prior positions whose Skip
byte is nonzero, and emits `(65535,0)` if none survive.

Every captured word matches on both Lumen draws:

| Prior dimensions | Low words | High words |
|---|---:|---:|
| `65x49` | `3,185/3,185` | `3,185/3,185` |
| `130x98` | `12,740/12,740` | `12,740/12,740` |
| `260x195` | `50,700/50,700` | `50,700/50,700` |
| `520x390` | `202,800/202,800` | `202,800/202,800` |
| `1040x780` | `811,200/811,200` | `811,200/811,200` |

That is `2,161,250` exact low/high words per draw and `4,322,500` across the
repeat pair. Lumen's next-level selected index lies inside the corresponding
Lumen half-open band in `100.0000%` of cells at each controlled transition.

## Repeatability Bound

LLDB instrumentation perturbs the selected maps, so the repeat is retained as
a noise bound rather than hidden:

| Level | Dimensions | Exact | Within 4 | MAE |
|---:|---:|---:|---:|---:|
| 0 | `65x49` | 21.4443% | 63.2653% | 15.3243 |
| 1 | `130x98` | 21.9937% | 70.9027% | 4.0578 |
| 2 | `260x195` | 20.5424% | 72.3590% | 3.4694 |
| 3 | `520x390` | 20.7959% | 72.9586% | 3.3745 |
| 4 | `1040x780` | 17.2393% | 75.1467% | 3.2799 |

These values are weaker than the previously retained noninstrumented final-map
repeat (`94.4%` within 4). No deterministic-map or bit-identical-render claim
is made.

## First Diverging Level

Both engines seed level 0 with the complete `1464`-entry lookup, so no
coarse-to-fine range builder has yet constrained its argmin. Phoenix already
differs there:

| Comparison | L0 within 4 | L3 within 4 |
|---|---:|---:|
| Phoenix vs Lumen draw 1 | 25.5259% | 38.9965% |
| Phoenix vs Lumen draw 2 | 28.1947% | 50.7327% |
| Lumen draw 1 vs draw 2 | 63.2653% | 72.9586% |

Thus the current Phoenix/Lumen divergence predates the range builder. It begins
in the level-0 full-band cost/geometry/guidance/SGM path or its inputs.

## Propagation Consequence

Current Phoenix range dumps exactly equal a clean-room application of the
admitted pool and floor-map/pad formula to Phoenix's own prior indices. Because
those prior indices differ, the source low/high maps rarely equal Lumen's:

| Transition | Low exact | High exact | Lumen truth in Phoenix band, draw 1 | draw 2 |
|---|---:|---:|---:|---:|
| `65x49 -> 130x98` | 2.1036% | 4.3642% | 46.2088% | 49.8587% |
| `130x98 -> 260x195` | 1.4678% | 7.1193% | 19.2170% | 28.5503% |
| `260x195 -> 520x390` | 2.1893% | 7.8343% | 16.9246% | 25.5251% |

The narrowing bands amplify the upstream level-0 difference. This is an image-
quality consequence of wrong prior winners, not evidence that Phoenix's
range-pool formula itself is wrong.

## Disposition

- The historical `53.1%` remains unrecoverable and is not reused.
- A fresh same-generation replacement now exists: current truth-in-Phoenix-
  band coverage is the draw-bounded table above.
- The previous causal label "range-builder root cause" is **REFUTED for this
  current source state**. Range construction is a deterministic downstream
  amplifier; the first observed divergence is the full-band level-0 argmin.
- The next parity investigation must compare level-0 operands and stages in
  dependency order: selected Guidance/source planes, composed records, raw
  G-42 local cost, then G-43 accumulation/argmin. It must not tune range width
  to compensate for upstream winners.

## Scope

- **Runtime numerical scope:** one Unit-2 `70mm` LRI, two instrumented Lumen
  draws, one current Phoenix canonical controlled render through level 3.
- **Installed formula scope:** the SHA-pinned selected `0x298ff0` pool and
  already admitted suffix formula.
- **Not claimed:** deterministic Lumen output, other scenes/focals/bodies,
  equality of Phoenix's upstream operands, or localization within G-42 versus
  G-43. Prior admitted Unit-1 four-focal and Unit-2 exact-focal evidence remains
  the broader mechanism scope.

Admit the complete Unit-2 tele full-map pool replay as a `CLM-STEREO-001`
addendum and record the Phoenix localization as implementation-audit evidence.
Claim status remains `PROVEN` / `SPEC_READY`.
