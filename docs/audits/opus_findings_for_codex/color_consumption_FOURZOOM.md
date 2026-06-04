<!-- GRADUATED finding. provenance: color-consumption render batch (color-render ab599958f3a679850) + orchestrator deterministic row-sum/I1I2I3 re-check, 2026-06-04. -->
**Status:** NEEDS_CODEX_VALIDATION — **GRADUATED to four-zoom OBSERVED** (Tier 1) for the per-camera CCM
apply AND the AWB reciprocal consumption (§3, now four-zoom 2026-06-04); the CCM→payload writer on the taken
`eax==0` path is the one narrowed scoped OPEN. Runtime LLDB; row-sums + I1I2I3-distinctness + AWB arithmetic
orchestrator-re-checked.

# Color consumption — per-camera CCM `0xa9f20` is the LRI Block-6 CCM (four-zoom)

## 1. `0xa9f20` consumes a REAL per-camera D65-normalized 3×3 CCM (four-zoom) — RESOLVES the per-camera-CCM Q
Captured at the apply call `0x3467ba` where `rdx = *[BayerPipelinePayload+0]+0x14` (`0x346797 movq (%r15),%rbx;
0x3467a3 addq $0x14,%rbx`). The 3×3 read live per tier:
| Tier | row-major 3×3 | row-sums (orch-checked) |
|---|---|---|
| 28mm | `[0.82463,0.16997,−0.03038; 0.25420,1.09188,−0.34609; −0.11277,−0.53307,1.47105]` | [0.96422,1.0,0.82521] |
| 35mm | `[0.82261,0.17100,−0.02939; 0.25270,1.09237,−0.34507; −0.11426,−0.53584,1.47532]` | [0.96422,1.0,0.82521] |
| 70mm | `[0.85571,0.13950,−0.03099; 0.26641,1.08083,−0.34724; −0.11007,−0.50882,1.44410]` | [0.96422,1.0,0.82521] |
| 150mm| `[0.84062,0.14719,−0.02359; 0.25515,1.08459,−0.33974; −0.12147,−0.52822,1.47491]` | [0.96422,1.0,0.82521] |
**Row-sums are EXACTLY the LRI Block-6 f2.2 row-sums `[0.9642, 1.0, 0.8252]` on all four tiers** (= D65 CIE
white) ⇒ `0xa9f20` applies the **per-camera LRI Block-6 CCM**, NOT the I1I2I3 decorrelation. Row0 ≈
`[0.82,0.17,−0.03]` is plainly not `[1/√3]×3`. Per-entry tier spread 0.007–0.033 = real per-tier/per-camera
calibration drift (reference camera differs by focal tier: ref=0 for 28/35, ref=8 for 70/150). Independence
corroborated statically: `0xa9f20`'s body has **0** calls to the I1I2I3 site `0xbfa20`. Two trailing floats
after the 9 entries = `[0.345669, 0.358496]`, identical all tiers (a fixed following field, not per-camera).

⇒ **the color pipeline is TWO distinct transforms: per-camera CCM (`0xa9f20`, LRI Block-6 f2.2) THEN fixed
I1I2I3 decorrelation (`0xbfa20`).** This RESOLVES the residual that `merge_magnitudes_FOURZOOM` §3 deferred
("a per-camera CCM at some OTHER VA … NOT investigated").

## 2. CCM is LRI-resident + payload-delivered, written at CONSTRUCTION not render (graduates `ccm_lri_residency_link`)
- The matrix at `*[payload+0]+0x14` is written during **payload/pipeline CONSTRUCTION inside factory
  `0x3184d0`**, and is **NOT rewritten during render** (WRITE-watchpoint on the live slot caught only
  `_platform_memset` buffer-reuse post-apply, never a matrix re-copy).
- The explicit **LRI-CCM doubles→float conversion is at `0x318dfc–0x318ea8`**: `9× movsd→cvtsd2ss→movss`
  into a contiguous float block (`rbp-0x4c0…`, 4-byte stride), sourced from a 9-double block filled by getter
  `0x264d90`, then copied by `0x33eaf0` into the payload. **BUT** that block is gated to mode `eax==2`
  (`0x318dd5 cmpl $0x2,%eax; jne`); under profile-3 four-zoom the predicate reads **`eax=0`** (runtime-verified
  at `0x318dd5`), taking the `0x318ebf` stage-builder branch (`0xc6f0`/`0xa9110`/`0x33ea90`).
- **Scoped OPEN:** the exact store that copies the per-camera CCM into `+0x14` on the *taken* `eax==0` path was
  not isolated within budget. Whether `eax` encodes "I1I2I3 vs CCM mode" and the `0x264d90` LRI key are open.

## 3. AWB reciprocal consumption (row34) — four-zoom CONFIRMED (2026-06-04, u2-render Task A)
WB = 1/gain folded into the demosaic color path, confirmed all four tiers by perturbation (overwrite the
1/R reciprocal heap copies → 0.125, re-render, decoded-pixel channel means vs same-tier baseline):
| Tier | 1/R | baseline R/G/B | perturbed R/G/B | R factor |
|---|---|---|---|---|
| 28mm | (prior) | — | — | large (R 150→249, G/B→0.06) |
| 35mm | 0.58170 | 0.1711/0.3340/0.2423 | 0.6525/0.4327/0.3039 | 3.82× R saturates |
| 70mm | 0.55163 | 0.1038/0.2039/0.1125 | 0.4520/0.2081/0.1149 | 4.35× R saturates, G/B flat |
| 150mm | 0.56702 | 0.1176/0.2371/0.1629 | 0.5342/0.2373/0.1625 | 4.54× R saturates, G/B flat |
Forcing 1/R saturates R and leaves G/B essentially unchanged ⇒ the WB reciprocal is consumed per-channel in
the demosaic/color path on every tier. The stable WB constants live at fixed low-heap addresses (the
collapse magnitude was band-width-invariant, so attribution to the WB constant is sound). The mechanism site
is the per-channel `divss` triple in `0xa9340` (`0xa9653/0xa9663/0xa9679`), reached from the CCM apply `0xa9f20`.

## Scope
Single mid-render matrix read per tier (the slot is reused — constant heap addr within a tier). Unit-1 only.
Did not census which camera index the sampled payload is, nor whether all 10–11 cameras carry distinct CCMs.
