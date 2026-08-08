#!/usr/bin/env python3
"""Coarse spatial map of the Lumen/Phoenix ratio on bright pixels only.

Usage: ratmap.py <phoenix_tag> [shot ...]
Bright-only (per-tile top-decile) so the shadow pedestal cannot bias it.
Prints an 8x6 grid of L/P per channel plus the global bright-pixel ratio.
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
TX, TY = 8, 6
for n in shots:
    pp, lp = f"/tmp/{n}_{tag}.hdr", f"{OUT}/{n}_lumen.hdr"
    if not (os.path.exists(pp) and os.path.exists(lp)):
        print("%-9s [missing]" % n); continue
    Lb, Pb = grid3(load(lp), G, GH), grid3(load(pp), G, GH)
    h, w = Pb.shape[0], Pb.shape[1]
    print("== %s (%s)  grid %dx%d" % (n, tag, w, h))
    for c in range(3):
        P, L = Pb[:, :, c], Lb[:, :, c]
        gm = P > np.quantile(P, 0.90)
        print("  %s global bright L/P = %.4f" % (CH[c], L[gm].sum() / P[gm].sum()))
        for ty in range(TY):
            y0, y1 = ty * h // TY, (ty + 1) * h // TY
            row = []
            for tx in range(TX):
                x0, x1 = tx * w // TX, (tx + 1) * w // TX
                p, l = P[y0:y1, x0:x1], L[y0:y1, x0:x1]
                m = p > np.quantile(p, 0.90)
                row.append("%.4f" % (l[m].sum() / p[m].sum()) if m.sum() else "  --  ")
            print("     " + " ".join(row))
