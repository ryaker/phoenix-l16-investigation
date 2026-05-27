# LLDB Evidence: `PipelineCache+0x8` Level Vector, Four-Zoom

**Status:** admitted evidence candidate for `CLM-PREFUSION-001` / `CLM-PREFUSION-002`

## Scope

This proof identifies the runtime storage at `PipelineCache+0x8` on the canonical bridge HDR path and ties it to the first visible `src1` / `src2` wrapper dimensions.

It does not identify the semantic contents of `src1` / `src2` and does not close the pre-fusion merge/reduction mechanism.

## Probe

Reusable probe harness:

- [pipelinecache_level_vector_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/pipelinecache_level_vector/pipelinecache_level_vector_probe.py)
- [level_vector_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/pipelinecache_level_vector/level_vector_28mm.lldb)
- [level_vector_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/pipelinecache_level_vector/level_vector_35mm.lldb)
- [level_vector_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/pipelinecache_level_vector/level_vector_70mm.lldb)
- [level_vector_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/pipelinecache_level_vector/level_vector_150mm.lldb)

Raw run outputs:

- `runs/pipelinecache_level_vector/level_vector_28mm.json`
- `runs/pipelinecache_level_vector/level_vector_35mm.json`
- `runs/pipelinecache_level_vector/level_vector_70mm.json`
- `runs/pipelinecache_level_vector/level_vector_150mm.json`

Invocation pattern:

```bash
arch -x86_64 lldb -b -s tools/lldb_probes/pipelinecache_level_vector/level_vector_28mm.lldb
arch -x86_64 lldb -b -s tools/lldb_probes/pipelinecache_level_vector/level_vector_35mm.lldb
arch -x86_64 lldb -b -s tools/lldb_probes/pipelinecache_level_vector/level_vector_70mm.lldb
arch -x86_64 lldb -b -s tools/lldb_probes/pipelinecache_level_vector/level_vector_150mm.lldb
```

All four accepted reports have:

| Zoom | LRI | Process status | Probe errors | Step cap |
|---|---|---:|---:|---:|
| `28mm` | `L16_02130` | `0` | `0` | `false` |
| `35mm` | `L16_03041` | `0` | `0` | `false` |
| `70mm` | `L16_03434` | `0` | `0` | `false` |
| `150mm` | `L16_02285` | `0` | `0` | `false` |

Each accepted run hit each probe site exactly once.

## Static Anchor

The installed `libcp.dylib` exposes the relevant construction shape:

- `0x3ea7fe` calls `0x3cfd80` from the `PipelineCache` constructor.
- `0x3cfd80` passes `PipelineCache+0x8` to `0x292070`, an 8-byte-element vector assignment helper.
- `0x3ea803` is immediately after that embedded initialization call.
- `0x3eb494` loads `rbx = *(PipelineCache+0x8)`.
- `0x3eb4a2` / `0x3eb4a5` read `int32` fields at `rbx+0x8` and `rbx+0xc`.
- `0x3eb4d5` / `0x3eb4d8` store those fields into the first wrapper at `owner+0x50/+0x54`.
- `0x3eb4df` stores the first wrapper inner pointer into `PipelineCache+0x238`.
- `0x3eb51a` / `0x3eb51d` read the same `rbx+0x8/+0xc` fields for the second wrapper.
- `0x3eb54d` / `0x3eb550` store those fields into the second wrapper at `owner+0x50/+0x54`.
- `0x3eb557` stores the second wrapper inner pointer into `PipelineCache+0x248`.
- `0x3eb588..0x3eb5af` computes and stores two ratio fields at `PipelineCache+0x1e8/+0x1ec` from vector entries `0` and `1`.

## Runtime Vector Contents

At `0x3ea803`, after `0x3cfd80` returns, `PipelineCache+0x8` is a vector header whose heap entries are packed `(int32 width, int32 height)` pairs.

| Zoom | `PipelineCache+0/+0x4` | `PipelineCache+0x8` vector entries |
|---|---:|---|
| `28mm` | `(512,512)` | `(10432,7824)`, `(4160,3120)`, `(2080,1560)`, `(1040,780)`, `(520,390)` |
| `35mm` | `(512,512)` | `(10432,7824)`, `(4160,3120)`, `(2080,1560)`, `(1040,780)`, `(520,390)` |
| `70mm` | `(512,512)` | `(8896,6672)`, `(4160,3120)`, `(2080,1560)`, `(1040,780)`, `(520,390)` |
| `150mm` | `(512,512)` | `(8896,6672)`, `(4160,3120)`, `(2080,1560)`, `(1040,780)`, `(520,390)` |

The constructor source vector captured at `0x3ea7d0` has the same entries as the post-constructor `PipelineCache+0x8` vector in each run.

## Wrapper Dimension Writes

At the first and second visible wrapper installation sites, both wrappers use vector entry `1`.

| Zoom | `src1 owner+0x50/+0x54` | `src1 owner+0x28` | `src2 owner+0x50/+0x54` | `src2 owner+0x28` |
|---|---:|---|---:|---|
| `28mm` | `(4160,3120)` | equals `PipelineCache*` | `(4160,3120)` | equals `PipelineCache*` |
| `35mm` | `(4160,3120)` | equals `PipelineCache*` | `(4160,3120)` | equals `PipelineCache*` |
| `70mm` | `(4160,3120)` | equals `PipelineCache*` | `(4160,3120)` | equals `PipelineCache*` |
| `150mm` | `(4160,3120)` | equals `PipelineCache*` | `(4160,3120)` | equals `PipelineCache*` |

Therefore the reads at `rbx+0x8/+0xc` are reads of vector entry `1`, not reads of an image object's `+0x8/+0xc` width/height fields.

## Ratio Fields

The ratio stores at `PipelineCache+0x1e8/+0x1ec` match vector entry `0 / entry 1` in each tier.

| Zoom | Captured ratio fields |
|---|---:|
| `28mm` | `2.507692337036133`, `2.507692337036133` |
| `35mm` | `2.507692337036133`, `2.507692337036133` |
| `70mm` | `2.1384615898132324`, `2.1384615898132324` |
| `150mm` | `2.1384615898132324`, `2.1384615898132324` |

These values correspond to:

- `10432 / 4160` and `7824 / 3120` for `28mm` / `35mm`
- `8896 / 4160` and `6672 / 3120` for `70mm` / `150mm`

## Proven Facts

- `PipelineCache+0x8` is a `std::vector`-style header whose elements are packed `(int32 width, int32 height)` pairs on the tested bridge HDR path.
- It is not proven to be an image pointer, composite buffer pointer, or pixel buffer.
- The visible `src1` and `src2` wrapper dimension fields are populated from vector entry `1`, which is `(4160,3120)` in all four canonical runs.
- The level vector's entry `0` is tiered: `10432x7824` at `28mm` / `35mm`, and `8896x6672` at `70mm` / `150mm`.
- The wrapper back-reference field `owner+0x28` equals `PipelineCache*` for both wrappers in all four accepted reports.

## Safe Conclusion

`PipelineCache+0x8` must be treated as level-dimension metadata, not as `src1` / `src2` image content and not as a hidden fused-image/composite pointer.

This closes one contamination risk in the `src1` / `src2` blocker lane. It does not close semantic `src1` / `src2` contents, camera membership, reducer math, C6 routing, or final acceptance/rejection.
