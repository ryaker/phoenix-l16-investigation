# Static/Runtime Evidence: `CapturedImage+0x30` Public `is_enabled` Origin

**Date:** 2026-06-30  
**Status:** VERIFIED; admitted Lane B public-field refinement  
**Bearing:** `state+0xe0` selected `lt::CapturedImage` objects

## Question

The first `state+0x448` population loop and several later consumers gate on
selected object byte `+0x30`. Prior evidence established only that the byte
was `1` in accepted runs.

This proof asks whether that byte has an exact public LRI/protobuf origin and
name.

## Artifacts

- Embedded-schema and two-body raw-wire verifier:
  `tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_embedded_calibration_proto_schema.py`
- Four-focal runtime/public join:
  `tools/lane_b_index5_public_meaning_audit.py`
- Static constructor-copy verifier:
  `tools/lldb_probes/index5_composed_geometry_origin/verify_composed_geometry_origin.py`
- Reused runtime packets:
  `runs/capturedimage_f2770_origin/f2770_origin_*.json`
- Exact object-identity companion:
  `docs/evidence/bundle_static_runtime_state_e0_capturedimage_identity_two_body.md`

## Public Schema Name

The SHA-pinned installed `camera_module.proto` descriptor names:

```text
CameraModule.field_3
  = optional bool is_enabled
  = default true
```

The verifier checks the exact field number, name, type, and default. It also
walks one wide and one tele LRI from each physical calibration body. Every
listed module in all four representatives carries field 3 explicitly as
wire value `1`:

| Body | Focal discriminator | Module count | Explicit `is_enabled = true` |
|---|---:|---:|---:|
| Unit-1 | `28mm` | 10 | 10 |
| Unit-1 | `70mm` | 11 | 11 |
| Unit-2 | `28mm` | 10 | 10 |
| Unit-2 | `70mm` | 11 | 11 |

This is a body and wide/tele wire-format discriminator, not a claim that
disabled modules can never occur in another LRI.

## Static Copy

The pinned `lt::CapturedImage` constructor body copies exactly:

```text
0xf27b0  mov al, byte ptr [r14 + 0x60]
0xf27b4  mov byte ptr [rdx + 0x30], al
```

The constructor reports identify `r14` as the same module input whose
camera ID, mirror position, lens position, exposure, and temperature already
match the same public `LightHeader.modules[camera]` record. The destination
`rdx` is the exact `lt::CapturedImage` object established by control-block
RTTI and same-process pointer custody.

## Four-Focal Runtime Join

For every constructed camera in the accepted Unit-1 focal quartet, the Lane B
audit now requires:

```text
constructor input+0x60
  == public LightHeader.modules[camera].is_enabled
  == CapturedImage+0x30
```

All values are `1` in these runs:

| Focal | Matched cameras |
|---|---|
| `28mm`, `35mm` | `A1..A5`, `B1..B5` |
| `70mm`, `150mm` | `B1..B5`, `C1..C6` |

The same packets retain exact public `CameraModule.id` key alignment, so this
is a per-camera join rather than a global-value coincidence.

## Admission and Boundary

Admitted:

- `CapturedImage+0x30` is exact public
  `LightHeader.modules[camera].is_enabled`;
- the constructor copies the decoded module value byte-for-byte;
- Unit-1 four-focal runtime coverage; and
- explicit same-field raw-wire confirmation on wide/tele LRIs from both
  physical bodies.

Still open:

- behavior for a public module whose `is_enabled` value is false;
- the `state+0xe0` lookup-context container name;
- numeric `CalibStage` selector mapping;
- whole `state+0x448` semantics outside admitted fields; and
- final source contribution and acceptance/rejection.

