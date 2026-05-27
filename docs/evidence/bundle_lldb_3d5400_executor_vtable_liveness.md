# Bundle + LLDB `0x3d5400` Executor Vtable And Liveness Evidence

## Question

The static `0x3d4e10` caller census found direct call site `0x3d5468`
inside loop body `0x3d5400`. This bundle asks whether that loop has a bounded
executor/vtable installation route and whether the `0x3d5468 -> 0x3d4e10`
handoff is live under the canonical bridge HDR quartet.

## Short Answer

- Static evidence binds vtable `0x66a728` slot `+0x30` to thunk `0x3d53c0`.
- Static evidence shows thunk `0x3d53c0` adjusts `rdi` by `+0x8` and jumps to
  `0x3d5400`.
- Static evidence shows `0x3d5400` calls `0x3d4e10` at `0x3d5468`.
- Static evidence shows `0x3d01b0` builds a callback object with vtable
  `0x66a728` at `0x3d0408` and dispatches it through executor `0x5670` at
  `0x3d042b`.
- Runtime first-hit LLDB probes show `0x3d0408`, `0x3d042b`, `0x3d53c0`, and
  first `0x3d5468` liveness for `28mm`, `35mm`, `70mm`, and `150mm`.
- Runtime samples at `0x3d042b` and `0x3d53c0` record callback-object vtable
  module VA `0x66a728` for the canonical quartet.

## What This Does Not Prove

- It does not provide full-render hit counts. The runtime probes intentionally
  stop at the first `0x3d5468` hit.
- It does not close indirect/vtable caller coverage outside the observed
  `0x66a728` executor route.
- It does not assign a public semantic name to the callback object, pair record,
  or selected-cache tile/read fields.
- It does not close final file/display sink, downstream row-image/final policy,
  or final contributor acceptance/rejection.

## Inputs

- Binary: `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Process binary: `/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lri_process`
- Static script:
  `tools/lldb_probes/static_3d5400_executor_vtable_disasm.lldb`
- Runtime probe:
  `tools/lldb_probes/selected_cache_3d5400_liveness/selected_cache_3d5400_liveness_probe.py`
- Runtime LLDB scripts:
  `tools/lldb_probes/selected_cache_3d5400_liveness/3d5400_liveness_28mm.lldb`
  `tools/lldb_probes/selected_cache_3d5400_liveness/3d5400_liveness_35mm.lldb`
  `tools/lldb_probes/selected_cache_3d5400_liveness/3d5400_liveness_70mm.lldb`
  `tools/lldb_probes/selected_cache_3d5400_liveness/3d5400_liveness_150mm.lldb`
- Canonical LRIs:
  `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri`
  `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri`
  `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri`
  `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri`

## Raw Outputs

Static outputs:

- `runs/static_3d5400_executor_vtable/3d5400_executor_vtable_static_disasm.txt`
- `runs/static_3d5400_executor_vtable/callers_0x3d53c0.txt`
- `runs/static_3d5400_executor_vtable/xref_rip_0x66a690.txt`
- `runs/static_3d5400_executor_vtable/xref_rip_0x66a728.txt`
- `runs/static_3d5400_executor_vtable/xref_rip_0x66a788.txt`

Runtime outputs:

- `runs/selected_cache_3d5400_liveness/3d5400_liveness_28mm.json`
- `runs/selected_cache_3d5400_liveness/3d5400_liveness_35mm.json`
- `runs/selected_cache_3d5400_liveness/3d5400_liveness_70mm.json`
- `runs/selected_cache_3d5400_liveness/3d5400_liveness_150mm.json`

The successful runtime reports above were run with LLDB outside the sandbox. Any
earlier sandbox `lost connection` logs in the same `runs/` directory are not
cited as evidence.

## Static Route

Repo-local callgraph output for thunk `0x3d53c0` contains no direct callers:

| Evidence | Raw anchor |
|---|---|
| no direct callgraph caller for `0x3d53c0` | `callers_0x3d53c0.txt:1` |

Repo-local RIP-reference output for `0x66a728` contains three hits:

| RIP ref | Raw anchor |
|---|---|
| `0x3d0408` | `xref_rip_0x66a728.txt:2` |
| `0x3d5363` | `xref_rip_0x66a728.txt:3` |
| `0x3d5384` | `xref_rip_0x66a728.txt:4` |

Installed-bundle LLDB disassembly provides the concrete route:

| Fact | Raw anchor |
|---|---|
| `0x3d0408` loads vtable address `0x66a728` | `3d5400_executor_vtable_static_disasm.txt:30` |
| `0x3d042b` dispatches executor `0x5670` | `3d5400_executor_vtable_static_disasm.txt:37` |
| helper/constructor body `0x3d5350` uses `0x66a728` | `3d5400_executor_vtable_static_disasm.txt:42` |
| copy/body `0x3d5380` uses `0x66a728` | `3d5400_executor_vtable_static_disasm.txt:60` |
| thunk body `0x3d53c0` starts | `3d5400_executor_vtable_static_disasm.txt:85` |
| thunk jumps to `0x3d5400` | `3d5400_executor_vtable_static_disasm.txt:89` |
| loop body `0x3d5400` starts | `3d5400_executor_vtable_static_disasm.txt:115` |
| loop body calls `0x3d4e10` at `0x3d5468` | `3d5400_executor_vtable_static_disasm.txt:148` |
| vtable `0x66a728` memory read starts | `3d5400_executor_vtable_static_disasm.txt:174` |
| vtable slot `+0x30` contains `0x3d53c0` | `3d5400_executor_vtable_static_disasm.txt:178` |

Safe static classification: the `0x3d5468` caller is no longer an unanchored
direct-callgraph edge. It is tied to the selected-cache/level-ROI executor
callback route where `0x3d01b0` builds a `0x66a728` callback object and executor
slot `+0x30` reaches `0x3d53c0 -> 0x3d5400 -> 0x3d5468 -> 0x3d4e10`.

## Runtime First-Hit Quartet

The runtime probes intentionally stop at the first `0x3d5468` hit. Therefore
their hit counts are first-hit probe counts, not full-render counts. In each
JSON, `process.state = stopped` and `exit_status = -1` are expected because the
probe stops the target before render completion.

| Zoom | `0x3d0408` setup | `0x3d042b` dispatch | `0x3d53c0` thunk | `0x3d5468` loop call | Vtable VA in dispatch/thunk samples |
|---|---:|---:|---:|---:|---|
| `28mm` | 1 | 1 | 1 | 1 | `0x66a728` |
| `35mm` | 4 | 3 | 3 | 1 | `0x66a728` |
| `70mm` | 1 | 1 | 1 | 1 | `0x66a728` |
| `150mm` | 3 | 2 | 2 | 1 | `0x66a728` |

Raw JSON anchors:

| Zoom | Evidence |
|---|---|
| `28mm` | `3d5400_liveness_28mm.json:3..21`, `:35`, `:200` |
| `35mm` | `3d5400_liveness_35mm.json:3..21`, `:35`, `:357` |
| `70mm` | `3d5400_liveness_70mm.json:3..21`, `:35`, `:207` |
| `150mm` | `3d5400_liveness_150mm.json:3..21`, `:35`, `:282` |

Safe runtime classification: the `0x66a728` executor route reaches
`0x3d5468 -> 0x3d4e10` before the first-hit probe stop on all four canonical
bridge HDR zooms.

## Closure

This closes the local liveness gap left by the static `0x3d4e10` caller census:
the separate `0x3d5400` loop caller is statically installed through
`0x66a728/+0x30` and is runtime-live at first hit across `28mm`, `35mm`,
`70mm`, and `150mm`.

The remaining end-goal blocker is still downstream row-image/final policy and
final contributor acceptance/rejection after the already classified caller,
helper, post-route, selected-cache, `0x3e5720`, `0x3d4e10`, and `0x3d5400`
executor-route families.
