# LLDB Evidence: `0x267010` Source-Index To Lookup-Float Mapping, Four Zoom

## Scope

This note validates the next Opus-quarantine residual upstream of the
`StereoLayer<false>` index-5 descriptor consumed by the `0x29ed90`
guided-upsample path.

It builds on:

- [lldb_index5_origin_classification_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_index5_origin_classification_four_zoom.md)
- [lldb_upsample_29ed90_worker_formula.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_upsample_29ed90_worker_formula.md)
- [lldb_stereolayer_index5_depth_descriptor_custody.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_stereolayer_index5_depth_descriptor_custody.md)

It proves a narrow runtime mapping fact:

- at `0x267010`, the `rsi` source descriptor is sampled as 16-bit entries;
- the `rdx` vector stores 4-byte float lookup values;
- for each sampled source entry, `lookup[source_u16]` exactly matches the
  corresponding 4-byte float in the stack descriptor observed after
  `0x267010` returns at `0x26e638`;
- this holds for the first 16 sampled entries of all six
  `StereoLayer<false>` indices `0..5` under `28mm`, `35mm`, `70mm`, and
  `150mm` no-auto-LRIS bridge-HDR runs.

It does not prove public physical meaning, public LRI/protobuf origin, full-map
statistics, final source contribution, anti-ghosting behavior, or final
acceptance/rejection.

## Artifacts

- Runtime probe:
  [index5_267010_mapping_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_index5_267010_mapping/index5_267010_mapping_probe.py)
- Runtime LLDB scripts:
  [index5_mapping_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_index5_267010_mapping/index5_mapping_28mm.lldb),
  [index5_mapping_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_index5_267010_mapping/index5_mapping_35mm.lldb),
  [index5_mapping_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_index5_267010_mapping/index5_mapping_70mm.lldb),
  [index5_mapping_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_index5_267010_mapping/index5_mapping_150mm.lldb)
- Runners:
  [run_four_zoom.sh](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_index5_267010_mapping/run_four_zoom.sh),
  [run_150.sh](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_index5_267010_mapping/run_150.sh)
- Raw outputs:
  `runs/codex_index5_267010_mapping/`

The accepted current artifacts have no `Traceback`, `error:`, `warning:`,
`lost connection`, `EXC`, or `SIGABRT` matches. All accepted JSON reports have
empty `errors` arrays.

## Runtime Result

All accepted runs used `--profile 3 --export-fmt 3 --no-auto-lris`, exited with
status `0`, avoided the probe step cap, and emitted files identified by the OS
`file` command as `Radiance HDR image data`.

| Focal tier | Build hits | After-build hits | JSON errors | Step cap | Output |
|---|---:|---:|---:|---|---|
| `28mm` | 6 | 6 | 0 | no | Radiance HDR |
| `35mm` | 6 | 6 | 0 | no | Radiance HDR |
| `70mm` | 6 | 6 | 0 | no | Radiance HDR |
| `150mm` | 6 | 6 | 0 | no | Radiance HDR |

The first full four-zoom run produced accepted `28mm`, `35mm`, and `70mm`
artifacts but rejected `150mm` before either mapping breakpoint fired. That
failed 150mm packet is not cited here. The admitted `150mm` facts come from the
subsequent isolated `run_150.sh` retry, which exited cleanly and overwrote the
raw `150mm` report/log/HDR with accepted artifacts.

## Proven Mapping

For every accepted focal tier, `0x267010` is reached six times for
`StereoLayer<false>` indices `0..5`. The source descriptor dimensions match the
pyramid dimensions, and the lookup vector length is tiered:

| Focal tiers | StereoLayer indices | Source descriptor sizes | Lookup count |
|---|---|---|---:|
| `28mm`, `35mm` | `0..5` | `65x49`, `130x98`, `260x195`, `520x390`, `1040x780`, `2080x1560` | 752 |
| `70mm`, `150mm` | `0..5` | `65x49`, `130x98`, `260x195`, `520x390`, `1040x780`, `2080x1560` | 1472 |

The probe read the first 16 source entries as `uint16`, read
`lookup[source_u16]` as `float32`, then compared those values with the first 16
float32 values in the stack descriptor after `0x267010` returned at
`0x26e638`. Every comparison matched for every captured index under all four
focal tiers.

Representative index-5 samples:

| Focal tier | First source `uint16` entries | First lookup floats | First built floats |
|---|---|---|---|
| `28mm` | `213, 212, 212, 212` | `704.609, 707.929, 707.929, 707.929` | `704.609, 707.929, 707.929, 707.929` |
| `35mm` | `32, 31, 32, 32` | `4661.022, 4810.247, 4661.022, 4661.022` | `4661.022, 4810.247, 4661.022, 4661.022` |
| `70mm` | `0, 0, 0, 0` | `640000.0, 640000.0, 640000.0, 640000.0` | `640000.0, 640000.0, 640000.0, 640000.0` |
| `150mm` | `20, 20, 20, 21` | `14383.891, 14383.891, 14383.891, 13713.620` | `14383.891, 14383.891, 14383.891, 13713.620` |

## Proven Boundary

Across the canonical four-zoom bridge-HDR quartet, with same-name LRIS
auto-loading disabled:

```text
StereoLayer<false> object
  -> source descriptor passed as 0x267010 rsi
  -> first sampled source entries read as uint16 indices
  -> lookup vector passed as 0x267010 rdx
  -> lookup[source_u16] float32 values
  -> stack destination descriptor observed after 0x267010 at 0x26e638
  -> later move into StereoLayer<false>+0x2a8
```

This narrows the prior source descriptor / lookup-vector unknown to an internal
sampled mapping fact: the tested source descriptor is an index image into a
tiered float lookup table for the sampled entries. It still does not identify
the public field names, upstream producer of the source index image, public
calibration/LRI origin of the lookup table, or physical meaning of the
resulting float values.

## Non-Claims

- This proof does not identify a public LRI/protobuf field name.
- This proof does not prove the descriptor is metric depth, disparity, inverse
  depth, confidence, or any other public physical quantity.
- This proof does not prove full-map statistics from the first sampled entries.
- This proof does not identify the upstream producer of the `uint16` source
  descriptor.
- This proof does not identify the public calibration origin of the lookup
  vector.
- This proof does not prove final merge source contribution, anti-ghosting
  behavior, or final acceptance/rejection.
