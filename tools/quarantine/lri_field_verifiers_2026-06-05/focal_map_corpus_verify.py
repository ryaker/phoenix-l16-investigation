#!/usr/bin/env python3
"""
focal_map_corpus_verify.py
Independent verification of 6 load-bearing claims against all 8 LRI seeds.

Thread: focal_map_corpus
Claims verified:
  1. Block count (11 for 28/35mm; 12 for 70/150mm)
  2. Block-3 calibration: 16 sub-msgs with cam_ids exactly [0..15] in order
  3. Block-3 sub f3 -> f2[0]=0x444c8000 (818.0), f2[1]=0x44bb8000 (1500.0)
  4. Block-3 calibration float-count pattern WWWWWTTTWTTTTTWW
  5. Block-6 top-level = 42 sub-msgs; cam_ids {0,2..14} x3; excluded={1,15}
  6. Second 16-cam block (idx4/idx5) f13 sub f4 = image blob (not calibration)
"""

import struct
import sys
from pathlib import Path

# ── LELR block walker ────────────────────────────────────────────────────────

def scan_lri_blocks(lri_path: str):
    blocks = []
    file_size = Path(lri_path).stat().st_size
    with open(lri_path, 'rb') as f:
        blk_offset = 0
        idx = 0
        while blk_offset < file_size:
            f.seek(blk_offset)
            hdr = f.read(32)
            if len(hdr) < 32 or hdr[0:4] != b'LELR':
                break
            total_len  = struct.unpack_from('<Q', hdr, 4)[0]
            msg_offset = struct.unpack_from('<Q', hdr, 12)[0]
            msg_len    = struct.unpack_from('<I', hdr, 20)[0]
            msg_type   = hdr[24]
            if total_len == 0:
                break
            f.seek(blk_offset + msg_offset)
            payload = f.read(msg_len)
            blocks.append({
                'idx': idx,
                'block_offset': blk_offset,
                'total_size': total_len,
                'msg_offset': msg_offset,
                'payload_size': msg_len,
                'payload': payload,
                'msg_type': msg_type,
            })
            blk_offset += total_len
            idx += 1
    return blocks


# ── Minimal protobuf parser ───────────────────────────────────────────────────

def read_varint(data: bytes, pos: int):
    result = 0
    shift = 0
    while pos < len(data):
        b = data[pos]; pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, pos
        shift += 7
    raise ValueError("truncated varint")


def parse_fields(data: bytes):
    """Yield (field_num, wire_type, raw_value). Stops on parse error."""
    pos = 0
    while pos < len(data):
        try:
            tag, pos = read_varint(data, pos)
        except (ValueError, IndexError):
            break
        fn = tag >> 3
        wt = tag & 0x7
        if fn == 0:
            break
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
        else:
            break


def get_repeated_field(data: bytes, target_fn: int, wire_type: int = None):
    """Return list of raw values for all occurrences of target field."""
    results = []
    for fn, wt, val in parse_fields(data):
        if fn == target_fn and (wire_type is None or wt == wire_type):
            results.append(val)
    return results


def get_first_field(data: bytes, target_fn: int, wire_type: int = None):
    """Return first match or None."""
    for fn, wt, val in parse_fields(data):
        if fn == target_fn and (wire_type is None or wt == wire_type):
            return val
    return None


def count_fixed32(data: bytes, depth: int = 0, max_depth: int = 6) -> int:
    """Recursively count fixed32 (wire_type=5) leaves in proto blob."""
    if depth > max_depth:
        return 0
    count = 0
    for fn, wt, val in parse_fields(data):
        if wt == 5:
            count += 1
        elif wt == 2 and isinstance(val, bytes) and len(val) > 0:
            count += count_fixed32(val, depth + 1, max_depth)
    return count


# ── Claim verifiers ──────────────────────────────────────────────────────────

def verify_claim1_block_count(lri_path: str, zoom_tier: str):
    """Claim 1: block count 11 (28/35mm) or 12 (70/150mm)."""
    blocks = scan_lri_blocks(lri_path)
    n = len(blocks)
    expected = 12 if zoom_tier in ('70mm', '150mm') else 11
    ok = (n == expected)
    # Collect payload sizes for context
    sizes = [b['payload_size'] for b in blocks]
    return ok, f"got {n} blocks (expected {expected}); payload_sizes={sizes}"


def verify_claim2_block3_camids(blocks):
    """Claim 2: Block-3 f13 repeated -> 16 sub-msgs, cam_ids exactly [0..15] in order."""
    # Block-3 is index 3 for all seeds
    if len(blocks) <= 3:
        return False, "fewer than 4 blocks"
    blk = blocks[3]
    payload = blk['payload']
    sub_msgs = get_repeated_field(payload, 13, wire_type=2)
    n = len(sub_msgs)
    if n != 16:
        return False, f"f13 count={n} (expected 16)"
    cam_ids = []
    for sub in sub_msgs:
        cid = get_first_field(sub, 1, wire_type=0)  # f1 = camera_id (varint)
        cam_ids.append(cid)
    expected = list(range(16))
    ok = (cam_ids == expected)
    return ok, f"cam_ids={cam_ids} (expected {expected})"


def verify_claim3_block3_f2_constants(blocks):
    """Claim 3: Block-3 sub f3 -> f2[0]=0x444c8000 (818.0), f2[1]=0x44bb8000 (1500.0).
    Check all 16 cams in all seeds."""
    if len(blocks) <= 3:
        return False, "fewer than 4 blocks"
    blk = blocks[3]
    payload = blk['payload']
    sub_msgs = get_repeated_field(payload, 13, wire_type=2)
    if len(sub_msgs) != 16:
        return False, f"f13 count={len(sub_msgs)}"

    issues = []
    for i, sub in enumerate(sub_msgs):
        f3 = get_first_field(sub, 3, wire_type=2)
        if f3 is None:
            issues.append(f"cam[{i}] f3 missing")
            continue
        f2_vals = get_repeated_field(f3, 2, wire_type=5)  # fixed32
        if len(f2_vals) < 2:
            issues.append(f"cam[{i}] f3.f2 count={len(f2_vals)} (need>=2)")
            continue
        v0 = f2_vals[0]
        v1 = f2_vals[1]
        f0 = struct.unpack('<f', struct.pack('<I', v0))[0]
        f1 = struct.unpack('<f', struct.pack('<I', v1))[0]
        if v0 != 0x444c8000:
            issues.append(f"cam[{i}] f2[0]=0x{v0:08x}({f0:.3f}) expected 0x444c8000(818.0)")
        if v1 != 0x44bb8000:
            issues.append(f"cam[{i}] f2[1]=0x{v1:08x}({f1:.3f}) expected 0x44bb8000(1500.0)")
    ok = len(issues) == 0
    return ok, ("ALL 16 cams: f2[0]=0x444c8000=818.0, f2[1]=0x44bb8000=1500.0" if ok else "; ".join(issues))


def verify_claim4_float_count_pattern(blocks):
    """Claim 4: float-count pattern WWWWWTTTWTTTTTWW.
    Wide cams {0,1,2,3,4,8,14,15} ~316-317 floats; Tele {5,6,7,9,10,11,12,13} ~341-342."""
    if len(blocks) <= 3:
        return False, "fewer than 4 blocks"
    blk = blocks[3]
    payload = blk['payload']
    sub_msgs = get_repeated_field(payload, 13, wire_type=2)
    if len(sub_msgs) != 16:
        return False, f"f13 count={len(sub_msgs)}"

    WIDE_CAMS = {0, 1, 2, 3, 4, 8, 14, 15}
    TELE_CAMS = {5, 6, 7, 9, 10, 11, 12, 13}
    EXPECTED_PATTERN = "WWWWWTTTWTTTTTWW"

    counts = []
    pattern_chars = []
    issues = []

    for i, sub in enumerate(sub_msgs):
        f3 = get_first_field(sub, 3, wire_type=2)
        if f3 is None:
            issues.append(f"cam[{i}] f3 missing")
            counts.append(0)
            pattern_chars.append('?')
            continue
        n = count_fixed32(f3, depth=0, max_depth=6)
        counts.append(n)
        if i in WIDE_CAMS:
            expected_char = 'W'
            if 316 <= n <= 317:
                pattern_chars.append('W')
            else:
                pattern_chars.append('w')
                issues.append(f"cam[{i}](Wide) count={n} expected 316-317")
        else:
            expected_char = 'T'
            if 341 <= n <= 342:
                pattern_chars.append('T')
            else:
                pattern_chars.append('t')
                issues.append(f"cam[{i}](Tele) count={n} expected 341-342")

    pattern_str = "".join(pattern_chars)
    ok = (pattern_str == EXPECTED_PATTERN and len(issues) == 0)
    detail = f"pattern={pattern_str} counts={counts}"
    if issues:
        detail += " ISSUES: " + "; ".join(issues)
    return ok, detail


def verify_claim5_block6_camids(blocks, zoom_tier: str):
    """Claim 5: Block-6 (idx=6 for 28/35mm, idx=7 for 70/150mm) top-level f13 = 42 sub-msgs.
    Distinct cams = {0,2,3,4,5,6,7,8,9,10,11,12,13,14} each x3; excluded = {1,15}."""
    blk6_idx = 7 if zoom_tier in ('70mm', '150mm') else 6
    if len(blocks) <= blk6_idx:
        return False, f"no block at idx={blk6_idx}"

    blk = blocks[blk6_idx]
    payload = blk['payload']
    sub_msgs = get_repeated_field(payload, 13, wire_type=2)
    n = len(sub_msgs)

    cam_ids = []
    for sub in sub_msgs:
        cid = get_first_field(sub, 1, wire_type=0)
        cam_ids.append(cid)

    EXPECTED_SET = {0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14}
    EXPECTED_EXCLUDED = {1, 15}

    observed_set = set(c for c in cam_ids if c is not None)
    missing_from_expected = EXPECTED_SET - observed_set
    unexpected_present = observed_set - EXPECTED_SET

    # Check each expected cam appears exactly 3 times
    from collections import Counter
    ctr = Counter(cam_ids)
    not_3x = {c: ctr[c] for c in EXPECTED_SET if ctr[c] != 3}
    excluded_present = {c for c in EXPECTED_EXCLUDED if c in ctr}

    ok = (n == 42 and
          not missing_from_expected and
          not unexpected_present and
          not not_3x and
          not excluded_present)

    detail = (f"block_idx={blk6_idx} payload={blk['payload_size']}B "
              f"sub_count={n}(expected 42) "
              f"cam_ids={sorted(ctr.keys())} "
              f"counts_x3={not not_3x} excluded_absent={not excluded_present}")
    if not ok:
        if not_3x:
            detail += f" BAD_COUNTS={not_3x}"
        if excluded_present:
            detail += f" EXCLUDED_PRESENT={excluded_present}"
        if missing_from_expected:
            detail += f" MISSING={missing_from_expected}"
        if unexpected_present:
            detail += f" UNEXPECTED={unexpected_present}"
    return ok, detail


def verify_claim6_second_16cam_block(blocks, zoom_tier: str):
    """Claim 6: Second 16-cam block (idx4 for 28/35mm, idx5 for 70/150mm) has
    f13 sub-msgs where f4 = ~15KB bytes blob (image/preview), NOT calibration floats."""
    blk_idx = 5 if zoom_tier in ('70mm', '150mm') else 4
    if len(blocks) <= blk_idx:
        return False, f"no block at idx={blk_idx}"

    blk = blocks[blk_idx]
    payload = blk['payload']
    sub_msgs = get_repeated_field(payload, 13, wire_type=2)
    n = len(sub_msgs)

    # Check f4 in each sub-msg
    f4_sizes = []
    f4_float_counts = []
    for sub in sub_msgs:
        f4 = get_first_field(sub, 4, wire_type=2)
        if f4 is not None:
            f4_sizes.append(len(f4))
            # Count fixed32 at top level only (depth=0)
            fc = sum(1 for fn, wt, v in parse_fields(f4) if wt == 5)
            f4_float_counts.append(fc)
        else:
            f4_sizes.append(0)
            f4_float_counts.append(0)

    # Expect: 16 sub-msgs, f4 ~15KB blobs, low fixed32 count at top level
    # (~15KB = ~15000 bytes; calibration would be ~316-342 floats = small payload)
    min_sz = min(f4_sizes) if f4_sizes else 0
    max_sz = max(f4_sizes) if f4_sizes else 0
    is_image_like = (min_sz > 5000)  # blobs >> calibration
    is_not_calibration = all(fc < 50 for fc in f4_float_counts)  # cal has 316+

    ok = (n == 16 and is_image_like and is_not_calibration)
    detail = (f"block_idx={blk_idx} payload={blk['payload_size']}B "
              f"sub_count={n}(expected 16) "
              f"f4_sizes_range=[{min_sz},{max_sz}] "
              f"f4_top_fixed32_counts={f4_float_counts[:4]}... "
              f"image_like={is_image_like} not_cal={is_not_calibration}")
    return ok, detail


# ── Main ──────────────────────────────────────────────────────────────────────

SEEDS = [
    # (label, path, zoom_tier)
    ("28mm_U1_02130_20180723", "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri", "28mm"),
    ("35mm_U1_03041_20181226", "/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri", "35mm"),
    ("70mm_U1_03434_20190518", "/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri", "70mm"),
    ("150mm_U1_02285_20180729", "/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri", "150mm"),
    # Unit-2 twins
    ("28mm_U2_02130_20180704", "/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri", "28mm"),
    ("35mm_U2_03041_20181028", "/Volumes/Base Photos/Light/2018-10-28/L16_03041.lri", "35mm"),
    ("70mm_U2_03434_20200714", "/Volumes/Base Photos/Light/2020-07-14/L16_03434.lri", "70mm"),
    ("150mm_U2_02285_20180707", "/Volumes/Base Photos/Light/2018-07-07/L16_02285.lri", "150mm"),
]

print("=" * 80)
print("focal_map_corpus_verify.py  — 6-claim x 8-seed verification")
print("=" * 80)

all_results = []

for label, lri_path, zoom_tier in SEEDS:
    print(f"\n{'─'*70}")
    print(f"SEED: {label}  ({zoom_tier})  {lri_path}")

    if not Path(lri_path).exists():
        print(f"  ERROR: file not found")
        all_results.append((label, [None]*6))
        continue

    blocks = scan_lri_blocks(lri_path)

    results = []

    # Claim 1
    ok1, d1 = verify_claim1_block_count(lri_path, zoom_tier)
    print(f"  C1 block_count  {'PASS' if ok1 else 'FAIL'}  {d1}")
    results.append(ok1)

    # Claim 2
    ok2, d2 = verify_claim2_block3_camids(blocks)
    print(f"  C2 camids_16    {'PASS' if ok2 else 'FAIL'}  {d2}")
    results.append(ok2)

    # Claim 3
    ok3, d3 = verify_claim3_block3_f2_constants(blocks)
    print(f"  C3 f2_constants {'PASS' if ok3 else 'FAIL'}  {d3}")
    results.append(ok3)

    # Claim 4
    ok4, d4 = verify_claim4_float_count_pattern(blocks)
    print(f"  C4 float_pat    {'PASS' if ok4 else 'FAIL'}  {d4}")
    results.append(ok4)

    # Claim 5
    ok5, d5 = verify_claim5_block6_camids(blocks, zoom_tier)
    print(f"  C5 blk6_camids  {'PASS' if ok5 else 'FAIL'}  {d5}")
    results.append(ok5)

    # Claim 6
    ok6, d6 = verify_claim6_second_16cam_block(blocks, zoom_tier)
    print(f"  C6 2nd16cam_blk {'PASS' if ok6 else 'FAIL'}  {d6}")
    results.append(ok6)

    all_results.append((label, results))

# Summary
print(f"\n{'='*80}")
print("SUMMARY (PASS/FAIL per seed x claim)")
print(f"{'Seed':<35} {'C1':>4} {'C2':>4} {'C3':>4} {'C4':>4} {'C5':>4} {'C6':>4}")
print("-" * 60)
all_pass = True
for label, results in all_results:
    row = "  ".join("PASS" if r else ("FAIL" if r is not None else "ERR ") for r in results)
    print(f"  {label:<33} {row}")
    if any(r is not True for r in results):
        all_pass = False

print()
print("Overall:", "ALL PASS" if all_pass else "SOME FAILURES")
print("=" * 80)
