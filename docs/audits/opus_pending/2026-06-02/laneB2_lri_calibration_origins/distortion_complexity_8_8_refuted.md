<!-- provenance: workflow wf_79b566a0-51d (l16-b2-finish-w7), 2026-06-03; finder+independent verifier; verifier reliable=True -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, deterministic LRI byte-parse, 28mm Unit-1 seed).
**Verifier reliability:** all load-bearing values independently re-parsed (PASS)

## Block-3 "8/8 distortion split" — RE-VERIFICATION (seed L16_02130 2018-07-23, 28mm)

**Method:** deterministic LRI byte-parse via `tools/lri_field_inspect.py` (`scan_lri_blocks`, `parse_proto_fields`). All values re-extractable. Volume `/Volumes/Base Photos` confirmed mounted; seed 162,625,863 B.

**Block identity:** the claim's "Block-3" = LELR block **idx 3** (msg_type 0, block_offset 162291712, payload 32832 B). The 16 cameras are its `f13` repeated sub-messages (the only top-level field repeated exactly 16x; idx4 also has 16x f13). Per-camera calibration tree: `f13[ci] -> f3 (cal msg) -> f3 (1682B) -> f1 (63B geometry) -> {f1 principal pt, f2 K-focal, f3 20B distortion, f5 dims}`.

### Q1 — 5 distortion coeffs (f3.3.1.3): ALL NON-ZERO, none identity
The 20-byte block is a RAW packed `5×float32` array (not nested proto). All 16 decode cleanly, every cam distinct and non-zero, layout `[k0,k1,0,0,k4]` for **all 16** (slots 2,3 = 0.0 universally):

| cam | flag | k0 | k1 | k2 | k3 | k4 |
|----|----|----|----|----|----|----|
| 0 |0| +3.264e-2 | +1.501e-1 | 0 | 0 | -5.774e-1 |
| 4 |0| +3.785e-2 | +1.446e-1 | 0 | 0 | -5.678e-1 |
| 5 |2| +2.256e-2 | -6.684e-2 | 0 | 0 | +3.606e-2 |
| 8 |1| +2.290e-2 | -8.256e-2 | 0 | 0 | +6.011e-2 |
| 12 |2| +3.599e-2 | -2.754e-1 | 0 | 0 | +3.251e-1 |
| 15 |1| +3.922e-2 | -2.750e-1 | 0 | 0 | +3.161e-1 |

(full 16-row table available; cams 0-4 have +k1/-k4 sign pattern, cams 5-15 have -k1/+k4 — a real per-tier optics difference, but ALL non-zero, NONE identity).

### Q2 — Missing LUTs? NO. All 16 carry every field.
`f3.f2[0]`=61B, `f3.f2[1]`=61B, `f3.f3.f2`=1614B — constant across all 16. No camera lacks any field. There is no "some cams lack the LUT" complexity difference.

### Q3 — Genuine flag, but TRI-valued; 8/8 is a size artifact of an UNRELATED sub-model
- Real per-cam flag `cam.f3.f1` is **{0,1,2}**: flag0={0,1,2,3,4}(5), flag1={8,14,15}(3), flag2={5,6,7,9,10,11,12,13}(8). NOT binary 8/8.
- The 1944-vs-2149 byte split = flag2 vs flag{0,1}. It lives ENTIRELY in `cam.f3.f2[2].f3` (76B for flag0/1 under inner field f1; 279B for flag2 under inner field f2). That block is anchored by float **818.0** (`f3.f2[2].f1`) — the SAME 818 constant CLAUDE.md flags as previously misread-as-fx. It is a SEPARATE calibration sub-model, NOT the lens-distortion polynomial.
- Real K focal: **fx=fy=4160** px, uniform across all 16 (no 818 misread here).

**Verdict:** the "8/8 distortion-complexity split (simple/identity vs full polynomial)" is **REFUTED as stated**. The agent counted a real byte-size/field-tag threshold of the 818.0-anchored sub-model and mislabeled it as distortion-polynomial complexity. The actual distortion polynomial is present and non-zero for all 16; the actual flag is tri-valued.