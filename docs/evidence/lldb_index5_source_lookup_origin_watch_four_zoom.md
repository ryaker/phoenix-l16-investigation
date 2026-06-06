# LLDB Evidence: Index-5 Source / Lookup Origin Watch, Four Zoom

## Scope

This note extends the `0x267010` / `0x299c70` source-index descriptor chain:

- [lldb_index5_267010_mapping_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_index5_267010_mapping_four_zoom.md)
- [lldb_source_index_299c70_producer_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_source_index_299c70_producer_four_zoom.md)
- [lldb_source_index_299c70_worker_formula_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_source_index_299c70_worker_formula_four_zoom.md)

It proves a narrow runtime custody boundary for the index-5
`StereoLayer<false>` object under canonical no-auto-LRIS bridge-HDR runs:

- the lookup-vector header at `StereoLayer<false>+0xe0` is live-populated
  through the `0xf02d0` allocation/fill path, with the final observed header
  write at `0xf043e`;
- the source-object control qword at `StereoLayer<false>+0xf8` is written at
  `0x26be62`;
- the populated same object later reaches the proven `0x26e4c6 -> 0x299c70`
  source-index producer path and the `0x26e620 -> 0x267010` lookup-vector
  builder path;
- the lookup-vector counts are `752` for `28mm` / `35mm` and `1472` for
  `70mm` / `150mm`;
- the source object consumed by the later producer samples has dimensions
  `2080 x 1560` and stride `2080`.

It does not prove public field names, public LRI/protobuf origin, public
calibration semantics, physical meaning, full-map statistics, final source
contribution, anti-ghosting behavior, or final acceptance/rejection.

## Artifacts

- Runtime probe:
  [source_lookup_origin_watch_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_index5_source_lookup_origin_watch/source_lookup_origin_watch_probe.py)
- Admitted runtime LLDB scripts:
  [source_lookup_origin_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_index5_source_lookup_origin_watch/source_lookup_origin_28mm.lldb),
  [source_lookup_origin_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_index5_source_lookup_origin_watch/source_lookup_origin_35mm.lldb),
  [source_lookup_origin_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_index5_source_lookup_origin_watch/source_lookup_origin_70mm.lldb),
  [source_lookup_origin_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_index5_source_lookup_origin_watch/source_lookup_origin_150mm.lldb)
- Raw outputs:
  `runs/codex_index5_source_lookup_origin_watch/`

The admitted JSON reports have no matches for `Traceback`, `error:`,
`warning:`, `lost connection`, `EXC`, `SIGABRT`, or `SIGSEGV`.

## Runtime Result

All accepted runs used `--profile 3 --export-fmt 3 --no-auto-lris`, exited with
status `0`, avoided the probe step cap, and emitted files identified by the OS
`file` command as `Radiance HDR image data`.

Each accepted run recorded six hits at each instrumented site:

```text
0x26b750  StereoLayer constructor
0x26bbd0  index setter
0x26e4c6  source-index branch
0x299c70  source-index producer entry
0x26e620  lookup-vector setup
0x267010  descriptor builder entry
0x26e638  descriptor builder return window
```

| Focal tier | Lookup count | Lookup bytes | Live lookup write | Source-control write | Later source sample | Output |
|---|---:|---:|---|---|---|---|
| `28mm` | 752 | 3008 | `0xf043e` | `0x26be62` | `2080 x 1560`, stride `2080` | Radiance HDR |
| `35mm` | 752 | 3008 | `0xf043e` | `0x26be62` | `2080 x 1560`, stride `2080` | Radiance HDR |
| `70mm` | 1472 | 5888 | `0xf043e` | `0x26be62` | `2080 x 1560`, stride `2080` | Radiance HDR |
| `150mm` | 1472 | 5888 | `0xf043e` | `0x26be62` | `2080 x 1560`, stride `2080` | Radiance HDR |

The final live lookup-vector write has the same stack prefix in all four
accepted runs:

```text
0xf043e <- 0x26c4dc <- 0x26bdf8 <- 0x26895a <- 0x2687ab <- 0x3fcb86
```

The source-control write has the same stack prefix in all four accepted runs:

```text
0x26be62 <- 0x26895a <- 0x2687ab <- 0x3fcb86 <- 0x3feb2f <- 0x3fbcb3
```

Representative first lookup floats, included only as run-local examples and
not as constants:

| Focal tier | First four lookup floats |
|---|---|
| `28mm` | `640000.0`, `121681.015625`, `67231.78125`, `46447.62109375` |
| `35mm` | `640000.0`, `121681.015625`, `67231.78125`, `46447.62109375` |
| `70mm` | `640000.0`, `201593.15625`, `119639.09375`, `85059.6328125` |
| `150mm` | `640000.0`, `201593.15625`, `119639.09375`, `85059.6328125` |

## Later Consumer Continuity

For every accepted focal tier, later populated samples prove continuity from
the same tracked index-5 object into the previously admitted producer and
builder paths:

| Site | Proven equality / populated state |
|---|---|
| `0x26e4c6` | `rdx == target+0xf8`; lookup count populated; source dimensions `2080 x 1560`, stride `2080` |
| `0x299c70` | `rsi == target+0xf8`; lookup count populated; source dimensions `2080 x 1560`, stride `2080` |
| `0x26e620` | lookup count populated; source dimensions `2080 x 1560`, stride `2080` |
| `0x267010` | `rdx == target+0xe0`; lookup count populated; source dimensions `2080 x 1560`, stride `2080` |
| `0x26e638` | lookup count populated; source dimensions `2080 x 1560`, stride `2080` |

This proves internal construction/custody continuity for the tracked object. It
does not prove that every earlier first-hit consumer sample is already
populated; some first-hit branch samples occur before the watched fields have
their final live values.

## Teardown Separation

After the live construction and consumer samples, each admitted run also
records teardown/clear writes:

- a local clear at `0x26f990 <- 0x2689ce <- 0x2687ab <- 0x3fcb86`;
- allocator/free-path clears under `_platform_memset$VARIANT$Rosetta` /
  `free_tiny` with libcp caller frames including `0x3f77c3` and `0x3f7a2e`.

These are separated from the live producer writes above and are not used as
origin evidence.

## Proven Boundary

Across the canonical four-zoom bridge-HDR quartet, with same-name LRIS
auto-loading disabled:

```text
StereoLayer<false> index 5
  +0xe0 lookup-vector header
    -> live-filled by 0xf02d0 path, final observed write at 0xf043e
    -> count 752 at 28mm / 35mm
    -> count 1472 at 70mm / 150mm
    -> later passed as rdx == this+0xe0 to 0x267010

  +0xf8 source object
    -> control qword written at 0x26be62
    -> later sampled as 2080 x 1560, stride 2080
    -> passed as rdx/rsi == this+0xf8 to 0x26e4c6 / 0x299c70
```

This narrows the internal construction path for the lookup vector and source
object consumed by the proven `0x299c70 -> 0x267010` chain. It does not identify
the public origin or physical meaning of either input.

## Non-Claims

- This proof does not identify a public LRI/protobuf field.
- This proof does not prove metric depth, disparity, inverse depth, confidence,
  or any other physical quantity.
- This proof does not prove the lookup-vector values are cross-image constants.
- This proof does not prove full-map statistics or all per-pixel source records.
- This proof does not prove final source contribution, anti-ghosting behavior,
  or final acceptance/rejection.
- A deeper `28mm` source-object field watch was run as an exploratory lead, but
  it hit the probe step cap and emitted a zero-byte HDR. It is not admitted as
  four-zoom evidence here.

## Validation

Validation commands run after the accepted probes:

```text
python3 -m py_compile tools/lldb_probes/codex_index5_source_lookup_origin_watch/source_lookup_origin_watch_probe.py
python3 <schema-aware JSON validator over the four accepted reports>
file runs/codex_index5_source_lookup_origin_watch/source_lookup_origin_{28mm,35mm,70mm,150mm}.hdr
rg -n 'Traceback|error:|warning:|lost connection|EXC|SIGABRT|SIGSEGV' <accepted JSON reports>
```

The JSON validator required each focal tier to have exit status `0`, no step
cap, empty `errors`, six hits at each instrumented site, a live lookup-vector
write at `0xf043e` with the expected count and byte span, a source-control
write at `0x26be62`, and later populated `0x26e4c6`, `0x299c70`, and
`0x267010` samples preserving the expected `this+0xf8` / `this+0xe0` argument
relationships.
