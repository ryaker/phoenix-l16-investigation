# Static/Runtime Evidence: `state+0xe0` CapturedImage Identity

**Date:** 2026-06-30  
**Status:** VERIFIED; admitted Lane B object-identity refinement  
**Bearing:** `CLM-WARP-003`, index-5 composed-camera producer path

## Question

Prior evidence bounded `state+0xe0` as a two-key shared-object lookup and
showed that its selected objects carry public camera/module fields plus two
internal `CalibStage` banks. The whole object was still described only as
"CapturedImage-like."

This proof asks whether the exact installed type and the objects selected by
the index-5 path can be joined without relying on suggestive error strings.

## Artifacts

- Reused and extended runtime harness:
  `tools/lldb_probes/index5_composed_geometry_origin/`
- Static/runtime verifier:
  `tools/lldb_probes/index5_composed_geometry_origin/verify_composed_geometry_origin.py`
- Rerunnable reports:
  `runs/index5_composed_geometry_origin/composed_geometry_*.json`
- Public-field companion:
  `docs/evidence/bundle_static_runtime_index5_composed_geometry_public_origins_two_body.md`

## Exact Installed Type

The pinned constructor path at `0xe5948..0xe59d2` proves:

```text
0xe5970  operator new(0x230)
0xe5985  install control-block vtable address point 0x665eb8
0xe5993  object = control block + 0x20
0xe59a4  call 0xf2770(object, input, owner)
0xe59c5  insert the resulting shared object through 0xe3240
```

The vtable's ABI typeinfo pointer is `0x665ee0`; its name pointer is
`0x5ae680`, whose exact installed RTTI string is:

```text
std::__1::__shared_ptr_emplace<
  lt::CapturedImage,
  std::__1::allocator<lt::CapturedImage>
>
```

The verifier pins the libcp SHA-256, all addresses above, the allocation
size, object offset, direct calls, typeinfo pointers, and complete RTTI name.

## Same-Process Pointer Join

The extended composed-geometry harness records each object immediately after
`0xf2770`, including the slid control-block address point and public camera
key. Later, at each `0x3ff1bc` index-5 iteration, it records the raw object
resolved through `state+0xe0`.

For every accepted case:

- every constructor event has control-block address point `libcp+0x665eb8`;
- every one of the five selected `state+0xe0` pointers is exactly one of
  those same-process constructed `lt::CapturedImage` pointers; and
- selected object `+0x60` equals the expected public `CameraModule.id`.

Coverage is:

| Case | Constructed CapturedImages | Selected by index-5 |
|---|---:|---|
| Unit-1 `28mm` | 10 | `A1,A5,A2,A3,A4` |
| Unit-1 `35mm` | 10 | `A1,A5,A2,A3,A4` |
| Unit-1 `70mm` | 11 | `B4,B2,B5,B1,B3` |
| Unit-1 `150mm` | 11 | `B4,B2,B5,B1,B3` |
| Unit-2 exact `28mm` | 10 | `A1,A5,A2,A3,A4` |

The Unit-2 run has the independently established distinct calibration
signature `223961c6bce6153e`, versus Unit-1 `722a6e721636c9c4`.

## Public Meaning

The exact safe name for the `state+0xe0` lookup result is now
`lt::CapturedImage`.

Joined with prior admitted evidence, the selected object has:

- `CapturedImage+0x60 = CameraModule.id`;
- `CapturedImage+0x30 = CameraModule.is_enabled`;
- `CapturedImage+0x54 = CameraModule.lens_position`;
- `CapturedImage+0x114/+0x118 =
  CameraModule.sensor_data_surface.size`;
- internal `CalibStage` record banks at `+0x12c` and `+0x180`; and
- owner-backed same-camera calibration lookup through `+0xa0`.

The object is a runtime aggregate constructed from public LRI camera and
calibration carriers. It is not a direct protobuf-message byte copy.

## Verifier Output

```text
static_composed_geometry_origin=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
28mm: OK keys=A1,A5,A2,A3,A4 anchor=A1 state_e0_objects=lt::CapturedImage(10)
35mm: OK keys=A1,A5,A2,A3,A4 anchor=A1 state_e0_objects=lt::CapturedImage(10)
70mm: OK keys=B4,B2,B5,B1,B3 anchor=B4 state_e0_objects=lt::CapturedImage(11)
150mm: OK keys=B4,B2,B5,B1,B3 anchor=B4 state_e0_objects=lt::CapturedImage(11)
unit2_28mm: OK keys=A1,A5,A2,A3,A4 anchor=A1 state_e0_objects=lt::CapturedImage(10)
cross_body_28mm=OK distinct_calibration_and_composed_record_bytes
```

The actual verifier also prints the already admitted maximum camera-center
separation and calibration signatures.

## Admission and Boundary

Admitted:

- exact `lt::CapturedImage` identity for objects selected through
  `state+0xe0`;
- exact same-process constructor-to-index-5 pointer custody;
- wide/tele route coverage plus one distinct-body discriminator; and
- continued public `CameraModule.id` alignment.

Still open:

- the secondary numeric factory/object lookup key;
- numeric `CalibStage` selector `0/1` mapping to `factory/current`;
- public names for fields outside the already admitted module/calibration
  paths;
- whole `state+0x448` payload semantics beyond its admitted components; and
- final source contribution and acceptance/rejection.
