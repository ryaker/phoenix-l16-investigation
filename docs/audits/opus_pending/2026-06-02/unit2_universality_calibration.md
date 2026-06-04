<!-- provenance: l16-investigator Unit-2 re-parse (a4fafc8e77f16a4a9) + orchestrator verify (vignetting sha, twin focal), 2026-06-03 -->
**Status:** NEEDS_CODEX_VALIDATION. Tests the graduated Unit-1 calibration findings on the **Unit-2** body.
Deterministic LRI parse, no render. Verdict: **calibration STRUCTURE is cross-unit universal; VALUES are
per-body** (Unit-1 `722a6e72…` ≠ Unit-2 `223961c6…` intrinsics sha = the CLAUDE.md body hashes).

# Unit-2 universality — calibration structure CONFIRMED cross-unit; values per-body

## Structure holds on Unit-2 (all 4 Unit-2 LRIs) — can drop "Unit-1 only" for STRUCTURE
Block count split (11 wide / 12 tele) ✓; intrinsics 5+5+6 + fx nesting ✓; distortion pure-radial (p1=p2=0
all 16) + 3 optical groups by (k1,k2,k3) ✓; Block-6 42 records + excluded {1,15} + CCM + spectral 3×76 ✓;
AWB f19 ✓; depth no-LRI-origin (LightHeader f13 absent, 0 stereo proto) ✓; LightHeader f4/f5 schema ✓.

## Values are per-body (keep value-level Unit-1 caveat on any numeric calibration)
Per-body (DIFFER U1 vs U2): fx (cam0 3375.9→3372.5, cam10 18794.7→18684.4), CCM matrix entries (row1
[0.8996,0.1317,-0.0671]→[0.9073,0.119,-0.062]), distortion k1/k2/k3 (cam0 [0.0326,0.1501,-0.5774]→
[0.0331,0.1495,-0.5693]), LUT point counts, lens-shading content (sha differ). Block sizes +1 byte on U2
(intrinsics 32832→32833, lens-shading 262968→262969) = per-body size delta. ⇒ **any doc quoting specific
numeric calibration values must scope them Unit-1 (or Unit-2)** — they are body-specific.

## NEW cross-unit INVARIANTS (structural constants, both bodies)
1. **CCM row-sums [0.9642, 1.0, 0.8252]** — byte-identical both bodies, all tiers (a color-model normalization
   property, NOT a per-unit value).
2. **Block-5 vignetting (1786 B) is BYTE-IDENTICAL cross-unit** (sha `37a0a85e` both — orchestrator-verified)
   ⇒ vignetting is a **shared/firmware-constant table, NOT per-body** (unlike every other calib block). Anomaly
   worth its own check; clean-room can treat vignetting as a model constant, not a per-unit parse.

## DATA CORRECTION — the documented Unit-2 "twins" are NOT a clean 28/35/70/150 ladder
LightHeader f4 (orchestrator-verified): 28mm `2018-07-04/L16_02130` f4=28 ✓; **"35mm" `2018-10-28/L16_03041`
f4=74 (70mm-tier, NOT 35mm)**; **"70mm" `2020-07-14/L16_03434` f4=149 (150mm-tier, NOT 70mm)**; "150mm"
`2018-07-07/L16_02285` f4=149. ⇒ the Unit-2 same-name files are really **(28, 70, 150, 150)**. This does NOT
affect calibration universality (per-camera blocks are full 16-cam tables independent of shot focal), BUT the
CLAUDE.md corpus note's Unit-2 twin focal mapping is WRONG and Lane B must not treat the U2 35/70 twins as true
35/70mm captures. ⚠ FLAG for Codex/Rich (CLAUDE.md is main-tree; not edited from quarantine).

## Effect on graduated docs
- The consolidated `lri_calibration_parser_FOURZOOM.md` is upgraded: **STRUCTURE = cross-unit (Unit-1+Unit-2);
  VALUES = per-body**. The "Unit-2 untested" residual is RESOLVED for structure (kept for values).
- INCONCLUSIVE: lens-shading {1,15}-identity (W3b) not reproduced on U2 — parse-resolution (extractor grabbed
  the main shading surface, not the W3b correction sub-grid); needs the exact W3b sub-grid path. Hold.
