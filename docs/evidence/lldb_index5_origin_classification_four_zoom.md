# LLDB Evidence: StereoLayer Index-5 Origin Classification, Four Zoom

## Scope

This note validates one Opus-quarantine residual around the `0x29ed90`
guided-upsample input path.

It builds on:

- [lldb_upsample_layer_depth_path.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_upsample_layer_depth_path.md)
- [lldb_upsample_29ed90_worker_formula.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_upsample_29ed90_worker_formula.md)
- [lldb_stereolayer_index5_depth_descriptor_custody.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_stereolayer_index5_depth_descriptor_custody.md)
- [lldb_lris_boundary_and_28mm_no_lris_depth_custody.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_lris_boundary_and_28mm_no_lris_depth_custody.md)

It proves:

- the later overwrite of `StereoLayer<false>+0x2a8` is runtime-live under
  `--no-auto-lris` on the canonical `28mm`, `35mm`, `70mm`, and `150mm`
  bridge-HDR quartet
- the overwrite path runs through
  `0x26dd40 -> 0x26e120 -> 0x267010 -> 0x26e64a -> 0xf340`
- all four runs execute the chain for six `StereoLayer<false>` objects with
  indices `0..5`; index `5` is the full `2080 x 1560` descriptor consumed by
  the already-proven `0x26aa30 -> 0x29ed90` path
- static disassembly classifies `0x267010` as a descriptor builder that creates
  a new 4-byte-output descriptor from a source descriptor plus a lookup/vector
  input, not as a direct whole-descriptor copy into `+0x2a8`

It does not prove the public physical meaning, public LRI/protobuf field
origin, or final merge effect of the descriptor.

## Artifacts

- Static script:
  [static_index5_origin_classification.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_opus_index5_origin_classification/static_index5_origin_classification.lldb)
- Runtime probe:
  [index5_origin_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_opus_index5_origin_classification/index5_origin_probe.py)
- Runtime LLDB scripts:
  [index5_origin_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_opus_index5_origin_classification/index5_origin_28mm.lldb),
  [index5_origin_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_opus_index5_origin_classification/index5_origin_35mm.lldb),
  [index5_origin_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_opus_index5_origin_classification/index5_origin_70mm.lldb),
  [index5_origin_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_opus_index5_origin_classification/index5_origin_150mm.lldb)
- Runner:
  [run_four_zoom.sh](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_opus_index5_origin_classification/run_four_zoom.sh)
- Raw outputs:
  `runs/codex_opus_index5_origin_classification/`

Repo-local scan found no `Traceback`, `error:`, `warning:`, `lost connection`,
`EXC`, or `SIGABRT` entries in the accepted runtime/static logs. All accepted
runtime JSON reports have empty `errors` arrays.

## Static Classification

All VAs below are installed `libcp.dylib` module VAs.

`0x26aa10` is the already-proven `UpsampleLayer` builder. Static disassembly
shows:

- `0x26aa30` calls the previous layer's virtual slot `+0x90`.
- `0x26aa36` keeps the returned descriptor pointer in `r14`.
- `0x26ab99 -> 0x2673a0` copies the previous descriptor into a stack
  descriptor.
- `0x26abe9 -> 0x29ed90` builds the high-resolution upsample output.
- `0x26ac13 -> 0xf340` moves the built descriptor into `UpsampleLayer+0x90`.

`0x26dd40` is the wrapper that precedes the later `StereoLayer<false>+0x2a8`
overwrite. Static disassembly shows it stores `this` in `rbx`, branches on
byte `this+0x54`, and then calls `0x26e120` at `0x26ddd7`.

`0x26e120` builds the later descriptor before it is moved into `this+0x2a8`.
For the runtime-observed index-5 path, the captured `this+0x78` byte is `0`,
which follows the static branch to `0x26e4c6 -> 0x299c70`. The later fixed
handoff is:

```text
0x26e620  rdx = this + 0xe0
0x26e628  rdi = rbp - 0x1d0
0x26e62f  rsi = rbp - 0x80
0x26e633  call 0x267010
0x26e638  r14 = this + 0x2a8
0x26e640  rsi = rbp - 0x1d0
0x26e647  rdi = r14
0x26e64a  call 0xf340
```

`0x267010` zeroes the destination descriptor, allocates it from the source
descriptor dimensions with element size `4`, reads 16-bit source entries
(`movzwl (%rax), %edx`), uses the first pointer in the third argument as a
4-byte lookup table (`movl (%r15,%rdx,4), %r9d`), and writes the looked-up
4-byte values into the destination descriptor. This classifies the final
`+0x2a8` overwrite as a runtime-built descriptor from source descriptor plus
lookup/vector state, not a direct copy of an existing whole descriptor.

## Runtime Result

All accepted runs used `--profile 3 --export-fmt 3 --no-auto-lris`, exited with
status `0`, avoided the probe step cap, and emitted files identified by the OS
`file` command as `Radiance HDR image data`.

| Focal tier | Process exit | Step cap | JSON errors | Update/build/move hits | `0x29ed90` hits | Previous-slot hits |
|---|---:|---|---:|---:|---:|---:|
| `28mm` | `0` | no | 0 | 6 each | 1 | 1 |
| `35mm` | `0` | no | 0 | 6 each | 1 | 1 |
| `70mm` | `0` | no | 0 | 6 each | 1 | 1 |
| `150mm` | `0` | no | 0 | 6 each | 1 | 1 |

The six later-overwrite hits per run correspond to `StereoLayer<false>` objects
with indices `0..5`, all in mode `8`. The observed descriptor sizes form the
same pyramid in every accepted run:

```text
index 0:   65 x   49, tile 32
index 1:  130 x   98, tile 16
index 2:  260 x  195, tile 8
index 3:  520 x  390, tile 4
index 4: 1040 x  780, tile 2
index 5: 2080 x 1560, tile 1
```

For index `5`, every focal tier shows:

- current `this+0x2a8` contents still at the initial-fill sample before
  `0x267010` returns
- a populated stack descriptor at `rbp-0x1d0` after `0x267010`
- the same sampled values moved into `this+0x2a8` after `0x26e64a -> 0xf340`
- `0x26aa39` later returns `this+0x2a8` through the previous-layer slot `+0x90`
  as the descriptor consumed by the `0x29ed90` upsample path

Representative first sampled index-5 values after the final move:

| Focal tier | Index-5 descriptor shape | First sampled values after `0x26e64a -> 0xf340` |
|---|---|---|
| `28mm` | `2080 x 1560`, stride `2080` | `704.609`, `707.929`, `707.929`, `707.929` |
| `35mm` | `2080 x 1560`, stride `2080` | `5516.734`, `5321.346`, `5321.346`, `5321.346` |
| `70mm` | `2080 x 1560`, stride `2080` | `640000.0`, `640000.0`, `640000.0`, `640000.0` |
| `150mm` | `2080 x 1560`, stride `2080` | `53901.297`, `85059.633`, `65987.242`, `85059.633` |

The first sampled values are point samples only. They are not full-map
statistics, constants, or semantic labels.

## Proven Boundary

Across the canonical four-zoom bridge-HDR quartet, with same-name LRIS
auto-loading disabled:

```text
StereoLayer<false> update wrapper 0x26dd40
  -> 0x26e120
  -> source stack descriptor + this+0xe0 lookup/vector state
  -> 0x267010 runtime-built 4-byte descriptor
  -> 0x26e64a / 0xf340 move into StereoLayer<false>+0x2a8
  -> vtable slot +0x90 returns this+0x2a8 at 0x26aa30/0x26aa39
  -> 0x29ed90 guided 2x upsample path
  -> UpsampleLayer+0x90
  -> pair-grid record+0x40
```

This narrows the previous public-origin unknown: the index-5 descriptor consumed
by `0x29ed90` is a runtime-built `StereoLayer<false>` pyramid product on the
tested path. A later follow-up,
[lldb_source_index_299c70_producer_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_source_index_299c70_producer_four_zoom.md),
now bounds the immediate internal `0x299c70` producer/custody path for the
source descriptor passed to `0x267010`. The public source-field names,
lookup/vector public origin, LRI-carried calibration inputs, callback worker
formula, and public physical meaning remain unknown.

## Non-Claims

- This proof does not identify a public LRI/protobuf field name.
- This proof does not prove the descriptor is metric depth, disparity, inverse
  depth, confidence, or any other public physical quantity.
- This proof by itself does not decode the source descriptor passed to
  `0x267010`, the lookup/vector at `this+0xe0`, or the worker bodies dispatched
  by `0x299c70` / `0x299da0`; the immediate `0x299c70` custody boundary is
  covered by
  [lldb_source_index_299c70_producer_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_source_index_299c70_producer_four_zoom.md).
- This proof does not prove full-map statistics from first sampled floats.
- This proof does not prove final merge source contribution, anti-ghosting
  behavior, or final acceptance/rejection.
