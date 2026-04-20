#!/usr/bin/env python3
"""Tool #2 — LRI Manifest Builder
Walk an LRI directory, extract per-file metadata, output queryable CSV manifest.
Uses existing lri_protobuf_walker.py as parser.
"""

import argparse
import csv
import json
import os
import struct
import sys
import time
from pathlib import Path

# Add phoenix-handoff/decoders to path for lri_protobuf_walker
REPO_ROOT = Path(__file__).parent.parent
WALKER_DIR = REPO_ROOT / "phoenix-handoff" / "decoders"
sys.path.insert(0, str(WALKER_DIR))

try:
    from lri_protobuf_walker import LRIFile, ProtoReader
    HAS_WALKER = True
except ImportError:
    HAS_WALKER = False

CACHE_FILENAME = ".manifest_cache.json"

CSV_FIELDS = [
    "lri_path", "size_mb", "date", "focal_tier",
    "ref_cam", "n_cameras", "fired_cams", "hdr_hint",
    "iso_min", "iso_max", "parse_error"
]

# LightHeader field numbers (per HwInfo agent renumbering finding)
FIELD_FOCAL_LENGTH   = 4
FIELD_REF_CAMERA     = 5
FIELD_CAMERA_MODULES = 12   # repeated CameraModule
FIELD_SENSOR_DATA    = 16   # repeated SensorData / Block 8 exposures

# CameraModule sub-fields
CAM_FIELD_ID        = 1
CAM_FIELD_ISO       = 10    # ISO speed (heuristic — may vary)

def focal_tier(mm: int) -> str:
    """Map focal length to L16 tier using midpoint boundaries."""
    if mm <= 31:   return "28mm"
    if mm <= 52:   return "35mm"
    if mm <= 110:  return "70mm"
    return "150mm"


def parse_lri_native(lri_path: Path) -> dict:
    """Parse LRI using lri_protobuf_walker. Returns dict of extracted fields."""
    row = {
        "lri_path": str(lri_path),
        "size_mb": round(lri_path.stat().st_size / (1024 * 1024), 2),
        "date": "",
        "focal_tier": "",
        "ref_cam": "",
        "n_cameras": "",
        "fired_cams": "",
        "hdr_hint": "",
        "iso_min": "",
        "iso_max": "",
        "parse_error": ""
    }

    # Date from path (YYYY-MM-DD directory component)
    for part in lri_path.parts:
        if len(part) == 10 and part[4] == '-' and part[7] == '-':
            row["date"] = part
            break

    try:
        lri = LRIFile(str(lri_path))
        blocks = lri.blocks if hasattr(lri, 'blocks') else []

        if not blocks:
            row["parse_error"] = "no_blocks"
            return row

        # Block 0 = LightHeader
        header_block = blocks[0]
        reader = ProtoReader(header_block.payload if hasattr(header_block, 'payload')
                             else header_block.data)

        focal_mm = None
        ref_cam = None
        cam_ids = []
        iso_values = []
        exposure_counts = {}

        for field_num, wire_type, value in reader.fields():
            if field_num == FIELD_FOCAL_LENGTH:
                focal_mm = int(value)
            elif field_num == FIELD_REF_CAMERA:
                ref_cam = int(value)
            elif field_num == FIELD_CAMERA_MODULES:
                # value is bytes for sub-message
                sub = ProtoReader(value)
                cam_id = None
                iso = None
                for sf, sw, sv in sub.fields():
                    if sf == CAM_FIELD_ID:
                        cam_id = int(sv)
                    elif sf == CAM_FIELD_ISO:
                        iso = int(sv)
                if cam_id is not None:
                    cam_ids.append(cam_id)
                if iso is not None:
                    iso_values.append(iso)
            elif field_num == FIELD_SENSOR_DATA:
                # Count distinct exposures — heuristic HDR hint
                # Just count repeated SensorData entries as exposure frames
                exp_key = "sensor"
                exposure_counts[exp_key] = exposure_counts.get(exp_key, 0) + 1

        if focal_mm is not None:
            row["focal_tier"] = focal_tier(focal_mm)
        if ref_cam is not None:
            row["ref_cam"] = str(ref_cam)
        row["n_cameras"] = str(len(cam_ids))
        row["fired_cams"] = "[" + ",".join(str(c) for c in sorted(cam_ids)) + "]"
        row["hdr_hint"] = str(len(exposure_counts))
        if iso_values:
            row["iso_min"] = str(min(iso_values))
            row["iso_max"] = str(max(iso_values))

    except Exception as e:
        row["parse_error"] = str(e)[:120]

    return row


def read_varint_bytes(data: bytes, pos: int):
    result = 0; shift = 0
    while pos < len(data):
        b = data[pos]; pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, pos
        shift += 7
    return result, pos


def skip_proto_field(wire_type: int, data: bytes, pos: int) -> int:
    if wire_type == 0:
        _, pos = read_varint_bytes(data, pos)
    elif wire_type == 1:
        pos += 8
    elif wire_type == 2:
        length, pos = read_varint_bytes(data, pos)
        pos += length
    elif wire_type == 5:
        pos += 4
    return pos


def extract_cam_id_from_module(sub: bytes) -> int | None:
    """Extract camera_id (field 2) from a LightHeader.field_12 sub-message."""
    pos = 0
    while pos < len(sub):
        try:
            tag, pos = read_varint_bytes(sub, pos)
        except Exception:
            break
        field_num = tag >> 3; wire_type = tag & 0x7
        if field_num == 2 and wire_type == 0:
            val, pos = read_varint_bytes(sub, pos)
            return val
        pos = skip_proto_field(wire_type, sub, pos)
    return None


def parse_lri_blocks(lri_path: Path):
    """Yield (block_offset, total_len, msg_offset, msg_len, msg_type) per LELR block.
    LELR header (32 bytes):
      [0:4]   magic "LELR"
      [4:12]  total_block_len (u64 LE)
      [12:20] msg_offset (u64 LE)  — offset from block start to proto payload
      [20:24] msg_len (u32 LE)
      [24]    msg_type (u8)
    """
    file_size = lri_path.stat().st_size
    with open(lri_path, 'rb') as f:
        pos = 0
        while pos < file_size:
            f.seek(pos)
            hdr = f.read(32)
            if len(hdr) < 32 or hdr[0:4] != b'LELR':
                break
            total_len  = struct.unpack_from('<Q', hdr, 4)[0]
            msg_offset = struct.unpack_from('<Q', hdr, 12)[0]
            msg_len    = struct.unpack_from('<I', hdr, 20)[0]
            msg_type   = hdr[24]
            if total_len == 0:
                break
            yield (pos, total_len, msg_offset, msg_len, msg_type)
            pos += total_len


def read_light_header_proto(lri_path: Path, block_offset: int, msg_offset: int, msg_len: int) -> bytes:
    """Read the LightHeader proto bytes from a block."""
    with open(lri_path, 'rb') as f:
        f.seek(block_offset + msg_offset)
        return f.read(msg_len)


def parse_lri_fallback(lri_path: Path) -> dict:
    """Parse LRI using direct binary reading of the LELR block format.
    LightHeader proto is at block_offset + msg_offset (end of image chunks).
    field 4 (varint) = focal_length_mm
    field 12 (repeated bytes) = per-camera sub-message, sub-field 2 = camera_id
    """
    row = {
        "lri_path": str(lri_path),
        "size_mb": round(lri_path.stat().st_size / (1024 * 1024), 2),
        "date": "",
        "focal_tier": "",
        "ref_cam": "",
        "n_cameras": "",
        "fired_cams": "",
        "hdr_hint": "",
        "iso_min": "",
        "iso_max": "",
        "parse_error": ""
    }

    for part in lri_path.parts:
        if len(part) == 10 and part[4] == '-' and part[7] == '-':
            row["date"] = part
            break

    try:
        focal_mm = None
        cam_ids = []
        n_img_blocks = 0

        for blk_off, total_len, msg_off, msg_len, msg_type in parse_lri_blocks(lri_path):
            if msg_len == 0 or msg_len > 50000:
                continue
            # Image chunk blocks: msg_offset >> 32 means proto is at end of large block
            # All blocks carry a LightHeader proto at msg_offset; we read them all.
            try:
                payload = read_light_header_proto(lri_path, blk_off, msg_off, msg_len)
            except Exception:
                continue

            pos = 0
            while pos < len(payload):
                try:
                    tag, pos = read_varint_bytes(payload, pos)
                except Exception:
                    break
                field_num = tag >> 3; wire_type = tag & 0x7
                if field_num == FIELD_FOCAL_LENGTH and wire_type == 0:
                    focal_mm, pos = read_varint_bytes(payload, pos)
                elif field_num == FIELD_CAMERA_MODULES and wire_type == 2:
                    length, pos = read_varint_bytes(payload, pos)
                    sub = payload[pos:pos+length]
                    pos += length
                    cam_id = extract_cam_id_from_module(sub)
                    if cam_id is not None:
                        cam_ids.append(cam_id)
                else:
                    pos = skip_proto_field(wire_type, payload, pos)

            n_img_blocks += 1
            # Only first 3 image-chunk blocks needed
            if n_img_blocks >= 3 and focal_mm is not None:
                break

        if focal_mm is not None:
            row["focal_tier"] = focal_tier(focal_mm)
        row["n_cameras"] = str(len(cam_ids))
        row["fired_cams"] = "[" + ",".join(str(c) for c in sorted(set(cam_ids))) + "]"

    except Exception as e:
        row["parse_error"] = str(e)[:120]

    return row


def parse_lri(lri_path: Path) -> dict:
    if HAS_WALKER:
        return parse_lri_native(lri_path)
    return parse_lri_fallback(lri_path)


def load_cache(cache_path: Path) -> dict:
    if cache_path.exists():
        try:
            with open(cache_path) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_cache(cache_path: Path, cache: dict):
    try:
        with open(cache_path, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception as e:
        print(f"[WARN] cache write failed: {e}", file=sys.stderr)


def build_manifest(lri_root: Path, output_path: Path, rebuild: bool = False):
    lri_files = sorted(lri_root.rglob("*.lri"))
    if not lri_files:
        print(f"[WARN] No .lri files found under {lri_root}", file=sys.stderr)

    cache_path = lri_root / CACHE_FILENAME
    cache = {} if rebuild else load_cache(cache_path)

    rows = []
    updated = 0

    for lri_path in lri_files:
        key = str(lri_path)
        mtime = lri_path.stat().st_mtime
        cache_entry = cache.get(key)

        if cache_entry and cache_entry.get("mtime") == mtime:
            rows.append(cache_entry["row"])
            continue

        print(f"  parsing {lri_path.name} ...", file=sys.stderr)
        row = parse_lri(lri_path)
        cache[key] = {"mtime": mtime, "row": row}
        rows.append(row)
        updated += 1

    save_cache(cache_path, cache)

    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] {len(rows)} LRIs → {output_path}  ({updated} re-parsed)", file=sys.stderr)
    return rows


def main():
    parser = argparse.ArgumentParser(description="LRI Manifest Builder")
    parser.add_argument("--lri-root", required=True, help="Root directory of LRI captures")
    parser.add_argument("--output", required=True, help="Output CSV path")
    parser.add_argument("--rebuild", action="store_true", help="Ignore cache, re-parse all")
    args = parser.parse_args()

    lri_root = Path(args.lri_root)
    if not lri_root.exists():
        print(f"[ERROR] lri-root not found: {lri_root}", file=sys.stderr)
        sys.exit(1)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = build_manifest(lri_root, output_path, rebuild=args.rebuild)

    # Print summary to stdout
    focal_counts = {}
    errors = 0
    for row in rows:
        t = row.get("focal_tier") or "unknown"
        focal_counts[t] = focal_counts.get(t, 0) + 1
        if row.get("parse_error"):
            errors += 1

    print(f"\nManifest summary:")
    print(f"  Total LRIs : {len(rows)}")
    for tier in sorted(focal_counts):
        print(f"  {tier:8s} : {focal_counts[tier]}")
    if errors:
        print(f"  parse errors: {errors}")


if __name__ == "__main__":
    main()
