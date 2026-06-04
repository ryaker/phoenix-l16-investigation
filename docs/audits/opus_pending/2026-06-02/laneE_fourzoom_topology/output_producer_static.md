<!-- provenance: orchestrator static disasm of 0x41a7d0/0x3c6ac0, 2026-06-03 -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, static disasm). Producer path OBSERVED; final compositing
location OPEN (post-collection container consumer, not in this path).

# Lane E — output PRODUCER path (per-tile), and where final compositing is NOT
`0x41a7d0` (per-tile render producer, mode `0x774(%rbx)`):
- **mode 0** (`0x41a8b0+`): tile-table slot `leaq (rcx,r15,8)`; `callq 0x3b0740`; `0x3b9770` (rect-rescale,
  builds `-0x90`); **`0x3c6ac0` ×2** (cached-image getter — fast path `leaq 0xa0(%rdi),%rax; ret`; slow path
  `0x3c6ad0+` mutex_lock + cache-fill `0x1bdfa0/0xe76a0/0x13f100`); then `0x1bea00`, `0x1be970(-0xa0)`,
  `0xfbda0(-0x90)` (writes the resampled tile), `__release_shared`, `0xf7c0`. ⇒ a per-tile RESAMPLE/WARP
  that produces ONE tile into a tile-table slot.
- mode 3 (`0x41a850`): `0x3c6f80`; else (`0x41a99a`) throws "Unexpected rendering mode!".
- `0x3c6ac0` = per-camera/per-level CACHED image getter (returns cached `+0xa0`, fills under lock if absent).

## Where final compositing is NOT (OBSERVED-absent here) + the open question
`0x41a7d0` produces a single tile; it does NOT composite tiles into the final image. The completed tiles are
enqueued by collector `0x3bf820` into a level+priority-keyed RB-tree container (per the scheduler finding).
The **final compositing (container → output image) is a separate POST-collection pass** that reads that
container after the work-queue drains — NOT located here. That consumer is the remaining Lane E gap (likely
reached after the `0x3adf30` work-queue join, in the caller that owns the tile container). Tractable next:
find the container (State RB-tree) consumer / the function that gathers level-keyed tiles into the output
Image, via the work-queue owner's post-join code or a runtime BP after the queue drains.
