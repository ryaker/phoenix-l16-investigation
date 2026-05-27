# Bundle + LLDB `0x3e5720` Caller Census Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib`, repo-local static callgraph direct-caller
query for `0x3e5720`, and bounded LLDB disassembly windows around all direct
callers of that row-conversion executor setup.

This document follows:

- `bundle_lldb_iramp_caller_3e5720_executor_setup.md`
- `bundle_lldb_iramp_caller_output_descriptor_sink.md`
- `bundle_lldb_selected_cache_caller_census_static.md`

The previous runtime proof classifies `0x3e5720` as an executor setup that
allocates/resizes a 6-byte-element destination descriptor and dispatches a
worker that maps source 16-byte `vec4` rows to destination 6-byte rows before
calling row callback `0x38a30`. This document asks a narrower static question:
which direct callers request `0x3e5720` in the repo-local static callgraph?

It proves:

- The repo-local static callgraph direct callers of `0x3e5720` are only
  `0x3e4b23`, `0x3ecabe`, and `0x3f1157`.
- `0x3e4b23` is inside body `0x3e4a80`: that body builds an owner `+0xf0`
  6-byte destination, calls `0x3e2e90` into a temporary descriptor, then calls
  `0x3e5720` with owner `+0xf0` as destination and that temporary descriptor as
  source. Prior branch-site runtime evidence already includes active callable
  slot `0x3e4a80`; this document adds static caller-body classification only.
- `0x3ecabe` is inside the already classified owner `+0xf0` output-sink body
  `0x3ec960`: after its selected-cache / sibling-wrapper branch and common
  `0x2d7320` vector-scale continuation, it calls `0x3e5720`.
- `0x3f1157` is inside body `0x3f0b90`, which contains the string
  `Requested DOFCache render with no blur!`: that body allocates/resizes owner
  `+0xf0` with 6-byte elements, calls selected-cache read body `0x3d01b0` plus
  additional image/geometry helpers, then calls `0x3e5720`.
- Ancillary static follow-up shows direct callers of `0x432db0` are `0x42d531`
  and `0x42fb71`; the `0x42fb40` body calls `0x3d0650` before calling
  `0x432db0`. This is included only to keep the later selected-cache caller
  surface bounded.

It does not prove:

- indirect or vtable caller coverage for `0x3e5720`
- runtime liveness for every static caller listed here
- public semantic names for owner `+0xf0`, the temporary descriptors, row
  channels, or pixel formats
- final file/display sink
- final contributor acceptance, rejection, or suppression policy
- exact semantic contents of visible `src1` or visible `src2`

## Inputs

Static proof target:

| What | Path |
|---|---|
| `libcp.dylib` | `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib` |

Repo-local callgraph artifacts:

| What | Path |
|---|---|
| callgraph script | `tools/disasm_callgraph.py` |
| static disassembly input | `tools/libcp_disasm_intel.txt` |
| callgraph database | `tools/libcp_callgraph.db` |

## Tooling Boundary

Reusable static LLDB script:

- `tools/lldb_probes/static_3e5720_caller_census_disasm.lldb`

Rerunnable raw outputs under ignored `runs/`:

- `runs/static_3e5720_caller_census/callers_0x3e5720.txt`
- `runs/static_3e5720_caller_census/callers_0x432db0.txt`
- `runs/static_3e5720_caller_census/callers_0x3e0af0.txt`
- `runs/static_3e5720_caller_census/callers_0x3e0b90.txt`
- `runs/static_3e5720_caller_census/3e5720_caller_static_disasm.txt`

No probe harness or live evidence dependency for this proof lives in
`/private/tmp`.

## Static Method

The direct-caller set comes from `tools/disasm_callgraph.py callers 0x3e5720`
against the current repo-local callgraph database. This bounds direct `callq`
edges represented in that database. It does not cover indirect calls, virtual
calls, function-pointer dispatch, or runtime liveness.

The LLDB script creates a static target from the installed `libcp.dylib`, runs
`image lookup` for every direct caller, and captures bounded disassembly windows
around the direct-caller bodies. It also captures bounded windows for `0x432db0`
because one later selected-cache caller surface feeds that helper after
`0x3d0650`.

## Direct-Caller Set

The callgraph output contains three direct callers:

| Caller | Raw line |
|---|---:|
| `0x3e4b23` | `callers_0x3e5720.txt:2` |
| `0x3ecabe` | `callers_0x3e5720.txt:3` |
| `0x3f1157` | `callers_0x3e5720.txt:4` |

Image lookup maps them to these installed-bundle unnamed-symbol offsets:

| Caller | Lookup raw line | Body family |
|---|---:|---|
| `0x3e4b23` | `5..7` | `___lldb_unnamed_symbol10059 + 163` |
| `0x3ecabe` | `8..10` | `___lldb_unnamed_symbol10158 + 350` |
| `0x3f1157` | `11..13` | `___lldb_unnamed_symbol10226 + 1479` |

## `0x3e4a80`: Active Callable Slot / Owner `+0xf0` Writer

`0x3e4b23` is inside body `0x3e4a80`.

Raw anchors:

| Fact | Raw line |
|---|---:|
| body start at `0x3e4a80` | `31` |
| setup helper `0x3cffc0` | `46` |
| alloc/resize helper `0xf540` with element size `6` | `50` |
| worker/projection path `0x3e2e90` | `70` |
| direct call to `0x3e5720` | `76` |

The body computes an owner `+0xf0` destination before the `0xf540` call, fills a
temporary descriptor through `0x3e2e90`, then passes owner `+0xf0` and the
temporary descriptor to `0x3e5720`.

Prior global branch-site runtime evidence includes active callable slot
`0x3e4a80`. This proof does not add a new runtime packet; it statically
classifies the body behind that active slot.

Safe classification: active-callable-slot writer that converts a temporary
`0x3e2e90` result into owner `+0xf0` through `0x3e5720`.

Non-closure: this is not the final file/display sink or final contributor
acceptance/rejection policy.

## `0x3ec960`: Owner `+0xf0` Output-Sink Continuation

`0x3ecabe` is inside body `0x3ec960`, which prior runtime evidence already
classifies as the owner `+0xf0` output-descriptor sink.

Raw anchors:

| Fact | Raw line |
|---|---:|
| body start at `0x3ec960` | `149` |
| setup helper `0x3cffc0` | `164` |
| alloc/resize helper `0xf540` with element size `6` | `168` |
| selected-cache branch call to `0x3d0650` | `199` |
| vector-scale helper `0x2d7320` | `227` |
| direct call to `0x3e5720` | `233` |

Safe classification: owner `+0xf0` output-sink continuation that reaches
`0x3e5720` after selected-cache / sibling-wrapper source construction and
common vector-scale plumbing.

Non-closure: public source semantics and final contributor policy remain
unclosed.

## `0x3f0b90`: DOFCache Render Surface

`0x3f1157` is inside body `0x3f0b90`.

Raw anchors:

| Fact | Raw line |
|---|---:|
| body start at `0x3f0b90` | `237` |
| alloc/resize helper `0xf540` with element size `6` | `267` |
| guard string `Requested DOFCache render with no blur!` | `342` |
| `0x3daf30` helper | `445` |
| selected-cache read `0x3d01b0` | `455` |
| `0x3db3e0` helper | `460` |
| helper `0x2c5a10` | `484` |
| helper `0x2a57a0` | `488` |
| helper `0x2a3ef0` | `498` |
| helper `0x2a4280` | `506` |
| direct call to `0x3e5720` | `557` |

The string xref query for `Requested DOFCache render with no blur!` has one
hit at `0x3f0d3e`, inside the same body.

Safe classification: DOFCache render surface that also converts an intermediate
descriptor into owner `+0xf0` through `0x3e5720`.

Non-closure: this static body does not prove bridge HDR liveness for the DOF
surface and does not define the base bridge-HDR final merge policy.

## Ancillary `0x432db0` Surface

The direct callers of `0x432db0` are:

| Caller | Raw line |
|---|---:|
| `0x42d531` | `callers_0x432db0.txt:2` |
| `0x42fb71` | `callers_0x432db0.txt:3` |

Raw anchors:

| Fact | Raw line |
|---|---:|
| body `0x42c8f0` start | `578` |
| `0x42c8f0` call to `0x432db0` | `1217` |
| body `0x42fb40` start | `1232` |
| `0x42fb40` call to `0x3d0650` | `1239` |
| `0x42fb40` call to `0x432db0` | `1245` |
| body `0x432db0` start | `1339` |
| `0x432db0` alloc/resize helper `0xf540` with element size `16` | `1357` |
| row-loop source load in `0x432db0` | `1425` |

Safe classification: `0x42fb40` is a later selected-cache caller surface that
feeds `0x432db0`; `0x432db0` starts by allocating/resizing a 16-byte-element
destination and enters row/vector processing.

Non-closure: the public output semantics of `0x432db0` are not classified here.

## Canonical Consequence

This census narrows the downstream `0x3e5720` search. In the current repo-local
static callgraph, direct callers of the row-conversion executor setup are only:

- active-callable-slot / owner `+0xf0` writer body `0x3e4a80`
- owner `+0xf0` output-sink body `0x3ec960`
- DOFCache render body `0x3f0b90`

Therefore `0x3e5720` is bounded as shared conversion/output plumbing, not the
final contributor acceptance/rejection decision. The remaining final-policy
search should move past these direct callers toward the consumers of owner
`+0xf0` data and any later file/display or suppression policy surfaces.
