# Lane A6 — Non-claims

1. **The exact closed-form score formula is NOT assembled.** Byte-verified constants + Codex's bounded
   structure identify the metric *family* (SSIM + CDF 9/7). The full expression — how the spatial-SSIM
   term and the wavelet term combine into `sqrt(q1·q2)`, and the exact `(−0.8)/0.19` remap — is a LEAD,
   not proven.

2. **The precise SSIM variant is NOT pinned.** Constants match standard SSIM stabilizers (K1=0.01,
   K2=0.03), but whether it is single-scale SSIM, MS-SSIM, IW-SSIM, or a custom wavelet-SSIM is not
   determined. "SSIM-class" is the honest scope.

3. **CDF 9/7 δ coefficient NOT tightly located.** α, β, γ, ζ, 1/ζ are byte-exact in the cluster
   `0x5cbfd0..0x5cc040`; δ (≈0.443507) was not in that cluster (one loose ~0.44347 hit elsewhere,
   unconfirmed). The wavelet-family ID rests on the 5 confirmed coefficients, which is conclusive, but
   the full 4-lifting-step decode is not closed.

4. **Helper bodies `0x371730` / `0x371a90` were NOT disassembled here.** Their CDF-9/7 role is inferred
   from the shared constant pool + Codex's "transform reductions" bounding, not from their instruction
   stream in this packet.

5. **Score → weight-vs-threshold consumption is NOT established here.** Whether the score is used purely
   as a reciprocal weight (Lane A3 reconciliation) or also as an acceptance/rejection threshold
   (Blocker 5) is a separate open question this packet does not resolve.

6. **Runtime score values are not semantic.** Per Codex's doc, first-hit tuple values are
   thread-scheduling dependent; do not promote any numeric sample.

7. Byte-reads are deterministic/OBSERVED; the metric-family identification is a LEAD pending Codex
   re-extraction. `NEEDS_CODEX_VALIDATION`.
