<!-- provenance: l16-investigator runtime W1 data sweep (ac6aa14ca26828b46), stampede-free first-hit capture, 2026-06-03 -->
**Status:** NEEDS_CODEX_VALIDATION. **W1 = four-zoom OPERAND data (the graduation pass).** Method: stampede-free
first-hit capture (BP one stage, read operands at first stop, kill) — 16/16 (stage,tier) cells hit, zero
misses. Scope = **first-hit sample**, one launch per (stage,tier), Unit-1, profile 3, --export-fmt 3. Confidence
= Verified for the captured first-hit operands; NOT extrapolated to all invocations.

# W1 batch 1 — per-tier operand data + corrections

## F1 — merge score `0x36cde0` (fires 4-zoom). Formula re-confirmed `sqrt(xmm0·xmm1)` at `0x36e511`.
Patches are f32 arrays (4/elem). **First-hit score = 0.0 (degenerate) at ALL tiers** — the first contributor
pairs against a boundary/zero patch. ⇒ formula + four-zoom firing CONFIRMED; **per-tier score MAGNITUDE NOT
captured** (needs a skip-degenerate-hits pass = a deeper W-pass). Stays STAGING (magnitude owed).

## F2 — CCM apply `0xbfa20` (fires 4-zoom) — MAJOR CORRECTION
First-hit matrix at `[rdi+0x8]`, **byte-identical 28/35/70/150**:
```
0.57735 0.57735 0.57735 0   (1/√3 luma)
0.70711 0       -0.70711 0  (1/√2)
0.40825 -0.81650 0.40825 0  (1/√6)
0   0   0   1
```
= the **fixed I1I2I3 / Ohta decorrelation basis** (4×4-embedded), constant across tiers. ⇒ **`0xbfa20` is a
GENERIC 4×4 color-matrix apply; its FIRST runtime use applies the constant I1I2I3 rotation, NOT a per-camera
CCM.** Corrects `ccm_apply_site_located.md` (which called `0xbfa20` "the per-camera CCM apply site"). The
static `setColorCorrection $_58 → 0xa9f20 → 0xbfa20` matrix=BayerPayload+0x14 chain is a real CALLER edge but
is NOT the first-hit invocation and is **unconfirmed at runtime**. Open: does a LATER `0xbfa20` hit apply a
per-camera CCM? (needs skip-first-hits pass.) CCM packet stays STAGING, corrected.

## F3 — stereo cost `0x2732f0` (fires 4-zoom) — GRADUATES (structure 4-zoom-confirmed)
- **Live caller = `0x276860` (runPass family) at every tier; dormant driver `0x2730c0` ruled out** (confirms W0).
  Chain `0x2732f0 ← 0x276860 ← 0x6090 ← 0x4de0`.
- **Layout correction:** record vector is DOUBLE-indirect — `vecobj=[rdi+0x10]; begin=[vecobj]; end=[vecobj+8]`;
  stride **0x50=80** (confirmed `lea (rdx,rdx,4); shl 4` = rdx·80). (My static packet's direct `[rdi+0x10]`
  read was off by one indirection.)
- **Record N = 4 at ALL tiers** (the 5+5+6 camera split does NOT appear here). Per-tier variation is the
  disparity search grid `[rdi+0x18]`: **188 (28/35) → 368 (70/150)** = wide vs tele group. The 80-byte records
  are per-camera near-identity affine/homography (e.g. 28mm rec0 rot [0.9998,0.0061;-0.0115,0.9988], trans
  45.8/11.05, scale ~1.0).

## F4 — undistort `0x261940` (fires 4-zoom) — GRADUATES
`this`=rsi; scale `[+0x08/0x0c]`=**1.0/1.0** all tiers. Center + LUT split by **camera GROUP, not per tier**:
| group | tiers | center `[+0x28]/[+0x2c]` | LUT head `*[+0x10]` |
|---|---|---|---|
| wide | 28, 35 | 2020.0 / 1505.0 | 1.0, 1.0000052, 1.0000052, 1.0000051… |
| tele | 70, 150 | 2075.0 / 1590.0 | 1.0, 1.0, 1.0, 1.0, 1.0000001… |
⇒ 28≡35 and 70≡150; consistent with wide-camera vs tele-camera distortion calibration. (Earlier packet had
70mm-only center 2075,1590; now the wide-group center 2020,1505 is added.)

## Graduations from this batch (→ findings_for_codex)
- `undistort_ordering_lut_runtime.md` (now four-zoom first-hit data; camera-group split).
- `stereo_cost_math_decoded.md` (math static + caller/N/record-layout four-zoom-confirmed; magnitude/cost-values
  + skip-degenerate still residual, scoped).
Both graduate with explicit **first-hit-sample** scope. NOT graduated: CCM (corrected, per-camera question
reopened), merge score (formula+firing only, magnitude degenerate).

## Custody TODO
W1 harness lived in `/tmp` (scratch). Port a durable version to `tools/lldb_probes/four_zoom_firsthit/` (method
in KMS + W0 doc): stampede-free = BP one stage, read operands at first stop, `process kill`.
