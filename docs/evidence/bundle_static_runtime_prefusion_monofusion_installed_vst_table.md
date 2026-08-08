# Static/Runtime Evidence: MonoFusion Installed Panchromatic VST Table

**Date:** 2026-07-02  
**Status:** VERIFIED corrective addendum  
**Bearing:** `CLM-PREFUSION-001`, `CLM-PREFUSION-002`

## Result

MonoFusion's A2/type-3 noise coefficients do **not** originate in the tested
LRI's public type-2 `LightHeader.sensor_data` protobuf. They originate in an
installed `libcp.dylib` panchromatic characterization table.

The prior evidence phrase "public-to-prepared VST conversion" is refuted for
this MonoFusion source. There is no such conversion in the admitted path.
Public `CameraModule.sensor_analog_gain` selects an installed table row by
`int(gain * 100)`.

## Installed Table

The installed table has 28 records of `0x20` bytes:

```text
uint32 gain
float  scale
float  threshold
float  cliff_slope
float  black_level
float  white_level
float  panchromatic_a
float  panchromatic_b
```

Its gain keys are `100, 125, ..., 775`. Every row carries
`cliff_slope=2`, `black_level=42`, and `white_level=1023`.

One complete installed copy begins at VA `0x5ad7c0`:

```text
size       = 896 bytes (28 * 0x20)
SHA-256    = e0e40ce025012b1df9c96d0ad59d00f45722d521c48a3bc04de806ae3467d878
copy count = 86
```

All 86 byte-search hits are identical complete 896-byte tables. Static
initializer `0xe1210` materializes one such table: its `0xe1b72` load refers
to the first record at `0x5ad7c0`, then it copies the records into the
installed runtime vector.

The complete 28-row decimal and exact float32-word table is now repo-owned in
`bundle_static_pile2_payload_digests_vst_wire_options.md`; that follow-up also
recomputes this table SHA independently.

## Constructor Custody

CapturedImage path `0xf2770` calls the type-3 constructor through
`0xf2b18 -> 0xef040 -> 0xeeb40`. Runtime at `0xef040` proves:

```text
sensor type = 3 (SENSOR_AR1335_MONO)
row count   = 28
row stride  = 0x20
```

All 28 runtime rows equal the installed `0x5ad7c0` table bytes. Constructor
`0xeeb40` sends each row's `panchromatic_a,b` through `0xee510`; copy path
`0xefc30 -> 0xf0480` preserves that float32 pair at internal row `+0xe0`.
Selector `0xef050` multiplies public analog gain by 100, truncates to an
integer key, and returns the matching row. It performs no coefficient
interpolation or conversion.

## Runtime Selections

| Run | Public analog gain | Key | Installed `(a,b)` selected |
|---|---:|---:|---|
| Unit-1 `28mm` | `1.5` | `150` | `(0.000306340138, -1.22690735e-05)` |
| Unit-1 `35mm` | `1.0` | `100` | `(0.000207456818, -8.68574170e-06)` |
| Unit-2 `28mm` | `7.75` | `775` | `(0.00148293283, -4.71424755e-05)` |

The Unit-1 `28mm` callback captures the complete constructor table. The
Unit-1 `35mm` and Unit-2 `28mm` worker packets independently reproduce the
installed key-100 and key-775 coefficients after the already-proven
`1/(R*C)` initializer scaling.

## Public LRI Discriminator

Embedded descriptors still prove the public names:

```text
LightHeader.sensor_data
  -> SensorData.type
  -> SensorData.data
  -> SensorCharacterization.vst_model[]
  -> VstNoiseModel.panchromatic.{a,b}
```

But each tested LRI carries `SensorData.type=2` (`SENSOR_AR1335`), while the
MonoFusion source is internal type `3` (`SENSOR_AR1335_MONO`). The public
type-2 selected rows are measurably different:

| Run/key | Public LRI type-2 `(a,b)` | Installed type-3 `(a,b)` |
|---|---|---|
| Unit-1 `28mm` / 150 | `(0.000302086235, -1.20084460e-05)` | `(0.000306340138, -1.22690735e-05)` |
| Unit-1 `35mm` / 100 | `(0.000204405005, -8.34425737e-06)` | `(0.000207456818, -8.68574170e-06)` |
| Unit-2 `28mm` / 775 | `(0.00154010509, -5.11798571e-05)` | `(0.00148293283, -4.71424755e-05)` |

Exact float-byte search also finds none of the three installed selected
pairs in their corresponding LRI files. The public schema proves names and
the negative discriminator; it is not coefficient custody for this path.

## Scope

This corrects the production-profile mode-0 MonoFusion input origin at
canonical Unit-1 `28mm` / `35mm`, with an exact-focal Unit-2 `28mm`
physical-body discriminator. Existing admitted canonical Unit-1 `70mm` /
`150mm` evidence proves those tele routes construct no MonoFusion and use
direct B4, so four-focal merge-critical scope is explicit.

This closes the former public-to-prepared VST residual. Later admitted
follow-ups close the per-frame source affine multiplier and secondary-map
callback. A later exhaustive basis-matrix follow-up closes transform
boundaries and packing. It does not close unobserved mode `1`, distributed reduction,
or final acceptance/rejection.

## Reproduction

```bash
python3 tools/lldb_probes/prefusion_monofusion_worker/verify_monofusion_worker.py
python3 tools/lldb_probes/prefusion_monofusion_worker/validate_reports.py
arch -x86_64 lldb -b \
  -s tools/lldb_probes/prefusion_monofusion_worker/unit1_28mm.lldb
```

Reusable artifacts live under
`tools/lldb_probes/prefusion_monofusion_worker/`; raw runtime reports and HDR
outputs live under ignored `runs/prefusion_monofusion_worker/`.
