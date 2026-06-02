# WSJF Priority

This file is planning guidance.

It is not a truth authority.

If this file and the canonical blocker or claim docs disagree, the blocker and claim docs win.

## Purpose

This file prioritizes the current blocker set toward the actual end goal:

- ghost-free parity-grade merge quality
- correct framing and participation
- stability across `28mm`, `35mm`, `70mm`, and `150mm`

## Inputs

This prioritization is grounded in:

- [PARITY_BLOCKERS.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/canonical/PARITY_BLOCKERS.md)
- [ENDGOAL_UNKNOWNS.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/canonical/ENDGOAL_UNKNOWNS.md)
- [BLOCKER_PATHS.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/canonical/BLOCKER_PATHS.md)

## WSJF Method

Standard WSJF:

`WSJF = Cost of Delay / Job Size`

Using these planning factors:

- `Business Value`
  How directly the blocker affects the end-goal quality bar.
- `Time Criticality`
  How much delaying this keeps the project from making honest forward progress now.
- `Risk Reduction / Opportunity Enablement`
  How much closing this blocker unlocks other blockers or prevents wrong implementation.
- `Job Size`
  Estimated investigation size, based on how concrete the existing resolution path already is.

Scale:

- benefit factors: `1..10`, higher is more important
- `Job Size`: `1..10`, higher is larger

## Raw WSJF Table

| Blocker | BV | TC | RR/OE | CoD | JS | WSJF | Notes |
|---|---:|---:|---:|---:|---:|---:|---|
| Pair-grid producer depth semantics / LRI origins / public names | 10 | 9 | 8 | 27 | 3 | **9.00** | Geometry-critical; storage, consumer formula, row matrix chain, tracked map-provider runtime path, descriptor custody boundary, four-zoom depth-builder handoff, `0x29ed90` worker formula, and `StereoLayer<false>` index-5 source custody are proven; remaining work is public meaning and LRI origin mapping |
| Exact pre-fusion merge/reduction mechanism behind `src1` / `src2` | 10 | 10 | 10 | 30 | 6 | **5.00** | Highest architectural leverage; `N-to-1 reducer` remains only a search shorthand; the visible wrapper, `PipelineCache+0x8` level-vector metadata correction, visible `src1` lookup key, visible `src1` payload constructor path / level vector, visible `src1` versus direct-contributor payload-family and secondary-callable splits, visible `src1` secondary-callable live handoff, visible `src1` worker/projection-record handoff to `0x3e4c50` / `0x3e42e0`, static `0x3e42e0` coordinate-transform formula and field-pack producer, visible `src1` source-image producer topology, first captured visible-`src1` source-producer virtual target `0x65b3c8/+0x30 = 0x341770`, capped lower virtual target census (`0x33f3e8` / `0x33f94f` all four zooms, `0x33ffd4` wide-tier only under tested gate), capped target-family visible-body static classification, bound indirect target chains `0x342d99 -> 0x342b80 -> 0x2eb560` and `0x3449f0 -> 0x345920 -> 0x2f53d0`, `0x341770` helper `0x2e8680` / callback `0x2e8cc0` as one-source Bayer/RAW region-helper work, visible `src2` hot state/static body boundary, and accumulator surfaces are four-zoom observed/static-bounded, while `0x3e2e90` / `0x3e4c50`, source-producer region-adapter/helper/census target visible bodies, owner cache selection, owner alternate-cache setup, visible `+0x678` constructor/runtime record-pack, selected layer virtual, record-consumer, `StereoLayer<false>::runPass` cost-path, sibling `StereoLayer<false>::compute` cost-path, prefusion callable-gate, candidate-scoring surfaces remain excluded as closure points; the immediate `0x2f53d0` helper chain is bounded as validation / descriptor-vector setup / bilateral-kernel-size dispatch / executor dispatch, its executor callback bodies are bounded as local descriptor transform / filtering / interpolation / normalization / accumulation surfaces, the tested first-visible-`src1` route selects `0x2fb320` rather than `0x2f78e0`, the selected `0x2fb320` worker is bounded as descriptor / `vec4` coefficient / normalized weighted-store mechanics, and all thirteen corrected upstream `CalibDataProcessor::State ()` `operator()` bodies are now four-zoom runtime-live with count pattern `(1,1,4,4,4,1,1,1,5,5,5,5,1)`; `0x247390` is excluded from that State census and refuted as a State body; public helper-field semantics, public descriptor-field names/origins, `State` return semantics, semantic `src1` contents, and merge/reducer closure remain excluded as closure points |
| Tele odd-camera routing, especially C6 | 8 | 7 | 8 | 23 | 3 | **7.67** | Strong tele-risk; keyed-helper/vector-builder and projection field-pack dispatcher boundaries are excluded, key `15` is proven constructed active then later cleared at `0x3c90a5`, focused identity proof ties the active key-list helper observations at `0x1bdbab` / `0x1bdbdd` to the same item pointer cleared at the mutation boundary, helper `0x1bdb60` is classified as key-list bookkeeping, all 58 direct static `call 0xf2720` sites now have admitted tele runtime census coverage, the newly covered active sites are constructor-adjacent key/container/tree materialization helpers, a post-mutation same-byte watchpoint sees the tracked active byte still `0` at 18 later stops per tele render, a selected-field watch proves pre-output `+0x60/+0x64` reads and cleanup-only watched pair/type ranges, the immediate post-mutation state consumer is proven, the downstream rect-vector builder, ImagePyramid consumer route, and immediate per-level zero-fill callsite are proven, selected later static `context+0x538` candidate families are zero-hit under complete four-zoom bridge HDR, representative first-8-byte data watchpoints have zero hits after zero-fill, expanded tele-grid first/middle/last data watchpoints across all five zero-filled levels have zero hits at `70mm` and `150mm`, candidate context consumer `0x3c9540 -> 0xe6c30` is zero-hit under tested tele bridge HDR, and both the direct candidate loop and stereo-side keyed-record loop prove key `15` is filtered by post-mutation `object+0x30 = 0`; remaining work is untested-field/alias proof, final effect of the watched `+0x60..+0x67` reads, unprobed range proof for later write/read behavior and final C6 image-merge effect of the zero-filled ImagePyramid/geometry route, alternate image-effecting routes, or terminal-filter proof |
| Full merge topology beyond the four-zoom-proven accumulator, entry signature, and direct contributor identity | 10 | 8 | 9 | 27 | 7 | **3.86** | Essential for spec closure, but now starts after `CLM-MERGE-002`, `CLM-MERGE-003`, and `CLM-MERGE-004` are four-zoom proven |
| Merge acceptance / rejection logic beyond accumulator | 10 | 7 | 9 | 26 | 9 | **2.89** | Very important; local SAD/WTA/refinement/bilinear tuple write, `0x36cde0` scalar production, `0x36e530` accumulator-prep source/weight wiring, first downstream tuple-consumer multiply-add, immediate post-reciprocal weighted add, immediate post-weighted-add shaping, caller-side post-IRAMP square-copy handoff, caller-side post-square vector-scale handoff, caller-side `0x3e5720` executor setup, row-callback binary16 conversion, owner `+0xf0` storage sink, first owner `+0xf0` downstream expansion family, immediate expansion handoff, expansion destination-context backing, first selected-cache route to `0x36f800`, first-owner branch census, first direct-branch post-route handoff, global branch-site caller/slot census, global post-route family classification, global parent-chain ancestry, static parent-chain body classification, static helper-surface classification, static selected-cache/post-route classification, static downstream direct-caller census, static selected-cache caller census, static `0x3e5720` caller census, static `0x3d4e10` caller census, static/runtime `0x3d5400` executor-route liveness, first weighted `0x36f800` store, row-cache helper formula, fresh first-dispatch row-plan segment coverage, and full-render leading/trailing row-cache reachability are now bounded, but downstream row-image/final policy after the classified caller/helper/post-route/direct-caller/selected-cache-caller/`0x3e5720`-caller/`0x3d4e10`-caller/`0x3d5400`-executor-route families and final suppression policy remain open |

## Raw Ranking

Pure WSJF gives this order:

1. pair-grid producer calibration semantics / LRI origins
2. C6 routing
3. `src1` / `src2` pre-fusion merge/reduction mechanism
4. four-zoom merge topology closure
5. final merge acceptance / rejection logic

## Dependency-Adjusted Order

Raw WSJF is not the whole story, because some blockers unlock others.

Recommended execution order:

1. `src1` / `src2` pre-fusion merge/reduction mechanism
2. pair-grid producer calibration semantics / LRI origins
3. C6 routing
4. four-zoom merge topology closure
5. final merge acceptance / rejection logic

## Why The Dependency-Adjusted Order Differs

### 1. `src1` / `src2` should start first even though it is third in raw WSJF

- Reason:
  it is the most central architectural unknown and partially conditions both tele routing and full topology closure.
- Scope:
  the search should not require one tidy `N-to-1` reducer closure; it should accept a distributed mechanism if the proof points there.
- Current narrowed boundary:
  tele promoted target-2 records are now proven to enter concrete `0x2416d0` selected-index vectors, the small admitted promoted sets reach `(state=5,target=2)` stores, watched state-5 records continue into `0x244560 -> 0x25d090`, four-zoom runs prove `0x2457c0` materializes finite non-sentinel coordinate pairs into `state+0x1e8` from the state-5 store path, representative emitted pairs are read by `0xe8e70` vector-copy work under both State-helper copy-out paths, and representative copied-destination pairs are touched again by `0xe8e70` under State-helper recopy plus higher node-vector materialization/copy sites; `0x25d090` output/effect, non-copy downstream image/effect after the copied coordinate-vector propagation sites, final acceptance/rejection, and reducer closure remain open.
- Consequence:
  solving it early reduces the chance of spending time validating the wrong topology story.

### 2. pair-grid calibration semantics should start immediately as a parallel peer

- Reason:
  it has the best raw WSJF and a tight existing decode path; the storage, consumer formula, row matrix chain, tracked map-provider runtime path, descriptor custody boundary, and four-zoom depth-builder handoff are already proven.
- Consequence:
  it is ideal for a parallel lane because it is geometry-bounded and mostly independent of the `src1` / `src2` path.

### 3. C6 routing should start early but not be forced to full closure before `src1` / `src2`

- Reason:
  it already has concrete exclusions, a proven constructor/mutation chain, focused active key-list helper observations tied to the same item pointer cleared at `0x3c90a5`, helper-body classification as key-list bookkeeping, admitted tele runtime census coverage for all 58 direct static `call 0xf2720` sites, same-byte post-mutation watchpoint proof that the tracked active byte remains `0` at all observed later active-byte stops, selected-field watchpoint proof for pre-output `+0x60/+0x64` reads and cleanup-only watched pair/type ranges, a proven immediate post-mutation state consumer, a proven immediate downstream rect-vector builder path plus ImagePyramid consumer, a proven immediate per-level zero-fill callsite, selected later static `context+0x538` candidate families excluded by zero-hit four-zoom liveness, representative first-8-byte data watchpoints showing zero later touches for those watched ranges, expanded tele-grid first/middle/last data watchpoints across all five zero-filled levels showing zero later touches at `70mm` and `150mm`, and two proven filter points: the visible-`src1` keyed helper / vector-builder boundary and projection field-pack dispatcher boundary are excluded as positive C6 routes; key `15` is constructed active, queried while active by key-list and constructor-adjacent helper surfaces, later cleared at `0x3c90a5`, and then observed inactive in the state-classification walk; candidate downstream context route `0x3c9540 -> 0xe6c30` is zero-hit under tested tele bridge HDR; and the direct candidate loop plus stereo-side keyed-record loop both filter key `15` by post-mutation `object+0x30 = 0` under canonical bridge HDR runs. Final closure still needs untested-field/alias proof, proof of the final effect of watched `+0x60..+0x67` reads, unprobed range proof for later write/read and image-merge effect of the zero-filled ImagePyramid/geometry route, alternate image-effecting route proof, or terminal-filter proof.
- Consequence:
  early work is valuable, but final closure may depend on blocker `#1`.

### 4. Four-zoom topology closure should follow the structural answers

- Reason:
  this is partly validation closure, not just discovery.
- Consequence:
  it should consume the results of `src1` / `src2`, pair-grid, and tele routing work rather than trying to substitute for them.

### 5. Final merge acceptance / rejection logic remains high value but broad

- Reason:
  it matters enormously to ghost-free quality, but it is currently the least pinpointed of the five.
- Consequence:
  it can run as a deeper disassembly lane, but it should not block the more sharply-bounded investigations from going first.

## Parallelization Map

Yes, this blocker set naturally parallelizes.

Recommended immediate lanes:

### Lane A

- Topic:
  `src1` / `src2` reducer
- Primary doc:
  [BLOCKER_PATHS.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/canonical/BLOCKER_PATHS.md)
- Nature:
  LLDB + installed-vtable + upstream-from-wrapper decode

### Lane B

- Topic:
  pair-grid producer calibration semantics / LRI origins
- Primary doc:
  [BLOCKER_PATHS.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/canonical/BLOCKER_PATHS.md)
- Nature:
  runtime/static tracing from the proven producer records back to public calibration fields and LRI block origins

### Lane C

- Topic:
  tele odd-camera routing / C6
- Primary docs:
  `c6_destination_and_depthcache.md`, `a2_destination.md`
- Nature:
  later write/read behavior and final C6 image/merge effect of the zero-filled post-mutation ImagePyramid/geometry route, untested-field/alias proof, final effect of watched `+0x60..+0x67` reads, alternate-route proof, or terminal-filter proof after the now-proven active `0x1bdbab` / `0x1bdbdd` observations, helper-body bookkeeping classification, `0x3c90a5` mutation, same-byte post-mutation watchpoint, selected-field watchpoint, state-classification consumer, rect-vector builder/ImagePyramid/zero-fill path, and post-mutation `object+0x30 = 0` direct/stereo gates
- Dependency note:
  can start immediately, but final closure may depend on Lane A

### Lane D

- Topic:
  final merge acceptance / rejection logic
- Primary docs:
  `iramp_substages_verified.md`, `iramp_kernel_body.md`
- Nature:
  bounded deeper disassembly after the now-proven IRAMP inner body, caller-side square-copy handoff, post-square vector-scale handoff, `0x3e5720` executor setup, row-callback binary16 conversion, owner `+0xf0` storage sink, first owner `+0xf0` downstream expansion family, immediate expansion handoff, expansion destination-context backing, first selected-cache route to `0x36f800`, first-owner branch census, first direct-branch post-route handoff, static selected-cache/post-route classification, static downstream direct-caller census, static selected-cache caller census, static `0x3e5720` caller census, static `0x3d4e10` caller census, static/runtime `0x3d5400` executor-route liveness, first weighted `0x36f800` store, row-cache helper formula, and fresh first-dispatch row-plan segment coverage
- Dependency note:
  mostly independent, but broader and expected to close slower than the higher-ranked lanes

### Lane E

- Topic:
  four-zoom topology closure
- Primary doc:
  [VALIDATION_POLICY.md](/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/docs/corpus/VALIDATION_POLICY.md)
- Nature:
  claim completion and validation on the canonical quartet
- Dependency note:
  should consume outputs from Lanes A through C before being frozen into spec

## Recommended Near-Term Execution

If only one lane runs:

1. `src1` / `src2` reducer
2. pair-grid calibration semantics / LRI origins
3. C6 routing

If two lanes run in parallel:

1. Lane A: `src1` / `src2`
2. Lane B: pair-grid calibration semantics / LRI origins

If three lanes run in parallel:

1. Lane A: `src1` / `src2`
2. Lane B: pair-grid calibration semantics / LRI origins
3. Lane C: C6 routing

If four lanes run in parallel:

1. Lane A: `src1` / `src2`
2. Lane B: pair-grid calibration semantics / LRI origins
3. Lane C: C6 routing
4. Lane D: IRAMP acceptance / rejection decode

## Practical Answer

If the question is "what should we do next, WSJF-adjusted, and can it be parallelized?", the answer is:

1. Start `src1` / `src2` decode now.
2. Start pair-grid calibration semantics / LRI origin decode in parallel immediately.
3. Start C6 routing work in parallel if capacity exists.
4. Hold four-zoom closure as the integration / validation lane.
5. Treat final merge acceptance / rejection logic as an important but broader deep-decode lane.
