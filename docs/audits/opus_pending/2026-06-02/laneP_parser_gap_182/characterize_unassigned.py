#!/usr/bin/env python3
"""Lane P — characterize the 182 LRIs unassigned by the two-unit partition.

Quarantine analysis (NEEDS_CODEX_VALIDATION). Deterministic, render-free.

The partition (runs/two_unit_corpus/per_file_unit_partition.py) assigns a unit only when some LELR
block has EXACTLY 16 field-13 records (16-camera intrinsics block); otherwise the file is "unassigned".
This script asks, for every unassigned file:
  1. Does it have LELR blocks at all? (none => truncated/corrupt/non-LELR)
  2. What field-13 record counts DO its blocks have? (older firmware may use !=16, or a different field)
  3. For a more-robust intrinsics candidate (the block with the MOST field-13 records, if >0), compute
     its payload sha256[:16] — does it match Unit-1 (722a6e72) / Unit-2 (223961c6) or a NEW signature?
Aggregate + date distribution. Output is raw observation only; no claim is promoted here.
"""
import sys, glob, hashlib, collections
sys.path.insert(0, '/Volumes/Dev/L16_Lumen_ReverseEngineering/tools')
import lri_field_inspect as L

UNIT1 = '722a6e721636c9c4'
UNIT2 = '223961c6bce6153e'
OUT = '/Volumes/Dev/L16-opus-quarantine/runs/laneP_parser_gap_182/characterize_report.txt'

def field13_counts(path):
    """Return list of (block_index, n_field13, payload_sha16) per block, or None if scan fails."""
    try:
        blks = L.scan_lri_blocks(path)
    except Exception:
        return None
    out = []
    for i, blk in enumerate(blks):
        try:
            n13 = sum(1 for fn, wt, rv in L.parse_proto_fields(blk['payload']) if fn == 13)
        except Exception:
            n13 = -1  # payload present but proto parse failed
        out.append((i, n13, hashlib.sha256(blk['payload']).hexdigest()[:16]))
    return out

def is_assigned(path):
    info = field13_counts(path)
    if info is None:
        return None
    for _, n13, _ in info:
        if n13 == 16:
            return True
    return False

files = sorted(glob.glob("/Volumes/Base Photos/Light/*/*.lri"))
unassigned = []
for p in files:
    if is_assigned(p) is not True:
        unassigned.append(p)

no_blocks = []                         # scan returned None or zero blocks
record_count_hist = collections.Counter()   # max field-13 count seen per unassigned file
candidate_sig = collections.Counter()  # sha of the max-field13 block
dates = collections.Counter()
detail = []

for p in unassigned:
    date = p.split('/')[-2]
    dates[date] += 1
    info = field13_counts(p)
    if not info:
        no_blocks.append(p)
        record_count_hist['NO_LELR_BLOCKS'] += 1
        detail.append((p, 'NO_LELR_BLOCKS', None))
        continue
    best = max(info, key=lambda t: t[1])  # block with most field-13 records
    maxn = best[1]
    record_count_hist[maxn] += 1
    sig = best[2] if maxn > 0 else None
    if sig is not None:
        if sig == UNIT1: candidate_sig['UNIT1(722a6e72)'] += 1
        elif sig == UNIT2: candidate_sig['UNIT2(223961c6)'] += 1
        else: candidate_sig[f'NEW:{sig}'] += 1
    detail.append((p, f'max_field13={maxn}', sig))

with open(OUT, 'w') as f:
    f.write(f"total corpus files: {len(files)}\n")
    f.write(f"unassigned (no block with exactly 16 field-13 records): {len(unassigned)}\n")
    f.write(f"of which NO parseable LELR blocks at all: {len(no_blocks)}\n\n")
    f.write("=== max field-13 record count per unassigned file (why not 16?) ===\n")
    for k, c in record_count_hist.most_common():
        f.write(f"  max_field13={k}: {c} files\n")
    f.write("\n=== candidate unit signature (sha of the max-field13 block; tests for a THIRD unit) ===\n")
    if not candidate_sig:
        f.write("  (none had any field-13 records)\n")
    for k, c in candidate_sig.most_common():
        f.write(f"  {k}: {c} files\n")
    f.write("\n=== date distribution of unassigned (early-firmware hypothesis) ===\n")
    for d, c in sorted(dates.items()):
        f.write(f"  {d}: {c}\n")
    f.write("\n=== per-file detail ===\n")
    for p, why, sig in detail:
        f.write(f"  {why:24s} sig={sig}  {p}\n")

print(f"DONE unassigned={len(unassigned)} no_blocks={len(no_blocks)}")
print("record_count_hist:", dict(record_count_hist))
print("candidate_sig:", dict(candidate_sig))
print("report:", OUT)
