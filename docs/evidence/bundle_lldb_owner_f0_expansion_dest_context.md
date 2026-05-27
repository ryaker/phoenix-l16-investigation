# Bundle + LLDB Owner `+0xf0` Expansion Destination Context Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib` and corrected canonical bridge HDR quartet.

This document bounds the destination backing store used by the immediate
owner `+0xf0` expansion handoff at `0x3d4e10 -> 0x3d50f0`.

It proves:

- `0x3d4e10` receives a caller-provided context whose field `+0x10` points to
  a persistent destination descriptor
- the local expanded descriptor at `rbp-0x90` is a clipped view into that
  context destination descriptor
- the local view and context descriptor share the same `qword_28` backing base
- the local view's data pointer is inside the context descriptor's 16-byte
  element backing span
- the proof holds at `28mm`, `35mm`, `70mm`, and `150mm`

It does not prove final file output, display output, public pixel-format names,
or final merge acceptance / rejection policy.

## Inputs

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Tooling Boundary

Reusable probes live in the repo:

- `tools/lldb_probes/owner_f0_expansion_dest_context/owner_f0_expansion_dest_context_probe.py`
- `tools/lldb_probes/owner_f0_expansion_dest_context/owner_f0_dest_context_28mm.lldb`
- `tools/lldb_probes/owner_f0_expansion_dest_context/owner_f0_dest_context_35mm.lldb`
- `tools/lldb_probes/owner_f0_expansion_dest_context/owner_f0_dest_context_70mm.lldb`
- `tools/lldb_probes/owner_f0_expansion_dest_context/owner_f0_dest_context_150mm.lldb`

Process output-path placeholders go under ignored
`runs/owner_f0_expansion_dest_context/`. No probe harness for this evidence
lives in `/private/tmp`.

## Static Proof

Installed bundle:
`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`.

The caller-side dispatcher at `0x3d47d0` calls `0x3d4e10` with `rdi` loaded
from the callback object's output context and `rsi` pointing at the source
shared-ptr-like pair:

```asm
0x3d4842  movq 0x10(%r14), %rdi
0x3d4846  leaq -0x30(%rbp), %rsi
0x3d484a  callq 0x3d4e10
...
0x3d4864  movq 0x10(%r14), %rdi
0x3d4868  leaq -0x30(%rbp), %rsi
0x3d486c  callq 0x3d4e10
```

Inside `0x3d4e10`, `rsi` supplies the source object. The source descriptor view
at `rbp-0x60` is built from that source object's `+0xf0` descriptor and
`+0x110` data pointer. The destination side is different: `0x3d4e10` reads
`[rdi+0x10]` and builds the local expanded descriptor at `rbp-0x90` as a view
into that caller-provided destination descriptor:

```asm
0x3d4e24  movq (%rsi), %r15
...
0x3d4ed7  movq 0x110(%r15), %r13
...
0x3d4f1a  leaq (%r13,%rax,2), %rax
0x3d4f26  movq %rax, -0x40(%rbp)
0x3d4f2a  movq %rdx, -0x38(%rbp)
...
0x3d4f49  movq 0x10(%rdi), %rdx
...
0x3d4fb0  addq 0x20(%rdx), %rsi
0x3d4fb4  movq 0x28(%rdx), %rdx
...
0x3d4fef  movq %rsi, -0x70(%rbp)
0x3d4ff3  movq %rdx, -0x68(%rbp)
0x3d501e  leaq -0x90(%rbp), %rdi
0x3d5025  leaq -0x60(%rbp), %rsi
0x3d5029  callq 0x3d50f0
```

`0x3d50f0` then allocates/resizes the local destination descriptor for
`16`-byte elements and dispatches the row worker through `0x5670`. The local
descriptor is destroyed after return, but the backing store belongs to the
caller-provided context descriptor, not to the stack wrapper.

## Runtime Proof

The LLDB probe stops first at `0x3ecac3`, records the exact owner `+0xf0`
descriptor and data range, then traps the first `0x3d4e10` entry whose source
pair points to that same owner. It records the caller context's destination
descriptor pointer from `context+0x10`, then accepts a `0x3d502e` handoff only
on the same thread and only when the source descriptor still points inside the
exact owner `+0xf0` range.

All accepted handoff packets observed:

- source descriptor `rbp-0x60` data pointer is inside the captured owner
  `+0xf0` range
- source offset modulo `6` is `0`
- destination view descriptor `rbp-0x90` data pointer is inside the context
  destination descriptor backing span
- destination view offset modulo `16` is `0`
- destination view `qword_28` matches context destination descriptor `qword_28`
- destination view first `vec4` sample has lane 3 = `1.0`

First-hit values below are live memory samples and offsets, not stable semantic
constants.

| Zoom | Context destination descriptor | Local destination view | Destination view offset bytes | Source offset bytes | Expanded first `vec4` |
|---|---:|---:|---:|---:|---|
| `28mm` | `464x436`, stride `464` | `132x436`, stride `464` | `0` | `2280` | `[0.21630859375, 0.36767578125, 0.2122802734375, 1.0]` |
| `35mm` | `463x464`, stride `463` | `144x215`, stride `463` | `0` | `914592` | `[0.004192352294921875, 0.00809478759765625, 0.004558563232421875, 1.0]` |
| `70mm` | `543x518`, stride `543` | `485x512`, stride `543` | `928` | `0` | `[0.05755615234375, 0.10772705078125, 0.062286376953125, 1.0]` |
| `150mm` | `573x543`, stride `573` | `49x226`, stride `573` | `0` | `881370` | `[0.23974609375, 0.48193359375, 0.331787109375, 1.0]` |

The differing first-hit dimensions and offsets are tile/view samples. They are
not semantic constants. The invariant proven here is the relationship between
the local view and the caller-provided context descriptor.

## Limits

This proof closes the immediate destination backing-store relationship for the
owner `+0xf0` expansion handoff. It does not close:

- consumers after the caller-provided context descriptor is populated
- final output or display semantics
- public row-channel / pixel-format names
- final contributor acceptance / rejection or suppression logic
- complete merge-quality policy beyond the bounded arithmetic path
