#!/usr/bin/env python3
"""
session3_block8_parse.py — Parse L16_02130.lri Block 8 to verify the
context_ptr[0] reciprocal hypothesis from Session 2's runtime probe.

Observed runtime: context_ptr[0x00] = (0.60669, 1.000, 0.56213, 0.36895)
Hypothesis: stored_R ≈ 1/0.60669 ≈ 1.648, stored_B ≈ 1/0.56213 ≈ 1.779

LELR header (32 bytes):
    [0:4]   "LELR" magic
    [4:12]  total_block_len u64
    [12:20] msg_off u64 (usually 32 — i.e. payload starts right after header)
    [20:24] msg_len u32
    [24:25] msg_type u8
    [25:32] reserved / other header fields
"""

import struct
import sys

sys.path.insert(0, '/Volumes/Dev/lumen-phoenix-scratch')
from awb_analysis import parse_fields, read_varint

LRI_PATH = "/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri"


def scan_lelr_blocks_full(file_data):
    """Scan using the 32-byte LELR header spec from the task brief."""
    blocks = []
    pos = 0
    idx = 0
    # NOTE: LRI files can have a preamble before the first LELR. Scan for magic.
    while pos < len(file_data) - 32:
        if file_data[pos:pos+4] != b'LELR':
            pos += 1
            continue
        try:
            total_block_len = struct.unpack_from('<Q', file_data, pos+4)[0]
            msg_off         = struct.unpack_from('<Q', file_data, pos+12)[0]
            msg_len         = struct.unpack_from('<I', file_data, pos+20)[0]
            msg_type        = file_data[pos+24]
        except Exception:
            break
        payload_start = pos + msg_off
        payload = file_data[payload_start:payload_start+msg_len]
        blocks.append({
            'idx': idx,
            'file_offset': pos,
            'total_block_len': total_block_len,
            'msg_off': msg_off,
            'msg_len': msg_len,
            'msg_type': msg_type,
            'payload': payload,
        })
        idx += 1
        if total_block_len == 0 or total_block_len > len(file_data):
            break
        pos += total_block_len
        if idx > 100:
            break
    return blocks


def fmt_field(fn, wt, val, indent=0):
    pad = "  " * indent
    if wt == 'f32':
        return f"{pad}f{fn}: f32 = {val:.6f}"
    if wt == 'd64':
        return f"{pad}f{fn}: d64 = {val:.6f}"
    if wt == 'varint':
        return f"{pad}f{fn}: varint = {val}"
    if wt == 'len':
        return f"{pad}f{fn}: len({len(val)}) = {val[:32].hex()}{'...' if len(val)>32 else ''}"
    return f"{pad}f{fn}: ?"


def walk_message(data, indent=0, path="", results=None):
    if results is None:
        results = []
    try:
        fields = parse_fields(data)
    except Exception:
        return results
    for fn, wt, val in fields:
        fp = f"{path}.f{fn}" if path else f"f{fn}"
        if wt == 'len':
            # Try parse as sub-message
            try:
                subfields = parse_fields(val)
                # If sub parse is "valid looking" (all field numbers > 0 and consumed reasonably), treat as msg
                looks_msg = len(subfields) > 0 and all(f[0] > 0 and f[0] < 200 for f in subfields)
            except Exception:
                looks_msg = False
            if looks_msg:
                results.append((fp, 'msg', f"len={len(val)}"))
                walk_message(val, indent+1, fp, results)
            else:
                # Try float array
                if len(val) >= 4 and len(val) % 4 == 0:
                    n = len(val) // 4
                    floats = struct.unpack_from(f'<{n}f', val, 0)
                    results.append((fp, 'packed_f32', list(floats)))
                else:
                    results.append((fp, 'bytes', val.hex()))
        else:
            results.append((fp, wt, val))
    return results


def main():
    print(f"Loading {LRI_PATH}")
    with open(LRI_PATH, 'rb') as f:
        data = f.read()
    print(f"  size: {len(data):,} bytes")

    blocks = scan_lelr_blocks_full(data)
    print(f"\nFound {len(blocks)} LELR blocks")
    for b in blocks[:30]:
        print(f"  Block[{b['idx']:2d}] @{b['file_offset']:>12,}  "
              f"total={b['total_block_len']:>10,}  "
              f"msg_off={b['msg_off']}  msg_len={b['msg_len']:>8,}  "
              f"msg_type={b['msg_type']}")

    # "Block 8" per task brief = positional index 8 (54-byte per-capture AWB payload)
    b8_blocks = [b for b in blocks if b['msg_type'] == 8]
    print(f"\nBlocks with msg_type=8: {len(b8_blocks)}")
    # Fallback: positional block 8 (msg_len ≈ 54)
    if not b8_blocks:
        print(f"  No msg_type=8 found; using positional index 8 (msg_len=54 candidate)")
        b8 = blocks[8]
    else:
        b8 = b8_blocks[0]
    print(f"\n=== BLOCK 8 ===")
    print(f"  file_offset: 0x{b8['file_offset']:08x} ({b8['file_offset']:,})")
    print(f"  msg_len    : {b8['msg_len']}")
    print(f"  payload hex: {b8['payload'].hex()}")

    # Walk fields
    print(f"\n=== BLOCK 8 FIELDS ===")
    results = walk_message(b8['payload'])
    for path, wt, val in results:
        if wt == 'f32':
            print(f"  {path}: f32 = {val:.6f}")
        elif wt == 'd64':
            print(f"  {path}: d64 = {val:.6f}")
        elif wt == 'varint':
            print(f"  {path}: varint = {val}")
        elif wt == 'msg':
            print(f"  {path}: [msg] {val}")
        elif wt == 'packed_f32':
            print(f"  {path}: packed_f32 = {val}")
        elif wt == 'bytes':
            print(f"  {path}: bytes = {val[:64]}{'...' if len(val)>64 else ''}")
        else:
            print(f"  {path}: {wt} = {val}")

    # Focus on f19 subtree
    print(f"\n=== FOCUS: f19 SUBTREE ===")
    f19_fields = [r for r in results if r[0].startswith('f19')]
    for path, wt, val in f19_fields:
        if wt == 'f32':
            print(f"  {path}: {val:.6f}")
        elif wt == 'varint':
            print(f"  {path}: varint = {val}")
        elif wt == 'msg':
            print(f"  {path}: [msg]")

    # Extract specific hypothesis fields
    print(f"\n=== HYPOTHESIS CHECK ===")
    target_r = None
    target_b = None
    g1 = None
    g2 = None
    for path, wt, val in results:
        if path == 'f19.f15.f1' and wt == 'f32':
            target_r = val
        elif path == 'f19.f15.f2' and wt == 'f32':
            g1 = val
        elif path == 'f19.f15.f3' and wt == 'f32':
            g2 = val
        elif path == 'f19.f15.f4' and wt == 'f32':
            target_b = val

    print(f"  Observed at runtime: context_ptr[0] = (0.60669, 1.000, 0.56213, 0.36895)")
    print(f"  f19.f15.f1 (R_gain) = {target_r}")
    print(f"  f19.f15.f2 (G1)     = {g1}")
    print(f"  f19.f15.f3 (G2)     = {g2}")
    print(f"  f19.f15.f4 (B_gain) = {target_b}")
    if target_r and target_r > 0:
        print(f"  1/R_gain = {1/target_r:.6f}  (expect ≈ 0.60669)")
    if target_b and target_b > 0:
        print(f"  1/B_gain = {1/target_b:.6f}  (expect ≈ 0.56213)")

    # Look for 0.36895 candidate
    print(f"\n=== HUNT FOR 0.36895 IN BLOCK 8 ===")
    for path, wt, val in results:
        if wt in ('f32', 'd64'):
            if abs(val - 0.36895) < 0.01:
                print(f"  *** MATCH *** {path}: {val:.6f}")
            elif 0.3 < val < 0.45:
                print(f"  near: {path}: {val:.6f}")

    # Also dump f19.f14 and f19.f16
    print(f"\n=== f19.f14 (candidate noise floor / sensor metrics) ===")
    for path, wt, val in results:
        if path.startswith('f19.f14'):
            if wt == 'f32':
                print(f"  {path}: f32 = {val:.6f}")
            elif wt == 'd64':
                print(f"  {path}: d64 = {val:.6f}")
            elif wt == 'varint':
                print(f"  {path}: varint = {val}")
            elif wt == 'msg':
                print(f"  {path}: [msg]")

    print(f"\n=== f19.f16 (flag) ===")
    for path, wt, val in results:
        if path.startswith('f19.f16'):
            print(f"  {path}: {wt} = {val}")


if __name__ == '__main__':
    main()
