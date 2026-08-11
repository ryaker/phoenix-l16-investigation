# ColorFusion CNR Guide Implementation

## Scope

This is the wiring contract for the profile-3 `ColorFusionBayer` second-output
weight and its conversion into CNR source lane 3. The arithmetic and camera
selection below are admitted formula slices of `CLM-DENOISE-002`; the parent
claim remains `PARTIAL` until a complete raw-input-to-CNR-tile replay and
Phoenix integration validation pass.

## Claim Inputs

- `CLM-DENOISE-002`
- `CLM-INPUT-001`
- `CLM-PREFUSION-002`
- `CLM-C6-001`

Controlling evidence:
`../../evidence/bundle_runtime_colorfusion_f_formula_selection_profile3.md`
and
`../../evidence/bundle_static_runtime_colorfusion_noise_public_origin_two_body.md`.

## Zoom Coverage

| Zoom | Required topology | Evidence scope |
|---|---|---|
| 28mm | reference A1; sources A5/A3/A4 | direct ordered-vector + transform runtime, Unit-1 |
| 35mm | reference A1; sources A5/A3/A4 | installed selector + admitted four-focal key order |
| 70mm | reference B4; sources B2/B5/B1/B3 | direct ordered-vector + transform runtime, Unit-2 |
| 150mm | reference B4; sources B2/B5/B1/B3 | installed selector + admitted four-focal key order |

## Inputs and layout

Operate at ColorFusion half resolution, nominally `2080x1560`. Each patch is
`16x16` with step `8`. Every transformed coefficient is `vec4<float>` in
Bayer-lane order inherited from the source plane; do not collapse to luma or
lane 0. The reference plane is separate from the source vector.

Enumerate the RawImageFactory/CaptureStack key list in first-occurrence order
and apply this predicate without sorting:

```text
keep candidate when
  candidate.is_enabled
  && candidate.id != target.id
  && camera_group(candidate.id) == camera_group(target.id)
  && ((candidate.sensor_bayer_red_override.x
       | candidate.sensor_bayer_red_override.y) >= 0)
```

For normal profile-3 LRIs this produces:

```text
wide: target/reference A1(0), sources [A5(4), A3(2), A4(3)]
tele: target/reference B4(8), sources [B2(6), B5(9), B1(5), B3(7)]
```

Do not include A2, the target itself, C cameras, or C6. Do not sort the
survivors: direct runtime packets prove the orders above, which are the
admitted wide `A1,A5,A2,A3,A4` and tele `B4,B2,B5,B1,B3` key orders after
filtering. Module accumulation must retain this order.

## Exact target preprocessing and scene-neutral gain

Build the target/reference Bayer plane at `4160x3120` as:

```text
public target RAW10
  -> selected default hot-pixel worker
  -> RestoreHighlightsBayer(c, black=42, white=1023)
  -> float32(uint16) - 42.0f
```

Use the already-admitted hot-pixel and Bayer HighlightRestore kernels. At the
true frame edge, provide a four-pixel halo with same-CFA parity extension:

```text
map(q,n) = q               if 0 <= q < n
         = q & 1           if q < 0
         = n-2 + (q & 1)   if q >= n
```

Do not leave a four-pixel border untouched and do not use edge, reflect,
symmetric, or zero extension.

The HighlightRestore gain `c` is not the raw reciprocal AWB vector. Starting
from the target/tier-anchor camera's public AUTO white-balance path, obtain the
exact `neutral_temp=T` and `neutral_tint=t` through the admitted normalized
reciprocal-AWB, `0x350570` fixed-point, and Robertson conversion. Then use the
same target camera's public A/D65 CCTs and color matrices:

```text
(x,y) = robertson_temp_tint_to_xy(T,t)
M     = mired_interpolate(M_D65, M_A, T)

iy = f32(1.0f / y)
X  = f32(x * iy)
Z  = f32(f32(f32(1.0f - y) - x) * iy)

q0 = f32(f32(M02*Z) + f32(f32(M00*X) + M01))
q1 = f32(f32(M12*Z) + f32(f32(M10*X) + M11))
q2 = f32(f32(M22*Z) + f32(f32(M20*X) + M21))
ig = f32(1.0f / q1)
c  = (f32(q0*ig), 1.0f, f32(q2*ig))
```

Preserve the shared reciprocal and multiply sequence; direct `q0/q1` and
`q2/q1` are not a bit-exact translation. Required checkpoint words are:

```text
Unit-1 A1 28mm: 3f150644 3f800000 3f211fbf
Unit-2 B4 70mm: 3f1c02e7 3f800000 3f03c976
```

## Exact target signal and shading tables

Reduce the final target float plane to `260x195xvec4`. For each `16x16`
block, first compute `r=x86_rcpps(max(0.1f,target))`, then sum each 8x8 Bayer
parity subset in row-pair outer / column-pair inner order and multiply the
sum by exact `1/256`. Store lanes in fixed spatial order:

```text
lane 0 = top-right
lane 1 = top-left
lane 2 = bottom-left
lane 3 = bottom-right
```

This order is independent of CFA phase. In particular, do not reorder B4/BGGR
to semantic RGBG lanes.

Build a separate scalar `260x195` shading table by applying the target's
public selected `FactoryModuleCalibration.vignetting` `17x13` profile to
unity. For either axis:

```text
step = f32(extent / (profile_extent-1))       // 16.25
boundary(g) = floor(f32(g*step))
local = f32(coordinate - f32(g*step))
inverse = f32(1.0f / floor(step))             // 1/16
```

Use binary32 Y interpolation. Use the admitted binary64 visible multiply/add
followed by binary32 store for X interpolation. Do not replace the boundaries
with `g*floor(step)`.

## Exact four-lane noise provider

For a patch's coarse coordinate `(px,py)`, enumerate the row-major 2x2
neighborhood and discard out-of-range coordinates rather than clamping them.
Average each surviving sequence with binary32 additions followed by division
by the surviving count:

```text
H = mean_valid(shading)       // scalar
D = mean_valid(signal)        // vec4
```

Select the first installed RGB SensorGainVars row whose gain key is at least
`int(f32(sensor_analog_gain*100))`, using the target camera's public analog
gain. Construct:

```text
model_a = [red.a, green.a, blue.a, green.a]
model_b = [red.b, green.b, blue.b, green.b]

variance = max(1e-5f,
               f32(f32(f32(42.0f + f32(1.0f/D))*model_a)
                       * f32(1.0f/1023.0f))
                   + model_b)
noise = f32(f32(f32(H*H)*variance) * f32(1023.0f*1023.0f))
core_noise = f32(noise * 8.0f)
```

Pass `core_noise` to the per-coefficient retention formula below. The color
table scale is `1.0`; do not apply the mono sibling's `0.25` scale.

## Patch transform

Use the normalized 5/3-family implementation already present in Phoenix
`engine/merge/monofusion.cpp`, not the unnormalized local transform currently
in `colorfusion.cpp`:

```text
forward levels: strides 1,2,4,8; rows then columns
right_last = final even sample
left_first = first detail sample
d_i = f32(f32(o_i * 0.7071067690849304f)
          - f32(f32(e_i + right_i) * 0.3535533845424652f))
s_i = f32(f32(1.4142135381698608f * e_i)
          + f32(f32(left_i + d_i) * 0.4999999701976776f))
```

Preserve float32 stores and order. Reuse/refactor the proven code rather than
maintaining a second transform transcription.

## Module retention

Use the installed 256-value `F[c]` table already carried by Phoenix. For each
source module and coefficient in ascending row-major order:

```text
for c = 0..255:
  for j = 0..3:
    d[j]   = f32(T[c][j] - S[c][j])
    d2[j]  = f32(d[j] * d[j])
    lam[j] = f32(F[c] * noise[j])
    w[j]   = f32(x86_rcp(f32(d2[j] + lam[j])) * d2[j])

  q = x86_max(x86_max(w[0],w[2]), x86_max(w[1],w[3]))
  accumulator = f32(accumulator + f32(1.0f - q))

m[k] = f32(accumulator * 0.00390625f)
```

Initialize `accumulator=+0.0f`. `noise` is a four-float live vector, not one
scalar. Implement x86 `MAXPS/MAXSS` source-on-tie/NaN behavior and the existing
exact unrefined `RCPPS` emulation. The same scalar `q` is broadcast if the
fused coefficient output is also implemented.

## Cross-module weight

```text
A = 1.0f
B = 0.0f
for k = 0..N-1 in selected source order:
  B = f32(B + f32(m[k] * m[k]))
  A = f32(A + f32(1.0f - m[k]))
numerator = f32(f32(A * A) + B)
denominator = f32(float((N + 1) * (N + 1)))
f_patch = f32(numerator / denominator)
```

Overlap-add `f_patch` using the installed half-sample Hann-16 window on the
step-8 lattice and the installed boundary/normalization behavior. Do not
rewrite `A` as `N+1-sum(m)` in executable code.

## Byte sidecar and CNR lane

The production boundary is intentionally quantized:

```text
t = trunc_toward_zero(f32(f * 256.0f))
b = uint8(max(t - 1, 0))

if b == 0:
  lut = 0.0f
else:
  lut = f32(sqrt(f32(float(b + 1) / 256.0f)))

scale = sqrtf(profile_scalar_cc)
guide = f32(lut * scale)
lane3 = f32(guide * guide)
```

For profile 3 and public `SENSOR_AR1335(2)`, `profile_scalar_cc` is exact
`1.0f` at every installed analog-gain row. Keep the selector in the data model
because other installed sensor/profile banks are not constant one. Preserve
the byte-zero special case and the final float32 square; `lane3=f` is not an
allowed shortcut.

Pixel-double the half-resolution byte/guide plane into the full-resolution
CNR tile using the already admitted nearest 2x coordinate mapping. Supply this
as source lane 3 before covariance/mean computation.

## Required Phoenix changes

1. Replace `colorModuleRetention(array<float,256>, scalar_noise)` with a
   256-by-vec4 interface plus `array<float,4>` noise.
2. Use the per-coefficient four-lane max and installed float32 accumulation
   order.
3. Change `colorFusionWeight` to `A=1; A+=1-m`, retaining source-vector order.
4. Replace/refactor the local unnormalized transform with the proven
   normalized transform from `monofusion.cpp`.
5. Build the target RAW plane, scene-neutral HighlightRestore gain, parity
   frame halo, reciprocal-signal table, vignetting table, and four-lane noise
   vector exactly as specified above.
6. Build reference/source half-resolution Bayer planes from the exact ordered
   camera vectors above; do not use a generated composite as the fixed
   reference and do not sort source IDs.
7. Emit the u8 sidecar, decode it through the LUT/scalar/square path, 2x map
   it, and replace CNR's constant lane 3.

## Validation gates

Before final-image tuning, require:

1. `verify_colorfusion_f_runtime.py` reproduces all three retained Unit-1
   28mm `m`, `A`, `B`, and numerator words exactly.
2. `run_colorfusion_noise_public_origin.sh` passes both public-origin cases,
   including both complete `4160x3120` HighlightRestore frames and the exact
   gain/signal/shading/noise words.
3. A Phoenix replay of those same vec4 blobs matches `0x3f40e9fe`,
   `0x3f58699a`, `0x3f51ea60`, and patch `f=0x3e8e8cf6` exactly.
4. Camera-selection unit tests return the ordered wide/tele vectors above from
   public records, including A2 and C6 rejection.
5. Exhaustive bytes `0..255` match the installed LUT and post-square SHA-256
   values already admitted for `CLM-DENOISE-002`.
6. Capture and replay one complete ColorFusion/CNR tile at wide and tele,
   then repeat on a second physical body. This is the gate that upgrades the
   parent claim; it cannot be replaced by final-image visual tuning.

## Known exclusions

- Direct source-ID vectors and raw-to-transformed checkpoints are retained for
  Unit-1 `28mm` wide and exact-focal Unit-2 `70mm` tele. Both transform packets
  replay all `1024` float32 words exactly.
- Target RAW-to-noise public-origin packets use the same two cases. Complete
  target, signal, shading, gain, and provider-noise words replay exactly.
- Whole-tile ColorFusion output, complete CNR tile output, and final image
  parity remain validation work. `CLM-DENOISE-002` therefore remains
  `PARTIAL/BLOCKER`.
