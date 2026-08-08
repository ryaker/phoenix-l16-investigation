# Evidence: Index-5 Depth Path Public-Meaning Gap Audit, Four Zoom

**Frame-index follow-up (2026-06-30):**
`bundle_static_runtime_capturedimage_frame_index_public_origin.md`
subsequently names observed `object+0x64` as public
`CameraModule.frame_index` and the matched RawImageFactory key as its selected
frame index. Statements below that leave `object+0x64` unnamed preserve this
audit's original proof boundary.

**CalibStage follow-up (2026-06-30):**
`bundle_static_runtime_calibstage_public_names_two_body.md` subsequently maps
numeric `CalibStage 0=factory` at `CapturedImage+0x180` and
`CalibStage 1=current` at `+0x12c`. Complete bank-field semantics remain open.

**Public-name follow-up (2026-06-19):** the installed bundle's serialized
protobuf descriptors now replace several anonymous paths in this audit with
exact public names. `LightHeader.field_12` is `LightHeader.modules`;
module fields `2/4/5/8/10` are `id`, `mirror_position`, `lens_position`,
`sensor_exposure`, and `sensor_temparature`; geometry `field_6` is
`CalibrationFocusBundle.focus_hall_code`; and the K/pose paths are named
`intrinsics.k_mat` and `extrinsics.canonical.rotation/translation`. See
[bundle_static_runtime_index5_public_proto_schema_names.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_index5_public_proto_schema_names.md).
Statements below that keep anonymous names describe this audit's original
proof boundary; the companion proof supersedes only those naming gaps.

**Distortion-origin follow-up (2026-06-26):** a two-body static/runtime
verifier now closes the public source of the `0x145980` box-producing
calibration record as
`LightHeader.module_calibration[camera].geometry.distortion.polynomial`.
Live center, normalization, complete coefficient-vector, and fit-cost words
match the same-camera public LRI records on Unit-1 wide and Unit-2 tele runs.
See
[bundle_static_runtime_state_448_distortion_polynomial_public_origin_two_body.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_state_448_distortion_polynomial_public_origin_two_body.md).

## Scope

This note audits the current Lane B evidence for the `StereoLayer<false>`
index-5 path that feeds the internally depth-labeled pair-grid map stored at
`record+0x40`.

Prompted question:

- trace `state+0xe0`, `state+0x448`, and `record+0x40` back to concrete public
  calibration / LRI origins and names;
- update canonical docs only if the current proof standard actually admits the
  result.

Bottom line: the current evidence admits a concrete internal name and custody
chain for `record+0x40`: it is the `lt::UpsampleLayer+0x90` descriptor whose
disabled debug dump is named `depth_... .dp`, built through `0x29ed90` from the
`StereoLayer<false>` index-5 source. Follow-up deterministic LRI parsing also
admits public camera/config carrier paths for the canonical LRIs:
`LightHeader.field_12[i].field_2` as camera id, raw
`LightHeader.field_12[i].field_4`, `field_5`, `field_8`, and `field_10`
module fields, and the 262,968-byte warp/calibration block's `field_13`
entries as 16 keyed per-camera nominal tables. Those public facts align with
the already admitted runtime projection-key subsets, but they still do **not**
prove the exact public LRI/protobuf field path into full `state+0xe0`, full
`state+0x448` beyond the scoped first-payload pose fields admitted below, or
the index-5 lookup/source records.

Follow-up `0xf2770` constructor reruns add one more admitted runtime/public
bridge: for the constructed CapturedImage-like object family, `object+0x60`
matches `LightHeader.field_12[camera].field_2`, `object+0x50` matches
`field_4` when present and `0` otherwise, `object+0x54` matches public
`field_5`, constructor input `+0x40` matches public `field_8`, and constructor
input `+0x48 * 2` matches public `field_10`. `object+0x64` is observed as
discriminator `0`, and `object+0x30` is constructed active (`1`). Fresh raw
captures of `object+0x10c`, `object+0x12c`, and `object+0x180` still do not
appear as exact byte copies inside the three LRI calibration payload classes.

Follow-up enriched `0xf33d0` reruns add a narrower positive public-origin
bridge for the State-helper path: wide-tier A1-A5 selector-0 packets exactly
match fixed32 fields in the 32,832-byte public intrinsics calibration block,
including the camera-keyed K matrix and compact pose record paths listed below.
A component-granularity verifier also proves exact public pose-record copies
for B4 in all four focal tiers and C5 in the tele tiers. The same verifier does
not admit exact public K-matrix copies for B4/C5, proves most other B/C-side
nontrivial fixed32 values are absent from the public calibration fixed32 index
under this check, and shows tele `0xf33d0` destination keys are `B1..C5`,
excluding public-fired `C6`. Therefore this audit narrows the public-meaning
gap but does not close the Lane B blocker and does not support a canonical
claim/status upgrade.

Follow-up `0x1f0ce0 -> 0xf33d0` producer verification localizes that B4/C5 K
gap one step earlier. The producer writes identical source records into both
accepted selector banks for each captured key; A1-A5 wide packets remain exact
public K/pose copies, while B4/C5 pose packets remain exact public copies and
their K packets are already zoom-variant non-exact records at this producer
edge. This supports derived / producer-local K treatment, not a public
protobuf field name for the full `CalibStage` or State records.

Follow-up `0x23faf0` record-chain reruns add another component-scoped guardrail
around the same conclusion: the pre-call left/right/output records around the
State-helper `0x23faf0` call contain exact public component matches listed in
[lldb_state_helper_23faf0_record_chain_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_state_helper_23faf0_record_chain_four_zoom.md), but the verifier records zero exact full 0xa4-byte source-record copies inside the LRI calibration payloads. This supports derived/composed-record treatment; it does not promote `state+0xe0` or `state+0x448` to public protobuf-field names.

Follow-up `state+0x448` payload-origin probing closes one first-payload slice:
the first visible insertion/update path copies payload `+0x00..+0x20` from the
public 32,832-byte intrinsics-block pose rotation component and payload
`+0x24..+0x2c` from the matching public translation component. The anchor is
`A1` for `28mm` / `35mm` and `B4` for `70mm` / `150mm`, and that anchor
component is shared across all first-pass inserted keys for the tier. The same
probe records zero exact public fixed32-sequence hits for the immediate later
`+0x30..+0x3c` source slices. Subsequent
[lldb_state_448_later_box_formula_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_state_448_later_box_formula_four_zoom.md)
probing closes formula-level meaning for that later slice: `+0x30/+0x34` is
uniform float32 scale and `+0x38/+0x3c` is float32 box origin from `0x260e40`
over the `0x145980(object)` box and `object+0x114/+0x118 = [4160,3120]`.
Companion static-origin proof in
[lldb_state_448_box_producer_static_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_state_448_box_producer_static_origin_four_zoom.md)
names that size pair as the LRI-stored full sensor ROI and bounds the box as a
computed distortion/undistortion envelope over owner-backed calibration data.
Together these admit component/formula/computed origins for payload
`+0x00..+0x3c` only; they do not assign a public semantic name to the whole
`state+0x448` payload or a public protobuf field number to the box-producing
calibration structure.

Follow-up index-5 lookup-vector probing closes the internal generator mechanics
for the tracked `StereoLayer<false>+0xe0` table: `0x26c480` builds a stack
vector through `0x28fa60` / `0x28f5a0` / `0x28f860`, `0xf02d0` copies it into
`this+0xe0`, and `0x267010` later consumes it unchanged. The retained object
fields at the copy point are `this+0x298/+0x29c = [200.0, 640000.0]`, and the
full vector exactly matches the installed helper's float32 reciprocal near/far
ramp from `640000.0` down to `200.0`. The verifier finds zero full-vector LRI
block hits, zero full public calibration fixed32-sequence hits, and zero scalar
fixed32 hits in the public calibration payloads. This admits an internal
generated near/far lookup table, not a direct public LRI/protobuf table.
Follow-up
[lldb_lookup_endpoint_count_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_lookup_endpoint_count_origin_four_zoom.md)
closes the endpoint/count producer mechanics as static binary endpoint
constants plus internal `0x28f5a0` source-record count math. A further
deterministic custody join in
[bundle_static_runtime_index5_triangulator_depth_bound_custody.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_index5_triangulator_depth_bound_custody.md)
proves that the selected `[200.0, 640000.0]` pair is also installed as the
lower/upper bound pair on the one-scalar Triangulator reprojection problem,
whose scalar scales ray `(bx,by,1)`. This closes the lookup vector's internal
role as a reciprocal ray-depth hypothesis grid. Public units, public
calibration/LRI/protobuf origin and names, source-record public names, and
public source-index names / physical semantics remain open.

Follow-up `0x29a140` source-local producer reruns now persist the complete
`2080 x 1560` 4-byte input descriptor and complete `2080 x 1560` byte mask
descriptor that feed the tracked `StereoLayer<false>+0xf8` record formula. The
source-local validator checks each dump by size and SHA-256, and the aggregate
verifier confirms zero exact hits for those full byte arrays in both the whole
LRI payload stream and the public calibration payload subset across all four
tiers. This rules out direct public byte-copy origin for those generated arrays
under this check; it does not exclude transformed or derived public origins and
does not assign public names to the input entries, mask bytes, or records.

Follow-up
[lldb_26d750_source_range_builder_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_26d750_source_range_builder_four_zoom.md)
closes the immediate internal source-index descriptor boundary that feeds that
`0x29a140` input. Across the canonical Unit-1 four-zoom corpus plus one Unit-2
exact-28mm spot check, `0x26d750` receives `source_layer+0x2a8`,
`source_layer+0x208`, target min/max fields, and mode `8`; builds a
`2080 x 1560`, stride-`2080`, 4-byte descriptor of `(lower,count)` `uint16`
pairs from half-resolution lower/upper range tables; and passes that populated
descriptor unchanged as `rsi` to `0x29a140`. Combined with the existing
`0x29a140` and `0x29a670` proofs, this admits the source-index descriptor's
internal role as per-pixel candidate ranges over the index-5 reciprocal
ray-depth lookup vector. It still does not assign public LRI/protobuf names,
source-record public names, public units, or final contribution semantics.

Follow-up
[lldb_276860_xmm4_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_276860_xmm4_origin_four_zoom.md)
closes one more internal source-record operand boundary: for one stepped
target-index-5 packet per focal tier, `%xmm4_low` is reconstructed exactly
from `xmm8 - [[rbp-0x208] + rdx]`, `object+0x60`, the observed
mask/blend/horizontal-sum/sign/clamp sequence, and local
polynomial/exponent-bit assembly before it feeds the already-admitted sampled
`%xmm3` pre-add term. This is an internal arithmetic origin, not a public
semantic name or public LRI/protobuf field origin for the operands.
Follow-up
[lldb_276860_operand_source_context_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_276860_operand_source_context_four_zoom.md)
then binds the immediate source context for that subtraction: sampled `%xmm8`
is loaded from the target object's `+0x200` vector table after a matched local
guide-byte conversion from target `+0x288`, `[rbp-0x208]` equals target
`+0x1e8`, and `[rbp-0x210]` equals target `+0x198`. A refreshed watchpoint
rerun also binds the final target qwords to same-object internal producer
stores: `+0x198` through `0x26ca94` (watch stop `0x26ca9b`), `+0x1e8`
through `0x26cbcd` (watch stop `0x26cbd4`), `+0x200` through `0x26cc01`
(watch stop `0x26cc08`), and `+0x288` through `0x26c633` (watch stop
`0x26c63a`). The same verifier checks the local buffer layout: `+0x198` is a
`16656`-entry `uint16` table base for this packet, `+0x200` is `33312` bytes
into the `+0x1e8` vector buffer, and the sampled subtraction vector is `16`
bytes past `+0x200`. This remains internal custody only, not public field
naming or physical meaning.
Follow-up
[lldb_index5_operand_public_origin_audit_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_index5_operand_public_origin_audit_four_zoom.md)
extends the aggregate verifier with exact byte-search checks for the sampled
operand guide-first16, guide-sample16, and subtraction-vector slices. All three
16-byte slices have zero exact hits in the whole LRI payload stream and zero
exact hits in the public calibration payload subset across all four tiers; the
subtraction vector also has zero exact public calibration fixed32-sequence
hits. The paired two-byte table value is reported only as a guardrail because
it is too small for a meaningful public-origin absence claim. This narrows the
gap but does not admit a public semantic name or a canonical status upgrade.

## Artifacts

- Existing runtime/static evidence:
  [lldb_iramp_map_provider_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_iramp_map_provider_four_zoom.md),
  [lldb_upsample_layer_depth_path.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_upsample_layer_depth_path.md),
  [lldb_upsample_29ed90_worker_formula.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_upsample_29ed90_worker_formula.md),
  [lldb_stereolayer_index5_depth_descriptor_custody.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_stereolayer_index5_depth_descriptor_custody.md),
  [lldb_index5_origin_classification_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_index5_origin_classification_four_zoom.md),
  [lldb_index5_267010_mapping_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_index5_267010_mapping_four_zoom.md),
  [lldb_source_index_299c70_producer_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_source_index_299c70_producer_four_zoom.md),
  [lldb_source_index_299c70_worker_formula_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_source_index_299c70_worker_formula_four_zoom.md),
  [lldb_index5_source_lookup_origin_watch_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_index5_source_lookup_origin_watch_four_zoom.md),
  [lldb_index5_source_object_field_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_index5_source_object_field_origin_four_zoom.md),
  [lldb_29a140_source_local_producer_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_29a140_source_local_producer_four_zoom.md),
  [lldb_26d750_source_range_builder_four_zoom.md](/Volumes/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_26d750_source_range_builder_four_zoom.md),
  [lldb_src1_projection_field_dispatcher_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_src1_projection_field_dispatcher_four_zoom.md),
  [bundle_proof_lri_calibration_origin_static.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_lri_calibration_origin_static.md),
  [bundle_proof_iramp_calib_object_accessors.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_calib_object_accessors.md),
  [bundle_proof_iramp_state_448_tree_builder.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_state_448_tree_builder.md),
  [bundle_proof_iramp_state_448_later_payload_writes.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_state_448_later_payload_writes.md),
  [bundle_proof_iramp_source_record_constructors.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_source_record_constructors.md),
  [bundle_proof_iramp_23faf0_composition_helper.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_23faf0_composition_helper.md),
  [lldb_state_helper_23faf0_record_chain_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_state_helper_23faf0_record_chain_four_zoom.md),
  [lldb_f33d0_1f0ce0_producer_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_f33d0_1f0ce0_producer_four_zoom.md),
  [lldb_1f0ce0_k_source_trace_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_1f0ce0_k_source_trace_four_zoom.md),
  [lldb_state_448_payload_public_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_state_448_payload_public_origin_four_zoom.md),
  [lldb_index5_lookup_vector_public_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_index5_lookup_vector_public_origin_four_zoom.md),
  [bundle_static_runtime_index5_triangulator_depth_bound_custody.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_index5_triangulator_depth_bound_custody.md),
  [lldb_capturedimage_f2770_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_capturedimage_f2770_origin_four_zoom.md),
  [lldb_276860_operand_source_context_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_276860_operand_source_context_four_zoom.md),
  [lldb_index5_operand_public_origin_audit_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_index5_operand_public_origin_audit_four_zoom.md)
- New tracked audit verifier:
  [lane_b_index5_public_meaning_audit.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lane_b_index5_public_meaning_audit.py)
- Patched reusable probe harness:
  [f2770_origin_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/capturedimage_f2770_origin/f2770_origin_probe.py),
  [run_four_zoom.sh](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/capturedimage_f2770_origin/run_four_zoom.sh),
  [state_helper_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helpers_23c5f0_f33d0_runtime/state_helper_probe.py),
  [verify_1f0ce0_producer.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helpers_23c5f0_f33d0_runtime/verify_1f0ce0_producer.py),
  [record_chain_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helper_23faf0_record_chain/record_chain_probe.py),
  [verify_record_chain.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_helper_23faf0_record_chain/verify_record_chain.py),
  [state_448_payload_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_448_payload_public_origin/state_448_payload_probe.py),
  [verify_state_448_payload_public.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_448_payload_public_origin/verify_state_448_payload_public.py),
  [lookup_vector_public_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_index5_lookup_vector_public_origin/lookup_vector_public_probe.py),
  [verify_lookup_vector_public_origin.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_index5_lookup_vector_public_origin/verify_lookup_vector_public_origin.py),
  [verify_20ca00_depth_bound_custody.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_depth_bound_custody.py),
  [source_local_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_29a140_source_local_producer/source_local_probe.py),
  [validate_reports.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_29a140_source_local_producer/validate_reports.py),
  [source_range_builder_probe.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_26d750_source_range_builder/source_range_builder_probe.py),
  [verify_source_range_builder.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_26d750_source_range_builder/verify_source_range_builder.py),
  [xmm4_origin_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_276860_xmm4_origin/xmm4_origin_probe.py),
  [validate_xmm4_origin.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_276860_xmm4_origin/validate_xmm4_origin.py),
  [operand_source_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_276860_operand_source_context/operand_source_probe.py),
  [verify_operand_source.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_276860_operand_source_context/verify_operand_source.py)
- Raw reports checked by the verifier:
  `runs/iramp_map_provider_runtime/`,
  `runs/projection_field_dispatcher/`,
  `runs/capturedimage_f2770_origin/`,
  `runs/state_helpers_23c5f0_f33d0_runtime/`,
  `runs/state_helper_23c5f0_exit_snapshot/`,
  `runs/state_helper_f34e0_match_runtime/`,
  `runs/state_helper_23faf0_record_chain/`,
  `runs/state_448_payload_public_origin/`,
  `runs/codex_index5_lookup_vector_public_origin/`,
  `runs/stereo_candidate_gate/`,
  `runs/codex_276860_xmm4_origin/`,
  `runs/codex_276860_operand_source_context/`,
  `runs/codex_index5_source_lookup_origin_watch/`,
  `runs/codex_index5_source_object_field_origin/`,
  `runs/codex_29a140_source_local_producer/`,
  `runs/codex_26d750_source_range_builder/`

## Verification

Command:

```bash
python3 tools/lane_b_index5_public_meaning_audit.py
python3 tools/lldb_probes/state_helpers_23c5f0_f33d0_runtime/verify_1f0ce0_producer.py
python3 tools/lldb_probes/state_helper_23faf0_record_chain/verify_record_chain.py
python3 tools/lldb_probes/state_448_payload_public_origin/verify_state_448_payload_public.py
python3 tools/lldb_probes/codex_index5_lookup_vector_public_origin/verify_lookup_vector_public_origin.py
python3 tools/lldb_probes/prefusion_node_dest_sentinel_custody/verify_20ca00_depth_bound_custody.py
python3 tools/lldb_probes/codex_29a140_source_local_producer/validate_reports.py
python3 tools/lldb_probes/codex_26d750_source_range_builder/verify_source_range_builder.py
python3 tools/lldb_probes/codex_276860_xmm4_origin/validate_xmm4_origin.py
python3 tools/lldb_probes/codex_276860_operand_source_context/verify_operand_source.py
```

The verifier checks:

- the canonical LRIs still carry byte-identical calibration payloads with sizes
  `32832`, `262968`, and `35266`;
- the public LRI camera/config carrier fields decode to expected four-zoom
  focal/fired-camera sets, and the 262,968-byte block carries 16
  `field_13` per-camera nominal-table entries;
- the accepted runtime projection-field dispatcher keys are subsets of those
  public fired-camera sets and map to the expected camera names;
- the `0xf2770` constructor reports construct one CapturedImage-like runtime
  object per public fired camera, with output `object+0x60` matching public
  `LightHeader.field_12[camera].field_2`, `object+0x50` matching public
  `field_4` when present and `0` otherwise, `object+0x54` matching public
  `field_5`, constructor input `+0x40` matching public `field_8`, constructor
  input `+0x48 * 2` matching public `field_10`, `object+0x64 == 0`, and
  constructed active byte `object+0x30 == 1`;
- fresh `0xf2770` raw captures from object `+0x10c`, stage-1 bank `+0x12c`,
  and stage-0 bank `+0x180` are not exact byte copies inside the three LRI
  calibration payload classes;
- the same constructor captures show `object+0x10c` is born with
  `4160 x 3120` shape and `1.0 / 1.0` scale, while both `CalibStage` banks are
  born as the same default identity-shaped 21-float span;
- the enriched `0xf33d0` reports show destination keys matching the public
  fired set at `28mm` / `35mm`, and matching public-fired `B1..C5` at `70mm` /
  `150mm` while excluding public-fired `C6`;
- the same `0xf33d0` check parses the 32,832-byte public intrinsics block and
  proves exact fixed32 matches for wide-tier A1-A5 selector-0 records:
  `field_13[camera].field_3.field_2[0].field_2.field_1` for the K matrix,
  `field_13[camera].field_3.field_2[2].field_3.field_1.field_1` for the
  rotation matrix, and
  `field_13[camera].field_3.field_2[2].field_3.field_1.field_2` for the
  translation triple;
- component-granularity fixed32 sequence indexing also proves exact public
  rotation-matrix and translation-triple copies for B4 in all four focal tiers
  and C5 in `70mm` / `150mm`, while their K matrices are not exact public
  fixed32-sequence copies;
- the constructor-side `0x1f0ce0 -> 0xf33d0` verifier proves the two producer
  calls copy identical source records into both selector banks per key, and
  shows B4/C5 K records are zoom-variant non-exact packets while B4/C5 poses
  remain exact public copies;
- nontrivial B/C-side `0xf33d0` source values mostly do not appear as fixed32
  calibration fields under the same recursive protobuf check, so the verifier
  does not promote them to exact public-origin copies;
- captured raw state-helper spans where present, and decoded eight-float
  fallback records otherwise, are not exact byte copies inside the three LRI
  calibration payload classes. This keeps those packets from proving direct
  public field origin;
- LRI proto values include `4160` and `3120`, while the runtime pyramid sizes
  `2080`, `1560`, `1040`, `520`, `390`, plus final output sizes and
  lookup-count-like values, are absent as proto field values. The value `780`
  does appear as a public encoder nominal, so this verifier does not use it as
  an absence claim for pyramid dimensions;
- the four map-provider JSON reports still bind the tracked
  `0x3f7040 -> 0x3f72f0 -> 0x268480` path to provider target `0x26b590` and
  preserve equality between the provider return and `record+0x40`;
- the four lookup-origin JSON reports still show six live sites per focal tier
  and a final lookup-vector header write at `0xf043e`, with counts `752` for
  `28mm` / `35mm` and `1472` for `70mm` / `150mm`;
- the four source-object field JSON reports still bind `this+0xf8` and
  `this+0xe0` continuity into `0x299c70` / `0x267010`;
- the four `0x29a140` JSON reports still validate the source-local
  record-byte-span formula and `2080 x 1560` record descriptor. The patched
  source-local probe now persists the full input descriptor and mask descriptor
  as binary dumps; the source-local validator checks those dumps by size and
  SHA-256. The aggregate verifier checks both full dumps plus the sampled first
  input-descriptor bytes, first mask bytes, and first-record header bytes
  against the whole LRI payload stream and public calibration payload subset,
  with zero exact hits in all four tiers. This is an exact direct byte-copy
  absence check, not a transformed-origin exclusion.
- the five `0x26d750` source-range reports validate the caller/entry argument
  boundary, source and output descriptor shapes, sampled `(lower,count)` range
  formula, unchanged handoff into `0x29a140`, and one Unit-2 exact-28mm
  structural spot check.
- the four `state+0x448` payload-origin reports validate process completion,
  first-payload key sets, exact public pose rotation/translation component
  origins for payload `+0x00..+0x2c`, and zero exact public fixed32-sequence
  hits for the checked immediate later `+0x30..+0x3c` source slices; the later
  box-formula reports separately validate that slice as uniform scale plus box
  origin over the `0x145980(object)` box and `4160 x 3120` object size.
- the four index-5 lookup-vector public-origin reports validate process
  completion, the `0xf02d0` copied source span, retained target fields
  `index=5`, `mode=8`, `this+0x298/+0x29c = [200.0, 640000.0]`,
  `2080 x 1560`, exact float32 reciprocal near/far ramp bytes, unchanged later
  `0x267010` consumption, and zero full-vector LRI block hits / zero public
  calibration fixed32 hits for the checked vector.
- the deterministic depth-bound verifier pins the mode-selection, state-copy,
  Triangulator owner-copy, and Ceres lower/upper-bound call windows; resolves
  both imported bound setters; validates the two binary endpoint rows; and
  requires all four complete canonical runtime reports to select constructor
  mode `0`, which chooses `[200.0, 640000.0]`.
- the four `%xmm4` origin reports validate early-terminate stepped packets at
  `0x27786f..0x277903`, exact byte reconstruction for each captured arithmetic
  stage, and final `%xmm4_low` values `0.999925256`, `0.959209323`,
  `0.829063177`, and `0.939458907` for `28mm`, `35mm`, `70mm`, and `150mm`;
  the same validator finds zero exact full-vector LRI payload hits and zero
  exact nonzero scalar-word LRI payload hits for the sampled `object+0x60`
  scale vector.
- the four operand-source-context reports validate sampled `%xmm8` custody
  through target `+0x200` and target `+0x288`, subtraction-vector custody
  through target `+0x1e8`, table custody through target `+0x198`, and
  same-object internal producer custody for the final target qwords
  `+0x198`, `+0x1e8`, `+0x200`, and `+0x288`. It also validates the sampled
  `0x26c8e0` buffer layout: `+0x198` capacity `16656` `uint16` entries,
  `+0x200 - +0x1e8 = 33312` bytes, and sampled subtraction-vector delta
  `+16` from `+0x200`. The aggregate verifier additionally checks sampled
  guide-first16,
  guide-sample16, and subtraction-vector slices against the whole LRI payload
  stream and the public calibration payload subset, with zero exact hits for
  all three 16-byte slices in all four tiers, and zero exact public
  calibration fixed32-sequence hits for the subtraction vector.

Verifier output:

The `nontrivial_fixed32_absent` numerator/denominator is a run-local broad
absence guardrail over captured `0xf33d0` packets, not an admitted algorithm
constant. The exact values can move when full-render `0xf33d0` liveness outside
the stable constructor-side producer subset changes.

```text
LRI static check: OK {'32832': '722a6e721636c9c4', '262968': 'f0c34433f9cf9b07', '35266': '6a0d52b6a4d1b4de'}
28mm: OK; LRI_focal=28 fired=A1,A2,A3,A4,A5,B1,B2,B3,B4,B5 warp_field13=16; f2770_keys=A1,A2,A3,A4,A5,B1,B2,B3,B4,B5 object+0x64=0 active=1 module_fields=field_2,field_4,field_5,field_8,field_10 stage_raw=10/10 stage_lri_exact_hits=0/70; f33d0_dest_keys=A1,A2,A3,A4,A5,B1,B2,B3,B4,B5 selectors=0,1 public_intrinsics_exact_selector0=A1,A2,A3,A4,A5 public_pose_exact_selector0=A1,A2,A3,A4,A5,B4 nontrivial_fixed32_absent=520/688; projection_keys=A1,B1,B2,B3,B4,B5; state_record_lri_exact_hits=0/156 source=snapshot; record+0x40=UpsampleLayer+0x90 provider target 0x26b590; lookup_count=752; source_object=this+0xf8 control=8 desc=2080x1560; source_local_bytes=89124024 source_local_sample_lri_hits=input_first32:0,mask_first16:0,record_headers64:0 source_local_full_lri_hits=input_descriptor:0,mask_descriptor:0 source_local_full_calib_hits=input_descriptor:0,mask_descriptor:0 input_sha=bbd1f2660e698e5a mask_sha=1a28b93c687d4a8b
35mm: OK; LRI_focal=35 fired=A1,A2,A3,A4,A5,B1,B2,B3,B4,B5 warp_field13=16; f2770_keys=A1,A2,A3,A4,A5,B1,B2,B3,B4,B5 object+0x64=0 active=1 module_fields=field_2,field_4,field_5,field_8,field_10 stage_raw=10/10 stage_lri_exact_hits=0/70; f33d0_dest_keys=A1,A2,A3,A4,A5,B1,B2,B3,B4,B5 selectors=0,1 public_intrinsics_exact_selector0=A1,A2,A3,A4,A5 public_pose_exact_selector0=A1,A2,A3,A4,A5,B4 nontrivial_fixed32_absent=556/736; projection_keys=A1,B1,B2,B3,B4,B5; state_record_lri_exact_hits=0/156 source=snapshot; record+0x40=UpsampleLayer+0x90 provider target 0x26b590; lookup_count=752; source_object=this+0xf8 control=8 desc=2080x1560; source_local_bytes=108064312 source_local_sample_lri_hits=input_first32:0,mask_first16:0,record_headers64:0 source_local_full_lri_hits=input_descriptor:0,mask_descriptor:0 source_local_full_calib_hits=input_descriptor:0,mask_descriptor:0 input_sha=8ad065d99c1e78f9 mask_sha=1a28b93c687d4a8b
70mm: OK; LRI_focal=70 fired=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5,C6 warp_field13=16; f2770_keys=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5,C6 object+0x64=0 active=1 module_fields=field_2,field_4,field_5,field_8,field_10 stage_raw=11/11 stage_lri_exact_hits=0/77; f33d0_dest_keys=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5 selectors=0,1 public_intrinsics_exact_selector0=none public_pose_exact_selector0=B4,C5 nontrivial_fixed32_absent=798/848; projection_keys=B4,C1,C2,C3,C4,C5; state_record_lri_exact_hits=0/52 source=f34e0_fallback; record+0x40=UpsampleLayer+0x90 provider target 0x26b590; lookup_count=1472; source_object=this+0xf8 control=8 desc=2080x1560; source_local_bytes=95362208 source_local_sample_lri_hits=input_first32:0,mask_first16:0,record_headers64:0 source_local_full_lri_hits=input_descriptor:0,mask_descriptor:0 source_local_full_calib_hits=input_descriptor:0,mask_descriptor:0 input_sha=55e72401635b67ac mask_sha=1a28b93c687d4a8b
150mm: OK; LRI_focal=149 fired=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5,C6 warp_field13=16; f2770_keys=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5,C6 object+0x64=0 active=1 module_fields=field_2,field_4,field_5,field_8,field_10 stage_raw=11/11 stage_lri_exact_hits=0/77; f33d0_dest_keys=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5 selectors=0,1 public_intrinsics_exact_selector0=none public_pose_exact_selector0=B4,C5 nontrivial_fixed32_absent=638/688; projection_keys=B4,C1,C2,C3,C4,C5; state_record_lri_exact_hits=0/108 source=snapshot; record+0x40=UpsampleLayer+0x90 provider target 0x26b590; lookup_count=1472; source_object=this+0xf8 control=8 desc=2080x1560; source_local_bytes=84730560 source_local_sample_lri_hits=input_first32:0,mask_first16:0,record_headers64:0 source_local_full_lri_hits=input_descriptor:0,mask_descriptor:0 source_local_full_calib_hits=input_descriptor:0,mask_descriptor:0 input_sha=4354607a307874cf mask_sha=1a28b93c687d4a8b
```

```text
28mm: OK; first_payload_0x00_0x20_call_241590:events=10:keys=A1,A2,A3,A4,A5,B1,B2,B3,B4,B5:public_seq=10/10:components=rotation:A1x10; first_payload_0x24_0x2c_call_2415b0:events=10:keys=A1,A2,A3,A4,A5,B1,B2,B3,B4,B5:public_seq=10/10:components=translation:A1x10; later_payload_0x30_0x34_call_2415d0:events=5:keys=A1,A2,A3,A4,A5:public_seq=0/5:components=none; later_payload_0x38_0x3c_call_2415f0:events=5:keys=A1,A2,A3,A4,A5:public_seq=0/5:components=none
35mm: OK; first_payload_0x00_0x20_call_241590:events=10:keys=A1,A2,A3,A4,A5,B1,B2,B3,B4,B5:public_seq=10/10:components=rotation:A1x10; first_payload_0x24_0x2c_call_2415b0:events=10:keys=A1,A2,A3,A4,A5,B1,B2,B3,B4,B5:public_seq=10/10:components=translation:A1x10; later_payload_0x30_0x34_call_2415d0:events=5:keys=A1,A2,A3,A4,A5:public_seq=0/5:components=none; later_payload_0x38_0x3c_call_2415f0:events=5:keys=A1,A2,A3,A4,A5:public_seq=0/5:components=none
70mm: OK; first_payload_0x00_0x20_call_241590:events=10:keys=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5:public_seq=10/10:components=rotation:B4x10; first_payload_0x24_0x2c_call_2415b0:events=10:keys=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5:public_seq=10/10:components=translation:B4x10; later_payload_0x30_0x34_call_2415d0:events=5:keys=B1,B2,B3,B4,B5:public_seq=0/5:components=none; later_payload_0x38_0x3c_call_2415f0:events=5:keys=B1,B2,B3,B4,B5:public_seq=0/5:components=none
150mm: OK; first_payload_0x00_0x20_call_241590:events=10:keys=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5:public_seq=10/10:components=rotation:B4x10; first_payload_0x24_0x2c_call_2415b0:events=10:keys=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5:public_seq=10/10:components=translation:B4x10; later_payload_0x30_0x34_call_2415d0:events=5:keys=B1,B2,B3,B4,B5:public_seq=0/5:components=none; later_payload_0x38_0x3c_call_2415f0:events=5:keys=B1,B2,B3,B4,B5:public_seq=0/5:components=none
```

```text
28mm: OK count=752 sha=e52206cbe601e978 reciprocal_ramp=640000.0->200.0 first4=[640000.000, 121681.016, 67231.781, 46447.621] last4=[200.802231, 200.534225, 200.266922, 200.000000] lri_full_hits=0 calib_fixed32_sequence_hits=0 calib_scalar_hits=0/2708704
35mm: OK count=752 sha=e52206cbe601e978 reciprocal_ramp=640000.0->200.0 first4=[640000.000, 121681.016, 67231.781, 46447.621] last4=[200.802231, 200.534225, 200.266922, 200.000000] lri_full_hits=0 calib_fixed32_sequence_hits=0 calib_scalar_hits=0/2708704
70mm: OK count=1472 sha=85202a045de94c33 reciprocal_ramp=640000.0->200.0 first4=[640000.000, 201593.156, 119639.094, 85059.633] last4=[200.411209, 200.274826, 200.138626, 200.000000] lri_full_hits=0 calib_fixed32_sequence_hits=0 calib_scalar_hits=0/5302144
150mm: OK count=1472 sha=85202a045de94c33 reciprocal_ramp=640000.0->200.0 first4=[640000.000, 201593.156, 119639.094, 85059.633] last4=[200.411209, 200.274826, 200.138626, 200.000000] lri_full_hits=0 calib_fixed32_sequence_hits=0 calib_scalar_hits=0/5302144
```

```text
xmm4_origin_28mm.json: OK table=240 clamped=-0.000000 floor=-1 fraction=1.000000 xmm4_low=0.999925256 object_0x60_lri_full_hits=0 object_0x60_lri_nonzero_scalar_hits=0/3
xmm4_origin_35mm.json: OK table=199 clamped=-0.060112 floor=-1 fraction=0.939888 xmm4_low=0.959209323 object_0x60_lri_full_hits=0 object_0x60_lri_nonzero_scalar_hits=0/3
xmm4_origin_70mm.json: OK table=225 clamped=-0.270505 floor=-1 fraction=0.729495 xmm4_low=0.829063177 object_0x60_lri_full_hits=0 object_0x60_lri_nonzero_scalar_hits=0/3
xmm4_origin_150mm.json: OK table=215 clamped=-0.090168 floor=-1 fraction=0.909832 xmm4_low=0.939458907 object_0x60_lri_full_hits=0 object_0x60_lri_nonzero_scalar_hits=0/3
```

```text
28mm: ... field_origins={'0x198': 'watch:0x26ca9b', '0x1e8': 'watch:0x26cbd4', '0x200': 'watch:0x26cc08', '0x288': 'producer:guide_store_0x288_reuse_26c633'} field_layout={'expanded_width': 2082, 'table_u16_capacity': 16656, 'midpoint_bytes': 33312, 'sub_delta_from_0x200': 16} guide_u8x4=a8383001 operand_lri_full_hits=guide_first16:0,guide_sample16:0,subvec16:0 subvec_public_fixed32_sequence_hits=0 table_u16_lri_hits=1
35mm: ... field_origins={'0x198': 'watch:0x26ca9b', '0x1e8': 'watch:0x26cbd4', '0x200': 'watch:0x26cc08', '0x288': 'producer:guide_store_0x288_reuse_26c633'} field_layout={'expanded_width': 2082, 'table_u16_capacity': 16656, 'midpoint_bytes': 33312, 'sub_delta_from_0x200': 16} guide_u8x4=2b766d01 operand_lri_full_hits=guide_first16:0,guide_sample16:0,subvec16:0 subvec_public_fixed32_sequence_hits=0 table_u16_lri_hits=0
70mm: ... field_origins={'0x198': 'watch:0x26ca9b', '0x1e8': 'watch:0x26cbd4', '0x200': 'watch:0x26cc08', '0x288': 'producer:guide_store_0x288_reuse_26c633'} field_layout={'expanded_width': 2082, 'table_u16_capacity': 16656, 'midpoint_bytes': 33312, 'sub_delta_from_0x200': 16} guide_u8x4=5f5a5801 operand_lri_full_hits=guide_first16:0,guide_sample16:0,subvec16:0 subvec_public_fixed32_sequence_hits=0 table_u16_lri_hits=1
150mm: ... field_origins={'0x198': 'watch:0x26ca9b', '0x1e8': 'watch:0x26cbd4', '0x200': 'watch:0x26cc08', '0x288': 'producer:guide_store_0x288_reuse_26c633'} field_layout={'expanded_width': 2082, 'table_u16_capacity': 16656, 'midpoint_bytes': 33312, 'sub_delta_from_0x200': 16} guide_u8x4=b1562c01 operand_lri_full_hits=guide_first16:0,guide_sample16:0,subvec16:0 subvec_public_fixed32_sequence_hits=0 table_u16_lri_hits=1
```

## Admitted Positive Result

The concrete name for `record+0x40` is now as strong as the current installed
bundle allows:

```text
record+0x40
  <- 0x25e500 stores caller map pointer
  <- 0x3f72f0 / 0x268480 provider return
  <- UpsampleLayer vtable address point 0x658eb0, slot +0x90 = 0x26b590
  <- 0x26b590 returns UpsampleLayer+0x90
  <- 0x26aa10 depth-path builder fills UpsampleLayer+0x90
  <- 0x29ed90 guided 2x upsample output, 4160 x 3120 float descriptor
  <- previous-layer +0x90 descriptor, index-5 StereoLayer<false>+0x2a8,
     2080 x 1560 float source
```

The installed binary's own disabled debug-output branch labels
`UpsampleLayer+0x90` as `depth_... .dp`. That admits an internal installed-bundle
name: the pair-grid map pointer is the `UpsampleLayer` depth descriptor. This
is still not a public LRI/protobuf field name.

The LRI-origin part that is admitted is shape / carrier scope only:

- `4160 x 3120` is an LRI-stored per-camera full sensor ROI value.
- `2080 x 1560` and the smaller pyramid dimensions are not LRI-stored proto
  values in the canonical quartet; they are libcp-computed halvings.
- The canonical quartet carries byte-identical intrinsics, distortion, and
  depthcfg calibration payloads for this physical unit; the intrinsics payload
  contains 16 distinct per-camera records.

## Public LRI Camera/Config Bridge

The tracked verifier now independently decodes the public camera/config carrier
fields needed for the current Lane B key-space comparison:

```text
LightHeader.field_12[i].field_2 = camera_id
LightHeader.field_12[i].field_4 = raw module scalar copied to constructor input+0x34 / object+0x50
LightHeader.field_12[i].field_5 = raw module scalar copied to constructor input+0x38 / object+0x54
LightHeader.field_12[i].field_8 = raw module scalar copied to constructor input+0x40
LightHeader.field_12[i].field_10 = raw module scalar equal to 2 * constructor input+0x48
262,968-byte warp/calibration block field_13[cam].field_1 = camera_id
262,968-byte warp/calibration block field_13[cam].field_4.field_2[j].field_1 =
    nominal encoder ADC for that camera/config entry
```

The decoded public fired-camera sets are:

| Zoom | LRI focal value | Public fired cameras |
|---|---:|---|
| `28mm` | `28` | `A1,A2,A3,A4,A5,B1,B2,B3,B4,B5` |
| `35mm` | `35` | `A1,A2,A3,A4,A5,B1,B2,B3,B4,B5` |
| `70mm` | `70` | `B1,B2,B3,B4,B5,C1,C2,C3,C4,C5,C6` |
| `150mm` | `149` | `B1,B2,B3,B4,B5,C1,C2,C3,C4,C5,C6` |

The same parse confirms the 262,968-byte warp/calibration block has 16 keyed
`field_13` camera entries in every canonical LRI. Cameras
`A1,A2,A3,A4,A5,B4,C2,C3` carry one nominal config entry; cameras
`B1,B2,B3,B5,C1,C4,C5,C6` carry four nominal config entries.

The already admitted runtime `0x3f6170` projection-field dispatcher sees only
these public-key subsets:

| Zoom | Runtime projection keys | Relation to public fired set |
|---|---|---|
| `28mm` | `A1,B1,B2,B3,B4,B5` | subset of public fired cameras |
| `35mm` | `A1,B1,B2,B3,B4,B5` | subset of public fired cameras |
| `70mm` | `B4,C1,C2,C3,C4,C5` | subset of public fired cameras; excludes public-fired `C6` |
| `150mm` | `B4,C1,C2,C3,C4,C5` | subset of public fired cameras; excludes public-fired `C6` |

This proves a public camera-id/key alignment for the tested dispatcher boundary.
It does not prove that `state+0xe0` or `state+0x448` were populated directly
from those public fields, and it does not prove a public field name for the
index-5 lookup vector.

The refreshed `0xf2770` constructor reports prove the same public camera-id
alignment one step closer to the object family used by `state+0xe0` lookup:

| Zoom | Constructed object keys at `object+0x60` | Relation to public fired set |
|---|---|---|
| `28mm` | `A1,A2,A3,A4,A5,B1,B2,B3,B4,B5` | exact public fired-camera set |
| `35mm` | `A1,A2,A3,A4,A5,B1,B2,B3,B4,B5` | exact public fired-camera set |
| `70mm` | `B1,B2,B3,B4,B5,C1,C2,C3,C4,C5,C6` | exact public fired-camera set |
| `150mm` | `B1,B2,B3,B4,B5,C1,C2,C3,C4,C5,C6` | exact public fired-camera set |

For these constructor packets, the verifier also proves these exact raw
public-field mappings:

```text
constructor input+0x30 -> object+0x60 == LightHeader.field_12[camera].field_2
constructor input+0x34 -> object+0x50 == LightHeader.field_12[camera].field_4
constructor input+0x38 -> object+0x54 == LightHeader.field_12[camera].field_5
constructor input+0x40 == LightHeader.field_12[camera].field_8
constructor input+0x48 * 2 == LightHeader.field_12[camera].field_10
```

For records where `field_4` is absent, the runtime-side `input+0x34` /
`object+0x50` value is `0`. `object+0x64` is always `0`, and `object+0x30` is
constructed as active (`1`). This gives public key/raw-field alignment for the
`object+0x60` side of the already-bounded `0xe6ba0` lookup predicate
(`object+0x64`, `object+0x60`) and a raw public origin for `object+0x54`. It
does not assign public semantic names to `object+0x64`, `object+0x30`,
`field_4`, `field_5`, `field_8`, or `field_10`, and it does not prove that
every later `state+0xe0` lookup target is constructor-identical to these
packets.

The patched constructor probe also captures raw spans from the direct
`object+0x10c` accessor area and both `CalibStage` banks (`object+0x12c` and
`object+0x180`). The verifier checks `70`, `70`, `77`, and `77` raw spans for
`28mm`, `35mm`, `70mm`, and `150mm`, respectively, and finds zero exact copies
inside the three LRI calibration payload classes. This again is narrow negative
evidence against direct byte-copy proof, not proof against transformed or
derived calibration origins. The same captures show the constructor-time
`object+0x10c` span carries full-sensor shape `4160 x 3120` and `1.0 / 1.0`
scale, and both constructor-time `CalibStage` banks are the same default
identity-shaped 21-float span. That means this constructor packet is a public
camera-key / default-object birth point, not the observed source of non-default
calibration bank contents.

As a guard against accidental over-reading, the verifier also byte-searches
the three calibration payload classes for exact raw state-helper spans or,
where raw spans are unavailable, decoded eight-float fallback records. It checks
`156`, `156`, `52`, and `108` candidates for `28mm`, `35mm`, `70mm`, and
`150mm`, respectively, and finds zero exact copies. The `70mm` row is explicitly
from the older successful `f34e0` fallback report because the fresh
`snapshot_70mm` raw rerun stopped inside `___lldb_unnamed_symbol_2e8cc0` at the
known `libcp+0x2e945d` probe perturbation boundary before reaching `0x23c5f0`.
This is narrow negative evidence: the checked state-helper packets do not
themselves prove a direct LRI byte-copy origin. It does not exclude transformed,
reordered, partial, double-precision, or later-populated origins.

## `0xf33d0` Public-Intrinsics Bridge

The enriched `state_helpers_23c5f0_f33d0_runtime` probe now captures, at each
`0xf33d0` hit, the destination object's key fields and the three source records
copied by the helper:

- destination `object+0x30`, `object+0x60`, and `object+0x64`;
- `rsi` source record: 9 fixed32 values, captured as eight floats plus the
  ninth raw dword;
- `rdx` source record: another 9 fixed32 values, captured the same way;
- `rcx` source triple: three raw fixed32 dwords;
- pre-copy destination bank snapshots at `object+0x180` and `object+0x12c`.

The four fresh complete runs show these destination key sets:

| Zoom | `0xf33d0` destination keys | Relation to public fired set |
|---|---|---|
| `28mm` | `A1,A2,A3,A4,A5,B1,B2,B3,B4,B5` | exact public fired-camera set |
| `35mm` | `A1,A2,A3,A4,A5,B1,B2,B3,B4,B5` | exact public fired-camera set |
| `70mm` | `B1,B2,B3,B4,B5,C1,C2,C3,C4,C5` | subset of public fired set; excludes public-fired `C6` |
| `150mm` | `B1,B2,B3,B4,B5,C1,C2,C3,C4,C5` | subset of public fired set; excludes public-fired `C6` |

Every captured `0xf33d0` destination object has `object+0x64 == 0` and
`object+0x30 == 1` at the copy boundary. This is consistent with the `0xf2770`
constructor object family, but still does not prove a public field name for
either offset.

The positive public-origin result is narrower and exact. For `28mm` and `35mm`,
selector-0 records for A1-A5 exactly match the public 32,832-byte intrinsics
payload's fixed32 fields:

```text
K matrix:
  32832-byte block field_13[camera].field_3.field_2[0].field_2.field_1

Rotation matrix:
  32832-byte block field_13[camera].field_3.field_2[2].field_3.field_1.field_1

Translation triple:
  32832-byte block field_13[camera].field_3.field_2[2].field_3.field_1.field_2
```

The same exact public match is also present in selector-1 for A1-A5 in the
accepted wide runs. This proves that at least the A-bank `CalibStage` packets
entering `0xf33d0` are direct public intrinsics / pose calibration records,
keyed by public camera id.

The proof extends only partially into the B/C-side records. A
component-granularity fixed32 sequence index over the three public calibration
payload classes proves exact public rotation-matrix and translation-triple
copies for B4 in all four focal tiers and C5 in the tele tiers:

```text
Rotation matrix:
  32832-byte block field_13[camera].field_3.field_2[2].field_3.field_1.field_1

Translation triple:
  32832-byte block field_13[camera].field_3.field_2[2].field_3.field_1.field_2
```

It does not prove exact public K-matrix copies for B4 or C5, and it does not
prove exact public records for the other B/C-side packets. The verifier
recursively indexes fixed32 fields in the three public calibration payload
classes and then checks the nontrivial `0xf33d0` source values that did not
match the compact/component public records above. The remaining B/C-side values
mostly do not appear as fixed32 public calibration fields under this check:

| Zoom | Nontrivial unmatched fixed32 source values absent from public calibration fixed32 index |
|---|---:|
| `28mm` | `520 / 688` |
| `35mm` | `556 / 736` |
| `70mm` | `798 / 848` |
| `150mm` | `638 / 688` |

This does not disprove a public origin for the remaining B/C records. It says
the current evidence admits exact public pose copies only for B4/C5, does not
admit B4/C5 K copies, and does not admit the rest as exact fixed32 public-field
copies. They may be selected, transformed, interpolated, or derived from
calibration records that require a deeper schema decode or runtime computation
trace.

The follow-up `0x1f0ce0` producer verifier narrows the B4/C5 K case from
"maybe later transformed" to a producer-edge boundary:

```text
static_1f0ce0_calls_and_selector_setup=OK
28mm: selector_pair_source_equal=10/10 full_public=A1,A2,A3,A4,A5 pose_only_public=B4 k_not_public=B1,B2,B3,B4,B5
35mm: selector_pair_source_equal=10/10 full_public=A1,A2,A3,A4,A5 pose_only_public=B4 k_not_public=B1,B2,B3,B4,B5
70mm: selector_pair_source_equal=10/10 full_public=none pose_only_public=B4,C5 k_not_public=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5
150mm: selector_pair_source_equal=10/10 full_public=none pose_only_public=B4,C5 k_not_public=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5
cross_tier=B4_pose_stable_K_variants4,C5_pose_stable_K_variants2,A1-A5_wide_stable
```

At `0x1f1328` / `0x1f134b`, the same source records are copied into selector
`0` and selector `1` banks for each key. B4 pose is exact-public and stable
across all four focal tiers, while B4 K has four tier-specific raw variants.
Tele C5 pose is exact-public and stable across `70mm` / `150mm`, while C5 K
has two tele-tier variants. The verifier also guards the static K stack local
and the post-`0xf3350` scale window, where fields `0`, `4`, `2`, and `5` are
multiplied before both selector-bank copies. This is stronger evidence for
derived K treatment, but it still does not decode the complete numeric K
formula or assign a public field name to the whole `CalibStage` packet.

## `state+0xe0` Boundary

Current admitted evidence traces `state+0xe0` to an internal object lookup
context:

```text
state+0xe0
  -> 0x1be970 / 0xe6ba0
  -> shared image-like object lookup by object+0x64 and object+0x60
  -> 0xf34e0 CalibStage bank selector at object+0x12c / object+0x180
  -> 0xf3350 direct object+0x10c accessor
  -> 0xf3360 owner-backed tree lookup keyed by object+0x60
```

The installed string `wrong CalibStage, must be factory or current` admits only
that the code has two accepted `CalibStage` banks and rejects other stage
values. It does not prove which numeric value maps to public word `factory` or
`current`, and it does not identify the LRI protobuf field path for those banks.

For the index-5 depth source specifically, the admitted chain is:

```text
StereoLayer<false>+0xe0 lookup vector
  -> this+0x298/+0x29c retained as [200.0, 640000.0]
  -> 0x28fa60 / 0x28f5a0 / 0x28f860 generated stack vector
  -> exact float32 reciprocal near/far ramp from 640000.0 down to 200.0
  -> count 752 for 28mm / 35mm; count 1472 for 70mm / 150mm
  -> copied by 0xf02d0 into this+0xe0, final observed write at 0xf043e
  -> later consumed unchanged by 0x267010 as lookup[source_u16] -> float
```

No direct public LRI/calibration table origin is admitted for the lookup vector:
the full vector has zero LRI block byte hits, zero full public calibration
fixed32-sequence hits, and zero scalar public calibration fixed32 hits under the
checked payload classes. The admitted positive origin is internal generation
from static binary endpoint constants plus the internally computed count.
Follow-up endpoint/count proof binds `this+0x298/+0x29c` to the selected
`[200.0, 640000.0]` binary-table row and binds the count producer to
`0x28f5a0` math over five `0xa8` source records. Follow-up depth-bound custody
proves the same selected pair reaches `state+0x100/+0x104`, then Triangulator
owner `+0x70/+0x74`, and is installed as the lower/upper bounds on the same
one-scalar Ceres parameter used by the ray-depth reprojection cost. The exact
reciprocal table is therefore internally a ray-depth hypothesis grid. Public
units, calibration/LRI/protobuf origin and names, source-record public names,
and public source-index names / physical semantics remain open.
The follow-up `%xmm4` origin proof additionally closes sampled internal
formation of one source-record scalar operand feeding the payload costs, but
the vectors and object fields that feed that operand still have no admitted
public LRI/protobuf names. The sampled `object+0x60` scale vector has zero
exact full-vector and zero exact nonzero scalar-word hits in the LRI payload
streams under the current verifier.

The `0xf2770` constructor reruns now admit that, for the captured constructor
family feeding the same object-key vocabulary, `object+0x60` is the public
camera id and `object+0x54` is the raw public
`LightHeader.field_12[camera].field_5` module scalar. They also bind
`object+0x50` / constructor input `+0x34` to public `field_4`, constructor
input `+0x40` to public `field_8`, and constructor input `+0x48 * 2` to public
`field_10`. They do not prove the public name for `object+0x64`, the public
name or terminal semantics for `object+0x30`, the semantic names of those raw
module fields, or the LRI/protobuf path that produces the `CalibStage` banks.

The enriched `0xf33d0` reruns now prove that the A1-A5 wide-tier packets copied
into this object-family `CalibStage` path are exact fixed32 copies from the
public intrinsics block's camera-keyed K matrix and compact pose record paths.
They also prove exact public pose-record copies for B4 and tele C5. That is a
concrete public origin for those scoped components only. The same check does
not admit B4/C5 K matrices, other B/C-side `CalibStage` packets, tele `C6`, or
the full `state+0xe0` object-family contents as exact public-origin records.
The producer-edge verifier further shows B4/C5 K packets are already
zoom-variant non-exact records before downstream State-helper composition.

The refreshed `0x23faf0` record-chain verifier checks the pre-call left record,
right record, output-before record, and output-after record in all 26 four-site
groups per focal tier. It finds zero exact full 0xa4-byte source-record copies
in the canonical LRI calibration payload classes (`0/104` per tier), while
admitting only component-scoped public matches: pre-call left translations
match A1 at wide tiers and B4 at tele tiers; right-record components include
wide A2-A5 K/pose plus B4 pose matches and one tele C5 pose match. That is
evidence for transformed/composed runtime records, not a public field name for
the whole `state+0xe0` object-family record.

## `state+0x448` Boundary

Current admitted evidence traces `state+0x448` to an internal keyed
tree/control object:

```text
state+0x448
  -> constructor-created tree/control object
  -> first visible population enumerates keys from state+0xe0
  -> resolves objects through 0x1be970
  -> skips objects with object+0x30 == 0
  -> keys inserted/found by object+0x60 through 0xf2720
  -> payload fields +0x00..+0x2c copied at first insertion
  -> later direct writes populate payload fields through +0x80
```

This proves structure and custody. It still does not prove the public LRI
field names for the payload fields, the public semantic name of `object+0x30`,
or the exact LRI calibration block / proto field path that produced each
payload record.

The `state_448_payload_public_origin` follow-up now admits a scoped public
origin for the first visible payload-copy sites:

```text
payload +0x00..+0x20
  <- 0x241590 source rbp-0x3d0
  == 32832-byte intrinsics block
     field_13[anchor].field_3.field_2[2].field_3.field_1.field_1
     rotation component

payload +0x24..+0x2c
  <- 0x2415b0 source rbp-0x3dc
  == 32832-byte intrinsics block
     field_13[anchor].field_3.field_2[2].field_3.field_1.field_2
     translation component
```

The anchor is `A1` for `28mm` / `35mm` and `B4` for `70mm` / `150mm`.
That anchor component is shared across all first-pass inserted keys:

| Zoom | First-pass keys | Public anchor copied into `+0x00..+0x2c` |
|---|---|---|
| `28mm` | `A1,A2,A3,A4,A5,B1,B2,B3,B4,B5` | `A1` rotation / translation |
| `35mm` | `A1,A2,A3,A4,A5,B1,B2,B3,B4,B5` | `A1` rotation / translation |
| `70mm` | `B1,B2,B3,B4,B5,C1,C2,C3,C4,C5` | `B4` rotation / translation |
| `150mm` | `B1,B2,B3,B4,B5,C1,C2,C3,C4,C5` | `B4` rotation / translation |

Tele public-fired `C6` is not inserted by this first visible
`state+0x448` payload path under the tested runs. The immediate later
`+0x30..+0x3c` source slices cover `A1..A5` at wide tiers and `B1..B5` at tele
tiers, but record zero exact public fixed32-sequence hits under the same
recursive calibration fixed32-sequence index. That is narrow negative evidence
only; it does not exclude transformed, partial, non-fixed32, double-precision,
or later-populated public origins for those fields.

The follow-up later-box formula proof resolves the tested `+0x30..+0x3c`
slice as formula output rather than exact public fixed32 copy: payload
`+0x30/+0x34` is uniform scale, payload `+0x38/+0x3c` is box origin, and both
come from `0x260e40` over the `0x145980(object)` box and
`object+0x114/+0x118 = [4160,3120]`. Follow-up static-origin proof names that
size pair as the LRI-stored full sensor ROI. The 2026-06-26 follow-up further
traces the box-producing calibration record to public
`GeometricCalibration.distortion.polynomial` center, normalization,
coefficient, and fit-cost fields. The envelope and scale remain derived
runtime values rather than direct protobuf fields.

The refreshed `0x23faf0` record-chain verifier also keeps `state+0x448`
component-scoped: it captures the pre-call left record used by the helper and
finds exact public translation components for A1 at wide tiers and B4 at tele
tiers, but no exact full source-record byte copy. This narrows possible origins
without naming `state+0x448` as a public protobuf table.

## Rejected Upgrades

This audit explicitly does not admit these tempting statements:

- "`state+0xe0` is the public LRI intrinsics record."
- "All `state+0xe0` / `CalibStage` records are exact public LRI intrinsics
  copies." Scoped A1-A5 K/pose and B4/C5 pose copies are admitted, but broader
  records are not.
- "`state+0x448` is the public LRI distortion/warp table."
- "All `state+0x448` payload fields have public LRI origins." First-pass
  payload `+0x00..+0x2c` has an admitted exact public pose-component origin,
  and later `+0x30..+0x3c` has formula-level box/scale meaning with the size
  pair traced to public full-sensor ROI and the box-producing calibration
  record traced to public `GeometricCalibration.distortion.polynomial`.
  Whole-payload identity and direct public names for the derived envelope and
  scale remain open.
- "`CalibStage` numeric `0` or `1` maps to public `factory` or `current`."
- "`object+0x30` is a public active/valid/reference field name."
- "`object+0x64` is a public field name."
- "The full object containing `object+0x54` is a direct public protobuf
  record." The field itself is now named: `object+0x54` comes from
  `LightHeader.modules[].lens_position`.
- "`StereoLayer<false>` index `5` is a public LRI field."
- "`record+0x40` is an LRI-stored depth map."
- "`StereoLayer<false>+0xe0` is a direct public LRI/protobuf lookup table."
- "The lookup-vector counts `752` / `1472` or endpoints `200.0` / `640000.0`
  are public LRI constants."
- "The ray-depth bounds have known public units or a known public
  calibration/LRI/protobuf field name."
- "The `0x29a140` source-local input descriptor or mask descriptor cannot be
  public-derived." The current check excludes exact direct byte copies only.
- "The `0x26d750` source-range descriptor has a public LRI/protobuf name." The
  current proof admits internal `(lower,count)` candidate-range semantics only.
- "The sampled `%xmm4` operand has a public semantic/LRI name." Its internal
  arithmetic formation is admitted; its public operand names/origins are not.
- "The target fields `+0x198`, `+0x1e8`, `+0x200`, and `+0x288` have public
  semantic names." They now have same-object internal producer custody only.
- "The runtime projection-key subset proves the full `state+0xe0` or
  `state+0x448` public field origin."

The proof standard requires a byte/proto field path or runtime observation that
connects the public field to the live runtime storage. The current evidence
provides that connection only for the scoped `0xf2770` raw module-field
mappings, scoped A1-A5 K/pose and B4/C5 pose `0xf33d0` packets, the captured
K-helper formula, the scoped first-pass `state+0x448` pose payload fields, and
the scoped `0x23faf0` record-chain components described above. The index-5
lookup vector now has an admitted internal generator formula and internal
ray-depth hypothesis-grid role, but not public units or a public
LRI/protobuf field origin.

## Consequence

No canonical claim status upgrade is made from this audit.

Safe downstream wording:

```text
The pair-grid `record+0x40` map is the internally depth-labeled
`lt::UpsampleLayer+0x90` descriptor, built by the proven index-5
`StereoLayer<false>` / `0x267010` / `0x29ed90` chain. Its dimensions trace to
the LRI-stored `4160 x 3120` sensor ROI plus libcp-computed pyramid halvings.
The public LRI camera/config key space is decoded through `LightHeader.field_12`
and the 262,968-byte warp/calibration block `field_13`, and the tested runtime
projection keys are public-fired camera subsets. The captured `0xf2770`
constructor object keys at `object+0x60` exactly match the public fired-camera
sets, with `object+0x64=0` observed in that object family.
The enriched `0xf33d0` packets prove an exact public intrinsics-block origin for
wide A1-A5 K matrix / pose records and exact public pose copies for B4 plus tele
C5, but not for B4/C5 K matrices, the remaining B/C records, tele C6, the full
`state+0xe0` object family, or full `state+0x448`. The index-5 lookup vector is
now internally classified as a generated float32 reciprocal near/far table from
`this+0x298/+0x29c = [200.0, 640000.0]`, with counts `752` at wide tiers and
`1472` at tele tiers; it is not a direct public LRI/calibration byte-copy, and
follow-up endpoint/count proof binds the endpoint pair to static binary float
tables and the count to internal `0x28f5a0` source-record math. The selected
endpoint pair is also installed as the lower/upper bound pair on the
one-scalar Triangulator ray-depth reprojection problem, closing the lookup
vector's internal role as a reciprocal ray-depth hypothesis grid while leaving
public units and public calibration/LRI/protobuf origin open. The sampled
`%xmm4` operand feeding the source-record payload cost term now has an admitted
internal formation formula through `0x27786f..0x277903` plus immediate
operand-custody context for `%xmm8`, target `+0x1e8`, target `+0x198`, target
`+0x200`, and target `+0x288`; those target qwords are now tied to same-object
internal stores at `0x26ca94`, `0x26cbcd`, `0x26cc01`, and `0x26c633`, with
sampled internal layout `+0x198` as a `16656`-entry `uint16` table base and
`+0x200` as an interior pointer `33312` bytes into `+0x1e8`; these are not
public operand names or LRI/protobuf origins. The `0x26d750` source-range
builder now proves the internal source-index descriptor is a per-pixel
`(lower,count)` candidate range over the index-5 reciprocal ray-depth lookup
vector, and that descriptor feeds the already bounded `0x29a140` / `0x29a670`
source-local min-cost path. Public source-index names, source-record public
names, public units, and public calibration/LRI/protobuf names for the
ray-depth bounds remain open.
The `0x1f0ce0` producer verifier localizes the B4/C5 K non-match to the
producer edge: those K packets are already zoom-variant before the later
State-helper record-chain composition.
The first visible `state+0x448` payload-copy path now has exact public
pose-component origins for payload `+0x00..+0x2c`: A1 rotation/translation at
wide tiers and B4 rotation/translation at tele tiers, shared across all
first-pass inserted keys; tele C6 is excluded from that first-pass path.
The refreshed `0x23faf0` record-chain proof adds component-scoped public
matches and zero full-record LRI byte-copy hits, reinforcing that those runtime
records are composed/derived rather than public-record copies under the current
proof standard.
```

This wording is intentionally narrower than "public meaning closed."
