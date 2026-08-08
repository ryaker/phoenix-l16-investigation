#!/usr/bin/env python3
"""Spatial map of near-zero pixels in a Lumen master vs a Phoenix master.

Prints, per shot, a 16x12 map of the fraction of pixels whose G value is below
a threshold, for Lumen and for Phoenix.  Reveals whether Lumen's deep-black
mass is a localized region (mask/geometry) or spread over the frame (tone).

Usage: zeromap.py <phoenix_tag> [shot ...]
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
THR = 1e-4
TX, TY = 16, 12


def tilemap(A):
    g = A[:, :, 1]
    h, w = g.shape
    rows = []
    for ty in range(TY):
        y0, y1 = ty * h // TY, (ty + 1) * h // TY
        r = []
        for tx in range(TX):
            x0, x1 = tx * w // TX, (tx + 1) * w // TX
            r.append((g[y0:y1, x0:x1] < THR).mean())
        rows.append(r)
    return rows


for n in shots:
    for label, path in (("L", f"{OUT}/{n}_lumen.hdr"), ("P", f"/tmp/{n}_{tag}.hdr")):
        if not os.path.exists(path):
            print("%-9s %s [missing]" % (n, label)); continue
        A = load(path)
        print("== %s %s  frac(G < %g)  %dx%d" % (n, label, THR, A.shape[1], A.shape[0]))
        for r in tilemap(A):
            print("   " + " ".join("%5.3f" % v for v in r))
