import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
_a = sys.argv
sys.argv = [_a[0]]
from radial import load, grid3, G, GH, OUT
sys.argv = _a

tag = sys.argv[1]
shots = sys.argv[2:]
yy, xx = np.mgrid[0:GH, 0:G]
rad = np.sqrt(((yy + 0.5) / GH - 0.5) ** 2 + ((xx + 0.5) / G - 0.5) ** 2) / 0.5

for n in shots:
    L = load(f"{OUT}/{n}_lumen.hdr"); P = load(f"/tmp/{n}_{tag}.hdr")
    Lb, Pb = grid3(L, G, GH), grid3(P, G, GH)
    lg, pg = Lb[:, :, 1], Pb[:, :, 1]
    m = (lg > 1e-5) & (pg > 1e-5)
    p = pg[m]; r = (lg / pg)[m]; rr = rad[m]
    q = np.quantile(p, np.linspace(0, 1, 11))
    print(n)
    print("  decile   phxG_lo    phxG_hi     medRatio   medRad    n")
    for i in range(10):
        s = (p >= q[i]) & (p <= q[i + 1]) if i == 9 else (p >= q[i]) & (p < q[i + 1])
        if s.sum() < 8:
            continue
        print("   %2d    %.6f  %.6f    %.4f    %.3f   %5d"
              % (i, q[i], q[i + 1], float(np.median(r[s])), float(np.median(rr[s])), s.sum()))
    # radius-controlled: within the outer ring only, split by brightness
    for lo, hi in ((0.0, 0.4), (0.8, 1.42)):
        s0 = (rr >= lo) & (rr < hi)
        if s0.sum() < 40:
            continue
        pv = p[s0]; rv = r[s0]
        qq = np.quantile(pv, [0.0, 0.25, 0.5, 0.75, 1.0])
        out = []
        for i in range(4):
            s = (pv >= qq[i]) & (pv <= qq[i + 1]) if i == 3 else (pv >= qq[i]) & (pv < qq[i + 1])
            if s.sum() < 5:
                out.append("--")
            else:
                out.append("%.4f" % float(np.median(rv[s])))
        print("  rad %.1f-%.2f  brightness-quartile ratios: %s" % (lo, hi, "  ".join(out)))
