<!-- provenance: l16-investigator finder (static disasm) + orchestrator instruction/constant re-extraction, 2026-06-03 -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine; finder + orchestrator-verified — every cited instruction +
constant re-extracted). Decodes the depth/stereo COST MATH (was a bare bookmark; now a mechanism). Binary
`libcp.dylib` x86_64. This is the multi-view depth-estimation algorithm Lumen uses; a clean-room
reimplementation reproduces it from this decode.

# Stereo cost math — weighted truncated-L1 multi-view photo-consistency (DECODED)

> ⚠ **W0 four-zoom CORRECTION (2026-06-03, `four_zoom_firing_census_W0.md`):** the `0x2730c0` driver below is
> **DORMANT at runtime** (0 hits, all four tiers) — its "records>3 → calls `0x2732f0`" topology is NOT the
> live bridge-HDR path. The `0x2730c0→0x2732f0` edge exists statically (`0x273103`) but never fires. The cost
> body `0x2732f0` IS live (fires 4-zoom via `runPass 0x276790`; other static callers `0x272ca9`/`0x2773dc`/
> `0x278a57`, `0x2773dc` in the runPass region). **The cost MATH below stands; the driver/gating section (§
> "Multi-pass topology") is corrected — the live caller chain is runPass, not the driver.** W1 must capture it.

## Cost metric (OBSERVED, `0x2732f0`, per-depth-hypothesis kernel)
For a candidate depth scalar `s` (= `[r13+4*i]`, per-pixel), project the reference pixel into each enabled
source camera via that camera's 80-byte record (a 3×4 projection matrix), bilinear-sample the camera image,
and accumulate a capped absolute-difference cost across ALL N source cameras:

1. **Projection** (`0x2733cc..0x273442`): `v = M0·(s·[rdi+0x20]·M48) + M1·(s·[rdi+0x24]·M4c) + M2·s + M3`
   (4-wide homogeneous); `w = 1.0/v.z` (`1.0`@`0x5a8128`); `u' = v.x·w + 0.25`, `v' = v.y·w + 0.25`
   (`0.25`@`0x5a8200` = sampling bias).
2. **Bilinear fetch + clamp** (`0x273447..0x2734f4`): clamp `(u',v')` to `[1,W-3]×[1,H-3]`; gather 4 neighbor
   rows; `pavgb` sub-pixel bilinear blends (fraction = low bit of `2u'`,`2v'`).
3. **Cost = capped L1** (OBSERVED `0x2735ce..0x27365c`): `d = |sample − ref|` via `pmaxub;pminub;psubb`;
   `d = min(d, ceiling)` via `pminub xmm,xmm13` (per-tile robust **truncation cap**); widen `pmovzxbw` +
   **saturating accumulate** `paddusw`. Done over **4 directional reference patches** (`[rdi+0x40..0x70]`).
   ⇒ a **truncated (robust) L1 / SAD-family** photo-consistency residual — NOT NCC, NOT census, NOT SSD
   (all three explicitly refuted: no product-correlation/mean-subtraction, no xor+popcnt, no squaring).
4. **Per-camera weight + fixed-point reduce** (OBSERVED `0x273666..0x2736a9`): `cost·weight` (`pmullw`/
   `pmulhuw` → 32-bit), `(·+16)>>5` (round-divide by 32; `16`@`0x5dadd0`), `min(·, 65535)` (`65535.0`@
   `0x5a8864`), then **`add word ptr [accumulator], cost` — summed across all N camera records** into one
   16-bit cost. `weight` = per-camera uint16 `[rcx+8·idx]` (visibility/confidence; source not decoded).
5. **Second accumulator + consistency check** (OBSERVED `0x2736bf..0x273a78`, gated `rdx≥2`): the same cost
   into a 2nd accumulator, gated by a **re-projection coordinate match** (`setne`/`cmp` `0x2737e4..0x27381d`)
   = a left-right / forward-backward **consistency check**.

## Per-tile state builder (OBSERVED, `0x275630`)
Builds: the residual **clamp ceiling** `xmm13` (`packuswb` `0x275683`); per-camera `(x+1,y+1,x-2,y-2)` sample
bbox (`paddd [0x5dade0]` = `(1,1,-2,-2)`); fixed-point sample LUT via `divps [0x5dadf0]={8160,8160,8160,8160}`
(**8160 = 255·32**, tying the byte residual range to the `>>5` divide). Projection/rectification setup — does
NOT reduce N→1.

## Multi-pass topology (OBSERVED)
- `0x2730c0` driver: `records = vecbytes>>4`; `imul eax,ecx,0xcccccccd; cmp eax,3; jg` ⇒ **if >3 source
  cameras enabled, run the `0x2732f0` accumulator pass**, then a 2nd per-camera refinement pass (`0x275c70`).
- `runPass(int)` `0x276790` dispatches on layer `+0xc` (vtable `+0xb0` → `call [rax+0x30]`); `cmp [rbx+0xc],8`
  selects heavy build `0x276860` vs `0x277e70`. Heavy path builds the source-record vector gated by a
  per-camera **enable mask** (`0x276977`) — ties to guard "no lower src cams are enabled. cannot compute
  depth" (`0x6325fd`). Coarse-to-fine is layer-field driven, not an internal pyramid loop.

## Decoded constants (all byte-verified — RE facts for clean-room reimplementation)
`1.0`@`0x5a8128` (1/w); `0.25`@`0x5a8200` (uv sample bias); `65535.0`@`0x5a8864` (per-camera cost ceiling);
`16`(int)@`0x5dadd0` (round bias for `>>5`); `(1,1,-2,-2)`@`0x5dade0` (sample-bbox offsets); `8160.0`(=255·32)
@`0x5dadf0` (fixed-point scale); `(3.0,0.0625,8.0,10.0)`@`0x5a9b04` (runPass per-camera scalar select — role
INFERRED).

## Clean-room summary (reimplementable algorithm)
Plane-sweep multi-view stereo: for each candidate depth `s`, warp the reference pixel into each enabled source
camera (per-camera 3×4 projection), bilinear-sample, compute robust truncated-L1 photo-consistency over a
4-patch neighborhood in decorrelated bytes, weight per camera, sum across cameras (fixed-point `(Σ·w+16)/32`,
cap 65535); maintain a consistency-checked second cost; the depth winner is chosen by the caller.

## Residuals (NEEDS_CODEX_VALIDATION / next pass)
- The **outer plane-sweep**: candidate-depth search range + step (the caller that fills the `s` array `[r13]`)
  — NOT in these bodies (no `phminposuw`/`minps`-argmin here = OBSERVED-absent).
- The **argmin + sub-pixel depth refine** that turns the cost accumulators into the index-5 descriptor `+0x2a8`
  depth value (in the caller of `0x2730c0`).
- Per-camera uint16 **weight** source/semantics; whether the consistency accumulator drives rejection vs blend.
- compute() sibling `0x2727f0` and guided-upsample `0x29ed90` math not decoded here.
