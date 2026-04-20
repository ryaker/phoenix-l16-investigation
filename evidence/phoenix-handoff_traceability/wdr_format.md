# WDR LRI Format — Investigation Findings
**Date:** 2026-04-13
**Status:** CLOSED — **No dedicated WDR format exists in LRI.** HDR/WDR is a render-time tone-mapping operation, not a capture-time bracket format. The catalog label "WDR" is a misnomer.

---

## TL;DR

**Phoenix does not need a WDR-specific parser.** The "WDR" class in `lri_catalog.db` (3,242 files) is a chunk0_len heuristic (`< 70 MB`) that catches zoom/firmware variants with full-sensor readout — *not* dual-exposure or bracketed captures. No LRI file format variant encodes per-camera exposure brackets.

HDR/WDR rendering is applied in the **ISP tone-adjust stage** via `lt::ExposureFusion(...)`, which operates on a **single exposure** already in the render pipeline. The four `HDR_MODE_{NONE,DEFAULT,NATURAL,SURREAL}` enum values live in `.ltpb.ViewPreferences.HDRMode` — they are user rendering preferences, not capture metadata.

---

## Evidence

### 1. No HDR/WDR/bracket symbols in libcp
Searched `/Volumes/Dev/lumen-phoenix-scratch/q123/strings_all.txt` for: `WDR`, `wdr_`, `wide_dynamic`, `widedynamic`, `bracket`, `multi_exposure`, `multi_frame`, `mf_hdr`, `exposure_bracket`. **No matches.** Only matches are `.ltpb.ViewPreferences.HDRMode` (render-preference enum) and `exposure_fusion` (listed alongside `tone-adjust`, `shadow_highlight`, `laplacian_pyramid` as an ISP pipeline stage name).

### 2. ExposureFusion is a pipeline-stage kernel, not a format
From `lumen_side_analysis.md`:
```
lt::ExposureFusion(Image<vec4x32f>& dst, const Image<vec4x32f>& src, float weight, const ExposureFusionParam&)
```
Signature is `src → dst` on a **single image** with a scalar weight. No signature reads multiple brackets. It implements a tone-mapping pyramid on already-demosaicked RGB — it does not merge separate raw exposures from LRI. Sits at pipeline stage `tone-adjust` (stage 14-ish), post-fusion.

### 3. The catalog "WDR" label is a heuristic misnomer
From `catalog_worker_2017.py`:
```python
elif block0_len < 70_000_000:
    return 'WDR', 0, 0
```
This labels any file with chunk0_len below 70 MB as "WDR" without inspecting content. Verified by parsing 30+ "WDR" files — they all have standard LightHeader protobuf, standard `W=4160, H=3120, bpr=5200` sensor-mode fields, and standard per-camera records. No field distinguishes them from 2018-normal as "HDR-enabled".

### 4. What the "WDR" cluster actually is
Three sub-clusters, classified by firmware version read from LightHeader byte field:

| chunk0_len | Files | Firmware | Cam chunks | Per-cam bytes | Cameras | Notes |
|------------|-------|----------|------------|---------------|---------|-------|
| 68,157,472 | 1,295 | 0.1.7530 / 0.1.61140 / 0.1.64229 | 4+3+4 = 11 | 16,777,224 (~16 MiB) | 11 | Very early firmware, 70mm zoom (5B+6C) |
| 67,110,254 ±4 | ~570 | 0.1.57498 | 4+3+4 = 11 | 16,777,224 | 11 | Same as the `oqe_unknown_format.md` firmware; 70mm zoom |
| 64,914,7xx ±30 | ~1,377 | 1.0.16965 / 1.0.53531 | 4+3+4 = 11 | 16,228,384 first-cam, 16,228,352 rest | 11 | Production firmware, 70mm zoom, tighter per-cam packing |

All three variants share:
- **3 camera-data LELR chunks** (vs 2017-normal/2018-normal which have 2 chunks)
- **11 cameras total** (split 4+3+4 across the three chunks)
- **Full 3120-row readout** (vs 2018-normal 1950 rows)
- **10-bit MIPI-packed Bayer**, `bpr = 4160×10/8 = 5200`
- Standard 5 calibration LELR blocks at the file tail (geo/vig+CRA/CCM/lut/stats)

The **11-camera layout** matches Phoenix's documented **70mm zoom mode** (5B + 6C cameras). The 2018-normal format (5-cam chunks) matches **28mm / 35mm** mode (5A-only per chunk, 2 chunks = 10 cams).

### 5. Per-camera LightHeader fields (confirmed via protobuf walk)
Each `f12` record (one per camera) in the LightHeader contains:
- `f2` = camera index (6, 8, 9, 14, ...)
- `f5` = exposure time (µs) — e.g. 1402, 1452, 1380, 693 **varies per camera for auto-exposure metering, NOT bracket pairs**. Values are spread by per-camera stats, not dual short/long.
- `f7` = analog gain (f32, e.g. 1.438)
- `f8` = raw_exposure integer (capture counter or equivalent)
- `f9.f2` = sensor W/H = 4160/3120
- `f9.f4` = bpr = 5200
- `f9.f5` = absolute byte offset of this camera's data within the chunk payload

No `f12` subfield encodes "this camera is the long/short exposure of a bracket pair".

---

## Header detection (how Phoenix should classify)

Phoenix should **not** use `chunk0_len < 70 MB` as a WDR indicator. Correct flow:

```python
# Read chunk0 header
cl  = u64_le(data, 4)    # chunk_len
o12 = u64_le(data, 12)   # camera_data_bytes
o20 = u64_le(data, 20)   # LightHeader size

# Parse LightHeader, extract firmware string (matches r'[01]\.[01]\.\d+ \d+Z')
fw = extract_firmware(data[32+o12 : 32+o12+o20])

# Walk chunks from file start; for each chunk with o12 > 1 MB, read per-camera
# records from the chunk's LightHeader (at chunk_off + 32 + chunk_o12).
# Camera count per chunk = (chunk_o12 // per_cam_size), NOT header byte 7.

# Use LightHeader's f12[i].f9.f5 as the ABSOLUTE byte offset of camera i within
# the chunk payload — this is the authoritative placement field.
```

**Critical**: byte 7 of the chunk header was previously guessed as ncams. It is **off by one in some files and not reliable** — use `off12 / per_cam_size` or the f12 record count instead.

---

## Chunk stride / per-camera bytes

| Firmware class | Chunk count | Cam split | Per-cam stride |
|----------------|-------------|-----------|----------------|
| 2017-normal (earlier prod) | 2 | 5+5 = 10 | 10,616,832 |
| 2018-normal (`1.0.169xx`) | 2 | 5+5 = 10 | 10,142,716 |
| 0.1.x transitional (UNKNOWN 83.8M) | 3 | 8+8 = 16 | 10,485,764 |
| **"WDR" 68.1M (0.1.x early)** | 3 | **4+3+4 = 11** | **16,777,224** |
| **"WDR" 67.1M (0.1.57498)** | 3 | **4+3+4 = 11** | **16,777,224** |
| **"WDR" 64.9M (1.0.169xx)** | 3 | **4+3+4 = 11** | **16,228,384** (first), **16,228,352** (rest) |
| BJPG (post-2018-06-26) | Variable | per-JPEG | JPEG-indexed |

All three "WDR" variants are 11-cam **70mm-zoom** captures. The difference from 2018-normal is (a) camera count (11 vs 10) because 70mm activates all 6 C cameras plus 5 B cameras, and (b) full 3120-row readout (vs 1950 rows for 28mm/35mm). This matches `phoenix-pipeline-facts.md`:

> C cameras do NOT fire at 28mm
> 70mm cameras = 5B + 6C = 11

---

## Per-bracket exposure metadata

**There are no per-bracket exposures.** Each camera has a single exposure + gain. The ExposureFusion renderer operates on tone-mapped variants of the single fused image at render time, not on raw brackets from the LRI file.

**If Phoenix wants to honor `HDR_MODE_NATURAL/SURREAL`, the correct thing is:**
1. Render the normal image through the full fusion + tone-adjust pipeline.
2. Apply `ExposureFusion(src, dst, weight, ExposureFusionParam)` as a post-tone-mapping operator on a single RGB image, with `weight` driven by the HDRMode preference.
3. No additional reading from the LRI is needed.

The ExposureFusion kernel is in libcp and reads `ExposureFusionParam` from the view preferences, not from the LRI.

---

## Python decode snippet (for 11-cam "WDR" files)

```python
import struct, numpy as np

def decode_mipi10(raw_bytes, W=4160):
    # 10-bit MIPI-packed Bayer — same as 2018-normal/oqe_unknown
    u8 = np.frombuffer(raw_bytes, dtype=np.uint8).reshape(-1, 5)
    px = np.empty(u8.shape[0]*4, dtype=np.uint16)
    px[0::4] =  u8[:,0]        | ((u8[:,1] & 0x03) << 8)
    px[1::4] = (u8[:,1] >> 2)  | ((u8[:,2] & 0x0F) << 6)
    px[2::4] = (u8[:,2] >> 4)  | ((u8[:,3] & 0x3F) << 4)
    px[3::4] = (u8[:,3] >> 6)  |  (u8[:,4]          << 2)
    return px.reshape(-1, W)

def parse_wdr_chunk(f, chunk_off):
    f.seek(chunk_off)
    hdr = f.read(32)
    assert hdr[:4] == b'LELR'
    chunk_len = struct.unpack_from('<Q', hdr, 4)[0]
    o12       = struct.unpack_from('<Q', hdr, 12)[0]
    o20       = struct.unpack_from('<Q', hdr, 20)[0]

    # Read LightHeader from end of camera data region
    f.seek(chunk_off + 32 + o12)
    lh = f.read(o20)
    cams = parse_f12_records(lh)  # returns list of dicts with f9.f5 absolute offsets

    # Per-camera offsets live in f12[i].f9.f5 — authoritative
    # Compute per-cam size from consecutive offsets
    offs = sorted([c['byte_offset'] for c in cams])
    per_cam = offs[1] - offs[0] if len(offs) >= 2 else (o12 - offs[0])

    f.seek(chunk_off + 32 + offs[0])
    cam0_raw = f.read(per_cam)

    # 64.9M (1.0.x) and 68.1M/67.1M (0.1.x) both use bpr=5200, W=4160, H=3120
    # Only first H_int = 3120 rows are sensor data; tail is padding/stats
    bpr = 5200
    bayer = decode_mipi10(cam0_raw[:bpr*3120], W=4160)
    return bayer, cams

def walk_wdr_file(path):
    with open(path, 'rb') as f:
        data_len = f.seek(0, 2); f.seek(0)
        off = 0
        chunks = []
        while off + 32 <= data_len:
            hdr = f.read(32)
            if hdr[:4] != b'LELR': break
            cl = struct.unpack_from('<Q', hdr, 4)[0]
            o12 = struct.unpack_from('<Q', hdr, 12)[0]
            if o12 > 1_000_000:   # camera-data chunk, not calibration
                chunks.append(off)
            off += cl
            f.seek(off)
    # Expect 3 camera chunks totalling 11 cameras (4+3+4)
    return chunks
```

---

## Verified on

- `/Volumes/Base Photos/Light/2018-06-26/L16_01922.lri` — 1.0.16965 (64.9M cluster), 3 chunks (3+2+3 by header byte7, actually 4+3+4 = 11 cams by per-cam stride), per-cam=16,228,352
- `/Volumes/Base Photos/Light/2018-03-30/L16_01808.lri` — 0.1.57498 (67.1M cluster), 3 chunks, per-cam=16,777,224
- `/Volumes/Base Photos/Light/2017-12-01/L16_00004.lri` — 0.1.61140 (68.1M cluster), 3 chunks, per-cam=16,777,224
- `/Volumes/Base Photos/Light/2018-01-20/L16_00150.lri` — 0.1.7530 (68.1M cluster), same 4+3+4 structure
- Additional 30 random "WDR" files sampled for firmware distribution — all fall into these 3 clusters, all use standard LightHeader layout.

---

## What this unblocks for Phoenix

1. **No WDR parser needed.** The existing MIPI-10 decoder works for all these files; the only differences are (a) 3 camera-data chunks instead of 2, (b) variable cam split 4+3+4 instead of 5+5, and (c) per-camera stride that must be read from `f12.f9.f5` offsets in the LightHeader rather than assumed constant.

2. **Recommended format classification for Phoenix:** detect by `(chunk_count, chunks_per_chunk, per_cam_stride)` triple read from LightHeader, not by chunk0_len ranges. This will correctly distinguish zoom modes (10-cam 28mm vs 11-cam 70mm) and firmware eras within a single parse.

3. **HDR_MODE rendering:** implement as a post-tone-mapping `ExposureFusion` pass on the already-fused RGB canvas, driven by a render-time `HDRMode` parameter (NONE=skip, DEFAULT/NATURAL/SURREAL = different weight params). The LRI file itself does not influence this decision — it is a user preference applied in the render pipeline.

4. **Action item (followup, not blocker):** verify the `ExposureFusionParam` struct layout from libcp RTTI so Phoenix can populate it correctly for each HDR_MODE. The struct is referenced by `lt::ExposureFusion(..., const ExposureFusionParam&)` — see `/Volumes/Dev/lumen-phoenix-scratch/libcp_demangled_internals.txt` for RTTI.

---

## Open questions (low priority)

- Does **any** L16 capture mode actually perform a physical exposure-bracket (two raw reads at different shutter times)? The evidence says no — ExposureFusion is entirely software. But confirming that the AR1335 sensor driver never issues a dual-integration readout would close this question definitively. (Source: Android APK camera HAL, not in this investigation's scope.)
- The `f8` field in per-camera records (values 1.2M–6.6M) is not decoded. Not needed for pixel decode — likely a capture timestamp or raw-exposure register value. Document if it becomes relevant for post-processing.

---

## Confidence

- No format-level WDR exists: **Verified** — no strings, no symbols, no per-camera bracket metadata, ExposureFusion signature reads single `src`.
- "WDR" catalog label is a chunk0_len heuristic misnomer: **Verified** — source in `catalog_worker_2017.py`, matches 3,242-file cluster.
- 11-camera 70mm zoom explanation: **Verified indirect** — cam count matches Phoenix facts doc; per-cam stride divides cleanly by 11; LightHeader f12 records enumerate 11 cameras with indices from the B/C banks.
- Per-camera stride values: **Verified** — off12/11 arithmetic exact for 64.9M and 68.1M clusters.
- ExposureFusion is a post-fusion pipeline stage: **Verified** — `exposure_fusion` listed next to `tone-adjust`/`shadow_highlight` in ISP stage strings; function signature takes single `src` image.
