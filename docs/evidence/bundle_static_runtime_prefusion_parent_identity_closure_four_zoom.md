# Pre-Fusion Parent Identity Closure

**Date:** 2026-07-02  
**Status:** VERIFIED; admission-ready for `CLM-PREFUSION-001`  
**Scope:** Canonical profile-3 bridge HDR at Unit-1 `28mm`, `35mm`, `70mm`,
and `150mm`, with exact-focal Unit-2 `28mm` / `70mm` discriminators where
needed to eliminate a single-body identity concern.

## Rechecked Proof Chain

The following repo-local verifiers were rerun against the pinned installed
`libcp.dylib` and admitted runtime reports:

```text
prefusion_cache_rtti_identity=OK
reference_single_camera=OK
src2_processlevel1_identity=OK
src2_source_camera_identity=OK
iramp_operand_roles=OK
PASS MonoFusion selector profiles=0->0,1->1,2->1,3->0 canonical_wide=mode0 canonical_tele=no-MonoFusion
```

Reproducers:

```bash
python3 tools/lldb_probes/prefusion_cache_rtti_identity/verify_prefusion_cache_rtti_identity.py
python3 tools/lldb_probes/prefusion_reference_single_camera/verify_reference_single_camera.py
python3 tools/lldb_probes/prefusion_src2_processlevel1_identity/verify_src2_processlevel1_identity.py
python3 tools/lldb_probes/prefusion_src2_source_camera_identity/verify_src2_source_camera_identity.py
python3 tools/lldb_probes/iramp_operand_role_custody/verify_iramp_operand_roles.py
python3 tools/lldb_probes/prefusion_monofusion_mode_selector/verify_mode_selector.py
```

## Exact Parent Identities

The old parent-row wording that called `src1` and `src2` "composite-ish
wrappers over a shared callable" is superseded:

- visible `src1` is `lt::ReferenceImageCache`, retaining exactly one public
  `lt::CapturedImage::Camera`: A1/key `0` at wide and B4/key `8` at tele;
- direct contributors are distinct `lt::SourceImageCache` objects: B1..B5 at
  wide and C1..C5 at tele;
- visible `src2` is `PipelineCache::initResAmp::$_2 ->
  PipelineCache::processLevel1 ->
  ImageWarpClamped<ResamplerFilter=2,vec4x32f>`;
- profile-3 wide `src2` ancestry is A1 target plus A2 through decoded
  MonoFusion mode `0`;
- profile-3 tele constructs no MonoFusion and uses direct B4; and
- outer IRAMP consumes `src1` as the coarse registration guide, `src2` as the
  full-vector reference/baseline patch, and five warped direct sources as
  candidates.

The wrapper callables are distinct and their roles are not anonymous. The
distributed profile-3 reduction is closed by the separately admitted exact
score formula, inverse reconstruction formula, exhaustive local candidate
policy, and final-file score intervention.

## Zoom and Body Scope

The exact wrapper/executor and IRAMP role joins cover canonical Unit-1
`28mm`, `35mm`, `70mm`, and `150mm`. The source-camera identity additionally
uses exact-focal Unit-2 `28mm` and `70mm`; the decoded profile-3 wide
MonoFusion path has an exact-focal Unit-2 `28mm` discriminator. This is enough
to reject a one-body identity artifact without multiplying every arithmetic
test across both cameras.

The canonical quartet remains one calibration body. Capture-date or possible
camera-firmware differences are not attributed to body, and no cross-body
numeric invariance is claimed.

## Admission Consequence

`CLM-PREFUSION-001` is a parent identity/topology claim. Its original premise
has been corrected by stronger installed RTTI and runtime evidence, and its
canonical profile-3 implementation boundary is now `PROVEN` /
`SPEC_READY` at all four focal tiers.

This closure does not decode MonoFusion mode `1` for compatibility renderer
profiles `1` / `2`; installed selector proof places that formula outside the
canonical profile-3 target.

## Joined Evidence

- `docs/evidence/bundle_static_runtime_prefusion_cache_rtti_identity_four_zoom.md`
- `docs/evidence/bundle_static_runtime_prefusion_reference_single_camera_four_zoom.md`
- `docs/evidence/bundle_static_runtime_prefusion_src2_processlevel1_identity_four_zoom.md`
- `docs/evidence/bundle_static_runtime_prefusion_src2_source_camera_identity_two_body.md`
- `docs/evidence/bundle_static_runtime_prefusion_monofusion_source_descriptor_two_body.md`
- `docs/evidence/bundle_static_runtime_iramp_operand_roles_four_zoom.md`
- `docs/evidence/bundle_static_runtime_prefusion_monofusion_mode_selector_profiles.md`
- `docs/evidence/bundle_static_runtime_iramp_score_formula_four_zoom.md`
- `docs/evidence/bundle_static_runtime_iramp_accumulator_reconstruction_four_zoom.md`
- `docs/evidence/bundle_static_runtime_iramp_candidate_policy_four_zoom.md`
- `docs/evidence/lldb_final_iramp_score_image_effect_wide_tele.md`

