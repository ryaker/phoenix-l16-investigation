# CCM Scene Chromaticity Public Origin And Exact Conversion

**Claim target:** `CLM-CCM-002`  
**Installed binary:** `libcp.dylib` SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`  
**Method:** installed-body extraction, runtime-initialized constant dump through a
direct x86_64 harness, public protobuf replay, and retained four-focal runtime
packet equality

## Question

Close the earlier phrase "live scene chromaticity" by proving its public LRI
inputs and exact installed conversion to the `(x,y)` consumed by
`0x350bc0`.

## Reusable Artifacts

- `tools/lldb_probes/ccm_chromaticity_origin/dump_ccm_chromaticity.c`
- `tools/lldb_probes/ccm_chromaticity_origin/run_dump.sh`
- `tools/lldb_probes/ccm_chromaticity_origin/verify_ccm_chromaticity_origin.py`
- ignored output under `runs/ccm_chromaticity_origin/`

Reproduce without LLDB:

```bash
tools/lldb_probes/ccm_chromaticity_origin/run_dump.sh
```

## Public Source Chain

For every structurally complete local LRI, `ViewPreferences.awb_mode` is
absent and therefore defaults to public `AWB_MODE_AUTO`. The constructor at
`0x1bd270` reaches the already-proven public accessor `0x13f170` and obtains:

```text
LightHeader.view_preferences.awb_gains.r
LightHeader.view_preferences.awb_gains.g_r
LightHeader.view_preferences.awb_gains.b
```

It constructs the camera-neutral RGB triplet in float32:

```text
q = (1/r, 1/g_r, 1/b)
n = q / max(q.r, q.g, q.b)
```

The common scale does not change chromaticity. The triplet is stored at
per-camera helper `+0x74/+0x78/+0x7c`.

The same constructor obtains the selected camera's public A and D65
`ColorCalibration.color_matrix` records, calls `0x350570`, and stores its
result at helper `+0x80/+0x84`. It then calls `0xab2e0` and stores public
renderer-property values:

```text
helper+0x88 = auto_white_balance.neutral_temp
helper+0x8c = auto_white_balance.neutral_tint
```

`0x1bdfb0` publishes those exact floats into the property tree. The ISP object
constructor's mode-`3` branch reads `neutral_temp` and `neutral_tint` into
object `+0x15d0/+0x15d4`. Finally, installed callback
`Pipeline::setWhiteBalance(AWB)::$_23` at `0x342a80` performs:

```text
neutral_temp, neutral_tint
  -> 0xab130 / 0xab160
  -> reconstructed (x,y)
  -> 0x350bc0 A/D65 CCM interpolation
```

The direct harness observes the initialized property names
`auto_white_balance`, `type`, `neutral_color`, `neutral_temp`, and
`neutral_tint`; these are installed public renderer configuration names, not
invented clean-room labels.

## Neutral RGB To Chromaticity Solver

SHA-pinned `0x350570` begins at internal illuminant-`5` white point:

```text
xy_0 = float32(0x3eb0fb8d, 0x3eb78cd0)
     = (0.3456691801548004, 0.35849618911743164)
```

For at most 30 iterations, all arithmetic is float32:

```text
T_i = robertson_xy_to_cct(xy_i)
M_i = mired_interpolate(public_D65_color_matrix,
                        public_A_color_matrix, T_i)
I_i = inverse_3x3(M_i)

z0 = I_i[0]*n.r + I_i[1]*n.g + I_i[2]*n.b
z1 = I_i[3]*n.r + I_i[4]*n.g + I_i[5]*n.b
z2 = I_i[6]*n.r + I_i[7]*n.g + I_i[8]*n.b
s  = z0 + z1 + z2
xy_next = (z0/s, z1/s)
```

The interpolated matrix determinant must be greater than float32 `1e-6` or
the installed body throws `singular matrix found!`. Iteration stops when:

```text
abs(x_next - x_i) + abs(y_next - y_i) < float32(1e-6)
```

If iteration 29 is reached, the returned value is
`0.5f * (xy_next + xy_i)`. Otherwise `xy_next` is returned directly.

That solver result is intentionally round-tripped through
`xy -> (neutral_temp,neutral_tint) -> xy` before live CCM use. The replay must
therefore compare the reconstructed xy, not the pre-round-trip solver xy.

## Robertson Table And Formulas

The installed 31-row table is runtime-initialized at `0x66d410`. Each row is
four float32 words `(mired,u,v,slope)`. The exact 496-byte table SHA-256 is:

```text
a82b3a43e3e19947839db421b880770a0590ee4eefa088ff7a3914a5ef081ada
```

Exact words, listed as float32 bit patterns:

```text
row  mired       u            v            slope
 0   00000000    3e3861a6     3e86ec18     be794079
 1   41200000    3e38feef     3e8822bc     be8273d6
 2   41a00000    3e39ae92     3e897397     be899ae9
 3   41f00000    3e3a732e     3e8ad96a     be921ea3
 4   42200000    3e3b5200     3e8c52e7     be9c01a3
 5   42480000    3e3c4b0a     3e8ddebe     bea74bc7
 6   42700000    3e3d60e9     3e8f77af     beb3ffac
 7   428c0000    3e3e939f     3e911c6d     bec21ff3
 8   42a00000    3e3fe5c9     3e92c7b9     bed1b08a
 9   42b40000    3e4154ca     3e9476f3     bee2b40f
10   42c80000    3e42e33f     3e96262d     bef52fc2
11   42fa0000    3e474a77     3e9a5269     bf150093
12   43160000    3e4c692f     3e9e50c6     bf3467e0
13   432f0000    3e522d0e     3ea2085b     bf5958b8
14   43480000    3e587e7c     3ea56ffc     bf825461
15   43610000    3e5f4dbe     3ea87e7c     bf9bc01a
16   437a0000    3e66833c     3eab352b     bfb9c0ec
17   43898000    3e6e0c9e     3ead96a7     bfdd6a16
18   43960000    3e75dcc6     3eafa82f     c00413a9
19   43a28000    3e7ddebe     3eb16f00     c01df55a
20   43af0000    3e8306a3     3eb2f2fa     c03db3d0
21   43bb8000    3e872b02     3eb43958     c06535a8
22   43c80000    3e8b5b2d     3eb548aa     c08ba027
23   43d48000    3e8f8f47     3eb6277c     c0ac09d5
24   43e10000    3e93c750     3eb6db0e     c0d73d08
25   43ed8000    3e97fcb9     3eb769ec     c109872b
26   43fa0000    3e9c2f83     3eb7d806     c1352f1b
27   44034000    3ea05bc0     3eb827fa     c17a0c4a
28   44098000    3ea4801f     3eb86057     c1ba999a
29   440fc000    3ea89b52     3eb883ba     c223147b
30   44160000    3eacaab9     3eb894c4     c2e8e666
```

For xy input, `0xab2e0` first converts to CIE 1960 UCS coordinates:

```text
d = 1.5f - x + 6.0f*y
u = 2.0f*x / d
v = 3.0f*y / d
```

For row `i`, let:

```text
normal_i = normalize((slope_i, 1))
distance_i = normal_i.y*(v-v_i) - normal_i.x*(u-u_i)
```

The body scans for the first row whose signed distance is non-positive and
interpolates it with the preceding positive row. With
`w = -distance_i/(distance_(i-1)-distance_i)`, it uses:

```text
locus  = row_i.uv + w*(row_(i-1).uv - row_i.uv)
normal = normalize(normal_i + w*(normal_(i-1) - normal_i))
mired  = row_i.mired + w*(row_(i-1).mired - row_i.mired)
CCT    = 1000000.0f / mired
tint   = -3000.0f * (normal.y*(u-locus.u) + normal.x*(v-locus.v))
```

`0xab160` performs the inverse table interpolation with
`mired=1000000.0f/temperature` and `offset=-tint/3000.0f`, then converts back:

```text
u = locus.u + offset*normal.y
v = locus.v + offset*normal.x
d = u - 4.0f*v + 2.0f
x = 1.5f*u / d
y = v / d
```

The cross-component normal convention above is the installed convention and
must not be replaced by a McCamy approximation or an inferred reciprocal-AWB
`rg/bg` proxy.

## Exact Four-Focal Public Replay

The verifier discovers the live anchor matrix pair by exact public bytes,
parses the same LRI's public AWB gains, invokes the installed solver using only
those public values, performs the stored temp/tint round trip, and requires all
eight reconstructed xy words to equal the retained runtime packet exactly:

| Focal | Anchor camera | Reconstructed live xy | Final CCT | Tint |
|---|---|---|---:|---:|
| `28mm` | A1 / key `0` | `(0.3464407921, 0.3529967964)` | `4953.663574 K` | `0.547458172` |
| `35mm` | A1 / key `0` | `(0.3474981785, 0.3551827073)` | `4922.083496 K` | `2.62130618` |
| `70mm` | B4 / key `8` | `(0.3420673311, 0.3483845592)` | `5107.863770 K` | `-1.00971413` |
| `150mm` | B4 / key `8` | `(0.3483559787, 0.3504959941)` | `4870.953125 K` | `-5.40934229` |

The earlier tele probes captured entry xy but intentionally did not stop again
for CCT. This direct installed-function replay supplies the exact tele CCT/tint
values and independently reproduces the retained entry words.

## Admission Boundary

Admit for canonical profile-3 bridge HDR:

- AUTO scene chromaticity originates from the tier-anchor camera's public
  `ViewPreferences.awb_gains` plus its public A/D65 color matrices;
- the exact normalized-neutral, fixed-point matrix solve, Robertson table,
  temp/tint property custody, and reconstructed xy are closed;
- all four focal tiers replay to exact retained live xy words.

Public AWB carrier parsing already covers both calibration bodies, but this
exact CCM xy replay uses the canonical Unit-1 focal quartet. The installed
formula has no body or firmware selector. This evidence does not claim two-body
pixel equality, does not attribute any future difference to firmware, and does
not generalize to synthetically authored non-AUTO preference modes absent from
the complete local corpus.
