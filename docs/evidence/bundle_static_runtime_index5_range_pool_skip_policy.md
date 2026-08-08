# Static/Runtime Evidence: Index-5 Range Pool and Skip Policy

**Date:** 2026-07-17  
**Status:** VERIFIED; admitted `CLM-STEREO-001` / G-40 addendum  
**Bearing:** selected profile-3 mode-8 levels 1 through 5

## Question

The prior G-40 admission began with already-produced `prior_low` and
`prior_high` tables. It did not specify the `0x298ff0` neighborhood that
produces those tables from the prior Depth-map hypothesis index and Skip mask.
An implementation filled the gap with a symmetric radius-2 pool over every
pixel. That substitution changes per-level Range-map extents.

## Artifacts

- focused LLDB replay:
  `tools/lldb_probes/index5_range_pool_policy/range_pool_probe.py`
- reusable runner:
  `tools/lldb_probes/index5_range_pool_policy/run_lri.sh`
- installed/static and retained-runtime verifier:
  `tools/lldb_probes/index5_range_pool_policy/verify_range_pool_policy.py`
- focused report:
  `runs/index5_range_pool_policy/unit1_28mm/report.json`
- joined prior kernel/liveness reports:
  `runs/codex_26d750_source_range_builder/source_range_{28mm,35mm,70mm,150mm,unit2_28mm}.json`

## Installed Pipeline

The verifier pins installed `libcp.dylib` SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

For every transition from level `L-1` to level `L`:

1. `0x267120` produces the prior-depth hypothesis-index descriptor consumed
   by this stage.
2. `0x2705c0` exposes the prior `Skip mask` as a matching byte descriptor.
3. `0x26d887` loads `kernel_size = target StereoLayer+0x14`.
4. `0x26d8a7 -> 0x298ff0` computes low/high index tables.
5. The already-admitted suffix maps target pixels into those tables, applies
   `target+0x10` padding, clamps to the lookup, and emits Range-map
   `(lower,count)` records.

All accepted runtime packets have:

```text
kernel_size (target+0x14) = 4
range padding (target+0x10) = 1
```

## Exact Pool

`0x298ff0` derives its negative-side extent as:

```text
left = ceil(kernel_size/2) - 1
```

For the selected value `4`, the horizontal and vertical offsets are therefore:

```text
-1, 0, +1, +2
```

The two installed callback bodies `0x2993f0` and `0x2997b0` implement a
separable rectangular min/max. Equivalently, for output position `(x,y)`:

```text
V = []
for dy in {-1,0,1,2}:
  sy = clamp(y+dy, 0, height-1)
  for dx in {-1,0,1,2}:
    sx = clamp(x+dx, 0, width-1)
    if prior_skip_mask[sy,sx] != 0:
      V.append(prior_hypothesis_index[sy,sx])

prior_low[x,y]  = min(V) if V else 65535
prior_high[x,y] = max(V) if V else 0
```

Thus zero Skip-mask bytes are excluded and nonzero bytes participate. Boundary
coordinates are clamped independently, which duplicates edge samples but does
not change min/max. The footprint is asymmetric 4x4, not symmetric radius 2.

The all-invalid result is proved by the installed initializers
`low=0xffff`, `high=0` and conditional update branches. No all-invalid window
occurred in the focused selected Unit-1 28mm packet; that sentinel consequence
is installed-static, not a claimed runtime incidence.

## Joined G-40 Suffix

The subsequent admitted target-to-source mapping samples the low/high tables:

```text
sx = floor(x * (source_width  - 1) / (target_width  - 1))
sy = floor(y * (source_height - 1) / (target_height - 1))

lower = max(prior_low[sy,sx] - 1, 0)
upper = min(prior_high[sy,sx] + 1, lookup_count - 1)
count = upper - lower
```

The `+1/-1` here is Range-map hypothesis padding and is separate from the 4x4
spatial pool.

## Runtime Replay

One focused Unit-1 `28mm` process captured all five transitions:

```text
65x49 -> 130x98
130x98 -> 260x195
260x195 -> 520x390
520x390 -> 1040x780
1040x780 -> 2080x1560
```

At each transition, the probe replays corners and center from live source/mask
bytes and matches both output words exactly. The final transition also finds
and replays a mixed-mask 4x4 neighborhood. Joined earlier complete reports
confirm `kernel_size=4` and post-pool liveness at Unit-1
`28/35/70/150mm` plus exact-focal Unit-2 `28mm`.

## Scope and Admission

Admitted as a selected profile-3 mode-8 G-40 formula addendum:

- exact installed pool, edge, Skip-mask, and empty-set policies are
  body/focal independent for the pinned bundle;
- exact five-transition replay is Unit-1 `28mm`;
- kernel/liveness coverage is Unit-1 four-focal plus Unit-2 exact-28mm;
- no body/firmware equality or causation is claimed;
- profiles 1/2, other modes, other installed bundles, and arbitrary malformed
  inputs remain outside scope.

## Verification

```text
$ python3 tools/lldb_probes/index5_range_pool_policy/verify_range_pool_policy.py
index5_range_pool_static=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
kernel_size=4 offsets=-1,0,1,2 x -1,0,1,2 boundary=clamp
mask_nonzero=include mask_zero=exclude all_invalid=(65535,0)
five_transition_replay=OK
unit1_28mm_kernel=4
unit1_35mm_kernel=4
unit1_70mm_kernel=4
unit1_150mm_kernel=4
unit2_28mm_kernel=4
```
