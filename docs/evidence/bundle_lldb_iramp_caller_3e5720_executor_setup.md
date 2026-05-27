# Bundle + LLDB IRAMP Caller `0x3e5720` Executor Setup Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib` and corrected canonical bridge HDR quartet.

This document bounds the caller-side `0x3e5720` surface reached after the
post-square vector-scale helper.

It proves:

- `0x3e5720` is reached from the same caller-side path after `0x2d7320`
- `0x3e5720` resizes/allocates the destination descriptor with element size `6`
- it builds a stack callback object with vtable `0x66b020`
- it dispatches row chunks through generic executor `0x5670`
- its worker body reads source rows as 16-byte `vec4` elements and destination
  rows as 6-byte elements before calling row callback `0x38a30`
- the canonical four-zoom bridge HDR quartet all reach the executor setup with
  `512x512` source and destination descriptors

This proof did not itself decode the row callback. Follow-up evidence in
`bundle_lldb_iramp_row_callback_38a30_conversion.md` bounds the `0x38a30`
conversion math. Public pixel-format names, final file output, and final
acceptance / rejection logic remain open.

## Inputs

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Tooling Boundary

Reusable probes live in the repo:

- `tools/lldb_probes/iramp_caller_3e5720_executor_setup/executor_setup_probe.py`
- `tools/lldb_probes/iramp_caller_3e5720_executor_setup/executor_setup_28mm.lldb`
- `tools/lldb_probes/iramp_caller_3e5720_executor_setup/executor_setup_35mm.lldb`
- `tools/lldb_probes/iramp_caller_3e5720_executor_setup/executor_setup_70mm.lldb`
- `tools/lldb_probes/iramp_caller_3e5720_executor_setup/executor_setup_150mm.lldb`

Process output-path placeholders go under ignored
`runs/iramp_caller_3e5720_executor_setup/`; the probe stops before render
completion.

No probe harness for this evidence lives in `/private/tmp`.

## Static Proof

Installed bundle:
`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`.

The caller invokes `0x3e5720` immediately after `0x2d7320` and before destroying
the temporary descriptor:

```asm
0x3ecaa4  callq 0x2d7320
0x3ecaa9  movq  (%r14), %rax
0x3ecaac  leaq  0xf0(%rax), %rdi
0x3ecab3  testq %rax, %rax
0x3ecab6  cmoveq %rax, %rdi
0x3ecaba  leaq  -0x70(%rbp), %rsi
0x3ecabe  callq 0x3e5720
0x3ecac3  leaq  -0x70(%rbp), %rdi
0x3ecac7  callq 0xf4e0
```

The `0x3e5720` setup body resizes/allocates the destination descriptor from the
source dimensions with element size `6`, builds a stack callback object, and
dispatches executor `0x5670`:

```asm
0x3e5757  leaq  0x10(%r14), %rsi
0x3e575b  movl  $0x6, %edx
0x3e5760  movq  %rbx, %rdi
0x3e5763  callq 0xf540
...
0x3e5794  leaq  0x285885(%rip), %rax  ## 0x66b020
0x3e579b  movq  %rax, -0x60(%rbp)
0x3e579f  leaq  -0x68(%rbp), %rax
0x3e57a3  movq  %rax, -0x58(%rbp)
0x3e57a7  movq  %rbx, -0x50(%rbp)
0x3e57ab  movq  %r14, -0x48(%rbp)
0x3e57af  xorl  %edi, %edi
0x3e57b1  movq  %r15, %rcx
0x3e57b4  callq 0x5670
```

The worker body at `0x3e58c0` receives row ranges from `0x5670`. Its visible
loop computes a 6-byte destination row pointer and a 16-byte source row pointer,
then calls the row callback:

```asm
0x3e58e0  movq  0x8(%r14), %rax
0x3e58e4  movq  0x10(%r14), %rcx
0x3e58e8  movq  0x20(%rcx), %rdx
0x3e58ec  movslq 0x18(%rcx), %rcx
0x3e58f3  imulq %rbx, %rcx
0x3e58f7  leaq  (%rcx,%rcx,2), %rcx
0x3e58fb  leaq  (%rdx,%rcx,2), %rdi
0x3e58ff  movq  0x18(%r14), %rcx
0x3e5903  movslq 0x18(%rcx), %rsi
0x3e5907  imulq %rbx, %rsi
0x3e590b  shlq  $0x4, %rsi
0x3e590f  addq  0x20(%rcx), %rsi
0x3e5913  movl  0x10(%rcx), %edx
0x3e5916  callq *(%rax)
```

For this worker, the proven pointer roles are:

```text
dest_row = dest_data + row * dest_stride * 6
source_row = source_data + row * source_stride * 16
width = source_descriptor.width
```

The conversion row callback at `*(callback_aux_first_qword)` is `0x38a30`.
This setup proof identifies the callback target; follow-up evidence in
`bundle_lldb_iramp_row_callback_38a30_conversion.md` decodes the observed
conversion path.

## Runtime Proof

The LLDB probes stop at `0x3e57b4`, immediately before the generic executor
dispatch. Runtime addresses are normalized to installed-bundle VAs.

All four packets observed:

- `rip = 0x3e57b4`
- caller PC after return = `0x3ecac3`
- callback vtable = `0x66b020`
- callback auxiliary first qword = `0x38a30`
- executor range = `begin 0`, `end 512`, `chunk 128`
- destination descriptor = `512x512`, stride `512`
- source descriptor = `512x512`, stride `512`

The first source vector values below are first-hit samples. They prove live data
shape and source descriptor wiring, not stable semantic constants.

| Zoom | Source first `vec4` at setup | Destination first bytes before executor |
|---|---|---|
| `28mm` | `(0.287604839, 0.498429567, 0.298605084, 1.0)` | `00 00 00 00 00 00 00 00 00 00 00 00` |
| `35mm` | `(0.010645830, 0.023397928, 0.023048786, 1.000000119)` | `00 00 00 00 00 00 00 00 00 00 00 00` |
| `70mm` | `(0.069627538, 0.128437683, 0.072057061, 1.0)` | `95 01 95 01 9f 01 99 01 9a 01 98 01` |
| `150mm` | `(0.310946465, 0.625591695, 0.434180319, 1.0)` | `a9 98 93 41 82 d6 92 41 69 c2 d3 41` |

Destination first bytes are included only as observed memory state before the
executor runs. They are not interpreted as final output values.
