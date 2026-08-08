# Scoped Checklist Handoff (Not Final)

## Authority

- Canonical root: `docs/TRUTH.md` version `3.0.265`
- Claim authority: `docs/canonical/CLAIM_LEDGER.md`
- Current blockers: `docs/canonical/PARITY_BLOCKERS.md`

This manifest records closure of the former A-E checklist only. It is not a
final handoff to a spec writer. The investigation remains active until every
implementation-required fact for an independent LRI-to-merged-image
application is admitted. The ledger wins if any prose disagrees.

Recheck the manifest, evidence custody, narrow admissions, and deliberately
unclosed blocker statuses with:

```bash
python3 tools/verify_final_truth_completion.py
```

## Closed Stub Map

| Stub | Claim(s) | Primary evidence |
|---|---|---|
| A1/A5 wavelet weights and abs mask | `CLM-MERGE-005` addenda | `bundle_static_runtime_final_stage_constants_four_zoom.md` |
| A2 sharpen Gaussian | `CLM-SHARPEN-001` | `bundle_static_runtime_final_stage_constants_four_zoom.md` |
| A3/A4 bilateral and NLM | `CLM-DENOISE-001` | `bundle_static_runtime_final_stage_constants_four_zoom.md` |
| B1 CalibStage names/slices | `CLM-WARP-003` addenda | `bundle_static_runtime_calibstage_slice_public_names.md` |
| B2 Cost-volume operands | `CLM-WARP-003` addenda | `bundle_static_runtime_index5_cost_operand_names_four_zoom.md` |
| B3 CCM illuminants | `CLM-CCM-002` | `bundle_static_runtime_ccm_illuminant_selection_four_zoom.md` |
| B4 State-machine owner | `CLM-PREFUSION-001/002` addenda | `bundle_static_runtime_calibdataprocessor_public_identity_four_zoom.md` |
| C1 terminal calibration feed | `CLM-WARP-003` addendum | `bundle_static_runtime_prefusion_postterminal_state_to_pipelinecache_four_zoom.md` |
| C2 SGM tuning | `CLM-WARP-003` addenda | `bundle_static_runtime_index5_sgm_parameter_origins_four_zoom.md` |
| C3 row/pixel/file policy | `CLM-MERGE-005` addendum | `bundle_static_runtime_row_image_public_policy_four_zoom.md` |
| C4 C6 terminal exclusion | `CLM-C6-001` | `bundle_static_runtime_c6_terminal_filter_differential_tele.md` |
| C5 wide guard divergence | `CLM-PREFUSION-002` addendum | `bundle_static_runtime_prefusion_wide_218bc4_path_divergence.md` |
| D1 Unit-2 constructor join | `CLM-WARP-003` addendum | `lldb_unit2_capturedimage_constructor_runtime_join.md` |
| E1 Laplacian clarity | `CLM-SHARPEN-002` | `bundle_static_runtime_laplacian_clarity_kernel_28mm.md` |
| Final contributor policy and image consequence | `CLM-MERGE-005/006` | `lldb_final_iramp_score_image_effect_wide_tele.md` |
| Canonical MonoFusion mode disposition | `CLM-PREFUSION-002` | `bundle_static_runtime_prefusion_monofusion_mode_selector_profiles.md` |
| Canonical prefusion parent identity/topology | `CLM-PREFUSION-001` | `bundle_static_runtime_prefusion_parent_identity_closure_four_zoom.md` |
| Canonical tele firing topology | `CLM-ZOOM-002` | `bundle_static_runtime_tele_firing_topology_two_body.md` |

All evidence files above live under `docs/evidence/`.

## Implementation Values

Use the exact constants, formulas, names, and zoom scopes in the
`Final Truth Completion Checklist` table in `docs/TRUTH.md`. In particular:

- preserve float32 values; do not substitute rounded decimal constants;
- treat bilateral spatial support as a uniform 5x5 box, separate from its
  range weight;
- implement SGM with installed `P1=1`, nominal adaptive `P2/P1=500`, and
  guide decay `log2(e)/(18,48,48)`;
- represent the owner cache as `Vec3<Float16>` and working rows as
  `vec4x32f`;
- exclude C6 from canonical tele bridge-HDR super-resolution contribution;
- implement surviving IRAMP contributors as continuous score weights with no
  later per-contributor predicate on the admitted CLI route; and
- implement the admitted Laplacian transfer and `0.75^level` blend, not a
  passthrough stub.

## Scope Guards

- Four-focal claims use the canonical Unit-1 `28/35/70/150mm` quartet unless
  the evidence explicitly adds Unit-2.
- D1 is exact-focal Unit-2 `28mm`.
- E1 runtime liveness is Unit-1 `28mm`; its formula/defaults are
  installed-bundle static same-mechanism proof.
- C4 is canonical `70mm/150mm` bridge HDR; GUI/non-bridge paths are excluded.
- Final score image-effect differential is canonical Unit-1 `35mm/70mm`;
  its four-focal scope is the joined score-use and descriptor-to-writer
  custody proof, not four separate intervention renders.

## Excluded Compatibility Scope

Do not silently broaden the canonical spec to these surfaces:

- MonoFusion mode `1` is reachable for Renderer profiles `1` / `2` and its
  scalar formula is closed at TRUTH `3.0.336`, but those complete alternate
  profile surfaces remain compatibility scope because canonical profile `3`
  excludes them;
- residual implementation-required whole-State/Guidance/selector semantics
  are not open blockers unless a future implementation demonstrates a
  concrete need beyond the admitted operational identities.

The scoped checklist is closed, but the full handoff is withheld. Current
blockers are the ledger `BLOCKER` rows and are summarized in
`PARITY_BLOCKERS.md`; no spec freeze or implementation handoff is authorized.
