# LLDB Evidence: `src1` And Direct Contributor Payload Families Four-Zoom

## Scope

This note records runtime payload-family facts for the visible `src1` lookup
path and the adjacent direct-contributor lookup path on the corrected canonical
four-zoom bridge HDR seed set.

It proves only:

- the visible `src1` lookup at `0x3e0af0`, when reached from `0x3ecc10`,
  resolves through object `+0x18` to a `0x490`-byte payload family with vtable
  address point `libcp+0x65f140`
- the direct contributor lookups at `0x3e0a60` resolve through object `+0x30`
  to a `0x1f0`-byte payload family with vtable address point
  `libcp+0x65f490`
- this payload-family split is stable across the canonical `28mm`, `35mm`,
  `70mm`, and `150mm` bridge HDR seeds

It does not prove:

- the exact camera composition of `src1`
- the exact camera composition of `src2`
- whether the visible `src1` payload is raw, composite, reference, cached,
  resampled, or otherwise produced
- the exact upstream merge/reduction mechanism
- C6 routing
- final merge acceptance / rejection logic

## Probe Method

The probe used LLDB breakpoint callbacks at:

| VA | Meaning |
|---:|---|
| `0x3e0b02` | inside `0x3e0af0`, immediately after the internal `0x1bea00` key derivation |
| `0x3e0a60` | explicit per-key map lookup used by the adjacent direct-contributor path |

The `0x3e0b02` callback was filtered by return address:

| Return offset | Meaning |
|---:|---|
| `0x3ecc42` | visible `src1` wrapper body returned from `0x3e0af0` |

For each LRI, the callback wrote JSON after capturing one `src1` payload and
five direct-contributor payloads. The process was intentionally killed after
that finish condition. The probe is not a render-completion test.

The JSON contains SHA-256 fields over pointer-bearing runtime object bytes.
Those hashes are capture artifacts and are not used as semantic identity proof.

## Runtime Artifacts

| Zoom | Artifact |
|---|---|
| `28mm` | `/private/tmp/l16_payload_family_probe_28mm.json` |
| `35mm` | `/private/tmp/l16_payload_family_probe_35mm_true.json` |
| `70mm` | `/private/tmp/l16_payload_family_probe_70mm.json` |
| `150mm` | `/private/tmp/l16_payload_family_probe_150mm.json` |

Each artifact reached:

| Zoom | Event count | `src1` payload count | Direct contributor payload count | Finish reason |
|---|---:|---:|---:|---|
| `28mm` | `6` | `1` | `5` | `captured_src1_and_five_contributor_payloads` |
| `35mm` | `6` | `1` | `5` | `captured_src1_and_five_contributor_payloads` |
| `70mm` | `6` | `1` | `5` | `captured_src1_and_five_contributor_payloads` |
| `150mm` | `6` | `1` | `5` | `captured_src1_and_five_contributor_payloads` |

## Tested Files

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Direct Contributor Payload Family

Runtime packets from `0x3e0a60`:

| Zoom | Direct contributor keys | Lookup tree | Payload size hint | Vtable address point | First visible slots | `byte+0xf0` | `i32+0xf4` |
|---|---|---|---:|---:|---|---:|---:|
| `28mm` | `[5,6,7,8,9]` | `object+0x30` | `0x1f0` | `0x65f490` | `0x3e81f0`, `0x3e8260`, `0x3e77e0` | `17` | `0` |
| `35mm` | `[5,6,7,8,9]` | `object+0x30` | `0x1f0` | `0x65f490` | `0x3e81f0`, `0x3e8260`, `0x3e77e0` | `17` | `0` |
| `70mm` | `[10,11,12,13,14]` | `object+0x30` | `0x1f0` | `0x65f490` | `0x3e81f0`, `0x3e8260`, `0x3e77e0` | `17` | `0` |
| `150mm` | `[10,11,12,13,14]` | `object+0x30` | `0x1f0` | `0x65f490` | `0x3e81f0`, `0x3e8260`, `0x3e77e0` | `17` | `0` |

This is the same key-vector split proven by
[lldb_src_lookup_and_src2_state_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_src_lookup_and_src2_state_four_zoom.md)
and
[lldb_iramp_contributor_identity_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_iramp_contributor_identity_four_zoom.md).

## Visible `src1` Payload Family

Runtime packets from `0x3e0b02` with return offset `0x3ecc42`:

| Zoom | `src1` key | Lookup tree | Payload size hint | Vtable address point | First visible slots | `byte+0xf0` | `i32+0xf4` |
|---|---:|---|---:|---:|---|---:|---:|
| `28mm` | `0` | `object+0x18` | `0x490` | `0x65f140` | `0x3e53a0`, `0x3e54c0`, `0x3e2dc0` | `1` | `17` |
| `35mm` | `0` | `object+0x18` | `0x490` | `0x65f140` | `0x3e53a0`, `0x3e54c0`, `0x3e2dc0` | `1` | `17` |
| `70mm` | `8` | `object+0x18` | `0x490` | `0x65f140` | `0x3e53a0`, `0x3e54c0`, `0x3e2dc0` | `1` | `17` |
| `150mm` | `8` | `object+0x18` | `0x490` | `0x65f140` | `0x3e53a0`, `0x3e54c0`, `0x3e2dc0` | `1` | `17` |

This confirms the installed-bundle payload-family surface previously bounded
in
[bundle_proof_src1_payload_runtime_surfaces.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_src1_payload_runtime_surfaces.md)
on live four-zoom bridge HDR execution.

## Safe Conclusions

- Proven:
  the visible `src1` lookup payload family and the direct contributor payload
  family are different runtime object families on all four canonical focal
  seeds.
- Proven:
  direct contributor payloads use `object+0x30`, `0x1f0` size hint,
  vtable address point `0x65f490`, and first visible slots `0x3e81f0`,
  `0x3e8260`, `0x3e77e0`.
- Proven:
  visible `src1` payloads use `object+0x18`, `0x490` size hint,
  vtable address point `0x65f140`, and first visible slots `0x3e53a0`,
  `0x3e54c0`, `0x3e2dc0`.
- Proven:
  the visible `src1` payload should not be treated as just another member of
  the direct contributor-vector payload family.
- Still unproven:
  the exact semantic contents or upstream producer math for the visible `src1`
  payload.
- Still unproven:
  the exact upstream merge/reduction mechanism behind `src1` / `src2`.
- Still unproven:
  C6 routing and final merge acceptance / rejection logic.

## Canonical Consequence

This evidence narrows `CLM-PREFUSION-001` and `CLM-PREFUSION-002`.

It does not close `CLM-PREFUSION-002`.
