<!-- provenance: workflow wf_23c404a1-2cc (l16-lri-inputs-w8), 2026-06-03; finder+independent verifier; verifier reliable=False -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, deterministic LRI byte-parse, 28mm Unit-1 seed). Field-name labels CANDIDATE; values OBSERVED.
**Verifier reliability:** core PASS; a sub-detail claim corrected below (LEAD)

## LRI Block Inventory / Role-Map
**File:** `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` (155.1 MB, 28mm canonical seed)
**Parser:** `tools/lri_field_inspect.py` (`scan_lri_blocks`, `parse_proto_fields`) — deterministic, re-extractable.
**Blocks:** 11 LELR. Status labels: OBSERVED = parsed bytes; LEAD = role inference not byte-proven. NEVER PROVEN.

### Key structural finding (OBSERVED)
The LELR header is 32 bytes: `magic | total_len(u64) | msg_offset(u64) | msg_len(u32) | msg_type(u8)`. **Raw image data lives in the block BODY between byte 32 and `msg_offset`, NOT in the proto payload.** For blocks 0 and 2, `msg_offset = 81141760` so the proto payload sits at the END of an ~81 MB block; the ~81.14 MB body before it is the raw sensor data.

### Per-block table (all OBSERVED unless noted)
| idx | blk_off | total_size | msg_off | payload | msg_type | top-level fields (fn:wt×count) | role |
|---|---|---|---|---|---|---|---|
| 0 | 0 | 81,143,279 | 81,141,760 | 1519 | 0 | 1:v,2:v,3:b16,4:v=28,5:v=0,9:b17,11:b2,12:b×5,17:f32,18:b54,23:b836,24:b6,26:b7 | **RAW-DATA container #1** (body holds 5 raw planes: cam 0,4,6,8,9) + LightHeader metadata payload |
| 1 | 81,143,279 | 2,577 | 32 | 25 | 1 | 10:f32=1.5348,11:v,16:v=0,18:f32=1.5348,19:v | small ancillary, msg_type=1 (LEAD: AF/lens or stat record; 2520B body region) |
| 2 | 81,145,856 | 81,145,856 | 81,141,760 | 681 | 0 | 1:v,2:v,3:b16,4:v=28,9:b17,12:b×5,18:b52,24:b6,26:b7 | **RAW-DATA container #2** (body holds 5 raw planes: cam 1,2,3,5,7) + LightHeader metadata payload |
| 3 | 162,291,712 | 32,864 | 32 | 32,832 | 0 | 6:v,7:v,8:b3,13:b×16,18:b12 | **intrinsics (KNOWN)** — 16 records (per-camera), each rec: f1=idx,f3=<~1.9KB blob>,f7=<13B> |
| 4 | 162,324,576 | 263,000 | 32 | 262,968 | 0 | 13:b×16 | **per-module large calibration maps (LEAD)** — 16 records ~15.1/17.8KB; rec: f1=idx,f4=<~15KB>,f7=<13B>. Size split mirrors block 3 → same 16-position ordering; LEAD: lens-shading/vignette/distortion |
| 5 | 162,587,576 | 1,818 | 32 | 1786 | 0 | 16:b1782 → inner f1=2,f2=<1777B float blob> | **color/tone submsg (LEAD)** — inner blob begins with fixed32 floats (e.g. 42.0, 1023.0) |
| 6 | 162,589,394 | 35,298 | 32 | 35,266 | 0 | 13:b×42 | **color/shading spectral (KNOWN)** — 42 records 519..1472B; rec: f1=idx,f2=<blob> |
| 7 | 162,624,692 | 66 | 32 | 34 | 0 | 14:b32 | tiny tail metadata (LEAD: 32B sub-record) |
| 8 | 162,624,758 | 1,024 | 32 | 54 | 0 | 19:b51 | tiny metadata, 1024B padded block, 938B body region (LEAD) |
| 9 | 162,625,782 | 43 | 32 | 11 | 1 | 2:f32=0,7:v=0,9:v=0,13:v=0 | tiny zeroed record, msg_type=1 (LEAD: status/flags, all zero) |
| 10 | 162,625,825 | 38 | 32 | 6 | 2 | 3:v=1532356285 | tiny tail, msg_type=2 (LEAD: f3=1532356285 ≈ unix ts 2018-07-23, matches capture date) |

### Raw / metadata split (OBSERVED)
- **RAW sensor data:** ONLY blocks 0 and 2. Each carries 5 camera planes in the body (~16.23 MB/cam). 5+5 = **10 fired cameras** = 28mm count. Per-cam 16,228,346 B vs 4160×3120×10/8 = 16,224,000 B → 13MP 10-bit-packed Bayer (LEAD on exact geometry).
- **Metadata:** all other blocks (1,3,4,5,6,7,8,9,10) are small proto payloads.

### Camera partition (OBSERVED, from field12 CameraModule.camera_id)
- Block 0: cam **0, 4, 6, 8, 9**
- Block 2: cam **1, 2, 3, 5, 7**
- Block 0.18 HwInfo confirms same 5 (0,4,6,8,9); CameraModule.f4 (mirror_encoder_adc) nonzero only for cam 6,8,9 / 5,7 (movable tele/mid modules), 0 or absent for wide modules.

### Notable metadata values (OBSERVED)
- `BLK0.field4 = BLK2.field4 = 28` (28mm focal marker)
- `BLK0.field26` decodes inner ascii **"WDR"** (wide-dynamic-range/HDR capture mode)
- `BLK0.field9 = "1.0.16965 6439493"` (version/serial-like)
- `BLK0.field3 = 08e20f1007...` 16B (capture_id, self-delimited proto)

## Verifier correction(s)
- **file:/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri BLK0 raw body [32,81141760); CameraModule.field9.field5 offsets**: 81141728/5 = 16228345.6 (non-integer); claimed value 16228346 is wrong. Actual per-camera raw slice sizes from CameraModule.field9.field5 offsets: cam_id=0,4,6,8 each 16228352 bytes; cam_id=9 = 16228320 bytes. Neither matches 16228346. 4160x3120*10/8 = 16224000 confirmed correct.
