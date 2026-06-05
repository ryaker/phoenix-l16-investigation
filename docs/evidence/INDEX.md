# Evidence Index

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
  Installed-bundle plus repo-local LLDB proof binding the `0x24c320` / `0x24d610` candidate-scoring output vectors to the shared `0x2439b0` record-state gate by exact output-vector pointer continuity across complete canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR renders. This is scorer-output custody proof, not reducer closure.
- `bundle_lldb_prefusion_record_state_gate_histogram_four_zoom.md`
  Installed-bundle plus repo-local LLDB proof bounding `0x2439b0` as a live record-state gate for the custody-bound candidate-scorer output vectors: admitted wide family-A runs are unchanged at the boundary, admitted tele family-B runs promote target-2 records from state `3` to state `4`, and sampled downstream `0x241fd0` / `0x2416d0` / watched-store sites did not match the exact known scorer-output vector under this probe. This is record-state boundary proof, not reducer closure or final acceptance/rejection.
- `bundle_lldb_prefusion_promoted_record_watch_tele.md`
  LLDB hardware data-watch proof that selected tele records promoted by `0x2439b0` from `(state=3,target=2)` to `(state=4,target=2)` are later consumed in clean canonical `70mm` / `150mm` renders and at least one watched record per tele seed advances to `(state=5,target=2)` through `0x2416d0`. This is downstream consumer proof for watched promoted records, not public state semantics, final image contribution, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_state5_selected_index_path_tele.md`
  LLDB runtime proof that promoted target-2 record indices captured at `0x2439b0` later enter concrete `0x2416d0` selected-index vectors under clean canonical `70mm` / `150mm` renders, and that the small promoted sets captured here are observed reaching `(state=5,target=2)` stores. This is selected-index/state-relabel proof, not public acceptance semantics, final image contribution, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_state5_later_watch_tele.md`
  LLDB hardware data-watch proof that watched promoted tele records that become `(state=5,target=2)` continue downstream into the `0x244560` heavy-consumer family and the already-bounded `0x25d090` candidate block-geometry / active-block helper family. This is later state/candidate/geometry flow, not image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_state5_coord_output_four_zoom.md`
  LLDB runtime proof that `0x2457c0` is live and normally returning across the canonical `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR quartet, sampled hits at the admitted `0x24593b` store-path site have `record+0x24 == 5`, and every admitted return leaves finite non-sentinel coordinate pairs in `state+0x1e8`. This is coordinate-output materialization proof, not image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_state5_coord_consumer_watch_four_zoom.md`
  LLDB hardware read-watch proof that representative finite non-sentinel coordinate pairs emitted by `0x2457c0` into `state+0x1e8` are later read by `0xe8e70` vector-copy work under both State-helper copy-out paths (`0x224d70 -> 0x245a40` and `0x224e50 -> 0x245a20 -> 0x244560`) across the canonical four-zoom bridge HDR quartet. This is coordinate-vector custody / copy-out proof, not image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_state5_coord_copy_dest_watch_four_zoom.md`
  LLDB hardware read/write-watch proof that representative finite non-sentinel destination pairs copied out by the State-helper `0xe8e70` path are touched again by `0xe8e70` vector-copy work across the canonical four-zoom bridge HDR quartet. Static/runtime evidence binds the admitted later caller frames to State-helper recopy sites plus higher node-vector materialization/copy sites at `0x22a61a -> 0xe8e70 -> 0x22a61f` and `0x22c93a -> 0xe8e70 -> 0x22c93f`. This is coordinate-vector custody / propagation proof, not image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_state5_coord_node_dest_watch_four_zoom.md`
  LLDB hardware read/write-watch proof that representative finite non-sentinel destination pairs copied into the `0x22a61a -> 0xe8e70 -> 0x22a61f` node-vector destination reach non-copy candidate/index/scoring-selection code under `0x21b2e0` and its `0x21c4f0` callback path across the canonical four-zoom bridge HDR quartet. The capped window proves at least one finite node-destination pair per run, not all copied pairs; it is not image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_node_sentinel_write_four_zoom.md`
  LLDB runtime/static proof that the downstream `0x21b2e0` path executes coordinate-pair sentinel invalidation writes at `0x21b923` and `0x21b92a` across the canonical four-zoom bridge HDR quartet. Runtime samples show finite non-sentinel coordinate pairs before the x-lane store and x already changed to `-1.0` before the y-lane store; static disassembly proves both stores write raw bits `0xbf800000` (`-1.0`). This is coordinate invalidation/rejection write proof, not image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_lldb_prefusion_node_sentinel_downstream_watch_four_zoom.md`
  LLDB hardware read/write-watch proof that selected sentinel-marked node-vector coordinate pairs are touched later by downstream code across the canonical four-zoom bridge HDR quartet. Watchpoints were armed only after the full pair read `(-1.0, -1.0)` immediately after `0x21b92a`, and every sampled later touch still observed `(-1.0, -1.0)`. Sampled downstream surfaces include State-family copy/record propagation plus coordinate scan/scoring/materialization windows. This is downstream sentinel-coordinate custody / consumption proof, not image-effect proof, source-contribution proof, reducer closure, or final acceptance/rejection.
- `bundle_static_prefusion_state_22ae60_copy_record_surfaces.md`
  Static + reused runtime proof classifying the sampled State-family `0xe0ae0` copy callers under `0x22ae60`: `0x20bd60` / `"point BA"` is keyed record materialization, `0x25e4b0` is the no-map `0x25e0c0` row-producer variant, `0x20dca0` is keyed record storage, `0x20ca00` is selected Ceres setup with positive-coordinate gates, and `0x239ac0` / `0x239e00` are keyed pair-vector propagation surfaces. This prevents treating those sampled windows as opaque possible reducers; it does not prove image effect, reducer closure, or final acceptance/rejection.
- `bundle_static_prefusion_sentinel_216f60_scan_count_window.md`
  Static + reused runtime proof that sampled tele sentinel-coordinate stops inside the `0x216f60` scan/count window still read `(-1.0, -1.0)`, while static disassembly proves that the local vector/scalar count paths count only pairs where both lanes are positive and require at least eight counted entries before continuing. This is local non-counting proof for sampled sentinel reads, not exhaustive terminality, image-effect proof, reducer closure, or final acceptance/rejection.
- `bundle_static_prefusion_sentinel_20b5e0_branch_window.md`
  Static + reused runtime proof that the sampled `0x20b912` downstream sentinel stops across the canonical four-zoom quartet sit immediately after an x-lane load from a still-sentinel `(-1.0, -1.0)` pair, and that the local static `0x20b5e0` branch/write window has a nonpositive/sentinel path that bypasses the `0x20bac0..0x20bac8` update writes. This is local branch-boundary proof for sampled sentinel reads, not exhaustive terminality, image-effect proof, reducer closure, or final acceptance/rejection.
- `lldb_iramp_wrapper_accumulator_four_zoom.md`
  LLDB runtime proof that the canonical four-zoom bridge HDR quartet all hit the visible `src1` wrapper, `src2` wrapper, contributor wrapper, and IRAMP accumulator surfaces at `0x3ecc10`, `0x3ecd80`, `0x3eced0`, and `0x369fa1`.
- `lldb_iramp_entry_signature_four_zoom.md`
  LLDB runtime proof that the canonical four-zoom bridge HDR quartet all enter `0x365960` with `src1`, `src2`, `srcs[5]`, `warps[5]`, scale, and ROI.
- `lldb_iramp_count_use_vector_four_zoom.md`
  LLDB runtime proof that the live `0x3661b0` count-use window at `0x366a50..0x366a65` reads a vector header through `r15+0x18`, computes `(end-begin)/16`, and reaches `0x366a65` with live count `5` across 16 capped packets per canonical focal tier. This is count-use evidence only, not a complete reducer proof.
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
- `bundle_lldb_owner_f0_global_rowcache_segments.md`
  Installed-bundle plus repo-local LLDB proof removing the first-dispatch boundary for `0x372760` row-cache segments. Complete canonical bridge HDR renders show row-plan return `0x3722b0` live at all four zooms; leading/trailing store sites are live at `28mm` and `70mm`, and have zero hits at `35mm` and `150mm` under the tested canonical runs. First captured leading/trailing samples at `28mm` and `70mm` match the reconstructed 4-tap horizontal `vec4` formula. Public field names, downstream row-image/final policy, and final acceptance/rejection remain open.
- `bundle_proof_pair_grid_roi_transform.md`
  Installed-bundle proof that IRAMP's first pair grid is ROI-derived, that a second same-sized transformed pair grid is produced from it, and that the transformed-grid bbox feeds the later clipping / zero-fill helper path.
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
  after `0x264440`, the `rbp-0x378` output record changes across
  `0x23cbbc -> 0x23faf0`, remains stable through later node writes, and mapped
  output fields are materialized into local tree-node fields in all `104`
  admitted four-zoom groups. This is helper-record-to-local-tree custody proof,
  not public field semantics, post-`0x23c5f0` image effect, reducer closure, or
  final acceptance/rejection.
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
- `bundle_proof_prefusion_feature_selection_lane.md`
  Installed-bundle proof bounding the visible `0x258fe0` / `0x2598a0` feature-selection lane away from reducer closure.
- `bundle_proof_prefusion_reducer_arithmetic_static.md`
  Deterministic closed-form verification that the 16 accumulator weights captured in `bundle_lldb_iramp_36e530_accumulator_prep.md` are the periodic (DFT-even) Hann window of length 16, `w[n] = sin²(π(n+0.5)/16)`, to float32 precision (max residual 1.13e-7; symmetric Hann ruled out at 5.70e-2; taps sum to N/2 = 8.0). Scoped to the window closed form only; does not identify the `src1`/`src2` reducer and does not advance `CLM-PREFUSION-002`.
- `bundle_proof_two_unit_corpus_static.md`
  Per-file machine-verified identification of TWO physical L16 units across the whole corpus by intrinsics calibration SHA-256 (Unit-1 `722a6e72…` 5724 files; Unit-2 `223961c6…` 3484 files). Proves folders are date-organized not unit-organized (13 date-folders mix both units). REFUTES the prior Unit A/B labeling — all four canonical seeds are Unit-1, so every "four-zoom verified" claim was one body × four focals, not two bodies (universality unproven). Lists the Unit-2 same-name twin seeds (true cross-unit four-zoom set). 182/9390 files unassigned (parser gap, not a third unit).
- `bundle_proof_lri_calibration_origin_static.md`
  Independently re-verified static facts (Lane B / WSJF #2): the three calibration blocks (intrinsics/distortion/depthcfg) are byte-identical across the four canonical LRIs; the 16 intrinsics records are pairwise distinct (genuine per-camera calibration); the full sensor ROI 4160×3120 is LRI-stored while all pyramid/level dims are libcp-computed halvings. Parity consequence: Phoenix must parse per-camera calibration + sensor ROI from each LRI (supports standalone distribution). Includes a scoped, human-flagged observation that all four LRIs share identical calibration (likely one body) without rewriting the Unit A/B doctrine.

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
