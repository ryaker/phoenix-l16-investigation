# LLDB Evidence: `state+0x448` Payload Public-Origin Probe, Four Zoom

**Public-name follow-up (2026-06-19):** embedded protobuf descriptor proof now
names the anonymous paths below as
`LightHeader.module_calibration[anchor].geometry.per_focus_calibration[2].extrinsics.canonical.rotation`
and `.translation`. See
[bundle_static_runtime_index5_public_proto_schema_names.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_static_runtime_index5_public_proto_schema_names.md).

## Scope

This note extends the Lane B public-meaning audit for the bounded
`state+0x448` tree/control object.

It tests the first runtime payload-copy sites admitted by
[bundle_proof_iramp_state_448_tree_builder.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_state_448_tree_builder.md)
and the immediate later `+0x30..+0x3c` writes admitted by
[bundle_proof_iramp_state_448_later_payload_writes.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_state_448_later_payload_writes.md):

```text
0x3f30ee -> 0x241590(payload, rbp-0x3d0), writes payload +0x00..+0x20
0x3f3128 -> 0x2415b0(payload, rbp-0x3dc), writes payload +0x24..+0x2c
0x3f3599 -> 0x2415d0(payload, rbp-0x5d0), writes payload +0x30..+0x34
0x3f35f5 -> 0x2415f0(payload, rbp-0x5d8), writes payload +0x38..+0x3c
```

It asks whether those runtime source slices have exact public calibration
origins in the canonical LRIs.

## Artifacts

- Runtime probe:
  [state_448_payload_probe.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_448_payload_public_origin/state_448_payload_probe.py)
- Runtime verifier:
  [verify_state_448_payload_public.py](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_448_payload_public_origin/verify_state_448_payload_public.py)
- Runtime LLDB scripts:
  [state_448_payload_28mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_448_payload_public_origin/state_448_payload_28mm.lldb),
  [state_448_payload_35mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_448_payload_public_origin/state_448_payload_35mm.lldb),
  [state_448_payload_70mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_448_payload_public_origin/state_448_payload_70mm.lldb),
  [state_448_payload_150mm.lldb](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_448_payload_public_origin/state_448_payload_150mm.lldb)
- Convenience runner:
  [run_four_zoom.sh](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lldb_probes/state_448_payload_public_origin/run_four_zoom.sh)
- Raw outputs:
  `runs/state_448_payload_public_origin/state_448_payload_{28mm,35mm,70mm,150mm}.json`
  and `.hdr`

The first redirected `run_four_zoom.sh` attempt lost the LLDB connection before
writing a JSON report and is rejected. The admitted packets are the subsequent
direct single-tier LLDB runs; all four wrote JSON and `10432 x 7824` HDR output.

## Verification

Commands:

```bash
python3 -m py_compile \
  tools/lldb_probes/state_448_payload_public_origin/state_448_payload_probe.py \
  tools/lldb_probes/state_448_payload_public_origin/verify_state_448_payload_public.py
python3 tools/lldb_probes/state_448_payload_public_origin/verify_state_448_payload_public.py
```

The verifier requires:

- each JSON reports process exit `0`, no step cap, no probe errors, and a
  paired output file with Radiance HDR magic bytes;
- LLDB breakpoint hit counts equal the probe's event counts;
- the first two payload-copy sites have matching key sets;
- wide first-insertion keys are `A1..B5`;
- tele first-insertion keys are `B1..C5`, excluding public-fired `C6`;
- later `+0x30..+0x3c` writes cover `A1..A5` at wide tiers and `B1..B5` at
  tele tiers;
- every `+0x00..+0x20` source slice is an exact public fixed32 sequence and
  exactly matches the public 32,832-byte intrinsics-block rotation component
  for anchor `A1` at wide tiers and anchor `B4` at tele tiers;
- every `+0x24..+0x2c` source slice is an exact public fixed32 sequence and
  exactly matches the same anchor's public translation component;
- no checked `+0x30..+0x3c` two-word source slice is an exact public fixed32
  sequence under the recursive calibration fixed32-sequence index.

Verifier output:

```text
28mm: OK; first_payload_0x00_0x20_call_241590:events=10:keys=A1,A2,A3,A4,A5,B1,B2,B3,B4,B5:public_seq=10/10:components=rotation:A1x10; first_payload_0x24_0x2c_call_2415b0:events=10:keys=A1,A2,A3,A4,A5,B1,B2,B3,B4,B5:public_seq=10/10:components=translation:A1x10; later_payload_0x30_0x34_call_2415d0:events=5:keys=A1,A2,A3,A4,A5:public_seq=0/5:components=none; later_payload_0x38_0x3c_call_2415f0:events=5:keys=A1,A2,A3,A4,A5:public_seq=0/5:components=none
35mm: OK; first_payload_0x00_0x20_call_241590:events=10:keys=A1,A2,A3,A4,A5,B1,B2,B3,B4,B5:public_seq=10/10:components=rotation:A1x10; first_payload_0x24_0x2c_call_2415b0:events=10:keys=A1,A2,A3,A4,A5,B1,B2,B3,B4,B5:public_seq=10/10:components=translation:A1x10; later_payload_0x30_0x34_call_2415d0:events=5:keys=A1,A2,A3,A4,A5:public_seq=0/5:components=none; later_payload_0x38_0x3c_call_2415f0:events=5:keys=A1,A2,A3,A4,A5:public_seq=0/5:components=none
70mm: OK; first_payload_0x00_0x20_call_241590:events=10:keys=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5:public_seq=10/10:components=rotation:B4x10; first_payload_0x24_0x2c_call_2415b0:events=10:keys=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5:public_seq=10/10:components=translation:B4x10; later_payload_0x30_0x34_call_2415d0:events=5:keys=B1,B2,B3,B4,B5:public_seq=0/5:components=none; later_payload_0x38_0x3c_call_2415f0:events=5:keys=B1,B2,B3,B4,B5:public_seq=0/5:components=none
150mm: OK; first_payload_0x00_0x20_call_241590:events=10:keys=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5:public_seq=10/10:components=rotation:B4x10; first_payload_0x24_0x2c_call_2415b0:events=10:keys=B1,B2,B3,B4,B5,C1,C2,C3,C4,C5:public_seq=10/10:components=translation:B4x10; later_payload_0x30_0x34_call_2415d0:events=5:keys=B1,B2,B3,B4,B5:public_seq=0/5:components=none; later_payload_0x38_0x3c_call_2415f0:events=5:keys=B1,B2,B3,B4,B5:public_seq=0/5:components=none
```

## Admitted Result

For the first visible `state+0x448` insertion/update path, the source slices
copied into payload fields `+0x00..+0x2c` have exact public component origins:

```text
payload +0x00..+0x20
  <- 0x241590 source rbp-0x3d0
  == 32832-byte intrinsics block
     field_13[anchor].field_3.field_2[2].field_3.field_1.field_1
     rotation component

payload +0x24..+0x2c
  <- 0x2415b0 source rbp-0x3dc
  == 32832-byte intrinsics block
     field_13[anchor].field_3.field_2[2].field_3.field_1.field_2
     translation component
```

The anchor is `A1` for `28mm` / `35mm`, and `B4` for `70mm` / `150mm`.
The copied anchor component is shared across all inserted first-pass keys in
the tested tier, not selected per destination key.

The first-pass inserted key sets are:

| Zoom | First-pass `state+0x448` keys |
|---|---|
| `28mm` | `A1,A2,A3,A4,A5,B1,B2,B3,B4,B5` |
| `35mm` | `A1,A2,A3,A4,A5,B1,B2,B3,B4,B5` |
| `70mm` | `B1,B2,B3,B4,B5,C1,C2,C3,C4,C5` |
| `150mm` | `B1,B2,B3,B4,B5,C1,C2,C3,C4,C5` |

Tele public-fired `C6` is not inserted by this first visible `state+0x448`
payload path under the tested runs.

The immediate later `+0x30..+0x3c` source slices are not exact public fixed32
sequences under the same recursive calibration fixed32-sequence index:

| Zoom | Later keys | `+0x30/+0x34` public sequence hits | `+0x38/+0x3c` public sequence hits |
|---|---|---:|---:|
| `28mm` | `A1,A2,A3,A4,A5` | `0 / 5` | `0 / 5` |
| `35mm` | `A1,A2,A3,A4,A5` | `0 / 5` | `0 / 5` |
| `70mm` | `B1,B2,B3,B4,B5` | `0 / 5` | `0 / 5` |
| `150mm` | `B1,B2,B3,B4,B5` | `0 / 5` | `0 / 5` |

This is narrow negative evidence only. It does not exclude transformed,
partial, non-fixed32, double-precision, or later-populated public origins for
those fields.

## Non-Claims

- This does not prove public semantic names for the `state+0x448` payload as a
  whole.
- This does not prove the public origin of payload fields beyond `+0x2c`.
- This does not prove the public origin of the later `+0x30..+0x3c` fields.
- This does not identify `state+0x448` as a public protobuf table.
- This does not prove public meanings for `object+0x30`, `state+0xe0`, the
  index-5 lookup vector, or the `0x299c70 -> 0x267010` source-index path.
- This does not prove final source contribution, anti-ghosting behavior, or
  final acceptance/rejection.
