<!-- provenance: l16-investigator W5 mid-render magnitude capture (ae7b8ff22388c7f26) + orchestrator arithmetic check, 2026-06-03/04 -->
**Status:** NEEDS_CODEX_VALIDATION. **The "Kth-hit uncapturable under Rosetta" tool wall is BROKEN.** Method:
LLDB ignore-count + conditional breakpoints (core-handled, NO Python per-hit callback) reach mid-render hits in
~11–50 s, no stampede. Magnitudes captured 28mm+70mm (35/150 → W5b). read-watchpoints stay dead (not needed).

# W5 — data-dependent magnitudes captured (wall broken)

## METHOD (reusable; corrects the prior premature "wall")
- **ignore-count:** `breakpoint set --shlib libcp.dylib --address 0xVA -i N` → stops once on hit N+1, no
  stampede. Cost ~linear in N (N=2000 ~18s, 8000 ~47s; N=200000 too slow). Threads stop cleanly.
- **conditional:** `-c "(*(int*)&$xmmN) != 0xHEX"` (register lane) / `-c "(*(int**)($rdi+8))[k] != 0xHEX"`
  (deref struct ptr) → stops on first data-matching hit, full-render scan ~11–15s. **Syntax note:** LLDB
  rejects `(unsigned)$xmm`/`$xmm.uint32[0]`; use the pointer-cast form above.
- **step-inst:** after stopping, `thread step-inst` walks single-thread (mulss→sqrtss) with no stampede.

## 1. Score kernel `0x36cde0` = `sqrt(factorA·factorB)` — REAL non-degenerate values
Return: `0x36e511 mulss xmm0,xmm1` (2 factors) → `0x36e515 sqrtss` → `0x36e528 ret`.
| Tier | hit | factorA | factorB | product | score=√ (orch-checked) |
|---|---|---|---|---|---|
| 70mm | #2001 | 0.44620 | 0.88553 | 0.39512 | 0.62859 ✓ |
| 70mm | #8001 | 0.77157 | 0.78882 | 0.60862 | 0.78014 ✓ |
| 28mm | #8001 | 0.72990 | 0.83486 | 0.60936 | 0.78062 ✓ |
Genuine per-contributor scores in [0,1] (wavelet-SSIM-style), NOT the degenerate 0/1/0.2 first-hit. Confirms the
two-factor `sqrt(factorA·factorB)` formula WITH live magnitudes.

## 2. Merge Σscore `0x36a938 rcpss` (inside terminal merge `0x3661b0`) — REAL accumulated denominators
xmm2 pre-rcpss = accumulated Σscore (broadcast by `0x36a934 shufps`); post = 1/Σscore normalizer.
| Tier | Σscore | 1/Σscore | exact 1/Σ | rcpss rel-err (hw ~12-bit) |
|---|---|---|---|---|
| 70mm | 0.39071 | 2.55957 | 2.55943 | 5.6e-5 |
| 28mm | 0.25464 | 3.92627 | 3.92710 | 2.1e-4 |
| (common) | 0.20000 | 5.00000 | 5.0 | — |
⇒ direct evidence the merge computes **1/Σscore** as the soft-average normalizer (the 0.2 first-hit is a real
but common value, not just degenerate).

## 3. Per-camera CCM `0xbfa20` — RESOLVED: fixed I1I2I3 (Ohta), NOT per-camera
Loads 4×4 from `[[rdi+0x8]]` (rows +0/+0x10/+0x20/+0x30), transposes. Exactly TWO matrices across full renders:
M1 = I1I2I3 forward (bits `0x3f13cd36/0x3f350529/0x3ed10625/0x3f800000`), M2 = its 3×3 transpose (orthonormal
⇒ inverse=transpose). **Full-render conditional excluding BOTH → process exits clean (2/2, 28mm+70mm).** ⇒ no
LRI-derived per-camera 3×3 is promoted to 4×4 at this site; the reopened per-camera-CCM question is answered:
`0xbfa20` = fixed I1I2I3 decorrelation (forward+transpose), data-independent, identical 28/70. (A per-camera CCM
at some OTHER VA, and the `[rdi+0x8]` matrix producer, NOT investigated = residual.)

## Scope / residuals
- Tiers 28+70 only (35/150 → W5b, method proven so mechanically reachable). Single mid-render samples (prove
  non-degenerate magnitudes + the math chain; NOT full per-pixel distributions).
- Does NOT prove `0x3661b0`/`0x36cde0` ARE the merge/reducer per the two-prong rule (N-accept + N→1-store) —
  confirms MAGNITUDE semantics of already-located sites. reducer_verdict stays staging.
- One non-reproducible race stop (concurrent condition eval) — NOT a finding (2/3 clean).

## Graduates AFTER W5b completes 35/150
score_kernel_36cde0_two_factors, score_production (magnitude), ccm_apply_site_located (per-cam resolved),
+ upgrade terminal_merge_3661b0 (Σscore magnitude). HELD until 4-tier.
