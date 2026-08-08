#!/usr/bin/env python3
"""Ohta-luma achromatic ratio (lumen / phoenix) for the 5-shot corpus.

Usage: achro.py <tag>      where phoenix renders live at /tmp/{name}_{tag}.hdr
and the Lumen masters at runs/verify_master/{name}_lumen.hdr.

Same decode as hdrmean.py (flat RGBE, exponent bias 136).
"""
import numpy as np, os, sys

OUT = "/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/runs/verify_master"
WR, WG, WB = 0.2155500054359436, 0.43230700492858887, 0.35214298963546753
NAMES = ["u1_28", "u1_35", "u1_70", "u1_150", "u2_35"]


def load(path):
    with open(path, "rb") as f:
        raw = f.read()
    i = raw.find(b"\n\n")
    j = raw.index(b"\n", i + 2)
    d = raw[i + 2:j].split()
    H = int(d[1]); W = int(d[3])
    a = np.frombuffer(raw, dtype=np.uint8, count=W * H * 4,
                      offset=j + 1).reshape(H, W, 4).astype(np.float32)
    s = np.ldexp(1.0, a[:, :, 3].astype(np.int32) - 136)
    return a[:, :, :3] * s[:, :, None], W, H


def means(path):
    img, W, H = load(path)
    g = img[:, :, 1]
    nz = g > 1e-6
    return (float(img[:, :, 0][nz].mean()), float(g[nz].mean()),
            float(img[:, :, 2][nz].mean()), W, H)


tag = sys.argv[1] if len(sys.argv) > 1 else "wfix"
print("shot     %-24s %-24s  achro(lumen/phx)" % ("phoenix R/G/B", "lumen R/G/B"))
for n in NAMES:
    pp = sys.argv[2] if len(sys.argv) > 2 and len(NAMES) == 1 else f"/tmp/{n}_{tag}.hdr"
    lp = f"{OUT}/{n}_lumen.hdr"
    if not (os.path.exists(pp) and os.path.exists(lp)):
        print("%-8s [missing %s]" % (n, pp if not os.path.exists(pp) else lp))
        continue
    pr, pg, pb, pw, ph = means(pp)
    lr, lg, lb, lw, lh = means(lp)
    yp = WR * pr + WG * pg + WB * pb
    yl = WR * lr + WG * lg + WB * lb
    print("%-8s %.6f %.6f %.6f   %.6f %.6f %.6f   %.4f   "
          "(R %.4f G %.4f B %.4f)  %dx%d vs %dx%d"
          % (n, pr, pg, pb, lr, lg, lb, yl / yp,
             lr / pr, lg / pg, lb / pb, pw, ph, lw, lh))
