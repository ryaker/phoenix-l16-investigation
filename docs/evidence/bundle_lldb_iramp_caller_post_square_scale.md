# Bundle + LLDB IRAMP Caller Post-Square Vector-Scale Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib` and corrected canonical bridge HDR quartet.

This document bounds the caller-side handoff immediately after the IRAMP
caller's square-copy helper and before the later `0x3e5720` executor/setup
surface.

It proves:

- after the branch that can call the IRAMP wrapper at `0x3ec770`, the caller
  builds a one-descriptor wrapper over the descriptor at `rbp-0x70`
- the same wrapper includes a four-float vector at wrapper offset `+0x10`
- the caller passes `rdi = rbp-0x70` and `rsi = rbp-0xb0` into helper `0x2d7320`
  at call site `0x3ecaa4`
- static inspection of `0x2d7320` shows it allocates/resizes the destination
  from the source descriptor dimensions, then multiplies source `vec4` lanes by
  the wrapper vector and stores the result to the destination
- the canonical four-zoom bridge HDR quartet all reach this handoff with a
  `512x512` descriptor and `source_desc_from_wrapper == destination_descriptor`

It does not prove public semantics for the four-float vector, does not prove
that this descriptor is the final rendered image, and does not close the later
`0x3e5720` executor/setup surface or final acceptance / rejection logic.

## Inputs

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Tooling Boundary

Reusable probes live in the repo:

- `tools/lldb_probes/iramp_caller_post_square_scale/post_square_scale_probe.py`
- `tools/lldb_probes/iramp_caller_post_square_scale/post_square_scale_28mm.lldb`
- `tools/lldb_probes/iramp_caller_post_square_scale/post_square_scale_35mm.lldb`
- `tools/lldb_probes/iramp_caller_post_square_scale/post_square_scale_70mm.lldb`
- `tools/lldb_probes/iramp_caller_post_square_scale/post_square_scale_150mm.lldb`

Process output-path placeholders go under ignored
`runs/iramp_caller_post_square_scale/`; the probe stops before render
completion.

No probe harness for this evidence lives in `/private/tmp`.

## Static Proof

Installed bundle:
`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`.

The visible caller path builds a vector after the branch that may call
`0x3ec770`:

```asm
0x3eca46  callq 0x3ec770
0x3eca4b  movq  0x170(%r15), %rax
0x3eca52  movq  (%rax), %rsi
0x3eca55  leaq  -0xc0(%rbp), %rdi
0x3eca5c  callq 0x1bea20
0x3eca61  movss -0xc0(%rbp), %xmm0
0x3eca69  movss -0xb8(%rbp), %xmm1
0x3eca71  insertps $0x10, -0xbc(%rbp), %xmm0
0x3eca7b  insertps $0x20, %xmm1, %xmm0
0x3eca81  insertps $0x30, 0x1bb69d(%rip), %xmm0
0x3eca8b  leaq  -0x70(%rbp), %rdi
0x3eca8f  movq  %rdi, -0xb0(%rbp)
0x3eca96  movaps %xmm0, -0xa0(%rbp)
0x3eca9d  leaq  -0xb0(%rbp), %rsi
0x3ecaa4  callq 0x2d7320
```

Helper `0x1bea20` copies three 32-bit fields from the object passed in `rsi`:

```asm
0x1bea24  movl 0x74(%rsi), %eax
0x1bea27  movl %eax, (%rdi)
0x1bea29  movl 0x78(%rsi), %eax
0x1bea2c  movl %eax, 0x4(%rdi)
0x1bea2f  movl 0x7c(%rsi), %eax
0x1bea32  movl %eax, 0x8(%rdi)
```

Do not assign public names to those fields here; this proof only establishes
the caller-side data movement and vector construction.

Helper `0x2d7320` has the same descriptor-allocation shape as the prior
square-copy helper, but its copy loops multiply by the vector at wrapper
offset `+0x10`:

```asm
0x2d733f  movq  (%rsi), %rax
0x2d7342  movl  0x10(%rax), %ecx
0x2d7345  movl  0x14(%rax), %eax
0x2d734e  leaq  -0x30(%rbp), %rsi
0x2d7352  movl  $0x10, %edx
0x2d7357  callq 0xf540
```

One unrolled vector body:

```asm
0x2d742c  movaps 0x10(%rsi), %xmm0
0x2d7460  movaps -0x10(%rbx), %xmm1
0x2d7464  mulps  %xmm0, %xmm1
0x2d7467  movaps %xmm1, -0x10(%rdi)
0x2d746b  movaps (%rbx), %xmm1
0x2d746e  mulps  %xmm0, %xmm1
0x2d7471  movaps %xmm1, (%rdi)
```

Equivalent scalar/tail and four-vector bodies appear at `0x2d74d0..0x2d74d6`,
`0x2d7510..0x2d753a`, `0x2d7610..0x2d7617`, and `0x2d7650..0x2d7677`.

For this helper, the proven arithmetic is:

```text
dest_vec4 = source_vec4 * wrapper_vec4
```

## Runtime Proof

The LLDB probes stop at `0x3ecaa4`, immediately before the `0x2d7320` helper
call. All four packets observed:

- `source_desc_from_wrapper == destination_descriptor`
- descriptor dimensions are `512x512`
- descriptor stride is `512`
- wrapper offset `+0x10` contains the vector consumed by `0x2d7320`

The first source vector values below are first-hit samples. They prove live data
shape and helper input, not stable semantic constants.

| Zoom | Wrapper vector | First source `vec4` | Predicted first `vec4` after helper |
|---|---|---|---|
| `28mm` | `(0.582126737, 1.0, 0.629390538, 1.0)` | `(0.494058788, 0.498429567, 0.474435270, 1.0)` | `(0.287604830, 0.498429567, 0.298605070, 1.0)` |
| `35mm` | `(0.581704795, 1.0, 0.624196708, 1.0)` | `(0.322386146, 0.314022005, 0.283436060, 1.0)` | `(0.187533567, 0.314022005, 0.176919856, 1.0)` |
| `70mm` | `(0.551634431, 1.0, 0.631660402, 1.0)` | `(0.126229852, 0.128427640, 0.114073604, 1.0)` | `(0.069632733, 0.128427640, 0.072055779, 1.0)` |
| `150mm` | `(0.567012906, 1.0, 0.624709785, 1.0)` | `(0.454739094, 0.520894289, 0.578509688, 1.0)` | `(0.257842935, 0.520894289, 0.361400663, 1.0)` |

The runtime packets therefore prove the handoff for `28mm`, `35mm`, `70mm`, and
`150mm`. They do not prove anything about `0x3e5720` or later consumers after
`0x2d7320` returns.
