# Validation Policy

This file defines the corpus rules for parity validation.

## Master Corpus

Primary LRI corpus:

- `/Volumes/Base Photos/Light`

The corpus remains outside the repo. The repo stores only manifests, policies, and named subsets.

## Hard Rule

All parity validation must work for:

- `28mm`
- `35mm`
- `70mm`
- `150mm`

No merge-critical behavior is considered complete if one of those zoom tiers is still unvalidated or implicitly inherited without proof.

## Canonical Zoom Quartet

These are the current seed LRIs for the baseline per-zoom validation set:

| Zoom | LRI | Unit signature | Path |
|---|---|---|---|
| 28mm | `L16_02130` | Unit-1 `722a6e72...` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| 35mm | `L16_03041` | Unit-1 `722a6e72...` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| 70mm | `L16_03434` | Unit-1 `722a6e72...` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| 150mm | `L16_02285` | Unit-1 `722a6e72...` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

These four files are seeds, not the whole corpus. Passing the quartet is necessary for a parity claim, but it is not a substitute for broader corpus validation. Per-file calibration-hash proof refutes the older `Unit A` / `Unit B` seed labels: all four canonical seeds are Unit-1, so runtime "four-zoom verified" currently means one physical body across four focal tiers, not two-unit universality. The Unit-2 same-name twin set is listed in [bundle_proof_two_unit_corpus_static.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_two_unit_corpus_static.md).

Correction note: `/Volumes/Base Photos/Light/2018-12-19/L16_02951.lri` is not a 35mm seed under direct `LightHeader` decode; it reports `image_focal_length = 98` and `5B+6C`. Use `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` for the true 35mm seed.

## Corpus Identity Rules

The corpus contains LRIs from two physical L16 devices. `L16_#####.lri` filenames are not globally unique across devices, so a filename alone is not a valid sample identity.

Every validation artifact must identify an LRI by:

- full absolute path
- zoom / focal tier
- physical device or unit label when known
- reason for inclusion in the validation set

Do not merge results from two LRIs only because their filenames match. Treat same-name LRIs at different paths or from different devices as distinct captures until proven otherwise.

## Selective Cross-Unit Validation

Cross-unit validation is claim- and risk-based. It is not a blanket rule to
repeat every four-zoom probe on both physical units.

Run a Unit-2 discriminator when a claim:

- consumes per-file calibration values or assigns public calibration origins,
- depends on camera membership, key routing, thresholds, counts, or branch
  incidence that may change with calibration or scene content,
- is intended to assert a unit-invariant data format or formula, or
- has already shown a difference between Unit-1 and Unit-2 twin captures.

Installed-bundle control flow, byte-guarded static disassembly, and local
arithmetic identities do not each require a duplicate full matrix when their
runtime input and output boundaries have already received suitable cross-unit
sampling.

The default minimal Unit-2 runtime set is one wide anchor and one tele anchor.
Add a crop tier only when it takes a distinct route or exposes a difference.
Every report must name omitted tiers and explain why the selected cases are the
right discriminators.

Because Unit-1 and Unit-2 twins are different captures, a differing runtime
observation is a cross-unit twin-capture difference. Do not attribute it solely
to physical body identity unless scene/content and instrumentation effects are
independently controlled.

## Required Validation Classes

Every parity milestone should run at least these validation classes:

1. **Identity / participation**
   - fired-camera set
   - anchor / contributor routing
   - zoom-tier behavior

2. **Geometry**
   - warp / coordinate generation
   - framing and crop behavior
   - contributor alignment

3. **Merge quality**
   - ghosting
   - trailers
   - edge doubling
   - visible contributor mismatch

4. **Regression**
   - no quality drop on any previously-passing zoom tier

## Validation Matrix Template

Use this table in future validation reports:

| Topic | 28mm | 35mm | 70mm | 150mm | Notes |
|---|---|---|---|---|---|
| Fired-camera set |  |  |  |  |  |
| Anchor / contributor routing |  |  |  |  |  |
| Warp coordinate generation |  |  |  |  |  |
| Merge / accumulation behavior |  |  |  |  |  |
| Framing / crop behavior |  |  |  |  |  |
| Ghosting / trailers |  |  |  |  |  |

## Future Named Subsets

Recommended future corpus subsets:

- `golden_merge_set`
- `zoom_identity_set`
- `tele_routing_set`
- `crop_behavior_set`
- `regression_set`

Each subset should list:

- exact LRI path
- zoom
- unit
- device / owner context when known
- reason for inclusion
- current expected result
