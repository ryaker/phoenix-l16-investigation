# Cross-Talk Selector Public Origins

## Result

The selected scalar cross-talk table inputs are joined to public LRI fields.
The installed selector receives:

```text
sensor_type = LightHeader.sensor_data.type
variant = any FactoryModuleCalibration.color[].color_matrix is present
CCT = robertson_xy_to_cct(scene_xy)
```

`scene_xy` is the same public-AWB plus public A/D65 color-calibration result
already formula-closed by
`bundle_static_runtime_ccm_chromaticity_public_origin_four_zoom.md`. This
bundle pins its direct conversion to the CCT consumed by the cross-talk amount
fit. It removes the last internal-only labels from the A/B/C table selector;
it does not change the selected worker formula or its scope.

## Installed Custody

Binary:
`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`

SHA-256:
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`

The verifier instruction-pins these paths:

```text
0xfe607 call 0xf2730             sensor selector
0xf2734 mov eax,[rdi+0x100]      CapturedImage sensor type

0xfe60f mov rdi,rbx
0xfe612 call 0xf36c0             variant selector
0xf36c4 mov rax,[rdi+0xa0]
0xf36cb mov al,[rax+0x280]

0x33e91e lea rsi,[rbx+0xc]       scene xy
0x33e929 call 0xab2e0            Robertson xy -> CCT/tint
0x33e9e1 call 0xfe570            cross-talk amount fit
```

The selected factory at `0xfe570` therefore receives the sensor, variant, and
CCT values whose origins are proved below.

## Sensor Type

The installed embedded descriptors name the source fields:

```text
LightHeader.sensor_data       field 16, message
SensorData.type               field 1, enum
SensorType 2                  SENSOR_AR1335
```

The `sensor_type.proto` serialized descriptor SHA-256 is
`c7800a32690c4dbb09faa66d84cda8aecdb7b67a22183e3a47190e241af8b952`.
Both exact-28mm body inputs contain only public type `2`, and both the amount
fit and generated-IR builder capture type `2`.

## Variant Predicate

The installed `FactoryModuleCalibration` converter at `0xe3360` sets owner
byte `+0x280` as follows:

```text
0xe3a1c cmp dword [rbx+0x20],0        repeated color count
0xe3a30 mov rax,[rbx+0x28]           repeated color array
0xe3a34 mov rsi,[rax+r13*8+8]        ColorCalibration message
0xe3a39 test byte [rsi+0x10],4       generated has-bit for field 3
0xe3a3f mov byte [r12+0x280],1       set variant
```

The SHA-pinned embedded schema names the messages and field:

```text
FactoryModuleCalibration.color       field 2, repeated ColorCalibration
ColorCalibration.color_matrix        field 3
```

For this proto2 generated layout, mask `4` is field 3's presence bit. Thus
the formerly internal `variant_flag` has the concrete public predicate:

```text
variant = exists(color record with color_matrix present)
```

Each tested physical-body LRI has 42 such records. Captures agree at all
three boundaries: fit selector `1`, generated-IR builder `1`, and owner
`+0x280 = 1`.

## Scene CCT

The cross-talk producer passes `primary+0xc`, the live scene `(x,y)`, directly
to installed Robertson converter `0xab2e0`, then passes the resulting CCT to
the amount fit. The public origin and exact formula for that scene value are
already admitted: public `ViewPreferences.awb_gains` and the selected
camera's public A and D65 `ColorCalibration.color_matrix` records are solved
and round-tripped through the installed temperature/tint conversion.

This bundle independently requires those public AWB and A/D65 carriers in
each tested body and checks bit equality between `0xab2e0`'s captured CCT and
the fit's CCT:

| Input | Captured public-derived scene xy | CCT passed to fit |
|---|---|---:|
| Unit-1 exact `28mm` | `(0.34644079208374023, 0.3529967963695526)` | `4953.66357421875` |
| Unit-2 exact `28mm` | `(0.3719750940799713, 0.36769843101501465)` | `4175.767578125` |

The Unit-1 movable B2 packet receives the same scene-owner xy and CCT while
independently exercising camera group 1 and the optional C-table gate.

## Scope

Installed formula and schema scope are body/focal independent. Exact selector
custody and public-field census cover distinct-calibration exact-28mm inputs
from both physical bodies plus the Unit-1 movable B2 discriminator. The
upstream public AWB/A-D65 scene solve has its separately admitted Unit-1
four-focal runtime replay. Companion cross-talk evidence supplies complete
Unit-1 four-focal and exact-70mm Unit-2 selected-path liveness.

This does not claim profiles 1/2, non-AR1335 inputs, absent-color-matrix
packages, firmware invariance, or body/firmware causation.

## Reproduction

```bash
python3 tools/lldb_probes/correction_liveness/verify_crosstalk_selector_public_origins.py
```

Expected terminal summary begins:

```text
crosstalk_selector_origins=OK ... cases=2 ...
```
