# Evidence: Public Movable-Mirror Pose Formula

## Result

The installed profile-3 calibration constructor's movable-mirror path is
closed from public LRI fields through the exact factory/current `R,t` packet.
The live `CameraModule.mirror_position` is not converted to mirror angle by a
linear fit. For every supported calibration packet observed in the two local
physical-unit signatures, Lumen applies the public type-0 quadratic inverse,
selects the minus root, rotates the public zero-angle mirror normal, reflects
the public real camera through the resulting mirror plane, and applies an
image-axis sign matrix in extrinsics.

The runtime movable set is:

```text
B1 B2 B3 B5 C1 C2 C3 C4
 5  6  7  9 10 11 12 13
```

In the selected tele constructor packets, B4 (`8`) and C5 (`14`) use fixed
pose records. This corrects the older config-cardinality inference that called
C2/C3 fixed and C5 movable; config-table cardinality is not the geometric pose
constructor's movable/fixed discriminator.

## Public Schema

Installed `mirror_system.proto` descriptor SHA-256:

```text
1aeb93af4da6e7a8377f41095187709e6fd17c337f5977cbaae4142bac562848
```

The descriptor proves these implementation-required public names:

| Message | Field | Public name |
|---|---:|---|
| `MirrorSystem` | 1 | `real_camera_location` |
|  | 2 | `real_camera_orientation` |
|  | 3 | `rotation_axis` |
|  | 4 | `point_on_rotation_axis` |
|  | 5 | `distance_mirror_plane_to_point_on_rotation_axis` |
|  | 6 | `mirror_normal_at_zero_degrees` |
|  | 7 | `flip_img_around_x` |
|  | 8 | `mirror_angle_range` |
|  | 9 | `reprojection_error` |
| `MirrorActuatorMapping` | 1 | `transformation_type` |
|  | 2 | `actuator_length_offset` |
|  | 3 | `actuator_length_scale` |
|  | 4 | `mirror_angle_offset` |
|  | 5 | `mirror_angle_scale` |
|  | 6 | `actuator_angle_pair_vec` |
|  | 7 | `quadratic_model` |
|  | 8 | `angle_to_hall_code_error` |
|  | 9 | `hall_code_to_angle_error` |
|  | 10 | `hall_code_range` |
| `QuadraticModel` | 1 | `use_rplus_for_left_segment` |
|  | 2 | `use_rplus_for_right_segment` |
|  | 3 | `inflection_value` |
|  | 4 | `model_coeffs` |

The exact enum is `MEAN_STD_NORMALIZE = 0` and `TAN_HALF_THETA = 1`.
Every checked packet in both physical calibration signatures is type 0. Type 1
is accepted by the installed schema/body but is not observed or admitted here.

## Exact Actuator Formula

Let `h` be public `CameraModule.mirror_position`, let `c0..c5` be the six
public `quadratic_model.model_coeffs`, and use the public mapping scalars.
The installed path evaluates in double precision after converting public
float32 fields to double:

```text
x = (h - actuator_length_offset) / actuator_length_scale

A = c0*x + c3
B = c1*x + c4
C = c2*x + c5

disc    = B*B - 4*A*C
r_plus  = (-B + sqrt(disc)) / (2*A)
r_minus = (-B - sqrt(disc)) / (2*A)

if h < inflection_value:
    use_plus = use_rplus_for_left_segment
else:
    use_plus = use_rplus_for_right_segment

r = r_plus if use_plus else r_minus
theta_degrees = mirror_angle_offset + mirror_angle_scale*r
```

All checked public packets set both root flags false, so every observed
supported packet selects `r_minus` on either side of the inflection. The
Unit-1 70mm B2 example uses `h=790` and produces exactly
`44.17436883135109` degrees. The verifier obtains zero error for every live
angle in the Unit-1 70/150mm and Unit-2 70mm runs.

## Exact Pose Formula

Let the public fields be:

```text
a0 = rotation_axis
n0 = mirror_normal_at_zero_degrees
Q  = real_camera_orientation
C0 = real_camera_location
P0 = point_on_rotation_axis
d  = distance_mirror_plane_to_point_on_rotation_axis
```

Then:

```text
a = normalize(a0)
theta = theta_degrees * pi / 180
n = Rodrigues(a, theta) * n0

P = P0 + d*n
H = I - 2*n*n^T
C = C0 + 2*n*dot(n, P - C0)

F = diag(-1,  1, 1)  when flip_img_around_x == false
F = diag( 1, -1, 1)  when flip_img_around_x == true

R = F * transpose(Q) * H
t = -R*C
```

The installed degree conversion constant at `0x5d3ac8` is exactly
`pi/180`. The body computes `R,t` in double precision, then converts them to
float32 for the CalibStage factory/current records. It does not add an image
width/height principal-point offset at this constructor edge.

## Installed Static Proof

Installed `libcp.dylib` SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

The verifier Capstone-asserts the mode-2 dispatch and public live-value
handoff, six-coefficient `A/B/C` construction, quadratic solver and public
left/right root selector, axis normalization, degree conversion, mirror-plane
center reflection, `flip_img_around_x` sign branch, orientation transpose, and
`t=-R*C`. It also pins the concatenated relevant body windows:

```text
5b14a40594e44ea1094ea398cc40cf4602a0d99e2c5480989ce4e54cc2c5e856
```

The constructor chain is:

```text
0x1f1047 mode 2
  -> 0x1f1072 / 0x1f0a00 public MirrorSystem + mapping selection
  -> 0x1f109c / 0x1c1860 / 0x1ed4d0 actuator inversion
  -> 0x1f10b2 / 0x1c79e0 / 0x1c7580 pose construction
  -> 0x1f1328 factory CalibStage float32 copy
```

## Runtime Matrix

| Physical signature / focal | Movable keys checked | Public-field error | Angle error | Pose result |
|---|---|---:|---:|---:|
| Unit-1 `28mm` | `5,6,7,9` | public decode | static/replayed | float32 `R,t` bit-exact |
| Unit-1 `35mm` | `5,6,7,9` | public decode | static/replayed | float32 `R,t` bit-exact |
| Unit-1 `70mm` | all eight | `0` | `0` | double max error `1.78e-14`; float32 bit-exact |
| Unit-1 `150mm` | all eight | `0` | `0` | double max error `3.73e-14`; float32 bit-exact |
| Unit-2 `70mm` | all eight | `0` | `0` | double max error `3.20e-14`; float32 bit-exact |

The `28/35mm` rows independently reuse completed retained `0x1f0ce0`
constructor reports and compare their final selector-0 float32 packets. The
three dedicated reports each record eight mapping entries, eight mapping
exits, eight pose entries, eight pose exits, ten factory copies, no probe
errors, no step cap, normal process exit, and a valid Radiance output.

## Scope And Nonclaims

- Four-zoom merge-critical scope is Unit-1 `28/35/70/150mm`; `28/35mm`
  exercise the four firing movable B cameras and `70/150mm` exercise all eight
  movable B/C cameras.
- Cross-unit discrimination is exact-focal Unit-2 `70mm`, exercising all eight
  movable cameras under calibration signature `223961c6...`; Unit-1 uses
  `722a6e72...`.
- Installed formula scope is body/focal independent for this pinned binary and
  observed type-0 packet family.
- Capture-date or possible firmware differences are not assigned as causes.
- Type-1 `TAN_HALF_THETA`, malformed discriminants, and unobserved calibration
  signatures are not generalized from the type-0 runtime corpus.
- Later bundle adjustment may update the current CalibStage bank. This evidence
  closes the public constructor origin/formula, not every downstream mutation.
- The old config-cardinality document is not otherwise promoted; only its
  movable/fixed geometric classification is corrected here.

## Implementation Consequence

A clean-room implementation must replace a linear Hall-to-angle approximation
with the public quadratic inverse above and construct extrinsics with the exact
`F * Q^T * H` convention. Moving `flip_img_around_x` into K with image-size
principal-point offsets is not equivalent at this edge. Any residual optical
flow or self-calibration should remain diagnostic until the exact public
constructor pose and the already-admitted downstream calibration updates are
implemented and revalidated.

## Reproduction

```bash
python3 tools/lldb_probes/movable_mirror_pose_formula/verify_movable_mirror_pose.py
```

Expected terminal markers include:

```text
static_movable_mirror=OK
unit1_28mm_retained: ... f32_pose_err=0
unit1_35mm_retained: ... f32_pose_err=0
unit1_70mm: ... max_angle_err=0
unit1_150mm: ... max_angle_err=0
unit2_70mm: ... max_angle_err=0
```

The reusable full runner is:

```bash
bash tools/lldb_probes/movable_mirror_pose_formula/run_two_body.sh
```

Admit as `CLM-WARP-003` and `CLM-STATE-001` addenda. Existing claim statuses
remain unchanged.
