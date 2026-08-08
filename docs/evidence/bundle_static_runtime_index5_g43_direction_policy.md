# Installed/Runtime Evidence: Index-5 G-43 SGM Direction Policy

**Date:** 2026-07-15  
**Status:** VERIFIED; proposed `CLM-STEREO-001` addendum  
**Bearing:** selected mode-8 `StereoLayer<false>::runPass` worker `0x276860`

## Question

G-43 left the SGM spatial directions, sweep count/order, and scratch-state
initialization unspecified. The implementation placeholder assumed four
cardinal paths. This proof tests that assumption directly.

## Artifacts

- `tools/lldb_probes/g43_g40_census/census_probe.py`
- `tools/lldb_probes/g43_direction_vectors/g43_spatial_probe.py`
- `tools/lldb_probes/g43_direction_vectors/verify_g43_directions.py`
- retained reports under `runs/g43_g40_census/` and
  `runs/g43_direction_vectors/`
- prior recurrence proof:
  `docs/evidence/bundle_static_runtime_index5_sgm_recurrence_roles_four_zoom.md`

The census and spatial probes intentionally terminate after the required
packets. Complete four-focal route liveness comes from the prior admitted
worker/cost-path proof.

## Exact Directions

The worker saves signed sweep direction `ecx`, then loops path index `0..3`.
At `0x2777a6`, it loads one signed horizontal component from the four-element
direction array. Path `0` selects the preceding pixel in the current scanline;
paths `1..3` select the adjacent preceding scanline.

For the positive sweep, the runtime array is:

```text
[-1, -1, 0, 1]
```

Therefore its current-to-predecessor vectors are:

```text
path 0  (-1,  0)  left
path 1  (-1, -1)  upper-left
path 2  ( 0, -1)  up
path 3  ( 1, -1)  upper-right
```

For the negative sweep, the array is sign-reversed:

```text
[1, 1, 0, -1]
```

Its vectors are the four opposites:

```text
path 0  ( 1, 0)  right
path 1  ( 1, 1)  lower-right
path 2  ( 0, 1)  down
path 3  (-1, 1)  lower-left
```

The focused positive and negative packets each contain eight complete groups
of path indices `0,1,2,3`. Their ring-buffer addresses independently prove
that path `0` is one `width+2` row from paths `1..3`, while paths `1..3`
advance horizontally according to the captured signed component array.

This is eight-path SGM, not four-path cardinal SGM.

## Sweep Order

For every fully censused level at both Unit-1 `35mm` and `70mm`, worker calls
are grouped as:

```text
234 calls with ecx = +1
234 calls with ecx = -1
```

No sign interleave occurs between those groups. Static control flow selects
the top/left origin for positive tasks, the bottom/right origin for negative
tasks, advances the outer coordinate by the signed direction, and swaps the
scratch halves after each completed scan segment. Task execution inside one
sign group remains executor-parallel; this proof does not impose a serial
whole-image task order that the binary does not require.

The finest `2080x1560` layer has direct positive and negative spatial packets;
the broad census is intentionally capped before its complete call sequence.

## Initialization and Aggregation

The installed allocator `0x26c8e0` initializes:

- the complete two-half `Line buf` allocation to `u16 2000` using the exact
  16-byte pattern at `0x5dae00`;
- the complete two-half `Min cost buf` allocation to the same `u16 2000`;
- the two-half vec4 `Pixel buf` to zero.

For each current pixel/path recurrence, `%xmm4` starts as `0xffff` for the
current minimum reduction. Each path writes its current path costs to
`Line buf`, writes the reduced minimum to the opposite `Min cost buf` half,
and uses `paddusw` to accumulate into the Cost-volume payload. Four paths are
processed per signed sweep; the two sweeps therefore contribute eight
saturating-u16 path costs.

## Verification

```text
g43_static=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9 line_min_init_u16=2000 pixel_init=zero paths_per_sweep=4
35mm: OK layers=6 coarse_sweeps=+234,-234
70mm: OK layers=6 coarse_sweeps=+234,-234
spatial=OK positive_packets=32 negative_packets=32
directions=(-1,0),(-1,-1),(0,-1),(1,-1) + opposites; aggregation=eight_path_saturating_u16
g43_direction_policy=OK
```

## Scope and Admission Boundary

Admit for canonical profile-3 index-5 stereo:

- exact eight spatial directions;
- four paths per positive/negative sweep;
- forward-group then reverse-group scheduling with executor-parallel tasks;
- exact `Line buf`, `Min cost buf`, and `Pixel buf` initial values; and
- saturating-u16 eight-path aggregation.

Direct runtime census covers Unit-1 `35mm` wide and `70mm` tele, including
finest-layer positive/negative packets. Installed control and arithmetic are
focal/body independent, and prior complete route proof supplies liveness at
Unit-1 `28/35/70/150mm`. No Unit-2 G-43 packet is claimed. This does not close
G-40's dynamic per-level active-hypothesis construction, level-0 range seed,
or arbitrary supported-input compatibility.
