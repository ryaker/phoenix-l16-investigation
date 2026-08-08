# PatchNLM Patch-Overlap Topology and Full-Frame Boundary Policy

## Result

The selected profile-3 `ImageDenoisePatchNLM<4>` producer topology and
boundary policy are installed-formula closed. It is a patch overlap-add
algorithm, not an independent center-pixel NLM average.

For an input `source[width,height]`, Lumen first initializes full-frame
`vec4` accumulators:

```text
numerator[p]   = 0.01f * source[p]
denominator[p] = (0.01f, 0.01f, 0.01f, 0.01f)
```

The reference-center region is the half-open rectangle
`[2,width-1) x [2,height-1)`. The generic executor tiles that region in
`128x128` rectangles and invokes the worker in four modes `0,1,2,3`; mode
bits select the left/right and top/bottom half of each incoming rectangle.

Within a selected partition, reference centers advance by `step_size=2`.
Each base row obtains a deterministic `(phase_x,phase_y)` pair from a
12,553-pair vector. The vector starts from 48-bit state `0x330e` and applies:

```text
state = (0x5deece66d * state + 0xb) mod 2^48
phase = uint32(state >> 16) % step_size
```

The first eight pairs for the selected step are
`(0,1),(1,0),(1,1),(1,1),(1,0),(0,1),(1,0),(0,0)`. Each partition starts at:

```text
i = uint32((width * partition_y0 + partition_x0) * 0xdeadbeef) % 12553
```

and consumes one pair per base row, wrapping at 12,553. The phase-shifted
reference center is capped at `partition_end-1` on each axis.

For reference center `(rx,ry)`, the actual reference patch uses offsets
`{-2,-1,0,+1}` on both axes, exactly 16 `vec4` samples. The selected public
configuration contains `patch_size=5`, but this installed `<4>` specialization
does not load 25 samples.

For `window_size=5`, candidate centers use a full-width half-open window. At
the upper edge the start shifts back after clipping the end:

```text
cx1 = min(width  - 1, max(2, rx - floor(window_size/2)) + window_size)
cy1 = min(height - 1, max(2, ry - floor(window_size/2)) + window_size)
cx0 = cx1 - window_size
cy0 = cy1 - window_size
```

Candidate rows advance by one. Within candidate row `cy`, selected x
coordinates are `cx0 + (cy & 1), +2, ... < cx1`, giving a deterministic
checkerboard subset of the five-wide window. Every selected candidate patch
uses the same 4x4 offsets. The already-admitted L1/max/tent law computes one
`vec4` weight `w` per selected candidate, using `range_scale[reference_center]`.
The body accumulates the weighted candidate patches locally, then overlap-adds
all 16 local vectors and the shared local weight sum into the 16 output
locations belonging to the reference patch:

```text
for each selected candidate center (cx,cy):
    for py,px in {-2,-1,0,+1}^2:
        local_numerator[py,px] += w * source[cy+py,cx+px]
    local_denominator += w

for py,px in {-2,-1,0,+1}^2:
    numerator[ry+py,rx+px] += local_numerator[py,px]
    denominator[ry+py,rx+px] += local_denominator
```

After all four passes, a full-frame worker computes RGB as
`rcpps(denominator)*numerator` and restores alpha from the original source
with `blendps 8`.

This construction is the boundary policy. The worker never forms an
out-of-range patch and has no edge-clamp branch. Pixels not reached by a
particular patch retain the positive `0.01` source/weight seed, so every
full-frame denominator remains nonzero before normalization.

## Installed Proof

Installed `libcp.dylib` SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

| Range | SHA-256 | Role |
|---|---|---|
| `0x3066d0..0x306d40` | `bfebe7619117a2db022e28894a2dbc2456fe8f2d255306939a508675d91b3da8` | complete parent |
| `0x1a3c0..0x1a73b` | `9f65748b5293f8c1c02c5e77c2e4d6eb7d6290e6467050cf7800da5e2b0f4ff3` | `0.01*source` numerator initializer |
| `0x18f960..0x18fcea` | `d950649d44164d3a6c36e1891bc1203e87e4c72887e76b1d9c67413e9e8fed74` | denominator constant fill |
| `0x306717..0x306817` | `d3865d159e3bd6cc0af4bedd7b4a884314dd625292e0182f26caf3cd73e01893` | phase-vector generator |
| `0x30689c..0x306a16` | `153e933278459dcaa37efb8755646294a9b8a899690a11f0d2ce43fa7eb1900a` | seed, bounds, tile, first dispatch |
| `0x3070e0..0x307d90` | `862f185f5d4cd3d365ebf5ff65091520b2697cdd9d83a1e8bf4c42a4b2a5ddbb` | partition, patches, candidates, overlap-add |
| `0x307d90..0x307ea7` | `1415cf342baae4666c4a15d84d99acb004eff16de46a3c71dd042643de8d5cab` | full-frame normalization / alpha preserve |

The verifier pins the four-lane constant at `0x5a8a60` to binary32 `0.01`,
the region and tile immediates, all four task modes and calls, the LCG
constants and replayed phase prefix, the 4x4 load loop, reference-center
range-scale read, upper-edge window shift, candidate checkerboard, step-2
reference loops, exactly 16 numerator stores, exactly 16
denominator stores, and the normalizer's three unrefined packed reciprocal
and alpha-preserve sites.

## Scope and Runtime Join

The topology and boundary formula are SHA-pinned installed-bundle static
proof and therefore body/focal independent for this binary. Existing admitted
runtime route evidence proves this exact `0x3066d0 -> 0x3070a0/0x3070e0 ->
0x307d90` family live on Unit-1 `28mm`, `35mm`, `70mm`, and `150mm`, plus
exact-`35mm` Unit-2. The numerical weight replay remains Unit-1 `28mm`.

A fresh callback capture was attempted, but the new harness and the previously
accepted `nlm_weight_formula` control both stalled in the current debugger
environment. No result from those attempts is used here. Installed-bundle
static proof is independently sufficient for this body-internal topology.

This admission closes selected PatchNLM patch scheduling and full-frame edge
construction. It does not claim a bit-exact replay of Lumen's concurrent
task-addition order, alternate PatchNLM specializations, unselected denoise
routes, or full post-denoise image parity.

## Reproduction

```bash
python3 tools/lldb_probes/nlm_topology_boundary/verify_nlm_topology_boundary.py
```

Expected terminal line begins:

```text
static_nlm_topology_boundary=OK
```
