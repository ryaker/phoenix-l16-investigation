# CalibStage Transferred-Slice Public Names

## Question

Name the three slices transferred from the selected `state+0x448` node into
the selector-1/current `CalibStage` bank:

```text
node+0x30..+0x53
node+0x60..+0x83
node+0x54..+0x5f
```

## Reusable verifier

```bash
python3 tools/lldb_probes/calibstage_slice_public_names/verify_calibstage_slice_public_names.py
```

The aggregator reruns three independent admitted verifiers:

- `calibstage_public_names/verify_calibstage_public_names.py`;
- `index5_composed_geometry_origin/verify_composed_geometry_origin.py`; and
- `prefusion_wide_minimum_selector/verify_wide_minimum_selector.py`.

Together they pin the installed selector accessor/copy body, prove exact
transfer bytes, verify the composed-record field roles across all four
canonical focal tiers, and repeat the 28mm result on a second physical body
with distinct calibration bytes.

## Result

The installed binary exposes only two public `CalibStage` selector names:

```text
CalibStage 0 = factory = CapturedImage+0x180
CalibStage 1 = current = CapturedImage+0x12c
```

The three selected-node slices have these public calibration names and
internal destination positions:

| Selected node slice | Current bank destination | Public calibration name |
|---|---|---|
| `node+0x30..+0x53` | `CapturedImage+0x12c..+0x14f` / bank `+0x00..+0x23` | `FactoryModuleCalibration.geometry.per_focus_calibration[].intrinsics.k_mat` |
| `node+0x60..+0x83` | `CapturedImage+0x150..+0x173` / bank `+0x24..+0x47` | `FactoryModuleCalibration.geometry.per_focus_calibration[].extrinsics.canonical.rotation` |
| `node+0x54..+0x5f` | `CapturedImage+0x174..+0x17f` / bank `+0x48..+0x53` | `FactoryModuleCalibration.geometry.per_focus_calibration[].extrinsics.canonical.translation` |

The non-monotonic node order comes from the larger composed geometry record,
where translation precedes rotation:

```text
record+0x00..+0x20 = composed/focus-evaluated K
record+0x24..+0x2c = anchor-relative translation
record+0x30..+0x50 = anchor-relative rotation
```

The normalization/composition chain repacks these as `K, R, t` for
`f33d0`, which writes the contiguous `0x54`-byte current bank.

## Public-origin boundary

These names describe the public calibration quantities and their protobuf
ancestry. The later selected-node values are composed/focus-evaluated and
BA-normalized internal values; they are not asserted to be byte-identical
protobuf wire fields. No third or otherwise unnamed `CalibStage` bank appears
in the complete installed accessor/call-reference census.

## Scope

- Installed-bundle static proof: exact selector names, bank offsets, copy
  order, and accessor/call-reference census.
- Runtime: Unit-1 `28mm`, `35mm`, `70mm`, and `150mm` composed-record
  verification.
- Cross-body discriminator: exact-focal Unit-2 `28mm`.

This closes the requested B1 naming gap. It does not turn derived calibration
records into direct protobuf copies or close unrelated pre-fusion/image
acceptance behavior.
