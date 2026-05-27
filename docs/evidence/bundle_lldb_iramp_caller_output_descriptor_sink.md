# Bundle + LLDB IRAMP Caller Output Descriptor Sink Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib` and corrected canonical bridge HDR quartet.

This document bounds the caller-side destination that receives the `0x3e5720`
row-conversion output after IRAMP return, square-copy, vector-scale, and
row-callback conversion.

It proves:

- body `0x3ec960` is installed as slot `+0x30` of vtable/address point
  `0x65f5e0`
- `0x3ec960` computes the owner-backed destination descriptor as
  `(*rsi) + 0xf0`
- the body allocates/resizes that descriptor with element size `6`
- after the source path, square-copy, vector-scale, and `0x3e5720` conversion,
  the body destroys the temporary `rbp-0x70` descriptor and returns
- runtime packets at `28mm`, `35mm`, `70mm`, and `150mm` all show the
  owner-backed descriptor populated as `512x512`, stride `512`, with first
  bytes present after `0x3e5720`

It does not prove that `owner+0xf0` is final file output, display output, or the
last consumer-visible image. Downstream consumers and final acceptance /
rejection logic remain open.

## Inputs

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Tooling Boundary

Reusable probes live in the repo:

- `tools/lldb_probes/iramp_caller_output_descriptor_sink/output_descriptor_sink_probe.py`
- `tools/lldb_probes/iramp_caller_output_descriptor_sink/output_sink_28mm.lldb`
- `tools/lldb_probes/iramp_caller_output_descriptor_sink/output_sink_35mm.lldb`
- `tools/lldb_probes/iramp_caller_output_descriptor_sink/output_sink_70mm.lldb`
- `tools/lldb_probes/iramp_caller_output_descriptor_sink/output_sink_150mm.lldb`

Process output-path placeholders go under ignored
`runs/iramp_caller_output_descriptor_sink/`; the probe stops immediately after
`0x3e5720` returns and before render completion.

No probe harness for this evidence lives in `/private/tmp`.

## Static Proof

Installed bundle:
`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`.

The installed bundle stores `0x3ec960` at vtable/address-point `0x65f5e0`
slot `+0x30`:

```text
0x65f5e0 + 0x30 = 0x65f610
qword[0x65f610] = 0x3ec960
```

The constructor/copy-adjacent bodies at `0x3ec8f0` and `0x3ec920` install the
same address point `0x65f5e0`, tying `0x3ec960` to that callable family.

At entry, `0x3ec960` saves `rsi` as `r14`, reads the owner pointer from
`(*r14)`, and computes `owner+0xf0` as the destination descriptor pointer:

```asm
0x3ec972  movq  %rsi, %r14
0x3ec979  movl  $0xf0, %ebx
0x3ec97e  addq  (%r14), %rbx
```

The same body computes temporary dimensions through `0x3cffc0`, allocates /
resizes the owner-backed destination descriptor with element size `6`, then
builds the temporary source descriptor path:

```asm
0x3ec985  movq  %r12, %rdi
0x3ec988  movq  %r15, %rsi
0x3ec98b  movq  %r14, %rdx
0x3ec98e  callq 0x3cffc0
0x3ec993  movl  $0x6, %edx
0x3ec998  movq  %rbx, %rdi
0x3ec99b  movq  %r12, %rsi
0x3ec99e  callq 0xf540
```

After the branch-specific source path and post-square vector-scale helper, the
body re-derives the same `owner+0xf0` destination descriptor and passes it to
`0x3e5720`:

```asm
0x3ecaa4  callq 0x2d7320
0x3ecaa9  movq  (%r14), %rax
0x3ecaac  leaq  0xf0(%rax), %rdi
0x3ecaba  leaq  -0x70(%rbp), %rsi
0x3ecabe  callq 0x3e5720
0x3ecac3  leaq  -0x70(%rbp), %rdi
0x3ecac7  callq 0xf4e0
0x3ecadb  retq
```

Thus, within this body, no additional post-`0x3e5720` policy is visible before
return. The only visible operation after `0x3e5720` is destruction of the
temporary descriptor. This does not identify the later consumers of
`owner+0xf0`.

## Runtime Proof

The LLDB probes stop at `0x3ecac3`, immediately after `0x3e5720` returns and
before the temporary descriptor is destroyed. Runtime addresses are normalized
to installed-bundle VAs.

All four packets observed:

- stop site = `0x3ecac3`
- `output_descriptor == *(r14) + 0xf0`
- output descriptor dimensions = `512x512`
- output descriptor stride = `512`
- temporary descriptor at `rbp-0x70` is still live and has dimensions `512x512`
  immediately before destruction

First-hit values below are live memory samples, not stable semantic constants.

| Zoom | Temp first `vec4` before destroy | Owner `+0xf0` first 12 bytes after `0x3e5720` |
|---|---|---|
| `28mm` | `(0.390671372, 0.700535834, 0.447431713, 1.0)` | `40 36 9a 39 28 37 05 36 67 39 e8 36` |
| `35mm` | `(0.012593084, 0.025125448, 0.017090088, 1.0)` | `72 22 6e 26 60 24 4b 22 4b 26 47 24` |
| `70mm` | `(0.057570606, 0.107754953, 0.062299024, 1.0)` | `5e 2b e5 2e f9 2b 1d 2c dd 2f 71 2c` |
| `150mm` | `(0.309773713, 0.623812079, 0.432311058, 1.0)` | `f4 34 fd 38 ea 36 fd 34 06 39 f6 36` |

The owner-backed descriptor first bytes are consistent with the already proven
`0x38a30 -> 0xbfef0` float-channel to binary16 conversion shape. This proof
only establishes the storage sink for that conversion inside `0x3ec960`.

## Limits

This proof closes the immediate caller-side storage boundary for the converted
6-byte rows: they land in descriptor `owner+0xf0` for the observed
`0x3ec960 -> 0x3e5720` path.

It does not close:

- later consumers of `owner+0xf0`
- public channel or pixel-format names
- final file output or display semantics
- complete candidate acceptance / rejection or contributor-suppression logic
