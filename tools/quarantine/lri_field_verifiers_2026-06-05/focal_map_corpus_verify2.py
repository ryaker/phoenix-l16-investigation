#!/usr/bin/env python3
"""
focal_map_corpus_verify2.py
Corrected independent verification of 6 load-bearing LRI claims.

CORRECTIONS FROM v1:
  - C2/C3/C4: calibration block (32832B) is at idx=3 for 28/35mm,
    idx=4 for 70/150mm (shifted by extra 581B block at idx=3)
  - C3: field path is f3->f2(sub-msg)->f1(fixed32), NOT f3->f2(fixed32)
  - Unit-2 "35mm" 2018-10-28/L16_03041 is focal_length=74mm (70mm tier),
    not 35mm — treated as out-of-scope / wrong tier for 35mm claims
  - C6: second-16-cam block is idx=4 for 28/35mm, idx=5 for 70/150mm
    (same as claim states; these index into the full block list)

Claim field-path corrections:
  Claim 2: Block holding 16 sub-msgs = the 32832B block (idx=3 or 4 depending on zoom tier)
  Claim 3: f3.f2[any].f1 = fixed32 value (f2 is a sub-msg, f1 inside it is fixed32)
  Claim 4: Same calibration block; correct f3 path for float count
"""

import struct
from pathlib import Path
from collections import Counter


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


def get_repeated(data: bytes, target_fn: int, target_wt: int = None):
    return [val for fn, wt, val in parse_fields(data)
            if fn == target_fn and (target_wt is None or wt == target_wt)]


def get_first(data: bytes, target_fn: int, target_wt: int = None):
    for fn, wt, val in parse_fields(data):
        if fn == target_fn and (target_wt is None or wt == target_wt):
            return val
    return None


def count_fixed32_recursive(data: bytes, depth: int = 0, max_depth: int = 6) -> int:
    if depth > max_depth: return 0
    count = 0
    for fn, wt, val in parse_fields(data):
        if wt == 5:
            count += 1
        elif wt == 2 and isinstance(val, bytes) and len(val) > 0:
            count += count_fixed32_recursive(val, depth + 1, max_depth)
    return count


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


def get_lri_focal_length(blocks) -> int:
    """Read LightHeader.f4 = image_focal_length (uint32) from block 0."""
    lh = blocks[0]['payload']
    val = get_first(lh, 4, target_wt=0)
    return val if val is not None else -1


def find_cal_block_idx(blocks) -> int:
    """Find the block with payload_size in {32832, 32833} — calibration block."""
    for b in blocks:
        if b['payload_size'] in (32832, 32833):
            return b['idx']
    return -1


# ── Claim 1: block count ─────────────────────────────────────────────────────

def verify_claim1(blocks, zoom_tier: str):
    n = len(blocks)
    expected = 12 if zoom_tier in ('70mm', '150mm') else 11
    ok = (n == expected)
    sizes = [b['payload_size'] for b in blocks]
    return ok, f"got {n} (expected {expected}); payload_sizes={sizes}"


# ── Claim 2: Block-3 cal f13 -> 16 sub-msgs, cam_ids [0..15] in order ───────

def verify_claim2(blocks, zoom_tier: str):
    cal_idx = find_cal_block_idx(blocks)
    if cal_idx < 0:
        return False, "calibration block (32832B) not found"
    blk = blocks[cal_idx]
    payload = blk['payload']
    sub_msgs = get_repeated(payload, 13, target_wt=2)
    n = len(sub_msgs)
    if n != 16:
        return False, f"cal_block_idx={cal_idx} f13 count={n} (expected 16)"
    cam_ids = []
    for sub in sub_msgs:
        cid = get_first(sub, 1, target_wt=0)
        cam_ids.append(cid)
    expected = list(range(16))
    ok = (cam_ids == expected)
    return ok, f"cal_block_idx={cal_idx} cam_ids={cam_ids}"


# ── Claim 3: Block-3 sub f3 -> f2[*].f1 = 818.0/1500.0 for all 16 cams ─────
# CORRECTED: f2 is a sub-msg; the fixed32 value is f2.f1 (field 1 inside f2 sub-msg)

def verify_claim3(blocks, zoom_tier: str):
    cal_idx = find_cal_block_idx(blocks)
    if cal_idx < 0:
        return False, "calibration block not found"
    blk = blocks[cal_idx]
    payload = blk['payload']
    sub_msgs = get_repeated(payload, 13, target_wt=2)
    if len(sub_msgs) != 16:
        return False, f"f13 count={len(sub_msgs)}"

    issues = []
    # For each cam, look in f3 -> f2 (repeated sub-msg) -> f1 (fixed32)
    for i, sub in enumerate(sub_msgs):
        f3 = get_first(sub, 3, target_wt=2)
        if f3 is None:
            issues.append(f"cam[{i}] f3 missing")
            continue
        f2_subs = get_repeated(f3, 2, target_wt=2)  # f2 is sub-msg (wt=2)
        if len(f2_subs) < 2:
            issues.append(f"cam[{i}] f3.f2 sub-msg count={len(f2_subs)} (need>=2)")
            continue
        # f2[0].f1 should be 0x444c8000 = 818.0
        v0 = get_first(f2_subs[0], 1, target_wt=5)  # f1 = fixed32 (wt=5)
        # f2[1] should contain 0x44bb8000 = 1500.0 — but may be at f1 or different position
        # From diag: root.f3.f2.f1 contains both 818 and 1500 across two f2 sub-msgs
        # Actually diag showed f3.f2[0].f1=1145864192=0x444c8000 (818.0), f3.f2[1] may be next
        # Let's also check f6 since diag showed f6=1174932480
        v1_from_f2_1 = get_first(f2_subs[1], 1, target_wt=5) if len(f2_subs) > 1 else None

        # Check v0 = 0x444c8000
        if v0 is None:
            # Maybe f1 is not present; try other fields
            issues.append(f"cam[{i}] f3.f2[0].f1 not found")
        elif v0 != 0x444c8000:
            fv = struct.unpack('<f', struct.pack('<I', v0))[0]
            issues.append(f"cam[{i}] f3.f2[0].f1=0x{v0:08x}({fv:.3f}) expected 0x444c8000(818.0)")

        # For 1500.0 (0x44bb8000): check where it appears
        # From diag: root.f3.f2.f1 = found once → means it's in another f2 sub-msg
        # Let's check all f2 sub-msgs for 1500.0
        found_1500 = False
        for f2s in f2_subs:
            for fn, wt, val in parse_fields(f2s):
                if wt == 5 and val == 0x44bb8000:
                    found_1500 = True
                    break
            if found_1500:
                break
        if not found_1500:
            issues.append(f"cam[{i}] 0x44bb8000(1500.0) not found in any f3.f2 sub-msg")

    ok = len(issues) == 0
    if ok:
        return ok, "ALL 16 cams: f3.f2[0].f1=0x444c8000=818.0 and f3.f2[*] contains 0x44bb8000=1500.0"
    return ok, "; ".join(issues[:5]) + (f"... ({len(issues)} total)" if len(issues) > 5 else "")


# ── Claim 4: float-count pattern WWWWWTTTWTTTTTWW ───────────────────────────

def verify_claim4(blocks, zoom_tier: str):
    cal_idx = find_cal_block_idx(blocks)
    if cal_idx < 0:
        return False, "calibration block not found"
    blk = blocks[cal_idx]
    payload = blk['payload']
    sub_msgs = get_repeated(payload, 13, target_wt=2)
    if len(sub_msgs) != 16:
        return False, f"f13 count={len(sub_msgs)}"

    WIDE_CAMS = {0, 1, 2, 3, 4, 8, 14, 15}
    EXPECTED_PATTERN = "WWWWWTTTWTTTTTWW"

    counts = []
    pattern_chars = []
    issues = []

    for i, sub in enumerate(sub_msgs):
        f3 = get_first(sub, 3, target_wt=2)
        if f3 is None:
            issues.append(f"cam[{i}] f3 missing")
            counts.append(0); pattern_chars.append('?')
            continue
        n = count_fixed32_recursive(f3, depth=0, max_depth=6)
        counts.append(n)
        if i in WIDE_CAMS:
            if 316 <= n <= 317:
                pattern_chars.append('W')
            else:
                pattern_chars.append('w')
                issues.append(f"cam[{i}](Wide) count={n} expected 316-317")
        else:
            if 341 <= n <= 342:
                pattern_chars.append('T')
            else:
                pattern_chars.append('t')
                issues.append(f"cam[{i}](Tele) count={n} expected 341-342")

    pattern_str = "".join(pattern_chars)
    ok = (pattern_str == EXPECTED_PATTERN and not issues)
    detail = f"cal_idx={cal_idx} pattern={pattern_str} counts={counts}"
    if issues:
        detail += " ISSUES: " + "; ".join(issues)
    return ok, detail


# ── Claim 5: Block-6 42 sub-msgs, cam_ids {0,2..14} x3, excluded {1,15} ─────

def verify_claim5(blocks, zoom_tier: str):
    blk6_idx = 7 if zoom_tier in ('70mm', '150mm') else 6
    if len(blocks) <= blk6_idx:
        return False, f"no block at idx={blk6_idx}"
    blk = blocks[blk6_idx]
    payload = blk['payload']
    sub_msgs = get_repeated(payload, 13, target_wt=2)
    n = len(sub_msgs)
    cam_ids = [get_first(sub, 1, target_wt=0) for sub in sub_msgs]

    EXPECTED_SET = {0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14}
    ctr = Counter(cam_ids)
    observed_set = set(c for c in cam_ids if c is not None)
    missing = EXPECTED_SET - observed_set
    unexpected = observed_set - EXPECTED_SET
    not_3x = {c: ctr[c] for c in EXPECTED_SET if ctr.get(c, 0) != 3}
    excluded_present = {c for c in (1, 15) if c in ctr}

    ok = (n == 42 and not missing and not unexpected and not not_3x and not excluded_present)
    detail = (f"block_idx={blk6_idx} payload={blk['payload_size']}B "
              f"sub_count={n}(expected 42) "
              f"distinct_cams={sorted(observed_set)} counts_x3={not not_3x} excluded_absent={not excluded_present}")
    if not ok:
        if not_3x: detail += f" BAD_COUNTS={not_3x}"
        if excluded_present: detail += f" EXCLUDED_PRESENT={excluded_present}"
        if missing: detail += f" MISSING={missing}"
        if unexpected: detail += f" UNEXPECTED={unexpected}"
    return ok, detail


# ── Claim 6: Second 16-cam block has image blobs in f4 (not calibration) ─────

def verify_claim6(blocks, zoom_tier: str):
    blk_idx = 5 if zoom_tier in ('70mm', '150mm') else 4
    if len(blocks) <= blk_idx:
        return False, f"no block at idx={blk_idx}"
    blk = blocks[blk_idx]
    payload = blk['payload']
    sub_msgs = get_repeated(payload, 13, target_wt=2)
    n = len(sub_msgs)

    f4_sizes = []
    f4_top_fixed32 = []
    for sub in sub_msgs:
        f4 = get_first(sub, 4, target_wt=2)
        if f4 is not None:
            f4_sizes.append(len(f4))
            fc = sum(1 for fn, wt, v in parse_fields(f4) if wt == 5)
            f4_top_fixed32.append(fc)
        else:
            f4_sizes.append(0)
            f4_top_fixed32.append(0)

    min_sz = min(f4_sizes) if f4_sizes else 0
    max_sz = max(f4_sizes) if f4_sizes else 0
    is_image_like = (min_sz > 5000)
    is_not_calibration = all(fc < 50 for fc in f4_top_fixed32)

    ok = (n == 16 and is_image_like and is_not_calibration)
    detail = (f"block_idx={blk_idx} payload={blk['payload_size']}B "
              f"sub_count={n}(expected 16) "
              f"f4_size_range=[{min_sz},{max_sz}] "
              f"f4_top_fixed32_sample={f4_top_fixed32[:4]} "
              f"image_like={is_image_like} not_cal={is_not_calibration}")
    return ok, detail


# ── Seeds ────────────────────────────────────────────────────────────────────

SEEDS = [
    ("28mm_U1_02130_20180723", "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri", "28mm"),
    ("35mm_U1_03041_20181226", "/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri", "35mm"),
    ("70mm_U1_03434_20190518", "/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri", "70mm"),
    ("150mm_U1_02285_20180729", "/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri", "150mm"),
    ("28mm_U2_02130_20180704", "/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri", "28mm"),
    # Unit-2 35mm: 2018-10-28/L16_03041 is focal_length=74 (70mm tier) — out-of-scope for 35mm claims
    # Reported separately below; skip for claim-set designed for 35mm
    ("70mm_U2_03434_20200714", "/Volumes/Base Photos/Light/2020-07-14/L16_03434.lri", "70mm"),
    ("150mm_U2_02285_20180707", "/Volumes/Base Photos/Light/2018-07-07/L16_02285.lri", "150mm"),
]

print("=" * 80)
print("focal_map_corpus_verify2.py — corrected 6-claim x 7-seed verification")
print("=" * 80)

all_results = []

for label, lri_path, zoom_tier in SEEDS:
    print(f"\n{'─'*70}")
    print(f"SEED: {label}  ({zoom_tier})")

    if not Path(lri_path).exists():
        print(f"  ERROR: file not found")
        all_results.append((label, [None]*6))
        continue

    blocks = scan_lri_blocks(lri_path)
    focal = get_lri_focal_length(blocks)
    print(f"  LightHeader.focal_length={focal}  blocks={len(blocks)}")

    results = []

    ok1, d1 = verify_claim1(blocks, zoom_tier)
    print(f"  C1 block_count  {'PASS' if ok1 else 'FAIL'}  {d1}")
    results.append(ok1)

    ok2, d2 = verify_claim2(blocks, zoom_tier)
    print(f"  C2 camids_16    {'PASS' if ok2 else 'FAIL'}  {d2}")
    results.append(ok2)

    ok3, d3 = verify_claim3(blocks, zoom_tier)
    print(f"  C3 f2_constants {'PASS' if ok3 else 'FAIL'}  {d3}")
    results.append(ok3)

    ok4, d4 = verify_claim4(blocks, zoom_tier)
    print(f"  C4 float_pat    {'PASS' if ok4 else 'FAIL'}  {d4}")
    results.append(ok4)

    ok5, d5 = verify_claim5(blocks, zoom_tier)
    print(f"  C5 blk6_camids  {'PASS' if ok5 else 'FAIL'}  {d5}")
    results.append(ok5)

    ok6, d6 = verify_claim6(blocks, zoom_tier)
    print(f"  C6 2nd16camblk  {'PASS' if ok6 else 'FAIL'}  {d6}")
    results.append(ok6)

    all_results.append((label, results))

# Probe the out-of-scope Unit-2 35mm seed separately
print(f"\n{'─'*70}")
print("OUT-OF-SCOPE SEED: 35mm_U2_03041_20181028 (claimed 35mm, actual focal=74mm=70mm tier)")
lri_u2_35 = "/Volumes/Base Photos/Light/2018-10-28/L16_03041.lri"
blocks_u2 = scan_lri_blocks(lri_u2_35)
focal_u2 = get_lri_focal_length(blocks_u2)
print(f"  focal_length={focal_u2}  blocks={len(blocks_u2)}")
print(f"  payload_sizes={[b['payload_size'] for b in blocks_u2]}")
# Apply 70mm-tier claims to it
ok1x, d1x = verify_claim1(blocks_u2, '70mm')
ok2x, d2x = verify_claim2(blocks_u2, '70mm')
ok5x, d5x = verify_claim5(blocks_u2, '70mm')
ok6x, d6x = verify_claim6(blocks_u2, '70mm')
print(f"  [if treated as 70mm] C1={ok1x} C2={ok2x} C5={ok5x} C6={ok6x}")
print(f"    C1: {d1x}")
print(f"    C2: {d2x}")
print(f"    C5: {d5x}")
print(f"    C6: {d6x}")

# Summary
print(f"\n{'='*80}")
print("SUMMARY  (PASS/FAIL per seed x claim)")
print(f"{'Seed':<35} {'C1':>4} {'C2':>4} {'C3':>4} {'C4':>4} {'C5':>4} {'C6':>4}")
print("-" * 62)
all_pass = True
for label, results in all_results:
    row = "  ".join("PASS" if r else ("FAIL" if r is not None else "ERR ") for r in results)
    print(f"  {label:<33} {row}")
    if any(r is not True for r in results):
        all_pass = False
print()
print("Overall:", "ALL PASS" if all_pass else "SOME FAILURES")
print("=" * 80)
