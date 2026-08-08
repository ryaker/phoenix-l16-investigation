# Exact Public Distortion Model And 4096-Entry Table

**Date:** 2026-07-03  
**Status:** Admitted evidence for `CLM-WARP-004`  
**Scope:** SHA-pinned installed body; public calibration checked on exact-focal
`28/35/70/150mm` representatives from both calibration bodies; complete
runtime table replay on Unit-1 `28mm` A1 and Unit-2 `70mm` B4

## Result

The live projection path uses the public records:

```text
FactoryModuleCalibration.geometry.distortion.polynomial
  .distortion_center
  .normalization
  .coeffs
  .fit_cost

FactoryModuleCalibration.geometry.distortion.cra.pixel_size
```

For the five public polynomial coefficients, the installed conversion order
is exactly:

```text
[k1, k2, p1, p2, k3]
```

With pixel coordinate `(u,v)`, public center `(cx,cy)`, and public
normalization `(nx,ny)`:

```text
x = (u-cx)/nx
y = (v-cy)/ny
r2 = x*x + y*y
radial = 1 + k1*r2 + k2*r2^2 + k3*r2^3

xd = x*radial + 2*p1*x*y + p2*(3*x*x + y*y)
yd = y*radial + p1*(x*x + 3*y*y) + 2*p2*x*y

ud = nx*xd + cx
vd = ny*yd + cy
```

This is the five-coefficient Brown-Conrady model. The names are used here for
the proved arithmetic roles, not inferred from coefficient magnitude.

All 16 records in every exact-focal representative from both bodies have five
coefficients and `p1=p2=0`. The installed body nevertheless implements the
nonzero tangential terms shown above.

## Public Units

`distortion_center` and `normalization` are used directly in sensor-pixel
coordinates. `k1,k2,k3,p1,p2` operate on normalized coordinates and are
dimensionless. `CRA.pixel_size` converts pixel radius to the shared physical
length unit used by `CRA.sensor_distance` and `CRA.exit_pupil_distance`.
The public value is float32 `0.0010999999940395355` for every camera in both
checked calibration bodies; the associated distances are physically
millimeter-scale, so the operational conversion is `0.0011 mm/pixel`.

The implementation requires the stored float32 value and operation order; it
does not need to infer this value from camera class.

## Thirty Correction Samples

`libcp+0x145590` builds 30 float32 correction samples. For
`j in [0,29]`:

```text
rho[j] = float32(j) * float32(0.1)
u[j] = cx + rho[j] / pixel_size
v[j] = cy

delta[j] =
  pixel_size * (BrownConrady(u[j],v[j]).x - cx) - rho[j]
```

The sample ray is the positive normalized x axis. The vector is a correction,
not an absolute distorted radius. This explains the later `1 + correction/r`
table form.

The verifier executes every `mulss`, `addss`, `subss`, and `divss` with
float32 rounding. All 30 generated radii and corrections match both runtime
captures byte for byte.

## 4096-Entry Table

`libcp+0x146380` prepares a uniformly spaced interpolator over the 30 sample
pairs. `libcp+0x144d20..0x144ddd` fills the table:

```text
table[0] = 1

for i = 1..4095:
    q = min(float32(i) * pixel_size, rho[29])
    z = (q-rho[0]) / ((rho[29]-rho[0])/29)
    n = clamp(trunc(z), 1, 27)
    f = z-n
```

`delta(q)` is the four-point cubic Lagrange interpolant through sample indices
`n-1,n,n+1,n+2`:

```text
w[-1] = -f*(f-1)*(f-2)/6
w[ 0] =  (f+1)*(f-1)*(f-2)/2
w[ 1] = -(f+1)*f*(f-2)/2
w[ 2] =  (f+1)*f*(f-1)/6

delta(q) = sum(w[k] * delta[n+k], k=-1..2)
table[i] = 1 + delta(q)/q
```

The verifier uses the instruction order rather than an algebraically
reassociated polynomial. Public records reproduce the complete runtime table:

| Runtime discriminator | Key | Calibration SHA-256 prefix | Table SHA-256 |
|---|---:|---|---|
| Unit-1 `28mm` | A1 / `0` | `722a6e721636c9c4` | `36590f6afdf1d3bea47197a1466ce707c5e4b5ce8ef53fa072afdad879bb0ab8` |
| Unit-2 `70mm` | B4 / `8` | `223961c6bce6153e` | `cd0a159d27ade82a9ceb9f794e0ef81f9a69321d55c08606042753230f77c561` |

These are different public calibrations and different wide/tele routing
classes. The differing table hashes are expected and independently replayed.

## Consumer

The already admitted projection consumer at `libcp+0x3e42e0` first applies its
homogeneous 3x3 row pack, then:

```text
dx = projected_x - center_x
dy = projected_y - center_y
radius_index = min(
  trunc(sqrt((scale_x*dx)^2 + (scale_y*dy)^2)),
  4095
)
k = table[radius_index]
out = center + k * (dx,dy)
```

There is no table interpolation at consumption time. Fractional behavior is
precomputed by the 4096-entry generator.

## `valid_roi` Exclusion

The public schema contains `Distortion.Polynomial.valid_roi`, but the
installed conversion window `0x131b62..0x131d96` copies only center,
normalization, coefficients, and optional `fit_cost` into the runtime record.
It does not read the generated-message `valid_roi` member or retain it in the
record consumed by `0x145590`.

The table builder and `0x3e42e0` consumer receive only the converted record and
therefore do not use `valid_roi`. This is a path-scoped exclusion; it does not
claim that no other Lumen feature can inspect that public field.

## Coverage

Deterministic public parsing covers:

- Unit-1 `28/35/70/150mm`;
- Unit-2 exact-focal `28/35/70/150mm`;
- all 16 camera calibration records in each file.

Each body has one stable geometry payload hash across its four checked focal
tiers, while the two bodies have different hashes. This establishes both
four-zoom carrier coverage and a real body-calibration discriminator without
duplicating the static arithmetic probe at every focal.

Runtime joins are Unit-1 wide A1 and Unit-2 tele B4. The table/model bodies
have no camera/focal branch once the public record is supplied. Existing
four-focal projection-consumer evidence proves the same consumer family live
on the canonical Unit-1 quartet.

No conclusion attributes the two calibration payloads solely to firmware or
body causation; the proof requires only their distinct stored values.

## Reproduction

Reusable harness:

- `tools/lldb_probes/distortion_table/distortion_table_probe.py`
- `tools/lldb_probes/distortion_table/unit1_28mm.lldb`
- `tools/lldb_probes/distortion_table/unit2_70mm.lldb`
- `tools/lldb_probes/distortion_table/run_two_body.sh`
- `tools/lldb_probes/distortion_table/verify_distortion_table.py`

Raw rerunnable captures:

```text
runs/distortion_table/
```

Commands:

```bash
bash tools/lldb_probes/distortion_table/run_two_body.sh
python3 tools/lldb_probes/distortion_table/verify_distortion_table.py
```

Expected verifier status: `PASS`.

## Admission

This closes the public coefficient names/order, normalization, units needed by
the computation, exact Brown-Conrady arithmetic, public pixel-size origin,
30-sample construction, cubic Lagrange interpolation, 4096-entry table,
consumer indexing, and path-scoped `valid_roi` exclusion.

It does not close unrelated pair-grid composition, stereo depth policy,
sensor corrections, or output encoding.
