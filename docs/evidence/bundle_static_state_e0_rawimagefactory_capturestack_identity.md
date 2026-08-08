# Static Evidence: `state+0xe0` RawImageFactory Identity

**Date:** 2026-06-30  
**Status:** VERIFIED; admitted Lane B lookup-context refinement  
**Bearing:** `CLM-WARP-003`, index-5 composed-camera producer path

**Superseding follow-up:** `bundle_static_runtime_capturedimage_frame_index_public_origin.md`
subsequently names factory `+0x10` / CapturedImage `+0x64` as the selected
public `CameraModule.frame_index` key. The non-conclusion below records this
document's proof boundary at the time it was written.

## Question

Prior evidence proved that `state+0xe0 -> 0x1be970 -> 0xe6ba0` selects exact
`lt::CapturedImage` objects by two integer fields. The object type was known,
but the lookup context stored at `state+0xe0` remained anonymous.

## Artifact

Reusable deterministic verifier:

```text
tools/lldb_probes/state_e0_rawimagefactory_identity/
  verify_state_e0_rawimagefactory_identity.py
```

It checks the installed `libcp.dylib` SHA-256, RTTI chains, constructor
allocations, exact call targets, and pointer-copy instructions.

## Type Anchors

The installed RTTI names are exact:

```text
std::__1::__shared_ptr_emplace<lt::CaptureStack,...>
std::__1::__shared_ptr_pointer<
    lt::RawImageFactory*,
    std::__1::default_delete<lt::RawImageFactory>,
    ...
>
```

The first control-block address point is `0x665dc0`, with typeinfo name at
`0x5adc00`. The second is `0x66a498`, with typeinfo name at `0x604350`.

## Construction Chain

The installed body at `0x3c9370` performs:

```text
allocate 0x2d0 bytes
install CaptureStack shared-control-block address point
object = allocation + 0x18
call 0xe52c0(object, input_stream)

allocate 0x90 bytes
call 0x1bdc70 -> 0x1bd270(factory, shared CaptureStack, 0)
wrap factory pointer with shared_ptr_pointer<lt::RawImageFactory*>
store factory shared pointer at renderer-owner +0xa0/+0xa8
```

`0x1bd270` copies the incoming `CaptureStack` shared pointer into factory
`+0x00/+0x08`, stores the numeric constructor argument at factory `+0x10`,
and then enumerates camera keys through `0x1bdb60`.

## Exact State Join

The owner accessor and constructor chain is:

```text
0x3c6ac0(owner) -> owner+0xa0
0x3b2feb -> 0x3c6ac0
0x3b3008 passes that returned shared_ptr address as rsi
0x3b3011 -> 0x3f46d0 -> 0x3f2c40
```

`0x3f2c40` then performs the exact retained shared-pointer copy:

```asm
0x3f2c63  mov r14, rsi
0x3f2ce0  mov rax, qword ptr [r14]
0x3f2ce3  mov qword ptr [r13 + 0xe0], rax
0x3f2cea  mov rdi, qword ptr [r14 + 8]
0x3f2cee  mov qword ptr [r13 + 0xe8], rdi
```

Therefore:

```text
state+0xe0 = lt::RawImageFactory*
state+0xe8 = its shared control block
```

This is a retained `shared_ptr<lt::RawImageFactory>` field, not a generic
lookup-context pointer.

## Lookup Role

The admitted index-5 path loads `state+0xe0` into `0x1be970`. That helper:

1. reads `RawImageFactory+0x00`, the retained `lt::CaptureStack*`;
2. reads numeric factory field `+0x10`;
3. passes both that value and the requested camera key to `0xe6ba0`;
4. receives a shared `lt::CapturedImage` or throws
   `invalid image pointer!`.

`0xe6ba0` scans the CaptureStack's shared CapturedImage vector and compares
candidate `+0x64` and public `CameraModule.id` carrier `+0x60`.

The prior accepted runtime pointer join covers selected objects across all
four Unit-1 focal tiers and exact-28mm Unit-2. This static proof names the
common factory/context used by that path; it does not require a new runtime
packet.

## Reproduction

```bash
python3 tools/lldb_probes/state_e0_rawimagefactory_identity/verify_state_e0_rawimagefactory_identity.py
```

Accepted output:

```text
state_e0_rawimagefactory_identity=OK ... owner+0xa0=shared_ptr<lt::RawImageFactory> state+0xe0/+0xe8=retained_raw/control backing=shared_ptr<lt::CaptureStack>
```

## Conclusions

- The exact safe name for the `state+0xe0` lookup context is
  `lt::RawImageFactory`.
- Its backing camera collection is `lt::CaptureStack`, constructed from the
  capture input stream.
- The selected values are exact `lt::CapturedImage` objects already joined to
  public per-camera capture and calibration fields.

## Non-Conclusions

- Factory `+0x10` and `CapturedImage+0x64` remain a numeric matched key; this
  proof does not name them `frame_index`.
- Numeric `CalibStage` values `0/1` are not mapped to `factory/current`.
- This does not name the whole owner-held `+0x678` object or every
  `CapturedImage`/State field.
- This does not close final source contribution or merge acceptance.
