import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_a = sys.argv
sys.argv = [_a[0]]
from radial import load, grid3, boxgrid, ncc, crop_center, G, GH, OUT
sys.argv = _a

tag = sys.argv[1]
shots = sys.argv[2:]
yy, xx = np.mgrid[0:GH, 0:G]
rad = np.sqrt(((yy + 0.5) / GH - 0.5) ** 2 + ((xx + 0.5) / G - 0.5) ** 2) / 0.5
EDGES = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.42]

for n in shots:
    pp, lp = f"/tmp/{n}_{tag}.hdr", f"{OUT}/{n}_lumen.hdr"
    L, P = load(lp), load(pp)
    Pg = np.log1p(np.maximum(boxgrid(P[:, :, 1], G, GH), 0) * 1e3)
    curve = []
    for z in np.arange(0.90, 1.101, 0.005):
        if z <= 1.0:
            c = ncc(np.log1p(np.maximum(boxgrid(crop_center(L, z)[:, :, 1], G, GH), 0) * 1e3), Pg)
        else:
            a = np.log1p(np.maximum(boxgrid(crop_center(P, 1.0 / z)[:, :, 1], G, GH), 0) * 1e3)
            c = ncc(np.log1p(np.maximum(boxgrid(L[:, :, 1], G, GH), 0) * 1e3), a)
        curve.append((z, c))
    best = max(curve, key=lambda t: t[1])
    print("%s fine-zoom best=%.3f ncc=%.4f" % (n, best[0], best[1]))
    print("   " + "  ".join("%.3f:%.4f" % t for t in curve[::2]))
    Lb, Pb = grid3(L, G, GH), grid3(P, G, GH)
    print("   ring     medG_lumen   medG_phx    ratio_of_med   med_of_ratio")
    for a, b in zip(EDGES[:-1], EDGES[1:]):
        m = (rad >= a) & (rad < b) & (Lb[:, :, 1] > 1e-5) & (Pb[:, :, 1] > 1e-5)
        if m.sum() < 8:
            continue
        ml = float(np.median(Lb[:, :, 1][m])); mp = float(np.median(Pb[:, :, 1][m]))
        mr = float(np.median(Lb[:, :, 1][m] / Pb[:, :, 1][m]))
        print("   %.1f-%.1f  %.6f    %.6f    %.4f        %.4f" % (a, b, ml, mp, ml / mp, mr))
