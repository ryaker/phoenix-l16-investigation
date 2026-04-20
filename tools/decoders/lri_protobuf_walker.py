#!/usr/bin/env python3
"""
session2_awb_mode_scan.py — Scan LRI corpus for awb_mode distribution,
verify whether non-AUTO captures still populate auto_white_balance.neutral_color.

Based on awb_analysis.py parser (reuses protobuf utilities).

Block 8 layout (from awb_analysis.txt):
  Block 8 payload (~54 bytes, per-capture)
  Contains sub-messages for AWB fields.
  Key fields:
    f19.f15.{f1,f4} = [R_gain, B_gain]
    f19.f16         = mode flag (observed = 0 = AUTO?)
  The auto_white_balance sub-message (protobuf field key) contains:
    .type          = AWBMode enum (0-8)
    .neutral_color = Vec2 (x, y) chromaticity
    .neutral_temp  = int K
    .neutral_tint  = float
  The configurator at 0x13eda0 reads these from a bitmask (bits 0x4/0x8/0x2).
"""

import os
import struct
import sys
import math
import glob
from collections import defaultdict

# Reuse parser utilities inline (no import to avoid path issues)

def read_varint(data, offset):
    result = 0; shift = 0
    while offset < len(data):
        b = data[offset]; offset += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return result, offset


def parse_fields(data):
    fields = []; offset = 0
    while offset < len(data):
        try:
            tag, offset = read_varint(data, offset)
        except Exception:
            break
        wire_type = tag & 0x07
        field_number = tag >> 3
        if field_number == 0:
            break
        if wire_type == 2:
            try:
                length, offset = read_varint(data, offset)
            except Exception:
                break
            if offset + length > len(data):
                break
            sub = data[offset:offset + length]
            fields.append((field_number, 'len', sub))
            offset += length
        elif wire_type == 0:
            try:
                val, offset = read_varint(data, offset)
            except Exception:
                break
            fields.append((field_number, 'varint', val))
        elif wire_type == 5:
            if offset + 4 > len(data):
                break
            val = struct.unpack_from('<f', data, offset)[0]
            fields.append((field_number, 'f32', val))
            offset += 4
        elif wire_type == 1:
            if offset + 8 > len(data):
                break
            val = struct.unpack_from('<d', data, offset)[0]
            fields.append((field_number, 'd64', val))
            offset += 8
        else:
            break
    return fields


def scan_lelr_blocks(file_data, limit=50):
    blocks = []; pos = 0; idx = 0
    while pos + 32 <= len(file_data) and file_data[pos:pos+4] == b'LELR':
        total_size = struct.unpack_from('<I', file_data, pos+4)[0]
        payload_size = struct.unpack_from('<I', file_data, pos+20)[0]
        payload_offset = pos + 32
        payload = file_data[payload_offset: payload_offset + payload_size]
        blocks.append({
            'idx': idx,
            'off': pos,
            'total': total_size,
            'size': payload_size,
            'payload': payload,
        })
        if total_size == 0:
            break
        pos += total_size
        idx += 1
        if idx > limit:
            break
    return blocks


def flatten_fields(data, path="", out=None, depth=0):
    """Recursively flatten all fields into path -> (wt, val) mapping.
    out is a list of (path, wt, val).
    """
    if out is None:
        out = []
    if depth > 10:
        return out
    try:
        fields = parse_fields(data)
    except Exception:
        return out
    for fn, wt, val in fields:
        p = f"{path}.f{fn}" if path else f"f{fn}"
        out.append((p, wt, val))
        if wt == 'len' and len(val) > 0 and len(val) < 100000:
            # Try to parse as sub-message (if it's not, parse_fields returns [])
            flatten_fields(val, p, out, depth+1)
    return out


# Block 8 is the small per-capture AWB block (~40-80 bytes).
# Block 1 is also small but contains ISO/exposure (varint-heavy).
# We'll identify Block 8 by size and content heuristics.

def identify_awb_block(blocks):
    """Find the block containing AWB per-capture data.
    Strategy: smallest block with f19 sub-message containing f15 (float array).
    """
    candidates = []
    for b in blocks:
        if b['size'] < 4 or b['size'] > 1000:
            continue
        try:
            flat = flatten_fields(b['payload'])
        except Exception:
            continue
        paths = {p for p, _, _ in flat}
        # Block 8 has f19.f15.f1 etc per awb_analysis
        if any(p.startswith('f19.f15') for p in paths):
            candidates.append(b)
    if candidates:
        # Prefer smallest
        return min(candidates, key=lambda b: b['size'])
    return None


AWB_MODE_NAMES = {
    0: "AUTO",
    1: "DAYLIGHT",
    2: "SHADE",
    3: "CLOUDY",
    4: "TUNGSTEN",
    5: "FLUORESCENT",
    6: "FLASH",
    7: "CUSTOM",
    8: "KELVIN",
}


def extract_awb_info(file_data):
    """Extract AWB info from an LRI.
    Returns dict with: mode (int or None), mode_name, neutral_color (tuple or None),
    neutral_temp (int or None), neutral_tint (float or None), gains (R,B), block8_found.
    """
    blocks = scan_lelr_blocks(file_data)
    awb_block = identify_awb_block(blocks)
    info = {
        'block8_found': awb_block is not None,
        'block8_idx': awb_block['idx'] if awb_block else None,
        'block8_size': awb_block['size'] if awb_block else None,
        'mode': None,
        'mode_name': None,
        'neutral_color': None,
        'neutral_temp': None,
        'neutral_tint': None,
        'gains_R': None,
        'gains_B': None,
        'all_varints_in_range': [],
        'all_floats': [],
        'all_paths': [],
    }
    if not awb_block:
        return info
    flat = flatten_fields(awb_block['payload'])
    info['all_paths'] = [(p, wt, val if wt != 'len' else f"<{len(val)}B>") for p, wt, val in flat]

    # AWB gains: f19.f15.f1 (R), f19.f15.f4 (B)
    for p, wt, val in flat:
        if p == 'f19.f15.f1' and wt == 'f32':
            info['gains_R'] = val
        if p == 'f19.f15.f4' and wt == 'f32':
            info['gains_B'] = val

    # Look for awb_mode varint. Based on 0x13eda0 evidence:
    # struct+0x24 gets AWB mode (compared against 9), struct+0x2c gets type (compared against 8).
    # In the protobuf, awb_mode should be a varint field at the top level of Block 8
    # or nested under the AWB sub-message. Field numbers are unknown; we scan all varints.
    # Valid AWB mode values: 0..8.
    for p, wt, val in flat:
        if wt == 'varint' and 0 <= val <= 8:
            info['all_varints_in_range'].append((p, val))

    # The neutral_color sub-message — look for any len field containing
    # exactly 2 floats (x, y chromaticity). Or the configurator reads
    # (int_temp, float_midpoint*0.5, int_tint) at sub-proto offsets +0x14/0x18/0x1c.
    # In proto wire format, neutral_color would be a nested sub-message with
    # two f32 fields (f1=x, f2=y) typically.

    # Search for path candidates matching (x,y) pattern - floats in chromaticity range
    # Chromaticity (x,y) is typically in [0.1, 0.7]
    candidates_xy = []
    for p, wt, val in flat:
        if wt == 'len' and 8 <= len(val) <= 32:
            subflat = flatten_fields(val)
            floats = [(sp, sv) for sp, swt, sv in subflat if swt == 'f32']
            if len(floats) == 2:
                x, y = floats[0][1], floats[1][1]
                if 0.1 <= x <= 0.7 and 0.1 <= y <= 0.7:
                    candidates_xy.append((p, x, y))
    info['neutral_color_candidates'] = candidates_xy

    # Look for neutral_temp (int K, typically 2000-10000)
    for p, wt, val in flat:
        if wt == 'varint' and 2000 <= val <= 15000:
            if info['neutral_temp'] is None:
                info['neutral_temp'] = (p, val)

    # Collect float summary
    info['all_floats'] = [(p, val) for p, wt, val in flat if wt == 'f32']
    return info


def classify_awb_mode(info):
    """From extracted info, infer awb_mode value.
    Heuristic: mode is likely a top-level varint in Block 8 outside f19.
    The configurator reads mode at struct+0x24, type at struct+0x2c.
    """
    # Find varints with value 0..8 that are NOT under f19 (which is sensor data)
    # Try specific field candidates first
    mode_candidates = []
    for p, v in info['all_varints_in_range']:
        # Skip known sensor sub-message f19 subfields
        if 'f19' in p:
            continue
        mode_candidates.append((p, v))
    return mode_candidates


def process_file(path):
    try:
        with open(path, 'rb') as f:
            file_data = f.read()
    except Exception as e:
        return None
    return extract_awb_info(file_data)


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────

def main():
    # Phase 1: Process the 6 known production LRIs deeply
    known = [
        "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri",
        "/Volumes/Base Photos/Light/2018-10-23/L16_02586.lri",
        "/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri",
        "/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri",
        "/Volumes/Base Photos/Light/2018-09-26/L16_02500.lri",
        "/Volumes/Base Photos/Light/2020-07-14/L16_03460.lri",
    ]

    print("="*78)
    print("PHASE 1: DEEP SCAN OF 6 KNOWN LRIs")
    print("="*78)

    for path in known:
        if not os.path.exists(path):
            print(f"\nMISSING: {path}")
            continue
        print(f"\n--- {os.path.basename(path)} ({os.path.dirname(path).split('/')[-1]}) ---")
        info = process_file(path)
        if info is None:
            print("  FAILED to read")
            continue
        print(f"  Block8 found: {info['block8_found']} (idx={info['block8_idx']}, size={info['block8_size']})")
        print(f"  Gains: R={info['gains_R']}, B={info['gains_B']}")
        print(f"  Varints 0..8 (candidates for awb_mode):")
        for p, v in info['all_varints_in_range']:
            print(f"    {p} = {v}  ({AWB_MODE_NAMES.get(v, '?')})")
        print(f"  Neutral color (x,y) candidates: {info['neutral_color_candidates']}")
        print(f"  Neutral temp candidates: {info['neutral_temp']}")
        print(f"  All floats in Block8:")
        for p, v in info['all_floats'][:30]:
            print(f"    {p} = {v:.6f}")
        print(f"  All paths ({len(info['all_paths'])}):")
        for p, wt, v in info['all_paths'][:60]:
            if wt == 'f32':
                print(f"    {p}: f32 = {v:.6f}")
            elif wt == 'varint':
                print(f"    {p}: varint = {v}")
            else:
                print(f"    {p}: {wt} {v}")

    # Phase 2: Batch scan a large sample to find non-AUTO captures
    print("\n" + "="*78)
    print("PHASE 2: BATCH SCAN — search for non-AUTO captures")
    print("="*78)

    all_lris = glob.glob("/Volumes/Base Photos/Light/**/*.lri", recursive=True)
    print(f"Total LRIs in corpus: {len(all_lris)}")

    # Sample: 1 per date directory to cover diversity
    by_date = defaultdict(list)
    for p in all_lris:
        date = os.path.dirname(p).split('/')[-1]
        by_date[date].append(p)
    sample = [v[0] for v in by_date.values()]
    print(f"Sampling 1 per date directory: {len(sample)} files")

    # Track all candidate-mode varints observed, counts per value
    mode_field_counts = defaultdict(lambda: defaultdict(int))  # path -> {value: count}
    neutral_color_present_counts = 0
    neutral_color_absent_counts = 0
    block8_missing = 0
    files_with_nonzero_mode = []

    for i, path in enumerate(sample):
        info = process_file(path)
        if info is None or not info['block8_found']:
            block8_missing += 1
            continue
        if info['neutral_color_candidates']:
            neutral_color_present_counts += 1
        else:
            neutral_color_absent_counts += 1
        # Track candidate mode varints
        for p, v in info['all_varints_in_range']:
            if 'f19' in p:
                continue
            mode_field_counts[p][v] += 1
            if v > 0:  # non-AUTO
                files_with_nonzero_mode.append((path, p, v))

    print(f"\nBlock 8 missing: {block8_missing}")
    print(f"Neutral color present: {neutral_color_present_counts}")
    print(f"Neutral color absent:  {neutral_color_absent_counts}")
    print(f"\nMode-candidate varint fields (path -> value distribution):")
    for p, dist in sorted(mode_field_counts.items()):
        total = sum(dist.values())
        dist_str = ", ".join(f"{v}={c}" for v, c in sorted(dist.items()))
        print(f"  {p}: {total} files, values: {dist_str}")

    print(f"\nFiles with non-zero mode candidate ({len(files_with_nonzero_mode)}):")
    for path, p, v in files_with_nonzero_mode[:50]:
        print(f"  {os.path.basename(path)} : {p}={v} ({AWB_MODE_NAMES.get(v, '?')})")

    # Phase 3: if non-AUTO found, deep-scan each
    print("\n" + "="*78)
    print("PHASE 3: DEEP SCAN OF NON-AUTO CAPTURES (if any)")
    print("="*78)
    if not files_with_nonzero_mode:
        print("No non-AUTO captures found in sample. Scanning ALL LRIs...")
        # Full scan
        full_nonzero = []
        full_processed = 0
        for path in all_lris:
            info = process_file(path)
            full_processed += 1
            if info is None or not info['block8_found']:
                continue
            for p, v in info['all_varints_in_range']:
                if 'f19' in p:
                    continue
                if v > 0:
                    full_nonzero.append((path, p, v))
                    break
            if full_processed % 1000 == 0:
                print(f"  ...processed {full_processed}/{len(all_lris)}, non-AUTO found: {len(full_nonzero)}")
        print(f"\nFull scan complete: {full_processed} files, {len(full_nonzero)} non-AUTO candidates")
        for path, p, v in full_nonzero[:30]:
            print(f"  {os.path.basename(path)}: {p}={v}")

        if full_nonzero:
            # Deep scan first 5 non-AUTO
            print("\nDeep scan of first 5 non-AUTO LRIs:")
            for path, p, v in full_nonzero[:5]:
                info = process_file(path)
                print(f"\n--- {os.path.basename(path)} ({p}={v}) ---")
                print(f"  Gains: R={info['gains_R']}, B={info['gains_B']}")
                print(f"  Neutral color (x,y) candidates: {info['neutral_color_candidates']}")
                print(f"  All varints 0..8: {info['all_varints_in_range']}")
        else:
            print("\n>>> NO non-AUTO LRIs in entire 9438-file corpus. All captures use AWB_MODE_AUTO. <<<")
    else:
        for path, p, v in files_with_nonzero_mode[:10]:
            info = process_file(path)
            print(f"\n--- {os.path.basename(path)} ({p}={v}) ---")
            print(f"  Gains: R={info['gains_R']}, B={info['gains_B']}")
            print(f"  Neutral color (x,y) candidates: {info['neutral_color_candidates']}")


if __name__ == "__main__":
    main()
