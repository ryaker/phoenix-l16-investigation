<!-- provenance: l16-investigator runtime W1c first-hit merge sweep (ac8c68e5d7ee576da) + orchestrator static verify, 2026-06-03 -->
**Status:** NEEDS_CODEX_VALIDATION. W1c four-zoom first-hit data on the terminal IRAMP merge `0x3661b0`. Method:
stampede-free (BP one stage, read at first stop, kill). 28mm run CLEAN (`.lris` hidden→`.bak` then RESTORED,
10514107 B back at canonical path; only file mutation, reverted). Scope = first-hit/tile/tier, Unit-1, profile 3.

# W1c — terminal merge structure (four-zoom) + tool-limit on reduction magnitude

## OBSERVED four-zoom (all confirmed 4/4 tiers)
- **Contributor count N = 5** per merge invocation, uniform 28/35/70/150 (matches Codex committed
  entry-signature). **Layout correction (orchestrator-verified `0x366a50`):** the contributor vector is at
  `ctx+0x18` (ptr→std::vector); `N = (end−begin)/16` (16-byte elements = plane ptr + score/weight ptr).
  `mov rcx,[r15+0x18]; mov rax,[rcx]; mov rcx,[rcx+0x8]; sub; sar 0x4`. **NOT `[rdi+0x8]/[rdi+0x10]`** (that's
  a different 192-byte inline working-set vector; the static packets' `[arg0+0x8]` field map is corrected).
- **Merge runs PER 512×512 tile:** `[rdi+0x38]` output Image = 512×512 stride 512 all tiers; `rsi` = per-tile
  rect (e.g. 28mm first-hit (4608,3072,5120,3584)). Per-tier full-canvas difference is handled by TILING, not
  this descriptor — so the merge core is tier-invariant at the tile level.
- **lane-3 detail-transfer blend `0x36aa30` FIRES 4-zoom:** at `blendps`, xmm0=(5,5,5,5), xmm4=(1.0,0.2,0.2,1.0)
  — the `recip*0.2` constant live + identical all tiers.
- **B-spline-in-merge `0x368657` FIRES 4-zoom** (ties merge-interior resample to every tier).

## TOOL LIMIT (Rosetta) — reduction magnitude NOT obtainable at first-hit
At `rcpss 0x36a938` (1/Σscore), the input is **0.2 (constant) at first-hit all tiers** → rcpss=5.0; this is the
lane-3 0.2 path, NOT an accumulated per-pixel Σscore. The actual `1/Σscore` soft-average magnitude is
**data-dependent and only appears at later (Kth) hits**, which Rosetta cannot cheaply skip to (per-hit
continue = stampede; read-watchpoints dead). ⇒ **merge reduction VALUES = UNKNOWN at first-hit; needs
native-arm64/single-step or a differential-render approach.** Stated per-datum; does NOT downgrade the
structural facts above.

## Graduations (→ findings_for_codex, first-hit scope)
- `terminal_merge_3661b0.md` — N=5 4-zoom, per-512×512-tile, output dims, lane3+bspline fire, ctx+0x18 layout
  corrected. (Structure four-zoom OBSERVED; reduction magnitude = tool-limited residual.)
- `lane3_blend.md` — `0x36aa30` fires 4-zoom, recip*0.2 constant live all tiers.

## Stays staging (tool-limited / not a full verdict)
- `reducer_verdict.md` — W1c proves the signature ACCEPTS N=5 four-zoom, but the finder is explicit this is a
  CANDIDATE for "merge accepts N>1", NOT a full N→1 reducer verdict (reducer body/accumulator stores not
  verified this run; two-condition rule). Stays staging.
- `score_production.md` / `score_kernel_36cde0_two_factors.md` — score/Σscore MAGNITUDE degenerate at first-hit
  (tool limit). Formula + firing 4-zoom; magnitude owed (native-arm64 / differential).
