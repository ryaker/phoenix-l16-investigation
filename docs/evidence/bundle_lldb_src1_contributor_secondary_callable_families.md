# Bundle + LLDB Evidence: `src1` And Direct Contributor Secondary Callable Families

## Scope

This note extends
[lldb_src1_contributor_payload_family_four_zoom.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lldb_src1_contributor_payload_family_four_zoom.md).

It records one additional runtime-plus-static fact:

- the visible `src1` `0x490` payload family carries a secondary callable /
  address-point value at payload `+0x60` that resolves to `libcp+0x65f388`
- the direct contributor `0x1f0` payload family carries a different secondary
  callable / address-point value at payload `+0x60` that resolves to
  `libcp+0x65f4d8`
- this split is observed across the canonical `28mm`, `35mm`, `70mm`, and
  `150mm` bridge HDR seeds

It does not prove:

- the semantic contents of visible `src1`
- the semantic contents of visible `src2`
- the exact upstream merge/reduction mechanism
- C6 routing
- final merge acceptance / rejection logic

## Runtime Artifacts

The runtime source is the JSON already produced by the payload-family probe:

| Zoom | Artifact |
|---|---|
| `28mm` | `/private/tmp/l16_payload_family_probe_28mm.json` |
| `35mm` | `/private/tmp/l16_payload_family_probe_35mm_true.json` |
| `70mm` | `/private/tmp/l16_payload_family_probe_70mm.json` |
| `150mm` | `/private/tmp/l16_payload_family_probe_150mm.json` |

## Tested Files

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Runtime Result

At runtime, payload qword `+0x60` is family-specific:

| Zoom | Path | Keys | Payload vtable | Payload `+0x60` address point | Static address point | Substantive slot `+0x30` |
|---|---|---|---:|---:|---:|---:|
| `28mm` | direct contributors | `[5,6,7,8,9]` | `0x65f490` | `base+0x65f4d8` | `0x65f4d8` | `0x3e78d0` |
| `28mm` | visible `src1` | `0` | `0x65f140` | `base+0x65f388` | `0x65f388` | `0x3e4a80` |
| `35mm` | direct contributors | `[5,6,7,8,9]` | `0x65f490` | `base+0x65f4d8` | `0x65f4d8` | `0x3e78d0` |
| `35mm` | visible `src1` | `0` | `0x65f140` | `base+0x65f388` | `0x65f388` | `0x3e4a80` |
| `70mm` | direct contributors | `[10,11,12,13,14]` | `0x65f490` | `base+0x65f4d8` | `0x65f4d8` | `0x3e78d0` |
| `70mm` | visible `src1` | `8` | `0x65f140` | `base+0x65f388` | `0x65f388` | `0x3e4a80` |
| `150mm` | direct contributors | `[10,11,12,13,14]` | `0x65f490` | `base+0x65f4d8` | `0x65f4d8` | `0x3e78d0` |
| `150mm` | visible `src1` | `8` | `0x65f140` | `base+0x65f388` | `0x65f388` | `0x3e4a80` |

## Static Vtable Bytes

Static reads from the installed `libcp.dylib`:

| Address point | Slot `+0x00` | Slot `+0x08` | Slot `+0x10` | Slot `+0x18` | Slot `+0x20` | Slot `+0x28` | Slot `+0x30` | Slot `+0x38` | Slot `+0x40` |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `0x65f388` | `0x3e49f0` | `0x3e4a00` | `0x3e4a10` | `0x3e4a40` | `0x3e4a60` | `0x3e4a70` | `0x3e4a80` | `0x3e4b70` | `0x3e4b90` |
| `0x65f4d8` | `0x3e7840` | `0x3e7850` | `0x3e7860` | `0x3e7890` | `0x3e78b0` | `0x3e78c0` | `0x3e78d0` | `0x3e7ae0` | `0x3e7b00` |

For both families, the early slots are short return/delete/clone/copy support
surfaces. The first substantive inspected slot is `+0x30`.

## `src1` Secondary Slot `+0x30 = 0x3e4a80`

The visible `src1` secondary callable body at `0x3e4a80`:

- reads the primary payload pointer from `this+0x8`
- uses `0x3cffc0` to compute a temporary size / rectangle descriptor
- calls `0xf540` with `edx = 6` for the output object at `base+0xf0`
- builds a rectangle from the request and payload fields
- calls `0x3e2e90` on the `0x490` payload
- calls `0x3e5720` with the temporary image descriptor
- destroys the temporary descriptor through `0xf4e0`

The important proven boundary is that this secondary callable routes through
the already bounded `0x490` payload ROI/process body at `0x3e2e90`.

`0x3e5720` is a follow-up executor/setup surface that calls `0xf540` with
`edx = 6`, builds a stack callback object, and dispatches it through generic
executor `0x5670`.

This does not expose a multi-camera reducer.

## Direct Contributor Secondary Slot `+0x30 = 0x3e78d0`

The direct contributor secondary callable body at `0x3e78d0`:

- checks a level-like field at `(*rsi)+0x18`
- throws the string `Invalid level requested in SourceImageCache!` when that
  field is nonzero
- reads the contributor payload-like object through `this+0x8`
- uses `0x3d0b50` to compute a temporary size / rectangle descriptor
- calls `0xf540` with `edx = 8` for the output object at `base+0xf0`
- builds stack callback objects around the contributor payload
- calls `0x261050`
- calls `0x3e82d0` with the temporary image descriptor
- destroys the temporary descriptor through `0xf4e0`

`0x3e82d0` is a follow-up executor/setup surface that calls `0xf540` with
`edx = 8`, builds a stack callback object, and dispatches it through generic
executor `0x5670`.

This does not expose a multi-camera reducer.

## Safe Conclusions

- Proven:
  visible `src1` payloads and direct contributor payloads differ at both the
  primary payload family and the secondary callable family.
- Proven:
  visible `src1` secondary callable address point `0x65f388` reaches
  substantive slot `0x3e4a80`, which routes through `0x3e2e90`.
- Proven:
  direct contributor secondary callable address point `0x65f4d8` reaches
  substantive slot `0x3e78d0`, whose visible body includes the
  `Invalid level requested in SourceImageCache!` guard and a different
  `0x261050` / `0x3e82d0` path.
- Still unproven:
  the semantic contents of visible `src1` / `src2`.
- Still unproven:
  the exact upstream merge/reduction mechanism.

## Canonical Consequence

This evidence narrows `CLM-PREFUSION-001` and `CLM-PREFUSION-002`.

It does not close `CLM-PREFUSION-002`.
