# LLDB Evidence: FusionCacheBayer u8 weight-plane WRITER hunt (2026-08-11)

## Status: INCONCLUSIVE on the headline unknown; new corroborating static proof

This note attacks open item 1 of
`bundle_static_runtime_cnr_lane3_u8_weight_origin_unit1_70mm.md`: **which
upstream producer deposits the byte VALUES into the shared `lt::TileStorage`
that backs `FusionCacheBayer+0xe0`, and its public semantic name.**

It does **not** name that producer and does **not** recover its exact per-byte
arithmetic. It rules the read/view/`$_1` side out at the instruction level
(reinforcing already-documented structure), diagnoses precisely why the direct
watchpoint instrument cannot catch the writer as posed, and specifies the
corrected next instrument.

Test input: canonical Unit-1 70mm `L16_03434`
(`/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri`), profile 3, HDR.
Installed `libcp.dylib` SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`.
All VAs below are installed `libcp.dylib` module VAs.

## New static proof (verified)

### 1. The byte TileCache (`+0xe0`) ctor is a passive pyramid VIEW builder

`FusionCacheBayer` ctor `0x4064c0` builds the byte cache at `0x40663e` by
calling `0x3d1f80`, which is a 5-byte thunk:

```text
0x3d1f80: push rbp; mov rbp,rsp; pop rbp; jmp 0x3d1d40
```

`0x3d1d40` is the real ctor. Its 4th argument (`rcx`) is a `shared_ptr`; it
stores the pointer at `view+0x38` and the control block at `view+0x40`
(`0x3d1d85..0x3d1d91`, with `__add_shared`). It then walks a **pyramid** of
`(w,h)` level descriptors, computing per-level tile counts by integer division,
and aborts with the string **"TileCache pyramid not sorted!"** (`0x3d1eaa`) if
levels are unsorted. The generator slot `view+0x70` is initialized to `0`
(`0x3d1da0`).

=> `+0xe0` is a multi-level **view over a shared `lt::TileStorage`**, exactly as
previously documented. The ctor writes **no** pixel data.

### 2. The `$_1` generator does NO per-pixel work (vtable is all trivial thunks)

The runtime generator object (from `runs/.../unit1_70mm_gen_introspect.json`,
`byte_view+0x70`) has vtable module-VA `0x660188`, RTTI-named
`...__func<...FusionCacheBayer::$_1..., void(shared_ptr<lt::Tile<unsigned char>> const&)>`.
Static dump of that `__func` vtable and disassembly of **every** target:

```text
0x660180: [typeinfo 0x6601d0]  0x4078a0  0x4078b0  0x4078c0
          0x4078e0  0x4078f0  0x407900  0x407910  0x407920  0x407940
```

- `0x4078a0` / `0x4078f0` / `0x407910`: bare `push/mov/pop/ret` (no-ops)
- `0x4078b0` / `0x407900`: tail-jump to `operator delete`
- `0x4078c0`: `new(16)` + set typeinfo (`__clone`)
- `0x4078e0`: store typeinfo at `(rsi)` (placement `__clone`)
- `0x407920`: `target(type_info&)` typeinfo compare
- `0x407940`: `target_type()` returns typeinfo

None of the nine target functions contains a loop, a memory-fill, or per-pixel
arithmetic. Regardless of which slot is `operator()`, the `$_1` generator
performs **no** byte computation. This is instruction-level confirmation of the
already-documented conclusion that `$_1` is an accessor/reader, not the writer.

### 3. Byte tiles are already resident before the consumer runs

`runs/.../unit1_70mm_storage_writer.json`: at consumer `0x406a10` the FCB owner
is hit `269` times (`selected_hits=269`) with a single stable descent
`0x406a10 <- 0x3ebb80 <- 0x3ec960 <- 0x3d47d0 <- ... <- 0x3d0650 <- 0x3bb2b0 <- 0x3adf30`,
yet `complete_counts.byte = complete_counts.float = 0`. No tile completes into
FCB storage inside the observed window => **the byte tiles are deposited
upstream, before FusionCacheBayer's consumer ever reads them.**

### 4. The byte plane is a 2x-doubled half-res u8 weight map

`runs/.../unit1_70mm_bytebuf_reuse.json`: the live 522x522 stride-522 (u8) tile
at `0x7f7c90008040` **already held** the spatially-doubled pattern
`255,255,254,254,255,255,254,254,...` when first observed (each source value
repeated 2x horizontally, i.e. a nearest-neighbour 2x upsample of a ~261x261
half-res u8 weight map). Every subsequent watchpoint write on that block decodes
as **float32** (`00 00 18 43`=152.0f, `00 00 56 43`=214.0f, ...): the 272484-byte
u8 tile is freed and the block recycled as a float buffer downstream. The u8
producer never appears post-consumer because it has already run.

Note: this is a **distinct** plane from the `UpsampleLayer` guided 2x upsample
in `lldb_upsample_29ed90_worker_formula.md` (that one writes a 4160x3120 FLOAT
destination from a 2080x1560 float source). The FCB weight plane is u8, tiled
522x522, half-res-doubled. Do not conflate them.

## Why the direct watchpoint instrument is inconclusive

Findings 3-4 pin down the failure mode that defeated the prior 14 instruments
and this one:

- The u8 tile is **pre-resident**: any hook at or after the FCB consumer /
  `0x1bce50` LUT helper observes an already-filled buffer, so a watchpoint set
  there only ever catches the block's **next** (float) lifetime after reuse.
- Catching the write therefore requires arming **before** the fill, i.e. at the
  u8 tile's allocation. This run's new probe
  (`u8tile_producer_watch_probe.py`) hooked `malloc`, matched an allocation in
  `[270000,300000]` (the 522x522=272484 u8 tile band), stepped out to read the
  returned buffer, and armed a 1-byte write watchpoint. Two defects made it
  inconclusive:
  1. **Size band is not unique to the byte tile.** The match fired early in
     startup; many ~270-300KB allocations exist, so arming on the first is not
     guaranteed to be the byte tile.
  2. **`SBThread.StepOut()` inside the breakpoint callback is fragile** under
     Rosetta batch lldb: the process stops with reason "step out" and the
     post-step arm did not reliably complete (no `U8P_ARMED`, no watchpoint
     hits across ~3 min of `drive()`), so `drive()` degenerated into a plain
     run-to-completion.

## Corrected next instrument (concrete)

Catch the deposit at **insertion into the specific TileStorage**, not at the
view or at raw malloc:

1. Break at consumer `0x406a10` **once, read-only**, to capture the byte
   `TileStorage` object pointer `S = *(FCB+0xf0)` for this render (no
   re-conclusion; this is allowed — the forbidden set is *hooking* the read
   path repeatedly, not a single identity read).
2. Statically resolve `lt::TileStorage`'s tile-insert method: the empty
   storage is `operator new(0xa0)` at ctor `0x406605`, control-block vtable
   `0x66b298`, float sibling `0x66b240`. Disassemble the `TileStorage` object
   vtable (object begins after the `__shared_ptr_emplace` header at
   control+0x10/0x18) to find its `insert(level,x,y,Tile)` entry; hook that,
   filtered to `this == S`. At the hit, the argument tile is freshly computed
   and the **backtrace frame #1..N is the producer** — RTTI-resolve it and read
   its source descriptor. This avoids both the pre-resident-timing wall and the
   malloc-uniqueness problem.
3. Alternative if TileStorage insert is inlined: arm the malloc watchpoint but
   (a) filter to **exact** size `272484`, (b) replace the in-callback
   `StepOut()` with a one-shot breakpoint planted at the caller return address
   `*(rsp)` whose callback reads `rax` and arms the watchpoint (race-free, no
   step in callback), and (c) after the first write, verify the destination
   holds a **doubled u8 weight** (not float) before accepting the producer.

## Honest non-claims

- The upstream producer's function address, RTTI/public name, and exact
  per-byte fill arithmetic remain **unknown** after this session.
- Findings 1-3 reinforce the already-documented "`$_1`/view is not the writer"
  structure with new instruction-level evidence; they are corroboration, not a
  new advance on the producer identity.
- Finding 4 (2x-doubled half-res u8 weight map) is a new constraint on the
  producer's output shape/arithmetic but does not identify the producer.
- `lt::SoftISP::Stats` and `setWhiteBalance::$_22` appear in the FCB/generator
  captured context (gen_introspect) but there is **no** evidence in this session
  tying either to the byte-tile writes; no producer name is asserted.

## Artifacts (this session)

- New probe: `tools/lldb_probes/cnr_lane3_producer/u8tile_producer_watch_probe.py`
- New driver: `tools/lldb_probes/cnr_lane3_producer/unit1_70mm_u8tile_producer.lldb`
- Static disassembly transcripts referenced inline (ctor `0x4064c0`, real byte
  TileCache ctor `0x3d1d40`, `$_1` __func vtable `0x660188` targets
  `0x4078a0..0x407940`).
- Re-analysed prior runs: `unit1_70mm_gen_introspect.json`,
  `unit1_70mm_storage_writer.json`, `unit1_70mm_bytebuf_reuse.json`.

---

## Session 2 addendum: the malloc-catch instrument and why it does not name the producer

I built the corrected next instrument and ran it. It is
`tools/lldb_probes/cnr_lane3_producer/u8tile_writer_catch_probe.py` +
`unit1_70mm_u8tile_writer.lldb`. Design (deadlock-avoiding, race-free arming):

1. hook `malloc`; when `rdi` is in the 522x522 u8-tile band, plant a ONE-SHOT
   breakpoint at the caller return address `*(rsp)` (no `SBThread.StepOut`);
2. the one-shot ret callback reads `rax` (fresh buffer) and arms a 1-byte WRITE
   watchpoint at `buf+0x400`;
3. on the first write, VERIFY the doubled-u8 weight signature
   (`b[2i]==b[2i+1]` over a DENSE, non-sparse region — checked both at `buf`
   head and in a 96-byte window around the just-written watch byte, which is
   header- and fill-order-agnostic). Accept -> capture producer backtrace +
   store operands; reject float/sparse -> disarm and hunt the next allocation.

### Result: INCONCLUSIVE, with a decisive negative finding

The instrument works and self-corrects (early false positive on a mostly-zero
buffer was fixed by requiring density; a flat bright weight region has few
distinct values, so distinctness must NOT be gated), but it did **not** accept
any doubled-u8 tile. Across the guided-upsample burst it armed/verified
**> 3200** allocations of size ~272484 and rejected **all** of them as
float/unpaired.

Decisive point: `522*522 (u8 tile) == 261*261*4 (half-res float) == 272484
bytes`. The fusion/upsample stage allocates thousands of 261x261 **float**
working buffers at exactly the u8-tile size; the probe correctly rejects every
one (they fail the equal-adjacent-byte test). Yet a real 272484-byte u8 weight
buffer provably exists (`bytebuf_reuse` seed, doubled pattern). The absence of
**any** doubled-u8 acceptance among thousands of same-size allocations indicates
the u8 byte tiles are **not discrete `malloc(272484)` blocks** — they are
carved from a tile pool / arena (consistent with the arena-packed tile addresses
seen earlier, e.g. `0x7f7c90008040`). **malloc-size filtering therefore cannot
catch the byte-tile producer.**

Secondary limitation: the arm-and-block scheme stalls if an armed candidate's
watched byte is never written before the buffer is freed (malloc_entry ignores
new candidates while `armed`), which is why runs freeze mid-hunt.

### Corrected next instrument (pool-aware, deadlock-free)

Do not hook `malloc`. Instead:

1. Statically disassemble the **storage tile-get** on the read path
   (`0x406a10 -> 0x3d2ca0` extraction) to recover the `TileStorage`/pool tile
   record layout and the arena base+stride by which a `(level,x,y)` maps to a
   `Tile<unsigned char>` data pointer. (Static reads/disasm are allowed; do not
   hook the read path.)
2. From that layout, find the sibling **tile-acquire / tile-put** (the function
   that hands out or installs a `Tile<unsigned char>` data pointer for a
   `(level,x,y)` into that same pool). Hook it, filtered to
   `storage == S = *(FCB+0xf0)` captured by ONE read-only stop at `0x406a10`.
3. On the first acquire/put of a byte tile, the caller frames are the producer:
   RTTI-resolve and read its source descriptor + store loop. This is one hit
   per real tile (deadlock-free) and pool-agnostic.

Alternative if the pool acquire is inlined: watch the arena directly. Pass 1:
one read-only stop at `0x406a10`, resolve the byte tile data pointer and its
containing arena base/size. Pass 2 (fresh run is required — addresses differ):
arm the watchpoint on the arena during the PRODUCER phase (before the CNR
consumer) rather than after; the producer phase precedes `0x406a10`, so break on
the first upstream fusion entry that touches `S`, then watch.

### Honest status

The producer function address, RTTI/public name, and exact per-byte arithmetic
remain **UNKNOWN** as of session 2 — resolved in session 3 below.

---

## Session 3: PRODUCER NAMED + exact per-byte arithmetic (RESOLVED)

The malloc/pool framing was a dead end because the premise ("byte tiles are
pre-resident, produced upstream") was **wrong**. Runtime backtrace capture at the
`lt::Tile<unsigned char>` constructor proves the byte tiles are generated
**lazily, on cache-miss, by FusionCacheBayer itself**, during the CNR consumer
descent.

### How it was found

RTTI string scan of `libcp.dylib` surfaced `__shared_ptr_emplace<lt::Tile<h>>`
(name `0x605450`, vtable `0x66ab48`) and `lt::TileCache<unsigned char>::renderROI<h>`.
A `__text` scan for RIP-relative `leaq` to `0x66ab48` gave the make_shared sites;
the `Tile<h>` constructor common to them is `0x3d7710`. Breaking on `0x3d7710`
(probe `tile_h_factory_probe.py`) captured a stable producer backtrace. A full
profile-3 HDR render of `L16_03434` runs in ~30 s at full speed (the earlier
malloc hook, not the render, was the bottleneck).

### The producer chain (runtime-proven)

```
0x406a10  FusionCacheBayer CNR consumer (setWhiteBalance path)
  -> 0x406afa
  -> 0x3d1ac6 / task dispatch (0x55a2,0x3873,0x5d97)
  -> 0x3d69b2  TileCache<h> generate-on-miss dispatch
  -> 0x407710  FusionCacheBayer BYTE-TILE GENERATOR  <=== the producer
       -> 0x3d16d0            compute tile ROI in source coords
       -> [FCB+0x120] 0x1aab40   render float ROI from the float TileCache<float>
                                  (half-res source -> 2x "doubling"; const-float scaled)
       -> 0x1bd1e0            float -> u8 encode (the per-byte arithmetic)
       -> 0x3d1f90            insert the u8 tile into byte cache [FCB+0xe0]
  -> 0x3d2610 / 0x3d7710  make_shared<Tile<h>> + Tile<h> ctor (fill from source)
```

`0x407710`: `r12 = *(rdi+8) = FusionCacheBayer` (confirmed: it uses `FCB+0xe0`
byte cache and `FCB+0x128` float cache, the exact ctor offsets). It uses the
float `TileCache<float>` at `FCB+0x128` (via `0x3d16d0`) for ROI/coordinate
mapping, renders the tile's float ROI via `0x1aab40` on the float-source member
`[FCB+0x120]`, encodes float->u8 via `0x1bd1e0`, and inserts via `0x3d1f90` into
the byte cache `FCB+0xe0`. (Exact field semantics of `FCB+0x120` vs `+0x128` are
not fully assigned; the WRITER and its arithmetic below do not depend on it.)

### Exact per-byte arithmetic (`0x1bd1e0`, static disasm)

```
scale = 256.0f            ; float32 const at libcp VA 0x5a9250
for y in 0..h-1:          ; h = dst[+0x14]
  for x in 0..w-1:        ; w = dst[+0x10]
    f    = src_f32[y*src_stride + x]         ; src floats at src[+0x20], stride src[+0x18]
    t    = (int) trunc(f * scale)            ; mulss ; cvttss2si
    byte = t - 1                             ; decl
    if byte < 0: byte = 0                    ; jns / xor  (clamp >= 0)
    dst_u8[y*dst_stride + x] = (unsigned char) byte
```

i.e. **`byte = max( (int)trunc(f * 256.0f) - 1, 0 )`**, dst bytes at `dst[+0x20]`.

This is the exact inverse of the proven consumer LUT `guide = sqrt((b+1)/256)`:
the plane stores a linear weight `f in [0,1]` as `b = trunc(256 f) - 1` (clamped),
and the consumer recovers `sqrt((b+1)/256) ~= sqrt(f)`, then squares back to `f`
in CNR lane 3. The loop closes exactly. The "spatial doubling"
(`255,255,254,254,...`) is the half-res float source rendered into a full-res
tile ROI by `0x1aab40` (the ROI scale const applied in `0x407710`).

### Corrections to prior sessions / docs

- **Refuted**: "byte tiles are pre-resident; producer is upstream of
  FusionCacheBayer." They are generated **by** FusionCacheBayer on demand.
- **Refuted**: "$_1 generator is a no-op." Session-1 examined only the `__func`
  *management* thunks (`0x4078a0..0x407940`, trivial clone/destroy/target). The
  actual per-tile generator body is `0x407710` and does real work.
- `storage_writer`'s "0 completions" was a wrong completion hook (`0x3D00F0`),
  not evidence of pre-residency.

### Anti-repeat

Grepped the FusionCacheBayer bundles and evidence dir: `0x407710`, `0x1aab40`,
`0x3d1f90`, and the `byte = max(trunc(256 f) - 1, 0)` arithmetic are **not**
documented anywhere. `0x1bd1e0` appears once (`bundle_proof_src1_source_image_producer_topology.md`)
only as an unexplained call target (`0x1be5f3 calls 0x1bd1e0`); its arithmetic
and its role as the FusionCacheBayer byte-weight encoder are new here.

### Artifacts (session 3)

- `tools/lldb_probes/cnr_lane3_producer/tile_h_factory_probe.py` +
  `unit1_70mm_tile_h_factory.lldb` (runtime backtrace catch at `0x3d7710`)
- run: `runs/cnr_lane3_producer/unit1_70mm_tile_h_factory.json`
- `renderroi_h_probe.py` (+driver) — proved `renderROI<h>` generation is NOT the
  path (0 hits), i.e. the byte cache is filled via `0x407710`, not `renderROI`.
- static disasm: producer `0x407710`, encoder `0x1bd1e0`, scale const `0x5a9250`
  = `256.0f`.

### Remaining (smaller) open point

The float source semantics behind `FCB+0x120` fed to `0x1aab40` — resolved in
session 4 below.

---

## Session 4: the float weight `f` = `lt::ColorFusionBayer` (source named; formula bottoms out in the L16 color-fusion core)

### `FCB+0x120` RTTI (runtime, `fcb120_probe.py`, break at `0x407710`, `fcb=*(rdi+8)`)

```
FusionCacheBayer+0x120  ->  lt::ColorFusionBayer   (RTTI N2lt16ColorFusionBayerE, vtable libcp 0x657aa0)
  ColorFusionBayer+0x60  = __func< lt::ColorFusionBayer::initialize(bool const*, lt::Vec2<float> const&)::$_1 >
                           signature  (lt::Rectangle<int> const&) -> lt::vec4x32f     (per-tile float producer)
  ColorFusionBayer+0x120 = shared_ptr<lt::RawImageFactory>        (the raw Bayer input)
  ColorFusionBayer+0x90/0xc0/0xf0/0x1f8 = heap float image planes (the fused module data)
```

`0x1aab40` is therefore `lt::ColorFusionBayer::process` (its `this` = `FCB+0x120`
= the ColorFusionBayer object). It maps the full-res tile ROI to half-res source
coords (integer `>>1` at `0x1aac60..0x1aac74`; base dims at `this+0x80/0x84`
doubled at `0x1aab9c`), i.e. a **half-res -> full-res 2x** expansion. The output
byte tile's exact pair duplication (`255,255,254,254,...`) is empirically
**nearest-neighbour** replication (interpolation would yield intermediate
values); a `this+0x60` virtual sampler is invoked but not fully disassembled.

### What `f` is (for Phoenix)

`f` (= CNR lane3 = guide^2) is the **second output of `lt::ColorFusionBayer`** —
a per-pixel Bayer color-fusion **blending weight/confidence in `[0,1]`**, computed
from the `lt::RawImageFactory` (the raw per-module Bayer input) and sampled at
half resolution, 2x-expanded, then quantised `byte = max(trunc(256 f) - 1, 0)`.
`ColorFusionBayer` is exactly the class `docs/LIBRARY_INVENTORY.md` calls "the L16
fusion pipeline you're trying to rebuild." Its per-pixel float formula lives in
`ColorFusionBayer::process` / its compute core `0x19C790` (const in the prior
`colorfusion_weight_probe.py`).

### Honest scope boundary + anti-repeat

- **Not new naming**: `tools/lldb_probes/cnr_lane3_producer/colorfusion_weight_probe.py`
  (a prior session) already states in its docstring that `0x407710` (`$_0`) asks
  `ColorFusionBayer::process (0x1aab40)` for two outputs and the second is
  quantised by `0x1bd1e0` into the `+0xe0` u8 cache. That topology + the
  `ColorFusionBayer` name were already known there, but were **never promoted to
  an evidence bundle**, and the main CNR bundle still lists the producer as open.
  What sessions 3-4 add and *prove*: the exact byte arithmetic
  `max(trunc(256 f) - 1, 0)` (scale `256.0f` @`0x5a9250`), the runtime RTTI
  confirmation `FCB+0x120 = lt::ColorFusionBayer`, and its `RawImageFactory`
  input + `initialize::$_1` per-tile callable.
- **Deep unknown (stop here, precisely)**: the per-pixel float value produced by
  `ColorFusionBayer::process` (core `0x19C790`) is the L16 **color-fusion
  blending-weight** computation over the raw Bayer modules. Deriving its exact
  formula is the core multi-module fusion RE — a separate, large effort, NOT a
  simple AWB/SoftISP scalar. It is not derived here. For Phoenix: lane3 must be
  ColorFusionBayer's weight output; until that fusion core is reproduced, lane3
  cannot be computed from a closed public formula — but it is definitively NOT
  the disproven constant `1.0`, and the byte<->float encode/decode around it is
  fully closed.

### `0x407710` `$_0` vs `$_1` clarification

Runtime RTTI at `0x407710` entry is the FusionCacheBayer float generator
`$_0` (over `Tile<float>`), not `$_1`. `0x407710` is the shared generator body:
it obtains the ColorFusionBayer outputs, stores the `Tile<float>` (cache `+0x128`)
**and** emits the quantised u8 sidecar (`0x1bd1e0`) into the byte cache `+0xe0`.
Session 3's "byte-tile generator" identification of `0x407710` stands; the
`$_0`/`$_1` label is corrected here.

### Artifacts (session 4)

- `tools/lldb_probes/cnr_lane3_producer/fcb120_probe.py` +
  `unit1_70mm_fcb120.lldb`; run `runs/cnr_lane3_producer/unit1_70mm_fcb120.json`
- static disasm `0x1aab40` (ColorFusionBayer::process; half-res->full-res 2x).
