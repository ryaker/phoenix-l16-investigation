# Static/Runtime Evidence: Complete LRI Consumed-Block Contract

## Result

The image-producing LELR input contract is decoded for every structurally
complete LRI in the local corpus.

The installed reader accepts exactly three record types:

| LELR `msg_type` | Protobuf message |
|---:|---|
| `0` | `ltpb.LightHeader` |
| `1` | `ltpb.ViewPreferences` |
| `2` | `ltpb.GPSData` |

Standalone type-1 and type-2 messages are wrapped into the corresponding
`LightHeader` field, and all records are merged in file order. A clean-room
reader must therefore merge partial preference records; selecting only the
last record or only `LightHeader.view_preferences` is wrong.

## Custody

- Installed binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- SHA-256:
  `b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`
- Canonical runtime:
  Unit-1 `28mm`, `35mm`, `70mm`, and `150mm`, profile `3`,
  `--no-auto-lris`
- Archive census:
  `9,438` LRIs below `/Volumes/Base Photos/Light`
- Reusable verifier:
  `tools/lldb_probes/lri_consumed_block_roles/verify_lri_consumed_block_roles.py`
- Archive census:
  `tools/lldb_probes/lri_consumed_block_roles/census_lri_block_contract.py`
- Runtime harness:
  `tools/lldb_probes/lri_consumed_block_roles/run_four_zoom.sh`
- Raw rerunnable reports:
  `runs/lri_consumed_block_roles/`

The corpus contains both independently proved calibration bodies and many
firmware versions. This evidence does not attribute layout differences to
body.

## Installed Reader Proof

The LELR parser is `0x13cc80`, called at `0xe532c`. Its type dispatch is:

- type `0`: parse directly into `LightHeader`;
- type `1`: `0x13cdef -> 0x180a50`, whose RTTI is
  `ltpb::ViewPreferences`, retained at `LightHeader+0xe0`;
- type `2`: `0x13cdc7 -> 0x187170`, whose RTTI is `ltpb::GPSData`,
  retained at `LightHeader+0x100`.

`0xe52c0` iterates the resulting records and merges present fields. The four
runtime reports reproduce every file's exact ordered `(msg_type,msg_len)`
sequence at `0x13cda3`.

## Complete Block Roles

The canonical wide inputs contain 11 records and the tele inputs contain 12
because tele has three raw chunks rather than two. Their non-raw roles are:

1. geometry calibration;
2. vignetting calibration;
3. sensor characterization;
4. color calibration;
5. device calibration;
6. partial `ViewPreferences` records;
7. GPS metadata.

All type-0 fragments are public `LightHeader` messages. The calibration
fragments use the already admitted public fields:

- `FactoryModuleCalibration.geometry`;
- `FactoryModuleCalibration.vignetting`;
- `FactoryModuleCalibration.color`;
- `LightHeader.sensor_data`;
- `LightHeader.device_calibration`.

### Sensor characterization

All four canonical inputs carry:

```text
SensorData.type = SENSOR_AR1335 (2)
SensorCharacterization.black_level = 42
SensorCharacterization.white_level = 1023
SensorCharacterization.cliff_slope = 2
vst_model gain keys = 100,125,...,775
vst_model count = 28
```

Existing admitted MonoFusion evidence consumes the black/white/cliff values
and proves that its mono VST coefficients instead come from the different
installed type-3 table. This block is decoded even where one particular
consumer excludes its type-2 VST rows.

## Preference Merge And Live Formulas

Each canonical input executes three calls to the field-wise merge body
`0x13eda0`: one standalone image-target record, one wrapped crop/AWB record,
and one standalone EV/orientation/aspect record.

The merged public crop is converted from `(start,size)` to:

```text
(start.x, start.y, float32(start.x + size.x), float32(start.y + size.y))
```

and the live crop-policy helper returns that exact four-float rectangle:

| Focal | Merged crop |
|---|---|
| `28mm` | `(0,0,1,1)` |
| `35mm` | `(0.0956730768,0.104487181,0.895673096,0.904487193)` |
| `70mm` | `(0.00288461545,0.00256410264,0.997115374,0.996794879)` |
| `150mm` | `(0.266826928,0.266666681,0.733173072,0.733333349)` |

`ViewPreferences.image_gain` and
`ViewPreferences.image_integration_time_ns` are live. For each
`CapturedImage`, `0xf3fc0` computes exactly:

```text
numerator   = float32(float32(image_integration_time_ns) * image_gain)
denominator = float32(float32(sensor_exposure) * sensor_analog_gain)
scale       = float32(numerator / denominator)
```

Every captured return at all four focal tiers replays bit-exactly from the
merged public target and the already admitted public
`CameraModule.sensor_exposure` / `sensor_analog_gain` copies.

The complete renders also execute crop, disable-crop, AWB, and orientation
accessors. EV-offset, display-gain, display-integration, aspect-ratio, and GPS
accessors record zero hits under the same quartet. These are tested-path
zeroes, not binary-wide non-use claims.

## Device Calibration And GPS

The canonical device block is:

```text
FactoryDeviceCalibration.flash:
  ledcool_lux        = 314.7666320800781
  ledcool_max_lumens = 418.6396484375
  ledcool_cct        = 4962.73291015625
  ledwarm_lux        = 315.63568115234375
  ledwarm_max_lumens = 419.79547119140625
  ledwarm_cct        = 2364.2685546875
```

Runtime object scanning finds the exact six-float sequence in the parsed
generated object behind `LightHeader+0xd0`. A complete Capstone instruction
census over the sole CaptureStack record-merge body `0xe52c0..0xe5f8c` finds
zero reads of source `LightHeader+0xd0`; the flash calibration is therefore
parsed but not carried into canonical merged-image state.

GPS is carried into `CaptureStack+0x1a8`. Its only installed accessor callers
are `0x419d6d` and `0x419d7e` in the output metadata serialization body, and
the accessor records zero hits in all four tested HDR renders. GPS is output
metadata, not a merged-pixel input.

## Full Corpus Census

Of `9,438` local LRIs:

- `9,242` are structurally complete;
- `196` are structurally incomplete;
- complete files contain only record types `0`, `1`, and `2`;
- no complete file contains a field outside the installed public schemas;
- every complete file has raw, geometry, vignetting, sensor, color, device,
  preference, and GPS roles;
- no complete file is missing an image-critical role.

Preference layout is firmware-era variation:

- `2,906` complete files carry the gain message directly in a standalone
  `ViewPreferences` record;
- `6,336` carry it under `LightHeader.view_preferences`.

Every complete input carries public fields `ev_offset`, `awb_mode`,
`orientation`, `image_gain`, `image_integration_time_ns`, `aspect_ratio`,
`crop`, `awb_gains`, and `is_on_tripod`. All have `awb_mode=0` and
`aspect_ratio=0`. Orientation values are:

```text
ORIENTATION_NORMAL    (0): 8769
ORIENTATION_ROT90_CW  (1):  408
ORIENTATION_ROT90_CCW (2):   65
```

This corrects the older over-broad wording that every complete LRI omits
`awb_mode`: the gain-bearing message omits it, but a separate preference
record explicitly supplies `AWB_MODE_AUTO`.

The `2,906` legacy layouts additionally carry `qc_lux_index`; the `6,336`
newer layouts carry `display_gain` and `display_integration_time_ns`. This
split must not be represented as a physical-body effect.

## Scope

This closes the LELR record/schema/merge contract for every structurally
complete local input and the image-critical preference formulas observed in
canonical profile `3`.

It does not claim that GPS or flash metadata must be preserved by a
pixel-parity implementation. It also does not close the separate output-lane
requirement to validate final placement/tagging for the `473` complete inputs
with non-normal public orientation.
