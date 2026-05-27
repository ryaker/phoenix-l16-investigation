# Bundle + LLDB IRAMP Caller Square-Copy Handoff Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib` and corrected canonical bridge HDR quartet.

This document bounds the caller-side handoff immediately after IRAMP returns to
the visible wrapper function at `0x3ec770`.

It proves:

- after `0x365960` returns, the caller validates the IRAMP-return descriptor
  dimensions against the ROI width and height
- the caller wraps the IRAMP-return descriptor at stack address `rbp-0x60` with
  a one-pointer stack wrapper at `rbp-0x88`
- the caller passes that wrapper and the saved destination descriptor into
  helper `0xd76a0` at call site `0x3ec80f`
- static inspection of `0xd76a0` shows it allocates/resizes the destination from
  the source descriptor dimensions, then copies source `vec4` lanes into the
  destination after squaring each lane
- the canonical four-zoom bridge HDR quartet all reach the handoff with
  `512x512` source descriptors matching their live ROI dimensions

It does not prove that this destination is the final rendered image, does not
name the squared values as gamma / color / exposure semantics, and does not
close downstream acceptance / rejection logic.

## Inputs

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Tooling Boundary

Reusable probes live in the repo:

- `tools/lldb_probes/iramp_caller_square_copy/square_copy_probe.py`
- `tools/lldb_probes/iramp_caller_square_copy/square_copy_handoff_28mm.lldb`
- `tools/lldb_probes/iramp_caller_square_copy/square_copy_handoff_35mm.lldb`
- `tools/lldb_probes/iramp_caller_square_copy/square_copy_handoff_70mm.lldb`
- `tools/lldb_probes/iramp_caller_square_copy/square_copy_handoff_150mm.lldb`

Process output-path placeholders go under ignored `runs/iramp_caller_square_copy/`;
the probe stops before render completion.

No probe harness for this evidence lives in `/private/tmp`.

## Static Proof

Installed bundle:
`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`.

The caller initializes the stack descriptor, invokes IRAMP, checks the returned
descriptor dimensions against the ROI, then wraps and forwards the descriptor:

```asm
0x3ec7d0  leaq  -0x60(%rbp), %r14
0x3ec7d4  movq  %r14, %rdi
0x3ec7d7  movq  %rbx, %r9
0x3ec7da  callq 0x365960
0x3ec7df  movl  0x8(%rbx), %ecx
0x3ec7e2  subl  (%rbx), %ecx
0x3ec7e4  movq  -0x50(%rbp), %rax
0x3ec7e8  cmpl  %ecx, %eax
0x3ec7ea  jne   0x3ec86a
0x3ec7ec  movl  0xc(%rbx), %ecx
0x3ec7ef  subl  0x4(%rbx), %ecx
0x3ec7f2  shrq  $0x20, %rax
0x3ec7f6  cmpl  %ecx, %eax
0x3ec7f8  jne   0x3ec86a
0x3ec7fa  leaq  -0x60(%rbp), %rax
0x3ec7fe  movq  %rax, -0x88(%rbp)
0x3ec805  leaq  -0x88(%rbp), %rsi
0x3ec80c  movq  %r15, %rdi
0x3ec80f  callq 0xd76a0
```

Helper `0xd76a0` receives:

```text
rdi = destination descriptor
rsi = pointer to wrapper whose first qword points to the source descriptor
```

Its prologue reads source width and height from the wrapped descriptor and
resizes/allocates the destination with element size `0x10`:

```asm
0xd76bf  movq  (%rsi), %rax
0xd76c2  movl  0x10(%rax), %ecx
0xd76c5  movl  0x14(%rax), %eax
0xd76c8  movl  %ecx, -0x30(%rbp)
0xd76cb  movl  %eax, -0x2c(%rbp)
0xd76ce  leaq  -0x30(%rbp), %rsi
0xd76d2  movl  $0x10, %edx
0xd76d7  callq 0xf540
```

The visible vector-copy loops square every source lane before storing to the
destination. One unrolled body is:

```asm
0xd77d0  movaps -0x10(%rdx), %xmm0
0xd77d4  mulps  %xmm0, %xmm0
0xd77d7  movaps %xmm0, -0x10(%rdi)
0xd77db  movaps (%rdx), %xmm0
0xd77de  mulps  %xmm0, %xmm0
0xd77e1  movaps %xmm0, (%rdi)
```

Equivalent scalar/tail and four-vector bodies appear at `0xd7840..0xd7846`,
`0xd7880..0xd78aa`, `0xd7970..0xd7977`, and `0xd79b0..0xd79d7`.

## Runtime Proof

The LLDB probes stop at `0x3ec80f`, immediately before the helper call. All four
packets observed:

- `rsi == rbp-0x88`
- `*(uint64_t *)rsi == rbp-0x60`
- `rdi == r15`
- source descriptor dimensions equal the live ROI width and height
- destination descriptor fields are zero before `0xd76a0` allocates/resizes it

The first source vector values below are first-hit samples. They prove live data
shape and the helper's visible arithmetic input, not semantic constants.

| Zoom | ROI rect | Source descriptor | First source `vec4` | Squared `vec4` |
|---|---|---|---|---|
| `28mm` | `(0,0,512,512)` | `512x512`, stride `512` | `(0.540089786, 0.542212665, 0.530203164, 1.0)` | `(0.291696977, 0.293994574, 0.281115395, 1.0)` |
| `35mm` | `(512,512,1024,1024)` | `512x512`, stride `512` | `(0.063104495, 0.067124628, 0.066357106, 1.0)` | `(0.003982177, 0.004505716, 0.004403266, 1.0)` |
| `70mm` | `(0,0,512,512)` | `512x512`, stride `512` | `(0.295040578, 0.298041672, 0.283286601, 1.0)` | `(0.087048942, 0.088828838, 0.080251298, 1.0)` |
| `150mm` | `(2048,1536,2560,2048)` | `512x512`, stride `512` | `(0.703140795, 0.755193651, 0.800139964, 1.0)` | `(0.494406978, 0.570317450, 0.640223961, 1.0)` |

The runtime packets therefore prove the handoff for `28mm`, `35mm`, `70mm`, and
`150mm`. They do not prove anything about later consumers after the helper
returns.
