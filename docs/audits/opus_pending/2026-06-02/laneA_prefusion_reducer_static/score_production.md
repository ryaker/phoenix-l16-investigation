<!-- provenance: workflow wf_4bb93945-fac (l16-prefusion-fanout), 2026-06-03; finder+independent verifier; verifier reliable=True -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, weak-labeled, static disasm/LRI-parse only).
**Verifier reliability:** all load-bearing VAs independently re-extracted (PASS)

# QUARANTINE PACKET: score production 0x36cde0 -> tuple -> Sscore -> 1/Sscore (0x36a938)

Binary: /Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib (Mach-O x86_64). Method: static `arch -x86_64 lldb --batch` disassemble + `memory read -f f`. All labels OBSERVED unless noted LEAD.

## 1. 0x36cde0 return = sqrt(factorA * factorB)  [OBSERVED]
- 0x36e511 `mulss %xmm1, %xmm0`
- 0x36e515 `sqrtss %xmm0, %xmm0`
- 0x36e519..0x36e527 epilogue; 0x36e528 `retq`
- This is the ONLY sqrtss in 0x36cde0..0x36e528. The function is ~6 KB (entry 0x36cde0, ret 0x36e528), much larger than the previously-bundled "scalar core" excerpt (bundle_lldb_iramp_36cde0_scalar.md, which stops near 0x36d0e5). So sqrt(product) is confirmed; the two factors (q1,q2) are produced by two large interleaved sub-blocks (xmm0 and xmm1 at 0x36e511). The precise per-factor VA lineage of xmm0/xmm1 is PARTIAL (LEAD) because the function body is interleaved with data/branch material (disasm misaligns near 0x36e485).

## 2. SSIM-contrast-structure sub-block (factor candidate q1) [OBSERVED]
First quad block 0x36ce06..0x36cf24 computes per-window mean/var/cov over a 16x16-ish tile (two loops, addps/mulps), then:
- 0x36cea6 `movaps ->0x5cbfc0` (=1/256) scales the accumulated sums (window normalization)
- mean-square subtraction: 0x36cebf `mulps`, 0x36cec2 `subps`, then `maxps 0` (variance floor >=0) at 0x36cec8/0x36ced7/0x36cee3
- C-constants: 0x36ceed/0x36cef4/0x36cef7 use 0x5fdc50 region (C1/K1=0.01); rcpps at 0x36cefd; final `maxps 0` then `minps ->0x5a8920` (=1.0) at 0x36cf1a, stored to -0x80(%rbp)
- Floor mechanism: 0x36cf06 `addps ->0x5fdc60` (-0.8), 0x36cf0d `mulps ->0x5fdc70` (5.26315784 = 1/0.19): i.e. (x-0.8)/0.19 renormalization = the ">=~0.8 SSIM floor" rescaled to [0,1].

## 3. SSIM constant table @ 0x5fdc50 [OBSERVED, memory read -f f]
- 0x5fdc50: 0.00999999977  (K1 = 0.01)
- 0x5fdc54: 0.0299999993   (K2 = 0.03)
- 0x5fdc58: 0.0299999993
- 0x5fdc5c: 1.0
- 0x5fdc60: -0.8, -0.8, -0.8, -0.0
- 0x5fdc70: 5.26315784 (x4)  (= 1/(1-0.8))
- 0x5cbfc0: 0.00390625 (x4)  (= 1/256)
- 0x5a8920: 1.0 (x4)  (min-clamp)
These are referenced BY 0x36cde0 (rip targets computed from 0x36cea6/0x36ceed/0x36cf06/0x36cf0d/0x36cf1a).

## 4. Tuple store of the score [OBSERVED]
- 0x369e3f `callq 0x36cde0` (sole call site in enclosing fn ___lldb_unnamed_symbol_3661b0)
- 0x369e72 `leaq (%rax,%rax,2),%rax` -> x3 => 3-float (12-byte) record stride; base `0x60(%rcx,%rdx)`
- 0x369e7e `movss %xmm1,(%rcx,%rax,4)`     slot0 (from -0x4310)
- 0x369e8b `movss %xmm1,0x4(%rcx,%rax,4)`  slot1 (from -0x4320)
- 0x369e91 `movss %xmm0,0x8(%rcx,%rax,4)`  slot2 = the 0x36cde0 score  <-- 3rd scalar

## 5. Sscore running sum and 1/Sscore [OBSERVED]
Separate later loop (NOT the score call site):
- 0x36a7d8 `movss 0x8(%rbx,%rcx,4),%xmm0` reads tuple slot2 (the score) -> 0x36a7de saves to -0x4300
- 0x36a838 `callq 0x372a00` (per-iter bilinear sample helper; consumes slots 0/1, not the score)
- 0x36a8fe `addss %xmm3,%xmm2`  xmm3=-0x4300 (score), xmm2=-0x42f0 (running Sscore)
- loop trip test 0x36a91d-0x36a92e (count = (ptr_hi-ptr_lo)>>7 * 0xCCC.. => /5*128/... record count)
- 0x36a934 `shufps $0x0,%xmm2,%xmm2`; 0x36a938 `rcpss %xmm2,%xmm2` = 1/Sscore; stored 0x36a93c to -0x42f0
- 1/Sscore is then broadcast (0x36a946) and used as a per-contributor normalization weight downstream (0x36a958+, call 0x19e7d0).

## Falsification result
PREDICTION held for (1) sqrt(product) and (3) constants @0x5fdc50. CORRECTION for (2): the score is produced once (0x369e3f) and parked in tuple slot2 (0x369e91); the accumulation loop reads slot2 (0x36a7d8) and sums (0x36a8fe), then reciprocates (0x36a938). The loop immediately preceding 0x36a934 calls 0x372a00, NOT 0x36cde0 -- the prior scaffold phrasing "the loop just before 0x36a934" implying it calls the score fn is refuted.

## Cross-check vs committed evidence
bundle_lldb_iramp_36cde0_scalar.md exists and documents the scalar core up to ~0x36d0e5; this packet EXTENDS it past the previously-unshown tail (sqrtss/ret at 0x36e515/0x36e528) and pins the constant table values + tuple/Sscore wiring. No committed doc modified.