<!-- provenance: l16-investigator runtime probe (1 render, 70mm) + orchestrator static re-extraction of 0x261940, 2026-06-03 -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine). (A) ordering = OBSERVED runtime; static decode of `0x261940`
orchestrator-VERIFIED. (B) LUT-identity = OPEN (honest negative, range-limited — see caveat). Upgrades the
static LEAD in `distortion_apply_stage.md` (`LensUndistortCRA 0x261940`). One render: 70mm `L16_03434.lri`
(Unit-1), profile 3.

# Lane B2 — undistort `0x261940` runs PER-RENDER BEFORE the merge; live LUT is a real (non-identity) radial curve

> ✅ **GRADUATED to four-zoom OBSERVED (2026-06-03, `four_zoom_data_W1_batch1.md`).** First-hit operands captured
> at all four tiers: scale `[+0x08/0x0c]`=1.0/1.0 all tiers; center+LUT split by **camera GROUP** — wide
> (28≡35) center 2020.0/1505.0, LUT head `1.0,1.0000052,1.0000052,1.0000051…`; tele (70≡150) center
> 2075.0/1590.0, LUT head `1.0,1.0,1.0,1.0,1.0000001…`. (Supersedes the earlier 70mm-only center 2075/1590.)
> Scope = first-hit sample/tier, Unit-1. Residual: per-camera attribution within a tier; full-LUT compare;
> Unit-2.

## (A) ORDERING — OBSERVED (upgraded from static call-graph LEAD)
In one 70mm render, BPs on `0x261940` (undistort) and `0x3661b0` (merge entry): undistort fired **25 times
before** the first merge hit (`first_u_seq=1`, `first_m_seq=26`). ⇒ **undistort precedes merge** at runtime.
Confirms the pipeline ordering `per-camera undistort → … → IRAMP merge`.
- Scope: NOT proven per-camera-attributed — `this` captured once (`0x600000008300`); the 25 hits were not
  shown to be 1-per-camera, and one-LUT-shared-vs-per-camera-LUT was not enumerated. (Residual.)

## Static decode of `0x261940` (orchestrator-VERIFIED, instruction-exact)
Leaf kernel. `rsi`=`this`; `rdx,rcx`=int pixel coords; result via `rdi`. Confirmed instructions:
- `this+0x30..` 3×3 projective matrix → perspective divide (`0x26199d divss`).
- `this+0x28/0x2c` = center (cx,cy) subtracted (`0x2619a9`/`0x2619b2`).
- `this+0x08/0x0c` = scale → radius `r=sqrt((s0·dx)²+(s1·dy)²)` (`0x2619dc sqrtss`).
- `cvttss2si` → int radius **clamped to [0,4095]**: `0x2619e4 cmp eax,0x1000; 0x2619e9 mov ecx,0xfff;
  0x2619ee cmovl` ⇒ a **~4096-entry LUT**.
- `this+0x10` = LUT base: `0x2619f4 mov rcx,[rsi+0x10]; movss (rcx,rax,4),xmm` = `float32 LUT[radius]`.
- Output `out = center + offset·LUT[r]`.

## (B) Live undistort LUT shape (runtime, one kernel object)
4096×f32 at `this+0x10`: `LUT[0]=1.0`, rises to **peak 1.001802 @ idx 1711**, crosses below 1.0 @ ~2584,
flattens to **0.999774 for idx ≥ ~2816** (tail beyond image extent). min 0.999774 / max 1.001802; 1337
entries deviate from 1.0 by >0.001; **rise-then-fall = pincushion→barrel signature**. ⇒ a **genuine radial
correction curve (±0.18%), NOT identity** — and distinct from the near-identity `+0x100` table the
merge-projection probe saw (so undistort-LUT ≠ merge-projection-transform).
- Runtime kernel fields at hit #3: scale `[1,1]`, center `[2075,1590]` px, matrix `[0.998077,~0,2.99976; ~0,
  0.998077,1.99976; …]` (near-identity affine + (3,2) offset).

## (B) LUT origin = f3.3.2.5? — OPEN; the probe's raw-scan negative is RANGE-LIMITED (NOT evidence of absence)
The probe brute-scanned `L16_03434.lri` for 101 consecutive f32 near 1.0 (and 101 (x,y) pairs): **0 hits**.
**But this does NOT refute the LRI origin**: lane-b2 (`lane-b2-lri-calibration-origins`) found f3.3.2.5 via
**proto field parsing** (`lri_field_inspect.py`), and its 101-pt y values are in **[0, 31.65] (pixel radius
units), non-monotone** — NOT ~1.0 multipliers. The probe scanned the WRONG value range (≈1.0) for that table,
so its negative is a scan-range artifact. The runtime LUT (4096× multiplier≈1.0) is plausibly **derived** from
the f3.3.2.5 radius map (convert radius-remap → per-radius multiplier, upsample 101→4096), but that derivation
is **unconfirmed**. ⇒ LUT-origin remains OPEN, not refuted.

## Clean-room relevance
Undistort = per-camera, pre-merge, pure LUT-indexed radial remap with a 3×3 projective pre-map + (cx,cy)
center + scale, 4096-entry radius LUT. Phoenix builds this LUT from the LRI Block-3 f3.3.2.5 radius map
(proto-parsed, values in px) re-expressed as a per-radius correction and upsampled — Rule #0 OK (LRI-resident).

## Residuals (NEEDS_CODEX_VALIDATION)
- Per-camera attribution of the 25 pre-merge undistort hits; one-shared-LUT vs per-camera-LUT.
- The exact f3.3.2.5 → 4096-multiplier-LUT derivation (radius-units → multiplier; 101→4096 interpolation).
- Other zooms/units (only 70mm Unit-1 here); the merge body itself not analyzed (entry only, for ordering).
