# Bundle + LLDB Owner `+0xf0` Read-Context Route Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib` and corrected canonical bridge HDR quartet.

This document bounds the first captured route from the owner-backed `+0xf0`
descriptor expansion into the caller's read/rescale context.

Follow-up note: `bundle_lldb_owner_f0_route_census.md` extends this first-route
proof. The first accepted route here still uses `0x3d4842`, but the follow-up
first-owner census proves sibling direct branch `0x3d4864` is also live on
`28mm`, `70mm`, and `150mm` under the same first-owner descriptor scope. Do not
read this document as proof that all owner `+0xf0` routes use `0x3d4842`.

It proves:

- the first accepted owner `+0xf0` expansion route captured by this probe uses
  the `0x3d47d0` active-callable branch at `0x3d4842`
- the active callable's substantive slot is `0x3ec960`, the already bounded
  owner `+0xf0` output-descriptor sink
- the `0x3d4e10` output context is the parent `0x3d01b0` stack context at
  `rbp-0x108`
- that context's `+0x10` destination descriptor is the same descriptor pointer
  that `0x3d01b0` saved from its caller-provided output argument at `rbp-0x148`
- the first captured route returns from `0x3d01b0` to `0x3d084d`, inside the
  already bounded `0x3d0650` selected-cache read/rescale path
- the same temporary descriptor is then passed as `rsi` to `0x36f800` at
  `0x3d08ce`, with `rdi` holding the requested output descriptor and `rdx` /
  `rcx` holding offset / scale pair arguments
- the proof holds at `28mm`, `35mm`, `70mm`, and `150mm`

It does not prove:

- every possible owner `+0xf0` expansion route or call order
- that sibling branch `0x3d4864` is dead or irrelevant
- full worker math inside `0x36f800`
- public names for the offset / scale pairs or pixel format
- final output or display semantics
- final merge acceptance / rejection policy

## Inputs

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Tooling Boundary

Reusable probes live in the repo:

- `tools/lldb_probes/owner_f0_read_context_route/owner_f0_read_context_route_probe.py`
- `tools/lldb_probes/owner_f0_read_context_route/owner_f0_route_28mm.lldb`
- `tools/lldb_probes/owner_f0_read_context_route/owner_f0_route_35mm.lldb`
- `tools/lldb_probes/owner_f0_read_context_route/owner_f0_route_70mm.lldb`
- `tools/lldb_probes/owner_f0_read_context_route/owner_f0_route_150mm.lldb`

Rerunnable raw JSON packets live under ignored
`runs/owner_f0_read_context_route/`. No probe harness for this evidence lives
in `/private/tmp`.

## Static Proof

Installed bundle:
`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`.

Inside `0x3d01b0`, the caller-provided output descriptor arrives in `rsi`,
is saved in `r8`, and is stored in the local `rbp-0x148`. The body then
allocates/resizes that output descriptor through `0xf540`:

```asm
0x3d01c7  movq %rsi, %r8
...
0x3d024f  movq %r8, %rdi
0x3d0252  movq %r8, -0x148(%rbp)
0x3d0259  callq 0xf540
```

The local context object that later reaches `0x3d4e10` is built at
`rbp-0x108`. Its `+0x10` field is loaded from `rbp-0x148`, so it points back
to that same caller-provided output descriptor:

```asm
0x3d02f2  movq %r9, -0x108(%rbp)
0x3d02f9  movq %r12, -0x100(%rbp)
0x3d0300  movq -0x148(%rbp), %rax
0x3d0307  movq %rax, -0xf8(%rbp)
```

The closure allocated at `0x3d0374` stores `&rbp-0x108` at closure `+0x18`.
Because the worker thunk at `0x3d4790` shifts `rdi` by `8` before entering
`0x3d47d0`, the worker reads that field as `[r14+0x10]` and passes it to
`0x3d4e10`:

```asm
0x3d039e  leaq -0x108(%rbp), %r14
0x3d03a5  movq %r14, 0x18(%rax)
...
0x3d4794  addq $0x8, %rdi
...
0x3d4842  movq 0x10(%r14), %rdi
0x3d4846  leaq -0x30(%rbp), %rsi
0x3d484a  callq 0x3d4e10
```

The route captured by this proof returns from `0x3d01b0` to `0x3d084d`,
inside the selected-cache read/rescale body `0x3d0650`. Static inspection
shows that path calls `0x3d01b0` into a temporary descriptor at `rbp-0x70`,
then passes that same temporary to `0x36f800`:

```asm
0x3d083d  leaq -0x70(%rbp), %rsi
0x3d0841  leaq -0x40(%rbp), %rdx
0x3d0845  movq %r15, %rdi
0x3d0848  callq 0x3d01b0
...
0x3d08bc  leaq -0x70(%rbp), %rsi
0x3d08c0  leaq -0x80(%rbp), %rdx
0x3d08c4  leaq -0x90(%rbp), %rcx
0x3d08cb  movq %r14, %rdi
0x3d08ce  callq 0x36f800
```

Existing evidence `bundle_proof_src1_owner_cache_selection.md` bounds
`0x36f800` as resampling setup, not exposed N-to-1 reducer math. This proof
adds runtime ownership/context routing for the owner `+0xf0` expansion path.

## Runtime Proof

The probe first stops at `0x3ecac3` and records the exact owner `+0xf0`
descriptor. It then accepts only a later `0x3d4842` or `0x3d4864` packet whose
local source pair points back to that exact owner. For accepted packets, it
reads the parent `0x3d01b0` frame and the caller frame, then stops at
`0x3d08ce` only when the selected-cache temporary descriptor equals the
previously proven context destination descriptor.

All four accepted packets observed:

- branch = `active_callable_then_3d4e10`
- active callable slot `+0x30 = 0x3ec960`
- `output_context == parent_3d01b0_rbp - 0x108`
- `context+0x10 == parent_3d01b0[rbp-0x148]`
- caller return after `0x3d01b0` = `0x3d084d`
- post-route = `0x3d08ce -> 0x36f800`
- `rsi` at `0x3d08ce` equals the same temporary descriptor proven as
  `context+0x10`

First-hit values below are live tile samples and must not be promoted to
semantic constants.

| Zoom | Parent ROI passed to `0x3d01b0` | Temp descriptor passed to `0x36f800` | Requested output descriptor before `0x36f800` | Offset pair | Scale pair | First temp `vec4` |
|---|---:|---:|---:|---:|---:|---|
| `28mm` | `[0,1197,436,1661]` | `436x464`, stride `436` | `543x575`, stride `543` | `[0.0,2.50927734375]` | `[0.7975460290908813,0.7975460290908813]` | `[0.344970703125,0.603515625,0.37060546875,1.0]` |
| `35mm` | `[1184,1114,1648,1578]` | `464x464`, stride `464` | `575x575`, stride `575` | `[2.74853515625,2.564453125]` | `[0.7975460290908813,0.7975460290908813]` | `[0.01508331298828125,0.0258026123046875,0.01445770263671875,1.0]` |
| `70mm` | `[454,0,997,518]` | `543x518`, stride `543` | `575x551`, stride `575` | `[2.402862548828125,0.0]` | `[0.935251772403717,0.935251772403717]` | `[0.1778564453125,0.3037109375,0.1878662109375,1.0]` |
| `150mm` | `[1075,1277,1618,1820]` | `543x543`, stride `543` | `575x575`, stride `575` | `[2.4100341796875,2.4244384765625]` | `[0.935251772403717,0.935251772403717]` | `[0.283935546875,0.57763671875,0.400146484375,1.0]` |

The scale-pair values match the wide/tile and tele/tile samples captured here,
but this document does not assign public semantic names to them.

## Limits

This proof narrows the immediate consumer after the owner `+0xf0` expansion
destination context. It closes only the first captured route through
`0x3d0650 -> 0x36f800` across the canonical four-zoom bridge HDR quartet.
The first-owner branch census is covered separately by
`bundle_lldb_owner_f0_route_census.md`.
The complete-render branch-site caller/slot census is covered separately by
`bundle_lldb_owner_f0_global_route_census.md`.

It does not close:

- `0x36f800` weighted-store details beyond this route checkpoint, which are covered separately by `bundle_lldb_owner_f0_resample_36f800.md`
- helper-store and first-dispatch row-plan details, which are covered separately by `bundle_lldb_owner_f0_resample_helpers_372500_372760.md`
- full-render `0x36f800` leading/trailing row-cache segment reachability, which is covered separately by `bundle_lldb_owner_f0_global_rowcache_segments.md`
- complete post-route family classification, which is covered separately by `bundle_lldb_owner_f0_global_post_route_families.md`
- public offset / scale / pixel-format semantics
- final file/display output semantics
- final contributor acceptance / rejection or suppression logic
