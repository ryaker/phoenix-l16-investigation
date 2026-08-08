# Correction Liveness and Public Vignetting Schema

> **Corrective supersession (TRUTH 3.0.339):** the cross-talk zero-hit
> conclusion below is refuted. The census breakpointed vtable slot `+0x38`
> while executor `0x2e20` invokes slot `+0x30`. See
> `bundle_corrective_runtime_crosstalk_callback_liveness_two_body_four_zoom.md`.
> The public-schema and vignetting results in this document remain admitted.

## Scope

This is the first consumer-driven proof for `CLM-CORRECTION-001`. It proves
that lens-shading/vignetting is actually applied on every canonical focal
tier, while the four concrete cross-talk row workers have zero hits under the
same complete renders. Related cross-talk property and IR-correction model
surfaces are live. It also extracts the exact public protobuf names and grid
dimensions.

Cross-talk is excluded only from the tested canonical profile-3 quartet, not
globally from the installed bundle.

## Installed Bundle

- binary:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- SHA-256:
  `b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`
- embedded descriptor:
  `vignetting_characterization.proto`
- serialized descriptor SHA-256:
  `890ef948e0497ff6ac1ea793c1387f947b6cdad4636d049f9951aca4df7861fb`

The installed descriptor gives these exact public fields:

```text
FactoryModuleCalibration.vignetting
VignettingCharacterization.crosstalk
VignettingCharacterization.vignetting[]
VignettingCharacterization.relative_brightness
VignettingCharacterization.lens_hall_code

CrosstalkModel.width
CrosstalkModel.height
CrosstalkModel.data[]
CrosstalkModel.data_packed[]

MirrorVignettingModel.hall_code
MirrorVignettingModel.vignetting
VignettingModel.width
VignettingModel.height
VignettingModel.data[]
```

`tools/lri_field_inspect.py` now carries those descriptor-proved names.
Direct decode of canonical Unit-1 block 4 shows all 16 module calibrations
contain:

- one `17 x 13` `CrosstalkModel`;
- exactly `17 * 13 * 16 = 3536` packed float32 values, one 4x4 matrix per
  grid point;
- one mirror-vignetting model for fixed cameras or four models for movable
  cameras;
- each mirror model contains exactly `17 * 13 = 221` float32 values.

## Runtime Harness

- `tools/lldb_probes/correction_liveness/correction_liveness_probe.py`
- `tools/lldb_probes/correction_liveness/unit1_{28,35,70,150}mm.lldb`
- `tools/lldb_probes/correction_liveness/run_four_zoom.sh`
- `tools/lldb_probes/correction_liveness/verify_vignetting_profiles.py`
- `tools/lldb_probes/correction_liveness/vignetting_row_probe.py`
- `tools/lldb_probes/correction_liveness/verify_vignetting_row.py`
- ignored reports:
  `runs/correction_liveness/unit1_{28,35,70,150}mm.json`

All four renders completed with exit status `0`. Breakpoint counts are
instrumented-run observations, not algorithm constants:

| Site | `28mm` | `35mm` | `70mm` | `150mm` |
|---|---:|---:|---:|---:|
| `RemoveVignettingGeneric` variant 0 | 1569 | 1371 | 1363 | 971 |
| variant 1 | 174 | 172 | 5 | 5 |
| variant 2 | 44 | 43 | 45 | 40 |
| shared vignetting-data constructor `0x106cb0` | 628 | 703 | 532 | 369 |
| IR-model selector variant 0 | 1221 | 1161 | 1129 | 928 |
| IR-model selector variant 1 | 1174 | 1122 | 1098 | 875 |
| IR-model selector variant 2 | 12 | 12 | 12 | 12 |
| `RemoveCrossTalkGeneric<vec4x32f,false>` worker | 0 | 0 | 0 | 0 |
| `RemoveCrossTalkGeneric<float,false>` worker | 0 | 0 | 0 | 0 |
| `RemoveCrossTalkGeneric<vec4x32f,true>` worker | 0 | 0 | 0 | 0 |
| `RemoveCrossTalkGeneric<float,true>` worker | 0 | 0 | 0 | 0 |

The same runs hit public property reads for
`lens_shading.type`, `lens_shading.multiplier`,
`cross_talk_correction.type`, and `ir_correction` on every tier.

RTTI type names and their installed vtables independently identify the four
cross-talk workers at `0xfebf0`, `0x1019a0`, `0x1053b0`, and `0x106c80`;
generic executor `0x2e20` invokes its row callback through vtable slot
`+0x30`. Their zero counts therefore exclude the pixel workers, not merely
one guessed wrapper address. Property reads are configuration activity and
do not contradict the worker exclusion.

## Static Operational Boundary

RTTI identifies the three vignetting bodies as:

```text
RemoveVignettingGeneric<vec4x32f,true>
RemoveVignettingGeneric<float,true>
RemoveVignettingGeneric<vec4x32f,false>
```

Their shared constructor `0x106cb0`:

1. reads `CapturedImage+0x50`, whose admitted public origin is
   `CameraModule.mirror_position`;
2. clamps to an endpoint mirror model or brackets two public
   `MirrorVignettingModel.hall_code` keys;
3. for an interior code `h`, computes float32
   `t=(h-h1)/(h0-h1)` and linearly combines all 221 profile floats in
   instruction order as `t*V0 + (1-t)*V1`;
4. runs one of two profile-shaping branches selected by the runtime boolean.

For interpolated profile value `V`, public `lens_shading.multiplier = m`, and
runtime inverse flag `q`, the exact shaping is:

```text
S = float32(float32(float32(V - 1.0f) * m) + 1.0f)
output = q ? float32(S / V) : S
```

Thus observed `(q,m)` pairs `(0,1)`, `(1,0)`, and `(1,1)` produce `V`, `1/V`,
and `1`.

Two-body runtime replay:

| Discriminator | Complete packets | Runtime keys | Result |
|---|---:|---:|---|
| Unit-1 canonical `28mm` | 12 | 10 | all 221 floats byte-exact |
| Unit-2 exact `70mm` | 12 | 10 | all 221 floats byte-exact, including interior interpolation |

The selected public calibration is
`LightHeader.module_calibration[CapturedImage+0x60]`. The selected record's
own public `camera_id` is not the vector index and the vector order differs
between the two bodies. The verifier requires the unique public profile match
to occur at exactly that runtime index; this avoids attributing calibration
ordering to firmware or physical-body causation.

The installed `17x13` 4x4 IR-table builder at `0x102ab0` has only direct
callers in the two cross-talk wrapper bodies (`0xfb000`, `0xfb6a0`).
Construction/configuration can therefore be live while the four terminal
cross-talk row workers remain zero-hit. Under the canonical quartet, those
IR tables have no admitted pixel effect outside the excluded cross-talk path.

The `vec4x32f,true` row worker at `0x108080` bilinearly samples that shaped
`17 x 13` profile over the requested image rectangle, multiplies RGB lanes by
the sampled scalar, and preserves alpha. The `vec4x32f,false` worker at
`0x1086c0` uses the same sample and multiplies all four lanes. The float
specialization has the same scalar profile role.

The worker uses profile spacing equal to mapped image span divided by
`(profile_width-1, profile_height-1)`, floors the profile-cell indices, and
performs float32 row-slope interpolation followed by its visible double
pixel-coordinate multiply/add and float32 conversion. A stopped Unit-1
`28mm` store at `0x108257` captures spacing `(260,260)`, tile origin
`(2048,0)`, profile cell `x=7`, factor `1.7397128343582153`, source
`(0.0286896061,0.0309858881,0.0195157155,1)`, and output
`(0.0499116741,0.0539065488,0.0339517407,1)`. The independent verifier
replays all four output lanes exactly.

This proves real pixel-domain lens-shading application, not mere calibration
parsing. Exact shaping constants and coordinate/rounding replay are retained
as the next formula-closure step.

## Admission

- Runtime: canonical Unit-1 `28/35/70/150mm`, completed full renders.
- Static: SHA-pinned installed bundle and embedded public schema.
- Cross-unit: Unit-1 `28mm` plus exact-focal Unit-2 `70mm`; all public profile
  bytes differ by calibration and both replay exactly.
- Claim consequence: `CLM-CORRECTION-001` is `PROVEN` / `SPEC_READY` for
  canonical profile-3 LRI-to-merged-image scope.
