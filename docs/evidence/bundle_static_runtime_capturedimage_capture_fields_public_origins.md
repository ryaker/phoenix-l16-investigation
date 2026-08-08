# Static/Runtime Evidence: CapturedImage Public Capture Fields

**Date:** 2026-06-30  
**Status:** VERIFIED; admitted Lane B field-level refinement  
**Bearing:** `CLM-WARP-003`, index-5 `state+0xe0` selected objects

**Superseding follow-up:** `bundle_static_runtime_capturedimage_frame_index_public_origin.md`
subsequently names the secondary factory/object key as public
`CameraModule.frame_index`. The non-conclusion below records this document's
proof boundary at the time it was written.

## Question

Once the selected `state+0xe0` objects were identified exactly as
`lt::CapturedImage`, which additional object fields can be traced to concrete
public `LightHeader.modules[camera]` names without inferring from anonymous
values?

## Artifacts

- Existing completed Unit-1 four-focal constructor reports:
  `runs/capturedimage_f2770_origin/f2770_origin_{28mm,35mm,70mm,150mm}.json`
- Extended reusable probe:
  `tools/lldb_probes/capturedimage_f2770_origin/f2770_origin_probe.py`
- Static/runtime verifier:
  `tools/lldb_probes/capturedimage_f2770_origin/verify_public_capture_fields.py`
- Added exact-28mm Unit-2 rerun harness:
  `tools/lldb_probes/capturedimage_f2770_origin/f2770_origin_unit2_28mm.lldb`
  and `run_unit2_28mm.sh`

The Unit-2 runtime harness was attempted on 2026-06-30, but LLDB lost its
debugserver connection before the process launched and wrote no report.
Therefore this document makes no Unit-2 constructor-runtime claim.

## Public Schema

The SHA-pinned embedded `CameraModule` descriptor names:

| Field | Public name | Type |
|---:|---|---|
| `7` | `sensor_analog_gain` | required `float` |
| `8` | `sensor_exposure` | required `uint64` |
| `10` | `sensor_temparature` | optional `sint32` |
| `14` | `sensor_digital_gain` | optional `float` |

`sensor_temparature` is the exact spelling in the installed public descriptor.

## Pinned Constructor Copies

For installed `libcp.dylib` SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`,
`0xf2770` contains these direct copies:

```asm
0xf27b7  movq  0x40(%r14), %rax
0xf27bb  movq  %rax, 0x38(%rdx)
0xf27bf  movl  0x3c(%r14), %eax
0xf27c3  movl  %eax, 0x40(%rdx)

0xf27f3  testb $0x8, %ch
0xf27f8  movl  0x50(%r14), %eax
0xf2806  movl  %eax, 0x44(%rdx)
0xf2809  movb  $0x1, 0x48(%rdx)

0xf280d  testb $0x1, %ch
0xf2812  movl  0x48(%r14), %eax
0xf2826  movl  %eax, 0x104(%rdx)
0xf282c  movb  $0x1, 0x108(%rdx)
```

Here `r14` is the captured constructor input and `rdx` is the new
`lt::CapturedImage`.

## Runtime/Public Join

The verifier checks all `42` completed constructor events from the canonical
Unit-1 focal quartet by same public camera ID:

| Constructor/object field | Public origin |
|---|---|
| input `+0x3c` and `CapturedImage+0x40` | raw float32 `CameraModule.sensor_analog_gain` |
| input `+0x40` and direct-copy `CapturedImage+0x38` | `CameraModule.sensor_exposure` |
| input `+0x50` and present optional `CapturedImage+0x44` | raw float32 `CameraModule.sensor_digital_gain` |
| input `+0x48` and `CapturedImage+0x104` | decoded `CameraModule.sensor_temparature` |

The evidence is discriminating rather than zero-only: the events contain two
distinct analog-gain bit patterns, `40` distinct exposure values, and two
distinct digital-gain bit patterns. Every constructor packet has the optional
digital-gain presence bit set. For the positive sampled temperatures, public
`sint32` ZigZag wire value equals twice the decoded constructor/object value.

The same verifier checks exact-wide and exact-tele Unit-2 LRIs. Their
calibration payloads have Unit-2 hash prefix `223961c6bce6153e`, and all `10`
wide / `11` tele public module records contain fields `7`, `8`, `10`, and
`14`. This is two-body public-source/schema coverage; it is not a second-body
constructor-runtime join.

## Reproduction

```bash
python3 tools/lldb_probes/capturedimage_f2770_origin/verify_public_capture_fields.py
python3 tools/lane_b_index5_public_meaning_audit.py
```

Accepted verifier summary:

```text
capturedimage_public_capture_fields=OK ... events=42 field7_values=2 field8_values=40 field14_values=2 unit2_modules=10,11
```

## Conclusions

- `CapturedImage+0x38` is the public camera's `sensor_exposure`.
- `CapturedImage+0x40` is the public camera's `sensor_analog_gain`.
- Present optional `CapturedImage+0x44` is the public camera's
  `sensor_digital_gain`; `+0x48` is its internal presence state.
- Present optional `CapturedImage+0x104` is decoded public
  `sensor_temparature`; `+0x108` is its internal presence state.
- These are direct per-capture module values, not derived calibration records.

## Non-Conclusions

- This does not name the RawImageFactory/CapturedImage secondary numeric key.
- This does not map numeric `CalibStage` selectors.
- This does not name all `CapturedImage` fields, the pair at `+0x58/+0x5c`,
  or transformed calibration banks.
- It does not prove a Unit-2 constructor-runtime equality packet.
- It does not close final source contribution, anti-ghosting, or merge
  acceptance/rejection.
