# Static/Runtime Evidence: Index-5 Skip-Mask Consumption

**Date:** 2026-07-17  
**Status:** VERIFIED; admitted `CLM-STEREO-001` addendum  
**Bearing:** selected profile-3 mode-8 levels 4 and 5

## Question

The admitted pattern-2 builder writes one zero and three `0xff` bytes in each
2x2 cell at levels 4 and 5. This proof asks whether the three nonzero positions
receive depth through a later guided fill, or remain in SGM under a different
local-cost policy.

## Artifacts

- thread-gated branch/local-cost probe:
  `tools/lldb_probes/index5_skip_consumption/skip_consumption_probe.py`
- low-frequency completed-record probe:
  `tools/lldb_probes/index5_skip_consumption/final_argmin_probe.py`
- reusable runners:
  `tools/lldb_probes/index5_skip_consumption/run_lri.sh` and
  `run_final_lri.sh`
- installed/runtime verifier:
  `tools/lldb_probes/index5_skip_consumption/verify_skip_consumption.py`
- accepted reports:
  `runs/index5_skip_consumption/{unit1_28_thread_gated_v2,unit1_28_final_v2,unit2_28_thread_gated,unit2_28_final}/`

## Installed Control Flow

The verifier pins installed `libcp.dylib` SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

At `0x27750c..0x277535`, `StereoLayer+0x208` `Skip mask` is indexed at the
current pixel:

```text
if skip_mask[y,x] == 0:
    local_cost = admitted normalized G-42 photometric cost
else:
    local_cost[0:active_count] = 0
```

The nonzero arm passes the aligned local-cost temporary and byte count
`2*active_count` to `0x555eb2`; exact runtime vectors below prove the resulting
active `uint16` span is zero. Both arms converge at `0x277567` and proceed into
the same eight-direction G-43 recurrence. The recurrence reads the local vector
at `0x2779ee`, adds the selected predecessor/P1/P2 smoothness term, subtracts
the prior directional minimum, writes `Line buf`, and saturating-adds each path
into that pixel's Cost-volume record.

After all paths, the independently admitted `0x299c70 -> 0x29a670` worker
visits every record, chooses the first minimum cost, and writes:

```text
depth_hypothesis_index = base + step * first_argmin(costs)
```

Thus pattern 2 sparsifies only the G-42 unary/data term. It does not remove
three pixels from SGM or from the Depth-map output.

## Two-Body Runtime Join

Thread-gated exact-focal `28mm` captures select adjacent full-resolution
index-5 pixels `(0,0)` and `(1,0)` from both physical calibration bodies:

| Body | Mask-0 local prefix | Mask-255 local prefix |
|---|---|---|
| Unit-1 | `251,252,251,248,247,250,243,244` | `0,0,0,0,0,0,0,0` |
| Unit-2 | `243,243,243` | `0,0,0` |

Independent argmin-only runs inspect their completed records:

| Body | Mask | Completed cost prefix | Selected absolute index |
|---|---:|---|---:|
| Unit-1 | `0` | `3048,3056,3038,3000,2986,3012,2922,2928` | `213` |
| Unit-1 | `255` | `20,19,17,21,21,17,9,6` | `212` |
| Unit-2 | `0` | `2924,2922,2916` | `22` |
| Unit-2 | `255` | `5,2,1` | `22` |

The nonzero-mask positions therefore have zero local photometric cost but
nonzero completed SGM costs and ordinary selected hypotheses on both bodies.

## Relationship to Upsampling

The selected index-5 Depth map is first complete at `2080x1560`, including all
three nonzero-mask positions per 2x2 cell. The separately admitted guided
`0x29ed90` stage later upsamples that complete map to `4160x3120`; it is not
the mechanism that fills pattern-2 holes. At level 4 the same installed
`runPass` body and pattern-2 selection produce a complete `1040x780` map before
it becomes the prior map for level 5.

## Scope and Admission

Admitted for selected profile-3 mode-8:

- mask byte `0` computes the admitted G-42 local term;
- mask byte nonzero supplies an all-zero local term;
- both arms execute the same eight-path SGM recurrence and per-pixel Cost
  volume;
- every record reaches the ordinary first-minimum hypothesis selector; and
- pattern-2 nonzero positions are not later filled by guided upsample.

Installed formula scope is body/focal independent for the pinned bundle.
Direct branch and final-record replay covers exact-focal Unit-1 and Unit-2
`28mm` at index 5. Existing receipts prove pattern 2 is selected at levels 4
and 5, complete mask equality at Unit-1 `28/35/70/150mm`, and the same final
argmin worker live over all six levels at those four focals. Other sampling
patterns, modes, profiles, and installed bundles are outside scope.

## Verification

```text
$ python3 tools/lldb_probes/index5_skip_consumption/verify_skip_consumption.py
index5_skip_consumption_static=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
unit1_28mm=OK branch_xy=(0,0)/(1,0) local0=251/0 selected=213/212
unit2_28mm=OK branch_xy=(0,0)/(1,0) local0=243/0 selected=22/22
mask0=compute_G42 mask_nonzero=zero_unary both=SGM_then_cost_volume_first_argmin
```
