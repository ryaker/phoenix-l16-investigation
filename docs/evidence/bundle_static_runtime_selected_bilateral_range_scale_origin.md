# Static and Runtime Proof: Selected Bilateral Range-Scale Origin

## Scope

This bundle closes the generated `range_scale` input used by the admitted
selected `0x2fb320` / `0x2fd070` bilateral workers and the downstream
PatchNLM path. It identifies the public inputs, installed calibration table,
exact two-stage float32 formula, fixed matrix, and live floor value.

Runtime scope is the canonical Unit-1 `28mm`, `35mm`, `70mm`, and `150mm`
profile-3 quartet plus exact-35mm Unit-2. Installed arithmetic is SHA-pinned.
This is not a claim about unselected denoise arms or alternate profiles.

## Artifacts

- Verifier:
  `tools/lldb_probes/selected_bilateral_formula/verify_range_scale_origin.py`
- Machine-readable result:
  `runs/selected_bilateral_formula/range_scale_origin.json`
- Reused retained reports:
  `runs/awb_public_origin/`, `runs/capturedimage_f2770_origin/`,
  `runs/2f53d0_downstream_helpers/`, `runs/denoise_route_census/`, and
  `runs/selected_bilateral_formula/`

Reproduce with:

```bash
python3 tools/lldb_probes/selected_bilateral_formula/verify_range_scale_origin.py \
  --json-out runs/selected_bilateral_formula/range_scale_origin.json
```

Accepted result:

```text
capturedimage_public_capture_fields=OK ... events=42 ... unit2_runtime_events=10
static_selected_bilateral=OK ... constants=abs_mask,alpha_lane,one,epsilon
selected_bilateral_range_scale=OK ... vst_rows=28 scope=unit1_four_focal+unit2_35mm
```

## Installed Pin

Installed `libcp.dylib` SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

The verifier pins the complete custody/formula bodies at `0x342b80`,
`0x342ca0`, `0x344470`, `0x345920`, `0xef050`, `0xef890`, `0xefa50`,
`0x2f4470`, `0x2f53d0`, `0x2f5fa0`, and `0x2f63f0`. The exact hashes are
emitted in the JSON result.

Installed RTTI independently identifies the selected wrapper families as:

- `Pipeline::setDenoising(...)::$_51`, operating on three `vec4x32f` images;
- `$_53`, operating on `BayerFloatPipelinePayload`; and
- `$_55`, operating on `ColorPipelinePayload`.

This explains the canonical wide/tele wrapper difference without assigning a
body or firmware cause: both payload wrappers reach the same formula body.

## Public And Installed Origins

The public/input custody is:

```text
LightHeader.view_preferences.awb_gains.{r,g_r,b}
  -> neutral = float32(1/r, 1/g_r, 1/b)
  -> payload[0][0..2]

CameraModule.sensor_analog_gain
  -> CapturedImage+0x40
  -> int(float32(gain * 100))
  -> lower_bound installed RGB SensorGainVars row
```

The same `payload[0]` pointer is used at both relevant stages:

- `0x342ca0 -> 0x342b80 -> 0x2eb560` passes it unchanged as the three-float
  demosaic neutral vector. Independent stopped-frame proof matches that vector
  exactly to reciprocal public AWB at all four canonical focals.
- `0x344470 -> 0xef890 -> 0xefa50` passes it unchanged as callback `+0x18`,
  where `0xefa50` reads the same first three floats.

`0x344470` obtains gain through `0xf32d0(CapturedImage)`, which returns
`CapturedImage+0x40`. The existing constructor verifier is rerun here and
exactly joins all 42 Unit-1 four-focal events and 10 Unit-2 28mm events to
public `CameraModule.sensor_analog_gain`.

The selected noise coefficients and level constants have installed-bundle
numeric custody. The installed RGB SensorGainVars table has 28 rows at gain
keys `100..775` step `25`; every row has RGB black `42`, white `1023`, and
named `red/green/blue.{a,b}` coefficients. These names are schema-equivalent
to public `SensorCharacterization.vst_model[]`, but the installed coefficients
are measurably different from the LRI type-2 rows. Do not replace them with
the public numeric rows. The installed black/white values happen to match the
canonical public type-2 values.

## Stage 1: RGB Standard Deviation

For source `vec4` pixel `x`, use the first three channels. Define:

```text
n = float32(1 / awb_gains.{r,g_r,b})
B = 42.0f
W = 1023.0f
A = selected installed (red.a, green.a, blue.a)
C = selected installed (red.b, green.b, blue.b)
```

The exact installed operation order is:

```text
invW   = float32(1.0f / W)
span   = float32(float32(W - B) * invW)
scale  = float32(n * span)                 // componentwise
offset = float32(B * invW)
u      = float32(float32(x * scale) + offset)
v      = float32(float32(u * A) + C)
sigma_rgb = sqrt(max(float32(1e-5), v))
```

The variance floor is exact float32 bits `0x3727c5ac` in all four SIMD lanes,
or `9.999999747378752e-06`. This corrects the earlier bounded static
description that treated the max operand as zero.

## Stage 2: Ohta Variance Propagation

The installed matrix is row-major:

```text
M = [
  [ 0.5773500204086304,  0.5773500204086304,  0.5773500204086304],
  [ 0.7071099877357483,  0.0,                 -0.7071099877357483],
  [ 0.40825000405311584,-0.8165000081062317,  0.40825000405311584]
]
```

For output channel `j`, `0x2f4470 -> 0x2f5fa0` computes:

```text
s2[c] = float32(sigma_rgb[c] * sigma_rgb[c])
m2[j,c] = float32(M[j,c] * M[j,c])

tR = float32(s2[R] * m2[j,R])
tG = float32(s2[G] * m2[j,G])
tB = float32(s2[B] * m2[j,B])
variance_ohta[j] = float32(tB + float32(tG + tR))
sigma_ohta[j] = sqrt(variance_ohta[j])
```

The generated callback image is then:

```text
range_scale = max((0.0024999999441206455, 0, 0, 0),
                  (sigma_ohta[0], sigma_ohta[1], sigma_ohta[2], 0))
```

The floor is exact float32 bits `0x3b23d70a`. All six retained `0x2f53d0`
samples in each Unit-1 focal report and exact-35mm Unit-2 carry that same
`config+0x18` word. Final range-scale lane 3 is zero.

For bit-oriented parity, preserve the two separate `sqrt`/square stages and
the stated float32 addition order. Algebraically collapsing them changes
rounding and the `1e-5` first-stage floor.

## Runtime Join

- Accepted `0x2f4470` capped-window count: `128` at each canonical Unit-1
  focal tier.
- Retained `0x2f53d0` config checks: six samples each at Unit-1
  `28/35/70/150mm` and Unit-2 exact `35mm`.
- Final selected bilateral callback replay remains 16 Unit-1 35mm radius-2
  samples plus eight Unit-2 35mm radius-4 samples. Every captured generated
  range scale has lane 0 at or above the live `0.0025f` floor and lane 3 zero.

The retained reports do not contain all intermediate per-pixel Stage-1
operands, so this bundle does not claim an end-to-end runtime replay from raw
pixel to final range-scale word. Formula proof is installed static; runtime
proves public carrier values, selected-route liveness, config words, and final
callback custody.

## Admission

Admit as `CLM-DENOISE-002` and `CLM-DENOISE-001` addenda:

- exact generated `range_scale` arithmetic and operation order;
- public reciprocal `ViewPreferences.awb_gains` neutral origin;
- public per-`CapturedImage` `CameraModule.sensor_analog_gain` selector;
- installed RGB SensorGainVars `red/green/blue.{a,b}` numeric custody;
- exact installed black/white, `1e-5`, Ohta matrix, and `0.0025` floor values;
- Unit-1 four-focal liveness with exact-35mm Unit-2 route/control coverage.

Non-admissions:

- LRI-public numeric custody for the installed RGB SensorGainVars rows;
- a public protobuf name for internal `config+0x18`;
- liveness or equivalence of unselected kernel-size / boolean arms;
- a body/firmware cause for the wide/tele payload-wrapper selection.
