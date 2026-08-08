# LLDB Evidence: `state+0x448` Box Producer Static Origin, Four Zoom

**Public-name follow-up (2026-06-26):** two-body static/runtime custody now
traces the live box-producing calibration record to
`LightHeader.module_calibration[camera].geometry.distortion.polynomial`,
including exact center, normalization, coefficient-vector, and fit-cost word
matches. The `4160 x 3120` size carrier is
`LightHeader.modules[].sensor_data_surface.size`. See
[bundle_static_runtime_state_448_distortion_polynomial_public_origin_two_body.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_state_448_distortion_polynomial_public_origin_two_body.md).

## Scope

This note narrows the remaining public-origin boundary behind
[lldb_state_448_later_box_formula_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_state_448_later_box_formula_four_zoom.md).

That runtime proof shows later `state+0x448` payload `+0x30..+0x3c` is copied
from the `0x260e40` formula over:

- the box produced by `0x145980(object)`;
- the size pair at `object+0x114/+0x118`.

This static verifier proves the installed producer shape for the box and reuses
the existing Lane B LRI verifier for the public ROI name of the size pair.

## Artifacts

- Static verifier:
  [verify_box_producer_static.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_448_later_box_formula/verify_box_producer_static.py)
- Runtime formula verifier:
  [verify_box_formula.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_448_later_box_formula/verify_box_formula.py)
- Raw runtime outputs:
  `runs/state_448_later_box_formula/`

## Verified Static Anchors

The verifier re-extracts the installed disassembly from
`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
and requires these anchor sets:

```text
0x145980 box producer
  calls 0xf3350(object)           ; object+0x10c block
  calls 0x145590(object)          ; builds sampled object-derived vectors
  calls 0xf3360(object)           ; owner-backed keyed lookup by object+0x60
  calls 0xf3330(object)           ; object+0xa0 owner/CaptureStack pointer
  calls 0xf2720(object)           ; object+0x60 key
  calls 0xe7730(owner, key)       ; reference-camera scale path
  calls 0x146380(...)             ; packages copied float-vector inputs
  stores final int32 box words to output +0x00/+0x04/+0x08/+0x0c
```

```text
0x145590 sampled-vector producer
  calls 0xe730 / 0xe810 over owner-backed optional calibration data
  writes two 30-float vectors
  guards missing CaptureStack and empty Optional data
```

```text
0xe810 radial interpolation helper
  reads center-like fields at +0x98/+0x9c
  reads radius/step-like fields at +0x80/+0x90
  reads float-vector begin/end pointers at +0x50/+0x58 and +0x68
```

The verifier also checks the existing Lane B static LRI facts:

```text
calibration payload hashes:
  32832  -> 722a6e721636c9c4
  262968 -> f0c34433f9cf9b07
  35266  -> 6a0d52b6a4d1b4de

present public proto values:
  780, 3120, 4160
```

The public ROI path for `4160 x 3120` is already admitted in
[bundle_proof_lri_calibration_origin_static.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_lri_calibration_origin_static.md):

```text
LightHeader.CameraModule[i].f9.f2.f1 = 4160
LightHeader.CameraModule[i].f9.f2.f2 = 3120
```

## Verifier Output

```text
static_box_producer=OK windows=f3330_f3350_accessors,box_producer_145980,sample_vector_145590,vector_pack_146380,reference_scale_e7730,radial_interp_e810
lri_static=OK calibration_hashes=262968:f0c34433f9cf9b07,32832:722a6e721636c9c4,35266:6a0d52b6a4d1b4de roi_values=780,3120,4160
```

## Safe Field Meaning

For the later `state+0x448` payload slice proven by the runtime formula
verifier:

```text
payload +0x30/+0x34
  = uniform scale
  = max(public_full_sensor_width / computed_box_width,
        public_full_sensor_height / computed_box_height)

payload +0x38/+0x3c
  = computed box origin
  = [float32(box.x0), float32(box.y0)]

public_full_sensor_width/height
  = object+0x114/+0x118
  = 4160 x 3120 under the admitted runtime samples
  = LRI-stored per-camera full sensor ROI
```

The `0x145980` box is a computed distortion/undistortion envelope over
owner-backed calibration data. The installed producer samples object-derived
distortion/undistortion vectors, validates matching vector sizes, computes
float min/max-style bounds, and writes the final integer box words.

## Safe Conclusion

- Proven:
  `state+0x448` payload `+0x30/+0x34` scale is normalized against the public
  LRI per-camera full sensor ROI `4160 x 3120`.
- Proven:
  `state+0x448` payload `+0x38/+0x3c` origin comes from the computed
  `0x145980` distortion/undistortion envelope box.
- Proven:
  the `0x145980` box is not a simple direct public fixed32/protobuf rectangle
  copy in the installed path; it is computed from owner-backed calibration
  data through `0x145590`, `0xe810`, `0xe7730`, and `0x146380`.
- Proven by the follow-up:
  the owner-backed calibration structure feeding `0x145980` comes from public
  `GeometricCalibration.distortion.polynomial` fields.
- Still unproven:
  a direct public field name for the computed envelope, uniform scale, or
  whole `state+0x448` payload.

## Validation Commands

```bash
python3 -m py_compile \
  tools/lldb_probes/state_448_later_box_formula/verify_box_producer_static.py
python3 tools/lldb_probes/state_448_later_box_formula/verify_box_producer_static.py
python3 tools/lldb_probes/state_448_later_box_formula/verify_box_formula.py
```
