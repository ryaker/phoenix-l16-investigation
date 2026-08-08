#!/usr/bin/env python3
"""Per-pixel Lumen-vs-Phoenix transfer curve, restricted to the CENTRAL region
so any frame-edge / radial confound is removed.  Fine log-spaced Phoenix bins,
median Lumen value per bin, plus the implied local gain dL/dP.

usage: knee.py <tag> <shot> [<lumen_shot>] [<centre_frac>]
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
    CF = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
    P, _, _ = load("/tmp/%s_%s.hdr" % (shot, tag))
    L, _, _ = load("%s/%s_lumen.hdr" % (OUT, lshot))
    TW = 2000
    p = down(P, TW).astype(np.float64)
    l = down(L, TW).astype(np.float64)
    H = min(p.shape[0], l.shape[0])
    p, l = p[:H], l[:H]
    y0, y1 = int(H * (1 - CF) / 2), int(H * (1 + CF) / 2)
    x0, x1 = int(TW * (1 - CF) / 2), int(TW * (1 + CF) / 2)
    p, l = p[y0:y1, x0:x1], l[y0:y1, x0:x1]
    print("centre %.0f%% region: %dx%d px" % (CF * 100, p.shape[1], p.shape[0]))

    for ci, cn in ((1, "G"), (0, "R"), (2, "B")):
        pp = p[:, :, ci].ravel()
        ll = l[:, :, ci].ravel()
        m = pp > 1e-6
        pp, ll = pp[m], ll[m]
        lo, hi = np.percentile(pp, 0.2), np.percentile(pp, 99.8)
        edges = np.exp(np.linspace(np.log(max(lo, 1e-6)), np.log(hi), 25))
        print("\n%s  n=%d   P range %.5g .. %.5g" % (cn, len(pp), lo, hi))
        print("      P_mid        med L        L/P      dL/dP(local)")
        prev = None
        for i in range(len(edges) - 1):
            mm = (pp >= edges[i]) & (pp < edges[i + 1])
            if mm.sum() < 200:
                continue
            pm = float(np.median(pp[mm])); lm = float(np.median(ll[mm]))
            slope = ""
            if prev is not None and pm > prev[0]:
                slope = "%8.4f" % ((lm - prev[1]) / (pm - prev[0]))
            print("  %11.6g  %11.6g  %8.4f  %s" % (pm, lm, lm / pm, slope))
            prev = (pm, lm)
        if ci != 1:
            continue
        # affine fit on the upper half only -> extrapolate the implied intercept
        hi_m = pp > np.percentile(pp, 60)
        A = np.stack([pp[hi_m], np.ones(hi_m.sum())], 1)
        b, *_ = np.linalg.lstsq(A, ll[hi_m], rcond=None)
        print("  upper-40%% affine: L = %.6f*P %+.6f   -> x-intercept P0=%+.6f"
              % (b[0], b[1], -b[1] / b[0]))


if __name__ == "__main__":
    main()
