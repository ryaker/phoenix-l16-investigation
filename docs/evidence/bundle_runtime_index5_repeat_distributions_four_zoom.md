# Four-Zoom Index-5 Repeat Distributions and Validation Oracle

## Claim

Ten complete index-5 hypothesis-index/depth samples per canonical Unit-1 focal
tier establish that the selected depth surface is focal-dependently
nondeterministic, while its index-to-depth conversion is a deterministic
bit-exact invariant.

This evidence supplies the missing intermediate-map validation policy:

- do not require one depth-map golden hash;
- require exact shape/type, focal-specific index bounds, finite public-mm
  depth bounds, and bit-exact `depth[p] = lookup[index[p]]` coupling;
- retain the measured pair distributions as diagnostics, not as a permissive
  numerical pass radius; and
- make parity acceptance at the final image boundary use the admitted
  focal-specific output-repeat envelopes plus deterministic stage, geometry,
  routing, and artifact checks.

## Harness and Samples

- complete-map capture:
  `tools/lldb_probes/reference_stage_maps/reference_stage_map_probe.py`
- optimized repeat driver:
  `tools/lldb_probes/reference_stage_maps/early_repeat_campaign_driver.py`
- repeat runner:
  `tools/lldb_probes/reference_stage_maps/run_early_repeat_campaign_to_10.sh`
- distribution analyzer:
  `tools/lldb_probes/reference_stage_maps/analyze_index5_repeat_distributions.py`
- full-map coupling verifier:
  `tools/lldb_probes/reference_stage_maps/verify_index5_full_map_coupling.py`
- ignored analysis packets:
  `runs/reference_stage_maps/index5_repeat_distributions.json` and
  `runs/reference_stage_maps/index5_full_map_coupling.json`

Samples 1 and 2 at all focal tiers are successful full renders with all four
stage maps. Sample 3 at `28mm` and `35mm` is also a successful full render.
The remaining samples stop only after both complete `2080x1560` index-5 maps
have been written and streamed. Early termination occurs after the artifacts
under test exist; those samples are not represented as completed outputs or
used for final-output distributions.

All 40 pairs contain:

- `3,244,800` little-endian `uint16` hypothesis indices; and
- `3,244,800` little-endian float32 millimeter depths.

## Exact Classes

| Focal | Hypothesis-index classes | Depth classes | Exact class sizes |
|---|---:|---:|---|
| `28mm` | `4` | `4` | `4,4,1,1` |
| `35mm` | `2` | `2` | `9,1` |
| `70mm` | `10` | `10` | ten singletons |
| `150mm` | `10` | `10` | ten singletons |

Index and depth class partitions are identical within each focal tier, as
required by direct lookup coupling.

## Pair Distributions

Each focal has 45 unordered sample pairs. Normalized RMSE is
`sqrt(sum((A-B)^2) / sum(0.5*(A^2+B^2)))`; symmetric L1 is
`sum(abs(A-B))/sum(abs(A)+abs(B))`.

### Depth map

| Focal | Unequal fraction median / max | RMSE mm median / max | Normalized RMSE median / max | Symmetric L1 median / max |
|---|---:|---:|---:|---:|
| `28mm` | `0.00209196 / 0.489359` | `0.369287 / 411.088` | `0.00009783 / 0.108436` | `0.00000288 / 0.0203365` |
| `35mm` | `0 / 0.000737796` | `0 / 16.2778` | `0 / 0.000374963` | `0 / 0.0000131859` |
| `70mm` | `0.873159 / 0.999229` | `185661.56 / 231160.13` | `0.800077 / 1.397124` | `0.352349 / 0.927772` |
| `150mm` | `0.999971 / 1.0` | `5852.77 / 292232.69` | `0.717528 / 1.397885` | `0.373608 / 0.955937` |

### Hypothesis-index map

| Focal | Unequal fraction median / max | Index RMSE median / max | Normalized RMSE median / max | Symmetric L1 median / max |
|---|---:|---:|---:|---:|
| `28mm` | `0.00209196 / 0.489359` | `0.100088 / 2.50922` | `0.00075491 / 0.0189488` | `0.00001729 / 0.00437708` |
| `35mm` | `0 / 0.000737796` | `0 / 0.0516881` | `0 / 0.000456482` | `0 / 0.0000120128` |
| `70mm` | `0.873159 / 0.999229` | `12.9363 / 70.3224` | `0.628580 / 1.170644` | `0.221355 / 0.726977` |
| `150mm` | `0.999971 / 1.0` | `25.1685 / 60.1857` | `0.690609 / 1.359721` | `0.367661 / 0.927141` |

The large tele ranges make a nearest-reference numerical threshold unsuitable
as a correctness gate. A candidate could be close under such a radius while
violating the installed algorithm. Distribution metrics remain useful for
diagnosis and for detecting behavior outside every observed Lumen run.

## Bit-Exact Physical Coupling

The independent verifier regenerates the admitted installed reciprocal
ray-depth lookup:

- count `752` at `28mm` / `35mm`;
- count `1472` at `70mm` / `150mm`;
- float32 endpoints `[640000.0 ... 200.0]` mm using the installed operation
  order.

For every sample and every pixel it verifies:

```text
0 <= hypothesis_index[p] < lookup_count
depth_mm[p] bitwise-equals lookup[hypothesis_index[p]]
isfinite(depth_mm[p])
200.0 <= depth_mm[p] <= 640000.0
```

Result:

```text
samples = 40
pixels = 129,792,000
float32 word mismatches = 0
```

This is a strong clean-room stage oracle. Winner-selection nondeterminism is
allowed only within an implementation that independently reproduces the
admitted cost-volume/SGM/index policy; it does not relax the exact lookup and
physical-unit contract.

## Validation Policy Consequence

Canonical profile-3 validation is layered:

1. Public input parsing, deterministic formulas, camera routing, geometry,
   crop, and output encoding must satisfy their exact admitted checks.
2. Camera-scoped undistorted RGBA16F planes use the exact stage references;
   the complete `28mm` repeat proves byte determinism for all five live
   contributors.
3. Index-5 maps use structural and bit-exact coupling invariants above. Their
   empirical numerical distributions are diagnostic, not a standalone pass.
4. Final output uses the four focal-specific ten-repeat linear-RGB envelopes.
   Being inside an envelope is necessary but not sufficient; visible
   ghosting, trails, misregistration, wrong framing/routing, or any failed
   deterministic check remains a failure.

This policy avoids both invalid extremes: requiring an impossible tele golden
hash and accepting arbitrary maps merely because Lumen's tele distribution is
broad.

## Admission Scope

- Zoom scope: canonical Unit-1 `28mm`, `35mm`, `70mm`, and `150mm`.
- Sample scope: ten complete index/depth maps per focal; 45 pairs per focal.
- Body scope: Unit-1 fixed inputs only. A second body is not needed to measure
  repeatability of these exact files and is not inferred from the result.
- Formula scope: installed SHA-pinned lookup generator and previously admitted
  index-map producer/cost policy.
- Claim consequence: together with the four-focal stage artifacts and
  final-output repeat evidence, `CLM-VALIDATION-001` is `PROVEN` /
  `SPEC_READY` for canonical profile-3 validation.

