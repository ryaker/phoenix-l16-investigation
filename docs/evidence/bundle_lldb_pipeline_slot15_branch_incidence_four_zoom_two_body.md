# LLDB Proof: Pipeline Slot 15 Is an Exact Copy on the Tested Profile-3 Route

## Question

The installed-static bundle proves that payload slot `15` compares the current
color configuration against a fixed linear-ProPhoto/D50 packet, returns on
equality, and otherwise calls `ImageConvertColorSpace`. Which branch is
actually selected by canonical profile-3 rendering?

## Scope

This proof covers complete no-auto-LRIS profile-3 HDR renders at Unit-1
`28mm`, `35mm`, `70mm`, and `150mm`, plus an exact-focal Unit-2 `28mm` wide
control. A Unit-2 exact-`70mm` tele discriminator uses one positive equal-path
sample and a separate complete render with only both live unequal-conversion
sites armed.

This is branch-incidence proof for those inputs. It does not claim that the
unequal converter is unreachable in every profile, GUI/editing path, or unseen
input variant, and it does not assign any difference to body or firmware.

## Pinned Branch Sites

The verifier SHA-pins all three installed wrappers and checks these exact
sites:

| Payload | Equal return path | Unequal conversion path |
|---|---:|---:|
| Bayer | `0x34a6ad` | `0x34a6b4` |
| BayerFloat | `0x34a81d` | `0x34a824` |
| Color | `0x34a98d` | `0x34a994` |

At each stop, the probe reads the current descriptor's exact 52-byte color
configuration through the live wrapper holder, hashes it, and decodes its
nine matrix floats, white point, and source/target selectors.

## Complete Four-Focal Census

All five complete full-census renders exit `0` and write populated HDR:

| Input | Bayer equal | BayerFloat equal | Color equal | Unequal total |
|---|---:|---:|---:|---:|
| Unit-1 `28mm` | 780 | 348 | 348 | 0 |
| Unit-1 `35mm` | 780 | 282 | 282 | 0 |
| Unit-1 `70mm` | 768 | 269 | 0 | 0 |
| Unit-1 `150mm` | 744 | 83 | 0 | 0 |
| Unit-2 `28mm` | 780 | 348 | 348 | 0 |

The Unit-1 canonical quartet therefore executes `4,684` slot-15 calls, all on
the equal/copy path. The complete Unit-2 wide control adds `1,476` equal/copy
calls and zero conversions.

Every captured configuration has the same SHA-256:

```text
2478eb9014a50bca3b65e190c9d40f9fa5ede08054a0b49f11e144c49efbccfc
```

It is byte-identical to the fixed 52-byte linear-ProPhoto/D50 packet admitted
by `bundle_static_runtime_pipeline_linear_prophoto_stage_four_zoom.md`.

Tele Color remains zero-hit, matching the prior payload target census; this is
a scoped route fact, not a global exclusion.

## Unit-2 Tele Discriminator

Hot all-branch breakpoints perturb this tele render enough to expose the known
LLDB timing race. The accepted discriminator therefore separates positive
liveness from complete negative census:

1. a low-cap positive stop observes Unit-2 `70mm` Bayer at `0x34a6ad` with the
   exact target packet and the equal/copy outcome;
2. a fresh complete render arms only Bayer `0x34a6b4` and BayerFloat
   `0x34a824`, exits `0`, writes the full HDR, and records zero hits at both
   unequal-conversion sites.

The incomplete positive-sample render is not treated as completed-output
evidence. The complete mismatch-only render is not used alone as positive
wrapper liveness. Their joined scopes provide the intended tele body
discriminator without overclaiming a full hot-site count.

## Reproduction

Static branch-layout check:

```bash
python3 tools/lldb_probes/pipeline_linear_prophoto_stage/verify_slot15_branch_incidence.py
```

Canonical quartet:

```bash
tools/lldb_probes/pipeline_linear_prophoto_stage/run_slot15_four_zoom.sh
```

Two-body controls:

```bash
tools/lldb_probes/pipeline_linear_prophoto_stage/run_slot15_two_body_controls.sh
```

Combined report verification:

```bash
python3 tools/lldb_probes/pipeline_linear_prophoto_stage/verify_slot15_branch_incidence.py \
  --require unit1_28mm unit1_35mm unit1_70mm unit1_150mm unit2_28mm \
  --require-zero unit2_70mm \
  --require-sample unit2_70mm
```

Raw rerunnable reports live under ignored
`runs/pipeline_linear_prophoto_stage/`. Reusable probe artifacts live under
`tools/lldb_probes/pipeline_linear_prophoto_stage/`.

## Admission Boundary

Safe admission: on the tested canonical profile-3 route, slot `15` is an
observed exact-copy stage, not merely a conditionally classified converter.
The Unit-1 four-focal census sees zero unequal conversions in `4,684` calls;
the Unit-2 wide control agrees in `1,476` calls; and the targeted Unit-2 tele
discriminator samples the exact equal packet while a complete mismatch-only
render sees zero conversions.

Not admitted: formulas for generic unequal selector pairs, universal no-op
behavior outside the tested route, or body/firmware causation.
