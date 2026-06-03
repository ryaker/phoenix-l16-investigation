<!-- provenance: workflow wf_3fc00563-7ce (l16-prefusion-fanout-w2), 2026-06-03; finder+independent verifier; verifier reliable=True -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, weak-labeled, static disasm/LRI-parse only).
**Verifier reliability:** all load-bearing VAs independently re-extracted (PASS)

## Score fn 0x36cde0: backward-trace of the two factors at 0x36e511

**Return shape (OBSERVED):** `ret = sqrtss( xmm0 * xmm1 )` where
- `xmm0` = `minss` result at **0x36e40b** = horizontal-min of the 4-lane vector in stack slot **-0x70(%rbp)**
- `xmm1` = `minss` result at **0x36e42c** = horizontal-min of the 4-lane vector in stack slot **-0x80(%rbp)** (loaded 0x36e41a)
- Neither xmm0 nor xmm1 is written between 0x36e437 and 0x36e511. The loop 0x36e4a0-0x36e509 uses only xmm2; 0x36e50f `jne 0x36e529` is the `__stack_chk_fail` canary branch, so 0x36e511 is the normal fall-through.

**REFUTATION of q1=SSIM / q2=wavelet:** The two final multiplicands are NOT one SSIM factor and one wavelet factor. They are two horizontal-minima drawn from the SAME wavelet-scaled reduction family. Evidence:
- All four per-orientation reduction blocks (r12+0x1540/0x1550/0x1560/0x1570 at 0x36d080 / 0x36d79c / 0x36e06e / 0x36e355) multiply by **wavelet scale lanes** 0x5fdb10..0x5fdb1c ({-0.0052,-0.0104,-0.0208,-0.0417}) and 0x5d4c20 (=-8). None of the four final reduction blocks references the SSIM cluster.
- The SSIM consts 0x5fdc50 (K={0.01,0.03,0.03,1}), 0x5fdc60 (floor -0.8), 0x5fdc70 (renorm 5.2632) are consumed UPSTREAM, in the vector SSIM-map blocks at **0x36cea6** (result -> -0x80(rbp) @0x36cf24) and **0x36e200** (0x36e21e/0x36e247/0x36e24e). These produce per-tile vectors that feed the reductions; they are not a top-level factor.

**Topology (OBSERVED):** SSIM-class statistical map (mu/sigma2/sigma_xy accumulation 0x36ce40-0x36cea4, mapped via K/floor/renorm) -> feeds per-orientation tiles -> four wavelet-scaled scalar reductions into stack slots -0x50/-0x60/-0x70/-0x80 -> two of those slots (-0x70, -0x80) are horizontal-min'd to xmm0,xmm1 -> `sqrt(xmm0*xmm1)`. (-0x50/-0x60 hmin'd too at 0x36e3c8/0x36e3e6 but written back to slots, not into the final pair.)

**K raw-vs-squared (UNRESOLVED / LEAD):** In the inspected ranges (0x36cde0-0x36cf30, 0x36e200-0x36e260) the K vector at 0x5fdc50 is added directly (addps) into the denominator path; no self-square (`mulps 0x5fdc50,0x5fdc50`) or explicit `(K*L)^2` of those lanes was observed. This leans "raw as stored" but the upstream L (dynamic-range) scaling of the mu/sigma terms before the K-add was not fully traced, so a squared-equivalent folded into the stat normalization cannot be excluded. Marked LEAD.

**Delta vs committed evidence:** `docs/evidence/bundle_lldb_iramp_36cde0_scalar.md` already states `sqrt(xmm0*xmm1)` and inventories the consts, but did NOT backward-resolve which sub-computation produces xmm0 vs xmm1. The xmm0=0x36e40b / xmm1=0x36e42c hmin finalization, the both-are-wavelet finding, and the SSIM-consts-are-upstream finding are new.