# Live State / Object Semantics Closure

## Claim

The canonical profile-3 image path has no remaining anonymous State,
`CapturedImage`, CalibStage, or generated-record field with an unclosed
operational source or formula. Later admitted proofs supersede the broad
historical residual list that kept `CLM-STATE-001` open.

This is an exclusion-based closure, not a claim that every byte of every C++
object has a public protobuf name. Numeric State enum labels, padding,
allocation metadata, diagnostic-only fields, and fields with no demonstrated
image consumer are not implementation requirements.

## Reusable Closure Verifier

```bash
python3 tools/lldb_probes/state_object_semantics_closure/verify_state_object_semantics_closure.py
```

The aggregator runs 13 independent installed-static/runtime verifiers. It
requires each verifier's terminal marker and fails on any nonzero exit or
missing artifact. Expected terminal line:

```text
state_object_semantics_closure=OK
```

## Whole-State Identity and Publication

- Installed RTTI identifies the owner as `lt::CalibDataProcessor`, with
  `runReferenceGroupCams` and `runHigherGroupCams` callbacks returning public
  `CalibDataProcessor::State()`.
- Complete `28/35/70/150mm` runs execute all 13 callback bodies through 38
  paired dispatcher calls per render.
- `state+0xe0/+0xe8` is the retained `shared_ptr<lt::RawImageFactory>`, backed
  by `shared_ptr<lt::CaptureStack>`.
- The terminal whole-State root, not the replaced finalizer sibling, is
  retained at `PipelineCache+0x180` and passed five times through `0x3f7040`
  into `PipelineCache+0x258` after finalization. This positive consequence is
  verified at all four canonical focal tiers and exact-focal Unit-2 `35mm`.

Therefore the whole object needs an internal implementation structure and
the admitted operational records, not a nonexistent one-message protobuf
identity or guessed numeric State labels.

## Public Capture and Calibration Inputs

The image-consequential `CapturedImage` carriers used by admitted formulas
have direct public origins:

| Internal field | Public/operational identity |
|---|---|
| `+0x30` | `CameraModule.is_enabled` |
| `+0x38` | `CameraModule.sensor_exposure` |
| `+0x40` | `CameraModule.sensor_analog_gain` |
| `+0x44` + presence | optional `CameraModule.sensor_digital_gain` |
| `+0x54` | `CameraModule.lens_position` |
| `+0x60` | `CameraModule.id` |
| `+0x64` | `CameraModule.frame_index`; selected factory key is frame `0` |
| `+0x104` + presence | optional `CameraModule.sensor_temparature` |
| `+0x114/+0x118` | `CameraModule.sensor_data_surface.size` |

The constructor/public joins cover all 42 Unit-1 four-focal events and an
exact-focal Unit-2 `28mm` ten-camera runtime discriminator. Body-dependent
calibration values are inputs, not hardcoded universal numbers.

## CalibStage and Generated Records

The complete installed accessor/reference census exposes exactly two stages:

```text
0 = factory at CapturedImage+0x180
1 = current at CapturedImage+0x12c
```

The selected transfer into current is exactly the derived/focus-evaluated and
BA-normalized public calibration tuple:

- `intrinsics.k_mat`;
- `extrinsics.canonical.rotation`; and
- `extrinsics.canonical.translation`.

No third bank name or image-consumed anonymous transferred slice exists in
the installed census.

The five `StereoLayer+0x258` items have whole-record operational identity as
derived per-image, tier-anchor-relative calibrated camera models. Their
meaningful fields are closed as composed K, anchor-relative t/R, derived
offset/scale, public distortion coefficients, and the composed
normalization/center matrix. Runtime/public joins cover Unit-1 four focal
tiers and exact-focal Unit-2 `28mm`. Padding at `+0x64..+0x67` and
`+0xa4..+0xa7` is not assigned semantics because no formula consumes it.

## Downstream Formula Closure

The former State residual list also named downstream items that are now
separate proven claims:

- Guidance is exact `[R,0.5*(G1+G2),B,1]`; selected default hot-pixel removal
  and Bayer-noise LUT generation are formula-closed.
- SGM tuning and recurrence roles are closed, including `Line buf`,
  `Min cost buf`, local cost, adaptive P2 cap, and Cost-volume accumulation.
- IRAMP roles, candidate/sentinel policy, score, accumulator preparation,
  inverse CDF 9/7 reconstruction, weighted contribution, and final-file score
  consequence are closed across the canonical quartet.
- Four-focal stage artifacts and ten-sample index-5 distributions now define
  the validation oracle; stable one-map hashes are explicitly not required.

These are the demonstrated consumers that could have made anonymous State
fields blocking. Their exact inputs and math are admitted independently.

## Residual Disposition

| Historical residual | Current disposition |
|---|---|
| Numeric `CalibDataProcessor::State` enum labels | Nonblocking control-flow labels; all callback bodies/order and image consequences are closed. |
| One public protobuf name for whole State | No such requirement; State is an internal processor object assembled from named public inputs. |
| Remaining `CapturedImage` bytes | No demonstrated consumer outside the admitted field/formula set. Do not invent names. |
| Complete names for every CalibStage byte | Installed census has only factory/current; consumed transfer is exact K/R/t. |
| Whole `state+0x448` protobuf identity | Internal keyed derived-record tree; image-consumed camera-model outputs and public ancestry are closed. |
| Guidance `C0..C2` and universal `C3` | Superseded by exact four-focal/two-body `[R,(G1+G2)/2,B,1]` proof. |
| Stable full-map distributions | Superseded by the admitted ten-sample nondeterministic-map validation policy. |
| Final source contribution / acceptance | Superseded by proven IRAMP operand, candidate, reconstruction, and final-image consequence claims. |
| MonoFusion mode `1` | Explicitly excluded from canonical profile `3`; compatibility-only profiles `1/2`. |

No row above contains an implementation-required unknown for the canonical
profile-3 LRI-to-merged-image target.

## Scope and Admission

- Installed static scope: pinned `libcp.dylib` SHA-256
  `b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`.
- Runtime scope: canonical Unit-1 `28mm`, `35mm`, `70mm`, and `150mm`, with
  exact-focal Unit-2 discriminators at calibration/body-sensitive joins.
- Profile scope: canonical bridge-HDR profile `3`; profiles `1/2` remain
  `CLM-COMPAT-001` reference-only.
- Claim consequence: `CLM-STATE-001` is `PROVEN` / `SPEC_READY`. A future
  newly demonstrated image consumer can open a new scoped claim, but
  anonymous naming alone cannot reopen this one.

