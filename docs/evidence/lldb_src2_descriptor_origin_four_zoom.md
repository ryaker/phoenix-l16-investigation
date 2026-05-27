# LLDB Evidence: Visible `src2` Source Descriptor Origin Across Four Zooms

## Scope

This proof narrows the previously open visible-`src2` callback `+0x08`
source-descriptor question.

It proves that, on the accepted visible-`src2` path under the canonical bridge
HDR quartet, the descriptor later stored into callback `+0x08` is populated by
a virtual call through the `PipelineCache+0x1d8` object, vtable slot `+0x18`,
with runtime target `libcp+0x406a10`. Prior wrapper evidence identifies
`PipelineCache+0x1d8` as the `FusionCacheBayer` object family and lists
`0x406a10` among that family's methods; this proof adds four-zoom runtime
custody for the descriptor produced by that method.

It does not prove the public semantic name, LRI origin, or final merge role of
that descriptor.

## Artifacts

- Runtime helper:
  [src2_descriptor_origin_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src2_descriptor_origin/src2_descriptor_origin_probe.py)
- Runtime scripts:
  [src2_descriptor_origin_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src2_descriptor_origin/src2_descriptor_origin_28mm.lldb),
  [src2_descriptor_origin_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src2_descriptor_origin/src2_descriptor_origin_35mm.lldb),
  [src2_descriptor_origin_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src2_descriptor_origin/src2_descriptor_origin_70mm.lldb),
  [src2_descriptor_origin_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src2_descriptor_origin/src2_descriptor_origin_150mm.lldb)
- Static source for construction edge:
  `runs/src2_state_3ebb80/static_src2_state_3ebb80.log`
- Prior object-family proof:
  [bundle_proof_src_wrappers.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_src_wrappers.md)
- Runtime logs:
  `runs/src2_descriptor_origin/src2_descriptor_origin_28mm.log`,
  `runs/src2_descriptor_origin/src2_descriptor_origin_35mm.log`,
  `runs/src2_descriptor_origin/src2_descriptor_origin_70mm.log`,
  `runs/src2_descriptor_origin/src2_descriptor_origin_150mm.log`

Commands:

```bash
arch -x86_64 lldb -b -s tools/lldb_probes/src2_descriptor_origin/src2_descriptor_origin_28mm.lldb > runs/src2_descriptor_origin/src2_descriptor_origin_28mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/src2_descriptor_origin/src2_descriptor_origin_35mm.lldb > runs/src2_descriptor_origin/src2_descriptor_origin_35mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/src2_descriptor_origin/src2_descriptor_origin_70mm.lldb > runs/src2_descriptor_origin/src2_descriptor_origin_70mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/src2_descriptor_origin/src2_descriptor_origin_150mm.lldb > runs/src2_descriptor_origin/src2_descriptor_origin_150mm.log
```

## Static Construction Edge

The installed-bundle static log shows the descriptor at `rbp-0x2200` is zeroed
and passed as the output argument to a virtual call through
`PipelineCache+0x1d8`:

- `0x3ebf36`: zeroes `rbp-0x2200`
- `0x3ebf3d`: loads `PipelineCache+0x1d8` into `rdi`
- `0x3ebf45`: loads that object's vtable
- `0x3ebf48`: loads vtable slot `+0x18`
- `0x3ebf4c`: loads `rbp-0x2200` into `r14`
- `0x3ebf5a`: moves `r14` into `rsi`
- `0x3ebf5d`: calls the loaded slot target

Source lines:
`static_src2_state_3ebb80.log:307..314`.

The same stack descriptor is later reloaded and installed into the callback
object used by the generic executor:

- `0x3ec36b`: loads `rbp-0x2200` into `r13`
- `0x3ec375`: passes `r13` to helper `0xf430`
- `0x3ec410`: allocates / initializes the callback object
- `0x3ec41a`: stores `r13` into callback field `+0x08`
- `0x3ec41e`: stores destination descriptor pointer `rbx` into callback field
  `+0x10`
- `0x3ec434`: stores the state tuple pointer into callback field `+0x20`
- `0x3ec43f`: stores the coefficient-table pointer into callback field
  `+0x28`
- `0x3ec462`: dispatches generic executor `0x5440`

Source lines:
`static_src2_state_3ebb80.log:530..532` and
`static_src2_state_3ebb80.log:566..581`.

This static edge ties the runtime-produced descriptor to callback `+0x08`.
Prior evidence already binds callback `+0x08` as the source descriptor consumed
by worker `0x3ed2e0`; see
[lldb_src2_executor_target_28mm.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_src2_executor_target_28mm.md).

## Runtime Probe Method

The runtime helper sets hardware breakpoints at:

- `libcp+0x3ebf5d`: immediately before the virtual call
- `libcp+0x3ebf5f`: immediately after the virtual call

The helper accepts only samples whose saved return address is `libcp+0x3ecdad`,
which scopes the capture to the visible `src2` path. For each accepted before
sample it records:

- `PipelineCache`
- `PipelineCache+0x1d8`
- `PipelineCache+0x1e0`
- source-descriptor output pointer
- descriptor contents before the virtual call
- region tuple passed beside the descriptor
- virtual-call object / vtable / slot `+0x18` target

For accepted after samples it reads the same descriptor again.

## Runtime Summary

| Seed | `before_hits` | `after_hits` | Accepted after | Slot `+0x18` target | Descriptor before | First accepted descriptor after |
|---|---:|---:|---:|---:|---|---|
| `28mm` / `L16_02130` | `57` | `49` | `1` | `0x406a10` | zeroed | `220x220`, stride `220`, data pointer nonzero |
| `35mm` / `L16_03041` | `55` | `50` | `2` | `0x406a10` | zeroed | `234x234`, stride `234`, data pointer nonzero |
| `70mm` / `L16_03434` | `55` | `50` | `2` | `0x406a10` | zeroed | `268x270`, stride `268`, data pointer nonzero |
| `150mm` / `L16_02285` | `25` | `21` | `1` | `0x406a10` | zeroed | `270x270`, stride `270`, data pointer nonzero |

All four summary packets report:

- `slot18_vas: [4221456]`
- `rax_target_vas: [4221456]`
- `4221456 == 0x406a10`
- `"errors": []` in the full JSON packet

Line evidence:

- `28mm`: summary at `src2_descriptor_origin_28mm.log:38`, full JSON at
  `:39`
- `35mm`: summary at `src2_descriptor_origin_35mm.log:36`, full JSON at
  `:37`
- `70mm`: summary at `src2_descriptor_origin_70mm.log:36`, full JSON at
  `:37`
- `150mm`: summary at `src2_descriptor_origin_150mm.log:29`, full JSON at
  `:30`

The hit totals and accepted-sample counts are probe observations, not algorithm
constants.

## Proven Facts

- The accepted visible-`src2` source-descriptor producer call is the virtual
  call at `libcp+0x3ebf5d`.
- That call uses `PipelineCache+0x1d8` as the object and vtable slot `+0x18`
  as the target slot.
- Across `28mm`, `35mm`, `70mm`, and `150mm`, the accepted slot target is
  `libcp+0x406a10`.
- The output descriptor passed in `rsi` is zeroed before the call and contains
  a readable tile descriptor with nonzero data pointer after the call.
- Static construction proof ties that same stack descriptor to callback
  `+0x08`, the source descriptor consumed by the already-bound worker
  `0x3ed2e0`.

## Safe Conclusion

The visible `src2` callback `+0x08` source descriptor is not an unconstrained
mystery pointer. On the accepted canonical bridge HDR path, it is produced
through:

`0x3ebb80 -> PipelineCache+0x1d8/FusionCacheBayer -> vtable slot +0x18 -> 0x406a10 -> stack descriptor rbp-0x2200 -> callback +0x08 -> worker 0x3ed2e0`

This narrows visible `src2` descriptor custody. It does not identify the public
semantic contents of the descriptor, its LRI-origin fields, whether it is an
already selected descriptor, or whether later policy uses its materialized
output in a final merge-quality decision.

## Remaining Unknowns

- public semantic name and LRI origin for the descriptor produced by
  `0x406a10`
- public role of the `0x406a10` method output inside the visible `src2`
  pipeline
- whether the `0x3ed2e0` materialized result is final preparation for an
  already selected descriptor or part of later merge-quality policy
- final contributor acceptance / rejection logic
