> GRADUATED to four-zoom OBSERVED (2026-06-03, W1b — four_zoom_data_W1b.md). drain structure 4-zoom; tile-count .lris-confounded not tier. Scope=first-hit/tier, Unit-1.

<!-- provenance: l16-investigator finder (static disasm) + orchestrator independent re-extraction of load-bearing VAs, 2026-06-03 -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, STATIC disasm; finder-produced, orchestrator-verified — all
load-bearing VAs independently re-extracted, see "Verification" below). Closes the Lane E gap left open in
`output_producer_static.md` ("final compositing = a separate post-collection container consumer = open").

# Lane E — final compositing consumer: list drain-and-gather `0x3bfe60` (+ RB-tree anchor REFUTED)

## Chain (OBSERVED)
`requestRenderROI` tile-collector lambda `0x3bf820` → builds a `{tag=0xd, level=2,…}` 0x70-byte **TileUpdate**
descriptor → real insert `0x3bfc40` into a container at **`RendererPrivate+0x260`** → workers drain →
render orchestrator `0x3bca90` (in the `RendererPrivate::startRendering` __func RTTI cluster) calls join-wait
`0x3c25a0` (pthread_cond_wait on +0x2c0 until count +0x270==0 / flag +0x278) → calls **gather `0x3bfe60`**
(container → `std::vector<TileUpdate>` of 0x70-byte structs) → filter by level/type → per-tile
ImagePyramid/Image-buffer write.

## The container is a priority-sorted doubly-linked list — NOT an RB-tree (REFUTES prior anchor)
Prior packets (`output_producer_static.md`, scheduler notes) called it a "level+priority-keyed RB-tree." That
is **REFUTED**: layout on `RendererPrivate` is a circular ring **head/tail +0x260/+0x268, count +0x270,
stopped-flag +0x278, mutex +0x280, condvar +0x2c0**. Insert `0x3bfc40` locks +0x280, walks `next=+0x8(node)`
comparing the **single sort key `+0x14`** (descending priority), `malloc(0x80)`, splices `prev=(node)`/
`next=+0x8(node)`, copies the 0x70-byte payload to `node+0x10` (`0x3efda0`), `incq +0x10`. No
left/right/parent/color fields. Level-guard mismatch throws **"Tile update has incorrect level!"** (cstring
file `0x634d39`).

## Gather `0x3bfe60(this=&container+0x260, out_vec*)` (OBSERVED, re-extracted)
1. Lock mutex (`0x3bfe7b call` pthread_mutex_lock); early-out if flag `[r15+0x18]`(=+0x278)≠0.
2. Clear `out_vec` (dtor loop stride 0x70).
3. **Ring walk:** `rbx=[r15+0x8]`(head); `cmp rbx,r15; je end` (ring sentinel = container); body reads
   payload `rbx+0x10`, appends to out_vec via `0x3f0130` (in-place copy) or `0x3c0c70` (grow); advance
   `rbx=[rbx+0x8]`; loop while `rbx≠r15`.
4. **Empty list:** second walk unlinks each node, saves `r14=[rbx+0x8]` then `operator delete`s it
   (`0x55638c`), zeroes count, unlocks. ⇒ drain semantics (copy-out then destroy).

## Post-gather compositing in `0x3bca90` (OBSERVED structure; copy-vs-blend = INFERRED)
Iterates the gathered vector at stride 0x70 (size via `0x6db6db6db6db6db7` magic = /0x70), **filters** tiles
by fields `(elem)==2, +0x24==0, +0x70==2, +0x94==0` (level/type select) into a second vector, then per tile:
`CIAPI::ImagePyramid` ctor `0x3985f0`, `operator[]` `0x3987e0`, `Image::width/height/stride/data`
`0x398010/20/30/00`, and **per-tile virtual-processor dispatch** `0x401ab0` + `call *%rax` (0x3bd05d/
0x3bd270/0x3bd355) writing into the destination Image buffer. ⇒ **per-region placement** (each tile's
processor writes its region), NOT a single N→1 accumulate-blend at THIS level. (The per-pixel N→1 multi-source
merge is the downstream IRAMP `0x3661b0` per [[lane-a3-merge-mechanism-findings]] — separate from this
assembly.) A distinct blend path exists elsewhere (cstring "blending weight has to be smaller than 128_u8!"
file `0x633da7`, ref ~`0x38b5bf`/`0x38b8d9`) — NOT inside this gather/orchestrator.

## Verification (orchestrator independent re-extraction — PASS)
- RB-tree refutation confirmed by the **libc++-correct** symbol family (this dylib links `libc++.1`,
  `std::__1`, sha256 `b38dc4b3…`): `__tree` helpers = **0**, `std::__1::map/set/multimap/multiset` = **0**,
  AND `std::__1::list/forward_list` = **0** (nm + c++filt, orchestrator-re-extracted 2026-06-04). (The earlier
  `_Rb_tree_increment`=0 check used the **libstdc++** name — 0 here by construction, right conclusion / wrong
  symbol family; superseded by this libc++ check.) ⇒ the container is neither an RB-tree NOR a `std::list` —
  it is a **hand-rolled/intrusive pointer-walk** (next/prev in the 0x80-byte node), consistent with the
  `0x3bfe60` ring-walk + `0x3bfc40` 0x80-byte-node insert.
- "Tile update has incorrect level!" present at file `0x634d39` (exact).
- `0x3bfe60` ring-walk / gather / unlink-delete disassembly matches the finder claim instruction-for-
  instruction (`0x3bfeb8`/`0x3bfebc`/`0x3bff08` walk; `0x3f0130`/`0x3c0c70` append; `0x55638c` delete).
- `[r15+0x18]` flag reconciles: r15 = &(RendererPrivate+0x260) ⇒ +0x8/+0x10/+0x18 = head/count/flag at
  +0x268/+0x270/+0x278.

## RTTI corrections (the anchors are std::function lambdas, reached only by indirect dispatch)
collector `0x3bf820` = `RendererPrivate::requestRenderROI $_12`; producer `0x41a7d0` =
`RendererPrivate::exportImage`; join `0x3adf30` = `WorkerThreadPool::start`. (0 direct callq/lea to any of
the three in __TEXT.)

## Residuals (NEEDS_CODEX_VALIDATION)
- copy-vs-blend at the byte level: per-tile processor vtable target not traced to memcpy-vs-weighted-blend;
  the blend cstring lives in an undecoded sibling function. INFERRED = per-region placement.
- Second gather caller `0x3b67b0` (sibling render variant) role not traced.
- Whether `0x3bca90` is `startRendering`'s worker body vs a sibling in the same RTTI cluster.
- All static; no runtime. Finder scratch (`/tmp/libcp_objd.txt`) is non-durable per custody rules.
