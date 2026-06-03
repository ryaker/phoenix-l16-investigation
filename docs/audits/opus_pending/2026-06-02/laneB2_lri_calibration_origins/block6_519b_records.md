<!-- provenance: workflow wf_79b566a0-51d (l16-b2-finish-w7), 2026-06-03; finder+independent verifier; verifier reliable=False -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, deterministic LRI byte-parse, 28mm Unit-1 seed).
**Verifier reliability:** core structure PASS; a value-characterization claim FAILED and is corrected below (LEAD)

## Block-6 519B record decode — seed L16_02130.lri (2018-07-23), block idx=6

Re-extract: `cd /Volumes/Dev/L16_Lumen_ReverseEngineering; python3` using `tools/lri_field_inspect.py` helpers `scan_lri_blocks` + `parse_proto_fields`. Block idx=6, payload 35266B, msg_type=0. Records = repeated field **13** (wire2), 42 entries = 14 cameras x (1472,519,519). Each record: `f1`(varint=0), `f2`(sub-msg). Discriminator = **f2.f1** (field 1 inside f2): 1472->2, 519a->0, 519b->6.

### (1) Full field enumeration of a 519B record (camera 0, f2.1==0; f2.1==6 identical layout)
| Path | Wire | Count | Content | cam0 f1==0 value | cam0 f1==6 value |
|---|---|---|---|---|---|
| f2.1 | varint | 1 | enum discriminator | **0** | **6** |
| f2.2 | bytes(45) | 1 | 3x3 matrix (9x fixed32 .1..-.9) | rows [0.5933,0.2880,0.0829],[0.0819,1.1473,-0.2292],[-0.2842,-0.8507,1.9601] | rows [0.8107,0.0676,0.0860],[0.2126,0.9459,-0.1586],[-0.1271,-0.4614,1.4137] |
| f2.3 | bytes(45) | 1 | 3x3 matrix (9x fixed32) | rows [0.8445,-0.2681,0.0415],[-0.2209,0.9538,0.3141],[0.0318,0.1617,0.5229] | rows [0.6890,-0.0951,-0.0358],[-0.3106,1.0973,0.2450],[-0.0206,0.2197,0.4969] |
| f2.4 | fixed32 | 1 | scalar float | 0.80076 | 0.60722 |
| f2.5 | fixed32 | 1 | scalar float | 0.46339 | 0.55036 |
| f2.6 | bytes(15) | **24** | RGB triplet (3x fixed32) | e.g. [0.117,0.099,0.042],[0.397,0.348,0.154]... | (24 triplets) |

(1472B/f2.1==2 adds **f2.8** (950B): subfields {(1,varint):1,(2,bytes):3} — the spectral payload, ABSENT from both 519B records.)

### (2) What distinguishes f1==0 from f1==6
They are **structurally identical** (same fields 1,2,3,4,5, 24x6; no f2.8). They differ ONLY in the f2.1 enum (0 vs 6) and the actual numeric matrix/scalar values. Interpretation (LEAD): two distinct **illuminant / calibration-condition instances** of the same calibration record type (the 1472 f2.1==2 is a third instance that additionally carries the spectral block). Not different schemas.

### (3) Classification — do they carry the two 3x3 matrices?
**YES.** Both 519B records carry BOTH 3x3 matrices:
- **f2.2 = white-point-normalized CCM.** Row-sums are the thread's reference **[0.9642, 1.0, 0.8252]** EXACTLY, and this is **INVARIANT across all 14 cameras AND all 3 variants (f1=0/2/6)**. Constant row-sums = fixed reference-white constraint in target color space. (OBSERVED)
- **f2.3 = a second, distinct 3x3 matrix** (per-camera sensor/adaptation matrix, LEAD). Row-sums VARY per camera ([0.576-0.624, ~1.047, 0.667-0.730]). Not the inverse of f2.2 (inv(f2.2)!=f2.3; f2.2@f2.3 != I) — so two separate transforms, not a forward/inverse pair.
- **f2.4 / f2.5** = two per-camera scalar floats (anti-correlated across variants; WB-chromaticity-ratio-like, LEAD — NOT confirmed as black level).
- **f2.6** = 24 RGB measured-response triplets, ColorChecker-24-patch-like (LEAD), plausibly the chart from which the CCM was solved.

So: the 519B records are NOT "black-level / AWB / per-channel-gain only" records — they primarily carry the two 3x3 color matrices plus 24 chart triplets plus 2 scalars.

## Verifier correction(s)
- **LRI block[6] field13 records, all 42 inner f2.6 repeated sub-messages**: Structure verified: exactly 24 sub-messages per record in all 42 records, each exactly 15B, with field tags 0x0d/0x15/0x1d = fields 1/2/3 wire-type 5 (fixed32). First two claimed examples match exactly. HOWEVER, claimed value range '~0.04-0.5' is WRONG: actual global range is 0.0139-0.9113. Triplet index [18] (apparent high-reflectance/white patch) consistently reaches green channel ~0.911 across all cameras. 169 individual component values exceed 0.5. Structure claim passes; range characterization fails.
