# Static/Runtime Evidence: Index-5 Disparity Lane Convention

**Date:** 2026-07-10  
**Status:** VERIFIED; admitted `CLM-STEREO-001` refinement  
**Bearing:** target-index-5 SGM recurrence and reciprocal ray-depth hypotheses

## Question

The existing four-focal proof reconstructs the unsigned-16 SIMD recurrence at
`0x2779b0..0x277a10`, but conservatively calls its two `+P1` inputs `src0`
and `src6`. This proof asks which one is `d-1`, which one is `d+1`, how SIMD
lane order maps to cost-record hypothesis order, and whether increasing index
means nearer or farther ray depth.

## Artifacts

- reusable verifier:
  `tools/lldb_probes/index5_stereo_residual_policy/verify_disparity_lane_convention.py`
- reused accepted four-focal recurrence packets:
  `runs/codex_276860_payload_vector_formula/vector_formula_*.json`
- reused accepted reciprocal-lookup packets:
  `runs/codex_index5_lookup_vector_public_origin/lookup_vector_*.json`
- adjacent proofs:
  `lldb_276860_payload_vector_formula_four_zoom.md`,
  `bundle_static_runtime_index5_sgm_recurrence_roles_four_zoom.md`, and
  `lldb_index5_lookup_vector_public_origin_four_zoom.md`

No new render was required. The verifier reruns all existing packet validators,
pins the installed recurrence body and lane-manipulation opcodes, and then
checks the cross-packet pointer and record relationships below.

## Exact Lane Splice

For every accepted sample, the two `Line buf` read addresses satisfy:

```text
higher_address = lower_address + 4 bytes
```

They are therefore separated by two `uint16` words. Their six overlapping
words are equal in all `67/67` samples. If the contiguous predecessor path
costs are `P[k-1]..P[k+8]`, the two loads are:

```text
lower  = [P[k-1], P[k],   P[k+1], ..., P[k+6]]
higher = [P[k+1], P[k+2], P[k+3], ..., P[k+8]]
```

The installed `psrld`, `pslldq`, and `pblendw 0xfe` sequence produces:

```text
current = [lower[1], higher[0], ..., higher[6]]
        = [P[k], P[k+1], ..., P[k+7]]
```

The recurrence is thus exactly:

```text
selected(d) = min(
    predecessor(d),
    sat_add(predecessor(d - 1), P1),
    sat_add(predecessor(d + 1), P1),
    min_predecessor + adaptive_P2
)

path_cost(p,d) =
    sat_sub(
        sat_add(local_cost(p,d), selected(d)),
        min_predecessor)
```

The existing proof covers the final `Line buf`, `Min cost buf`, and
Cost-volume stores; this note resolves the previously anonymous lane direction.

## Record and Physical Direction

The selected runtime records all have hypothesis-index step `1`. Their cost
list is consumed in increasing memory/lane order, and the later proven
minimum-cost worker returns:

```text
absolute_hypothesis_index = base + step * argmin(costs)
```

The index-5 lookup is already independently reproduced as:

```text
lookup[i] = 1 / (1/far + i * reciprocal_step)
far = 640000 mm
near = 200 mm
```

It is strictly decreasing with increasing index. Therefore:

| Recurrence term | Index direction | Ray-depth direction | Inverse-depth/disparity direction |
|---|---|---|---|
| `d - 1` / lower load | lower | farther | lower |
| `d` / assembled current | unchanged | current | current |
| `d + 1` / higher load | higher | nearer | higher |

This is a hypothesis-axis convention. It is independent of which of the four
spatial SGM scan directions supplies the predecessor path.

## Four-Focal Result

```text
28mm=OK samples=16 headers=(214, 10, 1, 16)
35mm=OK samples=20 headers=(27, 3, 1, 8)
70mm=OK samples=15 headers=(58, 5, 1, 8)
150mm=OK samples=16 headers=(55, 4, 1, 8)
static_libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
disparity_lane_convention=OK samples=67 lane_order=increasing_hypothesis_index lower_neighbor=farther higher_neighbor=nearer lookup=far_to_near
```

The listed headers are sampled live records `(base,count,step,rounded_count)`,
not global constants.

## Admission and Scope

Admitted for canonical Unit-1 profile-3 bridge HDR at `28mm`, `35mm`, `70mm`,
and `150mm`:

- SIMD lane order is increasing absolute hypothesis index;
- the first penalized neighbor is `d-1`, farther/lower inverse depth;
- the second penalized neighbor is `d+1`, nearer/higher inverse depth; and
- the unpenalized splice is exactly the current `d` vector.

The installed formula is body-independent for the pinned bundle; runtime
packet coverage is Unit-1 four-focal and sampled rather than a full-map dump.
This closes the exact disparity-direction lane convention. It does not assign
public names to Guidance components or generalize compatibility
profiles.

`CLM-STEREO-001` remains `PARTIAL` / `BLOCKER` only for Guidance component
semantics needed to reproduce the selected stereo-image input.
