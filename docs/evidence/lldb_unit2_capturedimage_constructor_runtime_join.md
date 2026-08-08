# Unit-2 CapturedImage Constructor Runtime Join

## Question

Obtain the previously missing Unit-2 runtime packet for direct
`CameraModule` sensor fields copied by constructor `0xf2770`.

## Input and body identity

- Exact-focal Unit-2 `28mm`:
  `/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri`
- Unit identity:
  per-file intrinsics calibration SHA-256 prefix `223961c6bce6153e`
- Installed `libcp.dylib` SHA-256:
  `b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`

## Reusable artifacts

- `tools/lldb_probes/capturedimage_f2770_origin/f2770_origin_probe.py`
- `tools/lldb_probes/capturedimage_f2770_origin/f2770_origin_unit2_28mm.lldb`
- `tools/lldb_probes/capturedimage_f2770_origin/run_unit2_28mm.sh`
- `tools/lldb_probes/capturedimage_f2770_origin/verify_public_capture_fields.py`
- ignored report/output:
  `runs/capturedimage_f2770_origin/f2770_origin_unit2_28mm.{json,hdr}`

Reproduce:

```bash
bash tools/lldb_probes/capturedimage_f2770_origin/run_unit2_28mm.sh
python3 tools/lldb_probes/capturedimage_f2770_origin/verify_public_capture_fields.py
```

## Runtime result

The rerun launched normally, completed with 10 paired pre/post constructor
events, and wrote populated `10432x7824` Radiance HDR. The packet covers every
public camera key `0..9` exactly once.

For every same-key Unit-2 module:

| Constructor/object field | Exact public equality |
|---|---|
| input `+0x40`, `CapturedImage+0x38` | `CameraModule.sensor_exposure` |
| input `+0x3c`, `CapturedImage+0x40` | raw float32 `CameraModule.sensor_analog_gain` |
| present input `+0x50`, `CapturedImage+0x44` | raw float32 `CameraModule.sensor_digital_gain` |
| input `+0x48`, `CapturedImage+0x104` | decoded `CameraModule.sensor_temparature` |

The Unit-2 packet is discriminating:

- exposure has ten captured values;
- analog-gain words are `0x40780000` (`3.875`) and `0x40f80000`
  (`7.75`);
- digital-gain word is `0x3f800000` (`1.0`) with presence set; and
- decoded temperatures span `34..43`.

The verifier also rechecks the pinned constructor-copy instructions and all 42
canonical Unit-1 four-focal events.

## Admission boundary

This closes checklist D1: direct sensor-field public origins now have an exact
constructor-runtime join on Unit-2 as well as Unit-1. Runtime body scope is one
exact-focal Unit-2 `28mm` LRI with all ten cameras, which is sufficient to test
the second physical calibration body; it is not a claim that every focal must
repeat the body-independent direct-copy proof.
