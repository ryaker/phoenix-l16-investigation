#!/usr/bin/env python3
"""
block6_f28_decode.py — Independent parser for block[6] field-28 spectral claims.

Tests claims 1-8 from thread block6_f28_decode against:
  /Volumes/Base Photos/Light/2018-07-23/L16_02130.lri

All parsing is standalone — does not use lri_field_inspect.py logic.
"""

import struct
import sys
from pathlib import Path

LRI_PATH = "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"

# ── Proto primitives ────────────────────────────────────────────────────────────

def read_varint(data: bytes, pos: int):
    result = 0
    shift = 0
    while pos < len(data):
        b = data[pos]; pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, pos
        shift += 7
    raise ValueError("truncated varint at pos %d" % pos)


def parse_proto_flat(data: bytes):
    """Yield (field_num, wire_type, raw_value) for one level."""
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
            val, pos = read_varint(data, pos)
            yield fn, wt, val
        elif wt == 1:
            if pos + 8 > len(data): break
            val = struct.unpack_from('<Q', data, pos)[0]
            pos += 8
            yield fn, wt, val
        elif wt == 2:
            length, pos = read_varint(data, pos)
            if pos + length > len(data): break
            val = data[pos:pos+length]
            pos += length
            yield fn, wt, val
        elif wt == 5:
            if pos + 4 > len(data): break
            val = struct.unpack_from('<I', data, pos)[0]
            pos += 4
            yield fn, wt, val
        else:
            break


def collect_field(data: bytes, target_fn: int):
    """Return list of raw values for a specific field number at this level."""
    results = []
    for fn, wt, val in parse_proto_flat(data):
        if fn == target_fn:
            results.append((wt, val))
    return results


# ── LRI block scanner ────────────────────────────────────────────────────────────

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
            if total_len == 0:
                break
            f.seek(blk_offset + msg_offset)
            payload = f.read(msg_len)
            blocks.append({'idx': idx, 'payload': payload, 'total_size': total_len})
            blk_offset += total_len
            idx += 1
    return blocks


# ── Claim tests ──────────────────────────────────────────────────────────────────

def test_claim1(blk6_payload: bytes):
    """
    Claim 1: block[6].field13[rec0].field2.field8
      expect: 950-byte sub-message; parses to f1(varint)=1 + 3x repeated field2 each len=313
    """
    print("\n=== CLAIM 1 ===")
    # block[6] top-level is a repeated message at field 13
    f13_entries = collect_field(blk6_payload, 13)
    print(f"  field13 entries in block[6]: {len(f13_entries)}")
    if not f13_entries:
        print("  FAIL: no field13 found")
        return None, None

    rec0_wt, rec0_data = f13_entries[0]
    print(f"  rec0 wire_type={rec0_wt}, size={len(rec0_data)} bytes")

    # Inside rec0, find field2
    f2_entries = collect_field(rec0_data, 2)
    print(f"  rec0.field2 entries: {len(f2_entries)}")
    if not f2_entries:
        print("  FAIL: no field2 in rec0")
        return None, None

    rec0_f2_data = f2_entries[0][1]  # first field2 instance
    print(f"  rec0.field2 size: {len(rec0_f2_data)} bytes")

    # Inside rec0.field2, find field8
    f8_entries = collect_field(rec0_f2_data, 8)
    print(f"  rec0.field2.field8 entries: {len(f8_entries)}")
    if not f8_entries:
        print("  FAIL: no field8 in rec0.field2")
        return None, None

    f8_data = f8_entries[0][1]
    f8_len = len(f8_data)
    print(f"  rec0.field2.field8 size: {f8_len} bytes  (expect ~950)")

    # Parse inside f8: expect f1(varint)=1 + 3x field2
    inner_f1 = collect_field(f8_data, 1)
    inner_f2 = collect_field(f8_data, 2)
    print(f"  f8.field1 entries: {len(inner_f1)}, values: {[v for wt,v in inner_f1]}")
    print(f"  f8.field2 entries: {len(inner_f2)}")
    f2_sizes = [len(v) for wt, v in inner_f2 if wt == 2]
    print(f"  f8.field2 sizes: {f2_sizes}  (expect [313,313,313])")

    f1_val = inner_f1[0][1] if inner_f1 else None
    passed = (
        f8_len >= 940 and f8_len <= 960 and
        f1_val == 1 and
        len(inner_f2) == 3 and
        all(s == 313 for s in f2_sizes)
    )
    status = "PASS" if passed else "FAIL"
    print(f"  => {status}: f8_len={f8_len}, f1={f1_val}, f2_count={len(inner_f2)}, f2_sizes={f2_sizes}")
    return passed, f8_data


def test_claim2(f8_data: bytes):
    """
    Claim 2: block[6].field13[rec0].field2.field8.field2[0]
      expect: 313B sub-message decoding to f1=380, f2=755, f3=304-byte blob
    """
    print("\n=== CLAIM 2 ===")
    if f8_data is None:
        print("  SKIP: no f8_data from claim 1")
        return False, None

    inner_f2 = collect_field(f8_data, 2)
    if not inner_f2:
        print("  FAIL: no field2 entries in f8")
        return False, None

    ch0_data = inner_f2[0][1]
    print(f"  field2[0] size: {len(ch0_data)} bytes  (expect 313)")

    ch_f1 = collect_field(ch0_data, 1)
    ch_f2 = collect_field(ch0_data, 2)
    ch_f3 = collect_field(ch0_data, 3)

    f1_val = ch_f1[0][1] if ch_f1 else None
    f2_val = ch_f2[0][1] if ch_f2 else None
    f3_val = ch_f3[0][1] if ch_f3 else None
    f3_len = len(f3_val) if isinstance(f3_val, bytes) else 0

    print(f"  field2[0].f1 = {f1_val}  (expect 380)")
    print(f"  field2[0].f2 = {f2_val}  (expect 755)")
    print(f"  field2[0].f3 size = {f3_len} bytes  (expect 304)")

    passed = (f1_val == 380 and f2_val == 755 and f3_len == 304)
    status = "PASS" if passed else "FAIL"
    print(f"  => {status}")
    return passed, (f8_data, ch0_data, f3_val)


def test_claim3(f3_blob: bytes):
    """
    Claim 3: field3 = exactly 76 little-endian float32s
      first 4 bytes = acc0903e => 0.28272 (approximately)
      does NOT re-parse as proto
    """
    print("\n=== CLAIM 3 ===")
    if f3_blob is None:
        print("  SKIP: no blob from claim 2")
        return False, None

    blob_len = len(f3_blob)
    n_floats = blob_len // 4
    remainder = blob_len % 4
    print(f"  blob size: {blob_len} bytes, floats={n_floats}, remainder={remainder}  (expect 304/4=76)")

    if blob_len < 4:
        print("  FAIL: too short")
        return False, None

    first_raw = struct.unpack_from('<I', f3_blob, 0)[0]
    first_float = struct.unpack_from('<f', f3_blob, 0)[0]
    print(f"  first 4 bytes raw: 0x{first_raw:08x}  (expect 0x3e0903ac or similar ~0.28)")
    print(f"  first float: {first_float:.6f}  (expect ~0.28272)")

    # Try to re-parse as proto — should be garbage or fail
    proto_fields = list(parse_proto_flat(f3_blob))
    can_parse = len(proto_fields) > 5  # if it yields many valid-looking fields it parses
    print(f"  proto re-parse yields {len(proto_fields)} fields  (expect: few/none — this is float data)")

    # Unpack all 76 floats
    floats = struct.unpack_from(f'<{n_floats}f', f3_blob, 0)

    passed = (
        n_floats == 76 and
        remainder == 0 and
        abs(first_float - 0.28272) < 0.002
    )
    status = "PASS" if passed else "FAIL"
    print(f"  => {status}: n_floats={n_floats}, first={first_float:.5f}")
    return passed, floats


def test_claim4(floats):
    """
    Claim 4: (f2 - f1) / (N-1) = (755-380)/75 = 5.0 exactly => 76 samples at 5nm step 380..755nm
    """
    print("\n=== CLAIM 4 ===")
    if floats is None:
        print("  SKIP: no floats from claim 3")
        return False, None

    n = len(floats)
    f1 = 380
    f2 = 755
    if n < 2:
        print("  FAIL: not enough floats")
        return False, None

    step = (f2 - f1) / (n - 1)
    expected_step = 5.0
    step_exact = (step == expected_step)
    print(f"  N={n}, range=({f1},{f2}), step=(755-380)/(76-1) = {f2-f1}/{n-1} = {step}")
    print(f"  step == 5.0 exactly: {step_exact}")
    # Wavelength for each index
    wavelengths = [f1 + i * step for i in range(n)]
    print(f"  wavelengths[0]={wavelengths[0]}, wavelengths[-1]={wavelengths[-1]}")

    passed = step_exact and n == 76
    status = "PASS" if passed else "FAIL"
    print(f"  => {status}")
    return passed, floats


def test_claim5(f8_data: bytes):
    """
    Claim 5: 3 channel peak indices rec0: idx43, idx29, idx18
      => peaks at 595nm, 525nm, 470nm => R/G/B spectral ordering
    """
    print("\n=== CLAIM 5 ===")
    if f8_data is None:
        print("  SKIP: no f8_data")
        return False

    inner_f2 = collect_field(f8_data, 2)
    if len(inner_f2) < 3:
        print(f"  FAIL: only {len(inner_f2)} channels, need 3")
        return False

    peak_indices = []
    peak_wavelengths = []
    channel_floats_list = []

    for ch_idx, (wt, ch_data) in enumerate(inner_f2):
        ch_f1 = collect_field(ch_data, 1)
        ch_f3 = collect_field(ch_data, 3)
        f1_val = ch_f1[0][1] if ch_f1 else 380
        f3_blob = ch_f3[0][1] if ch_f3 else None
        if f3_blob and len(f3_blob) == 304:
            floats = struct.unpack_from('<76f', f3_blob)
            peak_idx = max(range(76), key=lambda i: floats[i])
            peak_nm = f1_val + peak_idx * 5
            peak_indices.append(peak_idx)
            peak_wavelengths.append(peak_nm)
            channel_floats_list.append(floats)
            print(f"  channel {ch_idx}: peak_idx={peak_idx}, peak_nm={peak_nm}nm, peak_val={floats[peak_idx]:.4f}")
        else:
            print(f"  channel {ch_idx}: missing or wrong-size f3 blob")
            return False

    # Expected: idx43 (595nm), idx29 (525nm), idx18 (470nm)
    expected_indices = [43, 29, 18]
    expected_nm = [595, 525, 470]

    passed = (peak_indices == expected_indices)
    nm_match = (peak_wavelengths == expected_nm)

    print(f"  observed indices: {peak_indices}  (expect {expected_indices})")
    print(f"  observed nm:      {peak_wavelengths}  (expect {expected_nm})")
    print(f"  indices match: {passed}, nm match: {nm_match}")
    status = "PASS" if passed and nm_match else "FAIL"
    print(f"  => {status}")
    return passed and nm_match


def test_claim6(blk6_payload: bytes):
    """
    Claim 6: all 42 records — f2.f8 present only in 14 f2.f1==2 records (len=950);
             28 f2.f1 in {0,6} records have len=0
    """
    print("\n=== CLAIM 6 ===")
    f13_entries = collect_field(blk6_payload, 13)
    print(f"  Total field13 (record) entries: {len(f13_entries)}  (expect 42)")

    f1_0_count = 0
    f1_2_count = 0
    f1_6_count = 0
    f1_other = []
    f8_nonzero_count = 0
    f8_zero_count = 0
    f8_on_f1_2 = 0
    f8_on_other = 0
    f8_lengths_on_f1_2 = []

    for rec_wt, rec_data in f13_entries:
        if rec_wt != 2:
            continue
        # Get field2 inside this record
        f2_list = collect_field(rec_data, 2)
        if not f2_list:
            continue
        f2_data = f2_list[0][1]

        # Get f2.field1 (camera type selector)
        f2_f1 = collect_field(f2_data, 1)
        f1_val = f2_f1[0][1] if f2_f1 else None

        # Get f2.field8
        f2_f8 = collect_field(f2_data, 8)
        f8_len = len(f2_f8[0][1]) if f2_f8 else 0

        if f1_val == 0:
            f1_0_count += 1
        elif f1_val == 2:
            f1_2_count += 1
        elif f1_val == 6:
            f1_6_count += 1
        else:
            f1_other.append(f1_val)

        if f8_len > 0:
            f8_nonzero_count += 1
            if f1_val == 2:
                f8_on_f1_2 += 1
                f8_lengths_on_f1_2.append(f8_len)
            else:
                f8_on_other += 1
        else:
            f8_zero_count += 1

    total_records = len(f13_entries)
    print(f"  f2.f1 == 0: {f1_0_count}")
    print(f"  f2.f1 == 2: {f1_2_count}  (expect 14)")
    print(f"  f2.f1 == 6: {f1_6_count}")
    print(f"  f2.f1 other: {f1_other}")
    print(f"  f8 non-zero (present): {f8_nonzero_count}  (expect 14)")
    print(f"  f8 zero/absent: {f8_zero_count}  (expect 28)")
    print(f"  f8 present on f1==2 records: {f8_on_f1_2}  (expect 14)")
    print(f"  f8 present on other f1 records: {f8_on_other}  (expect 0)")
    print(f"  f8 lengths on f1==2: {sorted(set(f8_lengths_on_f1_2))}  (expect ~950)")

    passed = (
        total_records == 42 and
        f1_2_count == 14 and
        f8_nonzero_count == 14 and
        f8_zero_count == 28 and
        f8_on_f1_2 == 14 and
        f8_on_other == 0
    )
    status = "PASS" if passed else "FAIL"
    print(f"  => {status}")
    return passed


def test_claim7(blk6_payload: bytes):
    """
    Claim 7: all 14 large records share (380,755) and 3 channels;
             per-camera curve values differ; cams10-14 ~35% lower peaks
    """
    print("\n=== CLAIM 7 ===")
    f13_entries = collect_field(blk6_payload, 13)

    large_records = []
    for rec_wt, rec_data in f13_entries:
        if rec_wt != 2:
            continue
        f2_list = collect_field(rec_data, 2)
        if not f2_list:
            continue
        f2_data = f2_list[0][1]
        f2_f1 = collect_field(f2_data, 1)
        f1_val = f2_f1[0][1] if f2_f1 else None
        if f1_val != 2:
            continue
        f2_f8 = collect_field(f2_data, 8)
        if not f2_f8:
            continue
        f8_data = f2_f8[0][1]
        large_records.append(f8_data)

    print(f"  Large records (f1==2, f8 present): {len(large_records)}  (expect 14)")

    range_consistency = True
    channel_count_consistency = True
    peak_values = []  # per record, per channel: [ch0_peak, ch1_peak, ch2_peak]

    for rec_idx, f8_data in enumerate(large_records):
        inner_f1 = collect_field(f8_data, 1)
        inner_f2 = collect_field(f8_data, 2)
        ch_count = len(inner_f2)

        if ch_count != 3:
            channel_count_consistency = False
            print(f"  rec{rec_idx}: channel count={ch_count} (expect 3)")
            continue

        rec_peaks = []
        rec_ranges = []
        for ch_wt, ch_data in inner_f2:
            ch_f1 = collect_field(ch_data, 1)
            ch_f2 = collect_field(ch_data, 2)
            ch_f3 = collect_field(ch_data, 3)
            f1v = ch_f1[0][1] if ch_f1 else None
            f2v = ch_f2[0][1] if ch_f2 else None
            f3_blob = ch_f3[0][1] if ch_f3 else None
            rec_ranges.append((f1v, f2v))
            if f3_blob and len(f3_blob) == 304:
                floats = struct.unpack_from('<76f', f3_blob)
                peak_val = max(floats)
                rec_peaks.append(peak_val)
            else:
                rec_peaks.append(None)

        # Check range consistency
        for r in rec_ranges:
            if r != (380, 755):
                range_consistency = False

        peak_values.append(rec_peaks)
        print(f"  rec{rec_idx:02d}: ranges={rec_ranges}, peaks={[f'{p:.4f}' if p else 'None' for p in rec_peaks]}")

    # Check per-camera curve values differ
    if len(peak_values) == 14:
        # Compare first channel peaks across all 14 records
        ch0_peaks = [p[0] for p in peak_values if p[0] is not None]
        ch0_unique = len(set(round(p, 4) for p in ch0_peaks))
        print(f"\n  ch0 peaks across 14 records (unique values): {ch0_unique}  (expect >1 — values differ)")

        # Cams 10-14 = last 5 (indices 9-13) vs first 9
        # Compare average peak of last 5 vs first 9
        early_avg = sum(ch0_peaks[:9]) / 9 if len(ch0_peaks) >= 9 else None
        late_avg = sum(ch0_peaks[9:14]) / 5 if len(ch0_peaks) >= 14 else None
        if early_avg and late_avg:
            ratio = late_avg / early_avg
            print(f"  early 9 avg ch0 peak: {early_avg:.4f}")
            print(f"  late 5 avg ch0 peak: {late_avg:.4f}")
            print(f"  ratio (late/early): {ratio:.3f}  (expect ~0.65 = ~35% lower)")
            late_lower = ratio < 0.8  # claim: ~35% lower
        else:
            late_lower = False
    else:
        ch0_unique = 0
        late_lower = False

    passed = (
        len(large_records) == 14 and
        range_consistency and
        channel_count_consistency and
        ch0_unique > 1 and
        late_lower
    )
    status = "PASS" if passed else "FAIL"
    print(f"\n  range_consistency={range_consistency}, channel_count_ok={channel_count_consistency}")
    print(f"  values_differ={ch0_unique > 1}, late_lower_35pct={late_lower}")
    print(f"  => {status}")
    return passed


def main():
    print(f"LRI: {LRI_PATH}")
    blocks = scan_lri_blocks(LRI_PATH)
    print(f"Total LELR blocks: {len(blocks)}")
    if len(blocks) < 7:
        print("ERROR: need at least 7 blocks (indices 0-6)")
        sys.exit(1)

    blk6 = blocks[6]
    print(f"Block[6] payload size: {blk6['payload_size'] if 'payload_size' in blk6 else len(blk6['payload'])} bytes")

    # Store payload in variable — it wasn't in the original scan_lri_blocks return
    blk6_payload = blk6['payload']

    # Pull rec0 data and f8 for claim 1+2
    c1_pass, f8_data = test_claim1(blk6_payload)
    c2_pass, c2_ctx = test_claim2(f8_data)

    f3_blob = c2_ctx[2] if c2_ctx else None
    c3_pass, floats = test_claim3(f3_blob)
    c4_pass, _ = test_claim4(floats)
    c5_pass = test_claim5(f8_data)
    c6_pass = test_claim6(blk6_payload)
    c7_pass = test_claim7(blk6_payload)

    print("\n=== CLAIM 8 (LEAD — interpretive, not verifiable by parse) ===")
    print("  Claim 8 states these 380-755nm 76-tap curves are spectral sensitivity curves")
    print("  consumed at render time; exact downstream consumer in libcp not traced here.")
    print("  This is a LEAD, not an OBSERVED claim — cannot pass/fail by LRI parse alone.")
    print("  Observation: 76 float32 values per channel spanning 380-755nm at 5nm resolution")
    print("  with per-camera variation is consistent with spectral sensitivity characterization.")
    print("  Confidence: Hypothesis. Source: LRI block[6] field13[*].field2.field8.field2[N].field3")
    print("  Scope: LRI parse only; libcp consumer not traced in this investigation.")

    print("\n=== SUMMARY ===")
    results = {
        1: c1_pass,
        2: c2_pass,
        3: c3_pass,
        4: c4_pass,
        5: c5_pass,
        6: c6_pass,
        7: c7_pass,
        8: None,  # LEAD
    }
    for k, v in results.items():
        if v is None:
            print(f"  Claim {k}: LEAD (not verifiable by LRI parse)")
        else:
            print(f"  Claim {k}: {'PASS' if v else 'FAIL'}")

    reliable = all(v is True for k, v in results.items() if v is not None)
    print(f"\nAll parse claims pass: {reliable}")
    return reliable


if __name__ == "__main__":
    main()
