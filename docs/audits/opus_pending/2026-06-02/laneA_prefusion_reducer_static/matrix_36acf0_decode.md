<!-- provenance: workflow wf_3fc00563-7ce (l16-prefusion-fanout-w2), 2026-06-03; finder+independent verifier; verifier reliable=True -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, weak-labeled, static disasm/LRI-parse only).
**Verifier reliability:** all load-bearing VAs independently re-extracted (PASS)

## Matrix at 0x36acf0 — classification packet

**Region (libcp.dylib, static disasm):**
- Matrix load: `0x36ac7d..0x36acb5` — 3x `movss` + 3x `movq`, interleaved by `unpcklpd` into xmm0/xmm1/xmm2.
- Apply loop: `0x36acf0..0x36ad35` (scalar-tail) and `0x36ad50..0x36ad7c` (main, unrolled).
- Lane-3 blend: `blendps $0x8, xmm3, xmm4` with xmm3 = `movaps 0x5a88d0` = (0,0,0,1).

**RIP targets (computed; contiguous __bss block):**
| instr VA | target VA | __bss index |
|---|---|---|
| 0x36ac85 movq xmm0 | 0x671980 | f0,f1 |
| 0x36ac7d movss xmm1->xmm0 | 0x671988 | f2 |
| 0x36ac99 movq xmm1 | 0x67198c | f3,f4 |
| 0x36ac91 movss xmm2->xmm1 | 0x671994 | f5 |
| 0x36acad movq xmm2 | 0x671998 | f6,f7 |
| 0x36aca5 movss xmm3->xmm2 | 0x6719a0 | f8 |

After `unpcklpd`: xmm0=[f0,f1,f2,0], xmm1=[f3,f4,f5,0], xmm2=[f6,f7,f8,0].
Apply: `out = in.x*xmm0 + in.y*xmm1 + in.z*xmm2`, then `out.w := 1.0`.

**Q1 — rodata VALUES & VAs:** The three loaded vectors live at **__DATA.__bss+18448 (0x671980..0x6719a3)**, which reads **all zeros in the static image** → they are NOT rodata constants; they are written at runtime. The prior committed runtime read (`docs/evidence/bundle_lldb_iramp_post_weighted_add_shaping.md` L157-159) recorded the three vectors as (0.57735,0.57735,0.57735) / (0.70711,0,-0.70711) / (0.40825,-0.81650,0.40825).

**Q2 — classification:** Orthonormal (norms=1.0, pairwise dots=0.0, det=-1.0). Constants = 1/sqrt3, 1/sqrt2, 1/sqrt6, 2/sqrt6. Row-sums = 1.732, 0.0, 0.0. → NOT identity, NOT near-1-diagonal color matrix, NOT row-sum≈1 white-preserving CCM. It is an **achromatic-axis + 2-chroma orthonormal decorrelation rotation/reflection** (opponent/PCA-style; first axis = luminance (1,1,1)/sqrt3).

**Q3 — runtime-__bss vs rodata-constant:** **RUNTIME __bss** (0x671980, `__DATA.__bss + 18448`). Only the lane-3 source (0,0,0,1) at 0x5a88d0 is true `__TEXT.__const`. Applied **per-output-pixel** in the loop.

**Separation note:** The prior-evidence loop at `0x36abf0` is a different stage — a clamped lerp using two true rodata clamp bounds — and is NOT this matrix multiply.