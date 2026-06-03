# Lane A7 — Non-claims

1. **Lane semantics of `weight_vec4` not resolved.** Three lanes use raw score, lane 0 gets the
   `2·max(score−0.5,0)` boost; which lane is a color channel vs a weight/normalization-accumulator
   channel (and how that interacts with `Σw·src / Σw`) needs the **source vec4 layout** (the buffer at
   `0x36a8c0 (%rcx,%rdi)`), not resolved here. So the precise per-channel effect is a LEAD.

2. **"Ghost suppression" is an interpretation, not proven.** The soft-weighting MECHANISM (no hard
   reject; >0.5 boost) is OBSERVED. That it *is* the trail/ghost-suppression of Blocker 5 depends on
   Lane A6's SSIM-class identification (itself a LEAD) and on the score being a per-contributor
   alignment-quality metric.

3. **Scope-bound to `0x36a7d8..0x36a93c`.** "No hard score threshold" is for THIS consumer span. Hard
   gating exists elsewhere in the pipeline (e.g. the per-tile coverage sentinel `0x80000000` in Lane A3,
   and C6 routing) — those are upstream *selection*, not score-based merge acceptance. This packet does
   not claim Lumen never rejects.

4. **No runtime confirmation.** Static dataflow only; first-hit score values are thread-dependent
   (per Codex) and not promoted. The `-0.5`/`0.2`/`2.0` constants are byte-read (deterministic).

5. **Does not assemble the full post-blend policy** (the `0x36aa30` separable-weight product, the
   `0x36abf0` guided detail-transfer with `maxps/minps` clamps, the `0x36acf0` 3x3-matrix lane mix).
   Those are later stages, bounded only by shape here.

6. `NEEDS_CODEX_VALIDATION`. No canonical doc touched; no cross-citation of an Opus packet as fact
   (A6/A3 referenced as sibling context, not as proof).
