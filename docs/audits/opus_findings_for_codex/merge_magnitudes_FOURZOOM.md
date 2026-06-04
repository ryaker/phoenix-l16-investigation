<!-- GRADUATED finding. provenance: W5 (28/70, ae7b8ff22388c7f26) + W5b (35/150, a18096c1c6a5289b5) mid-render LLDB magnitude capture + orchestrator deterministic arithmetic/bit-pattern re-check (2026-06-04). Consolidates + graduates the data-dependent-magnitude residual that was the former "Rosetta Kth-hit tool wall". -->
**Status:** NEEDS_CODEX_VALIDATION — **GRADUATED to four-zoom OBSERVED** (Tier 1). The data-dependent
magnitudes of the merge/score/CCM sites — the former **"Kth-hit uncapturable under Rosetta" tool wall** —
are captured on **all four canonical tiers (28/35/70/150mm, Unit-1)**. Every score/Σscore/CCM value below
was re-checked deterministically by the orchestrator from raw IEEE-754 bits (a·b=product, √product=score,
1/Σ reciprocal, I1I2I3 basis constants) — relerr ≤ 1e-4 (rcpss is hardware ~12-bit). Scope: **single
mid-render sample per tier** (score: 2 samples on 28/35/70) — proves non-degenerate magnitudes + the math
chain, NOT a full per-pixel distribution. Unit-1 only.

# Merge / score / CCM data-dependent magnitudes — four-zoom

## METHOD (the wall-break; reusable)
The earlier "uncapturable under Rosetta" claim was **premature** — only per-hit Python-callback /
`--auto-continue` had been tried (those stampede 30+min on multi-thread stop). **LLDB ignore-count +
conditional breakpoints are core-handled (no Python callback), reach mid-render in ~11–50s, no stampede:**
- **ignore-count:** `breakpoint set --shlib libcp.dylib --address 0xVA -i N` → stops once on hit N+1.
  (Cost ~linear: N=2000 ~18s, N=8000 ~47s. ⚠ N must be **below the BP's total call count** — `0xbfa20`
  (CCM) is invoked <2000×/render, so `-i 2000` overshoots → use first-hit `-i 0` there.)
- **conditional:** `-c "(*(int*)&$xmmN) != 0xHEX"` (register lane) / `-c "(*(int**)($rdi+8))[k] != 0xHEX"`
  (deref struct ptr). LLDB **rejects** `(unsigned)$xmm` / `$xmm.uint32[0]` — use the pointer-cast form.
- **step-inst:** after stopping, `thread step-inst` walks single-thread (mulss→sqrtss) with no stampede.
- Launch quirk: `settings set target.run-args` rejects `--profile` (ambiguous lldb opt) ⇒ use
  `process launch -- "<seed>" "<out>" "--profile" "3" "--export-fmt" "3"` (quoted, space-path-safe).
- read-watchpoints stay DEAD under Rosetta; differential-render defeated by nondeterminism — those two
  remain the only verified limits (not needed here).

## 1. Score kernel `0x36cde0` = `sqrt(factorA · factorB)` — non-degenerate, four-zoom
Return chain `0x36e511 mulss %xmm1,%xmm0` (xmm0=factorA, xmm1=factorB) → `0x36e515 sqrtss` → `0x36e528 ret`.
| Tier | hit | factorA | factorB | product | score=√ (orch bit-checked) |
|---|---|---|---|---|---|
| 28mm | #8001 | 0.72990 | 0.83486 | 0.60936 | **0.78062** ✓ |
| 35mm | #2001 | 0.21769 | 0.54373 | 0.11836 | **0.34404** ✓ |
| 35mm | #8001 | 0.22764 | 0.38145 | 0.08683 | **0.29467** ✓ |
| 70mm | #2001 | 0.44620 | 0.88553 | 0.39512 | **0.62859** ✓ |
| 70mm | #8001 | 0.77157 | 0.78882 | 0.60862 | **0.78014** ✓ |
| 150mm | #2001* | 0.97720 | 1.00000 | 0.97720 | **0.98853** ✓ |
\*150mm #2001 first landed on a genuine **zero-factor pixel** (factorA=factorB=0 — a real masked/zero-weight
sample, not garbage); re-sampled with `xmm0≠0 && xmm1≠0` for the representative value. Genuine
per-contributor scores in [0,1] (wavelet-SSIM-style) on every tier — NOT the degenerate 0/1/0.2 first-hit.

## 1b. Merge weighting FORMULA (static, byte-re-extracted 2026-06-04 — graduates `lane_semantics`)
The first weighted-add (`0x36a8b0` loop) is a **score-weighted average** `Σ(w·src)/Σscore`. Independently
re-disassembled from `b38dc4b3`:
- **per-contributor accumulate** `0x36a8c0`: `movaps src(%rcx,%rdi),%xmm1; mulps %xmm0(=weight_vec4),%xmm1;
  addps dest(%rdx,%rdi),%xmm1; movaps %xmm1,(%rdx,%rdi)`.
- **denominator = Σ raw score (scalar)** `0x36a8fe addss %xmm3,%xmm2` with `%xmm3 = -0x4300 = score` (NOT the
  boosted lane-0 weight) → normalized `0x36a934 shufps $0; 0x36a938 rcpss` = **1/Σscore** (the same site
  whose magnitude §2 captures).
- **weight_vec4 construction** (`0x36a852–0x36a878`, byte-verified incl. the constant):
  `xmm1 = score + (−0.5)` (`addss [0x5a8120]`, read = `0xbf000000` = **−0.5**) → `xorps %xmm0` (=0) →
  `maxss` ⇒ `max(score−0.5, 0)` → `addss %xmm0,%xmm0` (**×2**) → `blendps`(lane0 only) → `addps`(+broadcast
  score) ⇒ **`weight_vec4 = (score + 2·max(score−0.5,0), score, score, score)`**.
⇒ lanes 1–3 = plain score-weighted mean; **lane 0 super-linearly over-weights high-similarity contributors
(score > 0.5)**. Combined with the score kernel (§1, zeros below cs-SSIM≈0.8): poorly-matched contributors
contribute ≈nothing; well-matched ones average, lane 0 favoring the best. (Physical identity of lane 0 —
color vs luma vs weight channel — remains a LEAD; the `-0x1260`/`-0x1230` descriptor layout is not decoded.)

## 2. Merge Σscore `0x36a938 rcpss` (inside terminal merge `0x3661b0`) — real accumulated denominators
`0x36a934 shufps $0,%xmm2` broadcasts the accumulated Σscore → `0x36a938 rcpss %xmm2,%xmm2` = 1/Σscore
soft-average normalizer. (common-0.2 skipped via `-c (*(int*)&$xmm2) != 0x3e4ccccd`.)
| Tier | Σscore | 1/Σscore (rcpss) | exact 1/Σ | rel-err |
|---|---|---|---|---|
| 28mm | 0.25464 | 3.92627 | 3.92710 | 2.1e-4 |
| 35mm | 0.94357 | 1.05981 | 1.05981 | 6.6e-6 |
| 70mm | 0.39071 | 2.55957 | 2.55943 | 5.6e-5 |
| 150mm | 5.20000 | 0.19229 | 0.19231 | 8.6e-5 |
| (common) | 0.20000 | 5.00000 | 5.0 | — |
⇒ direct four-zoom evidence the merge computes **1/Σscore** as the soft-average normalizer; accumulated
Σscore is genuinely tier-varying (150mm carries far more accumulated weight at its sampled tile than 35mm).

## 3. CCM `0xbfa20` — fixed I1I2I3 (Ohta), four-zoom uniform, NOT per-camera
Loads 4×4 from `[[rdi+0x8]]`. First-9 floats row-major, **bit-identical all four tiers**:
```
0x3f13cd36 ×3              = 0.57735 0.57735 0.57735   = 1/√3      (luminance axis)
0x3f350529 0 0xbf350529    = 0.70711 0 -0.70711        = ±1/√2     (R−B opponent)
0x3ed10625                 = 0.40825                    = 1/√6      (R−2G+B opponent)
```
= the **Ohta/PCA `I1I2I3` orthonormal decorrelation basis** (M1 forward; M2 = its 3×3 transpose,
orthonormal ⇒ inverse=transpose). **Four-zoom exclusion test:** conditional excluding BOTH matrices
(`-c "(*(int*)(*(long*)($rdi+8))) != 0x3f13cd36"` — the (0,0) entry is transpose-invariant so one condition
covers M1+M2) → **full render to 100%, clean exit (status 0), conditional never fired, on ALL FOUR tiers**
(28/70 W5, 35/150 W5b). ⇒ no LRI-derived per-camera 3×3 is promoted to 4×4 at this site on any tier; the
reopened per-camera-CCM question is closed for `0xbfa20`: it is the **fixed I1I2I3 decorrelation**,
data-independent, tier-uniform. (A per-camera CCM at some OTHER VA, and the `[rdi+0x8]` matrix producer,
NOT investigated = residual.)

## Scope / residuals (do not over-read)
- Single mid-render sample per tier (score: 2nd sample on 28/35/70). Proves non-degenerate magnitudes + the
  math chain; NOT full per-pixel distributions, NOT total call-count censuses.
- Does NOT prove `0x3661b0`/`0x36cde0` ARE the merge/reducer per the two-prong rule (N-accept + N→1-store) —
  this confirms MAGNITUDE semantics of already-located sites. `reducer_verdict.md` stays staging.
- CCM exclusion proves only that no non-I1I2I3 matrix reaches `0xbfa20` under the tested renders — not that
  `0xbfa20` is the binary's only CCM site.
- Unit-1 only; Unit-2 twins untested (and the U2 corpus lacks a clean 35mm tier — see corpus correction).

## Supersedes / graduates
Closes the "TOOL WALL (Rosetta)" residual in `REMEDIATION_LEDGER.md` and the magnitude residual in
`PIPELINE_SYNTHESIS.md` (stage 4/7). Graduates staging docs `score_kernel_36cde0_two_factors.md`,
`score_production.md`, `ccm_apply_site_located.md`; upgrades the Σscore note in
`terminal_merge_3661b0_FOURZOOM.md`. Working capture log: `../opus_pending/2026-06-02/four_zoom_data_W5_magnitudes.md`.
