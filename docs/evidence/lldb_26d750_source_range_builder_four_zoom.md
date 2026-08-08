# Evidence: `0x26d750` Index-5 Source-Range Builder, Four Zoom

## Scope

This LLDB proof targets the immediate producer edge before the existing
`0x29a140` source-local object proof:

```text
0x26bd90 caller
  -> 0x26be35 call 0x26d750
  -> 0x26be50 call 0x29a140
  -> 0x299c70 / 0x29a670 source-index producer/worker
  -> 0x267010 index-image-to-lookup-vector expansion
```

The question is whether the `StereoLayer<false>` index-5 source-index
descriptor has an admitted internal meaning before it enters `0x29a140`.

Bottom line: yes, within internal scope. For the tracked index-5 object,
`0x26d750` builds a `2080 x 1560`, stride-`2080`, 4-byte-per-pixel descriptor
whose entries are two `uint16` values:

```text
u16 +0x00 = lower source-record / lookup index
u16 +0x02 = count
```

The builder derives those pairs from lower/upper half-resolution range tables,
applies the target object's `+0x10` padding field, clamps against the live
lookup-vector count, and passes the populated descriptor unchanged as `rsi` to
`0x29a140`. Combined with the already admitted `0x29a140` and `0x29a670`
proofs, this closes the internal source-index descriptor as a per-pixel
candidate range over the index-5 reciprocal ray-depth lookup vector.

This does not admit a public LRI/protobuf field name, public unit, source-record
public name, full-map distribution, final image contribution, anti-ghosting
policy, or final acceptance/rejection behavior.

## Static Edge

Installed disassembly binds the caller and callee sites used by the probe:

```text
0x26be35: call 0x26d750
0x26be3a: lea rdx, [r14 + 0x208]
0x26be50: call 0x29a140

0x26d750: source-range builder entry
0x26d7aa: after seeded output descriptor
0x26d7f5: after 0x267120
0x26d8ac: after 0x298ff0 local range-table construction
0x26d9bc: sampled output-pair store
0x26da56: builder return
```

At the `0x26be35` caller edge and at the `0x26d750` entry, the verifier checks
the same argument relationships:

```text
rdi = target StereoLayer object
rsi = source_layer + 0x2a8
rdx = source_layer + 0x208
r8  = caller rbp - 0x60 output descriptor local
r9  = target + 0x23c max-upper field
stack arg = target + 0x238 min-lower field
ecx = 8
```

The source descriptors at `source_layer+0x2a8` and `source_layer+0x208` are
both `1040 x 780`, stride `1040`. The output descriptor created by `0x26d750`
is `2080 x 1560`, stride `2080`.

## Runtime Corpus

The complete accepted corpus is the canonical Unit-1 four-zoom set plus one
Unit-2 exact-28mm spot check:

| Report | LRI scope | Output first pair |
|---|---|---|
| `source_range_28mm.json` | Unit-1 canonical 28mm `L16_02130` | `(205, 9)` |
| `source_range_35mm.json` | Unit-1 canonical 35mm `L16_03041` | `(27, 3)` |
| `source_range_70mm.json` | Unit-1 canonical 70mm `L16_03434` | `(2, 4)` |
| `source_range_150mm.json` | Unit-1 canonical 150mm `L16_02285` | `(19, 5)` |
| `source_range_unit2_28mm.json` | Unit-2 exact 28mm `L16_02130` | `(20, 3)` |

All five runs exit `0` and write Radiance HDR outputs. The Unit-2 exact-28mm
run proves this edge is not only a Unit-1 artifact for the tested focal class;
it is not claimed as all-body/all-focal coverage.

## Admitted Formula

For sampled stores at `0x26d9bc`, the verifier reconstructs the live formula
from registers, local range-table pointers, and the target/output descriptor:

```text
mapped_x = floor(x * (source_width  - 1) / (target_width  - 1))
mapped_y = floor(y * (source_height - 1) / (target_height - 1))

low_word  = u16[range_low  + 2 * (mapped_x + mapped_y * range_low_stride)]
high_word = u16[range_high + 2 * (mapped_x + mapped_y * range_high_stride)]

lower = max(low_word - target+0x10, 0)
upper = min(high_word + target+0x10, max_lookup_index)
count = upper - lower

u16[output + 4 * (x + y * output_stride) + 0] = lower
u16[output + 4 * (x + y * output_stride) + 2] = count
```

The verifier requires at least eight sampled stores per report to satisfy that
formula and to match the value actually stored in the output descriptor. Each
accepted report captured 17 target `builder_after_output_store` stops before
disabling the store breakpoint.

Example first-pixel checks:

| Scope | `low_word` | `high_word` | `max_lookup_index` | Stored `(lower,count)` |
|---|---:|---:|---:|---|
| 28mm Unit-1 | 206 | 213 | 751 | `(205, 9)` |
| 35mm Unit-1 | 28 | 29 | 751 | `(27, 3)` |
| 70mm Unit-1 | 3 | 5 | 1471 | `(2, 4)` |
| 150mm Unit-1 | 20 | 23 | 1471 | `(19, 5)` |
| 28mm Unit-2 | 21 | 22 | 735 | `(20, 3)` |

At `0x26be50`, the same populated descriptor is passed to `0x29a140` as `rsi`;
`rdx` is `target+0x208` and `ecx` remains `8`. This is the previously admitted
`0x29a140` source-local producer input boundary.

## Integration With Prior Proofs

This proof sits between the existing source-object and source-index proofs:

- `lldb_index5_source_object_field_origin_four_zoom.md` proves the immediate
  `StereoLayer<false>+0xf8` assembly path through `0x29a140`, `0x28f420`, and
  `0xf340`.
- `lldb_29a140_source_local_producer_four_zoom.md` proves that `0x29a140`
  converts the input 4-byte descriptor into source-local records with headers
  `(input_u16_0, input_u16_2, 1, rounded)`, where
  `rounded = ceil(input_u16_2 / 8) * 8`.
- `lldb_source_index_299c70_worker_formula_four_zoom.md` proves sampled
  `0x29a670` worker tiles write the selected min-cost source-record index.
- `lldb_index5_267010_mapping_four_zoom.md` proves `0x267010` consumes the
  resulting `uint16` source descriptor as indices into `StereoLayer<false>+0xe0`
  and writes `lookup[source_u16]` float output.

With this new edge, the internal chain is now:

```text
0x26d750 output pair
  -> lower/count candidate range per target pixel
  -> 0x29a140 source-local records
  -> 0x299c70 / 0x29a670 min-cost selected source index
  -> 0x267010 lookup[source_u16]
  -> float value from the internally generated reciprocal ray-depth table
```

The public-meaning gap is therefore narrower: source-index descriptor semantics
are no longer open as an internal behavior question. They remain open as public
LRI/protobuf naming, physical-unit naming, and final contribution questions.

## Artifacts

- Probe harness:
  [source_range_builder_probe.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_26d750_source_range_builder/source_range_builder_probe.py)
- Verifier:
  [verify_source_range_builder.py](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_26d750_source_range_builder/verify_source_range_builder.py)
- Runners:
  [run_four_zoom.sh](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_26d750_source_range_builder/run_four_zoom.sh),
  [run_unit2_28.sh](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_26d750_source_range_builder/run_unit2_28.sh)
- LLDB scripts:
  [source_range_28mm.lldb](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_26d750_source_range_builder/source_range_28mm.lldb),
  [source_range_35mm.lldb](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_26d750_source_range_builder/source_range_35mm.lldb),
  [source_range_70mm.lldb](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_26d750_source_range_builder/source_range_70mm.lldb),
  [source_range_150mm.lldb](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_26d750_source_range_builder/source_range_150mm.lldb),
  [source_range_unit2_28mm.lldb](/Volumes/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/codex_26d750_source_range_builder/source_range_unit2_28mm.lldb)
- Raw reports:
  `runs/codex_26d750_source_range_builder/`

## Verification

Commands:

```bash
bash tools/lldb_probes/codex_26d750_source_range_builder/run_four_zoom.sh
bash tools/lldb_probes/codex_26d750_source_range_builder/run_unit2_28.sh
python3 tools/lldb_probes/codex_26d750_source_range_builder/verify_source_range_builder.py
file runs/codex_26d750_source_range_builder/source_range_*.hdr
```

Verifier output:

```text
source_range_150mm.json: OK target=0x7fc28c104980 data=0x7fc28e8c8040 first_pairs=[(19,5), ...]
source_range_28mm.json: OK target=0x7f9c037044e0 data=0x7f9b84fc8040 first_pairs=[(205,9), ...]
source_range_35mm.json: OK target=0x7f99a7844590 data=0x7f999252c040 first_pairs=[(27,3), ...]
source_range_70mm.json: OK target=0x7ff1bc7649c0 data=0x7ff1a98c8040 first_pairs=[(2,4), ...]
source_range_unit2_28mm.json: OK target=0x7f81891149d0 data=0x7f80e65d4040 first_pairs=[(20,3), ...]
```

All `.hdr` outputs identify as Radiance HDR image data.

## Rejected Upgrades

This proof does not admit these stronger statements:

- "`0x26d750` proves a public LRI/protobuf source-index field."
- "The source-records have public semantic names."
- "The ray-depth endpoint pair has public units or a public calibration field
  name."
- "The first-pair values above are constants." They are report samples.
- "The Unit-2 exact-28mm spot check proves all physical bodies and focals."
- "The internal source-index range proves final image contribution or
  acceptance/rejection."

No canonical claim status upgrade is made from this proof.
