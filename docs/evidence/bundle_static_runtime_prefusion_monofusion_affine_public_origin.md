# Static/Runtime Evidence: MonoFusion Source Affine Public Origin

**Date:** 2026-07-02  
**Status:** VERIFIED, scoped formula closure  
**Bearing:** `CLM-PREFUSION-001`, `CLM-PREFUSION-002`

## Result

Production-profile MonoFusion normalizes its A2 source into the A1 target
exposure domain as:

```text
Q = f32(
      f32(f32(A1.sensor_exposure) * A1.sensor_analog_gain)
      /
      f32(f32(A2.sensor_exposure) * A2.sensor_analog_gain)
    )

frame_scale = f32(Q / R)

normalized_A2 =
    (raw_A2 - black_level) * frame_scale + black_level
```

`R=2.3183400630950928` is the installed `SENSOR_AR1335_MONO` response.
Public `CameraModule.sensor_digital_gain` is not used in this calculation.

## Installed Formula

SHA-pinned helper `0xe67c0..0xe6ad4`:

1. resolves the active target camera and the requested source key;
2. loads `CapturedImage+0x38 = CameraModule.sensor_exposure`;
3. loads `CapturedImage+0x40 = CameraModule.sensor_analog_gain`;
4. computes target exposure-times-analog divided by source
   exposure-times-analog with float32 operations; and
5. returns that ratio.

The initializer calls `0xe67c0` at `0x1b2387`, gets the installed sensor
response through `0xef820` at `0x1b239b`, divides by response field `+0x0c`,
and passes the result into affine helper `0x1b4390`.

The pinned helper also has an optional owner-metadata ratio branch. The three
live MonoFusion packets below return exactly the public exposure/analog ratio,
so that correction is neutral under the admitted route. This proof does not
generalize the neutral branch to unrelated callers.

## Public/Runtime Join

Embedded protobuf descriptors and direct LRI decoding name all four operands:

```text
LightHeader.modules[A1].sensor_exposure
LightHeader.modules[A1].sensor_analog_gain
LightHeader.modules[A2].sensor_exposure
LightHeader.modules[A2].sensor_analog_gain
```

| Run | A1 `(exposure,analog)` | A2 `(exposure,analog)` | `Q` | `frame_scale=Q/R` |
|---|---|---|---:|---:|
| Unit-1 `28mm` | `(11238709,1.0)` | `(14639008,1.5)` | `0.51181560754776` | `0.22076813876628876` |
| Unit-1 `35mm` | `(1301331,1.0)` | `(2606820,1.0)` | `0.4992024898529053` | `0.21532754600048065` |
| Unit-2 `28mm` | `(42009320,3.875)` | `(42005140,7.75)` | `0.5000497102737427` | `0.21569299697875977` |

All three computed `frame_scale` words equal the runtime affine multiplier
exactly. The Unit-2 row is the physical-body discriminator. Capture dates and
firmware era may affect public values, so this proof joins each runtime result
to its own LRI fields rather than attributing numeric differences to body.

## Scope

Admitted for canonical Unit-1 `28mm` / `35mm` wide plus exact-focal Unit-2
`28mm`. Existing admitted Unit-1 `70mm` / `150mm` evidence proves those tele
routes construct no MonoFusion and use direct B4, giving explicit canonical
four-focal route scope.

This closes the public origin and exact formula for the former
`frame_scale` residual. The secondary callback is closed by the dedicated
follow-up bundle, and an exhaustive basis-matrix follow-up closes transform
boundaries and packing. It does not close unobserved mode `1`,
distributed reduction, or final contributor acceptance/rejection.

## Reproduction

```bash
python3 tools/lldb_probes/prefusion_monofusion_worker/verify_monofusion_worker.py
python3 tools/lldb_probes/prefusion_monofusion_worker/validate_reports.py
```

The verifier pins `0xe67c0`, `0xef820`, their initializer callsites, public
protobuf fields, and all three LRI tuples. The runtime validator reproduces
each affine multiplier with exact float32 equality.
