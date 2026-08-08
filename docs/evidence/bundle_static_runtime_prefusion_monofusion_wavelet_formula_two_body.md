# Static/Runtime Evidence: Wide MonoFusion Mode-0 Wavelet Formula

**Date:** 2026-07-02  
**Status:** VERIFIED, scoped Lane A formula refinement  
**Bearing:** `CLM-PREFUSION-001`, `CLM-PREFUSION-002`

## Scope

This proof decodes the production-profile mode-0 path inside
`lt::MonoFusion::0x1b37a0`. The later corrective addendum
`bundle_static_runtime_prefusion_monofusion_installed_vst_table.md` proves
that its type-3 panchromatic coefficients come from an installed table, not
the LRI's public type-2 rows.

> **Corrective arithmetic addendum (2026-08-08):**
> `bundle_static_runtime_prefusion_monofusion_mode0_patch_terminal_exact_replay.md`
> supersedes this document where it described the noise mean, Wiener operand
> roles, or inverse axis order. The noise helper uses the mean of a separate
> public-vignetting auxiliary patch; `w` weights the target and `1-w` weights
> the source; and the live inverse stages execute row before column.

Runtime coverage:

| Physical body | Focal | LRI | Result |
|---|---:|---|---|
| Unit-1 | `28mm` | `2018-07-23/L16_02130` | complete `10432x7824` HDR |
| Unit-1 | `35mm` | `2018-12-26/L16_03041` | complete `10432x7824` HDR |
| Unit-2 | `28mm` | `2018-07-04/L16_02130` | complete `10432x7824` HDR |

All three select object mode `0`, enter `0x1a3c00`, and have zero observed
mode-1 `0x19f790` calls. Existing admitted Unit-1 `70mm` / `150mm` and
Unit-2 `70mm` evidence proves the complementary tele route constructs no
`MonoFusion` object. The merge-critical four-focal route partition is
therefore explicit: this formula is live at canonical `28mm` / `35mm` wide
and absent from canonical `70mm` / `150mm` tele.

The Unit-2 `28mm` run is the physical-body discriminator. No claim below
requires four redundant body/focal combinations when the static mechanism is
identical and this exact-focal body check agrees.

## Reusable Artifacts

- Runtime callback probe:
  `tools/lldb_probes/prefusion_monofusion_worker/monofusion_worker_probe.py`
- Unit-1 `28mm` / `35mm` and Unit-2 `28mm` LLDB scripts in the same directory
- Runtime validator:
  `tools/lldb_probes/prefusion_monofusion_worker/validate_reports.py`
- Installed-bundle/schema/LRI verifier:
  `tools/lldb_probes/prefusion_monofusion_worker/verify_monofusion_worker.py`
- Direct x86_64 transform probe:
  `tools/lldb_probes/prefusion_monofusion_worker/probe_dct.c`
- Transform runner and validator:
  `run_dct_probe.sh`, `validate_dct_probe.py`
- Ignored raw reports, completed HDR files, and transform output:
  `runs/prefusion_monofusion_worker/`

Commands:

```bash
python3 tools/lldb_probes/prefusion_monofusion_worker/verify_monofusion_worker.py
python3 tools/lldb_probes/prefusion_monofusion_worker/validate_reports.py
tools/lldb_probes/prefusion_monofusion_worker/run_dct_probe.sh
```

The static verifier pins installed `libcp.dylib` SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`
and full hashes of the initializer, worker, lifting, inverse, noise, Wiener,
and affine helper bodies.

## Public Input Names

Embedded installed descriptors prove:

```text
LightHeader.sensor_data
  -> SensorData.type
  -> SensorData.data
  -> SensorCharacterization.black_level
  -> SensorCharacterization.white_level
  -> SensorCharacterization.cliff_slope
  -> SensorCharacterization.vst_model[]
       .gain
       .threshold
       .scale
       .panchromatic.a
       .panchromatic.b

CameraModule.sensor_analog_gain
CameraModule.sensor_digital_gain
CameraModule.sensor_exposure
CameraModule.sensor_bayer_red_override
```

The exact public `SensorType` enum maps `2` to `SENSOR_AR1335` and `3` to
`SENSOR_AR1335_MONO`. All three LRIs carry one type-2 characterization:

```text
black_level  = 42
white_level  = 1023
cliff_slope  = 2
vst gains    = 100, 125, ..., 775
```

Every gain row has a public `panchromatic.{a,b}` model. These rows are a
negative discriminator, not MonoFusion coefficient custody:

| Run | analog | digital | exposure | selected gain row | public panchromatic `(a,b)` |
|---|---:|---:|---:|---:|---|
| Unit-1 `28mm` | `1.5` | `1.015625` | `14639008` | `150` | `(0.000302086235, -1.20084460e-05)` |
| Unit-1 `35mm` | `1.0` | `1.0` | `2606820` | `100` | `(0.000204405005, -8.34425737e-06)` |
| Unit-2 `28mm` | `7.75` | `1.0` | `42005140` | `775` | `(0.00154010509, -5.11798571e-05)` |

Installed helper `0xef050` computes `int(sensor_analog_gain * 100)` and
selects the matching model; its failure string is
`no noise model for ISO`.

The source `CapturedImage` is A2/key `1`, with internal sensor type `3`,
`SENSOR_AR1335_MONO`. Installed sensor-response lookup returns

```text
R = 2.3183400630950928
```

for that type in both physical-body runs. `R` is not the public
`SensorCharacterization.cliff_slope`, which is exactly `2.0`.

Corrective static/runtime proof closes the selected model as an installed
type-3 table row. There is no public-row-to-prepared-model conversion in this
path.

## Initializer Formula

The initializer finds one negative-override mono source (`N=1`, A2) and
counts four enabled same-group non-mono records (`C=4`) in all detailed
two-body packets. With response `R`, it stores:

```text
alpha       = C / (N*R + C)
noise_scale = 1 + C/R
```

Observed float32 values:

```text
alpha       = 0.6330776214599609
noise_scale = 2.725372314453125
```

For installed selected panchromatic coefficients `a_selected,b_selected`:

```text
a = a_selected / (R*C)
b = b_selected / (R*C)
```

The two detailed runs reproduce the stored words exactly:

| Run | installed selected `(a,b)` | stored scaled `(a,b)` |
|---|---|---|
| Unit-1 `28mm` | `(0.000306340138, -1.22690735e-05)` | `(3.30344265e-05, -1.32304513e-06)` |
| Unit-2 `28mm` | `(0.00148293283, -4.71424755e-05)` | `(0.000159913208, -5.08364565e-06)` |

The selected values are installed float32 constants and differ from the
corresponding public type-2 protobuf wire floats.

Initializer helper `0x1b3cd0` and `0x1b4390` give the exact source
normalization:

```text
normalized_source = (raw_source - black_level) * frame_scale + black_level
```

All three runs use `black_level=42`; observed `frame_scale` is
`0.220768139`, `0.215327546`, and `0.215692997`, respectively. Corrective
formula proof closes:

```text
frame_scale =
  (A1.sensor_exposure * A1.sensor_analog_gain)
  /
  (A2.sensor_exposure * A2.sensor_analog_gain * R)
```

with float32 evaluation at every operation. `sensor_digital_gain` is not an
operand.

## Mode-0 Block Topology

`0x1a3c00` requires equal nonzero source and flow-vector counts. The tested
packets have:

```text
target/source image = 4160 x 3120
flow image          = 519 x 389
source count        = 1
flow count          = 1
patch               = 16 x 16
patch step          = 8 x 8
```

Each reduced flow sample is a signed-short `(x,y)` displacement. Helper
`0x1a2520` extracts an edge-replicated 16x16 source patch.

### Installed transform

Forward `0x1a28f0` and inverse `0x1a2c10` are a normalized multilevel 5/3
lifting pair over the 16x16 block. The pinned active float32 constants are:

```text
1/sqrt(2)       = 0.7071067690849304
1/(2*sqrt(2))   = 0.3535533845424652
sqrt(2)         = 1.4142135381698608
1/2             = 0.4999999701976776
```

The interior lifting equations have the exact installed form:

```text
d_i = x_odd/sqrt(2) - (x_even_left + x_even_right)/(2*sqrt(2))
s_i = sqrt(2)*x_even + (d_left + d_right)/2
```

The full forward, inverse, boundary, packing, and recursive helper bodies are
SHA-pinned by the verifier. The direct basis probe additionally proves:

```text
constant forward DC = 15.9999981
constant round-trip max error = 3.57627869e-7
impulse round-trip max error  = 1.19209290e-7
```

A plain row-major orthonormal DCT-II is refuted: installed-vs-DCT impulse
maximum errors are `0.598` and `0.773`. Earlier DCT shorthand must not be
used.

The follow-up `bundle_installed_prefusion_monofusion_transform_edges.md`
exhaustively closes the clean-room edge extension, interleaved coefficient
packing, and forward/inverse lattice schedule with complete 256-basis
matrices.

## Patch Noise Formula

For target patch pixels `I_j`, pixel count `P`, scaled panchromatic model
`(a,b)`, black `B`, white `W`, and the separately computed mean `mu` of the
corresponding public-vignetting auxiliary view, helper `0x18e940` computes:

```text
H = sqrt(P / sum_j(1 / (I_j + 0.1)^2))
z = max(B/W, (B + (H-B)/mu) / W)
V = (mu*W)^2 * max(1e-5, a*z + b)
```

Installed constants `0.1`, `1.0`, and float32 `1e-5` are byte-pinned. The
body uses reciprocal instructions, so bit-level parity should preserve its
float32 evaluation order.

## Coefficient-Domain Wiener Blend

The fixed 16x16 coefficient-weight table is installed at `0x5d0070` behind
descriptor `0x5cedf0`. Its exact 1024 bytes have SHA-256:

```text
3eebf27ff044f8a715e45ab3fe17972728f2bf0e596d1259d7d2aa3d25c85ca4
```

The verifier validates the hash and emits all 256 exact float32 values with:

```bash
python3 tools/lldb_probes/prefusion_monofusion_worker/verify_monofusion_worker.py \
  --dump-coefficient-table
```

For target coefficient `T_k`, aligned source coefficient `S_k`, table value
`F_k`, patch variance `V`, and initializer `noise_scale`:

```text
lambda_k = V * noise_scale * F_k
delta2_k = (S_k - T_k)^2
w_k      = delta2_k / (delta2_k + lambda_k)
S_k      = w_k*T_k + (1-w_k)*S_k
confidence = (256 - sum_k(w_k)) / 256
```

`0x18da80` initializes the confidence accumulator to float32 `256` and
multiplies by exact `1/256 = 0.00390625` after all coefficients. It uses
approximate packed reciprocals for `w_k`. Thus `w_k` is the target/rejection
weight and confidence is the grouped mean source-retention weight
`mean(1-w_k)`.

The inverse transform returns the blended spatial patch. Invalid source
overlap falls back to the target patch.

## Overlap and Final Scalar Blend

The one-dimensional overlap tap is:

```text
h(i) = 0.5 * (1 - cos(2*pi*(i+0.5)/16)),  i=0..15
```

The installed constants are double `0.5` and float-derived double
`2*pi = 6.2831854820251465`. The 2D overlap weight is separable
`h(x)*h(y)`, with 8-pixel patch spacing.

After overlap accumulation, the mode-0 scalar result is:

```text
mono = alpha * target + ((1-alpha)/N) * accumulated_sources
```

For the canonical wide route, `N=1`. The follow-up
`bundle_static_runtime_prefusion_monofusion_confidence_callback_two_body.md`
closes the secondary-map callback and its overlap-add formula.

The already-admitted `0x1b3530` wrapper then combines this scalar result with
the target vec4 image through its two 3x3 coefficient packs and preserves
target alpha.

## Verification Output

```text
prefusion_monofusion_transform=OK
plain_row_major_orthonormal_DCT_II=REFUTED
prefusion_monofusion_worker_static=OK
transform=normalized_5/3_lifting_forward_inverse_pair
half_Hann(i)=0.5*(1-cos(2*pi*(i+0.5)/16))
public_to_internal_vst_preparation=NOT_CLAIMED
prefusion_monofusion_worker=OK
unit1_28mm: mode=0 branch=0x1a3c00 subtract=42 multiply=0.220768139 add=42
unit1_35mm: mode=0 branch=0x1a3c00 subtract=42 multiply=0.215327546 add=42
unit2_28mm: mode=0 branch=0x1a3c00 subtract=42 multiply=0.215692997 add=42
```

## Admission and Remaining Boundary

Admitted, with canonical four-focal route scope and Unit-2 wide
discriminator:

- public A1/A2 capture selectors and exact exposure/analog affine formula;
- installed type-3 panchromatic VST source;
- initializer count/response/blend/noise-scaling formulas;
- black-level affine source normalization;
- mode-0 16x16/step-8 flow-aligned block topology;
- normalized 5/3 lifting forward/inverse transform identity and active
  equations;
- exact fixed 16x16 coefficient-weight table custody;
- exact patch-noise and coefficient Wiener formulas;
- exact half-sample Hann overlap formula; and
- final target/source scalar blend.

Not admitted:

- mode-1 `0x19f790`, absent under the tested production-profile runs;
- noncanonical source counts/IDs;
- the outer distributed IRAMP reduction and final contributor
  acceptance/rejection policy.

This materially narrows `CLM-PREFUSION-002`, but the claim remains
`OPEN/BLOCKER`.
