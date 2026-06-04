<!-- orchestrator remediation tracker, 2026-06-03. The master gate for the four-zoom upgrade of the 2-day quarantine corpus. -->
# REMEDIATION LEDGER — four-zoom upgrade of the quarantine corpus

**Directive (Rich, 2026-06-03):** run the four-zoom playbook (see `../opus_findings_for_codex/README.md`)
disciplined through EVERY finding doc from the last 2 days. None graduates to Tier 1 (findings_for_codex)
until its per-tier (28/35/70/150) data is captured + verified. **Current truth: 16 / 80 graduated** (W1: 2 render-findings; W3: 14 LRI-calibration docs via consolidated `../opus_findings_for_codex/lri_calibration_parser_FOURZOOM.md`).

Cadence is render-bound (4 sequential renders per data sweep, minutes each, one external disk under
Rosetta) — this is a multi-day campaign, not a pass. Renders are BATCHED: one 4-render sweep with many
breakpoints captures per-tier data for many runtime docs at once, then those docs graduate together.

## Execution waves (WSJF; render-batched)
- **W0 (DONE — `four_zoom_firing_census_W0.md`):** four-zoom firing census. 19/21 stages fire all-tier; 2
  dormant (bilateral W3 `0x2f6ad0`, stereo driver `0x2730c0`). Firing tier-invariant (5+5+6 does NOT gate
  stereo-cost firing). Forced 3 corrections (stereo driver dormant→runPass path; bilateral W3 dormant; sharpen
  ctor `0x360a00`). Floor only — scopes W1; NOT graduation. Method: "drain" harness (per-hit callbacks stall
  under Rosetta) ⇒ W1 must stop SELECTIVELY (1-2 stages/render) → even more render-bound.
- **W1:** four-zoom DATA sweep #1 — merge/score/gates/CCM/undistort/resample/compositing (lane A/D/E + B2 color).
- **W2:** four-zoom DATA sweep #2 — denoise/sharpen/CNR/bilateral + stereo cost (the new stages).
- **W3 (DONE):** 4-LRI re-parse — 14 calibration/distortion/color/AWB/header docs GRADUATED via consolidated finding; Claim-1 block-count correction (11 wide / 12 tele, role=payload-size not index); AWB=54B f19.15; depth-no-LRI confirmed 4-LRI. Block-4/5 internal grids + Unit-2 still owed.
- **W4:** residual/single-claim docs + synthesis docs re-derived from graduated children.

## Ledger (all start STAGING / four-zoom OWED)

| # | doc | tier | four-zoom | wave |
|---|-----|------|-----------|------|
| 1 | BLIND_SPOTS_discovered_stages.md | STAGING | OWED | - |
| 2 | denoise_sharpen_kernel_math.md | STAGING | OWED | - |
| 3 | denoise_sharpen_tone_stages_mapped.md | STAGING | OWED | - |
| 4 | depth_stereo_no_lri_origin.md | STAGING (LRI-side graduated) | W3: Claim6 four-LRI✓ (consolidated); runtime ctor part static | W3 |
| 5 | laneA_prefusion_reducer_static/accumulate_search_216f60.md | STAGING | OWED | - |
| 6 | laneA_prefusion_reducer_static/contributor_gate.md | STAGING | OWED | - |
| 7 | laneA_prefusion_reducer_static/geom_record_consumer_static.md | STAGING | OWED | - |
| 8 | laneA_prefusion_reducer_static/geometry_builder_216f60.md | STAGING | OWED | - |
| 9 | laneA_prefusion_reducer_static/lane3_blend.md | STAGING | OWED | - |
| 10 | laneA_prefusion_reducer_static/matrix_36acf0_bss_storage.md | STAGING | OWED | - |
| 11 | laneA_prefusion_reducer_static/matrix_36acf0_decode.md | STAGING | OWED | - |
| 12 | laneA_prefusion_reducer_static/merge_projection_radial_identity.md | STAGING | OWED | - |
| 13 | laneA_prefusion_reducer_static/reducer_verdict.md | STAGING | OWED | - |
| 14 | laneA_prefusion_reducer_static/score_kernel_36cde0_two_factors.md | STAGING | W1: firing✓ magnitude-owed (degenerate first-hit) | W1 |
| 15 | laneA_prefusion_reducer_static/score_production.md | STAGING | OWED | - |
| 16 | laneA_prefusion_reducer_static/score_q1q2_lineage.md | STAGING | OWED | - |
| 17 | laneA_prefusion_reducer_static/src2_box_role.md | STAGING | OWED | - |
| 18 | laneA_prefusion_reducer_static/src2_callback_374ac0.md | STAGING | OWED | - |
| 19 | laneA_prefusion_reducer_static/terminal_merge_3661b0.md | STAGING | OWED | - |
| 20 | laneA3_combine_store_site/CORRECTION.md | STAGING | OWED | - |
| 21 | laneA3_combine_store_site/LEDGER_RECONCILIATION.md | STAGING | OWED | - |
| 22 | laneA3_combine_store_site/step0_inner_body.md | STAGING | OWED | - |
| 23 | laneA3_combine_store_site/step0_reconciliation.md | STAGING | OWED | - |
| 24 | laneA5_output_finalization/apply_structure.md | STAGING | OWED | - |
| 25 | laneA5_output_finalization/colormatrix_runtime_const_RESOLVED.md | STAGING | OWED | - |
| 26 | laneA5_output_finalization/guided_detail_transfer.md | STAGING | OWED | - |
| 27 | laneA5_output_finalization/kernel_identity.md | STAGING | OWED | - |
| 28 | laneA5_output_finalization/matrix_36acf0_bss_storage.md | STAGING | OWED | - |
| 29 | laneA5_output_finalization/post_blend_color_matrix.md | STAGING | OWED | - |
| 30 | laneA6_score_metric/closed_form_stage1.md | STAGING | OWED | - |
| 31 | laneA6_score_metric/closed_form_stage2.md | STAGING | OWED | - |
| 32 | laneA6_score_metric/score_completion_kraw_scales.md | STAGING | OWED | - |
| 33 | laneA7_score_consumption/lane_semantics.md | STAGING | OWED | - |
| 34 | laneB2_lri_calibration_origins/awb_consumption_runtime.md | STAGING | OWED | - |
| 35 | laneB2_lri_calibration_origins/awb_wb_gains_block8.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 36 | laneB2_lri_calibration_origins/block1_ancillary.md | STAGING | OWED | - |
| 37 | laneB2_lri_calibration_origins/block4_lens_shading_grid.md | STAGING | OWED | - |
| 38 | laneB2_lri_calibration_origins/block5_vignetting.md | STAGING | OWED | - |
| 39 | laneB2_lri_calibration_origins/block6_519b_records.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 40 | laneB2_lri_calibration_origins/block6_color_candidate.md | STAGING | OWED | - |
| 41 | laneB2_lri_calibration_origins/block6_color_shading.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 42 | laneB2_lri_calibration_origins/block6_f28_spectral_curves.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 43 | laneB2_lri_calibration_origins/block6_grouping.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 44 | laneB2_lri_calibration_origins/calibration_unknowns_block6.md | STAGING | OWED | - |
| 45 | laneB2_lri_calibration_origins/camera_focal_map_excluded_pair.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 46 | laneB2_lri_calibration_origins/ccm_apply_site_located.md | STAGING (CORRECTED) | W1: 0xbfa20 first-hit=I1I2I3 not per-cam CCM; per-cam claim reopened | W1 |
| 47 | laneB2_lri_calibration_origins/ccm_apply_site_static.md | STAGING | OWED | - |
| 48 | laneB2_lri_calibration_origins/ccm_consumption_runtime_INCONCLUSIVE.md | STAGING | OWED | - |
| 49 | laneB2_lri_calibration_origins/ccm_lri_residency_link.md | STAGING | OWED | - |
| 50 | laneB2_lri_calibration_origins/cross_unit_values.md | STAGING | OWED | - |
| 51 | laneB2_lri_calibration_origins/crosscorpus_distortion.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 52 | laneB2_lri_calibration_origins/crosscorpus_focal_map_excluded_pair.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 53 | laneB2_lri_calibration_origins/crosscorpus_spectral_f28.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 54 | laneB2_lri_calibration_origins/distortion_apply_stage.md | STAGING | OWED | - |
| 55 | laneB2_lri_calibration_origins/distortion_complexity_8_8_refuted.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 56 | laneB2_lri_calibration_origins/distortion_lut_full_decode.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 57 | laneB2_lri_calibration_origins/distortion_undistort_spec.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 58 | laneB2_lri_calibration_origins/four_zoom_two_unit.md | STAGING | OWED | - |
| 59 | laneB2_lri_calibration_origins/lightheader_block0.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 60 | laneB2_lri_calibration_origins/lri_block_inventory.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 61 | → GRADUATED: opus_findings_for_codex/undistort_ordering_lut_FOURZOOM.md | **GRADUATED** | four-zoom OBSERVED (first-hit; camera-group LUT split) | W1 |
| 62 | laneB2_lri_calibration_origins/verified_field_map.md | STAGING | OWED | - |
| 63 | laneC6_remaining/c6_grouptype2_survival.md | STAGING | OWED | - |
| 64 | laneD_final_acceptance_static/accept_consumer_calibstage.md | STAGING | OWED | - |
| 65 | laneD_final_acceptance_static/accept_reject_gate_located.md | STAGING | OWED | - |
| 66 | laneD_final_acceptance_static/acceptance_gate_location.md | STAGING | OWED | - |
| 67 | laneD_final_acceptance_static/calib_to_merge_link_LEAD.md | STAGING | OWED | - |
| 68 | laneD_final_acceptance_static/e6ba0_not_accumulator.md | STAGING | OWED | - |
| 69 | laneD_final_acceptance_static/final_acceptance_filter.md | STAGING | OWED | - |
| 70 | laneD_final_acceptance_static/gate2_gate3_reject_semantics.md | STAGING | OWED | - |
| 71 | laneE_fourzoom_topology/final_compositing_consumer.md | STAGING | OWED | - |
| 72 | laneE_fourzoom_topology/level_dispatcher_topology.md | STAGING | OWED | - |
| 73 | laneE_fourzoom_topology/level_fire_runtime_28mm.md | STAGING | OWED | - |
| 74 | laneE_fourzoom_topology/output_producer_static.md | STAGING | OWED | - |
| 75 | laneE_fourzoom_topology/resample_kernels_constants.md | STAGING | OWED | - |
| 76 | laneE_fourzoom_topology/scheduler_recombine_runtime.md | STAGING | OWED | - |
| 77 | laneP_parser_gap_182/residual_alternate_container.md | STAGING | OWED | - |
| 78 | MERGE_MECHANISM_SYNTHESIS.md | STAGING | OWED | - |
| 79 | MERGE_PIPELINE.md | STAGING | OWED | - |
| 80 | → GRADUATED: opus_findings_for_codex/stereo_cost_math_FOURZOOM.md | **GRADUATED** | four-zoom OBSERVED (first-hit; caller 0x276860, N=4 all tiers, layout corrected) | W1 |