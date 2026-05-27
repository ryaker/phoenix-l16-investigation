# Bundle + LLDB IRAMP Tuple Post-Reciprocal Weighted-Add Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib` and corrected canonical bridge HDR quartet.

This document bounds the immediate path after the tuple-consumer scalar sum is
converted to a reciprocal.

It proves:

- the scalar sum is converted into a reciprocal packet at `0x36a934..0x36a93c`
- helper `0x19e7d0` is a SIMD scale/copy helper for descriptor-backed `vec4`
  image buffers
- the caller uses that helper with a broadcast reciprocal vector at `0x36a94a..0x36a974`
- after the helper returns, the caller blends `reciprocal * 0.2` into lane 3
  of each normalized `vec4`
- `0x36aa30..0x36aa57` performs a separable weight-table product, multiplies
  the blended `vec4`, adds the destination `vec4`, and stores the result
- the canonical four-zoom bridge HDR quartet all reach this post-reciprocal
  weighted-add site

It does not prove public field names, public weight semantics, non-first-hit
representativeness, complete later downstream policy after the weighted-add
loop, or final ghost-suppression acceptance / rejection.

## Inputs

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Tooling Boundary

Reusable probes live in the repo:

- `tools/lldb_probes/iramp_tuple_post_reciprocal_weighted_add/post_recip_add_probe.py`
- `tools/lldb_probes/iramp_tuple_post_reciprocal_weighted_add/post_recip_add_first_28mm.lldb`
- `tools/lldb_probes/iramp_tuple_post_reciprocal_weighted_add/post_recip_add_first_35mm.lldb`
- `tools/lldb_probes/iramp_tuple_post_reciprocal_weighted_add/post_recip_add_first_70mm.lldb`
- `tools/lldb_probes/iramp_tuple_post_reciprocal_weighted_add/post_recip_add_first_150mm.lldb`

Generated render outputs go under ignored
`runs/iramp_tuple_post_reciprocal_weighted_add/`.

No probe harness for this evidence lives in `/private/tmp`.

## Static Proof

Installed bundle:
`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`.

### Reciprocal Packet And Scale/Copy Helper

The first downstream tuple-consumer proof already bounds the loop that adds the
third tuple scalar into a running scalar sum. Immediately after that loop, the
scalar sum is broadcast, converted to a scalar reciprocal, and stored on stack:

```asm
0x36a934  shufps $0x0, %xmm2, %xmm2
0x36a938  rcpss  %xmm2, %xmm2
0x36a93c  movaps %xmm2, -0x42f0(%rbp)
```

The caller then broadcasts the reciprocal low lane and passes it to `0x19e7d0`
through a wrapper at `rbp-0x11d0`:

```asm
0x36a943  movaps %xmm2, %xmm0
0x36a946  shufps $0x0, %xmm0, %xmm0
0x36a94a  leaq   -0x1250(%rbp), %rdi
0x36a951  movq   %rdi, -0x11d0(%rbp)
0x36a958  movaps %xmm0, -0x11c0(%rbp)
0x36a95f  leaq   -0x11d0(%rbp), %rax
0x36a966  movq   %rax, -0x11a8(%rbp)
0x36a96d  leaq   -0x11a8(%rbp), %rsi
0x36a974  callq  0x19e7d0
```

Static inspection of `0x19e7d0` shows repeated `vec4` loads from a source
descriptor, multiplication by the wrapper vector at `wrapper+0x10`, and stores
to the destination descriptor. Representative bodies:

```asm
0x19e8df  movaps 0x10(%rax), %xmm0
...
0x19e910  movaps -0x10(%rdx), %xmm1
0x19e914  mulps  %xmm0, %xmm1
0x19e917  movaps %xmm1, -0x10(%rdi)
0x19e91b  movaps (%rdx), %xmm1
0x19e91e  mulps  %xmm0, %xmm1
0x19e921  movaps %xmm1, (%rdi)
```

The later unrolled loops continue the same load / `mulps` / store pattern and
return normally at `0x19eb5f`.

### Post-Helper Weighted Add

After `0x19e7d0` returns, the caller prepares a vector whose lane 3 is
`reciprocal * 0.2`:

```asm
0x36a9b5  movaps -0x42f0(%rbp), %xmm4
0x36a9bc  mulss  0x5df904(%rip), %xmm4
0x36a9c4  shufps $0x24, %xmm4, %xmm4
```

`0x5df904` is the already-verified `0.200000003` constant.

The add loop loads a normalized source `vec4`, replaces lane 3 with lane 3 of
`xmm4`, multiplies by a separable weight product loaded from the table at
`*(r13+0x28)`, adds the destination `vec4`, and stores back:

```asm
0x36aa30  movaps (%r10,%rdi), %xmm0
0x36aa35  blendps $0x8, %xmm4, %xmm0
0x36aa3b  movq   0x28(%r13), %rax
0x36aa3f  movq   (%rax), %rax
0x36aa42  movss  (%rax,%rdx,4), %xmm1
0x36aa47  mulss  (%rax,%rcx,4), %xmm1
0x36aa4c  shufps $0x0, %xmm1, %xmm1
0x36aa50  mulps  %xmm0, %xmm1
0x36aa53  addps  (%rsi,%rdi), %xmm1
0x36aa57  movaps %xmm1, (%rsi,%rdi)
```

For this instruction window, the proven arithmetic is:

```text
blended = (normalized.x, normalized.y, normalized.z, reciprocal * 0.2)
weight_product = weight[inner_index] * weight[outer_index]
dest_after = dest_before + weight_product * blended
```

Do not promote `weight[]` to a public kernel name here; only the table access
and arithmetic are proven.

## Runtime Proof

The LLDB probe breaks at `0x36aa30`, before the `movaps` / `blendps` /
weight-product add loop. It captures:

- the reciprocal stack packet at `rbp-0x42f0`
- the live `xmm4` value before the lane-3 blend
- source `vec4` before blend
- destination `vec4` before add
- the two table weights selected by `rdx` and `rcx`
- the script-computed `dest_after` implied by the static instruction sequence

The first captured hit in each run is a baseline-sum packet with reciprocal
`5.0` and scalar sum `0.2`. These first-hit numeric samples prove liveness and
instruction-window arithmetic; they are not semantic constants and are not
claimed to represent every later tile.

### Four-Zoom Packets

| Zoom | Dimension | Source row stride | Dest row stride | Reciprocal packet | `xmm4` before blend |
|---|---:|---:|---:|---|---|
| `28mm` | `40` | `640` | `9344` | `(5.0, 0.200000003, 0.200000003, 0.200000003)` | `(1.0, 0.200000003, 0.200000003, 1.0)` |
| `35mm` | `40` | `640` | `9328` | `(5.0, 0.200000003, 0.200000003, 0.200000003)` | `(1.0, 0.200000003, 0.200000003, 1.0)` |
| `70mm` | `34` | `544` | `9056` | `(5.0, 0.200000003, 0.200000003, 0.200000003)` | `(1.0, 0.200000003, 0.200000003, 1.0)` |
| `150mm` | `34` | `544` | `9056` | `(5.0, 0.200000003, 0.200000003, 0.200000003)` | `(1.0, 0.200000003, 0.200000003, 1.0)` |

| Zoom | Source before blend | Weight product | Predicted destination after add |
|---|---|---:|---|
| `28mm` | `(0.160464257, 0.0, 0.0, 0.0)` | `0.000002375748452` | `(0.000000381222710, 0.0, 0.0, 0.000002375748452)` |
| `35mm` | `(0.362024784, 0.0, 0.0, 0.0)` | `0.000002375748452` | `(0.000000860079820, 0.0, 0.0, 0.000002375748452)` |
| `70mm` | `(0.160464257, 0.0, 0.0, 0.0)` | `0.000004549358011` | `(0.000000730009353, 0.0, 0.0, 0.000004549358011)` |
| `150mm` | `(-0.188274205, 0.0, 0.0, 0.0)` | `0.000004549358011` | `(-0.000000856526762, 0.0, 0.0, 0.000004549358011)` |

The selected first-hit scalar weights were:

- `28mm` / `35mm`: `0.001541346312 * 0.001541346312`
- `70mm` / `150mm`: `0.002132922411 * 0.002132922411`

## Proven Conclusions

The following are proven for the installed bundle and tested bridge HDR path:

- The tuple-consumer running scalar sum feeds an immediate reciprocal at
  `0x36a934..0x36a93c`.
- The reciprocal is passed to `0x19e7d0`, whose visible body copies/scales
  descriptor-backed `vec4` buffers by a broadcast vector.
- The post-helper add loop replaces lane 3 of the normalized source vector with
  `reciprocal * 0.2`.
- The post-helper add loop then applies
  `weight[inner_index] * weight[outer_index]` and accumulates into the
  destination vector.
- The post-reciprocal weighted-add site is runtime-observed on the canonical
  `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR quartet.

## Not Proven Here

- Public semantic names for the tuple fields.
- Public semantic names for the weight table.
- That the first-hit baseline packet is representative of later non-baseline
  tiles.
- Complete downstream policy after `0x36aa57`.
- The complete candidate predicate.
- Final contributor acceptance / rejection or ghost-suppression policy.
