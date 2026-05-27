# LLDB Evidence: `0x2f53d0` Downstream Helper Liveness Four-Zoom

## Scope

This note follows the bound visible-`src1` indirect target
`0x3449f0 -> 0x345920 -> 0x2f53d0` from
[lldb_src1_indirect_callable_targets_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_src1_indirect_callable_targets_four_zoom.md).

It classifies the immediate downstream helper surface of `0x2f53d0` under the
first visible-`src1` secondary-callable gate `libcp+0x3e4b09`. Counts are capped
at `128` packets per site per LRI and are therefore lower bounds for nonzero
sites, not algorithm constants.

## Artifacts

- Static script:
  [static_2f53d0_downstream_helpers_disasm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/2f53d0_downstream_helpers/static_2f53d0_downstream_helpers_disasm.lldb)
- Runtime probe:
  [helper_liveness_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/2f53d0_downstream_helpers/helper_liveness_probe.py)
- Runtime LLDB scripts:
  [helper_liveness_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/2f53d0_downstream_helpers/helper_liveness_28mm.lldb),
  [helper_liveness_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/2f53d0_downstream_helpers/helper_liveness_35mm.lldb),
  [helper_liveness_70mm_lazy.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/2f53d0_downstream_helpers/helper_liveness_70mm_lazy.lldb),
  [helper_liveness_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/2f53d0_downstream_helpers/helper_liveness_150mm.lldb)
- Accepted raw runtime outputs:
  `runs/2f53d0_downstream_helpers/helper_liveness_28mm.{log,json}`,
  `runs/2f53d0_downstream_helpers/helper_liveness_35mm.{log,json}`,
  `runs/2f53d0_downstream_helpers/helper_liveness_70mm_lazy.{log,json}`,
  `runs/2f53d0_downstream_helpers/helper_liveness_150mm.{log,json}`
- Raw static output:
  `runs/2f53d0_downstream_helpers/static_2f53d0_downstream_helpers_disasm.log`

Repo-local scan found no `Traceback`, `error:`, `warning:`, `lost connection`,
`EXC`, `SIGABRT`, or JSON `errors` entries in the accepted runtime/static logs.

## Runtime Result

All four accepted bridge HDR runs exited with process status `0`. None hit the
drive step cap.

| Site | Meaning in this probe | `28mm` | `35mm` | `70mm` | `150mm` |
|---|---|---:|---:|---:|---:|
| `0x2f53d0` | target entry | `128` | `128` | `128` | `128` |
| `0x2f55bb` | prebranch `0xab590` call | `128` | `128` | `128` | `128` |
| `0x2f5679` | prebranch `0x2f4470` call | `128` | `128` | `128` | `128` |
| `0x2f59a1` | loop `0x2f6420` call | `128` | `128` | `128` | `128` |
| `0x2f59d4` | loop `0x135d0` call | `128` | `128` | `128` | `128` |
| `0x2f5acc` | final `0x2f6420` call | `128` | `128` | `128` | `128` |
| `0x2f5afe` | final `0x135d0` call | `128` | `128` | `128` | `128` |
| `0x2f5b2c` | positive-branch `0x3066d0` call | `128` | `128` | `128` | `128` |
| `0x2f5bcb` | nonpositive-branch `0x3048b0` call | `0` | `0` | `0` | `0` |
| `0x2f5c84` | postbranch `0xab590` call | `128` | `128` | `128` | `128` |

The `70mm` accepted artifact is the lazy probe. A non-lazy 70mm attempt stopped
before `0x3e4b09` at the known `libcp+0x2e945d` instrumentation race shape and
is not used as evidence for helper liveness.

## Static Bounds

All VAs below are installed `libcp.dylib` module VAs.

| Body | Static bound |
|---|---|
| `0x2f53d0` | Validates source and guide/vst descriptors as non-empty and same-sized, validates pyramid-size relation, allocates/resizes temporary descriptor/vector records, calls `0xab590`, `0x2f4470`, two `0x2f6420` sites, two `0x135d0` sites, and then branches to `0x3066d0` or `0x3048b0` before optional postbranch `0xab590`. Error strings include `src invalid!`, `vst invalid!`, `guide/source image size mismatch!`, and `pyramid size mismatch!`. |
| `0x2f6420` | Builds a region rectangle from an input bounds record or full descriptor dimensions, subtracts `3` from the kernel-size argument, switches over seven supported kernel-size cases, allocates a `0x28`-byte callback object for the selected case, and dispatches through generic executor `0x5440`. Unsupported cases raise `Unsupported bilateral kernel size!`. |
| `0x135d0` | Allocates/resizes a destination descriptor through `0xf540`, allocates a `0x28`-byte callback object containing four descriptor/record pointers, and dispatches through generic executor `0x5440`. |
| `0x3066d0` | Builds a byte vector through helper `0x306e30`, fills it with a deterministic integer recurrence divided by the live `r9d` argument, prepares descriptor storage through `0xf430` / `0xf540`, calls `0x1a3c0` and `0x18f960`, runs four `0x5440` callback-object dispatches with mode values `0..3`, then dispatches a `0x5670` row executor. |
| `0x3048b0` | Validates two input descriptor dimensions match, allocates a `0x40`-byte callback object with destination/source/vst descriptors plus two integer parameters and one byte parameter, then dispatches through `0x5440`. Error string: `src/vst image size mismatch!`. This body had zero runtime hits in the accepted gated four-zoom runs above. |
| `0xab590` | Validates non-empty image data and positive dimensions, allocates/resizes through `0xf540`, then dispatches a callback object through `0x5440`. |
| `0x2f4470` | Copies/resizes one descriptor, builds squared coefficient vectors from a helper parameter record, allocates a `0x38`-byte callback object, and dispatches through `0x5440`. |

## Proven Boundary

- The accepted four-zoom runtime packet shows `0x2f53d0` and the helper calls
  `0xab590`, `0x2f4470`, `0x2f6420`, `0x135d0`, `0x3066d0`, and postbranch
  `0xab590` are live under the first visible-`src1` gate.
- The accepted four-zoom runtime packet shows zero `0x3048b0` hits under the
  same gated probe conditions.
- Static inspection bounds the immediate `0x2f53d0` helper chain to validation,
  descriptor/vector setup, bilateral-kernel-size dispatch, callback-object
  dispatch through `0x5440`, and one row-executor dispatch through `0x5670`.

## Non-Claims

- This proof does not classify the callback bodies invoked by `0x5440` or
  `0x5670`.
- This proof does not assign public algorithm names to `src`, `guide`, `vst`,
  bilateral-kernel, or row-executor fields.
- This proof does not identify semantic `src1` or `src2` contents.
- This proof does not close `CLM-PREFUSION-002`.
- This proof does not prove the capped `128` packet windows are exhaustive
  full-render totals for nonzero sites.
- This proof does not resolve C6 routing.
- This proof does not resolve final merge acceptance/rejection.
