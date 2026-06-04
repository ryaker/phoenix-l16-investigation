> GRADUATED to four-zoom OBSERVED (2026-06-03, W1b — four_zoom_data_W1b.md). B-spline=merge-interior(0x3661b0), Catmull-Rom=separate 0x3d0650 stage; both fire 4-zoom. Scope=first-hit/tier, Unit-1.

<!-- provenance: orchestrator static disasm + constant byte-decode of 0x2b2be0 and 0x36f800, 2026-06-03 -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, STATIC disasm + float constant byte-decode). Verify-before-trust
check on the handoff's resample-kernel labels ("B-spline `0x2b2be0` / Catmull-Rom `0x36f800`"). Binary:
`libcp.dylib` Mach-O x86_64.

> **CORRECTION 2026-06-03 (same day): the `0x36f800` "Catmull-Rom" REFUTATION below was MY ERROR — now
> RETRACTED. Full polynomial reconstruction proves `0x36f800` IS Catmull-Rom.** I pattern-matched raw
> constants and missed (a) the **1/6 normalization factored out** — `{9,−15,6}÷6 = {1.5,−2.5,1}` = Catmull-Rom
> piece-1 `1.5d³−2.5d²+1`; and (b) the **index-scaled linear term** `−0.375×64 = −24`. Reconstructed piece-2:
> `(−3d³+15d²−24d+12)/6 = −0.5d³+2.5d²−4d+2` = Catmull-Rom piece-2 exactly. See the corrected section at the
> bottom. **Both original handoff labels (B-spline `0x2b2be0`, Catmull-Rom `0x36f800`) are CORRECT.** Lesson:
> reconstruct the full polynomial — do NOT refute a kernel identity from raw constants without accounting for
> a factored-out normalization and unit scaling.

# Resample kernels — `0x2b2be0` = cubic B-spline CONFIRMED; `0x36f800` = Catmull-Rom CONFIRMED (refutation retracted)

## `0x2b2be0` = CUBIC B-SPLINE (CONFIRMED — handoff label correct)
Constant pool (byte-decoded from RIP-relative refs in the body): `0.166667 (=1/6)`, `3.0`, `6.0`, `-6.0`,
`4.0`, `2.0`, `1.0`, `0.015625 (=1/64)`, `-0.1875`, `0.0`. Interval tests against `1.0` and `2.0` (support
[-2,2]). These are the **textbook cubic B-spline basis**:
- `|x|∈[0,1): (1/6)(3|x|³ − 6|x|² + 4)` ⇒ coefficients {3, −6, 4} × 1/6 (all present).
- `|x|∈[1,2): (1/6)(−|x|³ + 6|x|² − 12|x| + 8) = (1/6)(2−|x|)³` ⇒ {6, 2} present.
⇒ **clean-room: Phoenix's separable resample uses the standard cubic B-spline weights — reimplementable from
the published basis (Rule #0 OK, no copied bytes).** (The `1/64`, `-0.1875` are likely a coarser/secondary
path or a fixed-fraction sub-sample table.)

## `0x36f800` = CATMULL-ROM 4-tap kernel LUT builder (CONFIRMED — full reconstruction)
`0x36f800` **precomputes a Catmull-Rom resampling-kernel lookup table** (4KB stack buffer `[rbp-0x1000]`,
`sub rsp,0x1058`, loop over integer index `ecx`). Per iteration: `t=(float)ecx`, **phase `a = t·(1/64)`**
(`xmm8=1/64`) ⇒ 64 sub-pixel phases per unit. It evaluates the SAME piecewise cubic at the **four neighbor
distances of a 4-tap interpolator** and stores 4 taps (`movaps [rax-0x30]`, `[rax-0x20]`, `[rax-0x10]`,
`[rax-0x00]`):
- tap0: `d = a+1` (`xmm0+1.0`); tap1: `d = a`; tap2: `d = 1−a` (`1.0−xmm0`); tap3: `d = 2−a`.
Each tap uses the two-piece kernel selected by `ucomiss d vs 1.0` then `vs 2.0` (value 0 for d≥2):
- **|d|<1: `(9d³ − 15d² + 6)/6` = `1.5d³ − 2.5d² + 1`** (consts `xmm11=9, xmm3=−15, xmm4=6, xmm5=1/6`).
- **1≤|d|<2: `(−3d³ + 15d² − 24d + 12)/6` = `−0.5d³ + 2.5d² − 4d + 2`** (consts `xmm14=−3, xmm15=15`; the
  linear `−24d` comes out as `xmm13·(−0.375)` = `(64a)·(−0.375)` = `−24a` plus the const `−12.0`, and since
  `d=a+1` that is exactly `−24d+12`).
Both pieces are the **Keys cubic with a=−0.5 = Catmull-Rom**, /6-normalized in the bytes. ⇒ the earlier
"refuted" verdict was wrong: the diagnostic 1.5/−2.5/−0.5/2.5/−4 ARE present once the ÷6 and the ×64 index
scaling are undone.

## `0x2b2be0` vs `0x36f800` — both are 4-tap LUT builders, different bases (clean-room)
Phoenix's separable resampler uses **two selectable 4-tap kernels**: cubic **B-spline** (`0x2b2be0`, smoothing)
and **Catmull-Rom** (`0x36f800`, interpolating), each precomputed into a 64-phase LUT. Reimplementable from
the published Keys/B-spline formulas (Rule #0 OK — no copied bytes).

## Action taken
Handoff RESAMPLE line corrected to: B-spline `0x2b2be0` + Catmull-Rom `0x36f800` both CONFIRMED (4-tap, 64-phase
LUT builders). (Earlier same-day handoff edit that called `0x36f800` "refuted/unidentified" is superseded.)

## Residuals (NEEDS_CODEX_VALIDATION)
- Which kernel is selected for which inter-level resample at runtime (B-spline vs Catmull-Rom); the IRAMP
  levels 1-4 are the resample octaves per the dispatcher finding (static-only here).
- The secondary constants in `0x2b2be0` (`1/64`, `-0.1875`) — likely its own phase-step / a derivative tap.
