#!/usr/bin/env python3
"""Deterministic Unit-2 70mm level-0 boundary comparison (audit Next-Investigation #3).

Compares Phoenix dumps against the DETERMINISTIC Lumen captures
(runs/index5_nondeterminism/u2_70_executor_serial_r1 + u2_70_serial2d30_r1),
in the audit's prescribed order, reporting the FIRST divergent boundary:

  A. Guidance + four source planes (2080x1560 RGBA8, byte-exact target)
  B. Composed projection records (numeric; Phoenix geom.txt vs captured H)
  C. Normalized G-42 local cost at the captured reference pixel
     (local_curve.u16le, hypotheses [lower, lower+count))
  D. Final argmin index map (index5_hypothesis_index.u16le, u16le 2080x1560)

This is ACCEPTANCE comparison against proven deterministic captures -- it
identifies which ported stage first diverges. It licenses no tuning: any fix
must port proven behavior from the ledger/bundles, never fit the diff.

usage: compare_u2_70_level0_boundary.py <phoenix_dump_dir>
  where <phoenix_dump_dir> contains phx_src_image*.rgba8, idx_lvl5_*.u16,
  geom.txt, and the run.log with the [dumpcost] lines (pass the run.log path
  via --runlog if elsewhere).
"""
import argparse
import hashlib
import json
import os
import re
import struct
import sys

CAP = "/Volumes/Dev/L16_Lumen_ReverseEngineering/runs/index5_nondeterminism"
SER = os.path.join(CAP, "u2_70_executor_serial_r1")
IDX = os.path.join(CAP, "u2_70_serial2d30_r1")
W, H = 2080, 1560


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def cmp_bytes(a, b, label, elem="byte"):
    da, db = open(a, "rb").read(), open(b, "rb").read()
    if len(da) != len(db):
        print(f"  [{label}] SIZE MISMATCH phoenix={len(da)} lumen={len(db)}")
        return False
    if da == db:
        print(f"  [{label}] EXACT ({len(da)} bytes)")
        return True
    n = sum(1 for x, y in zip(da, db) if x != y)
    print(f"  [{label}] DIFFERS: {n}/{len(da)} {elem}s differ "
          f"({100.0*n/len(da):.3f}%)")
    return False


def cmp_u16_maps(a, b, label):
    da, db = open(a, "rb").read(), open(b, "rb").read()
    if len(da) != len(db):
        print(f"  [{label}] SIZE MISMATCH phoenix={len(da)} lumen={len(db)}")
        return False
    ua = struct.unpack(f"<{len(da)//2}H", da)
    ub = struct.unpack(f"<{len(db)//2}H", db)
    diff = [i for i in range(len(ua)) if ua[i] != ub[i]]
    if not diff:
        print(f"  [{label}] EXACT ({len(ua)} u16)")
        return True
    deltas = [abs(ua[i] - ub[i]) for i in diff]
    within1 = sum(1 for d in deltas if d <= 1)
    print(f"  [{label}] DIFFERS: {len(diff)}/{len(ua)} px "
          f"({100.0*len(diff)/len(ua):.3f}%), |delta| max={max(deltas)} "
          f"mean={sum(deltas)/len(deltas):.2f}, within-1={within1}")
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dumpdir")
    ap.add_argument("--runlog", default=None)
    args = ap.parse_args()
    d = args.dumpdir
    runlog = args.runlog or os.path.join(os.path.dirname(d.rstrip("/")), "run.log")

    rep = json.load(open(os.path.join(SER, "report.json")))
    print(f"captures: {SER}")
    print(f"phoenix : {d}")
    first_divergent = None

    # --- A: planes ---------------------------------------------------------
    # MEASURED 2026-08-10: u2_70_executor_serial_r1/image3.rgba8 (B1) is a
    # RACED capture -- 22.9% exact-zero (unwritten) tiles, 73.8% of bytes
    # differ vs r2, while images 0/1/2/4 are byte-identical r1==r2 and the
    # index5 map is byte-identical across serial2d30 r1/r2/r3. The plane G-42
    # consumed was complete; only the interpose read raced B1's
    # materialization. Ground truth for image3 therefore comes from r2.
    SER2 = SER.replace("_r1", "_r2")
    print("\nA. Guidance + source planes (level-0 2080x1560 RGBA8)")
    print("   (image3 compared against r2 -- r1's B1 capture is raced, see comment)")
    for i in range(5):
        base = SER2 if i == 3 else SER
        lum = os.path.join(base, f"image{i}.rgba8")
        cand = [f for f in os.listdir(d)
                if re.fullmatch(rf"phx_src_image{i}_{W}x{H}\.rgba8", f)]
        if not cand:
            print(f"  [image{i}] MISSING phoenix dump")
            first_divergent = first_divergent or f"A.image{i} (missing)"
            continue
        if not cmp_bytes(os.path.join(d, cand[0]), lum, f"image{i}"):
            first_divergent = first_divergent or f"A.image{i}"

    # --- B: records --------------------------------------------------------
    print("\nB. Composed projection records (captured 4x80B H | phoenix geom.txt)")
    recs = open(os.path.join(SER, "projection_records.bin"), "rb").read()
    for r in range(4):
        hcols = struct.unpack_from("<16f", recs, r * 0x50)
        print(f"  lumen rec{r} H col2/col3: "
              f"{[round(v,6) for v in hcols[8:12]]} {[round(v,6) for v in hcols[12:16]]}")
    gt = os.path.join(d, "geom.txt")
    if os.path.exists(gt):
        print("  phoenix geom.txt present -- numeric K/R/t comparison is manual "
              "(H = K_src [R|t] K_ref^-1 composition; no byte instrument yet)")
    else:
        print("  phoenix geom.txt MISSING")

    # --- C: G-42 local curve at reference pixel ---------------------------
    print(f"\nC. Normalized G-42 local cost at pixel {rep['reference_pixel']} "
          f"(hyp {rep['lower_hypothesis']}..{rep['lower_hypothesis']+rep['hypothesis_count']-1})")
    curve = struct.unpack(f"<{rep['hypothesis_count']}H",
                          open(os.path.join(SER, "local_curve.u16le"), "rb").read())
    print(f"  lumen  curve: {list(curve)}")
    phx_curve = None
    if os.path.exists(runlog):
        for line in open(runlog, errors="replace"):
            if "[dumpcost]" in line:
                print(f"  phoenix {line.strip()}")
                phx_curve = line.strip()
    if phx_curve is None:
        print("  phoenix [dumpcost] lines not found in run.log")

    # --- D: argmin index map ----------------------------------------------
    print("\nD. Final argmin index-5 map (u16le 2080x1560, deterministic capture)")
    lum_idx = os.path.join(IDX, "index5_hypothesis_index.u16le")
    cand = [f for f in os.listdir(os.path.join(d, os.pardir, "dumps"))
            if f.startswith("idx_lvl5_")] if os.path.isdir(os.path.join(d, os.pardir, "dumps")) else []
    cand = [f for f in os.listdir(d) if f.startswith("idx_lvl5_")] or cand
    if cand:
        if not cmp_u16_maps(os.path.join(d, cand[0]), lum_idx, "index5"):
            first_divergent = first_divergent or "D.index5"
    else:
        print("  phoenix idx_lvl5 dump MISSING")
        first_divergent = first_divergent or "D.index5 (missing)"

    print(f"\nFIRST DIVERGENT BOUNDARY: {first_divergent or 'none (A,D exact)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
