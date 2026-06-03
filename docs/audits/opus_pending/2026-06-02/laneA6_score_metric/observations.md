# Lane A6 — Observations

Function `0x36cde0` (callee of the Lane A3 contributor body at `0x369e3f`; inputs `rdi=-0x4240` reference
patch, `rsi=-0x11a0` warped contributor patch; returns scalar in `xmm0`). Codex's
`bundle_lldb_iramp_36cde0_scalar.md` bounded the structure; this packet adds the constant-family identity.

## O1 — SSIM-class spatial statistics (Codex-bounded structure + byte-verified stabilizers)

Codex's doc (cited, not re-derived here) shows the first 16×16 loop accumulates, then ×`1/256`
(`0x5cbfc0`, byte-verified): patch means μ_A, μ_B; squared-sums → variances σ²_A, σ²_B via
`sqsum − mean²` with `maxps` non-negative clamp; cross-sum → covariance σ_AB via `cross − μ_Aμ_B` with
`maxps` clamp. These five quantities (μ_A, μ_B, σ²_A, σ²_B, σ_AB) are exactly the SSIM components.

Stabilizers (byte-verified): `0x5fdc50 = (0.01, 0.03, 0.03, 1.0)`. These are the **standard SSIM
constants K1=0.01, K2=0.03** (the two `0.03` lanes = the two C2 uses in luminance/contrast/structure).
SSIM(x,y) = [(2μ_Aμ_B+C1)(2σ_AB+C2)] / [(μ_A²+μ_B²+C1)(σ²_A+σ²_B+C2)].

Remap constants (byte-verified, role LEAD): `0x5fdc70 = 5.26315784 = 1/0.19`, `0x5fdc60 = (-0.8,-0.8,-0.8,-0.0)`
— consistent with a linear remap of an SSIM-like value, e.g. `(s − 0.8)/0.19`, clamped — i.e. stretching
the high end of the similarity range into a weight. Exact remap not closed-form-proven.

## O2 — CDF 9/7 biorthogonal wavelet stage (byte-verified coefficients)

Second-stage helpers `0x371730` / `0x371a90` (called on the `r14`/reference patch) use the **CDF 9/7
lifting coefficients** (the JPEG-2000 lossy DWT / Cohen–Daubechies–Feauveau 9/7):

| rodata | value | CDF 9/7 role |
|---|---|---|
| `0x5cbfd0` | 1.58613432 | α (predict-1), magnitude |
| `0x5cbfe0` | 3.17226863 | 2α |
| `0x5cbff0` | −0.05298012 | β (update-1) |
| `0x5cc000` | −0.10596024 | 2β |
| `0x5cc010` | −0.88291109 | γ (predict-2) |
| `0x5cc020` | −1.76582217 | 2γ |
| `0x5cc030` | 1.14960444 | ζ (scaling K) |
| `0x5cc040` | 0.86986440 | 1/ζ |
| `0x5cbf80` | 0.70710677 | 1/√2 (Haar/orthonormal norm) |
| `0x5cbfa0` | 1.41421354 | √2 |

α, β, γ, ζ, 1/ζ match canonical CDF 9/7 to 6–7 significant figures — conclusive for the wavelet family.
(δ ≈ 0.443507 was NOT found in this tight cluster; one loose ~0.44347 hit exists elsewhere, unconfirmed —
see `non_claims.md`.)

## O3 — return

`0x36e511 mulss %xmm1,%xmm0 ; 0x36e515 sqrtss %xmm0,%xmm0` → the score is `sqrt(q1·q2)` of two scalar
sub-results (Codex-proven). LEAD: a geometric mean of two quality terms (e.g. spatial-SSIM term ×
wavelet-domain term), consistent with composite structural-similarity / quality metrics.

## Interpretation (LEAD)

The per-contributor merge weight is a **wavelet-domain SSIM-class structural-similarity / quality score**:
spatial SSIM statistics (μ/σ²/σ_AB with K1=0.01, K2=0.03) combined, via a `sqrt` of a product, with a
CDF 9/7 wavelet-transform term. This is the "patch statistics + transform reduction" Codex bounded,
now identified at the constant level as SSIM + CDF 9/7 — both published and clean-room-reimplementable.
The exact closed form (which SSIM variant; how the wavelet term enters the product; the `(−0.8)/0.19`
remap) is not assembled here.
