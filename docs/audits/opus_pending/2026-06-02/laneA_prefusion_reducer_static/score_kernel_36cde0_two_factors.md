<!-- provenance: orchestrator static disasm of libcp.dylib 0x36cde0 + helpers 0x371730/0x371a90 + const decode, 2026-06-03 -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, STATIC disasm + constant byte-decode). Resolves the open
"q1=SSIM / q2=wavelet still LEAD" from [[lane-a3-merge-mechanism-findings]] (wave-1). The IRAMP merge weight
`score = sqrt(factor1 · factor2)` (Codex `bundle_lldb_iramp_36cde0_scalar.md` = `sqrtss(x·y)`) — both factors
are now decoded. Binary: `libcp.dylib` Mach-O x86_64.

# Lane A — merge score kernel `0x36cde0`: the two quality factors decoded

> ◑ **W1 four-zoom note (2026-06-03, `four_zoom_data_W1_batch1.md`):** the kernel FIRES at all four tiers and
> the `sqrt(xmm0·xmm1)` return is re-confirmed at `0x36e511`. BUT first-hit scores are **degenerate 0.0 at every
> tier** (the first contributor pairs against a boundary/zero patch), so per-tier score MAGNITUDE is NOT yet
> captured. Formula + four-zoom firing = OBSERVED; magnitude owed (skip-degenerate-hits W-pass). Stays Tier-0
> STAGING until magnitude is captured.

The per-contributor merge weight is a **geometric mean of two agreement scores**, each clamped to [0,1]:
one **structural-similarity (SSIM contrast-structure) term** and one **multi-scale wavelet-detail term**.
This is the weight that feeds the `1/Σscore`-normalized soft average in the terminal merge `0x3661b0`.

## FACTOR 1 — windowed SSIM contrast-structure term (fully OBSERVED, 0x36ce06..0x36cf24)
Over a **16×16 window** (loop `0x36ce30..0x36cea4`; both patches `rdi`=X and `rsi`=Y; 4-wide SSE = per-channel
RGBA), it accumulates the five SSIM moments, then `*1/256` (`0x5cbfc0`=0.00390625) → means:
- `ΣX,ΣY → μX,μY`; `ΣX²,ΣY² → ` var via `mean(sq)−mean²` (`subps`), each `max(0,·)` → `σX², σY²`;
  `ΣXY → cov = mean(XY)−μXμY`, `max(0,·)` → `σXY`.
- Combine (`0x36cee6..0x36cf24`): `cs = (2·σXY + C2) / (σX² + σY² + C2)` with **C2 = 0.03** (`0x5fdc50` =
  `{0.01, 0.03, 0.03, 1.0}` = `{C1,C2,C2,1}`; the **luminance term `(2μXμY+C1)/(μX²+μY²+C1)` is NOT computed**
  — this is the SSIM *contrast×structure* sub-term only, not full SSIM).
- **Alpha/coverage weighting:** `shufps xmm0,xmm0,0xff` broadcasts **mean of channel-3 (Y's lane-3 = alpha/
  coverage)** and multiplies it into the cs term ⇒ `factor1_raw = μY_alpha · cs`.
- **Affine remap + clamp:** `(factor1_raw − 0.8) · 5.26316` then `clamp[0,1]` — consts `0x5fdc60`=−0.8 (floor),
  `0x5fdc70`=5.26316 = **1/0.19**, `0x5a8920`=1.0 (ceil). ⇒ maps cs∈[0.8,1.0]→[0,1]; cs<0.8 ⇒ 0.
  Result stored `[rbp-0x80]`.

## FACTOR 2 — multi-scale (4 dyadic) wavelet-detail term (OBSERVED structure; 0x36cf28+)
After factor-1, two separable filter helpers run on the Y patch (`rdi=r14`):
- `0x371730` / `0x371a90` = **separable high-pass detail extractors**: each loads a sample and a neighbor,
  `mulps` the neighbor by a fixed low-pass coef (`0x5cbfd0/0x5cbfe0/0x5cbff0/0x5cc000`) and `subps`
  (signal − lowpass = **detail/wavelet coefficient**); strides `0xe0/0xf0` (horizontal) and `0xf00/0x1000`
  with a −0x100 loop (vertical) ⇒ a 2D separable wavelet/detail transform across the patch.
- The continuation loop (`0x36cf50+`) reads the transformed planes, `andps` with `0x5a81f0` = `0x7fffffff`
  (**abs-value mask** → |detail|), and accumulates.
- **Dyadic scale weights** `0x5fdb10` = `[-0.005208, -0.010417, -0.020833, -0.041667]` = `[-1/192, -1/96,
  -1/48, -1/24]` → **ratio 1:2:4:8 across 4 scales** (the multi-scale structure cited in wave-1).
⇒ factor-2 = a **4-scale wavelet-detail agreement** score (the |detail| energy comparison), clamped like
factor-1. (Exact per-scale combine arithmetic of factor-2 = LEAD; the *form* — separable high-pass + dyadic
1:2:4:8 weights + abs accumulate, second clamped agreement — is OBSERVED.)

## COMBINE (Codex-committed): `score = sqrt(factor1 · factor2)`
`0x36cde0` returns `sqrtss(xmm0·xmm1)` (Codex `bundle_lldb_iramp_36cde0_scalar.md`) ⇒ the contributor weight =
**geometric mean of (structural cs-SSIM) and (multi-scale wavelet detail)**, each in [0,1]. Stored
unconditionally to tuple slot-2 (`0x369e91`) and consumed by the `rcpss 1/Σscore 0x36a938` soft-average.

## Clean-room meaning (Rule #0: reimplemented algorithm, not copied bytes)
Phoenix's merge weights each contributor by `w = sqrt( clamp01((μ_alpha·cs − 0.8)/0.19) · wavelet_detail )`,
where `cs = (2σXY+C2)/(σX²+σY²+C2)`, C2=0.03, over a 16×16 window, and `wavelet_detail` = the 4-scale
(1:2:4:8) high-pass |detail| agreement. Then per-pixel output = `Σ w_i·p_i / Σ w_i`. The constants
(C2=0.03, 0.8 floor, 0.19 span, 1/192 base scale) are libcp's; a clean-room impl derives/justifies its own.

## Cross-check vs COMMITTED evidence (verify-before-trust — PASS)
Codex's committed `docs/evidence/bundle_lldb_iramp_36cde0_scalar.md` independently corroborates this decode:
returns `sqrt(xmm0·xmm1)` (its line 13/171/209) = my `sqrt(factor1·factor2)`; SAME constants `0x5fdc50`=
`(0.01,0.03,0.03,1.0)` and `0x5fdc60`=`(-0.8,…)` (its line 128-129); "after the first statistics stage, the
body calls **two internal helpers on the `r14` patch**" + "absolute-value reductions, repeated patch-statistics
blocks" (its line 137/146) = my factor-2 (helpers `0x371730`/`0x371a90` on r14, abs-mask Σ|coef|); "non-negative
**variance-like and covariance-like** terms… clamps/scales" (its line 207) = my σX²/σY²/σXY cs term. **No
contradiction.** This packet ADDS the exact arithmetic Codex left as "variance-like/clamped": the explicit
`(2σXY+C2)/(σX²+σY²+C2)` cs form, C2=0.03, the alpha-mean weight, and the 1:2:4:8 dyadic factor-2 weights.
Note: Codex deliberately did NOT assert the public name "SSIM" — factor-1 is identified here as the SSIM
contrast-structure form by **mathematical recognition of the decoded formula**, not by any symbol string.

## Residuals (NEEDS_CODEX_VALIDATION)
- Exact factor-2 per-scale combine arithmetic (the 4-scale reduction → single [0,1] value) — form OBSERVED
  (separable high-pass + abs Σ + dyadic weights), exact closed formula LEAD. Codex's extra filter consts
  `0x5cc010`=−0.882911, `0x5cc040`=0.869864 are the helper low-pass taps (its line 158/161).
- factor-2 input = **r14 (Y patch)** — RESOLVED by Codex line 137 (helpers operate on r14); cross-patch
  detail comparison (vs X) not separately traced.
- Single-scale vs multi-scale: factor-1 is single-scale on the raw patch (OBSERVED); only factor-2 is
  multi-scale. (Corrects any prior phrasing implying BOTH factors are multi-scale wavelet.)
- All static; no runtime confirmation of the score values for a live contributor.
