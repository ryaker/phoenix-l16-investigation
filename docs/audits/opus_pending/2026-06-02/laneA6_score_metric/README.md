# Lane A6 — the per-contributor merge SCORE metric at `0x36cde0`

**Status:** `NEEDS_CODEX_VALIDATION`. Extends (does not replace) Codex's committed
`docs/evidence/bundle_lldb_iramp_36cde0_scalar.md`, which bounded `0x36cde0` as a patch-statistics +
transform-reduction scalar returning `sqrt(xmm0*xmm1)` but **explicitly left the metric un-named**.
Binary `libcp.dylib` sha256 `b38dc4b3…`, VA == file offset. Constants are byte-read (OBSERVED);
the metric-family identification is a strong **LEAD**.

## What `0x36cde0` is (LEAD, constant-anchored)

The per-contributor merge weight (the 3rd field of the `(flow_x, flow_y, score)` tuple from Lane A3) is a
**CDF 9/7 wavelet-domain, SSIM-class structural-similarity / quality score** computed between the two
16×16 patches (`-0x4240` reference vs `-0x11a0` warped contributor). It combines:

1. **Spatial SSIM statistics** — Codex bounded the first 16×16 loop as accumulating μ_A, μ_B, σ²_A, σ²_B,
   σ_AB, normalized by 1/256, with variance/covariance clamped non-negative. The stabilizer constants at
   `0x5fdc50 = (0.01, 0.03, 0.03, 1.0)` are the **standard SSIM K1=0.01, K2=0.03** (C1=(K1·L)², C2=(K2·L)²).
2. **A CDF 9/7 biorthogonal wavelet transform** — the second-stage helpers (`0x371730`, `0x371a90`) use
   the byte-verified **CDF 9/7 lifting coefficients** (JPEG-2000 lossy DWT) plus √2 Haar normalization.

Both are **named, published algorithms** → clean-room Phoenix can reimplement the merge-weight metric
from the SSIM formula + CDF 9/7 lifting without copying any libcp bytes.

## Why it matters

This names the metric that drives **merge weighting** (Blocker 1/3, the score-weighted reduction of
Lane A3) and is a candidate input to **acceptance/rejection** (Blocker 5, the least-mapped wall — a
quality score is exactly what a ghost/trail-suppression gate would threshold on). Identifying it as
structural-similarity (not raw SAD/SSD) is a substantive semantic step.

## Byte-verified constants (OBSERVED — deterministic, see `commands.txt`)

SSIM stabilizers: `0x5fdc50 = (0.01, 0.03, 0.03, 1.0)`. Patch normalization: `0x5cbfc0 = 1/256`.
Haar √2: `0x5cbf80 = 0.70710677`, `0x5cbfa0 = 1.41421354`.
**CDF 9/7 lifting** (vs canonical α=−1.586134, β=−0.052980, γ=0.882911, ζ=1.149604, 1/ζ=0.869864):
`0x5cbfd0=1.58613432` (α), `0x5cbfe0=3.17226863` (2α), `0x5cbff0=-0.05298012` (β),
`0x5cc000=-0.10596024` (2β), `0x5cc010=-0.88291109` (γ), `0x5cc020=-1.76582217` (2γ),
`0x5cc030=1.14960444` (ζ), `0x5cc040=0.86986440` (1/ζ). All match to 6–7 sig figs.

## Files
- `observations.md` — the constants + how they map to SSIM/CDF-9/7; the assembled-so-far arithmetic.
- `non_claims.md` — what is NOT proven (the exact closed form; δ; the precise SSIM variant).
- `commands.txt` — reproducible byte-reads.
- `manifest.json` — machine-readable summary.
