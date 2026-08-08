#!/usr/bin/env python3
"""Separate the two u2_35 defects:
   (1) a SPATIAL falloff in the well-exposed part of the frame
   (2) a LOW-END crush confined to dark cells
Restricts to cells above a luma floor, then fits ratio vs radius / |dx| / |dy|.

usage: ratiosplit.py <tag> <shot> [<lumen_shot>] [<grid>] [<lumafloor>]
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
    NG = int(sys.argv[4]) if len(sys.argv) > 4 else 16
    FLOOR = float(sys.argv[5]) if len(sys.argv) > 5 else 0.01
    P, _, _ = load("/tmp/%s_%s.hdr" % (shot, tag))
    L, _, _ = load("%s/%s_lumen.hdr" % (OUT, lshot))
    TW = 1200
    p = down(P, TW).astype(np.float64)
    l = down(L, TW).astype(np.float64)
    H = min(p.shape[0], l.shape[0])
    p, l = p[:H], l[:H]
    cy, cx = H / 2.0, TW / 2.0
    rmax = np.hypot(cy, cx)

    rec = []
    for gy in range(NG):
        y0, y1 = gy * H // NG, (gy + 1) * H // NG
        for gx in range(NG):
            x0, x1 = gx * TW // NG, (gx + 1) * TW // NG
            pp = p[y0:y1, x0:x1, 1].ravel()
            ll = l[y0:y1, x0:x1, 1].ravel()
            m = pp > 1e-5
            if m.sum() < 50:
                continue
            rat = float(np.median(ll[m] / pp[m]))
            lum = float(np.median(pp[m]))
            dy = ((y0 + y1) / 2.0 - cy) / rmax
            dx = ((x0 + x1) / 2.0 - cx) / rmax
            per = []
            for c in range(3):
                a = p[y0:y1, x0:x1, c].ravel()[m]
                b = l[y0:y1, x0:x1, c].ravel()[m]
                per.append(float(np.median(b / np.maximum(a, 1e-9))))
            rec.append((dx, dy, np.hypot(dx, dy), rat, lum, per))

    a = np.array([(r[0], r[1], r[2], r[3], r[4]) for r in rec])
    dx, dy, rad, rat, lum = a.T
    for name, sel in (("ALL", np.ones(len(rat), bool)),
                      ("BRIGHT (luma>%g)" % FLOOR, lum > FLOOR),
                      ("DARK   (luma<=%g)" % FLOOR, lum <= FLOOR)):
        n = int(sel.sum())
        if n < 4:
            print("%-22s n=%d (too few)" % (name, n)); continue
        r_, d_, x_, y_, l_ = rat[sel], rad[sel], np.abs(dx[sel]), np.abs(dy[sel]), lum[sel]
        print("\n%-22s n=%3d  ratio med=%.4f  [%.4f .. %.4f]" %
              (name, n, np.median(r_), r_.min(), r_.max()))
        for nm, v in (("radius", d_), ("|dx|", x_), ("|dy|", y_),
                      ("dx", dx[sel]), ("dy", dy[sel]), ("log luma", np.log(l_))):
            X = np.stack([np.ones(n), v], 1)
            b, *_ = np.linalg.lstsq(X, r_, rcond=None)
            r2 = 1.0 - ((r_ - X @ b) ** 2).sum() / max(((r_ - r_.mean()) ** 2).sum(), 1e-30)
            print("   ratio ~ %+.4f %+.4f*%-9s R2=%.4f  corr=%+.4f" %
                  (b[0], b[1], nm, r2, np.corrcoef(v, r_)[0, 1]))

    sel = lum > FLOOR
    print("\nBRIGHT-cell ratio vs radius, binned:")
    d_, r_ = rad[sel], rat[sel]
    edges = np.linspace(0, d_.max() + 1e-9, 7)
    for i in range(6):
        m = (d_ >= edges[i]) & (d_ < edges[i + 1])
        if m.sum():
            print("   r=%.2f-%.2f  n=%3d  med ratio=%.4f" %
                  (edges[i], edges[i + 1], m.sum(), np.median(r_[m])))
    pc = np.array([r[5] for r in rec])[sel]
    print("\nBRIGHT per-channel median ratio: R=%.4f G=%.4f B=%.4f" %
          tuple(np.median(pc, 0)))


if __name__ == "__main__":
    main()
