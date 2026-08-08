# Static/Runtime Proof: Public Orientation To Final Export Placement

## Result

For canonical profile-3 HDR export, public
`ViewPreferences.orientation` values `1` and `2` are not metadata-only.
They configure opposite affine transforms that are copied unchanged into
`CIAPI::Renderer::writeImage`, propagated through final helper `0x4182a0`,
and consumed by `GetExportTransformOutput` body `0x419080`.

The output canvas remains landscape `10432 x 7824`; Lumen does not swap the
writer dimensions for either 90-degree orientation.

At selected source level `8320 x 6240`, define:

```text
sx = float32(6240 / 10432) = 0.5981594920158386
sy = float32(8320 / 7824)  = 1.0633946657180786
```

The emitted row-major affine matrices map destination coordinates to selected
source-level coordinates:

```text
ORIENTATION_ROT90_CW (1):
  x_src = sy * y - 0.0001220703125
  y_src = 6240 - sx * x

ORIENTATION_ROT90_CCW (2):
  x_src = 8320 - sy * y
  y_src = sx * x
```

Both directions select source ROI `[0,0,8320,6240]`. The clockwise
`-0.0001220703125` translation is the exact installed float32 result, not a
rounded zero.

## Scope

- Installed `libcp.dylib`, SHA-256
  `b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`.
- Unit-2 exact `35mm`, public `ORIENTATION_ROT90_CW`:
  `/Volumes/Base Photos/Light/2017-12-02/L16_00622.lri`.
- Unit-1 exact `35mm`, public `ORIENTATION_ROT90_CCW`:
  `/Volumes/Base Photos/Light/2018-01-24/L16_00202.lri`.
- Existing admitted normal-orientation output proof covers canonical Unit-1
  `28/35/70/150mm` plus exact-`28mm` Unit-2.
- The complete local corpus has only orientation values `0`, `1`, and `2`.
  Dormant public enum values `3..7` and renderer profiles `1/2` are outside
  this admission.

The two rotated inputs come from different calibration bodies and firmware
eras. The installed transform mechanism is common. This evidence does not
attribute any observed difference to body or firmware.

## Public Schema And Corpus

Installed `view_preferences.proto` names the complete enum:

```text
0 ORIENTATION_NORMAL
1 ORIENTATION_ROT90_CW
2 ORIENTATION_ROT90_CCW
3 ORIENTATION_ROT90_CW_VFLIP
4 ORIENTATION_ROT90_CCW_VFLIP
5 ORIENTATION_VFLIP
6 ORIENTATION_HFLIP
7 ORIENTATION_ROT180
```

The rerunnable `9,438`-file census finds these values among the `9,242`
structurally complete inputs:

```text
0: 8769
1:  408
2:   65
```

No complete local LRI uses values `3..7`.

## Installed Formula

Accessor `0x13f180` returns `ViewPreferences+0x2c`. Final setup body
`0x3c6450` calls it at `0x3c65c0` and `0x3c65e8`, checks the optional-present
byte, rejects values greater than `7`, and returns the public value.

Renderer initialization then:

1. stores the new `CIAPI::Transform` at owner `+0xb0`;
2. queries property selector `2`;
3. calls `0x39b800 -> 0x402830` with that orientation;
4. retains the transform for `Renderer::writeImage`.

`TransformImpl` constructor `0x401bf0` reduces full dimensions by their GCD,
so `10432 x 7824` becomes aspect-domain `4 x 3`.

For reduced dimensions `(W,H)`, `0x402830` writes these internal matrices:

```text
CW:
  [ 0, -1, 0,
    1,  0, 0,
    (W-H)/2, (W+H)/2, 1 ]

CCW:
  [ 0,  1, 0,
   -1,  0, 0,
    (W+H)/2, (H-W)/2, 1 ]
```

It also writes the normalized envelope:

```text
[
  (1 - H/W)/2,
  (1 - W/H)/2,
  (1 + H/W)/2,
  (1 + W/H)/2
]
```

For `4 x 3`, runtime captures are:

```text
CW matrix:   [0,-1,0, 1,0,0, 0.5,3.5,1]
CCW matrix:  [0, 1,0,-1,0,0, 3.5,-0.5,1]
envelope:    [0.125,-0.1666666865,0.875,1.166666746]
```

`GetExportTransformOutput` body `0x419080`:

- scales the transform through `0x402a90`;
- reads the transform envelope through `0x402c20`;
- transforms the envelope corners;
- chooses a source level;
- rounds the transformed bounds, expands them by two pixels, and clamps to
  the selected source dimensions;
- emits the source ROI, two float32 scales, and final affine matrix.

## Runtime Custody

Each admitted run records:

```text
orientation accessor hits             2
orientation transform construction    1
CIAPI::Transform matrix-copy reads     9
scaled transform outputs               2
completed TransformOutput records      2
final output helper                    1
writer virtual call                    1
process exit                           0
```

For each direction:

- the first `0x39b68a` copy source is the exact transform pointer configured
  at `0x402a03`;
- all nine copies preserve every matrix and envelope float;
- the first copy stack includes `CIAPI::Renderer::writeImage`;
- the last three copy stacks include final helper `0x4182a0`;
- both `0x419080` invocations emit the same final ROI/scales/matrix;
- the final writer descriptor is `10432 x 7824`, row bytes `166912`,
  bytes per pixel `16`.

The intermediate selected-level matrices are:

```text
CW:  [0,-1,0, 1,0,0, 1040,7280,1]
CCW: [0, 1,0,-1,0,0, 7280,-1040,1]
```

The completed final matrices are:

```text
CW:
  [0,  1.0633946657, -0.0001220703125,
  -0.5981594920, 0, 6240,
   0, 0, 1]

CCW:
  [0, -1.0633946657, 8320,
   0.5981594920, 0, 0,
   0, 0, 1]
```

## Reproduction

```bash
bash tools/lldb_probes/output_orientation_policy/run_two_body.sh
python3 tools/lldb_probes/output_orientation_policy/verify_output_orientation_policy.py
```

Artifacts:

- `tools/lldb_probes/output_orientation_policy/output_orientation_policy_probe.py`
- `tools/lldb_probes/output_orientation_policy/unit2_35mm_cw.lldb`
- `tools/lldb_probes/output_orientation_policy/unit1_35mm_ccw.lldb`
- `tools/lldb_probes/output_orientation_policy/run_two_body.sh`
- `tools/lldb_probes/output_orientation_policy/verify_output_orientation_policy.py`
- `runs/output_orientation_policy/`
- `runs/lri_consumed_block_roles/corpus_contract.json`

## Consequence

For complete local profile-3 inputs, public orientation placement is now
formula-level closed across every observed enum value. A clean-room
implementation matching Lumen must preserve the landscape writer canvas and
apply the destination-to-source affine map above; merely writing an EXIF
orientation tag or swapping output dimensions does not match the installed
path.

This narrows `CLM-OUTPUT-002` but does not close it. The tested Radiance file
still does not self-identify linear ProPhoto primaries, and the independent
application still needs one correctly tagged modern output contract.
