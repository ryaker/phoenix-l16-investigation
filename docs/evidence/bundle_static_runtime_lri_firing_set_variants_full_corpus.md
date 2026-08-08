# Static/Runtime Evidence: Full-Corpus Firing Sets And Supported Variants

## Result

The public camera firing topology of every structurally complete local LRI is
one of exactly two sets, selected perfectly by the public
`LightHeader.image_reference_camera` value:

| Complete LRIs | Reference camera | Public fired modules |
|---:|---|---|
| `6,078` | `A1` (`0`) | `A1..A5,B1..B5` |
| `3,164` | `B4` (`8`) | `B1..B5,C1..C6` |

No complete LRI has a reduced, empty, or third firing set. Reduced sets occur
only in the `196` structurally incomplete files and have no complete
calibration-body signature.

Focal length is not a universal firing-family selector. Three complete files
cross the otherwise dominant `<70 = wide`, `>=70 = tele` boundary:

| LRI | Focal | Reference | Fired set | Unit signature |
|---|---:|---|---|---|
| `2018-05-25/L16_01175` | `28` | `B4` | tele | `722a6e721636c9c4` |
| `2018-06-26/L16_01931` | `74` | `A1` | wide | `223961c6bce6153e` |
| `2018-10-24/L16_02786` | `28` | `B4` | tele | `223961c6bce6153e` |

All three complete successfully under Renderer profile `3` and write
`10432x7824` Radiance HDR files. These are supported input variants, not
malformed archive debris.

Their public merged framing records are internally consistent with topology,
not with the anomalous focal label:

| LRI | Public crop `(x0,y0,x1,y1)` | Orientation |
|---|---|---:|
| `L16_01175` | `(0.266826928,0.266666681,0.733173072,0.733333349)` | normal `0` |
| `L16_01931` | `(0.095192306,0.102564104,0.895192325,0.902564108)` | normal `0` |
| `L16_02786` | `(0.266826928,0.266666681,0.733173072,0.733333349)` | clockwise `1` |

The two 28mm/tele crops are bit-identical to the canonical 150mm crop. The
74mm/wide crop is in the 35mm crop family. Existing admitted generic crop and
orientation formulas make these public values implementable, but this
evidence does not substitute public-value presence for a variant-specific
runtime route join.

## Custody

- Corpus: `9,438` LRIs below `/Volumes/Base Photos/Light`
- Complete/incomplete split: `9,242 / 196`
- Installed renderer library:
  `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`
- Installed library SHA-256:
  `b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9`
- Census:
  `tools/lldb_probes/lri_firing_set_census/census_lri_firing_sets.py`
- Verifier:
  `tools/lldb_probes/lri_firing_set_census/verify_lri_firing_set_census.py`
- Installed selector verifier:
  `tools/lldb_probes/lri_firing_set_census/verify_reference_camera_family_selector.py`
- Rerun entry point:
  `tools/lldb_probes/lri_firing_set_census/run_census.sh`
- Ignored raw report and render outputs:
  `runs/lri_firing_set_census/`

The scanner walks public LELR headers and protobuf payloads while skipping raw
surface bytes by the declared block lengths. It records focal value, public
reference camera, fired `CameraModule.id` set, firmware string, calibration
payload signature, structural completeness, and every exception path.

## Deterministic Verification

```text
lri_firing_set_census=OK complete=9242 wide=6078 tele=3164 reference_invariant=A1->wide,B4->tele focal_route_exceptions=3 renders=3
```

The three runtime outputs are each `326,479,924` bytes and have:

```text
#?RADIANCE
FORMAT=32-bit_rle_rgbe

-Y 7824 +X 10432
```

The two anomalous 28mm/tele files span both proved calibration signatures and
different camera firmware strings (`0.1.57498 5955738` and
`1.0.16965 6439493`). This is corroboration against a single-body or
single-firmware accident; it does not assign causation to body or firmware.

## Installed Reference-Camera Family Selector

SHA-pinned installed windows close the public scorer-family selection chain:

```text
LightHeader.image_reference_camera
  -> e52c0 reads generated LightHeader+0x124
  -> 0x137d70 CameraID range check
  -> CaptureStack+0x44
  -> 0xe6cf0
  -> runReferenceGroupCams::$_1 callback+0x10
  -> 0x229ec0 camera-key mapping
  -> parent+0x450
  -> 0x224cc0 / 0x242a80
  -> scorer-state+0x234
  -> family switch at 0x244f71
```

The exact installed mapping is:

```text
camera key 8  -> mode 1
camera key 14 -> mode 2
other valid CameraID -> mode 0

mode 1 or 2 -> family B (0x248580 -> 0x24d610)
mode 0      -> family A (0x2481a0 -> 0x24c320)
```

The embedded installed schema independently names LightHeader field `5` as
`image_reference_camera : CameraID`. The complete corpus contains only public
reference values `0` and `8`, so all complete supported LRIs deterministically
select family A and B respectively; focal is absent from this selector.

```text
reference_camera_family_selector=OK LightHeader.image_reference_camera->CaptureStack+0x44->callback+0x10 camera8=mode1 camera14=mode2 other=mode0 mode1/2=familyB mode0=familyA
```

## Public Operational Boundary

The complete-corpus rule that is safe to implement is:

1. decode the public fired `LightHeader.modules` records;
2. use public `image_reference_camera` as the reference identity;
3. consume public merged crop/orientation independently;
4. do not infer camera family or framing from `image_focal_length` alone.

The canonical four-focal evidence already closes the wide and tele formulas
when focal and topology agree, and the installed selector now proves the
candidate scorer family from public reference camera. This evidence does not
yet prove that a 28mm/tele variant executes every other admitted tele
reducer/stereo/C6 route while consuming its public 150mm crop, nor that the
74mm/wide variant executes every other admitted wide route while consuming
its public 35mm-family crop. Reusable candidate-output
custody LLDB scripts and a compact three-case route/crop/C6 campaign are
staged in the same probe directory, but their runs were not admitted because
debugger execution was unavailable during this session. The compact entry
point is `run_variant_routes.sh`; its verifier requires the complete expected
public-key/family/MonoFusion/C6/crop pattern and completed HDR output.

## Scope And Consequence

This is full-local-corpus static proof plus successful profile-3 runtime
output proof for all three complete focal/topology exceptions. It refutes a
universal focal-threshold firing rule and proves that non-baseline capture
variants cannot remain categorically outside the independent LRI-input exit
criterion.

It does not yet close exact reducer-family selection, C6 behavior, crop/warp
composition, or formula-level output parity for those three variants. Those
remain a scoped compatibility blocker.
