# findings_for_codex — Tier 1 (graduated, four-zoom-upgraded)

This directory is **EMPTY by default** and fills slowly. A packet appears here ONLY after it has passed the
four-zoom upgrade playbook and is therefore eligible to be shared as a finding for Codex's validation.

## Why this tier exists (Rich, 2026-06-03)
The work under `docs/audits/opus_pending/2026-06-02/` (Tier 0 / staging / "quarantine²") is raw RE — mostly
STATIC disasm or SINGLE-ZOOM runtime. That is **not finding-grade**: handing it to Codex as "findings" would
make him *discover* my corner-cutting rather than *confirm* validated work. So nothing in staging is a finding
until I upgrade it myself.

## Graduation gate (the four-zoom playbook) — ALL steps required
A staging packet graduates into this directory only after:
1. **Load-bearing claims enumerated** (each VA / constant / mechanism the packet asserts).
2. **Four-zoom runtime data captured** — 28mm L16_02130 / 35mm L16_03041 / 70mm L16_03434 / 150mm L16_02285
   (all Unit-1): at each claim's breakpoint/site, read the actual per-tier operands (values, camera sets,
   contributor counts, params) — NOT just hit-counts. (LRI-only claims: re-parse ALL FOUR LRIs, not a subset.)
3. **Per-tier verified** — the claim holds (or is scope-bound / corrected) at every tier it's asserted for.
4. **Packet rewritten** to four-zoom OBSERVED with explicit per-tier data + scope; tool limits (Rosetta
   read-watchpoints dead) stated per-datum, never used to downgrade the whole finding.
5. **`git mv`** staging → here (or **consolidate** many staging docs into one parent finding — the calibration,
   static-submechanism, and magnitude parents each absorb 3–14 staging docs), and the REMEDIATION_LEDGER row
   flipped to GRADUATED. For pure-static / LRI-resident claims, "four-zoom" = **deterministic re-extraction**
   (byte-exact re-disasm of the VAs, or re-parse of all four LRIs) — the code/rodata is identical regardless of
   which LRI renders, so re-extraction IS the rigor (it does not require four separate renders).

Still `NEEDS_CODEX_VALIDATION` even here — Codex validates/upgrades to ledger truth. This tier only means
"done to the rigor that makes it worth his time."

## Graduated index (entry points for Codex; start with PIPELINE_SYNTHESIS)
- **PIPELINE_SYNTHESIS.md** — end-to-end 10-stage graduated picture (READ FIRST).
- **Merge / fusion core:** `terminal_merge_3661b0_FOURZOOM` (N=5 soft-average), `lane3_blend_FOURZOOM`
  (detail-transfer), `merge_magnitudes_FOURZOOM` (4-tier score √(a·b) / Σscore 1/Σ / CCM=fixed I1I2I3 —
  closes the former Rosetta tool wall), `geometry_builder_216f60_FOURZOOM`, `contributor_gate_FOURZOOM`.
- **Depth / stereo:** `depth_stereo_no_lri_origin_FOURZOOM`, `stereo_cost_math_FOURZOOM`.
- **Resample / denoise / sharpen:** `resample_kernels_FOURZOOM`, `denoise_sharpen_stages_FOURZOOM`,
  `denoise_sharpen_kernel_math_FOURZOOM`.
- **Color (two transforms):** `color_consumption_FOURZOOM` (per-camera CCM `0xa9f20` = LRI Block-6 f2.2, then
  fixed I1I2I3 `0xbfa20`); runtime corrections in `cgroup_runtime_FOURZOOM` (L2-4 fires, gate2/3 fire,
  merge-projection ≈identity, I1I2I3 const bit-verified, calib≠merge object).
- **Undistort / calibration / accept / output:** `undistort_ordering_lut_FOURZOOM`,
  `lri_calibration_parser_FOURZOOM` (+ 2026-06-04 sub-facts addendum: Block-1 AE, cross-unit cam0, field map),
  `accept_reject_gate_FOURZOOM`, `final_compositing_consumer_FOURZOOM` (intrusive list, RB-tree refuted).
- **Two-body universality:** `unit2_runtime_universality_FOURZOOM` (merge/score/CCM/I1I2I3 hold on body-2
  223961c6 — structure universal, values per-body; closes the "every claim was on one body" gap).
- **Non-graduated-row audit:** `RESIDUAL_VALIDATION_LEDGER` (the 19 subsumed/superseded/retracted rows, each
  validated or invalidated to rigor) + `parked_residuals_decoded_FOURZOOM` (6 shed sub-mechanisms decoded
  byte-exact: merge SELECTION gate `0x36930f`, State dispatcher `0x22f3fd`, CalibStage banks `0xf33d0`,
  `0x1f0a00` intrusive walk, `0x29ed90` BilateralUpsample, `{flow,score}` tuple store).
- **Static sub-mechanisms (byte-verified):** `static_submechanisms_verified_FOURZOOM` (13 lane-A/D/E/B2/C6
  VAs: src-boxing, resample-apply, detail-transfer, score closed-form, CCM apply-sites, undistort kernel,
  accept filter, level dispatcher, C6 key-15).
