# Evidence: G-38 Undistort Envelope Formula

## Result

G-38 is formula-closed for the installed `0x145980` builder. The output is not
an opaque fitted rectangle and it is not copied from public `valid_roi`.
Starting from the admitted public Brown-Conrady polynomial and pixel scale,
the builder constructs a radial inverse correction, samples all four image
edges, takes their inner valid extrema, and converts those extrema to an
integer half-open box.

The clean-room float32 replay exactly reproduces 20 retained canonical Unit-1
boxes across `28/35/70/150mm` and five new exact-focal Unit-2 `70mm` boxes.

## Public Inputs

The already-admitted public calibration inputs are:

```text
FactoryModuleCalibration.geometry.distortion.polynomial
  .distortion_center
  .normalization
  .coeffs              # [k1,k2,p1,p2,k3]

FactoryModuleCalibration.geometry.distortion.cra.pixel_size
CameraModule.sensor_data_surface.size
```

The selected route uses `W=4160`, `H=3120`, and public CRA
`pixel_size=0.0011f` on both checked calibration signatures. The installed
`0xe7730`/stage-scale path produces the same effective pixel scale under the
observed identity stage scale. Public `Distortion.Polynomial.valid_roi` is not
consumed by this path.

## Radial Samples

For `j=0..29`, helper `0x145590` evaluates the admitted exact Brown-Conrady
mapping on the horizontal ray through public center `(cx,cy)`:

```text
rho[j] = f32(f32(j) * 0.1f)
input  = (cx + rho[j] / pixel_size, cy)
mapped = BrownConrady(input)

distorted_radius[j] = f32((mapped.x - cx) * pixel_size)
x[j] = f32(distorted_radius[j] / pixel_size)
d[j] = f32(rho[j] / pixel_size - x[j])
```

Thus `x[]` is distorted radius in pixels and `d[]` is the radial pixel delta
needed to recover the undistorted radius.

## Cubic Radius Evaluator

Helper `0x146380` stores both 30-float vectors and computes:

```text
first = x[0]
last  = x[29]
step  = f32((last - first) / 29.0f)
```

For a queried distorted pixel radius `q`:

```text
position = f32((q - first) / step)
i = clamp(trunc_toward_zero(position), 1, 27)
t = f32(position - f32(i))
t2 = f32(t * t)
s = f32(1.0f - f32(0.5f * t))

wm1 = f32(f32(f32(t2 - t) * s) / 3.0f)
w2  = f32(f32(f32(t2 - 1.0f) * t) / 6.0f)

c = f32(f32(f32(1.0f - t2) * d[i])
        + f32(f32(t2 + t) * d[i+1]))
c = f32(c * s)
c = f32(c + f32(wm1 * d[i-1]))
c = f32(c + f32(w2 * d[i+2]))

target_radius = f32(q + c)
```

This is the same four-point cubic Lagrange family used by the admitted
4096-entry distortion table, but here the independent axis is distorted pixel
radius and the returned value is the corresponding undistorted pixel radius.
The endpoint-index clamp permits cubic extrapolation through the first/last
four samples; it does not clamp the radius itself.

## Edge Sweeps

All operations below round as scalar float32 after every installed arithmetic
instruction.

### Left and right edges

The builder evaluates 91 vertical sample positions:

```text
y_step = f32(f32(H) * f32(1.0/90.0))
y_j = f32(f32(j) * y_step), j=0..90
```

For each `y_j`, it evaluates radii from the public center to `x=0` and
`x=W-1`, maps each through the cubic radius evaluator, and reconstructs the
corresponding undistorted edge coordinates:

```text
left_x  = cx - target_radius(left_r)  * cx / left_r
right_x = cx + target_radius(right_r) * (W-1-cx) / right_r

left  = max(0, every left_x)
right = min(W-1, every right_x)
```

### Top and bottom edges

The builder evaluates 121 horizontal sample positions:

```text
x_step = f32(f32(W) * f32(1.0/120.0))
x_i = f32(f32(i) * x_step), i=0..120
```

It performs the symmetric calculation at `y=0` and `y=H-1`:

```text
top_y    = cy - target_radius(top_r)    * cy / top_r
bottom_y = cy + target_radius(bottom_r) * (H-1-cy) / bottom_r

top    = max(0, every top_y)
bottom = min(H-1, every bottom_y)
```

The loops intentionally include sample coordinates `H` and `W` at their last
steps while evaluating edge radii against `W-1` and `H-1`.

## Integer Box

The final four signed-int32 words use SSE truncation toward zero:

```text
x0 = trunc(left)
y0 = trunc(top)
x1 = x0 + trunc(right  + 1.0f - left)
y1 = y0 + trunc(bottom + 1.0f - top)

box = [x0, y0, x1, y1]
```

The existing downstream `0x260e40` admission then computes:

```text
origin = [float32(x0), float32(y0)]
uniform_scale = max(float32(W)/float32(x1-x0),
                    float32(H)/float32(y1-y0))
```

and copies the result into the later keyed calibration payload.

## Static Proof

Installed `libcp.dylib` SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

Pinned windows:

| Window | Bytes | SHA-256 | Role |
|---|---:|---|---|
| `0x145980..0x14624d` | 2253 | `1ff1fb1ee335178428a8f412e490f40535bf35361be15b9f6010f3b85123850e` | complete normal builder |
| `0x145a1f..0x146141` | 1826 | `93a6d49fc8676dbb1949e762aaf8ae1d72af94fc8fc559323611108dac516b32` | vector scale, sweeps, extrema, box |
| `0x146380..0x146501` | 385 | `24f543dd29eecdfdcdb38a87b12870febfa1a0d2936ce2464e2ab5c82711a19e` | vector pack and step |

Capstone assertions pin vector scaling/subtraction, cubic index conversion and
clamps, all extrema operations, loop counts `91`/`121`, and final SSE
truncation. Constants are exact installed float32 `1/90`, float32 `1/120`,
double `1/3`, and double `1/6` at their mixed-precision interpolation sites.

## Runtime Replay

The verifier first rechecks the prior public-calibration distortion tables:

| Case | Camera | Table SHA-256 prefix |
|---|---|---|
| Unit-1 exact `28mm` | A1 / key `0` | `36590f6afdf1d3be` |
| Unit-2 exact `70mm` | B4 / key `8` | `cd0a159d27ade82a` |

Both complete 4096-float tables remain byte-exact public-calibration replays.

Box replay coverage:

| Scope | Keys | Exact boxes |
|---|---|---:|
| Unit-1 `28mm` | A1-A5 / `0..4` | 5/5 |
| Unit-1 `35mm` | A1-A5 / `0..4` | 5/5 |
| Unit-1 `70mm` | B1-B5 / `5..9` | 5/5 |
| Unit-1 `150mm` | B1-B5 / `5..9` | 5/5 |
| Unit-2 `70mm` | B1-B5 / `5..9` | 5/5 |

The Unit-2 run exited `0`, exercised all five box/downstream-copy sites per
key, and used calibration digest `223961c6...`; Unit-1 uses `722a6e72...`.
This is a real second-body calibration discriminator. Capture date and possible
firmware differences are not assigned as causes.

The verifier also rechecks all 20 retained RGBA16F undistorted source planes
across the canonical focal quartet and the byte-identical repeated `28mm`
set. Those are downstream validation artifacts, not a claim that Unit-2 plane
pixels equal Unit-1.

## Scope And Admission

- Formula: installed static proof, body/focal independent for this binary.
- Public table replay: Unit-1 A1 and Unit-2 B4, exact-focal wide/tele.
- Box replay: Unit-1 four focal tiers plus Unit-2 exact `70mm`.
- Downstream reference planes: 20 Unit-1 planes across four focal tiers.
- This closes G-38's envelope, integer-box, and already-joined scale/origin
  arithmetic.
- It does not assign a protobuf field name to the derived envelope, attribute
  differences to firmware/body, or close unrelated warp records.

Admit as a `CLM-WARP-003` addendum. Claim status remains unchanged.

## Reproduction

```bash
bash tools/lldb_probes/g38_undistort_envelope/run_unit2_70mm_box.sh
python3 tools/lldb_probes/g38_undistort_envelope/verify_g38_undistort_envelope.py
```

Expected terminal marker:

```text
g38_undistort_envelope=OK
```
