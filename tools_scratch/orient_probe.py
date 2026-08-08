#!/usr/bin/env python3
"""Is the tele candidate the right map in the wrong orientation, or the wrong map?

The controlled scorer reports only the BEST flip per statistic, and on
campaign/u2_70mm_a two different statistics picked two different flips
(pearson_raw -> flipud, within4 -> rot180).  That is either a real orientation
bug or two flips both beating a candidate that agrees with nothing; the two
look identical in a best-of summary and different in a full table, so print the
full table.

Also prints each orientation's best CONSTANT index offset and the within-4 it
reaches there, because a map that is spatially right but shifted along the
ladder is a different defect from a map that is spatially wrong, and within-4
alone cannot tell them apart.
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


def pearson(a, b):
    a = a.ravel() - a.mean()
    b = b.ravel() - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return 0.0 if d == 0 else float((a * b).sum() / d)


def main(argv):
    ref_dir, cand_npy, phoenix = argv[1], argv[2], argv[3]
    sys.path.insert(0, os.path.join(phoenix, "tools", "parity"))
    import score_depth_controlled as S

    d_full, _ = S.measure_d_full(ref_dir)
    truth = np.fromfile(os.path.join(ref_dir, "index5_hypothesis_index.u16le"),
                        dtype="<u2").astype(np.float64).reshape(REF_H, REF_W)
    ours = S.depth_to_index(np.load(cand_npy).astype(np.float64), d_full)
    t = area_resample(truth, *ours.shape)
    print(f"D_full={d_full}  grid={ours.shape[0]}x{ours.shape[1]}")

    orients = {
        "identity": ours,
        "fliplr": np.fliplr(ours),
        "flipud": np.flipud(ours),
        "rot180": ours[::-1, ::-1],
        "transpose-ish (rot90 resized)": None,
    }
    print(f"\n{'orientation':<16} {'pearson':>9} {'within4':>9} {'within16':>9} "
          f"{'medoff':>7} {'w4@off':>8} {'w16@off':>8}")
    for k, v in orients.items():
        if v is None:
            continue
        d = t - v
        med = float(np.median(d))
        row = (pearson(t, v),
               float(np.mean(np.abs(d) <= 4) * 100),
               float(np.mean(np.abs(d) <= 16) * 100),
               med,
               float(np.mean(np.abs(d - med) <= 4) * 100),
               float(np.mean(np.abs(d - med) <= 16) * 100))
        print(f"{k:<16} {row[0]:9.4f} {row[1]:9.2f} {row[2]:9.2f} "
              f"{row[3]:7.1f} {row[4]:8.2f} {row[5]:8.2f}")

    # Pearson is not robust, and 1.43% of our cells sit at index 40..340 on a
    # ladder whose truth stops at 40.  Those cells carry sd(ours)=33.9 against
    # sd(ours|bulk)=4.35, so they set the covariance denominator for EVERY
    # orientation.  Re-run the table with them excluded -- if the winning
    # orientation changes, the flip control was scoring the outliers, not the
    # orientation.
    bulk = ours < 40
    print(f"\nsame table over the {bulk.mean() * 100:.2f}% of cells with ours<40 "
          f"(mask fixed from the identity map, so every row scores the same cells):")
    print(f"{'orientation':<16} {'pearson':>9} {'within4':>9} {'within16':>9} {'medoff':>7} {'w4@off':>8}")
    for k, v in orients.items():
        if v is None:
            continue
        tb, vb = t[bulk], v[bulk]
        d = tb - vb
        med = float(np.median(d))
        print(f"{k:<16} {pearson(tb, vb):9.4f} {np.mean(np.abs(d) <= 4) * 100:9.2f} "
              f"{np.mean(np.abs(d) <= 16) * 100:9.2f} {med:7.1f} "
              f"{np.mean(np.abs(d - med) <= 4) * 100:8.2f}")

    # A vertically mirrored SCENE and a vertically mirrored MAP are
    # indistinguishable unless the reference itself is asymmetric.  Measure the
    # reference's own self-similarity under each flip: if truth already matches
    # its own flipud well, "flipud wins" says nothing about my pipeline.
    print(f"\nreference self-similarity (how much a flip even changes the truth):")
    for k, v in (("fliplr", np.fliplr(t)), ("flipud", np.flipud(t)),
                 ("rot180", t[::-1, ::-1])):
        print(f"  truth vs {k:<8} pearson {pearson(t, v):7.4f}  "
              f"within4 {np.mean(np.abs(t - v) <= 4) * 100:6.2f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
