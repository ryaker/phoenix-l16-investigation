#!/usr/bin/env python3
"""Is the tele residual a constant index shift, a gain, or neither?

Removing a single constant from our index map lifts within-4 from 28% to 62%,
so most of the tele residual is one number.  Which number it is decides where
the bug lives: a flat offset across the ladder is an ORIGIN error (the band's
base, or an off-by-N in the lookup), while an offset that grows with index is a
GAIN error (the ladder step, i.e. D_full or the near/far bound pair), and those
two live in different code.

Prints the offset binned by Lumen's own index, and a least-squares fit of
ours = a*truth + b, so the two are distinguishable rather than assumed.
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
    ref_dir, cand_npy, phoenix = argv[1], argv[2], argv[3]
    sys.path.insert(0, os.path.join(phoenix, "tools", "parity"))
    import score_depth_controlled as S

    d_full, _ = S.measure_d_full(ref_dir)
    truth = np.fromfile(os.path.join(ref_dir, "index5_hypothesis_index.u16le"),
                        dtype="<u2").astype(np.float64).reshape(REF_H, REF_W)
    ours = S.depth_to_index(np.load(cand_npy).astype(np.float64), d_full)
    t = area_resample(truth, *ours.shape)

    print(f"{'truth bin':>12} {'n':>8} {'ours med':>9} {'offset med':>11} {'offset p25':>11} {'offset p75':>11}")
    edges = [0, 4, 6, 8, 10, 12, 15, 18, 22, 26, 30, 34, 40, 1464]
    for a, b in zip(edges[:-1], edges[1:]):
        m = (t >= a) & (t < b)
        n = int(m.sum())
        if n < 200:
            continue
        d = ours[m] - t[m]
        print(f"{a:5d}..{b:<5d} {n:8d} {np.median(ours[m]):9.2f} "
              f"{np.median(d):11.2f} {np.percentile(d,25):11.2f} {np.percentile(d,75):11.2f}")

    # ours = a*truth + b, on the bulk only (drop our >100 tail so a handful of
    # blown-out cells cannot set the slope).
    m = ours < 100
    A = np.vstack([t[m].ravel(), np.ones(m.sum())]).T
    coef, *_ = np.linalg.lstsq(A, ours[m].ravel(), rcond=None)
    print(f"\nleast squares over {m.sum()} cells with ours<100:  "
          f"ours = {coef[0]:.4f} * truth + {coef[1]:.3f}")
    resid = ours[m].ravel() - A @ coef
    print(f"  residual sd {resid.std():.2f};  a pure offset would give a=1.000")

    # What does the best single constant buy, and what does the best affine buy?
    d = t - ours
    med = np.median(d)
    print(f"\nbest constant shift {med:+.2f}:  within4 "
          f"{np.mean(np.abs(d - med) <= 4) * 100:.2f}%")
    # Undo the fit on OURS and compare to truth.  (Applying the fit to truth and
    # then inverting it is comparing truth to itself; that printed 100.00% here
    # and it measured nothing.)
    unfit = (ours - coef[1]) / coef[0]
    print(f"un-gained (ours-{coef[1]:.3f})/{coef[0]:.4f}:  within4 "
          f"{np.mean(np.abs(t - unfit) <= 4) * 100:.2f}%  "
          f"within16 {np.mean(np.abs(t - unfit) <= 16) * 100:.2f}%")

    # How much of the reported score is a few blown-out cells?  sd(ours) over the
    # whole map is 33.9 while the fit residual is a few index units, which can
    # only be true if a small tail is carrying the spread -- and pearson is a
    # ratio of exactly those two quantities.
    def pear(x, y):
        x = x.ravel() - x.mean(); y = y.ravel() - y.mean()
        dd = np.sqrt((x * x).sum() * (y * y).sum())
        return 0.0 if dd == 0 else float((x * y).sum() / dd)
    print(f"\ncells: total {ours.size}, ours>100 {int((ours > 100).sum())} "
          f"({(ours > 100).mean() * 100:.2f}%), ours>40 {int((ours > 40).sum())} "
          f"({(ours > 40).mean() * 100:.2f}%)")
    print(f"  sd(ours) all {ours.std():.2f}   sd(ours) where ours<100 {ours[m].std():.2f}"
          f"   sd(truth) {t.std():.2f}")
    print(f"  pearson all cells {pear(t, ours):.4f}   "
          f"pearson where ours<100 {pear(t[m], ours[m]):.4f}")
    for cap in (40, 60, 100):
        mm = ours < cap
        print(f"  pearson where ours<{cap:<4d} {pear(t[mm], ours[mm]):7.4f}  "
              f"on {mm.mean() * 100:5.2f}% of cells")

    # Is the shift spatially uniform?  A shift that varies across the frame is a
    # geometry error wearing an offset's clothes.
    print("\nper-quadrant median offset (ours - truth):")
    H, W = ours.shape
    for name, sl in (("top-left", (slice(0, H // 2), slice(0, W // 2))),
                     ("top-right", (slice(0, H // 2), slice(W // 2, W))),
                     ("bot-left", (slice(H // 2, H), slice(0, W // 2))),
                     ("bot-right", (slice(H // 2, H), slice(W // 2, W)))):
        print(f"  {name:<10} {np.median(ours[sl] - t[sl]):+7.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
