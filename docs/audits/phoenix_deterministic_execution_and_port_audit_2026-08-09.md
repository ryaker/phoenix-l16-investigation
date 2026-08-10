# Phoenix Deterministic Execution And Port Audit, 2026-08-09

**Truth snapshot:** `docs/TRUTH.md` v3.0.350  
**Authority:** `docs/canonical/CLAIM_LEDGER.md`  
**Phoenix snapshot:** `/Users/ryaker/L16_Phoenix/phoenix`, HEAD
`f7f0a23e2bf359f43520c2c8adca471edb433ab3`, plus the repairs listed below

## Purpose

This is an implementation audit against admitted profile-3 truth. It is not a
new truth source and does not score image similarity. The reusable checker is:

```bash
python3 tools/audit_phoenix_profile3_contract.py
```

## Findings

### P0: CNR still consumes a disproven constant fourth lane

Phoenix `tools/phoenix_fuse.cpp` computes CNR tile moments from three RGB lanes
and algebraically substitutes `meanA = 1` / `AP[c] = sum(p_c)`. Installed and
runtime proof now establishes that source lane 3 is data-driven
`guide^2`, and all eight focused Unit-1 `70mm` dispatches use that producer
rather than the empty-guide constant-1 arm.

The guide is a half-resolution/pixel-doubled per-tile image at denoise-task
`+0x60`, produced inside RTTI-named
`lt::Internal::Pipeline::setWhiteBalance::$_22`. Its exact source and
normalization remain open, so a code repair is not yet licensed. This audit
admits that correction as `CLM-DENOISE-002 PARTIAL/BLOCKER` in TRUTH 3.0.350.

Consequence: Phoenix's current CNR covariance/noise matrix is wrong even when
the admitted public AWB, SensorGainVars, and SVD formulas are otherwise wired.
The existing verifier reports `16/16` captured packets for the true lane and
`0/16` for the constant-1 substitute.

### P1: Production calibration uses an explicit fit, not an installed replay

`tools/phoenix_depth.cpp` defaults `refine_mode = "auto"` and runs an NCC plus
Huber/Gauss-Newton intrinsics/pose refinement described in its own comments as
a non-parity fit. Its per-point NCC work is output-disjoint and repeatable in
the current source, but the algorithm is not the admitted installed
CalibDataProcessor/BA arithmetic.

This is not permission to disable refinement blindly: level-0 records must be
compared against a deterministic Lumen capture first. The implementation must
either replay a subsequently closed installed formula or carry an explicit
non-parity label; it cannot be called ledger-exact.

### P1: No release-level fresh-process repeat gate exists

The production banded G-43 implementation is serial, uses saturating-u16
combines, and is deterministic by ownership. However, Phoenix has no release
test that repeats the full profile-3 process and compares calibration records,
G-42, G-43, the index-5 map, and final bytes. The former CMake option
`PHOENIX_DETERMINISTIC` was declared but had no consumer and changed no code;
it has been removed rather than preserved as a false control.

The normative test matrix and ownership rules are now in
`docs/canonical/PARITY_SPEC/08_DETERMINISTIC_EXECUTION.md`.

### P2: A shadow depth API still contains placeholders

`engine/depth/pipeline.cpp` still calls `buildCostVolumePlaceholder`, while
the actual `phoenix_fuse` route shells out to `phoenix_depth_tool`, whose
banded path contains the current projection/G-42/G-43 implementation. The
shadow API is not the current production depth output, but its public-looking
name and tests make accidental reuse likely. It should either delegate to the
production implementation or be renamed and isolated as a synthetic test
fixture.

## Repaired In This Pass

### Skip-mask edge-task policy

The production tool duplicated the pattern-2 generator with simple
`tx += 64`, `ty += 64` loops. At `2080x1560` that creates `33x25 = 825` fresh
MT19937 task streams. Lumen's admitted executor creates `32x24 = 768` tasks,
with final tiles `[1984,2080)` and `[1472,1560)`.

Independent replay gives:

```text
admitted: tasks=768 sha256=1a28b93c687d4a8b5c743cb009de4082513f8758709e73f8fc735ede9b9d92ba
old tool: tasks=825 sha256=5950e2c5c994aff154b2cd0ca8a3ca171940c7b2f4817c29aebe3fbcc4a444b4
byte delta: 71,728
```

The duplicate was removed. `phoenix_depth_tool` now calls the already-correct
`depth::buildSkipMaskPattern2`, and boundary-byte assertions were added to the
depth tests so counts alone cannot hide a future RNG-restart error.

### G-43 deterministic trace order

The production banded path already ran eight serial passes with saturating-u16
combines, so it did not reproduce Lumen's data race. Its call order has now
been aligned to the admitted positive predecessor group followed by the
negative group:

```text
(-1,0), (-1,-1), (0,-1), (1,-1),
( 1,0), ( 1, 1), (0, 1), (-1,1)
```

The separate `engine/depth` headers, pipeline comment, and phase report were
corrected from the obsolete four-path account to eight paths.

## Verification

```text
phoenix_depth_tool build: PASS
phoenix_depth_tests: 34 passed, 0 failed, 0 skipped
git diff --check: PASS
```

The audit checker now reports only the unresolved CNR lane-3 failure and the
noncanonical prefusion-fit warning.

## Stale Proposed Work

- C6/key 15 is already terminally closed for canonical tele bridge HDR by
  `CLM-C6-001`; it is not a remaining profile-3 investigation item.
- MonoFusion mode 1's scalar formula is closed for profiles 1/2 compatibility
  scope. Canonical profile 3 uses mode 0 at wide and no MonoFusion at tele, so
  mode-1 breadth does not block the profile-3 app.

## Next Investigation

1. Follow denoise-task `+0x60` backward at runtime inside
   `setWhiteBalance::$_22`; match its guide against the lambda's concrete
   `Image<u16>`, `CapturedImage`, and `SoftISP::Stats` inputs and close the
   normalization.
2. Extend that guide/source proof across four focals and both physical bodies,
   then add a complete CNR tile replay and port it.
3. Run the deterministic Unit-2 `70mm` level-0 boundary comparison in order:
   Guidance and four sources, composed records, normalized G-42, each G-43
   direction/aggregate, then argmin.
4. Add the fresh-process Phoenix self-repeat gate from the deterministic
   execution spec.

