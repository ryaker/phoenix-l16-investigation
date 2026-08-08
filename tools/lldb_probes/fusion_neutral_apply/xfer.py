#!/usr/bin/env python3
"""Binned Lumen-vs-Phoenix transfer curve (no model assumed).

Usage: xfer.py <phoenix_tag> [shot ...]
Prints, per channel, the median Lumen value in each Phoenix-value bin plus the
ratio L/P, so a pure gain (flat ratio), a gain+offset (ratio rising to an
asymptote) and a genuine curve are distinguishable by eye.
"""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_a = sys.argv
sys.argv = [_a[0]]
from radial import load, grid3, G, GH, OUT, NAMES
sys.argv = _a

tag = sys.argv[1]
shots = sys.argv[2:] or NAMES
CH = "RGB"
NB = 14
for n in shots:
    pp, lp = f"/tmp/{n}_{tag}.hdr", f"{OUT}/{n}_lumen.hdr"
    if not (os.path.exists(pp) and os.path.exists(lp)):
        print("%-9s [missing]" % n); continue
    Lb, Pb = grid3(load(lp), G, GH), grid3(load(pp), G, GH)
    print("== %s (%s)" % (n, tag))
    for c in range(3):
        p, l = Pb[:, :, c].ravel(), Lb[:, :, c].ravel()
        m = p > 1e-7
        p, l = p[m], l[m]
        qs = np.quantile(p, np.linspace(0.02, 0.995, NB + 1))
        row = []
        for i in range(NB):
            k = (p >= qs[i]) & (p < qs[i + 1])
            if k.sum() < 20:
                continue
            pm, lm = np.median(p[k]), np.median(l[k])
            row.append("%.5f:%.4f" % (pm, lm / pm if pm > 0 else 0))
        print("  %s  %s" % (CH[c], "  ".join(row)))
