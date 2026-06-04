<!-- provenance: l16-investigator static W2 kernel-math decode (a8a76eb0bb89642b0) + orchestrator verify, 2026-06-03 -->
**Status:** NEEDS_CODEX_VALIDATION. W2 = denoise/sharpen kernel-math completion (static; four-zoom FIRING for
CNR/bilateral/sharpen already established in W0/W1b). Orchestrator-verified the load-bearing NLM-tent claim.

# W2 — denoise/sharpen kernel math (completes denoise_sharpen_kernel_math graduation)

## Unifying insight: ALL Lumen denoise weights are TENT/piecewise-linear (or covariance) — NONE exponential
- **Bilateral W5 (active worker `0x2f78e0`)** = same TENT as W3: `w = max(1 − max(0,|Δ|−thr)/range, 1e-6)`,
  consts 1.0 `0x5a8920` / ε=1e-6 `0x5e7380` / envelope 0.75 `0x5af320` / absmask `0x5a81f0` / sign-flip
  `0x5a88e0`. NEW: the `range` normalizer is **data-adaptive** — a min/max sort network (`0x2f834c..0x2f83ad`)
  computes local order stats → `rcpps`=1/range; channel-decorrelation basis `0x5f2380/0x5f2390` applied before
  the sort; spatial term = uniform 5×5 box (range-only weighting). Tent CONFIRMED for the active window.
- **NLM / PatchNLM<4>** (body **`0x3070e0`**, orchestrator-verified) = TENT too: `w = max(0, 1 − (d−thr)·slope)`
  (`0x30776b`: subps thr `[rbp-0x280]`; maxps 0; mulps slope `[rbp-0x290]`; `1.0`-subps; maxps 0), then
  `rcpps` 1/Σw `0x3076c0`. 4×4 patch (`0x5ab040`=16.0 norm), **SAD-ish abs distance** (absmask, no square).
  ⇒ **refutes the textbook `exp(−d²/h²)` NLM**. (Firing in bridge HDR UNtested — W0 didn't instrument NLM.)
- (CNR = covariance/structure-tensor, per the already-graduated denoise stages doc.)

## Sharpen = symmetric 7-tap normalized Gaussian FIR + unsharp
- Apply `0x3588f0` = symmetric 7-tap FIR (4 unique coeffs `+0x48/+0x4c/+0x50/+0x54`, each ×sum-of-symmetric-
  neighbors via `palignr`); produces the BLUR.
- Generator `0x96980` = `exp(−0.5·x²/σ²)` normalized to sum 1 (consts −0.5 `0x5a8120`, center-step 0.5
  `0x5a886c`; σ==0 → unit impulse).
- Unsharp combine consts 1.0 `0x5a8128` / 1.3 `0x5f1050` present (`orig + amount·(orig−blur)`).

## Graduation
- `denoise_sharpen_kernel_math.md` → GRADUATES: W5 tent decoded, NLM body located + tent decoded, sharpen FIR
  decoded; firing 4-zoom established (CNR/bilateral/sharpen). Core math complete.

## Residuals (scoped, do not block graduation)
- Sharpen σ→`SharpenLineFactory +0x48..+0x54` linkage (σ=1.0 at inspected caller `0x352597`, but 20 callers of
  `0x96980` — needs runtime read to confirm; so the numeric taps ≈[0.0044,0.054,0.242,0.399,…] are CANDIDATE).
- Unsharp combine instruction VA undecoded (consts found, expression not pinned).
- NLM search-window radius = runtime param (static slot poisoned `0xdeadbeef`); thr/slope computed in caller
  frame (not static consts); SAD-vs-SSD = SAD-leaning (abs, no square) but reduction order obscured.
- NLM firing in bridge HDR untested (separate from the decode).
