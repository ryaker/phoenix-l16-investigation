#!/usr/bin/env python3
"""Global robust affine fit lumen = a*phoenix + b per channel, plus quantiles.

Usage: fitall.py <phoenix_tag> [shot ...]
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
for n in shots:
    pp, lp = f"/tmp/{n}_{tag}.hdr", f"{OUT}/{n}_lumen.hdr"
    if not (os.path.exists(pp) and os.path.exists(lp)):
        print("%-9s [missing]" % n); continue
    Lb, Pb = grid3(load(lp), G, GH), grid3(load(pp), G, GH)
    print(n)
    for c in range(3):
        p, l = Pb[:, :, c].ravel(), Lb[:, :, c].ravel()
        m = (p > 1e-6) & (l >= 0)
        p, l = p[m], l[m]
        a, b = np.polyfit(p, l, 1)
        for _ in range(4):           # IRLS-ish trim
            r = l - (a * p + b)
            s = 1.4826 * np.median(np.abs(r - np.median(r))) + 1e-12
            k = np.abs(r) < 3 * s
            a, b = np.polyfit(p[k], l[k], 1)
        qp = np.quantile(p, [0.01, 0.05, 0.25, 0.50, 0.95])
        ql = np.quantile(l, [0.01, 0.05, 0.25, 0.50, 0.95])
        print("  %s a=%.5f b=%+.6f  x0=%+.6f | P%s | L%s"
              % (CH[c], a, b, -b / a,
                 np.array2string(qp, precision=5, floatmode='fixed'),
                 np.array2string(ql, precision=5, floatmode='fixed')))
