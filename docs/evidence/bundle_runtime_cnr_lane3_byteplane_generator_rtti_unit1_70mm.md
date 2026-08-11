# Runtime Evidence: CNR Lane-3 Byte-Plane PRODUCER named by generator RTTI (Unit-1 70mm)

Date: 2026-08-11
Binary: installed `libcp.dylib` SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`
Render: Unit-1 `70mm` `L16_03434.lri`, profile 3, export-fmt 3 (canonical CNR bridge-HDR).

## Target

WSJF rank-1 open item under `CLM-DENOISE-002`: *where* the
`FusionCacheBayer+0xe0` `TileCache<unsigned char>` weight plane (whose level-0
byte becomes the CNR lane-3 guide via `guide = LUT[b] * sqrt(FCB+0xcc)`, then
`lane3 = guide^2`) is PRODUCED upstream, its public role, and the `+0xcc`
scalar origin.

## Why the prior 14 instruments could not catch it (now proven statically)

New static reads this session (all against installed `libcp.dylib`) show the
entire consumer path is READ-ONLY, so nothing hooked there can ever see the
writer:

- `FusionCacheBayer` ctor `0x4064c0` builds the byte view at `+0xe0` via
  `0x3d1f80` and stores it; its object vtable `0x66b298` contains only
  `__shared_weak_count` destroy/deallocate/get_deleter thunks
  (`0x407c20/0x407cd0/0x407d90/0x407e30`). This is the shared_ptr **control
  block** — the exact "dead end" earlier instruments hit. The byte cache is a
  passive typed VIEW over a shared `TileStorage`.
- The consumer `0x406a10` at `+298` calls `0x3d2ca0(rdi=FCB+0xe0, level=0)`.
  `0x3d2ca0` is a pure GATHER: it computes tile-grid coverage
  (`idiv` by tile dims), builds a `0x30`-byte read-functor
  (`0x3d2e64`, vtable `typeinfo…+14728`), and dispatches it through executors
  `0x5440`/`0x5670` to read-workers `0x3d79a0`/`0x3d8590`, which return
  `shared_ptr<Tile<uchar>>` already present in storage (later `__release_shared`
  at `0x3d2f74`). No production, no writes — matching the prior "0 completion
  events at `0x3D00F0`" and the accessor-only worker captures.

Conclusion: the byte writer runs **upstream** of `FusionCacheBayer` and
deposits tiles into the shared `TileStorage`. All 14 prior instruments were on
the consumer/read side.

## New instrument (this session)

`tools/lldb_probes/cnr_lane3_producer/gen_introspect_probe.py`
driven by `unit1_70mm_gen_introspect.lldb`, report
`runs/cnr_lane3_producer/unit1_70mm_gen_introspect.json`.

Untried angle: the byte `TileCache` stores a **generator functor** at
`byte_view+0x70` (installed in the FCB ctor at `0x4066cc` via
`0x3d2c10`). Break once at `0x406a10` (rdi = live `FusionCacheBayer`), then
RTTI-resolve the generator, its stored/captured pointers, and the backing
`TileStorage`; decode any pointer as an lt image descriptor. Bounded: 2 hits,
then `Kill`. It ran clean on two worker-thread hits.

## Result — the producer is now NAMED (RTTI, bit-exact, live)

The generator at `byte_view+0x70` (vtable `0x660188`) demangles to:

```
std::__1::__function::__func<
  lt::FusionCacheBayer::FusionCacheBayer(
      std::shared_ptr<lt::RawImageFactory> const&,
      lt::RendererProfileConfig const&)::$_1,
  std::allocator<...>,
  void (std::shared_ptr<lt::Tile<unsigned char>> const&)>
```

So the byte-plane producer is the **`FusionCacheBayer` constructor's `$_1`
per-tile fill callback**, signature `void(shared_ptr<lt::Tile<unsigned char>>
const&)` — the hook that fills each level-0 byte tile. This is PROVEN: it is the
object's own vtable/typeinfo, not an inference.

Newly revealed by the same RTTI: the owning constructor's public inputs are
`std::shared_ptr<lt::RawImageFactory>` and `lt::RendererProfileConfig`. The
byte weight plane therefore derives from the **RAW image factory** under the
**renderer profile config** — its public origin.

### Generator captured context (indicated)

Scanning `generator[0x00..0x120]` and RTTI-resolving pointers yields two
identical structured blocks (stride ~`0xA0`, i.e. a two-element per-camera
array — consistent with the two-body/two-exposure fusion input, not random
heap neighbours):

| gen offset | RTTI-resolved type |
|---|---|
| `+0x70` / `+0x110` | `std::shared_ptr<lt::SoftISP::Stats*>` (default_delete) |
| `+0x78` / `+0x118` | `std::function<... lt::Internal::Pipeline::setWhiteBalance(lt::Internal::PipelineBase::AWB)::$_22 ...>` over `(SoftISP::Stats&, Image<unsigned short> const&, CapturedImage const&, Rectangle<int> const&)` |
| `+0x80` | `std::shared_ptr<lt::Internal::Pipeline>` (emplace) |
| `+0x50..+0x68` / `+0xf0..+0x108` | raw handles `0x7f7ddb84xxxx` (unresolved; the per-camera `Image<u16>`/`CapturedImage`/geometry triplet the AWB callback declares) |
| `+0x90` | 4-char tag `0x4d55545a` = `"ZTUM"` (also present in the `TileStorage` header) |

Interpretation (indicated, not yet proven by body disassembly): the byte
weight plane is a **SoftISP / AWB (`setWhiteBalance`) product** over the 10-bit
`Image<unsigned short>` sensor plane plus `SoftISP::Stats`, tiled as
`Tile<unsigned char>` into the shared `TileStorage`. `FusionCacheBayer::$_1` is
the registered tile-fill hook that binds the byte `TileCache` to that pipeline
output. This does **not** contradict the earlier "setWhiteBalance::$_22 is
context, not the executing CNR frame" correction — `$_22` is a *captured input*
of the byte producer, held for its declared `Image<u16>`/`CapturedImage`/`Stats`
inputs, and the CNR still does not execute inside it.

### Backing storage and scalar

- `FCB+0xf0` / `byte_view+0x40` = `std::shared_ptr<lt::TileStorage>`
  (`__shared_ptr_emplace<lt::TileStorage>`), the shared backing the byte view
  and the writer both reference. Its header carries the same `"ZTUM"` tag and a
  `1.0f`.
- `FCB+0xcc = 1.0f` (live) — the exact scalar the consumer square-roots
  (`sqrtf(FCB+0xcc)`); sibling `FCB+0xdc = 1.0f`. Both are `FusionCacheBayer`
  members set in the ctor from the `RendererProfileConfig` argument (the
  precise config field is not yet pinned).
- Consumer backtrace (worker thread): `0x406a10 <- 0x3ebf5f <- 0x3eca39 <-
  0x3d4842 <- 0x5d97 <- 0x3873 <- 0x55a2 <- 0x3d03d6 <- 0x3d084d <- 0x3bb822 <-
  0x3adfce <- 0x280e <- _pthread_start`.

## What this advances / refutes

- ADVANCES: converts the unknown from "unnamed deep src2 materialization" to a
  **named producer** — `lt::FusionCacheBayer::FusionCacheBayer(shared_ptr<lt::RawImageFactory>,
  lt::RendererProfileConfig)::$_1`, a `void(shared_ptr<Tile<unsigned char>>)`
  per-tile fill hook — with named public inputs (`RawImageFactory`,
  `RendererProfileConfig`, `SoftISP::Stats`, `setWhiteBalance` AWB,
  `Image<unsigned short>`, `CapturedImage`). Public semantic role of the byte
  plane: a **SoftISP AWB / white-balance-derived per-tile weight**.
- REFUTES: the byte cache is not lazily produced on the CNR path, and the
  writer is not anywhere below `0x406a10` — closing the consumer-side search
  that consumed the prior 14 instruments.
- REFINES the `+0xcc` scalar: confirmed live `1.0f`, a `FusionCacheBayer`
  member sourced from `RendererProfileConfig` (public), narrowing (not closing)
  its origin.

## Still open (next instrument)

1. The exact `$_1` byte arithmetic. The generator's `__func` management vtable
   (`0x660188`) slots are trivial (clone/destroy/target only; `operator()`
   maps to a `ret`), so the numeric fill is performed through the **captured
   `setWhiteBalance::$_22` SoftISP/AWB path** rather than in `$_1` itself. Next:
   break on the `setWhiteBalance::$_22` `__func` invoke (vtable `0x1092d9848`,
   RTTI as above) and capture the byte-tile write — its `Image<u16>` input and
   output `Tile<uchar>` give the formula. This is the `CLM-PREFUSION-002`
   boundary.
2. Prove the `+0x50..+0x68` raw triplets are the dereferenced source (vs held
   for lifetime only) by watching a write to a fresh `Tile<uchar>` data buffer
   from inside the `$_22` invoke.
3. Pin the `RendererProfileConfig` field that sets `+0xcc`, and route incidence
   across focal tiers / physical bodies.

## Artifacts

- Probe: `tools/lldb_probes/cnr_lane3_producer/gen_introspect_probe.py`
- Driver: `tools/lldb_probes/cnr_lane3_producer/unit1_70mm_gen_introspect.lldb`
- Report: `runs/cnr_lane3_producer/unit1_70mm_gen_introspect.json`
- Static derivations (no launch):
  `static_bytecache_desc.lldb`, `static_producer_methods.lldb`,
  `static_consumer_406a10.lldb`, `static_extract_3d2ca0.lldb`,
  `static_fcb_ctor.lldb`, `static_generator.lldb`, `static_genmethods.lldb`,
  `static_gen_opcall.lldb` (same directory).
