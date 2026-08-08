# Static/Runtime Evidence: Exhaustive Local IRAMP Candidate Policy

**Date:** 2026-07-02  
**Status:** VERIFIED; admitted as local `CLM-PREFUSION-002` / `CLM-MERGE-005` closure  
**Scope:** exhaustive SHA-pinned installed `0x3661b0` body plus prior complete
canonical Unit-1 `28mm`, `35mm`, `70mm`, and `150mm` runtime joins

## Question

Which direct-source candidates enter local IRAMP processing, which are
discarded, and is there a hidden score threshold after `0x36cde0`?

This proof concerns the complete local policy inside installed
`0x3661b0..0x36b91f`. It does not claim that no later global output policy can
suppress the already-composited result.

## Reusable Verifier

`tools/lldb_probes/iramp_candidate_policy/verify_iramp_candidate_policy.py`

The verifier:

- SHA-pins the complete installed body;
- disassembles it with Capstone;
- exhaustively enumerates every immediate sentinel occurrence;
- exhaustively enumerates every direct edge into projection rejection,
  record rejection, WTA-boundary rejection, and later sentinel skips;
- pins critical formula opcodes and the score call target; and
- rejects any floating compare in the continuous score-use window.

## Exhaustive Sentinel Census

The complete body contains exactly six instructions with sentinel immediates:

| Address | Role |
|---|---|
| `0x366c0d` | projected-bbox max initializer `INT_MIN` |
| `0x366c2c` | second projected-bbox max initializer `INT_MIN` |
| `0x366da0` | invalid projected pair store `(INT_MIN,INT_MIN)` |
| `0x36930f` | first per-point pair-table sentinel compare |
| `0x369ed0` | post-WTA boundary-failure sentinel rewrite |
| `0x36a7ac` | downstream same-pair sentinel compare |

There is no other `0x80000000` compare/store in `0x3661b0`.

Only exact `INT_MIN` is sentinel. Prior four-focal runtime packets include
non-sentinel value `-1`, confirming that negative values are not generally
rejected.

## 1. Projected Pair Validity

For each direct source/warp record, a projected pair is sentinelized at
`0x366da0` through exactly five incoming rejection edges:

```text
0x366c90: source x/y is negative or >= source width/height
0x366d27: projected coordinate 1 >= upper bound
0x366d30: projected coordinate 1 < -8
0x366d39: projected coordinate 0 >= upper bound
0x366d42: projected coordinate 0 < -8
```

Accepted projected coordinates add `0.5`, convert by truncating float32 to
int32, and update min/max bounds. Rejected entries receive the full
`(INT_MIN,INT_MIN)` pair.

## 2. Partner-Record Admission

Exactly four branches skip record append at common target `0x368b89`:

```text
0x366b60: source/grid extent <= 0
0x366e18: first valid-pair bbox span <= 0
0x366e25: no finite valid projected pair (minimum remains INT_MAX)
0x366e3c: second valid-pair bbox span <= 0
```

Therefore a direct source gets a local `0x280` partner record only when its
source/grid extent is positive, at least one projected pair is valid, and the
valid projected-pair bbox has strictly positive span in both dimensions.

No other direct branch enters the common record-rejection target.

## 3. Per-Point Search Admission

For each output point and populated partner record:

1. `0x36930f` checks the first int32 of the selected pair-table entry.
2. Exact `INT_MIN` jumps through `0x36931b -> 0x369f0b`, skipping that record.
3. Non-sentinel entries run coarse 16-step SIMD SAD/WTA.
4. The selected 16-by-16 neighborhood must pass all four bounds at
   `0x36969b`, `0x3696b4`, `0x3696c8`, and `0x3696e8`.
5. Any boundary failure converges at `0x369ed0`, rewrites the same pair-table
   entry to full sentinel, and skips the record.
6. A surviving entry runs local `[-2,+2]^2` refinement, bilinear candidate
   sampling, `0x36cde0`, coefficient accumulation, and tuple write.

Those four comparisons are the only incoming branches to the post-WTA
sentinel rewrite.

## 4. Continuous Score Policy

There is no score acceptance threshold.

For every surviving non-sentinel candidate, `0x36cde0` returns `t` and the
caller stores it. The later same-record loop checks only the same pair-table
sentinel at `0x36a7ac`; it does not compare `t`.

The complete score-use formula is branchless:

```text
multiplier = (t + 2*max(0,t-0.5), t, t, t)
denominator += t
```

The only visible `0.5` operation is `max(0,t-0.5)`, which smoothly boosts
lane 0 above `0.5`; it is not an accept/reject gate. `t=0` remains a valid
continuous candidate with zero direct multiplier/denominator addition.

The only conditional branches in the neighboring loop control image extent
and iteration count, not score value.

## Empty Partner Vector

If no direct source produces a partner record, the admitted
`0x3692dc..0x3692e4` empty-vector gate bypasses per-partner search and enters
the baseline reconstruction/accumulator region. Empty is therefore an
explicit local baseline case, not an error.

## Four-Zoom Runtime Join

Prior admitted complete-render evidence supplies runtime liveness:

- `bundle_lldb_iramp_partner_record_population.md` reaches record append on
  all four canonical focals;
- `lldb_iramp_sentinel_gate_targets_four_zoom.md` reaches both exact-sentinel
  skip and non-sentinel process targets on all four;
- `bundle_lldb_iramp_refined_tuple_four_zoom.md` reaches WTA, refinement,
  score, and tuple write on all four; and
- `bundle_lldb_iramp_tuple_downstream_consumer.md` reaches the branchless
  continuous score multiply/add on all four.

Those runs write HDR. Static policy is invariant in the installed binary.
The canonical quartet is one calibration body, and numerical differences
are not attributed to body or firmware.

## Verification Output

```text
iramp_candidate_policy_static=OK libcp=b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9
sentinel_immediate_sites=6
projection_rejection_edges=5
record_rejection_edges=4
post_wta_boundary_rejection_edges=4
score_policy=continuous_branchless_no_threshold
iramp_candidate_policy=OK
```

## Admission Boundary

Admitted:

- exhaustive local projected-pair validity and sentinel production;
- exhaustive partner-record append/rejection gates;
- exhaustive per-point sentinel skip and WTA-boundary sentinel rewrite;
- exact-sentinel-only rejection, with `-1` remaining non-sentinel;
- no local score threshold; and
- continuous score weighting for every surviving non-sentinel candidate.

Still open:

- any later global final-output accept/suppress policy outside `0x3661b0`;
- a public schema name for internal partner/tuple fields, if one exists; and
- MonoFusion mode `1` relevance or unreachability.

The local candidate-policy portion of `CLM-PREFUSION-002` / `CLM-MERGE-005`
is closed. The claims remain `PARTIAL` only for their separately stated
global/public residuals.
