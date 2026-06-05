#!/usr/bin/env python3
"""Spectral block corpus verifier — independent RE parse.

For each seed LRI:
  1. Scan LELR blocks, identify the spectral block index (28mm=idx6, others=idx7)
     by checking msg_type and payload size hints.
  2. Parse the outer field-13 repeated message (per-camera spectral entries).
  3. For each per-camera entry, decode field 2 (3x channel sub-messages) and
     field 1 (cam_id).
  4. For each channel sub-msg: field1=wavelength_start(int), field2=wavelength_end(int),
     field3=304-byte blob (76 float32 LE).
  5. Report: num_cams, channels, nm range, float count, per-cam ch0 peak (val+nm).
  6. Compute SHA-256 over first 12 floats (f32 LE, ch0) of cam0 per seed.

Reports claims vs actuals for each seed.
"""

import hashlib
import struct
import sys
from pathlib import Path

# ─── protobuf primitives ─────────────────────────────────────────────────────

def read_varint(data: bytes, pos: int):
    result, shift = 0, 0
    while pos < len(data):
        b = data[pos]; pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            return result, pos
        shift += 7
    raise ValueError("truncated varint at end of data")


def iter_fields(data: bytes):
    """Yield (field_num, wire_type, raw_value) from a proto blob."""
    pos = 0
    while pos < len(data):
        try:
            tag, pos = read_varint(data, pos)
        except (ValueError, IndexError):
            break
        fnum = tag >> 3
        wt   = tag & 0x7
        if fnum == 0:
            break
        if wt == 0:
            val, pos = read_varint(data, pos)
            yield fnum, wt, val
        elif wt == 1:
            if pos + 8 > len(data): break
            val = struct.unpack_from('<Q', data, pos)[0]
            pos += 8
            yield fnum, wt, val
        elif wt == 2:
            length, pos = read_varint(data, pos)
            if pos + length > len(data): break
            val = data[pos:pos+length]
            pos += length
            yield fnum, wt, val
        elif wt == 5:
            if pos + 4 > len(data): break
            val = struct.unpack_from('<I', data, pos)[0]
            pos += 4
            yield fnum, wt, val
        else:
            break  # unknown wire type


# ─── LELR block scanner ───────────────────────────────────────────────────────

def scan_blocks(lri_path: str):
    blocks = []
    fsize = Path(lri_path).stat().st_size
    with open(lri_path, 'rb') as f:
        off, idx = 0, 0
        while off < fsize:
            f.seek(off)
            hdr = f.read(32)
            if len(hdr) < 32 or hdr[0:4] != b'LELR':
                break
            total_len  = struct.unpack_from('<Q', hdr, 4)[0]
            msg_offset = struct.unpack_from('<Q', hdr, 12)[0]
            msg_len    = struct.unpack_from('<I', hdr, 20)[0]
            msg_type   = hdr[24]
            if total_len == 0:
                break
            f.seek(off + msg_offset)
            payload = f.read(msg_len)
            blocks.append({
                'idx': idx,
                'off': off,
                'msg_type': msg_type,
                'payload_size': msg_len,
                'total_size': total_len,
                'payload': payload,
            })
            off += total_len
            idx += 1
    return blocks


# ─── spectral block extraction ────────────────────────────────────────────────

def extract_spectral_entry(entry_blob: bytes):
    """Parse one per-camera spectral message:
    field 1 = cam_id (varint)
    field 2 = repeated channel sub-msg (3x expected):
        field 1 = wl_start (varint, nm)
        field 2 = wl_end   (varint, nm)
        field 3 = float blob (304 bytes = 76 float32 LE)
    Returns: {'cam_id': int, 'channels': [{'wl_start','wl_end','floats':[76 f32]}]}
    """
    cam_id = None
    channels = []
    for fnum, wt, val in iter_fields(entry_blob):
        if fnum == 1 and wt == 0:
            cam_id = val
        elif fnum == 2 and wt == 2:
            # channel sub-message
            ch = {}
            for cfnum, cwt, cval in iter_fields(val):
                if cfnum == 1 and cwt == 0:
                    ch['wl_start'] = cval
                elif cfnum == 2 and cwt == 0:
                    ch['wl_end'] = cval
                elif cfnum == 3 and cwt == 2:
                    n = len(cval) // 4
                    ch['floats'] = list(struct.unpack_from(f'<{n}f', cval))
                    ch['blob_bytes'] = len(cval)
            channels.append(ch)
    return {'cam_id': cam_id, 'channels': channels}


def parse_spectral_block(payload: bytes):
    """Parse LightHeader field 13 (depth_config label in old map, actually spectral data).
    The spectral block payload IS the repeated-field-13 message:
    field 13 repeated => per-camera spectral entries.

    Actually: the spectral block IS the block payload directly.
    The block payload is a proto message where field 13 is repeated
    (one per camera).
    """
    cam_entries = []
    # field 13 = repeated sub-msg containing per-camera spectral data
    for fnum, wt, val in iter_fields(payload):
        if fnum == 13 and wt == 2:
            entry = extract_spectral_entry(val)
            cam_entries.append(entry)
    return cam_entries


# ─── SHA-256 of first-12 floats of cam0 ch0 ──────────────────────────────────

def sha256_first12(cam_entries):
    """SHA-256 over first 12 float32 values of cam0, channel 0, as raw LE bytes."""
    if not cam_entries:
        return None
    # find cam_id=0
    cam0 = None
    for e in cam_entries:
        if e['cam_id'] == 0:
            cam0 = e
            break
    if cam0 is None or not cam0['channels']:
        return None
    ch0 = cam0['channels'][0]
    floats = ch0.get('floats', [])
    if len(floats) < 12:
        return None
    raw = struct.pack(f'<12f', *floats[:12])
    return hashlib.sha256(raw).hexdigest()[:12]  # first 12 hex chars = 48 bits


# ─── per-cam ch0 peak ─────────────────────────────────────────────────────────

def ch0_peak(cam_entries):
    """Return dict cam_id -> (peak_nm, peak_val) for ch0."""
    results = {}
    for e in cam_entries:
        cid = e['cam_id']
        if not e['channels']:
            results[cid] = None
            continue
        ch0 = e['channels'][0]
        floats = ch0.get('floats', [])
        if not floats:
            results[cid] = None
            continue
        wl_start = ch0.get('wl_start', 380)
        wl_end   = ch0.get('wl_end', 755)
        n = len(floats)
        nm_step = (wl_end - wl_start) / (n - 1) if n > 1 else 0
        pk_idx = max(range(n), key=lambda i: floats[i])
        pk_nm  = wl_start + pk_idx * nm_step
        pk_val = floats[pk_idx]
        results[cid] = (pk_nm, pk_val)
    return results


# ─── main ─────────────────────────────────────────────────────────────────────

SEEDS = [
    # (label, lri_path, expected_spectral_block_idx)
    ("U1_28", "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri", 6),
    ("U1_35", "/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri", 7),
    ("U1_70", "/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri", 7),
    ("U1_150","/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri", 7),
    ("U2_28", "/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri",  6),
    ("U2_35", "/Volumes/Base Photos/Light/2018-10-28/L16_03041.lri",  7),
    ("U2_70", "/Volumes/Base Photos/Light/2020-07-14/L16_03434.lri",  7),
    ("U2_150","/Volumes/Base Photos/Light/2018-07-07/L16_02285.lri",  7),
]

def main():
    print("=" * 80)
    print("SPECTRAL CORPUS INDEPENDENT VERIFICATION")
    print("=" * 80)

    sha_by_label = {}

    for label, lri_path, expected_idx in SEEDS:
        print(f"\n{'─'*70}")
        print(f"SEED: {label}  path={lri_path}")
        lri = Path(lri_path)
        if not lri.exists():
            print(f"  [ERROR] file not found")
            continue

        blocks = scan_blocks(str(lri))
        print(f"  blocks found: {len(blocks)}")
        print(f"  block sizes: { [(b['idx'], b['payload_size']) for b in blocks[:12]] }")

        if expected_idx >= len(blocks):
            print(f"  [ERROR] expected block idx {expected_idx} does not exist (only {len(blocks)} blocks)")
            continue

        spectral_block = blocks[expected_idx]
        payload = spectral_block['payload']
        print(f"  spectral block idx={expected_idx} payload_bytes={len(payload)}")

        cam_entries = parse_spectral_block(payload)
        print(f"  cam entries (field-13 repeats): {len(cam_entries)}")

        if not cam_entries:
            print(f"  [ERROR] no cam entries found — trying alt block indices...")
            for b in blocks:
                test_entries = parse_spectral_block(b['payload'])
                if len(test_entries) >= 10:
                    print(f"    found {len(test_entries)} entries at block idx={b['idx']}")
                    cam_entries = test_entries
                    break
            if not cam_entries:
                print(f"  [ERROR] no spectral data found in any block")
                continue

        # Summarize
        cam_ids = sorted([e['cam_id'] for e in cam_entries if e['cam_id'] is not None])
        print(f"  cam_ids: {cam_ids}  (count={len(cam_ids)})")

        for e in cam_entries[:2]:  # show first 2 cams in detail
            cid = e['cam_id']
            print(f"  cam {cid}: {len(e['channels'])} channels")
            for i, ch in enumerate(e['channels']):
                n = len(ch.get('floats', []))
                blob = ch.get('blob_bytes', n*4)
                print(f"    ch{i}: wl={ch.get('wl_start','?')}-{ch.get('wl_end','?')}nm  "
                      f"floats={n}  blob_bytes={blob}")

        # Per-cam ch0 peaks
        peaks = ch0_peak(cam_entries)
        print(f"  ch0 peaks by cam:")
        for cid in sorted(peaks.keys()):
            if peaks[cid]:
                nm, val = peaks[cid]
                print(f"    cam{cid:2d}: peak={nm:.1f}nm  val={val:.5f}")
            else:
                print(f"    cam{cid:2d}: NONE")

        # SHA-256 of first 12 floats of cam0 ch0
        sha = sha256_first12(cam_entries)
        sha_by_label[label] = sha
        print(f"  SHA-256(first12 floats cam0 ch0): {sha}")

        # Verify per-cam entry size consistency
        entry_sizes = []
        for e in cam_entries:
            sz = 0
            for ch in e['channels']:
                sz += ch.get('blob_bytes', 0)
            entry_sizes.append(sz)
        print(f"  per-cam total float blob bytes: min={min(entry_sizes)} max={max(entry_sizes)}")

    # Summary table
    print(f"\n{'='*70}")
    print("SHA-256(first12) SUMMARY:")
    for lbl, sha in sha_by_label.items():
        print(f"  {lbl:8s}: {sha}")

    print("\nCROSS-UNIT COMPARISON:")
    u1_shas = set(v for k, v in sha_by_label.items() if k.startswith("U1_") and v)
    u2_shas = set(v for k, v in sha_by_label.items() if k.startswith("U2_") and v)
    print(f"  U1 unique shas: {u1_shas}")
    print(f"  U2 unique shas: {u2_shas}")
    print(f"  U1 intra-consistent: {len(u1_shas) == 1}")
    print(f"  U2 intra-consistent: {len(u2_shas) == 1}")
    u1_sha = next(iter(u1_shas)) if u1_shas else None
    u2_sha = next(iter(u2_shas)) if u2_shas else None
    print(f"  U1 != U2: {u1_sha != u2_sha if u1_sha and u2_sha else 'UNKNOWN'}")

    # Claim 1 expected sha
    print(f"\nExpected from claim:")
    print(f"  U1 sha: 6feebc3c5989")
    print(f"  U2 sha: c0dceb3813b5")
    if u1_sha:
        print(f"  U1 match: {u1_sha == '6feebc3c5989'}")
    if u2_sha:
        print(f"  U2 match: {u2_sha == 'c0dceb3813b5'}")


if __name__ == "__main__":
    main()
