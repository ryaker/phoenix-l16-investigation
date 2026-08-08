# Static/Runtime Evidence: Exact Index-5 Plane-Sweep Correspondence

**Date:** 2026-07-16  
**Status:** VERIFIED; admitted `CLM-STEREO-001` formula addendum  
**Bearing:** selected profile-3 mode-8 index-5 cost-volume construction

## Questions

This bundle closes two implementation-facing questions:

1. the exact coordinate system and calibrated transform used to project one
   index-5 reference ray-depth hypothesis into each non-anchor stereo image;
2. the identity of the fixed G-42 reference operand.

## Artifacts

- reusable LLDB harness:
  `tools/lldb_probes/index5_plane_sweep_correspondence/`
- static/runtime verifier:
  `verify_plane_sweep_correspondence.py`
- generated replay packet:
  `runs/index5_plane_sweep_correspondence/unit1_28mm/correspondence_examples.json`
- same-render runtime packet:
  `runs/index5_plane_sweep_correspondence/unit1_28mm/report.json`
- independent fallback/runtime-repeat inputs:
  - `runs/index5_composed_geometry_origin/composed_geometry_28mm.json`
  - `runs/codex_index5_lookup_vector_public_origin/lookup_vector_public_28mm.json`
  - `runs/reference_stage_maps/unit1_28mm/index5_hypothesis_index.u16le`

The verifier pins installed `libcp.dylib` SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

It also pins complete code windows for `0x25e0c0`, `0x25e4b0`,
`0x26a790`, the live mode-8 caller at `0x2769fc`, projection/cost worker
`0x2732f0`, and its mode-8 caller around `0x276f76..0x2773e1`.

## Coordinate Domain

For selected index `5`, `(u,v)` is in the live StereoLayer level domain:

```text
width  = 2080
height = 1560
stride = 2080 pixels
```

The winning-hypothesis image and all five `Images` operands use that domain.
The worker receives the current integer level pixel as float32 at context
`+0x20/+0x24`. It does not receive full-resolution `4160x3120` coordinates.
No extra factor of two belongs in the projection formula.

The five wide-tier camera products are ordered:

```text
A1, A5, A2, A3, A4
```

`0x26a790` begins at ordinal `1`, so A1 is the fixed reference and four
projection records are built for A5, A2, A3, and A4. The tele-tier equivalent
is B4 reference followed by B2, B5, B1, and B3.

## Image Domain

The sampled images are not native/distorted `4160x3120` sensor planes.
They are the generated `2080x1560 Image<vec4x8ui>` products of public
`lt::StereoISP::CreateStereoImage`.

Installed custody already proves those products enter `StereoLayer+0x240`
`Images`. The SHA-pinned `CreateStereoImage` body constructs the calibrated
lens field at `0x27bee4 -> 0x145580`, constructs its no-map camera projection
at `0x27bf4b -> 0x25e4b0`, and installed RTTI names the associated
`ImageWarp<ResamplerFilter 5, ..., LensUndistortCRA, ...>` specialization.
Thus this is the calibration-undistorted stereo/pinhole domain.

This must not be confused with the separately captured
`SourceImageCache *_undistorted_plane.rgba16f` artifacts. Those are larger
RGBA16F source-cache products for another pipeline boundary. Index 5 samples
the 2080x1560 `CreateStereoImage` vec4u8 products.

## Exact Geometry Construction

For each source, the input `0xa8` camera records supply float32 `K`, `R`, and
`t`. `0x25e0c0` promotes them to double and forms homogeneous 4x4 matrices:

```text
E = [ R  t ]
    [ 0  1 ]

Cref = Kref4 * Eref
Csrc = Ksrc4 * Esrc
H    = Csrc * inverse(Cref)
```

The exact multiply order is therefore:

```text
H = (Ksrc4 * [Rsrc|tsrc]) * inverse(Kref4 * [Rref|tref])
```

The installed `0x9db20` helper performs the double 4x4 inverse. The result is
converted to float32 and physically stored transposed in each `0x50` worker
record:

```text
record +0x00..0x0c = H column 0
record +0x10..0x1c = H column 1
record +0x20..0x2c = H column 2
record +0x30..0x3c = H column 3
record +0x40       = null map pointer
record +0x48/+0x4c = 1.0f, 1.0f
```

This transpose is intentional. The SIMD worker multiplies the four stored
columns by four scalar coordinates, thereby evaluating ordinary `H*q`.

## Exact Projection

Let `d` be the selected float32 ray-depth lookup value in millimeters. It is
not inverse depth. For integer level pixel `(u,v)`, `0x2732f0` evaluates in
this float32 instruction order:

```text
qx = f32(f32(u * d) * scale_x)       # scale_x = 1 here
qy = f32(f32(v * d) * scale_y)       # scale_y = 1 here

P  = f32(d  * H_column_2)
P  = f32(P  + H_column_3)
P  = f32(P  + qx * H_column_0)
P  = f32(P  + qy * H_column_1)

inv_z = f32(1.0f / P.z)
sx    = f32(f32(P.x * inv_z) + 0.25f)
sy    = f32(f32(P.y * inv_z) + 0.25f)
```

Equivalently, before float32 rounding:

```text
P = H * [u*d, v*d, d, 1]^T
```

The source center is clamped to:

```text
x in [source.x0 + 1, source.x1 - 3]
y in [source.y0 + 1, source.y1 - 3]
```

Integer bases use truncation toward zero. `trunc(2*sx)&1` and
`trunc(2*sy)&1` choose the half-pixel phases. The worker uses x86 `pavgb`, so
each selected half-step is rounded unsigned-byte average `(a+b+1)>>1`. The
resulting 3x3 projected source patch is compared against the fixed 3x3 anchor
patch by the admitted G-42 metric.

## Three Concrete Same-Render Replays

One Unit-1 canonical `28mm` process captures the live index-5 projection
vector, all five image descriptors, the complete 752-float lookup, and three
winner-map values. Replaying the installed float32 formula against that single
packet produces:

| A1 reference `(u,v)` | winner | `d` mm | A5 sample | A2 sample | A3 sample | A4 sample |
|---|---:|---:|---|---|---|---|
| `(1040,780)` | `25` | `5953.966797` | `(1089.551025,796.334412)` | `(1057.396484,810.977600)` | `(1053.224609,809.952515)` | `(1042.535645,806.796021)` |
| `(520,390)` | `115` | `1303.835205` | `(617.367920,401.122803)` | `(569.687622,443.534637)` | `(528.617493,440.712952)` | `(499.513977,393.158844)` |
| `(1560,1170)` | `84` | `1783.670898` | `(1638.277222,1190.905273)` | `(1593.517822,1219.621094)` | `(1564.498901,1219.392212)` | `(1546.806396,1182.438477)` |

The probe stopped intentionally after both required packets were present; it
records `capture_complete=true`, six index-to-depth hits, `4040` filtered
mode-8 projection-return hits, and no errors. The report and replay SHA-256
digests are respectively `3d926762...bfc86` and `71cbf70b...f6310`.

An earlier independent replay used separately completed retained captures and
selected winners `25/116/85`; this same-render packet selected `25/115/84`.
That one-index variation is consistent with the admitted index-5 repeat
distribution and is not folded into the correspondence formula. The values
above are the direct same-render implementation discriminator.

## Fixed G-42 Reference

The fixed reference operand is not a generated multi-camera composite.
Existing installed/runtime proof establishes source-versus-`Images[0]`
pairing in `0x2732f0`:

- wide: A1 is fixed, A5/A2/A3/A4 are projected;
- tele: B4 is fixed, B2/B5/B1/B3 are projected.

`Images[0]` is that anchor camera's own `StereoISP::CreateStereoImage` output.
For the selected collapse2 path, its four uint8 Guidance components are:

```text
[R, 0.5*(G1+G2), B, 1]
```

with the admitted rounding/saturation and default hot-pixel stage. It is not
a running average, synthesized view, or composed color image.

## Scope and Admission

Admitted as a `CLM-STEREO-001` addendum:

- exact installed correspondence formula and multiply order;
- 2080x1560 StereoLayer coordinate domain;
- calibrated `CreateStereoImage` undistorted-domain source identity;
- A1/B4 fixed-anchor identity and four projected source order;
- exact `+0.25f`, clamp, truncation, half-phase, and `pavgb` sampling policy;
- three Unit-1 `28mm` same-render runtime/replay examples.

The installed arithmetic is focal/body independent. Existing runtime proof
shows the same mode-8 `0x2732f0` body live at Unit-1 `28/35/70/150mm`; existing
two-body composed-geometry proof verifies the public calibration-record
mechanism on Unit-1 four focal tiers plus exact-28mm Unit-2. The numeric table
above is direct same-render Unit-1 `28mm` only. No claim is made that different bodies or
firmware produce identical calibration coefficients or identical source
coordinates.

## Verification

```text
index5_plane_sweep_static=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
matrix=H=(Ksrc*Esrc)*inverse(Kref*Eref); stored=float32(transpose(H))
projection=P=H*[u*d,v*d,d,1]; sample=(Px/Pz+0.25,Py/Pz+0.25)
pixel=(1040, 780) h=25 d_mm=5953.9668 A5=(1089.551025,796.334412), A2=(1057.396484,810.977600), A3=(1053.224609,809.952515), A4=(1042.535645,806.796021)
pixel=(520, 390) h=115 d_mm=1303.83521 A5=(617.367920,401.122803), A2=(569.687622,443.534637), A3=(528.617493,440.712952), A4=(499.513977,393.158844)
pixel=(1560, 1170) h=84 d_mm=1783.6709 A5=(1638.277222,1190.905273), A2=(1593.517822,1219.621094), A3=(1564.498901,1219.392212), A4=(1546.806396,1182.438477)
index5_plane_sweep_correspondence=OK
```
