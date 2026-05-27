# LLDB Evidence: IRAMP Entry Signature Four-Zoom Runtime Packets

## Scope

This note records first-entry runtime packets at `libcp+0x365960` for the
canonical four-zoom bridge HDR seed files.

It proves that the tested `28mm`, `35mm`, `70mm`, and `150mm` bridge HDR paths
all enter IRAMP with:

- `src1` in `rsi`.
- `src2` in `rdx`.
- a 5-element contributor source vector in `rcx`.
- a matching 5-element `0x50`-stride warp-record vector in `r8`.
- a scalar scale in `xmm0`.
- a ROI pointer in `r9`.

It does not prove contributor camera identity.

It does not prove the upstream merge/reduction mechanism behind `src1` /
`src2`.

It does not prove final merge acceptance / rejection logic.

## Probe Method

The probe used `arch -x86_64 lldb` against:

`/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/tools/lri_process`

The target process used:

- `DYLD_LIBRARY_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`
- `DYLD_FRAMEWORK_PATH=/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks`
- `--profile 3 --export-fmt 3`

Each run installed one pending breakpoint:

```text
breakpoint set --shlib libcp.dylib --address 0x365960
breakpoint command add -s python 1 -o "import l16_lldb_boundary_cmd as m; m.entry(frame, bp_loc, internal_dict)"
```

The callback dumped the first observed entry packet and intentionally killed
the process. The first observed ROI tile is scheduler-dependent under
multi-threaded render execution, so the ROI values below are evidence that a
valid tile entry was captured, not a claim about global render ordering.

LLDB displayed multi-thread breakpoint stops after the callback wrote JSON.
The JSON packets are the evidence source.

## Tested Files

| Zoom | LRI | Unit | Path |
|---|---|---|---|
| `28mm` | `L16_02130` | Unit A | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | unit unknown | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | Unit A | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | Unit B | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

Correction note: the former `35mm` row used `/Volumes/Base Photos/Light/2018-12-19/L16_02951.lri`; direct `LightHeader` decode later proved that path is a 98mm tele-tier sample. The `35mm` row above is the corrected rerun from `/private/tmp/l16_iramp_entry_35mm_true.json`; see [lri_35mm_seed_correction_true35_runtime.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/lri_35mm_seed_correction_true35_runtime.md).

## Entry Packet Results

| Zoom | Captured PC | ROI | `xmm0` scale | `rcx` source count | `r8` warp count |
|---|---|---|---:|---:|---:|
| `28mm` | `0x108fdf960` | `[0, 7168, 512, 7824]` | `2.507692337` | 5 | 5 |
| `35mm` | `0x108fdf960` | `[512, 512, 1024, 1024]` | `2.507692337` | 5 | 5 |
| `70mm` | `0x108fdf960` | `[4096, 512, 4608, 1024]` | `2.138461590` | 5 | 5 |
| `150mm` | `0x108fdf960` | `[4096, 2560, 4608, 3072]` | `2.138461590` | 5 | 5 |

All four packets captured the same visible wrapper slot families:

| Runtime argument | Vtable file offset | Captured `vtable+0x30` target |
|---|---:|---:|
| `src1` from `rsi` | `0x65f668` | `0x3ecc10` |
| `src2` from `rdx` | `0x65f6e8` | `0x3ecd80` |
| each contributor source-vector item from `rcx` | `0x65f768` | `0x3eced0` |

Every captured source vector had exactly five contributor items, and every
captured contributor item resolved to the `0x65f768 -> 0x3eced0` family.

Every captured warp-record vector had exactly five `0x50`-stride records.

For every captured warp record in these first-entry packets:

- `record+0x48` decoded as `1.0`.
- `record+0x4c` decoded as `1.0`.
- the five records within a packet shared one `record+0x40` map pointer.

## Relationship To Static Bundle Proof

This runtime result agrees with:

[bundle_proof_iramp_live_signature_and_warp_records.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/evidence/bundle_proof_iramp_live_signature_and_warp_records.md)

That static proof shows `processLevel0` passes:

- `rsi = *(PipelineCache+0x238)`
- `rdx = *(PipelineCache+0x248)`
- `rcx = PipelineCache+0x270`
- `r8 = PipelineCache+0x258`
- `xmm0 = *(float *)(PipelineCache+0x1e8)`
- `r9 = ROI`

This LLDB proof supplies the missing direct four-zoom runtime packets for that
same argument shape.

## Safe Conclusions

- Proven:
  the canonical four-zoom bridge HDR quartet all reached `libcp+0x365960`.
- Proven:
  each captured entry packet had `src1`, `src2`, `srcs[5]`, `warps[5]`,
  `scale`, and `roi` in the expected live argument registers.
- Proven:
  the captured `srcs` vector count and captured `warps` vector count matched
  at `5` for all four zooms.
- Proven:
  the visible wrapper slot families were the same across all four first-entry
  packets.
- Still unproven:
  contributor camera identity for each vector item.
- Still unproven:
  the exact upstream merge/reduction mechanism behind `src1` / `src2`.
- Still unproven:
  final merge acceptance / rejection logic beyond arithmetic accumulation.

## Canonical Consequence

`CLM-MERGE-003` can now be treated as four-zoom runtime-proven for the narrow
call-signature claim: on the tested bridge HDR path, IRAMP receives two
anchor-side IGs plus a five-item contributor source vector, paired with five
warp records, scale, and ROI.

This does not close camera routing, `src1` / `src2` pre-fusion behavior, or
anti-ghosting acceptance / rejection logic.
