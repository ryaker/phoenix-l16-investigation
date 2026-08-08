# Static/Runtime Evidence: Index-5 Guidance YUV Formula

**Date:** 2026-07-16  
**Status:** VERIFIED; corrective `CLM-STEREO-001` addendum  
**Bearing:** `StereoLayer<false>+0x288` `Guidance`, G-42 fixed reference

## Correction

Earlier evidence correctly proved that `StereoISP::CreateStereoImage` first
forms a half-resolution float collapse2 image with components
`[R, 0.5*(G1+G2), B, 1]`. It incorrectly treated that intermediate as the
float image packed into key `0` and excluded `StereoISP::ConvertToYUV` from
the key-0 custody chain.

The SHA-pinned body proves the opposite. `CreateStereoImage` calls
`0x27adc0` at `0x27bff0` with the collapse2 float descriptor and a generated
4x4 matrix. Installed RTTI names the callback
`lt::StereoISP::ConvertToYUV(...)::$_0`; its runtime callback address point is
`0x659020`, whose worker slot `+0x30` is `0x27ce60`. The returned float
descriptor is copied at `0x27bff5..0x27c003` and the selected direct route
rounds and saturates it into `Image<vec4x8ui>` at
`0x27c100..0x27c1d7`.

Therefore selected key-0 Guidance is `[Y,U,V,1]`, not final
`[R,0.5*(G1+G2),B,1]`. The latter remains the exact pre-YUV collapse2
intermediate.

## Artifacts

- Reusable capture:
  `tools/lldb_probes/index5_guidance_channel_origin/create_stereo_color_stage_probe.py`
- Generic runner:
  `tools/lldb_probes/index5_guidance_channel_origin/run_create_stereo_color_stage.sh`
- Static/full-plane verifier:
  `tools/lldb_probes/index5_guidance_channel_origin/verify_create_stereo_yuv.py`
- Rerunnable reports and ignored image dumps:
  `runs/index5_guidance_channel_origin/create_stereo_color_{unit1_28mm,l16_06689,unit2_28mm}/`
- Reused public AWB proof:
  `docs/evidence/bundle_static_runtime_awb_public_origin_four_zoom_two_body.md`
- Reused collapse2/hot-pixel proof:
  `docs/evidence/bundle_static_runtime_index5_guidance_collapse2_hot_pixel.md`
- Reused key-0 cache/Guidance custody:
  `docs/evidence/bundle_static_runtime_index5_guidance_public_producer_origin.md`

The capture deletes prior report and image artifacts before every launch.
This fixes an earlier harness weakness under which an LLDB launch failure
could leave an old report available to the shell. Failed/lost-connection
launches now cannot pass.

## Public Inputs

For the selected camera, `0xf3340(CapturedImage)` returns
`CapturedImage+0xa8`. `0xef820` dispatches its first integer as installed
`SensorType`; embedded `sensor_type.proto` names value `2` exactly
`SENSOR_AR1335`. Each source LRI has one public
`LightHeader.sensor_data.type = SENSOR_AR1335(2)` packet, and every runtime
entry reads `CapturedImage+0xa8 = 2`.

The returned installed type-2 response is:

```text
w = [0.2155500054359436,
     0.43230700492858887,
     0.35214298963546753]
```

The three words also occur exactly in the installed image at `0x5fc100`.
They are identical in all three runtime packets. They are installed
sensor-type constants, not values copied from the public LRI sensor
characterization table.

The other matrix input is:

```text
p = [float32(1 / ViewPreferences.awb_gains.r),
     float32(1 / ViewPreferences.awb_gains.g_r),
     float32(1 / ViewPreferences.awb_gains.b)]
```

The verifier decodes those named fields from each report's own source LRI
and requires exact float32-word equality with the runtime vector.

## Matrix Construction

Let `w=(a,b,c)`, `p=(pr,pg,pb)`, and let every shown elementary operation
round to float32. The exact `0x27b82d..0x27b97f` construction is:

```text
S     = c + a
nb    = -b                         # sign-bit xor
q     = -b*b
y1    = (c-a)*nb / pg
m     = S / pg
x1    = (q-c*S) / pr
z1    = (a*S-q) / pb
x2    = nb / pr
z2    = nb / pb

nw    = sqrt(a*a + b*b + c*c)
s1    = nw / sqrt(x1*x1 + y1*y1 + z1*z1)
s2    = nw / sqrt(x2*x2 + m*m + z2*z2)

M = [ a      b      c      0 ]
    [ x1*s1  y1*s1  z1*s1  0 ]
    [ x2*s2  m*s2   z2*s2  0 ]
    [ 0      0      0      0 ]
```

The verifier preserves the installed multiply/add and square/add order. It
reproduces all 16 captured matrix words exactly in all three packets.

For each pre-YUV pixel `x`, worker `0x27ce60` computes `t=M*x` in this exact
component order:

```text
t = x3*M_col3
t = t + x2*M_col2
t = t + x0*M_col0
t = t + x1*M_col1
```

## Signed Power and Offset

Each component then receives the installed sign-preserving fast-power
approximation to exponent `1/2.2`, followed by byte-domain scale and offset:

```text
q = sign(t) * 255 * fast_pow_abs(t, 0.45454543828964233)
yuv_float = q + [0,128,128,0]
yuv_float.C3 = 1
```

This is not replaced by host `pow()`. The verifier emulates the worker's
integer mantissa/exponent extraction, clamps its log-domain exponent to
`[-126,128]`, applies the exact polynomial sequence, rebuilds the exponent
bits, and preserves every intermediate float32 rounding. Pinned constants
are:

| Role | float32 / bits |
|---|---|
| absolute mask | `0x7fffffff` |
| mantissa mask | `0x007fffff` |
| log polynomial | `0.204204366`, `-1.25254691`, `3.33102155`, `-2.28267884` |
| exponent | `0.454545438` (`1/2.2`) |
| clamp | `-126`, `128` |
| exp polynomial | `0.0780245215`, `0.226067156`, `0.695833564`, `0.999925196` |
| scale | `255` |
| offset | `[0,128,128,0]` |

The final direct pack uses SSE `cvtps2dq`, hence round-to-nearest-even under
the observed default MXCSR, followed by signed-word and unsigned-byte
saturation. It does not shuffle lanes. Final Guidance is operationally:

```text
Guidance = saturating_u8(round_nearest_even([Y,U,V,1]))
```

## Runtime Discriminators

All captures are selected key `0`, `2080 x 1560`, and terminate after the
first packed anchor image. Each row passes exact replay of 16 matrix words,
all `12,979,200` post-YUV float words, and all `12,979,200` packed bytes.

| Packet | Public AWB `(r,g,b)` | Packed SHA-256 |
|---|---|---|
| Unit-1 canonical `28mm` `L16_02130` | `(1.71783900,1,1.58883858)` | `7a3f8a4dfeed538200e67c1288a8e3c1989b3de442dde327f127a06102c2bb68` |
| Unit-1 independent `L16_06689` | `(1.98879659,1,1.44023824)` | `7c373e31a1e04fdca0a9ab3f0ab02d20e408c8d00102a48a01f4d3c9724e131d` |
| exact-focal Unit-2 `28mm` `L16_02130` | `(1.64829481,1,1.77895069)` | `cf28aadd40f877d505383e3b01ed7d9d0735459c0e7cfd7cfe9e44da965793f3` |

The packets deliberately separate a second scene/current builder input from
a second physical body. Numeric differences are joined to each LRI's public
AWB values; no body or firmware cause is inferred.

## Scope and Admission

Admitted for selected profile-3 key-0 Guidance:

- pre-YUV collapse2 is `[R,0.5*(G1+G2),B,1]`;
- `StereoISP::ConvertToYUV` is on the key-0 custody path;
- final float lanes are named `[Y,U,V,1]` by installed RTTI and exact
  callback custody;
- exact sensor-response/AWB matrix construction, signed-power approximation,
  byte-domain offset, and direct byte pack are formula-closed; and
- scene and physical-body discriminators reproduce complete planes exactly.

Installed formula scope is focal-independent. Existing accepted Unit-1
four-focal producer/cost-volume custody establishes use of the shared path at
`28/35/70/150mm` (A1 wide, B4 tele). The new complete arithmetic packets are
two Unit-1 scenes plus exact-focal Unit-2 `28mm`; no claim is made that the
three captured AWB matrices are universal constants.

This corrective admission supersedes only the old claim that packed Guidance
itself is `[R,0.5*(G1+G2),B,1]` or that `ConvertToYUV` is a separate Upsample-
only route. It does not alter the already-proven collapse2 intermediate,
hot-pixel formula, key-0 cache custody, G-42 metric, SGM recurrence, depth
geometry, or non-anchor affine color-match path.
