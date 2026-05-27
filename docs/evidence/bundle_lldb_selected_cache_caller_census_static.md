# Bundle + LLDB Selected-Cache Caller Census Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib`, repo-local static callgraph direct-caller
query for `0x3d0650`, and bounded LLDB disassembly windows around all direct
callers of that selected-cache read/rescale body.

This document follows:

- `bundle_lldb_owner_f0_selected_cache_route_static_classification.md`
- `bundle_lldb_downstream_route_caller_census_static.md`

The previous selected-cache route proof classifies `0x3d0650` as an exact-size
read or read-then-`0x36f800` rescale body. This document asks a different
static question: which direct call sites request that selected-cache body in
the repo-local static callgraph, and what kind of plumbing surrounds those
calls?

It proves:

- The repo-local static callgraph direct callers of `0x3d0650` are only
  `0x3a1cf9`, `0x3a265e`, `0x3a743e`, `0x3b07a4`, `0x3bb57e`,
  `0x3bb5f0`, `0x3bb620`, `0x3bb7d5`, `0x3bb81d`, `0x3bb930`,
  `0x3bba43`, `0x3eca15`, `0x42fb56`, and `0x42fe00`.
- The `0x3a1cf9`, `0x3a265e`, and `0x3a743e` windows call `0x3d0650` and
  then feed `0x31b110`, which prior helper-surface evidence classifies as a
  source/RAW/STD adapter into `0x33fb30`.
- `0x3b07a4` is the small `0x3b0740` owner-cache selector body already present
  in the runtime-proven parent-chain family: it chooses object field `+0x6b8`
  or `+0x688`, calls `0x3d0650`, and returns.
- `0x3bb57e`, `0x3bb5f0`, `0x3bb620`, `0x3bb7d5`, `0x3bb81d`,
  `0x3bb930`, and `0x3bba43` are branch arms inside one larger
  owner/tile-cache surface, body `0x3bb2b0`. Those arms call `0x3d0650` from
  object field `+0x6b8` or `+0x688`, and several continuations feed
  `0x31b110`.
- `0x3eca15` is a branch inside the owner `+0xf0` output-sink body
  `0x3ec960`: one branch reaches `0x3d0650`, sibling branches reach
  `0x3ebb80` or `0x3ec770`, and the common continuation reaches `0x2d7320`
  then `0x3e5720`.
- `0x42fb56` calls `0x3d0650` and then `0x432db0`.
- `0x42fe00` calls `0x3d0650`, then `0x2d7320`, `0x3e0b90`, and `0x31b110`.

It does not prove:

- indirect or vtable caller coverage for `0x3d0650`
- runtime liveness for every static caller listed here
- final file/display sink
- final contributor acceptance, rejection, or suppression policy
- public semantic names for the selected-cache objects, branch controls,
  helper fields, row/image channels, or pixel formats
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

- `tools/lldb_probes/static_selected_cache_caller_census_disasm.lldb`

Rerunnable raw outputs under ignored `runs/`:

- `runs/static_selected_cache_caller_census/callers_0x3d0650.txt`
- `runs/static_selected_cache_caller_census/selected_cache_caller_static_disasm.txt`

Auxiliary direct-caller query outputs retained with the same run:

- `runs/static_selected_cache_caller_census/callers_0x3e5720.txt`
- `runs/static_selected_cache_caller_census/callers_0x3d0d20.txt`

No probe harness or live evidence dependency for this proof lives in
`/private/tmp`.

## Static Method

The direct-caller set comes from `tools/disasm_callgraph.py callers 0x3d0650`
against the current repo-local callgraph database. This bounds direct `callq`
edges represented in that database. It does not cover indirect calls, virtual
calls, function-pointer dispatch, or runtime liveness.

The LLDB script creates a static target from the installed `libcp.dylib`, runs
`image lookup` for every direct caller, then captures bounded disassembly
windows around the caller bodies and branch clusters.

## Direct-Caller Set

The callgraph output contains fourteen direct callers:

| Caller | Raw line |
|---|---:|
| `0x3a1cf9` | `callers_0x3d0650.txt:2` |
| `0x3a265e` | `callers_0x3d0650.txt:3` |
| `0x3a743e` | `callers_0x3d0650.txt:4` |
| `0x3b07a4` | `callers_0x3d0650.txt:5` |
| `0x3bb57e` | `callers_0x3d0650.txt:6` |
| `0x3bb5f0` | `callers_0x3d0650.txt:7` |
| `0x3bb620` | `callers_0x3d0650.txt:8` |
| `0x3bb7d5` | `callers_0x3d0650.txt:9` |
| `0x3bb81d` | `callers_0x3d0650.txt:10` |
| `0x3bb930` | `callers_0x3d0650.txt:11` |
| `0x3bba43` | `callers_0x3d0650.txt:12` |
| `0x3eca15` | `callers_0x3d0650.txt:13` |
| `0x42fb56` | `callers_0x3d0650.txt:14` |
| `0x42fe00` | `callers_0x3d0650.txt:15` |

Image lookup maps them to these installed-bundle unnamed-symbol offsets:

| Caller | Lookup raw line | Body family |
|---|---:|---|
| `0x3a1cf9` | `5..7` | `___lldb_unnamed_symbol9267 + 761` |
| `0x3a265e` | `8..10` | `___lldb_unnamed_symbol9270 + 430` |
| `0x3a743e` | `11..13` | `___lldb_unnamed_symbol9288 + 750` |
| `0x3b07a4` | `14..16` | `___lldb_unnamed_symbol9395 + 100` |
| `0x3bb57e` | `17..19` | `___lldb_unnamed_symbol9488 + 718` |
| `0x3bb5f0` | `20..22` | `___lldb_unnamed_symbol9488 + 832` |
| `0x3bb620` | `23..25` | `___lldb_unnamed_symbol9488 + 880` |
| `0x3bb7d5` | `26..28` | `___lldb_unnamed_symbol9488 + 1317` |
| `0x3bb81d` | `29..31` | `___lldb_unnamed_symbol9488 + 1389` |
| `0x3bb930` | `32..34` | `___lldb_unnamed_symbol9488 + 1664` |
| `0x3bba43` | `35..37` | `___lldb_unnamed_symbol9488 + 1939` |
| `0x3eca15` | `38..40` | `___lldb_unnamed_symbol10158 + 181` |
| `0x42fb56` | `41..43` | `___lldb_unnamed_symbol10733 + 22` |
| `0x42fe00` | `44..46` | `___lldb_unnamed_symbol10736 + 208` |

## Source-Adapter Caller Windows

Three caller windows call `0x3d0650` and then call `0x31b110`.

| Caller | Body start | `0x3d0650` call | Post-call adapter / helper anchors |
|---|---:|---:|---|
| `0x3a1cf9` | `49` | `212` | `0x31b110` at `229` |
| `0x3a265e` | `261` | `354` | `0x31b110` at `370`; `0x37aa70` at `383` |
| `0x3a743e` | `396` | `550` | `0x31b110` at `566`; later cache/update helpers continue in the captured window |

Prior helper-surface evidence classifies `0x31b110` as a source/RAW/STD adapter
into `0x33fb30`.

Safe classification: static selected-cache read callers that feed source-adapter
plumbing.

Non-closure: these static windows are not final contributor policy and are not
runtime liveness proof for every listed caller.

## `0x3b0740`: Small Owner-Cache Selector

`0x3b07a4` is inside body `0x3b0740`.

Raw anchors:

| Fact | Raw line |
|---|---:|
| body start at `0x3b0740` | `608` |
| reads selector data through `0x3c6f80` | `623` |
| reads object field `+0x6b8` | `626` |
| calls `0x3f06d0` | `627` |
| selected `+0x6b8` branch | `630` |
| selected `+0x688` branch | `632` |
| direct call to `0x3d0650` | `637` |

Prior parent-chain runtime evidence already includes return site `0x3b07a9`.

Safe classification: small owner-cache selector into `0x3d0650`.

Non-closure: the selector is not final contributor policy.

## `0x3bb2b0`: Multi-Branch Owner/Tile-Cache Surface

Seven direct `0x3d0650` callers are branch arms inside body `0x3bb2b0`:

| Caller | Raw line |
|---|---:|
| `0x3bb57e` | `798` |
| `0x3bb5f0` | `818` |
| `0x3bb620` | `826` |
| `0x3bb7d5` | `918` |
| `0x3bb81d` | `934` |
| `0x3bb930` | `991` |
| `0x3bba43` | `1048` |

Raw anchors:

| Fact | Raw line |
|---|---:|
| body start at `0x3bb2b0` | `648` |
| descriptor allocation through `0xf540` | `771` |
| computed branch jump | `781` |
| branch reads through object field `+0x6b8` | `788`, `793`, `808`, `813`, `908`, `913` |
| branch reads through object field `+0x688` | `822`, `929`, `986`, `1043` |
| continuations call `0x31b110` | `839`, `947`, `1004`, `1061` |

Prior parent-chain runtime evidence includes return site `0x3bb822` for the
owner-cache rescale family. This static window shows that `0x3bb822` is one of
several branch continuations after `0x3d0650`, not the whole static caller
surface.

Safe classification: multi-branch owner/tile-cache caller surface around
`0x3d0650`, with multiple branches feeding source-adapter plumbing.

Non-closure: this does not prove every branch is live in bridge HDR, and it
does not prove final contributor acceptance/rejection.

## `0x3ec960`: Owner `+0xf0` Output-Sink Branch

`0x3eca15` is inside body `0x3ec960`, which prior evidence already classifies
as the owner `+0xf0` output-descriptor sink.

Raw anchors:

| Fact | Raw line |
|---|---:|
| body start at `0x3ec960` | `1066` |
| branch through `0x3e0af0` | `1106` |
| branch call to `0x3d0650` | `1116` |
| sibling branch call to `0x3ebb80` | `1125` |
| sibling branch call to `0x3ec770` | `1130` |
| common continuation at `0x3eca4b` | `1131` |
| call to `0x2d7320` | `1144` |
| call to `0x3e5720` | `1150` |

Safe classification: owner `+0xf0` output-sink branch that can source its
temporary descriptor through selected-cache read/rescale, sibling wrapper
paths, then common vector-scale and `0x3e5720` conversion/output plumbing.

Non-closure: this does not prove which branch is taken by every runtime packet,
public source semantics, or final acceptance/rejection.

## `0x42fb40` And `0x42fd30`: Later Static Caller Surfaces

`0x42fb56` is inside body `0x42fb40`.

Raw anchors:

| Fact | Raw line |
|---|---:|
| body start at `0x42fb40` | `1154` |
| direct call to `0x3d0650` | `1161` |
| call to `0x432db0` | `1167` |

`0x42fe00` is inside body `0x42fd30`.

Raw anchors:

| Fact | Raw line |
|---|---:|
| body start at `0x42fd30` | `1175` |
| branch through `0x3e0af0` | `1229` |
| direct call to `0x3d0650` | `1237` |
| call to `0x2d7320` | `1251` |
| call to `0x3e0b90` | `1254` |
| call to `0x31b110` | `1299` |

Safe classification: later static selected-cache caller surfaces that continue
into helper/adaptor plumbing after `0x3d0650`.

Non-closure: no bridge HDR runtime liveness is proven here, and these windows
do not identify final contributor policy.

## Canonical Consequence

This census narrows the `0x3d0650` direct-caller search. In the current
repo-local static callgraph, direct callers of the selected-cache read/rescale
body fall into:

- three source-adapter-style caller windows
- one small owner-cache selector body
- one multi-branch owner/tile-cache surface
- the owner `+0xf0` output-sink branch body
- two later helper/adaptor caller surfaces around `0x42fb40` and `0x42fd30`

The remaining final-policy search should not treat `0x3d0650` or its direct
caller set as final contributor acceptance/rejection without new evidence.
Runtime proof still controls liveness, and direct-callgraph proof still does not
cover indirect/vtable routes.
