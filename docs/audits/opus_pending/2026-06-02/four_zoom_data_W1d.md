<!-- provenance: l16-investigator runtime W1d first-hit sweep (ab77d0b76b23e1896), 2026-06-03 -->
**Status:** NEEDS_CODEX_VALIDATION. W1d four-zoom first-hit firing + structure. Method: stampede-free (BP one
stage, read at first stop, kill). 28mm `.lris` hidden→restored (verified 10514107 B). Scope = first-hit/tier,
Unit-1, profile 3. All 7 sites fired 4/4 tiers; no BP missed.

# W1d — depth-runtime + lane-A geometry/contributor (four-zoom firing + structure)

## Depth runtime cluster (FIRES 4-zoom) → graduates depth runtime side
- `0x29ed90` guided-upsample, `0x226c70` depth-compute (xref "no lower src cams" `0x6325fd`), `0x276790`
  StereoLayer::runPass — all FIRE 28/35/70/150.
- **Depth-compute enabled "lower src cams" count = 4 at every tier** (read at `0x226cab`, count=(end−begin)/4
  from builder `0x22ee10`, 4-byte elems). No tier/group difference at first hit.

## lane-A geometry/contributor cluster (FIRES 4-zoom)
- `0x216f60` geometry/warp-record builder (CalibDataProcessor::State spawner) — FIRES all tiers.
- `0x36930f` contributor sentinel (`cmpl $0x80000000`) in merge `0x3661b0` — FIRES all tiers; first-hit
  `eax=0x80000000, rsi(idx)=0` ⇒ index-0 slot is the sentinel/skip marker, uniform all tiers (structure).
- `0x36cde0` score kernel — FIRES standalone all tiers (magnitude still tool-limited).

## COHERENCE SYNTHESIS — "5+5+6" is static lens grouping, NOT runtime camera count
Across the runtime sweeps: stereo cost record N=**4** (W1a), depth-compute lower-src-cams=**4** (W1d), terminal
merge contributors N=**5** (W1c) — **all tier-invariant** (same at 28/35/70/150). ⇒ the **5+5+6** split is
purely the Block-3 intrinsics/lens focal grouping (static calibration); the runtime active-processing uses
FIXED small contributor sets (4 stereo / 4 depth-src / 5 merge) per tile regardless of focal tier. This
reconciles every "5+5+6 not observed at runtime" finding (W0/W1a/W1c/W1d) into one statement.

## Graduations (→ findings_for_codex, first-hit/firing scope)
- `depth_stereo_no_lri_origin.md` — FULL graduate: LRI-side (no depth origin) already graduated via the
  consolidated calibration finding; runtime side now 4-zoom (DepthCache/StereoLayer/upsample fire; 4 src cams).
- `contributor_gate.md` — sentinel `0x36930f` structure 4-zoom (index-0=0x80000000 uniform).
- `geometry_builder_216f60.md` — `0x216f60` fires 4-zoom (role confirmed; internal record semantics = residual).

## Stays staging
- `score_production.md` / `score_kernel_36cde0_two_factors.md` — firing 4-zoom but score/Σscore MAGNITUDE
  tool-walled (Rosetta Kth-hit). Magnitude owed (native-arm64/differential).
