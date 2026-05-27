# Bundle + LLDB Parent-Chain Static Classification Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib`, static disassembly of the parent-chain
bodies proven live by `bundle_lldb_owner_f0_global_route_ancestry.md`.

This document follows:

- `bundle_lldb_owner_f0_global_route_census.md`
- `bundle_lldb_owner_f0_global_post_route_families.md`
- `bundle_lldb_owner_f0_global_route_ancestry.md`

The prior ancestry proof supplies the four-zoom runtime fact: complete bridge
HDR renders at `28mm`, `35mm`, `70mm`, and `150mm` reach these parent chains
from read-context branch sites `0x3d4842` / `0x3d4864`. This document classifies
the static bodies behind those parent return PCs. It is not a new hit-count
proof and not a final-output proof.

It proves:

- `0x280e` is a callback runner / exception wrapper. It invokes a callback
  through vtable slot `+0x30`, writes byte `0` to `rbx+0x14`, returns `0`, and
  stores caught exceptions through `std::exception_ptr`.
- `0x3adfce` is a callback iteration dispatcher. It loops through `0x3af770`,
  invokes two callback fields through vtable slot `+0x30`, and has an exception
  callback at owner offset `+0x150`.
- `0x3b07a9` returns from body `0x3b0740`, which chooses between owner
  `+0x6b8` and owner `+0x688` using `0x3c6f80` / `0x3f06d0`, then calls
  `0x3d0650`.
- `0x41a8d3` is inside a mode-switching direct-render/tile body. In the
  observed mode-0 path, it calls `0x3b0740`, then computes a float rectangle
  through `0x3b9770`, looks up a map/object through `0x3c6ac0` /
  `0x1bea00` / `0x1be970`, and calls `0xfbda0`.
- `0x3b9770` computes four float rectangle values from level dimensions and
  a rectangle input; it is a geometry conversion helper.
- `0xfbda0` allocates a 16-byte-element destination, computes scale/ROI fields,
  builds a callback object, and dispatches through helper `0x2e20` plus
  virtual calls. Its guarded error strings include bayer/vignetting-data
  failures. This proves a tile/image worker surface, not final merge policy.
- `0x3bb822` is inside a large owner-cache tile body `0x3bb2b0`. At the focused
  window, it returns from `0x3d0650`, indexes owner vector `+0x870`, calls
  `0x31b110` with the same descriptor passed as both `rsi` and `rdx`, then
  clips/adjusts the descriptor in place.
- `0x374cf3` is inside ROI adapter body `0x374ac0`. That body allocates a
  16-byte-element destination, clips an ROI/view into the source descriptor,
  invokes a callback at `0x374cf1`, then zero-fills out-of-ROI rows/regions
  with `__bzero`.
- `0x3665da` is inside the huge worker `0x3661b0`; immediately before it,
  `0x3665d5` calls `0x374ac0`. After `0x3665da`, the body computes/clips
  descriptor regions and continues worker setup.
- `0x365f50` is inside IRAMP body `0x365960`. The live positive-ROI path
  allocates/resizes a 16-byte-element descriptor, calls `0x3661b0` at
  `0x365f4b`, then jumps to cleanup at `0x366019`.
- `0x3ec7df` is inside `0x3ec770`, the already bounded caller-side
  `PipelineCache::processLevel0` path: it calls `0x365960`, validates returned
  descriptor dimensions against ROI, wraps `rbp-0x60`, and calls `0xd76a0`.
- `0x3eca4b` is inside owner `+0xf0` sink body `0x3ec960`. That body chooses
  its source path by level, then converges at `0x3eca4b`, reads owner `+0x170`,
  calls `0x1bea20`, applies the already bounded `0x2d7320` vector-scale
  helper, and calls `0x3e5720` with destination `(*rsi)+0xf0`.

It does not prove:

- public names for the owner-cache/direct-render or visible-`src1` families
- the final file/display sink
- final contributor acceptance, rejection, or suppression policy
- public pixel-format names
- that the same parent-chain body set is exhaustive outside the canonical
  bridge HDR quartet

## Inputs

Static proof target:

| What | Path |
|---|---|
| `libcp.dylib` | `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib` |

Runtime ancestry dependency:

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Tooling Boundary

Reusable static LLDB scripts live in the repo:

- `tools/lldb_probes/static_parent_chain_disasm.lldb`
- `tools/lldb_probes/static_parent_chain_focused_disasm.lldb`

Rerunnable raw LLDB outputs live under ignored `runs/static_parent_chain/`:

- `parent_chain_static_disasm.txt`
- `parent_chain_focused_static_disasm.txt`

No probe harness or live evidence dependency for this proof lives in
`/private/tmp`.

## Static Method

The scripts create a static LLDB target from the installed `libcp.dylib`, then
run `image lookup` plus `disassemble` around the parent-chain VAs proven live by
the runtime ancestry census.

The first script captures broad function context. The focused script uses
explicit start/end windows where count-based disassembly would otherwise stop
before large-function return PCs.

## Callback / Dispatcher Glue

### `0x280e`

`image lookup --address 0x280e` resolves to
`___lldb_unnamed_symbol718 + 158`.

The body:

- loads a callback object from `0x8(%rbx)`
- loads callback field `+0x20`
- invokes vtable slot `+0x30` at `0x280c`
- writes `0` to `0x14(%rbx)` at `0x280e`
- returns `0`
- catches exceptions and assigns `std::current_exception()` into the caller
  object

Safe classification: callback runner / exception wrapper.

### `0x3adfce`

`image lookup --address 0x3adfce` resolves to
`___lldb_unnamed_symbol9370 + 158`.

The body:

- loops through `0x3af770`
- invokes a first callback through vtable slot `+0x30` at `0x3adfcc`
- invokes a second callback through vtable slot `+0x30` at `0x3adff1`
- loops back to `0x3adf90`
- on exception, calls a callback stored at owner offset `+0x150`

Safe classification: callback iteration dispatcher.

## Owner-Cache / Direct-Render Chain

### `0x3b0740 -> 0x3b07a9`

`image lookup --address 0x3b07a9` resolves to
`___lldb_unnamed_symbol9395 + 105`.

The body:

- calls `0x3c6f80`
- calls `0x3f06d0` on owner `+0x6b8`
- compares float values
- chooses owner `+0x6b8` or owner `+0x688`
- passes the selected object to `0x3d0650`
- returns at `0x3b07a9`

Safe classification: selected owner-cache read wrapper into `0x3d0650`.

### `0x41a7d0 -> 0x41a8d3`

`image lookup --address 0x41a8d3` resolves to
`___lldb_unnamed_symbol10556 + 259`.

The mode-0 path:

- reads owner state from `*(r12+0x10)`
- reads tile/ROI fields from owner `+0x520`
- calls `0x3b0740` at `0x41a8ce`
- returns at `0x41a8d3`
- calls `0x3b9770` at `0x41a8e3`
- obtains a map/object pointer through `0x3c6ac0`
- derives a key through `0x1bea00`
- performs lookup through `0x1be970`
- calls `0xfbda0` at `0x41a935`

Safe classification: direct-render/tile orchestrator for the observed mode-0
route. It is not a final-policy proof.

### `0x3b9770`

`image lookup --address 0x3b9770` resolves to
`___lldb_unnamed_symbol9452`.

The body:

- reads dimensions via owner `+0x6a8` / `0x3e0b90`
- reads per-level dimensions from owner `+0x4d8`
- converts an input int rectangle to four float values by dividing by those
  dimensions
- returns the four-float rectangle

Safe classification: level-aware rectangle scaling helper.

### `0xfbda0`

`image lookup --address 0xfbda0` resolves to
`___lldb_unnamed_symbol2730`.

The body:

- rejects invalid bayer dimensions
- checks an optional/model path through `0xf3570`
- allocates/resizes a 16-byte-element destination through `0xf540`
- computes multiple scale and ROI fields
- builds a `0x48`-byte callback object
- dispatches through helper `0x2e20`
- invokes virtual calls at `0xfc05f` and `0xfc06c`
- contains guarded error strings for missing vignetting model/data

Safe classification: bayer/vignetting-guarded tile/image worker surface. This
does not prove final merge or acceptance policy.

### `0x3bb2b0 -> 0x3bb822`

`image lookup --address 0x3bb822` resolves to
`___lldb_unnamed_symbol9488 + 1394`.

The broad body:

- constructs tile/level rectangles
- allocates/resizes a 16-byte-element descriptor
- contains several `0x3d0650` selected-cache calls

The focused `0x3bb822` window proves:

- `0x3bb81d` calls `0x3d0650`
- `0x3bb822` reads owner vector `+0x870`
- `0x3bb867` calls `0x31b110` with the same descriptor as `rsi` and `rdx`
- after `0x31b110`, the body clips/adjusts the descriptor in place
- a sibling window at `0x3bb930 -> 0x3bb935` repeats the same post-call shape

Safe classification: owner-cache tile/read body with post-read helper and
descriptor clipping. This does not name public policy.

## Visible-`src1` / IRAMP Nested Chain

### `0x374ac0 -> 0x374cf3`

`image lookup --address 0x374cf3` resolves to
`___lldb_unnamed_symbol9013 + 563`.

The body:

- allocates/resizes a 16-byte-element destination via `0xf540`
- clips a requested ROI/view against the source descriptor
- invokes a callback at `0x374cf1`
- returns at `0x374cf3`
- zero-fills rows/regions with `__bzero`

Safe classification: ROI adapter plus zero-fill wrapper.

### `0x3661b0 -> 0x3665da`

`image lookup --address 0x3665da` resolves to
`___lldb_unnamed_symbol8958 + 1066`.

The body:

- has a large `0x4498` stack frame
- builds ROI-aligned grids/temporary descriptors
- calls `0x374ac0` at `0x3665d5`
- returns at `0x3665da`
- continues descriptor clipping and worker setup

Safe classification: large worker/dispatcher beneath IRAMP; `0x3665da` is the
return from the ROI adapter callback wrapper.

### `0x365960 -> 0x365f50`

`image lookup --address 0x365f50` resolves to
`___lldb_unnamed_symbol8957 + 1520`.

The focused positive-ROI path:

- checks ROI width and height
- allocates/resizes a 16-byte-element descriptor through `0xf540`
- calls `0x3661b0` at `0x365f4b`
- jumps to cleanup at `0x366019` from `0x365f50`

Safe classification: IRAMP body return from the large worker, then cleanup.

### `0x3ec770 -> 0x3ec7df`

`image lookup --address 0x3ec7df` resolves to
`___lldb_unnamed_symbol10151 + 111`.

The body:

- verifies init flags at object offsets `+0x190` and `+0x1f0`
- calls IRAMP `0x365960` at `0x3ec7da`
- validates the returned descriptor dimensions against the ROI
- wraps `rbp-0x60`
- calls square-copy helper `0xd76a0`

Safe classification: caller-side `PipelineCache::processLevel0` / IRAMP
caller-side square-copy handoff, already bounded by earlier evidence.

### `0x3ec960 -> 0x3eca4b`

`image lookup --address 0x3eca4b` resolves to
`___lldb_unnamed_symbol10158 + 235`.

The body:

- computes destination descriptor `(*rsi)+0xf0`
- allocates/resizes that descriptor with element size `6`
- chooses one of three source paths by level: level `2..4` uses `0x3e0af0`
  lookup followed by `0x3d0650`, level `1` uses `0x3ebb80`, and level `0`
  uses `0x3ec770`
- converges at `0x3eca4b`
- reads owner field `+0x170`
- calls `0x1bea20`
- calls vector-scale helper `0x2d7320`
- calls `0x3e5720` with destination `(*rsi)+0xf0`

Safe classification: owner `+0xf0` sink / conversion setup already bounded by
earlier evidence. The nested `0x3d4842` continuation observed in the ancestry
census is therefore not final output by itself.

## Interpretation Boundary

This proof narrows the downstream blocker by separating parent-chain bodies into
three proven structural groups:

- callback/iteration glue: `0x280e`, `0x3adfce`
- owner-cache/direct-render tile and image-worker surfaces: `0x3b0740`,
  `0x41a7d0`, `0x3b9770`, `0xfbda0`, `0x3bb2b0`
- visible-`src1` / IRAMP nested wrapper and owner `+0xf0` sink surfaces:
  `0x374ac0`, `0x3661b0`, `0x365960`, `0x3ec770`, `0x3ec960`

It does not close downstream row-image/final policy. The remaining blocker is
still to identify which post-branch surfaces feed the final displayed/exported
image and where contributor acceptance/rejection is decided.
