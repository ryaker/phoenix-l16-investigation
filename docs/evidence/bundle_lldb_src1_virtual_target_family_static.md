# Installed-Bundle Static Proof: Visible `src1` Lower Target Family Bodies

## Scope

This proof classifies the lower target bodies observed by the first-visible-`src1` gated four-zoom virtual-target census.

The runtime source set comes from [lldb_src1_virtual_target_census_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_src1_virtual_target_census_four_zoom.md). This document adds installed-bundle static disassembly only. It does not add new runtime liveness beyond that census.

## Artifacts

- Probe script: [static_src1_virtual_target_family_disasm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/static_src1_virtual_target_family_disasm.lldb)
- Raw output: `runs/src1_virtual_target_family_static/static_src1_virtual_target_family_disasm.log`
- Output size: `6429` lines
- Output scan: no `error:` or `warning:` lines were present in the raw output under the repo-local scan.
- Binary: `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`

All VAs below are installed `libcp.dylib` module VAs.

## Runtime Target Families Classified Here

The prior four-zoom census observed these lower virtual target families under the first visible-`src1` gate:

| Runtime site | Target vtable slot / body pairs classified here |
|---|---|
| `0x33f3e8` | `0x65ae40 -> 0x340a30`, `0x65aec8 -> 0x340b00`, `0x65b3c8 -> 0x341770`, `0x65b5c8 -> 0x342280`, `0x65b9c8 -> 0x342c60`, `0x65bdb8 -> 0x343620`, `0x65bf18 -> 0x343e10`, `0x65c818 -> 0x345a10`, `0x65ca18 -> 0x345d50`, `0x65d978 -> 0x34a610`, `0x65de38 -> 0x34b3b0` |
| `0x33f94f` wide and tele shared | `0x65af48 -> 0x340bf0`, `0x65afc8 -> 0x340cc0`, `0x65b648 -> 0x342360`, `0x65ba48 -> 0x3430d0`, `0x65ca98 -> 0x345f30`, `0x65d9f8 -> 0x34a780` |
| `0x33f94f` tele-only additions in the capped window | `0x65be38 -> 0x3438d0`, `0x65c898 -> 0x345ae0`, `0x65deb8 -> 0x34b8a0` |
| `0x33ffd4` wide-tier capped-window family | `0x65b148 -> 0x340f70`, `0x65b1c8 -> 0x341040`, `0x65bea8 -> 0x343b80`, `0x65c998 -> 0x345c80`, `0x65da68 -> 0x34a8f0`, `0x65df28 -> 0x34b970` |

The prior census caps nonzero virtual-site packets at `512`, so these target-family lists are capped-window observations, not exhaustive full-render target sets.

## Body Classification

| Target body / group | Static classification from inspected instructions | Boundary |
|---|---|---|
| `0x340a30` | Tiny thunk: moves `rsi` to `rdi` and jumps to `0x350ff0`. | Not a reducer body. |
| `0x350ff0` | Clips / updates record `+0x100` descriptor fields, prepares descriptor fields from `+0x118/+0x120/+0x128`, calls `0x352ce0`, then cleanup/move helper `0xf4e0`. | Descriptor/ROI materialization path. |
| `0x340bf0` | Tiny thunk to `0x350ef0`. | Not a reducer body. |
| `0x350ef0` | Similar `+0x100` descriptor path with element-scale setup, calls `0x352a80`, then cleanup. | Descriptor/ROI materialization path. |
| `0x340f70` | Tiny thunk to `0x3510f0`. | Not a reducer body. |
| `0x3510f0` | Reads reciprocals from the first three floats of `(*record)`, clips descriptor `+0x70` through `+0x88/+0x90/+0x98`, calls `0x353e50`, then moves the descriptor through `0xf340` / `0xf4e0`. | Descriptor/scale materialization path. Existing stale tooling labels for this helper are not cited as truth here. |
| `0x340b00`, `0x340cc0`, `0x341040` | Parameterized wrappers: call `0xf32d0`, read `*(rax)`, copy object constants from `+0x16b0/+0x1670/+0x1674`, then call `0x3589c0`. | Wrapper/descriptor update path. |
| `0x3589c0` | Large record/ROI descriptor update helper. The inspected body reads and clips descriptor groups around `+0x70` and `+0xa0`. | No inspected multi-input reducer is exposed in this body. |
| `0x341770` | Per-source region-adapter / record-update body already bounded in prior evidence. It clips integer region fields, calls `0xf2750` and helper `0x2e8680`, and writes adjusted fields around `+0x100..+0x128`. | Prior proof bounds helper `0x2e8680` and callback `0x2e8cc0` to one-source Bayer/RAW region work. |
| `0x342280`, `0x342360` | Thunks that pass `*(rdi+0x8)` as `rdi`, set `edx = 1`, and jump to `0x341b30`. | Not reducer bodies. |
| `0x341b30` | Clips record `+0xd0` through `+0xe8/+0xf0/+0xf8`, branches on `edx`, computes local descriptor dimensions/scales, calls `0xfb6a0` or `0xf9ef0`, then writes/clips descriptor fields. | Descriptor/remap preparation path. |
| `0xfb6a0`, `0xf9ef0` | Descriptor/remap helpers with allocation, scale/reciprocal math, and field movement through helpers such as `0xf3570`, `0xf540`, and `0xf430`. | Public semantics are not named by this proof. |
| `0x342c60`, `0x3430d0` | Thunks to `0x342ca0`. | Effective body is `0x342ca0`. |
| `0x342ca0` | Clips record `+0xd0`, calls `0xf2750`, then makes an indirect call through object field `0x1560(%r14)` and vtable slot `+0x30` using `record+0x70` plus a local descriptor. Optional mode-dependent descriptor/grid materialization calls `0x34e400`. | Visible body is per-record descriptor work. The indirect callable target is not classified by this document. |
| `0x34e400` | Allocates/resizes via `0xf540` and copies/resamples 32-bit elements into a destination with fixed 16.16 stepping. | No inspected multi-input merge is exposed in this helper. |
| `0x343620`, `0x3438d0`, `0x343b80` | Near-identical bodies: clip `+0x70` descriptor, add object state `+0x1610`, call `0x351a50`, then move result into `record+0x70` through `0xf340` and cleanup. | Descriptor executor setup path. |
| `0x351a50` | One-descriptor executor helper: uses `0xf540`, allocates callback state, dispatches generic executor `0x5440`, then performs cleanup. | No inspected multi-input reducer is exposed in this helper. |
| `0x343e10` | Clips `+0x100`, calls `0xf2750`, consumes `(*rbx)+0x198`, calls `0x30b770`, and moves result into `record+0x100`. | One-source materialization handoff. |
| `0x30b770` | One-source Bayer/materialization helper. It checks source mode / dimensions, allocates a destination through `0xf540`, selects one callback among `0x30b9f0`, `0x30dc60`, `0x30ff60`, and `0x312810`, and dispatches through `0x5440`. | No inspected multi-input reducer is exposed in this helper. |
| `0x345a10`, `0x345ae0`, `0x345c80` | Thunks to `0x344470`. | Effective body is `0x344470`. |
| `0x344470` | Clips/reconfigures `+0x70`, calls `0xf32d0`, `0xef890`, and later contains indirect/optional callable behavior. | Visible body is per-record descriptor reconfiguration. The indirect callable target is not classified by this document. |
| `0xef890` | One-descriptor executor helper: calls `0xef050`, allocates through `0xf540`, allocates callback state, and dispatches executor `0x5670`. | No inspected multi-input reducer is exposed in this helper. |
| `0x345d50`, `0x345f30` | Clip `+0x70`, use object fields `+0x1618/+0x161c`, then call `0xfbda0`. | Existing canonical docs classify `0xfbda0` in selected owner-cache/direct-render tile surfaces; this document does not add a new public name. |
| `0x34a610`, `0x34a780`, `0x34a8f0` | Parameter/cache consistency guard and descriptor update family. Each calls `0x2d6cd0`, compares returned fields to `(*record)+0x48..+0x78`, and, when fields differ, tail-calls `0xa9f20` with `record+0x70`, the same descriptor, a parameter record, `(*record)+0x48`, and flag `1`. | Cache/state update or descriptor materialization path; not proven image acceptance/rejection. |
| `0x2d6cd0` | One-time singleton accessor that initializes a `0x34`-byte record through `0xa9910` / `0xa9ea0` once and returns its pointer. | Parameter-provider helper. |
| `0xa9f20` | Descriptor executor/materialization helper: validates non-empty image data, calls selector/table helper `0xaa110`, allocates through `0xf540`, calls `0xa9340`, allocates callback state, and dispatches via `0x5440`. | No inspected multi-input reducer is exposed in this helper. |
| `0x34b3b0`, `0x34b8a0`, `0x34b970` | Thunks to `0x34b3f0`. The `0x34b970` disassembly window continues into adjacent destructor-like code after the thunk boundary; the effective target body is the thunk to `0x34b3f0`. | Effective body is `0x34b3f0`. |
| `0x34b3f0` | Descriptor/cache/materialization updater. Calls `0xf3340`, `0xf32d0`, `0xef050`, `0xf0610`, uses optional `record+0x60` / `record+0x50` descriptor paths, moves descriptors through `0xf340`, and calls `0x307ee0`. | No inspected multi-input reducer is exposed before the `0x307ee0` helper call. |
| `0x307ee0` | Complex image/math/materialization helper. It uses `0xf840`, `0x232440`, `0x308f50`, `log2f`, `0x2628e0`, `0x13910`, `ldexp`, callback allocation, and executor dispatch `0x5440`. | This proof does not assign public semantics to the helper. |

## Small Helper Bounds

| Helper | Static bound |
|---|---|
| `0xf32d0` | Returns `rdi+0x40`. |
| `0xf3340` | Returns `rdi+0xa8`. |
| `0xf2750` | Returns `rdi+0x58`. |
| `0xf36e0` | Returns `rdi+0x1d8`. |
| `0xf0610` | Copies descriptor-like groups through `0xf0480`. |
| `0xef050`, `0xef120` | Descriptor/vector utility surfaces only in this proof. |

## Proven Boundary

The inspected first-level target bodies and directly inspected helper callees classify as thunks, descriptor clipping/update, ROI/materialization, one-source Bayer/RAW region work, cache/parameter consistency, single-descriptor executor setup, selected tile/read-rescale handoff, or image/materialization helpers.

This proof does not identify a visible first-level target body as the exact pre-fusion `src1` / `src2` merge/reduction mechanism.

This proof does not identify a visible first-level target body as final contributor acceptance/rejection.

The two inspected bodies with indirect callable behavior, `0x342ca0` and `0x344470`, remain bounded only for their visible instructions and directly inspected helper calls. Their dynamic callable targets are outside this proof.

The `0x34a610` / `0x34a780` / `0x34a8f0` family is bounded as cache/parameter consistency and descriptor materialization/update behavior. This proof does not support naming that family as image acceptance/rejection.

## Non-Claims

- This proof does not identify semantic `src1` or `src2` contents.
- This proof does not close `CLM-PREFUSION-002`.
- This proof does not prove the capped runtime target-family lists are exhaustive full-render target sets.
- This proof does not classify dynamic callable targets behind the indirect calls inside `0x342ca0` or `0x344470`.
- This proof does not resolve C6 routing.
- This proof does not resolve final merge-quality policy.
