# Four-Zoom Lumen Self-Repeat Distributions

## Claim

Ten clean profile-3 bridge-HDR renders of each canonical Unit-1 seed establish
per-focal empirical repeat distributions for the final `10432 x 7824`
Radiance output. The old unqualified `~0.034 counts` nondeterminism floor is
refuted: repeat variation is focal-dependent, frequently affects most pixels,
and forms repeated whole-output classes at `28mm`, `35mm`, and `150mm`.

This closes only the final-output self-repeat part of `CLM-VALIDATION-001`.
Undistorted-plane references and full depth/disparity reference maps remain
open.

## Reusable Harness

- `tools/validation/run_self_repeats.sh`
- `tools/validation/analyze_self_repeats.py`
- ignored raw root: `runs/reference_validation/self_repeats/`
- complete analysis packet:
  `runs/reference_validation/self_repeats/analysis_linear.json`

The runner deletes partial output before each attempt and allows up to three
attempts. This matters operationally: the initial `35mm` campaign attempt and
the first attempt at `150mm` repeat 10 terminated before producing a complete
file; their retries completed. These are harness/render outcomes, not hidden
or counted as image samples.

Rerun:

```bash
tools/validation/run_self_repeats.sh
python3 tools/validation/analyze_self_repeats.py \
  runs/reference_validation/self_repeats \
  --json-out runs/reference_validation/self_repeats/analysis_linear.json
```

## Corpus

| Tier | Absolute LRI path | Body scope | Complete repeats |
|---|---|---|---:|
| `28mm` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` | Unit-1 `722a6e72...` | 10 |
| `35mm` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` | Unit-1 `722a6e72...` | 10 |
| `70mm` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` | Unit-1 `722a6e72...` | 10 |
| `150mm` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` | Unit-1 `722a6e72...` | 10 |

This campaign measures same-input renderer repeatability, so a second body
would answer a different question. Cross-unit validation remains required at
calibration- and routing-sensitive implementation boundaries, not for
estimating the repeat distribution of these four fixed inputs.

## Method

The analyzer streams all ten outputs in parallel and evaluates all 45
unordered pairs per tier. It verifies common dimensions and complete bodies,
hashes the decoded RGBE stream, and records:

- differing-pixel fraction and absolute byte-code differences;
- symmetric linear RGB L1:
  `sum(abs(A-B)) / sum(abs(A)+abs(B))`;
- normalized linear RGB RMSE:
  `sqrt(sum((A-B)^2) / sum(0.5*(A^2+B^2)))`;
- mean absolute `log2` luminance difference above `2^-20`.

RGBE samples are decoded to bin-center values as
`(mantissa + 0.5) * 2^(exponent-136)` for nonzero exponents. Byte-code metrics
include all four RGBE bytes and are diagnostic only; the linear metrics are
the meaningful scale-independent comparison.

## Results

| Tier | Unique decoded outputs / class sizes | Symmetric L1 p95 / max | Normalized RMSE p95 / max | Mean abs log2 luminance p95 / max |
|---|---|---:|---:|---:|
| `28mm` | 2 / `8,2` | `0.00427959 / 0.00427959` | `0.0109204 / 0.0109204` | `0.0168387 / 0.0168387` |
| `35mm` | 5 / `6,1,1,1,1` | `0.00231677 / 0.00387275` | `0.00915038 / 0.0109248` | `0.0281829 / 0.0371984` |
| `70mm` | 10 / ten singletons | `0.0150576 / 0.0152112` | `0.0422472 / 0.0423124` | `0.0611084 / 0.0617437` |
| `150mm` | 5 / `6,1,1,1,1` | `0.00523489 / 0.00530825` | `0.0128726 / 0.0130886` | `0.0295898 / 0.0319578` |

For completeness, p95 mean absolute RGBE-code differences are `2.24215`,
`3.33928`, `6.81704`, and `3.82644` at `28/35/70/150mm`; p95 differing-pixel
fractions are `0.892672`, `0.791066`, `0.931019`, and `0.942777`.

## Validation Consequence

There is no defensible single global byte-count floor. Validation must compare
linear decoded values and retain focal-specific repeat envelopes. For this
40-render campaign, the observed per-tier maximum normalized-RMSE values above
are the empirical same-input ambiguity bounds. A clean-room result outside a
tier's observed envelope is distinguishable from every measured Lumen repeat;
a result inside it is not thereby proved correct and still needs stage,
geometry, and artifact checks.

The distributions are reference evidence, not algorithm constants and not a
license to weaken formula-level equality where deterministic replay is
available.

## Admission Scope

- Runtime proof: yes, 40 complete full-resolution outputs and 180 pairwise
  comparisons.
- Zoom scope: canonical Unit-1 `28mm`, `35mm`, `70mm`, and `150mm`.
- Unit scope: Unit-1 only, appropriate to fixed-input repeatability.
- Claim status consequence: `CLM-VALIDATION-001` advances from `OPEN` to
  `PARTIAL`; undistorted-plane references and complete depth/disparity maps
  remain blocking.
