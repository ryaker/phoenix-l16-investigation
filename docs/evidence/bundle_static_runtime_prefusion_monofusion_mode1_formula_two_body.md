# Static/Runtime Evidence: MonoFusion Mode-1 Exact Formula

**Date:** 2026-07-25  
**Status:** VERIFIED; scoped `CLM-COMPAT-001` addendum  
**Installed scope:** MonoFusion mode-1 body used by Renderer profiles `1/2`  
**Runtime scope:** profile `1`, Unit-1 canonical `35mm`, plus Unit-2 exact-`28mm` boundary discriminator

## Question

The installed selector proof established that Renderer profiles `1` and `2`
dispatch MonoFusion body `0x19f790`, while canonical profile `3` dispatches
mode `0` at wide focal tiers and constructs no MonoFusion at tele. What exact
scalar formula does mode `1` implement, including image boundaries and invalid
flow overlap?

## Reusable Proof

The harness is under:

```text
tools/lldb_probes/prefusion_monofusion_mode1/
  mode1_tile_probe.py
  verify_mode1_formula.py
  unit1_35mm_profile1.lldb
  unit1_35mm_profile1_gate.lldb
  unit1_35mm_profile1_edge.lldb
  unit1_35mm_profile1_invalid.lldb
  unit2_28mm_profile1_horizontal_edge.lldb
  run_*.sh
```

Rerunnable binary captures and JSON reports are under ignored
`runs/prefusion_monofusion_mode1/`. No `/tmp` artifact is an evidence
dependency.

Verify all retained packets with:

```bash
python3 tools/lldb_probes/prefusion_monofusion_mode1/verify_mode1_formula.py
```

## Installed Custody

The verifier pins installed `libcp.dylib` SHA-256:

```text
b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
```

It also pins the complete mode-1 body `0x19f790..0x1a2520`, final combiner
`0x1a2ff0..0x1a3c00`, five-tap helper `0x1a750..0x1ab10`, the complete
partial-patch arm `0x1a0730..0x1a1d30`, the confidence gate, and final
descriptor-combine windows. Direct-call checks join mode `1` to the same
already-admitted transform, Wiener, inverse, half-Hann overlap, and secondary
confidence helpers used by mode `0`:

```text
0x1a05b0 -> 0x1a750   separable five-tap filter
0x1a1d52 -> 0x1a28f0 forward normalized 5/3 transform
0x1a1d80 -> 0x18da80 coefficient Wiener blend/confidence
0x1a1d88 -> 0x1a2c10 inverse normalized 5/3 transform
0x1a1ff2 -> 0x18ce90 scalar half-Hann overlap add
0x1a2042 -> 0x18d530 confidence half-Hann overlap add
0x1a2091 -> 0x18ce90 scalar half-Hann overlap add
0x1a223d -> 0x1a2ff0 final descriptor expression
```

The prior selector packet observed `48` calls to this same installed body for
each of profiles `1` and `2` on the same canonical Unit-1 `35mm` LRI. The
numeric captures below use profile `1`; installed-formula applicability to
profile `2` follows from that exact common-body dispatch, not from assumed
profile equivalence.

## Exact Mode-1 Formula

Let `O_i` be the flow-aligned original source patch for contributor `i`, and
let the fixed float32 kernel be:

```text
k = [
  0.021900000050663948,
  0.22849999368190765,
  0.4991999864578247,
  0.22849999368190765,
  0.021900000050663948
]
```

Mode `1` first applies this kernel vertically, then horizontally, with each
five-term sum accumulated from tap `-2` through `+2` in float32:

```text
L_i = horizontal_k(vertical_k(O_i))
H_i = O_i - L_i
```

One interior Unit-1 `35mm` capture replays all `256/256` low-pass values and
all `256/256` residual values bit for bit from the retained full source image.

`L_i` then takes the same admitted forward normalized-5/3, coefficient Wiener,
inverse, and half-Hann overlap path as mode `0`. Let `F_i` be that filtered
spatial result and `c_i` the admitted Wiener confidence. The high-pass gate is:

```text
g(c) = 0                         when c < 0.5
       c                         when c == 0.5
       float32((c-0.5)*2.25)     when 0.5 < c <= 0.8999999761581421
       c                         when c > 0.8999999761581421
```

The exact-equality arm at `0.5` is intentionally stated: the installed
comparisons produce the discontinuous value `0.5`, not zero. A live Unit-1
packet has:

```text
c       = 0.8691551089286804
g(c)    = 0.8305990099906921
```

and matches the sloped arm bit for bit.

For target scalar image `T`, source count `N`, and the already-admitted
initializer blend `alpha`, the final mode-1 scalar is:

```text
output = alpha*T
       + ((1-alpha)/N) * overlap_sum_i(F_i)
       + (1/N) * overlap_sum_i(g(c_i)*H_i)
```

The body computes `(1-alpha)/N` and `1/N` explicitly at
`0x1a2144..0x1a2173`. The retained Unit-1 tile has `N=1`,
`alpha=0.6330776214599609`, and `1-alpha=0.36692237854003906`. Replaying the
installed add/multiply order matches all `272,484/272,484` output float32
cells exactly.

The secondary map uses the already-admitted callback unchanged:

```text
X = sum_i(1-c_i)
Y = sum_i(c_i*c_i)

secondary = (alpha + (1-alpha)*X/N)^2
          + ((1-alpha)^2*C/(N^2*R))*Y
```

## Boundary and Invalid Overlap

The partial-patch arm is live, not defensive dead code.

The first Unit-1 `35mm` partial packet has valid `16x10` source and low-pass
descriptors. Its fixed `16x16` blocks use exact row map:

```text
[0,0,0,0,0,0,0,1,2,3,4,5,6,7,8,9]
```

The Unit-2 exact-`28mm` discriminator has valid `9x16` descriptors and exact
column map:

```text
[0,1,2,3,4,5,6,7,8,8,8,8,8,8,8,8]
```

Thus both axes use nearest-valid-coordinate extension. In both captures, all
`256` low-pass work-block values and all `256` float32 `source-lowpass`
residual values replay exactly.

The no-overlap arm is also live on Unit-1 `35mm`. One retained packet proves:

```text
filtered_accumulator_after = filtered_accumulator_before + target_patch
residual_accumulator_after = residual_accumulator_before
X_after                    = X_before + 1
Y_after                    = Y_before
```

All `256` filtered and residual cells match exactly. This is precisely an
invalid contributor treated as `c=0` while falling back to the target patch
for the filtered-source term.

## Verification Output

```text
prefusion_monofusion_mode1=OK
lowpass=vertical_then_horizontal_5tap exact_256_of_256
residual=original_source_minus_lowpass exact_256_of_256
partial_boundary_nearest_edge=row_map_[0, 0, 0, 0, 0, 0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9] exact_256_of_256
partial_boundary_nearest_edge=column_map_[0, 1, 2, 3, 4, 5, 6, 7, 8, 8, 8, 8, 8, 8, 8, 8] exact_256_of_256
invalid_overlap=target_fallback_c0 exact_256_of_256
gate_confidence=0.869155109 gate_scale=0.83059901 exact_float32=OK
final_combine_exact=272484_of_272484
```

## Scope and Admission

Admit this as a `CLM-COMPAT-001` addendum:

- installed formula scope: the common MonoFusion mode-1 body selected by
  Renderer profiles `1/2`;
- complete numeric tile, confidence-gate, vertical-boundary, and invalid-arm
  runtime scope: profile `1`, Unit-1 canonical `35mm`;
- horizontal-boundary and physical-body discriminator: profile `1`, Unit-2
  exact-`28mm`;
- profile `2`: common-body liveness only, with no separate numeric tile replay;
- profile `3`: no change to the admitted four-focal partition; wide uses mode
  `0`, while tele constructs no MonoFusion.

The two inputs differ by body, scene, date, and potentially capture firmware.
The cross-body result is used only as an implementation discriminator; no
firmware or body causation is claimed.

This closes the mode-1 `0x19f790` scalar algorithm and its installed image
boundary behavior. It does not make all of `CLM-COMPAT-001` complete: editor
DebugView object formulas/public meanings, QuickSelect segmentation and commit
semantics, untested edit controls/levels, and other explicitly scoped editor
branches remain reference-only.
