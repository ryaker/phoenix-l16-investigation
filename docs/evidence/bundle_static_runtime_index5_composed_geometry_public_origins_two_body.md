# Static/Runtime Evidence: Index-5 Composed Geometry Public Origins

**Date:** 2026-06-30  
**Status:** VERIFIED; admitted Lane B field-classification refinement  
**Bearing:** `CLM-WARP-003`, index-5 lookup-count geometry

## Question

The five `StereoLayer<false>+0x258` items were already bounded as per-image
composed geometry records produced from same-key `state+0xe0` and
`state+0x448` inputs. Their whole-field public meaning was still open.

This proof asks:

1. which public cameras the five records represent;
2. which public calibration paths feed each record field;
3. what geometric quantity `0x28f5a0` derives from them; and
4. whether the result survives a different physical calibration body.

## Artifacts

- Runtime probe:
  `tools/lldb_probes/index5_composed_geometry_origin/composed_geometry_origin_probe.py`
- Runtime scripts and runners:
  `tools/lldb_probes/index5_composed_geometry_origin/composed_geometry_*.lldb`,
  `run_four_zoom.sh`, and `run_unit2_28mm.sh`
- Static/runtime verifier:
  `tools/lldb_probes/index5_composed_geometry_origin/verify_composed_geometry_origin.py`
- Rerunnable raw outputs:
  `runs/index5_composed_geometry_origin/`

The verifier pins installed `libcp.dylib` SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

It also pins complete static windows for `0x264270`, `0x23faf0`,
`0x3ff050`, and `0x28f5a0`.

A same-process type-identity follow-up now proves that every selected
`state+0xe0` object is exactly an `lt::CapturedImage`, not merely an
image-like object. See
`bundle_static_runtime_state_e0_capturedimage_identity_two_body.md`.

## Direct Producer Custody

The probe captures each camera iteration at:

```text
0x3ff1bc  after 0x264440 builds the state+0xe0 CalibStage record
0x3ff1d6  after 0x23faf0 composes state+0x448 with that record
0x3ff43c  before the Images/record/flag vectors are installed
```

All five accepted renders record exactly `5`, `5`, and `1` hits at those
sites. Every render completes with exit status `0` and a Radiance HDR output.

The numeric slices copied from each `0x23faf0` output match the corresponding
final `+0x258` item byte-for-byte. The vector-owned coefficient storage is
copied by value and may have different allocation pointers; record padding is
not assigned semantics.

## Public Input Names

For every captured item:

- the `state+0xe0` object key equals public `CameraModule.id`;
- runtime `object+0x54` exactly equals public `CameraModule.lens_position`;
- runtime `object+0x114/+0x118` is public
  `CameraModule.sensor_data_surface.size = 4160 x 3120`;
- the `state+0x448` input `+0x00..+0x20` exactly equals the tier anchor's
  public `extrinsics.canonical.rotation`;
- the `state+0x448` input `+0x24..+0x2c` exactly equals the tier anchor's
  public `extrinsics.canonical.translation`; and
- the `state+0xe0` record's complete coefficient vector exactly equals the
  same camera's public `geometry.distortion.polynomial.coeffs`.

The source record's secondary 3x3 matrix is also byte-exactly reconstructed
from the same camera's public
`geometry.distortion.polynomial.{distortion_center,normalization}`:

```text
[ normalization.x, 0, distortion_center.x ]
[ 0, normalization.y, distortion_center.y ]
[ 0, 0, 1 ]
```

The installed builder scales these terms by the live image-surface scale when
that scale is non-identity. The admitted captures have the identity source
scale before composition.

## Whole Record Classification

Combining the pinned `0x264270` builder, `0x23faf0` composition helpers, and
the direct runtime payload checks classifies the meaningful `0xa8` item
fields as:

| Item range | Meaning and origin |
|---|---|
| `+0x00..+0x20` | composed 3x3 intrinsics matrix; public ancestry is per-focus `intrinsics.k_mat`, evaluated at `CameraModule.lens_position` using public `focus_hall_code` |
| `+0x24..+0x2c` | anchor-relative extrinsic translation |
| `+0x30..+0x50` | anchor-relative extrinsic rotation |
| `+0x54..+0x60` | derived two-axis offset/scale adjustment tuple |
| `+0x68..+0x78` | owned float vector copied from public `Distortion.Polynomial.coeffs` |
| `+0x80..+0xa0` | composed 3x3 distortion normalization/center matrix derived from public `distortion_center` and `normalization` |

`+0x64..+0x67` and stride tail `+0xa4..+0xa7` are not assigned public
meaning by this proof.

The correct whole-record identity is therefore a **derived per-image,
anchor-relative calibrated camera-model record**. It is not a direct
protobuf-message byte copy.

## Camera Order and Anchor

The complete runtime order is stable by focal family:

| Scope | Record keys | First/tier anchor |
|---|---|---|
| Unit-1 `28mm`, `35mm` | `A1,A5,A2,A3,A4` | `A1` |
| Unit-1 `70mm`, `150mm` | `B4,B2,B5,B1,B3` | `B4` |
| Unit-2 exact `28mm` | `A1,A5,A2,A3,A4` | `A1` |

The first composed translation is zero within float32 error in every case.
The wide/tele distinction is therefore the expected tier switch from the A
camera family around `A1` to the B camera family around `B4`.

## `0x28f5a0` Geometry

For each composed output, `0x28f5a0` uses rotation `R` and translation `t`
from `+0x24..+0x50` to form an axis-reordered `R^T t`. Axis reordering and
the sign used for the inverse-extrinsic center preserve Euclidean distance.
The retained maximum is therefore the maximum separation of the five
anchor-relative extrinsic centers:

| Case | Maximum separation |
|---|---:|
| Unit-1 `28mm` | `43.855163` |
| Unit-1 `35mm` | `43.855163` |
| Unit-1 `70mm` | `35.540384` |
| Unit-1 `150mm` | `35.406025` |
| Unit-2 `28mm` | `43.290031` |

This replaces the former generic “transformed-3-vector spread” description.
The proof does not separately assign a public unit to canonical-extrinsics
translation.

## Two-Body Discriminator

The Unit-2 exact-28mm run has intrinsics calibration signature
`223961c6bce6153e`, distinct from Unit-1 `722a6e721636c9c4`.

It preserves the same key order, `A1` anchor, public field joins, and producer
mechanism while producing different composed-record bytes and a different
maximum separation. This is the body-relevant discriminator; repeating all
four focal tiers on Unit-2 is not needed for the claimed mechanism.

## Verifier Output

```text
static_composed_geometry_origin=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
28mm: OK keys=A1,A5,A2,A3,A4 anchor=A1 max_camera_center_separation=43.855163 unit=722a6e721636c9c4 polynomial=722a6e721636c9c4
35mm: OK keys=A1,A5,A2,A3,A4 anchor=A1 max_camera_center_separation=43.855163 unit=722a6e721636c9c4 polynomial=722a6e721636c9c4
70mm: OK keys=B4,B2,B5,B1,B3 anchor=B4 max_camera_center_separation=35.540384 unit=722a6e721636c9c4 polynomial=722a6e721636c9c4
150mm: OK keys=B4,B2,B5,B1,B3 anchor=B4 max_camera_center_separation=35.406025 unit=722a6e721636c9c4 polynomial=722a6e721636c9c4
unit2_28mm: OK keys=A1,A5,A2,A3,A4 anchor=A1 max_camera_center_separation=43.290031 unit=223961c6bce6153e polynomial=223961c6bce6153e
cross_body_28mm=OK distinct_calibration_and_composed_record_bytes
```

## Admission and Remaining Boundary

Admitted for the Lane B portion of `CLM-WARP-003`:

- the five `+0x258` items have whole-field operational identity as derived
  per-image, tier-anchor-relative calibrated camera-model records;
- their public calibration ancestry is the named camera module, focus-dependent
  intrinsics, canonical extrinsics, sensor surface, and distortion-polynomial
  paths above; and
- `0x28f5a0` uses their maximum extrinsic-center separation to size the
  reciprocal ray-depth hypothesis grid.

Still open:

- numeric `CalibStage` selector-to-`factory/current` mapping;
- the whole `state+0xe0` and `state+0x448` containers outside the admitted
  field paths;
- public origins/names for other Cost-volume operands;
- a public LRI/protobuf field for the binary-installed ray-depth bounds; and
- final source contribution and acceptance/rejection.
