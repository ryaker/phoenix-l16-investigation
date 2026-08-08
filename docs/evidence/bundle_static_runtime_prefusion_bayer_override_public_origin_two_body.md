# Bundle Static/Runtime Evidence: Public Bayer-Override Origin

## Scope

This proof closes the public LRI name and origin of the two-int pair copied
through:

```text
constructor input+0x28 holder+0x18
  -> CapturedImage item+0x58/+0x5c
  -> FusionCacheBayer selector scan
```

The pair is public
`LightHeader.modules[camera].sensor_bayer_red_override`, type
`Point2I{x, y}`.

This is a field-origin and naming proof for the direct `0xe59a4 -> 0xf2770`
constructor family. It does not establish why the public override uses a
particular value, make C6 active after its later clear, or close final
contributor acceptance/rejection.

## Artifacts

- Verifier:
  [verify_bayer_override_public_origin.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_bayer_override_public_origin/verify_bayer_override_public_origin.py)
- Extended central audit:
  [lane_b_index5_public_meaning_audit.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lane_b_index5_public_meaning_audit.py)
- Runtime reports:
  `runs/capturedimage_f2770_origin/f2770_origin_{28mm,35mm,70mm,150mm}.json`
- Prior constructor custody:
  [lldb_capturedimage_f2770_origin_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_capturedimage_f2770_origin_four_zoom.md)
- Prior selector scan:
  [lldb_fusioncachebayer_scan_collection_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_fusioncachebayer_scan_collection_four_zoom.md)

Run:

```bash
python3 tools/lldb_probes/prefusion_bayer_override_public_origin/verify_bayer_override_public_origin.py
python3 tools/lane_b_index5_public_meaning_audit.py
```

## Public Schema Name

The verifier extracts and decodes the installed embedded protobuf descriptors.
They name:

```text
CameraModule field 13
  sensor_bayer_red_override
  optional .ltpb.Point2I

Point2I field 1 = required int32 x
Point2I field 2 = required int32 y
```

The embedded `point2i.proto` descriptor SHA-256 is:

```text
1a4f336364f571acc1e45173298aa1a5d8f8be208dad43b2db55edd51a5a8fcb
```

## Static Copy

The installed `libcp.dylib` is pinned by SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`.
The verifier independently pins the `0xf2d40..0xf2d7f` window and these copy
instructions:

```text
0xf2d4c  test constructor presence bit for the optional Point2I
0xf2d53  load constructor input+0x28 holder
0xf2d62  load packed Point2I x/y from holder+0x18
0xf2d6d  store x to CapturedImage+0x58
0xf2d71  store y to CapturedImage+0x5c
```

## Four-Focal Runtime Join

For every one of the `42` accepted constructor events, the verifier decodes
the matching public `CameraModule.sensor_bayer_red_override` from the LRI and
requires exact equality at both runtime boundaries:

```text
input+0x28 holder+0x18 == public Point2I{x,y}
CapturedImage+0x58/+0x5c == public Point2I{x,y}
```

The module patterns are stable within focal tier:

| Scope | Modules | Unique `(-1,-1)` key |
|---|---:|---|
| Unit-1 `28mm` / `35mm` | `10` | `A2` / key `1` |
| Unit-1 `70mm` / `150mm` | `11` | `C6` / key `15` |

All other pairs are the exact public per-camera values `(0,0)`, `(1,0)`,
`(0,1)`, or `(1,1)`.

## Two-Body Check

The public carrier is also decoded from exact-focal Unit-2 representatives
whose calibration payload SHA-256 is
`223961c6bce6153e52aa20298ab7eae7a6edb3f2824950a433fdc49df0d4ade1`:

| Body | LRI | Modules | Unique `(-1,-1)` key |
|---|---|---:|---|
| Unit-2 | `2018-07-04/L16_02130`, 28mm | `10` | `A2` / key `1` |
| Unit-2 | `2018-10-25/L16_02894`, 70mm | `11` | `C6` / key `15` |

This is the body-discriminating check needed for the public carrier. Runtime
copy custody remains the accepted Unit-1 four-focal constructor scope.

## Consequence

The former anonymous selector fields have exact public meaning:

```text
CapturedImage+0x58 = CameraModule.sensor_bayer_red_override.x
CapturedImage+0x5c = CameraModule.sensor_bayer_red_override.y
```

Therefore the `FusionCacheBayer` constructor scan's sign-bit predicate is a
predicate over the public Bayer-red override coordinates:

- wide tier finds A2/key `1` with `(-1,-1)`;
- tele tier has C6/key `15` with `(-1,-1)`, but C6 is outside the scan's
  target camera-group bucket and is later independently cleared inactive.

This removes the public-origin gap for `+0x58/+0x5c`. The remaining Lane A
unknown is the selector's algorithmic purpose and downstream distributed
reduction/acceptance policy, not the source or public name of these two fields.
