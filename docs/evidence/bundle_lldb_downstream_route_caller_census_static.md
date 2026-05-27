# Bundle + LLDB Downstream Route Direct-Caller Census Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib`, repo-local static callgraph direct-caller
queries, and bounded LLDB disassembly windows around newly classified direct
callers for selected downstream route helpers.

This document follows:

- `bundle_lldb_owner_f0_global_post_route_families.md`
- `bundle_lldb_owner_f0_global_route_ancestry.md`
- `bundle_lldb_owner_f0_parent_chain_static_classification.md`
- `bundle_lldb_owner_f0_helper_surface_static_classification.md`
- `bundle_lldb_owner_f0_selected_cache_route_static_classification.md`

The prior runtime proofs supply the live owner `+0xf0` route facts. This
document is not a new runtime hit-count proof. It is a static installed-bundle
direct-caller census for downstream helpers that were exposed by those route
proofs, plus bounded classification of the direct callers that were not already
classified in earlier evidence.

It proves:

- The repo-local static callgraph direct callers of `0x36f800` are only
  `0x36a273`, `0x3d08ce`, and `0x3d143e`.
- The repo-local static callgraph direct callers of `0x3d01b0` are only
  `0x3a3531`, `0x3d072d`, `0x3d0848`, `0x3ecc55`, and `0x3f0f38`.
- The repo-local static callgraph direct callers of `0x3edb80` are only
  `0x3ecc74` and `0x3ecdc7`.
- The repo-local static callgraph direct caller of `0x3d50f0` is only
  `0x3d5029`.
- The newly inspected `0x36f800` direct callers are IRAMP-internal descriptor
  resample handoff at `0x36a273` and a TileCache-like read/rescale sibling at
  `0x3d143e`.
- The newly inspected `0x3d01b0` direct callers are a source-adapter caller at
  `0x3a3531` and a DOFCache render caller at `0x3f0f38`.
- The newly inspected `0x3edb80` direct caller `0x3ecdc7` is a visible-`src2`
  one-image normalization wrapper through `0x3ebb80 -> 0x3edb80`.

It does not prove:

- complete indirect or vtable caller coverage
- runtime liveness for the newly inspected static-only callers
- final file/display sink
- final contributor acceptance, rejection, or suppression policy
- public names for cache surfaces, row/image channels, pixel formats, offsets,
  scales, or helper fields
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

- `tools/lldb_probes/static_downstream_route_caller_census_disasm.lldb`

Rerunnable raw outputs under ignored `runs/`:

- `runs/static_downstream_route_caller_census/callers_0x36f800.txt`
- `runs/static_downstream_route_caller_census/callers_0x3d01b0.txt`
- `runs/static_downstream_route_caller_census/callers_0x3edb80.txt`
- `runs/static_downstream_route_caller_census/callers_0x3d50f0.txt`
- `runs/static_downstream_route_caller_census/downstream_route_caller_static_disasm.txt`

No probe harness or live evidence dependency for this proof lives in
`/private/tmp`.

## Static Method

The direct-caller sets come from repo-local `tools/disasm_callgraph.py callers`
queries against the current callgraph database. These outputs bound direct
`callq` edges represented in that database. They do not cover indirect calls,
virtual calls, function-pointer dispatch, or route-specific runtime liveness.

The LLDB script creates a static target from the installed `libcp.dylib`, then
runs `image lookup` plus address-bounded disassembly around the direct callers
that were not already classified by prior evidence:

- `0x36a273`
- `0x3d143e`
- `0x3a3531`
- `0x3f0f38`
- `0x3ecdc7`

## `0x36f800`: Direct-Caller Set

The callgraph output contains three direct callers:

| Caller | Raw line |
|---|---:|
| `0x36a273` | `callers_0x36f800.txt:2` |
| `0x3d08ce` | `callers_0x36f800.txt:3` |
| `0x3d143e` | `callers_0x36f800.txt:4` |

Prior evidence already classifies `0x3d08ce` as the selected-cache
read-then-rescale call inside `0x3d0650`.

### `0x36a273`: IRAMP-Internal Descriptor Resample Handoff

`image lookup --address 0x36a273` resolves inside
`___lldb_unnamed_symbol8958 + 16579`, the same broad IRAMP-family body already
covered by earlier merge evidence.

The bounded window shows:

| Fact | Raw line |
|---|---:|
| image lookup for `0x36a273` | `5` |
| nearby 16-byte descriptor allocation through `0xf540` at `0x36a252` | `18` |
| direct call to `0x36f800` at `0x36a273` | `23` |
| post-call continuation at `0x36a278` | `24` |

The visible post-call instructions read `0x48(%r15)`, load scale-like floats,
multiply input rectangle fields, align values to 8-pixel boundaries, and
continue IRAMP-internal ROI/tile arithmetic.

Safe classification: IRAMP-internal descriptor resample handoff.

Non-closure: this bounded window does not prove final row-image policy or
final contributor acceptance/rejection.

### `0x3d143e`: TileCache-Like Read/Rescale Sibling

`image lookup --address 0x3d143e` resolves inside
`___lldb_unnamed_symbol9769 + 638`.

The bounded window shows:

| Fact | Raw line |
|---|---:|
| image lookup for `0x3d143e` | `66` |
| output descriptor allocation through `0xf540` at `0x3d1202` | `72` |
| exact-size read call to `0x3d0d20` at `0x3d129d` | `116` |
| rescale-path read call to `0x3d0d20` at `0x3d13b8` | `185` |
| rescale call to `0x36f800` at `0x3d143e` | `213` |
| guard text `"TileCache pyramid not sorted!"` | `336` |

The visible body selects a level from a dimension vector, performs an exact-size
read through `0x3d0d20` when requested dimensions match, or reads a transformed
ROI into a temporary descriptor and calls `0x36f800` with computed offset/scale
double pairs when rescaling is needed.

Safe classification: TileCache-like read/rescale sibling of the selected-cache
body `0x3d0650`.

Non-closure: this body is read/rescale plumbing. It is not final contributor
acceptance/rejection.

## `0x3d01b0`: Direct-Caller Set

The callgraph output contains five direct callers:

| Caller | Raw line |
|---|---:|
| `0x3a3531` | `callers_0x3d01b0.txt:2` |
| `0x3d072d` | `callers_0x3d01b0.txt:3` |
| `0x3d0848` | `callers_0x3d01b0.txt:4` |
| `0x3ecc55` | `callers_0x3d01b0.txt:5` |
| `0x3f0f38` | `callers_0x3d01b0.txt:6` |

Prior evidence already classifies:

- `0x3d072d` as exact-size selected-cache read cleanup.
- `0x3d0848` as selected-cache temporary read before `0x36f800`.
- `0x3ecc55` as visible-`src1` read before `0x3ecc74 -> 0x3edb80`.

### `0x3a3531`: Source-Adapter Caller

`image lookup --address 0x3a3531` resolves inside
`___lldb_unnamed_symbol9271 + 161`, with body start at `0x3a3490`.

The bounded window shows:

| Fact | Raw line |
|---|---:|
| image lookup for `0x3a3531` | `388` |
| body start at `0x3a3490` | `495` |
| helper call `0x3d0110` on object field `+0x68` | `508` |
| direct call to `0x3d01b0` at `0x3a3531` | `544` |
| post-read call to `0x3bafb0` from object field `+0x48` | `546` |
| call to `0x3e0a20` | `548` |
| call to `0x31b110` | `561` |

Prior helper-surface evidence classifies `0x31b110` as a source/RAW/STD adapter
into `0x33fb30`. This caller reads a level/ROI through `0x3d01b0`, then feeds a
source-adapter helper path.

Safe classification: source-adapter caller of `0x3d01b0`.

Non-closure: this static caller window is not a proven owner `+0xf0` runtime
route and does not prove final merge policy.

### `0x3f0f38`: DOFCache Render Caller

`image lookup --address 0x3f0f38` resolves inside
`___lldb_unnamed_symbol10226 + 936`.

The bounded window shows:

| Fact | Raw line |
|---|---:|
| image lookup for `0x3f0f38` | `688` |
| guard text `"Requested DOFCache render with no blur!"` | `710` |
| call to `0x3daf30` at `0x3f0efe` | `813` |
| direct call to `0x3d01b0` at `0x3f0f38` | `823` |
| call to `0x3db3e0` at `0x3f0f54` | `828` |
| call to `0x2c5a10` at `0x3f0fea` | `852` |
| call to `0x2a3ef0` at `0x3f1047` | `866` |

The visible body contains an explicit DOFCache no-blur guard string, builds and
clamps several ROI records, calls one cache/render helper path, calls
`0x3d01b0`, then continues into additional helper calls.

Safe classification: DOFCache render caller of `0x3d01b0`.

Non-closure: this static caller window is not a proven bridge HDR owner `+0xf0`
route and does not prove final merge policy.

## `0x3edb80`: Direct-Caller Set

The callgraph output contains two direct callers:

| Caller | Raw line |
|---|---:|
| `0x3ecc74` | `callers_0x3edb80.txt:2` |
| `0x3ecdc7` | `callers_0x3edb80.txt:3` |

Prior evidence already classifies `0x3ecc74` as visible-`src1` one-image
normalization after a visible read through `0x3d01b0`.

### `0x3ecdc7`: Visible-`src2` One-Image Normalization Wrapper

`image lookup --address 0x3ecdc7` resolves inside
`___lldb_unnamed_symbol10176 + 71`, with body start at `0x3ecd80`.

The bounded window shows:

| Fact | Raw line |
|---|---:|
| image lookup for `0x3ecdc7` | `924` |
| body start at `0x3ecd80` | `928` |
| call to `0x3ebb80` at `0x3ecda8` | `942` |
| direct call to `0x3edb80` at `0x3ecdc7` | `950` |
| returns `true` after temporary descriptor cleanup | `951..958` |

The visible body reads object field `+0x8`, calls `0x3ebb80` to populate a
temporary descriptor, wraps that temporary descriptor, calls `0x3edb80` with
the requested output descriptor, destroys the temporary descriptor, and returns
`true`.

Safe classification: visible-`src2` one-image normalization wrapper through
`0x3ebb80 -> 0x3edb80`.

Non-closure: this does not prove visible `src2` semantic contents or final
contributor acceptance/rejection.

## `0x3d50f0`: Direct-Caller Set

The callgraph output contains one direct caller:

| Caller | Raw line |
|---|---:|
| `0x3d5029` | `callers_0x3d50f0.txt:2` |

Prior evidence already classifies `0x3d5029` as the size-gated call from
`0x3d4e10` into the 6-byte-to-vec4 expansion executor `0x3d50f0`.

Safe static consequence: within the repo-local static direct-callgraph,
`0x3d50f0` has no other direct caller. Remaining unclassified routes to the
same downstream data, if present, must be outside this direct-call set.

Non-closure: this does not cover indirect calls, virtual dispatch, or final
acceptance/rejection.

## Canonical Consequence

This census narrows the direct-call downstream search:

- `0x36f800` direct callers in the current static callgraph are selected-cache
  read/rescale, a TileCache-like read/rescale sibling, and IRAMP-internal
  descriptor resample handoff.
- `0x3d01b0` direct callers in the current static callgraph are exact-size
  selected-cache read, selected-cache temporary read before `0x36f800`,
  visible-`src1` read before `0x3edb80`, a source-adapter caller, and a
  DOFCache render caller.
- `0x3edb80` direct callers in the current static callgraph are visible-`src1`
  and visible-`src2` one-image normalization wrappers.
- `0x3d50f0` has only the previously classified `0x3d4e10` direct caller in
  the current static callgraph.

The remaining final-policy search should not assign final contributor
acceptance/rejection to these direct helper surfaces without new evidence. The
open path is downstream or sideways from them: indirect/vtable routes,
post-resample consumers, row-image consumers, final file/display sinks, or
distributed policy that has not yet been isolated to one direct helper body.
