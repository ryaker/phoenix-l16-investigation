<!-- provenance: workflow wf_23c404a1-2cc (l16-lri-inputs-w8), 2026-06-03; finder+independent verifier; verifier reliable=False -->
**Status:** NEEDS_CODEX_VALIDATION (quarantine, deterministic LRI byte-parse, 28mm Unit-1 seed). Field-name labels CANDIDATE; values OBSERVED.
**Verifier reliability:** core PASS; a sub-detail claim corrected below (LEAD)

## Block-0 LightHeader decode — L16_02130.lri (2018-07-23, 28mm, Unit-1)

Source: `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri`, Block-0 (block_offset=0, msg_offset=81141760, msg_type=0, payload=1519 bytes). Re-extractable: `cd /Volumes/Dev/L16_Lumen_ReverseEngineering; python3` with `tools/lri_field_inspect.py:scan_lri_blocks()[0]['payload']` then `parse_proto_fields()`.

### Top-level fields (OBSERVED values; CANDIDATE names)
| Field | Wire | OBSERVED value | CANDIDATE name | Clean-room need |
|---|---|---|---|---|
| f1 | varint | 15506288127949507416 (0xd73166e583498b58) | capture_guid_hi | No |
| f2 | varint | 10269686990286241384 (0x8e8541e812763e68) | capture_guid_lo (NOT ns-timestamp) | No |
| f3 | sub(16B) | 2018,7,23,11,31,22,359 = 2018-07-23 11:31:22.359 | capture_datetime | Metadata out |
| f4 | varint | 28 | image_focal_length | YES |
| f5 | varint | 0 | image_reference_camera | YES |
| f9 | string | '1.0.16965 6439493' | pipeline/software_version | No |
| f11 | sub(2B) | 0x2838 | zoom/mode sub | Maybe |
| f12 | sub x5 | per-camera (below) | repeated CameraModule | YES core |
| f17 | fixed32 | 0.0 | tof_range/unused | No |
| f18 | sub(54B) | hw_info 5 cams | HwInfo | YES (cal keys) |
| f23 | sub(836B) | two 19-pt curves | response/vignette LUT | Likely YES |
| f24 | sub(6B) | f1=1,f2=28,f3=6 | mode descriptor | Maybe |
| f26 | sub(7B) | f1=2,f2='WDR' | hdr/WDR mode tag | Maybe |

### f12 per-camera (repeated CameraModule) — fired set {0,4,6,8,9}
| cam_id(f2) | f3 | f4 | f5 exposure | f7 gain | f8 counter | f10 focus | f14 | f1.f2 float pair |
|---|---|---|---|---|---|---|---|---|
| 0 | 1 | — | 10640 | 1.0 | 11238709 | 84 | 1.0 | (0.500,0.4997) |
| 4 | 1 | — | 9200 | 1.5 | 14635416 | 62 | 1.0156 | (0.527,0.510) |
| 6 | 1 | 400 | 1262 | 1.5 | 14651304 | 58 | 1.0156 | (0.045,0.064) |
| 8 | 1 | 0 | 1592 | 1.5 | 14642265 | 60 | 1.0156 | (0.525,0.482) |
| 9 | 1 | 467 | 1530 | 1.5 | 14645000 | 54 | 1.0156 | (0.968,0.916) |

Ranges (actual parsed min/max): f5 exposure 1262..10640; f7 gain 1.0..1.5; f10 focus 54..84.

### f18 hw_info (HwInfo) — CameraModuleHwInfo records
ids {0,4,6,8,9}; each f2=2; f3 (lens_type) = 4 for cams 0&4, = 3 for cams 6,8,9; f4=1 on cams 6&9; f5=1 on cams 6,8,9. HwInfo f2=0, f3=1.

### f23 (836B) — two parallel 19-point tables (LEAD)
f2[] and f3[] each 19 entries keyed by increasing varint (26,183,340,...,2851; step ~157). f2 vals cluster ~[-0.02,0.97,0.25]; f3 vals monotonic from [0,0,0] up to ~[0.14,-0.08,0.12]. CANDIDATE color/tone response or vignette-vs-radius. Not per-camera.

### Clean-room renderer needs (from Block-0)
1. f4 focal (28) selects zoom tier/grouping.
2. f5 reference_camera (0) geometric anchor.
3. f12 repeated CameraModule: per-fired-camera exposure(f5), gain(f7), focus(f10), per-cam f4, normalized pair f1.f2 — normalize/align each frame before merge.
4. f12/f18 camera_id sets = fired mask {0,4,6,8,9}.
5. f18 hw_info ids+lens_type = intrinsics/calibration table keys.
6. f23 curves likely applied at render (LEAD).
7. f3 datetime, f9 version = metadata passthrough only.

## Verifier correction(s)
- **LRI offset 81141760 Block-0 field 23, bytes[836], inner f2 and f3 repeated entries**: len=836 PASS; f2 count=19 PASS; f3 count=19 PASS; keys 26..2851 step=157 (one step=156) PASS; 3 floats per entry PASS; f2 range [-0.0293,0.9856] consistent with claim; f3 first entry=[0,0,0] PASS; BUT f3 is NOT fully monotonic: col0 is bell-shaped (rises 0->0.169 then falls to 0.142), col2 reverses sign mid-sequence -- only col1 is monotonically decreasing; 'monotonic from [0,0,0]' is only partially true
