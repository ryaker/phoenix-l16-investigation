# Static/Runtime Evidence: Index-5 Public Protobuf Schema Names

> Superseding follow-up (2026-06-30):
> `bundle_static_index5_depth_bounds_installed_origin.md` closes the bounds'
> origin as installed constants. No public protobuf field name exists for the
> selected mode-0 pair on the installed path.

**Date:** 2026-06-19  
**Status:** VERIFIED; admitted naming refinement, no claim-status upgrade  
**Bearing:** Lane B, `CLM-WARP-003`; public meaning of `state+0xe0`,
`state+0x448`, and `record+0x40`

**2026-06-26 follow-up:** the later
[distortion-polynomial public-origin proof](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_state_448_distortion_polynomial_public_origin_two_body.md)
supersedes this document's narrower non-claim about the computed envelope's
input ancestry. The envelope remains computed, but its same-camera public
inputs are now proven as
`FactoryModuleCalibration.geometry.distortion.polynomial.{distortion_center, normalization, coeffs, fit_cost}`.

## Question

Earlier Lane B proof connected live runtime fields to anonymous public paths
such as `LightHeader.field_12.field_5` and
`field_13.field_3.field_2[*].field_6`, but it could not assign those fields
semantic names. This proof asks whether the installed bundle itself carries a
machine-decodable public protobuf schema and whether the named wire fields are
present on both physical L16 bodies.

## Method

`libcp.dylib` embeds serialized `FileDescriptorProto` byte strings. The new
standalone verifier:

1. locates `camera_module.proto`, `geometric_calibration.proto`, and
   `lightheader.proto` by their protobuf field-1 filename signatures;
2. decodes the descriptor wire format without relying on generated protobuf
   bindings or guessed strings;
3. checks exact field numbers, names, labels, types, and referenced types;
4. walks representative wide and tele LRIs from both verified calibration
   bodies and validates the named wire fields, full sensor size, geometry
   records, focus bundles, and focus-Hall-code fields.

The installed binary is fixed by SHA-256:

```text
libcp.dylib = b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

Embedded descriptor custody:

| Descriptor | File offset | Serialized bytes | SHA-256 |
|---|---:|---:|---|
| `camera_module.proto` | `0x5c81b0` | 1,330 | `b6f688e5e96edb6721b0a80040e0fec1fc61a59f6893fdcaef7b54d408797b1f` |
| `geometric_calibration.proto` | `0x5c73b0` | 1,513 | `0ae64c39c443f72f9dd72706efa428571c183a32d76b7504ce86c8d4dd0bfe5e` |
| `lightheader.proto` | `0x5c8b10` | 2,484 | `8c3795d6c609bcfe01e7302ccf385278e63dd17e63d42ef5481a47b31c81ab75` |

## Public Names for the Runtime Module Bridge

The embedded descriptors prove these exact `LightHeader.modules` fields:

| Prior anonymous path | Public schema name | Type |
|---|---|---|
| `LightHeader.field_12` | `LightHeader.modules` | repeated `CameraModule` |
| `field_12[].field_2` | `CameraModule.id` | required `CameraID` enum |
| `field_12[].field_3` | `CameraModule.is_enabled` | optional `bool`, default `true` |
| `field_12[].field_4` | `CameraModule.mirror_position` | optional `int32` |
| `field_12[].field_5` | `CameraModule.lens_position` | required `int32` |
| `field_12[].field_8` | `CameraModule.sensor_exposure` | required `uint64` |
| `field_12[].field_9.field_2` | `CameraModule.sensor_data_surface.size` | required `Point2I` |
| `field_12[].field_10` | `CameraModule.sensor_temparature` | optional `sint32` |

`sensor_temparature` is the spelling stored in the installed public schema.
Because protobuf `sint32` uses zigzag encoding, the previously observed
`constructor input+0x48 * 2 == raw field_10` relation is the nonnegative wire
encoding of decoded `sensor_temparature == constructor input+0x48`.

Combining these names with the existing four-zoom `0xe59a4 -> 0xf2770`
runtime copy proof admits:

```text
constructor input+0x30 -> object+0x60 = CameraModule.id
constructor input+0x60 -> object+0x30 = CameraModule.is_enabled
constructor input+0x34 -> object+0x50 = CameraModule.mirror_position
constructor input+0x38 -> object+0x54 = CameraModule.lens_position
constructor input+0x40               = CameraModule.sensor_exposure
constructor input+0x48               = decoded CameraModule.sensor_temparature
object+0x114/+0x118                  = CameraModule.sensor_data_surface.size
```

The runtime copy portion remains scoped to the accepted canonical Unit-1
four-zoom constructor reports. The schema and LRI carrier names are checked on
both bodies below.

## Public Names for Focus-Dependent Intrinsics

The prior numeric calibration paths now decode exactly as:

```text
LightHeader.field_13
  = LightHeader.module_calibration

field_13[camera].field_3
  = FactoryModuleCalibration.geometry

field_13[camera].field_3.field_2[*]
  = GeometricCalibration.per_focus_calibration[*]

...field_2.field_1
  = GeometricCalibration.CalibrationFocusBundle.intrinsics.k_mat

...field_6
  = GeometricCalibration.CalibrationFocusBundle.focus_hall_code

...field_3.field_1.field_1
  = GeometricCalibration.CalibrationFocusBundle.extrinsics.canonical.rotation

...field_3.field_1.field_2
  = GeometricCalibration.CalibrationFocusBundle.extrinsics.canonical.translation
```

This resolves the two semantic names left open by the accepted
`0x1f0ce0 -> 0x1f96e0` K-source trace:

- runtime `object+0x54` is the capture's `CameraModule.lens_position`;
- the paired public calibration scalars are
  `CalibrationFocusBundle.focus_hall_code`.

Therefore the already-proven float32 helper formula has concrete public
meaning: for the captured two-record branch, it interpolates or extrapolates
selected `intrinsics.k_mat` fields over calibrated `focus_hall_code` at the
capture's live `lens_position`. This names a focus-dependent intrinsics
calibration path; it does not name selector bank `0` / `1` as factory/current.

## Two-Body Wire Verification

The verifier checks one wide and one tele LRI per physical body:

| Body | Tier | Geometry payload | Fired modules | Geometry records | Focus bundles | Named `focus_hall_code` values |
|---|---|---|---:|---:|---:|---:|
| Unit-1 | 28mm | `722a6e721636c9c4...`, 32,832 B | 10 | 16 | 48 | 32 |
| Unit-1 | 70mm | `722a6e721636c9c4...`, 32,832 B | 11 | 16 | 48 | 32 |
| Unit-2 | 28mm | `223961c6bce6153e...`, 32,833 B | 10 | 16 | 48 | 32 |
| Unit-2 | 70mm | `223961c6bce6153e...`, 32,833 B | 11 | 16 | 48 | 32 |

All module records decode through the same embedded schema, explicitly carry
`is_enabled = true`, and carry `sensor_data_surface.size = 4160 x 3120`. The
different calibration hashes and different observed module values demonstrate
that this is a real cross-body check, not four aliases of one calibration
payload.

This is the risk-relevant Body A/Body B discriminator. A second complete LLDB
four-zoom campaign is not needed to prove installed descriptor names or wire
types. No universal runtime-value distribution is claimed for either body.

## Installed Public Depth Boundary

The verifier also decodes all 34 embedded `.proto` descriptors and checks the
installed public depth/export surface:

```text
Stereo.depth_format = DepthFormat enum
Stereo.depth_offset = uint64
Stereo.depth_level = uint32
DepthFormat = Float32
```

No decoded embedded protobuf field name contains a standalone `near` or `far`
token. Separately, the installed DNG/XMP writer strings explicitly advertise:

```text
GDepth:Format="RangeInverse"
GDepth:Units="mm"
```

This proves that one public exported Google-depth surface is float32-backed,
range-inverse, and labeled in millimeters. It does **not** prove custody from
the live index-5/Triangulator scalar or `record+0x40` into that exporter. The
internal ray-depth unit therefore remains open under the existing proof
standard; `mm` is a concrete next trace target, not an admitted unit for the
`[200,640000]` bounds.

## Consequence for the Three Lane B Operands

### `state+0xe0`

The whole container still has no one-to-one public protobuf-record identity.
Its admitted object family is derived/composed. The public ancestry is now
more concrete, however: live camera key, mirror position, lens position,
sensor exposure, sensor temperature, per-focus K matrices, focus Hall codes,
and canonical rotation/translation all have exact public names and paths. The
captured K producer is specifically focus-dependent intrinsics evaluation.

### `state+0x448`

The first payload `+0x00..+0x2c` names become exact public canonical
extrinsics paths: anchor `per_focus_calibration[2].extrinsics.canonical.rotation`
and `.translation`. The later `+0x30..+0x3c` formula's `4160 x 3120` input is
public `CameraModule.sensor_data_surface.size`. Follow-up static custody and
two-body runtime matching prove that the same-camera converted record feeding
the computed distortion/undistortion envelope comes from public
`geometry.distortion.polynomial.{distortion_center, normalization, coeffs, fit_cost}`.
The envelope and whole payload remain derived rather than one-to-one public
fields.

### `record+0x40`

`record+0x40` remains the internally depth-labeled `UpsampleLayer+0x90`
descriptor built from the index-5 runtime chain. Its `4160 x 3120` dimensions
have the concrete public origin `CameraModule.sensor_data_surface.size`.
Its pixels are runtime-generated depth values, not an LRI-stored depth map;
the ray-depth bounds remain installed binary constants with no proved public
LRI field or public unit.

## Non-Claims

- This does not identify the full `state+0xe0` or `state+0x448` object as a
  direct public protobuf record.
- This does not map CalibStage numeric selectors to public `factory` or
  `current` names.
- This does not make the computed distortion/undistortion envelope itself a
  direct protobuf field; only its public polynomial input ancestry is proven.
- This does not assign public units or an LRI field to the `[200,640000]`
  ray-depth bounds. The installed GDepth exporter says `mm`, but custody from
  this internal path to that export surface is not proven.
- This does not close source-index descriptor semantics, source-record public
  names, final contribution, or acceptance/rejection.
- This does not change the status of `CLM-WARP-003` or unblock the spike.

## Artifacts

- Verifier:
  [verify_embedded_calibration_proto_schema.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_embedded_calibration_proto_schema.py)
- Rerunnable raw JSON:
  `runs/index5_public_schema/embedded_calibration_proto_schema.json`
- Runtime public-origin audit:
  [lldb_index5_depth_public_meaning_gap_audit_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_index5_depth_public_meaning_gap_audit_four_zoom.md)
- K producer trace:
  [lldb_1f0ce0_k_source_trace_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_1f0ce0_k_source_trace_four_zoom.md)
- `state+0x448` payload origin:
  [lldb_state_448_payload_public_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_state_448_payload_public_origin_four_zoom.md)

Verifier command:

```bash
python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_embedded_calibration_proto_schema.py \
  --lri "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri" \
  --lri "/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri" \
  --lri "/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri" \
  --lri "/Volumes/Base Photos/Light/2018-10-25/L16_02894.lri"
```

Terminal result:

```text
embedded_calibration_proto_schema=OK
```
