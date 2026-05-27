# LLDB Evidence: IRAMP Map-Provider Runtime Four-Zoom

## Scope

This note follows the installed-bundle producer path for the `record+0x40` map
pointer in the IRAMP `PipelineCache+0x258` `0x50`-byte records.

It builds on:

- [bundle_proof_iramp_record_producer_scale_and_dispatch.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_record_producer_scale_and_dispatch.md)
- [bundle_proof_iramp_source_record_constructors.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_source_record_constructors.md)
- [bundle_proof_src1_678_virtuals_and_record_consumer.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_src1_678_virtuals_and_record_consumer.md)

It proves runtime target/value binding for:

```text
0x3f7040 -> 0x3f72f0 -> 0x268480 -> UpsampleLayer slot +0x90 -> 0x25e500 -> record+0x40
```

It does not assign a public calibration-field name to the returned map.

## Artifacts

- Static script:
  [static_iramp_map_provider_disasm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/iramp_map_provider_runtime/static_iramp_map_provider_disasm.lldb)
- Runtime probe:
  [map_provider_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/iramp_map_provider_runtime/map_provider_probe.py)
- Runtime LLDB scripts:
  [map_provider_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/iramp_map_provider_runtime/map_provider_28mm.lldb),
  [map_provider_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/iramp_map_provider_runtime/map_provider_35mm.lldb),
  [map_provider_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/iramp_map_provider_runtime/map_provider_70mm.lldb),
  [map_provider_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/iramp_map_provider_runtime/map_provider_150mm.lldb)
- Accepted raw runtime outputs:
  `runs/iramp_map_provider_runtime/map_provider_28mm.{log,json}`,
  `runs/iramp_map_provider_runtime/map_provider_35mm.{log,json}`,
  `runs/iramp_map_provider_runtime/map_provider_70mm.{log,json}`,
  `runs/iramp_map_provider_runtime/map_provider_150mm.{log,json}`
- Raw static output:
  `runs/iramp_map_provider_runtime/static_iramp_map_provider_disasm.log`

Repo-local scan found no `Traceback`, `error:`, `warning:`, `lost connection`,
`EXC`, `SIGABRT`, or JSON `errors` entries in the accepted runtime/static logs.

## Runtime Result

All four accepted bridge HDR runs exited with process status `0`. None hit the
drive step cap.

| Site | Meaning in this probe | `28mm` | `35mm` | `70mm` | `150mm` |
|---|---|---:|---:|---:|---:|
| `0x3f7040` | record dispatcher entry | `5` | `5` | `5` | `5` |
| `0x3f719d` | same-category `0x268480` call | `0` | `0` | `0` | `0` |
| `0x3f71a2` | same-category return after `0x268480` | `0` | `0` | `0` | `0` |
| `0x3f71bb` | same-category after `0x25e500` | `0` | `0` | `0` | `0` |
| `0x3f7480` | cross-category `0x268480` call | `5` | `5` | `5` | `5` |
| `0x3f7485` | cross-category return after `0x268480` | `5` | `5` | `5` | `5` |
| `0x3f749e` | cross-category after `0x25e500` | `5` | `5` | `5` | `5` |
| `0x26848f` | provider virtual call reached from the tracked producer returns | `5` | `5` | `5` | `5` |

The provider virtual-call target was the same in all accepted packets:

| Zoom | Provider type / vtable address point | Slot `+0x90` target | Target body | `0x268480` return count | `record+0x40` count |
|---|---:|---:|---|---:|---:|
| `28mm` | `UpsampleLayer` / `0x658eb0` | `0x26b590` | returns `UpsampleLayer+0x90` | one pointer, `5` hits | same pointer, `5` hits |
| `35mm` | `UpsampleLayer` / `0x658eb0` | `0x26b590` | returns `UpsampleLayer+0x90` | one pointer, `5` hits | same pointer, `5` hits |
| `70mm` | `UpsampleLayer` / `0x658eb0` | `0x26b590` | returns `UpsampleLayer+0x90` | one pointer, `5` hits | same pointer, `5` hits |
| `150mm` | `UpsampleLayer` / `0x658eb0` | `0x26b590` | returns `UpsampleLayer+0x90` | one pointer, `5` hits | same pointer, `5` hits |

The accepted samples also show `record+0x48/+0x4c = (1.0, 1.0)` at the
post-`0x25e500` capture point for all four canonical seeds.

## Static Bounds

All VAs below are installed `libcp.dylib` module VAs.

- `0x3f7040` dispatches by two `0xf6c60`-derived categories.
- In the accepted runtime runs above, only the cross-category branch was reached
  for the tracked `0x3f7040` entries.
- `0x3f72f0` calls `0x268480` at `0x3f7480`.
- `0x268480` reads `context+0x18`, reads the object pointer at `tmp-0x8`, and
  calls the object's vtable slot `+0x90` at `0x26848f`.
- Prior static proof identifies vtable address point `0x658eb0` as
  `UpsampleLayer`; its typeinfo name pointer at `0x658f58` is `0x5db2c0`, and
  the string at `0x5db2c0` is `N2lt13UpsampleLayerE`.
- Static inspection of the selected runtime target `0x26b590` shows it returns
  `UpsampleLayer+0x90`.
- `0x3f7485` receives the `0x268480` return in `rax`.
- `0x3f7496` moves that return value into `rcx`, and `0x3f7499` calls
  `0x25e500`.
- Prior static proof shows `0x25e500` stores its fourth argument into
  `record+0x40`; the accepted runtime packets above directly verify the stored
  `record+0x40` value matches the `0x268480` return value.

## Proven Boundary

- Across the accepted `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR runs, the
  tracked post-wrapper `0x3f7040` producer entries all took the cross-category
  `0x3f72f0` branch.
- Across the same runs, `0x268480` called vtable address point `0x658eb0` slot
  `+0x90 = 0x26b590`; prior static proof identifies `0x658eb0` as
  `UpsampleLayer` by RTTI string `N2lt13UpsampleLayerE`.
- The selected slot body `0x26b590` returns `UpsampleLayer+0x90`.
- Across the same runs, the `0x268480` return pointer is the pointer written
  into the composed `0x50` record at `record+0x40`.

## Non-Claims

- This proof does not assign a public semantic field name to
  `UpsampleLayer+0x90`.
- This proof does not prove which LRI calibration block populated the object
  reached through `state+0xb0`.
- This proof does not prove the public calibration meaning of the map consumed
  by the second pair-grid transform.
- This proof does not prove the same-category branch is dead code. It proves
  zero same-category hits under the accepted four canonical bridge HDR runs
  above.
- This proof does not close `src1` / `src2` reducer behavior, C6 routing, or
  final merge acceptance/rejection.
