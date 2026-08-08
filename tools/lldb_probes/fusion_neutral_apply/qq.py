#!/usr/bin/env python3
"""Alignment-free quantile-quantile diagnostic: lumen = a*phoenix + b.

Resolutions differ between Phoenix renders and the Lumen masters, so a
per-pixel diff is not available.  The luma *quantile* curve is, and it
separates the two failure modes cleanly:

    pure gain error      -> a != 1, b ~ 0
    pure pedestal error  -> a ~ 1,  b != 0

Usage: qq.py <tag> [shot ...]
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
    return a[:, :, :3] * s[:, :, None]


def luma(path):
    img = load(path)
    y = WR * img[:, :, 0] + WG * img[:, :, 1] + WB * img[:, :, 2]
    g = img[:, :, 1]
    return y[g > 1e-6].ravel()


tag = sys.argv[1]
shots = sys.argv[2:] or NAMES
Q = np.arange(1.0, 100.0, 1.0)
print("shot      slope a   intercept b   b/median_L   fit rms    "
      "P[q05,q50,q95]              L[q05,q50,q95]")
for n in shots:
    pp, lp = f"/tmp/{n}_{tag}.hdr", f"{OUT}/{n}_lumen.hdr"
    if not (os.path.exists(pp) and os.path.exists(lp)):
        print("%-9s [missing]" % n)
        continue
    P = np.percentile(luma(pp), Q)
    L = np.percentile(luma(lp), Q)
    a, b = np.polyfit(P, L, 1)
    rms = float(np.sqrt(np.mean((a * P + b - L) ** 2)))
    med = float(np.median(L))
    print("%-9s %8.5f  %+11.6f  %+9.4f%%  %.6f   "
          "[%.4f %.4f %.4f]  [%.4f %.4f %.4f]"
          % (n, a, b, 100.0 * b / med, rms,
             P[4], P[49], P[94], L[4], L[49], L[94]))
