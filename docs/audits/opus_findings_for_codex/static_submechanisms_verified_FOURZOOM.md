<!-- GRADUATED finding. provenance: orchestrator-directed independent deterministic re-extraction (bbatch-disasm adaef6ffa42306728) from libcp.dylib sha256 b38dc4b3, 2026-06-04. Consolidates 13 lane-A/D/E/B2/C6 static sub-mechanism staging docs whose four-zoom-equivalent rigor = byte-exact re-disassembly (zoom-invariant code/rodata). -->
**Status:** NEEDS_CODEX_VALIDATION — **GRADUATED to STATIC-DETERMINISTIC verified** (Tier 1). Each claim
below was **independently re-extracted instruction-for-instruction at the cited VA and byte-exact for every
rodata constant**, straight from `libcp.dylib` (sha256 `b38dc4b3…`, `__TEXT` vmaddr=0 ⇒ fileVA==fileoffset),
NOT from the staging doc's prose. These are pure code/rodata facts — **identical regardless of which LRI
renders**, so deterministic re-extraction IS the four-zoom-equivalent rigor (same precedent as
`lri_calibration_parser_FOURZOOM`, which graduated on deterministic four-LRI re-parse). All 13 = **PASS**.

# Static sub-mechanisms — byte-verified (libcp `b38dc4b3`)

## Merge interior / src boxing
- **src2 box `0x366900–0x36695a` + callback `0x374ac0`** (staging: `src2_box_role`, `src2_callback_374ac0`)
  — src2 (`0x366915 movq 0x10(%r15),%rsi`) drives an in-place **margin zero-fill** in `0x374ac0`
  (`__bzero 0x555eb2` ×4: TOP `0x374d76`, LEFT `0x374e79/0x374e9f`, RIGHT `0x374f39`, BOTTOM `0x374fc6`),
  via a std::function sink (`0x374ce5 movq 0x30(%rax); 0x374cf1 callq *%rax`). The box is **dead in
  `0x3661b0`** (its only post-call read `-0x17b8` was zeroed by the `0x366907 movaps→-0x17c0` store).

## Resample APPLY (Q16.16, 64-phase, separable 4-tap)
- **`0x2b3208 cvttsd2si` … `0x2b3398 shrl $0xa; andl $0x3f` (64-phase) … `0x2b3410 mulps;…;0x2b3432 addps;
  0x2b3435 movaps→(%rdx)`** (staging: `apply_structure`). Phase scale const `0x5abed8 = double 65536.0`
  (Q16.16). 4-tap MAC confirmed.

## Guided detail-transfer (bounded injection)
- **`0x36abf0–0x36ac15`** (staging: `guided_detail_transfer`):
  `out = (B+C) + clamp((A−B)·2·C.lane3, −0.1, +0.1)`. Constants byte-verified: `0x5a887c=2.0`,
  `0x5fdbc0=−0.1` (maxps), `0x5cbf70=+0.1` (minps); `0x36abff shufps $0xff` = C.lane3.

## Score closed form (cs-SSIM × wavelet, geometric mean)
- **q1 `0x36cea6–0x36cf24`** (staging: `closed_form_stage1`): SSIM-cs term
  `clamp((μ·(2σ_AB+0.03)/(σ²_A+σ²_B+0.03) − 0.8)/0.19, 0, 1)`. Constants: `0x5fdc50={0.01,0.03,0.03,1.0}`,
  `0x5fdc60={−0.8,…}`, `0x5fdc70={5.263…,1.0}`, `0x5cbfc0=1/256`, `0x5a8920=1.0`. (`rcpps 0x36cefd` = the
  divide.)
- **q2 `0x371730` (+`0x371a90`)** (staging: `closed_form_stage2`): wavelet-domain statistic, coeff
  `0x5cbfe0 = 3.1722686290740967`. Final `0x36e511 mulss; 0x36e515 sqrtss` ⇒ **score = √(q1·q2)** (only
  sqrtss in the fn).
- **dyadic scales `0x5fdb10` = {−0.00520833,−0.01041667,−0.02083333,−0.04166667}** = strict **1:2:4:8**
  (staging: `score_completion_kraw_scales`); reduction `0x36e3c4–0x36e471` accumulates ALL FOUR slots
  (`0x2580/0x2590/0x25a0/0x25b0(%r12)`, none discarded); K added **RAW** (`addps 0x5fdc50`, no preceding
  square — refutes (K·L)²).

## CCM apply sites (static)
- **4×4 apply `0xbfa20`** (`0xbfa47 movq 0x8(%rdi)` matrix ptr; 4 movups rows; pixel loop `0xbfad0`
  shufps $0/$0x55/$0xaa/$0xff + 3 addps) and **3×3 `0x300980`** (4-pixel SoA path) (staging:
  `ccm_apply_site_static`). **Byte-search of the D50 CCM row-sum constants `0.9642` and `0.8252` = 0 hits**
  (f32 and f64) ⇒ those row-sums are NOT embedded constants (they're LRI-derived / computed). (`1.0` f32 =
  5627 hits — ubiquitous, non-discriminating.) The runtime identity of `0xbfa20` = fixed I1I2I3, see
  `merge_magnitudes_FOURZOOM`.

## Undistort kernel (pure-LUT radial)
- **`0x261940` LensUndistortCRA** (staging: `distortion_apply_stage`): ONE `0x2619dc sqrtss`, ONE LUT load
  `0x2619f8 movss (%rcx,%rax,4)`, clamp `[0,0xfff]` (`0x2619e4 cmpl $0x1000; movl $0xfff`), TWO muls (x,y).
  **No Horner polynomial** — pure 4096-entry LUT. Affine(0x30..0x4c)→divide→sub principal-pt(0x28/0x2c)→
  focal(0x8/0xc). (Per-camera/PRE-merge ordering = call-graph LEAD, render-owed, not a static-bytes claim.)

## Acceptance / lane-D
- **`0xe6ba0–0xe6c0b` = keyed SELECT-ONE lookup, NOT an accumulator** (staging: `e6ba0_not_accumulator`):
  vector walk `0xe6bd0 callq 0xf3320`(cmp keyA) / `0xe6be0 callq 0xf2720`(cmp keyB); **0 FP-arith ops**
  (mulss/addss/divss/subss + packed forms all = 0 in range) — only the `xorps` zero-fill idiom.
- **`0x218b30` statistics reducer** (staging: `final_acceptance_filter`): per-pair guards
  `0x218bc0 ucomiss;jae` (x) + `0x218bd0 ucomiss;jbe` (y); accumulates clamped-score sum
  (`0x218ca4 addss`, minss-clamped) + threshold-exceed count (`0x218c99 seta; 0x218cab addl`) + accept count
  (`0x218cae incl`); epilogue `0x218ceb divss`(1/(n+eps)) → exceed-fraction `→(%r14)` + mean (`0x218d00
  mulss`) returned. Caller skip-guard `0x2170d1 cmpl $0x8; jl` (**<8 positive pairs → skip merge body**).

## Lane-E level dispatcher
- **dispatcher `0x3ec9dc`** (staging: `level_dispatcher_topology`): `movl 0x18(%rax)` level →
  `leal -0x2; cmpl $0x3; jae → 0x3d0650` (**L2-4**); else `testl; je → 0x3ec770` (**L0 merge**);
  `cmpl $0x1; jne err else → 0x3ebb80` (**L1 resample**). Vtable `0x65f5e0 + 0x30 = 0x3ec960` (byte-read).

## Lane-C6 key-15 / group-type-2 (static half)
- **`0xf6c60`** (staging: `c6_grouptype2_survival`): `cmpl $0xf; ja` abort; `movl $0xfc00; btl %esi; jb →
  movl $0x2,(%rdi)` (bits 10–15 + key-15 → type-2). **`0xf2720` = `movl 0x60(%rdi); ret`**; **`0xe6cf0` =
  `movl 0x44(%rdi); ret` (CONTAINER +0x44 reader)**. Clear chain `0x3c907d callq 0xe6cf0 → 0x3c9087 callq
  0xf6c60 → 0x3c908c cmpl $0x2,-0x118; je` (container-type-2 SKIPS clear) else `0x3c9098 callq 0xf2720; …;
  0x3c90a5 movb $0x0,0x30(%rax)`. Clear-guard keys on **CONTAINER +0x44, not the item key** — confirmed.
  Census: **exactly 58 `callq 0xf2720` sites** (objdump count). (The runtime +0x44 *value* is render-owed.)

## Scope
Static code/rodata only (deterministic, zoom-invariant). Runtime-ordering sub-claims that some docs also
carry (per-camera/PRE-merge for undistort; the C6 +0x44 runtime value) are explicitly **render-owed** and
NOT graduated here. Binary-specific to `b38dc4b3`; re-verify VAs if the dylib is swapped.
