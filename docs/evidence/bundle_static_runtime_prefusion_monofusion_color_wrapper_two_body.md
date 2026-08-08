# Static + Runtime Evidence: MonoFusion Response-Basis Color Wrapper

## Claim

Installed wrapper `0x1b3530` does not apply an unnamed fitted RGB ratio after
mode-0 MonoFusion. It preserves the two opponent-color coordinates of the A1
target, replaces only the response/luma coordinate with the fused scalar from
`0x1b37a0`, and transforms back to RGB through the exact inverse basis.

The two object coefficient packs are not public protobuf matrix fields:

- object `+0x114..+0x134` is a deterministic response/opponent basis derived
  from the installed response selected by public
  `LightHeader.sensor_data.type = SENSOR_AR1335 (2)`;
- object `+0x138..+0x158` is its exact float32 inverse, produced by installed
  helper `0x9d7e0`;
- object `+0xf0[1]` and `+0xf0[2]` are publicly named
  `SensorCharacterization.black_level` and `white_level`.

This closes the former public-meaning/value gap for the immediate post-reducer
wrapper. It does not independently replay the complete full-frame scalar image
emitted by `0x1b37a0` or prove other installed builds.

## Scope

Direct numerical runtime proof uses exact-`28mm` LRIs from both physical
calibration signatures:

- Unit-1: `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri`
- Unit-2: `/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri`

Prior admitted route proof supplies merge-critical scope: canonical profile-3
`28mm` and `35mm` use the same mode-0 MonoFusion wrapper; canonical `70mm` and
`150mm` construct no MonoFusion and use direct B4. No claim of equal scene
pixels, firmware identity, or a separate numerical `35mm` replay is made.

## Reusable Artifacts

- LLDB callback:
  [color_wrapper_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_monofusion_color_wrapper/color_wrapper_probe.py)
- Two-body runner:
  [run_two_body.sh](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_monofusion_color_wrapper/run_two_body.sh)
- Static/runtime verifier and clean-room replayer:
  [verify_color_wrapper.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_monofusion_color_wrapper/verify_color_wrapper.py)
- Rerunnable reports:
  `runs/prefusion_monofusion_color_wrapper/{unit1_28mm,unit2_28mm}.json`

The reports are ignored run products; this document and the verifier contain
the durable checked facts and reconstruction.

## Installed Static Proof

The verifier first checks installed `libcp.dylib` SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`
and pins these exact windows:

| Range | Role | SHA-256 |
|---|---|---|
| `0x1b1360..0x1b1528` | constructor and coefficient preparation | `607207b5e26b0c3f3f6f8bb7ce86db5bbb2b2f2cc4883f867421fef46ebb2360` |
| `0x1b3530..0x1b375c` | complete response-coordinate replacement wrapper | `61dfd8999ea456a4e92e97635de2357d729f5e7c40177577822c242a13bbef13` |
| `0x09d7e0..0x09d96a` | exact float32 3x3 inverse | `09dc1b8297117595002c0e07aa93915064b049d013e82e1dd5d7f74843acab2a` |
| `0x0ab830..0x0ab93b` | response/opponent basis builder | `193603b136bb189fef0a7aa96cd9e95fbc5bdbb032555ae2fe621663d9ee047d` |

For installed response `w=(a,b,c)`, define, with every operation rounded to
binary32 in instruction order:

```text
d = sqrt(2*b*b + (a+c)*(a+c))
u = -b*b - (a+c)*c
v = (c-a)*(-b)
t = (a+c)*a + b*b
e = sqrt(u*u + v*v + t*t)

M = [ a,    b,       c
     -b/d, (a+c)/d, -b/d
      u/e,  v/e,     t/e ]

N = inverse3_float32(M)
```

`0xab830` initially normalizes the first row as well, but constructor stores at
`0x1b14cb..0x1b14e7` deliberately restore the unnormalized response `a,b,c`.
The resulting exact object words on both bodies are:

```text
M = [ 0.2155500054359436,  0.43230700492858887,  0.35214298963546753,
     -0.5181682109832764,  0.6804434657096863,  -0.5181682109832764,
     -0.7755553722381592, -0.11839920282363892,  0.6200770139694214 ]

N = [ 0.6031803488731384, -0.5181682705879211,  -0.7755553722381592,
      1.2097381353378296,  0.680443525314331,   -0.11839919537305832,
      0.9854127168655396, -0.5181682705879211,   0.6200770139694214 ]
```

The clean-room cofactor/inverse formula reproduces all nine `N` words exactly.

## Exact Pixel Formula

Let `p=(r,g,b,a)` be the A1 target RGBA emitted by the internal worker and `m`
its fused scalar. Let public `B=black_level`, `W=white_level`. The installed
SSE grouping is:

```text
q0 = p.b*M02 + (p.g*M01 + p.r*M00)
q1 = p.b*M12 + (p.g*M11 + p.r*M10)
q2 = p.b*M22 + (p.g*M21 + p.r*M20)

s = (m-B) * float32(1/(W-B))

out.r = (q2*N02 + q1*N01) + s*N00
out.g = (q2*N12 + q1*N11) + s*N10
out.b = (q2*N22 + q1*N21) + s*N20
out.a = p.a
```

Operationally, `q0` is replaced by normalized fused scalar `s`; `q1/q2` and
alpha are retained.

## Runtime Replay

At the first live wrapper tile, LLDB captures the object, pointed
normalization record, both input descriptors, ROI, all 18 matrix words, three
pre-wrapper RGBA pixels, their three fused scalars, and the same pixels after
the wrapper. Both bodies expose the exact public/installed record:

```text
sensor_type = 2 (SENSOR_AR1335)
black_level = 42.0
white_level = 1023.0
cliff_slope = 2.0
span = 981.0
response = [0.2155500054359436,
            0.43230700492858887,
            0.35214298963546753, 0.0]
```

The verifier independently reconstructs both matrices and every output lane:

```text
unit1_28mm=OK matrix_words=18/18 pixel_words=12/12
unit2_28mm=OK matrix_words=18/18 pixel_words=12/12
monofusion_color_wrapper=OK
scope=exact-28mm Unit-1+Unit-2; wide-only wrapper; tele route absent
```

The two scenes have distinct input/fused/output values, so equality is not an
identity-only artifact. Across both bodies, all `36` checked matrix words and
all `24` checked output words match bit-for-bit.

## Admission Consequence

For canonical profile-3 wide rendering, a clean-room implementation must not
re-inject MonoFusion by a scalar RGB ratio. It must construct `M`, compute its
exact float32 inverse `N`, replace the response coordinate with
`(fused_scalar-black)/(white-black)`, preserve the two opponent coordinates
and alpha, and transform back. At canonical tele, this wrapper is absent.

