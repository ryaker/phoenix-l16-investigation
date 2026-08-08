# Static/Runtime Evidence: New Two-Body Calibration Package Corpus

**Date:** 2026-07-16  
**Status:** VERIFIED, scoped `CLM-LRI-001`, `CLM-CORRECTION-001`, and
`CLM-COMPAT-002` addendum  
**Static corpus scope:** two physical calibration signatures, 81 complete new
photograph LRIs, one incomplete LRI, and seven calibration-only LELR containers  
**Runtime scope:** canonical Unit-1 `64mm` wide, `71mm` tele, and old-firmware
`150mm` tele, profile 3, complete Radiance HDR

## Question

What do the standalone calibration files from both physical cameras contain,
how do they relate to calibration embedded in ordinary photographs, and do
their separate hot-pixel maps enter the selected profile-3 path?

## Reusable Verifiers And Custody

`tools/validation/verify_new_lri_calibration_corpus.py` performs a read-only
LELR/protobuf census and writes the rerunnable report:

```text
runs/new_lri/calibration_corpus_2026-07-16.json
```

`tools/lldb_probes/new_lri_variant_census/` contains the installed-static
operator verifier and three runtime probes. Runtime JSON reports are under
`runs/new_lri/variant_census/`. Each zero-hit report now records and verifies
`process={valid:true,state:"exited",exit_status:0}`; a stopped, failed, or
missing process receipt is rejected.

The static verifier pins installed `libcp.dylib` SHA-256
`b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`.

## Body Identity And Reversed Folder Labels

Folder names are not camera identity. The package geometry payload proves:

| Folder label | Canonical identity | Geometry signature | Device UUID words |
|---|---|---|---|
| `Unit 1` | Unit-2 | `223961c6bce6153e...` | `cb225c823202370343d12d05459009b7` |
| `Unit 2` | Unit-1 | `722a6e721636c9c4...` | `7b16be5e646fc40069abec274db42c1e` |

Thus the user-supplied folder labels are reversed relative to the canonical
unit naming already established from per-file calibration signatures.

## Standalone Package To Photograph Join

Each `calibration.lri` is a complete five-block LELR package containing
geometry, vignetting, sensor characterization, color, and device calibration.
For each physical signature, every package payload digest is present unchanged
in all 13 Unit-2 or 68 Unit-1 complete photographs in this new corpus.

| Role | Unit-2 payload SHA-256 | Unit-1 payload SHA-256 |
|---|---|---|
| geometry | `223961c6bce6153e52aa20298ab7eae7a6edb3f2824950a433fdc49df0d4ade1` | `722a6e721636c9c4bc8249f2f0fea14cf34ff00e66a3e50ee17f1e9d8649513e` |
| vignetting | `4ed37b69a473f7c53d0146386509084bf470d75171dfe433ff296e64e28f682c` | `f0c34433f9cf9b07bcf0880f7363db346c79a71a06aef2093a36954eac7660eb` |
| sensor characterization | `37a0a85efe28bcd79e4e6d558edf4832fe43b79107fa11d892a9bc0ffb7cc7a0` | same |
| color | `34f1fc511ef7f6c5d1180c0d2d25a0c55cd75ad538518a44f02c54c49d1e93eb` | `6a0d52b6a4d1b4de62eda1975acec1ada4b0577fdaa2e93ff362247f426c8875` |
| device calibration | `9b83392cc76509cbb19ab0ad7a28c117d4dca995866f3aa3c16b69750577576e` | `7c9f84d9504fbdb761a039f7de6b98486f072d23ed037837b10c166cf597a9c8` |

The complete package file SHA-256 values are
`55d6a343420c49c976b8c87e1036571fc95887fdf0fc7ca676d87181bd4debb8`
for folder `Unit 1` / canonical Unit-2 and
`93ec337b0636d965768ec1236247579b295046c25adfa5b4a54cb4de3f67f52f`
for folder `Unit 2` / canonical Unit-1. `crosstalkcamparams.rec` and
`colorcamparams.rec` are exact complete LELR blocks from their matching
package, not independently transformed data.

## Sensor Characterization Invariance

The public SensorData message is type `2` and contains exact black level `42`,
white level `1023`, cliff slope `2`, and 28 SensorGainVars rows at gain keys
`100,125,...,775`. The decoded row semantics have SHA-256
`8146cf8131776db77b3b3fed70a92e148f44eff5f39ae29000c8105cd9a0f574`.

The exact SensorData-containing payload digest and decoded semantics are
unchanged across both physical signatures and every observed firmware group:
all `9,242` prior complete photographs plus all `81` new complete photographs.
The verifier specifically requires a wire-2 field `16` containing valid
`SensorData{type,data}`. This prevents unrelated top-level field-16 messages
from being misclassified as sensor payloads.

## Zoom Calibration Boundary

The two distinct `zoom_calib_v0` payloads cover all 16 cameras and omit
distortion. After removing distortion, fixed cameras
`A1,A2,A3,A4,A5,B4,C5,C6` match their body's package geometry exactly.
Movable cameras `B1,B2,B3,B5,C1,C2,C3,C4` match the other public geometry
fields but differ in field 6, `angle_optical_center_mapping`.

These files are therefore a distinct calibration revision/stage artifact, not
a byte-equivalent substitute for the final geometry embedded in photographs.
No selected profile-3 consumer of the standalone files is claimed.

## Hot-Pixel Package Boundary

Installed embedded descriptor SHA-256
`81dbe8fab2e3d75ea777db868ced4a94f329da5d3bca8ef680347ee33c8c0926`
names `HotPixelMap.data` and its repeated `HotPixelMeasurement` fields:
`data_offset`, `data_size`, `data_exposure`, `sensor_temparature` (installed
spelling), `sensor_gain`, `pixel_variance`, and `threshold`.

Each physical package has one measurement for every camera, 32 total. Every
measurement uses exposure `15000`, gain `7.75`, threshold
`0.0003000000142492354`, and a zlib-compressed `4160x3120` byte map that
decodes to exactly `12,979,200` bytes. The body-specific files are:

| Canonical body | `hotpixel.rec` size | File SHA-256 |
|---|---:|---|
| Unit-2 | 27,622,099 | `7b4f4ae66ab2b2871f2b83ce1a83d5ac5ba52db982f30495644582a0ad5ec77c` |
| Unit-1 | 29,299,488 | `c76ad485322c32c0ce3f55549778311ead5759b04a1c3798dcee0cd2eb93600d` |

All 830 fired-camera records in the 81 complete photographs set public
`sensor_dpc_on=true`; none embeds a `HotPixelMap` or `DeadPixelMap` record.
This is an input-boundary fact. It does not equate `sensor_dpc_on` with the
standalone map or replace the separately admitted default dynamic hot-pixel
formula.

## Runtime Exclusion And Intermediate-Focal Routes

The installed hot-pixel-leakage operator at `0x3412f0` has body SHA-256
`d6171d861a49366186401ed1f1c5360969576305c511ae669292c1dfd1999a14`;
its correction helper is `0x10acd0`. Seven sites covering entry, calibration
presence/applicability guards, active path, and helper call all record zero
hits in three cleanly completed runs:

| Input | Public route | Result |
|---|---|---|
| Unit-1 `L16_06684`, 64mm | A1-reference wide | HDR complete; all seven sites zero |
| Unit-1 `L16_06675`, 71mm | B4-reference tele | HDR complete; all seven sites zero |
| Unit-1 `L16_00464`, 150mm, firmware `0.1.64229` | B4-reference tele | HDR complete; all seven sites zero |

The 64mm and 71mm runs also reproduce the already-admitted wide and tele
payload-family target sets respectively. Zero hits are limited to these three
profile-3 runs and may not be generalized to every profile or API surface.

## Admission Consequence

- Ordinary clean-room LRI rendering uses the five calibration roles embedded
  in each photograph; the recovered body package proves their concrete origin.
- Camera identity must be keyed by calibration signature/device identity, not
  the supplied directory labels.
- The common sensor characterization is invariant across the complete old and
  new photograph corpus despite body and camera-firmware differences.
- Standalone hot-pixel and zoom-calibration artifacts are real and decoded,
  but no evidence admits them as additional required inputs to the selected
  profile-3 photograph render.
- The new corpus adds no third public firing topology; its 61 wide and 20 tele
  photographs retain the established A1/B4 reference split.
