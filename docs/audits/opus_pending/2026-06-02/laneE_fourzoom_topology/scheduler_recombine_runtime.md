<!-- provenance: runtime probe agent abfeafab (single 28mm render), 2026-06-03 -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, runtime LLDB, single 28mm profile-3 render). OBSERVED dispatch tally + static classification of targets; deeper pixel-assembly layer NOT crossed (bounded).

# Lane E — RUNTIME: the tiled work-queue scheduler + where tile outputs gather

## Prediction → partially refuted at this layer
Predicted L1 feeds L0 / tiles copied into one [arg0+0x38] image with no global Laplacian add. Result:
NO global Laplacian add at the dispatched layer (refuted-for-this-render); tiles are gathered PER LEVEL
into separate level-keyed containers (LEAD toward L0/L1 kept distinct, assembled deeper); the per-tile
pixel-copy is one layer below 0x41a7d0 (not crossed).

## OBSERVED (one 28mm render; libcp __TEXT loadbase 0x108c7a000; runtime VA = base+fileVA)
`0x3adf30` = locked work-queue consumer loop (predicate `0x3af770` = lock `0x38`, cond-wait `0x55607a`).
740 dispatches, 3 distinct targets; post-loop finalize `0x3ae0b2` = **0 hits** this render:
- `0x3adfcc` → **0x41a7d0** ×300 = per-tile RENDER PRODUCER / mode dispatcher. Branches on mode `0x774(%rbx)`:
  mode 0 → 0x3b0740, 0x3b9770 (rect-rescale), 0x3c6ac0 (image getter, ×2); mode 3 → 0x3c6f80; else throws
  "Unexpected rendering mode!" (`0x634bd6`). Tail `callq *0x10(%rax)` writes the tile into a `0x4d8`-table
  slot (`r15<<3`). *Per-tile output produced here.*
- `0x3adff1` → **0x3bf820** ×370 = per-tile RESULT COLLECTOR, level-keyed (throws "Tile update has
  incorrect level!" `0x634d39`); calls `0x3bfc40` (locked RB-tree/list insert, 0x80-byte node, size++ at
  `0x10(%r14)`, "Illegal priority!" `0x634ae0`) then `0x3efda0` (variant copy/cleanup). *Level+priority-keyed
  GATHER of completed tiles — NOT a pixel merge.*
- `0x3adfcc` → **0x3bb2b0** ×70 = per-tile geometry/region setup (SIMD bbox clamp; no image write).

## Interpretation (Lane E topology, OBSERVED + LEAD)
The "four-zoom merge topology" within one capture = a **tiled work-queue render**: tasks produce per-tile
outputs (mode-0 render: level-0 camera merge `0x3661b0` / level-1 resample `0x3ebb80`), which are **gathered
per-level into level-keyed containers** (`0x3bf820`/`0x3bfc40`), with final image assembly one layer deeper
(`0x41a7d0→0x3c6ac0` image getter + the `*0x10(%rax)` tile-slot write). **No global Laplacian/cross-resolution
add observed** on the bridge path. Combined with the level-fire finding (only L0/L1 fire, zoom-independent,
28mm+70mm), Lane E topology is now substantially mapped.

## Open (deeper, lower-WSJF)
- The exact pixel-copy/assembly instruction behind `0x41a7d0→0x3c6ac0` and how the level-keyed containers
  are consumed into the final image — one layer deeper (per-tile compute; overlaps the already-mapped IRAMP
  merge). Whether any cross-resolution combine lives below 0x3c6ac0/0x3b0740 — LEAD, uncrossed.
- Single render, 28mm/Unit-1, profile 3; S3 0-hits scope-bound to this capture.
