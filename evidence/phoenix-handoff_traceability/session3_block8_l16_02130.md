# Session 3 — L16_02130 Block 8 Parse & context_ptr[0] Hypothesis Verification

**Date:** 2026-04-13
**LRI:** `/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri` (162,625,865 bytes)
**Parser:** `/Volumes/Dev/lumen-phoenix-scratch/session3_block8_parse.py`

---

## Runtime Reference (Session 2)
```
context_ptr[0x00] = (0.60669, 1.000, 0.56213, 0.36895)
```
Hypothesis: values 0..2 are reciprocals of stored Block 8 f19.f15 gains.
Value 3 (0.36895) was unexplained.

---

## LELR Block Map (L16_02130)

Note: the `msg_type` byte in the 32-byte LELR header is **NOT** what we
thought. `msg_type=8` does **not** exist in this file. The "Block 8" of the
task brief is positional index 8 — the small 54-byte AWB/per-capture payload
near the file tail. All 11 LELR blocks share `msg_type=0` except blocks 1, 9
and 10. The positional Block 8 is the only 54-byte block and matches the
schema exactly.

| idx | file_offset | total_len | msg_len | msg_type |
|-----|-------------|-----------|---------|----------|
| 0 | 0x00000000 | 81,143,323 | 1,563 | 0 |
| 1 | 0x04d5b99b | 2,533 | 25 | 1 |
| 2 | 0x04d63880 | 81,145,856 | 681 | 0 |
| 3 | 0x09ac7280 | 32,865 | 32,833 | 0 |
| 4 | 0x09acf2e1 | 263,001 | 262,969 | 0 |
| 5 | 0x09b0f87a | 1,818 | 1,786 | 0 |
| 6 | 0x09b0ff94 | 35,298 | 35,266 | 0 |
| 7 | 0x09b18996 | 66 | 34 | 0 |
| **8** | **0x09b189d8 (162,624,760)** | **1,024** | **54** | **0** |
| 9 | 0x09b18dd8 | 43 | 11 | 1 |
| 10 | 0x09b18e03 | 38 | 6 | 2 |

**Block 8 file offset:** `0x09b189d8` = 162,624,760 (decimal)
**Block 8 payload offset (post-header):** `0x09b189f8` = 162,624,792
**Block 8 payload length:** 54 bytes
**Payload hex:**
```
9a013372180a0a0d000000001500000000120a0d0000803f150000803f
7a140d53fbd23f150000803f1d0000803f25a8b4e33f800100
```

---

## Parsed Protobuf Fields (Block 8)

```
f19 : message (51 bytes)
  f14 : message (24 bytes)            [sensor metrics / noise floor]
    f1 : message (10 bytes)
      f1 : f32 = 0.000000
      f2 : f32 = 0.000000
    f2 : message (10 bytes)
      f1 : f32 = 1.000000
      f2 : f32 = 1.000000
  f15 : message (20 bytes)            [AWB stored gains]
    f1 : f32 = 1.648295                ← R_gain
    f2 : f32 = 1.000000                ← G1 (fixed)
    f3 : f32 = 1.000000                ← G2 (fixed)
    f4 : f32 = 1.778951                ← B_gain
  f16 : varint = 0                    [flag]
```

Top-level field number `19` (0x9a 0x01 = tag for field 19, wire type 2) wraps
the per-capture AWB/sensor submessage. No other top-level fields in Block 8.

---

## Hypothesis Verification — CONFIRMED

| Channel | Stored gain (Block 8) | 1 / stored | Runtime context_ptr[0] | Δ |
|---------|----------------------|------------|------------------------|---|
| R | **1.648295** | **0.606688** | 0.60669 | < 1e-5 |
| G1 | 1.000000 | 1.000000 | 1.000 | 0 |
| G2 | 1.000000 | 1.000000 | (not slot) | — |
| B | **1.778951** | **0.562129** | 0.56213 | < 1e-5 |

The ISP kernel is reading Block 8 f19.f15 stored gains and writing their
**reciprocals** into `context_ptr[0]` at pipeline setup. Session 2's
observation `divss` reciprocal pattern was actually the caller computing
`1/gain` once at setup, not per-pixel. Match is exact to 5+ decimal places.

---

## The 0.36895 Mystery — NOT in Block 8

**0.36895 does NOT appear anywhere in Block 8.** Full hunt:

- All f32/d64 values in Block 8: `{0, 0, 1, 1, 1.648295, 1, 1, 1.778951}`
- Nothing in the `0.3 – 0.45` range.
- f19.f14 (the suspected noise-floor / sensor-gain field) contains only
  `(0, 0)` and `(1, 1)` pairs — clearly placeholder/identity defaults.
  On this capture there is no populated noise floor.
- f19.f16 flag is 0.

**Conclusion:** the 4th `context_ptr[0]` lane is **not** sourced from Block
8's f19 subtree on this capture. Candidates for where 0.36895 comes from:

1. **A different LELR block** — the LightHeader (Block 3, 32,833 bytes) or
   the per-sensor calibration block (Block 4, 262,969 bytes) likely holds an
   exposure/ISO scalar or a global noise floor that the kernel packs into
   slot 3.
2. **Derived at runtime** from ISO / exposure time / analog gain — e.g.
   `1 / (analog_gain * digital_gain)` or a sensor-temp-compensated black
   level. 0.36895 is a plausible reciprocal of a ~2.71 exposure factor.
3. **Padding/alignment** — unlikely since the runtime probe saw a
   deterministic non-zero value, not uninitialized memory.

**Recommended Session 4 follow-up:** run `walk_all_fields` across Blocks 3,
4, 5, 6 of L16_02130 looking for any f32 within `0.36895 ± 0.001`, and in
parallel check capture EXIF (ISO / shutter / gain) for a value whose
reciprocal is 0.36895. Do **not** assume it's in Block 8 — it isn't.

---

## Summary

- Reciprocal hypothesis for slots 0/1/2 of `context_ptr[0]`: **CONFIRMED
  with 5-decimal precision** against L16_02130 Block 8 f19.f15.
- Slot 3 (0.36895): **REJECTED as a Block-8-resident value**. Must come
  from another LELR block or be computed at pipeline setup from exposure
  metadata.
- Block 8 schema is exactly as `awb_analysis.txt` documented: 54 bytes,
  `f19.{f14,f15,f16}`, with f15 = `(R, 1, 1, B)`.
- f19.f14 is populated with placeholder `(0,0)` / `(1,1)` pairs on this
  capture — noise floor is either unused by this camera unit on this
  scene or stored elsewhere.
- Block 8 file offset in L16_02130: **`0x09b189d8` (162,624,760)**,
  payload starts at `0x09b189f8` (162,624,792), 54 bytes long.
