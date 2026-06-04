<!-- W4 capstone: coherent picture from the four-zoom-GRADUATED findings only. 2026-06-03. -->
**Status:** NEEDS_CODEX_VALIDATION. Synthesis of the **Tier-1 graduated** findings (four-zoom OBSERVED, this
dir). Staging working-docs cited but not relied on. Each finding's scope (first-hit / structure / Unit-1) is in
its own packet. This is the entry point for Codex's validation pass.

# L16 bridge-HDR pipeline — four-zoom-graduated synthesis

## End-to-end order (all stages four-zoom firing-confirmed unless noted)
1. **LRI calibration parse** (`lri_calibration_parser_FOURZOOM`) — intrinsics 5+5+6, distortion pure-radial
   (3 optical groups), Block-6 CCM+spectral (excl {1,15}), Block-8 AWB f19.15, lens-shading 16×17×13×4×4,
   vignetting. **STRUCTURE cross-unit (U1+U2); VALUES per-body.** Block count 11 wide / 12 tele.
2. **Per-camera UNDISTORT** (`undistort_ordering_lut_FOURZOOM`) — `0x261940`, 4096-LUT radial; center/LUT split
   by camera GROUP (wide 2020,1505 / tele 2075,1590); runs PRE-merge.
3. **Stereo DEPTH** (`depth_stereo_no_lri_origin_FOURZOOM`, `stereo_cost_math_FOURZOOM`) — runtime-computed (NO
   LRI origin); cost = weighted truncated-L1 multi-view photo-consistency (`0x2732f0` via runPass `0x276790`,
   live caller `0x276860`, NOT the dormant driver `0x2730c0`); **N=4 source cams, tier-invariant**. Depth feeds
   the merge warp (ledger CLM-WARP-003). Plane-sweep search+argmin = caller (tool-walled magnitude).
4. **IRAMP terminal MERGE** (`terminal_merge_3661b0_FOURZOOM`, `merge_magnitudes_FOURZOOM`) — `0x3661b0`,
   per 512×512 tile, **N=5 contributors** (ctx+0x18 vector, N=(end-begin)/16), tier-invariant; weighted
   soft-average **1/Σscore four-zoom-captured** (`0x36a938 rcpss`: Σscore 0.255/0.944/0.391/5.20 →
   3.93/1.06/2.56/0.192 for 28/35/70/150); score kernel `0x36cde0` = `sqrt(cs-SSIM × 4-scale wavelet)`,
   non-degenerate [0,1] all four tiers; lane-3 detail-transfer `0x36aa30` (recip·0.2); contributor sentinel
   `0x36930f`. **Reduction MAGNITUDE now CAPTURED four-zoom (W5+W5b, tool wall broken).** B-spline resample is
   merge-interior.
5. **RESAMPLE** (`resample_kernels_FOURZOOM`) — B-spline `0x2b2be0` (merge-interior) + Catmull-Rom `0x36f800`
   (separate stage `0x3d0650`); both 4-tap 64-phase LUT builders.
6. **DENOISE** (`denoise_sharpen_stages_FOURZOOM`, `denoise_sharpen_kernel_math_FOURZOOM`) — ColorNoiseReduction
   (`0x34b3f0`, covariance/multi-scale, registers before CCM); bilateral active window **W5** (`0x2f78e0`,
   TENT range weight); NLM/PatchNLM<4> (`0x3070e0`, TENT, 4×4 SAD patch). **All denoise weights tent/covariance
   — none exponential.** CNR params 1.0/1.0 four-zoom.
7. **COLOR — TWO transforms** (`color_consumption_FOURZOOM`): (a) **per-camera CCM `0xa9f20`** = the LRI
   **Block-6 f2.2** 3×3 (row-sums [0.9642,1.0,0.8252], read live four-zoom; matrix `*[payload+0]+0x14`,
   written at construction `0x3184d0` not render) — the per-camera-CCM question is RESOLVED; THEN (b) **fixed
   I1I2I3 decorrelation `0xbfa20`** (Ohta 1/√3,1/√2,1/√6; exclude-both → clean exit all tiers; bit-identical
   four-zoom; static-init `__const 0x5f2380`/`0x374505`→`__bss 0x671980`, write-wp 0 hits — also = the
   post-merge `0x36acf0` matrix). `0xa9f20` and `0xbfa20` are distinct + not call-linked. AWB reciprocals
   folded into the demosaic color matrix (28mm runtime confirmed; 35/70/150 OWED — lead: `0xa9340` divss triple).
8. **SHARPEN / tone-adjust** (`denoise_sharpen_kernel_math_FOURZOOM`) — symmetric 7-tap Gaussian-FIR unsharp
   (`0x3588f0` + gen `0x96980`); separate Laplacian-pyramid clarity path (undecoded).
9. **CALIB accept/reject gate** (`accept_reject_gate_FOURZOOM`) — `0x216f60`/`0x217ac6`, 0.25 ceiling, fires
   4-zoom (35mm near-boundary 0.2485); gate2/3 untriggered.
10. **OUTPUT ASSEMBLY** (`final_compositing_consumer_FOURZOOM`) — gather `0x3bfe60` drains a priority-sorted
    doubly-linked list (NOT RB-tree), per-region tile placement.

## Cross-wave syntheses (each multi-finding)
- **"5+5+6" is the STATIC lens/intrinsics focal grouping only.** Runtime contributor counts are tier-invariant:
  stereo 4 / depth-src 4 / merge 5. The merge/depth core is tier-independent at the tile level; per-tier
  full-canvas differences are handled by TILING.
- **All denoise weighting is tent/covariance, never exponential** (bilateral W5, NLM, CNR).
- **Calibration: structure universal cross-unit, values per-body.** Cross-unit invariants: CCM row-sums
  [0.9642,1.0,0.8252] + Block-5 vignetting (byte-identical = firmware constant).

## RESIDUALS for Codex
- **Data-dependent MAGNITUDES — RESOLVED four-zoom (W5+W5b, `merge_magnitudes_FOURZOOM`).** The "Kth-hit
  uncapturable under Rosetta" wall is BROKEN: LLDB ignore-count (`-i N`) + conditional (`-c`) breakpoints are
  core-handled (no Python), reach mid-render in ~11–50s, no stampede. Captured all four tiers: score
  `0x36cde0`=√(a·b) non-degenerate [0,1]; merge Σscore `0x36a938`=1/Σ soft-average normalizer; CCM
  `0xbfa20`=fixed I1I2I3, exclude-both→clean exit all four (per-camera-CCM CLOSED for this site). Remaining
  (non-load-bearing): full per-pixel distribution + total call-count censuses. read-watchpoints dead +
  differential defeated by nondeterminism remain the only verified limits.
- **Unit-2 RUNTIME** untested (calibration cross-unit done; runtime findings Unit-1-only). ⚠ The documented
  Unit-2 "twins" are focals (28,70,150,150) NOT (28,35,70,150) — no clean Unit-2 35mm in the corpus; CLAUDE.md
  corpus note is wrong (flag).
- **Long-tail staging** (~28 docs remain, down from ~50): the verified static sub-mechanisms + magnitudes +
  LRI sub-facts graduated 2026-06-04. Still owed (per ledger): lane-A3 combine-store, lane-A5 kernel/bss
  dupes, lane-A6/A7 score-consumption runtime, several lane-B2 runtime-consumption (AWB/CCM differential),
  lane-D/E runtime tallies, BLIND_SPOTS. Many are subsumed by graduated parents; the genuinely-owed remainder
  is mostly RUNTIME (differential-render / Unit-2) not static.
- **Decode gaps:** unsharp combine VA; Laplacian-pyramid clarity kernel; NLM search radius (runtime param);
  lens-shading {1,15} sub-grid on Unit-2; the CCM→payload+0x14 writer on the taken `eax==0` path (per-camera
  CCM *existence* now RESOLVED — it's `0xa9f20`/Block-6 f2.2); AWB 35/70/150 perturbation.

> Count: REMEDIATION_LEDGER 59/80 graduated (78/80 resolved; 2 staging — AWB 35/70/150 owed, 1 corpus-capped). This synthesis covers the graduated subset; it is NOT a claim the whole pipeline is
> validated — the residuals above are first-class open items.
> **2026-06-04 corrections (see `cgroup_runtime_FOURZOOM`):** stage 10 pyramid-merge runs **L0+L1+L2-4 all
> firing** (the prior "only L0/L1, L2-4=0" was a python-hit-drop artifact; counts are tier-VARYING);
> stage 9 calib gate2/gate3 **DO fire** (28/35/70); merge-projection radial ≈identity (undistort stays a
> separate pre-merge stage); post-merge color matrix = fixed I1I2I3 const bit-verified four-zoom.
