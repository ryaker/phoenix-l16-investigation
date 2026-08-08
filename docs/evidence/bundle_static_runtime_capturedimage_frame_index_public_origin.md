# Static/Runtime Evidence: CapturedImage Frame-Index Public Origin

**Date:** 2026-06-30  
**Status:** VERIFIED; admitted Lane B lookup-key refinement  
**Bearing:** `CLM-WARP-003`, index-5 `state+0xe0` lookup path

## Question

What is the secondary integer matched between `RawImageFactory+0x10` and
`CapturedImage+0x64` by `0x1be970 -> 0xe6ba0`, and does it have a concrete
public LRI name?

## Artifact

Reusable verifier:

```text
tools/lldb_probes/capturedimage_frame_index_origin/
  verify_frame_index_public_origin.py
```

Optional multiframe constructor harness:

```text
tools/lldb_probes/capturedimage_f2770_origin/
  f2770_origin_multiframe_28mm.lldb
  run_multiframe_28mm.sh
```

It checks the installed binary hash, embedded protobuf descriptor, generated
parser instructions, CapturedImage constructor copy, RawImageFactory
construction and lookup instructions, two physical-body multiframe LRIs, the
existing completed four-focal constructor reports, and an optional corpus
census.

## Embedded Public Name

The SHA-pinned embedded `camera_module.proto` descriptor identifies field 15
of `.ltpb.CameraModule` as:

```text
optional uint32 frame_index = 15
```

The generated `CameraModule` parser at `0x163510` has the matching field
sequence and object layout. In particular:

```asm
0x1638e9  cmp   eax, 0x78
0x1638f2  or    byte ptr [r12 + 0x11], 0x10
0x163913  mov   dword ptr [r12 + 0x54], esi
```

Wire tag `0x78` is `(15 << 3) | 0`, the varint tag for public field 15. The
branch sets has-bit `0x1000` and stores the decoded value at generated
`CameraModule+0x54`. The parser's adjacent tags and destinations agree with
the same embedded descriptor, including field 2 `id`, field 3 `is_enabled`,
field 4 `mirror_position`, field 5 `lens_position`, field 7
`sensor_analog_gain`, field 8 `sensor_exposure`, field 10
`sensor_temparature`, and field 14 `sensor_digital_gain`.

## CapturedImage Copy

Pinned constructor `0xf2770` consumes that same has-bit and value:

```asm
0xf27e3  test  ch, 0x10
0xf27e8  mov   eax, dword ptr [r14 + 0x54]
0xf27ec  mov   dword ptr [rdx + 0x64], eax
```

Therefore:

```text
CapturedImage+0x64 = CameraModule.frame_index
```

All `42` completed Unit-1 constructor events from the canonical four focal
tiers have the field present, with generated input `+0x54 = 0` and constructed
`CapturedImage+0x64 = 0`.

## RawImageFactory Lookup

The renderer-owner construction path passes integer zero to the
`RawImageFactory` constructor at `0x3c93d1 -> 0x1bdc70`. Constructor body
`0x1bd270` stores the argument at factory `+0x10`.

`0x1be970` loads that field and calls `0xe6ba0`. The latter scans the retained
`CaptureStack` and compares:

```text
0xf3320(CapturedImage) = CapturedImage+0x64
    against RawImageFactory+0x10

0xf2720(CapturedImage) = CapturedImage+0x60
    against the requested public CameraModule.id
```

The exact safe name for `RawImageFactory+0x10` is therefore its selected
`CameraModule.frame_index` lookup key. In the admitted renderer-owner
construction path, that selected frame index is constant `0`.

## Two-Body Discriminator

Two multiframe LRIs provide nonzero public values and physical-body coverage:

| Body | LRI | Focal | Calibration hash prefix | Public camera/frame grid |
|---|---|---:|---|---|
| Unit-1 | `2018-07-23/L16_02153.lri` | `28` | `722a6e721636c9c4` | camera IDs `0..9` x frame indices `0..3` |
| Unit-2 | `2020-07-14/L16_03275.lri` | `35` | `223961c6bce6153e` | camera IDs `0..9` x frame indices `0..3` |

Each sample contains exactly 40 decoded `(CameraModule.id, frame_index)`
pairs. Full-file SHA-256 values are pinned by the verifier.

The optional corpus census found `9,376` LRIs with decodable frame-index
values:

```text
(0,)          9,128 files
(0,1,2,3)       248 files
```

This excludes a zero-only value coincidence and shows that the public field is
actively used for multiframe capture indexing on both physical bodies.

## Reproduction

```bash
python3 tools/lldb_probes/capturedimage_frame_index_origin/verify_frame_index_public_origin.py
python3 tools/lldb_probes/capturedimage_frame_index_origin/verify_frame_index_public_origin.py \
  --scan-corpus "/Volumes/Base Photos/Light"
```

Accepted summary:

```text
capturedimage_frame_index_public_origin=OK ... samples=Unit-1:28mm:722a6e721636c9c4,Unit-2:35mm:223961c6bce6153e runtime_zero_events=42 chain=CameraModule.frame_index->protobuf+0x54->CapturedImage+0x64->RawImageFactory+0x10_lookup corpus_scanned=9376 value_sets={(0,): 9128, (0, 1, 2, 3): 248}
```

## Conclusions

- `CapturedImage+0x64` is exact public `CameraModule.frame_index`.
- `RawImageFactory+0x10` is the selected frame-index key used to choose a
  `CapturedImage` before matching public `CameraModule.id`.
- The admitted renderer-owner construction selects frame index `0`.
- This closes the former secondary numeric-key name on the index-5
  `state+0xe0` path.

## Non-Conclusions

- This does not claim that every RawImageFactory construction globally selects
  frame `0`; the constant is proven for the admitted renderer-owner path.
- A new multiframe LLDB constructor packet was not obtained. The attempted
  debugger launch could not open its input and produced zero events; it is not
  used as evidence.
- This does not map numeric `CalibStage` selectors, name remaining
  `CapturedImage` fields/banks, or prove final source contribution and
  acceptance/rejection.
