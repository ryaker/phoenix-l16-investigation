# Evidence: G-40 Index-5 Per-Level Hypothesis Construction

## Result

G-40 is formula-closed for the selected profile-3, mode-8 stereo route. The
six runtime `StereoLayer<false>` levels are `65x49`, `130x98`, `260x195`,
`520x390`, `1040x780`, and `2080x1560`. The level-0 seed spans the complete
reciprocal ray-depth lookup. Higher levels derive a per-pixel candidate range
from the prior level's generated `Depth map` and `Skip mask`; the global active
extent is the maximum candidate upper endpoint, rounded up to a multiple of
eight.

The active extent is therefore not a fixed per-level table. It is a
scene-derived value. Earlier reads from `StereoLayer+0x23c` at hot SGM worker
entry were timing-sensitive because they could occur while `0x26d750` was
still updating that field. Only the producer-store captures in this bundle
are admitted.

## Installed Static Proof

The installed `libcp.dylib` is pinned by SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

### Level 0

At `0x26c220`, the selected constructor:

```text
lookup_count = (this+0xe8 - this+0xe0) / sizeof(float)
mode         = this+0x0c                         # 8 on selected route
extent       = ceil(lookup_count / mode) * mode

this+0x23c = extent
this+0x238 = 0
```

It then calls `0x29a520 -> 0x29a1d0` with width, height, `extent`, and
`mode`. Every initial per-pixel variable record is:

```text
u16 +0 = 0                     # base hypothesis index
u16 +2 = extent                # allocated/valid count here
u16 +4 = 1                     # hypothesis-index step
u16 +6 = extent                # padded count; equal at level 0
```

Thus level 0 is not seeded from a previous Depth map. It is a full-span Range
map over the generated reciprocal ray-depth lookup, with lower index zero.

### Levels 1 Through 5

The already admitted `0x26d750` range-builder formula is joined here to its
global fields and producer barrier. For each target pixel:

```text
sx = floor(x * (source_width  - 1) / (target_width  - 1))
sy = floor(y * (source_height - 1) / (target_height - 1))

lower = max(prior_low[sy,sx]  - padding, 0)
upper = min(prior_high[sy,sx] + padding, lookup_count - 1)
count = upper - lower
```

`0x26d750` writes `(u16 lower, u16 count)` to the generated Range map while
updating:

```text
this+0x238 = min over all pixels(lower)
this+0x23c = max over all pixels(upper)
```

After Range-map conversion by `0x29a140`, both caller families at
`0x26be9e..0x26bebf` and `0x26c13e..0x26c15d` commit:

```text
active_extent = ceil((this+0x23c) / mode) * mode
this+0x23c = active_extent
```

`0x299fd0` converts each Range-map pair to a cost-volume variable record with
base `lower`, valid `count`, step `1`, and a per-record padded count
`ceil(count/8)*8`. The global `this+0x23c` extent and the per-pixel valid
counts are related but are not interchangeable.

## Runtime Proof

The probe stops only before the three stable commit stores:

```text
0x26c277  level-0 full-lookup extent
0x26bebf  prior-layer Range-map extent
0x26c15d  alternate Depth-provider Range-map extent
```

Each accepted Unit-1 canonical render produced exactly six packets, exited
zero, used mode `8`, and satisfied the installed ceil-to-mode formula.

| Focal | Lookup count | Level 0..5 committed active extents |
|---|---:|---|
| 28mm | 752 | `752, 632, 272, 256, 256, 256` |
| 35mm | 752 | `752, 752, 752, 752, 752, 752` |
| 70mm | 1472 | `1472, 1408, 1392, 1328, 1200, 1152` |
| 150mm | 1472 | `1472, 48, 48, 48, 48, 48` |

The corresponding completed `(min_lower, raw_max_upper)` pairs are:

| Focal | Level 0..5 pairs |
|---|---|
| 28mm | `(0,752), (6,629), (8,268), (8,253), (7,250), (6,250)` |
| 35mm | `(0,752), (0,751), (0,750), (0,748), (0,748), (0,746)` |
| 70mm | `(0,1472), (0,1407), (0,1392), (0,1324), (0,1193), (0,1149)` |
| 150mm | `(0,1472), (4,44), (15,42), (15,42), (14,42), (13,42)` |

These numeric sequences characterize the four canonical LRIs only. A clean
room implementation must compute them from each input's generated maps; it
must not hardcode them.

## Scope

- Runtime extent packets: canonical Unit-1 `28/35/70/150mm`.
- Formula: SHA-pinned installed code, body- and focal-independent for the
  selected mode-8 route.
- Cross-body discriminator: the prior admitted `0x26d750` evidence validates
  the same per-pixel range formula on an exact-focal Unit-2 `28mm` LRI. This
  bundle does not claim Unit-2 per-level commit packets.
- Not covered: other stereo modes, profiles, sampling-pattern arms, arbitrary
  firmware/bundle versions, or universal numeric extent sequences.

## Artifacts

- Probe: `tools/lldb_probes/g40_hypothesis_policy/hypothesis_policy_probe.py`
- Four-focal runner: `tools/lldb_probes/g40_hypothesis_policy/run_four_zoom.sh`
- Verifier: `tools/lldb_probes/g40_hypothesis_policy/verify_g40_hypothesis_policy.py`
- Runtime reports: `runs/g40_hypothesis_policy/hypothesis_{28mm,35mm,70mm,150mm}.json`
- Joined prior evidence: `docs/evidence/lldb_26d750_source_range_builder_four_zoom.md`

The runner writes image output only to `/private/tmp` and removes it after
each run. No scratch image is an evidence dependency.

## Verification

```bash
python3 tools/lldb_probes/g40_hypothesis_policy/verify_g40_hypothesis_policy.py
```

Expected terminal line:

```text
g40_hypothesis_policy=OK
```

## Rejected Upgrades

- The four observed extent sequences are not universal constants.
- `StereoLayer+0x23c` is not safely sampled at arbitrary worker entry.
- Unit-1 four-focal coverage is not two-body four-focal coverage.
- This proof does not generalize to unselected stereo modes or profiles.
