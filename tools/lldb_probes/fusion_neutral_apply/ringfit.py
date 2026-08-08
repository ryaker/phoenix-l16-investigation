#!/usr/bin/env python3
"""Per-ring affine fit lumen = a_r * phoenix + b_r on the FOV-aligned grid.

Discriminates two failure modes that both look like "edge falloff mismatch":
  (1) a shading-profile error  -> a_r varies with radius, b_r ~ 0
  (2) a residual pedestal that is AMPLIFIED by the lens-shading gain
      -> a_r ~ const, b_r grows (negatively) with radius in step with the gain

Usage: ringfit.py <phoenix_tag> [shot ...]
"""
import numpy as np, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_argv = sys.argv
sys.argv = [_argv[0]]
from radial import load, grid3, boxgrid, ncc, crop_center, G, GH, OUT, NAMES
sys.argv = _argv

tag = sys.argv[1]
shots = sys.argv[2:] or NAMES
yy, xx = np.mgrid[0:GH, 0:G]
rad = np.sqrt(((yy + 0.5) / GH - 0.5) ** 2 + ((xx + 0.5) / G - 0.5) ** 2) / 0.5
EDGES = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.42]

for n in shots:
    pp, lp = f"/tmp/{n}_{tag}.hdr", f"{OUT}/{n}_lumen.hdr"
    if not (os.path.exists(pp) and os.path.exists(lp)):
        print("%-9s [missing]" % n); continue
    L, P = load(lp), load(pp)
    Pg = np.log1p(np.maximum(boxgrid(P[:, :, 1], G, GH), 0) * 1e3)
    best = None
    for z in np.arange(0.30, 1.61, 0.01):
        if z <= 1.0:
            c = ncc(np.log1p(np.maximum(boxgrid(crop_center(L, z)[:, :, 1], G, GH), 0) * 1e3), Pg)
        else:
            a = np.log1p(np.maximum(boxgrid(crop_center(P, 1.0 / z)[:, :, 1], G, GH), 0) * 1e3)
            c = ncc(np.log1p(np.maximum(boxgrid(L[:, :, 1], G, GH), 0) * 1e3), a)
        if best is None or c > best[1]:
            best = (z, c)
    z = best[0]
    if z <= 1.0:
        Lb, Pb = grid3(crop_center(L, z), G, GH), grid3(P, G, GH)
    else:
        Lb, Pb = grid3(L, G, GH), grid3(crop_center(P, 1.0 / z), G, GH)
    print("%s  zoom=%.2f ncc=%.4f   (green channel)" % (n, z, best[1]))
    print("  ring        n     a_r      b_r        b_r/meanP    meanP")
    for lo, hi in zip(EDGES[:-1], EDGES[1:]):
        m = (rad >= lo) & (rad < hi) & (Lb[:, :, 1] > 1e-5) & (Pb[:, :, 1] > 1e-5)
        if m.sum() < 16:
            continue
        p, l = Pb[:, :, 1][m], Lb[:, :, 1][m]
        a, b = np.polyfit(p, l, 1)
        print("  %.1f-%.1f  %5d  %.4f  %+.6f  %+8.2f%%   %.5f"
              % (lo, hi, m.sum(), a, b, 100.0 * b / p.mean(), p.mean()))
