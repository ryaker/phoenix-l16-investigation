<!-- provenance: workflow wf_3fc00563-7ce (l16-prefusion-fanout-w2), 2026-06-03; finder+independent verifier; verifier reliable=False -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, weak-labeled, static disasm/LRI-parse only).
**Verifier reliability:** one claim failed re-extraction (a detail; core stands) — see correction at end; treat that item as LEAD

## Lane B: Block-6 record grouping + f3.2.6 focal-split characterization

Seed: `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` (28mm). Cross-check: `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` (70mm). Tool: `tools/lri_field_inspect.py` (scan_lri_blocks / parse_proto_fields). All facts are byte-deterministic and re-extractable; LRI proto paths cited. Static-only; no LLDB run was needed. Cross-checked `docs/evidence/` — no prior committed doc covers these specifics (novel).

### Q1 — Does f3.2.6 (or Block-3 fx) map to the 28/70/150 grouping?

OBSERVED: `f3.2.6` (Block idx3, f13->f3->f3.2[0]->f6, wt5 float) clusters cams0-4 high (7907..9381) vs cams5-15 low (1372..2293) — a **5/11 split**. This does NOT match the 5/5/6 focal array.

OBSERVED: the per-camera fx in `f3.3.1` sub-field 2 is uniform **4160** across all 16 cams — it is the capture reference intrinsic, not the array grouping.

OBSERVED (the real answer): the camera matrix at `f13->f3->f3.2[0]->f3.2.2 (47B) -> inner f1` packed float32 has its fx element split into THREE clean tiers in camera-id order:
- cams 0-4: fx ~ 3370-3377 (5 cams) -> **28mm**
- cams 5-9: fx ~ 8283-8309 (5 cams) -> **70mm**
- cams 10-15: fx ~ 18637-18794 (6 cams) -> **150mm**

LEAD: ratios mid/wide=2.46 (70/28=2.50), tele/wide=5.54 (150/28=5.36) confirm the physical focal-tier identification. So the canonical **5x28 / 5x70 / 6x150** grouping IS in the LRI — in f3.2.2's matrix fx, by camera id — but NOT in f3.2.6.

OBSERVED caveat: camera modules are not single-focal at firing — 28mm fired {0,4,6,8,9}, 70mm fired {6,8,9,14}; ids 6/8/9 fire in both. The f3.2.2 tiering is the static calibration array, distinct from per-shot firing.

### Q2 — What makes the 14 large (1472B) records differ from 28 small (519B)?

OBSERVED: NOT the f2.6 vector — both large and small have exactly **24** f2.6 entries of 15B (3 float32 points). The discriminator is `f2.1`: value `2` -> large, values `0`/`6` -> small. The 14 large records are large solely because they carry an extra `f2.8` sub-message of **950 bytes** (1472-519=953). f2.8 = {f2.8.1 varint=1, f2.8.2 repeated x3, each 313B}. Common geometry in every record: f2.2/f2.3 = two 45B 3x3 matrices, f2.4/f2.5 = two scalar floats (the briefing's 0.964/1.0/0.825 row-sums live in f2.2/f2.3).

### Q3 — Does 42 relate to camera pairs/combinations?

OBSERVED arithmetic: 42 = **14 cameras x 3 records**. Camera ids present = 0-14 EXCEPT 1 and 15 (14 ids), each with exactly 3 records (f2.1 in {0,2,6}). 42 != C(16,2)=120, != C(14,2)=91, != C(5,2)+C(11,2)=65. It is NOT a pairs/combinations count. (The absent ids 1 and 15 are also the boundary ids of the f3.2.6 5/11 split; their omission from Block 6 is noted but not explained here.)

### Stability
OBSERVED: identical Block-6 shape on 28mm (idx6) and 70mm (idx7) — both Unit-1, so this is per-body static calibration.

## Verifier correction(s) — load-bearing
- **LRI:/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri block[3] f13->f3->f3.2[0]->f3.2.2(47B)->inner f1 packed fixed32 (3x3 matrix fx element)**: Path: f3.2.2 is a 47-byte sub-message containing inner field f1 (45-byte blob); that 45-byte blob is 9 wire-type-5 fixed32 floats (fields 1-9 = 3x3 camera matrix). Observed fx (field 1) values: cam0=3375.9, cam1=3368.9, cam2=3371.1, cam3=3372.4, cam4=3377.4 (tier1); cam5=8283.4, cam6=8309.0, cam7=8307.7, cam8=8304.2, cam9=8297.9 (tier2); cam10=18794.7, cam11=18658.6, cam12=18730.6, cam13=18637.7, cam14=18677.8, cam15=18655.1 (tier3). The 5/5/6 tier split and three-tier structure match. However, cam1=3368.9 falls 1.1 units below the stated lower bound of ~3370, and cam10=18794.7 is 0.7 units above the stated upper bound ~18794. The claimed integer ranges do not fully contain the observed float32 values for tier1 minimum.
