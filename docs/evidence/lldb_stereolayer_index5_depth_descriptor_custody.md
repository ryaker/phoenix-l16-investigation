# LLDB Evidence: `StereoLayer<false>` Index-5 Depth Descriptor Custody

## Scope

This note follows the previous-layer descriptor consumed by the
`UpsampleLayer` depth-path builder at `0x26aa10`.

It builds on:

- [lldb_upsample_layer_depth_path.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_upsample_layer_depth_path.md)
- [lldb_upsample_29ed90_worker_formula.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_upsample_29ed90_worker_formula.md)

It proves:

- the previous-layer slot `+0x90` call at `0x26aa30` returns descriptor
  `this+0x2a8` from a `StereoLayer<false>`-family object whose runtime index is
  `5`
- the returned descriptor is shaped `2080 x 1560`, stride `2080`, at the
  `28mm`, `35mm`, `70mm`, and `150mm` canonical bridge HDR seeds
- the object is mode `8`, tile `1`, and has depth size fields
  `+0x2a0/+0x2a4 = 2080/1560` at the handoff
- the descriptor is first populated through a stack ending
  `0x26c518 <- 0x26bdf8 <- 0x26895a <- 0x2687ab`, then later overwritten
  through a stack ending `0x26e64f <- 0x26dddc <- 0x268967 <- 0x2687ab`
- static installed-bundle inspection binds the relevant vtable/accessor and
  descriptor-move surfaces

It does not assign a public LRI/protobuf field origin or public semantic name
to `StereoLayer<false>` index `5`.

Contamination boundary note: a later audit found that the repo-local
`tools/lri_process` harness auto-loaded same-name `.lris` sidecars when present,
and canonical `28mm` seed `L16_02130` has such a sidecar. The 28mm index-5
handoff in this proof was rerun with LRIS auto-loading disabled and the same
captured handoff/descriptor-custody facts still hold; see
[lldb_lris_boundary_and_28mm_no_lris_depth_custody.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_lris_boundary_and_28mm_no_lris_depth_custody.md).

## Artifacts

- Static LLDB script:
  [static_index5_custody_chain.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/stereolayer_depth_writer/static_index5_custody_chain.lldb)
- Runtime probe:
  [stereolayer_index5_watch_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/stereolayer_depth_writer/stereolayer_index5_watch_probe.py)
- Runtime LLDB scripts:
  [index5_watch_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/stereolayer_depth_writer/index5_watch_28mm.lldb),
  [index5_desc_watch_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/stereolayer_depth_writer/index5_desc_watch_35mm.lldb),
  [index5_desc_watch_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/stereolayer_depth_writer/index5_desc_watch_70mm.lldb),
  [index5_desc_watch_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/stereolayer_depth_writer/index5_desc_watch_150mm.lldb)
- Raw static output:
  `runs/stereolayer_depth_writer/static_index5_custody_chain.log`
- Raw runtime outputs:
  `runs/stereolayer_depth_writer/index5_watch_28mm.{log,json}`,
  `runs/stereolayer_depth_writer/index5_desc_watch_35mm.{log,json}`,
  `runs/stereolayer_depth_writer/index5_desc_watch_70mm.{log,json}`,
  `runs/stereolayer_depth_writer/index5_desc_watch_150mm.{log,json}`

Repo-local scan found no `Traceback`, `error:`, `warning:`, `lost connection`,
`EXC`, or `SIGABRT` entries in the promoted runtime/static logs. All promoted
runtime JSON reports have empty `errors` arrays.

## Static Bounds

All VAs below are installed `libcp.dylib` module VAs.

The `StereoLayer<false>` vtable address point at `0x667ae0` contains:

| Vtable offset | Target | Bound role |
|---|---:|---|
| `+0x40` | `0x26bbd0` | runtime index setter; incoming `esi == 5` identifies the tracked object |
| `+0x50` | `0x26bca0` | size setter for object fields `+0x2a0/+0x2a4` |
| `+0x90` | `0x26fb50` | returns `this+0x2a8` |
| `+0x98` | `0x26fb60` | returns `this+0x2d8` |

`0x26fb50` is the accessor used by the `0x26aa30` previous-layer slot call:

```text
0x26fb54: lea 0x2a8(%rdi), %rax
```

`0xf340` is the descriptor move/swap helper observed at all descriptor
population writes in this proof. The watchpoints fire on its stores to the
destination descriptor fields at `0xf383`, `0xf389`, `0xf3ad`, `0xf3b9`, and
`0xf3c4`.

`0x26bca0` writes the tracked size fields:

```text
0x26bce2: movl %eax, 0x2a4(%rdi)
0x26bce8: ret
```

Runtime watchpoints show the preceding width write plus this height write turn
the index-5 object size into `2080 x 1560`.

The initial descriptor population path is statically bounded as:

```text
0x26bdf3 -> 0x26c480
0x26c4dc stores constant 0x491c4000  ; 640000.0f
0x26c4fd -> 0x18e800
0x26c505 loads this+0x2a8
0x26c513 -> 0xf340
0x26c518 destroys the local descriptor
```

Runtime watchpoints bind that path to stack:

```text
0xf3c4 <- 0x26c518 <- 0x26bdf8 <- 0x26895a <- 0x2687ab <- 0x3fcb86
```

The later descriptor overwrite path is statically bounded as:

```text
0x268962 -> 0x26dd40
0x26ddd7 -> 0x26e120
0x26e633 -> 0x267010
0x26e638 loads this+0x2a8
0x26e64a -> 0xf340
0x26e64f destroys the local descriptor
```

Runtime watchpoints bind that path to stack:

```text
0xf3c4 <- 0x26e64f <- 0x26dddc <- 0x268967 <- 0x2687ab <- 0x3fcb86
```

Static slot `+0x30 = 0x26fb70` can copy an externally supplied descriptor into
`this+0x2a8`, but the targeted `28mm` bridge HDR probe recorded zero hits at
`0x26fb70`. Static slot `+0x10 = 0x26cc40` was also tested as a possible
producer and recorded zero hits on the same `28mm` bridge HDR path. These are
scoped negatives under that tested path, not dead-code claims.

## Runtime Result

The promoted handoff evidence is:

| Zoom | Runtime JSON | Process | Step cap | `0x26aa30/0x26aa39` | Previous object | Returned descriptor |
|---|---|---|---|---:|---|---|
| `28mm` | `index5_watch_28mm.json` | exited `0` | no | `1 / 1` | index `5`, mode `8`, tile `1`, size `2080 x 1560` | `2080 x 1560`, stride `2080` |
| `35mm` | `index5_desc_watch_35mm.json` | exited `0` | no | `1 / 1` | index `5`, mode `8`, tile `1`, size `2080 x 1560` | `2080 x 1560`, stride `2080` |
| `70mm` | `index5_desc_watch_70mm.json` | exited `0` | no | `1 / 1` | index `5`, mode `8`, tile `1`, size `2080 x 1560` | `2080 x 1560`, stride `2080` |
| `150mm` | `index5_desc_watch_150mm.json` | stopped after probe step cap | yes, after capture | `1 / 1` | index `5`, mode `8`, tile `1`, size `2080 x 1560` | `2080 x 1560`, stride `2080` |

The `150mm` run captured the same handoff and descriptor-writer stacks before
the LLDB drive loop hit the probe step cap. This is evidence for the captured
handoff only; it is not a completed-render proof.

Descriptor data-pointer writes observed before cleanup:

| Zoom | Initial writer stack | Initial first sampled floats | Later writer stack | Later first sampled floats |
|---|---|---|---|---|
| `28mm` | `0xf3c4 <- 0x26c518 <- 0x26bdf8 <- 0x26895a <- 0x2687ab` | `640000, 640000, 640000, 640000` | `0xf3c4 <- 0x26e64f <- 0x26dddc <- 0x268967 <- 0x2687ab` | `704.609, 707.929, 707.929, 707.929` |
| `35mm` | `0xf3c4 <- 0x26c518 <- 0x26bdf8 <- 0x26895a <- 0x2687ab` | `640000, 640000, 640000, 640000` | `0xf3c4 <- 0x26e64f <- 0x26dddc <- 0x268967 <- 0x2687ab` | `5953.97, 5727.02, 5727.02, 5727.02` |
| `70mm` | `0xf3c4 <- 0x26c518 <- 0x26bdf8 <- 0x26895a <- 0x2687ab` | `640000, 640000, 640000, 640000` | `0xf3c4 <- 0x26e64f <- 0x26dddc <- 0x268967 <- 0x2687ab` | `640000, 640000, 640000, 640000` |
| `150mm` | `0xf3c4 <- 0x26c518 <- 0x26bdf8 <- 0x26895a <- 0x2687ab` | `640000, 640000, 640000, 640000` | `0xf3c4 <- 0x26e64f <- 0x26dddc <- 0x268967 <- 0x2687ab` | `14383.9, 14383.9, 14383.9, 14383.9` |

The sampled floats are only the first captured floats at the descriptor data
pointer. They are not full-map statistics. In particular, the `70mm` first
sample remaining `640000.0` is recorded as an observation only; this proof does
not claim the full `70mm` descriptor is flat.

Cleanup/destructor writes to the same descriptor fields were also observed
through stack `0xf50a <- 0x273c7f <- 0x273aee <- 0x3f77c3 <- 0x3f7a2e` after
the live descriptor had already been consumed. Those cleanup writes are not
treated as producer writes.

## Proven Boundary

Across the canonical bridge HDR quartet, the previous-layer source descriptor
consumed by the proven `0x29ed90` depth upsample path is internally bound to:

```text
StereoLayer<false> object
  index field = 5
  mode field = 8
  tile field = 1
  size fields +0x2a0/+0x2a4 = 2080 x 1560
  descriptor +0x2a8
  vtable slot +0x90 = 0x26fb50
    -> returns this+0x2a8
  consumed by 0x26aa30 / observed at 0x26aa39
  then passed into the already-proven 0x29ed90 guided 2x upsample path
```

This closes the internal object/descriptor custody for the low-resolution float
source consumed by `0x29ed90`. It does not close that descriptor's public LRI
field origin or public semantic name.

## Non-Claims

- This proof does not identify the LRI block, protobuf field, or public schema
  name that ultimately supplies `StereoLayer<false>` index `5`.
- This proof does not assign public semantic meaning to the index `5`, mode
  `8`, or tile `1` fields.
- This proof does not prove full-map statistics from the first sampled floats.
- This proof does not claim `0x26fb70` or `0x26cc40` are dead code; they had
  zero hits only under the targeted `28mm` bridge HDR probes described above.
- This proof does not close `src1` / `src2` semantic contents, C6 routing, or
  final merge acceptance/rejection.
