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
