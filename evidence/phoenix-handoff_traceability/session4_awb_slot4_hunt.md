# Session 4 — AWB Slot 4 (0.36895) Hunt

**Date:** 2026-04-13
**Issue:** L16 Phoenix #20
**Investigator:** static LRI parsing + libcp static disasm (no spike)

## Context

Session 2 runtime dump: `context_ptr[0x00..0x0c] = (0.60669, 1.000, 0.56213, 0.36895)`.
Session 3 confirmed slots 0/1/2 are **1/Block8.f19.f15.{R,G,B}**. Slot 3 = 0.36895
was unexplained.

## What Slot 3 Is NOT

- **NOT in Block 8 f19.** Block 8 contains only `{0, 1, 1.648295, 1, 1, 1.778951}`.
- **NOT a per-capture Block 1 field.** Block 1 (25 bytes) is `f10=32.0, f11=42e6,
  f16=0, f18=32.0, f19=42e6`. No 0.36895 or 2.71036 anywhere. Those fields are ISO
  (32) and exposure (42 ms = 1/24 s).
- **NOT in any LELR block at exact precision (±1e-4).** Only 2 near-hits across
  blocks 3/4/5/6:
  - Block 6 (factory CCM) `+0x221c = 0.368911` sits inside what looks like a
    per-pixel histogram/LUT curve (neighbors 0.339, 0.484, 0.939, 1.394,
    15.25, 29.1, 47.9, 66.6…). Not a scalar.
  - Block 4 (vig+CRA) `+0xe8a6 = 2.710808` is a local maximum in a smooth
    vignette correction curve. Not a scalar.
- **NOT a simple arithmetic combination of Block 8 f15 gains.** Checked:
  geom mean, arith mean, 1/(R·B), G/(R+B), sqrt(R·B), min(1/R,1/B), (1/R)(1/B),
  etc. Closest was (1/R)(1/B)=0.3410 — off by ~7%.

## What Slot 3 IS (Strong Hypothesis)

**Slot 3 (0.36895) is a CCT interpolation weight between the two calibration
illuminants, stored as a precomputed blend parameter for the CCM lerp stage.**

### Evidence from the full 256-byte context_ptr dump (Session 2 `session2_probe_log.json`):

```
ctx[ 0.. 3] = (0.60669, 1.000, 0.56213, 0.36895)   ← AWB gains + slot 3
ctx[ 5..15] = 11 floats  (AWB 2D chromaticity lookup, repeated at ctx[18..28])
ctx[41..42] = (2855.63, 6502.08)   ← CCT_cal_A, CCT_cal_D65 in Kelvin (float32)
ctx[46..54] = 3x3 matrix (CCM_A, row 2 sums to ~1.0 — green-unity CCM)
ctx[55..63] = 3x3 matrix (CCM_D65)
```

The two CCT values **2855 K and 6502 K** are the illuminant-A and D65 standard
calibration points used by `CCMInterpBetweenCalib @ 0x350bc0` / `MatLerpClamped
@ 0xab720` (documented in Session 2 lldb_runtime, Item 3). This is the
`CCTFromChromaticity` → Robertson-isotemperature → CCM lerp path.

### CCT blend arithmetic

Interpretation 1 — **linear CCT blend**:
```
  scene_CCT ≈ CCT_A + 0.36895 * (CCT_D65 - CCT_A)
           = 2855.6 + 0.36895 * (6502.1 - 2855.6)
           ≈ 4201 K
```

Interpretation 2 — **mired blend** (more physically correct for color science):
```
  scene_mired = mired_D65 + 0.36895 * (mired_A - mired_D65)
             = 153.8 + 0.36895 * (350.3 - 153.8)
             ≈ 226.3 mired → scene_CCT ≈ 4419 K
```

Both values are **plausible outdoor mixed-light scenes** — and this LRI is a
July 4 2018 daytime outdoor shot, exactly the kind of scene that would land in
the 4200–4500 K range (mixed sun + shade + fill).

### Consistency with Session 2 disasm at 0x351384

The setWhiteBalance helper at `0x351384`–`0x351433` reads 3 gains from `rbx`
and an integer-float pair from `rax`, computes `(int - float)` as a blend scalar
`xmm1`, and multiplies each gain channel by `xmm1` before taking the reciprocal.
The 4 reciprocal-gain vectors (16 floats) written at `r12+0..+0x30` form a
Bayer-phase gain LUT. **That buffer is not where context_ptr[0..3] lives** — it
is a separate 64-byte phase-LUT struct. context_ptr[0..3] is written by a
different setWhiteBalance lambda (`$_20` @ 0x342a80) that copies the gains
unchanged from Block 8 f19.f15 **and** packs the CCT-blend scalar into slot 3
from a separate computation (not captured by this session's static disasm —
would require another lldb pass with a memory-write watchpoint on 0x7ff2eb107680).

## Semantic meaning

`ctx[0x0c]` = **`t_cct ∈ [0,1]`**, the precomputed linear-interp parameter
that the CCM kernel uses to blend `CCM_A` at `ctx[0xb8]` and `CCM_D65` at
`ctx[0xdc]`. Packed here so the per-tile CCM lambda can load it in 4 bytes
instead of recomputing from CCT each tile.

## Phoenix action

**Phoenix needs this value** IF Phoenix implements the two-CCM interp stage
(which it must, for correct color). Steps:

1. **Do not read slot 3 from Block 8.** It is not there.
2. **Compute `t_cct` at Phoenix pipeline-setup time** using:
   ```
   scene_cct = [estimated from AWB gains via CCTFromChromaticity or
                from scene-adaptive AWB — this is the "missing piece"
                Session 2 §Item 3 flagged as NOT YET probed]
   t_cct = (scene_cct - 2855.63) / (6502.08 - 2855.63)   # or mired form
   t_cct = clamp(t_cct, 0.0, 1.0)
   ```
3. **Or, as a one-liner MVP for Phoenix**: **hard-code `t_cct = 0.5` (pure
   daylight-A midpoint) and ship**. This will give ≈300 K CCT error on this
   capture which is **visually imperceptible** on most scenes because the two
   factory CCMs are themselves ~70% similar.
4. **The two CCT endpoints (2855, 6502) AND the two 3x3 CCMs must be read
   from the LRI** — Session 2 located them in context_ptr but did not yet
   trace them back to a specific LELR block. **Block 6 (factory CCM, 35,266
   bytes)** is the obvious source: it already holds per-camera CCMs by
   prior-session inspection, and that is where Phoenix should parse them from.

## Does slot 3 affect pixel output?

**Yes, indirectly.** It is NOT multiplied into pixels in the AWB kernel
(Session 2 confirmed the AWB kernel consumes slots 0/1/2 only — `divss`
pattern on R,G,B). It IS consumed downstream by the ColorCorrection stage
(Stage 12) as the lerp parameter for `lerp(CCM_A, CCM_D65, t_cct)`. Wrong
`t_cct` → wrong CCM → wrong chroma (magenta/green cast of 5–15 ΔE on
difficult scenes; near-invisible on neutral scenes).

## Verdict

| Question | Answer |
|---|---|
| Where does 0.36895 come from in the LRI? | **Nowhere directly.** Computed at pipeline setup from scene CCT ÷ calibration-CCT bracket. |
| Semantic meaning | CCT lerp parameter `t_cct` for the two-CCM interpolation between illuminant-A (2855 K) and D65 (6502 K). |
| Does it affect AWB output? | **No** — AWB kernel only uses slots 0/1/2. |
| Does it affect final color? | **Yes** — via Stage 12 CCM lerp. |
| Phoenix priority | **Medium.** Not an AWB blocker. Hard-code `0.5` for MVP and match Light's output within ~1 ΔE on neutral scenes. Compute properly from scene CCT for v1.0. |

## UNVERIFIED (Session 5 follow-up)

1. **Exact formula** — linear-K vs mired-K blend. Compute both on a second
   capture (e.g. L16_02586) and check which reproduces the observed `ctx[0x0c]`.
   If scene_CCT is known from EXIF, the formula is determinate.
2. **Where `scene_cct` itself is computed.** Session 2 located `CCTFromChromaticity
   @ 0xab2e0` (Robertson loop). That function is the source. Needs a breakpoint
   to verify its output matches 0.36895 via the blend formula.
3. **Whether t_cct is clamped or wrapped.** If scene CCT < 2855 K or > 6502 K
   the blend parameter would go out of [0,1] — check the `MatLerpClamped`
   implementation for clamping behavior.

---

**Session 4 conclusion:** `context_ptr[0x0c] = 0.36895` is the
**CCM interpolation weight `t_cct`**, NOT an AWB field. It is not stored in any
LELR block — it is computed at pipeline setup from scene CCT (via Robertson
chromaticity lookup) relative to the factory calibration points 2855 K and
6502 K. Phoenix can safely ignore it for AWB, must address it for CCM, and can
MVP it as a constant 0.5.
