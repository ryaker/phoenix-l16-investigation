> GRADUATED to four-zoom OBSERVED (2026-06-03, W1c — four_zoom_data_W1c.md). 0x36aa30 fires 4-zoom; recip*0.2 detail-transfer constant live all tiers. Scope=first-hit/tile/tier, Unit-1. Reduction MAGNITUDE = Rosetta tool-limited (residual).

<!-- provenance: workflow wf_4bb93945-fac (l16-prefusion-fanout), 2026-06-03; finder+independent verifier; verifier reliable=True -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, weak-labeled, static disasm/LRI-parse only).
**Verifier reliability:** all load-bearing VAs independently re-extracted (PASS)

# Quarantine packet (WEAK-LABELED): lane-3 reciprocal*0.2 = per-pixel correction gain, then forced to 1.0

Scope: static disasm of `libcp.dylib` (`/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib`), function `___lldb_unnamed_symbol_3661b0`. No runtime/LLDB-launch in this packet (those samples already exist in the two committed bundles cited below). NOT a merge/reducer verdict.

## VERDICT (1-line)
Lane 3 (vec4 offset +0xc) is set to `reciprocal*0.2` (blendps at 0x36aa35), READ downstream as a per-pixel scalar gain on a clamped correction term (shufps $0xff at 0x36abff -> mulps at 0x36ac06), then OVERWRITTEN to 1.0 by a later matrix-transform stage (blendps $0x8 against const (0,0,0,1) at 0x36ad2c). It is a correction weight, not a final normalizer/alpha.

## Q1 — where 0.2 is loaded, multiplied by reciprocal, written to lane 3
```
0x36a938  rcpss  %xmm2, %xmm2
0x36a93c  movaps %xmm2, -0x42f0(%rbp)         ; save reciprocal
0x36a9b5  movaps -0x42f0(%rbp), %xmm4         ; reload reciprocal
0x36a9bc  mulss  0x274f40(%rip), %xmm4        ; RIP-target 0x5df904 = 0x3e4ccccd = 0.200000003
0x36a9c4  shufps $0x24, %xmm4, %xmm4          ; xmm4 = xmm4[0,1,2,0]  -> lane3 = reciprocal*0.2
...
0x36aa30  movaps (%r10,%rdi), %xmm0           ; source vec4
0x36aa35  blendps $0x8, %xmm4, %xmm0          ; xmm0[3] = reciprocal*0.2   <-- WRITE to +0xc
0x36aa42  movss  (%rax,%rdx,4), %xmm1         ; weight-table value
0x36aa47  mulss  (%rax,%rcx,4), %xmm1         ; separable weight product
0x36aa4c  shufps $0x0, %xmm1, %xmm1
0x36aa50  mulps  %xmm0, %xmm1                 ; weighted source (incl. lane3)
0x36aa53  addps  (%rsi,%rdi), %xmm1           ; accumulate
0x36aa57  movaps %xmm1, (%rsi,%rdi)           ; store accumulator
```
Constant proof: `memory read 0x5df904` -> `3e4ccccd 3eb33333 3fd55555 c0a00000` (lane0 = 0.2).

## Q2 — what lane 3 carries downstream (the +0xc read after accumulate)
```
0x36abf0  movaps (%rdx), %xmm3               ; reference vec4
0x36abf3  movaps (%rax), %xmm4               ; dest_before
0x36abf6  subps  %xmm4, %xmm3                ; delta = reference - dest_before
0x36abf9  movaps (%rcx), %xmm5               ; accumulated vec4 (lane3 = reciprocal*0.2)
0x36abfc  movaps %xmm5, %xmm6
0x36abff  shufps $0xff, %xmm6, %xmm6         ; xmm6 = lane3 broadcast  <-- READ of +0xc
0x36ac03  mulps  %xmm0, %xmm3                ; delta * 2.0   (xmm0 from 0x5a887c = 2.0)
0x36ac06  mulps  %xmm6, %xmm3                ; delta * lane3-weight
0x36ac09  maxps  %xmm1, %xmm3                ; clamp >= -0.1 (0x5fdbc0)
0x36ac0c  minps  %xmm2, %xmm3                ; clamp <= +0.1 (0x5cbf70)
0x36ac0f  addps  %xmm4, %xmm5               ; accumulator + dest_before
0x36ac12  addps  %xmm3, %xmm5               ; + bounded correction
0x36ac15  movaps %xmm5, (%rax)             ; store
```
Constants: 0x5a887c=2.0; 0x5fdbc0=-0.1x4; 0x5cbf70=+0.1x4.

## Fate of lane 3 after use (correction to "final alpha/normalizer" theory)
A subsequent loop applies a 3x3 matrix multiply (row consts loaded 0x36ac7d..0x36acb5; lanes 0/1/2 broadcast & MAC at 0x36ad12/0x36ad1c/0x36ad26) then:
```
0x36ad2c  blendps $0x8, %xmm3, %xmm4         ; xmm4[3] = xmm3[3]
```
where xmm3 = const at 0x5a88d0 = (0,0,0,1) (`memory read 0x5a88d0` -> `0 0 0 1`). So lane 3 is forced to 1.0 (homogeneous/alpha placeholder), i.e. the confidence weight is consumed locally, not propagated to the output pixel.

## Interpretation (LEAD, not fact)
Lane 3 = a per-pixel confidence/weight derived from reciprocal*0.2 (a normalized inverse of some accumulated count/energy), used to scale a bounded (+/-0.1) detail/ghost-suppression-style correction (delta between a reference buffer and the dest buffer, gain 2.0). After the correction it is discarded (set to 1.0). This is consistent with a guarded refinement step, NOT a denominator normalization of the weighted sum. (Reducer/merge verdict not asserted: signature N>1 acceptance and accumulator N->1 reduction not jointly proven here.)

## Novelty / cross-check
- Q1 already in `docs/evidence/bundle_lldb_iramp_tuple_post_reciprocal_weighted_add.md` (lines 103-121).
- Q2 already in `docs/evidence/bundle_lldb_iramp_post_weighted_add_shaping.md` (lines 12-19, 65-77; incl. "forces lane 3 to 1.0").
- This packet independently re-extracts all VAs/constants and adds explicit (0,0,0,1) lane-3-force const at 0x5a88d0 and the 2.0 scale at 0x5a887c. No contradiction found with committed bundles.

## Open
- The matrix-transform row constants at 0x36ac7d..0x36acb5 not decoded to values (whether YCbCr/XYZ/identity-scale) — would confirm the "color-space transform" naming in the shaping bundle.
- Semantics of the reciprocal source (what sum 1/(sum) measures) not established here.
- All static; runtime lane-3 numeric samples live in the two cited bundles, not re-collected.