# LRI Header — Per-Capture Fired Cameras & Mirror Configs

**Date:** 2026-04-13
**Purpose:** Document the LRI binary fields that tell Phoenix (1) which cameras fired for a given capture, and (2) which mirror/encoder config each movable camera used. Pure binary RE against real LRI files — no reliance on spike conclusions.

**Schema correction (2026-06-19):** `libcp.dylib` embeds the complete
`camera_module.proto` and `lightheader.proto` descriptors. Machine extraction
proves the field names and types used below. Earlier guesses that field 5 was
exposure-related, field 8 was timestamp-like, and field 10 was a focus step are
refuted; the exact names are `lens_position`, `sensor_exposure`, and
`sensor_temparature` (the installed schema's spelling). See
`docs/evidence/bundle_static_runtime_index5_public_proto_schema_names.md`.

**Verified on three real LRIs (three different zoom levels, same camera unit):**
- `/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri` — 28mm (zoom=28)
- `/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri` — 70mm (zoom=70)
- `/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri` — 150mm (zoom=149)

And cross-checked across **159 additional captures** from six date folders spanning zoom 28–149 (see §Validation).

---

## 1. LRI Container — LELR Block Header (32 bytes)

Every LRI file is a linear sequence of LELR blocks. Each block starts with a 32-byte header:

| Offset | Size | Field | Meaning |
|--------|------|-------|---------|
| 0      | 4    | magic | `"LELR"` |
| 4      | 8    | total_block_len (u64 LE) | bytes from start of this header to start of next block |
| 12     | 8    | msg_offset (u64 LE) | offset (from start of this header) to protobuf message payload |
| 20     | 4    | msg_len (u32 LE) | length of protobuf message |
| 24     | 1    | msg_type (u8) | message type tag (observed: 0, 1, 2) |
| 25     | 7    | reserved / pad | |

To walk the block table: start at offset 0, read 32 bytes, record, advance by `total_block_len`, repeat until `total_block_len==0` or EOF.

The protobuf message payload lives at `block_offset + msg_offset`, `msg_len` bytes long. For small-payload blocks (metadata-only, e.g. the LightHeader blocks inside image chunks), `msg_offset == 32` (immediately after header). For image chunks, `msg_offset` can be nearly the full block size — the raw image bytes precede the LightHeader.

### Block types in a typical L16 LRI

From L16_02130.lri (28mm, 10 fired cameras, 2 image chunks):

| # | block_offset | total | msg_off | msg_len | role |
|---|--:|--:|--:|--:|---|
| 0 | 0 | 81,143,279 | 81,141,760 | 1,519 | **IMAGE CHUNK + LightHeader** (A1, A5, B2, B4, B5) |
| 1 | 81,143,279 | 2,577 | 32 | 25 | unknown small |
| 2 | 81,145,856 | 81,145,856 | 81,141,760 | 681 | **IMAGE CHUNK + LightHeader** (A2, A3, A4, B1, B3) |
| 3 | 162,291,712 | 32,864 | 32 | 32,832 | **Block A** — GeometricCalibration (16 cams) |
| 4 | 162,324,576 | 263,000 | 32 | 262,968 | **Block B** — Vignetting/CRA/warp (16 cams) |
| 5 | 162,587,576 | 1,818 | 32 | 1,786 | metadata |
| 6 | 162,589,394 | 35,298 | 32 | 35,266 | **Block C** — ColorCalibration (14×3 CCMs) |
| 7 | 162,624,692 | 66 | 32 | 34 | metadata |
| 8 | 162,624,758 | 1,024 | 32 | 54 | AWB block (f19.f15 = `[R,1,1,B]`) |
| 9 | 162,625,782 | 43 | 32 | 11 | tail |
| 10 | 162,625,825 | 38 | 32 | 6 | tail |

70mm / 150mm files have **three** image chunks (blocks 0, 2, 3), each covering a disjoint subset of the 11 cameras that fire at telephoto zooms.

---

## 2. Per-Capture Fired-Camera List → `LightHeader.field_12`

Each image-chunk block carries an embedded `LightHeader` protobuf at the end of the block (at `block_offset + msg_offset`, `msg_len` bytes long). The LightHeader has a **repeated** `field_12` of type `bytes`, with **one entry per camera whose raw sensor data lives in that chunk**.

The sum of `field_12` entries across all image chunks in a file IS the fired-camera set for that capture.

### Per-camera inner message (each `field_12` entry)

Decoded as protobuf. Fields observed across all verified captures:

| field | wire_type | meaning | notes |
|------:|:---------:|---|---|
| 2 | varint | `CameraModule.id` (`CameraID`) | 0–4 = A1..A5, 5–9 = B1..B5, 10–15 = C1..C6 |
| 3 | varint | `CameraModule.is_enabled` (`bool`) | defaults to `true` |
| 4 | varint | `CameraModule.mirror_position` (`int32`) | capture-time mirror position; 0 for fixed mirrors |
| 5 | varint | `CameraModule.lens_position` (`int32`) | live lens-position code used by focus-dependent intrinsics evaluation |
| 7 | fixed32 | `CameraModule.sensor_analog_gain` (`float`) | required |
| 8 | varint | `CameraModule.sensor_exposure` (`uint64`) | required |
| 9 | bytes | `CameraModule.sensor_data_surface` | includes `size = 4160 x 3120` |
| 10 | varint | `CameraModule.sensor_temparature` (`sint32`) | zigzag encoded; spelling is from installed schema |
| 15 | varint | `CameraModule.frame_index` (`uint32`) | optional |
| 16 | varint | `CameraModule.sensor_dpc_on` (`bool`) | defaults to `true` |

For this deliverable, the config-selection fields remain **2** (`id`) and **4**
(`mirror_position`). The additional names above are descriptor-proven and are
used by the Lane B public-origin evidence.

### LightHeader top-level fields also useful

| field | wire_type | meaning | example |
|------:|:---------:|---|---|
| 4 | varint | **zoom focal length** (mm) | 28, 29, 35, 50, 70, 135, 149 |

(Field 4 is present at the top level of the LightHeader inside image chunk block 0 in every file. It's the user-selected zoom.)

---

## 3. Factory Nominal Encoder Positions → Warp Block `field_13`

The ~263 KB warp/vignetting block (`msg_len` in range 250,000–280,000) has a top-level repeated `field_13` of type `bytes`, one entry per camera. Each entry is a `PerCameraCalibration`-ish message:

| field | wire_type | meaning |
|------:|:---------:|---|
| 1 | varint | **camera_id** |
| 4 | bytes   | **MirrorActuatorMapping**-ish sub-message |
| 7 | bytes (13 B) | constant build-time date stamp (1970-01-01 02:23:14) — identical for all 16 cameras |

Inside `field_4` (the "MirrorActuatorMapping"-ish sub-message):

| field | wire_type | content |
|------:|:---------:|---|
| 1 | bytes (14,151 B) | grid `(17 × 13 × N floats)` — appears to be vignetting / distortion grid |
| 2 | bytes (repeated) | **per-config encoder park positions** — **1 entry for fixed-mirror cameras, 4 entries for movable cameras** |
| 3 | fixed32 | scalar (IEEE 754 float32) — observed values 0.994..1.12 — per-camera scale factor |
| 4 | varint | small int (529..15710) — differs between cameras, possibly entrance-pupil reference |

Each `field_2` entry inside `field_4` is a small message:

| field | wire_type | content |
|------:|:---------:|---|
| 1 | varint | **nominal encoder ADC for this mirror config** |
| 2 | bytes (891 B) | R_fold / warp data for this config (not needed for config selection) |

### Key structural distinction

- **Fixed-mirror cameras** have exactly **one** `field_2` entry with `field_1 = 0` and a `field_4` sub-message of 15,061 bytes.
- **Movable-mirror cameras** have exactly **four** `field_2` entries (the 4 mirror park positions) and a `field_4` sub-message of 17,762 bytes.

The number of `field_2` entries directly enumerates how many discrete configs a camera supports.

### Verified nominals for L16_02130 unit (this camera body)

(Identical in all three files — factory calibration is device-level, carried in every LRI.)

| cam_id | name | entry_size | nominals (config 0..3) | movable? |
|---:|:---:|:---:|:---|:---:|
|  0 | A1 | 15,061 | `[0]` | no |
|  1 | A2 | 15,061 | `[0]` | no |
|  2 | A3 | 15,061 | `[0]` | no |
|  3 | A4 | 15,061 | `[0]` | no |
|  4 | A5 | 15,061 | `[0]` | no |
|  5 | B1 | 17,762 | `[637, 519, 403, 749]` | **yes** |
|  6 | B2 | 17,762 | `[780, 666, 554, 887]` | **yes** |
|  7 | B3 | 17,762 | `[719, 627, 532, 806]` | **yes** |
|  8 | B4 | 15,061 | `[0]` | no |
|  9 | B5 | 17,762 | `[719, 596, 476, 838]` | **yes** |
| 10 | C1 | 17,762 | `[674, 579, 483, 775]` | **yes** |
| 11 | C2 | 15,061 | `[0]` | no |
| 12 | C3 | 15,061 | `[0]` | no |
| 13 | C4 | 17,762 | `[761, 636, 509, 882]` | **yes** |
| 14 | C5 | 17,762 | `[684, 583, 483, 782]` | **yes** (but see §5) |
| 15 | C6 | 17,762 | `[581, 486, 387, 677]` | **yes** (but see §5) |

**Movable set: B1, B2, B3, B5, C1, C4, C5, C6** (8 cameras with steerable mirrors).
**Fixed set: A1, A2, A3, A4, A5, B4, C2, C3** (8 cameras with fixed mirrors).

> **Correction to prior notes.** The earlier investigation assumed "B and C cameras have 4 configs each, with B2 = wide-angle park and B3 = telephoto park." That mental model is incomplete:
> - B4 (ID 8), C2 (ID 11), and C3 (ID 12) are **fixed** on this unit (one config).
> - C5 (ID 14) and C6 (ID 15) do have 4 factory-nominal configs — but they always report encoder=0 at capture time, which means the simple `argmin` test cannot recover their "actual" config (see §5).

---

## 4. Config Selection Algorithm

For each camera in the fired-camera set:

```python
def select_config(encoder_reading, nominals):
    if not nominals or len(nominals) < 2:
        return 0     # fixed mirror — only one config exists
    return min(range(len(nominals)),
               key=lambda i: abs(encoder_reading - nominals[i]))
```

Apply this per movable camera using `encoder_reading = LightHeader.field_12[cam].field_4` and `nominals = warp_block.field_13[cam].field_4.field_2[i].field_1`.

---

## 5. Verified Selection — 3 LRIs, Different Zooms

### L16_02130.lri — zoom = 28 (28mm, 10 cameras fire)

| cam | encoder | closest nominal | config |
|---:|---:|---:|---:|
| A1..A5 | 0 | n/a (fixed) | 0 |
| B1 | 359 | 403 | **2** |
| B2 | 400 | 554 | **2** |
| B3 | 434 | 532 | **2** |
| B4 | 0 | n/a (fixed) | 0 |
| B5 | 467 | 476 | **2** |

**All B cameras select config 2 at 28mm.** C cameras do not fire.

### L16_03434.lri — zoom = 70 (70mm, 11 cameras fire)

| cam | encoder | closest nominal | config |
|---:|---:|---:|---:|
| B1 | 726 | 749 | **3** |
| B2 | 790 | 780 | **0** ⚠ |
| B3 | 856 | 806 | **3** |
| B4 | 0 | n/a (fixed) | 0 |
| B5 | 863 | 838 | **3** |
| C1 | 433 | 483 | **2** |
| C2 | 388 | n/a (fixed) | 0 |
| C3 | 409 | n/a (fixed) | 0 |
| C4 | 535 | 509 | **2** |
| C5 | 0 | 483 | **2** |
| C6 | 0 | 387 | **2** |

Note B2 picks config **0** at 70mm because its nominals `[780, 666, 554, 887]` are ordered such that config 0 (780) is closest to the actual encoder (790). B1, B3, B5 pick config 3. **The config index is NOT a semantic "wide/tele park" constant across cameras** — each camera's nominal table has its own order.

### L16_02285.lri — zoom = 149 (150mm, 11 cameras fire)

| cam | encoder | closest nominal | config |
|---:|---:|---:|---:|
| B1 | 728 | 749 | 3 |
| B2 | 812 | 780 | 0 |
| B3 | 855 | 806 | 3 |
| B4 | 0 | n/a (fixed) | 0 |
| B5 | 862 | 838 | 3 |
| C1 | 633 | 674 | 0 |
| C2 | 576 | n/a (fixed) | 0 |
| C3 | 591 | n/a (fixed) | 0 |
| C4 | 735 | 761 | 0 |
| C5 | 0 | 483 | 2 |
| C6 | 0 | 387 | 2 |

### C5 / C6 anomaly

Both C5 and C6 have legitimate 4-config factory nominals **but report `encoder=0` in the LightHeader on every verified capture (28mm, 70mm, 150mm).** Naïve argmin always yields config 2 for them, which cannot be physically correct at three different zoom levels.

**Interpretation (unverified, flagged for follow-up):** either (a) C5/C6 are effectively fixed at the factory-set "park" position on this camera unit and the 4-entry nominal table is vestigial, (b) the firmware does not route an ADC readback to the LightHeader for these specific actuators, or (c) config selection for C5/C6 uses a different algorithm (e.g., derived from the commanded zoom instead of encoder readback). The LRI binary alone does not distinguish these cases. LLDB tracing of `MirrorActuatorMapping::selectConfig()` or similar on `libcp.dylib` during a render is needed to resolve this. **Phoenix should hardcode the C5/C6 config per zoom (likely config 0 at ≥70mm, absent at <70mm) until this is resolved, OR use the argmin result as-is and validate against rendered output.**

---

## 6. Python Decode Snippet

Standalone. Reads an LRI, returns `(zoom, fired_cameras_with_configs)`. No external dependencies beyond Python 3.

```python
#!/usr/bin/env python3
"""LRI per-capture camera + config extractor.
Usage: python3 lri_header.py <file.lri>
"""
import struct, sys

CAMERA_NAMES = {
    0:"A1",1:"A2",2:"A3",3:"A4",4:"A5",
    5:"B1",6:"B2",7:"B3",8:"B4",9:"B5",
    10:"C1",11:"C2",12:"C3",13:"C4",14:"C5",15:"C6",
}

# ---- protobuf primitives ----
def read_varint(data, pos):
    result = 0; shift = 0
    while pos < len(data):
        b = data[pos]; pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, pos
        shift += 7
        if shift > 63: raise ValueError
    raise ValueError

def parse_proto(data):
    """Yield (field_num, wire_type, raw_bytes_if_wt2, decoded_value)."""
    out = []; pos = 0
    while pos < len(data):
        try:
            tag, pos = read_varint(data, pos)
        except Exception: break
        fn, wt = tag >> 3, tag & 7
        if wt == 0:
            try: v, pos = read_varint(data, pos)
            except Exception: break
            out.append((fn, 0, None, v))
        elif wt == 1:
            if pos+8 > len(data): break
            out.append((fn, 1, None, struct.unpack_from('<Q', data, pos)[0]))
            pos += 8
        elif wt == 2:
            try: ln, pos = read_varint(data, pos)
            except Exception: break
            if pos+ln > len(data): break
            out.append((fn, 2, data[pos:pos+ln], None))
            pos += ln
        elif wt == 5:
            if pos+4 > len(data): break
            out.append((fn, 5, None, struct.unpack_from('<I', data, pos)[0]))
            pos += 4
        else: break
    return out

# ---- LELR block table ----
def build_block_table(data):
    blocks = []; pos = 0
    while pos + 32 <= len(data):
        if data[pos:pos+4] != b'LELR': break
        total   = struct.unpack_from('<Q', data, pos+4)[0]
        msg_off = struct.unpack_from('<Q', data, pos+12)[0]
        msg_len = struct.unpack_from('<I', data, pos+20)[0]
        blocks.append(dict(offset=pos, total=total, msg_off=msg_off, msg_len=msg_len))
        if total == 0: break
        pos += total
    return blocks

def payload(data, blk):
    return data[blk['offset']+blk['msg_off'] : blk['offset']+blk['msg_off']+blk['msg_len']]

# ---- extract fired cameras + per-camera encoder ----
def extract_capture(data):
    blocks = build_block_table(data)
    zoom = None
    fired = {}  # cam_id -> encoder
    for blk in blocks:
        if blk['msg_len'] == 0: continue
        for fn, wt, raw, val in parse_proto(payload(data, blk)):
            if fn == 4 and wt == 0 and zoom is None:
                zoom = val
            elif fn == 12 and wt == 2:
                cid = enc = None
                for ifn, iwt, iraw, ival in parse_proto(raw):
                    if ifn == 2 and iwt == 0: cid = ival
                    elif ifn == 4 and iwt == 0: enc = ival
                if cid is not None:
                    fired[cid] = enc
    return zoom, fired

# ---- extract factory nominals from warp block ----
def extract_nominals(data):
    blocks = build_block_table(data)
    warp = None
    for blk in blocks:
        if 250_000 < blk['msg_len'] < 280_000:
            warp = blk; break
    if warp is None: return {}
    out = {}
    for fn, wt, raw, _ in parse_proto(payload(data, warp)):
        if fn != 13 or wt != 2: continue
        cid = None; f4_bytes = None
        for efn, ewt, eraw, ev in parse_proto(raw):
            if efn == 1 and ewt == 0: cid = ev
            elif efn == 4 and ewt == 2: f4_bytes = eraw
        if cid is None or f4_bytes is None: continue
        noms = []
        for sfn, swt, sraw, _ in parse_proto(f4_bytes):
            if sfn == 2 and swt == 2:
                for ifn, iwt, _, iv in parse_proto(sraw):
                    if ifn == 1 and iwt == 0:
                        noms.append(iv); break
        out[cid] = noms
    return out

def select_config(enc, noms):
    if not noms or len(noms) < 2:
        return 0
    return min(range(len(noms)), key=lambda i: abs(enc - noms[i]))

# ---- top-level ----
def decode(path):
    with open(path, 'rb') as f:
        data = f.read()
    zoom, fired = extract_capture(data)
    noms = extract_nominals(data)
    result = dict(zoom=zoom, cameras={})
    for cid, enc in sorted(fired.items()):
        nm = noms.get(cid, [])
        result['cameras'][cid] = dict(
            name    = CAMERA_NAMES.get(cid, f"?{cid}"),
            encoder = enc,
            nominals= nm,
            config  = select_config(enc, nm),
            movable = len(nm) >= 2,
        )
    return result

if __name__ == '__main__':
    import json
    print(json.dumps(decode(sys.argv[1]), indent=2))
```

---

## 7. Validation Across 159 Additional LRIs

Stream-scanned 159 LRIs across 6 date folders. Every capture had exactly one of these fired-camera sets:

| zoom bucket | zoom values observed | fired cameras | count |
|---|---|---|---|
| 28mm | 28, 29, 31, 33 | **A1–A5 + B1–B5** (10) | 60 |
| 35mm | 35, 44, 50, 56, 57, 58, 60 | **A1–A5 + B1–B5** (10) | 59 |
| 70mm | 70, 79 | **B1–B5 + C1–C6** (11) | 4 |
| tele | 107, 110, 120, 129, 133, 134, 135, 141, 145, 146, 149 | **B1–B5 + C1–C6** (11) | 36 |

**Key observation — the firing set has exactly two regimes separated by a sharp transition at 70mm:**
- **zoom < 70mm** → 10 cameras = 5A + 5B, **no C cameras**.
- **zoom ≥ 70mm** → 11 cameras = 5B + 6C, **no A cameras**.

No intermediate / mixed zoom mode was observed in 159 captures.

**This corrects the prior claim in `phoenix-pipeline-facts.md` that "150mm = C cameras only (6)".** Real 150mm captures fire 11 cameras (all 5 B cameras + all 6 C cameras).

### Config selection stats for B cameras (across 80 captures)

| zoom bucket | B1 | B2 | B3 | B5 |
|---|---|---|---|---|
| 28mm (z<40) | cfg2 (100%) | cfg1/cfg2 | cfg2 | cfg2 |
| 35mm (40≤z<60) | cfg0 (100%) | cfg1 (100%) | cfg0 | cfg0 |
| 70mm (60≤z<80) | cfg0 / cfg3 | cfg0 / cfg3 | cfg3 | cfg0 / cfg3 |
| 80mm≤z<140 (tele) | cfg3 (100%) | cfg0 (100%) | cfg3 | cfg3 |
| 150mm (z≥140) | cfg3 (100%) | cfg0 (100%) | cfg3 | cfg3 |

Config index varies with zoom but is **not a fixed "config 2 = wide / config 3 = tele"** rule. Each movable camera has its own nominal table, so the index that encodes "wide park" versus "tele park" is camera-specific. Phoenix MUST compute the index via argmin per camera; it cannot assume a shared constant.

---

## 8. Summary Table — Protobuf Paths

| Datum | Block | Field path | Wire type | Notes |
|---|---|---|---|---|
| Zoom focal length (mm) | image chunk 0 | `LightHeader.field_4` | varint | single value per capture |
| Fired camera IDs | image chunks 0, 2 (and 3 for telephoto) | `LightHeader.field_12[i].field_2` | varint | union across chunks = complete fired set |
| Per-camera encoder reading | image chunks 0, 2, 3 | `LightHeader.field_12[i].field_4` | varint | 0 for fixed-mirror cams, 230..900 for movables (C5/C6 always 0) |
| Per-camera factory nominal table | warp block (msg_len ≈ 262,968) | `WarpBlock.field_13[cam].field_4.field_2[i].field_1` | varint | 1 entry for fixed, 4 for movable; unchanged across captures from same unit |
| Camera id for warp entry | warp block | `WarpBlock.field_13[cam].field_1` | varint | |

### LELR block header byte layout

| Offset | Size | Field |
|---|---|---|
| 0 | 4 | `"LELR"` magic |
| 4 | 8 | total block length (u64 LE) |
| 12 | 8 | msg offset (u64 LE) |
| 20 | 4 | msg length (u32 LE) |
| 24 | 1 | msg type (u8) |

---

## 9. Open Questions (flagged, not resolved here)

1. **C5/C6 config selection.** Their encoder is always 0 → argmin is meaningless. Need LLDB trace of libcp.dylib mirror-config selection during a real render to learn the actual rule.
2. **LightHeader inner fields 5, 8, 10.** Probably exposure time, timestamp, focus step — not required for camera/config identification but would be nice to map for Phoenix metadata.
3. **ltpb schema recovery.** `libcp.dylib` embeds `LightHeader` as a class but not in the `.ltpb.X` descriptor string pool, so the `.proto` file is not directly recoverable by string scraping. Could probably be recovered from protobuf FileDescriptor tables in the dylib — out of scope for this writeup.
4. **WDR / BJPG variants.** All verified files were 2018-normal format. WDR and BJPG variants may have a different LightHeader schema — untested.
