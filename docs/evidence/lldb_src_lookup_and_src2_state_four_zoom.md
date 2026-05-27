# LLDB Evidence: `src1` Lookup Key And `src2` State Four-Zoom Runtime Packets

## Scope

This note records runtime facts for the visible `src1` and `src2` wrapper
paths on the corrected canonical four-zoom bridge HDR seed set.

It proves only:

- the key used by the visible `src1` payload lookup at `0x3e0af0` when reached
  from the `0x3ecc10` wrapper body
- the key vector collected by the adjacent post-wrapper `initResAmp` path
- the visible `src2` hot-path state object read by `0x3ebb80`

It does not prove:

- the full camera composition of `src1` or `src2`
- the exact upstream merge/reduction mechanism
- the pixel math that produced the payloads behind those wrappers
- C6 routing
- final merge acceptance / rejection logic

## Probe Method

The `src1` / contributor-key probe used LLDB breakpoint callbacks at:

| VA | Meaning |
|---:|---|
| `0x3e0b02` | inside `0x3e0af0`, immediately after the internal `0x1bea00` key derivation |
| `0x3eb5de` | after `0x3e0bb0` collects the post-wrapper key vector |
| `0x3e0a60` | explicit per-key map lookup used while building `PipelineCache+0x270` wrappers |

The `0x3e0b02` packets were filtered by return address:

| Return offset | Meaning |
|---:|---|
| `0x3ecc42` | `src1` visible wrapper body returned from `0x3e0af0` |
| `0x3ea901` | constructor validation lookup |

The `src2` state probe used LLDB breakpoint callbacks at:

| VA | Meaning |
|---:|---|
| `0x3ebbab` | `0x3ebb80` hot path; callback reads `PipelineCache+0x1e0` directly from `r14+0x1e0` |

The `0x3ebb80` packets were filtered by return address:

| Return offset | Meaning |
|---:|---|
| `0x3ecdad` | visible `src2` wrapper body returned from `0x3ebb80` |
| `0x3eca39` | dispatcher path returned from `0x3ebb80` |

## Runtime Artifacts

| Zoom | `src1` / key-vector artifact | `src2` state artifact |
|---|---|---|
| `28mm` | `/private/tmp/l16_src_lookup_probe_28mm.json` | `/private/tmp/l16_src2_state_probe_28mm.json` |
| `35mm` | `/private/tmp/l16_src_lookup_probe_35mm_true.json` | `/private/tmp/l16_src2_state_probe_35mm_true.json` |
| `70mm` | `/private/tmp/l16_src_lookup_probe_70mm.json` | `/private/tmp/l16_src2_state_probe_70mm.json` |
| `150mm` | `/private/tmp/l16_src_lookup_probe_150mm.json` | `/private/tmp/l16_src2_state_probe_150mm.json` |

## Tested Files

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## `src1` Lookup Key Result

Runtime packets from `0x3e0b02` with return offset `0x3ecc42`:

| Zoom | `src1` derived key | `src1` tree sample from object `+0x18` | Number of sampled `src1` lookups |
|---|---:|---|---:|
| `28mm` | `0` | `[0]` | `12` |
| `35mm` | `0` | `[0]` | `12` |
| `70mm` | `8` | `[8]` | `12` |
| `150mm` | `8` | `[8]` | `12` |

Using the established camera-id naming domain, key `0` maps to `A1` and key
`8` maps to `B4`. This is a key-domain naming statement only. It does not
prove that the returned payload is a raw single-camera image.

## Adjacent Contributor Key Vector Result

The post-wrapper `initResAmp` key-vector path collects a separate key set from
the same cache object.

Runtime packets from `0x3eb5de` and `0x3e0a60`:

| Zoom | Collected key vector | Explicit lookup keys | Tree sample from object `+0x30` |
|---|---|---|---|
| `28mm` | `[5,6,7,8,9]` | `[5,6,7,8,9]` | `[5,6,7,8,9]` |
| `35mm` | `[5,6,7,8,9]` | `[5,6,7,8,9]` | `[5,6,7,8,9]` |
| `70mm` | `[10,11,12,13,14]` | `[10,11,12,13,14]` | `[10,11,12,13,14]` |
| `150mm` | `[10,11,12,13,14]` | `[10,11,12,13,14]` | `[10,11,12,13,14]` |

This matches the direct contributor-vector identity proven separately in
[lldb_iramp_contributor_identity_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_iramp_contributor_identity_four_zoom.md).

The important new separation is:

- `src1` visible lookup uses object `+0x18` and key `0` or `8`
- the direct contributor wrappers use object `+0x30` and keys `[5..9]` or
  `[10..14]`

## `src2` Visible Hot-State Result

Runtime packets from `0x3ebb80` with return offset `0x3ecdad` show a stable
tiered state object at `PipelineCache+0x1e0`.

The state object is not observed as a camera-id key vector in this probe. Its
small vector and scalar fields decode as tiered resample / geometry state.

| Zoom | `state+0x00/+0x04` as f32 | `state+0x20/+0x24` as f32 | `state+0x28..+0x48` as f32 | Number of sampled `src2` calls |
|---|---|---|---|---:|
| `28mm` | `(1.0, 1.0)` | `(2020.0, 1505.0)` | `(0.991346, 0.0, 17.0, 0.0, 0.991346, 13.0, 0.0, 0.0, 1.0)` | `12` |
| `35mm` | `(1.0, 1.0)` | `(2020.0, 1505.0)` | `(0.991346, 0.0, 17.0, 0.0, 0.991346, 13.0, 0.0, 0.0, 1.0)` | `12` |
| `70mm` | `(1.0, 1.0)` | `(2075.0, 1590.0)` | `(0.998077, -0.0, 2.999756, -0.0, 0.998077, 1.999756, -0.0, -0.0, 1.0)` | `12` |
| `150mm` | `(1.0, 1.0)` | `(2075.0, 1590.0)` | `(0.998077, -0.0, 3.0, -0.0, 0.998077, 1.999878, -0.0, -0.0, 1.0)` | `12` |

The vector at `state+0x08..+0x10` contains 32 f32-like entries near `1.0` in
the sampled packets:

| Zoom group | Vector pattern |
|---|---|
| `28mm` / `35mm` | starts at `1.0`, then values near `1.000005`, same pattern on both wide seeds |
| `70mm` / `150mm` | starts at `1.0`, then values near `1.000000..1.000002`, same pattern on both tele seeds |

## Safe Conclusions

- Proven:
  the visible `src1` lookup at `0x3e0af0`, as reached from `0x3ecc10`, derives
  key `0` at `28mm` / `35mm` and key `8` at `70mm` / `150mm`.
- Proven:
  the adjacent post-wrapper direct-contributor key vector is `[5..9]` at
  `28mm` / `35mm` and `[10..14]` at `70mm` / `150mm`, matching direct IRAMP
  contributor identity.
- Proven:
  the visible `src2` wrapper's hot `0x3ebb80` path reads a tiered
  `PipelineCache+0x1e0` state object whose sampled fields are stable across
  the wide pair and the tele pair.
- Still unproven:
  the exact upstream merge/reduction mechanism behind `src1` / `src2`.
- Still unproven:
  whether the `src1` payload key identifies a raw single-camera image, a
  composite image, a reference image, or another cache product.
- Still unproven:
  C6 routing and final merge acceptance / rejection logic.

## Canonical Consequence

This evidence narrows `CLM-PREFUSION-001` and `CLM-PREFUSION-002`.

It does not close `CLM-PREFUSION-002`.
