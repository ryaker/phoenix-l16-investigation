<!-- provenance: workflow wf_4ebb1a19-717 (l16-lri-block4-w9), 2026-06-03; finder + (verifier where it ran); verifier reliable=None -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, deterministic LRI byte-parse, 28mm Unit-1 seed).
**Verifier reliability:** verifier stage did not run; ORCHESTRATOR independently re-extracted the key structural claim (field13x16, 17x13 grid, 14144B=3536f=221x16, 4x4 near-identity, range -0.0194/1.0314) — PASS

## Block 4 decode — L16_02130.lri (2018-07-23), per-camera calibration grid

All values are deterministic LRI byte-parse via tools/lri_field_inspect.py (scan_lri_blocks, parse_proto_fields). Label: OBSERVED. NEVER PROVEN.

### Block identity
- Block idx 4: block_offset=0... (LELR walk), payload_size=262968 B, total_size=263000, msg_type=0.
- Top level: a single proto. ONLY field present = **field 13, wire-type 2, repeated 16x**. Entry sizes 15081 / 17783 B. (262968 ≈ 16 records.)

### (1) One record's field structure (representative camera_id=12, rec0, 15081 B)
Record top fields (proto):
- **field 1 (varint) = camera_id** — across the 16 records this enumerates 0..15 exactly once each. OBSERVED.
- **field 4 (bytes, 15061 B for small / 17762 B for large) = the LARGE payload sub-message.**
- **field 7 (bytes, 13 B)** = small sub-message; decodes to varints {1:1970, 2:1, 3:1, 4:2, 5:23, 6:14} (looks like version/format tag block; role LEAD only).

field 4 sub-message subfields:
- sub1 (bytes, 14151 B) — the calibration grid container.
- sub2 (bytes, 896 B small / 897 B, **repeated 4x in large records**) — secondary structure; its inner field2 blob is 891 B, NOT divisible by 4 and decodes to garbage as float32 → NOT a float grid (different encoding). LEAD only.
- sub3 (fixed32) = float 1.6462 (small) / 1.6273 (large) — single scalar, role LEAD.
- sub4 (varint) = varies per camera (529..15710) — role LEAD.

sub1 inner fields (the grid container):
- inner field 1 (varint) = **17  → W**
- inner field 2 (varint) = **13  → H**
- inner field 4 (bytes, **14144 B**) = the float payload.

### (2) Big payload decoded as float32 + factorization
- 14144 B / 4 = **3536 float32** (clean, divisible by 4). OBSERVED.
- Factorization: 3536 = **221 x 16**, and **221 = 17 x 13 = W x H** (matches inner dims fields exactly).
- So shape = **221 grid points (17 wide x 13 tall) x 16 floats per point**. NOT N*3.
- The 16 floats per point form a **4x4 matrix near identity**:
  - diagonal indices {0,5,10,15} ≈ 1.0
  - off-diagonal small (±0.02)
  - **indices 3, 6, 9, 12 are EXACTLY 0.0 across ALL 16 cameras** (sparse 4th-column/row pattern)
  - **symmetry: ch1 == ch2 and ch13 == ch14 (max abs diff 0.0 over the grid)** for rec0.
- **Actual value range (rec0, full 3536 floats): min = -0.019440004602074623, max = 1.0313801765441895.** (Range corrected/explicit per discipline.)
  - diagonal-only {0,5,10,15}: min 0.9898586, max 1.0313802, mean 1.0008642.
  - off-diagonal: min -0.019440, max 0.011693.

### Shape (radial test, rec0)
- idx15 diagonal: center≈1.000, corner_mean≈1.020 (TL 1.0194 / BR 1.0286) → gain rises toward corners.
- radius-vs-gain Pearson corr (normalized radius): ch0=0.23, ch5=0.225, ch10=0.342, ch15=0.449 (all positive). center r<0.3 vs corner r>0.9: ch15 1.0005→1.0084; ch10 0.996→0.9972; ch5 1.0022→1.0035; ch0 0.9978→1.0001.
- → mild **radial corner-rising correction**, strongest on the 4th channel (ch15). Consistent with lens-shading/vignetting compensation gain.

### (3) Per-channel?
**Multi-channel: 4 channels (a 4x4 matrix per sample), NOT single-channel and NOT 3-grid RGB.** The 4x4 with near-1 diagonal + small symmetric cross terms is a 4-channel (Bayer R/Gr/Gb/B style) shading + cross-channel color-correction operator per grid point. The 4 hard-zero entries {3,6,9,12} indicate a fixed sparse matrix template.

### (4) Classification
**Per-camera lens-shading / color-shading (vignetting) CORRECTION grid**, expressed as a per-grid-point 4x4 channel-mixing matrix sampled on a 17x13 lattice over the sensor.
- It is a gain/correction map (values ~1.0, radial), NOT a distortion DISPLACEMENT field (those would be 2-vector pixel offsets, often large; here entries are unitless near-1 gains with hard-zero structure).
- It is NOT a simple scalar vignetting grid (each point is a 4x4, multi-channel).

### Uniformity / tiering
- **Grid dims (17x13x16) and blob size (14144 B) are IDENTICAL across all 16 cameras.** The grid is genuine per-camera calibration: rec0 vs rec1 (different cameras) max abs grid diff = 0.1092 (real per-camera variation, not noise).
- **Record-size tiering is NOT in the grid** — it is the sub2 multiplicity:
  - 15081 B records (sub2 x1): camera_ids {0,1,2,3,4,8,11,12} (8 cameras)
  - 17783 B records (sub2 x4): camera_ids {5,6,7,9,10,13,14,15} (8 cameras)
  - Clean 8/8 split → two lens/sensor families; the larger tier carries 4 copies of sub2. (Family→focal mapping is a LEAD, not decoded here.)

### Scope NOT investigated
- sub2 (891-B inner blob) encoding not decoded (not float32). field 7 / sub3 / sub4 semantics are LEADs only.
- No libcp disasm or LLDB tracing performed — proto FIELD NUMBERS for field 4 / sub1 are unmapped to source names; "lens-shading/vignetting" classification is inferred from value structure (4x4 near-identity, radial corner-rising, per-camera) not from a named symbol.
- Only one LRI (28mm Unit-1) parsed; cross-zoom/cross-unit invariance of the 17x13x16 grid NOT checked.
- Bayer channel ordering (which of R/Gr/Gb/B = ch0/5/10/15) is an assumption, not verified.

## Universality self-check (orchestrator, OBSERVED)
The 17x13x16 (14144B) grid holds across seeds; per-body-constant + Unit-1 != Unit-2:
- U1 28mm (2018-07-23): first floats [1.00312, 0.00091, 1.00719(ch5), 1.01935(ch15)], range -0.0194/1.0314.
- U1 150mm (2018-07-29): byte-identical first floats to U1 28mm => per-body-constant across zooms.
- U2 28mm twin (2018-07-04): DIFFERENT [1.01342, 0.00830, 0.99987, 0.97445], range -0.0429/1.0474 => Unit-1 != Unit-2.
Block INDEX shifts (Block 4 in 11-block seeds, Block 5 in 12-block seeds), tracking block-count not focal.
