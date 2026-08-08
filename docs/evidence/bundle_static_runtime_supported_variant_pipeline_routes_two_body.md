# Evidence: Supported Focal/Topology Variant Pipeline Routes

## Result

The three complete local LRIs whose focal label crosses the dominant
wide/tele topology boundary are closed for the canonical profile-3 pipeline.
Public `LightHeader.image_reference_camera` and the public fired-module set,
not `image_focal_length`, select the image route.

Both `28mm`/tele exceptions use the admitted tele path: B4 reference, direct
IRAMP contributors `C1..C5`, no MonoFusion, C6 clear, tele depth/scale policy,
five cross-category warp records, and the public 150mm-family crop. The
`74mm`/wide exception uses the admitted wide path: A1 reference, A1/A2
MonoFusion mode 0, direct contributors `B1..B5`, no C6 clear, wide
depth/scale policy, five cross-category warp records, and its public
35mm-family crop.

No focal-threshold exception remains among the `9,242` structurally complete
local LRIs.

## Complete Variant Matrix

| LRI | Public route | Scorer observation | MonoFusion | C6 | Direct IRAMP contributors | IRAMP scale | Public crop family |
|---|---|---|---|---:|---|---:|---|
| Unit-1 `L16_01175`, focal 28 | B4 / tele, mode 1 | family B selected; no live A/B scorer call in this render | none | clear once | `C1..C5` | `2.1384615898132324` | canonical 150mm |
| Unit-2 `L16_02786`, focal 28 | B4 / tele, mode 1 | family B body live | none | clear once | `C1..C5` | `2.1384615898132324` | canonical 150mm |
| Unit-2 `L16_01931`, focal 74 | A1 / wide, mode 0 | family A body live | mode 0 | no clear | `B1..B5` | `2.507692337036133` | 35mm family |

The Unit-1 `L16_01175` zero-hit scorer result is retained exactly. Installed
selection still maps reference key `8` / mode `1` to family B; this render
produces no live call to either substantive scorer body. A clean-room
implementation must permit the selected calibration-scoring stage to have no
candidate work. Zero hits are not promoted into a different family or a
global skip rule.

## Common Image Route

All three complete runs:

- execute the `lt::CalibDataProcessor` dispatcher;
- select `StereoLayer<false>::runPass` primary body `0x276860`, tile-state
  builder `0x275630`, and primary plane-sweep cost body `0x2732f0`;
- record zero hits at sibling `0x277e70` and sibling cost body `0x2730c0`;
- reach range-map builder `0x26d750` and guided upsample `0x29ed90`;
- call `0x3f7040` exactly five times and cross-category path `0x3f72f0`
  exactly five times;
- reach `src1`, `src2`, and direct wrappers `0x3ecc10`, `0x3ecd80`, and
  `0x3eced0`;
- reach IRAMP entry `0x365960`, inner body `0x3661b0`, and accumulator
  `0x369fa1`; and
- exit `0` with a `10432x7824` Radiance HDR.

Hot sites were disabled after eight hits. Counts equal to eight are liveness
caps, not full-render totals. Five warp-builder/cross-category hits and one
guided-upsample hit are uncapped exact counts for these runs.

## Direct Contributor And Warp Packet

The first captured IRAMP entry in each run contains five 16-byte source
items and five `0x50` warp records. Contributor image-generator object `+0x08`
is the function-data pointer; signed `funcdata+0x90` yields exact public camera
IDs:

```text
L16_01175: 10,11,12,13,14 = C1..C5
L16_02786: 10,11,12,13,14 = C1..C5
L16_01931:  5, 6, 7, 8, 9 = B1..B5
```

Every sampled IRAMP ROI is `512x512`. Its absolute tile origin is a scheduler
observation, not a constant.

## Public Crop And Orientation Join

The compact route reports independently capture one crop-return packet per
variant:

```text
L16_01175 = (0.2668269277, 0.2666666806, 0.7331730723, 0.7333333492)
L16_02786 = (0.2668269277, 0.2666666806, 0.7331730723, 0.7333333492)
L16_01931 = (0.0951923057, 0.1025641039, 0.8951923251, 0.9025641084)
```

These bit-match their public LRI values. The first two are the canonical
150mm crop; the third is a wide/35mm-family crop. `L16_02786` additionally
uses public clockwise orientation, already formula-closed for profile 3.
Thus crop and orientation are consumed from public values independently of
the anomalous focal label.

## Static And Corpus Join

Installed `libcp.dylib` SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

The nested static verifier rechecks the exact installed chain from public
`LightHeader.image_reference_camera` through `CaptureStack+0x44`, the mode
mapping (`8 -> 1`, `14 -> 2`, other valid IDs `-> 0`), and the family split
(`mode 0 -> A`, modes `1/2 -> B`). It also rechecks the complete-corpus
invariant:

```text
A1 -> A1..A5,B1..B5: 6,078 complete LRIs
B4 -> B1..B5,C1..C6: 3,164 complete LRIs
```

The variant runtime addresses are the same already-admitted static formula
bodies used by the canonical four-focal routes. This is a same-mechanism
join, not a second extraction of every formula.

## Scope

- Public topology: all `9,242` structurally complete local LRIs.
- Exception runtime: all three known complete focal/topology exceptions.
- Physical bodies: both calibration signatures are represented by the two
  `28mm`/tele exceptions; the `74mm`/wide exception is Unit-2 and joins the
  already-admitted wide same-mechanism route.
- The two `28mm`/tele files also carry different camera firmware strings.
  This rejects a single-body/single-firmware accident but does not attribute
  route causation to body or firmware.
- Profiles `1/2`, GUI/editing paths, and structurally incomplete LRIs remain
  outside `CLM-COMPAT-002` and under their existing compatibility scope.

## Artifacts

- Compact route probe: `tools/lldb_probes/lri_firing_set_census/variant_route_probe.py`
- Pipeline census probe: `tools/lldb_probes/lri_firing_set_census/variant_pipeline_probe.py`
- Runners: `tools/lldb_probes/lri_firing_set_census/run_variant_routes.sh`, `run_variant_pipeline.sh`
- Verifier: `tools/lldb_probes/lri_firing_set_census/verify_variant_pipeline.py`
- Reports and outputs: `runs/lri_firing_set_census/variant_{route,pipeline}_*.{json,hdr}`

## Verification

```bash
python3 tools/lldb_probes/lri_firing_set_census/verify_variant_pipeline.py
```

Expected prefix:

```text
variant_pipeline=OK
```

## Rejected Upgrades

- Focal length is not a safe wide/tele topology selector.
- Successful output creation alone is not the route proof; the admitted join
  includes stereo, warp, contributor, IRAMP, C6, crop, and output surfaces.
- Unit-1 `L16_01175` does not prove that family B is globally skipped; it is a
  selected-family/no-live-candidate observation for that render.
- The exceptions are not attributed to physical body or firmware.
- This profile-3 supported-input closure is not support for profiles `1/2`,
  GUI/editing paths, or structurally incomplete files.
