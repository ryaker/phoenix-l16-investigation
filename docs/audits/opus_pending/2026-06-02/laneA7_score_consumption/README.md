# Lane A7 — how the per-contributor SCORE is consumed (Blocker 5: acceptance/rejection)

**Status:** `NEEDS_CODEX_VALIDATION`. Extends Codex's `iramp_tuple_downstream_consumer` +
`iramp_tuple_post_reciprocal_weighted_add` (which proved the consumption path but left "final
ghost-suppression acceptance/rejection" open) and this campaign's Lane A6 (score = SSIM-class metric).
Binary `libcp.dylib` sha256 `b38dc4b3…`, VA == file offset. Instruction reads + the `-0.5` constant are
OBSERVED (deterministic); the ghost-suppression interpretation is a LEAD (rests on A6's SSIM identity).

## Headline (Blocker 5 — least-mapped wall)

Within the IRAMP score-consumer span (`0x36a7d8..0x36a93c`), the per-contributor score is consumed as a
**soft, normalized blend weight — there is NO hard score-thresholded accept/reject branch.** The only
float operation that gates on the score is a `maxss` clamp; every conditional branch in the span is a
loop bound, not a score predicate. Ghost/trail suppression is therefore **soft** (low-similarity
contributors are down-weighted, not dropped), with a **super-linear emphasis above score 0.5**.

## The weight, exactly (OBSERVED, `score_weight_dataflow.txt`)

```
0x36a7d8 movss 0x8(%rbx,%rcx,4),%xmm0   ; score = 3rd tuple field (Lane A3/A6)
0x36a7de movaps %xmm0,-0x4300            ; save
0x36a84b movaps -0x4300,%xmm3            ; xmm3 = score
0x36a855 addss [0x5a8120=-0.5],%xmm1     ; score - 0.5
0x36a85d xorps %xmm0,%xmm0
0x36a860 maxss %xmm1,%xmm0               ; max(score-0.5, 0)        (clamp, NOT a branch)
0x36a864 movaps %xmm3,%xmm1 ; shufps $0  ; xmm1 = (score,score,score,score)
0x36a86b addss %xmm0,%xmm0               ; 2*max(score-0.5,0)
0x36a872 blendps $0xe,xmm2(=0),xmm0      ; xmm0 = (2*max(score-0.5,0), 0,0,0)
0x36a878 addps %xmm1,%xmm0               ; weight_vec4 = (score+2*max(score-0.5,0), score, score, score)
...
0x36a8c4 mulps %xmm0,%xmm1               ; weight_vec4 * source_vec4
0x36a8c7 addps (%rdx,%rdi),%xmm1 ; store ; accumulate
...
0x36a938 rcpss %xmm2                      ; reciprocal of accumulated weight (normalized blend)
0x36a9bc mulss [0x5df904=0.2]            ; reciprocal*0.2 -> lane 3 blend (Codex-bounded)
```

So per contributor: **`weight_vec4 = (score + 2·max(score−0.5, 0), score, score, score)`**, multiplied
into the source vec4 and accumulated; the running weight is then reciprocal-normalized (`Σ w·src / Σ w`).
Three lanes use the **raw** score; lane 0 receives a **super-linear boost** once score exceeds **0.5**.

## Interpretation (LEAD)

Combined with Lane A6 (score = CDF 9/7 wavelet-domain SSIM-class structural similarity, range ~0..1):
this is a **structural-similarity-weighted normalized blend** where well-matched contributors (high
SSIM) dominate via the >0.5 boost and poorly-matched (ghosting) contributors are softly suppressed by
low weight. This is a coherent, *soft* answer to Blocker 5's "why Lumen avoids visible trails" — no hard
rejection is needed because misaligned contributors carry near-zero structural-similarity weight.

## Files
- `observations.md` — full dataflow + the decoded constants.
- `non_claims.md` — lane semantics, scope bounds, A6 dependency.
- `commands.txt` — reproducible extraction + constant decode.
- `manifest.json`.
Raw slice (gitignored runs/): `runs/laneA7_score_consumption/score_weight_dataflow.txt`.
