<!-- provenance: workflow wf_23c404a1-2cc (l16-lri-inputs-w8), 2026-06-03; finder+independent verifier; verifier reliable=True -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, deterministic LRI byte-parse, 28mm Unit-1 seed). Field-name labels CANDIDATE; values OBSERVED.
**Verifier reliability:** all load-bearing values independently re-parsed (PASS)

## THREAD: AWB/WB gains in L16_02130.lri (2018-07-23, 28mm)

File: `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` (162,625,863 bytes, 11 LELR blocks).
Tool: `tools/lri_field_inspect.py` (scan_lri_blocks + parse_proto_fields). All values re-extractable.

### (1) WB/AWB gains location + parsed values  [OBSERVED]
- **Block 8, field path `B8.19.15` = four float32: [1.717839, 1.0, 1.0, 1.588839]**
  - Layout = Bayer **R / G1 / G2 / B**, G normalized to 1.0, R=1.718 and B=1.589 both >1 (matches the classic WB-gain signature and the predicted ~1.3-2.5 range).
  - Abs file offset **0x9b17535** (Block 8 payload off 31). Raw tagged bytes:
    `0d 26e2db3f | 15 0000803f | 1d 0000803f | 25 105fcb3f`
    (tags 0x0d/0x15/0x1d/0x25 = proto fields 1-4 wire-type 5).
- Sibling `B8.19.14` = identity pairs `[(0,0)],[(1,1)]` (offset/gain placeholders).
- Block 8 has exactly ONE top-level field-19 submsg (payload only 54 bytes).

### (2) Per-capture vs per-camera  [OBSERVED]
- **GLOBAL / per-capture.** Single occurrence; no repetition; no camera_id alongside it. Contrast with Block 6 which has 42 per-camera entries.

### (3) Distinct from Block-6 f2.4/f2.5 scalars and CCM  [OBSERVED]
- Block 6 = 42 repeated `field 13` submsgs (per-camera color cal).
  - `B6.13.2.4` / `B6.13.2.5` = the per-camera "f2.4/f2.5" scalars: SUB-1.0, vary per camera (id0: 0.80076/0.46339; id5: 0.74364/0.44207; id2: 0.79419/0.44137...). These are ratio-like but are NOT a G=1/R,B>1 WB quad — clearly a different quantity from the Block-8 gains.
  - `B6.13.2.2` (9 floats) and `B6.13.2.3` (9 floats) = per-camera **3x3 CCM(s)** (row example [0.593,0.288,0.083 / 0.082,1.147,-0.229 / -0.284,-0.851,1.960]).
  - `B6.13.2.6` = repeated RGB triples (shading/color-checker grid).
- Conclusion: Block-8 global WB gains, Block-6 per-camera f2.4/f2.5 scalars, and Block-6 per-camera CCM are three DISTINCT field groups.

### (4) CCT / illuminant scalar  [LEAD — effectively absent]
- Swept all 11 blocks for varint+f32 in 1800..12000: every hit resolves to sensor dims (4160x3120), exposure ticks, image size, or calibration grid points. **No clean standalone color-temperature field.**
- Closest temperature-SHAPED value: per-camera `B0.12.1.3 ~ 3542-3553` (CameraModule, unlabeled, role unknown) — weak LEAD only, not confirmed as CCT.

### Caveats / scope
- Field-NUMBER -> NAME labels for Blocks 6/8 are LEADs (proto schema not independently verified); the parsed VALUES and byte offsets are OBSERVED.
- Single LRI (Unit-1, 28mm) only. Did NOT re-run on 35/70/150mm or the Unit-2 twins; per-capture-vs-some-other-grouping universality unverified across the corpus.
- Did NOT trace libcp consumption of B8.19.15 — block role inferred from value shape, not from runtime read.
- Block 5 = lens vignetting/falloff curve (radius 100..775 polynomial), Block 3/4 = large per-camera geometric/photometric cal (not WB).