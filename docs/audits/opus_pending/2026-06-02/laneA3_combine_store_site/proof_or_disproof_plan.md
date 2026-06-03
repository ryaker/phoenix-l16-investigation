# Lane A3 — Proof / disproof plan (runtime)

## Decisive question

Does one output element receive accumulate-writes from **≥2 distinct contributors** (H-REDUCE), or is
each output element written by **exactly 1 contributor** (H-MOSAIC)?

## Cheap experiment (no hardware watchpoint needed)

Break at `0x369f65` (the `addq -0x1710(%rbp), %rdx` that resolves the dest base+warp-offset, just
before the inner `,%rcx,4` tile indexing). At each hit, log:

- `rdx` — the resolved per-tile dest base+offset (the output address family for this tile).
- the live contributor identity — snapshot from `-0x4410(%rbp)` (set by `0x366b6a movq %rbx,-0x4410(%rbp)`),
  i.e. the current contributor index `rbx`.

Auto-continue after logging (breakpoint `--auto-continue` + Python tally) so the render completes.

### Decision rule
- **Same `rdx` value observed under ≥2 distinct contributor ids ⇒ H-REDUCE proven** (for that tile,
  that zoom): overlapping contributions sum into one output region.
- **Every `rdx` value observed under exactly 1 contributor id ⇒ H-MOSAIC**: disjoint tiling.

Because `0x369f65` fires per-tile (not per-pixel), the hit volume is tractable for a tally callback.

## Scope discipline

- Run **four-zoom** (28/35/70/150mm canonical Unit-1 seeds) — a merge-topology claim is zoom-bound.
- Renders **sequential only** (documented 150mm thread-timing crash); only while Codex is confirmed
  offline.
- Report stays scope-bound: a result is "OBSERVED under tested ROI tiles," not "all pixels."
- This proves overlap-vs-disjoint of the accumulate. It does NOT by itself close `CLM-PREFUSION-002`
  (acceptance/rejection + semantic payload remain separate open items).

## Disjointness from Codex's live thread

This walks the IRAMP accumulator (`0x365960`/`0x3661b0`/`0x369f65`) backward. It must NOT instrument
the `0x23c5f0`/`0x23faf0` State-helper chain that Codex's uncommitted `state_helper_23faf0_record_chain`
thread is following forward. Disjoint VAs by construction.

## Harden-static option (no render)

If a render window is unavailable, extract and trace `0x374ac0` (crop helper that sets the `-0x1730`/
`-0x1710` view base) to confirm whether `this->0x8` is the externally-visible output buffer or an
internal scratch — this strengthens O3 without a render.
