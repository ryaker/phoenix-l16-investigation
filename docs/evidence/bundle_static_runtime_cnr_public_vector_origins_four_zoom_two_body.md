# Static and Runtime Proof: ColorNoiseReduction Vector Origins

## Scope

This bundle extends
`bundle_static_runtime_cnr_worker_formula_four_zoom_two_body.md` by naming and
proving the origins of the four live CNR worker vectors `V10`, `V20`, `V30`,
and `V40`.

Coverage is Unit-1 canonical profile-3 bridge-HDR `28mm`, `35mm`, `70mm`, and
`150mm`, plus an exact-35mm Unit-2 control. This closes only the vector
origin/name gap for `CLM-DENOISE-002`. At this evidence stage, the matrix
helper `0x309270 -> 0x309d50` and the Unit-2 exact-35mm `0x2fd070`
sibling-arm selector remained open. The later
`bundle_static_runtime_cnr_matrix_helper_svd_four_zoom_two_body.md` proof
closes the matrix-helper gap only. The later
`bundle_static_runtime_denoise_selector_2fd070_two_body.md` proof closes the
selector-cause gap only.

## Artifacts

Reusable verifier:

- `tools/lldb_probes/denoise_route_census/verify_cnr_public_origins.py`

Inputs reused from the worker-formula proof:

- `runs/denoise_route_census/unit1_28mm_cnr_formula.json`
- `runs/denoise_route_census/unit1_35mm_cnr_formula.json`
- `runs/denoise_route_census/unit1_70mm_cnr_formula.json`
- `runs/denoise_route_census/unit1_150mm_cnr_formula.json`
- `runs/denoise_route_census/unit2_35mm_cnr_formula.json`

Verifier outputs:

- `runs/denoise_route_census/cnr_public_origins.json`
- `runs/denoise_route_census/verify_cnr_public_origins.txt`

Verifier result:

```text
cnr_public_origins=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9 table=5e3f94c8b13b11c3c144dc765587479e49e4508d033a4a3603a026e486df104d selected=unit1_28mm:100,unit1_35mm:100,unit1_70mm:100,unit1_150mm:100,unit2_35mm:400
```

The verifier parses the public LRI records with `tools/lri_field_inspect.py`,
extracts the installed RGB SensorGainVars table from the SHA-pinned bundle,
and byte-compares the expected vectors against the live `0x307ee0` parameter
block captured by the formula probes.

## Static Proof

The verifier pins the installed `libcp.dylib` SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

It also pins the setup body and extracted installed table:

| Artifact | Range / role | SHA-256 |
|---|---:|---|
| CNR setup | `0x34b3f0..0x34b808` | `6f7ac1fc4faf18ccc4ef5c9b70dff4336a807ff53194efcb357ba25e467fbf0d` |
| Installed RGB SensorGainVars JSON | rows `100..775` step `25` | `5e3f94c8b13b11c3c144dc765587479e49e4508d033a4a3603a026e486df104d` |

The pinned setup call surface is:

| Callsite | Target | Role |
|---:|---:|---|
| `0x34b439` | `0xf3340` | returns the live CNR characterization/table carrier |
| `0x34b445` | `0xf32d0` | returns the public camera gain carrier |
| `0x34b451` | `0xef050` | selects the SensorGainVars row |
| `0x34b460` | `0xf0610` | copies the selected row |
| `0x34b6bb` | `0x307ee0` | launches the CNR body with the built parameter block |

Static inspection of `0xef050` verifies the row-key formula:

```text
raw_key = int(float32(sensor_analog_gain * 100.0))
selected_row = first installed SensorGainVars row with row.gain >= raw_key
```

The `100.0` multiplier is the float32 constant at `0x5ae770`. This is a
lower_bound-style selector over the installed rows.

## Vector Mapping

The live parameter block vectors are:

```text
V10 = (1 / awb_gains.r, 1 / awb_gains.g_r, 1 / awb_gains.b, 1)
V20 = 1 / (V10 * V10)
V30 = (selected.red.a, selected.green.a, selected.blue.a, 0)
V40 = (selected.red.b, selected.green.b, selected.blue.b, 0)
```

`V10` uses public `LightHeader.view_preferences.awb_gains.{r,g_r,b}`. The
green lane is `g_r`; `g_b` is present in the public message but is not used by
this CNR parameter vector. `V20` is derived from `V10`.

`V30` and `V40` use public selector custody:

```text
LightHeader.image_reference_camera
  -> LightHeader.modules[reference].sensor_analog_gain
  -> int(float32(sensor_analog_gain * 100.0))
  -> installed RGB SensorGainVars lower_bound row
```

The coefficient names are schema-equivalent to public
`SensorCharacterization.vst_model[].{red,green,blue}.{a,b}`, but the numeric
coefficient custody on this installed route is the installed bundle table, not
the LRI's public type-2 rows. The verifier finds a public type-2 row for every
tested selected gain and verifies `public_equals_installed = false` for every
tested LRI.

## Coverage

| Sample | Focal | Reference camera | Public reference gain | Raw key | Installed row | Public type-2 row equals installed? |
|---|---:|---:|---:|---:|---:|---|
| Unit-1 `28mm` `L16_02130` | `28` | `0` | `1.0` | `100` | `100` | no |
| Unit-1 `35mm` `L16_03041` | `35` | `0` | `1.0` | `100` | `100` | no |
| Unit-1 `70mm` `L16_03434` | `70` | `8` | `1.0` | `100` | `100` | no |
| Unit-1 `150mm` `L16_02285` | `149` | `8` | `1.0` | `100` | `100` | no |
| Unit-2 exact `35mm` `L16_01956` | `35` | `0` | `3.875` | `387` | `400` | no |

Selected installed coefficient rows used by the tested samples:

| Row | `red.a` | `green.a` | `blue.a` | `red.b` | `green.b` | `blue.b` |
|---:|---:|---:|---:|---:|---:|---:|
| `100` | `0.00019453687127679586` | `0.00019225437426939607` | `0.00019354157848283648` | `-7.4401973506610375e-06` | `-7.228214144561207e-06` | `-7.3382539085287135e-06` |
| `400` | `0.0007358293514698744` | `0.0007364588091149926` | `0.0007340562297031283` | `-2.6041971068480052e-05` | `-2.497744389984291e-05` | `-2.5868637749226764e-05` |

The full installed table has 28 rows, `100..775` in steps of `25`, and is
captured in `runs/denoise_route_census/cnr_public_origins.json`.

## Admission

This is a `CLM-DENOISE-002` partial-strengthening:

- admitted: public origin/name for `V10` as reciprocal
  `LightHeader.view_preferences.awb_gains.{r,g_r,b}` with alpha `1`;
- admitted: `V20` as the derived reciprocal square of `V10`;
- admitted: selector and schema-equivalent names for `V30` / `V40` as installed
  RGB SensorGainVars `red/green/blue.{a,b}` selected by public
  `LightHeader.image_reference_camera -> modules[].sensor_analog_gain`;
- admitted: Unit-1 `28/35/70/150mm` selects installed row `100`;
- admitted: exact-35mm Unit-2 selects installed row `400`, because
  `int(float32(3.875 * 100.0)) = 387` and the lower_bound row is `400`;
- superseded by later proof: clean-room internals of
  `0x309270 -> 0x309d50` or an independently specified equivalent;
- superseded by later proof: selector cause for the Unit-2 exact-35mm extra
  `0x2fd070` denoise sibling arm.
