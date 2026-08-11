# ColorFusion Target Noise: Public Origin and Two-Body Bit Replay

**Claim target:** `CLM-DENOISE-002`  
**Installed binary:** `libcp.dylib` SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`  
**Runtime inputs:** Unit-1 `28mm` `L16_02130` SHA-256
`2ac51af5c219639638ba34bb98975b62ee922331214043a938a7c37052700ff5`;
exact-focal Unit-2 `70mm` `L16_02894` SHA-256
`780157dd7542c175554a4b1f024cc0f9eef98ef4172467c579143d02c0f89179`

## Question and research gate

The preceding ColorFusion bundle closed the transformed-patch retention and
cross-module weight formulas but treated the live four-lane `noise` operand as
an input. This bundle traces that operand through target RAW preprocessing,
coarse reciprocal-signal and vignetting tables, installed SensorGainVars, and
the provider at `0x1ac6c0` back to concrete public LRI fields.

`tools/whatknown.sh ColorFusionBayer` returned `DOCUMENTED`, so the existing
formula and selection evidence was connected rather than re-investigated.
`tools/whatknown.sh highlight_restore_gain` returned `NO HITS`; the exact
HighlightRestore gain join was therefore a genuine investigation target.
After the direct join was found, `tools/whatknown.sh 0x350820` returned
`DOCUMENTED` for the installed conversion helper, whose already-admitted
Robertson and matrix-interpolation components are composed here.

## Reusable artifacts

- `tools/lldb_probes/colorfusion_f_runtime/noise_signal_origin_probe.py`
- `tools/lldb_probes/colorfusion_f_runtime/noise_signal_plane_probe.py`
- `tools/lldb_probes/colorfusion_f_runtime/hotpixel_lut_probe.py`
- `tools/lldb_probes/colorfusion_f_runtime/highlight_join_probe.py`
- `tools/verifiers/verify_colorfusion_noise_public_origin.py`
- `tools/verifiers/verify_colorfusion_highlight_join.cpp`
- `tools/verifiers/run_colorfusion_noise_public_origin.sh`
- ignored raw captures under `runs/colorfusion_f_runtime/`

Reproduce all retained comparisons with:

```bash
tools/verifiers/run_colorfusion_noise_public_origin.sh
```

## Exact HighlightRestore gain custody

`ColorFusionBayer::initialize` at `0x1ab2d0` preserves its third argument, the
AUTO `neutral_temp` / `neutral_tint` pair, and passes it as `rcx` to target and
source calls of `0x1ac010`. In the target call:

```text
0x1ab368  rdx = &ColorFusionBayer+0x140       target camera key
0x1ab392  rcx = saved neutral_temp/tint
0x1ab399  call 0x1ac010
```

`0x1ac010` obtains the keyed camera calibration through
`RawImageFactory+0x118 -> 0x1bdfa0 -> 0x351da0`, calls `0x350820` at
`0x1ac067`, and passes its three-float output unchanged to
`RestoreHighlightsBayer` at `0x1ac1ac`. Thus the vector is not guessed from a
nearby color stage and is not the raw reciprocal AWB triplet.

The public source chain before `0x350820` is the admitted AUTO chain:

```text
ViewPreferences.awb_gains
  -> normalized float32 (1/r, 1/g_r, 1/b)
  -> 0x350570 fixed-point solve with target ColorCalibration A/D65 matrices
  -> Robertson xy-to-(neutral_temp, neutral_tint)
```

For `temperature=T`, `tint=t`, public endpoint CCTs/matrices, `0x350820`
performs the following separately-rounded binary32 operations:

```text
(x,y) = robertson_temp_tint_to_xy(T,t)
M     = mired_interpolate(M_D65, M_A, T)

iy = f32(1.0f / y)
X  = f32(x * iy)
Z  = f32(f32(f32(1.0f - y) - x) * iy)

q0 = f32(f32(M02 * Z) + f32(f32(M00 * X) + M01))
q1 = f32(f32(M12 * Z) + f32(f32(M10 * X) + M11))
q2 = f32(f32(M22 * Z) + f32(f32(M20 * X) + M21))
ig = f32(1.0f / q1)
c  = (f32(q0 * ig), 1.0f, f32(q2 * ig))
```

The multiply by one shared `ig` is parity-relevant; direct `q0/q1` and
`q2/q1` are not the installed instruction sequence. The exact public replay
matches all captured gain words:

| Case | Raw normalized reciprocal AWB | `0x350820` / captured `c` |
|---|---|---|
| Unit-1 `28mm`, A1/key 0 | `3f150642 3f800000 3f211fbd` | `3f150644 3f800000 3f211fbf` |
| Unit-2 `70mm`, B4/key 8 | `3f1c02e8 3f800000 3f03c972` | `3f1c02e7 3f800000 3f03c976` |

This supersedes the earlier `1e-6`-only fit in
`docs/CLM-HIGHLIGHT-RESTORE-001.md`. Its physical interpretation was right,
but the implementation boundary is the exact temp/tint-to-neutral conversion
above.

## Public target plane

For the ColorFusion target camera, `0x1ac010` constructs:

```text
public RAW10
  -> admitted selected default hot-pixel worker
  -> RestoreHighlightsBayer(public c, black=42, white=1023)
  -> float32(uint16) - 42.0f
```

The new call/return probe captures the complete post-hot-pixel and
post-highlight `4160x3120` planes plus CFA phase and `c`. The already-admitted
Phoenix kernel reproduces every word only when its four-pixel true-frame halo
uses same-CFA parity extension:

```text
map(q,n) = q                         when 0 <= q < n
         = q & 1                     when q < 0
         = n - 2 + (q & 1)           when q >= n
```

Unit-1 phase is `(1,0)` and HighlightRestore changes zero pixels. Unit-2
phase is `(1,1)` and changes `24,020` pixels. Both full frames replay
`12,979,200 / 12,979,200` words exactly. On Unit-2 the non-parity controls
leave residuals: no extension `97`, edge `19`, reflect `9`, symmetric `19`,
and zero `43` words. The parity rule is therefore a measured discriminator,
not an arbitrary edge choice.

The public hot-pixel replay also matches all target words before
HighlightRestore. Unit-1 changes `9,896` RAW pixels; Unit-2 changes `6,651`.
The Unit-2 closure LUTs equal the installed selected SensorGainVars row in
spatial BGGR order `[blue,green,green,red]`; the admitted worker's effective
comparison uses `4.0f * LUT`.

## Exact coarse signal table

Body `0x18e150` reduces the final target float plane into a `260x195xvec4`
table. For each `16x16` block:

```text
r(x,y) = x86_rcpps(max(0.1f, target(x,y)))
lane 0 = f32(sum64(top-right parity, row-pair then column-pair order) * 1/256)
lane 1 = f32(sum64(top-left  parity, row-pair then column-pair order) * 1/256)
lane 2 = f32(sum64(bottom-left parity, row-pair then column-pair order) * 1/256)
lane 3 = f32(sum64(bottom-right parity,row-pair then column-pair order) * 1/256)
```

This is fixed spatial order `[TR,TL,BL,BR]`, not semantic RGBG order. Unit-2
BGGR is the discriminator: only fixed spatial order matches, at
`50,700 / 50,700` vectors. The two complete tables match all `202,800`
float32 words each.

## Exact coarse shading table

The target camera's public selected `FactoryModuleCalibration.vignetting`
`17x13` profile is applied to a unity `260x195` scalar image. For either axis:

```text
step = f32(extent / (profile_extent - 1)) = 16.25f
cell boundary(g) = floor(f32(g * step))
local = f32(coordinate - f32(g * step))
inverse = f32(1.0f / floor(step)) = 1/16
```

Y interpolation is the admitted binary32 multiply/add. X uses the installed
visible binary64 multiply/add followed by a binary32 store. Both retained
tables match all `50,700` words. Boundaries based on `g*floor(step)` or rounded
`g*step` do not match.

## Noise provider formula

RTTI identifies `0x1ac6c0` as
`ColorFusionBayer::initialize::$_1`. At patch coordinate `(px,py)`, discard
out-of-range members of `{px,px+1} x {py,py+1}` and average the survivors in
row-major float32 order:

```text
H = mean2x2_valid(coarse_shading)       scalar
D = mean2x2_valid(coarse_signal)        vec4

variance = max(1e-5f,
               f32(f32(f32(42.0f + f32(1.0f / D)) * model_a)
                       * f32(1.0f / 1023.0f))
                   + model_b)
noise = f32(f32(H*H) * variance) * f32(1023.0f*1023.0f)
core_noise = f32(noise * 8.0f)
```

`model_a=[red.a,green.a,blue.a,green.a]` and likewise for `model_b`. Select
the first installed RGB SensorGainVars row whose integer gain key is at least
`int(float32(sensor_analog_gain*100))`. Color uses table scale `1.0`; the
installed mono sibling uses `0.25`. Public black/white levels are `42/1023`.

Fresh captures deliberately exercise partial neighborhoods: Unit-1 patch
`(-1,95)` and Unit-2 patch `(-1,-1)`. Both reconstructed four-float `noise`
vectors and their core `x8` products match bit-for-bit:

```text
Unit-1: 445f9c3c 44d9390f 44960ec4 44d9f4a9
Unit-2: 43b41a65 4303c384 43b158f9 4324993e
```

## Admission boundary

Admit this as a `CLM-DENOISE-002` addendum at direct Unit-1 wide and
exact-focal Unit-2 tele runtime scope, with installed formula scope independent
of body/focal. The target RAW-to-noise path and its public origins are
implementation-ready. Prior route evidence supplies the normal wide/tele
target identities and four-focal incidence.

Do **not** promote the parent claim. This bundle does not replay every source
camera's complete half-resolution plane, the half-Hann overlap-add of all
patch weights, the complete u8 sidecar, or the final CNR tile. Those remain the
rank-1 implementation/validation boundary.
