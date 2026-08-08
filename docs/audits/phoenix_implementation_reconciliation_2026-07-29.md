# Phoenix Implementation Reconciliation, 2026-07-29

**Truth snapshot:** `docs/TRUTH.md` v3.0.342  
**Authority:** `docs/canonical/CLAIM_LEDGER.md`  
**Implementation reviewed:** `/Users/ryaker/L16_Phoenix/phoenix`

## Purpose

This is an implementation audit, not a new truth source or pipeline spec. It
pins concrete Phoenix divergences against already-admitted clean-room evidence
after the latest builder changes. If this document disagrees with the claim
ledger, the ledger wins.

The reviewed Phoenix worktree was dirty. All listed changes are treated as
newer user/builder work and must be preserved during repair.

## Pinned Source Snapshot

```text
21220df6fb319cdbc7b90d86b94805dd860ddf8a899f253523279e0a2803aa0d  tools/phoenix_fuse.cpp
f0876ecd715ada9ec7adb308c80c0aa4c7886f9edc4d7cb1732dbb6ca917da7e  engine/premerge/demosaic.cpp
d69eaf14ed0d131478d85a4ec40e75267d12274f467d0b46c4e092f0024500b7  engine/premerge/vignetting.h
38161d2c6ed8d8ae27cf4e6323eb0a1862087e9eeed83a76da833de0ee358aa4  engine/merge/monofusion.cpp
ccc50571d6bd89ea943f73292160a7ededb421d46dcb349f5c04e5c9d5bec168  engine/merge/mono_flow.cpp
700c3f6c44bda4735b8650ffa1fdb8ca9557b04eb0dad38e668aa4624a15cbd0  engine/merge/merge_types.h
8d3d00e174c599cdc7649b7e2518660a2fbb2e250ae1c5e099b0461b04791e58  engine/postmerge/patch_nlm.cpp
```

## Current Blocking Divergences

### 1. Color-camera preparation is one conflated product

`tools/phoenix_fuse.cpp:1127-1253` currently builds one full-resolution plane
as hot-pixel -> demosaic of raw DN -> black subtraction/clamp/rescale ->
vignetting -> undistort. The admitted selected pipeline has distinct products
and different stage contracts:

- selected scalar color preparation preserves negative normalized samples and
  applies cross-talk before `DemosaickLightV1`;
- the admitted color vignetting worker operates later in the fixed
  `2080x1560` domain with its exact mapped rectangle and interpolation order;
- MonoFusion flow operands have their own pre-undistort public constructions;
- full-resolution IRAMP/reference operands must not inherit a half-resolution
  StereoLayer coordinate rule by accident.

Concrete defects in the snapshot:

- `phoenix_fuse.cpp:1229-1235` demosaics before normalization and clamps the
  black-subtracted result to zero;
- `phoenix_fuse.cpp:1241-1249` maps the `17x13` grid across current image
  endpoints with `(W-1,H-1)`, not the admitted `2080x1560` worker geometry;
- `engine/premerge/vignetting.h:10,53` still says cross-talk is excluded.

The cross-talk exclusion is superseded by TRUTH v3.0.339 through v3.0.341 and
the admitted `CLM-CORRECTION-001` addenda. The selected profile-3 `float,true`
worker, public matrix-grid origin, generated IR rows, selector fields, amount,
and scalar formula are now implementation requirements.

**Required repair:** split product builders by their actual consumers. Build
the scalar pre-demosaic color path in admitted order, preserve signed float
values, add selected public cross-talk, and construct the fixed-domain stereo
color product separately from full-resolution merge/MonoFusion products.

### 2. Production MonoFusion does not consume the admitted operands or flow

The new `engine/merge/mono_flow.*` code is present, but the production driver
does not call it. `phoenix_fuse.cpp:1341` invokes `monoFuseLuma` without a flow
argument, so the canonical wide route still uses zero displacement.

The driver also changes the admitted arithmetic:

- `phoenix_fuse.cpp:1193-1203` applies the A2 exposure affine and an additional
  `1023/(1023-42)` rescale before entering MonoFusion;
- `monofusion.cpp:186-201` applies `(source-42)*frame_scale+42` again, so the
  exposure affine is applied twice;
- `phoenix_fuse.cpp:1339-1340` folds the extra rescale into `VstNoise.scale`;
- `phoenix_fuse.cpp:1328-1329` uses guessed luma weights
  `(0.25,0.5,0.25)` instead of installed AR1335
  `(0.2155500054359436,0.43230700492858887,0.35214298963546753)`;
- `phoenix_fuse.cpp:1347-1352` ratio-scales RGB and clamps it nonnegative,
  which is not the admitted generated-descriptor construction.

The standalone flow validators begin from captured or separately prepared
operand planes. They demonstrate the flow worker but do not prove that the
production driver constructs its A1/A2 level-0 operands from public LRI fields.

**Required repair:** construct the exact public A1 reference and A2 source
flow operands, generate the admitted five-level pyramids, run `monoFlow`, pass
its nonzero/rejection vectors to `monoFuseLuma`, and apply the source affine
exactly once. Validate the production entry point against the existing
two-body operand, pyramid, flow, and coefficient-stage oracles.

### 3. Exact unrefined SSE reciprocal is implemented as division

`engine/premerge/demosaic.cpp:9-11`,
`engine/merge/merge_types.h:20-31`, and
`engine/postmerge/patch_nlm.cpp:15-21` deliberately replace admitted
unrefined `rcpss`/`rcpps` with `1.0f/x`. `engine/merge/monofusion.cpp` also
uses exact divisions at reciprocal-defined formula sites.

TRUTH v3.0.342 and
`docs/evidence/bundle_runtime_x86_rcpss_rcpps_exact_emulation.md` remove that
portability waiver for the current reference environment. The integer-only
mapping matches scalar and packed instructions over 6,242,316 cases.

**Required repair:** add one header-only `phoenix::x86Rcp` primitive and use it
only where the admitted operation is an unrefined SSE reciprocal. Preserve
each parent formula's float32 operation order; do not replace ordinary divide
instructions indiscriminately.

### 4. MonoFusion coefficient math still contains approximations

`engine/merge/monofusion.cpp:112-123` computes patch noise with binary64 sums,
exact division, and implementation-only denominator guards.
`monofusion.cpp:221` computes the Wiener weight with exact division and an
invented `1e-20f` epsilon. Those choices conflict with the admitted float32
order and unrefined reciprocal sites.

**Required repair:** replay the installed stage order with the shared exact
reciprocal primitive and extend the existing MonoFusion tests to compare
whole intermediate packets, including nonzero flow and rejected vectors.

### 5. PatchNLM topology and boundary policy were incorrect

`engine/postmerge/patch_nlm.cpp` implements an independent center-pixel
candidate average with edge-clamped 4x4 patches. The installed selected body
instead uses deterministic phased reference patches and overlap-adds all 16
weighted candidate-patch pixels into full-frame numerator/denominator images
seeded with `0.01*source` / `0.01`. This is not merely an edge discrepancy;
it changes the entire frame's accumulation topology. The installed body also
uses reference-center range scale and a row-parity checkerboard candidate set,
not all 25 centers.

**Proof and repair target:** TRUTH v3.0.343 and
`bundle_static_runtime_nlm_patch_overlap_topology.md` close the installed
topology, phase generator, interior bounds, reference-center range-scale
lookup, checkerboard candidate selection, and no-clamp boundary construction.
Phoenix must replace its current
worker with that overlap-add algorithm. Concurrent task-addition order remains
a validation detail for bit-level comparison.

## Repair Order

1. Add and exhaustively test the shared exact reciprocal primitive.
2. Split the current catch-all plane builder into consumer-specific products.
3. Implement the admitted selected scalar cross-talk before color demosaic.
4. Wire exact public MonoFusion A1/A2 operands, pyramid construction, flow,
   rejection, and single exposure affine into production.
5. Validate each boundary against existing captured two-body stage oracles
   before judging end-to-end image deltas.
6. Replace PatchNLM's center-pixel/clamped worker with the admitted phased
   overlap-add topology, then audit other remaining full-frame edge choices.

## Supersession Note

`implementation_repair_handoff_2026-07-16.md` remains useful for earlier
depth/merge repairs, but its statement that cross-talk is excluded from the
tested profile-3 route is superseded by the later corrective liveness,
formula, and selector admissions. This document supersedes that one only for
the concrete snapshot and defects listed here; neither document supersedes
the claim ledger.

## 2026-08-01 Repair Status

The implementation snapshot has moved since this audit was written. The
following findings above are now repaired and independently exercised:

- the shared portable unrefined SSE reciprocal is implemented and tested
  against direct `_mm_rcp_ss` on x86_64;
- selected PatchNLM now follows the admitted phased overlap-add topology;
- MonoFusion coefficient arithmetic uses the admitted float32 reciprocal
  operations; and
- `DemosaickLightV1` has been corrected beyond the original audit target.

The demosaic repair exposed an error in the former canonical prose itself, not
just Phoenix. Corrective bundle
`bundle_corrective_static_runtime_demosaicklightv1_fullframe_two_body.md` and
TRUTH v3.0.344 now establish red/blue first-stage and green refined-stage
ownership, virtual derived-plane halos, asymmetric residual guards, and exact
21-tap addition order. Current Phoenix matches all `51,916,800` installed RGBA
float32 words on each Unit-1 and Unit-2 exact-`28mm` A1 operand and all
`66,560` compared tiled guide/residual words. Native premerge tests pass
`21/21` active cases; x86_64 passes `22/22`, with two pre-existing
artifact-dependent skips in each architecture.

The former production MonoFusion wiring finding is closed at the flow boundary.
`phoenix_fuse` now derives the exact A1/A2 level-0 operands from public RAW,
builds the admitted `[2,4,4,4]` pyramids and residual flow, and feeds that flow
to `monoFuseLuma` in the native pre-undistort frame. Unit-1 and Unit-2 exact-
`28mm` smoke renders reproduce the installed final rejection totals exactly:
`73,073` and `521`. The remaining production boundary is narrower: Phoenix
still re-injects the fused scalar into its already processed RGB anchor by a
ratio, while installed wrapper `0x1b3530` applies two 3x3 coefficient packs and
an object-owned offset/scale. Those pack values, public origins, and exact
scalar-to-RGB application remain investigation work.
