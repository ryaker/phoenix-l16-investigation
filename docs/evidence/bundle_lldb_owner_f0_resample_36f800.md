# Bundle + LLDB Owner `+0xf0` `0x36f800` Resample Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib` and corrected canonical bridge HDR quartet.

This document is the checkpoint for the first proven `0x36f800` worker path
after the owner-backed `+0xf0` expansion route.

It proves:

- the captured route starts at the already bounded owner `+0xf0` sink
  `0x3ec960`
- the accepted handoff uses active callable branch `0x3d4842` and active
  callable slot `0x3ec960`
- the parent `0x3d01b0` caller returns to `0x3d084d` in the selected-cache
  read/rescale path
- the same route reaches `0x3d08ce -> 0x36f800`
- inside that `0x36f800` call, the callback vtable slot `+0x30` is
  `0x3721d0`
- `0x3721d0` shifts the callback object by `+0x8` and jumps to `0x372210`
- the first captured worker store at `0x372488` writes a destination `vec4`
  equal to the four captured source `vec4` rows multiplied by the four
  captured weight `vec4`s, across `28mm`, `35mm`, `70mm`, and `150mm`

It does not prove:

- every possible `0x36f800` caller
- every possible owner `+0xf0` route
- helper activity later covered separately by `bundle_lldb_owner_f0_resample_helpers_372500_372760.md`
- public names for offset / scale / pixel-format fields
- final output or display semantics
- final contributor acceptance / rejection or suppression policy

## Inputs

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Tooling Boundary

Reusable probes live in the repo:

- `tools/lldb_probes/owner_f0_resample_36f800/owner_f0_resample_36f800_probe.py`
- `tools/lldb_probes/owner_f0_resample_36f800/owner_f0_resample_28mm.lldb`
- `tools/lldb_probes/owner_f0_resample_36f800/owner_f0_resample_35mm.lldb`
- `tools/lldb_probes/owner_f0_resample_36f800/owner_f0_resample_70mm.lldb`
- `tools/lldb_probes/owner_f0_resample_36f800/owner_f0_resample_150mm.lldb`

Rerunnable raw JSON packets live under ignored
`runs/owner_f0_resample_36f800/`. Static disassembly captures for this
checkpoint also live under the same ignored run directory. No probe harness for
this evidence is stored outside the repo.

## Static Proof

Installed bundle:
`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`.

Static disassembly commands used for this checkpoint:

```bash
arch -x86_64 lldb --batch \
  -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' \
  -o 'disassemble --start-address 0x36f800 --end-address 0x370180' \
  -o 'disassemble --start-address 0x5440 --end-address 0x56d0'
```

```bash
arch -x86_64 lldb --batch \
  -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' \
  -o 'memory read --format x --size 8 --count 16 0x669738' \
  -o 'disassemble --start-address 0x372100 --end-address 0x372240'
```

```bash
arch -x86_64 lldb --batch \
  -o 'target create /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib' \
  -o 'disassemble --start-address 0x372210 --end-address 0x372780'
```

Inside `0x36f800`, the entry saves the four arguments as:

- `rdi` destination descriptor into `%rbx`
- `rsi` source descriptor into `%r15`
- `rdx` offset pair into `%r12`
- `rcx` scale pair into `%r14`

The setup then builds a 64-entry stack weight table and a `0x30`-byte callback
object. The callback fields are:

```asm
0x36fae2  movq %rcx, (%rax)        ; vtable/address point 0x669738
0x36fae5  movq %r12, 0x8(%rax)     ; offset pair
0x36fae9  movq %r14, 0x10(%rax)    ; scale pair
0x36faed  movq %r15, 0x18(%rax)    ; source descriptor
0x36faf8  movq %rcx, 0x20(%rax)    ; stack weight table
0x36fafc  movq %rbx, 0x28(%rax)    ; destination descriptor
```

The callback vtable/address point at `0x669738` contains slot `+0x30 =
0x3721d0`:

```text
0x00669738: 0x0000000000372120 0x0000000000372130
0x00669748: 0x0000000000372140 0x0000000000372180
0x00669758: 0x00000000003721b0 0x00000000003721c0
0x00669768: 0x00000000003721d0 0x00000000003721e0
```

`0x3721d0` is the immediate dispatch thunk. It shifts `rdi` to the callback
field payload at object `+0x8`, loads one int from `rdx`, and jumps to
`0x372210`:

```asm
0x3721d4  addq $0x8, %rdi
0x3721d8  movl (%rdx), %edx
0x3721db  jmp 0x372210
```

The worker body `0x372210` reads the offset/scale pointers, source descriptor,
weight table, and destination descriptor from that shifted callback payload. It
then uses helper `0x372500` and inner helper `0x372760` for coordinate/row-cache
preparation. The first captured destination write is the visible weighted
`vec4` combine at `0x372460..0x372485`:

```asm
0x372460  movaps (%rax), %xmm0
0x372463  mulps  (%r8), %xmm0
0x372467  movaps (%rcx), %xmm1
0x37246a  mulps  (%r9), %xmm1
0x37246e  addps  %xmm0, %xmm1
0x372471  movaps (%rsi), %xmm0
0x372474  mulps  (%r10), %xmm0
0x372478  addps  %xmm1, %xmm0
0x37247b  movaps (%rdi), %xmm1
0x37247e  mulps  (%r11), %xmm1
0x372482  addps  %xmm0, %xmm1
0x372485  movaps %xmm1, (%rdx)
```

Therefore, for this route, the dispatch target is
`0x36f800 -> 0x5440 -> 0x3721d0 -> 0x372210`. Adjacent body `0x36fba0` is not
the proven vtable target for this owner `+0xf0` route.

## Runtime Proof

The probe is deliberately gated to prevent contamination from unrelated
selected-cache reads:

1. It first stops at `0x3ecac3` and records the exact owner object and
   `owner+0xf0` descriptor.
2. It accepts only a later `0x3d4842` / `0x3d4864` handoff whose source pair
   points back to that exact owner.
3. It requires the handoff caller to be `0x3d084d` in `0x3d0650`.
4. It accepts only the following `0x3d08ce` call whose `rsi` descriptor equals
   that handoff's `context+0x10` destination descriptor.
5. It accepts only the following `0x36fb1f` setup whose callback object fields
   match the exact `rdi` / `rsi` / `rdx` / `rcx` arguments captured at
   `0x3d08ce`.

All four runtime packets observed:

- route handoff active callable slot `+0x30 = 0x3ec960`
- route handoff caller return after `0x3d01b0 = 0x3d084d`
- rescale call site `0x3d08ce`
- `0x36f800` caller return `0x3d08d3`
- callback vtable slot `+0x30 = 0x3721d0`
- worker entry after prologue `0x372224`
- first captured weighted store after `0x372488`
- callback source/destination/offset/scale pointers match the exact
  `0x3d08ce` arguments

First-hit values below are live tile samples and must not be promoted to
semantic constants.

| Zoom | Source descriptor | Destination descriptor | Offset pair | Scale pair | First-store weights | Max diff |
|---|---:|---:|---:|---:|---|---:|
| `28mm` | `464x436`, stride `464` | `575x543`, stride `575` | `[2.82208251953125, 0.0]` | `[0.7975460290908813, 0.7975460290908813]` | `[0.0, 1.0, 0.0, 0.0]` | `0.0` |
| `35mm` | `463x464`, stride `463` | `575x575`, stride `575` | `[2.092041015625, 2.564453125]` | `[0.7975460290908813, 0.7975460290908813]` | `[-0.053833008, 0.475952148, 0.647094727, -0.069213867]` | `3.406967152841389e-09` |
| `70mm` | `518x518`, stride `518` | `551x551`, stride `551` | `[0.0, 0.0]` | `[0.935251772403717, 0.935251772403717]` | `[0.0, 1.0, 0.0, 0.0]` | `0.0` |
| `150mm` | `542x543`, stride `542` | `575x575`, stride `575` | `[2.10791015625, 2.4244384765625]` | `[0.935251772403717, 0.935251772403717]` | `[-0.070501328, 0.66768074, 0.454267502, -0.051446915]` | `2.4157429834303912e-08` |

The `Max diff` column compares the destination `vec4` read after the
`0x372485` store against the probe-computed sum:

```text
source0 * weight0 + source1 * weight1 + source2 * weight2 + source3 * weight3
```

The small nonzero values at `35mm` and `150mm` are within single-precision
rounding tolerance for the captured floats.

## Limits

This checkpoint narrows the downstream owner `+0xf0` route through one concrete
resampling worker path. It proves the dispatch target and first captured
weighted `vec4` store for the gated route across the canonical four-zoom bridge
HDR quartet.

It does not close full `0x36f800` math. The helper checkpoint is covered
separately by `bundle_lldb_owner_f0_resample_helpers_372500_372760.md`;
full-render leading/trailing row-cache reachability is covered separately by
`bundle_lldb_owner_f0_global_rowcache_segments.md`; alternate downstream routes
after owner `+0xf0` expansion and final policy remain open.
