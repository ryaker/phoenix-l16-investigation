# Bundle + LLDB Global `0x372760` Row-Cache Segment Census Evidence

**Date:** 2026-05-13
**Status:** Partial evidence admitted for canonical review.
**Scope:** Installed `libcp.dylib`, corrected canonical bridge HDR quartet,
complete-render census of row-plan return `0x3722b0` and non-middle
`0x372760` row-cache store sites.

This document follows:

- `bundle_lldb_owner_f0_resample_36f800.md`
- `bundle_lldb_owner_f0_resample_helpers_372500_372760.md`
- `bundle_lldb_owner_f0_global_post_route_families.md`

Earlier helper evidence proved the first gated owner `+0xf0` dispatch and found
only the middle `0x372760` segment in that fresh first dispatch. This probe
removes the first-dispatch boundary and counts complete bridge HDR renders.

It proves:

- all four canonical zoom runs completed with exit status `0`
- row-plan return `0x3722b0` is live across all four canonical full renders
- leading row-cache store site `0x372898` and trailing row-cache store site
  `0x3729e0` are live at `28mm` and `70mm`
- leading/trailing row-cache store sites had zero hits at `35mm` and `150mm`
  under these exact canonical bridge HDR runs
- the first captured leading/trailing store samples at `28mm` and `70mm` match
  the same reconstructed 4-tap horizontal `vec4` formula used by the earlier
  helper proof

It does not prove:

- that `35mm` or `150mm` can never hit leading/trailing segments in other LRIs,
  export modes, or non-canonical conditions
- public semantic names for offset, scale, clamp, or pixel-format fields
- downstream row-image/final policy after these row-cache fills
- parent-chain ancestry above the classified read-context caller families,
  which is covered separately by
  `bundle_lldb_owner_f0_global_route_ancestry.md`
- final contributor acceptance / rejection or suppression policy

## Inputs

| Zoom | LRI | Path |
|---|---|---|
| `28mm` | `L16_02130` | `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` |
| `35mm` | `L16_03041` | `/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri` |
| `70mm` | `L16_03434` | `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` |
| `150mm` | `L16_02285` | `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` |

## Tooling Boundary

Reusable probe harness:

- `tools/lldb_probes/owner_f0_resample_36f800/owner_f0_resample_36f800_probe.py`

Per-zoom LLDB scripts:

- `tools/lldb_probes/owner_f0_resample_36f800/global_rowcache_segments_28mm.lldb`
- `tools/lldb_probes/owner_f0_resample_36f800/global_rowcache_segments_35mm.lldb`
- `tools/lldb_probes/owner_f0_resample_36f800/global_rowcache_segments_70mm.lldb`
- `tools/lldb_probes/owner_f0_resample_36f800/global_rowcache_segments_150mm.lldb`

Rerunnable raw JSON packets live under ignored
`runs/owner_f0_resample_36f800/`:

- `global_rowcache_segments_28mm.json`
- `global_rowcache_segments_35mm.json`
- `global_rowcache_segments_70mm.json`
- `global_rowcache_segments_150mm.json`

No probe harness or live evidence dependency for this proof lives in
`/private/tmp`.

## Runtime Method

The LLDB scripts set three pending `libcp.dylib` breakpoints before launch:

- `0x3722b0`: row-plan return after `0x372500`
- `0x372898`: after-store site for the leading clamped row-cache segment
- `0x3729e0`: after-store site for the trailing clamped row-cache segment

The row-plan callback counts every plan and records predicted horizontal segment
counts from the plan fields. The leading/trailing callbacks count live dynamic
store hits and preserve the first packet for each live non-middle segment. Store
packets read the row-plan from the caller worker frame, not the helper frame.

The predicted segment totals are per row-plan horizontal counts. They are not
the same unit as live store breakpoint counts because `0x372760` can be called
multiple times for rows under a plan.

## Runtime Summary

| Zoom | Exit | Row-plan hits | Leading store hits | Trailing store hits | Row-plans with leading/trailing predicted | First leading diff | First trailing diff |
|---|---:|---:|---:|---:|---:|---:|---:|
| `28mm` | `0` | `1571` | `6938` | `6938` | `15 / 15` | `0.0` | `1.2223608791828156e-08` |
| `35mm` | `0` | `1128` | `0` | `0` | `0 / 0` | n/a | n/a |
| `70mm` | `0` | `1131` | `6908` | `6908` | `13 / 13` | `0.0` | `5.21540641784668e-08` |
| `150mm` | `0` | `300` | `0` | `0` | `0 / 0` | n/a | n/a |

The nonzero first-trailing diffs are within the same single-precision tolerance
used by the earlier `0x372760` helper formula proof.

## Captured Formula Boundary

For live leading/trailing samples, the reconstructed formula is:

```text
fixed_x = signed 16.16 x coordinate
floor_x = fixed_x >> 16
frac_index = (fixed_x >> 10) & 0x3f
indices = clamp([floor_x - 1, floor_x, floor_x + 1, floor_x + 2], source_min_x, source_max_x)
weights = weight_table[frac_index][0..3]
dest_vec4 = sum(source_row[indices[i]] * weights[i] for i in 0..3)
```

The first leading samples prove left-edge clamping:

| Zoom | Source min/max | Source indices | Max diff |
|---|---|---|---:|
| `28mm` | `0 / 435` | `[0,0,1,2]` | `0.0` |
| `70mm` | `0 / 517` | `[0,0,1,2]` | `0.0` |

The first trailing samples prove right-edge clamping:

| Zoom | Source min/max | Source indices | Max diff |
|---|---|---|---:|
| `28mm` | `0 / 512` | `[510,511,512,512]` | `1.2223608791828156e-08` |
| `70mm` | `0 / 832` | `[830,831,832,832]` | `5.21540641784668e-08` |

## Interpretation Boundary

This proof closes the old blocker wording "global leading/trailing row-cache
segment reachability" for the corrected canonical bridge HDR quartet:

- `28mm`: leading and trailing are reachable and live
- `35mm`: leading and trailing were not reached in this run
- `70mm`: leading and trailing are reachable and live
- `150mm`: leading and trailing were not reached in this run

It does not name the public meaning of the row-plan fields, and it does not
explain how later row-image/final policy accepts, rejects, suppresses, or
weights the produced contributor influence.
