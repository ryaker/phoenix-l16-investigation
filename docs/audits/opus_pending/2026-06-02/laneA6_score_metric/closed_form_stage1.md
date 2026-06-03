# Lane A6 addendum — stage-1 score closed form (SSIM contrast-structure, assembled)

**Status:** `NEEDS_CODEX_VALIDATION`. Upgrades A6 from constant-spotting to an **assembled** first-stage
arithmetic (the spatial term); the second stage (CDF 9/7 wavelet, helpers `0x371730`/`0x371a90`) and the
final `sqrt(q1·q2)` combination remain LEAD. Instructions + constants are OBSERVED (deterministic).
Binary `libcp.dylib` sha256 `b38dc4b3…`.

## Assembled arithmetic (`0x36cea6..0x36cf24`)

Per-lane (vec4) over the two 16×16 patches A (`r14`/reference) and B (`r12`/contributor), after the
accumulation loop, all ×`1/256` (`0x5cbfc0`):
```
μ_A, μ_B, E[A²], E[B²], E[AB]
σ²_A = max(0, E[A²] − μ_A²)            (0x36cebc..0x36cec8)
σ²_B = max(0, E[B²] − μ_B²)            (0x36cecb..0x36ced7)
σ_AB = max(0, E[AB] − μ_A·μ_B)        (0x36ceda..0x36cee3)

num  = 2·σ_AB + C2                      (0x36ceea addps self; 0x36cef4 +C2)
den  = σ²_A + σ²_B + C2                 (0x36cef7 +C2; 0x36cefa +σ²_B)
cs   = num / den   via rcpps           (0x36cefd rcpps; = (2σ_AB+C2)/(σ²_A+σ²_B+C2))   <-- SSIM contrast-structure
T    = μ_A[3] · cs                      (0x36cee6 shufps $0xff broadcast μ_A lane3; 0x36cf00·0x36cf03 mulps)
q1   = clamp( (T − 0.8) · (1/0.19), 0, 1.0 )   (0x36cf06 +(−0.8); 0x36cf0d ×5.2631; 0x36cf17 max0; 0x36cf21 min1)
store q1 -> -0x80(%rbp)                 (0x36cf24)
```

## Byte-verified constants (deterministic)

- `C2 = 0.03` — from `0x5fdc50 = (0.01, 0.03, 0.03, 1.0)` (used at `0x36cef4` & `0x36cf0d` rip→`0x5fdc50`).
  (Standard SSIM uses C2=(K2·L)²; here `0.03` is applied **directly** — a simplified/variant SSIM.)
- offset `−0.8` — `0x5fdc60` (rip→ from `0x36cf06`).
- scale `1/0.19 = 5.2631579` — `0x5fdc70` (rip→ from `0x36cf0d`).
- upper clamp `1.0` — `0x5a8920` (rip→ from `0x36cf1a`).

## What this establishes

1. **The metric is genuinely SSIM-derived** — `cs = (2σ_AB+C2)/(σ²_A+σ²_B+C2)` is the canonical SSIM
   **contrast×structure** term, now assembled from the disasm (not merely inferred from constants).
   (It is NOT full canonical SSIM: the luminance term is replaced by a single `μ_A[3]` factor, C2 is
   used un-squared, and a `(·−0.8)/0.19` stretch + `[0,1]` clamp is applied.)
2. **A built-in soft floor at similarity ≈ 0.8.** Because `q1 = clamp((T−0.8)/0.19, 0, 1)`, any
   contributor whose luminance-weighted SSIM-cs `T` falls below `0.8` yields `q1 = 0` → score
   `sqrt(q1·q2) = 0` → A7 weight `max(0, 0−0.5) = 0`. So **low-structural-similarity contributors are
   driven to zero weight by the score itself** — a layered, *soft-but-effective* rejection that sharpens
   the Blocker-5 answer (ghost/trail suppression): the effective acceptance band is SSIM-cs ≳ 0.8.

## Non-claims
- Stage-2 (CDF 9/7 wavelet, `0x371730`/`0x371a90`) and the `sqrt(q1·q2)` combination are NOT assembled
  here (still LEAD from A6).
- Per-lane semantics: stats are vec4 (per channel); the `μ_A[3]` lane-3 factor (alpha/4th channel)
  weighting the cs term is observed but its public meaning is unknown.
- `T`'s exact range/units depend on patch normalization; "≈0.8 floor" assumes T is a normalized
  similarity in [0,1], consistent with the clamp but not independently proven.
- LLM-read disasm; constants byte-verified. `NEEDS_CODEX_VALIDATION`.
