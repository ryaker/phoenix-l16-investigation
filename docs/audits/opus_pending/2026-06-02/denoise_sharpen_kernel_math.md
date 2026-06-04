<!-- provenance: l16-investigator finder (static disasm) + orchestrator instruction/constant re-extraction, 2026-06-03 -->
**Status:** NEEDS_CODEX_VALIDATION + **NOT FOUR-ZOOM VALIDATED (static-only, zero renders).** This packet is
NOT done to Codex rigor — it is a static decode that has NOT been run at 28/35/70/150. It must get a four-zoom
runtime pass before it counts as done. Binary `libcp.dylib` x86_64.

# Denoise / sharpen kernel math + tuning defaults (STATIC decode — four-zoom pass OWED)

> ⚠ **W0 four-zoom CORRECTIONS (2026-06-03, `four_zoom_firing_census_W0.md`):** (1) the **bilateral W3 worker
> `0x2f6ad0` is DORMANT** at all four tiers — the launcher `0x2f6420` fires ~2,400–3,000× but dispatches to a
> non-W3 window; the W3 math below is a dormant example, and W1 must identify the live W{5,7,9} worker.
> (2) The sharpen factory ctor address is **`0x360a00`** (`push rbp` entry), NOT `~0x360b00` (which is `nop`
> padding) — orchestrator-verified. CNR apply/worker/installer + sharpen ctor/method DO fire four-zoom.

## SHARPEN = UNSHARP MASK (VERIFIED static; NOT four-zoom)
- Gaussian kernel generator `0x96980`: `coef = -0.5/σ²` (`mulss xmm0,xmm0` σ², `divss` by it), tap index lanes
  via `paddd`, `expf` (stubs `0x555f84`/`0x555eb2`) ⇒ `exp(-x²/(2σ²))` unnormalized Gaussian, taps 0..7.
- `SharpenLineFactory<f>` ctor `0x360bf0` (0x60-byte obj); methods `0x361020`/`0x361490` validate symmetry
  ("Kernel must be symmetric" `0x633b3d`, tol **1e-4** `0x5d45e0`).
- Per-scanline apply `0x3588f0`: **symmetric 7-tap 1D separable convolution** — symmetric pairs summed
  (`addps`) then shared-coeff multiply (`mulps`), coeffs at factory `+0x48/+0x4c/+0x50/+0x54` (VERIFIED).
- Builder: amount vs **1.0** (`0x5a8128`) / **1.3** (`0x5f1050`).
- A DISTINCT Laplacian-pyramid path exists (`CreateAndBlendLaplacianPyramids` `0x5f11b0`, `MattingLaplacianTiling`)
  = the `tone_adjust.lpyr_clarity` path — NOT decoded (gap).

## BILATERAL = piecewise-linear TENT range weight (VERIFIED static W3; NOT four-zoom)
- Launcher `0x2f6420`, tile 64×64, valid W∈{3,5,7,9} (`W3→0x2f6ad0, W5→0x2f78e0, W7→0x2f87e0, W9→0x2f97e0`).
- W3 math: `Δ=|nb−center|`, max-channel reduce; `t=max(maxΔ − guide·scale, 0)`; `t·=rcp(norm)`;
  **weight = max(1.0 − t, 1e-6)** (`1.0`@`0x5a8920`, **ε=1e-6**@`0x5e7380`); `num+=w·nb, den+=w`;
  `out = num·rcp(den)`. ⇒ **tent `max(1−|Δ|∞/R, ε)` — NOT exponential, NOT a LUT.** A min/max sorting network
  builds a local envelope scaled **0.75** (`0x5af320`). W5/7/9 share the rcp-normalized average (HYPOTHESIS:
  same weight, larger window — inner expr not decoded).

## NLM / PatchNLM<4> — NOT located (GAP). Symbols exist (RTTI 0x5f3580/0x5f3670/0x5f3720) but body unpinned.

## TUNING DEFAULTS (VERIFIED, byte-read — RE facts, no shipping caveat)
- `color_noise_reduction.color_denoise_multiplier` = **1.0**; `denoising.threshold_multiplier` = **1.0**
  (applied as `1.0/field`, `divss 0x3cc61e`).
- `tone_mapping.sharpening` = **0.5/1.0/1.5** (profile-dep); `tone_mapping.sharpening_scale` = **0.5/0.25**.
- `pipeline.parameter_scale` = **powf(0.5, window_field−1)** (base 0.5 `0x5a886c`) = 1.0/0.5/0.25/0.125.
- `bilateral_denoiser.window_size` default = **3** (`mov esi,0x3` `0x3cc4ac`).
- `tone_adjust.lpyr_clarity` stored ×**0.01** (`0x5a8868`) = percent units.
- Config-struct offsets: nlm chroma_boost `+0xd0`, bilateral chroma_boost `+0xd4`, threshold `+0xd8`.

## FOUR-ZOOM PASS OWED (this is NOT optional)
Run 28/35/70/150 with breakpoints on `0x34b3f0`(CNR), `0x2f6420`(bilateral), `0x3588f0`(sharpen apply),
`0x96980`(gauss): confirm WHICH denoise/sharpen paths fire at EACH tier, the actual per-tier window sizes /
amounts / σ used (read at the stop), and whether tiers select different profiles. Static says what the code
WOULD do; only the four-zoom run says what it DOES per tier. Until then this finding is half-done.

## Gaps (decode-level)
NLM/PatchNLM body+weight math; W5/7/9 inner weight expr; Laplacian-pyramid clarity kernel; fusion_sharpening
/fusion_detail_gain math; which sensor index selects which default profile; runtime profile override of these
compiled defaults.
