# LLDB Evidence: Visible `src2` Executor Target at 28mm

## Scope

This proof follows the generic executor dispatch exposed by the visible `src2`
body `0x3ebb80` and binds the first accepted `28mm` runtime callable target.

It proves only the canonical `28mm` seed:

- LRI: `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri`
- Output: `runs/src2_executor_target/src2_executor_target_28mm.hdr`
- Profile/export: bridge HDR, `--profile 3 --export-fmt 3`

Follow-up evidence in
[lldb_src2_executor_target_four_zoom_scope.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_src2_executor_target_four_zoom_scope.md)
extends this to bounded four-zoom gate/dispatch scope. This document remains
the static worker classification and full `28mm` dispatch/worker/output proof.

## Artifacts

- Runtime probe:
  [src2_executor_target_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src2_executor_target/src2_executor_target_28mm.lldb)
- Runtime helper:
  [src2_executor_target_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src2_executor_target/src2_executor_target_probe.py)
- Runtime output:
  `runs/src2_executor_target/src2_executor_target_28mm.log`
- Static worker script:
  [static_src2_executor_worker_3ed2e0.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/src2_executor_target/static_src2_executor_worker_3ed2e0.lldb)
- Static worker output:
  `runs/src2_executor_target/static_src2_executor_worker_3ed2e0.log`

Commands:

```bash
arch -x86_64 lldb -b -s tools/lldb_probes/src2_executor_target/src2_executor_target_28mm.lldb > runs/src2_executor_target/src2_executor_target_28mm.log
arch -x86_64 lldb -b -s tools/lldb_probes/src2_executor_target/static_src2_executor_worker_3ed2e0.lldb > runs/src2_executor_target/static_src2_executor_worker_3ed2e0.log
```

Verification:

- runtime process exited `0` and wrote a `10432x7824` HDR output
  (`src2_executor_target_28mm.log:34`, `:36`)
- runtime summary: one accepted gate, one accepted dispatch, one worker entry,
  and `gate_hits = 49` (`:39`)
- runtime packet has `"errors": []` (`:40`)
- static script created the installed `libcp.dylib` target and resolved
  `0x3ed2e0` as `___lldb_unnamed_symbol10194`
  (`static_src2_executor_worker_3ed2e0.log:4`, `:6`, `:8`)

## Proven Runtime Binding

The accepted visible-`src2` executor gate is:

- gate site: `libcp+0x3ec462`
- caller: `libcp+0x3ecdad`
- callback vtable address point: `libcp+0x65f7e8`
- callback slot `+0x30`: `libcp+0x3ed2e0`

The accepted dispatch is through generic tiler forwarding site `libcp+0x5d94`,
and the dynamic worker breakpoint enters the same target, `libcp+0x3ed2e0`
(`src2_executor_target_28mm.log:39`, `:40`).

The first accepted callback packet includes two descriptor-like fields:

- callback `+0x08`: `220 x 220`, stride `220`
- callback `+0x10`: `217 x 217`, stride `217`

Those are first-accepted-tile runtime values, not algorithm constants
(`src2_executor_target_28mm.log:40`).

## Proven Runtime State Sample

The accepted callback `+0x20` state bundle reads:

- tile offset pair: `(0, 0)`
- transform-origin pair: `(0, 0)`
- `cache+0x1e0` state pointer: readable
- radial scales at state `+0x00/+0x04`: `(1.0, 1.0)`
- radial table head: `1.0, 1.0000052452087402, ...`
- radial table tail at index `4092`: four copies of `0.9999083280563354`
- state `+0x20/+0x24`: `(2020.0, 1505.0)`
- state `+0x28..+0x48` float matrix:
  `(0.9913462400436401, 0.0, 17.0; 0.0, 0.9913462400436401, 13.0; 0.0, 0.0, 1.0)`

The accepted callback `+0x28` table is readable; its first 32 captured floats
start with four `0.0`, then four `1.0`, followed by zeros in the sampled head
(`src2_executor_target_28mm.log:40`).

These values are scoped to the first accepted `28mm` packet from this run.

## Static Worker Classification

The installed-bundle static table at `0x65f7e8` contains `0x3ed2e0` at slot
`+0x30` (`static_src2_executor_worker_3ed2e0.log:12`, `:16`).

Static body `0x3ed2e0` is a bounded per-rectangle worker:

- it reads rectangle bounds from the `rsi` work item and loops over rows and
  columns (`static_src2_executor_worker_3ed2e0.log:44`, `:70`, `:470`, `:477`)
- it reads a source descriptor from callback `+0x08` and a destination
  descriptor from callback `+0x10` (`:48`, `:73`)
- it computes the destination address as 16-byte elements from destination
  stride and `(x, y)` (`:80`, `:85`, `:86`)
- it reads callback `+0x20`, follows that tuple to `cache+0x1e0`, and uses
  state fields from there (`:89`, `:92`, `:95`)
- it computes three row equations over the output coordinate, divides by the
  third row, subtracts state offsets, computes a radius, clamps radius index
  at `0x1000`, reads one radial scale-table float, and applies it to the
  projected coordinate (`:100`, `:115`, `:117`, `:120`, `:132`, `:134`, `:138`)
- it converts projected coordinates through a `64.0` scale, takes integer
  source coordinates with `sarl $0x6`, and takes fractional indexes with
  `andl $0x3f` (`:153`, `:155`, `:158`, `:311`, `:408`)
- it uses direct in-bounds source addressing when a full 4x4 neighborhood is
  available, otherwise it clamps rows/columns or writes the default vector
  loaded from callback `+0x18` when the neighborhood is outside
  (`:161`, `:176`, `:178`, `:193`, `:194`, `:196`)
- it reads the callback `+0x28` coefficient table and applies SIMD `mulps` /
  `addps` stages over 4x4 source vectors (`:313`, `:321`, `:324`, `:343`,
  `:418`, `:420`)
- it forms the final output vector with `-0.25`, `maxps`, and add, then stores
  one 16-byte vector to the destination (`:463`, `:464`, `:465`, `:467`)

Static constant reads confirm literal floats used by the worker:

- `0x5a8124 = -1.0`, `0x5a8128 = 1.0`
- `0x5d6368 = 64.0`
- `0x5d9a20..0x5d9a2c = (-0.25, -0.25, -0.25, -0.25)`

See `static_src2_executor_worker_3ed2e0.log:19..25`.

## Safe Conclusion

For the canonical `28mm` seed only, the visible `src2` generic executor
dispatch at `0x3ebb80 -> 0x3ec462` resolves to callback slot
`0x65f7e8/+0x30 = 0x3ed2e0`.

The bound worker is a one-source descriptor resampling/materialization worker:
it projects output coordinates through `cache+0x1e0` state, applies a
4096-entry radial scale table, uses 1/64 fractional indexing into a callback
coefficient table, samples/clamps a 4x4 SIMD `vec4` neighborhood, and writes a
16-byte destination vector.

This narrows the visible `src2` executor target. It does not prove semantic
`src2` contents, does not prove a multi-source reducer closure, and does not
close final merge acceptance/rejection logic.

## Remaining Unknowns

- semantic `src2` contents across the four-zoom executor-target path
- public semantic names and LRI origins for `cache+0x1e0` fields
- full coefficient-table values / generator behind callback `+0x28`
- public semantic identity and LRI origin of the source descriptor consumed at
  callback `+0x08`; producer custody is now bounded separately in
  [lldb_src2_descriptor_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_src2_descriptor_origin_four_zoom.md)
- whether this materialized descriptor feeds a later merge-quality decision or
  only normalizes/readies an already selected source
