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
4. **IRAMP terminal MERGE** (`terminal_merge_3661b0_FOURZOOM`) — `0x3661b0`, per 512×512 tile, **N=5
   contributors** (ctx+0x18 vector, N=(end-begin)/16), tier-invariant; weighted soft-average (1/Σscore); score
   kernel `0x36cde0` = `sqrt(cs-SSIM × 4-scale wavelet)`; lane-3 detail-transfer `0x36aa30` (recip·0.2);
   contributor sentinel `0x36930f`. **Reduction MAGNITUDE tool-walled.** B-spline resample is merge-interior.
5. **RESAMPLE** (`resample_kernels_FOURZOOM`) — B-spline `0x2b2be0` (merge-interior) + Catmull-Rom `0x36f800`
   (separate stage `0x3d0650`); both 4-tap 64-phase LUT builders.
6. **DENOISE** (`denoise_sharpen_stages_FOURZOOM`, `denoise_sharpen_kernel_math_FOURZOOM`) — ColorNoiseReduction
   (`0x34b3f0`, covariance/multi-scale, registers before CCM); bilateral active window **W5** (`0x2f78e0`,
   TENT range weight); NLM/PatchNLM<4> (`0x3070e0`, TENT, 4×4 SAD patch). **All denoise weights tent/covariance
   — none exponential.** CNR params 1.0/1.0 four-zoom.
7. **COLOR** — CCM 4×4 apply `0xbfa20` is a GENERIC apply; first-hit = fixed **I1I2I3 decorrelation** (NOT
   per-camera CCM — that claim reopened, staging); AWB reciprocals folded in (28mm-only runtime); fixed I1I2I3
   basis confirmed 3× (`0x5f2380`).
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
- **TOOL WALL (Rosetta x86_64; no native-arm64):** merge reduction MAGNITUDE, score/Σscore VALUES, per-camera
  CCM later-hit — uncapturable at first-hit; Kth-hit re-triggers the stampede; read-watchpoints dead;
  differential defeated by libcp output nondeterminism. Need native-arm64 single-step / instrumented build /
  Codex tooling. (Structure graduated; values open.)
- **Unit-2 RUNTIME** untested (calibration cross-unit done; runtime findings Unit-1-only). ⚠ The documented
  Unit-2 "twins" are focals (28,70,150,150) NOT (28,35,70,150) — no clean Unit-2 35mm in the corpus; CLAUDE.md
  corpus note is wrong (flag).
- **Long-tail staging** (~50 docs): lane-A score/output sub-mechanisms, CCM-static, BLIND_SPOTS, synthesis —
  many covered by graduated parents; per-doc four-zoom still owed per the ledger.
- **Decode gaps:** unsharp combine VA; Laplacian-pyramid clarity kernel; NLM search radius (runtime param);
  per-camera CCM existence; lens-shading {1,15} sub-grid on Unit-2.

> Count: REMEDIATION_LEDGER 28/80 graduated. This synthesis covers the graduated subset; it is NOT a claim
> the whole pipeline is validated — the residuals above are first-class open items.
