# Bundle Proof: Index-5 Range, Cost-Volume, and Depth Names

## Scope

This bundle joins installed `StereoLayer<false>` debug labels to the admitted
index-5 runtime chain. It resolves the semantic names of the generated
source-range descriptor, `StereoLayer<false>+0xf8` object, `0x299c70` output,
and `StereoLayer<false>+0x2a8` output without claiming that generated runtime
products are direct LRI/protobuf fields.

## Artifacts

- Static/runtime verifier:
  `tools/lldb_probes/index5_public_field_names/verify_index5_public_field_names.py`
- Reused range-map reports:
  `runs/codex_26d750_source_range_builder/source_range_*.json`
- Reused cost-volume/index-map custody reports:
  `runs/codex_299c70_source_index_producer/source_index_*.json`
- Reused minimum-cost worker reports:
  `runs/codex_299c70_worker_formula/worker_formula_*.json`
- Reused endpoint/count reports:
  `runs/codex_lookup_endpoint_count_origin/endpoint_count_origin_*.json`

The verifier pins installed `libcp.dylib` SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

## Exact Installed Names

The installed debug routine at `0x26fe00` pairs these literal strings with
these exact `StereoLayer<false>` fields:

| Field | Installed label | Label xref | Field use |
|---|---|---:|---:|
| `+0x2a8` | `Depth map` | `0x26fe3f` | `0x26fe54` |
| `+0x240` | `Images` | `0x26fe83` | `0x26fe9b` |
| `+0x288` | `Guidance` | `0x26fed3` | `0x26feeb` |
| `+0x208` | `Skip mask` | `0x26ff23` | `0x26ff3b` |
| `+0x1e0` | `Pixel buf` | `0x26ff73` | `0x26ff8b` |
| `+0x1b8` | `Range buf` | `0x26ffc3` | `0x26ffdb` |
| `+0x188` | `Min cost buf` | `0x270013` | `0x27002b` |
| `+0x148` | `Line buf` | `0x270063` | `0x27007b` |
| `+0xf8` | `Cost volume` | `0x2700b3` | `0x2700cb` |

Two separate installed xrefs at `0x299f9c` and `0x29a5aa` use the literal:

```text
Range map needs to be the same size as mask.
```

That names the descriptor consumed with the mask inside the cost-volume
constructor family. It must not be conflated with the separately labeled
`StereoLayer+0x1b8` `Range buf`; this proof does not establish pointer identity
between those two objects.

## Custody Join

Static callsite verification and the reused runtime reports establish:

```text
previous StereoLayer+0x2a8 "Depth map"
previous StereoLayer+0x208 "Skip mask"
  -> 0x26d750
  -> generated per-pixel "Range map" of (lower,count)

Range map + target StereoLayer+0x208 "Skip mask"
  -> 0x29a140 / 0x299fd0
  -> target StereoLayer+0xf8 "Cost volume"

Cost volume
  -> 0x299c70 / worker 0x29a670
  -> minimum-cost depth-hypothesis index map

index map + reciprocal ray-depth lookup
  -> 0x267010
  -> StereoLayer+0x2a8 "Depth map"
```

The exact `0x299c70` worker formula gives the cost-volume record fields their
formula-derived semantic names:

```text
record+0x00: base depth-hypothesis index
record+0x04: depth-hypothesis index step
record+0x08: uint16 cost list

selected_index = first argmin(record+0x08 costs)
output_index =
    u16(record+0x00) + u16(record+0x04) * selected_index
```

The output index is then expanded through the already admitted reciprocal
ray-depth lookup and ultimately becomes the millimeter `Depth map`. Therefore
the former generic "source-index descriptor" is a generated minimum-cost
depth-hypothesis index map, and its variable records are per-pixel cost-volume
records.

## Per-Image Composed Geometry Records

The five `0xa8` records at `StereoLayer+0x258` are a separate family from the
variable Cost-volume records. Static custody proves the producer loop:

```text
one source-camera iteration
  -> append one 0x10 item to the exact StereoLayer+0x240 "Images" vector
  -> resolve the same camera through state+0xe0
  -> find the same-key state+0x448 node
  -> 0x264440
  -> 0x23faf0 composition
  -> append one 0xa8 composed geometry record
  -> StereoLayer+0x258
```

The constructor preserves the two vectors separately: `0x26ba90` copies the
`Images` vector to `+0x240` and the parallel `0xa8` vector to `+0x258`.
Complete Unit-1 reports at all four focal tiers show exactly five 16-byte
`Images` entries and five `0xa8` composed geometry records.

`0x28f5a0` uses each record's fields `+0x24..+0x2c` and `+0x30..+0x50` to
form a three-coordinate value by three dot products, computes Euclidean
separation from the first record's value, and retains the maximum separation.
That geometry-spread scalar participates in the already proven lookup-count
formula. This admits the family-level semantic name **per-image composed
geometry records**. It does not assign public protobuf names to every field of
the `0xa8` record.

## Coverage

- The range-map callsite/custody reports cover the complete Unit-1 canonical
  `28mm`, `35mm`, `70mm`, and `150mm` quartet plus exact-focal Unit-2 `28mm`.
- Cost-volume to index-map custody and sampled minimum-cost worker formulas
  cover all six StereoLayer indices on the Unit-1 four-focal quartet.
- The paired `Images` / composed-geometry-record count and `0x28f5a0`
  geometry-spread consumer cover the Unit-1 four-focal quartet.
- The installed labels and callsite hashes are body-independent facts of the
  pinned binary.

The verifier reports:

```text
static_index5_public_field_names=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
source_range_{28mm,35mm,70mm,150mm,unit2_28mm}=OK
source_index_{28mm,35mm,70mm,150mm}=OK
worker_formula_{28mm,35mm,70mm,150mm}=OK
endpoint_count_origin_{28mm,35mm,70mm,150mm}=OK
index5_public_field_names=OK
```

## Admission

Admitted for the Lane B portion of `CLM-WARP-003`:

- `StereoLayer<false>+0x2a8` is exactly named `Depth map`;
- `StereoLayer<false>+0x208` is exactly named `Skip mask`;
- `StereoLayer<false>+0xf8` is exactly named `Cost volume`;
- the generated `0x26d750` `(lower,count)` descriptor is the per-pixel
  `Range map` consumed by the cost-volume builder;
- the `0x299c70` output is a generated minimum-cost depth-hypothesis index map;
  and
- the variable `0x29a140` records are per-pixel cost-volume records with a
  base hypothesis index, hypothesis-index step, and cost list;
- `StereoLayer+0x240` is exactly named `Images`; and
- `StereoLayer+0x258` is the parallel vector of per-image composed geometry
  records used by `0x28f5a0` to compute the geometry-spread term in the lookup
  count.

Together with the separate GDepth custody proof, the named `Depth map` contains
millimeter ray depth, while its generated lookup contains reciprocal
millimeter values.

## Origin Classification and Non-Claims

- The Range map, Cost volume, minimum-cost index map, and Depth map are
  runtime-generated products. They are not direct public LRI/protobuf fields.
- The selected depth bounds originate in pinned binary float tables and are
  not direct LRI calibration copies under the admitted checks.
- This proof does not assign public LRI/protobuf names to every image,
  guidance, cost, or mask operand used to generate the Cost volume.
- This proof does not assign direct protobuf field identity to every
  `StereoLayer+0x258` composed-geometry-record field.
- This proof does not identify the whole `state+0xe0` or `state+0x448`
  records as direct protobuf messages.
- This proof does not establish final source contribution, anti-ghosting
  behavior, or merge acceptance/rejection.
