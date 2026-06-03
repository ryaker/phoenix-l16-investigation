# Lane A7 — Observations

Span: `0x36a7d8..0x36a93c` inside IRAMP func `0x3661b0` (the tuple-consumer / weighted-add Codex
documented). Slice in `runs/laneA7_score_consumption/score_weight_dataflow.txt`. VA == file offset.

## O1 — score read (OBSERVED)
`0x36a7d8 movss 0x8(%rbx,%rcx,4),%xmm0` reads the 3rd tuple field (offset `+0x8`) — the per-contributor
score from Lane A3/A6 — and saves it to `-0x4300`. (Tuple fields 1,2 at `+0x0/+0x4` are read separately
at `0x36a7f7/0x36a808` to adjust a coordinate pair via `0x372a00`; that is flow, not weighting.)

## O2 — weight construction (OBSERVED, byte-anchored)
```
0x36a84b xmm3 = score
0x36a855 xmm1 = score + (-0.5)        ; const @0x5a8120 = -0.5 (byte-verified)
0x36a860 xmm0 = max(score-0.5, 0)
0x36a86b xmm0 = 2*max(score-0.5, 0)
0x36a872 xmm0 = (2*max(score-0.5,0), 0, 0, 0)   ; blendps $0xe with zero
0x36a878 xmm0 = (score, score, score, score) + xmm0
        => weight_vec4 = (score + 2*max(score-0.5,0),  score,  score,  score)
```
The single float gate on the score is the `maxss` clamp at `0x36a860`. No `ucomiss`/`comiss`/`cmpss`
on the score exists in the span; the conditional branches (`0x36a845 jle`, `0x36a8bc jle`,
`0x36a8e0 jl`, `0x36a8ec jl`) are all loop-count bounds (`testl %eax` / `cmpq`), not score predicates.

## O3 — accumulate + normalize (OBSERVED)
`0x36a8c0..0x36a8cb`: `xmm1 = source_vec4; mulps weight_vec4; addps dest; store` — per-contributor
weighted accumulation into the dest buffer. After the contributor loop, `0x36a934 shufps + 0x36a938
rcpss` form the reciprocal of the accumulated weight (a normalized weighted blend, `Σ w·src / Σ w`),
matching Codex's `iramp_tuple_post_reciprocal_weighted_add`. `0x36a9bc mulss [0x5df904=0.2]` blends
`reciprocal*0.2` into lane 3 (Codex-bounded).

## O4 — decoded constants (byte-verified)
- `0x5a8120 = -0.5` (the score offset before the max(·,0) clamp).
- `0x5df904 = 0.2` (lane-3 reciprocal blend).
- `0x5a887c = 2.0` (guided-blend stage `0x36abf0`, `subps/mulps/maxps/minps` clamped detail transfer).

## Interpretation (LEAD)
The merge weight is `(score + 2·max(score−0.5,0), score, score, score)` per contributor, normalized by
the reciprocal of the accumulated weight. Three lanes weight by raw score; lane 0 super-linearly boosts
contributors scoring above 0.5. With Lane A6 (score = SSIM-class structural similarity), this is a
structural-similarity-weighted normalized blend → **soft** ghost/trail suppression (Blocker 5): no hard
reject, but low-similarity contributors carry low weight and high-similarity ones are emphasized.
