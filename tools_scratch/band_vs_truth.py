#!/usr/bin/env python3
"""Where does Lumen's index actually live, and can my per-pixel band reach it?

Measures, per pyramid level, three numbers over the SAME pixels:
  - the fraction of Lumen's downsampled truth indices that fall INSIDE my band
  - the fraction that fall ABOVE my band's upper edge
  - the fraction that fall BELOW my band's lower edge
A level whose band cannot contain the truth cannot produce the truth, no matter
how faithful the cost volume and SGM downstream of it are.

Resampling is the scorer's exact `area_resample` so a number here is comparable
to a number there; using a different resampler would make the two disagree for
a reason that has nothing to do with the engine.
"""
import sys, os
import numpy as np

REF_W, REF_H = 2080, 1560


def area_resample(a, oh, ow):
    H, W = a.shape
    ye, xe = np.linspace(0, H, oh + 1), np.linspace(0, W, ow + 1)
    c = np.zeros((H + 1, W + 1))
    c[1:, 1:] = a.cumsum(0).cumsum(1)
    i0 = np.floor(ye).astype(int)
    f = ye - i0
    i0, i1 = np.clip(i0, 0, H), np.clip(i0 + 1, 0, H)
    R = c[i0] * (1 - f)[:, None] + c[i1] * f[:, None]
    j0 = np.floor(xe).astype(int)
    g = xe - j0
    j0, j1 = np.clip(j0, 0, W), np.clip(j0 + 1, 0, W)
    S = R[:, j0] * (1 - g)[None, :] + R[:, j1] * g[None, :]
    box = S[1:, 1:] - S[:-1, 1:] - S[1:, :-1] + S[:-1, :-1]
    return box / (np.diff(ye)[:, None] * np.diff(xe)[None, :])


def main(argv):
    if len(argv) < 3:
        print("usage: band_vs_truth.py <reference_dir> <bandprefix>")
        return 2
    ref_dir, prefix = argv[1], argv[2]
    p = os.path.join(ref_dir, "index5_hypothesis_index.u16le")
    truth = np.fromfile(p, dtype="<u2").astype(np.float64).reshape(REF_H, REF_W)
    print(f"truth {os.path.basename(ref_dir)}: min={truth.min():.0f} max={truth.max():.0f} "
          f"p5={np.percentile(truth,5):.0f} p50={np.percentile(truth,50):.0f} "
          f"p95={np.percentile(truth,95):.0f} distinct={len(np.unique(truth))}")

    d = os.path.dirname(prefix) or "."
    stem = os.path.basename(prefix)
    files = sorted(f for f in os.listdir(d) if f.startswith(stem + "_lvl"))
    if not files:
        print(f"NO BAND DUMPS matching {prefix}_lvl*  -- run with PHX_DUMPBAND set")
        return 2

    print(f"\n{'level':>5} {'grid':>12} {'lower med':>10} {'upper med':>10} "
          f"{'upper max':>10} {'inside%':>9} {'above%':>9} {'below%':>9}")
    for f in files:
        tail = f[len(stem) + 4:].rsplit(".", 1)[0]
        lvl, dims = tail.split("_", 1)
        W, H = (int(v) for v in dims.split("x"))
        pairs = np.fromfile(os.path.join(d, f), dtype="<u2").reshape(H, W, 2)
        lo = pairs[:, :, 0].astype(np.float64)
        hi = pairs[:, :, 1].astype(np.float64)
        t = area_resample(truth, H, W)
        inside = np.mean((t >= lo) & (t <= hi)) * 100.0
        above = np.mean(t > hi) * 100.0
        below = np.mean(t < lo) * 100.0
        print(f"{lvl:>5} {W:>5}x{H:<6} {np.median(lo):10.1f} {np.median(hi):10.1f} "
              f"{hi.max():10.0f} {inside:9.2f} {above:9.2f} {below:9.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
