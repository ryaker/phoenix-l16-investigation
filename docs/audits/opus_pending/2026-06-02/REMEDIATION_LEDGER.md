<!-- orchestrator remediation tracker, 2026-06-03. The master gate for the four-zoom upgrade of the 2-day quarantine corpus. -->
# REMEDIATION LEDGER — four-zoom upgrade of the quarantine corpus

**Directive (Rich, 2026-06-03):** run the four-zoom playbook (see `../opus_findings_for_codex/README.md`)
disciplined through EVERY finding doc from the last 2 days. None graduates to Tier 1 (findings_for_codex)
until its per-tier (28/35/70/150) data is captured + verified. **Current truth: 51 / 80 graduated** (+14 subsumed, +3 subsumed-corrected, +1 superseded, +1 retracted = 70/80 resolved; 10 STAGING). Jump 28→50 = 2026-06-04: tool wall BROKEN (W5+W5b → 4-tier merge/score/CCM magnitudes via `merge_magnitudes_FOURZOOM`, +weight_vec4 formula §1b); 13 static sub-mechanism docs byte-verified (`static_submechanisms_verified_FOURZOOM`); LRI sub-facts (incl 8-seed two-unit intrinsics) re-parsed (`lri_calibration_parser_FOURZOOM` addendum); 15 docs subsumption-confirmed into graduated parents (residuals → `SUBSUMPTION_RESIDUALS.md`). **11 STAGING remain:** 6 in the runtime C-group render batch (12/25/67/70/73/76), 3 differential-render-owed (34/48/49 AWB/CCM consumption), reducer_verdict two-prong (13, open), 77 corpus-capped partial. Earlier: W1:2 + W1b:4 render + W3:14 + W3b:2 LRI-calibration.

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
- **~~TOOL WALL (Rosetta)~~ — BROKEN (W5, 2026-06-04):** the "Kth-hit uncapturable under Rosetta" claim was premature (only per-hit Python-callback / `--auto-continue` had been tried — those stampede). **LLDB ignore-count (`-i N`) + conditional (`-c`) breakpoints are core-handled (no Python callback), reach mid-render hits in ~11–50s with no stampede.** Real magnitudes captured 28mm+70mm (score `0x36cde0`=√(a·b), merge Σscore `0x36a938`=1/Σ, CCM `0xbfa20`=fixed I1I2I3) — see `four_zoom_data_W5_magnitudes.md`. **35mm+150mm capture in flight (W5b)**; magnitude docs graduate as a 4-tier set on W5b completion. read-watchpoints dead + differential-defeated-by-nondeterminism remain the only verified limits.
- **W2:** four-zoom DATA sweep #2 — denoise/sharpen/CNR/bilateral + stereo cost (the new stages).
- **W3 (DONE):** 4-LRI re-parse — 14 calibration/distortion/color/AWB/header docs GRADUATED via consolidated finding; Claim-1 block-count correction (11 wide / 12 tele, role=payload-size not index); AWB=54B f19.15; depth-no-LRI confirmed 4-LRI. Block-4/5 internal grids + Unit-2 still owed.
- **Unit-2 universality (DONE for calibration):** STRUCTURE cross-unit-confirmed (7 calibration claims hold on Unit-2 body 223961c6); VALUES per-body. New invariants: CCM row-sums + Block-5 vignetting byte-identical cross-unit. CORRECTION: Unit-2 'twins' are focals (28,70,150,150) not (28,35,70,150) — CLAUDE.md corpus note wrong (flag for Codex). Runtime findings' Unit-2 still owed.
- **W4:** residual/single-claim docs + synthesis docs re-derived from graduated children.

## Ledger (all start STAGING / four-zoom OWED)

| # | doc | tier | four-zoom | wave |
|---|-----|------|-----------|------|
| 1 | BLIND_SPOTS_discovered_stages.md | SUBSUMED | →denoise_sharpen_*/depth parents (confirm-subsumed PASS). Residual: BilateralUpsample LEAD 0x29ed90 → SUBSUMPTION_RESIDUALS | sub |
| 2 | → GRADUATED: opus_findings_for_codex/denoise_sharpen_kernel_math_FOURZOOM.md | **GRADUATED** | W5+NLM tent, sharpen FIR decoded; firing 4-zoom | W2 |
| 3 | → GRADUATED: opus_findings_for_codex/denoise_sharpen_stages_FOURZOOM.md | **GRADUATED** | four-zoom OBSERVED (first-hit) | W1b |
| 4 | → GRADUATED: opus_findings_for_codex/depth_stereo_no_lri_origin_FOURZOOM.md | **GRADUATED** | four-zoom firing/structure | W1d |
| 5 | laneA_prefusion_reducer_static/accumulate_search_216f60.md | SUBSUMED | →geometry_builder_216f60_FOURZOOM (NOT-accumulator covered). Residual: 0x1f0a00 map-walk+ctor → SUBSUMPTION_RESIDUALS | sub |
| 6 | → GRADUATED: opus_findings_for_codex/contributor_gate_FOURZOOM.md | **GRADUATED** | four-zoom firing/structure | W1d |
| 7 | laneA_prefusion_reducer_static/geom_record_consumer_static.md | SUBSUMED | →geometry_builder + accept_consumer_calibstage. Residual: caller-census + State dispatcher 0x22f3fd → SUBSUMPTION_RESIDUALS | sub |
| 8 | → GRADUATED: opus_findings_for_codex/geometry_builder_216f60_FOURZOOM.md | **GRADUATED** | four-zoom firing/structure | W1d |
| 9 | → GRADUATED: opus_findings_for_codex/lane3_blend_FOURZOOM.md | **GRADUATED** | four-zoom structure (magnitude tool-limited) | W1c |
| 10 | laneA_prefusion_reducer_static/matrix_36acf0_bss_storage.md | SUBSUMED | →colormatrix_runtime_const_RESOLVED (I1I2I3 const; self-fwd-ptr). Clean, no residual | sub |
| 11 | laneA_prefusion_reducer_static/matrix_36acf0_decode.md | SUBSUMED | →merge_magnitudes §3 + colormatrix const + lane3_blend (lane3=1.0). Clean | sub |
| 12 | laneA_prefusion_reducer_static/merge_projection_radial_identity.md | STAGING | OWED | - |
| 13 | → GRADUATED(terminal_merge_3661b0_FOURZOOM verdict) | **GRADUATED** | two-prong byte-verified: N-accept loop + N→1 store 0x36aa50→57; src1/src2=geometry (H1 refuted); normalize/weight/score/lane3 all graduated. OPEN: sentinel-gate runtime, two-unit | Bstatic |
| 14 | → GRADUATED(merge_magnitudes_FOURZOOM) | **GRADUATED** | score `0x36cde0`=√(a·b) non-degenerate 4-tier: 28=.78062, 35=.34404/.29467, 70=.62859/.78014, 150=.98853 (orch bit-checked) | W5/W5b |
| 15 | → GRADUATED(merge_magnitudes_FOURZOOM) | **GRADUATED** | Σscore `0x36a938`=1/Σ 4-tier: 28 .2546→3.926, 35 .9436→1.060, 70 .3907→2.560, 150 5.20→.1923 | W5/W5b |
| 16 | laneA_prefusion_reducer_static/score_q1q2_lineage.md | **RETRACTED**-on-subsumption | central 'both-wavelet' claim REFUTED by static_submechanisms (q1=SSIM/q2=wavelet byte-verified); banner added; surviving K-raw bit preserved → SUBSUMPTION_RESIDUALS | flag |
| 17 | → GRADUATED(static_submechanisms_verified_FOURZOOM) | **GRADUATED** | src2 box→margin zero-fill in 0x374ac0, dead in 0x3661b0; byte-verified | Bstatic |
| 18 | → GRADUATED(static_submechanisms_verified_FOURZOOM) | **GRADUATED** | 0x374ac0 = 4×__bzero margin clear via std::function sink; byte-verified | Bstatic |
| 19 | → GRADUATED: opus_findings_for_codex/terminal_merge_3661b0_FOURZOOM.md | **GRADUATED** | four-zoom structure (magnitude tool-limited) | W1c |
| 20 | laneA3_combine_store_site/CORRECTION.md | SUBSUMED | →lane3_blend + terminal_merge (Hann/accumulate). Residual: 0x80000000 coverage-sentinel 0x36930f → SUBSUMPTION_RESIDUALS | sub |
| 21 | laneA3_combine_store_site/LEDGER_RECONCILIATION.md | SUBSUMED | →terminal_merge_3661b0_FOURZOOM (no standalone claim by construction). Clean | sub |
| 22 | laneA3_combine_store_site/step0_inner_body.md | SUBSUMED | self-retracted by step0_reconciliation (-0x4240=compared patch not accumulator). Clean | sub |
| 23 | laneA3_combine_store_site/step0_reconciliation.md | SUBSUMED | →terminal_merge + lane3_blend (N→1 reduction). Residual: (flow_x,flow_y,score) tuple store → committed iramp lane / SUBSUMPTION_RESIDUALS | sub |
| 24 | → GRADUATED(static_submechanisms_verified_FOURZOOM) | **GRADUATED** | resample APPLY Q16.16/64-phase/4-tap MAC; 0x5abed8=65536.0; byte-verified | Bstatic |
| 25 | laneA5_output_finalization/colormatrix_runtime_const_RESOLVED.md | STAGING (RESOLVER) | 0x671980 = fixed I1I2I3 const, static-init (write-wp 0 hits 28mm + recognizable 1/√3,1/√2,1/√6 + single __const writer 0x374505). Static-init ⇒ tier-invariant; 35/70/150+U2 = low-risk confirm | W1/W5 |
| 26 | → GRADUATED(static_submechanisms_verified_FOURZOOM) | **GRADUATED** | detail-transfer out=(B+C)+clamp((A−B)·2·C.l3,±0.1); consts byte-verified | Bstatic |
| 27 | laneA5_output_finalization/kernel_identity.md | SUBSUMED | →resample_kernels_FOURZOOM (B-spline 0x2b2be0 / Catmull-Rom 0x36f800 byte-identical). Clean | sub |
| 28 | laneA5_output_finalization/matrix_36acf0_bss_storage.md | SUBSUMED | DUPLICATE of row10 →colormatrix_runtime_const_RESOLVED. Clean | sub |
| 29 | laneA5_output_finalization/post_blend_color_matrix.md | **SUPERSEDED** | "runtime/per-LRI matrix" REFUTED by row 25 + W5 §3 (it's fixed I1I2I3 const). Banner added; reference-only, NOT finding-grade | 2026-06-04 |
| 30 | → GRADUATED(static_submechanisms_verified_FOURZOOM) | **GRADUATED** | q1 SSIM-cs closed form 0x36cea6; consts byte-verified | Bstatic |
| 31 | → GRADUATED(static_submechanisms_verified_FOURZOOM) | **GRADUATED** | q2 wavelet 0x371730 (3.1722686); score=√(q1·q2) 0x36e511/15 | Bstatic |
| 32 | → GRADUATED(static_submechanisms_verified_FOURZOOM) | **GRADUATED** | dyadic 1:2:4:8 (0x5fdb10), all 4 slots kept, K raw not (KL)² | Bstatic |
| 33 | → GRADUATED(merge_magnitudes_FOURZOOM §1b) | **GRADUATED** | weight_vec4=(score+2·max(score−0.5,0),s,s,s) byte-re-extracted (−0.5 const 0x5a8120 confirmed); denom=Σ raw score; 1/Σ at 0x36a938 | Bstatic |
| 34 | laneB2_lri_calibration_origins/awb_consumption_runtime.md | STAGING | OWED | - |
| 35 | laneB2_lri_calibration_origins/awb_wb_gains_block8.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 36 | → GRADUATED(lri_calibration_parser_FOURZOOM addendum) | **GRADUATED** | Block-1=per-capture AE (f10/18 gain, f11/19 exp_µs); 4-LRI values | Blri |
| 37 | laneB2_lri_calibration_origins/block4_lens_shading_grid.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED: dims 16×17×13×4×4 confirmed; {1,15} identity (not {3,6,9,12}) | W3b |
| 38 | laneB2_lri_calibration_origins/block5_vignetting.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED: 28-knot×4ch poly + falloff, global; confirmed | W3b |
| 39 | laneB2_lri_calibration_origins/block6_519b_records.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 40 | laneB2_lri_calibration_origins/block6_color_candidate.md | SUBSUMED | structure →lri_calibration_parser Claim4 (graduated CANDIDATE→OBSERVED). ⚠ dead LEAD Block6→A5-matrix (A5=I1I2I3 const) → SUBSUMPTION_RESIDUALS | sub |
| 41 | laneB2_lri_calibration_origins/block6_color_shading.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 42 | laneB2_lri_calibration_origins/block6_f28_spectral_curves.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 43 | laneB2_lri_calibration_origins/block6_grouping.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 44 | → GRADUATED(lri_calibration_parser_FOURZOOM addendum) | **GRADUATED** | Block-6 triad (2, 0, 6), f3.2 818/1500; 4-LRI re-parse | Blri |
| 45 | laneB2_lri_calibration_origins/camera_focal_map_excluded_pair.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 46 | → GRADUATED(merge_magnitudes_FOURZOOM) | **GRADUATED** | `0xbfa20`=fixed I1I2I3; exclude-both→clean exit ALL 4 tiers ⇒ per-camera-CCM CLOSED for this site | W5/W5b |
| 47 | → GRADUATED(static_submechanisms_verified_FOURZOOM) | **GRADUATED** | CCM apply 0xbfa20(4×4)/0x300980(3×3); D50 row-sums 0.9642/0.8252=0 hits | Bstatic |
| 48 | laneB2_lri_calibration_origins/ccm_consumption_runtime_INCONCLUSIVE.md | STAGING | OWED | - |
| 49 | laneB2_lri_calibration_origins/ccm_lri_residency_link.md | STAGING | OWED | - |
| 50 | → GRADUATED(lri_calibration_parser_FOURZOOM addendum) | **GRADUATED** | cross-unit cam0 K+dist differ per-body (U1 3375.9 vs U2 3372.5); schema identical | Blri |
| 51 | laneB2_lri_calibration_origins/crosscorpus_distortion.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 52 | laneB2_lri_calibration_origins/crosscorpus_focal_map_excluded_pair.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 53 | laneB2_lri_calibration_origins/crosscorpus_spectral_f28.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 54 | → GRADUATED(static_submechanisms_verified_FOURZOOM) | **GRADUATED** | 0x261940 undistort = pure 4096-LUT radial (1 sqrt/1 load/2 mul), no Horner | Bstatic |
| 55 | laneB2_lri_calibration_origins/distortion_complexity_8_8_refuted.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 56 | laneB2_lri_calibration_origins/distortion_lut_full_decode.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 57 | laneB2_lri_calibration_origins/distortion_undistort_spec.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 58 | → GRADUATED(lri_calibration_parser_FOURZOOM addendum) | **GRADUATED** | 8-seed (4-zoom×2-unit) intrinsics: per-body const, U1 fx 3376/8283/18795 vs U2 3373/8281/18684; block-idx varies (heuristic needed) | Blri |
| 59 | laneB2_lri_calibration_origins/lightheader_block0.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 60 | laneB2_lri_calibration_origins/lri_block_inventory.md | **GRADUATED**(→lri_calibration_parser_FOURZOOM) | four-LRI OBSERVED (Unit-1) | W3 |
| 61 | → GRADUATED: opus_findings_for_codex/undistort_ordering_lut_FOURZOOM.md | **GRADUATED** | four-zoom OBSERVED (first-hit; camera-group LUT split) | W1 |
| 62 | → GRADUATED(lri_calibration_parser_FOURZOOM addendum) | **GRADUATED** | cam0 Block-3 field map fully resolves (101/30-pt LUTs, date 2017-11-04); 4-LRI | Blri |
| 63 | → GRADUATED(static_submechanisms_verified_FOURZOOM) | **GRADUATED**(static) | C6 clear-guard keys CONTAINER +0x44 not item key; 58 f2720 sites; +0x44 runtime value still owed | Bstatic |
| 64 | laneD_final_acceptance_static/accept_consumer_calibstage.md | SUBSUMED | →accept_reject_gate_FOURZOOM (ACCEPT→0xf33d0). Residual: 0xf33d0 bank layout + 0x22f3ff dispatcher → SUBSUMPTION_RESIDUALS | sub |
| 65 | → GRADUATED: opus_findings_for_codex/accept_reject_gate_FOURZOOM.md | **GRADUATED** | four-zoom OBSERVED (first-hit) | W1b |
| 66 | laneD_final_acceptance_static/acceptance_gate_location.md | SUBSUMED | →accept_reject_gate_FOURZOOM (parent FOUND gate 0x217ab9 staging couldn't). Residual: call-site map + r14=-0x220 fix → SUBSUMPTION_RESIDUALS | sub |
| 67 | laneD_final_acceptance_static/calib_to_merge_link_LEAD.md | STAGING | OWED | - |
| 68 | → GRADUATED(static_submechanisms_verified_FOURZOOM) | **GRADUATED** | 0xe6ba0 = keyed SELECT-ONE, 0 FP-arith ops (verified) | Bstatic |
| 69 | → GRADUATED(static_submechanisms_verified_FOURZOOM) | **GRADUATED** | 0x218b30 stat reducer (mean+exceed-frac); <8 pairs→skip (0x2170d1) | Bstatic |
| 70 | laneD_final_acceptance_static/gate2_gate3_reject_semantics.md | STAGING | W1b: gate1 fires 4-zoom; gate2/3 still untriggered | W1b |
| 71 | → GRADUATED: opus_findings_for_codex/final_compositing_consumer_FOURZOOM.md | **GRADUATED** | four-zoom OBSERVED (first-hit) | W1b |
| 72 | → GRADUATED(static_submechanisms_verified_FOURZOOM) | **GRADUATED** | level dispatcher 0x3ec9dc: L0=0x3ec770/L1=0x3ebb80/L2-4=0x3d0650; vtable+0x30 | Bstatic |
| 73 | laneE_fourzoom_topology/level_fire_runtime_28mm.md | STAGING | OWED | - |
| 74 | laneE_fourzoom_topology/output_producer_static.md | A→SUBSUMED+CORRECTED | producer path OBSERVED; "RB-tree" REFUTED (libc++ symbol scan: __tree/map/set/list all 0); final-compositing question CLOSED by graduated final_compositing_consumer_FOURZOOM. Correction banner added | 2026-06-04 |
| 75 | → GRADUATED: opus_findings_for_codex/resample_kernels_FOURZOOM.md | **GRADUATED** | four-zoom OBSERVED (first-hit) | W1b |
| 76 | laneE_fourzoom_topology/scheduler_recombine_runtime.md | STAGING (CORRECTED) | dispatch tally OBSERVED 28mm; "RB-tree/list insert" REFUTED (intrusive 0x80-node list); correction banner added. Tally 35/70/150mm still owed (C, runtime) | 2026-06-04 |
| 77 | laneP_parser_gap_182/residual_alternate_container.md | STAGING (PARTIAL) | assigned LELR count verified (wide=11/tele=12; prose off-by-one fixed); unassigned-file 0–4 claim untestable in corpus | Blri |
| 78 | MERGE_MECHANISM_SYNTHESIS.md | A→SUBSUMED+CORRECTED | synthesis of graduated children; stale "runtime-populated color matrix" corrected → fixed I1I2I3 const (rows 25/W5) | 2026-06-04 |
| 79 | MERGE_PIPELINE.md | A→SUBSUMED+CORRECTED | navigational table; stage-10 "runtime/per-LRI color-correction" corrected → fixed I1I2I3 const | 2026-06-04 |
| 80 | → GRADUATED: opus_findings_for_codex/stereo_cost_math_FOURZOOM.md | **GRADUATED** | four-zoom OBSERVED (first-hit; caller 0x276860, N=4 all tiers, layout corrected) | W1 |