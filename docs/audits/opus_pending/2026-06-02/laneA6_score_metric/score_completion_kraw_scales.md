<!-- provenance: workflow wf_86500d78-8bf (l16-prefusion-fanout-w3), 2026-06-03; finder+independent verifier; verifier reliable=True -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, weak-labeled, static disasm/LRI-parse only).
**Verifier reliability:** all load-bearing VAs independently re-extracted (PASS)

## 0x36cde0 score metric — Q1 & Q2 (static, libcp.dylib)

Binary: `/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`. All re-extractable via `arch -x86_64 lldb --batch -o 'target create <dylib>' -o 'disassemble --start-address 0xADDR --count N'`. rodata via `memory read --size 4 --format f`.

### Q1 — K is RAW, not (K*L)^2 [OBSERVED]
Per-lane SSIM term block 0x36cea6..0x36cf24:
- 0x36cea6 mean-scale = 0x5cbfc0 = **0.00390625** (= 1/256) applied to all sums.
- C stabilizer loaded ONCE: `0x36ceed movaps 0x5fdc50` (=**0.0099999998**, the K1=0.01 SSIM const) into xmm2.
- Added RAW to numerator: `0x36cef4 addps xmm2,xmm1` where xmm1 = 2*cov (`0x36ceea addps xmm1,xmm1`).
- Added RAW to denominator: `0x36cef7 addps xmm2,xmm5` (xmm5=varA, clamped >=0) then `0x36cefa addps xmm4,xmm5` (+varB).
- **No `mulps` squares the constant; no dynamic-range L multiply precedes it.** => stabilizer is **raw K = 0.01**, NOT C=(K*L)^2.

The 0x36cf06/0x36cf0d pair is a SEPARATE post-SSIM affine remap, not a stabilizer:
- `0x36cf06 addps 0x5fdc60` = **-0.800000011**
- `0x36cf0d mulps 0x5fdc70` = **5.26315784 == 1/0.19 exactly**
- => `(ssim - 0.8) * (1/0.19)`, then `max(0)/min(1)` clamp (0x36cf14, 0x36cf1a-0x36cf24). Maps SSIM [0.8,1.0] -> [0,~1.05]. This explains 0x5fdc70's role: it is the remap gain, not a renorm of K.

(For completeness 0x5fdc50 quad = {0.01, 0.03, 0.03, 1.0}; 0x5fdc60 quad = {-0.8,-0.8,-0.8,-0}; 0x5fdc70 quad = {5.263,5.263,5.263,1.0}.)

### Q2 — Four slots are SCALES (dyadic), not orientations [OBSERVED]
Each r12+0x154x scalar reads pairs with one scale const from 0x5fdb10:
| slot | read VA | scale const | value |
|---|---|---|---|
| 0 | 0x36d080 movss 0x1540(r12) | 0x5fdb10 | -0.00520833 (1x) |
| 1 | 0x36d79c movss 0x1550(r12) | 0x5fdb14 | -0.01041667 (2x) |
| 2 | 0x36e06e movss 0x1560(r12) | 0x5fdb18 | -0.02083333 (4x) |
| 3 | 0x36e355 movss 0x1570(r12) | 0x5fdb1c | -0.04166667 (8x) |

Strict **1:2:4:8 dyadic (octave) progression** => wavelet SCALES. Orientations (LH/HL/HH/LL) carry no inherent x2 magnitude ratio; scales do. (Companion 0x5fdb20.. = {0.3125,0.4375,0.5625,0.625} per-scale offsets.)

### Q2 — "-0x70/-0x80 survive, -0x50/-0x60 discarded": REFUTED at function 0x36cde0
The final-block reduction 0x36e3c4..0x36e437 applies an **identical** horizontal-min to ALL FOUR slots and accumulates ALL FOUR into distinct r12 accumulators:
- -0x80 (xmm5) -> 0x2580(r12) @0x36e43b
- -0x70 (xmm4) -> 0x2590(r12) @0x36e44d
- -0x60 (xmm2) -> 0x25a0(r12) @0x36e45f
- -0x50 (xmm3) -> 0x25b0(r12) @0x36e471

No slot is discarded inside 0x36cde0. So the THREAD's "discard -0x50/-0x60" cannot be a property of this function; it would belong to a downstream consumer of the four accumulators (untraced).

### Return value provenance: STATIC-UNCROSSABLE GAP [LEAD -> needs runtime]
Single return: `0x36e511 mulss xmm1,xmm0 ; 0x36e515 sqrtss xmm0,xmm0 ; 0x36e528 retq` (only sqrtss / only retq in the function). xmm0/xmm1 are NOT loaded in the exit preamble (0x36e483-0x36e4ae GPR-only) nor by the trailing weight loop (0x36e4b0-0x36e4db writes xmm2). Their last static writes are the -0x70 broadcast (xmm0 ~0x36e40f) and -0x80 broadcast (xmm1 ~0x36e433), which is **consistent** with `sqrt(hmin(-0x70)*hmin(-0x80))` as stated in the THREAD — but proving register liveness across the two intervening loops requires a runtime register read at 0x36e511 (breakpoint, read xmm0/xmm1). Static cannot certify this.