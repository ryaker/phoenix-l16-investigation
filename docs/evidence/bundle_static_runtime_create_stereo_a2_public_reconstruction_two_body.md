# Static/Runtime Evidence: CreateStereoImage A2 Public Reconstruction

**Date:** 2026-07-16  
**Status:** VERIFIED; `CLM-STEREO-001` / `CLM-CORRECTION-001` addendum  
**Bearing:** public LRI RAW10 to wide-tier A2 `CreateStereoImage` float plane

## Result

The complete full-resolution A2/key-`1` mono plane immediately before
scalar-to-vec4 replication is reproducible bit for bit from public LRI data.
The clean-room replay independently decodes:

- `CameraModule.sensor_data_surface` RAW10 bytes, dimensions, and stride;
- public `SensorCharacterization.black_level` and `white_level`;
- the A2 runtime calibration-vector slot's public
  `VignettingCharacterization.vignetting[]` profile;
- public A1/A2 `sensor_exposure` and `sensor_analog_gain`; and
- the already-proven A2 `sensor_bayer_red_override=(-1,-1)` policy that
  bypasses `relative_brightness` multiplication.

It exactly reproduces all `12,979,200` float32 pixels in each of canonical
Unit-1 `28mm`, the independent builder input `L16_06689`, and exact-focal
Unit-2 `28mm`: `38,937,600 / 38,937,600` pixels total.

## Artifacts

- Public full-plane verifier:
  `tools/lldb_probes/index5_guidance_channel_origin/verify_create_stereo_mono_public_reconstruction.py`
- Scalar-to-vec4 capture and verifier:
  `tools/lldb_probes/index5_guidance_channel_origin/create_stereo_mono_replication_probe.py`
  and `verify_create_stereo_mono_replication.py`
- Exposure/relative-brightness capture and verifier:
  `tools/lldb_probes/index5_guidance_channel_origin/create_stereo_exposure_scale_probe.py`
  and `verify_create_stereo_exposure_scale.py`
- Rerunnable ignored captures:
  `runs/index5_guidance_channel_origin/create_stereo_mono_replication_{unit1_28mm,new_06689,unit2_28mm}/`
  and matching `create_stereo_exposure_*` directories

All runtime artifacts are tied to their source LRI and SHA-256 checked before
use. The replay reads RAW and calibration fields afresh from that same LRI;
captured image values are not used as formula inputs.

## Installed Custody

The installed `libcp.dylib` is SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`.
The verifier pins:

| Body | Range | SHA-256 |
|---|---|---|
| scalar vignetting row worker | `0x108370..0x1085c5` | `57de18e3f50fd16f3f700643e618de41c3d6ee305fc9f757b48f1e8942524d50` |
| mono SoftISP wrapper | `0x31b470..0x31b525` | `3efdd072adf272c260620ec498741a139fb642b5b67ee0e2b8eb769b9cea7ac0` |
| selected sentinel-calibration branch | `0x3403f0..0x3408dc` | `9c98cef13b78f5ababf576963f82e611d036cb4fdd5e0d4c6055591ceecee8c2` |

At `0x31b4f6`, the A2 sentinel path directly calls `0x3403f0`. The pinned
vignetting worker supplies the exact float32 row interpolation, double
horizontal evaluation, float32 conversion, and final scalar multiply.

## Exact Formula

Let public RAW10 sample `r`, black level `B`, and white level `W`. Every
shown `f32` operation rounds to IEEE binary32:

```text
inv_range = f32(1.0 / f32(W - B))
n         = f32(f32(r - B) * inv_range)
```

The multiplication by a pre-rounded reciprocal is required. Replacing it
with per-pixel division differs by up to three ULP after the later stages on
the canonical plane.

For the public `17 x 13` vignetting grid `G`, the image-space node spacing is
exactly:

```text
dx = f32(4160 / (17 - 1)) = 260
dy = f32(3120 / (13 - 1)) = 260
```

There is no `+0.5`, `-0.5`, or other pixel-center offset. For pixel `(x,y)`,
let `gx=floor(x/dx)`, `gy=floor(y/dy)`, `lx=x-gx*dx`, and `ly=y-gy*dy`.
The installed worker performs vertical interpolation first:

```text
ty    = f32(f32(ly) * f32(1 / dy))
left  = f32(f32(ty * f32(G[gy+1,gx]   - G[gy,gx]))   + G[gy,gx])
right = f32(f32(ty * f32(G[gy+1,gx+1] - G[gy,gx+1])) + G[gy,gx+1])
slope = f32(f32(right - left) * f32(1 / dx))
V     = f32(double(lx) * double(slope) + double(left))
```

The correction and A1-relative exposure normalization are separate float32
multiplies:

```text
vignetted = f32(n * V)

A1_energy = f32(f32(A1.sensor_exposure) * A1.sensor_analog_gain)
A2_energy = f32(f32(A2.sensor_exposure) * A2.sensor_analog_gain)
scale     = f32(A1_energy / A2_energy)

mono = f32(vignetted * scale)
```

A2's public `VignettingCharacterization.relative_brightness` exists, but is
not an operand in this selected branch. Its proven
`sensor_bayer_red_override=(-1,-1)` copy yields the sentinel-invalid gate
pair, bypassing the optional relative-brightness ratio. Color-camera
CreateStereoImage branches do apply their separately proven
`source.relative_brightness / target.relative_brightness` factor.

There is no clamp after subtracting black. This is discriminating: the
builder input and Unit-2 contain A2 samples below `B=42`, and their rebuilt
planes preserve negative float values exactly.

The next installed conversion expands every scalar exactly to
`[mono,mono,mono,1]`. Separate complete captures verify all
`155,750,400` resulting float32 words across the same three LRIs.

## Runtime Results

| Input | Physical calibration | A2 RAW SHA-256 | public calibration slot / record ID | vignetting-grid SHA-256 | scale | output SHA-256 | exact pixels |
|---|---|---|---|---|---:|---|---:|
| canonical `L16_02130` | Unit-1 `722a6e72...` | `dcc6d8e66da6d85d0c2c65b18f5111d88ff3644c332134ee1418ca3c9403f044` | `1 / 0` | `84890ecf9040518479ad9d5445cdd70215585dccca162ff0bed6c095a56a8e38` | `0.51181560754776` | `0453f21a789a65be6247d516f751e7f7cde7d4ea07c78dbf4d7fc2312264d89f` | `12,979,200` |
| builder `L16_06689` | Unit-1 `722a6e72...` | `d6d4ed81e7d66886408af6e53df9364137aaf878e18de99abdd514249dc08356` | `1 / 0` | `84890ecf9040518479ad9d5445cdd70215585dccca162ff0bed6c095a56a8e38` | `0.5005342960357666` | `c33c07293c3d3516b877b66051ef03846275c3e64211231f263b731d1a18dc61` | `12,979,200` |
| exact-focal Unit-2 `L16_02130` | Unit-2 `223961c6...` | `d6a10dff2b6dfe4bdcd2ad3c58a87b4a18eb81178e9761fe390e5bf4493fd410` | `1 / 12` | `c5ed61d7a9291356d1c651c96c5e58896eba39526a280fc0cc803fe99c10f9b2` | `0.5000497102737427` | `d67927547d157ae326a9fefb40a0db09f04b062c48e216a935dc377a8d5f49da` | `12,979,200` |

The builder row is a distinct scene/current input, while Unit-2 changes the
physical calibration, public calibration record ID, grid bytes, RAW bytes,
and exposure scale. The repeated Unit-1 grid is correctly attributed to the
shared physical calibration, not to capture firmware.

The selected calibration is the public `module_calibration` vector element
at runtime key/index `1`; its own public `camera_id` is not the vector index.
That ordering rule was independently established by complete runtime grid
captures and is reinforced here because only the indexed profile reproduces
the full plane on both bodies.

## Scope and Admission

Admitted as an exact wide-tier A2/key-`1` CreateStereoImage reconstruction
for canonical profile 3. Runtime arithmetic covers two Unit-1 scenes and an
exact-focal Unit-2 `28mm` scene. Existing Unit-1 `28mm`/`35mm` producer
custody establishes the shared wide path at both canonical wide focal tiers;
tele uses the already-proven B4 color-anchor path and does not invoke this A2
mono branch.

This closes A2 public RAW-to-normalized-float construction and removes it as
a possible explanation for the `L16_02130` photometric-cost/depth mismatch.
It does not yet claim full public-RAW reconstruction of A1/A3/A4/A5 color
Guidance, nor does it by itself close G-42 cost discrimination on low-parallax
scenes.
