# Bundle + LLDB Owner `+0xf0` Expansion Handoff Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib` and corrected canonical bridge HDR quartet.

This document bounds the handoff immediately after the first proven downstream
consumer family for the owner-backed `+0xf0` descriptor.

It proves:

- the owner `+0xf0` descriptor populated by `0x3ec960 -> 0x3e5720` is later
  reintroduced as the source descriptor at the `0x3d4e10 -> 0x3d50f0` handoff
- the local source descriptor at `rbp-0x60` points inside the exact owner
  `+0xf0` data range recorded at `0x3ecac3`
- `0x3d50f0` produces a local destination descriptor at `rbp-0x90` with
  `16`-byte elements
- the observed expanded first element is a `vec4`-shaped float tuple whose
  lane 3 is `1.0` at `28mm`, `35mm`, `70mm`, and `150mm`

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

- `tools/lldb_probes/owner_f0_expansion_handoff/owner_f0_expansion_handoff_probe.py`
- `tools/lldb_probes/owner_f0_expansion_handoff/owner_f0_expansion_28mm.lldb`
- `tools/lldb_probes/owner_f0_expansion_handoff/owner_f0_expansion_35mm.lldb`
- `tools/lldb_probes/owner_f0_expansion_handoff/owner_f0_expansion_70mm.lldb`
- `tools/lldb_probes/owner_f0_expansion_handoff/owner_f0_expansion_150mm.lldb`

Process output-path placeholders go under ignored
`runs/owner_f0_expansion_handoff/`. No probe harness for this evidence lives in
`/private/tmp`.

## Static Proof

Installed bundle:
`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`.

Prior admitted proof already shows:

- `0x3ec960` stores the `0x3e5720` conversion result into owner `+0xf0`
- `0x3d50f0` allocates a `16`-byte-element destination and dispatches
  `0x5670 -> 0x3d5290`
- the selected converter path reaches `0x2ff00 -> 0xc0410`, expanding source
  binary16 triples into float rows with lane 3 written as `1.0`

The newly bounded caller is the surrounding `0x3d4e10` body. Static inspection
shows it builds local descriptors, calls `0x3d50f0`, and then immediately
destroys those local descriptors:

```asm
0x3d4e10  pushq %rbp
...
0x3d4fdd  leaq -0x90(%rbp), %rdi
0x3d4fe4  leaq -0x60(%rbp), %rsi
0x3d4fe8  callq 0x3d50f0
...
0x3d502e  leaq -0x90(%rbp), %rdi
0x3d5035  callq 0xf4e0
0x3d503a  leaq -0x60(%rbp), %rdi
0x3d503e  callq 0xf4e0
```

At `0x3d502e`, `0x3d50f0` has returned and both local descriptors are still
readable. This makes `0x3d502e` a safe handoff point for proving source/dest
descriptor relationship without naming public pixel-format semantics.

## Runtime Proof

The LLDB probe stops first at `0x3ecac3`, records the exact owner `+0xf0`
descriptor and data range, then installs a dynamic breakpoint at `0x3d502e`.
The `0x3d502e` callback only accepts a packet when the source descriptor
`rbp-0x60` points inside the exact owner `+0xf0` range captured earlier in the
same process.

All accepted packets observed:

- setup stop site = `0x3ecac3`
- handoff stop site = `0x3d502e`
- owner `+0xf0` descriptor dimensions = `512x512`
- owner `+0xf0` descriptor stride = `512`
- source descriptor `data_ptr` is inside the captured owner `+0xf0` data range
- source offset modulo the known `6`-byte row element shape is `0`
- expanded descriptor element size at the static site is `16`
- expanded descriptor first element has lane 3 = `1.0`

First-hit values below are live memory samples and offsets, not stable semantic
constants.

| Zoom | Source descriptor at `rbp-0x60` | Source offset bytes | Expanded descriptor at `rbp-0x90` | Expanded first `vec4` |
|---|---:|---:|---:|---|
| `28mm` | `132x436`, stride `512` | `2280` | `132x436`, stride `464` | `[0.21630859375, 0.36767578125, 0.2122802734375, 1.0]` |
| `35mm` | `248x215`, stride `512` | `913968` | `248x215`, stride `463` | `[0.01497650146484375, 0.0275421142578125, 0.0179443359375, 1.0]` |
| `70mm` | `6x512`, stride `512` | `0` | `6x512`, stride `518` | `[0.05755615234375, 0.10772705078125, 0.062286376953125, 1.0]` |
| `150mm` | `494x226`, stride `512` | `878700` | `494x226`, stride `543` | `[0.271728515625, 0.54638671875, 0.37841796875, 1.0]` |

The first `70mm` attempt in this run stopped at the known
instrumentation-sensitive `libcp+0x2e945d` crash before the setup packet was
captured. That failed attempt produced no evidence packet and is not part of
the admitted proof. A clean same-probe rerun produced the accepted `70mm`
packet above.

## Limits

This proof closes the immediate handoff after the first owner `+0xf0`
downstream expansion family. It does not close:

- final output or display semantics
- public row-channel / pixel-format names
- later consumers after the expanded `vec4` descriptor
- final contributor acceptance / rejection or suppression logic
- complete merge-quality policy beyond the bounded arithmetic path
