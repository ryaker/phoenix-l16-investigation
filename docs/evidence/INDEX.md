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
- `bundle_proof_prefusion_callable_gate_four_zoom.md`
  Installed-bundle plus LLDB runtime proof bounding the sampled prefusion `state+0x220` callable gate to inline false-return predicate bodies on the canonical four-zoom bridge HDR quartet.
- `bundle_proof_prefusion_candidate_scoring_family_four_zoom.md`
  Installed-bundle plus LLDB runtime proof bounding the `0x24c320` / `0x24d610` prefusion candidate-scoring families and local patch/search helpers on the canonical four-zoom bridge HDR quartet.
- `lldb_iramp_wrapper_accumulator_four_zoom.md`
  LLDB runtime proof that the canonical four-zoom bridge HDR quartet all hit the visible `src1` wrapper, `src2` wrapper, contributor wrapper, and IRAMP accumulator surfaces at `0x3ecc10`, `0x3ecd80`, `0x3eced0`, and `0x369fa1`.
- `lldb_iramp_entry_signature_four_zoom.md`
  LLDB runtime proof that the canonical four-zoom bridge HDR quartet all enter `0x365960` with `src1`, `src2`, `srcs[5]`, `warps[5]`, scale, and ROI.
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
  LLDB runtime proof that the direct payload candidate loop at `0x3e0330` visits keys `0..9` at `28mm`/`35mm` and `5..15` at `70mm`/`150mm`; tele key `15` / C6 reaches the loop but has `object+0x30 = 0`, skips before class compare, and never reaches the `0x3e05f5 -> 0x3f6170` dispatcher call under canonical bridge HDR runs.
- `lldb_stereo_candidate_gate_c6_four_zoom.md`
  LLDB runtime proof that the stereo-side keyed-record loop inside the `0x3f2c40` constructor branch visits keys `0..9` at `28mm`/`35mm` and `5..15` at `70mm`/`150mm`; tele key `15` / C6 reaches the loop but has `object+0x30 = 0`, skips before the post-gate path, and never reaches either tested `0xf2720` getter callsite under canonical bridge HDR runs.
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
- `bundle_proof_src1_region_adapter_helper_2e8680.md`
  Installed-bundle proof bounding helper `0x2e8680`, called by the selected `0x341770` visible-`src1` region-adapter body, to one-source Bayer/RAW region helper work with callback vtable `0x659fc0` and substantive slot `0x2e8cc0`; this is not reducer, C6-routing, final blend, or acceptance closure.
- `lldb_iramp_partner_gate_four_zoom.md`
  Installed-bundle plus repo-local LLDB proof bounding the local IRAMP partner-vector gate at `0x3692dc..0x3692e4`, the `0x280` partner-record stride, the empty-vector jump to the accumulator region, and first SAD participation at `0x3694b1`; non-empty gate and first SAD are runtime-observed on the canonical four-zoom quartet, while empty-gate runtime hits are observed only at `28mm` and `70mm`.
- `bundle_lldb_iramp_partner_record_population.md`
  Installed-bundle plus repo-local LLDB proof bounding the upstream partner-record append/population path: the first populated record path reaches `0x368b02` on the canonical four-zoom quartet, and the physical `0x280` record layout is four int32 scalar fields plus thirteen contiguous `0x30` descriptor-like blocks. Field semantics, complete candidate predicate, and final acceptance/rejection remain open.
- `bundle_lldb_iramp_refined_tuple_four_zoom.md`
  Installed-bundle plus repo-local LLDB proof bounding the live non-empty partner-record consumer path through coarse SIMD SAD / `phminposuw` winner selection, local absolute-difference refinement, guarded float refinement, 16x16 bilinear vec4 resampling, `0x36cde0`, and the three-float scratch write at `0x369e7e..0x369e91` across the canonical four-zoom quartet. Public field semantics and final acceptance/rejection remain open.
- `bundle_lldb_iramp_36cde0_scalar.md`
  Installed-bundle plus repo-local LLDB proof narrowing the third refined-tuple field: `0x36cde0` consumes the two prepared 16x16 `vec4` patches, runs patch-statistics / fixed-transform / weighted-reduction work, returns `sqrt(xmm0 * xmm1)`, and the caller stores that live `xmm0` scalar as the tuple's third float at `0x369e91`. Public field semantics remain open; the first downstream tuple consumer is covered by `bundle_lldb_iramp_tuple_downstream_consumer.md`.
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
- `bundle_proof_calibdataprocessor_lambda_family.md`
  Installed-bundle proof for the upstream `CalibDataProcessor::State()` lambda / runner family.
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
