# LLDB Evidence: IRAMP Contributor Identity Four-Zoom Runtime Packets

## Scope

This note records the directly observed contributor-source vector identity at
`libcp+0x365960` on the corrected canonical four-zoom bridge HDR seed set.

It proves only the identity of the five contributor source-vector items passed
directly into IRAMP under these tested bridge HDR runs.

It does not prove:

- the full content of `src1` or `src2`
- where fired cameras absent from the five-item contributor vector are routed
- whether C6 is discarded, folded upstream, used in a cost/depth path, or used
  elsewhere
- final merge acceptance / rejection logic

## Probe Method

The runtime packets come from LLDB breakpoint callbacks at:

`libcp+0x365960`

The callback dumped the first observed IRAMP entry packet and read each
contributor `ptr0` object's `funcdata+0x90` signed 64-bit value.

The camera-id mapping used here is the established L16 mapping:

| Range | Camera names |
|---|---|
| `0..4` | `A1..A5` |
| `5..9` | `B1..B5` |
| `10..15` | `C1..C6` |

## Runtime Artifacts

| Zoom | Runtime artifact |
|---|---|
| `28mm` | `/private/tmp/l16_iramp_entry_camids_28mm.json` |
| `35mm` | `/private/tmp/l16_iramp_entry_35mm_true.json` |
| `70mm` | `/private/tmp/l16_iramp_entry_camids_70mm.json` |
| `150mm` | `/private/tmp/l16_iramp_entry_camids_150mm.json` |

## Tested Files

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Direct LRI Fired Sets

Direct `LightHeader.field_4` and `LightHeader.field_12[i].field_2` decode gives:

| Zoom | `LightHeader.field_4` | Fired camera IDs | Fired camera names |
|---|---:|---|---|
| `28mm` | `28` | `[0,1,2,3,4,5,6,7,8,9]` | `A1,A2,A3,A4,A5,B1,B2,B3,B4,B5` |
| `35mm` | `35` | `[0,1,2,3,4,5,6,7,8,9]` | `A1,A2,A3,A4,A5,B1,B2,B3,B4,B5` |
| `70mm` | `70` | `[5,6,7,8,9,10,11,12,13,14,15]` | `B1,B2,B3,B4,B5,C1,C2,C3,C4,C5,C6` |
| `150mm` | `149` | `[5,6,7,8,9,10,11,12,13,14,15]` | `B1,B2,B3,B4,B5,C1,C2,C3,C4,C5,C6` |

This table proves C6 fires in the tested tele LRIs.

## IRAMP Contributor Vector Identity

Runtime `funcdata+0x90` values on the five contributor source-vector items:

| Zoom | Source count | Contributor camera IDs | Contributor names | ROI | `xmm0` scale |
|---|---:|---|---|---|---:|
| `28mm` | 5 | `[5,6,7,8,9]` | `B1,B2,B3,B4,B5` | `[5120,3584,5632,4096]` | `2.507692337036133` |
| `35mm` | 5 | `[5,6,7,8,9]` | `B1,B2,B3,B4,B5` | `[512,512,1024,1024]` | `2.507692337036133` |
| `70mm` | 5 | `[10,11,12,13,14]` | `C1,C2,C3,C4,C5` | `[8192,0,8896,512]` | `2.1384615898132324` |
| `150mm` | 5 | `[10,11,12,13,14]` | `C1,C2,C3,C4,C5` | `[5632,1536,6144,2048]` | `2.1384615898132324` |

For all four packets, each contributor `ptr0` object resolved to the
contributor wrapper family whose `vtable+0x30` target is `libcp+0x3eced0`.

## `src1` / `src2` Cam-ID Read Result

In these same entry packets, `src1` and `src2` had:

- shared `funcdata` pointer within each packet
- `funcdata_vtable_0x00 = 0x20000000200`
- `funcdata+0x90` reading as `0`
- zero qwords across the sampled `funcdata+0x80..+0xb8` window

Therefore this probe does not identify the cameras contained in `src1` or
`src2`. It proves only that the direct `funcdata+0x90` camera-id field is
present on contributor items, not on the sampled `src1` / `src2` funcdata
object.

## Safe Conclusions

- Proven:
  the corrected canonical `28mm` and `35mm` bridge HDR seeds pass `B1..B5` as
  the five direct IRAMP contributor source-vector items.
- Proven:
  the corrected canonical `70mm` and `150mm` bridge HDR seeds pass `C1..C5` as
  the five direct IRAMP contributor source-vector items.
- Proven:
  C6 fires in the tested `70mm` and `150mm` LRIs but is absent from the directly
  observed five-item IRAMP contributor vector.
- Still unproven:
  C6's exact downstream or upstream routing.
- Still unproven:
  the exact camera composition and generation math behind `src1` and `src2`.

## Canonical Consequence

This evidence can support a narrow claim about direct IRAMP contributor-vector
identity.

It cannot close the tele C6 routing blocker by itself.
