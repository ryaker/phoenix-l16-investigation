# LLDB Evidence: UpsampleLayer Depth-Path Builder

## Scope

This note follows the producer that fills the `UpsampleLayer+0x90` descriptor
already proven as the map stored into pair-grid `record+0x40`.

It builds on:

- [lldb_iramp_map_provider_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_iramp_map_provider_four_zoom.md)
- [lldb_upsample_map_custody.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_upsample_map_custody.md)

It proves:

- accepted `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR runs all execute the
  same focused `UpsampleLayer` builder path once
- the live builder takes a previous-layer `+0x90` descriptor shaped
  `2080 x 1560`, stride `2080`, calls `0x29ed90`, receives a `4160 x 3120`,
  stride-`4160` descriptor, copies it through `0x2673a0`, then moves it into
  `UpsampleLayer+0x90` through `0x26ac13 -> 0xf340`
- static installed-bundle evidence labels the `UpsampleLayer+0x90` debug dump
  path with `depth_` plus `.dp`

It does not assign a public LRI/protobuf field origin to this depth-path input
or output. This note itself does not decode the formula of the `0x29ed90`
worker body; the follow-up worker proof is
[lldb_upsample_29ed90_worker_formula.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_upsample_29ed90_worker_formula.md).

## Artifacts

- Static script:
  [static_upsample_layer_depth_path.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/upsample_map_semantics/static_upsample_layer_depth_path.lldb)
- Runtime LLDB scripts:
  [upsample_depth_path_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/upsample_map_semantics/upsample_depth_path_28mm.lldb),
  [upsample_depth_path_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/upsample_map_semantics/upsample_depth_path_35mm.lldb),
  [upsample_depth_path_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/upsample_map_semantics/upsample_depth_path_70mm.lldb),
  [upsample_depth_path_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/upsample_map_semantics/upsample_depth_path_150mm.lldb)
- Runtime probe module reused from the custody proof:
  [upsample_map_custody_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/upsample_map_custody/upsample_map_custody_probe.py)
- Raw accepted outputs:
  `runs/upsample_map_semantics/upsample_depth_path_28mm.{log,json}`,
  `runs/upsample_map_semantics/upsample_depth_path_35mm.{log,json}`,
  `runs/upsample_map_semantics/upsample_depth_path_70mm.{log,json}`,
  `runs/upsample_map_semantics/upsample_depth_path_150mm.{log,json}`
- Raw static output:
  `runs/upsample_map_semantics/static_upsample_layer_depth_path.log`

Repo-local scan found no `Traceback`, `error:`, `warning:`, `lost connection`,
`EXC`, `SIGABRT`, or JSON `errors` entries in the accepted runtime/static logs.

## Static Bounds

All VAs below are installed `libcp.dylib` module VAs.

- `0x26aa10` is the `UpsampleLayer` run body.
- `0x26aa30` calls the previous layer's slot `+0x90`; the return is held in
  `r14`.
- `0x26ab99 -> 0x2673a0` copies the previous-layer descriptor into a stack
  descriptor.
- `0x26abe9 -> 0x29ed90` builds the next stack descriptor from that copied
  previous-layer descriptor plus `UpsampleLayer` inputs.
- `0x26abfc -> 0x2673a0` copies the built descriptor into another stack
  descriptor.
- `0x26ac13 -> 0xf340` moves the built descriptor into `UpsampleLayer+0x90`.
- The debug-output branch gated by `UpsampleLayer+0x89` uses `0x22fa40` to
  write `UpsampleLayer+0x90` with a filename assembled from `depth_` and `.dp`.
- The same debug-output branch labels `UpsampleLayer+0xc0` with `conf_` and
  `.fst`, a derived depth image with `depth_` and `.jpg`, and the object at
  `UpsampleLayer+0x8` with `guidance_` and `.bmp`.
- `0x29ed90` constructs a callback object and dispatches work through `0x5440`.
  The statically adjacent worker family reaches a float store into the output
  descriptor. This note leaves the worker formula to the follow-up worker proof.

## Runtime Result

All accepted runs exited with process status `0` and did not hit the drive step
cap.

| Zoom | `0x26aa10` | previous `+0x90` | `0x29ed90` call | `0x29ed90` output | final `0xf340` source |
|---|---:|---|---:|---|---|
| `28mm` | `1` | `2080 x 1560`, stride `2080` | `1` | `4160 x 3120`, stride `4160` | `4160 x 3120`, stride `4160` |
| `35mm` | `1` | `2080 x 1560`, stride `2080` | `1` | `4160 x 3120`, stride `4160` | `4160 x 3120`, stride `4160` |
| `70mm` | `1` | `2080 x 1560`, stride `2080` | `1` | `4160 x 3120`, stride `4160` | `4160 x 3120`, stride `4160` |
| `150mm` | `1` | `2080 x 1560`, stride `2080` | `1` | `4160 x 3120`, stride `4160` | `4160 x 3120`, stride `4160` |

For each accepted runtime:

- `0x26aa30` reaches the previous layer's slot `+0x90`.
- `0x26aa39` observes the returned previous-layer descriptor.
- `0x26abe9` calls `0x29ed90` with a copied previous-layer descriptor shaped
  `2080 x 1560`, stride `2080`.
- `0x26abee` observes the `0x29ed90` destination descriptor shaped
  `4160 x 3120`, stride `4160`, with a nonzero data pointer.
- `0x26abfc` copies that built descriptor.
- `0x26ac13` passes a `4160 x 3120`, stride-`4160` source descriptor to
  `0xf340` for the move into `UpsampleLayer+0x90`.

## Proven Boundary

Across accepted `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR runs, the map
descriptor stored in `record+0x40` is internally produced by the
`UpsampleLayer` depth-path:

```text
previous layer +0x90 descriptor
  -> 0x2673a0 stack copy
  -> 0x29ed90 builder
  -> 0x2673a0 stack copy
  -> 0x26ac13 / 0xf340
  -> UpsampleLayer+0x90
  -> 0x268480 / 0x26b590 provider
  -> pair-grid record+0x40
```

The installed bundle's own debug strings label the `UpsampleLayer+0x90`
descriptor as the `depth_... .dp` output under the disabled debug-output branch.
That is an internal installed-bundle label, not a public LRI field name.

## Non-Claims

- This proof does not prove the LRI block or protobuf field that supplies the
  inputs to `0x29ed90`.
- This proof does not decode the `0x29ed90` worker formula; see
  [lldb_upsample_29ed90_worker_formula.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_upsample_29ed90_worker_formula.md).
- This proof does not map `depth_... .dp` to any public Light/LRI schema name.
- This proof does not decode the `UpsampleLayer+0xc0` `conf_... .fst` path.
- This proof does not close `src1` / `src2` reducer behavior, C6 routing, or
  final merge acceptance/rejection.
