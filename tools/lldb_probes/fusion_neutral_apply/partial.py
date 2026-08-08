#!/usr/bin/env python3
"""Partial test: within narrow Phoenix-luma bands, does the L/P ratio still
depend on radius?  If NO, the apparent radial falloff and the dark-region
crush are ONE luma-dependent transfer, not a spatial (vignette) error.

usage: partial.py <tag> <shot> [<lumen_shot>] [<grid>]
"""
import sys, numpy as np
from hdrmean import load

OUT = "/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/runs/verify_master"


def down(A, tw):
    h, w, _ = A.shape
    th = max(1, int(round(h * tw / float(w))))
    return A[(np.arange(th) * h // th)][:, (np.arange(tw) * w // tw)]


def main():
    tag, shot = sys.argv[1], sys.argv[2]
    lshot = sys.argv[3] if len(sys.argv) > 3 else shot
    NG = int(sys.argv[4]) if len(sys.argv) > 4 else 40
    P, _, _ = load("/tmp/%s_%s.hdr" % (shot, tag))
    L, _, _ = load("%s/%s_lumen.hdr" % (OUT, lshot))
    TW = 1600
    p = down(P, TW).astype(np.float64)
    l = down(L, TW).astype(np.float64)
    H = min(p.shape[0], l.shape[0])
    p, l = p[:H], l[:H]
    cy, cx = H / 2.0, TW / 2.0
    rmax = np.hypot(cy, cx)

    rat, lum, rad = [], [], []
    for gy in range(NG):
        y0, y1 = gy * H // NG, (gy + 1) * H // NG
        for gx in range(NG):
            x0, x1 = gx * TW // NG, (gx + 1) * TW // NG
            pp = p[y0:y1, x0:x1, 1].ravel()
            ll = l[y0:y1, x0:x1, 1].ravel()
            m = pp > 1e-6
            if m.sum() < 30:
                continue
            rat.append(float(np.median(ll[m] / pp[m])))
            lum.append(float(np.median(pp[m])))
            rad.append(np.hypot((y0 + y1) / 2.0 - cy, (x0 + x1) / 2.0 - cx) / rmax)
    rat = np.array(rat); lum = np.array(lum); rad = np.array(rad)
    print("cells=%d" % len(rat))

    print("\nratio vs LUMA (all radii pooled):")
    q = np.quantile(lum, np.linspace(0, 1, 11))
    for i in range(10):
        m = (lum >= q[i]) & (lum <= q[i + 1] if i == 9 else lum < q[i + 1])
        if m.sum():
            print("  luma %.5f-%.5f  n=%4d  ratio med=%.4f  (rad med=%.2f)" %
                  (q[i], q[i + 1], m.sum(), np.median(rat[m]), np.median(rad[m])))

    print("\nPARTIAL: ratio vs RADIUS within each luma quintile")
    qq = np.quantile(lum, np.linspace(0, 1, 6))
    for i in range(5):
        m = (lum >= qq[i]) & (lum <= qq[i + 1] if i == 4 else lum < qq[i + 1])
        if m.sum() < 20:
            continue
        r_, d_ = rat[m], rad[m]
        c = np.corrcoef(d_, r_)[0, 1]
        line = []
        for j in range(4):
            lo, hi = j * 0.25, (j + 1) * 0.25 + (1e9 if j == 3 else 0)
            mm = (d_ >= lo) & (d_ < hi)
            line.append("r%.2f-%.2f:%s" % (lo, min(hi, 1.0),
                        ("%.4f" % np.median(r_[mm])) if mm.sum() >= 3 else "  --  "))
        print("  luma %.5f-%.5f n=%4d corr(rad)=%+.3f | %s" %
              (qq[i], qq[i + 1], m.sum(), c, "  ".join(line)))

    print("\nPARTIAL: ratio vs LUMA within each radius band")
    for j in range(4):
        lo, hi = j * 0.25, (j + 1) * 0.25 + (1e9 if j == 3 else 0)
        m = (rad >= lo) & (rad < hi)
        if m.sum() < 20:
            continue
        r_, l_ = rat[m], lum[m]
        c = np.corrcoef(np.log(l_), r_)[0, 1]
        qs = np.quantile(l_, np.linspace(0, 1, 5))
        line = []
        for i in range(4):
            mm = (l_ >= qs[i]) & (l_ <= qs[i + 1] if i == 3 else l_ < qs[i + 1])
            line.append("%.4f" % np.median(r_[mm]) if mm.sum() >= 3 else "  --  ")
        print("  rad %.2f-%.2f n=%4d corr(logluma)=%+.3f | Q1..Q4 ratio: %s" %
              (lo, min(hi, 1.0), m.sum(), c, "  ".join(line)))

    X = np.stack([np.ones(len(rat)), rad, np.log(lum)], 1)
    for nm, cols in (("radius only", [0, 1]), ("logluma only", [0, 2]),
                     ("both", [0, 1, 2])):
        Xo = X[:, cols]
        b, *_ = np.linalg.lstsq(Xo, rat, rcond=None)
        r2 = 1 - ((rat - Xo @ b) ** 2).sum() / ((rat - rat.mean()) ** 2).sum()
        print("R2 %-13s = %.4f   beta=%s" % (nm, r2, np.round(b, 4)))


if __name__ == "__main__":
    main()
