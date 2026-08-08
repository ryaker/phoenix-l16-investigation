# MonoFusion Mode-0 Patch and Terminal Exact Replay

**Date:** 2026-08-08  
**Claim:** `CLM-PREFUSION-002` corrective addendum  
**Result:** `PROVEN` at the scope below

## Purpose

This bundle resolves three implementation-significant ambiguities left by the
earlier mode-0 formula narrative:

1. the noise helper's scalar `mu` comes from a separate public-vignetting
   auxiliary patch, not from the target image patch used for its harmonic term;
2. the installed Wiener coefficient update weights the target by `w` and the
   source by `1-w`, the reverse of the older prose; and
3. the installed inverse transform executes row before column at the live
   stride-2 and stride-1 stages, not column before row.

It also closes the float-flow to packed-flow conversion and the final scalar
tile combine on the same live production packet.

## Custody and Reproduction

Installed image:

```text
/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib
SHA-256 b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

Runtime input:

```text
Unit-1 exact 28mm
/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri
```

Reusable harness:

```text
tools/lldb_probes/prefusion_monofusion_mode0_tile/
  mode0_tile_probe.py
  unit1_28mm.lldb
  probe_inverse_coarse.c
  run_inverse_stages.sh
  verify_mode0_tile.py
```

Ignored, rerunnable captures are under:

```text
runs/prefusion_monofusion_mode0_tile/unit1_28mm/
```

After capture, the complete verifier is:

```bash
bash tools/lldb_probes/prefusion_monofusion_mode0_tile/run_inverse_stages.sh
```

The verifier SHA-pins the installed mode-0, noise, Wiener, transform,
overlap, and terminal windows, plus the 1024-byte coefficient table.

## Live ABI

At mode-0 entry `0x1a3c00`, the selected packet contains:

```text
output             522 x 522 float32
secondary output   empty
target             522 x 522 float32
auxiliary          full-domain 4160 x 3120 float32
sources            one 4160 x 3120 float32 image
flows              one 519 x 389 packed signed-int16 pair image
ROI                 [0,0,522,522]
```

The captured patch is the first live production patch in that top-left tile.
Its aligned source view is `[686,822,702,838]`.

## Public Auxiliary Origin and Mean

The auxiliary descriptor is not the target image. The complete
`4160x3120` capture matches every one of `12,979,200` float32 words generated
from the selected public `17x13` vignetting profile for calibration camera ID
`12`, mirror position `0`.

For grid node spacing `D=260` and binary32 `q=f32(1/D)`, a row is generated as:

```text
ty    = f32(local_y * q)
left  = f32(f32(ty * f32(bottom_left  - top_left )) + top_left)
right = f32(f32(ty * f32(bottom_right - top_right)) + top_right)
slope = f32(f32(right - left) * q)
pixel = f32(binary64(local_x) * binary64(slope) + binary64(left))
```

The live first-patch `mu` is the row-major scalar-binary32 mean of the
auxiliary map's top-left `8x8` view:

```text
sum = 0f
for y in 0..7:
    for x in 0..7:
        sum = f32(sum + auxiliary[y,x])
mu = f32(sum / 64f)
```

This independently generated result is exact:

```text
mu = 3.693539619445801
bits = 0x406c62f4
```

Static `0x1a4515..0x1a4549` supplies the same `addss` row-major reduction and
single `divss` operation. A separate 24-hit Unit-1 `35mm` capture confirms the
same operand distinction: each `mu` tracks the auxiliary view mean while the
target-patch arithmetic mean differs by one to two orders of magnitude.

## Noise Formula

Let `I_j` be the 256 target-patch samples. Only the harmonic statistic uses
those target values; `mu` is the auxiliary mean above:

```text
r_j = rcp_current_reference(f32(I_j + 0.1f))
H   = f32(sqrt(rcp_current_reference(f32(sum_j f32(r_j*r_j) / 256f))))
z   = max(f32(B/W), f32((B + f32((H-B)/mu)) / W))
m   = max(1e-5f, f32(a*z + b))
V   = f32(f32(f32(mu*W) * f32(mu*W)) * m)
```

The repo-local verifier preserves the installed current-reference reciprocal
mapping and scalar grouping. It reproduces the live variance word exactly:

```text
V = 142.7699432373047
```

## Correct Wiener Roles

For target coefficient `T_k`, aligned source coefficient `S_k`, installed
table value `F_k`, initializer `noise_scale`, and patch variance `V`:

```text
d       = f32(S_k - T_k)
d2      = f32(d*d)
lambda  = f32(F_k * f32(noise_scale*V))
w       = f32(rcpps_current_reference(f32(d2+lambda)) * d2)
output  = f32(f32(w*T_k) + f32(f32(1-w)*S_k))
```

Thus `w` is the target/rejection weight. It approaches one as source-target
disagreement dominates. The prior prose formula
`(1-w)*T + w*S` is role-reversed and is superseded.

The worker's reported confidence is:

```text
confidence = f32((256 - pairwise_grouped_sum(w_k)) * (1/256))
           = grouped mean(1-w_k)
```

All `256/256` live coefficient words and the confidence word match exactly.

## Transform Order

The captured target spatial patch reproduces all `256/256` forward
coefficient words. The corrected coefficient buffer then reproduces all
`256/256` inverse spatial words.

The live inverse order is:

```text
fused installed coarse-lattice inverse
stride 2: row, then column
stride 1: row, then column
```

Three direct installed-function checkpoints after coarse, complete stride 2,
and stride-1 row each match all 256 words. This supersedes the older generic
"column then row" inverse description. The fused coarse schedule and
stage-specific installed constants are required for bit equality.

## Packed Flow Consequence

The preceding float32 flow oracle and the live mode-0 packed descriptor agree
for all `403,782/403,782` components under:

```text
packed = signed_int16_low_word(trunc_toward_zero(float32_component))
```

Rejected vectors are not saturated before this store. `146,146` components
wrap modulo 65536. The first packed pair is `(694,830)`; with target halo
origin `(-8,-8)`, the resulting source patch is exactly
`[686,822,702,838]`, matching the live descriptor. A clean-room path must
preserve this low-word behavior rather than clamp rejected vectors.

## Terminal Combine

For the selected one-source route, every one of the `522x522 = 272,484`
terminal cells matches:

```text
one_minus_alpha = f32(1-alpha)
output = f32(f32(alpha*target) + f32(one_minus_alpha*overlap))
```

This is exact from the captured target and pre-combine overlap images to the
post-combine output. It does not by itself regenerate every overlap cell from
all preceding patches; the admitted half-Hann overlap formula remains the
authority for that intervening reduction.

## Verification Receipt

```text
prefusion_monofusion_mode0_tile=OK
auxiliary_mean_noise_variance=142.769943 exact_float32=OK
public_vignetting_auxiliary_exact=12979200_of_12979200
flow_int16_conversion_exact=403782_of_403782 wrapped_rejection_components=146146
inverse_stage_checkpoints_exact=3_of_3
forward_wiener_inverse_exact=256_of_256
final_combine_exact=272484_of_272484
flow_type=i16x2 first_displacement=(694, 830)
```

## Scope and Admission

- **Numerical runtime scope:** one arbitrary live mode-0 production patch and
  one complete terminal tile at Unit-1 exact `28mm`; complete public
  auxiliary map at the same scope.
- **Installed formula scope:** SHA-pinned selected mode-0 bodies.
- **Four-focal route scope:** prior admitted proof establishes profile-3
  `28mm/35mm` mode-0 liveness and `70mm/150mm` no-MonoFusion/direct-B4
  exclusion. This correction is therefore merge-critical with explicit
  four-focal applicability, not four redundant numerical tile replays.
- **Body scope:** prior exact-focal two-body mode-0, flow, public-vignetting,
  and transform evidence supplies the body discriminator. This bundle adds no
  claim of numeric invariance or firmware causation.
- **Not claimed:** an all-patch clean-room regeneration of the complete
  `522x522` overlap image, other installed builds, or compatibility mode 1.

Admit the corrected auxiliary-mean origin, Wiener operand roles, inverse
axis order, packed-flow low-word behavior, and exact terminal combine as a
corrective `CLM-PREFUSION-002` addendum. Claim status remains `PROVEN` /
`SPEC_READY` at its existing selected-profile scope.
