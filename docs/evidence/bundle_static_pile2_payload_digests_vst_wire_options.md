# Static Proof: Full Calibration Digests, VST Rows, and Leaf Wire Options

## Scope

This bundle independently re-extracts three deterministic items reported by
the external Pile-2 handoff:

1. full SHA-256 digests of the three shared Unit-1 calibration payloads;
2. every exact row of the installed 28-row `SENSOR_AR1335_MONO` VST table; and
3. public protobuf leaf tags, including the formerly unresolved explicit
   `[packed]` options on four repeated-float fields.

It uses the installed `libcp.dylib` with SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`
and the four canonical Unit-1 LRIs. These are static/schema constants and
payload identities, not a body/firmware or pixel-equality claim.

## Calibration Payload Digests

The verifier walks LELR blocks, hashes the exact protobuf payload byte slice,
requires 16 field-13 records for the two calibration-record blocks, and
requires one identical digest per size across Unit-1 `28/35/70/150mm`:

| Payload role | Bytes | Full SHA-256 |
|---|---:|---|
| intrinsics | 32,832 | `722a6e721636c9c4bc8249f2f0fea14cf34ff00e66a3e50ee17f1e9d8649513e` |
| distortion | 262,968 | `f0c34433f9cf9b07bcf0880f7363db346c79a71a06aef2093a36954eac7660eb` |
| depth configuration | 35,266 | `6a0d52b6a4d1b4de62eda1975acec1ada4b0577fdaa2e93ff362247f426c8875` |

The intrinsics digest is the Unit-1 calibration signature. This table does not
claim that Unit-2 has the same intrinsics bytes.

## Exact Installed VST Table

The table begins at VA `0x5ad7c0`, contains 28 records of `0x20` bytes, and
has SHA-256
`e0e40ce025012b1df9c96d0ad59d00f45722d521c48a3bc04de806ae3467d878`.

Record layout is:

```text
u32 gain
f32 scale, threshold, cliff_slope, black_level, white_level,
    panchromatic_a, panchromatic_b
```

Every row has `cliff_slope=2`, `black_level=42`, and `white_level=1023`.
The last column lists the exact seven float32 words in layout order and is the
bit-level authority for clean-room constants.

| gain | scale | threshold | pan a | pan b | exact float32 words |
|---:|---:|---:|---:|---:|---|
| 100 | 74.4856873 | 0.00596670387 | 0.000207456818 | -8.6857417e-06 | 4294f8ac 3bc38457 40000000 42280000 447fc000 395988c4 b711b8fa |
| 125 | 67.1544418 | 0.00666128006 | 0.000254400889 | -1.01740925e-05 | 42864f13 3bda46de 40000000 42280000 447fc000 3985611c b72ab165 |
| 150 | 61.3578491 | 0.00726774288 | 0.000306340138 | -1.22690735e-05 | 42756e70 3bee263f 40000000 42280000 447fc000 39a09c47 b74dd745 |
| 175 | 56.7404556 | 0.00784769468 | 0.000358184392 | -1.44959258e-05 | 4262f63a 3c00939e 40000000 42280000 447fc000 39bbcab2 b7733387 |
| 200 | 53.8029137 | 0.00840817671 | 0.000398355129 | -1.52743396e-05 | 4257362f 3c09c273 40000000 42280000 447fc000 39d0da52 b7802165 |
| 225 | 50.6764603 | 0.00894529 | 0.00044542941 | -1.63957538e-05 | 424ab4b2 3c128f44 40000000 42280000 447fc000 39e98886 b789899d |
| 250 | 48.2387352 | 0.00942320097 | 0.000493855623 | -1.85498593e-05 | 4240f477 3c1a63c5 40000000 42280000 447fc000 3a017617 b79b9b85 |
| 275 | 45.628788 | 0.0099023534 | 0.000546811032 | -2.0436757e-05 | 423683e1 3c223d7b 40000000 42280000 447fc000 3a0f57de b7ab6f9a |
| 300 | 43.9249268 | 0.0102879852 | 0.000597100123 | -2.24683572e-05 | 422fb320 3c288ef0 40000000 42280000 447fc000 3a1c86b6 b7bc7a6e |
| 325 | 41.9443779 | 0.0107046133 | 0.000654310687 | -2.49596324e-05 | 4227c70b 3c2f6267 40000000 42280000 447fc000 3a2b860c b7d16067 |
| 350 | 40.34161 | 0.0110308155 | 0.000713722489 | -2.75923521e-05 | 42215dcf 3c34ba98 40000000 42280000 447fc000 3a3b191b b7e77620 |
| 375 | 38.8205261 | 0.0115449037 | 0.000759243441 | -2.81464745e-05 | 421b4838 3c3d26d6 40000000 42280000 447fc000 3a4707f7 b7ec1c18 |
| 400 | 37.8823013 | 0.0119284056 | 0.000796906766 | -2.77698455e-05 | 4217877a 3c436f5c 40000000 42280000 447fc000 3a50e782 b7e8f34a |
| 425 | 36.8288345 | 0.0121557023 | 0.000855595223 | -3.28919559e-05 | 421350ba 3c4728b6 40000000 42280000 447fc000 3a604a06 b809f578 |
| 450 | 35.6260452 | 0.0126554146 | 0.000902001688 | -2.99273215e-05 | 420e8112 3c4f58a8 40000000 42280000 447fc000 3a6c744f b7fb0c6f |
| 475 | 34.6484756 | 0.0130672473 | 0.00093967258 | -3.38090576e-05 | 420a980a 3c561802 40000000 42280000 447fc000 3a76545c b80dce33 |
| 500 | 33.7362022 | 0.0133966999 | 0.000992617104 | -3.51456474e-05 | 4206f1df 3c5b7dd5 40000000 42280000 447fc000 3a821ab4 b813695a |
| 525 | 33.0826645 | 0.0137022426 | 0.00103916193 | -3.58480575e-05 | 420454a6 3c607f5f 40000000 42280000 447fc000 3a88347d b8165b8f |
| 550 | 32.1953621 | 0.0140718166 | 0.00109070365 | -3.72103787e-05 | 4200c80d 3c668d7a 40000000 42280000 447fc000 3a8ef5f1 b81c1257 |
| 575 | 31.9622211 | 0.0142324837 | 0.00112776016 | -4.21948389e-05 | 41ffb2a1 3c692f5d 40000000 42280000 447fc000 3a93d15a b830fa5d |
| 600 | 30.8683472 | 0.0147785926 | 0.00117735204 | -3.8647464e-05 | 41f6f260 3c7221e9 40000000 42280000 447fc000 3a9a5161 b8221966 |
| 625 | 30.3698502 | 0.0149282739 | 0.00124454044 | -4.15256945e-05 | 41f2f574 3c7495b8 40000000 42280000 447fc000 3aa31fd9 b82e2be0 |
| 650 | 29.9081955 | 0.0153127387 | 0.00126806484 | -4.46551494e-05 | 41ef43fc 3c7ae248 40000000 42280000 447fc000 3aa63532 b83b4c1a |
| 675 | 29.3494186 | 0.0156535096 | 0.00131469965 | -4.24704558e-05 | 41eacb9c 3c803bca 40000000 42280000 447fc000 3aac5200 b832224e |
| 700 | 28.8090649 | 0.0160337146 | 0.00135112158 | -4.36611699e-05 | 41e678f7 3c835923 40000000 42280000 447fc000 3ab1181e b83720d3 |
| 725 | 28.5688934 | 0.0162446797 | 0.00138492824 | -4.79585105e-05 | 41e48d18 3c851390 40000000 42280000 447fc000 3ab5867b b849270f |
| 750 | 28.1127796 | 0.0164958052 | 0.00143637764 | -5.00337301e-05 | 41e0e6f9 3c872236 40000000 42280000 447fc000 3abc44d6 b851db4f |
| 775 | 27.6303043 | 0.0168435685 | 0.00148293283 | -4.71424755e-05 | 41dd0add 3c89fb86 40000000 42280000 447fc000 3ac25ef8 b845bad9 |

## Embedded Descriptor Pins

| Descriptor | File offset | Bytes | SHA-256 |
|---|---:|---:|---|
| `distortion.proto` | `0x5c6f80` | 617 | `3651b91818e2f71d387d4bbb83be9c8aca43d1fb7fead5d62a69742d8c50ec08` |
| `color_calibration.proto` | `0x5c7c00` | 778 | `986015aea1758f57c5fa36e2d29d68eafe81fc5b563a6c28fedae1a18f5f937d` |
| `vignetting_characterization.proto` | `0x5c9ea0` | 575 | `890ef948e0497ff6ac1ea793c1387f947b6cdad4636d049f9951aca4df7861fb` |
| `sensor_characterization.proto` | `0x5c9740` | 566 | `0c249e4e9acbf7d4c1dcb0e3faa0ebbb8ca498f632ba263544924816f9385609` |

## Leaf Wire Contract

Wire type follows the declared protobuf type: enum/integer is `0`, message is
`2`, ordinary float is `5`, and explicitly packed repeated float is `2`.

Selected complete leaf contract:

```text
Distortion
  1 polynomial:message/2, 2 cra:message/2
Distortion.Polynomial
  1 distortion_center:message/2, 2 normalization:message/2,
  3 coeffs:repeated-float/2 packed=true, 4 fit_cost:float/5,
  5 valid_roi:message/2
Distortion.CRA
  1 distortion_center:message/2, 2 sensor_distance:float/5,
  3 exit_pupil_distance:float/5, 4 pixel_size:float/5,
  5 cra:repeated-message/2, 6 coeffs:repeated-message/2,
  7 fit_cost:float/5, 8 valid_roi:message/2,
  9 lens_hall_code:float/5, 10 distance_hall_ratio:float/5

ColorCalibration
  1 type:enum/0, 2 forward_matrix:message/2, 3 color_matrix:message/2,
  4 rg_ratio:float/5, 5 bg_ratio:float/5,
  6 macbeth_data:repeated-message/2, 7 illuminant_spd:repeated-message/2,
  8 spectral_data:message/2
ColorCalibration.SpectralData
  1 format:enum/0, 2 channel_data:repeated-message/2
ColorCalibration.SpectralSensitivity
  1 start:uint32/0, 2 end:uint32/0,
  3 data:repeated-float/2 packed=true

VignettingCharacterization
  1 crosstalk:message/2, 2 vignetting:repeated-message/2,
  3 relative_brightness:float/5, 4 lens_hall_code:int32/0
CrosstalkModel
  1 width:uint32/0, 2 height:uint32/0, 3 data:repeated-message/2,
  4 data_packed:repeated-float/2 packed=true
VignettingModel
  1 width:uint32/0, 2 height:uint32/0,
  3 data:repeated-float/2 packed=true
MirrorVignettingModel
  1 hall_code:int32/0, 2 vignetting:message/2

SensorCharacterization
  1 black_level:float/5, 2 white_level:float/5,
  3 cliff_slope:float/5, 4 vst_model:repeated-message/2
VstNoiseModel
  1 gain:uint32/0, 2 threshold:float/5, 3 scale:float/5,
  4 red:message/2, 5 green:message/2, 6 blue:message/2,
  7 panchromatic:message/2
VstModel
  1 a:float/5, 2 b:float/5
```

The installed `ColorCalibration.IlluminantType` enum remains
`A=0, D50=1, D65=2, D75=3, F2=4, F7=5, F11=6, TL84=7, UNKNOWN=99`.

## Reproduction

```bash
python3 tools/validation/verify_pile2_static_extractions.py \
  --json-out runs/validation/pile2_static_extractions.json
```

The verifier independently reads the installed binary and canonical LRIs. It
does not import the external Pile-2 scripts or results document.

## Admission Boundary

Admit the three full Unit-1 payload digests under `CLM-LRI-001`; the complete
28-row installed type-3 panchromatic table under `CLM-PREFUSION-002`; and the
descriptor-decoded leaf numbers/types plus explicit packed options under
`CLM-LRI-001`, `CLM-WARP-004`, `CLM-CCM-002`, and
`CLM-CORRECTION-001`.

The VST constants are installed/static and body-independent; public analog
gain selects a row as already admitted. The payload digest identity is Unit-1
four-focal scope only. No Unit-2 payload equality or firmware cause is
claimed.
