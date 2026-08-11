# Static Decode: ColorFusionBayer weight `f` readout (CNR lane-3) — 0x19C790

**Date:** 2026-08-11  **Method:** static disassembly decode only (no runtime, no
Lumen/Phoenix run, no pixel comparison). Source: tools/libcp_disasm_intel.txt;
constants read from installed libcp.dylib __TEXT,__const. 3 parallel decode
agents + main-thread instruction spot-check. whatknown-gated (f readout was the
NO-HITS residual per PORT_STATUS 2026-08-11g).

## Result: the color weight `f` (CNR lane-3) is PINNED to an explicit formula.

    f = [ ((N+1) - Σ_k m_k)^2  +  Σ_k m_k^2 ] / (N+1)^2

- N = number of Bayer modules intersecting the 16x16 patch (vector at [rbp-0x5388],
  size = (end-begin)/0x30). The "+1" is the base/reference term (empty-intersection
  modules contribute m_k = 0, adding C=1 to A).
- m_k = per-module retention scalar emitted by 0x18eb00.

## Instruction evidence (spot-checked on main thread)

### 0x18eb00 — per-module Wiener retention (PROVEN mono formula, vectorized 4-lane)
- d = T - S            subps  @0x18eb36
- d^2                  mulps  @0x18eb3c
- λ (= param·[r8])     mulps  @0x18eb43
- d^2 + λ              addps  @0x18eb47
- 1/(d^2+λ)            rcpps  @0x18eb4a
- w = d^2/(d^2+λ)      mulps  @0x18eb4d
- blend w·T+(1-w)·S    mulps@0x18eb67, addps@0x18eb6a
- retention (1-w) acc  subps@0x18eb73, addps [rsi]@0x18eb76 ; init C=[0x5a8920]=(1,1,1,1)
- × 1/256              mulps [0x5cbfc0]@0x18ebaf   (0x5cbfc0 = 0.00390625 = 1/256, read from const)
=> m_k is the color analog of the PROVEN mono confidence (256-Σw)/256, per module.

### 0x19C790 body (0x19c790..0x19d6dc) — cross-module combine (GENUINELY-NEW color)
- m_k load             movaps [rbp-0x52f0]              @0x19d242
- C - m_k              subps xmm0,[0x5a8920]            @0x19d249/0x19d250   (C=(1,1,1,1))
- m_k^2                mulps xmm1,xmm1                  @0x19d253
- B += m_k^2           addps [rbp-0x5370]               @0x19d25d
- A += C (skip/base)   addps [0x5a8920]                 @0x19d42c
- A^2                  mulps xmm0,xmm0  (A=[rbp-0x5380]) @0x19d503
- A^2 + B              addps [rbp-0x5370]               @0x19d506 → store [rbp-0x5330] @0x19d50d
- (N+1)                imul rax,r15 (inv-3 count)+1     @0x19d643
- (N+1)^2              imul rax,rax                     @0x19d64a
- image tile ÷(N+1)    call 0x19f470                    @0x19d633
- weight tile ÷(N+1)^2 call 0x19dc30                    @0x19d695  → 2nd output arg [rbp-0x5400]
  (2nd output = FCB "second output" quantized by 0x1bd1e0 into CNR lane3 byte plane)

### Control flow (0x19C790)
patch-row y step8 (head 0x19cc20) → patch-col x step8 (head 0x19cc70) →
per-module k=0..N-1 (head 0x19cf70): extract patch 0x19d8e0 → fwd wavelet 0x18fe00 →
scale → Wiener 0x18eb00 (emits m_k) → inv wavelet 0x19eb60 → overlap-add.
Shared half-sample Hann helper 0x18ce50 @0x19cb07 (same as mono).

## PROVEN-SHARED with mono template (do not re-derive)
- Wiener weight w=d^2/(d^2+λ) and blend w·T+(1-w)·S  (0x18eb00)
- retention (1-w), ×1/256 → the (256-Σw)/256 confidence SHAPE, per module
- 16x16/step-8 patch geometry; half-sample Hann OLA (0x18ce50)
- patch-noise H=sqrt(P/Σ1/(I+0.1)^2) is mono-identical (0x18e940/0x18ea20, 0.1@0x5c5800)
  but those siblings are NOT called by the color core; the color noise path adds a
  runtime-config affine/clamp/scale wrapper (0x18e9e4..0x18ea19).

## GENUINELY-NEW color (this decode)
- Cross-module quadratic combine f=(A^2+B)/(N+1)^2 (A=(N+1)-Σm, B=Σm^2). Mono has no
  B term and divides by the first power of 256. This is the color-specific readout.
- Accumulator init inline to C=1 (0x5a8920); mono accumulator helper 0x18da80 is NOT
  called by the color core (confirmed).
- Two outputs: fused image ÷(N+1) [0x19f470]; weight ÷(N+1)^2 [0x19dc30].
- Dual-plane separable-windowed 16x16 marshaling: 0x18ebc0/0x18f690 (plane bases
  [rdi+0x20]/[rdi+0x28], pack loops @0x18ed20/@0x18f7e0); patch ctor 0x18e770;
  √2-normalized fwd/inv lifting 0x18fe00 / 0x19eb60 (coeffs 1/√2,1/(2√2),√2,0.5 @0x5cbf80-b0).

## Residual confirmations before PORTING (small, bounded)
1. m_k internal accounting in 0x18eb00: 4-lane-per-call vs full-patch, exact λ source
   ([r8]), and whether m_k ∈ [0,1] per module (affects numeric range, NOT the f combine).
2. 0x18fe00 fwd-wavelet epilogue UNRESOLVED in linear dump (0x1903fd→0x190403); coeffs known.

## CORRECTION to PORT_STATUS 2026-08-11g
That note said 0x19dc30/0x19e7d0/0x19eb60 "use the proven Wiener table 0x5d0070 with
vectorized wavelet math." REFUTED by boundary-correct decode: 0x19dc30 = ÷(N+1)^2
normalizer (dest=src/divisor, divisor=arg->[+0x10], const 1.0 @0x5a8920, body
0x19dc30..0x19df4e); 0x19e7d0 = ×scale sibling; 0x19eb60 = inverse √2 wavelet lifting.
The Wiener weight lives in 0x18eb00, NOT those. The earlier signature scan used 2500-line
windows that crossed function boundaries. Also: 0x5cedf0/0x5cee00 are int ROI/index masks
(0,0,16,16)/(16,16,16,-1), not the λ weight table; 0x5d0470 is a heterogeneous param
block, NOT a second λ table. 0x5d0070 remains the proven 256-float λ table.
