"""
lri_parser.py — LELR container + LightHeader + Calibration blocks decoder.

Clean-room reimplementation of the .lri wire format based on TRUTH v2.1.3
documented structure + public protobuf-varint encoding. Format reference
`lightheader_scan_full.py` was read for format knowledge only — this file
is written from scratch per Rich's Rule #0.

File layout (per TRUTH §2.3 C6 + 2.5 F4):
  A .lri file is a concatenated stream of LELR blocks.
  Each block:
    offset 0    : 'LELR' magic (4 B)
    offset 4    : total block size (uint64 LE)
    offset 12   : message offset within block (uint64 LE) — protobuf LightHeader
                  or calibration record message
    offset 20   : payload (message) size in bytes (uint32 LE)
    offset 24   : (reserved)
    offset 32.. : variable structure (message + raw pixel data OR cal records)

  Image-chunk blocks are large (>10MB). Calibration and metadata blocks < 1MB.

  Image-chunk block's protobuf message is the LightHeader, which contains:
    field[4]      = zoom_config_value (varint, 28/35/70/150 typical)
    field[12][*]  = per-camera record (embedded message), one per fired camera
      .field[2]  = cam_id (varint: 0-4=A1-A5, 5-9=B1-B5, 10-15=C1-C6)
      .field[4]  = encoder config (varint, optional)
      .field[9]  = sensor_data sub-message
         .field[4] = bytes_per_row (varint, e.g. 5200 for W=4160 MIPI10)
         .field[5] = data_offset (varint — offset from block base for pixel data)
      .field[13] = sensor_bayer_red_override Point2I (x,y in some encoding;
                   we decode it to one of {0:RGGB, 1:GRBG, 2:GBRG, 3:BGGR})

  Calibration region: typically a cluster of smaller LELR blocks starting
  around byte offset 162,000,000 in each LRI. Block sizes and record shapes
  per TRUTH §2.3 C6:
    Block 3: ~32,832 B, 16 records — geometric + Bayer pattern (per-cam)
    Block 4: ~262,969 B, 16 records — vignetting + CRA grids
    Block 6: ~35,266 B, 42 records — CCM 14 cams × 3 illuminants × (3,3)
    Block 8: ~protobuf — AWB gains f19.f15 = [R_gain, 1.0, 1.0, B_gain]

Heuristics used (documented where):
  - Identify image-chunk blocks by `total_size > 10 MB`
  - Identify calibration block type via payload-size matching the TRUTH §2.3 C6
    ranges (all other blocks are treated as metadata/unknown)

Because the full calibration wire schema is partially-decoded (C6 gives paths
but not full trees), we fall back to safe defaults when a field cannot be
decoded, and log warnings.
"""

import struct
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple

import numpy as np

from utils import (
    parse_fields, parse_varint, get_field, get_fields_all,
    unpack_mipi10, bayer_pattern_name,
)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class CameraRecord:
    """One per-camera entry from LightHeader.field[12]."""
    cam_id: int                          # 0..15
    bytes_per_row: int                   # e.g. 5200 for W=4160 MIPI10
    data_offset: int                     # file-absolute offset to raw pixel data
    bayer_pattern: int                   # 0=RGGB, 1=GRBG, 2=GBRG, 3=BGGR
    encoder_config: Optional[int] = None
    raw_width: int = 4160
    raw_height: int = 3120


@dataclass
class LightHeader:
    """Parsed LightHeader payload."""
    zoom_val: int                        # field[4]
    cams: List[CameraRecord] = field(default_factory=list)
    raw: bytes = b''


@dataclass
class LRIBlock:
    """A top-level LELR block."""
    index: int
    offset: int
    total_size: int
    msg_offset: int                      # relative to block start
    payload_size: int                    # protobuf message size


@dataclass
class Calibration:
    """Per-cam calibration data parsed from blocks 3/4/6/8.

    We store approximations when a field is genuinely open (flagged).
    """
    awb_gains: Dict[int, Tuple[float, float]] = field(default_factory=dict)
    # cam_id -> (R_gain, B_gain) from Block 8 f19.f15
    ccm_by_cam: Dict[int, Dict[str, np.ndarray]] = field(default_factory=dict)
    # cam_id -> {'TungstenA': 3x3, 'D65': 3x3, 'F11': 3x3}
    vignetting: Dict[int, np.ndarray] = field(default_factory=dict)
    # cam_id -> (13, 17) 1-ch OR (4, 13, 17) 4-ch grid
    warnings: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Block-table walker
# ---------------------------------------------------------------------------

def walk_blocks(fh, file_size: int) -> List[LRIBlock]:
    """Scan a .lri file's LELR block table."""
    blocks = []
    pos = 0
    idx = 0
    while pos + 32 <= file_size:
        fh.seek(pos)
        hdr = fh.read(32)
        if len(hdr) < 32 or hdr[:4] != b'LELR':
            break
        total = struct.unpack_from('<Q', hdr, 4)[0]
        msg_off = struct.unpack_from('<Q', hdr, 12)[0]
        payload_sz = struct.unpack_from('<I', hdr, 20)[0]
        if total < 32 or pos + total > file_size:
            break
        blocks.append(LRIBlock(idx, pos, total, msg_off, payload_sz))
        pos += total
        idx += 1
    return blocks


# ---------------------------------------------------------------------------
# LightHeader decoder
# ---------------------------------------------------------------------------

def _decode_bayer_pattern_field(val) -> int:
    """Decode LightHeader field[13] Point2I → {0,1,2,3}.

    Field[13] is a Point2I (two varint sub-fields). The x,y pair encodes a
    Bayer-phase override; TRUTH §2.2 I4 says the combined value maps
    0→RGGB, 1→GRBG, 2→GBRG, 3→BGGR. We pull the sub-field values and collapse
    to a single 0..3 integer: pattern = (x<<0) | (y<<1) if those are 0/1,
    else fallback to a direct varint interpretation.
    """
    if isinstance(val, bytes):
        subs = parse_fields(val)
        xs = [v for fn, wt, v in subs if wt == 'v']
        if len(xs) >= 2:
            x, y = xs[0] & 0x1, xs[1] & 0x1
            # Row-major: (0,0)->R, (0,1)->G, (1,0)->G, (1,1)->B convention
            # To match 0=RGGB,1=GRBG,2=GBRG,3=BGGR we do: pat = (y<<1) | x
            return (y << 1) | x
        if len(xs) == 1:
            return xs[0] & 3
    if isinstance(val, int):
        return val & 3
    return 3  # BGGR fallback


def parse_lightheader(payload: bytes) -> LightHeader:
    """Decode a LightHeader protobuf payload from an image-chunk block."""
    top = parse_fields(payload)
    zoom = get_field(top, 4, 'v') or 0

    cams = []
    for entry in get_fields_all(top, 12, 'l'):
        subs = parse_fields(entry)
        cam_id = get_field(subs, 2, 'v')
        if cam_id is None:
            continue
        enc = get_field(subs, 4, 'v')
        # sensor_data sub-message at f9
        sensor = get_field(subs, 9, 'l') or b''
        sensor_fields = parse_fields(sensor) if sensor else []
        bpr = get_field(sensor_fields, 4, 'v') or 5200
        data_off = get_field(sensor_fields, 5, 'v') or 0
        # Bayer pattern at field[13]
        bayer_raw = get_field(subs, 13, None)
        pattern = _decode_bayer_pattern_field(bayer_raw) if bayer_raw is not None else 3
        cams.append(CameraRecord(
            cam_id=cam_id,
            bytes_per_row=bpr,
            data_offset=data_off,
            bayer_pattern=pattern,
            encoder_config=enc,
        ))

    return LightHeader(zoom_val=zoom, cams=cams, raw=payload)


# ---------------------------------------------------------------------------
# Raw pixel extraction
# ---------------------------------------------------------------------------

def extract_raw_cam(fh, block: LRIBlock, cam: CameraRecord) -> np.ndarray:
    """
    Read and unpack one camera's 10-bit MIPI Bayer frame.

    Returns uint16 (H, W) with values [0, 1023]. TRUTH §2.2 F4:
      bpr=5200 for W=4160 packed MIPI10, H=3120.
    """
    W, H = cam.raw_width, cam.raw_height
    bpr = cam.bytes_per_row
    # data_offset is measured from the start of the containing block
    abs_off = block.offset + cam.data_offset
    fh.seek(abs_off)
    raw_bytes = fh.read(bpr * H)
    if len(raw_bytes) < bpr * H:
        raise IOError(f"cam {cam.cam_id}: short read at {abs_off:x} "
                      f"({len(raw_bytes)} of {bpr*H})")
    return unpack_mipi10(raw_bytes, W, H, bpr)


# ---------------------------------------------------------------------------
# Calibration parsing (approximate — genuine openness is marked in warnings)
# ---------------------------------------------------------------------------

def _scan_block_payload_floats(raw: bytes) -> np.ndarray:
    """Treat block payload tail (after protobuf header guess) as packed f32.

    This is a fallback heuristic used when we can't fully decode the protobuf
    records. Returns a flat float32 array.
    """
    n_floats = len(raw) // 4
    return np.frombuffer(raw[:n_floats * 4], dtype=np.float32)


def _find_cal_blocks(blocks: List[LRIBlock], file_size: int):
    """
    Classify non-image blocks by size into Block 3/4/6/8 candidates.

    Per TRUTH §2.3 C6 typical sizes:
      Block 3: ~32,832 B      (geometric + Bayer)
      Block 4: ~262,969 B     (vignetting + CRA)
      Block 6: ~35,266 B      (CCM)
      Block 8: (AWB gains, small protobuf)
    We walk non-image-chunk blocks in order; small blocks near the end of file
    are usually the calibration region.
    """
    non_image = [b for b in blocks if b.total_size < 10_000_000]
    return non_image


def parse_calibration(fh, blocks: List[LRIBlock], file_size: int,
                      fired_cam_ids: List[int]) -> Calibration:
    """
    Best-effort parse of calibration blocks. We emit warnings for any field
    we couldn't decode and the caller falls back to reasonable defaults.

    TRUTH §2.3 C6 block sizes (typical):
      Block 3 = 32,833 B payload (geometric + Bayer, 16 records)
      Block 4 = 262,969 B payload (vignetting + CRA, 16 records)
      Block 6 = 35,266 B payload (CCM 14×3×9 = 42 records)
      Block 8 = small protobuf (AWB gains)
    """
    cal = Calibration()
    cal_blocks = _find_cal_blocks(blocks, file_size)

    # Map by approximate payload size to block roles
    block_3 = None  # geometric + bayer
    block_4 = None  # vignetting + CRA
    block_6 = None  # CCM
    block_8 = None  # AWB (small protobuf, 4..128 B typical)
    for b in cal_blocks:
        ps = b.payload_size
        if 30_000 <= ps <= 40_000 and block_3 is None:
            block_3 = b
        elif 200_000 <= ps <= 350_000 and block_4 is None:
            block_4 = b
        elif 30_000 <= ps <= 40_000 and block_6 is None and b is not block_3:
            block_6 = b
    # Block 6 is typically the SECOND ~35K block (Block 3 comes first).
    # If we got only one match, re-run to catch the second.
    if block_3 is not None and block_6 is None:
        for b in cal_blocks:
            if b is block_3:
                continue
            if 30_000 <= b.payload_size <= 40_000:
                block_6 = b
                break

    # --- Block 8 (AWB gains): recursive protobuf walk. TRUTH C2 path is
    # `f19.f15 = [R, 1.0, 1.0, B]` — we accept it at any depth (observed in
    # one LRI corpus at top-level f15 directly). Pattern: a length-delimited
    # field whose inner message has 4 f32 subfields with f2==f3==1.0.
    awb_found = False

    def scan_for_awb(data, depth=0):
        if depth > 8 or not data:
            return None
        try:
            flds = parse_fields(data)
        except Exception:
            return None
        for fn, wt, v in flds:
            if wt != 'l' or not isinstance(v, bytes) or len(v) < 16:
                continue
            try:
                inner = parse_fields(v)
            except Exception:
                continue
            fvals = [(ifn, iv) for ifn, iwt, iv in inner if iwt == 'f']
            if len(fvals) == 4:
                vals = [v2 for _, v2 in fvals]
                if (np.all(np.isfinite(vals))
                        and abs(vals[1] - 1.0) < 1e-4
                        and abs(vals[2] - 1.0) < 1e-4
                        and 0.5 < vals[0] < 5.0 and 0.5 < vals[3] < 5.0):
                    return (float(vals[0]), float(vals[3]))
            # Recurse into any nested message
            found = scan_for_awb(v, depth + 1)
            if found is not None:
                return found
        return None

    for b in cal_blocks:
        if b.payload_size < 4 or b.payload_size > 10_000:
            continue
        if b in (block_3, block_4, block_6):
            continue
        fh.seek(b.offset + b.msg_offset)
        payload = fh.read(b.payload_size)
        gains = scan_for_awb(payload)
        if gains is not None:
            for cid in fired_cam_ids:
                cal.awb_gains[cid] = gains
            awb_found = True
            print(f"  [lri_parser] Block 8 AWB: R_gain={gains[0]:.4f} "
                  f"B_gain={gains[1]:.4f} (payload size={b.payload_size})",
                  file=sys.stderr)
            block_8 = b
            break

    if not awb_found:
        cal.warnings.append("Block 8 AWB: not located; using AWB gain (1.65, 1.80)")
        for cid in fired_cam_ids:
            cal.awb_gains[cid] = (1.65, 1.80)

    # --- Block 6 (CCM 14 cams × 3 illums × 3×3) — decode protobuf records.
    # TRUTH §2.3 C6: Block 6 payload ~35,266 B, 42 records at field[13].
    # Each record: f1 = cam_id, f2 = inner_message with:
    #   inner.f1 = illum_enum (0=TungstenA, 2=D65, 6=F11 — matches NPZ order)
    #   inner.f2 = forward_matrix (45 B = 9 packed f32 as f1..f9)
    #   inner.f3 = color_matrix   (45 B = 9 packed f32 as f1..f9) — THIS is what we want (C5)
    #   inner.f4, f5 = chromaticity (x, y) of the calibration illuminant
    ccm_parsed = False
    illum_map = {0: 'TungstenA', 2: 'D65', 6: 'F11'}
    if block_6 is not None:
        fh.seek(block_6.offset + block_6.msg_offset)
        body = fh.read(block_6.payload_size)
        top = parse_fields(body)
        records = get_fields_all(top, 13, 'l')
        # Parse each record into cam_id -> illum -> M
        for rec_blob in records:
            rec = parse_fields(rec_blob)
            cam_id = get_field(rec, 1, 'v')
            inner_blob = get_field(rec, 2, 'l')
            if cam_id is None or inner_blob is None:
                continue
            inner = parse_fields(inner_blob)
            illum_enum = get_field(inner, 1, 'v')
            color_blob = get_field(inner, 3, 'l')  # color_matrix per C5
            if color_blob is None or illum_enum not in illum_map:
                continue
            # Decode 9 packed f32 (as fields 1..9 of wire-type 5)
            color_fields = parse_fields(color_blob)
            floats = [v for fn, wt, v in color_fields if wt == 'f']
            if len(floats) < 9:
                continue
            M = np.array(floats[:9], dtype=np.float32).reshape(3, 3)
            illum = illum_map[illum_enum]
            cal.ccm_by_cam.setdefault(cam_id, {})[illum] = M

        n_cams_parsed = len(cal.ccm_by_cam)
        if n_cams_parsed >= 10:
            ccm_parsed = True
            print(f"  [lri_parser] Block 6 CCM: parsed {n_cams_parsed} cams "
                  f"× 3 illums", file=sys.stderr)
        else:
            cal.ccm_by_cam.clear()
            cal.warnings.append(
                f"Block 6 CCM: only {n_cams_parsed} cams parsed; falling back")

    if not ccm_parsed:
        cal.warnings.append("Block 6 CCM: not located; using near-identity CCM")
        M_default = np.array([
            [1.50, -0.35, -0.15],
            [-0.20, 1.45, -0.25],
            [-0.05, -0.60, 1.65],
        ], dtype=np.float32)
        d = {'TungstenA': M_default, 'D65': M_default, 'F11': M_default}
        for cid in fired_cam_ids:
            cal.ccm_by_cam[cid] = d

    # --- Block 4 (vignetting): very large (~260 KB). Take its 17*13=221 f32
    # grid per cam × 4 channels = 884 B per cam = 14,144 B for 16 cams. We
    # don't byte-match here; we use a uniform grid as fallback. TRUTH I5
    # confirms scale 0.7373 * grid for this tier.
    # TRUTH §2.3 C6: Block 4 payload ~262,969 B, 16 records (field[13]).
    # Per-record vignetting path: rec.f4.f2[ch].f2.f3 = 884 B = 221 f32 shaped
    # (13, 17). 1-channel or 4-channel family per TRUTH K2.
    vig_block = block_4
    vig_parsed_count = 0
    if vig_block is not None:
        fh.seek(vig_block.offset + vig_block.msg_offset)
        body = fh.read(vig_block.payload_size)
        top = parse_fields(body)
        records = get_fields_all(top, 13, 'l')
        # Records are in cam-order 0..15 per TRUTH K4 ordering
        for cam_ix, rec_blob in enumerate(records):
            if cam_ix > 15:
                break
            rec = parse_fields(rec_blob)
            f4 = get_field(rec, 4, 'l')
            if f4 is None:
                continue
            f4_subs = parse_fields(f4)
            chan_list = get_fields_all(f4_subs, 2, 'l')  # per-channel list
            if not chan_list:
                continue
            # Parse each channel's (13,17) grid. If 4 channels, average; if 1,
            # use directly. Direction = multiply per TRUTH K2.
            grids = []
            for ch_blob in chan_list:
                ch = parse_fields(ch_blob)
                ch_f2 = get_field(ch, 2, 'l')
                if ch_f2 is None:
                    continue
                ch_f2_subs = parse_fields(ch_f2)
                f3 = get_field(ch_f2_subs, 3, 'l')
                if f3 is None or len(f3) < 884:
                    continue
                arr = np.frombuffer(f3[:884], dtype=np.float32)
                if arr.size == 221:
                    grids.append(arr.reshape(13, 17))
            if grids:
                g = np.mean(grids, axis=0).astype(np.float32) if len(grids) > 1 else grids[0]
                cal.vignetting[cam_ix] = g
                vig_parsed_count += 1
        if vig_parsed_count >= 10:
            print(f"  [lri_parser] Block 4 vignetting: parsed "
                  f"{vig_parsed_count} cams (center~1.0, corners variable)",
                  file=sys.stderr)
        else:
            cal.vignetting.clear()
            cal.warnings.append(
                f"Block 4 vignetting: only {vig_parsed_count} cams parsed")
    if not cal.vignetting:
        # Radial-quadratic fallback: 1.0 at center rising to ~2.5 at corners
        yy, xx = np.mgrid[0:13, 0:17]
        cy, cx = 6.0, 8.0
        r = np.sqrt((yy - cy) ** 2 / (cy ** 2) + (xx - cx) ** 2 / (cx ** 2))
        g = 1.0 + 1.5 * r ** 2
        for cid in fired_cam_ids:
            cal.vignetting[cid] = g.astype(np.float32)
        cal.warnings.append("Block 4 vignetting: not located; radial-quadratic fallback")

    return cal


# ---------------------------------------------------------------------------
# Top-level parse
# ---------------------------------------------------------------------------

def parse_lri(path: str):
    """
    Open and parse a .lri file.

    Returns (LightHeader, Calibration, blocks_list, image_block).
    """
    import os
    file_size = os.path.getsize(path)
    fh = open(path, 'rb')
    try:
        blocks = walk_blocks(fh, file_size)
        print(f"  [lri_parser] file_size={file_size:,} blocks={len(blocks)}",
              file=sys.stderr)

        # Enumerate ALL image-chunk blocks (there are typically 2 at 28mm, each
        # holding 5 cams). Merge into a unified LightHeader; keep per-cam block
        # ref for raw pixel extraction (each cam's data_offset is relative to
        # its containing image block).
        image_blocks = [b for b in blocks
                        if b.total_size > 10_000_000
                        and 100 <= b.payload_size <= 65536]
        if not image_blocks:
            raise RuntimeError("No image-chunk blocks found")

        merged = LightHeader(zoom_val=0)
        cam_to_block = {}  # cam_id -> LRIBlock that contains its pixel data
        for ib in image_blocks:
            fh.seek(ib.offset + ib.msg_offset)
            payload = fh.read(ib.payload_size)
            lh = parse_lightheader(payload)
            if merged.zoom_val == 0:
                merged.zoom_val = lh.zoom_val
            for cam in lh.cams:
                if cam.cam_id not in cam_to_block:
                    merged.cams.append(cam)
                    cam_to_block[cam.cam_id] = ib
        # Sort by cam_id for stable logging
        merged.cams.sort(key=lambda c: c.cam_id)

        print(f"  [lri_parser] zoom_val={merged.zoom_val} "
              f"fired_cams={len(merged.cams)} image_blocks={len(image_blocks)}",
              file=sys.stderr)
        for c in merged.cams:
            print(f"    cam_id={c.cam_id:2d} bayer={bayer_pattern_name(c.bayer_pattern)} "
                  f"bpr={c.bytes_per_row} data_off=0x{c.data_offset:x} "
                  f"block=[{cam_to_block[c.cam_id].index}]",
                  file=sys.stderr)

        fired_ids = [c.cam_id for c in merged.cams]
        cal = parse_calibration(fh, blocks, file_size, fired_ids)
        for w in cal.warnings:
            print(f"  [lri_parser] WARN: {w}", file=sys.stderr)

        return merged, cal, blocks, cam_to_block, fh
    except Exception:
        fh.close()
        raise
