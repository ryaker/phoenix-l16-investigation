#!/usr/bin/env python3
"""
Diagnostic script: probe actual block-3 structure for 70mm, and
investigate the f3->f2 path in Block-3 for 28mm.
"""
import struct
from pathlib import Path


def read_varint(data: bytes, pos: int):
    result = 0; shift = 0
    while pos < len(data):
        b = data[pos]; pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80): return result, pos
        shift += 7
    raise ValueError("truncated varint")


def parse_fields(data: bytes):
    pos = 0
    while pos < len(data):
        try: tag, pos = read_varint(data, pos)
        except: break
        fn = tag >> 3; wt = tag & 0x7
        if fn == 0: break
        if wt == 0:
            try: val, pos = read_varint(data, pos)
            except: break
            yield fn, wt, val
        elif wt == 1:
            if pos + 8 > len(data): break
            val = struct.unpack_from('<Q', data, pos)[0]; pos += 8
            yield fn, wt, val
        elif wt == 2:
            try: length, pos = read_varint(data, pos)
            except: break
            if pos + length > len(data): break
            val = data[pos:pos+length]; pos += length
            yield fn, wt, val
        elif wt == 5:
            if pos + 4 > len(data): break
            val = struct.unpack_from('<I', data, pos)[0]; pos += 4
            yield fn, wt, val
        else: break


def scan_lri_blocks(lri_path: str):
    blocks = []
    file_size = Path(lri_path).stat().st_size
    with open(lri_path, 'rb') as f:
        blk_offset = 0; idx = 0
        while blk_offset < file_size:
            f.seek(blk_offset)
            hdr = f.read(32)
            if len(hdr) < 32 or hdr[0:4] != b'LELR': break
            total_len  = struct.unpack_from('<Q', hdr, 4)[0]
            msg_offset = struct.unpack_from('<Q', hdr, 12)[0]
            msg_len    = struct.unpack_from('<I', hdr, 20)[0]
            if total_len == 0: break
            f.seek(blk_offset + msg_offset)
            payload = f.read(msg_len)
            blocks.append({'idx': idx, 'payload_size': msg_len, 'payload': payload})
            blk_offset += total_len; idx += 1
    return blocks


def get_repeated(data, fn_target, wt_target=None):
    return [val for fn, wt, val in parse_fields(data)
            if fn == fn_target and (wt_target is None or wt == wt_target)]


def get_first(data, fn_target, wt_target=None):
    for fn, wt, val in parse_fields(data):
        if fn == fn_target and (wt_target is None or wt == wt_target):
            return val
    return None


def top_fields(data, label=""):
    """Print top-level field numbers and wire types."""
    seen = {}
    for fn, wt, val in parse_fields(data):
        if fn not in seen:
            seen[fn] = (wt, len(val) if isinstance(val, bytes) else val)
    print(f"  {label} top fields: {dict(sorted(seen.items()))}")


# ── DIAGNOSTIC 1: Block-3 for 70mm — what field holds the 16 sub-msgs? ──────
print("=== DIAG 1: Block-3 structure for 70mm (different from 28mm because of extra idx3) ===")
# 70mm has an extra 581B block at idx3 — so Block-3 calibration is now at idx4
lri_70mm = "/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri"
blocks70 = scan_lri_blocks(lri_70mm)
print(f"Total blocks: {len(blocks70)}")
for i, b in enumerate(blocks70):
    print(f"  idx={i} payload={b['payload_size']}B")

# The claim says Block-3 (first 16-cam block) — let's check which index has 32832B
for i, b in enumerate(blocks70):
    if b['payload_size'] in (32832, 32833):
        print(f"\n  -> 32832B block is at idx={i}")
        sub13 = get_repeated(b['payload'], 13)
        print(f"     f13 sub-msg count = {len(sub13)}")
        if sub13:
            # Check first sub
            s = sub13[0]
            print(f"     first sub fields: ", end="")
            top_fields(s, f"sub[0]")
        break


# ── DIAGNOSTIC 2: f3 in Block-3 for 28mm — what does cam f3 actually contain? ──
print("\n=== DIAG 2: Block-3 cam calibration structure for 28mm ===")
lri_28mm = "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"
blocks28 = scan_lri_blocks(lri_28mm)
blk3 = blocks28[3]  # 32832B
sub13 = get_repeated(blk3['payload'], 13)
print(f"Block-3 payload={blk3['payload_size']}B, f13 count={len(sub13)}")

# Examine cam[0] sub-structure
if sub13:
    s0 = sub13[0]
    print(f"\nCam[0] sub-message top-level fields:")
    top_fields(s0, "cam[0]")

    # Get f3 (calibration nested msg)
    f3 = get_first(s0, 3)
    if f3:
        print(f"  f3 present, {len(f3)} bytes")
        print("  f3 top-level fields:")
        top_fields(f3, "f3")

        # What does f2 look like in f3?
        f2_all = [(wt, val) for fn, wt, val in parse_fields(f3) if fn == 2]
        print(f"  f3.f2 entries (wt, val):")
        for wt, val in f2_all[:5]:
            if isinstance(val, bytes):
                print(f"    wt={wt} len={len(val)} bytes")
            else:
                print(f"    wt={wt} val={val}")

        # Maybe f2 is a sub-message containing the fixed32 values?
        # Try treating f2[0] as sub-msg
        if f2_all:
            wt0, v0 = f2_all[0]
            if isinstance(v0, bytes):
                print(f"\n  f3.f2[0] as sub-msg ({len(v0)} bytes) top fields:")
                top_fields(v0, "f3.f2[0]")
                # Look for fixed32 in f3.f2[0]
                fixed32_in_f2_0 = [(fn, val) for fn, wt, val in parse_fields(v0) if wt == 5]
                print(f"  fixed32 in f3.f2[0]: {fixed32_in_f2_0[:4]}")

        # Check if the focal length floats are in f2 as sub-msgs containing fixed32
        # Try: f3 -> f2 (sub-msg) -> f2 (fixed32)
        for wt2, v2 in f2_all[:3]:
            if isinstance(v2, bytes):
                inner_f2 = [(fn, wt, val) for fn, wt, val in parse_fields(v2) if fn == 2 and wt == 5]
                if inner_f2:
                    print(f"  f3.f2_sub.f2_fixed32: {inner_f2[:4]}")
    else:
        print("  f3 NOT FOUND in cam[0]")
        # List what fields are present
        print("  Fields in cam[0]:", [(fn, wt) for fn, wt, _ in parse_fields(s0)])


# ── DIAGNOSTIC 3: Trace where 818.0 and 1500.0 live in cam[0] calibration ──
print("\n=== DIAG 3: Search for 0x444c8000 (818.0) in cam[0] calibration bytes ===")
if sub13:
    s0 = sub13[0]
    # Raw search in s0 bytes
    target = struct.pack('<I', 0x444c8000)
    idx_in_s0 = s0.find(target)
    print(f"  0x444c8000 (818.0) found at byte offset {idx_in_s0} in cam[0] sub-msg")

    target2 = struct.pack('<I', 0x44bb8000)
    idx2_in_s0 = s0.find(target2)
    print(f"  0x44bb8000 (1500.0) found at byte offset {idx2_in_s0} in cam[0] sub-msg")

    if idx_in_s0 >= 0:
        # Show surrounding context
        ctx_start = max(0, idx_in_s0 - 8)
        ctx_end = min(len(s0), idx_in_s0 + 16)
        print(f"  Hex context [{ctx_start}:{ctx_end}]: {s0[ctx_start:ctx_end].hex()}")

        # Walk the proto structure to find which field path contains this byte offset
        # Try: directly reading field from s0 at various depths
        # Find what field at top level contains offset idx_in_s0
        pos = 0
        while pos < len(s0):
            try: tag, new_pos = read_varint(s0, pos)
            except: break
            fn = tag >> 3; wt = tag & 0x7
            if fn == 0: break
            field_start = new_pos
            if wt == 0:
                try: val, new_pos = read_varint(s0, new_pos)
                except: break
            elif wt == 1:
                if new_pos + 8 > len(s0): break
                val = s0[new_pos:new_pos+8]; new_pos += 8
            elif wt == 2:
                try: length, new_pos = read_varint(s0, new_pos)
                except: break
                if new_pos + length > len(s0): break
                val = s0[new_pos:new_pos+length]
                if new_pos <= idx_in_s0 < new_pos + length:
                    print(f"  0x444c8000 is inside cam[0].f{fn} (wt={wt}, bytes {new_pos}..{new_pos+length})")
                new_pos += length
            elif wt == 5:
                if new_pos + 4 > len(s0): break
                val = s0[new_pos:new_pos+4]; new_pos += 4
            else: break
            if new_pos > idx_in_s0 + 4: break
            pos = new_pos


# ── DIAGNOSTIC 4: What is the correct path to 818.0/1500.0? ────────────────
print("\n=== DIAG 4: Deep search for 818.0 focal length in cam[0] ===")
def find_fixed32_path(data: bytes, target_val: int, path="root", depth=0, max_depth=8):
    if depth > max_depth:
        return
    for fn, wt, val in parse_fields(data):
        if wt == 5 and val == target_val:
            flt = struct.unpack('<f', struct.pack('<I', val))[0]
            print(f"  FOUND 0x{val:08x} = {flt:.3f} at path: {path}.f{fn}")
        elif wt == 2 and isinstance(val, bytes) and len(val) > 0:
            find_fixed32_path(val, target_val, f"{path}.f{fn}", depth+1, max_depth)

if sub13:
    s0 = sub13[0]
    print("Searching for 0x444c8000 (818.0):")
    find_fixed32_path(s0, 0x444c8000)
    print("Searching for 0x44bb8000 (1500.0):")
    find_fixed32_path(s0, 0x44bb8000)


# ── DIAGNOSTIC 5: Unit-2 35mm seed — is it actually 70mm? ───────────────────
print("\n=== DIAG 5: Unit-2 35mm seed block structure (2018-10-28/L16_03041) ===")
lri_35u2 = "/Volumes/Base Photos/Light/2018-10-28/L16_03041.lri"
blocks_35u2 = scan_lri_blocks(lri_35u2)
print(f"Block count: {len(blocks_35u2)}")
for i, b in enumerate(blocks_35u2):
    print(f"  idx={i} payload={b['payload_size']}B")
# Check the LightHeader focal length
lh = blocks_35u2[0]['payload']
for fn, wt, val in parse_fields(lh):
    if fn == 4:  # image_focal_length uint32
        print(f"  LightHeader.f4 (focal_length) = {val}")
    if fn == 11:  # zoom_factor float
        fv = struct.unpack('<f', struct.pack('<I', val))[0]
        print(f"  LightHeader.f11 (zoom_factor) = 0x{val:08x} ({fv:.3f})")
