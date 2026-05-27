# Bundle + LLDB IRAMP `0x36cde0` Scalar Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib` and corrected canonical bridge HDR quartet.

This document narrows the third field in the IRAMP refined three-float tuple.

It proves:

- the third tuple field at `0x369e91` is the live scalar returned in `xmm0` by `0x36cde0`
- `0x36cde0` consumes the two 16x16 `vec4` patches prepared immediately before the call
- `0x36cde0` computes patch statistics, fixed arithmetic reduction stages, weighted accumulation, and returns `sqrt(xmm0 * xmm1)` at `0x36e511..0x36e515`

It does not prove the public semantic name of the scalar, downstream tuple consumption, or final merge acceptance / rejection.

## Inputs

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Tooling Boundary

Reusable probes live in the repo:

- `tools/lldb_probes/iramp_36cde0_return/return_probe.py`
- `tools/lldb_probes/iramp_36cde0_return/return_first_28mm.lldb`
- `tools/lldb_probes/iramp_36cde0_return/return_first_35mm.lldb`
- `tools/lldb_probes/iramp_36cde0_return/return_first_70mm.lldb`
- `tools/lldb_probes/iramp_36cde0_return/return_first_150mm.lldb`

Generated run outputs go under ignored `runs/iramp_36cde0_return/`.

No probe harness for this evidence lives in `/private/tmp`.

## Static Proof

Installed bundle: `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`.

### Caller Wiring

The refined tuple path prepares two patch pointers and calls `0x36cde0`:

```asm
0x369e31  leaq -0x4240(%rbp), %rdi
0x369e38  leaq -0x11a0(%rbp), %rsi
0x369e3f  callq 0x36cde0
```

Immediately after the call, the same path writes the tuple. The third write uses `xmm0` unchanged from the `0x36cde0` return:

```asm
0x369e76  movss -0x4310(%rbp), %xmm1
0x369e7e  movss %xmm1, (%rcx,%rax,4)
0x369e83  movss -0x4320(%rbp), %xmm1
0x369e8b  movss %xmm1, 0x4(%rcx,%rax,4)
0x369e91  movss %xmm0, 0x8(%rcx,%rax,4)
```

### `0x36cde0` Inputs

The callee preserves the two patch pointers:

```asm
0x36cdf2  movq %rsi, %r14
0x36cdf5  movq %rdi, %r12
```

Within the first loop, `r14` and `r12` are read as aligned `vec4` streams.

### Patch Statistics

The first visible loop is a 16-by-16 traversal over the two patch buffers. It accumulates:

- sum from the `r14` patch
- sum from the `r12` patch
- square sum from the `r14` patch
- square sum from the `r12` patch
- cross product sum between the two patches

Representative instructions:

```asm
0x36ce40  movaps -0x10(%r14,%rsi), %xmm5
0x36ce46  addps %xmm5, %xmm0
0x36ce49  movaps -0x10(%r12,%rsi), %xmm6
0x36ce4f  addps %xmm6, %xmm1
0x36ce55  mulps %xmm5, %xmm6
0x36ce58  mulps %xmm5, %xmm5
0x36ce5b  addps %xmm4, %xmm5
...
0x36ce83  mulps %xmm2, %xmm2
0x36ce86  addps %xmm7, %xmm2
0x36ce89  addps %xmm6, %xmm3
```

The accumulated values are multiplied by `0.00390625` (`1/256`) from `0x5cbfc0`, proving the loop normalizes over a 256-sample patch:

```asm
0x36cea6  movaps 0x25f113(%rip), %xmm5 ; 0x5cbfc0 = 0.00390625
0x36cead  mulps %xmm5, %xmm0
0x36ceb0  mulps %xmm5, %xmm1
0x36ceb3  mulps %xmm5, %xmm4
0x36ceb6  mulps %xmm5, %xmm2
0x36ceb9  mulps %xmm5, %xmm3
```

The next operations compute variance-like and covariance-like terms and clamp them non-negative:

```asm
0x36cebf  mulps %xmm5, %xmm5
0x36cec2  subps %xmm5, %xmm4
0x36cec8  maxps %xmm4, %xmm5
...
0x36ceda  mulps %xmm0, %xmm1
0x36cedd  subps %xmm1, %xmm3
0x36cee3  maxps %xmm3, %xmm1
```

The result is then scaled and clamped with constants decoded from the installed bundle:

| Address | Decoded float vector |
|---|---|
| `0x5fdc50` | `(0.01, 0.03, 0.03, 1.0)` |
| `0x5fdc60` | `(-0.8, -0.8, -0.8, -0.0)` |
| `0x5fdc70` | `(5.26315784, 5.26315784, 5.26315784, 1.0)` |
| `0x5a8920` | `(1.0, 1.0, 1.0, 1.0)` |

This proves a normalized, clamped patch-statistics scalar path. It does not, by itself, prove a public name such as "score".

### Transform And Weighted Reductions

After the first statistics stage, the body calls two internal helpers on the `r14` patch:

```asm
0x36cf28  movq %r14, %rdi
0x36cf2b  callq 0x371730
0x36cf30  movq %r14, %rdi
0x36cf33  callq 0x371a90
```

Then it runs absolute-value reductions, repeated patch-statistics blocks, and fixed transform-style arithmetic. The constant pool contains repeated four-lane constants including:

| Address | Decoded float vector |
|---|---|
| `0x5cbf80` | `0.707106769` repeated |
| `0x5cbf90` | `0.353553385` repeated |
| `0x5cbfa0` | `1.41421354` repeated |
| `0x5cbfb0` | `0.49999997` repeated |
| `0x5cbfd0` | `1.58613431` repeated |
| `0x5cbfe0` | `3.17226863` repeated |
| `0x5cbff0` | `-0.0529801175` repeated |
| `0x5cc000` | `-0.105960235` repeated |
| `0x5cc010` | `-0.882911086` repeated |
| `0x5cc020` | `-1.76582217` repeated |
| `0x5cc030` | `1.14960444` repeated |
| `0x5cc040` | `0.869864404` repeated |

The static evidence proves fixed weighted transform/reduction arithmetic. It does not prove a public transform family name.

### Return Value

Near function exit, `0x36cde0` computes the scalar returned in `xmm0`:

```asm
0x36e511  mulss %xmm1, %xmm0
0x36e515  sqrtss %xmm0, %xmm0
0x36e528  retq
```

Therefore, the third tuple field written by the caller is the square root of the product of two scalar quantities produced by the prior patch-statistics / transform-reduction path.

## Runtime Proof

The LLDB probe breaks at `0x369e7e`, the first tuple store. At that instruction:

- `xmm1` is the first tuple float loaded from `[rbp-0x4310]`
- `xmm0` is still the `0x36cde0` return scalar that will be stored at `0x369e91`
- `rax` and `rcx` are the live output tuple index/base registers

All four canonical zooms reached this site with readable `xmm0`.

Representative packets from one run:

| Zoom | Vector state | First float stack/register | Second float stack | `xmm0` scalar | Output tuple index base |
|---|---|---:|---:|---:|---:|
| `28mm` | `diff=640`, `npartners=1` | `19.22564125061035` | `19.22564125061035` | `0.0` | `66` |
| `35mm` | `diff=640`, `npartners=1` | `36.77948760986328` | `21.733333587646484` | `0.0` | `876` |
| `70mm` | `diff=640`, `npartners=1` | `19.24615478515625` | `-12.830769538879395` | `0.0` | `807` |
| `150mm` | `diff=1280`, `npartners=2` | `16.394872665405273` | `-14.256410598754883` | `0.0` | `33` |

Important precision note: first-hit packets are thread-scheduling dependent under LLDB. During the same investigation, earlier first-hit attempts observed different first tuple packets, including non-zero `xmm0` samples (`0.5421872138977051` at `35mm` and `0.9204061627388` at `150mm`). Do not promote any first-hit numeric tuple values as semantic constants or representative per-image values.

The stable runtime fact is register wiring: across the tested quartet, `xmm0` is live and readable at the tuple-write site, and the third tuple store at `0x369e91` writes that `xmm0` scalar.

## Proven Conclusions

The following are proven for the installed bundle and tested bridge HDR path:

- `0x36cde0` is called after the IRAMP refined path builds a 16x16 bilinear-resampled `vec4` patch.
- `0x36cde0` consumes two patch buffers: caller `rdi = rbp-0x4240`, caller `rsi = rbp-0x11a0`; callee keeps them as `r12` and `r14`.
- `0x36cde0` computes normalized patch sums, square sums, and cross products over 256 samples.
- `0x36cde0` computes non-negative variance-like and covariance-like terms and clamps/scales them with installed-bundle constants.
- `0x36cde0` then runs additional helper, absolute-reduction, fixed-transform, and weighted-accumulation stages before returning.
- The returned scalar is `sqrt(xmm0 * xmm1)` at `0x36e511..0x36e515`.
- At the caller's tuple write, `0x369e7e` writes the first stack float, `0x369e8b` writes the second stack float, and `0x369e91` writes the scalar returned by `0x36cde0`.

## Not Proven Here

- A public semantic name for the `0x36cde0` return scalar.
- A public semantic name for any of the three tuple fields.
- Whether a given first-hit tuple packet is representative of a render.
- How the three-float tuple is consumed downstream.
- Whether this scalar is the final anti-ghosting acceptance / rejection decision.
