#!/usr/bin/env python3
"""Spatial ratio map L/P between a Lumen reference and a Phoenix render.

Separates a SPATIAL gain error (vignette / lens-shading: ratio correlates with
radius, independent of luma) from a TONE-TRANSFER error (ratio correlates with
luma, independent of position).

usage: ratiomap.py <tag> <shot> [<lumen_shot>] [<grid>]
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
    NG = int(sys.argv[4]) if len(sys.argv) > 4 else 12
    P, _, _ = load("/tmp/%s_%s.hdr" % (shot, tag))
    L, _, _ = load("%s/%s_lumen.hdr" % (OUT, lshot))
    TW = 1200
    p = down(P, TW).astype(np.float64)
    l = down(L, TW).astype(np.float64)
    H = min(p.shape[0], l.shape[0])
    p, l = p[:H], l[:H]
    pg, lg = p[:, :, 1], l[:, :, 1]

    print("grid %dx%d cells over %dx%d  (cell: med L/G, med P luma, radius)" %
          (NG, NG, TW, H))
    rows = []
    cy, cx = H / 2.0, TW / 2.0
    rmax = np.hypot(cy, cx)
    for gy in range(NG):
        y0, y1 = gy * H // NG, (gy + 1) * H // NG
        line = []
        for gx in range(NG):
            x0, x1 = gx * TW // NG, (gx + 1) * TW // NG
            pp = pg[y0:y1, x0:x1].ravel()
            ll = lg[y0:y1, x0:x1].ravel()
            m = pp > 1e-5
            if m.sum() < 50:
                line.append(np.nan); continue
            r = np.median(ll[m] / pp[m])
            line.append(r)
            rr = np.hypot((y0 + y1) / 2.0 - cy, (x0 + x1) / 2.0 - cx) / rmax
            rows.append((rr, r, float(np.median(pp[m]))))
        print("  " + " ".join("%6.3f" % v for v in line))

    a = np.array(rows)
    rad, rat, lum = a[:, 0], a[:, 1], a[:, 2]
    good = np.isfinite(rat) & (lum > 0)
    rad, rat, lum = rad[good], rat[good], lum[good]
    print("\ncells=%d  ratio: min=%.4f med=%.4f max=%.4f" %
          (len(rat), rat.min(), np.median(rat), rat.max()))
    ll = np.log(lum)
    print("corr(ratio, radius)   = %+.4f" % np.corrcoef(rad, rat)[0, 1])
    print("corr(ratio, log luma) = %+.4f" % np.corrcoef(ll, rat)[0, 1])
    # partial: regress ratio on both
    X = np.stack([np.ones_like(rad), rad, ll], 1)
    beta, *_ = np.linalg.lstsq(X, rat, rcond=None)
    pred = X @ beta
    ss = 1.0 - ((rat - pred) ** 2).sum() / ((rat - rat.mean()) ** 2).sum()
    print("ratio ~ %.4f %+.4f*radius %+.4f*log(luma)   R2=%.4f" %
          (beta[0], beta[1], beta[2], ss))
    # luma-only and radius-only R2
    for nm, Xo in (("radius", np.stack([np.ones_like(rad), rad], 1)),
                   ("logluma", np.stack([np.ones_like(rad), ll], 1))):
        b, *_ = np.linalg.lstsq(Xo, rat, rcond=None)
        pr = Xo @ b
        r2 = 1.0 - ((rat - pr) ** 2).sum() / ((rat - rat.mean()) ** 2).sum()
        print("  %-8s only  R2=%.4f" % (nm, r2))


if __name__ == "__main__":
    main()
