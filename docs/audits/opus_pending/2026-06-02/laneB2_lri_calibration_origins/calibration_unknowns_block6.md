<!-- provenance: workflow wf_4bb93945-fac (l16-prefusion-fanout), 2026-06-03; finder+independent verifier; verifier reliable=False -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, weak-labeled, static disasm/LRI-parse only).
**Verifier reliability:** ONE claim failed re-extraction - corrected below; treat that item as LEAD

# Quarantine Packet — LRI Calibration f3.2/f3.3 decode + Block-6 record grouping

Seed: `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` (28mm Unit-1). Method: deterministic proto parse via `tools/lri_field_inspect.py` (`scan_lri_blocks`, `parse_proto_fields`). All labels OBSERVED = directly re-extractable; LEAD = inferred role. Block index per `--list-blocks`: Block 3 = 32832B intrinsics (16x f13), Block 6 = 35266B (42x f13).

## Q1 — f3.2 scalars (path: Block3 -> f13[c] -> f3 -> f2[instance])
f3.f2 occurs as 3 instances per camera. Instance[0] (61B): {f1=f32, f2=47B, f4=varint, f6=f32}; instance[1] (61B) same shape; instance[2] (85B): {f1=f32, f3=76B, f4=0}.

OBSERVED constants across all 16 cameras:
- f3.2[0].f1 = 818.0 ; f3.2[1].f1 = 1500.0 ; f3.2[2].f1 = 818.0
- f3.2[0].f4 = 60 ; f3.2[1].f4 = 62 ; f3.2[2].f4 = 0

OBSERVED per-camera variation of f3.2.6 (f32):
| cam | f2[0].f6 | f2[1].f6 |
|--|--|--|
|0|8707|9654| 1|8143|8857| 2|8033|8682| 3|9381|10194| 4|7907|8681| 5|1582|1496| 6|1496|1372| 7|1759|1666| 8|1766|1675| 9|1699|1602| 10|2084|1612| 11|2020|1386| 12|2180|1704| 13|2293|1840| 14|2082|1566| 15|1941|1396|

Note: f6 splits cams 0-4 (high ~8000-10200) vs cams 5-15 (low ~1370-2300). PREDICTION that f6 tracks a smooth focal/scale = REFUTED; it is a per-camera scalar with a class split. f3.2.4 (60/62/0) and f3.2.1 (818/1500/818) are constants, NOT focal/scale. LEAD: f3.2 instances [0]/[1] are likely two color-channel or two-band intrinsic variants (constant f1 pair 818/1500 + per-cam f6) and instance[2] holds the actual K matrix.

OBSERVED: f3.2[0].f2.f1 (45B) = 3x3 intrinsic matrix K (9 f32): fx=fy=3375.88, cx=2084.52, cy=1541.34, m22=1.0. (Pinhole K; cx~=4160/2.) LEAD: this is the per-camera pixel-focal + principal point.

## Q2 — f3.3 distortion model (path: Block3 -> f13[c] -> f3 -> f3)
f3.3 = {f1: 63B header, f2: 1614B LUT container}.

f3.3.f1 (63B) OBSERVED:
- f1 (10B) = (2063.0, 1534.0)  -> LEAD distortion center
- f2 (10B) = (4160.0, 4160.0)  -> LEAD image dimensions WxH
- f3 (20B) = packed f32 5-vector [0.03264, 0.15008, 0.0, 0.0, -0.57745] -> LEAD Brown-Conrady [k1,k2,p1,p2,k3], radial-only (p1=p2=0). raw hex `e6b2053d2dae193e000000000000000090d313bf`
- f4 = f32 0.000376374 ; f5 (10B) = {1:18, 2:14, 3:4125, 4:3093} (varints; LEAD grid dims)

f3.3.f2 (1614B) OBSERVED: scalars f2=3.70034, f3=2.55704, f4=0.0011, f7=0, f9=8707, f10=0.000424935; plus two repeated LUT curves:
- f5: 101 entries, each 10B = {1:f32 x, 2:f32 y}. x: 0 -> 2.8907 (~0.029 step), y: 0 -> 29.707 monotonic. LEAD radial forward map (normalized r -> scaled distorted r).
- f6: 30 entries, each 10B = {1:f32 x, 2:f32 y}. x: 0 -> 2.9 (0.1 step), y small +/-0.024. LEAD residual/correction curve.

(f9=8707 inside f3.3.2 equals cam0 f3.2[0].f6 — same per-camera scalar reappears here.)

## Q3 — Block 6 record grouping (42 = 14 triads, NOT a flat 14/28 split)
OBSERVED sizes: Counter({519:28, 1472:14}). Each f13 record = {f1: varint 0, f2: sub-msg}.

OBSERVED triad pattern over idx 0..41 (repeats x14): [1472 (f2.1=2, f2.8 present), 519 (f2.1=0, no f2.8), 519 (f2.1=6, no f2.8)].

f2 subfields OBSERVED (both classes share): f2.1 varint enum (0/2/6), f2.2 (45B 3x3 matrix), f2.3 (45B 3x3 matrix), f2.4 f32, f2.5 f32, f2.6 x24 (each 15B = {1,2,3 f32 triple}). LARGE-only: f2.8 (950B) = {f1:varint 1, f2: three x313B sub-msgs, each = {1:varint 380, 2:varint 755, 3:304B}}.

DISCRIMINATOR: f2.1 enum + presence of f2.8 (iff f2.1=2). f2.6 count is constant 24 in BOTH classes -> PREDICTION (count distinguishes) REFUTED.

OBSERVED matrices in a LARGE record: f2.2 = [0.8996,0.1317,-0.0671 / 0.3100,1.0739,-0.3840 / -0.0572,-0.4301,1.3125] row-sums (0.964,1.000,0.825) [matches thread's stated values]; f2.3 = [0.7191,-0.1025,-0.0288 / -0.3390,1.1279,0.2412 / -0.0413,0.2591,0.4806]. LEAD: f2.2/f2.3 are 3x3 color/transform matrices (CCM-like, near unit row-sums).

## Scope disclaimers
Single LRI (one 28mm Unit-1 capture) parsed; per-camera trend (Q1 split) tested on this file's 16 cameras only — NOT re-run on 70/150mm or Unit-2 twins. All role names (CCM, distortion center, image dims, forward/residual LUT) are LEAD inferences from value shape, NOT confirmed against libcp consumer disasm. No runtime/LLDB performed. Cross-checked docs/evidence/: no prior doc covers the Block-6 triad/f2.8 grouping or f3.3 LUT entry layout (novel).

## Verifier correction (load-bearing)
- The f3.3.2.5 LUT y-axis is NOT monotonic: y rises 0 -> peak 31.651 at index 72 -> descends to 29.707 at index 100 (28 non-monotone transitions). The finder's 'y monotonic' was wrong; corrected value matches prior verified_field_map.md ('y: 0->31.65->29.7'). All other thread-5 claims passed re-extraction.
