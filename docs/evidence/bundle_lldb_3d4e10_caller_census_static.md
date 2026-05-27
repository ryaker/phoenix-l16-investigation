# Bundle + LLDB `0x3d4e10` Caller Census Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib`, repo-local static callgraph direct-caller
query for `0x3d4e10`, and bounded LLDB disassembly windows around all direct
callers of that owner `+0xf0` expansion handoff.

This document follows:

- `bundle_lldb_owner_f0_expansion_handoff.md`
- `bundle_lldb_owner_f0_expansion_dest_context.md`
- `bundle_lldb_owner_f0_selected_cache_route_static_classification.md`

Previous runtime proof shows `0x3d4e10` receives a caller-provided context whose
`+0x10` field points to the persistent 16-byte destination descriptor, and that
the local destination descriptor is a clipped view into that context descriptor.
This document asks which direct call sites request `0x3d4e10` in the current
repo-local static callgraph.

It proves:

- The repo-local static callgraph direct callers of `0x3d4e10` are only
  `0x3d484a`, `0x3d486c`, and `0x3d5468`.
- `0x3d484a` and `0x3d486c` are inside body `0x3d47d0`, the already bounded
  read-context branch-router body. They are the post-branch calls immediately
  after branch sites `0x3d4842` and `0x3d4864`.
- `0x3d5468` is inside body `0x3d5400`, a separate loop body that walks indexed
  entries, takes a read lock, calls `0x3d4e10`, unlocks, releases the shared
  object, and continues the loop.
- Inside `0x3d4e10`, the only direct call to `0x3d50f0` is at `0x3d5029`; the
  repo-local direct-caller query for `0x3d50f0` also returns only `0x3d5029`.
- Repo-local direct-caller queries show no direct callers of `0x3d47d0` or
  row worker body `0x3d5290`; prior runtime evidence reaches `0x3d47d0`
  through callable/branch routing, and `0x3d5290` is worker-dispatch plumbing.

It does not prove:

- indirect or vtable caller coverage for `0x3d4e10`
- runtime liveness for the new static loop caller `0x3d5468`
- final file/display sink
- final contributor acceptance, rejection, or suppression policy
- public semantic names for owner `+0xf0`, clipped-view descriptors, row
  channels, or pixel formats

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

- `tools/lldb_probes/static_3d4e10_caller_census_disasm.lldb`

Rerunnable raw outputs under ignored `runs/`:

- `runs/static_3d4e10_caller_census/callers_0x3d4e10.txt`
- `runs/static_3d4e10_caller_census/callers_0x3d50f0.txt`
- `runs/static_3d4e10_caller_census/callers_0x3d47d0.txt`
- `runs/static_3d4e10_caller_census/callers_0x3d5290.txt`
- `runs/static_3d4e10_caller_census/3d4e10_caller_static_disasm.txt`

No probe harness or live evidence dependency for this proof lives in
`/private/tmp`.

## Static Method

The direct-caller set comes from `tools/disasm_callgraph.py callers 0x3d4e10`
against the current repo-local callgraph database. This bounds direct `callq`
edges represented in that database. It does not cover indirect calls, virtual
calls, function-pointer dispatch, or runtime liveness.

The LLDB script creates a static target from the installed `libcp.dylib`, runs
`image lookup` for every direct caller, and captures bounded disassembly windows
around `0x3d47d0`, `0x3d4e10` / `0x3d50f0` / `0x3d5290`, and the separate
`0x3d5400` caller loop.

## Direct-Caller Set

The callgraph output contains three direct callers:

| Caller | Raw line |
|---|---:|
| `0x3d484a` | `callers_0x3d4e10.txt:2` |
| `0x3d486c` | `callers_0x3d4e10.txt:3` |
| `0x3d5468` | `callers_0x3d4e10.txt:4` |

Image lookup maps them to these installed-bundle unnamed-symbol offsets:

| Caller | Lookup raw line | Body family |
|---|---:|---|
| `0x3d484a` | `5..7` | `___lldb_unnamed_symbol9811 + 122` |
| `0x3d486c` | `8..10` | `___lldb_unnamed_symbol9811 + 156` |
| `0x3d5468` | `11..13` | `___lldb_unnamed_symbol9833 + 104` |

## `0x3d47d0`: Branch-Router Direct Calls

`0x3d484a` and `0x3d486c` are inside body `0x3d47d0`.

Raw anchors:

| Fact | Raw line |
|---|---:|
| body start at `0x3d47d0` | `25` |
| branch-site call through slot at `0x3d4840` | `58` |
| post-branch direct call to `0x3d4e10` at `0x3d484a` | `61` |
| sibling post-branch direct call to `0x3d4e10` at `0x3d486c` | `70` |

Prior runtime evidence already proves branch sites `0x3d4842` and `0x3d4864`
under the tested bridge HDR route. This document adds static direct-caller
coverage for the `0x3d4e10` handoff after those branch sites.

Safe classification: the proven branch-router body has two direct post-branch
handoffs into `0x3d4e10`.

Non-closure: direct-callgraph coverage of `0x3d47d0` itself is empty; the
runtime-proven route reaches it through callable/branch routing already covered
by prior evidence.

## `0x3d4e10`: Clipped Expansion Handoff

Raw anchors:

| Fact | Raw line |
|---|---:|
| body start at `0x3d4e10` | `86` |
| clipped source descriptor construction begins from owner `+0xf0` | `125` |
| clipped destination descriptor construction begins from context `+0x10` | `169`, `176` |
| direct call to `0x3d50f0` | `226` |
| local descriptor cleanup after `0x3d50f0` | `227` |

The direct-caller output for `0x3d50f0` contains one direct caller:

| Caller | Raw line |
|---|---:|
| `0x3d5029` | `callers_0x3d50f0.txt:2` |

Safe classification: `0x3d4e10` is the only direct static caller path into
`0x3d50f0` in the repo-local callgraph.

Non-closure: this does not name public pixel-format semantics or final
consumer policy.

## `0x3d50f0` / `0x3d5290`: Expansion Executor Plumbing

Raw anchors:

| Fact | Raw line |
|---|---:|
| `0x3d50f0` body start | `270` |
| alloc/resize helper `0xf540` with element size `16` | `289` |
| generic executor dispatch `0x5670` | `311` |
| row worker body `0x3d5290` start | `410` |

The direct-caller output for `0x3d5290` contains no direct callers; this matches
its role as row-worker dispatch plumbing rather than ordinary direct-call
surface.

Safe classification: `0x3d50f0` dispatches worker `0x3d5290` through executor
plumbing after the `0x3d4e10` handoff.

## `0x3d5400`: Separate Loop Caller

`0x3d5468` is inside body `0x3d5400`.

Raw anchors:

| Fact | Raw line |
|---|---:|
| body start at `0x3d5400` | `455` |
| indexed-entry loop setup | `463` |
| read lock | `483` |
| direct call to `0x3d4e10` | `488` |
| unlock | `490` |

Safe classification: separate static loop caller that walks indexed entries and
invokes the same `0x3d4e10` expansion handoff under a read lock.

Non-closure: no bridge HDR runtime liveness is proven for this loop caller in
this document.

## Canonical Consequence

This census narrows the owner `+0xf0` expansion-handoff caller search. In the
current repo-local static callgraph, direct callers of `0x3d4e10` are only:

- two already bounded branch-router post-branch handoffs inside `0x3d47d0`
- one separate indexed-entry loop body at `0x3d5400`

Therefore the remaining final-policy search should not continue treating
`0x3d4e10` / `0x3d50f0` as unbounded direct-call surfaces. The open work is
runtime liveness for the separate loop caller, public pixel-format semantics,
and downstream row-image/final acceptance policy after these expansion surfaces.
