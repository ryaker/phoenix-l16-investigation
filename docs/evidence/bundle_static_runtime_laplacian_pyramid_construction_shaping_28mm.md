# Laplacian-Pyramid Construction, Level Rule, and Tonal Shaping

## Question

Close G-61 beyond the previously admitted transfer LUT and callback: identify
the exact Gaussian/Laplacian construction, image-size level rule, and the
runtime arithmetic roles of the five named shadow/highlight/percentile fields.

## Reusable artifacts

- `tools/lldb_probes/laplacian_clarity/verify_laplacian_clarity.py`
- `tools/lldb_probes/laplacian_clarity/inspect_gaussian_rtti.py`
- `tools/lldb_probes/laplacian_clarity/unused_config_fields_watch_probe.py`
- `tools/lldb_probes/laplacian_clarity/unused_config_fields_a_28mm.lldb`
- `tools/lldb_probes/laplacian_clarity/unused_config_fields_b_28mm.lldb`
- `tools/lldb_probes/laplacian_clarity/run_unused_config_fields_28mm.sh`
- ignored raw JSON/HDR outputs under `runs/laplacian_clarity/`

Reproduce all three complete renders and the installed-binary verifier:

```bash
bash tools/lldb_probes/laplacian_clarity/run_28mm.sh
```

No live `/tmp` or `/private/tmp` artifact is an evidence dependency.

## Installed identities

The pinned installed binary has SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`.
Its RTTI/vtable chain names and binds:

| Operation | Address point | Typeinfo | Operator slot | Worker |
|---|---:|---:|---:|---:|
| `ImageGaussianFilterAndSubSample<float>` | `0x664fc8` | `0x665010` | `+0x30 = 0x14620` | `0x14670` |
| `ImageGaussianUpscaleAndSubtract<float>` | `0x665168` | `0x6651b0` | `+0x30 = 0x16210` | `0x16250` |

The verifier SHA-pins those workers, wrappers `0x12c50` and `0x133d0`,
pyramid builder `0x136e0`, reconstruction body `0x13e40`, level selector,
and the complete tonal-shaping range `0x2e5594..0x2e5c69`.

## Level selection

For source dimensions `(W,H)`, body `0x2e4d9b..0x2e4dd0` computes:

```text
n = clamp(trunc(log2(min(W,H)) - 2.0), 2, 6)
```

`trunc` is x86 `cvttsd2si`, hence truncation toward zero. The pyramid contains
`n` planes: `n-1` detail planes and one terminal Gaussian plane. The clarity
callback is applied to detail levels `0..n-2`, not the terminal lowpass.

The first retained Unit-1 `28mm` packet has `W=H=543`, so `n=6`; its observed
callback levels `0..4` are exactly the five detail levels predicted by the
static rule. The earlier observation of “five levels” was therefore callback
scope, not a universal total-level constant.

## Gaussian reduction

Each next Gaussian has dimensions:

```text
W_next = (W + 1) >> 1
H_next = (H + 1) >> 1
```

The exact float32 one-dimensional kernel at `0x5a8850` is:

```text
k = [0.05000000074505806, 0.25, 0.4000000059604645,
     0.25, 0.05000000074505806]
raw = [0x3d4ccccd, 0x3e800000, 0x3ecccccd,
       0x3e800000, 0x3d4ccccd]
```

With edge-clamped coordinates, worker `0x14670` implements:

```text
G[j+1](x,y) = sum(a=-2..2, b=-2..2,
                  k[a+2] * k[b+2] *
                  G[j](clamp(2*x+a), clamp(2*y+b)))
```

The implementation is separable and samples every second input coordinate.

## Expansion and Laplacian sign

`ImageGaussianUpscaleAndSubtract<float>` expands a coarse plane to the exact
dimensions of its fine operand using these separable parity kernels:

```text
even fine coordinate 2*i:    coarse[i-1:i+1] weights [0.1, 0.8, 0.1]
odd fine coordinate 2*i+1:   coarse[i:i+1]   weights [0.5, 0.5]
```

The worker uses precombined exact float32 products:

- odd/odd: four neighbors at `0.25`;
- even/odd or odd/even: two central neighbors at
  `0.4000000059604645` and four side neighbors at
  `0.05000000074505806`;
- even/even: center `0.64000004529953`, four axial neighbors
  `0.08000000566244125`, and four diagonals `0.010000000707805157`.

Coarse indices are edge-clamped. The stored detail sign is the reverse of the
common textbook convention:

```text
P[j]   = Expand(G[j+1]) - G[j]       for j = 0..n-2
P[n-1] = G[n-1]
```

Reconstruction body `0x13e40` starts from `P[n-1]` and descends with:

```text
R = Expand(R) - P[j]
```

This exactly recovers `G[j]` because the stored residual is negative-detail.

## Tonal-field arithmetic

The body maintains paired sample arrays `(x_i,y_i)` used by the transformed
pyramid construction. Define public config values:

```text
S = lpyr_shadows
H = lpyr_highlights
L = lpyr_lower_percentile
U = lpyr_higher_percentile
M = lpyr_mid_percentile
e = the separate float scalar passed to 0x2e4cf0 in xmm0
q = *lower_bound(samples, M)
```

The highlight ramp coefficients are:

```text
D = 2*(q*q + 4) - (q + 2)^2 + 1e-15
a = (2*(0.05*q + 2) - 1.05*(q + 2)) / D
b = (1.05*(q*q + 4) - (0.05*q + 2)*(q + 2)) / D
```

For each sample abscissa `x`, the body forms:

```text
shadow_weight(x) = exp((x + 5)^2 *
    (-2.5649492740631104 / (L + 5)^2  if x < -5
     else -0.1776280701160431))

shadow_amplitude = clamp(2/e, 0, 1)
                 * 1.3
                 * min(1.2, max(0.12, (8-L)/22))
                 * (1-S)

highlight_weight(x) = 0                                      if x < q
                    = clamp(a*x+b, 0, 1)^2 * highlight_shape  otherwise

highlight_shape = 0.9 * (2*(U-0.05) + U - (U-0.05)*U)
highlight_amplitude = clamp((U+1)*(2/3), 0.12, 1) * (1-H)

y_i <- y_i
     + shadow_weight(x_i) * shadow_amplitude
     - highlight_weight(x_i) * highlight_amplitude
```

The installed implementation deliberately mixes float32 intermediates with
double arithmetic for `a,b`; the verifier pins the instruction range and all
constants rather than claiming arbitrary reassociation is bit-identical.

There is one additional lower-tail branch when `S != 1` and `L > -6`:

```text
c = 1.3 * (-5-L)
tail(x) = c                                             if x <= -5
        = (1-clamp((x+6)/6,0,1))^2 * c                 if -5 < x < 0
        = 0                                             otherwise
y_i <- y_i + tail(x_i)
```

Thus `shadows` and `highlights` are not labels without consumers: they are
neutral at `1.0` and scale the two envelopes through `(1-S)` and `(1-H)`.
`lower`, `mid`, and `higher` place or shape those envelopes. Under the default
packet `(S,H,L,U,M)=(1,1,-8,0.2,-1)`, both main amplitudes are zero and the
tail branch is skipped, while all five fields are still read by the live body.

## Runtime read proof

Two complete canonical Unit-1 `28mm` no-auto-LRIS renders armed read-only
hardware watches after the first `0x2e4cf0` entry. Both exited `0` and wrote
populated Radiance HDR files. LLDB reports watch stops after the access, so
the consumer instruction is immediately before each reported PC:

| Config field | Offset | Read hit count | Observed post-access PC(s) |
|---|---:|---:|---|
| `lpyr_shadows` | `+0x04` | `1680` | `0x2e5a73`, `0x2e5bbb` |
| `lpyr_highlights` | `+0x08` | `70` | `0x2e5a29` |
| `lpyr_lower_percentile` | `+0x10` | `70` | `0x2e559a` |
| `lpyr_higher_percentile` | `+0x14` | `70` | `0x2e59d6` |
| `lpyr_mid_percentile` | `+0x18` | `70` | `0x2e55a8` |

This runtime evidence proves liveness and exact consumer sites for one body
and one focal tier. The formulas, level rule, RTTI identities, and kernels are
installed static same-mechanism proof and are not zoom-conditioned.

## Admission boundary

Admit as a `CLM-SHARPEN-002` addendum:

- the exact level-count rule and distinction between total/detail levels;
- the exact reduction kernel, dimensions, edge policy, expansion parity
  weights, negative-detail sign, and reconstruction recurrence; and
- the exact arithmetic roles of all five previously name-only tonal fields.

Runtime field liveness is Unit-1 `28mm`; no claim is made that nondefault
packets occur in every zoom tier or that the property values have direct GUI
custody. This closes G-61 at formula level.
