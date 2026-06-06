# LLDB Evidence: `0x299c70` Source-Index Descriptor Producer, Four Zoom

## Scope

This note validates one upstream custody boundary for the source descriptor
consumed by `0x267010` in the later `StereoLayer<false>+0x2a8` overwrite path.

It builds on:

- [lldb_index5_origin_classification_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_index5_origin_classification_four_zoom.md)
- [lldb_index5_267010_mapping_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_index5_267010_mapping_four_zoom.md)

It proves a narrow runtime custody fact:

- the tested `0x26e120` branch reaches `0x26e4c6 -> 0x299c70` for all six
  `StereoLayer<false>` indices `0..5` under `28mm`, `35mm`, `70mm`, and
  `150mm` no-auto-LRIS bridge-HDR runs;
- the `0x299c70` source object argument is `StereoLayer<false>+0xf8`;
- the `0x299c70` destination argument is the caller stack descriptor
  `rbp-0xe0`;
- the descriptor produced by `0x299c70` is the same 2-byte source descriptor
  moved into `rbp-0x80` at `0x26e4e0 -> 0xf340`;
- that moved descriptor is the source descriptor passed to `0x267010`;
- the lookup-vector argument at the `0x267010` callsite is
  `StereoLayer<false>+0xe0`.

It does not prove public field names, public LRI/protobuf origin, public
calibration semantics, the worker formula behind the `0x299c70` dispatch, full
map statistics, physical meaning, final source contribution, anti-ghosting
behavior, or final acceptance/rejection.

## Artifacts

- Runtime probe:
  [source_index_producer_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_299c70_source_index_producer/source_index_producer_probe.py)
- Runtime LLDB scripts:
  [source_index_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_299c70_source_index_producer/source_index_28mm.lldb),
  [source_index_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_299c70_source_index_producer/source_index_35mm.lldb),
  [source_index_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_299c70_source_index_producer/source_index_70mm.lldb),
  [source_index_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_299c70_source_index_producer/source_index_150mm.lldb)
- Static extractor:
  [static_source_index_producer.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_299c70_source_index_producer/static_source_index_producer.lldb)
- Runners:
  [run_four_zoom.sh](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_299c70_source_index_producer/run_four_zoom.sh),
  [run_150.sh](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_299c70_source_index_producer/run_150.sh)
- Raw outputs:
  `runs/codex_299c70_source_index_producer/`

The accepted current artifacts have no `Traceback`, `error:`, `warning:`,
`lost connection`, `EXC`, `SIGABRT`, or `SIGSEGV` matches. All accepted JSON
reports have empty `errors` arrays.

## Static Boundary

Independent static extraction in
`runs/codex_299c70_source_index_producer/static_source_index_producer.log`
shows the tested branch/call sequence:

```text
0x26e162  leaq 0xf8(%r12), %rdx
0x26e170  je 0x26e4c6
0x26e4c6  leaq -0xe0(%rbp), %rdi
0x26e4cd  movq %rdx, %rsi
0x26e4d0  callq 0x299c70
0x26e4d5  leaq -0x80(%rbp), %rdi
0x26e4d9  leaq -0xe0(%rbp), %rsi
0x26e4e0  callq 0xf340
0x26e620  leaq 0xe0(%r12), %rdx
0x26e62f  leaq -0x80(%rbp), %rsi
0x26e633  callq 0x267010
```

The same static extractor shows `0x299c70` reads width/height from
`source_object+0x30/+0x34`, allocates the destination descriptor with element
size `2` through `0xf540`, and dispatches generic executor `0x5440` with a
local callback object. Runtime packets below prove this static sequence is live
for the admitted four-zoom scope.

## Runtime Result

All accepted runs used `--profile 3 --export-fmt 3 --no-auto-lris`, exited with
status `0`, avoided the probe step cap, and emitted files identified by the OS
`file` command as `Radiance HDR image data`.

| Focal tier | Branch hits | `0x299c70` hits | `0x267010` hits | Chains | JSON errors | Output |
|---|---:|---:|---:|---:|---:|---|
| `28mm` | 6 | 6 | 6 | 6 | 0 | Radiance HDR |
| `35mm` | 6 | 6 | 6 | 6 | 0 | Radiance HDR |
| `70mm` | 6 | 6 | 6 | 6 | 0 | Radiance HDR |
| `150mm` | 6 | 6 | 6 | 6 | 0 | Radiance HDR |

Every focal tier produced six same-thread chains, one each for
`StereoLayer<false>` indices `0..5`. Every chain's built-in comparison checks
passed.

## Proven Chain

For every accepted focal tier and every captured index `0..5`, the probe
verified:

| Check | Result |
|---|---|
| branch `rdx == this+0xf8` at `0x26e4c6` | true for all chains |
| `0x299c70` entry `rsi == this+0xf8` | true for all chains |
| `0x299c70` entry `rdi == caller_rbp-0xe0` | true for all chains |
| `source_object+0x30/+0x34` dimensions match returned temp descriptor dimensions | true for all chains |
| dispatch callback field `+0x08` equals `0x299c70` destination descriptor | true for all chains |
| dispatch callback field `+0x10` equals `0x299c70` source object | true for all chains |
| descriptor after `0x299c70` dispatch equals descriptor after return at `0x26e4d5` | true for all chains |
| source descriptor before `0xf340` move equals descriptor after `0x299c70` return | true for all chains |
| destination descriptor after `0xf340` move equals source descriptor before move | true for all chains |
| `0x267010` callsite source descriptor equals moved destination descriptor | true for all chains |
| `0x267010` callsite `rdx == this+0xe0` | true for all chains |
| `0x267010` entry source and lookup arguments match the callsite | true for all chains |

The descriptor dimensions are the same six-level pyramid proven by the prior
mapping evidence:

```text
65x49, 130x98, 260x195, 520x390, 1040x780, 2080x1560
```

The lookup-vector counts at the `0x267010` callsite are unchanged from the prior
mapping proof: `752` for `28mm` / `35mm` and `1472` for `70mm` / `150mm`.

The `0x299c70` dispatch callback address point observed in the accepted packets
is `libcp+0x6680f0`. The callback object stores the destination descriptor
pointer at `+0x08` and the source object pointer at `+0x10`. This proof does
not decode the callback worker body or assign public semantics to those fields.

Representative index-5 first-8 `uint16` samples from this run, included only as
run-local examples and not as constants:

| Focal tier | First 8 source-index values at index 5 |
|---|---|
| `28mm` | `216, 218, 217, 214, 214, 214, 214, 212` |
| `35mm` | `27, 28, 28, 28, 28, 28, 27, 27` |
| `70mm` | `0, 0, 0, 0, 0, 0, 0, 0` |
| `150mm` | `50, 51, 50, 51, 51, 51, 50, 51` |

## Proven Boundary

Across the canonical four-zoom bridge-HDR quartet, with same-name LRIS
auto-loading disabled:

```text
StereoLayer<false> object
  -> source object at this+0xf8
  -> 0x299c70 builds a 2-byte descriptor at caller rbp-0xe0
  -> 0xf340 moves that descriptor into caller rbp-0x80
  -> 0x267010 consumes rbp-0x80 as its uint16 source descriptor
  -> 0x267010 consumes this+0xe0 as its lookup-vector argument
  -> 0x267010 builds the float descriptor later moved into this+0x2a8
```

This closes the immediate upstream producer/custody boundary for the tested
`0x267010` source descriptor. It does not close the public origin or physical
meaning of either the source object at `this+0xf8` or the lookup vector at
`this+0xe0`.

## Non-Claims

- This proof does not identify public LRI/protobuf field names.
- This proof does not identify public calibration semantics for `this+0xf8` or
  `this+0xe0`.
- This proof does not decode the worker formula behind the `0x299c70` callback
  dispatched through `0x5440`.
- This proof does not prove full-map statistics or run-independent source-index
  sample constants.
- This proof does not prove metric depth, disparity, inverse depth, confidence,
  or any other physical quantity.
- This proof does not prove final merge source contribution, anti-ghosting
  behavior, or final acceptance/rejection.
