# Static/Runtime Evidence: Index-5 Guidance Component Routes

**Date:** 2026-07-15  
**Status:** VERIFIED; admitted component-route and exact affine-fit refinement  
**Bearing:** `StereoLayer<false>+0x288` `Guidance`

> **Corrective supersession (2026-07-16):** Camera-key lineage, key-0
> selection, direct byte packing, and the later A5/A1 affine fit remain valid.
> The float source described below is post-`ConvertToYUV`, not raw collapse2
> RGB. Complete custody and full-plane replay now name key-0 lanes
> `[Y,U,V,1]`; see
> `bundle_static_runtime_index5_guidance_yuv_formula_two_body.md`.

## Question

Prior proof names Guidance's public producer as
`lt::StereoISP::CreateStereoImage` and its output type as
`Image<vec4x8ui>`, but deliberately leaves all four components unnamed.

This proof asks which internal route produces the exact key-`0` product later
reused as index-5 Guidance, what component math can be stated without
guessing, and what the two live integers compared immediately before the
producer call actually represent.

## Artifacts

- Reusable LLDB harness:
  `tools/lldb_probes/index5_guidance_channel_origin/`
- Component probe:
  `guidance_component_branch_probe.py`
- Unit-1 `28mm` launch:
  `guidance_component_branch_unit1_28mm.lldb` and
  `run_component_branch_unit1_28mm.sh`
- Static/runtime verifier:
  `verify_guidance_component_branches.py`
- Rerunnable report:
  `runs/index5_guidance_channel_origin/guidance_component_branch_unit1_28mm.json`
- Reused key-`0` custody report:
  `runs/index5_guidance_channel_origin/guidance_origin_28mm.json`

The component harness checksum-stages the canonical LRI under
`/private/tmp`, terminates immediately after the second route's affine
transform, and copies the report into the durable ignored `runs/` tree.
No scratch file is an evidence dependency.

## Separate Installed Color-Space Map

The SHA-pinned installed property map names:

| Selector | Installed name |
|---:|---|
| `1` | `none` |
| `2` | `srgb` |
| `3` | `adobe_rgb` |
| `4` | `linear_srgb` |
| `5` | `linear_prophoto_rgb` |
| `6` | `linear_adobe_rgb` |

The map is introduced by the installed property label
`output color-space`. This is a real installed schema, but it is **not** the
source of the two integers observed at `0x3f5035`. Earlier wording in this
evidence incorrectly joined those unrelated facts.

## Camera-Key Lineage

The sole caller `0x3fc750` obtains the tier-anchor camera key by calling
`0x1bea00` on `state+0xe0`, stores it at `[rbp-0x2c]`, and supplies that
address as the `rdx` argument to `0x3f4b90`. Its `rcx` argument is the current
four-byte item from a source-camera-key iterator; the caller advances that
iterator by four bytes at `0x3fc821`.

`0x3f4b90` preserves the source-key pointer at `[rbp-0x4b0]` and the anchor
pointer through `rbx/[rbp-0x4c0]`. It resolves both through the same
`state+0xe0 -> 0x1be970` CapturedImage map. At `0x3f5025..0x3f503d` it compares
`*source_key` with `*anchor_key` and passes the equality result as a boolean
argument to `StereoISP::CreateStereoImage`. These operands are camera keys,
not color-space selectors.

## Two Producer Invocations

The one-shot runtime packet records exactly two
`StereoISP::CreateStereoImage` invocations on the same thread and with the
same public `Image<vec4x32f>` output descriptor:

| Call | Source / anchor camera | Route booleans | Route |
|---:|---:|---:|---|
| `0` | `A1 / A1` (`0 / 0`) | `1 / 1` | direct float-to-byte pack |
| `1` | `A5 / A1` (`4 / 0`) | `0 / 1` | fitted affine three-channel match, then pack |

The independent cache-custody report observes key `0` insertion after exactly
one completed producer call and matches producer event index `[0]`.
Consequently call `0`, not the later affine-match call, is the exact product
installed as key `0`, then as `Images[0]`, and finally reused as index-5
Guidance.

## Key-0 Component Route

At `0x27c053`, call `0` copies its completed public
`Image<vec4x32f>` descriptor into the direct source. The exact source address
equals the public float-output argument recorded at function entry.

The installed `0x27c100..0x27c1d7` loop then:

1. reads each four-float pixel without a channel shuffle;
2. rounds all four lanes with `cvtps2dq`;
3. signed-packs and unsigned-saturates the results; and
4. writes one four-byte `vec4x8ui` pixel.

Five spatial samples from the `2080 x 1560` direct source have independent
values in lanes `0..2`; lane `3` is exactly `1.0` in every sample. This
supports the following operational names only:

| Guidance component | Admitted identity |
|---|---|
| `C0`, `C1`, `C2` | direct rounded/saturated SoftISP color components |
| `C3` | constant-one auxiliary component on all five sampled positions |

The downstream SGM guide-distance vector independently has a zero fourth
coefficient, so `C3` does not enter the admitted three-component guide
distance.

## Exact Later Affine-Match Route

Call `1` exists in the same producer body but is not key `0`. It invokes
`0x3775f0` to fit a data-derived three-channel affine transform and
`0x377930` to apply it before byte packing.

The installed caller constructs the fit object at `0x27c31b`, installs a
3x3 identity at `0x27c327..0x27c355`, and stores its inverse through
`0x376d30`. The selected route therefore has no unclassified pre/post color
matrix. `0x3775f0` scans the source and target float images independently.
Only samples with lane `C3 > 0.95f` enter the standard float32 Welford
accumulators:

```text
n'    = n + 1
delta = x - mean
mean' = mean + delta / n'
M2'   = M2 + (n / n') * outer(delta, delta)
```

The object stores each three-component mean, diagonal second moment, cross
moments in `(C0*C1, C1*C2, C2*C0)` order, and count. The fit requires at
least `100` valid samples in both images; otherwise `0x376e50` writes the
4x4 identity and returns false.

For each accepted side, the covariance preparation order is exact and
significant:

```text
inv_n_f32 = float32(1.0f / count_f32)
cov_f32   = float32(M2_f32 * inv_n_f32)  # population covariance
cov_f64   = double(cov_f32) + 0.001 * I
```

Let `Ls = chol(cov_source)` and `Lt = chol(cov_target)`, where `chol`
returns the lower-triangular double-precision Cholesky factor. The installed
`0x9d970` inverse and `0x25ec70` matrix products form:

```text
A = Lt * inverse(Ls)
b = mean_target - A * mean_source

M = [ A00 A01 A02 b0 ]
    [ A10 A11 A12 b1 ]
    [ A20 A21 A22 b2 ]
    [  0   0   0   1 ]
```

The double result is converted once to float32 for storage. This is a
lower-triangular color-covariance transfer, not a per-channel gain fit,
least-squares regression, von-Kries adaptation, or an app-level heuristic.

For the captured run, the fitted rows are:

```text
[ 0.823972225,  0,            0,           6.13440704 ]
[-0.074844249,  0.459807754,  0,          61.9629517  ]
[-0.287964791, -0.178175777,  0.304052234, 107.345886 ]
[ 0,            0,            0,           1          ]
```

The retained object contains source and target means, all six second moments,
counts `3,244,800` / `3,163,058`, and the emitted matrix. The verifier
independently rebuilds both population covariance matrices with the installed
float32 reciprocal/multiply order, performs the double Cholesky/inverse
composition, and matches all sixteen stored float32 words exactly. It also
recomputes all three output components at five positions from the captured
input and rows; every result agrees within `2e-5`. Installed `blendps $8`
preserves the input fourth lane, and all sampled input/output fourth lanes
equal `1.0`.

This contrast proves that the cross-camera A5 product is color-matched to the
A1 anchor in its first three components. It is not attributed to key-`0`
Guidance.

## Verification

```text
static_guidance_component_branches=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
installed_output_color_space_map=1:none,2:srgb,3:adobe_rgb,4:linear_srgb,5:linear_prophoto_rgb,6:linear_adobe_rgb
camera_key_lineage=state+0xe0 anchor; iterator source; same-map lookups; equality drives CreateStereoImage bool
runtime_routes=call0 source/anchor=A1/A1 direct; call1 source/anchor=A5/A1 affine-match
guidance_components=call0 C0/C1/C2 direct rounded color components; C3=1 pass-through
call1_affine_rows=0.823972225,0,0,6.13440704;-0.0748442486,0.459807754,0,61.9629517;-0.287964791,-0.178175777,0.304052234,107.345886;0,0,0,1
call1_affine_fit=population_covariance_float32_reciprocal;double_cholesky(target)*inverse(cholesky(source));epsilon=0.001;translation=target_mean-A*source_mean;all_16_words_exact
direct_sample_count=5 all_C3=1
guidance_component_branches=OK
```

The prior public-producer, cost-operand, and SGM-parameter verifiers remain
green.

## Admission and Boundary

Admitted:

- key-`0` / `Images[0]` / Guidance uses producer call `0`;
- the compared `0/0` and `4/0` values are source/anchor camera-key pairs,
  concretely A1/A1 and A5/A1 in this Unit-1 `28mm` packet;
- call `0` directly rounds and saturates three SoftISP color components;
- sampled `C3` is exactly `1`, and installed pack/apply paths preserve lane
  order; and
- the later call-`1` affine route is a separate product and is not Guidance;
  its exact population-covariance, regularized-Cholesky affine formula,
  minimum-sample fallback, and float/double rounding boundary are closed.

Scope: the formula and identity initialization are SHA-pinned installed-code
facts. Existing four-focal custody proves the shared `CreateStereoImage`
producer supplies the admitted A1-wide/B4-tele image sets, so the mechanism
is four-focal applicable. The bit-exact fitted-statistics replay is one
Unit-1 `28mm` A5/A1 discriminator; no claim is made that its numeric matrix is
constant across source cameras, captures, physical bodies, or firmware.

Still open:

- public semantic names for key-`0` `C0/C1/C2`;
- the live SoftISP output color-space/configuration that applies to those
  components (the installed property map alone does not establish it);
- a universal proof that `C3` is one at every pixel and every focal/body; and
- remaining Cost-volume recurrence sources, temporaries, caps, baselines,
  final contribution, and acceptance/rejection.

In particular, this evidence does not rename `C0/C1/C2` as RGB, YUV, NVI, or
another convention. The installed `ImageRGBToNVI` and `ConvertToYUV` names
are not on the admitted key-`0` custody chain.
