# Static/Runtime Evidence: `state+0x448` Distortion Polynomial Public Origin

**Date:** 2026-06-26  
**Status:** VERIFIED; admitted public-source refinement, no claim-status upgrade  
**Bearing:** Lane B, `CLM-WARP-003`; later `state+0x448` payload
`+0x30..+0x3c`

## Question

Earlier evidence proved that later `state+0x448` payload fields are computed
from:

```text
payload +0x30/+0x34 = uniform scale
payload +0x38/+0x3c = box origin
box                    = 0x145980(object)
size                   = CameraModule.sensor_data_surface.size
```

The remaining public-meaning gap was whether the calibration structure feeding
`0x145980` could be tied to a concrete public protobuf path.

## Public Schema

The installed serialized descriptors prove these exact names:

```text
LightHeader.module_calibration
FactoryModuleCalibration.geometry
GeometricCalibration.distortion
Distortion.polynomial
Distortion.Polynomial.distortion_center
Distortion.Polynomial.normalization
Distortion.Polynomial.coeffs
Distortion.Polynomial.fit_cost
Distortion.Polynomial.valid_roi
```

The admitted runtime path below consumes the first four polynomial data
components. It does not establish use of `valid_roi` by this box path.

## Static Custody

The verifier pins the installed `libcp.dylib` SHA-256 and exact instruction
anchors through the following chain:

```text
0xe3360 conversion path
  FactoryModuleCalibration.geometry
  -> 0x1302e0

0x1302e0
  GeometricCalibration+0x30
  -> Distortion
  Distortion+0x18
  -> Distortion.polynomial

  polynomial.distortion_center
  -> internal calibration record +0x60/+0x64

  polynomial.normalization
  -> internal calibration record +0x68/+0x6c

  polynomial.coeffs
  -> internal calibration record vector +0x70/+0x78/+0x80

  polynomial.fit_cost
  -> internal calibration record +0x88/+0x8c

0xf3360 -> 0xe7220
  owner tree lookup keyed by object+0x60
  -> the converted per-camera calibration record

0x145590
  checks record+0x90 polynomial presence
  reads record+0x60..+0x6c
  passes record+0x70 coefficient vector to 0xe730
  -> 0xe810 interpolation
  -> 0x145980 distortion/undistortion envelope box
```

Pinned combined static-window SHA-256:

```text
f9d22becc3993aedc44e6e244269747117480fb352996cf301a9439e6a3fcb63
```

## Two-Body Runtime Match

A breakpoint at `libcp+0x1455d5`, immediately after `0xf3360` returns the
keyed calibration record, captured the live center, normalization, coefficient
vector, and optional fit-cost words. The verifier independently parsed the
same camera's public
`module_calibration[].geometry.distortion.polynomial` record from each LRI and
required exact raw-word equality.

| Case | Physical body | Routing class | Runtime keys | Events | Geometry SHA-256 prefix |
|---|---|---|---|---:|---|
| Unit-1 exact 28mm | Unit-1 | wide | `0..9` | 28 | `722a6e721636c9c4` |
| Unit-2 exact 70mm | Unit-2 | tele | `5..14` | 28 | `223961c6bce6153e` |

Every captured event matched its same-camera public polynomial record:

- exact `distortion_center` words;
- exact `normalization` words;
- exact complete `coeffs` vector and count;
- exact `fit_cost` presence and word.

Both renders completed with exit status `0`. The different geometry hashes
make this a real two-body check, while the wide/tele choice covers both routing
classes without repeating a full four-zoom campaign on each body.

## Admitted Meaning

The later `state+0x448` formula now has concrete public input ancestry:

```text
box input
  <- computed 0x145980 distortion/undistortion envelope
  <- live converted per-camera calibration record
  <- LightHeader.module_calibration[camera]
     .geometry.distortion.polynomial
     .{distortion_center, normalization, coeffs, fit_cost}

size input
  <- LightHeader.modules[camera].sensor_data_surface.size

payload +0x30/+0x34
  = derived uniform scale

payload +0x38/+0x3c
  = derived box origin
```

This closes the public calibration/LRI origin of the box-producing structure.
It does not turn the computed envelope, uniform scale, or whole
`state+0x448` payload into direct protobuf fields.

## Three-Operand Boundary

- `state+0xe0`: scoped public camera, intrinsics, focus-Hall, and canonical
  pose components are named and admitted; the whole derived/composed container
  and selector-bank semantics remain open.
- `state+0x448`: first pose fields have direct public canonical-extrinsics
  origins, and the later box/scale slice now has named public
  `Distortion.polynomial` plus `sensor_data_surface.size` ancestry; the whole
  keyed payload remains derived.
- `record+0x40`: remains the internally depth-labeled runtime-generated
  `UpsampleLayer+0x90` descriptor. Its dimensions derive from public
  `sensor_data_surface.size`; its pixels are not an LRI-stored depth map, and
  the internal ray-depth bounds still lack a proved public unit or protobuf
  field.

## Non-Claims

- This does not prove that `state+0x448` is a direct public distortion table.
- This does not prove use of `Distortion.Polynomial.valid_roi` in this path.
- This does not name the computed envelope or uniform scale as protobuf fields.
- This does not close full `state+0xe0`, full `state+0x448`, source-record
  public names, index-5 physical semantics, ray-depth public units, final
  contribution, or acceptance/rejection.
- `CLM-WARP-003` remains `PARTIAL`.

## Artifacts

- Runtime probe:
  [distortion_public_origin_probe.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_448_later_box_formula/distortion_public_origin_probe.py)
- Static/runtime verifier:
  [verify_distortion_public_origin.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_448_later_box_formula/verify_distortion_public_origin.py)
- Two-body runner:
  [run_distortion_public_origin_two_body.sh](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_448_later_box_formula/run_distortion_public_origin_two_body.sh)
- Raw reports:
  `runs/state_448_distortion_public_origin/`

Validation:

```bash
bash tools/lldb_probes/state_448_later_box_formula/run_distortion_public_origin_two_body.sh
python3 tools/lldb_probes/state_448_later_box_formula/verify_distortion_public_origin.py
```

Verifier output:

```text
static_public_distortion_origin=OK window_sha256=f9d22becc3993aedc44e6e244269747117480fb352996cf301a9439e6a3fcb63 distortion.proto=3651b91818e2f71d geometric_calibration.proto=0ae64c39c443f72f lightheader.proto=8c3795d6c609bcfe
unit1_28mm: keys=0,1,2,3,4,5,6,7,8,9 events=28 geometry_sha256=722a6e721636c9c4
unit2_70mm: keys=5,6,7,8,9,10,11,12,13,14 events=28 geometry_sha256=223961c6bce6153e
```
