# Evidence: 35mm Seed Correction And Corrected Runtime Slice

## Scope

This note records a correction to the canonical four-zoom validation seed set.

It proves:

- `/Volumes/Base Photos/Light/2018-12-19/L16_02951.lri` is not a 35mm sample under direct `LightHeader` decode.
- `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` is a direct 35mm sample under direct `LightHeader` decode.
- The corrected true-35mm sample was rerun through the promoted IRAMP wrapper / accumulator and IRAMP entry-signature probes.
- The corrected true-35mm sample was also rerun through the already-documented prefusion candidate-scoring, callable-gate, and StereoLayer cost-path exclusion probes.

It does not prove physical unit identity for `L16_03041`; full absolute path remains the sample identity.

## Direct LRI Header Decode

Decoder:

`python3 tools/lri_field_inspect.py`

### Rejected Prior 35mm Seed

Path:

`/Volumes/Base Photos/Light/2018-12-19/L16_02951.lri`

Direct facts:

- `LightHeader.field_4 image_focal_length = 98`
- Union of `LightHeader.field_12[i].field_2` across image chunks:
  `5,6,7,8,9,10,11,12,13,14,15`
- Camera names:
  `B1,B2,B3,B4,B5,C1,C2,C3,C4,C5,C6`

Therefore `L16_02951` at this path is a tele-tier sample, not a 35mm validation seed.

### Corrected 35mm Seed

Path:

`/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri`

Direct facts:

- `LightHeader.field_4 image_focal_length = 35`
- Union of `LightHeader.field_12[i].field_2` across image chunks:
  `0,1,2,3,4,5,6,7,8,9`
- Camera names:
  `A1,A2,A3,A4,A5,B1,B2,B3,B4,B5`

Therefore `L16_03041` at this path is the corrected true-35mm validation seed.

## Corrected IRAMP Wrapper And Accumulator Slice

Runtime artifact:

`/private/tmp/l16_runtime_method_probe_35mm_true.json`

Probe path:

`/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri`

Result:

| Surface | Count |
|---|---:|
| `0x3ecc10` visible `src1` wrapper | 10 |
| `0x3ecd80` visible `src2` wrapper | 10 |
| `0x3eced0` contributor wrapper | 10 |
| `0x369fa1` IRAMP accumulator | 2 |

The JSON reported:

- `stop_reason = target_counts_reached`
- `callback_errors = []`

The first captured accumulator stack window matched the prior four-zoom window:

```text
0.009607374668121338
0.08426520228385925
0.22221490740776062
0.4024548828601837
0.5975451469421387
0.7777851819992065
0.9157348275184631
0.9903926849365234
0.9903926253318787
0.9157347679138184
0.7777850031852722
0.5975452065467834
0.40245479345321655
0.22221478819847107
0.08426520228385925
0.00960734486579895
```

## Corrected IRAMP Entry-Signature Slice

Runtime artifact:

`/private/tmp/l16_iramp_entry_35mm_true.json`

Probe path:

`/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri`

Result:

| Datum | Value |
|---|---|
| Captured PC | `0x108fdf960` |
| ROI | `[512, 512, 1024, 1024]` |
| `xmm0` scale | `2.507692337036133` |
| contributor source count | `5` |
| warp-record count | `5` |
| contributor `funcdata+0x90` camera IDs | `[5,6,7,8,9]` |
| contributor names | `B1,B2,B3,B4,B5` |
| contributor `vtable+0x30` target | `0x3eced0` for all five |

This proves the corrected true-35mm IRAMP contributor vector carries B-row contributors, matching the direct `LightHeader` wide-tier firing set.

## Corrected Prefusion Exclusion Slices

These reruns repair rows in prior "four-zoom" exclusion docs that had used `L16_02951` as the 35mm sample.

### Candidate-Scoring Family

Runtime artifact:

`/private/tmp/l16_prefusion_candidate_scoring_probe_true35/results.json`

Corrected true-35mm result:

| Surface | Hits |
|---|---:|
| `0x24c320` family A entry | `>=50` |
| `0x24d610` family B entry | `0` |
| `0x24cf90` family A helper | `>=20` |
| `0x24e070` family B helper | `0` |
| `0x24e350` family B helper | `0` |

Therefore the corrected bridge HDR split is:

- `28mm` and `35mm`: `0x24c320`
- `70mm` and `150mm`: `0x24d610`

The old `L16_02951` row remains valid only as a 98mm tele-sample observation, not as 35mm evidence.

### Callable Gate

Runtime artifact:

`/private/tmp/l16_prefusion_callable_gate_probe_true35/results.json`

Corrected true-35mm result:

| Surface | Hits |
|---|---:|
| `0x24200d` selector gate | `>=10` |
| `0x24459b` heavy initial gate | `4` |
| `0x24477b` heavy second gate | `4` |
| `0x245b29` heavy gate | `5` |
| `0x24c34f` downstream gate A | `>=10` |
| `0x24d64e` downstream gate B | `0` |

Therefore the corrected bridge HDR gate split is:

- `28mm` and `35mm`: downstream gate `0x24c34f`
- `70mm` and `150mm`: downstream gate `0x24d64e`

### StereoLayer Cost Path

Runtime artifact:

`/private/tmp/l16_stereolayer_cost_firsthit_true35/results.json`

Corrected true-35mm result:

| Surface | Hits |
|---|---:|
| `0x276790` runPass action | `>=20` |
| `0x276860` mode-8 worker | `>=20` |
| `0x277e70` default worker | `0` |
| `0x275630` per-tile state builder | `>=20` |
| `0x2730c0` count-4 projection cost | `0` |
| `0x2732f0` general projection cost | `>=20` |

This preserves the existing StereoLayer cost-path conclusion for true 35mm.

## Canonical Consequence

The canonical 35mm seed must be:

`/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri`

The prior seed:

`/Volumes/Base Photos/Light/2018-12-19/L16_02951.lri`

must not be cited as 35mm evidence. In current evidence it is a 98mm tele-tier sample.
