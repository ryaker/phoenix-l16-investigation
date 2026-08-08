#!/usr/bin/env python3
"""Low-end census of a Lumen master vs a Phoenix master.

For each channel: exact-zero fraction, fraction below a set of thresholds,
and the smallest nonzero values.  Decides whether Lumen hard-clamps a black
trim (mass at exactly 0) or merely scales.

Usage: lowend.py <phoenix_tag> [shot ...]
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_a = sys.argv
sys.argv = [_a[0]]
from radial import load, OUT, NAMES
sys.argv = _a

tag = sys.argv[1]
shots = sys.argv[2:] or NAMES
THR = [0.0, 1e-6, 1e-5, 1e-4, 5e-4, 1e-3, 0.0025, 0.005, 0.0075]
for n in shots:
    pp, lp = f"/tmp/{n}_{tag}.hdr", f"{OUT}/{n}_lumen.hdr"
    for label, path in (("L", lp), ("P", pp)):
        if not os.path.exists(path):
            print("%-9s %s [missing]" % (n, label)); continue
        A = load(path)
        print("== %s %s  (%s)" % (n, label, os.path.basename(path)))
        for c, cn in enumerate("RGB"):
            v = A[:, :, c].ravel()
            tot = v.size
            cnt = ["%.4f" % ((v <= t).sum() / tot) if t > 0 else
                   "%.4f" % ((v == 0.0).sum() / tot) for t in THR]
            nz = v[v > 0]
            mn = nz.min() if nz.size else 0.0
            print("   %s zero=%s  <=1e-6..7.5e-3: %s  minnz=%.3e" %
                  (cn, cnt[0], " ".join(cnt[1:]), mn))
