# LLDB Evidence: Visible `src1` Indirect Callable Targets Four-Zoom

## Scope

This note resolves the dynamic callable targets for the two indirect call sites
that were left outside
[bundle_lldb_src1_virtual_target_family_static.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_lldb_src1_virtual_target_family_static.md).

The runtime gate is the first visible-`src1` secondary-callable site
`libcp+0x3e4b09`. After that gate is hit, the probe records the first capped
window of calls at:

| Site | Caller body | Callable field | Runtime call instruction |
|---|---|---|---|
| `0x342d99` | `0x342ca0` | owner `+0x1560` | `callq *%r9` |
| `0x3449f0` | `0x344470` | owner `+0x1590` | `callq *%rax` |

The cap is `256` callback packets per call site per LRI. Counts below are
probe-window counts, not algorithm constants.

## Artifacts

- Runtime probe script: [src1_indirect_callable_targets_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src1_indirect_callable_targets/src1_indirect_callable_targets_probe.py)
- Runtime LLDB scripts:
  [src1_indirect_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src1_indirect_callable_targets/src1_indirect_28mm.lldb),
  [src1_indirect_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src1_indirect_callable_targets/src1_indirect_35mm.lldb),
  [src1_indirect_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src1_indirect_callable_targets/src1_indirect_70mm.lldb),
  [src1_indirect_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src1_indirect_callable_targets/src1_indirect_150mm.lldb)
- Static disassembly script: [static_src1_indirect_callable_targets_disasm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src1_indirect_callable_targets/static_src1_indirect_callable_targets_disasm.lldb)
- Raw runtime outputs:
  `runs/src1_indirect_callable_targets/src1_indirect_28mm.{log,json}`,
  `runs/src1_indirect_callable_targets/src1_indirect_35mm.{log,json}`,
  `runs/src1_indirect_callable_targets/src1_indirect_70mm.{log,json}`,
  `runs/src1_indirect_callable_targets/src1_indirect_150mm.{log,json}`
- Raw static output:
  `runs/src1_indirect_callable_targets/static_src1_indirect_callable_targets_disasm.log`

Repo-local scan found no `Traceback`, `error:`, `warning:`, `lost connection`,
`EXC`, `SIGABRT`, or JSON `errors` entries in those runtime/static logs.

## Runtime Result

All four canonical bridge HDR seeds exited with process status `0`. None hit the
drive step cap.

| Zoom | Gate packets | `0x342d99` packets | `0x3449f0` packets | Dynamic target set |
|---|---:|---:|---:|---|
| `28mm` | `1` | `256` | `256` | same two targets below |
| `35mm` | `1` | `256` | `256` | same two targets below |
| `70mm` | `1` | `256` | `256` | same two targets below |
| `150mm` | `1` | `256` | `256` | same two targets below |

The target tuple is identical in every captured packet across the quartet:

| Site | Vtable address point | Slot `+0x30` | Register target | Binding |
|---|---:|---:|---:|---|
| `0x342d99` | `0x65b948` | `0x342b80` | `0x342b80` | owner `+0x1560` callable target |
| `0x3449f0` | `0x65c798` | `0x345920` | `0x345920` | owner `+0x1590` callable target |

The runtime proof therefore closes the previous "indirect target unknown" gap
for these two tested visible-`src1` gated call sites.

## Static Bounds For The Bound Targets

All VAs below are installed `libcp.dylib` module VAs.

| Runtime target | Static bound |
|---|---|
| `0x342b80` | Adapter thunk. It remaps argument registers (`rsi -> rdi`, `rdx -> rsi`, `rcx -> rdx`, `r8 -> rcx`) and jumps to `0x2eb560`. |
| `0x2eb560` | Validates three neutral-white floats, validates Bayer image size/domain and red-coordinate state, allocates/resizes through `0xf540`, then dispatches one of four executor callback objects through `0x5440`. Error strings in the body include `invalid neutral white!`, `invalid bayer image size!`, `invalid bayer image domain!`, and `non-bayer red coordinate!`. |
| `0x345920` | Adapter thunk. It reads `object = *(callable+0x8)`, loads one input float from the call-site `r8` pointer into `xmm0`, passes `object+0x15dc` and `object+0x15fc`, remaps the other descriptor arguments, and jumps to `0x2f53d0`. |
| `0x2f53d0` | Validates two descriptor-like inputs as non-empty and same-sized, checks an owner/config field relationship, allocates/resizes descriptor storage through `0xf540`, builds local vector/descriptor records, and dispatches through helpers including `0xab590`, `0x2f4470`, `0x2f6420`, `0x135d0`, `0x3066d0`, and `0x3048b0`. Error strings in the inspected body include `src invalid!`. |
| `0xab590` | Direct helper inspected because `0x2f53d0` calls it. It validates non-empty image data and positive dimensions, allocates/resizes through `0xf540`, then dispatches a callback object through `0x5440`. |
| `0x2f4470` | Direct helper inspected because `0x2f53d0` calls it. It copies/resizes one descriptor, builds squared coefficient vectors from the helper parameter record, allocates a `0x38`-byte callback object, and dispatches through `0x5440`. |

## Proven Boundary

- The dynamic targets for the two previously unclassified indirect call sites
  inside `0x342ca0` and `0x344470` are now runtime-bound across `28mm`, `35mm`,
  `70mm`, and `150mm`.
- The `0x342ca0` indirect target is the adapter `0x342b80 -> 0x2eb560`.
- The `0x344470` indirect target is the adapter `0x345920 -> 0x2f53d0`.
- Static inspection bounds `0x2eb560` to Bayer-domain validation plus one-source
  executor dispatch.
- Static inspection bounds `0x2f53d0` to two-descriptor validation,
  temporary descriptor/vector setup, and helper dispatch. Its helper call chain
  is not assigned public merge semantics by this proof.

## Non-Claims

- This proof does not identify semantic `src1` or `src2` contents.
- This proof does not close `CLM-PREFUSION-002`.
- This proof does not prove the capped `256` packet windows are exhaustive
  full-render totals.
- This proof does not classify all downstream helper semantics under
  `0x2f53d0`, including `0x2f6420`, `0x3066d0`, and `0x3048b0`.
- This proof does not resolve C6 routing.
- This proof does not resolve final merge acceptance/rejection.
