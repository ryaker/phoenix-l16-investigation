<!-- orchestrator coverage ledger, 2026-06-03. Honest accounting of the zoom-rigor of every session finding. -->
# Four-zoom coverage ledger — what rigor each finding ACTUALLY has

**Standard (Rich, 2026-06-03):** every finding must be done to Codex rigor = runtime at ALL four focal tiers
(28mm L16_02130 / 35mm L16_03041 / 70mm L16_03434 / 150mm L16_02285, all Unit-1), capturing per-tier behavior
+ data, scope-bound. "It's the same binary," static-only, single-zoom, or hit-counts are NOT "done." This
ledger states the truth: **as of now, ZERO session findings are four-zoom data-validated.** All are static or
single-zoom and OWE a four-zoom runtime pass before they count.

| Finding (packet) | Current rigor | Four-zoom owed |
|---|---|---|
| Merge score kernel `0x36cde0` (score_kernel_36cde0_two_factors) | STATIC | per-tier score values + factor1/2 firing |
| gate2/gate3 reject (gate2_gate3_reject_semantics) | STATIC (gate1 was 70mm-only live) | gates at 28/35/150 too; per-tier accept/reject |
| Final compositing `0x3bfe60` (final_compositing_consumer) | STATIC | per-tile container drain at all 4 tiers |
| Undistort ordering + LUT (undistort_ordering_lut_runtime) | **70mm ONLY** | 28/35/150 ordering + per-tier LUT + per-camera attribution |
| CCM apply site `0xbfa20` (ccm_apply_site_located) | STATIC (CCM perturb was 28mm-only) | per-tier CCM matrix values + which variant fires |
| CCM LRI-residency (ccm_lri_residency_link) | STATIC + 2-LRI parse | the `+0x14` writer at runtime, 4 tiers |
| Depth no-LRI-origin (depth_stereo_no_lri_origin) | STATIC + 2-LRI parse | 4-LRI parse; runtime depth construct per tier |
| Resample kernels (resample_kernels_constants) | STATIC | which kernel fires per inter-level resample per tier |
| Stereo cost math (stereo_cost_math_decoded) | STATIC | per-tier camera set (5+5+6), cost values, search loop |
| Denoise/sharpen stages mapped (denoise_sharpen_tone_stages_mapped) | STATIC | which denoise/sharpen fire per tier |
| Denoise/sharpen kernel math (denoise_sharpen_kernel_math) | STATIC | per-tier window/amount/σ; profile selection |
| AWB Block-8 consumption (laneB2 awb_consumption_runtime) | **28mm ONLY** | reciprocal-WB consumption at 35/70/150 |
| CCM consumption (ccm_consumption_runtime_INCONCLUSIVE) | **28mm ONLY** | inconclusive even at 28; 4-tier needed |

## Four-zoom campaign (in motion / queued, WSJF)
1. **Firing census (RUNNING, agent acd7b507969083d99)** — floor: does each stage fire at 28/35/70/150 (counts).
   This is step 1, NOT the bar.
2. **Four-zoom DATA-capture sweep (NEXT)** — at each stage's BP across all 4 tiers, read the actual operands:
   merge score values, CCM 4x4 matrix, stereo per-tier camera set + cost, CNR/bilateral params, undistort LUT.
   One batched multi-BP sweep per tier (4 renders) capturing all load-bearing findings' per-tier data.
3. **Re-run the single-zoom probes at four-zoom:** undistort (was 70mm), AWB + CCM (were 28mm).
4. **4-LRI re-parse** for the depth/calibration LRI findings (was 2 LRIs).
Each finding's packet gets updated from STATIC/1-zoom → four-zoom OBSERVED only after its data is captured at
all four tiers. No finding is "done" until this ledger shows it four-zoom.

> Tool-limit honesty (NOT an excuse to lower the bar): read-watchpoints are dead under Rosetta x86_64; I use
> breakpoints + register/memory reads at the stop + differential renders (same as Codex's workaround). Where a
> specific datum genuinely needs single-step/native-arm64, I state that explicitly per-finding — I do not
> silently downgrade the whole finding to "static is fine."
