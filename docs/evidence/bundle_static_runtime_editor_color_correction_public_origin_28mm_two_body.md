# Editor Color-Correction Public Origin and Exact Replay

## Claim target

This bundle supports a scoped addendum to `CLM-COMPAT-001` for display
callback index `10`, installed RTTI name `setColorCorrection`.

The admitted runtime pixel effect is limited to the retained Unit-1 `28mm`,
profile-3 RenderType-1, default level-4 request. Public calibration extraction
and optimizer construction additionally cover exact-28mm photographs from both
physical bodies. Installed optimizer/map formulas are body- and focal-agnostic,
but this bundle does not claim live display-index-10 captures at four focals or
under alternate editor modes.

## Installed artifacts

- `libcp.dylib` SHA-256:
  `b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`
- bundled `libceres.dylib` SHA-256:
  `dad91f3f2b05af8705b48eaa42e04aea15a5f4640528a922d2ae843c8b85bec6`
- bundled Ceres build path names version `1.12.0`
- calibration wrapper: `0x113230..0x113720`, SHA-256
  `dc574caa5e54067da98e59c652c647a6cf227b77ee3d2d8f4f058e410f5acd4a`
- optimizer body: `0x116ee0..0x11ac30`, SHA-256
  `296194837f77e02ee4c01f383c355b7ce000eacbb528da2ea48d6948aa173ed6`
- CIEDE2000 helper: `0x1273c0..0x127870`, SHA-256
  `98127d1b7f765be58307f79717e5aace8604b4613461922b90a0e9569b4ecc7a`
- thin-plate-spline evaluator: `0x11c4c0..0x11c770`, SHA-256
  `6bae868d91a7a9d524f0ef3f52d0bed1e55b40ca3b849f819a571304d35512c7`

The deterministic verifier is
`tools/lldb_probes/editor_render_type_topology/verify_color_correction_optimizer_static.py`.

## Public calibration source

Installed protobuf descriptors identify field `6` of
`ltpb.ColorCalibration` as:

```text
repeated ltpb.Point3F macbeth_data
```

The repo-local extractor
`tools/lldb_probes/editor_render_type_topology/extract_macbeth_calibration.py`
finds the exact public records in calibration block `6` of both tested photos:

| Body | Photograph | SHA-256 | Records |
|---|---|---|---:|
| Unit-1 | `2018-07-23/L16_02130.lri` | `2ac51af5...ff5` | 42 |
| Unit-2 | `2018-07-04/L16_02130.lri` | `faba5cee...1ad` | 42 |

Each body has `14 cameras x 3 illuminants`, with public type values
`0 = A`, `2 = D65`, and `6 = F11`, and each record has 24 public Macbeth
points. For all 42 same-camera/type keys, the Unit-1 and Unit-2 raw
`macbeth_data` payload hashes differ (`0/42` equal). The endpoint values are
therefore body calibration, not universal constants.

The complete extraction manifest has SHA-256
`03e0170e5a2b0601ee663e3c34231b91e0b2141ab943d4f7ebb4d134f08d7d0a`.

The separately supplied newer standalone Unit-1/Unit-2 calibration packages
also contain 42 body-different records. Their generated maps do not equal this
older photograph's retained live map. That is a negative generation-boundary
result, not proof that the map formula changed with firmware.

## Fixed target and normalization

The installed vector at `libcp+0x66dfa0` contains 24 fixed XYZ Macbeth target
points. Its raw `24 x Vec3f` SHA-256 is
`ec37cf355a4aa2204cdc579be0c2952529a51a47b37e82ed24202bcaa2763c81`.

The wrapper converts that vector from color selector `7` to selector `8` under
D50 before optimization. The resulting fixed Lab target has SHA-256
`776d05c0ad42aa6d0c557c3037bdc9e1e260995a25bfe9d1b2e054101fb73d86`.
The optimizer converts the Lab target back from selector `8` to selector `7`;
that exact rounded XYZ vector has SHA-256
`3fec8ca91fd4710c9311f3f92dc82fd42dbc68832b390e81518032b44296b77e`.

These are the exact little-endian float32 words. They are embedded here so a
replacement need not recover constants from the installed binary:

| Patch | Embedded XYZ (7) | Target Lab (8) | Round-trip XYZ (7) |
|---:|---|---|---|
| 1 | `3df1ab08 3dd3b1a9 3d52fcbd` | `4219c27d 41596300 41686750` | `3df1ab0c 3dd3b1ae 3d52fcde` |
| 2 | `3ec9d045 3eb47c4c 3e469164` | `4283e32a 418f05d0 418eea08` | `3ec9d049 3eb47c4a 3e469167` |
| 3 | `3e2dd2a8 3e3d2737 3e8553c0` | `42484130 c090e340 c1b21424` | `3e2dd2b0 3e3d273f 3e8553c7` |
| 4 | `3de0bd0f 3e08b080 3d5a9463` | `422d22b0 c153adf0 41af7dd0` | `3de0bd13 3e08b08e 3d5a9474` |
| 5 | `3e79ada1 3e6debfb 3ea9b2fd` | `425d40a6 410cc860 c1c4e098` | `3e79add5 3e6dec06 3ea9b300` |
| 6 | `3e9c1b76 3ed5baf5 3eb0cb41` | `428d6370 c2042ae8 bdf3b800` | `3e9c1b78 3ed5bafe 3eb0cb4a` |
| 7 | `3ecf2ca5 3e9f9805 3d469e3a` | `427a9b16 420d4d68 42676764` | `3ecf2caf 3e9f9809 3d469e48` |
| 8 | `3dfd383a 3de96d8f 3e9519b7` | `4220f877 411b5d50 c2317412` | `3dfd384a 3de96d96 3e9519b9` |
| 9 | `3e9a0fc6 3e4aa689 3dd11c6d` | `424e656e 423f14e8 41871d54` | `3e9a0fcd 3e4aa68b 3dd11c72` |
| 10 | `3dab7762 3d83d65a 3dd4723b` | `41f3ebd4 41a828d8 c1a04250` | `3dab7767 3d83d664 3dd47241` |
| 11 | `3eb52c1e 3ee30ebc 3db8206b` | `4290eb80 c1ba8c60 4263fae8` | `3eb52c22 3ee30ec6 3db82070` |
| 12 | `3ef9f5c2 3edf1dd9 3d761749` | `428fe3ef 419b87e0 42883bbe` | `3ef9f5e2 3edf1de3 3d761750` |
| 13 | `3d8e9d64 3d6d1ca1 3e5b09d5` | `41e6fcc6 416ccdf0 c2489cdc` | `3d8e9d66 3d6d1cae 3e5b09f3` |
| 14 | `3e197de4 3e6c3e67 3d9f55e5` | `425c9490 c2173f80 41fd18c8` | `3e197ded 3e6c3e6f 3d9f55e7` |
| 15 | `3e60b0f9 3e01d1c7 3d1c7940` | `42291818 42585580 41e54518` | `3e60b100 3e01d1cc 3d1c7943` |
| 16 | `3f1a5db2 3f1ba6e1 3d972ad4` | `42a48b3a 407f7c80 429ffb12` | `3f1a5db3 3f1ba6e2 3d972ad6` |
| 17 | `3e9ea42d 3e4d740c 3e6d0192` | `424fa318 42470b38 c15d4f18` | `3e9ea42e 3e4d740c 3e6d01a5` |
| 18 | `3e0a00ce 3e42e324 3e9a7031` | `424ae5f8 c1e0fce0 c1dfa9c8` | `3e0a00e6 3e42e325 3e9a7037` |
| 19 | `3f60a55b 3f69b21c 3f39c035` | `42c10e79 befd0c00 401a3b80` | `3f60a560 3f69b21f 3f39c033` |
| 20 | `3f10948f 3f16a769 3ef775cc` | `42a26ad2 bf286e00 3e883400` | `3f109492 3f16a769 3ef775d0` |
| 21 | `3eb0ab1a 3eb81227 3e97ee5c` | `4284f72a bf0bc800 bc2d8000` | `3eb0ab1f 3eb8122b 3e97ee5f` |
| 22 | `3e3b7fbf 3e43ca46 3e2228e3` | `424b4f52 bf27ca00 be0fdc00` | `3e3b7fc2 3e43ca49 3e2228e4` |
| 23 | `3daf1673 3db6ef7e 3d997954` | `420f6a4d bf0d2c00 befcad00` | `3daf1671 3db6ef7c 3d997954` |
| 24 | `3cfc9100 3d02ea30 3cdc0c05` | `41a68108 3cb46000 bec67200` | `3cfc9129 3d02ea45 3cdc0c23` |

Before fitting, every public source patch lane is multiplied in float32 by:

```text
source_scale = round_f32(roundtrip_target_xyz[18].y / source_rgb[18].y)
```

Patch array index `18` is Macbeth patch 19, the first neutral patch. For the
retained Unit-1 camera-0/type-0 record, the scale is exactly
`1.0019376277923584`.

## Exact 3x3 optimizer

Let `S` be the normalized 24-row public source matrix and `Txyz` the rounded
fixed target XYZ matrix. Lumen appends source row
`[1e-6, 1e-6, 1e-6]`; the corresponding residual weight is zero. The other 24
weights are one. The initial 3x3 is the ordinary weighted least-squares solve
mapping source RGB to target XYZ. Ceres receives the nine parameters in Eigen
column-major order.

For each real patch, the optimizer computes:

```text
predicted_xyz = M * normalized_source_rgb
predicted_lab = CIELAB_D50(predicted_xyz)
residual[i]   = sqrt(weight[i]) * CIEDE2000(predicted_lab, target_lab[i])
residual[24]  = 0
```

The exact D50 xy float words are `0x3eb0fb8d,0x3eb78cd0`, or approximately
`0.3456691801548004,0.35849618911743164`. The cost object constructs
`1/Xn,1,1/Zn` in float32 from those words. CIELAB uses:

```text
epsilon = 0.008856451679035631
f(t) = cbrt(t)                                      when t > epsilon
     = 7.787037037037037*t + 0.13793103448275862   otherwise
L = 116*f(Y) - 16
a = 500*(f(X) - f(Y))
b = 200*(f(Y) - f(Z))
```

`0x1273c0` is the standard CIEDE2000 scalar formula. Direct installed-helper
evaluation of eight Sharma boundary/test pairs agrees with the independent
formula to less than `4e-14`.

The exact Ceres Solver 1.12 options are:

```text
minimizer_type            = LINE_SEARCH
line_search_direction     = BFGS
line_search_type          = WOLFE
linear_solver_type        = DENSE_QR
max_num_iterations        = 2000
function_tolerance        = 1e-10
gradient_tolerance        = 1.0000000000000002e-14
parameter_tolerance       = 1e-8          # 1.12 default retained
num_threads               = 1
logging_type              = SILENT
minimizer_progress_stdout = false
```

The no-debugger `__DATA,__interpose` capture in
`capture_ceres_solve_interpose.cpp` observes exactly those fields at the live
`ceres::Solve` boundary. For public Unit-1 camera `0`, type `0`, both Lumen and
the independent Ceres harness terminate after 15 iterations. Their initial
costs differ by less than `6e-12`, seeds by less than `1e-13`, optimized doubles
by less than `2e-14`, and the actual emitted raw matrix agrees in all nine
float32 words:

```text
3f3690a4 3e9137dd 3e32f2ec
3dc9b39a 3f90a205 bef76e1b
beaee203 bf5679ea 40843ad5
```

The independent cost, normalization, seed, and postprocess implementation is
`cleanroom_optimize_macbeth.cpp`. For exact parity verification it compiles
against upstream Ceres 1.12.0 headers and executes the bundled open-source
`libceres.dylib`; it makes no `libcp` call. A replacement application must
build/link upstream Ceres (or an independently validated equivalent), not use
the Lumen-bundled binary.

## Wrapper endpoint matrix

The optimizer's raw matrix is white-normalized before storage. In float32:

```text
W = [Xn, 1, Zn] from exact D50 xy
q = inverse(M) * W
stored_matrix = M * diag(q)
```

The installed grouping is `(inverse_row[0]*Xn + inverse_row[1]) +
inverse_row[2]*Zn`. The clean-room postprocess agrees with the public-record
wrapper in all nine stored words for the same endpoint:

```text
3f17e569 3e937278 3da9c3d4
3da7d166 3f92da53 be6abb48
be918127 bf59c4a7 3ffae31a
```

## HSV map construction

Installed-static proof gives the complete map construction:

1. Convert the first 18 chromatic normalized-source and fixed-target patches
   to HSV.
2. Form controls
   `clamp(target_h-source_h,-1/36,+1/36)`,
   `clamp(target_s/source_s,0.9,1.1)`, and
   `clamp(target_v/source_v,0.975,1.025)`.
3. Add 24 identity boundary controls: hue
   `0,1/6,...,5/6` crossed with saturation `0,0.15,0.95,1`.
4. Duplicate all 42 controls at hue minus one and hue plus one, yielding 126
   periodic controls.
5. Fit three thin-plate splines with
   `phi(r)=r^2*log10(r)`, affine tail `a0+a1*h+a2*s`, and
   `lambda=0.001500000013038516*mean_pair_distance^2`, where the mean is over
   all `N^2` control pairs.
6. Evaluate a `32x32x1` hue/saturation lattice and store the padded `33x33`
   `Vec4` grid (1089 cells). Saturation below `0.0001` forces value scale one.

At application, bilinear interpolation over the padded grid gives
`(hue_delta_wrapped, saturation_scale, value_scale, 0)`. Output is:

```text
h' = wrap01(h + map.x)
s' = clamp01(s * map.y)
v' = v * map.z                 # no upper clamp
```

The 84 two-body endpoint maps generated through the installed body are recorded
in manifest SHA-256
`415305254dd6e59c13e9c95195884280171595250fa0a7dd3c76cb37dd6afe3b`.

## Live endpoint selection

The retained live owner has scene xy words
`0x3eb160b2,0x3eb4bc02`. Installed `0xab2e0` returns scene CCT
`4953.66064453125` (`0x459acd49`). Owner endpoint CCTs are
`2855.63232421875` (A/type 0) and `6502.08203125` (D65/type 2).

The live `32x32x1` map SHA-256 is
`cefa2afb27dc42a1307bf4841b078b36f327c65d8b021c0afe7fc1937dc0fdc4`.
Across all 14 Unit-1 camera candidates, only public camera id `0` produces that
map exactly.

Map interpolation `0x350960` uses mixed float/double reciprocal-temperature
arithmetic and alpha `0.244790717959404` (`0x3e7aaa6b`):

```text
map = upper*(1-alpha) + lower*alpha
```

Matrix interpolation `0xab720` is a distinct all-float path with alpha
`0.24479074776172638` (`0x3e7aaa6d`):

```text
matrix = upper + alpha*(lower-upper)
```

The two alpha helpers must not be collapsed.

## Pixel effect and exact replay

The live conversion wrapper receives input/source selector `0` (the interpolated
custom camera matrix) and output/destination selector `5`
(`linear_prophoto_rgb`, D50). Selected converter `0xab940` computes:

```text
conversion = inverse(ProPhoto_RGB_to_XYZ) * custom_RGB_to_XYZ
```

Both configs carry exact D50 xy, so chromatic adaptation is identity. Its pixel
accumulation order is `(blue_term + red_term) + green_term`; alpha is copied.

Retained complete float images are:

| Stage | Size | SHA-256 |
|---|---:|---|
| display stage 3 input | `5,101,248` bytes | `5215ffca...c40` |
| display stage 10 output | `5,101,248` bytes | `b31fb9f6...927` |

Independent replay performs the custom-to-ProPhoto matrix conversion, RGB/HSV
map application, and HSV/RGB conversion. It matches all `5,101,248` output
bytes: `different_bytes=0`.

The consolidated verification report SHA-256 is
`518715f331cdb29da98cc21913c29bb9f805ae99e001c345bf90436ed71052cd`.

## Reproduction

Run:

```bash
bash tools/lldb_probes/editor_render_type_topology/run_live_color_correction_public_join.sh
```

The runner uses a scoped DYLD code interposer for the installed callback and
conversion wrapper because host debugger launch is disabled. It does not alter
system security settings. Upstream Ceres 1.12.0 source is cached under ignored
`runs/editor_render_type_topology/`; no durable evidence depends on `/tmp`.

## Admission boundary

This evidence closes the selected display index-10 public calibration origin,
optimizer, endpoint selection, matrix/map application, and complete pixel
effect at Unit-1 `28mm` default level 4. It proves body-specific calibration
values with exact-28mm records from two physical units.

It does not prove that every focal, pyramid level, editor cache, DOF mode,
manual control, F11 selection, or newer calibration generation selects the same
runtime branch or values. `CLM-COMPAT-001` therefore remains `PARTIAL` and
`REFERENCE_ONLY`; this closure is not merge-critical and does not change the
canonical profile-3 linear-output parity exit.
