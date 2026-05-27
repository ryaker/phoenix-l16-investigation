# Bundle + LLDB Owner `+0xf0` Downstream Consumer Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib` and corrected canonical bridge HDR quartet.

This document bounds the first proven downstream consumer family for the
owner-backed descriptor populated by `0x3ec960 -> 0x3e5720`.

It proves:

- the owner `+0xf0` descriptor populated by `0x3ec960` is later consumed
- the downstream consumer reaches `0x3d50f0 -> 0x5670 -> 0x3d5290`
- the row worker reaches `0x2ff00 -> 0xc0410`
- runtime packets at `28mm`, `35mm`, `70mm`, and `150mm` all pass a source row
  pointer inside the exact owner `+0xf0` data range to `0xc0410`
- the matching `0xc0410` call uses `ecx/cl = 0`

It does not prove that owner `+0xf0` is final file output, display output, or
the last merge-quality decision surface.

## Inputs

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Tooling Boundary

Reusable probes live in the repo:

- `tools/lldb_probes/owner_f0_downstream_watch/owner_f0_downstream_watch_probe.py`
- `tools/lldb_probes/owner_f0_downstream_watch/owner_f0_watch_28mm.lldb`
- `tools/lldb_probes/owner_f0_downstream_watch/owner_f0_watch_35mm.lldb`
- `tools/lldb_probes/owner_f0_downstream_watch/owner_f0_watch_70mm.lldb`
- `tools/lldb_probes/owner_f0_downstream_watch/owner_f0_watch_150mm.lldb`

Process output-path placeholders go under ignored
`runs/owner_f0_downstream_watch/`. No probe harness for this evidence lives in
`/private/tmp`.

## Static Proof

Installed bundle:
`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`.

The previously admitted output-sink proof shows `0x3ec960` stores the
`0x3e5720` conversion result into owner `+0xf0`.

The downstream consumer family is bounded as follows:

```asm
0x3d50f0  pushq %rbp
...
0x3d5127  leaq 0x10(%r14), %rsi
0x3d512b  movl $0x10, %edx
0x3d5130  movq %rbx, %rdi
0x3d5133  callq 0xf540
...
0x3d5177  movq %rbx, -0x50(%rbp)
0x3d517b  movq %r14, -0x48(%rbp)
0x3d5184  callq 0x5670
```

`0x3d50f0` allocates/resizes the destination descriptor with element size
`0x10`, builds an executor callback object with vtable `0x66a690`, stores the
destination descriptor in the callback and the source descriptor in the
callback, then dispatches generic executor `0x5670`.

The callback worker at `0x3d5290` walks rows. It computes a destination row from
the callback's destination descriptor using `16` bytes per output pixel, computes
a source row from the callback's source descriptor using `6` bytes per input
pixel, reads the source width/count field, and calls the converter selected in
the callback object:

```asm
0x3d52b0  movq 0x8(%r14), %rax
0x3d52b4  movq 0x10(%r14), %rcx
...
0x3d52c7  addq 0x20(%rcx), %rdi
0x3d52cb  movq 0x18(%r14), %rcx
0x3d52cf  movq 0x20(%rcx), %rdx
...
0x3d52df  leaq (%rdx,%rsi,2), %rsi
0x3d52e3  movl 0x10(%rcx), %edx
0x3d52e6  callq *(%rax)
```

Runtime stack samples show the selected converter path is
`0x2ff00 -> 0xc0410`. Static inspection of `0x2ff00` shows it calls `0xc0410`
with `ecx = 0`, then copies converted triples into `vec4` rows and writes lane
3 as `1.0`:

```asm
0x2ff79  movl $0xc00, %edx
0x2ff7e  xorl %ecx, %ecx
0x2ff80  leaq 0x40(%rsp), %rdi
0x2ff85  callq 0xc0410
...
0x2ffc1  movl $0x3f800000, (%rcx)
```

`0xc0410` reads 16-bit words from the source row and expands them into float32
values. This is the downstream inverse-shape of the already admitted
`0x38a30 -> 0xbfef0` float-channel to binary16-bit-pattern conversion. Public
channel or pixel-format names are not assigned here.

## Runtime Proof

The LLDB probe stops at `0x3ecac3`, records the exact owner `+0xf0` descriptor
and data range, then creates a downstream breakpoint at `0xc0410`. The
breakpoint only stops when live `rsi` falls inside that exact recorded data
range.

All four packets observed:

- setup stop site = `0x3ecac3`
- downstream stop site = `0xc0410`
- hit kind = `conversion_entry_source_range_match`
- owner `+0xf0` descriptor dimensions = `512x512`
- owner `+0xf0` descriptor stride = `512`
- live `rsi` at `0xc0410` is inside the owner `+0xf0` data range
- live `ecx/cl` at `0xc0410` is `0`

First-hit values below are live memory samples and offsets, not stable semantic
constants.

| Zoom | `0xc0410` source offset bytes | Offset mod 6 | Live `edx` | First 16 source bytes |
|---|---:|---:|---:|---|
| `28mm` | `0` | `0` | `1308` | `9a 34 f9 37 c7 34 95 34 f1 37 c1 34 8f 34 e7 37` |
| `35mm` | `913968` | `0` | `744` | `ab 23 0d 27 98 24 b2 23 10 27 97 24 6b 24 08 28` |
| `70mm` | `1295838` | `0` | `273` | `06 2c e2 2f 1e 2c 81 2b 61 2f 86 2b 8f 2b 3f 2f` |
| `150mm` | `777522` | `0` | `1383` | `8a 34 9d 38 63 36 88 34 9b 38 61 36 83 34 96 38` |

The `35mm`, `70mm`, and `150mm` offsets show why a watchpoint on only byte zero
is too narrow for crop/tele paths. The range-gated `0xc0410` proof is the
admitted runtime proof.

## Limits

This proof closes one downstream consumer boundary for the owner `+0xf0`
descriptor. It does not close:

- final output or display semantics
- public row-channel / pixel-format names
- whether later stages consume the expanded `vec4` descriptor
- final contributor acceptance / rejection or suppression logic
- complete merge-quality policy beyond the bounded arithmetic path
