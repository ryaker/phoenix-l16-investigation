# LLDB Evidence: UpsampleLayer Map Descriptor Custody

## Scope

This note follows the `UpsampleLayer+0x90` descriptor returned by the tracked
IRAMP map-provider path and stored into `record+0x40`.

It builds on:

- [bundle_proof_src1_678_virtuals_and_record_consumer.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_src1_678_virtuals_and_record_consumer.md)
- [lldb_iramp_map_provider_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_iramp_map_provider_four_zoom.md)
- [bundle_proof_iramp_pair_grid_transform_formula.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_pair_grid_transform_formula.md)

It proves:

- accepted `28mm`, `35mm`, and `70mm` bridge HDR runs populate
  `UpsampleLayer+0x90` through the `0x26ac13 -> 0xf340` copy site before the
  same descriptor is returned by `0x268480` and stored into `record+0x40`
- accepted `150mm` bridge HDR runtime proves the same provider/storage
  descriptor boundary without writer-body instrumentation
- the descriptor consumed through `record+0x40` has visible dimensions
  `4160 x 3120`, stride `4160`, and a nonzero data pointer in the accepted
  samples

It does not assign a public calibration-field name or LRI block origin to that
descriptor.

## Artifacts

- Static script:
  [static_upsample_map_custody_disasm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/upsample_map_custody/static_upsample_map_custody_disasm.lldb)
- Runtime probe:
  [upsample_map_custody_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/upsample_map_custody/upsample_map_custody_probe.py)
- Accepted runtime LLDB scripts:
  [upsample_map_core_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/upsample_map_custody/upsample_map_core_28mm.lldb),
  [upsample_map_core_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/upsample_map_custody/upsample_map_core_35mm.lldb),
  [upsample_map_core_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/upsample_map_custody/upsample_map_core_70mm.lldb),
  [upsample_map_provider_descriptor_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/upsample_map_custody/upsample_map_provider_descriptor_150mm.lldb)
- Rejected runtime LLDB script:
  [upsample_map_core_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/upsample_map_custody/upsample_map_core_150mm.lldb)
- Raw accepted outputs:
  `runs/upsample_map_custody/upsample_map_core_28mm.{log,json}`,
  `runs/upsample_map_custody/upsample_map_core_35mm.{log,json}`,
  `runs/upsample_map_custody/upsample_map_core_70mm.{log,json}`,
  `runs/upsample_map_custody/upsample_map_provider_descriptor_150mm.{log,json}`
- Raw static output:
  `runs/upsample_map_custody/static_upsample_map_custody_disasm.log`

Repo-local scan found no `Traceback`, `error:`, `warning:`, `lost connection`,
`EXC`, `SIGABRT`, or JSON `errors` entries in the accepted runtime/static logs.

## Static Bounds

All VAs below are installed `libcp.dylib` module VAs.

- `0x26a890` constructs an `UpsampleLayer` object and zeroes the embedded
  descriptor region starting at `this+0x90`.
- `0x26b590` returns `this+0x90`.
- `0x26aa10` is an `UpsampleLayer` body that prepares the `this+0x90`
  descriptor:
  `0x26aa30` calls the previous layer's slot `+0x90`, `0x26abe9` calls
  `0x29ed90` to build a stack descriptor, `0x26ac01` computes
  `r14 = this+0x90`, and `0x26ac13` calls `0xf340` with destination
  `this+0x90`.
- Prior consumer proof shows `record+0x40` is consumed as a float-map
  descriptor: the second pair-grid transform reads stride at `map+0x18`, data
  pointer at `map+0x20`, and samples with `movss`.

## Runtime Result

All accepted runs exited with process status `0` and did not hit the drive step
cap.

| Zoom | Writer copy at `0x26ac13` | Writer after `0x26ac18` | Provider `0x26848f` | `record+0x40` captures | Descriptor shape |
|---|---:|---:|---:|---:|---|
| `28mm` | `1` | `1` | `5` | `5` | `4160 x 3120`, stride `4160` |
| `35mm` | `1` | `1` | `5` | `5` | `4160 x 3120`, stride `4160` |
| `70mm` | `1` | `1` | `5` | `5` | `4160 x 3120`, stride `4160` |
| `150mm` | not instrumented in accepted run | not instrumented in accepted run | `5` | `5` | `4160 x 3120`, stride `4160` |

For the accepted `28mm`, `35mm`, and `70mm` writer-core runs:

- the object written at `0x26ac13` is the same object later seen at provider
  virtual call `0x26848f`
- the copy destination is exactly `UpsampleLayer+0x90`
- the provider return is exactly `UpsampleLayer+0x90`
- `record+0x40` stores that same descriptor pointer
- the descriptor is zero before the copy in the captured writer samples and
  has the same visible shape/data-pointer fields after the copy as at provider
  and record-storage time

For the accepted `150mm` provider-descriptor run:

- `0x268480` calls the same `UpsampleLayer` slot `+0x90 = 0x26b590`
- the provider return is exactly `UpsampleLayer+0x90`
- `record+0x40` stores that same descriptor pointer
- the descriptor has the same visible `4160 x 3120`, stride `4160` shape

The attempted `150mm` writer-core run
`runs/upsample_map_custody/upsample_map_core_150mm.{log,json}` is rejected as
evidence for writer custody: it stopped with `EXC_BAD_ACCESS` before capturing
writer/provider samples. It is not cited as accepted proof.

## Proven Boundary

- Across accepted `28mm`, `35mm`, and `70mm` runs,
  `0x26ac13 -> 0xf340` is the runtime writer that copies a populated descriptor
  into `UpsampleLayer+0x90`; that same descriptor is later returned through
  `0x268480` and stored in `record+0x40`.
- Across accepted `28mm`, `35mm`, `70mm`, and `150mm` runs, the tracked
  provider/storage boundary is the same:
  `UpsampleLayer 0x658eb0/+0x90 = 0x26b590 -> UpsampleLayer+0x90 -> record+0x40`.
- Across accepted samples, the descriptor fields consumed by the pair-grid
  formula expose dimensions `4160 x 3120`, stride `4160`, and a nonzero data
  pointer.

## Non-Claims

- This proof does not assign a public calibration-field name to
  `UpsampleLayer+0x90`.
- This proof does not prove the LRI block or protobuf field that populated the
  descriptor data.
- This proof does not prove 150mm writer-body custody at `0x26ac13`; the
  150mm writer-core run is explicitly rejected.
- This proof does not decode the sampled map values.
- This proof does not close `src1` / `src2` reducer behavior, C6 routing, or
  final merge acceptance/rejection.
