# Evidence: Index-5 Operand Public-Origin Audit, Four Zoom

## Scope

This note is a follow-up to
[lldb_index5_depth_public_meaning_gap_audit_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_index5_depth_public_meaning_gap_audit_four_zoom.md)
for the sampled `StereoLayer<false>` index-5 `0x276860` depth-path packet.

The target question is whether the current Lane B evidence can trace the
runtime operands behind `state+0xe0`, `state+0x448`, and `record+0x40` to
concrete public calibration / LRI names.

Bottom line: this audit does not admit a new public semantic name. It adds a
deterministic negative check for the sampled `0x276860` operand byte slices:
the sampled guide-byte spans and subtraction vectors are absent as exact
16-byte sequences in the whole LRI payload stream and in the checked public
calibration payloads for all four canonical focal tiers. The sampled
subtraction vector is also absent as an exact public calibration fixed32
sequence. The 16-bit table value is intentionally not used as an absence proof
because it is too small and has incidental LRI hits in several tiers.
The same refreshed operand-context harness now also proves same-object internal
producer custody for the target qword fields consumed by that packet:
`+0x198` through `0x26ca94`, `+0x1e8` through `0x26cbcd`, `+0x200` through
`0x26cc01`, and `+0x288` through `0x26c633`.

This supports runtime/internal operand custody, not public-origin closure.

## Admitted Public Bridges Before This Check

The current proof standard already admits these scoped public bridges:

- `record+0x40`: concrete internal identity is the `lt::UpsampleLayer+0x90`
  descriptor, debug-labeled by the disabled `depth_... .dp` dump path and
  built through `0x29ed90` from the `StereoLayer<false>` index-5 source. This
  is not a direct public LRI/protobuf field name.
- `state+0x448`: first-payload `+0x00..+0x20` is copied from the public
  32,832-byte intrinsics-block pose rotation component, and `+0x24..+0x2c`
  from the matching public translation component. Anchors are `A1` for
  `28mm` / `35mm` and `B4` for `70mm` / `150mm`. The checked later
  `+0x30..+0x3c` source slices still have zero exact public fixed32-sequence
  hits.
- `state+0xe0` family: the public LRI key/config carrier space is decoded
  through `LightHeader.field_12` module records and the 262,968-byte
  calibration block's `field_13` keyed nominal tables. The `0xf2770` bridge
  proves runtime object fields matching public camera module fields, and
  `0xf33d0` / `0x1f0ce0` prove exact public K/pose slices for the admitted
  camera subsets. The full `state+0xe0` contents and the index-5 lookup/source
  records still do not have public field names.

## New Operand Byte-Slice Check

The aggregate verifier
[lane_b_index5_public_meaning_audit.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lane_b_index5_public_meaning_audit.py)
now reloads the existing operand-context packets from
`runs/codex_276860_operand_source_context/` and checks three 16-byte operand
slices per focal tier:

- `guide_first16`: first 16 bytes of the guide descriptor reached through
  target `+0x288`;
- `guide_sample16`: the sampled 16 guide bytes consumed by the matched local
  store that later feeds the target `+0x200` vector table and sampled `xmm8`;
- `subvec16`: the 16-byte float vector read through `[rbp-0x208]`, which the
  operand-context proof binds to target `+0x1e8`.

For each slice, the verifier checks:

- exact byte-sequence hits across all payload blocks in the matching LRI;
- exact byte-sequence hits across the three public calibration payload classes
  with sizes `32832`, `262968`, and `35266`;
- for `subvec16`, exact public calibration fixed32-sequence hits.

The verifier requires all three 16-byte slices to have zero exact LRI payload
hits and zero exact calibration payload hits, and requires `subvec16` to have
zero exact public fixed32-sequence hits.

The refreshed operand-context validator also requires the final target qword
fields to have same-object internal custody:

| Target field | Internal custody proof |
|---|---|
| `+0x198` | write-watchpoint stop after the `0x26ca94` store, reported at `0x26ca9b` |
| `+0x1e8` | write-watchpoint stop after the `0x26cbcd` store, reported at `0x26cbd4` |
| `+0x200` | write-watchpoint stop after the `0x26cc01` store, reported at `0x26cc08` |
| `+0x288` | matched same-object producer breakpoint at `0x26c633`; also observed by the `+0x288` watchpoint at `0x26c63a` |

The same refreshed validator now also checks the local `0x26c8e0` buffer layout
used by the sampled packet:

| Layout item | Four-zoom value |
|---|---:|
| Guide descriptor dimensions | `2080 x 1560` |
| Expanded width | `2082` |
| Target `+0x198` table capacity | `16656` `uint16` entries |
| Target `+0x200 - +0x1e8` | `33312` bytes |
| Sampled subtraction-vector offset from `+0x200` | `16` bytes |

## Four-Zoom Results

| Tier | guide first16 | guide sample16 | subvec16 | subvec public fixed32 sequence hits | table u16 LRI hits |
|---|---|---|---|---:|---:|
| `28mm` | `a8383001a8383001a83a3101a73b3101` | `a8383001a83a3101a73b3101a73c3301` | `0000284300006042000040420000803f` | 0 | 1 |
| `35mm` | `2b776c012b766d012a736d012a776e01` | `2b766d012a736d012a776e0129786e01` | `00002c420000ee420000d8420000803f` | 0 | 0 |
| `70mm` | `625a59015f5a58015c5a58015c595a01` | `5f5a58015c5a58015c595a015a586001` | `0000c4420000b4420000b2420000803f` | 0 | 1 |
| `150mm` | `b1542b01b1562c01b0582e01b15c2e01` | `b1562c01b0582e01b15c2e01b15a2d01` | `000031430000a84200002c420000803f` | 0 | 1 |

For every row, `guide_first16`, `guide_sample16`, and `subvec16` have:

- `0` exact hits in the full LRI payload set;
- `0` exact hits in the public calibration payload subset;
- for `subvec16`, `0` exact public calibration fixed32-sequence hits.

The `table u16 LRI hits` column is reported only as a guardrail. A two-byte
needle is not a meaningful public-origin proof or absence proof, and the
incidental hits at `28mm`, `70mm`, and `150mm` are not promoted.

## Interpretation

This check strengthens the public-meaning gap rather than closing it. For the
sampled `0x276860` packet, the immediate operands are now bounded as:

- sampled `xmm8`: locally produced from target `+0x288` guide bytes and loaded
  from target `+0x200`;
- sampled subtraction vector: read through target `+0x1e8`, at `+16` bytes
  past the target `+0x200` interior pointer;
- paired table value: read through target `+0x198`, whose sampled capacity is
  `16656` `uint16` entries;
- sampled `xmm4_low`: reconstructed by
  [lldb_276860_xmm4_origin_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_276860_xmm4_origin_four_zoom.md)
  from those runtime operands and local arithmetic.

The target fields now have concrete same-object internal producer custody, but
no checked operand slice is admitted as a direct public LRI/protobuf byte copy
or as an exact public fixed32 calibration sequence. Therefore this audit does
not justify a canonical upgrade for the Lane B public-meaning blocker.

## Non-Claims

- This does not prove the sampled operands are never derived from public
  calibration values through arithmetic, interpolation, projection, or local
  image/depth processing.
- This does not assign public semantic names to target `+0x198`, `+0x1e8`,
  `+0x200`, or `+0x288`.
- This does not prove full-map payload distributions, all source records, all
  lane positions, or final merge contribution.
- This does not close source-index physical semantics, source-record public
  names, lookup-vector physical meaning, anti-ghosting, or final
  acceptance/rejection.

## Verification

Commands:

```bash
python3 -m py_compile tools/lane_b_index5_public_meaning_audit.py tools/lldb_probes/codex_276860_operand_source_context/operand_source_probe.py tools/lldb_probes/codex_276860_operand_source_context/verify_operand_source.py
python3 tools/lldb_probes/codex_276860_operand_source_context/verify_operand_source.py
python3 tools/lane_b_index5_public_meaning_audit.py
python3 tools/lldb_probes/codex_276860_xmm4_origin/validate_xmm4_origin.py
```

Relevant verifier output:

```text
28mm: ... field_origins={'0x198': 'watch:0x26ca9b', '0x1e8': 'watch:0x26cbd4', '0x200': 'watch:0x26cc08', '0x288': 'producer:guide_store_0x288_reuse_26c633'} field_layout={'expanded_width': 2082, 'table_u16_capacity': 16656, 'midpoint_bytes': 33312, 'sub_delta_from_0x200': 16} guide_u8x4=a8383001 operand_lri_full_hits=guide_first16:0,guide_sample16:0,subvec16:0 subvec_public_fixed32_sequence_hits=0 table_u16_lri_hits=1
35mm: ... field_origins={'0x198': 'watch:0x26ca9b', '0x1e8': 'watch:0x26cbd4', '0x200': 'watch:0x26cc08', '0x288': 'producer:guide_store_0x288_reuse_26c633'} field_layout={'expanded_width': 2082, 'table_u16_capacity': 16656, 'midpoint_bytes': 33312, 'sub_delta_from_0x200': 16} guide_u8x4=2b766d01 operand_lri_full_hits=guide_first16:0,guide_sample16:0,subvec16:0 subvec_public_fixed32_sequence_hits=0 table_u16_lri_hits=0
70mm: ... field_origins={'0x198': 'watch:0x26ca9b', '0x1e8': 'watch:0x26cbd4', '0x200': 'watch:0x26cc08', '0x288': 'producer:guide_store_0x288_reuse_26c633'} field_layout={'expanded_width': 2082, 'table_u16_capacity': 16656, 'midpoint_bytes': 33312, 'sub_delta_from_0x200': 16} guide_u8x4=5f5a5801 operand_lri_full_hits=guide_first16:0,guide_sample16:0,subvec16:0 subvec_public_fixed32_sequence_hits=0 table_u16_lri_hits=1
150mm: ... field_origins={'0x198': 'watch:0x26ca9b', '0x1e8': 'watch:0x26cbd4', '0x200': 'watch:0x26cc08', '0x288': 'producer:guide_store_0x288_reuse_26c633'} field_layout={'expanded_width': 2082, 'table_u16_capacity': 16656, 'midpoint_bytes': 33312, 'sub_delta_from_0x200': 16} guide_u8x4=b1562c01 operand_lri_full_hits=guide_first16:0,guide_sample16:0,subvec16:0 subvec_public_fixed32_sequence_hits=0 table_u16_lri_hits=1
```
