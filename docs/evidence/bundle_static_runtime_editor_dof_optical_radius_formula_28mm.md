# Evidence: Editor DOF Optical Range and Tile-Radius Formula

**Date:** 2026-07-16  
**Status:** VERIFIED, reference-only editor scope  
**Installed bundle:** `libcp.dylib` SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`

## Scope

This bundle closes the optical range helper at `0x2c5710`, the per-tile blur
radius helper at `0x2c5590`, and the public origin of the image scale used to
derive physical pixel pitch. Runtime replay is one Unit-1 `28mm`, profile-3,
RenderType-1 mode-1 DOF treatment. Public `data_scale` wire values are checked
across the exact-focal `28/35/70/150mm` representatives from both physical
calibration bodies.

This does not close `ImageCircleFilter`, the `RunTiledDefocusBlur` layer and
occlusion composition, modes `2/3/4`, or DOF runtime behavior at other focals.

## Reusable Artifacts

- Interposer:
  `tools/lldb_probes/editor_render_type_topology/capture_editor_dof_math_interpose.c`
- Exact x86 replay:
  `tools/lldb_probes/editor_render_type_topology/replay_editor_dof_math.c`
- Runner:
  `tools/lldb_probes/editor_render_type_topology/run_editor_dof_math.sh`
- Verifier:
  `tools/lldb_probes/editor_render_type_topology/verify_editor_dof_math.py`
- Rerunnable report:
  `runs/editor_render_type_topology/editor_dof_math_mode1_blur9_f2.json`

## Public and Installed Optical Tuple

`DOFCache` receives a six-word tuple from `0x3b4970`. Installed helper
`0xe7020` chooses physical and 35mm-equivalent focal lengths from reference
camera group and sensor type; `0xe76b0` chooses the fixed hardware f-number
from camera group; `0xe7730` computes pixel pitch from the reference image.

Installed float tables are exact binary values:

```text
camera group A hardware f-number = 2.0
camera group B hardware f-number = 2.0
camera group C hardware f-number = 2.4000000953674316

group B physical/equivalent focal = 9.1899995803833 / 70.0 mm
group C physical/equivalent focal = 19.770000457763672 / 150.0 mm

group A sensor type 1 = 4.559999942779541 / 35.0 mm
group A sensor type 4 = 3.950000047683716 / 28.0 mm
group A sensor type 2 = 3.680000066757202 / 28.0 mm

sensor type 4 base pixel pitch = 0.0012 mm
sensor type 2 base pixel pitch = 0.0011 mm
sensor type 1 base pixel pitch = 0.0014 mm
```

The installed protobuf descriptors name the public scale carrier:

```text
LightHeader.modules[].sensor_data_surface.data_scale: Point2F
Point2F.x / Point2F.y: required float
```

The `CapturedImage` constructor reads `CameraModule.Surface+0x28`, extracts
the `Point2F`, substitutes `[1,1]` only when both values are zero, and stores
the result at `CapturedImage+0x124/+0x128`. `0xe7730` reads `+0x124` and
computes:

```text
pixel_pitch_mm = sensor_type_base_pitch_mm / data_scale.x
```

All 84 camera-module records in the two-body exact-focal corpus carry
`data_scale = [1.0,1.0]`. For the treated A1 reference camera the selected
tuple is therefore physical focal `3.680000066757202`, equivalent focal
`28.0`, hardware f-number `2.0`, and pixel pitch `0.0010999999940395355` mm.
These lens constants are selected by installed camera identity/type logic;
they are not copied from `LightHeader.image_focal_length` or the optional
capture `ViewPreferences.f_number`.

## Focus-Range Formula

For inputs:

```text
z = focus depth
f = physical focal length
p = physical pixel pitch
N = f-number
b = maximum in-focus blur pixels, requiring 0 < b < 10
```

the float32 helper at `0x2c5710` evaluates, in this exact operation order:

```text
H = f*f / ((p+p)*N)
q = ((z-f)*b) / H
near = z / (1+q)
far_candidate = z / (1-q)
far_guarded = 100000.0 if far_candidate < 0 else far_candidate
far = min(far_guarded, 10*z)
```

The x86 replay preserves each scalar binary32 operation. It reproduces all
64 retained live calls byte for byte. The first treatment call is:

```text
input  = [6020.888671875, 3.680000066757202,
          0.0010999999940395355, 2.200000047683716,
          0.699999988079071]
output = [2403.19482421875, 60208.88671875]
bits   = [4516331e, 476b30e3]
```

## Per-Tile Radius Formula

`0x2ce6d0` supplies the two supported depth-type policies:

```text
depth type 0: R=512, near_scale=0.5
depth type 1: R=32,  near_scale=0.25
```

For a tile depth interval `[z0,z1]`, physical focal `f`, level pixel pitch
`p`, effective f-number `N`, and focus depth `zf`, `0x2c5590` computes:

```text
H = f*f / ((p+p)*N)

signed_radius(z):
  side = near_scale if z < zf else 1.0
  raw = side * H * (z-zf) * rcp_approx(z*(zf-f))
  return clamp(raw, -near_scale*R, R)

m = max(abs(signed_radius(z0)), abs(signed_radius(z1)))
e = trunc(log2f(m) / log2(2.0)) + 1
tile_radius = trunc(ldexp(1.0,e) * 1.600000023841858)
```

`rcp_approx` is the installed SSE `rcpss` instruction, not exact division.
The clean-room replay uses `_mm_rcp_ss` and preserves the installed arithmetic
order. It exactly reproduces one retained live representative for every
observed treatment result bucket:

```text
1, 3, 6, 12, 25, 51, 102
```

Those seven values are observed incidence for this treatment, not a universal
enumeration of possible outputs. The full treatment recorded 730 radius calls
with observed minimum `1` and maximum `102`.

## Validation

```text
installed_constants=OK physical_focal=9.1899995803833,19.770000457763672,4.559999942779541,3.950000047683716,3.680000066757202
installed_constants=OK equivalent_focal=70.0,150.0,35.0,28.0
installed_constants=OK pixel_pitch=0.0012,0.0011,0.0014 hardware_f_number=2.0,2.0,2.4000000953674316
public_data_scale=OK modules=84 values=[1.0]
focus_range_replay=OK samples=64
tile_radius_replay=OK representatives=7 results=[1, 3, 6, 12, 25, 51, 102]
```

Run with:

```bash
bash tools/lldb_probes/editor_render_type_topology/run_editor_dof_math.sh
python3 tools/lldb_probes/editor_render_type_topology/verify_editor_dof_math.py
```

## Admission Boundary

Admit as a `CLM-COMPAT-001` reference-only addendum: installed camera optical
constants, public `sensor_data_surface.data_scale` pitch ancestry, exact
focus-range formula, and exact tile-radius formula. Runtime formula replay is
Unit-1 `28mm`; public scale schema/value coverage is two bodies by four exact
focal tiers. Do not infer complete DOF rendering, other modes/focals, or a
base profile-3 merge requirement from this result.
