# Bundle + LLDB IRAMP `0x36e530` Accumulator-Prep Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib` and corrected canonical bridge HDR quartet.

This document narrows the function called immediately before the proven IRAMP
weighted accumulator at `0x369fa1..0x369fa8`.

It proves:

- `0x36e530` is called with the local IRAMP scratch buffer at `rbp-0x4240`
- after `0x36e530`, `rax` points to `scratch+0x1580` on all four canonical focal seeds
- the accumulator consumes that returned source-vector block with a 16-by-16 outer product of scalar weights from `rbp-0xa0`
- this is accumulator preparation / weighting, not final merge acceptance or rejection logic

It does not prove a public semantic name for the weights, a formula for their
generation, downstream tuple consumption, or final contributor acceptance /
rejection.

## Inputs

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Tooling Boundary

Reusable probes live in the repo:

- `tools/lldb_probes/iramp_36e530_accumulator_prep/prep_probe.py`
- `tools/lldb_probes/iramp_36e530_accumulator_prep/prep_first_28mm.lldb`
- `tools/lldb_probes/iramp_36e530_accumulator_prep/prep_first_35mm.lldb`
- `tools/lldb_probes/iramp_36e530_accumulator_prep/prep_first_70mm.lldb`
- `tools/lldb_probes/iramp_36e530_accumulator_prep/prep_first_150mm.lldb`

Generated render outputs go under ignored
`runs/iramp_36e530_accumulator_prep/`.

No probe harness for this evidence lives in `/private/tmp`.

## Static Proof

Installed bundle:
`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`.

### Caller Wiring

The local IRAMP path calls `0x36e530` with the same scratch base previously
used by the refined tuple path:

```asm
0x369f2d  leaq -0x4240(%rbp), %rdi
0x369f34  callq 0x36e530
```

Immediately after the call, the path computes the destination vector address
and enters the already-proven weighted accumulator:

```asm
0x369f80  movss -0xa0(%rbp,%rsi,4), %xmm0
0x369f89  movq  %rax, %rdi
0x369f90  movss -0xa0(%rbp,%rcx), %xmm1
0x369f99  mulss %xmm0, %xmm1
0x369f9d  shufps $0x0, %xmm1, %xmm1
0x369fa1  mulps (%rdi), %xmm1
0x369fa4  addps (%rdx,%rcx,4), %xmm1
0x369fa8  movaps %xmm1, (%rdx,%rcx,4)
```

The loop shape is fixed:

```asm
0x369fac  addq $0x4, %rcx
0x369fb0  addq $0x10, %rdi
0x369fb4  cmpq $0x40, %rcx
0x369fb8  jne  0x369f90
0x369fba  incq %rsi
0x369fbd  addq $0x100, %rax
0x369fc3  addq %r8, %rdx
0x369fc6  cmpq $0x10, %rsi
0x369fca  jne  0x369f80
```

Therefore, the accumulator is a 16-row by 16-column `vec4` source traversal.
For each row and column it multiplies `source_vec4` by
`weight[row] * weight[col]`, adds the current destination `vec4`, and stores the
result.

### `0x36e530` Shape

`0x36e530` begins by replacing five `vec4` slots with reciprocal
approximations:

```asm
0x36e530  rcpps  0x2580(%rdi), %xmm0
0x36e537  movaps %xmm0, 0x2580(%rdi)
0x36e53e  rcpps  0x2590(%rdi), %xmm0
0x36e545  movaps %xmm0, 0x2590(%rdi)
0x36e54c  rcpps  0x25a0(%rdi), %xmm0
0x36e553  movaps %xmm0, 0x25a0(%rdi)
0x36e55a  rcpps  0x25b0(%rdi), %xmm0
0x36e561  movaps %xmm0, 0x25b0(%rdi)
0x36e568  rcpps  0x25c0(%rdi), %xmm0
0x36e56f  movaps %xmm0, 0x25c0(%rdi)
```

It then uses selector bytes near `rdi+0x25d0` to choose those reciprocal
vectors and multiply a `16x16` block beginning near `rdi+0x1580`:

```asm
0x36e576  leaq   0x25d1(%rdi), %r8
0x36e57d  leaq   0x1590(%rdi), %r9
0x36e5a0  movzbl -0x1(%rax), %edx
0x36e5a4  shlq   $0x4, %rdx
0x36e5a8  movaps 0x2580(%rdi,%rdx), %xmm0
0x36e5b0  mulps  -0x10(%rcx), %xmm0
0x36e5b4  movaps %xmm0, -0x10(%rcx)
0x36e5b8  movzbl (%rax), %edx
0x36e5bb  shlq   $0x4, %rdx
0x36e5bf  movaps 0x2580(%rdi,%rdx), %xmm0
0x36e5c7  mulps  (%rcx), %xmm0
0x36e5ca  movaps %xmm0, (%rcx)
```

Later, the function explicitly sets `rax` to `rdi+0x1580`:

```asm
0x36ed01  leaq 0x1580(%rdi), %rax
0x36ed08  xorl %ecx, %ecx
0x36ed0a  movq %rax, %rdx
```

The visible body then performs fixed SIMD transform/reduction stages over
scratch offsets including `0x1580`, `0x1680`, `0x1780`, `0x1880`, `0x1980`,
`0x1a80`, `0x1b80`, `0x1c80`, `0x1d80`, `0x1e80`, `0x1f80`, `0x2080`,
`0x2180`, `0x2280`, `0x2380`, `0x2480`, and `0x2580`, and returns at
`0x36f7f3`.

The static evidence proves reciprocal/selector normalization plus in-place
fixed SIMD transform/reduction work. It does not prove a public transform family
name.

## Runtime Proof

The LLDB probe breaks at `0x369f80`, after `0x36e530` returns and before the
first accumulator row begins. It captures:

- `scratch_base = rbp - 0x4240`
- `source_ptr_rax`
- `source_offset_from_scratch`
- destination pointer and row stride
- the 16 scalar weights at `rbp-0xa0`
- first source and destination `vec4` samples

All four canonical zooms reached this site cleanly.

### Shared Weight Table

Every first-hit packet captured the same 16 scalar weights:

| Index | Weight |
|---:|---:|
| `0` | `0.009607374668121338` |
| `1` | `0.08426520228385925` |
| `2` | `0.22221490740776062` |
| `3` | `0.4024548828601837` |
| `4` | `0.5975451469421387` |
| `5` | `0.7777851819992065` |
| `6` | `0.9157348275184631` |
| `7` | `0.9903926849365234` |
| `8` | `0.9903926253318787` |
| `9` | `0.9157347679138184` |
| `10` | `0.7777850031852722` |
| `11` | `0.5975452065467834` |
| `12` | `0.40245479345321655` |
| `13` | `0.22221478819847107` |
| `14` | `0.08426520228385925` |
| `15` | `0.00960734486579895` |

The first scalar multiplier in the accumulator is
`weight[0] * weight[0] = 9.230164801365959e-05`.

### Four-Zoom Packets

| Zoom | `source_offset_from_scratch` | Destination row stride | First source `vec4` | First destination `vec4` before add |
|---|---:|---:|---|---|
| `28mm` | `5504` / `0x1580` | `3712` | `(0.0, 0.0, 0.0, 0.0)` | `(0.0, 0.0, 0.0, 0.0)` |
| `35mm` | `5504` / `0x1580` | `3712` | `(0.13831640779972076, -0.0023205720353871584, -0.003501236205920577, 1.0)` | `(0.0, 0.0, 0.0, 0.0)` |
| `70mm` | `5504` / `0x1580` | `4224` | `(0.0, 0.0, 0.0, 0.0)` | `(0.0, 0.0, 0.0, 0.0)` |
| `150mm` | `5504` / `0x1580` | `4224` | `(1.3246468305587769, -0.06681302934885025, -0.0030051462817937136, 1.0)` | `(0.0, 0.0, 0.0, 0.0)` |

The source and destination vector values are first-hit samples. They are not
semantic constants and must not be treated as representative image values. The
stable runtime fact is the pointer/weight/loop wiring.

## Proven Conclusions

The following are proven for the installed bundle and tested bridge HDR path:

- `0x36e530` is live immediately before the known IRAMP weighted accumulator.
- `0x36e530` receives caller `rdi = rbp-0x4240`.
- `0x36e530` performs reciprocal/selector normalization and fixed SIMD
  transform/reduction work over the local scratch region.
- On the canonical four-zoom first-hit packets, `0x36e530` returns a source
  pointer in `rax` equal to `scratch_base + 0x1580`.
- The caller copies that returned pointer into `rdi` at `0x369f89`.
- The accumulator at `0x369fa1..0x369fa8` multiplies each source `vec4` by
  `weight[row] * weight[column]`, adds the destination `vec4`, and stores the
  result.
- The 16 scalar weights listed above were captured identically in first-hit
  packets for `28mm`, `35mm`, `70mm`, and `150mm`.

## Not Proven Here

- A public semantic name for `0x36e530`.
- A public semantic name or generation formula for the 16 weights.
- Whether first-hit source-vector samples are representative.
- Downstream consumption of the three-float refined tuple.
- The complete upstream candidate predicate.
- Final contributor acceptance / rejection or ghost-suppression policy.
