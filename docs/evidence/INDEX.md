# Evidence Index

- [bundle_static_runtime_prefusion_monofusion_color_wrapper_two_body.md](bundle_static_runtime_prefusion_monofusion_color_wrapper_two_body.md)
  SHA-pinned exact MonoFusion response/opponent-basis construction and inverse,
  public sensor-type/black/white origins, and bit-exact live scalar-to-RGB
  replay on both physical exact-28mm bodies; canonical tele bypasses it.
- [bundle_static_runtime_nlm_patch_overlap_topology.md](bundle_static_runtime_nlm_patch_overlap_topology.md)
  SHA-pinned selected PatchNLM proof for deterministic phase generation,
  four quadrant passes, exact 4x4 patches, reference-center range scaling,
  checkerboard candidate selection, 16-cell overlap-add, positive full-frame
  seeds, and the resulting no-clamp boundary policy, joined to admitted
  four-focal/two-body route liveness.
- [bundle_static_runtime_prefusion_monofusion_reference_public_origin_two_body.md](bundle_static_runtime_prefusion_monofusion_reference_public_origin_two_body.md)
  Exact public A1 RAW10-to-MonoFusion-flow-reference reconstruction over both
  physical exact-28mm bodies, including demosaic/luma, reciprocal exposure
  affine, public vignetting, sqrt LUT, and the default-hot-pixel-route
  exclusion.
- [bundle_static_runtime_index5_range_pool_skip_policy.md](bundle_static_runtime_index5_range_pool_skip_policy.md)
- [bundle_runtime_unit2_70mm_range_generation_localization.md](bundle_runtime_unit2_70mm_range_generation_localization.md)
  Two fresh instrumented Unit-2 `70mm` draws replay all `4,322,500` captured `0x298ff0` low/high words exactly. A same-generation Phoenix level-0-to-3 comparison proves the current band formula matches its own prior indices but the parity divergence already exists at full-band level 0, refuting the range builder as the current causal origin and localizing next work to level-0 operands/cost/SGM.
  Exact G-40 predecessor pooling: selected kernel size 4, clamped asymmetric
  offsets `{-1,0,1,2}^2`, nonzero Skip-mask inclusion, and empty-set
  `(65535,0)` policy.
- [bundle_static_runtime_index5_perlevel_projection_scale_two_body_four_zoom.md](bundle_static_runtime_index5_perlevel_projection_scale_two_body_four_zoom.md)
  Installed plus complete two-body/four-focal proof of levels 0..5 coordinate
  lifting: steps `{32,16,8,4,2,1}`, fixed `2080x1560` source Images,
  invariant full-domain projection records, and exact `(1,1)` record scales.
- [bundle_static_runtime_output_orientation_policy_two_body.md](bundle_static_runtime_output_orientation_policy_two_body.md)
- [bundle_static_independent_tagged_linear_prophoto_float_tiff.md](bundle_static_independent_tagged_linear_prophoto_float_tiff.md)
- [bundle_static_runtime_index5_guidance_yuv_formula_two_body.md](bundle_static_runtime_index5_guidance_yuv_formula_two_body.md)
  Corrective installed/runtime proof that key-0 Guidance is exact
  `[Y,U,V,1]` after `StereoISP::ConvertToYUV`, with public AWB and
  `SENSOR_AR1335` origins plus complete scene/two-body float and byte replay.

This folder is the landing zone for proof artifacts that are allowed to feed the canonical zone.

For now, the strongest seed evidence lives partly at repo root and partly outside the repo in the scratch corpus.

Durable evidence must not depend on live `/tmp` or `/private/tmp` paths. Older
proof docs may preserve those paths as historical provenance, but future
canonical promotion requires embedded verified facts, a repo-local proof doc, or
a rerunnable repo-local probe under `tools/lldb_probes/`. Audit registers belong
under `docs/audits/`; raw rerunnable outputs belong under ignored `runs/`.

## Current Seed Evidence

### Repo-root proof docs

- `../LUMEN_APP_PROOF_ONLY_AUDIT.md`
  Direct bundle-backed proof corrections.
- `../TECHDOC_ALIGNED_TRUTH.md`
  Guardrail document aligned against `l16-tech-part-1-3.md`.
- `../SCRATCH_CORPUS_CONTAMINATION_AUDIT.md`
  Contamination map for the scratch corpus.

### Repo evidence docs

- `bundle_static_runtime_editor_acre_public_origins_28mm.md`
  Installed-schema/request-builder proof plus retained Unit-1 `28mm` runtime
  replay joining selected ACRE EV to the four public capture-normalization
  fields and `tone_mapping.type=light_v1` to enum `4`, curve index `1`, and
  exact LUT `libcp+0x5e41b4`.

- `bundle_static_pile2_payload_digests_vst_wire_options.md`
  Independent repo-local extraction of the full Unit-1 intrinsics,
  distortion, and depth-config payload SHA-256 digests; all 28 exact installed
  type-3 panchromatic VST rows with float32 words; descriptor-pinned leaf wire
  contracts; and explicit `packed=true` closure for all four formerly
  ambiguous repeated-float fields.

- `bundle_proof_src_wrappers.md`
  Installed-bundle proof for the first visible `src1` / `src2` wrapper layer.
- `lldb_pipelinecache_level_vector_four_zoom.md`
  LLDB runtime proof that `PipelineCache+0x8` is a five-entry packed `(int32 width, int32 height)` level-vector header on the canonical bridge HDR quartet, not an image/composite pointer; it also proves the visible `src1` / `src2` wrapper dimensions come from vector entry `1` as `4160x3120` across all four zooms.
- `bundle_proof_initresamp_post_wrapper_records.md`
  Installed-bundle proof bounding the `initResAmp` post-wrapper branch to per-key map/vector/record/wrapper construction at `PipelineCache+0x258` and `PipelineCache+0x270`.
- `bundle_proof_initresamp_per_key_wrapper_read_path.md`
  Installed-bundle proof bounding the `PipelineCache+0x270` per-key wrapper read path to single-payload ROI/tile processing plus square-root normalization.
- `bundle_proof_src1_visible_read_path.md`
  Installed-bundle proof bounding the visible `src1` read path to lookup, single-source level/ROI tile read, and one-image square-root normalization.
- `bundle_proof_src1_payload_provenance.md`
  Installed-bundle proof tracing the visible `src1` lookup payload back through `PipelineCache+0x170`, the caller's `+0x6a8/+0x6b0` shared-ptr-like pair, the `0x3dfcc0` map/tree builder, and the `0x3e27a0` payload constructor.
- `bundle_static_runtime_prefusion_cache_rtti_identity_four_zoom.md`
  SHA-pinned RTTI/control-block proof joined to the admitted four-focal payload
  packets. It exactly names owner `+0x6a8` as `lt::ImageCaches`, visible
  `src1` payload vtable `0x65f140` as `lt::ReferenceImageCache`, direct
  contributor vtable `0x65f490` as `lt::SourceImageCache`, and visible
  wrappers as `PipelineCache::initResAmp::$_1/$_2`. The camera-key join makes
  visible `src1` the A1-wide/B4-tele tier-anchor reference cache; the next
  bundle names `src2`, while complete multi-contributor reduction remains open.
- `bundle_static_runtime_prefusion_src2_processlevel1_identity_four_zoom.md`
  SHA-pinned RTTI/vtable proof joined to the admitted four-focal executor
  packets. It exactly names visible `src2` as
  `PipelineCache::initResAmp::$_2 -> PipelineCache::processLevel1 ->
  ImageWarpClamped<ResamplerFilter=2, vec4x32f>`, with callback
  `0x65f7e8/+0x30 = 0x3ed2e0`, and separates it from direct-contributor
  wrapper `initResAmp::$_3` at `0x65f768/+0x30 = 0x3eced0`. Public identity
  of the source descriptor and complete distributed reduction remain open.
- `bundle_static_runtime_prefusion_src2_source_camera_identity_two_body.md`
  SHA-pinned source-lookup proof plus early-terminate Unit-1/Unit-2 28mm/70mm
  packets. `FusionCacheBayer::0x406a10` derives A1/key `0` at wide and B4/key
  `8` at tele, and `0x1be970` returns the same-key active
  `lt::CapturedImage` with exact shared-control RTTI `0x665eb8`. The
  process-level-1 descriptor targets that tier anchor, not a direct protobuf
  image field; the next bundle closes its tested tier-dependent ancestry.
- `bundle_static_runtime_prefusion_monofusion_source_descriptor_two_body.md`
  Pinned installed-class proof plus complete Unit-1 four-focal and Unit-2
  28mm/70mm bridge-HDR packets. Optional `FusionCacheBayer+0x20` is exact
  `lt::MonoFusion`; wide targets A1 and selects only A2 through public
  `sensor_bayer_red_override=(-1,-1)`, then passes the generated descriptor to
  `0x31b110`. Tele constructs no MonoFusion and takes the direct B4
  `0x31acf0` route. Immediate `0x1b3530` post-worker pixel math is decoded;
  later bundles close its derived coefficient origins, internal worker, and
  canonical distributed policy.
- `bundle_static_runtime_prefusion_monofusion_wavelet_formula_two_body.md`
  SHA-pinned mode-0 worker/helper proof plus complete Unit-1 28mm/35mm and
  exact-focal Unit-2 28mm runtime. Public A2 capture fields select exact
  initializer scaling. The live wide worker uses flow-aligned 16x16 step-8
  patches, normalized 5/3 lifting, an exact installed 16x16 coefficient
  table, patch-noise/Wiener formulas, half-sample Hann overlap-add, and an
  exact target/source scalar blend. Canonical tele bypasses MonoFusion.
  Transform edge/permutation pseudocode, mode 1, confidence callback
  semantics, and distributed acceptance remain open.
- `bundle_static_runtime_prefusion_monofusion_installed_vst_table.md`
  Corrective installed-bundle/runtime proof that public analog gain selects
  a 28-row installed type-3 panchromatic table, not the different public
  type-2 LRI rows. Unit-1 28mm captures all constructor rows byte-exact;
  Unit-1 35mm and Unit-2 28mm reproduce the installed selected coefficients.
  This closes and refutes the former public-to-prepared VST residual.
- `bundle_static_runtime_prefusion_monofusion_affine_public_origin.md`
  SHA-pinned static, direct-LRI, and two-body runtime proof closing the exact
  float32 A2 source normalization multiplier as A1 exposure-times-analog over
  A2 exposure-times-analog and installed mono response. Digital gain is not
  used; canonical tele bypasses MonoFusion.
- `lldb_src1_payload_constructor_live_four_zoom.md`
  LLDB runtime proof that the visible `src1` payload constructor path `0x3dfcc0 -> 0x3e2db0 -> 0x3e27a0` is live across the canonical four-zoom bridge HDR quartet, with key `0` at `28mm`/`35mm`, key `8` at `70mm`/`150mm`, the same four-entry level vector, and the expected `0x490` / `0x65f140` / `0x65f388` payload family.
- `bundle_proof_src1_payload_runtime_surfaces.md`
  Installed-bundle proof bounding the first visible payload vtable slots, callable-slot helpers, per-level config fan-out, and single-level ROI/process bodies away from reducer closure.
- `bundle_proof_src1_project_roi_worker.md`
  Installed-bundle proof that the deeper `0x3e2e90` callback worker at `0x3e4c50` is a single-source projection / 4x4 SIMD resampling worker, not the exposed `src1` / `src2` pre-fusion merge/reduction mechanism.
- `bundle_proof_src1_owner_cache_selection.md`
  Installed-bundle proof that the owner cache-selection layer builds `+0x6a8/+0x6b0`, constructs `+0x688/+0x690` through `0x3eaf00 -> 0x3ea7d0`, selects between `owner+0x688` and `owner+0x6b8` at runtime, and dispatches one selected cache through `0x3d0650` read/rescale work rather than exposing the `src1` / `src2` pre-fusion merge/reduction mechanism.
- `bundle_proof_src1_alternate_cache_setup.md`
  Installed-bundle proof that optional `+0x698/+0x6a0` setup and `+0x6b8/+0x6c0` construction are owner-held setup/callback/cache-construction surfaces; its `+0x678/+0x680` coverage is limited to the visible constructor prefix.
- `bundle_proof_src1_678_constructor_runtime_surface.md`
  Installed-bundle proof bounding the visible `+0x678/+0x680` constructor body through normal return and the immediate `0x3f75e0` / `0x3f7a40` / `0x3f7b20` / `0x3f7c00` / `0x3f7ec0` runtime surfaces to setup, level gate, callable-slot, byte-count, and record/buffer materialization work rather than reducer closure.
- `bundle_proof_src1_678_virtuals_and_record_consumer.md`
  Installed-bundle proof bounding the selected `+0x40` and `+0x90` layer virtual targets to setters/accessors, bounding `0x3f8b30` as a consumer/writer of `0x3f7ec0` materialized record/buffer output, and previously locating the `StereoLayer<false>::runPass(int)` action path at `0x276790 -> 0x276860 / 0x277e70`.
- `bundle_proof_stereolayer_runpass_cost_path_four_zoom.md`
  Installed-bundle plus LLDB runtime proof bounding the `StereoLayer<false>::runPass(int)` action path to a mode-8 per-tile projection/sampling cost path on the canonical four-zoom bridge HDR quartet, with scoped zero-hit results for `0x277e70` and `0x2730c0`.
- `bundle_proof_stereolayer_compute_cost_sibling_four_zoom.md`
  Installed-bundle plus LLDB runtime proof bounding the sibling `StereoLayer<false>::compute()` lambda table at `0x667c28`, wrapper `0x274b10`, and worker `0x2727f0`. Static proof shows `0x2727f0` shares the same `0x275630` / `0x2730c0` / `0x2732f0` projection-cost family, while complete no-auto-LRIS bridge HDR probes across `28mm`, `35mm`, `70mm`, and `150mm` record zero hits for `0x274b10`, `0x2727f0`, adjacent setup helpers `0x272100` / `0x272640`, and their callsites, with live `runPass(int)` controls in the same runs.
- `bundle_proof_higherwarpdebug_renderdebugview_four_zoom.md`
  Installed-bundle plus LLDB runtime proof classifying high-address helper callers `0x42cb5d -> 0x3f6170`, `0x42cbc2 -> 0x3f7040`, and `0x42cc5a -> 0x3e55f0` as part of a `HigherWarpDebug::renderDebugView` local callback surface. Complete no-auto-LRIS bridge HDR probes across `28mm`, `35mm`, `70mm`, and `150mm` record zero hits for the debug-view entry/callsite/callback sites, while live controls at `0x3e05f5` and `0x3eb72d` hit five times per tier.
- `bundle_proof_prefusion_callable_gate_four_zoom.md`
  Installed-bundle plus LLDB runtime proof bounding the sampled prefusion `state+0x220` callable gate to inline false-return predicate bodies on the canonical four-zoom bridge HDR quartet.
- `bundle_proof_prefusion_candidate_scoring_family_four_zoom.md`
  Installed-bundle plus LLDB runtime proof bounding the `0x24c320` / `0x24d610` prefusion candidate-scoring families and local patch/search helpers on the canonical four-zoom bridge HDR quartet.
- `bundle_lldb_prefusion_candidate_output_custody_four_zoom.md`
  Installed-bundle plus repo-local LLDB proof, with repo-local verifier, binding the `0x24c320` / `0x24d610` candidate-scoring output vectors to the shared `0x2439b0` record-state gate by exact output-vector pointer continuity across complete canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR renders. This is scorer-output custody proof, not reducer closure.
- `bundle_lldb_prefusion_record_state_gate_histogram_four_zoom.md`
  Installed-bundle plus repo-local LLDB proof, with repo-local verifier, bounding `0x2439b0` as a live record-state gate for the custody-bound candidate-scorer output vectors: admitted wide family-A runs are unchanged at the boundary, admitted tele family-B runs promote target-2 records from state `3` to state `4`, and sampled downstream `0x241fd0` / `0x2416d0` / watched-store sites did not match the exact known scorer-output vector under this probe. This is record-state boundary proof, not reducer closure or final acceptance/rejection.
- `bundle_lldb_prefusion_promoted_record_watch_tele.md`
  LLDB hardware data-watch proof, with repo-local verifier, that selected tele records promoted by `0x2439b0` from `(state=3,target=2)` to `(state=4,target=2)` are later consumed in clean canonical `70mm` / `150mm` renders and at least one watched record per tele seed advances to `(state=5,target=2)` through `0x2416d0`. This is downstream consumer proof for watched promoted records, not public state semantics, final image contribution, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_state5_selected_index_path_tele.md`
  LLDB runtime proof, with repo-local verifier, that promoted target-2 record indices captured at `0x2439b0` later enter concrete `0x2416d0` selected-index vectors under clean canonical `70mm` / `150mm` renders, and that the small promoted sets captured here are observed reaching `(state=5,target=2)` stores. This is selected-index/state-relabel proof, not public acceptance semantics, final image contribution, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_state5_later_watch_tele.md`
  LLDB hardware data-watch proof, with repo-local verifier, that watched promoted tele records that become `(state=5,target=2)` continue downstream into the `0x244560` heavy-consumer family and the already-bounded `0x25d090` candidate block-geometry / active-block helper family. This is later state/candidate/geometry flow, not image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_block_geometry_effect_four_zoom.md`
  LLDB runtime proof bounding the `0x25d090` helper's admitted four-zoom effect as block-owned pair-vector growth plus descriptor-build / geometry-predicate / active-byte gating. Complete canonical no-auto-LRIS bridge HDR runs hit `44` entries per focal tier; active entries reach `0x25d2a0`, accepted entries grow both block pair-vector families and return true, and the only active-byte clears are two `70mm` geometry rejects. This is block-state effect proof, not image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_block_decision_cascade_four_zoom.md`
  LLDB runtime proof that the `0x244560` / `0x245a40` caller-side block-active decisions after paired `0x25d090` calls keep exactly one block active, record zero abort decisions, avoid the watched sentinel-fill path, and continue into `0x2457c0` callsites across the canonical no-auto-LRIS quartet. This is downstream block-decision / coordinate-output custody proof, not image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_state5_coord_output_four_zoom.md`
  LLDB runtime proof that `0x2457c0` is live and normally returning across the canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR quartet, sampled hits at the admitted `0x24593b` store-path site have `record+0x24 == 5`, and every admitted return leaves finite non-sentinel coordinate pairs in `state+0x1e8`. This is coordinate-output materialization proof, not image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_state5_coord_consumer_watch_four_zoom.md`
  LLDB hardware read-watch proof that representative finite non-sentinel coordinate pairs emitted by `0x2457c0` into `state+0x1e8` are later read by `0xe8e70` vector-copy work under both State-helper copy-out paths (`0x224d70 -> 0x245a40` and `0x224e50 -> 0x245a20 -> 0x244560`) across the canonical four-zoom bridge HDR quartet. This is coordinate-vector custody / copy-out proof, not image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_state5_coord_copy_dest_watch_four_zoom.md`
  LLDB hardware read/write-watch proof that representative finite non-sentinel destination pairs copied out by the State-helper `0xe8e70` path are touched again by `0xe8e70` vector-copy work across the canonical four-zoom bridge HDR quartet. Static/runtime evidence binds the admitted later caller frames to State-helper recopy sites plus higher node-vector materialization/copy sites at `0x22a61a -> 0xe8e70 -> 0x22a61f` and `0x22c93a -> 0xe8e70 -> 0x22c93f`. This is coordinate-vector custody / propagation proof, not image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_state5_coord_node_dest_watch_four_zoom.md`
  LLDB hardware read/write-watch proof that representative finite non-sentinel destination pairs copied into the `0x22a61a -> 0xe8e70 -> 0x22a61f` node-vector destination reach non-copy candidate/index/scoring-selection code under `0x21b2e0` and its `0x21c4f0` callback path across the canonical four-zoom bridge HDR quartet. The capped window proves at least one finite node-destination pair per run, not all copied pairs; it is not image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_state5_coord_node_dest_crossunit_28mm.md`
  Risk-based exact-`28mm` Unit-2 LLDB validation of the same state-5 node-destination non-copy consumer shape: the `0x22a61a -> 0xe8e70 -> 0x22a61f` node-vector copy site is live, three finite destination pairs are admitted, three watchpoints are armed, and the first watched pair reaches the same `0x21b444`, `0x21b44c`, `0x21c2b0`, and `0x21c2b6` candidate/index/scoring-selection consumer VAs as the Unit-1 four-focal proof. This is a second-body discriminator, not all-body/all-focal proof, image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_node_dest_sentinel_custody_four_zoom.md`
  LLDB same-address custody proof, with repo-local verifier, that one finite non-sentinel coordinate pair copied into the `0x22a61a -> 0xe8e70 -> 0x22a61f` node-vector destination per canonical focal tier is later the same runtime address rewritten by `0x21b923` / `0x21b92a` into `(-1.0, -1.0)`, then sampled in downstream touches while still sentinel. This links the node-destination consumer, sentinel-write, and sampled downstream-touch boundaries for representative pairs only; it is not all-pairs proof, image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_node_dest_20b5e0_branch_custody_four_zoom.md`
  LLDB same-address branch-custody proof, with repo-local verifier, that one finite non-sentinel coordinate pair copied into the `0x22a61a -> 0xe8e70 -> 0x22a61f` node-vector destination per canonical focal tier is later sentinelized at the same runtime address, then reaches `0x20b912` at that same address and single-steps through `0x20b91d -> 0x20ba90` and `0x20baab -> 0x20bafd` without visiting the local update-write block at `0x20bac0..0x20bac8`. This links copied node-destination identity to the sampled `0x20b5e0` local skip path only; it is not all-pairs proof, image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_node_dest_20ca00_source_copy_four_zoom.md`
  Reused LLDB same-address proof, with repo-local verifier, that one finite non-sentinel coordinate pair copied into the `0x22a61a -> 0xe8e70 -> 0x22a61f` node-vector destination per canonical focal tier is later sentinelized at the same runtime address, then source-read at that same address by `0xe0ae0` under caller return `0x20d309`, the second local vector copy inside `0x20ca00`. This links copied node-destination identity to the `0x20ca00` source-copy surface only; it is not destination-slot proof, gate-selection proof, image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_node_dest_20ca00_source_index_four_zoom.md`
  LLDB source/gate index proof, with repo-local verifier, that one representative copied node-destination address per canonical focal tier is source-read by `0xe0ae0` under caller return `0x20d309`, with readable local `source_index` and parent `gate_index`, and every captured candidate in the capped watchpoint window has `source_index != gate_index`. This is capped local non-selection proof for one watched address per tier; it is not destination-slot terminality, image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_node_dest_20ca00_gate_custody_selected_four_zoom.md`
  Selected-representative LLDB same-address gate-custody proof, with repo-local verifier, joining prior `0x22a61a` copied node-destination identity through sentinelization, the `0x20d309` source copy, computed destination-slot identity, and the `0x20d363 -> 0x20d565` skip branch for one `28mm` representative (`source_index == gate_index == 5394`) and one `70mm` representative (`source_index == gate_index == 77`). The selected `35mm` row is a capped no-match window and the selected `150mm` row is a full-render no-source-copy observation for one watched address. This is representative local gate-skip custody, not all-pairs proof, image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_node_dest_20ca00_gate_crossunit_selected.md`
  Risk-based selected cross-unit LLDB validation, with strict comparison verifier, observing the same full-sentinel `0x20d363 -> 0x20d565` gate-skip mechanism on Unit-2 in one complete `35mm` twin-capture run at index `12`. Unit-2 `28mm` / `70mm` anchors and a targeted Unit-2 `35mm` repeat are cap-limited no-match windows, so exact index and match incidence are not stable body/focal constants. This is cross-unit mechanism observation, not body-causation, all-pairs, image-effect, reducer-closure, or final-acceptance proof.
- `bundle_static_runtime_prefusion_20ca00_gate_skip_effect.md`
  Deterministic installed-bundle byte/import proof joined to selected Unit-1 and Unit-2 runtime packets. It proves `0x20d363 -> 0x20d565` bypasses keyed-node materialization, coordinate-to-double record writes, and imported `ceres::Problem::AddResidualBlock` at `0x20d560`, so those selected full-sentinel iterations add no residual through this local path. Post-loop `ceres::Solve` remains outside the skip; this is not all-pairs, shared-solve-output, image-effect, reducer-closure, or final-acceptance proof.
- `bundle_static_prefusion_20ca00_triangulator_callback_identity.md`
  Deterministic installed-bundle vtable/typeinfo and Capstone proof identifying `0x20ca00` as substantive slot `+0x30` of a `void(int,int,int)` lambda inside `lt::Triangulator::refine3dPoints()`, constructed at address point `0x657f00` and dispatched through executor `0x5670`. This corrects historical method-entry labels; callback argument names, public output meaning, runtime values, image effect, reducer closure, and final acceptance remain open.
- `bundle_static_prefusion_20ca00_record_range_custody.md`
  Deterministic installed-bundle SHA/Capstone proof tracing the parent owner through callable `+0x08` into the `0x20ca00` callback, binding the callback's post-solve triple to owner record fields `+0x08/+0x0c/+0x10` in a `0x14`-stride vector, and proving the immediate parent reduces positive `record+0x10` values to owner `+0x78/+0x7c`. This is internal solved-record ownership and immediate scalar-consumer proof, not public triple meaning, runtime-value, image-effect, reducer-closure, or final-acceptance proof.
- `bundle_static_prefusion_owner_range_phase_reuse.md`
  Deterministic installed-bundle SHA/Capstone proof that State body `0x22ae60` calls `0x20ada0` and then `0x20bd60` with the same owner pointer, and that those two phases write owner `+0x78/+0x7c` as pre-solve reciprocal extrema and later positive solved-record extrema. Full-text follow-up enumerates all 15 direct floating/vector numeric reads at encoded displacements `+0x78/+0x7c`, classifies them as other record families, and finds no direct same-displacement numeric consumer in the owner writer family or State caller. Aliases, adjusted pointers, integer bit-copies, indirect accessors, public names, image effect, reducer closure, and final acceptance remain open.
- `bundle_static_prefusion_20ca00_reprojection_cost.md`
  Deterministic installed-bundle typeinfo/import/SHA/Capstone proof identifying `0x667240` as the one-parameter, two-residual `AutoDiffCostFunction<lt::Internal::ReProjectionCost,...>` wrapper, tracing a unit-payload `CauchyLoss` through callable `+0x28` into `AddResidualBlock`, and verifying the exact scalar-ray 3x4 reprojection residual formula. This corrects the older raw-vtable label and proves internal ray-depth-scale semantics only, not public units, LRI origin, runtime solved values, image effect, reducer closure, or final acceptance.
- `bundle_static_runtime_index5_triangulator_depth_bound_custody.md`
  Deterministic installed-binary SHA/Capstone/import proof, joined to four complete canonical runtime mode packets, tracing the `0x3f2c40` constructor's mode-selected endpoint pair through `state+0x100/+0x104` and Triangulator owner `+0x70/+0x74` into Ceres lower/upper bounds on the one-scalar ray-depth reprojection problem. All four canonical Unit-1 focal tiers select mode `0` and `[200.0,640000.0]`, the same endpoint pair used by the index-5 reciprocal lookup vector. This admits the lookup's internal ray-depth hypothesis-grid role, not public units, public calibration/LRI/protobuf origin or names, public source-index names / physical semantics, solved values, image contribution, or final acceptance.
- `bundle_static_index5_depth_bounds_installed_origin.md`
  SHA-pinned complete code-reference census proving the bound-selecting
  constructor and its wrapper each have one direct caller, with the sole owner
  call hardcoding `edx=0`. The admitted `[200,640000] mm` mode-0 pair therefore
  has installed-constant origin and operational names Triangulator ray-depth
  lower/upper bounds; no LRI calibration/protobuf carrier supplies or names
  the pair on this path. The alternate nonzero pair remains publicly unnamed.
- `bundle_lldb_prefusion_20ca00_solve_output_28mm.md`
  Complete Unit-1 `28mm` solve-only runtime proof plus SHA-pinned two-stage post-Solve matrix formula, capturing 1,229 `0x20ca00` solve/write groups across ten completed callback frames. The solve changes the bounded ray-depth scalar in 279 groups; all 1,229 final selected `record+0x10` values equal the float32 solved scalar, and the immediate second transform leaves each captured triple bit-identical under this run. This is one body/focal/runtime distribution plus solved-record materialization proof, not public units/names, all-candidate behavior, shared-solve terminality, image contribution, reducer closure, or final acceptance.
- `bundle_lldb_prefusion_20ca00_solve_output_discriminators.md`
  Risk-based LLDB solve-output discriminator proof extending the `0x20ca00` first-write materialization surface to one Unit-1 tele run and one exact-focal Unit-2 run. Unit-1 `70mm` captures 3,456 solve/write groups with 317 solve-adjusted scalars; the first post-Solve write stores `f32(solved_scalar)` in every group, but the second transform changes every final triple, so final `record+0x10 == f32(solved_scalar)` is false for all captured groups. Unit-2 exact `35mm` captures 1,589 groups with 886 solve-adjusted scalars and exact final-z equality in that run; six pre-solve local scalars exceed the old Unit-1 mode-0 upper bound while all solved values remain within `[200,640000]`. This is discriminator runtime-value/materialization proof, not stable distribution, public units/names, all-candidate behavior, image contribution, reducer closure, or final acceptance.
- `bundle_lldb_prefusion_20ca00_record_z_downstream_watch_70mm.md`
  Capped Unit-1 `70mm` hardware-watch proof following one selected `0x20ca00` solved-record `record+0x10` field after the second post-Solve triple write. The watch arms at `0x20d737` on gate index `3906`, captures 64 read/write stops before the cap, records zero value changes, and observes same-address touches at the immediate `0x20bd60` parent scan, `0x239e00` / `0x239ac0` propagation, State/helper record-test/materialization windows, and downstream positive-record gate / transform-score window `0x2189c4`. This proves representative downstream custody only, not all-record behavior, terminality, image contribution, reducer closure, or final acceptance.
- `bundle_static_runtime_prefusion_218940_solved_record_score_window.md`
  Static + reused runtime proof, with repo-local verifier, joining the admitted Unit-1 `70mm` `record+0x10` downstream-watch packet to a SHA-pinned decode of helper `0x218940`. The watched finite positive z reaches `0x2189c4` 37 times with unchanged bits; installed code then skips only nonpositive/unordered z at `0x2189c8`, so the watched solved-record triple is locally admitted into the record/transform score body. This is representative local score-window admission only, not direct branch-step proof, all-record behavior, image contribution, reducer closure, or final acceptance.
- `bundle_static_runtime_prefusion_219210_record_score_caller_output.md`
  Static + reused runtime proof, with repo-local verifier, joining those same 37 `0x218940` helper samples to caller `0x219210`, slot `+0x30` of the `lt::SparseMirrorAngleOptimizer::optimize(...)::$_2` std-function callback. The runtime stack has return address `0x21937a` for every sample; installed code calls `0x218940` at `0x219375` and immediately stores the helper's `xmm0` return into the caller's per-index `[r14+0x18][r15]` float vector at `0x219381`. This is caller output-vector custody only, not stored-value proof, image contribution, reducer closure, or final acceptance.
- `bundle_static_runtime_prefusion_216f60_sparse_mirror_score_vector_consumer.md`
  Static + LLDB runtime proof, with repo-local verifier, showing that parent body `0x216f60` constructs the same `SparseMirrorAngleOptimizer::optimize(...)::$_2` callback and captures stack vector `[rbp-0x3f0]` at callback field `+0x18`. One complete Unit-1 `70mm` run carries the exact same closure, vector header, and 1,089-float begin pointer through 64 sampled post-store callback hits and the matched parent consumer at `0x217a68`; the parent min-like scan selects index `505` before side-output gates and selected-record materialization for `0xf33d0`. This is same-runtime callback-store to parent-consumer vector custody, not record-specific score proof, image contribution, reducer closure, or final acceptance.
- `bundle_static_runtime_prefusion_216f60_parent_score_selection_gate_matrix.md`
  SHA-pinned static plus complete runtime proof, with repo-local verifier, closing the local `0x216f60` parent decision over the callback score, side-output, and 24-byte candidate-record vectors. Across canonical Unit-1 `28mm` / `35mm` / `70mm` / `150mm` plus exact-focal Unit-2 `35mm`, the parent selects the minimum score, applies the selected-side `0.25` cap, selected-side versus center-side comparison, and optional float32 `selected_score <= 0.8 * center_score` gate, then materializes the selected 24-byte record and calls/returns from `0xf33d0` only for accepted winners. This is local score-selection and record-custody proof, not public vector/record naming, downstream image/source contribution, distributed reducer closure, or final merge acceptance/rejection.
- `bundle_static_runtime_prefusion_216f60_accepted_bank_downstream_custody_matrix.md`
  SHA-pinned static plus hardware-watch runtime proof, with repo-local verifier, extending accepted `0x216f60` winner custody through selector-1 `0xf33d0` into destination bank `+0x12c..+0x17f` and later unchanged `0x264270` reads. The canonical Unit-1 four-focal matrix plus exact-focal Unit-2 `35mm` all show direct `f34e0`-returned bank-copy reads and `f3350` accessor-side reads before a later State-helper `0xf33d0` overwrite; selected `0x3f7ec0` materialization sites are zero-hit under these complete no-auto-LRIS runs. This is accepted-bank-to-State/helper-record-assembly custody and a scoped route exclusion, not public record naming, final image/source contribution, distributed reducer closure, or final merge acceptance/rejection.
- `bundle_static_runtime_prefusion_264270_output_to_23faf0_four_zoom.md`
  SHA-pinned static plus two-phase one-hit hardware-watch proof, with repo-local verifier, carrying the exact `0x264270` output record assembled from an accepted selector-1 bank into `0x23faf0` and then carrying the exact composer destination into its first later consumer across the canonical four focal tiers. Wide tiers arrive through `0x239e00 -> 0x239ac0 -> State 0x22d250` and first load composer fields into `0x239e00` score-input locals at `0x23a179`; tele tiers arrive through `0x20afb0 -> 0x20ada0 -> State 0x22ae60` and first pass the composer destination into `0x20dbe0` matrix-composition math at `0x20dbef`. This is exact transform/score-state custody, not public record naming, final image/source contribution, distributed reducer closure, or final merge acceptance/rejection.
- `bundle_static_runtime_prefusion_composer_transform_materialization_four_zoom.md`
  SHA-pinned static plus route-gated runtime proof, with repo-local verifier, carrying that exact composer destination through its immediate transform calculation, first durable store, and later hardware-watch boundaries. Wide `0x239e00` computes and averages 2D Euclidean reprojection residuals, `0x239ac0` stores the exact returned scalar in a keyed payload, and `0x23a530` reads it back unchanged under State `0x22d250`. Tele `0x20dbe0` multiplies the composer `3x3` block by a `3x4` row block, and `0x20afb0` copies the exact 48 result bytes into a keyed node whose tracked prefix is first touched again only during recursive cleanup. The original wide branch labels are superseded by the next entry.
- `bundle_static_runtime_prefusion_wide_minimum_selector_calibstage_transfer.md`
  Corrective SHA-pinned static plus completed outcome-targeted `28mm` and independent `35mm` transfer/consumer proof showing the wide comparison is a local minimum selector. A lower candidate is materialized into the keyed record; a higher candidate retains the existing `state+0x448` record and copies its three source slices byte-exactly into the same-key per-camera `state+0xe0` selector-1 CalibStage bank. Both route effects align node/object key with public `CameraModule.id`; the checked transferred slices are derived records rather than exact public calibration fixed32 sequences. Post-transfer watches carry the exact selected bank through terminal composition, keyed BA camera-map normalization, exact record conversion/composition, and changed same-key selector-1 CalibStage write-back. This proves State calibration-record selection/normalization/write-back custody, not complete public naming, post-write-back image/source contribution, reducer closure, or final merge acceptance/rejection.
- `bundle_static_runtime_prefusion_terminal_two_pass_calib_consumer.md`
  SHA-pinned static plus outcome-gated Unit-1 `35mm` proof that a same-public-camera-key normalized selector-1 bank written in terminal State `0x22e1d0`'s first `0x23c5f0` pass remains byte-identical through the second helper call and is read from the exact object at pass-2 `0x23cba6 -> 0x264440`. Complete exact-focal Unit-1 and Unit-2 `35mm` controls prove the same ordered 19-read-per-pass keyed topology on both bodies while allowing body-specific bank values. This is terminal calibration-helper consumer custody, not image/source contribution, reducer closure, or final merge acceptance/rejection.
- `bundle_static_runtime_prefusion_postterminal_calib_finalize_two_body.md`
  Installed RTTI/call-target proof plus complete exact-focal Unit-1 and Unit-2 `35mm` runtime census of the terminal calibration continuation. Both bodies skip optional JPEG/overlay diagnostic body `0x227b00` with owner byte `+0x10d = 0`, execute `0x226240 -> 0x239a90`, replace the internal calibration sibling with a different non-null object, and return normally from the final `StereoAsyncAPI::ProcessingState` lambda (`$_7`, target state `8`). A post-finalization read/write watch records no later exact-owner-slot touch before `0x22e9f0` destruction clears and releases the sibling. Complete Capstone-decoded constructor proof also excludes publication of a separate alias by `0x239a90 -> 0x2399a0` itself. This is scoped post-terminal route/constructor/same-owner-slot classification, not absence of later or externally copied aliases or image/source effect.
- `bundle_static_runtime_prefusion_postterminal_state_to_pipelinecache_four_zoom.md`
  SHA-pinned static plus sequential canonical four-focal runtime proof and an exact-focal Unit-2 35mm discriminator distinguishing the terminal whole calibration State from its replaced `State+0x2a8` sibling. The exact State root is retained at `PipelineCache+0x180` and passed five times per render to `0x3f7040`, which builds the five `PipelineCache+0x258` paired transform/warp-field records from `state+0xe0/+0x448`; the replacement sibling is a different pointer and receives no exact-slot touch before destruction. This closes the proposed sibling-to-warp-vector feed negatively while proving the actual whole-State feed on both bodies.
- `bundle_lldb_prefusion_node_dest_tele_scan_score_identity.md`
  Reused same-address LLDB proof, with repo-local verifier, that one representative copied node-destination address per tele tier is later sentinelized at the same runtime address and then sampled at the same address in the `0x216f60` scan/count window and at the `0x218bc4` score/materialization guard operand site while still full `(-1.0, -1.0)`. By itself this links identity to bounded local scan/count and score-guard surfaces; the next entry adds same-address branch effect, while whole-vector terminality, image effect, reducer closure, and final acceptance/rejection remain open.
- `bundle_lldb_prefusion_node_dest_218bc4_branch_custody_tele.md`
  Selected same-address tele branch-step proof, joined to a SHA-pinned local-effect verifier, showing one previously finite copied pair per tele tier is sentinelized to full `(-1,-1)`, reaches `0x218bc4` at the same address, and takes the x-nonpositive branch directly to `0x218cb8`. That branch skips this loop's transform/score block, local score-sum update, over-threshold-count update, and positive-pair-count update for both watched pairs. This is representative local exclusion, not all-pairs/alias/alternate-route terminality, shared-solve terminality, image contribution, reducer closure, or final acceptance.
- `bundle_lldb_prefusion_node_sentinel_write_four_zoom.md`
  LLDB runtime/static proof, with repo-local verifier, that the downstream `0x21b2e0` path executes coordinate-pair sentinel invalidation writes at `0x21b923` and `0x21b92a` across the canonical four-zoom bridge HDR quartet. Runtime samples show finite non-sentinel coordinate pairs before the x-lane store and x already changed to `-1.0` before the y-lane store; static disassembly proves both stores write raw bits `0xbf800000` (`-1.0`). This is coordinate invalidation/rejection write proof, not image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_node_sentinel_downstream_watch_four_zoom.md`
  LLDB hardware read/write-watch proof, with repo-local verifier, that selected sentinel-marked node-vector coordinate pairs are touched later by downstream code across the canonical four-zoom bridge HDR quartet. Watchpoints were armed only after the full pair read `(-1.0, -1.0)` immediately after `0x21b92a`, and every sampled later touch still observed `(-1.0, -1.0)`. Sampled downstream surfaces include State-family copy/record propagation plus coordinate scan/scoring/materialization windows. This is downstream sentinel-coordinate custody / consumption proof, not image-effect proof, source-contribution proof, reducer closure, or final acceptance/rejection.
- `bundle_static_prefusion_state_22ae60_copy_record_surfaces.md`
  Static + reused runtime proof, with repo-local verifier, classifying the sampled State-family `0xe0ae0` copy callers under `0x22ae60`: `0x20bd60` / `"point BA"` is keyed record materialization, `0x25e4b0` is the no-map `0x25e0c0` row-producer variant, `0x20dca0` is keyed record storage, `0x20ca00` is selected Ceres setup with positive-coordinate gates, and `0x239ac0` / `0x239e00` are keyed pair-vector propagation surfaces. This prevents treating those sampled windows as opaque possible reducers; it does not prove image effect, reducer closure, or final acceptance/rejection.
- `bundle_static_runtime_prefusion_state_22ae60_cross_object_pair_vector_custody.md`
  SHA-pinned static proof joined to admitted runtime packets, showing that State `0x22ae60` constructs the solver-owner and sibling objects from shared upstream handles, that live State samples preserve shared top-level `0x14` record-vector and keyed pair-tree handles across all four Unit-1 focal tiers plus an exact-focal Unit-2 `28mm` discriminator, and that selected keyed-record pair-vector allocations are source-read through both helper objects across all four Unit-1 focal tiers plus that Unit-2 discriminator. This proves shared handle and selected pair-allocation custody, not all-record sharing, public names, image effect, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_20ca00_copied_sentinel_gate_four_zoom.md`
  LLDB hardware-watch proof, with repo-local verifier, following watched sentinel pairs copied by the second `0x20ca00` local vector copy at `0x20d304 -> 0xe0ae0 -> 0x20d309`. The admitted `70mm` run has one exact copied-slot match (`source_index == gate_index == 774`) whose copied destination is later read at `0x20d363` as `(-1.0, -1.0)` and branches to skip target `0x20d565`; admitted `28mm`, `35mm`, and `150mm` runs show capped no-match windows for the watched sentinel pairs. This is local copied-slot gate proof, not whole-vector terminality, image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_static_prefusion_sentinel_216f60_scan_count_window.md`
  Static + reused runtime proof, with repo-local verifier for the reused runtime subset, that sampled tele sentinel-coordinate stops inside the `0x216f60` scan/count window still read `(-1.0, -1.0)`, while static disassembly proves that the local vector/scalar count paths count only pairs where both lanes are positive and require at least eight counted entries before continuing. This is local non-counting proof for sampled sentinel reads, not exhaustive terminality, image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_sentinel_score_guard_tele.md`
  LLDB hardware watchpoint proof, with repo-local verifier, that selected tele sentinel-marked coordinate pairs reaching `0x218bc4` skip via `jae 0x218cb8`; the wide first-six watched sentinel pairs do not reach this guard within the watchpoint cap, and count-only wide runs prove the observed wide sentinel populations are larger than that watched subset (`152` at `28mm`, `106` at `35mm`). This is sampled tele guard-skip proof plus scoped wide non-observation/count, not image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_sentinel_score_guard_branch_step_tele.md`
  LLDB hardware-watch plus branch-step proof, with repo-local verifier, that sampled tele sentinel-marked coordinate pairs stopping at `0x218bc4` single-step directly to `0x218cb8` while still reading `(-1.0, -1.0)`. This replaces the prior flags-only inference for the admitted samples; it is still sampled local guard proof, not whole-vector terminality, image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_static_runtime_prefusion_sentinel_score_guard_local_loop_tele.md`
  Static + reused branch-step runtime proof, with repo-local verifier, that the admitted `70mm` / `150mm` sentinel-coordinate branch-step samples skip the local `0x218b30` positive-coordinate body containing `xmm1` accumulation, `r10d` update, and `r9d` increment; the same helper later derives its `r14` store after converting `r9d` / `r10d`. This is sampled local non-count / non-score evidence only, not whole-vector terminality, image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_sentinel_guard_direct_census_wide.md`
  LLDB direct-breakpoint proof, with repo-local verifier, that complete canonical `28mm` and `35mm` runs collect the full observed wide sentinel populations (`152` unique completed sentinel pairs at `28mm`, `106` at `35mm`) while direct `0x218bc4` guard breakpoint hits remain zero. This proves the `0x218b30` / `0x218bc4` guard site is not live under the admitted wide runs; it is not whole-vector terminality, image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_static_prefusion_sentinel_20b5e0_branch_window.md`
  Static + reused runtime proof that the sampled `0x20b912` downstream sentinel stops across the canonical four-zoom quartet sit immediately after an x-lane load from a still-sentinel `(-1.0, -1.0)` pair, and that the local static `0x20b5e0` branch/write window has a nonpositive/sentinel path that bypasses the `0x20bac0..0x20bac8` update writes. This is local branch-boundary proof for sampled sentinel reads, not exhaustive terminality, image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_sentinel_20b5e0_branch_step_four_zoom.md`
  LLDB runtime branch-step proof that three sampled watched `0x20b912` sentinel reads per canonical focal tier step through `0x20b91d` with flags taking `jae 0x20ba90`, then through `0x20baab` with flags taking `jbe 0x20bafd`, with zero admitted traces reaching the local `0x20bac0..0x20bac8` update writes. This is direct runtime flags/branch-target proof for sampled sentinel reads, not exhaustive terminality, image-effect proof, reducer closure, or final acceptance/rejection.
- `lldb_iramp_wrapper_accumulator_four_zoom.md`
  LLDB runtime proof that the canonical four-zoom bridge HDR quartet all hit the visible `src1` wrapper, `src2` wrapper, contributor wrapper, and IRAMP accumulator surfaces at `0x3ecc10`, `0x3ecd80`, `0x3eced0`, and `0x369fa1`.
- `lldb_iramp_entry_signature_four_zoom.md`
  LLDB runtime proof that the canonical four-zoom bridge HDR quartet all enter `0x365960` with `src1`, `src2`, `srcs[5]`, `warps[5]`, scale, and ROI.
- `lldb_iramp_count_use_vector_four_zoom.md`
  LLDB runtime proof that the live `0x3661b0` count-use window at `0x366a50..0x366a65` reads a vector header through `r15+0x18`, computes `(end-begin)/16`, and reaches `0x366a65` with live count `5` across 16 capped packets per canonical focal tier. This is count-use evidence only, not a complete reducer proof.
- `lldb_iramp_terminal_consolidation_four_zoom.md`
  LLDB runtime consolidation proof, with repo-local verifier, that the Opus-directed terminal harness cleanly captures eight samples per site across IRAMP entry, inner worker, sentinel compare, score multiply, tuple score store, reciprocal, and weighted-store sites for all four canonical focal tiers. This validates the harness and local packet arithmetic; it does not prove final source contribution or final acceptance/rejection.
- `lri_35mm_seed_correction_true35_runtime.md`
  Direct LRI-header and corrected LLDB-runtime proof replacing the mislabeled `L16_02951` 35mm seed with true-35mm `L16_03041`, and repairing the affected runtime split rows.
- `lldb_iramp_contributor_identity_four_zoom.md`
  LLDB runtime proof that the corrected four-zoom bridge HDR quartet passes `B1..B5` as direct IRAMP contributors at `28mm`/`35mm` and `C1..C5` at `70mm`/`150mm`; C6 remains a routing blocker.
- `lldb_src_lookup_and_src2_state_four_zoom.md`
  LLDB runtime proof that the visible `src1` lookup key is `0` at `28mm`/`35mm` and `8` at `70mm`/`150mm`, while the visible `src2` hot path reads a tiered `PipelineCache+0x1e0` resample-state object; this narrows but does not close the exact `src1` / `src2` reducer blocker.
- `bundle_lldb_src2_state_3ebb80_static.md`
  Installed-bundle static proof replacing the scratch-era `0x3ebb80` citation. It bounds visible `src2` path `0x3ecd80 -> 0x3ebb80 -> 0x3edb80` to `PipelineCache+0x1e0` state, `PipelineCache+0x1d8` fallback/source-descriptor plumbing, descriptor validation, a 64-entry scalar table, generic tiled executor dispatch, and one-image normalization. It does not identify semantic `src2` contents behind the generic executor dispatch.
- `lldb_src2_executor_target_28mm.md`
  Runtime plus installed-bundle static proof following the visible `src2` generic executor dispatch at `0x3ebb80 -> 0x3ec462` for the canonical `28mm` seed. The first accepted dispatch binds callback vtable `0x65f7e8`, slot `+0x30 = 0x3ed2e0`; static inspection classifies `0x3ed2e0` as a one-source descriptor resampling/materialization worker using `cache+0x1e0` projection/radial state, a 4096-entry radial table, 1/64 fractional coefficient-table indexing, 4x4 SIMD sampling/clamping, and 16-byte vector output.
- `lldb_src2_executor_target_four_zoom_scope.md`
  Follow-up runtime proof extending visible `src2` executor-target scope across the canonical quartet: all four canonical seeds prove accepted gate, accepted dispatch through `0x5d94`, worker entry at callback slot `0x65f7e8/+0x30 = 0x3ed2e0`, and completed `10432x7824` HDR output. `35mm`, `70mm`, and `150mm` use dynamic hardware completion probes.
- `lldb_src2_descriptor_origin_four_zoom.md`
  Follow-up runtime/static proof bounding the visible `src2` callback `+0x08` source-descriptor producer across the canonical quartet: static construction ties stack descriptor `rbp-0x2200` to callback `+0x08`, and accepted runtime probes show the descriptor is populated through `PipelineCache+0x1d8` vtable slot `+0x18 = 0x406a10` at `28mm`, `35mm`, `70mm`, and `150mm`. Public semantic contents and LRI origin remain open.
- `lldb_src2_406a10_branch_four_zoom.md`
  Follow-up LLDB proof bounding the branch/helper reached inside the visible `src2` `0x406a10` source-descriptor producer during complete canonical bridge HDR runs: `28mm` / `35mm` have object byte `+0x18 = 1` and reach `0x40721b -> 0x31b110`; `70mm` / `150mm` have object byte `+0x18 = 0` and reach `0x407458 -> 0x31acf0`. Prior evidence classifies those helper targets as source adapter / validation-wrapper surfaces, not reducer closure.
- `bundle_proof_fusioncachebayer_flag_origin_static.md`
  Installed-bundle static proof bounding the origin of `FusionCacheBayer+0x18` to constructor base initializer `0x402d20`, its sentinel-key computation, helper/accessor offsets, the later constructor branch at `0x4066fc`, and the nonzero-only construction of object field `+0x20`.
- `lldb_fusioncachebayer_flag_origin_four_zoom.md`
  LLDB runtime proof tying the visible-`src2` `0x406a10` branch selector back to constructor-origin state across the canonical four-zoom bridge HDR quartet: `28mm` / `35mm` write and later consume flag `1` and construct `FusionCacheBayer+0x20`; `70mm` / `150mm` write and later consume flag `0` and have zero `+0x20` store hits under the tested complete runs.
- `lldb_fusioncachebayer_scan_collection_four_zoom.md`
  LLDB runtime proof for the `0x402d20` scan-loop records that produce accepted key `1` at `28mm` / `35mm` and preserve sentinel `16` at `70mm` / `150mm`, plus static follow-up proving `0xf6c60` camera-ID group ordinals and `0xf2770` construction of item `+0x60` / `+0x58/+0x5c`; the `150mm` scan facts are pre-crash and not output-completion evidence.
- `lldb_capturedimage_f2770_origin_four_zoom.md`
  LLDB runtime proof at the direct `0xe59a4 -> 0xf2770` constructor callsite across the canonical quartet: wide seeds construct keys `0,4,6,8,9,1,2,3,5,7`, tele seeds construct keys `6,8,9,14,5,7,11,10,12,13,15`, all captured items are initially active at item `+0x30 = 1`, input `+0x30` equals output item `+0x60`, and input `+0x28/+0x18` carries the same two-int pair later observed at item `+0x58/+0x5c`.
- `bundle_static_runtime_prefusion_bayer_override_public_origin_two_body.md`
  SHA-pinned static/schema proof plus all `42` admitted Unit-1 four-focal
  constructor events and exact-focal Unit-2 public carriers names
  `CapturedImage+0x58/+0x5c` as
  `CameraModule.sensor_bayer_red_override.{x,y}`, public type `Point2I`.
  A2/key `1` is the unique wide `(-1,-1)` override and C6/key `15` the unique
  tele override on both bodies. Selector purpose and final policy remain open.
  Follow-up Lane B audit evidence binds the constructor-family `+0x30/+0x60`,
  `+0x34/+0x50`, `+0x38/+0x54`, `+0x40`, and `+0x48` subset to raw public
  `LightHeader.modules[camera]` fields; embedded-schema follow-up names them
  `id`, `mirror_position`, `lens_position`, `sensor_exposure`, and decoded
  `sensor_temparature`.
- `lldb_src1_contributor_payload_family_four_zoom.md`
  LLDB runtime proof that the visible `src1` lookup payload family is a `0x490` object with vtable address point `0x65f140`, while the direct contributor payload family is a `0x1f0` object with vtable address point `0x65f490`, across the canonical four-zoom bridge HDR quartet.
- `bundle_lldb_src1_contributor_secondary_callable_families.md`
  Bundle plus LLDB runtime proof that the visible `src1` and direct contributor payload families also differ at payload `+0x60`: visible `src1` uses secondary address point `0x65f388` with substantive slot `0x3e4a80`, while direct contributors use `0x65f4d8` with substantive slot `0x3e78d0`.
- `lldb_src1_secondary_callable_live_four_zoom.md`
  LLDB runtime proof that the visible `src1` secondary callable body at `0x3e4a80` is live across the canonical four-zoom bridge HDR quartet and that the first captured call-site packet passes the same `0x490` payload to `0x3e2e90`.
- `lldb_src1_worker_projection_record_four_zoom.md`
  LLDB runtime proof that the first captured worker/projection-record path beneath visible `src1` reaches `0x3e4c50` across the canonical four-zoom bridge HDR quartet, with callback fields for source image / output image / default vector / projection record / weight table and a payload-internal callable load from `payload+0x170` to `payload+0x150` whose slot `+0x30` is `0x3e42e0`.
- `bundle_proof_src1_projection_callable_transform.md`
  Installed-bundle proof that the live `0x3e42e0` projection callable is a two-float coordinate-transform body with three row equations, divide by the third row, recentering, and radius-indexed scale-table correction, with scaled variants at `0x3e44b0`, `0x3e46a0`, and `0x3e4890`.
- `bundle_proof_src1_projection_field_pack_producer.md`
  Installed-bundle proof bounding the producer path for the visible `src1` projection fields consumed by `0x3e42e0`: `0x3e27a0` calls `0x3f6170`, the dispatcher routes through same-category `0x3f6200` or cross-category `0x3f6940`, both converge on `0x145580` / `0x144f50`, and `0x144a70` forces the radius table to `4096` floats.
- `lldb_src1_projection_field_dispatcher_four_zoom.md`
  LLDB runtime proof that complete canonical bridge HDR runs hit projection field-pack dispatcher `0x3f6170` and its same/cross branches, with observed keys `0,5..9` at `28mm`/`35mm` and `8,10..14` at `70mm`/`150mm`; key `15` / C6 is not observed, so this tested dispatcher boundary is not a positive C6-routing observation.
- `lldb_direct_payload_candidate_gate_c6_four_zoom.md`
  LLDB runtime proof that the direct payload candidate loop at `0x3e0330` visits keys `0..9` at `28mm`/`35mm` and `5..15` at `70mm`/`150mm`; tele key `15` / C6 reaches the loop but has post-mutation `object+0x30 = 0`, skips before class compare, and never reaches the `0x3e05f5 -> 0x3f6170` dispatcher call under canonical bridge HDR runs.
- `lldb_stereo_candidate_gate_c6_four_zoom.md`
  LLDB runtime proof that the stereo-side keyed-record loop inside the `0x3f2c40` constructor branch visits keys `0..9` at `28mm`/`35mm` and `5..15` at `70mm`/`150mm`; tele key `15` / C6 reaches the loop but has post-mutation `object+0x30 = 0`, skips before the post-gate path, and never reaches either tested `0xf2720` getter callsite under canonical bridge HDR runs.
- `lldb_c6_active_byte_mutation_watch_tele.md`
  LLDB hardware write-watchpoint proof for tele key `15` / C6: the tested `0xf2770` path constructs C6 active at item `+0x30 = 1`, then both canonical tele seeds hit a later write at `libcp+0x3c90a5` that clears that same byte to `0`; static local gate shows this writer clears key `15` when the grouped context `+0x44` value is not group ordinal `2`. This proves the earlier direct/stereo C6 filters observe post-constructor mutated state, not constructor-birth state.
- `lldb_c6_focused_f2720_route_census_tele.md`
  Focused LLDB census of 24 selected direct `0xf2720` key-getter callsites under complete `70mm` and `150mm` bridge HDR runs. Both tele seeds show identical key-15 observations: active key-list helper hits at `0x1bdbab` / `0x1bdbdd`, active mutation-body hits at `0x3c9043` / `0x3c9098`, and later inactive key-15 hits at `0x3b2143`, `0x402df7`, and `0x40d219`. This proves focused key-query participation, not image contribution, terminal filtering, or full-route closure.
- `lldb_c6_unprobed_direct_f2720_route_census_tele.md`
  LLDB census of the remaining 34 direct `0xf2720` callsites outside the focused set under complete `70mm` and `150mm` bridge HDR runs. Both tele seeds show identical key-15 observations: active constructor-adjacent key/container/tree materialization hits at `0xe327e`, `0xe32f3`, `0xe4063`, `0xe5fd9`, and `0xe6020`, plus inactive shared-object lookup hits at `0xe6be0`; chunk B has no key-15 observations. Together with the focused 24-site proof, all 58 statically enumerated direct `call 0xf2720` sites now have admitted tele runtime census coverage. This does not prove terminality, non-`0xf2720` route absence, or final C6 image contribution/exclusion.
- `lldb_c6_postmutation_active_byte_watch_tele.md`
  LLDB hardware read/write watchpoint proof on the same tracked post-mutation key-15 `item+0x30` byte under complete canonical `70mm` and `150mm` bridge HDR runs. Both tele seeds arm one watchpoint at immediate inactive state `0x3c90a9`, record 18 later stops, and every stop observes `item+0x30 = 0`, `item+0x60 = 15`, `item+0x58/+0x5c = (-1,-1)`, and `item+0x100 = 3`. The stopped libcp VAs include active-byte gates outside the direct `0xf2720` inventory; this narrows same-byte reactivation/consumer behavior but does not prove whole-object terminality, other-field/alias absence, all non-`0xf2720` route absence, or final C6 image contribution/exclusion.
- `lldb_c6_postmutation_item_field_watch_tele.md`
  LLDB hardware read/write watchpoint proof on selected fields of the same tracked post-mutation key-15 item under complete canonical `70mm` and `150mm` bridge HDR runs. Both tele seeds arm watchpoints on `item+0x30`, `item+0x58..0x5f`, `item+0x60..0x67`, and `item+0x100..0x107` at immediate inactive state `0x3c90a9`. Pre-output libcp stops read the watched `+0x60..+0x67` range at `0xf2727` (`+0x60`) and `0xf3327` (`+0x64`), while the watched pair and type/adjoining ranges record only allocator-cleanup stops after output write. This narrows selected-field post-mutation behavior but does not prove whole-object terminality, untested-field/alias absence, or final C6 image contribution/exclusion.
- `lldb_c6_mutation_identity_tele.md`
  Focused LLDB identity trace tying the active key-list helper observations, mutation-body observations, `0x3c90a5` store, immediate `0x3c90a9` inactive state, and later `0x3b2143` inactive context-walk observation to the same tracked key-15 item pointer in complete `70mm` and `150mm` bridge HDR runs. Static inspection classifies helper `0x1bdb60` as key-list bookkeeping; this evidence by itself does not prove downstream context-consumer semantics or final C6 contribution/exclusion.
- `lldb_c6_postmutation_state_consumer_tele.md`
  LLDB runtime proof that the immediate caller path after `0x3c8f90` consumes the constructed `ctx+0xa0` object in complete canonical `70mm` and `150mm` bridge HDR renders: both tele seeds hit the post-mutation accessor path, walk the eleven-entry item vector, observe key `15` inactive at `0x3b2143`, write derived state fields `+0x0 = 3` and `+0x4 = 1` to context `+0xc8`, and queue context `+0x4b0 = 5`. This proves a state-classification consumer, not final image contribution or terminality.
- `lldb_c6_context_a0_consumer_negative_tele.md`
  Scoped negative LLDB proof for candidate context route `0x3c9540 -> 0xe6c30`: complete canonical `70mm` and `150mm` bridge HDR runs re-hit the constructor/mutation custody path but record zero hits at the candidate consumer/helper sites. This excludes only that route under tested tele conditions, not all downstream consumers or alternate C6 routes.
- `lldb_c6_postmutation_downstream_rect_vector_tele.md`
  LLDB runtime proof following the immediate downstream caller segment after the proven post-mutation `context+0xc8` / `context+0x4b0` state writes. Complete canonical `70mm` and `150mm` bridge HDR runs reread `context+0xc8` as state fields `+0x0 = 3` and `+0x4 = 1`, call `0x40b0e0` with return `0`, take the fallback `0x3c8c00` branch, compute raw/scaled pairs `(4160,3120)` / `(8914,6685)`, pass `context+0x4b0 = 5` as `r8d` into `0x3c8d00`, and return a five-entry vector of 16-byte integer tuples. This proves a live downstream rect-vector path for the proven state, not final image contribution, terminality, or alternate-route absence.
- `lldb_c6_rect_vector_consumer_four_zoom.md`
  LLDB runtime proof that the five-entry rect-vector route is consumed by the immediate caller across the canonical four-zoom bridge HDR quartet: the caller derives five `context+0x4c0` delta-dimension pairs from the rect tuples, passes those pairs to `0x3982b0`, builds a five-level `CIAPI::ImagePyramid`, stores its shared pointer at `context+0x538`, and installs nonzero downstream context object pointers. This proves vector-consumer identity as ImagePyramid construction; it does not prove final C6 image contribution/exclusion, terminality, alternate-route absence, or final merge acceptance/rejection.
- `lldb_c6_image_pyramid_zero_fill_four_zoom.md`
  LLDB runtime plus repo-local static proof that the five-level `context+0x538` ImagePyramid route is immediately iterated across the canonical four-zoom bridge HDR quartet: the caller reads each level image, builds a full-image stack descriptor, and invokes direct zero-fill callsite `0x3b2f54 -> 0xf7c0` once per level with bytes-per-pixel argument `4`. Runtime descriptor values satisfy the static contiguous zero-fill condition (`stride_pixels == width`) for all twenty level descriptors, and the first 32 bytes sampled after return are zero for all twenty descriptors. This proves an immediate zero-fill consumer of the ImagePyramid route; it does not prove final C6 image contribution/exclusion, terminality, alternate-route absence, later writer absence, or final merge acceptance/rejection.
- `lldb_c6_image_pyramid_downstream_liveness_four_zoom.md`
  Scoped negative LLDB proof for selected later static `context+0x538` candidate families. Complete canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR renders re-hit `0x3b2abd` once and `0x3b2f59` five times, but record zero hits at the selected histogram-like last-level consumer, last-level materializer, region/deeper-level consumer, direct first-image descriptor, and virtual-consumer sites. This excludes only those selected candidate VAs under the tested conditions; it does not prove terminality or absence of unprobed aliases/consumers.
- `lldb_c6_image_pyramid_data_watch_representative_four_zoom.md`
  Representative hardware data-watch proof for selected zero-filled ImagePyramid backing storage. After `0x3b2f59`, complete canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR renders arm a read/write watchpoint on the first 8 bytes of one selected level buffer; all four watchpoints record zero hits and all four renders exit cleanly. This proves no later read/write of those watched byte ranges only, not whole-buffer terminality.
- `lldb_c6_image_pyramid_data_watch_grid_tele.md`
  Expanded tele hardware data-watch proof for zero-filled ImagePyramid backing storage. After `0x3b2f59`, complete canonical `70mm` and `150mm` bridge HDR renders arm first/middle/last 8-byte read/write watchpoints across all five ImagePyramid levels; all 30 admitted grid cells record zero later watchpoint hits and exit cleanly. This proves no later read/write of those watched tele byte ranges only, not whole-buffer terminality or alias absence.
- `bundle_proof_src1_source_image_producer_topology.md`
  Installed-bundle proof bounding the source-image producer path beneath the visible `src1` `0x3e2e90` worker handoff: keyed cache helpers `0x1bdc80` / `0x1be750`, validation wrappers `0x31af30` / `0x31acf0`, lower producers `0x33ede0` / `0x33f480`, and shared per-source iterator `0x33f180`; this proves producer topology and per-source virtual dispatch, not semantic `src1` contents or reducer closure.
- `lldb_src1_keyed_helper_and_builder_boundary_four_zoom.md`
  LLDB runtime proof that complete canonical bridge HDR runs hit the visible-source keyed cache helper `0x1bdc80` but not the stack helper `0x1be750` or vector builder/updater body `0x1be270`; the observed tele helper keys are `5..14`, with no key `15`, so this tested helper boundary is not a positive C6-routing observation.
- `lldb_src1_visible_gated_virtual_four_zoom.md`
  LLDB runtime proof that the first captured lower producer path beneath the visible `src1` gate is `0x3e3279 -> 0x31af30 -> 0x33ede0 -> 0x33f180` across the canonical four-zoom bridge HDR quartet, and that the first captured per-source virtual target is vtable address point `0x65b3c8`, slot `+0x30 = 0x341770`; static inspection bounds `0x341770` to per-source region-adapter / record-update work, not reducer closure.
- `lldb_src1_virtual_target_census_four_zoom.md`
  LLDB runtime proof extending the first-captured visible-`src1` lower producer proof into a capped four-zoom target census: under the first-visible-`src1` gate, `28mm`/`35mm` reach `0x33f3e8`, `0x33f94f`, and `0x33ffd4`, while `70mm`/`150mm` reach `0x33f3e8` and `0x33f94f` with zero `0x33ffd4` hits under the tested complete runs. The `512` virtual-site counts are caps/lower bounds, not algorithm constants.
- [bundle_static_runtime_per_payload_pipeline_stage_order_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_per_payload_pipeline_stage_order_four_zoom.md)
  Installed-static plus retained-runtime proof of the fixed 16-slot payload callback permutation and exact active Bayer/BayerFloat/Color stage orders. `setToneAdjust` places Laplacian clarity at index 13, after index-11 Lab-L sharpen and index-12 lens shading where present, before index-15 `setToneMapping`; the following bundle classifies index 15 as conditional linear-ProPhoto materialization. Unit-1 `28/35mm` Color order is public AWB/color scale -> CNR -> adaptive desaturation -> denoise -> Lab-L sharpen -> clarity -> index 15; tele Color has scoped zero hits, while tele BayerFloat adds CNR/adaptive/denoise before sharpen. This is callback/descriptor-dependency order, not eager pixel wall-clock timing.
- [bundle_static_runtime_pipeline_linear_prophoto_stage_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_pipeline_linear_prophoto_stage_four_zoom.md)
  SHA-pinned installed-static plus direct x86_64 constructor/worker proof that index-15 `setToneMapping` is concretely conditional color-space materialization to a fixed `linear_prophoto_rgb`/D50 packet, not a nonlinear photographic look curve. The exact nine-float RGB-to-XYZ matrix, white point, selectors, and adaptation mode are pinned; matching linear-ProPhoto input takes the selected `0xab940` exact-copy path, preserving all four float lanes bit-for-bit. Existing Unit-1 `28/35/70/150mm` target sets supply wrapper liveness; unequal-source-config incidence remains open.
- [bundle_lldb_pipeline_slot15_branch_incidence_four_zoom_two_body.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_lldb_pipeline_slot15_branch_incidence_four_zoom_two_body.md)
  Follow-up exact branch-incidence proof for slot 15. Complete Unit-1 `28/35/70/150mm` renders execute 4,684 equal/copy branches and zero unequal conversions; complete Unit-2 `28mm` adds 1,476 equal copies and zero conversions. A low-perturbation Unit-2 `70mm` discriminator joins one exact equal-config sample to a separate completed mismatch-only render with zero Bayer/BayerFloat conversion hits. Generic unequal converters and body/firmware causation remain outside scope.
- `bundle_lldb_src1_virtual_target_family_static.md`
  Installed-bundle static proof classifying the visible bodies behind that capped lower target-family set. The inspected bodies bound to thunk / descriptor / region / materialization / cache / executor surfaces rather than proven reducer or final acceptance/rejection closure; indirect callable targets inside `0x342ca0` and `0x344470` remain outside this proof.
- `lldb_src1_indirect_callable_targets_four_zoom.md`
  LLDB runtime plus installed-bundle static proof resolving the two previously unclassified indirect callable targets inside `0x342ca0` and `0x344470` under the first visible-`src1` gate: across the canonical quartet, `0x342d99` binds `0x65b948/+0x30 = 0x342b80 -> 0x2eb560`, and `0x3449f0` binds `0x65c798/+0x30 = 0x345920 -> 0x2f53d0`.
- `lldb_2f53d0_downstream_helper_liveness_four_zoom.md`
  LLDB runtime plus installed-bundle static proof bounding the immediate `0x2f53d0` helper chain under the first visible-`src1` gate: `0xab590`, `0x2f4470`, `0x2f6420`, `0x135d0`, `0x3066d0`, and postbranch `0xab590` are live in capped windows across the canonical quartet, while `0x3048b0` has zero hits under accepted gated probes. Static inspection bounds the surface to descriptor/vector setup, bilateral-kernel dispatch, and executor dispatch; callback bodies are classified separately in the next entry.
- `lldb_2f53d0_callback_bodies_static.md`
  Installed-bundle static proof classifying the executor callback bodies under the already-live `0x2f53d0` helper chain as local descriptor transform, filtering, interpolation, normalization, and accumulation surfaces rather than semantic `src1` / `src2` reducer closure.
- `lldb_2f53d0_callback_arm_runtime_four_zoom.md`
  LLDB runtime proof that, under the first visible-`src1` `0x3e4b09` gate,
  complete accepted bridge HDR runs at `28mm`, `35mm`, `70mm`, and `150mm`
  select only the `0x2fb320` callback arm at `0x2f6420 -> 0x5440`; the
  hypothesis-relevant `0x2f78e0` arm and normalize sites `0x2f8584`,
  `0x2f859f`, and `0x2f85a5` have zero hits under that tested route.
- `lldb_2fb320_worker_runtime_four_zoom.md`
  LLDB runtime proof that the selected `0x2fb320` arm under the same first
  visible-`src1` gate is local descriptor / `vec4` coefficient work: callback
  fields `+0x08`, `+0x10`, and `+0x18` decode as readable same-shaped
  descriptor-like records, `+0x20` decodes as a `vec4` coefficient pointer, and
  the final sampled store writes approximate reciprocal-normalized `xmm4/xmm3`
  into destination memory across the canonical quartet.
- `bundle_proof_src1_region_adapter_helper_2e8680.md`
  Installed-bundle proof bounding helper `0x2e8680`, called by the selected `0x341770` visible-`src1` region-adapter body, to one-source Bayer/RAW region helper work with callback vtable `0x659fc0` and substantive slot `0x2e8cc0`; this is not reducer, C6-routing, final blend, or acceptance closure.
- `lldb_iramp_partner_gate_four_zoom.md`
  Installed-bundle plus repo-local LLDB proof bounding the local IRAMP partner-vector gate at `0x3692dc..0x3692e4`, the `0x280` partner-record stride, the empty-vector jump to the accumulator region, and first SAD participation at `0x3694b1`; non-empty gate and first SAD are runtime-observed on the canonical four-zoom quartet, while empty-gate runtime hits are observed only at `28mm` and `70mm`.
- `bundle_lldb_iramp_partner_record_population.md`
  Installed-bundle plus repo-local LLDB proof bounding the upstream partner-record append/population path: the first populated record path reaches `0x368b02` on the canonical four-zoom quartet, and the physical `0x280` record layout is four int32 scalar fields plus thirteen contiguous `0x30` descriptor-like blocks. Field semantics, complete candidate predicate, and final acceptance/rejection remain open.
- `bundle_lldb_iramp_refined_tuple_four_zoom.md`
  Installed-bundle plus repo-local LLDB proof bounding the live non-empty partner-record consumer path through coarse SIMD SAD / `phminposuw` winner selection, local absolute-difference refinement, guarded float refinement, 16x16 bilinear vec4 resampling, `0x36cde0`, and the three-float scratch write at `0x369e7e..0x369e91` across the canonical four-zoom quartet. Public field semantics and final acceptance/rejection remain open.
- `lldb_iramp_sentinel_gate_targets_four_zoom.md`
  LLDB runtime proof that the local IRAMP sentinel skip target `0x36931b` is reached with `eax == 0x80000000`, and the valid target `0x369320` is reached with non-sentinel `eax` values whose low table dword at `r12 + rsi * 8` matches `eax`, across capped samples on the canonical four-zoom bridge HDR quartet. This is branch-target evidence, not full candidate policy or final acceptance/rejection.
- `bundle_static_final_compositing_queue_drain.md`
  Installed-bundle static proof bounding the final-compositing queue/drain surface: `0x3bf820` builds a record with field values `0xd` and `2` and inserts it at owner `+0x260`, `0x3bfc40` priority-inserts `0x80` intrusive ring/list nodes with a 0x70-byte payload, `0x3c25a0` waits on the same count/stop state, `0x3bfe60` drains payloads into vector-like storage and deletes nodes, and `0x3bca90` filters 0x70-stride records before reaching ImagePyramid/Image accessor and per-tile virtual-dispatch surfaces. This refutes the RB-tree/std::list anchor for this surface, but is static only and does not prove copy-vs-blend, runtime liveness, final sink, or final acceptance/rejection.
- `lldb_final_compositing_queue_liveness_four_zoom.md`
  LLDB runtime proof that the narrowed final-compositing queue/drain surface is live across the canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge-HDR quartet: producer call-edge `0x3bf8bc -> 0x3bfc40`, insert body `0x3bfc40`, drain body `0x3bfe60`, orchestrator drain call-edge `0x3bcc51 -> 0x3bfe60`, and post-gather 0x70-stride filter loop `0x3bccc0` all hit with clean exits under `--no-auto-lris`. This proves liveness/operand shape only; it does not prove copy-vs-blend, final sink, final output semantics, anti-ghosting policy, or final acceptance/rejection.
- `lldb_final_compositing_switch_census_four_zoom.md`
  LLDB runtime proof censusing the `0x3bca90` post-gather switch under the canonical CLI bridge-HDR quartet. The observed record types / case targets are only `1`, `2`, `3`, `11`, and `16`; case `4` target `0x3bcf20`, containing the previously highlighted ImagePyramid/per-tile-dispatch branch, records zero hits under these tested runs. This is tested-path switch liveness/census only, not a universal zero-hit claim and not final output semantics.
- `lldb_final_compositing_case2_helper_four_zoom.md`
  LLDB runtime proof drilling into the live final-compositing case-`2` helper route across the canonical CLI bridge-HDR quartet. The case-`2` path reaches helper `0x3bf2f0`, the helper reaches callsites `0x3bf331`, `0x3bf344`, `0x3bf354`, and `0x3bf382`, and it records zero hits at alternate/helper callback/completion/error sites `0x3bf39a`, `0x3bf3be`, `0x3bf419`, `0x3bf481`, `0x3bf49a`, `0x3bf4c7`, `0x3bf50f`, and `0x3bf55a` under these tested runs. This is branch/callsite liveness only, not helper-body semantics or final output semantics.
- `lldb_final_compositing_case11_callback_four_zoom.md`
  LLDB runtime proof drilling into the live final-compositing case-`11` target across the canonical CLI bridge-HDR quartet. The case-`11` target and owner `+0x5d0` null test hit with the switch-census counts, but owner `+0x5d0` is zero in every captured sample, so callback callsite `0x3bd47b` and return site `0x3bd47d` record zero hits under these tested runs. This is tested-path gate behavior only, not global terminality or final output semantics.
- `lldb_final_compositing_case16_cleanup_four_zoom.md`
  LLDB runtime proof drilling into the live final-compositing case-`16` target across the canonical CLI bridge-HDR quartet. The case-`16` target, helper call `0x3bd2fe -> 0x3adad0`, and return site `0x3bd303` hit once per render; helper `0x3adad0` has four total invocations per render, every captured helper invocation reaches the raw local-count branch with `rbp-0x38 = 0`, and the callback/release/error sites record zero hits under these tested runs. This is tested-path cleanup behavior only, not global terminality or final output semantics.
- `lldb_final_compositing_case1_case3_boundary_four_zoom.md`
  LLDB runtime proof drilling into the remaining live final-compositing cases `1` and `3` across the canonical CLI bridge-HDR quartet. The case-`1` mutex / flag / condition-broadcast path hits once per render and changes the captured pointed flag byte from `0` to `1`; the case-`3` path passes `record+0x10`, `record+0x20`, `record+0x50`, `record+0x60`, and `record+0x68` into helper `0x4182a0`, whose selected normal callsites and normal return hit once per render while selected mismatch/error sites record zero hits. This is tested-path boundary/operand-custody proof only, not helper-body semantics or final output semantics.
- `lldb_final_output_hdr_writer_boundary_four_zoom.md`
  LLDB runtime proof that the tested CLI HDR path reaches helper `0x41e180`, follows the `.hdr` branch, calls writer helper `0x2326a0`, passes a populated `10432x7824` descriptor with row bytes `166912` and bytes-per-pixel field `16`, reaches virtual writer call `0x232731`, and emits files identified as `Radiance HDR image data` across the canonical four-zoom quartet. This is CLI HDR writer-boundary and descriptor-custody proof only, not pixel correctness, copy-vs-blend behavior, source contribution, acceptance/rejection, or non-CLI sink proof.
- `bundle_static_runtime_final_case3_output_config_four_zoom.md`
  Static plus reused runtime proof that the live final-compositing case-`3` path carries `10432x7824` dimensions and format argument `3` through `0x4182a0`, observes output color-space selector value `4`, bypasses the format-`2` compression subpath, and reaches the tested `.hdr` writer boundary with row bytes `166912` and bytes-per-pixel field `16`. This is output-configuration and writer-custody proof only, not public enum-name proof, pixel correctness, copy-vs-blend behavior, source contribution, acceptance/rejection, or non-CLI sink proof.
- `bundle_lldb_final_case3_to_hdr_writer_custody.md`
  Repo-local LLDB proof joining case-`3` `record+0x60` to the CLI HDR writer in the same render: Unit-1 `28mm`, `35mm`, `70mm`, and a narrowed positive-custody `150mm` run plus an exact-`28mm` Unit-2 discriminator carry `10432x7824` case-`3` dimensions through `0x4182a0 -> 0x41e180 -> 0x2326a0 -> 0x232731`; the writer descriptor has row bytes `166912`, bytes-per-pixel field `16`, and the virtual-writer data pointer matches the helper descriptor data pointer. Full normal/error-path scope is admitted for Unit-1 `28mm`/`35mm`/`70mm` and Unit-2 exact `28mm`; Unit-1 `150mm` is positive-custody only. This is same-render final-sink custody proof, not pixel correctness, source contribution, copy-vs-blend behavior, acceptance/rejection, or non-CLI sink proof.
- `bundle_lldb_iramp_36cde0_scalar.md`
  Installed-bundle plus repo-local LLDB proof narrowing the third refined-tuple field: `0x36cde0` consumes the two prepared 16x16 `vec4` patches, runs patch-statistics / fixed-transform / weighted-reduction work, returns `sqrt(xmm0 * xmm1)`, and the caller stores that live `xmm0` scalar as the tuple's third float at `0x369e91`. Public field semantics remain open; the first downstream tuple consumer is covered by `bundle_lldb_iramp_tuple_downstream_consumer.md`.
- `lldb_iramp_w5_magnitude_repro_four_zoom.md`
  Codex-owned LLDB reproduction of the W5 magnitude method: core-handled ignore-count / conditional breakpoints capture representative nonzero `0x36e511 -> 0x36e515` score arithmetic and non-common `0x36a938` reciprocal denominators across the canonical four-zoom quartet. This admits the runtime arithmetic and representative non-degenerate magnitudes, not Opus's exact sample rows as constants and not full reducer closure.
- `bundle_lldb_iramp_36e530_accumulator_prep.md`
  Installed-bundle plus repo-local LLDB proof bounding the immediate accumulator-prep call: `0x36e530` receives `rbp-0x4240`, performs reciprocal/selector normalization plus fixed SIMD transform/reduction work, returns `scratch+0x1580` in `rax` on the canonical four-zoom bridge HDR quartet, and the accumulator consumes that source block with a 16-by-16 outer product of captured scalar weights. Public weight semantics and final acceptance/rejection remain open.
- `bundle_lldb_iramp_tuple_downstream_consumer.md`
  Installed-bundle plus repo-local LLDB proof bounding the first downstream consumer of the refined three-float tuple: the consumer reads the third scalar at `0x36a7d8`, reads the first two tuple floats at `0x36a803` / `0x36a814`, passes the adjusted coordinate pair to `0x372a00`, forms multiplier `(t + 2 * max(0, t - 0.5), t, t, t)`, and reaches the downstream multiply-add loop at `0x36a8c0..0x36a8cb` across the canonical four-zoom bridge HDR quartet. Complete downstream policy and final acceptance/rejection remain open.
- `bundle_lldb_iramp_tuple_post_reciprocal_weighted_add.md`
  Installed-bundle plus repo-local LLDB proof bounding the immediate post-reciprocal path after the first downstream tuple consumer: `0x19e7d0` copies/scales descriptor-backed `vec4` buffers by the reciprocal vector, and `0x36aa30..0x36aa57` blends `reciprocal * 0.2` into lane 3, applies a separable weight-table product, adds into the destination vector, and is reached by the canonical four-zoom bridge HDR quartet. Later downstream policy and final acceptance/rejection remain open.
- `bundle_lldb_iramp_post_weighted_add_shaping.md`
  Installed-bundle plus repo-local LLDB proof bounding the immediate shaping stages after the post-reciprocal weighted add: `0x36abf0..0x36ac15` applies a lane-3-weighted clamped vector update, and `0x36ad50..0x36adac` applies a fixed 3-vector transform with lane 3 forced to `1.0`; both sites are reached by the canonical four-zoom bridge HDR quartet. Later downstream policy and final acceptance/rejection remain open.
- `bundle_lldb_iramp_caller_square_copy.md`
  Installed-bundle plus repo-local LLDB proof bounding the caller-side handoff after IRAMP returns: the caller validates the IRAMP-return descriptor dimensions against ROI, wraps the `rbp-0x60` descriptor at `rbp-0x88`, calls helper `0xd76a0`, and static helper inspection shows destination allocation followed by source `vec4` lane squaring into the destination; the handoff is reached by the canonical four-zoom bridge HDR quartet. Later downstream policy and final acceptance/rejection remain open.
- `bundle_lldb_iramp_caller_post_square_scale.md`
  Installed-bundle plus repo-local LLDB proof bounding the caller-side vector-scale handoff after the square-copy helper: the caller builds a wrapper over the `rbp-0x70` descriptor with a vector at wrapper `+0x10`, calls helper `0x2d7320`, and static helper inspection shows source `vec4` lanes are multiplied by that vector into the destination; the handoff is reached by the canonical four-zoom bridge HDR quartet. Later downstream policy and final acceptance/rejection remain open.
- `bundle_lldb_iramp_caller_3e5720_executor_setup.md`
  Installed-bundle plus repo-local LLDB proof bounding the `0x3e5720` executor setup after caller-side vector scaling: the surface allocates a 6-byte-element destination descriptor, builds callback vtable `0x66b020`, dispatches generic executor `0x5670`, and its visible worker maps source 16-byte `vec4` rows to destination 6-byte rows before calling row callback `0x38a30`; the setup is reached by the canonical four-zoom bridge HDR quartet. Row callback conversion is covered by `bundle_lldb_iramp_row_callback_38a30_conversion.md`; final acceptance/rejection remains open.
- `bundle_lldb_iramp_row_callback_38a30_conversion.md`
  Installed-bundle plus repo-local LLDB proof bounding the row callback behind callback auxiliary first qword `0x38a30`: on the canonical four-zoom bridge HDR quartet, `0x38a30` repacks source `vec4` lanes 0..2 into float triples and calls `0xbfef0` with `ecx = 0`, whose used branch converts float channels to 16-bit binary16 bit patterns; first captured callback rows at all four zooms match the static conversion formula. Public pixel-format names, later downstream policy, and final acceptance/rejection remain open.
- `bundle_lldb_iramp_caller_output_descriptor_sink.md`
  Installed-bundle plus repo-local LLDB proof bounding the immediate caller-side storage sink for the `0x3e5720` conversion output: body `0x3ec960` is vtable slot `0x65f5e0+0x30`, computes destination descriptor `(*rsi)+0xf0`, allocates/resizes it with element size `6`, passes it to `0x3e5720`, then destroys only the temporary descriptor and returns; runtime packets across the canonical four-zoom quartet show the owner-backed descriptor populated as `512x512`, stride `512`. Later consumers, public pixel-format names, and final acceptance/rejection remain open.
- `bundle_proof_owner_f0_constructor_install_four_zoom.md`
  Installed-bundle plus repo-local LLDB proof bounding the constructor-side custody edge into that owner `+0xf0` sink family: `0x3ea980` is a direct `0x3d0120` caller, the installed stack callable address point is `0x65f5e0`, table slot `0x65f5e0+0x30` is `0x3ec960`, and complete canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR runs prove the address point is installed into target inline callable storage before the already-bounded owner `+0xf0` sink body is reached. This is custody proof only; semantic `src1` / `src2` contents, owner-field semantics, final output, and final acceptance/rejection remain open.
- `bundle_lldb_owner_f0_downstream_consumer.md`
  Installed-bundle plus repo-local LLDB proof bounding the first proven downstream consumer family for owner `+0xf0`: `0x3d50f0` allocates a `16`-byte-element destination, dispatches executor `0x5670` with row worker `0x3d5290`, and the selected converter path reaches `0x2ff00 -> 0xc0410`; runtime packets across the canonical four-zoom quartet show live `rsi` at `0xc0410` inside the exact owner `+0xf0` data range with `ecx/cl = 0`. Final output semantics, public pixel-format names, later consumers, and final acceptance/rejection remain open.
- `bundle_lldb_owner_f0_expansion_handoff.md`
  Installed-bundle plus repo-local LLDB proof bounding the immediate handoff after the first proven owner `+0xf0` downstream expansion family: `0x3d4e10` calls `0x3d50f0`, and runtime packets at `0x3d502e` across the canonical four-zoom quartet show the local source descriptor at `rbp-0x60` points inside the exact owner `+0xf0` data range while the local expanded descriptor at `rbp-0x90` has `16`-byte elements and a first `vec4` sample with lane 3 = `1.0`. Later consumers, public pixel-format names, final output semantics, and final acceptance/rejection remain open.
- `bundle_lldb_owner_f0_expansion_dest_context.md`
  Installed-bundle plus repo-local LLDB proof bounding the destination backing store for that handoff: `0x3d4e10` receives a caller-provided context whose `+0x10` field points to the persistent 16-byte destination descriptor, and runtime packets across the canonical four-zoom quartet show local destination descriptor `rbp-0x90` is a clipped view into that context descriptor with matching `qword_28`, in-range data pointer, and 16-byte alignment. The first selected-cache route after this context is covered by `bundle_lldb_owner_f0_read_context_route.md`; public pixel-format names, final output semantics, and final acceptance/rejection remain open.
- `bundle_lldb_owner_f0_read_context_route.md`
  Installed-bundle plus repo-local LLDB proof bounding the first captured route after the owner `+0xf0` expansion destination context: the accepted route uses active callable branch `0x3d4842`, active callable slot `0x3ec960`, parent `0x3d01b0` output descriptor `rbp-0x148` as `context+0x10`, caller return `0x3d084d`, and the same temporary descriptor passed to `0x36f800` at `0x3d08ce` across the canonical four-zoom quartet. Weighted-store and helper-store details are covered separately by the owner `+0xf0` resample evidence docs; broader branch-site caller/slot families are covered by `bundle_lldb_owner_f0_global_route_census.md`, while public offset/scale/pixel-format names, final output semantics, and final acceptance/rejection remain open.
- `bundle_lldb_owner_f0_route_census.md`
  Installed-bundle plus repo-local LLDB proof extending the first-route evidence into a first-owner census: for the first captured owner `+0xf0` descriptor, `28mm`, `70mm`, and `150mm` also hit sibling direct branch `0x3d4864`, while `35mm` hit only `0x3d4842`; every accepted owner-matching packet still uses slot `0x3ec960`, returns to caller `0x3d084d`, and preserves the parent/context destination equality checks. This refutes "`0x3d4842` only" generalizations; direct-branch post-route proof is covered separately.
- `bundle_lldb_owner_f0_direct_branch_post_route.md`
  Installed-bundle plus repo-local LLDB proof following the first owner-matching direct branch to its immediate selected-cache post-route handoff: at `28mm`, `70mm`, and `150mm`, the first direct branch reaches `0x3d08ce -> 0x36f800` with `rsi` equal to the same temporary descriptor captured as `context+0x10`; `35mm` has no owner-matching direct branch under this first-owner probe. This proves the first direct-branch post-route only; broader branch-site caller/slot families are covered by `bundle_lldb_owner_f0_global_route_census.md`, while public field names, final output semantics, and final acceptance/rejection remain open.
- `bundle_lldb_owner_f0_global_route_census.md`
  Installed-bundle plus repo-local LLDB proof removing the first-owner gate and counting every hit at read-context branch sites `0x3d4842` and `0x3d4864` across complete canonical bridge HDR renders. All four runs exited `0`; all hits preserved the parent/context destination equality checks; every hit fell into caller set `{0x3d0732, 0x3d084d, 0x3ecc5a}` and active callable slot set `{0x3ec960, 0x3e4a80}`. Immediate post-route classification is covered by `bundle_lldb_owner_f0_global_post_route_families.md`; final acceptance/rejection remains open.
- `bundle_lldb_owner_f0_global_post_route_families.md`
  Installed-bundle plus repo-local LLDB proof classifying the immediate post-route behavior for the three global read-context caller families across the canonical quartet: `0x3d0732` is exact-size cleanup with no post call, `0x3d084d` reaches `0x3d08ce -> 0x36f800`, and `0x3ecc5a` reaches `0x3ecc74 -> 0x3edb80` visible-`src1` one-image normalization. This bounds immediate post-route family shape, but not final acceptance/rejection.
- `bundle_lldb_owner_f0_global_route_ancestry.md`
  Installed-bundle plus repo-local LLDB proof adding full-render parent-chain counts for the global read-context branch-site families. Across the canonical quartet, all hits still preserve the parent/context equality checks and caller/slot sets; `0x3d0732` returns through `0x3b07a9 -> 0x41a8d3 -> 0x3adfce -> 0x280e`, `0x3d084d` returns through `0x3bb822 -> 0x3adfce -> 0x280e`, and `0x3ecc5a` returns through `0x374cf3 -> 0x3665da -> 0x365f50 -> 0x3ec7df -> 0x3eca4b -> 0x3d4842` with some nested read-context continuations. Exact hot direct-branch hit totals are evidence-run counts, not algorithm constants; final acceptance/rejection remains open.
- `bundle_lldb_owner_f0_parent_chain_static_classification.md`
  Installed-bundle static LLDB proof classifying those runtime-proven parent-chain bodies. It separates callback/iteration glue (`0x280e`, `0x3adfce`) from selected owner-cache/direct-render tile surfaces (`0x3b0740`, `0x41a7d0`, `0x3b9770`, `0xfbda0`, `0x3bb2b0`) and visible-`src1` / IRAMP nested wrapper plus owner `+0xf0` sink surfaces (`0x374ac0`, `0x3661b0`, `0x365960`, `0x3ec770`, `0x3ec960`). Public semantic names, final file/display sink, and final acceptance/rejection remain open.
- `bundle_lldb_owner_f0_helper_surface_static_classification.md`
  Installed-bundle static LLDB proof classifying helper surfaces exposed by the owner `+0xf0` parent-chain route. It bounds `0x31b110` as source/RAW/STD adapter into `0x33fb30`, `0xfe720` as a 16-byte rectangle/ROI record-grid helper, `0x106cb0` as vignetting-data construction/interpolation, `0x2e20` as callback dispatch, and `0xf3570`, `0x3b9660`, `0x3c6ac0`, `0x1bea20`, `0x1bea00`, and `0x1be970` as owner/tile/map/field helper surfaces. Final file/display sink, downstream row-image/final policy, and final acceptance/rejection remain open.
- `bundle_lldb_owner_f0_selected_cache_route_static_classification.md`
  Installed-bundle static LLDB proof classifying selected-cache/post-route bodies exposed by the owner `+0xf0` route. It bounds `0x3d01b0` as level/ROI tile-read executor, `0x3d0650` as exact-size read or read-then-`0x36f800` rescale, `0x3d47d0` as read-context branch router, `0x3d4e10` / `0x3d50f0` / `0x3d5290` / `0x2ff00` / `0xc0410` as 6-byte-to-vec4 expansion and 16-bit-to-float conversion plumbing, and `0x3edb80` as one-image `sqrt(max())` normalization. Final file/display sink, public pixel-format names, downstream row-image/final policy, and final acceptance/rejection remain open.
- `bundle_lldb_downstream_route_caller_census_static.md`
  Installed-bundle static LLDB plus repo-local callgraph proof bounding direct callers of selected downstream route helpers. It shows `0x36f800` direct callers are selected-cache read/rescale, TileCache-like read/rescale, and IRAMP-internal resample handoff; `0x3d01b0` direct callers are selected-cache reads, visible-`src1` read, source-adapter caller, and DOFCache render caller; `0x3edb80` direct callers are visible-`src1` and visible-`src2` one-image normalization wrappers; and `0x3d50f0` has only the already classified `0x3d4e10` direct caller. This covers direct-callgraph edges only; indirect/vtable callers, final file/display sink, downstream row-image/final policy, and final acceptance/rejection remain open.
- `bundle_lldb_selected_cache_caller_census_static.md`
  Installed-bundle static LLDB plus repo-local callgraph proof bounding direct callers of selected-cache read/rescale body `0x3d0650`. The 14 direct callers fall into source-adapter-style caller windows, small owner-cache selector `0x3b0740`, multi-branch owner/tile-cache surface `0x3bb2b0`, owner `+0xf0` output-sink branch body `0x3ec960`, and later helper/adaptor caller surfaces around `0x42fb40` and `0x42fd30`. This covers direct-callgraph edges only; runtime liveness for every static caller, indirect/vtable callers, final file/display sink, downstream row-image/final policy, and final acceptance/rejection remain open.
- `bundle_lldb_3e5720_caller_census_static.md`
  Installed-bundle static LLDB plus repo-local callgraph proof bounding direct callers of row-conversion executor setup `0x3e5720`. The direct callers are active-callable-slot / owner `+0xf0` writer body `0x3e4a80`, owner `+0xf0` output-sink body `0x3ec960`, and DOFCache render body `0x3f0b90`; ancillary `0x432db0` coverage bounds the later `0x42fb40 -> 0x3d0650 -> 0x432db0` selected-cache caller surface. This covers direct-callgraph edges only; runtime liveness for every static caller, final file/display sink, downstream row-image/final policy, and final acceptance/rejection remain open.
- `bundle_lldb_3d4e10_caller_census_static.md`
  Installed-bundle static LLDB plus repo-local callgraph proof bounding direct callers of owner `+0xf0` expansion handoff `0x3d4e10`. The direct callers are the two already bounded branch-router post-branch handoffs at `0x3d484a` and `0x3d486c`, plus separate indexed-entry loop caller `0x3d5468` inside body `0x3d5400`; `0x3d50f0` has only direct caller `0x3d5029` inside `0x3d4e10`, and `0x3d5290` has no direct callers because it is worker-dispatch plumbing. This covers direct-callgraph edges only; the separate loop caller's executor route and first-hit liveness are covered by `bundle_lldb_3d5400_executor_vtable_liveness.md`.
- `bundle_lldb_3d5400_executor_vtable_liveness.md`
  Installed-bundle static LLDB plus repo-local runtime first-hit proof bounding the `0x66a728 -> 0x3d53c0 -> 0x3d5400 -> 0x3d5468 -> 0x3d4e10` executor route. Static proof shows `0x3d01b0` builds the `0x66a728` callback object and dispatches `0x5670`; runtime first-hit probes across `28mm`, `35mm`, `70mm`, and `150mm` show `0x3d0408`, `0x3d042b`, `0x3d53c0`, and first `0x3d5468` liveness with callback-object vtable module VA `0x66a728`. This proves first-hit liveness only; full-render counts, public semantic names, final file/display sink, downstream row-image/final policy, and final acceptance/rejection remain open.
- `bundle_lldb_owner_f0_resample_36f800.md`
  Installed-bundle plus repo-local LLDB proof bounding the first proven `0x36f800` worker path after the owner `+0xf0` selected-cache route: the gated route starts at owner `+0xf0`, reaches `0x3d08ce -> 0x36f800`, dispatches through callback vtable slot `0x3721d0` into static worker body `0x372210`, reaches after-prologue worker-entry probe `0x372224`, and the first captured store at `0x372488` writes a destination `vec4` equal to the four captured source `vec4`s times the four captured weight `vec4`s across the canonical four-zoom quartet. Row-plan/cache helper details are covered separately; public field names, final output semantics, and final acceptance/rejection remain open.
- `bundle_lldb_owner_f0_resample_helpers_372500_372760.md`
  Installed-bundle plus repo-local LLDB proof bounding row-plan/cache helper activity inside the same gated owner `+0xf0` route: `0x372210` converts offset/scale doubles to signed 16.16 fixed-point with `65536.0`, `0x372500` builds a row-plan struct with source descriptor, fixed scales, x start/end/clamp fields, and weight-table pointer, captured `0x372760` row-cache stores match the reconstructed 4-tap horizontal `vec4` formula across the canonical four-zoom quartet, and fresh first-dispatch row-plan packets capture all four unique worker regions per zoom with only the middle row-cache segment predicted/live in that dispatch. Full-render leading/trailing reachability is covered by `bundle_lldb_owner_f0_global_rowcache_segments.md`; alternate routes, public field names, final output semantics, and final acceptance/rejection remain open.
- `bundle_static_runtime_resample_64_phase_exact_formula.md`
  SHA-pinned installed-body plus complete runtime-table proof closing `libcp+0x36f800` as a 64-phase separable Catmull-Rom four-tap resampler. The instruction-ordered 4096-byte table is reproduced exactly, the selected-cache caller's offset/scale derivation is decoded, and prior four-focal worker/store evidence supplies canonical mechanism coverage.
- `bundle_static_runtime_final_rgbe_writer_exact_formula.md`
  Installed-body plus live first-row replay closing the canonical float32 RGB to Radiance RGBE byte formula, header, top-down orientation, and legacy flat body. Existing four-focal/Unit-2 custody supplies route coverage; the parent output claim remains partial because the emitted file does not self-tag its already proved linear ProPhoto primaries.
- `bundle_runtime_reference_self_repeat_distributions_four_zoom.md`
  Forty complete full-resolution renders and 180 pairwise comparisons establish focal-specific final-output repeat distributions for the canonical quartet, refute the old unqualified `~0.034 counts` floor, and define empirical linear-RGB ambiguity envelopes without promoting them to algorithm constants.
- `bundle_static_runtime_correction_liveness_public_schema_four_zoom.md`
  SHA-pinned embedded-schema extraction plus four-focal completed-render census proving live pixel-domain vignetting, live IR-model/configuration surfaces, exact public crosstalk/vignetting names, and the common `17x13` matrix/profile grid shapes. Its old cross-talk slot-`+0x38` zero-hit conclusion is superseded by the corrective bundle below.
- `bundle_corrective_runtime_crosstalk_callback_liveness_two_body_four_zoom.md`
  Corrective installed-slot and complete-runtime proof showing generic executor `0x2e20` calls vtable slot `+0x30`, not the previously watched `+0x38`; Unit-1 four-focal and exact-`70mm` Unit-2 renders execute scalar-true callback `0x1054d0`, and 240/240 captured stage-6 inputs share its stage-5 output allocation. This reopens exact scalar cross-talk arithmetic while retaining prior vignetting closure.
- `bundle_static_runtime_crosstalk_exact_formula_two_body.md`
  SHA-pinned installed/public proof closing the selected scalar-true path: public `FactoryModuleCalibration.camera_id` selects the byte-identical `17x13` 4x4 matrix grid, public RAW and installed A/B/C tables select the generated IR grid, public AWB prepares worker matrices, and exact coordinate/Bayer-neighbor/boundary/limiter/blend replay matches `67,600/67,600` output words on each exact-`28mm` body. A Unit-1 movable B2 packet supplies a camera-group/public-ID discriminator; companion complete renders supply four-focal liveness and demosaic custody.
- `bundle_static_runtime_crosstalk_selector_public_origins_two_body.md`
  SHA-pinned schema/static/runtime join naming every selected A/B/C-table input: public `LightHeader.sensor_data.type=SENSOR_AR1335(2)`, public `ColorCalibration.color_matrix` presence as the variant predicate, public camera-ID group, and the admitted public-AWB/A-D65 scene chromaticity converted by installed `0xab2e0` to the exact CCT received by the fit. Exact selector packets cover distinct-calibration exact-`28mm` inputs from both physical bodies plus Unit-1 movable B2.
- `bundle_runtime_x86_rcpss_rcpps_exact_emulation.md`
  Exhaustive current-Rosetta runtime proof of an integer-only portable `rcpss`/lane-wise `rcpps` bit formula. The top 11 input-fraction bits select 2,048 midpoint-reciprocal bins, the low 12 bits are ignored, and explicit special-value rules reproduce `6,242,316/6,242,316` scalar and packed-lane oracle cases. This removes exact-division as a necessary clean-room substitute while retaining current-reference-platform scope.
- `bundle_lldb_owner_f0_global_rowcache_segments.md`
  Installed-bundle plus repo-local LLDB proof removing the first-dispatch boundary for `0x372760` row-cache segments. Complete canonical bridge HDR renders show row-plan return `0x3722b0` live at all four zooms; leading/trailing store sites are live at `28mm` and `70mm`, and have zero hits at `35mm` and `150mm` under the tested canonical runs. First captured leading/trailing samples at `28mm` and `70mm` match the reconstructed 4-tap horizontal `vec4` formula. Public field names, downstream row-image/final policy, and final acceptance/rejection remain open.
- `bundle_proof_pair_grid_roi_transform.md`
  Installed-bundle proof that IRAMP's first pair grid is ROI-derived, that a second same-sized transformed pair grid is produced from it, and that the transformed-grid bbox feeds the later clipping / zero-fill helper path.
- `bundle_static_runtime_distortion_table_exact_formula_two_body.md`
  SHA-pinned static plus exact-focal two-body/four-zoom public-carrier proof closing the five-coefficient Brown-Conrady order `[k1,k2,p1,p2,k3]`, public `CRA.pixel_size` radius scale, 30 correction samples, four-point cubic Lagrange interpolation, complete 4096-entry table, projection-consumer indexing, and path-scoped `valid_roi` exclusion. Complete Unit-1 A1 and Unit-2 B4 runtime tables replay byte for byte from their different public calibration payloads.
- `bundle_proof_iramp_live_signature_and_warp_records.md`
  Installed-bundle proof tying `PipelineCache+0x258` to IRAMP's live paired record / warpfield-vector argument and to the transformed pair-grid consumer path.
- `bundle_proof_iramp_pair_grid_transform_formula.md`
  Installed-bundle proof of the consumer-side second-grid transform formula over the live `0x50` records.
- `bundle_proof_iramp_record_producer_scale_and_dispatch.md`
  Installed-bundle proof bounding the producer-side record dispatcher, row/map writer split, reciprocal scale helpers, and final `PipelineCache+0x258` scale-field normalization.
- `bundle_proof_iramp_row_composition_matrix_chain.md`
  Installed-bundle proof that `0x25ec70` is 4x4 double matrix multiply and that `0x25e0c0` writes row fields through a structured matrix chain.
- `bundle_proof_iramp_9db20_matrix_inverse.md`
  Installed-bundle proof that `0x9db20` copies one 4x4 double matrix and inverts it through the in-place inverse body at `0x9db80`.
- `bundle_proof_iramp_source_record_constructors.md`
  Installed-bundle proof bounding the IRAMP producer source-record constructors and `0x268480` map-provider path.
- `bundle_proof_iramp_23faf0_composition_helper.md`
  Installed-bundle proof bounding `0x23faf0` as source-record composition, `0x264980` as a two-axis field-shift helper, and `0x264460` as a positive two-axis scale helper.
- `bundle_proof_iramp_calib_object_accessors.md`
  Installed-bundle proof bounding `state+0xe0` object lookup plus the `0xf34e0`, `0xf3350`, and `0xf3360` object accessors used by IRAMP source-record construction.
- `bundle_proof_iramp_state_448_tree_builder.md`
  Installed-bundle proof bounding the `state+0x448` tree/control-object initialization, first visible insertion gate, keyed insert/find helper, and first payload-field copies.
- `bundle_proof_iramp_state_448_later_payload_writes.md`
  Installed-bundle proof bounding later direct writes to found `state+0x448` payload fields through `+0x80`, while excluding nearby stack-only and separate-record helper calls.
- `lldb_iramp_map_provider_four_zoom.md`
  LLDB runtime plus installed-bundle static proof binding the tracked post-wrapper `0x3f7040` map-provider path across the canonical quartet: all accepted tracked entries take `0x3f72f0`, `0x268480` calls the `UpsampleLayer` vtable address point `0x658eb0` slot `+0x90 = 0x26b590`, `0x26b590` returns `UpsampleLayer+0x90`, and that return is written into the composed record at `record+0x40`. Public map semantics and LRI calibration origin remain open.
- `lldb_upsample_map_custody.md`
  LLDB runtime plus installed-bundle static proof for `UpsampleLayer+0x90` descriptor custody: accepted `28mm`, `35mm`, and `70mm` runs prove `0x26ac13 -> 0xf340` copies the populated descriptor into `UpsampleLayer+0x90` before the same descriptor is returned by `0x268480` and stored at `record+0x40`; accepted `150mm` runtime proves the same provider/storage descriptor boundary without writer-body instrumentation. Public calibration semantics and LRI origin remain open.
- `lldb_upsample_layer_depth_path.md`
  LLDB runtime plus installed-bundle static proof for the `UpsampleLayer+0x90` depth-path builder: accepted `28mm`, `35mm`, `70mm`, and `150mm` runs prove `0x26aa10 -> 0x29ed90 -> 0x2673a0 -> 0x26ac13` turns a previous-layer `+0x90` `2080 x 1560` descriptor into the `4160 x 3120` `UpsampleLayer+0x90` descriptor, and installed debug strings label that descriptor as `depth_... .dp`. Public LRI origin and public semantic names remain open.
- `lldb_upsample_29ed90_worker_formula.md`
  LLDB runtime plus installed-bundle static proof for the `0x29ed90` callback worker: accepted `28mm`, `35mm`, `70mm`, and `150mm` runs prove callback vtable slot `0x668288/+0x30 = 0x29f5c0`, worker body `0x29f600`, output float store `0x29f9de`, the runtime payload layout, the `[1.0, 1/3]` coefficient table, scale `1/288`, and the static guided 2x upsample arithmetic. Public LRI origin and public semantic names remain open.
- `lldb_stereolayer_index5_depth_descriptor_custody.md`
  LLDB runtime plus installed-bundle static proof for the previous-layer descriptor consumed by the `0x29ed90` depth upsample path: across the canonical quartet, `0x26aa30` calls previous-layer slot `+0x90`, which returns `StereoLayer<false>` index-5 descriptor `this+0x2a8`, shaped `2080 x 1560`, stride `2080`; runtime watchpoints bind initial population through `0x26c518 <- 0x26bdf8 <- 0x26895a <- 0x2687ab` and later overwrite through `0x26e64f <- 0x26dddc <- 0x268967 <- 0x2687ab`. Public LRI origin and public semantic name remain open.
- `lldb_lris_boundary_and_28mm_no_lris_depth_custody.md`
  LLDB runtime proof that the canonical `28mm` index-5 depth descriptor custody path is not dependent on auto-loading the same-name `L16_02130.lris` sidecar: with `--no-auto-lris`, the constructor counts, index-5 size/source-vector shape, `0x26aa30` handoff, returned `2080 x 1560` descriptor, and initial-fill/later-overwrite stacks match the prior 28mm custody evidence. Public LRI origin and public semantic name remain open.
- `lldb_index5_origin_classification_four_zoom.md`
  LLDB runtime plus installed-bundle static proof classifying the later `StereoLayer<false>+0x2a8` overwrite feeding the `0x29ed90` guided-upsample path: under `--no-auto-lris`, the canonical quartet reaches `0x26dd40 -> 0x26e120 -> 0x267010 -> 0x26e64a -> 0xf340` for six `StereoLayer<false>` objects with indices `0..5`; index `5` is the full `2080 x 1560` descriptor returned through slot `+0x90`, and static `0x267010` builds a new 4-byte descriptor from source descriptor dimensions, 16-bit source entries, and `this+0xe0` lookup/vector state before the move into `+0x2a8`. Public physical meaning and LRI/protobuf origin remain open.
- `lldb_index5_267010_mapping_four_zoom.md`
  LLDB runtime proof for sampled `0x267010` mapping behavior: under `--no-auto-lris`, the canonical quartet reaches six `StereoLayer<false>` indices `0..5`; for each captured index, the first 16 sampled source entries are read as `uint16` indices into the `rdx` float lookup vector, and every sampled `lookup[source_u16]` value exactly matches the corresponding float in the built stack descriptor after `0x267010` returns at `0x26e638`. This proof alone did not close public physical meaning, public LRI/protobuf origin, immediate producer/custody, full-map statistics, or final merge effect.
- `lldb_source_index_299c70_producer_four_zoom.md`
  LLDB runtime plus static proof for the immediate upstream source-index
  descriptor producer feeding `0x267010`: under `--no-auto-lris`, the canonical
  quartet reaches `0x26e4c6 -> 0x299c70` for six `StereoLayer<false>` indices
  `0..5`; `0x299c70` receives `this+0xf8`, builds the 2-byte descriptor at
  caller `rbp-0xe0`, the descriptor is moved into caller `rbp-0x80`, and that
  moved descriptor is passed unchanged to `0x267010`, while the lookup-vector
  argument is `this+0xe0`. Public field names, LRI/protobuf origin, physical
  meaning, and final merge effect remain open.
- `lldb_source_index_299c70_worker_formula_four_zoom.md`
  LLDB runtime plus static proof for the sampled internal source-index callback
  worker formula feeding the `0x267010` source descriptor: static extraction
  binds callback address point `0x6680f0` through generic executor `0x5440`
  slot `+0x30` to worker `0x29a670`; accepted no-auto-LRIS four-zoom runs
  validate six dispatches and six sampled worker tiles per focal tier, with
  `192/192` sampled post-write `uint16` values matching the source-record
  min-cost formula. Public field names, LRI/protobuf origin, lookup-vector
  origin, physical meaning, full-map statistics, and final merge effect remain
  open.
- `lldb_26d750_source_range_builder_four_zoom.md`
  LLDB runtime proof for the immediate upstream source-range builder feeding
  the tracked index-5 source-local object: canonical Unit-1 four-zoom runs plus
  a Unit-2 exact-28mm spot check validate that `0x26bd90 -> 0x26d750` receives
  `source_layer+0x2a8`, `source_layer+0x208`, target min/max fields, and mode
  `8`; `0x26d750` emits a `2080 x 1560`, stride-`2080`, 4-byte descriptor of
  `(lower,count)` `uint16` pairs from half-resolution lower/upper range tables;
  and that descriptor is passed unchanged as `rsi` to `0x29a140`. This closes
  internal source-index descriptor range semantics only, not public
  LRI/protobuf field names, source-record public names, public units, final
  contribution, or acceptance/rejection.
- `lldb_index5_source_lookup_origin_watch_four_zoom.md`
  LLDB runtime watchpoint proof for internal construction/custody of the same
  tracked index-5 source/lookup inputs: under `--no-auto-lris`, the canonical
  quartet populates `StereoLayer<false>+0xe0` through the `0xf02d0` path with
  final observed write at `0xf043e`, writes `StereoLayer<false>+0xf8` control
  state at `0x26be62`, and later passes the populated same object into
  `0x26e4c6`, `0x299c70`, and `0x267010` with source dimensions
  `2080 x 1560`, stride `2080`. Public origin, physical meaning, full-map
  statistics, and final merge effect remain open.
- `lldb_index5_lookup_vector_public_origin_four_zoom.md`
  LLDB runtime/static verifier for the tracked index-5
  `StereoLayer<false>+0xe0` lookup vector. It proves `0x26c480` builds a stack
  vector through `0x28fa60` / `0x28f5a0` / `0x28f860`, copies it into
  `this+0xe0` through `0xf02d0`, and later reaches `0x267010` unchanged.
  Runtime packets retain object fields `this+0x298/+0x29c = [200.0, 640000.0]`
  and exact float32 reciprocal near/far ramps with counts `752` at `28mm` /
  `35mm` and `1472` at `70mm` / `150mm`. The verifier finds zero full-vector
  LRI block hits, zero full calibration fixed32-sequence hits, and zero scalar
  calibration fixed32 hits for the vector. The endpoint/count mechanics are
  closed by the next entry, and the separate Triangulator depth-bound custody
  entry admits the internal reciprocal ray-depth hypothesis-grid role; public
  source-index names / physical semantics, source-record public names, public
  units and public calibration/LRI/protobuf names, and final merge effect
  remain open.
- `lldb_lookup_endpoint_count_origin_four_zoom.md`
  LLDB runtime/static verifier for the endpoint and count producer mechanics of
  that generated index-5 lookup vector. It proves the selected canonical
  endpoint pair `[200.0, 640000.0]` comes from the first row of static binary
  float tables at `0x609428` / `0x609430`, is propagated through
  `0x3ff43c -> 0x2681b0 -> 0x26ba90`, and is stored in
  `this+0x298/+0x29c`. It also proves `0x28f5a0` computes the lookup count from
  five `0xa8` source records in `this+0x258`, `this+0x18`, first-record scalar,
  endpoint reciprocal span, clamp `0x1000`, and mode rounding by `this+0xc=8`,
  reproducing counts `752` at `28mm` / `35mm` and `1472` at `70mm` / `150mm`.
  By itself this does not prove public units/naming, source-index descriptor
  semantics, source-record public names, or final merge effect; the separate
  Triangulator depth-bound custody entry admits the internal reciprocal
  ray-depth hypothesis-grid role.
- `lldb_index5_source_object_field_origin_four_zoom.md`
  LLDB runtime/static proof for the immediate internal field assembly of the
  tracked index-5 `StereoLayer<false>+0xf8` source object: under
  `--no-auto-lris`, the canonical quartet validates `0x29a140` stack-local
  production, `0x26be5b` control write `2 -> 8`, `0x28f420` header move into
  `this+0x100`, `0xf340` descriptor move into `this+0x118`, descriptor
  dimensions `2080 x 1560`, stride `2080`, and later continuity into
  `0x26e4c6`, `0x299c70`, and `0x267010`. Public origin, physical meaning,
  full-map statistics, and final merge effect remain open.
- `lldb_29a140_source_local_producer_four_zoom.md`
  LLDB runtime/static proof for the immediate `0x29a140` source-local producer
  body behind the tracked index-5 `StereoLayer<false>+0xf8` field assembly:
  accepted four-zoom probes validate the `0x299eb0 -> 0x28f490 -> 0x299fd0`
  boundaries, populated `2080 x 1560` descriptor, record-base/offset-table
  state, and sampled `0x299fd0` record-layout formula. The patched probe now
  persists the complete input descriptor and mask descriptor as binary dumps,
  and the validators check their size/SHA plus zero exact whole-LRI and
  public-calibration payload hits for those full arrays and sampled
  first-record-header slices. This excludes direct byte-copy origin under the
  checked quartet only. Public origin, physical meaning, stable record
  constants, and final merge effect remain open.
- `lldb_index5_depth_public_meaning_gap_audit_four_zoom.md`
  Repo-local audit verifier and evidence synthesis for the Lane B index-5 depth
  public-meaning gap. It admits `record+0x40` as the internally depth-labeled
  `lt::UpsampleLayer+0x90` descriptor and independently decodes the public LRI
  camera/config key space (`LightHeader.field_12` and 262,968-byte
  warp/calibration `field_13`) used for runtime key alignment. Refreshed
  `0xf2770` constructor packets also prove constructed `object+0x60` keys match
  public `LightHeader.field_12[camera].field_2`, `object+0x50` matches raw
  public `field_4`, `object+0x54` matches raw public `field_5`, constructor
  input `+0x40` matches raw public `field_8`, and constructor input
  `+0x48 * 2` matches raw public `field_10`, with observed `object+0x64=0`
  and constructed `object+0x30=1` in that object family. Enriched `0xf33d0`
  packets prove exact public intrinsics-block fixed32 copies for wide A1-A5 K matrix / pose records
  and exact public pose copies for B4 plus tele C5, while B4/C5 K matrices,
  other B/C-side packets, tele C6, full `state+0xe0`, full `state+0x448`
  beyond the separately admitted first-payload pose fields, and the index-5
  source records remain outside admitted public-origin closure. The index-5
  lookup vector is separately admitted as an internally generated reciprocal
  near/far table, not a direct public LRI/calibration table.
  The `0x29a140` source-local full input/mask arrays now also have zero exact
  whole-LRI and public-calibration byte hits, which narrows direct-copy origin
  without excluding transformed public derivation.
  Companion `0x23faf0` record-chain verification adds component-scoped public
  matches plus zero full 0xa4-byte source-record LRI byte-copy hits.
- `bundle_static_runtime_index5_public_proto_schema_names.md`
  Deterministic extraction of the serialized `camera_module.proto`,
  `geometric_calibration.proto`, and `lightheader.proto` descriptors embedded
  in the installed `libcp.dylib`, plus raw-wire checks on representative wide
  and tele LRIs from both physical calibration bodies. It names the previously
  anonymous module fields as `id`, `mirror_position`, `lens_position`,
  `sensor_exposure`, `sensor_temparature`, and `sensor_data_surface.size`; it
  names the geometry paths as `per_focus_calibration[].intrinsics.k_mat`,
  `focus_hall_code`, and `extrinsics.canonical.rotation/translation`. Combined
  with prior runtime custody, this classifies the captured K helper as
  focus-dependent intrinsics evaluation at live lens position and gives
  `record+0x40` a public sensor-size origin without misnaming its generated
  pixels as an LRI-stored depth map. Full state-record identities, the public
  calibration/LRI/protobuf origin of the ray-depth bounds, public source-index
  names / physical semantics, and final effect remain open; claim status is
  unchanged.
- `bundle_static_runtime_index5_gdepth_mm_custody_four_zoom_two_body.md`
  SHA-pinned Capstone proof plus complete Unit-1 four-focal runtime and an
  exact-focal Unit-2 28mm body discriminator joins all six
  `StereoLayer<false>` index descriptors and the exact
  `UpsampleLayer+0x90` descriptor into the depth cache, proves the
  depth-to-reciprocal / reciprocal-resize / reciprocal-to-depth chain has no
  length-unit conversion, follows cache promotion into the live provider, and
  binds the provider's extrema to the public GDepth writer. This admits
  ray-depth scalars, `[200,640000]` bounds, and depth-map pixels in `mm`, with
  generated reciprocal lookup values in `mm^-1`. It does not identify the
  public calibration/LRI/protobuf source of the bounds, public
  source-index/source-record names, whole-record semantics, or final merge
  acceptance.
- `bundle_static_runtime_index5_range_cost_depth_public_names.md`
  SHA-pinned installed-label/xref proof joined to the existing Unit-1
  four-focal and exact-focal Unit-2 28mm range-builder reports, four-focal
  cost-volume/index custody, and sampled worker formulas. It exactly names
  `StereoLayer+0x2a8` as `Depth map`, `+0x208` as `Skip mask`, and `+0xf8` as
  `Cost volume`; names the generated `(lower,count)` descriptor as the
  per-pixel `Range map`; and classifies `0x299c70` output as the generated
  minimum-cost depth-hypothesis index map over per-pixel cost-volume records.
  It also exactly names `StereoLayer+0x240` as `Images` and proves `+0x258` is
  the parallel vector of five per-image composed geometry records built from
  `state+0xe0` plus same-key `state+0x448`; `0x28f5a0` computes their maximum
  geometry separation for the lookup-count formula. These are generated
  runtime products, not direct LRI/protobuf fields. This proof alone left the
  composed-record whole-field identity open; the next entry closes that
  operational identity while names/origins for remaining cost-volume
  operands, whole-State record identity, and final effect remain open.
- `bundle_static_runtime_index5_composed_geometry_public_origins_two_body.md`
  SHA-pinned static plus completed Unit-1 four-focal and exact-focal Unit-2
  `28mm` runtime proof classifying every meaningful field of the five
  `StereoLayer+0x258` items. It joins each item to public `CameraModule.id`,
  `lens_position`, `sensor_data_surface.size`, focus-dependent
  `intrinsics.k_mat`, anchor `extrinsics.canonical.rotation/translation`, and
  exact same-camera `Distortion.Polynomial` coefficients, center, and
  normalization. The records are derived per-image, tier-anchor-relative
  calibrated camera models, ordered `A1,A5,A2,A3,A4` at wide tiers and
  `B4,B2,B5,B1,B3` at tele tiers; `0x28f5a0` uses their maximum
  extrinsic-center separation. This closes the composed-record whole-field
  identity, not selector-bank naming, whole-State identity, remaining
  Cost-volume operands, bound protobuf identity, or final effect.
- `bundle_static_runtime_state_e0_capturedimage_identity_two_body.md`
  SHA-pinned control-block RTTI plus same-process pointer custody proving that
  every object selected through `state+0xe0` for index-5 composition is
  exactly `lt::CapturedImage`. Unit-1 four-focal coverage and an exact-28mm
  Unit-2 discriminator preserve public `CameraModule.id` alignment. This
  names the selected object type, not the lookup-context container, numeric
  `CalibStage` selector mapping, whole `state+0x448`, or final effect.
- `bundle_static_runtime_capturedimage_is_enabled_public_origin_two_body.md`
  Embedded-schema, two-body raw-wire, pinned constructor-copy, and Unit-1
  four-focal runtime proof that `CapturedImage+0x30` is exact public
  `LightHeader.modules[camera].is_enabled`. The sampled wide/tele LRIs on
  both bodies explicitly store `true`; false-value behavior, lookup-context
  naming, selector mapping, and final effect remain open.
- `bundle_static_runtime_capturedimage_capture_fields_public_origins.md`
  SHA-pinned `0xf2770` copies plus `42` Unit-1 four-focal constructor events
  name `CapturedImage+0x38` as public `CameraModule.sensor_exposure`, `+0x40`
  as `sensor_analog_gain`, optional `+0x44` as `sensor_digital_gain`, and
  optional `+0x104` as decoded `sensor_temparature`. Exact-wide/tele Unit-2
  LRIs verify the public source carriers; the attempted Unit-2 constructor
  run produced no packet, so cross-body constructor-runtime equality remains
  outside the claim.
- `bundle_static_state_e0_rawimagefactory_capturestack_identity.md`
  SHA-pinned RTTI, allocation, owner-accessor, constructor-call, and retained
  pointer proof naming `state+0xe0/+0xe8` exactly as a retained
  `shared_ptr<lt::RawImageFactory>`, backed by `shared_ptr<lt::CaptureStack>`
  constructed from the capture input stream. The factory supplies the
  previously bounded `0x1be970 -> 0xe6ba0` CapturedImage lookup. The following
  frame-index and CalibStage proofs close its secondary numeric key and
  numeric bank mapping; whole-State identity and final effect remain open.
- `bundle_static_runtime_capturedimage_frame_index_public_origin.md`
  SHA-pinned embedded-schema/parser/copy proof naming
  `CapturedImage+0x64` exactly as public `CameraModule.frame_index` and
  `RawImageFactory+0x10` as the selected-frame lookup key used before public
  camera-ID matching. The admitted renderer-owner path selects frame `0`;
  existing completed Unit-1 four-focal reports preserve `42` live zero-valued
  copies. Discriminating Unit-1 `28mm` and Unit-2 `35mm` burst LRIs each carry
  all ten camera IDs at frame indices `0..3`, while the optional corpus census
  finds `9,128` decodable `{0}` captures and `248` `{0,1,2,3}` captures.
- `bundle_static_runtime_calibstage_public_names_two_body.md`
  SHA-pinned complete `0xf33d0` reference census plus constructor, State/BA,
  and exact-focal two-body write-watch proof mapping numeric `CalibStage`
  names: selector `0` is `factory` at `CapturedImage+0x180`, and selector `1`
  is `current` at `+0x12c`. Both banks receive the same focus-evaluated public
  `FactoryModuleCalibration` packet at construction; every installed
  non-initial update targets current, while both body watches observe no live
  factory-bank write. This names the banks, not every packet field,
  whole-State identity, or final image/source effect.
- `bundle_static_runtime_index5_cost_operand_names_four_zoom.md`
  SHA-pinned installed-label proof joined to the accepted four-focal
  `0x276860` operand-source and completed payload-vector reports. It names
  target `+0x288` as `Guidance`, `+0x1e8/+0x200` as `Pixel buf` storage,
  `+0x198` as `Min cost buf` storage, and `+0x168` as `Line buf` storage.
  Static producer custody plus the composed-camera ordering identifies
  Guidance as the first/tier-anchor Images descriptor (`A1` wide, `B4` tele).
  The buffers are generated runtime products; local scale/bias fields,
  complete recurrence semantics, full-map distributions, and final effect
  remain open.
- `bundle_static_runtime_index5_g42_operand_pairing_metric.md`
  SHA-pinned installed/runtime proof of the selected index-5 plane-sweep
  pairing and local-cost arithmetic. Each projected source-`k` 3x3 byte patch
  is compared with the fixed unprojected `Images[0]` / Guidance anchor patch;
  component differences use caps `(2,6,6,0)`, saturating-u16 3x3 reduction,
  per-source weights with `+16` / `>>5`, a per-source `65535` clamp, and
  modulo-u16 cross-source accumulation. Twelve packets at each Unit-1
  `28/35/70mm` tier replay bit-for-bit; installed proof is focal/body
  independent and prior route proof supplies `150mm` liveness. The later
  G-43 and G-40 bundles close direction and per-level construction.
- `bundle_static_runtime_index5_g43_direction_policy.md`
  SHA-pinned installed/runtime closure of the selected SGM direction policy.
  Four positive paths use predecessors
  `(-1,0),(-1,-1),(0,-1),(1,-1)` and the negative sweep uses their opposites,
  yielding eight-path saturating-u16 aggregation. Wide `35mm` and tele `70mm`
  censuses prove positive-group then negative-group scheduling; installed
  allocation proof initializes complete `Line buf` and `Min cost buf` halves
  to `u16 2000` and `Pixel buf` to zero.
- `bundle_static_runtime_index5_g40_hypothesis_policy.md`
  SHA-pinned installed/runtime closure of the selected profile-3 mode-8
  per-level hypothesis policy. Level 0 seeds lower index zero over the full
  reciprocal lookup; levels 1 through 5 derive per-pixel Range-map
  `(lower,count)` records from the prior Depth map / Skip mask and commit
  `ceil(max_pixel_upper/8)*8`. Stable producer-store packets cover all six
  levels at Unit-1 `28/35/70/150mm`; observed extent sequences are
  scene-specific, not constants. Prior exact-focal Unit-2 `28mm` proof joins
  the same range-builder formula without claiming Unit-2 commit packets.
- `bundle_static_runtime_iramp_g49_subpixel_refinement.md`
  SHA-pinned installed/runtime closure of G-49's local IRAMP refinement. A
  row-major `3x3` integer SAD neighborhood drives a coupled two-variable
  float32 quadratic solve with conditional cross-term removal, exact-zero
  denominator fallback, and an all-or-nothing strict `abs(dx),abs(dy)<1`
  guard. Ninety-six Unit-1 four-focal packets replay bit-for-bit and exercise
  zero-denominator, accepted, and unit-guard-rejected outcomes.
- `bundle_static_runtime_index5_sgm_parameter_origins_four_zoom.md`
  SHA-pinned constructor/worker proof identifying target `+0x56 = 1` as the
  adjacent-hypothesis SGM penalty `P1`, target `+0x58 = 500.0` as the nominal
  guide-adaptive `P2/P1` ceiling scale, and target `+0x60` as the
  three-channel exponential guide-distance decay coefficients
  `log2(e)/(18,48,48)`. Auto-sidecar and no-sidecar constructor packets plus
  all four focal-tier worker packets agree. The producer uses only installed
  literals/constants, so these fields are body-independent algorithm tuning,
  not public calibration/LRI inputs. Per-component Guidance semantics, other
  recurrence terms, full-map distributions, and final effect
  remain open.
- `bundle_static_runtime_index5_guidance_public_producer_origin.md`
  SHA-pinned RTTI/call-chain proof plus an early-terminate Unit-1 `28mm`
  descriptor watch. It names `Images[0]` and reused `Guidance` as the
  tier-anchor `CapturedImage` product of
  `lt::StereoISP::CreateStereoImage`, whose first public argument is
  `Image<vec4x8ui>`, and proves exact descriptor custody through the key-`0`
  cache into `StereoLayer+0x240` `Images`. Existing four-focal ordering makes
  the anchor A1 wide or B4 tele; existing two-body composed-geometry proof
  covers the public calibration inputs and camera order. Per-component
  `vec4x8ui` semantics, a direct Unit-2 descriptor-equality packet, remaining
  recurrence terms, full-map distributions, and final effect remain open.
- `bundle_static_runtime_index5_guidance_component_routes.md`
  SHA-pinned component-route proof plus a Unit-1 `28mm` two-invocation
  packet. Independent key-`0` custody binds producer call `0` to Guidance;
  that call directly rounds/saturates its public `Image<vec4x32f>` output
  without lane shuffling. Five spatial samples carry independent `C0/C1/C2`
  color values and exact `C3=1`. Sole-caller/callee proof identifies the live
  pairs as source/anchor camera keys: A1/A1 direct and A5/A1 fitted affine.
  The fitted route is now formula-closed as float32 population covariance,
  double `+0.001 I` regularization, lower Cholesky transfer
  `chol(target)*inverse(chol(source))`, and mean translation; all sixteen
  captured matrix words replay exactly. The installed output-color-space map
  is separate and does not name these operands. The following bundle closes
  exact component semantics and live SoftISP configuration.
- `bundle_static_runtime_index5_guidance_collapse2_hot_pixel.md`
  Complete Unit-1 four-focal plus exact-focal Unit-2 `28mm` SoftISP property
  proof and all-phase E3 worker verification closing live Guidance as exact
  byte-packed `[R,0.5*(G1+G2),B,1]`. The same bundle proves the default
  hot-pixel pre-stage is nonzero and narrows it to a rank-6 residual, public
  analog-gain-selected installed Bayer noise LUTs, an exact `4*LUT` threshold,
  `0x8000` marker lifecycle, and a 96/96 replayed final isolation predicate.
  The clean-room LUT generator uniquely reproduces all `4096` captured words;
  both phase-dependent rank-neighborhood formulas replay the focused live
  residual exactly. Its former full-stage closure is superseded by the next
  corrective bundle.
- `bundle_static_runtime_hot_pixel_fullframe_correction_unit1_28mm.md`
  Complete Unit-1 exact-28mm A2 pre/post worker capture correcting the focused
  hot-pixel interpretation to one residual per rolling source row and
  row-varying isolation selector `(y&1) XOR phase`. Public replay is exact for
  every sample in the eight-pixel-inset interior; 118 global-edge samples and
  cross-body/focal full-frame validation remain open, returning
  `CLM-STEREO-001` to scoped `PARTIAL` / `BLOCKER` status.
- `bundle_static_runtime_hot_pixel_fullframe_boundary_two_body_wide.md`
  Superseding installed/runtime closure for the global edge. `0x178b0`
  constructs a six-pixel halo by same-parity edge projection and upper median
  over available same-CFA `3x3` lattice samples. Four representative backing
  allocations replay all `317,312` words per run, and complete worker replay
  matches all `12,979,200` output words for Unit-1 exact-`28mm`, Unit-2
  exact-`28mm`, and Unit-1 canonical-`35mm`, spanning three distinct LUTs.
  Opposite-phase controls remain nonzero. This restores selected
  `CLM-STEREO-001` to `PROVEN` / `SPEC_READY`; unselected compatibility arms
  remain outside scope.
- `bundle_static_runtime_index5_plane_sweep_correspondence.md`
  SHA-pinned installed proof of the selected index-5 correspondence domain,
  calibrated `CreateStereoImage` operand identity, exact composed-camera
  multiply order, transposed record layout, float32 projection order, and
  subpixel sampling policy. It also settles G-42's fixed reference as the
  tier anchor's own collapse2 Guidance and supplies a direct same-render
  Unit-1 `28mm` packet with five images, four projection records, a complete
  lookup, three winners, and their deterministic correspondence replays.
  Existing runtime joins cover the
  worker on Unit-1 `28/35/70/150mm` and the composed-geometry mechanism on
  exact-`28mm` Unit-2.
- `bundle_static_runtime_index5_sgm_recurrence_roles_four_zoom.md`
  SHA-pinned allocator/helper/worker proof joined to the accepted four-focal
  term and payload-vector packets. It names the remaining sampled recurrence
  roles: predecessor candidates and current path output are `Line buf`,
  `%xmm2` is the prior `Min cost buf` normalization baseline, `%xmm3` is that
  baseline plus guide-adaptive `P2`, and `[r10+2*rdx]` is the per-pixel local
  matching-cost temporary. The current minimum returns to the other
  `Min cost buf` half and the current path cost is accumulated into the
  Cost-volume payload. These are generated SGM terms, not additional public
  calibration/LRI fields; full-map distributions and final effect remain
  open.
- `lldb_f33d0_1f0ce0_producer_four_zoom.md`
  Static/runtime verifier for the constructor-side `0x1f0ce0 -> 0xf33d0`
  producer edge. It proves the installed bytes still set selector `0` and
  selector `1` before the two `0xf33d0` calls, the existing four-zoom packets
  copy identical source records into both accepted `CalibStage` banks per key,
  wide A1-A5 are exact public K/pose records, B4/C5 poses are exact public
  copies, and B4/C5 K records are already zoom-variant non-exact packets at the
  producer edge. This is derived-K boundary proof, not public field-name
  closure for `state+0xe0`, `state+0x448`, source-index/source-record
  semantics, or lookup-vector physical meaning.
- `lldb_1f0ce0_k_source_trace_four_zoom.md`
  LLDB runtime/static verifier refining the constructor-side K boundary: the
  first usable K vector after `0x1f0b00` is an exact public same-camera fixed32
  sequence under the 32,832-byte LRI intrinsics payload `field_13[camera=N]`;
  helper entry `0x1f96e0` receives the same camera's two public K records and
  public `focus_hall_code` scalars; `0xf3300` supplies runtime
  `object+0x54 = CameraModule.lens_position`; the
  captured two-record helper branch linearly interpolates/extrapolates K fields
  `0`, `2`, `4`, and `5` with float32 arithmetic; the tested `0xf3350` scale
  window is identity; and both final `0xf33d0` selector calls receive the same
  resulting K stack packet. Public names for selector banks, other B/C
  packets, and index-5 source records remain open;
  the index-5 lookup vector is now internally classified as a generated
  reciprocal near/far table.
- `bundle_static_runtime_focus_k_bracket_policy_two_body.md`
  G-37 closure for the public focus-dependent K evaluator. SHA-pinned
  installed proof closes stable Hall-coordinate sorting, one/two/three-record
  selection, exact float32 slope/intercept evaluation of K fields
  `{0,2,4,5}`, extrapolation, and the `0.001` separation guard. A structural
  census of eight exact-focal LRIs across both physical calibration signatures
  finds exactly two public focus/K records per camera; retained complete
  Unit-1 `28/35/70/150mm` packets bit-replay that observed branch. No
  three-record LRI incidence is claimed.
- `lldb_state_448_payload_public_origin_four_zoom.md`
  LLDB runtime/static verifier for the first visible `state+0x448` payload-copy
  sites. It proves payload `+0x00..+0x20` is copied from the public 32,832-byte
  intrinsics-block pose rotation component and payload `+0x24..+0x2c` is copied
  from the corresponding public translation component, using anchor `A1` at
  `28mm` / `35mm` and anchor `B4` at `70mm` / `150mm`, shared across the
  first-pass inserted keys. Tele first-pass keys are `B1..C5`, excluding
  public-fired `C6`. The checked later `+0x30..+0x3c` source slices record zero
  exact public fixed32-sequence hits; a separate later-box formula proof now
  gives formula-level meaning for that `+0x30..+0x3c` slice, while full
  `state+0x448` payload semantics, public names, and index-5 source records
  remain open. The index-5
  lookup vector is separately classified as an internal reciprocal near/far
  table, not a direct public LRI table.
- `lldb_state_448_later_box_formula_four_zoom.md`
  LLDB runtime/static verifier for the later `state+0x448` payload
  `+0x30..+0x3c` slice in the first visible constructor branch. It proves
  `+0x30/+0x34` is the uniform float32 scale
  `max(4160 / (box.x1 - box.x0), 3120 / (box.y1 - box.y0))`, `+0x38/+0x3c`
  is the float32 box origin, the box comes from `0x145980(object)`, and the
  size pair comes from `object+0x114/+0x118`. This closes formula-level meaning
  for that slice only; companion proofs name the size pair as public full
  sensor ROI and the box-producing input record as public
  `geometry.distortion.polynomial`, while the computed envelope and uniform
  scale remain derived rather than direct public fields.
- `bundle_static_runtime_g38_undistort_envelope_formula_two_body.md`
  G-38 formula closure for `0x145980`: exact public Brown-Conrady radial
  samples, four-point cubic inverse-radius evaluation, 91-sample vertical and
  121-sample horizontal inner-valid-edge sweeps, float32 extrema, and
  truncation into a half-open integer box. Public-calibration replay exactly
  matches 20 Unit-1 four-focal boxes and five exact-`70mm` Unit-2 boxes,
  rechecks byte-exact Unit-1 A1 / Unit-2 B4 4096-entry distortion tables, and
  retains the 20 four-focal RGBA16F undistorted planes as downstream
  validation.
- `lldb_state_448_box_producer_static_origin_four_zoom.md`
  Static verifier for the `0x145980` box producer feeding the later
  `state+0x448` formula. It proves the formula size pair is the LRI-stored
  full sensor ROI `4160 x 3120`, and bounds the box as a computed
  distortion/undistortion envelope over owner-backed calibration data.
- `bundle_static_runtime_state_448_distortion_polynomial_public_origin_two_body.md`
  Static/runtime two-body custody proof for that owner-backed calibration
  structure. It pins the generated-protobuf conversion and keyed lookup path,
  then matches live center, normalization, complete coefficient-vector, and
  fit-cost words to same-camera public
  `LightHeader.module_calibration[].geometry.distortion.polynomial` records on
  Unit-1 28mm and Unit-2 70mm. The computed envelope, scale, and whole
  `state+0x448` payload remain derived rather than direct protobuf fields.
- `lldb_source_record_payload_watch_four_zoom.md`
  LLDB hardware write-watchpoint proof for sampled source-record payload bytes
  after `0x299fd0`: accepted four-zoom probes arm watchpoints on zeroed
  `record+0x08` payload bytes for the first two source-local records and
  attribute sampled mutations to the `libcp+0x277a10` SIMD store inside
  `0x276860`. `%xmm5` arithmetic, full-map payload distributions, public
  origin/meaning, and final merge effect remain open.
- `lldb_276860_payload_vector_formula_four_zoom.md`
  LLDB runtime/static proof for sampled SIMD increment arithmetic feeding the
  `0x277a10` payload store: accepted four-zoom packets validate the
  `0x2779b0..0x277a10` unsigned-16 recurrence, full side-store and payload-store
  register agreement, watched-lane saturating accumulation where prior watched
  bytes are known, and narrow stable custody for the sampled record base /
  offset table / stride, `r9` destination, `r10` temporary pointer, and `%xmm1`
  broadcast from `object+0x56`. Public operand origin/meaning, the full
  upstream `%xmm3` pre-add term, full-map payload distribution, all records/lane
  positions, and final merge effect remain open.
- `lldb_276860_scalar_operand_origin_four_zoom.md`
  LLDB early-terminate packet proof for the immediate scalar setup before the
  admitted `0x2779b0..0x277a10` SIMD recurrence: accepted four-zoom packets pair
  `0x27786b`, `0x27791d`, and `0x277945` on the same target-index-5 context,
  proving sampled `%xmm2` is prepared from a `uint16` lookup through
  `rbp-0x210`, sampled `%xmm3` is prepared from the live post-add `edx`, and
  both broadcast-ready registers match those paired scalar values. The later
  `%xmm4` origin proof closes sampled internal `%xmm4` formation; public
  operand origin/meaning, full-map distribution, all records/lane positions,
  and final merge effect remain open.
- `lldb_276860_xmm3_term_step_four_zoom.md`
  LLDB early-terminate single-step proof for a non-degenerate sampled `%xmm3`
  term: after skipping the first four target table hits, accepted four-zoom
  packets validate `preadd = trunc_i32(f32(u16[object+0x56]) *
  f32[object+0x58] * xmm4_low)`, `postadd = preadd + table`, and the final
  `%xmm3` broadcast on one stepped target-index-5 packet per focal tier. The
  later `%xmm4` origin proof closes sampled internal `%xmm4` formation; public
  operand meanings, full-map distribution, all records/lane positions, and
  final merge effect remain open.
- `lldb_276860_xmm4_origin_four_zoom.md`
  LLDB early-terminate single-step proof for the preceding `%xmm4` producer
  window: accepted four-zoom packets reconstruct `%xmm4_low` exactly from
  `xmm8 - [[rbp-0x208] + rdx]`, `object+0x60`, the observed
  mask/blend/horizontal-sum/sign/clamp sequence, and the local
  polynomial/exponent-bit assembly at `0x27786f..0x277903`. This closes the
  sampled internal `%xmm4` formation boundary only; public operand meanings,
  LRI/protobuf origins, full-map distribution, all records/lane positions, and
  final merge effect remain open.
- `lldb_276860_operand_source_context_four_zoom.md`
  LLDB early-terminate packet proof for the immediate operand-custody context
  behind that sampled `%xmm4` subtraction: accepted four-zoom packets bind
  `%xmm8` to a same-thread load from the target object's `+0x200` vector table,
  where the matched local store is generated from guide bytes read through
  target `+0x288`; bind `[rbp-0x208]` to target `+0x1e8`; and bind the paired
  table base `[rbp-0x210]` to target `+0x198`. A refreshed same-object
  producer/watchpoint run also ties the final target qwords to internal stores
  `0x26ca94` (`+0x198`), `0x26cbcd` (`+0x1e8`), `0x26cc01` (`+0x200`), and
  `0x26c633` (`+0x288`), and validates the sampled `0x26c8e0` buffer layout:
  `+0x198` capacity `16656` `uint16` entries, `+0x200 - +0x1e8 = 33312`
  bytes, and sampled subtraction-vector delta `+16` from `+0x200`. Public
  field names, public LRI/protobuf origins, physical meaning, full-map
  distribution, and final merge effect remain open.
- `lldb_index5_operand_public_origin_audit_four_zoom.md`
  Repo-local verifier extension for the sampled `0x276860` operand public-origin
  gap. It checks guide first-16 bytes, sampled guide-16 bytes, and the
  subtraction vector against the whole LRI payload stream and the public
  calibration payload subset across all four canonical focal tiers, and checks
  the subtraction vector against public calibration fixed32 sequences. All
  admitted 16-byte checks have zero hits; the two-byte table value is reported
  but not used as an absence proof. The same audit carries forward the internal
  target-field producer custody and sampled buffer layout, but this remains
  scoped negative public-origin evidence, not public semantic naming or Lane B
  closure.
- `bundle_proof_calibdataprocessor_lambda_family.md`
  Installed-bundle proof for the upstream `CalibDataProcessor::State()` lambda / runner family.
- `lldb_calib_state_operator_runtime_four_zoom.md`
  LLDB runtime proof that all thirteen verified `CalibDataProcessor::State()`
  `operator()` bodies are live in complete accepted bridge HDR renders across
  `28mm`, `35mm`, `70mm`, and `150mm`; the corrected body list is `0x229df0`,
  `0x229ec0`, `0x22a0e0`, `0x22a9b0`, `0x22aaf0`, `0x22ae60`, `0x22af80`,
  `0x22bdf0`, `0x22bee0`, `0x22c350`, `0x22cd00`, `0x22d250`, and
  `0x22e1d0`, with full-render count pattern `(1,1,4,4,4,1,1,1,5,5,5,5,1)`.
  `0x247390` is excluded from the State census and refuted as a State body.
  This is runtime liveness, not reducer closure.
- `bundle_proof_state_machine_terminal_22e1d0_static.md`
  Installed-bundle static proof bounding terminal corrected State body `0x22e1d0`
  and shared dispatcher `0x22f0f0`: `0x22e1d0` performs keyed vector/tree/object
  lookup and helper dispatch over per-key records, calls `0x23c5f0`, `0xe6ba0`,
  and `0xf33d0`, and returns State value `9`; `0x22f0f0` invokes registered
  State function objects, stores returned `State` values at `r14+0x6c`, and can
  notify a callback object at `r14+0xe0`. This bounds another State-machine
  surface away from direct pixel reducer closure; public State semantics and
  `CLM-PREFUSION-002` remain open.
- `lldb_state_machine_return_runtime_four_zoom.md`
  LLDB runtime proof that the accepted no-auto-LRIS canonical bridge HDR quartet
  executes an identical ordered State-return skeleton at dispatcher sites
  `0x22f3f6` / `0x22f3ff`: `38` paired pre/post calls per render, clean
  `10432x7824` HDR output at `28mm`, `35mm`, `70mm`, and `150mm`, no JSON
  errors, no step cap, and the same `(operator, pre-state, returned State)`
  sequence across all four runs. This proves runtime return ordering for the
  tested dispatcher path, not public State semantics, reducer closure, or final
  acceptance/rejection.
- `bundle_static_state_family_full_body_call_surface.md`
  Installed-bundle static proof isolating the exact function body for each of
  the thirteen corrected State operators. The State operator bodies contain zero
  indirect calls; dispatcher `0x22f0f0` contains the expected indirect dispatch
  calls. The exact bodies expose direct helper-family surfaces and have zero
  direct calls to the listed known IRAMP/wrapper/owner-route VAs. This is a
  direct-call-surface proof only, not helper transitive closure, public State
  semantics, reducer closure, or final acceptance/rejection.
- `lldb_state_helpers_23c5f0_f33d0_four_zoom.md`
  Installed-bundle plus LLDB runtime proof bounding State helper `0x23c5f0`
  and selector-gated field-copy helper `0xf33d0`: complete accepted
  no-auto-LRIS bridge HDR runs at `28mm`, `35mm`, `70mm`, and `150mm` hit
  `0x23c5f0` exactly four times per run from State bodies `0x22af80` /
  `0x22e1d0`, hit `0xf33d0` without errors or caps, and prove the static
  `0x23c5f0 -> 0xf33d0` callsite at `0x23d38d` / return `0x23d392` live with
  selector `1`. This is helper-selector / field-copy boundary proof, not
  reducer closure.
- `lldb_state_helper_23c5f0_exit_snapshot_four_zoom.md`
  LLDB runtime proof that complete accepted no-auto-LRIS bridge HDR runs at
  `28mm`, `35mm`, `70mm`, and `150mm` pair every `0x23c5f0` entry with a
  normal pre-destroy exit, capture the post-`0xf33d0` local `rbp-0x4e0`
  integer coverage pattern, and snapshot the local pre-destroy tree with no
  traversal truncation. This is local helper-field / tree custody proof, not
  public State semantics, reducer closure, or final acceptance/rejection.
- `lldb_state_helper_f34e0_match_four_zoom.md`
  LLDB runtime proof that objects populated by the live `0x23c5f0 -> 0xf33d0`
  selector-`1` copy path are later passed to `0xf34e0` inside the same
  `0x23c5f0` helper family through `0x23c5f0 -> 0x264440 -> 0x264270`.
  Complete accepted no-auto-LRIS runs at all four focal tiers match nine prior
  destination objects and `204` selector-`1` `0xf34e0` calls per run. This is
  internal transitive helper-custody proof, not post-`0x23c5f0` image effect,
  reducer closure, or final acceptance/rejection.
- `lldb_state_helper_23faf0_record_chain_four_zoom.md`
  LLDB runtime proof bounding the next internal `0x23c5f0` record-chain step:
  after `0x264440`, the refreshed probe captures the pre-call
  `0x23faf0(dst=rbp-0x378, left=rbx+0x20, right=rbp-0x420)` tuple, the
  `rbp-0x378` output record changes across the call, remains stable through
  later node writes, and mapped output fields are materialized into local
  tree-node fields in all `104` admitted four-zoom groups. The verifier records
  zero exact full source-record LRI byte-copy hits while admitting only scoped
  public component matches. This is helper-record-to-local-tree custody proof,
  not public field semantics for the full records, post-`0x23c5f0` image effect,
  reducer closure, or final acceptance/rejection.
- `bundle_proof_prefusion_state_helper_chain.md`
  Installed-bundle proof bounding the first post-`State()` helper chain to setup / copy / reset work.
- `bundle_proof_prefusion_heavy_consumers.md`
  Installed-bundle proof bounding first heavy consumers to feature / pyramid / candidate state work.
- `bundle_proof_prefusion_dispatch_gate.md`
  Installed-bundle proof bounding the dispatcher / selector layer to record-state gating.
- `bundle_proof_prefusion_selection_helpers.md`
  Installed-bundle proof bounding selector helpers and bitset acceptance path.
- `bundle_proof_prefusion_callback_reuses_known_runner.md`
  Installed-bundle proof that the selector callback reuses the already-bounded higher-group runner.
- `bundle_proof_prefusion_block_geometry_helpers.md`
  Installed-bundle proof bounding candidate block-geometry helpers away from reducer closure.
- `bundle_lldb_prefusion_block_geometry_effect_four_zoom.md`
  LLDB runtime proof bounding the admitted four-zoom `0x25d090` effect as block-owned pair-vector growth plus descriptor-build / geometry-predicate / active-byte gating. This is block-state effect proof only; image/source contribution, final acceptance/rejection, and reducer closure remain open.
- `bundle_lldb_prefusion_block_decision_cascade_four_zoom.md`
  LLDB runtime proof that the downstream `0x244560` / `0x245a40` caller decisions after paired `0x25d090` calls continue with exactly one active block and reach `0x2457c0` callsites, with zero abort decisions and zero watched sentinel-fill path hits in the admitted quartet.
- `bundle_proof_prefusion_feature_selection_lane.md`
  Installed-bundle proof bounding the visible `0x258fe0` / `0x2598a0` feature-selection lane away from reducer closure.
- `bundle_proof_prefusion_reducer_arithmetic_static.md`
  Deterministic closed-form verification that the 16 accumulator weights captured in `bundle_lldb_iramp_36e530_accumulator_prep.md` are the periodic (DFT-even) Hann window of length 16, `w[n] = sin²(π(n+0.5)/16)`, to float32 precision (max residual 1.13e-7; symmetric Hann ruled out at 5.70e-2; taps sum to N/2 = 8.0). Scoped to the window closed form only; does not identify the `src1`/`src2` reducer and does not advance `CLM-PREFUSION-002`.
- `bundle_proof_two_unit_corpus_static.md`
  Per-file machine-verified identification of TWO physical L16 units across the whole corpus by intrinsics calibration SHA-256 (Unit-1 `722a6e72…` 5724 files; Unit-2 `223961c6…` 3484 files). Proves folders are date-organized not unit-organized (13 date-folders mix both units). REFUTES the prior Unit A/B labeling — all four canonical seeds are Unit-1, so every "four-zoom verified" claim was one body × four focals, not two bodies (universality unproven). Lists Unit-2 same-name counterparts, now scoped by follow-up verifier because two same-name files are not exact-focal 35mm / 70mm representatives. 182/9390 files unassigned (parser gap, not a third unit).
- `bundle_static_lane_b_crossunit_lri_public_carriers.md`
  Tracked render-free verifier for the Lane B public LRI carrier schema across Unit-1 canonical seeds and exact-focal Unit-2 representatives. Confirms the `LightHeader.field_12` carrier fields, 16-record intrinsics `field_13`, large warp/calibration `field_13`, and per-camera `4160x3120` ROI path on both bodies; records body-specific calibration/nominal-table differences and corrects the same-name Unit-2 `L16_03041` / `L16_03434` focal-tier scope. This is static public-carrier evidence only, not Unit-2 runtime index-5 custody or a ledger upgrade.
- `bundle_proof_lri_calibration_origin_static.md`
  Independently re-verified static facts (Lane B / WSJF #2): the three calibration blocks (intrinsics/distortion/depthcfg) are byte-identical across the four canonical LRIs; the 16 intrinsics records are pairwise distinct (genuine per-camera calibration); the full sensor ROI 4160×3120 is LRI-stored while all pyramid/level dims are libcp-computed halvings. Parity consequence: Phoenix must parse per-camera calibration + sensor ROI from each LRI (supports standalone distribution). Includes a scoped, human-flagged observation that all four LRIs share identical calibration (likely one body) without rewriting the Unit A/B doctrine.
  Later corpus proof confirms those canonical seeds are all Unit-1; the embedded-schema follow-up checks representative wide/tele LRIs from both Unit-1 and Unit-2 and names the geometry/module carriers without claiming identical per-body values.

### External scratch docs with claim-level authority

- `/Volumes/Dev/lumen-phoenix-scratch/ceres_evaluate_bodies.md`
- `/Volumes/Dev/lumen-phoenix-scratch/35mm_renderer_mechanism.md`
- `/Volumes/Dev/lumen-phoenix-scratch/calibration_audit.md`
- `/Volumes/Dev/lumen-phoenix-scratch/color_pipeline_audit.md`
- `/Volumes/Dev/lumen-phoenix-scratch/demosaicv1_details_cleanup.md`
- `/Volumes/Dev/lumen-phoenix-scratch/image_resolution_amp_verification.md`
- `/Volumes/Dev/lumen-phoenix-scratch/iramp_camera_identity.md`
- `/Volumes/Dev/lumen-phoenix-scratch/iramp_kernel_body.md`
- `/Volumes/Dev/lumen-phoenix-scratch/lightheader_camera_scan.md`
- `/Volumes/Dev/lumen-phoenix-scratch/composite_producer.md`
- `/Volumes/Dev/lumen-phoenix-scratch/runreferencegroupcams_body.md`
- `/Volumes/Dev/lumen-phoenix-scratch/tone_curve_location_and_zoom_crop.md`

## Rules

- Evidence docs may be narrow and technical.
- Evidence docs may include partial findings.
- Evidence docs do not become canonical by themselves.
- Every canonical claim must point back here or to an equivalent proof source.

## Future Naming

Recommended future filenames:

- `bundle_proof_<topic>.md`
- `lldb_<topic>_<zoom>.md`
- `disasm_<topic>.md`
- `validation_<topic>.md`
# Final formula-level constants

- [bundle_static_runtime_raw_sensor_layout_two_body_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_raw_sensor_layout_two_body_four_zoom.md)
  Embedded-schema, eight-LRI/two-body/four-focal, SHA-pinned installed-decoder, and stopped-frame runtime proof of the exact `RAW_PACKED_10BPP` surface layout, camera partitions, Bayer phases, and contiguous little-endian 10-bit unpack formula.

- [bundle_static_runtime_lri_consumed_block_contract_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_lri_consumed_block_contract_four_zoom.md)
  Installed reader/schema proof, complete four-focal preference/formula joins, flash/GPS exclusions, and a 9,438-file census closing every structurally complete LELR record type and block role.

- [bundle_static_runtime_final_stage_constants_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_final_stage_constants_four_zoom.md)
  SHA-pinned installed extraction of the wavelet detail weights, SIMD absolute-value mask, seven-tap sharpen Gaussian generator/worker, and `ImageDenoiseBilateralGeneric<5,true>` spatial support, plus clean four-focal runtime captures of the exact Gaussian coefficients and NLM `window_size=5`, `patch_size=5`, `step_size=2` configuration.

- [bundle_static_runtime_denoise_route_cnr_parameters_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_denoise_route_cnr_parameters_four_zoom.md)
  SHA-pinned installed RTTI/body proof plus Unit-1 four-focal and exact-35mm Unit-2 LLDB route census for live `setDenoising`, denoise algorithm, PatchNLM, and `ColorNoiseReduction` entry parameters, including the Unit-2 `0x2fd070` discriminator.

- [bundle_static_runtime_denoise_selector_2fd070_two_body.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_denoise_selector_2fd070_two_body.md)
  SHA-pinned selector-table proof plus exact-35mm two-body runtime discriminator showing Unit-2 `0x2fd070` is the observed `r9b=0`, kernel-size `9` sibling of the Unit-1 `r9b=0`, kernel-size `5` `0x2fb320` route.

- [bundle_static_runtime_selected_bilateral_formula_two_body.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_selected_bilateral_formula_two_body.md)
  SHA-pinned formula and exact-35mm two-body post-store replay for the selected `0x2fb320` radius-2 and `0x2fd070` radius-4 workers, including callback source/range-scale/destination/coefficient custody, uniform square support, zero-filled boundaries, tent weights, the `1e-6` floor, and unrefined packed reciprocal normalization; joined to prior Unit-1 four-focal liveness/store proof.
- [bundle_static_runtime_selected_bilateral_range_scale_origin.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_selected_bilateral_range_scale_origin.md)
  SHA-pinned two-stage construction of the selected generated `range_scale`: public reciprocal AWB and per-capture analog-gain origins, installed RGB SensorGainVars selection, exact black/white and `1e-5` variance floor, fixed Ohta variance propagation, live `0.0025` I1 floor, Unit-1 four-focal liveness, and exact-35mm Unit-2 route coverage.

- [bundle_static_runtime_cnr_worker_formula_four_zoom_two_body.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_cnr_worker_formula_four_zoom_two_body.md)
  SHA-pinned static and Unit-1 four-focal plus Unit-2 exact-35mm runtime proof of the live `ColorNoiseReduction` worker accumulation, noise/shaping vector, normalized helper-input matrix, and final RGB transform-store formula, with the matrix-helper-internal gap explicitly scoped.

- [bundle_static_runtime_cnr_public_vector_origins_four_zoom_two_body.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_cnr_public_vector_origins_four_zoom_two_body.md)
  SHA-pinned static extraction plus Unit-1 four-focal and Unit-2 exact-35mm runtime joins naming live CNR vectors: reciprocal public AWB, derived reciprocal square, and installed RGB SensorGainVars `red/green/blue.{a,b}` selected by public reference-camera analog gain.

- [bundle_static_runtime_cnr_matrix_helper_svd_four_zoom_two_body.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_cnr_matrix_helper_svd_four_zoom_two_body.md)
  SHA-pinned static and Unit-1 four-focal plus Unit-2 exact-35mm runtime proof that live CNR helper mode `0x14` is a 3x3 two-sided SVD equivalent, with output convention `M = B.T * diag(S) * A`.

- [bundle_static_runtime_calibstage_slice_public_names.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_calibstage_slice_public_names.md)
  Aggregated installed/static, Unit-1 four-focal, and Unit-2 exact-28mm proof naming the three selected-node slices transferred into current CalibStage as public `intrinsics.k_mat`, `extrinsics.canonical.rotation`, and `extrinsics.canonical.translation`, while preserving their derived/composed-value boundary.

- [bundle_static_runtime_c6_terminal_filter_differential_tele.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_c6_terminal_filter_differential_tele.md)
  SHA-pinned terminal-filter proof plus repeated tele runtime intervention: canonical baselines clear C6 and write HDR, while restoring only key-15 `CapturedImage.is_enabled` deterministically reaches the per-key `SourceImageCache` mono-module rejection and writes no image data.

- [bundle_static_runtime_ccm_illuminant_selection_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_ccm_illuminant_selection_four_zoom.md)
  Embedded-schema and four-LRI proof mapping stored variants to A/D65/F11, plus four-focal runtime public-matrix joins and SHA-pinned clamped reciprocal-temperature A/D65 interpolation.
- [bundle_static_runtime_ccm_chromaticity_public_origin_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_ccm_chromaticity_public_origin_four_zoom.md)
  SHA-pinned public `awb_gains` to normalized-neutral RGB custody, exact A/D65 fixed-point xy solve, runtime-extracted 31-row Robertson table and temp/tint round trip, with exact retained live-xy equality at all four canonical Unit-1 focal tiers.
- [bundle_static_runtime_row_image_public_policy_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_row_image_public_policy_four_zoom.md)
  Installed-RTTI, arithmetic, and four-focal runtime proof naming the separable half-sample Hann weights, orthonormal `I1/I2/I3 -> RGB` shaping, AWB channel vector, `Vec3<Float16>` cache rows, `vec4x32f` working rows, and the tested `linear_prophoto_rgb` to Radiance RGBE output policy.
- [bundle_static_runtime_calibdataprocessor_public_identity_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_calibdataprocessor_public_identity_four_zoom.md)
  Installed-RTTI and four-focal dispatcher proof identifying the 13-body State machine as `lt::CalibDataProcessor::{runReferenceGroupCams,runHigherGroupCams}` callbacks returning `CalibDataProcessor::State()`.
- [bundle_static_runtime_prefusion_wide_218bc4_path_divergence.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_prefusion_wide_218bc4_path_divergence.md)
  Installed selector/RTTI proof plus complete `28mm`/`35mm` count-only runs showing canonical wide selects `SparseMirrorAngleOptimizer::CostFunction` value `1` and sibling helper `0x218940`; guard `0x218bc4` belongs only to the zero-hit CostFunction-`0` / `0x218b30` family.
- [lldb_unit2_capturedimage_constructor_runtime_join.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_unit2_capturedimage_constructor_runtime_join.md)
  Exact-focal Unit-2 `28mm` runtime proof covering all ten camera keys and joining direct `CapturedImage` constructor fields to public exposure, analog gain, digital gain, and temperature values.
- [bundle_static_runtime_laplacian_clarity_kernel_28mm.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_laplacian_clarity_kernel_28mm.md)
  SHA-pinned installed formula and canonical Unit-1 `28mm` liveness proof for `CreateAndBlendLaplacianPyramids`: public `lpyr_*` config names, the exact 8049-sample `clamp + clarity-Gaussian` transfer, adjacent transformed-pyramid interpolation, `0.75^level` decay, defaults, and observed levels `0..4`.
- [bundle_static_runtime_laplacian_pyramid_construction_shaping_28mm.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_laplacian_pyramid_construction_shaping_28mm.md)
  SHA-pinned construction closure for `CLM-SHARPEN-002`: logarithmic `2..6` total-level rule, exact separable five-tap reduce and parity-dependent expand kernels, negative-detail sign/reconstruction, plus complete shadow/highlight/percentile shaping algebra and Unit-1 `28mm` read-watch liveness for all five public fields.
- [bundle_static_runtime_prefusion_monofusion_confidence_callback_two_body.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_prefusion_monofusion_confidence_callback_two_body.md)
  SHA-pinned installed callback formula plus exact-focal Unit-1 35mm and Unit-2 28mm runtime equality for MonoFusion's secondary confidence/output map, with explicit canonical four-zoom route scope.
- [bundle_static_runtime_prefusion_monofusion_flow_field_formula_two_body.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_prefusion_monofusion_flow_field_formula_two_body.md)
  Exact five-stage unsigned-16 SAD flow construction, quadratic refinement, public vignetting/gain rejection formula, and all-vector bit-exact replay: 215,473 vectors per body across two physical exact-28mm inputs, joined to the canonical wide-live/tele-absent route scope.
- [bundle_installed_prefusion_monofusion_transform_edges.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_installed_prefusion_monofusion_transform_edges.md)
  Exhaustive installed 256-basis forward/inverse proof of normalized 5/3 symmetric edge replication, interleaved smooth/detail packing, and strides 1/2/4/8 low-pass lattice recursion.
- [bundle_static_runtime_prefusion_reference_single_camera_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_prefusion_reference_single_camera_four_zoom.md)
  Installed constructor/accessor and four-focal runtime join proving visible `src1` has one public A1-wide/B4-tele camera origin.
- [bundle_static_runtime_iramp_operand_roles_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_iramp_operand_roles_four_zoom.md)
  SHA-pinned IRAMP custody and four-focal runtime join proving the distinct guide, reference, candidate, comparison, and normalized weighted-contribution roles.
- [bundle_static_runtime_iramp_score_formula_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_iramp_score_formula_four_zoom.md)
  SHA-pinned clean-room formula for `0x36cde0`, with candidate L1 normalization, two-scale structural/detail scoring, per-scale `min4`, one bit-exact live-input replay, and an explicit prior four-focal liveness/consequence join.
- [bundle_static_runtime_iramp_accumulator_reconstruction_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_iramp_accumulator_reconstruction_four_zoom.md)
  SHA-pinned clean-room formula for `0x36e530`: dyadic scale-selected reciprocal normalization plus exact four-stage inverse CDF 9/7 reconstruction, with `65,536/65,536` basis-float equality, two byte-exact live whole-buffer replays, and an explicit prior four-focal liveness/output join.
- [bundle_static_runtime_iramp_baseline_seed_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_iramp_baseline_seed_four_zoom.md)
  SHA-pinned proof that `0x36b920` initializes every numerator coefficient as exact float32 `0.2f * forward97(src2)` while all five baseline denominator vectors are `0.2f`, joined to a baseline identity reconstruction and prior complete four-focal IRAMP liveness.
- [bundle_static_runtime_iramp_candidate_policy_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_iramp_candidate_policy_four_zoom.md)
  Exhaustive SHA-pinned `0x3661b0` census closing local projected-pair, record-append, sentinel-skip, post-WTA rewrite, and continuous-score policy, joined to prior complete four-focal runtime liveness; final-file consequence is closed by the following differential.
- [lldb_final_iramp_score_image_effect_wide_tele.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_final_iramp_score_image_effect_wide_tele.md)
  Return-only `t=0` LLDB intervention with exact live-byte receipts, repeated control floors, and completed full-resolution Radiance outputs at canonical Unit-1 `35mm` and `70mm`, joined to complete four-focal score-use and post-IRAMP descriptor-to-writer custody.
- [bundle_static_runtime_prefusion_monofusion_mode_selector_profiles.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_prefusion_monofusion_mode_selector_profiles.md)
  SHA-pinned MonoFusion selector/constructor/worker custody plus same-LRI profiles `0..3`, two-body wide mode-0 joins, and tele no-MonoFusion joins, proving mode `1` is reachable for profiles `1` / `2` but excluded from canonical profile `3`.
- [bundle_static_runtime_prefusion_monofusion_mode1_formula_two_body.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_prefusion_monofusion_mode1_formula_two_body.md)
  SHA-pinned profiles-`1/2` MonoFusion mode-1 formula with exact separable five-tap low-pass, high-pass confidence gate, both-axis nearest-edge extension, live invalid-overlap fallback, and a `272,484`-cell exact final-tile replay across scoped Unit-1 `35mm` plus Unit-2 exact-`28mm` runtime.
- [bundle_static_runtime_prefusion_parent_identity_closure_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_prefusion_parent_identity_closure_four_zoom.md)
  Rechecked installed/runtime proof join reconciling the prefusion parent row with exact one-camera `ReferenceImageCache` `src1`, `processLevel1` `src2`, canonical wide mode-0 / tele direct-B4 ancestry, and distinct outer IRAMP operand roles.
- [bundle_static_runtime_tele_firing_topology_two_body.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_tele_firing_topology_two_body.md)
  Dedicated `CLM-ZOOM-002` proof joining exact-focal two-body public tele headers to completed canonical Unit-1 `70mm` / `150mm` constructor runs: the initial firing set is `B1..B5,C1..C6`, not C-only.
- [bundle_static_runtime_demosaicklightv1_exact_formula.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_demosaicklightv1_exact_formula.md)
  SHA-pinned four-phase `DemosaickLightV1` formula, corrected phase ownership and derived-plane boundary policy, exact residual construction, and refutation of the old five-level interpretation.
- [bundle_corrective_static_runtime_demosaicklightv1_fullframe_two_body.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_corrective_static_runtime_demosaicklightv1_fullframe_two_body.md)
  Corrective full-frame proof: exact Unit-1/Unit-2 `28mm` clean-room RGBA replays, tiled `A/B` intermediate equality, exact instruction ordering, finite virtual guide halos, and asymmetric residual guards.
- [bundle_static_runtime_awb_public_origin_four_zoom_two_body.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_awb_public_origin_four_zoom_two_body.md)
  Embedded public `ViewPreferences.awb_gains` schema, legacy/wrapped LRI layouts, complete 9,438-file corpus validity census, and exact four-zoom/two-body reciprocal joins to demosaic and post-square consumers.
- [bundle_static_runtime_index5_skip_mask_policy_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_index5_skip_mask_policy_four_zoom.md)
  SHA-pinned installed pattern-2 generator, direct Unit-1 index-5 receipt and exact 768-task grid, plus an independent per-task MT19937 replay equal to every byte of all four canonical Unit-1 full Skip masks.
- [bundle_static_runtime_index5_disparity_lane_convention_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_index5_disparity_lane_convention_four_zoom.md)
  Installed splice proof and all 67 accepted Unit-1 four-focal recurrence packets resolving `d-1/d/d+1` as farther/current/nearer on the reciprocal ray-depth hypothesis axis.
- [bundle_static_runtime_reference_stage_artifacts_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_reference_stage_artifacts_four_zoom.md)
  SHA-pinned `ImageLensUndistort` / `SourceImageCache` custody, 20 complete public-camera-keyed four-focal RGBA16F undistorted planes, all 16 complete depth/disparity base artifacts, byte-identical `28mm` undistorted repeats, and the scoped refutation of one deterministic tele depth-map golden.
- [bundle_runtime_index5_repeat_distributions_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_runtime_index5_repeat_distributions_four_zoom.md)
  Ten complete index-5 hypothesis/depth samples per focal, 180 pair comparisons, exact class counts `4/2/10/10`, and a 129,792,000-pixel bit-exact lookup-coupling proof defining the nondeterministic-map validation oracle.
- [bundle_static_runtime_state_object_semantics_closure.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_state_object_semantics_closure.md)
  Thirteen-verifier operational closure of canonical State, CapturedImage, CalibStage, derived-record, publication, downstream formula, and validation semantics, with anonymous padding and diagnostic labels explicitly excluded.
- [bundle_static_runtime_lri_firing_set_variants_full_corpus.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_lri_firing_set_variants_full_corpus.md)
  Full 9,438-file public firing-set census proving exact `A1 -> wide` / `B4 -> tele` reference-camera topology across all 9,242 complete LRIs, identifying three valid focal/topology exceptions, and completing profile-3 Radiance renders for all three.
- [bundle_static_runtime_nlm_weight_formula_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_nlm_weight_formula_four_zoom.md)
  SHA-pinned installed-body proof and Unit-1 28mm live operand replay for the selected PatchNLM L1/max/tent law, coefficient construction, reciprocal normalization, and lane-3 preserve policy, joined to prior four-focal route liveness.
- [bundle_static_runtime_unsharp_formula_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_unsharp_formula_four_zoom.md)
  SHA-pinned Lab-`L*` difference-of-Gaussians worker proof, exact four-focal live combine replay, direct public five-field packet custody, exact vibrance route and gain/amount/scale kernel-width formula, and complete Unit-1 28mm seven-family generated-kernel census.
- [bundle_static_runtime_iramp_forward_ohta_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_iramp_forward_ohta_four_zoom.md)
  SHA-pinned direct-contributor and `src2` application-point proof for the exact installed RGB-to-I1/I2/I3 transform, both live coefficient-column captures at Unit-1 `28mm`, negative proof that `0x36b920` does not mix color channels, and a machine-reverified four-focal IRAMP liveness join.
- [bundle_static_runtime_supported_variant_pipeline_routes_two_body.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_supported_variant_pipeline_routes_two_body.md)
  Full-corpus public selector join plus complete two-body runtime closure for both `28mm`/tele and the `74mm`/wide supported exceptions: scorer incidence, primary stereo/range/upsample path, MonoFusion/C6 behavior, five warp records, exact direct contributor IDs, IRAMP scale/reducer, public crop/orientation, and completed HDR.
- [bundle_static_runtime_movable_mirror_pose_formula_two_body.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_movable_mirror_pose_formula_two_body.md)
  Embedded-schema, SHA-pinned installed-formula, Unit-1 four-focal, and exact-focal Unit-2 `70mm` proof of the public type-0 quadratic Hall-to-angle inversion and exact reflected-camera `R,t` construction for all selected movable B/C cameras.
- [bundle_static_runtime_editor_profile3_topology_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_editor_profile3_topology_four_zoom.md)
  SHA-pinned installed Lumen call-graph proof plus profile-3 RenderType-1 four-focal runtime census: initial GUI-style pyramid construction reaches the admitted IRAMP and `src1`/`src2`/contributor wrapper topology with the canonical wide-MonoFusion/tele-direct split; one tested 28mm brush edit then issues five rerender requests with zero post-marker IRAMP, wrapper, MonoFusion, stereo-index, or calibration-composition hits.
- [bundle_static_runtime_new_calibration_package_corpus_two_body.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_new_calibration_package_corpus_two_body.md)
  Two-body standalone-package-to-photograph calibration join across 81 new complete LRIs; body-label reversal, common SensorData invariance across 9,323 complete photographs, decoded zoom/hot-pixel package boundaries, and clean-exit zero-hit hot-pixel-leakage probes at 64mm, 71mm, and old-firmware 150mm.
- [bundle_static_runtime_editor_display_packing_28mm.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_editor_display_packing_28mm.md)
- [bundle_static_runtime_editor_acre_formula_28mm.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_editor_acre_formula_28mm.md)
  SHA-pinned installed Lumen/libcp proof plus clean-exit Unit-1 28mm captures: exact five-level editor pyramid; live type-13 `requestRenderROI` record separated from public type-4 serialization; exact `RendererPrivate::$_2 -> 0x3bb2b0` producer; tested default level-4 `lt::PipelineCache ->` per-level Color-pipeline route; byte-exact HDR-input/before-call and editor-float/after-call joins; exact active indices `3,10,11,12,13,14,15` named by RTTI; nearest/even `255*float` saturated packing; conditional `GL_BGRA`/`GL_RGBA` policy; and all-opaque alpha. Remaining display-specific callback formulas and alternate DOF/mode behavior remain open.
- [bundle_static_runtime_editor_color_correction_public_origin_28mm_two_body.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_editor_color_correction_public_origin_28mm_two_body.md)
  Embedded-schema/two-body public `macbeth_data` extraction; SHA-pinned fixed target, CIEDE2000, Ceres 1.12 options, and TPS formulas; independent exact 3x3 optimizer and white-normalized wrapper endpoint; unique live camera-0 A/D65 selection; distinct exact map/matrix mired interpolation; and `0/5,101,248` differing bytes in the retained Unit-1 28mm default-level-4 display index-10 replay.
- [bundle_static_runtime_editor_dof_public_route_28mm.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_editor_dof_public_route_28mm.md)
  Installed/runtime proof joining public `Settings.DOF.f_num/focus_depth` to the exact mode-1 cache predicate, 388/388 live DOFCache reads, and a changed final packed level-4 buffer at one Unit-1 `28mm` treatment. Internal DOF blur/depth-compositing math and other modes/focals/bodies remain open.
- [bundle_static_runtime_editor_dof_optical_radius_formula_28mm.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_editor_dof_optical_radius_formula_28mm.md)
  Installed optical-table and public `sensor_data_surface.data_scale` pitch-origin proof, plus exact x86 replay of 64 live focus-range calls and all seven observed tile-radius result buckets at one Unit-1 `28mm` mode-1 treatment. Circle filtering, layered/occlusion composition, other modes, and other-focal runtime remain open.
- [bundle_static_runtime_editor_dof_circle_filter_28mm.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_editor_dof_circle_filter_28mm.md)
  SHA-pinned exact uniform integer-disk kernels for the vec4 and scalar DOF circle filters, including binary32 normalization, clamped-edge replication, incremental operation order, and one Unit-1 `28mm` live radius/call census.
- [bundle_static_runtime_editor_dof_layer_compositor_28mm.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_editor_dof_layer_compositor_28mm.md)
  SHA-pinned installed and Unit-1 28mm runtime closure for mode-1 signed layer construction/membership, three-neighbor opacity, native/scaled disk-plus-Gaussian dispatch, exact 64-phase cubic B-spline resampling, and reverse premultiplied source-over.
- [bundle_static_runtime_editor_rendering_modes_28mm.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_editor_rendering_modes_28mm.md)
  Parsed public five-value RenderingMode enum and exact libcp dispatch; controlled Unit-1 28mm five-mode route/output census; complete live 11-key DebugView selector/target/output census; exact default all-zero QuickSelect-mask blend/no-op proof; and one active public stroke producing a binary mask whose 501 sampled pixels exactly equal final packed-output change support.
- [bundle_static_runtime_editor_refocus_slider_formula_28mm.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_editor_refocus_slider_formula_28mm.md)
  SHA-pinned installed Rec.601, fast base-2 depth-mask, and cyan-blend formulas, with exact replay of 108,720,348 scalar pixels, 108,720,348 mask pixels, and 434,881,392 output lanes at one Unit-1 28mm RefocusSlider treatment.
- [bundle_static_runtime_editor_refocus_point_overlay_28mm.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_editor_refocus_point_overlay_28mm.md)
  SHA-pinned installed RefocusPoint strict-range predicate and red/alpha blend, with all-inside and mixed-outcome Unit-1 28mm treatments each replaying 434,881,392 output lanes exactly.
- [bundle_static_runtime_create_stereo_a2_public_reconstruction_two_body.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_create_stereo_a2_public_reconstruction_two_body.md)
  Public-LRI-to-float closure for wide A2: exact RAW10/sensor-level/vignetting/exposure reconstruction of 38,937,600 scalar pixels and 155,750,400 replicated vec4 words across two Unit-1 scenes and a distinct exact-focal Unit-2 calibration.
- [bundle_static_runtime_index5_sgm_cost_input_normalization.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_index5_sgm_cost_input_normalization.md)
  SHA-pinned installed formula plus exact-focal two-body `28mm` raw-to-normalized-to-recurrence custody proving binary32 `(1/27)/source_count` local-cost scaling and refuting a per-pixel band-min pedestal before G-43.
- [bundle_static_runtime_index5_skip_consumption_two_body.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_index5_skip_consumption_two_body.md)
  SHA-pinned branch/recurrence/argmin proof plus exact-focal two-body `28mm` captures proving nonzero pattern-2 mask pixels use zero unary cost but still receive ordinary SGM-regularized Cost-volume records and depth indices before guided upsample.
- [bundle_static_runtime_create_stereo_color_normalization_vignetting_two_body.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_create_stereo_color_normalization_vignetting_two_body.md)
  SHA-pinned selected color-camera stage proof: exact public `black_level`/`white_level` Bayer normalization and exact half-resolution public `17x13` vignetting replay over Unit-1 A1, distinct-calibration Unit-2 A1, and Unit-1 movable key 6 with four-model public mirror-position selection.
- [bundle_static_runtime_prefusion_monofusion_operand_pyramid_two_body.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_prefusion_monofusion_operand_pyramid_two_body.md)
  Exact public-input construction of both mode-0 MonoFusion flow operands plus SHA-pinned `2/4/4/4` FastCollapse reduction: complete two-body level-0 joins and `13,843,912/13,843,912` generated pyramid samples with exact kernels, phases, edge clamp, float32 order, and uint16 truncation.
- [bundle_static_runtime_prefusion_monofusion_mode0_patch_terminal_exact_replay.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_prefusion_monofusion_mode0_patch_terminal_exact_replay.md)
  Corrective installed/runtime mode-0 proof: complete public-vignetting auxiliary map and exact `8x8` mean origin, corrected target/source Wiener roles, direct row-before-column inverse checkpoints, signed-int16 low-word flow packing including rejected-vector wrap, one exact 256-word live forward/Wiener/inverse patch, and all `272,484` terminal tile cells exact at Unit-1 `28mm`, with explicit four-focal route scope.
- [bundle_static_runtime_prefusion_monofusion_mode0_full_overlap_exact_replay.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_prefusion_monofusion_mode0_full_overlap_exact_replay.md)
  Complete clean-room mode-0 scalar overlap replay: exact 4,489-patch lattice, 3,517 valid-source transforms, 972 spatial target bypasses, exact float32 overlap table/order, independently clipped auxiliary/target edge statistics, one exact remainder-patch packet, and all `272,484` pre-combine cells bit-identical at Unit-1 `28mm` with explicit four-focal route scope.
- [bundle_static_runtime_index5_nondeterminism_mechanism_two_body.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_index5_nondeterminism_mechanism_two_body.md)
  SHA-pinned bit-level proof that executor-parallel mode-8 G-43 workers perform an unsynchronized shared saturating-u16 payload RMW; four-focal same-address/multi-thread writes, live Unit-2 index-5 overlap, exact reproduction of the `52.88%` repeat statistic, upstream parent-gate scheduler sensitivity, and byte-identical deterministic-order controls across Unit-1 wide/tele plus Unit-2 tele. This closes the mechanism and suppressibility of observed profile-3 depth nondeterminism, while leaving the first unsafe instruction in separate pre-G42 producers outside scope.
- [bundle_static_runtime_cnr_lane3_u8_weight_origin_unit1_70mm.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_cnr_lane3_u8_weight_origin_unit1_70mm.md)
  SHA-pinned installed and Unit-1 70mm runtime proof identifying the CNR lane-3 source representation as `FusionCacheBayer+0xe0` `TileCache<unsigned char>`, closing the exact one-plane LUT/scalar/square operation order and installed two-/three-plane fixed-point combiners, and correcting the prior RTTI-context overclaim. Upstream byte-plane production/public meaning, scalar origin, route breadth, and complete CNR tile replay remain open.
- [bundle_runtime_colorfusion_f_formula_selection_profile3.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_runtime_colorfusion_f_formula_selection_profile3.md)
  Raw Unit-1 28mm transformed-patch capture and bit-exact four-lane Wiener/quadratic-combine replay, plus two-body wide/tele direct ordered camera vectors and `0/1024`-word normalized-transform replays, SHA-pinned installed selection, and profile-3 AR1335 `+0xcc` origin. Corrects the independent-lane, byte-identity, and ascending-camera-order overclaims and directly demonstrates the current Phoenix port mismatch.
- [bundle_static_runtime_colorfusion_noise_public_origin_two_body.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_colorfusion_noise_public_origin_two_body.md)
  SHA-pinned installed and direct Unit-1-wide/Unit-2-tele proof closing public AUTO scene-neutral HighlightRestore gain, parity-preserving full-frame target preprocessing, fixed-spatial reciprocal-signal reduction, public coarse vignetting, and exact four-lane SensorGainVars noise-provider output. Complete target/signal/shading tables and both full HighlightRestore frames replay bit-for-bit; source-plane/overlap/u8/CNR tile integration remains open.
