# LLDB Evidence: Visible `src2` `0x406a10` Branch Split Across Four Zooms

## Scope

This proof narrows the visible-`src2` source-descriptor producer body that was
previously bound as:

`0x3ebb80 -> PipelineCache+0x1d8/FusionCacheBayer -> vtable slot +0x18 -> 0x406a10`

It proves the runtime branch/helper reached inside `0x406a10` under complete
canonical bridge HDR runs:

- `28mm` / `35mm`: object byte `+0x18 = 1`, branch callsite
  `0x40721b -> 0x31b110`
- `70mm` / `150mm`: object byte `+0x18 = 0`, branch callsite
  `0x407458 -> 0x31acf0`

This is a branch/helper custody proof for the visible-`src2` source descriptor.
It does not identify the public semantic name, LRI field origin, final
acceptance/rejection policy, or merge/reducer closure.

## Artifacts

- Runtime helper:
  [src2_406a10_branch_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src2_406a10_branch/src2_406a10_branch_probe.py)
- Runtime scripts:
  [src2_406a10_branch_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src2_406a10_branch/src2_406a10_branch_28mm.lldb),
  [src2_406a10_branch_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src2_406a10_branch/src2_406a10_branch_35mm.lldb),
  [src2_406a10_branch_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src2_406a10_branch/src2_406a10_branch_70mm.lldb),
  [src2_406a10_branch_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src2_406a10_branch/src2_406a10_branch_150mm.lldb)
- Static body log:
  `runs/fusioncachebayer_406a10_static/disasm_406a10.log`
- Runtime logs:
  `runs/src2_406a10_branch/src2_406a10_branch_28mm.log`,
  `runs/src2_406a10_branch/src2_406a10_branch_35mm.log`,
  `runs/src2_406a10_branch/src2_406a10_branch_70mm.log`,
  `runs/src2_406a10_branch/src2_406a10_branch_150mm.log`
- Prior source-descriptor custody proof:
  [lldb_src2_descriptor_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_src2_descriptor_origin_four_zoom.md)
- Prior helper classifications:
  [bundle_lldb_owner_f0_helper_surface_static_classification.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_lldb_owner_f0_helper_surface_static_classification.md),
  [bundle_proof_src1_source_image_producer_topology.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_src1_source_image_producer_topology.md)

Commands:

```bash
arch -x86_64 lldb -b -s tools/lldb_probes/src2_406a10_branch/src2_406a10_branch_28mm.lldb > runs/src2_406a10_branch/src2_406a10_branch_28mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/src2_406a10_branch/src2_406a10_branch_35mm.lldb > runs/src2_406a10_branch/src2_406a10_branch_35mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/src2_406a10_branch/src2_406a10_branch_70mm.lldb > runs/src2_406a10_branch/src2_406a10_branch_70mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/src2_406a10_branch/src2_406a10_branch_150mm.lldb > runs/src2_406a10_branch/src2_406a10_branch_150mm.log
```

All four instrumented runs completed and wrote nonzero HDR outputs:
`runs/src2_406a10_branch/*.hdr`, each `311M` on this machine.

## Static Branch Boundary

The installed-bundle disassembly shows the branch selector inside `0x406a10`:

- `0x406a24..0x406a2a`: after prologue, `r12 = incoming region`,
  `r14 = output descriptor`, `r15 = object`
- `0x406b9f`: `cmpb $0x0, 0x18(%r15)`
- nonzero branch continues toward `0x40721b -> 0x31b110`
- zero branch jumps through `0x406d59` and later reaches
  `0x407458 -> 0x31acf0`

Prior vetted static classifications bound those helper targets:

- `0x31b110`: source image / source RAW / optional STD domain adapter into
  `0x33fb30`
- `0x31acf0`: source-size and optional-domain validation wrapper before
  routing into `0x33f480`

Those classifications are adapter/wrapper classifications, not reducer or final
acceptance policy.

## Runtime Probe Method

The runtime helper sets hardware breakpoints at:

- `0x406a2d`: after `0x406a10` prologue, before first object-field call
- `0x40721b`: callsite to `0x31b110`
- `0x407458`: callsite to `0x31acf0`
- `0x3ebf5f`: caller site immediately after the `0x406a10` virtual call

The entry and branch callbacks accept only `0x406a10` frames whose saved return
address is `0x3ebf5f`, which scopes them to the visible-`src2` source-descriptor
producer call. The after-callback accepts only caller frames whose saved return
address is `0x3ecdad`, matching the already-proven visible-`src2` caller path.

Samples are capped at eight records per category, but hit counters continue for
the full instrumented render. Hit counts are evidence-run observations, not
algorithm constants.

## Runtime Summary

`3256592 == 0x31b110`; `3255536 == 0x31acf0`.

| Seed | Object `+0x18` | `0x31b110` hits | `0x31acf0` hits | Accepted branch targets | First accepted output descriptor | Log anchors |
|---|---:|---:|---:|---|---|---|
| `28mm` / `L16_02130` | `1` | `348` | `0` | `[0x31b110]` | `294x224`, stride `294`, data pointer nonzero | summary `:330`, JSON `:331` |
| `35mm` / `L16_03041` | `1` | `282` | `0` | `[0x31b110]` | `234x234`, stride `234`, data pointer nonzero | summary `:220`, JSON `:221` |
| `70mm` / `L16_03434` | `0` | `0` | `269` | `[0x31acf0]` | `268x270`, stride `268`, data pointer nonzero | summary `:232`, JSON `:233` |
| `150mm` / `L16_02285` | `0` | `0` | `83` | `[0x31acf0]` | `270x268`, stride `270`, data pointer nonzero | summary `:76`, JSON `:77` |

The summary records report:

- `28mm`: `entry_hits=348`, `after_hits=347`,
  `accepted_object_flag_0x18_values=[1]`,
  `accepted_branch_vas=[3256592]`
- `35mm`: `entry_hits=282`, `after_hits=282`,
  `accepted_object_flag_0x18_values=[1]`,
  `accepted_branch_vas=[3256592]`
- `70mm`: `entry_hits=268`, `after_hits=267`,
  `accepted_object_flag_0x18_values=[0]`,
  `accepted_branch_vas=[3255536]`
- `150mm`: `entry_hits=81`, `after_hits=83`,
  `accepted_object_flag_0x18_values=[0]`,
  `accepted_branch_vas=[3255536]`

Small entry/branch/after count differences are debugger scheduling observations
from a multithreaded full render. The load-bearing fact is the branch split and
the zero opposite-branch hit count in each full instrumented run.

## Proven Facts

- The accepted visible-`src2` `0x406a10` path is branch-split by the object's
  byte at `+0x18` under the canonical quartet.
- `28mm` and `35mm` accepted samples have object `+0x18 = 1` and reach
  `0x40721b -> 0x31b110`; `0x31acf0` has zero hits in those runs.
- `70mm` and `150mm` accepted samples have object `+0x18 = 0` and reach
  `0x407458 -> 0x31acf0`; `0x31b110` has zero hits in those runs.
- The output descriptor passed into `0x406a10` is zeroed before the helper
  branch and readable with a nonzero data pointer after return.
- Prior evidence classifies `0x31b110` and `0x31acf0` as source adapter /
  validation-wrapper surfaces, not merge/reducer closure.

## Safe Conclusion

The visible-`src2` `0x406a10` source-descriptor producer is no longer an opaque
single node. Under complete canonical bridge HDR runs it has a focal-tier split:

- `28mm` / `35mm`: `0x406a10(flag +0x18 = 1) -> 0x31b110`
- `70mm` / `150mm`: `0x406a10(flag +0x18 = 0) -> 0x31acf0`

This narrows the descriptor producer into already-classified source adapter /
validation-wrapper families. It does not prove semantic `src2` contents, the
LRI origin of the source descriptor, final contributor acceptance/rejection, or
the merge/reducer closure.

## Remaining Unknowns

- public semantic meaning of the object byte at `+0x18`
- public semantic name and LRI origin for the descriptor produced by `0x406a10`
- whether the materialized `0x3ed2e0` result participates in later
  merge-quality policy or is only preparation for an already selected source
- final contributor acceptance / rejection logic
