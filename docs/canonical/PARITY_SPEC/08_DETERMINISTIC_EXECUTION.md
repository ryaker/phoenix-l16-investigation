# Deterministic Execution

## Scope

This section specifies the execution and ownership rules a Phoenix clean-room
implementation must use for reproducible profile-3 depth. It covers the
selected mode-8 G-42/G-43 path, its upstream prefusion/calibration barrier,
and repeat validation. It does not require Phoenix to reproduce the installed
Lumen data race or select one arbitrary stock-Lumen race outcome as a golden
map.

## Claim Inputs

- `CLM-STEREO-001`
- `CLM-WARP-003`
- `CLM-PREFUSION-002`
- `CLM-CALIBPROC-001`

The controlling admissions are the `CLM-STEREO-001` G-43 direction-policy,
cost-input-normalization, and nondeterminism-mechanism addenda in
`../CLAIM_LEDGER.md`.

## Zoom Coverage

| Zoom | Status | Notes |
|---|---|---|
| 28mm | Required | Same-address multi-writer proof; deterministic suppression on Unit-1 |
| 35mm | Required | Same-address multi-writer proof; installed direction-policy liveness |
| 70mm | Required | Same-address multi-writer proof; same-object overlap and deterministic suppression on Unit-2 |
| 150mm | Required | Same-address multi-writer proof; deterministic suppression on Unit-1 |

## Proven Lumen Behavior

The selected installed path performs eight directional SGM passes. The
current-to-predecessor vectors are:

```text
positive group: (-1,0), (-1,-1), (0,-1), (1,-1)
negative group: ( 1,0), ( 1, 1), (0, 1), (-1,1)
```

All positive-group tasks are submitted before all negative-group tasks. Tasks
inside a group execute concurrently. Each directional worker computes an
independent SGM path recurrence, but the installed implementation accumulates
the result into one shared Cost-volume payload with this non-atomic update:

```text
old = load_u16x8(shared_payload)
new = saturating_add_u16(old, directional_increment)
store_u16x8(shared_payload, new)
```

Different workers write the same payload address. Lost updates make the stock
result scheduler-dependent. The shared update is integer SIMD; the selected
Skip-mask RNG is deterministic; `Line buf` and `Min cost buf` are fully
initialized to `u16 2000`; and `Pixel buf` is fully initialized to zero.

Forcing the installed generic executor to invoke callbacks in ascending serial
order stabilizes complete index-5 maps and all captured pre-G42 operands in the
admitted two-body controls. This proves suppressibility by deterministic task
order. It does not identify the first unsafe instruction in every upstream
prefusion producer.

## Phoenix Execution Contract

### Global Rules

1. The same input LRI, Phoenix revision, configuration, architecture, and
   floating-point environment must produce byte-identical intermediate dumps
   and output files on every repeat.
2. Floating-point contraction and fast-math remain disabled. A deterministic
   schedule does not license reassociation or contraction.
3. Concurrent work is permitted only when every task owns disjoint output
   storage or when results are reduced later by a specified deterministic
   reduction. Thread count and completion timing must not affect bytes.
4. A mutex around a shared worker body is insufficient. It prevents overlap
   but leaves lock-acquisition order unspecified and did not stabilize Lumen in
   the admitted control.

### Prefusion And Calibration Barrier

Before G-42 construction begins, all candidate production, parent acceptance,
bundle-adjustment writeback, current-bank selection, and composed projection
records for that render must be complete and immutable.

Phoenix must enumerate candidate-producing work in a stable key/index order
and join it before constructing the selected StereoLayer. No depth worker may
observe a bank or projection record while another task can still replace it.
This is the required clean-room response to the admitted upstream
executor-order sensitivity. The exact first unsafe installed instruction in
that producer remains outside the proof and must not be invented in comments
or tests.

### G-42 Ownership

Each G-42 task may own any disjoint set of `(pixel, hypothesis)` cells. For
each cell it must:

1. iterate projected sources in the selected record-vector order;
2. compute the admitted per-source 3x3 cost without parallel reduction inside
   the cell;
3. combine source costs with the admitted `uint16` modulo-add semantics; and
4. apply the admitted binary32 `(1/27)/source_count` normalization once, after
   the source sum, with truncation toward zero.

The completed normalized local-cost volume is immutable during G-43.

### G-43 Ownership And Order

The normative Phoenix reference schedule is serial and uses the exact order
listed below:

```text
(-1,0), (-1,-1), (0,-1), (1,-1),
( 1,0), ( 1, 1), (0, 1), (-1,1)
```

For each direction, scan lines must advance in predecessor-topological order.
The first cell of every line and out-of-band predecessor state use the
admitted initialized state (`Line buf = 2000`, `Min cost buf = 2000`,
`Pixel buf = 0`) wherever the installed recurrence does so.

The portable deterministic reference must use one of these equivalent
ownership designs:

- **Serial shared aggregate:** finish one complete directional pass before
  the next pass reads or writes the aggregate.
- **Private directional planes:** each pass writes only its own `uint16`
  plane; after all passes join, combine planes into a zero-initialized
  aggregate in the normative direction order with saturating-u16 addition.

No task may perform a non-atomic read/modify/write on aggregate storage shared
with another live task. A `uint32` aggregate followed by one final clamp is
not the specified representation; the combine operation is saturating-u16 at
every path contribution.

Because all admitted path contributions are nonnegative, a correctly
implemented saturating-u16 sum has the same value under any serial direction
order. The normative order is still fixed for trace comparability and to keep
future implementation changes from silently introducing order-sensitive
behavior.

### Selection

Argmin visits hypotheses in ascending absolute-index order and updates the
winner only on strict lower cost. Ties therefore keep the first/lowest
absolute hypothesis index. Selection begins only after every required G-43
direction has completed and the aggregate is immutable.

## Build And Runtime Policy

Deterministic behavior is the normal validation contract, not an optional
algorithm variant. A build option named `PHOENIX_DETERMINISTIC` is meaningful
only if it changes target definitions or runtime scheduling and is covered by
repeat tests. Merely declaring an unused CMake option, setting a nominal
thread count, or wrapping workers in a mutex does not satisfy this section.

Optimized builds may use the private-plane design. They must match the serial
reference byte for byte before they are accepted.

## Known Exclusions

- Stock Lumen does not have one deterministic index-5 golden hash under its
  default executor.
- The first unsafe instruction in the observed upstream prefusion producer is
  not admitted.
- This section does not generalize the mode-8 schedule to unselected stereo
  modes, editor-only paths, another `libcp.dylib`, or malformed inputs.
- Final Radiance bytes were not captured under the executor interpose; the
  suppression proof is for the complete index-5 map and captured pre-G42
  state at the stated scope.

## Validation

### Required Self-Repeat Gate

For every release candidate, run at least three fresh-process repeats for one
exact-focal input from each body and each wide/tele family. At minimum this is
Unit-1 `28mm`, Unit-1 `150mm`, Unit-2 `28mm`, and Unit-2 `70mm`; the full gate
uses both bodies at `28/35/70/150mm` when the corpus is mounted.

Require exact equality for:

- accepted candidate-key sequence and numeric calibration-bank writeback;
- projection-record bytes after pointer fields are excluded;
- normalized G-42 local-cost dump;
- each private directional G-43 plane, when that design is used;
- final aggregated G-43 cost volume;
- index-5 hypothesis map; and
- final Phoenix output bytes for a fixed output encoding.

Any repeat mismatch is a Phoenix defect. It must not be waived using the
stock-Lumen repeat envelope.

### Stock-Lumen Comparison

Formula and captured-boundary replays remain exact. Whole-map comparison to
uncontrolled stock Lumen uses the admitted focal-specific repeat envelope and
must report which draw or deterministic interposed capture is the reference.
Do not describe an arbitrary stock map hash as canonical.

## Evidence

- `../../evidence/bundle_static_runtime_index5_nondeterminism_mechanism_two_body.md`
- `../../evidence/bundle_static_runtime_index5_g43_direction_policy.md`
- `../../evidence/bundle_static_runtime_index5_sgm_cost_input_normalization.md`
- `../../evidence/bundle_static_runtime_index5_sgm_recurrence_roles_four_zoom.md`

