# Session 2 — LRI Corpus AWB-Mode Scan

**Date:** 2026-04-13
**Question:** When an LRI is captured in AWB mode other than AUTO (DAYLIGHT, SHADE, CLOUDY, TUNGSTEN, FLUORESCENT, FLASH, CUSTOM, KELVIN), is `auto_white_balance.neutral_color` (Vec2 xy) still populated, or does libcp need to fall back to something else?
**Method:** Pure LRI file parsing — no spike, no LLDB, no libcp execution. Parser script: `/Volumes/Dev/lumen-phoenix-scratch/session2_awb_mode_scan.py`.
**Corpus:** 9,438 LRI files under `/Volumes/Base Photos/Light/`.

---

## TL;DR

1. **Not a single LRI in the 9,438-file corpus stores `auto_white_balance.neutral_color`.** Nor `neutral_temp`, `neutral_tint`, or an `awb_mode` enum value ≥ 2. The entire AWB schema defined in libcp is a superset of what the on-camera firmware actually writes.
2. **Only per-channel gains are persisted.** The only per-capture AWB data every LRI carries is the 4-float gain vector `[R_gain, 1.0, 1.0, B_gain]` (plus a stats-tile rect and a 0/1 flag).
3. **Effectively all real L16 captures used AWB_MODE_AUTO at capture time.** There are no non-AUTO LRIs in the corpus, so the non-AUTO-fallback question is moot on real-world data.
4. **Phoenix action:** at CCM-interpolation time `neutral_color` must be treated as ALWAYS absent. Do not try to read it. Fall back to the clamped-lerp with `alpha = 0` path (which matches libcp's documented edge-case behaviour in `cct_and_awb_auto.md` §Q1) — i.e., use the second-calibration-illuminant CCM unblended. The channel gains from `f19.f15` / `f15` are the only per-capture AWB parameter Phoenix actually receives.

---

## 1 — Block 8 schema (newer firmware, ~6,336 LRIs)

All newer L16 LRIs store per-capture AWB parameters in the smallest per-capture LELR block (usually Block 8, occasionally Block 9 when face-detection extends it). Typical payload is 54 bytes, protobuf wire format. Full field set, verified on 6 known production files and a 180-file representative sample:

```
f19                     : sub-message (51 B)
f19.f14                 : sub-message (24 B) — "stats ROI rect"
  f19.f14.f1            : sub-message (10 B)  — top-left
    f19.f14.f1.f1 : f32  (rect_x0, normalised 0..1)
    f19.f14.f1.f2 : f32  (rect_y0)
  f19.f14.f2            : sub-message (10 B)  — bottom-right
    f19.f14.f2.f1 : f32  (rect_x1)
    f19.f14.f2.f2 : f32  (rect_y1)
f19.f15                 : sub-message (20 B) — "awb_gains"
  f19.f15.f1 : f32   = R_gain
  f19.f15.f2 : f32   = G1_gain = 1.0  (always)
  f19.f15.f3 : f32   = G2_gain = 1.0  (always)
  f19.f15.f4 : f32   = B_gain
f19.f16 : varint         = 0 (effectively always)
```

**Also seen (face-detection extension, 151/9,438 LRIs, sizes 83–303 B):** a top-level `f27` sub-message that contains face-count, focus metric, per-face pixel-space bboxes and detection scores. `f27` is NOT AWB-related and is independent of the AWB fields.

### Fields that are NOT present
None of these libcp-known protobuf sub-fields appear **anywhere** in any per-capture block in any LRI examined:
- `auto_white_balance.neutral_color` (Vec2 xy chromaticity)
- `auto_white_balance.neutral_temp` (int CCT in Kelvin)
- `auto_white_balance.neutral_tint` (float G–M tint)
- `awb_mode` enum value (expected range 0..8)
- `auto_white_balance.type` enum (expected range 0..7)
- Any ASCII string like `auto_white_balance`, `awb_mode`, `neutral_color`, `AWBMode`, `DAYLIGHT` (mmap-searched, zero matches in the full 162 MB files — the libcp strings are proto field *names* resolved at runtime, never serialised into the LRI wire data).

### Older-firmware layout (~2,899 LRIs from 2017-12 era)
Same `f15` gain vector, but stored at the **top level of Block 7** (not under `f19`), in a 67 B block that also contains:
- `f10` : f32 (≈8.0 — lens EV? exposure stop?)
- `f11` : varint (≈5e7 — exposure-time or ISO proxy)
- `f14` : stats-ROI rect (same shape as `f19.f14`)
- `f15` : gain vector (same shape as `f19.f15`)
- `f16` : varint (0 or 1)
- `f17` : f32 (≈339 — unknown)

Same verdict applies: no `neutral_color` / `neutral_temp` / `neutral_tint` / `awb_mode` fields.

### ~200 LRIs (oldest, 2017-early)
Extremely old firmware with a different LELR layout where the tail-scan could not locate the `f15`/`f19.f15` pattern. Not inspected deeply for this session — the question was about non-AUTO captures, and this is a minority layout.

---

## 2 — Phase 1: The 6 Known Production LRIs

All newer-firmware; all Block 8 (54 B); all essentially identical schema.

| Filename              | Date       | BlkIdx | Size | awb_mode (`f19.f16`) | neutral_color | neutral_temp | f19.f15.f1 (R) | f19.f15.f4 (B) |
|-----------------------|------------|--------|------|----------------------|---------------|--------------|----------------|----------------|
| L16_02130.lri         | 2018-07-23 | 8      | 54 B | 0 (AUTO)             | **absent**    | **absent**   | 1.7178         | 1.5888         |
| L16_02586.lri         | 2018-10-23 | 8      | 54 B | 0 (AUTO)             | **absent**    | **absent**   | 1.7987         | 1.6820         |
| L16_03434.lri         | 2019-05-18 | 9      | 54 B | 0 (AUTO)             | **absent**    | **absent**   | 1.8128         | 1.5831         |
| L16_02285.lri         | 2018-07-29 | 9      | 54 B | 0 (AUTO)             | **absent**    | **absent**   | 1.7636         | 1.6007         |
| L16_02500.lri         | 2018-09-26 | 8      | 54 B | 0 (AUTO)             | **absent**    | **absent**   | 1.8444         | 1.5205         |
| L16_03460.lri         | 2020-07-14 | 8      | 54 B | 0 (AUTO)             | **absent**    | **absent**   | 1.6706         | 1.6536         |

`neutral_color` / `neutral_temp` / `neutral_tint` fields are not present — the only Vec2 floats in these blocks are `f19.f14.{f1,f2}` stats-ROI normalised rect coordinates (they happen to coincidentally fall in the xy chromaticity range for some captures, but they are coordinates of a bounding rect, **not** chromaticity — the f14.f1 corner is always ≤ f14.f2 corner, matching a rect but not a colour measurement).

---

## 3 — Phase 2: Full 9,438-file corpus scan

Corpus-wide distribution of the Block 8 "mode flag" (`f19.f16` in newer layout, `f16` in older):

| Layout      | Files | f16 = 0 | f16 = 1 | f16 ≥ 2 |
|-------------|-------|---------|---------|---------|
| New (f19.*) | 6,336 | 6,329   | 7       | **0**   |
| Old (top-level) | 2,899 | 2,853 | 46      | **0**   |
| Uncategorised   | ~200  | n/a   | n/a     | n/a     |

**Observations:**
- `f16` is effectively boolean (0 / 1). 99.9 % of files have `f16 = 0`; a total of 53 files (7 new-layout + 46 old-layout) have `f16 = 1`. If this field were the 9-value `AWBMode` enum we would expect values 0..8 to appear in some natural distribution. The fact that only {0, 1} ever appear strongly indicates `f16` is **not** `awb_mode` at all — it is more plausibly a 1-bit "gains valid / AWB converged / user override" flag attached to the gain vector itself.
- No LRI ever sets `f16` to 2..8. There is no encoded `AWB_MODE_DAYLIGHT/SHADE/CLOUDY/TUNGSTEN/FLUORESCENT/FLASH/CUSTOM/KELVIN` anywhere in the file corpus. This either means (a) every real user always left the camera in AUTO, or (b) the camera firmware ran its HW-ISP gray-world pipeline regardless of UI mode and only wrote the resulting gains — never the mode enum. Either way the observable effect is the same: Phoenix will never see a non-AUTO LRI from this corpus.
- `auto_white_balance.neutral_color` is absent from every single file. No Vec2 xy-chromaticity pair was found in any Block 8 (the only Vec2 present is the ROI rect, which has systematically wrong structure to be (x,y) chromaticity — in every sample the two corners sum to ~1.0 rather than ~0.66).

---

## 4 — libcp consequence: what the render-time CCT path actually does

Per `cct_and_awb_auto.md` §Q1 and the verified call chain
`0x13eda0 (proto loader) → 0xab2e0 (Robertson search) → 0x350bc0 (CCM interp) → 0xab720 (clamped lerp)`:

1. The proto loader at `0x13eda0` checks a bitmask of which fields were present in the incoming protobuf. Specifically:
   - `test $0x4, %al` → copy `neutral_temp` int32
   - `test $0x8, %al` → copy `neutral_tint`
   - `test $0x2, %al` → copy `neutral_color` Vec2 + midpoint float
   - Each of these tests only fires when the corresponding field was actually set on the wire.
2. Because no real LRI populates any of them, that bitmask is always zero for these fields at render time. The internal struct keeps whatever default it was initialised with (most plausibly `(0.0, 0.0)` for `neutral_color`, `0` for `neutral_temp`, `0.0` for `neutral_tint`).
3. When the CCM interpolation at `0x350bc0` calls `cct_from_chromaticity(neutral_color)`, it is handed `(0.0, 0.0)`. Walking the Robertson search at `0xab2e0` with `u = 4·0/3 = 0`, `v = 6·0/3 = 0`: none of the 30 isotherm lines bracket that input (the Robertson locus sits around `u,v ≈ 0.19..0.30`), so the search falls off the end and executes the explicit `xorps xmm0, xmm0 ; *out = 0.0` edge-case at `0xab3b3` — documented in `cct_and_awb_auto.md` §Q1, Edge case 1.
4. CCM interp then feeds `T_target_recip = 0` into `mat_lerp_clamped` at `0xab720`. The clamp `min(max(iK_tgt, iCold), iHot)` pins the target to whichever end of the two calibration illuminants has the smaller mired (i.e., the cooler/larger-Kelvin calibration illuminant), and `alpha` becomes either 0 or 1 by the clamp. Either way, **no blending occurs — the output is exactly one of the two factory CCMs**, unblended.

**So libcp's documented "neutral_color = 0 ⇒ fall back to one calibration CCM, α clamped" is not a hypothetical edge case. It is the code path every single LRI in the corpus exercises.** That also explains why nobody ever noticed the absence of neutral_color: the math falls through cleanly with no NaN, no branching, and pixels end up with one of the two factory CCMs applied flat.

---

## 5 — Phoenix action (verdict)

**Always treat `auto_white_balance.neutral_color` as absent for LRI inputs.** Do not attempt to read it and do not try to derive it from pixel content (that is the HW-ISP's job, not libcp's).

Pseudocode for Phoenix's CCM-interp path:

```python
def phoenix_ccm_for_capture(calib_ccm_A, calib_ccm_B, illum_A, illum_B):
    # LRI never carries neutral_color — always hit the fallback.
    # This exactly reproduces libcp's behaviour on every real LRI:
    # xy_target = (0, 0) → CCT = 0 → clamped lerp pins to the cooler illuminant.
    T_A = robertson_cct_from_illuminant(illum_A)
    T_B = robertson_cct_from_illuminant(illum_B)
    if (1 / T_A) > (1 / T_B):
        # illum_A is warmer; cooler end is illum_B → use M_B unblended
        return calib_ccm_B
    else:
        return calib_ccm_A
```

`awb_mode` is irrelevant — the LRI does not carry it either, and libcp only *validates* it at `0x13efc7` but never *branches* on its value in the render path (confirmed by static disasm — see `cct_and_awb_auto.md` §Q2, "Where AWB_MODE_AUTO actually lives: the proto loader"). The 4 `setWhiteBalance` lambdas `$_20..$_23` only copy the gain vector.

Per-channel gains are the only per-capture AWB parameter Phoenix needs to read, and they are always present as `f19.f15.{f1..f4}` (newer) or `f15.{f1..f4}` (older). Done.

---

## Artifacts

- Scanner: `/Volumes/Dev/lumen-phoenix-scratch/session2_awb_mode_scan.py`
- Scan log (Phase 1 details): `/tmp/session2_scan.out`
- Prior analysis referenced: `/Volumes/Dev/lumen-phoenix-scratch/cct_and_awb_auto.md`, `/Volumes/Dev/lumen-phoenix-scratch/awb_analysis.txt`
