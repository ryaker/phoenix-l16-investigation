#!/usr/bin/env python3
"""A statistic with no threshold in it, to settle the tele orientation question.

Masking "outliers" at index 40 works but buys the answer with a knob, and a
knob chosen after seeing the result is how a score stops being evidence.
Spearman needs no knob: it is a Pearson correlation of RANKS, so a cell at
index 340 counts exactly as much as a cell at index 41 (one rank step), and a
monotone gain compression -- which is what the tele map has, ours = 0.347*truth
+ 13.4 -- leaves it untouched.

If identity wins on Spearman with no mask, the FAILS-CONTROL verdict on
pearson_raw was the 1.43% tail, not the map.
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
    a = a.ravel() - a.mean(); b = b.ravel() - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return 0.0 if d == 0 else float((a * b).sum() / d)


def rankdata(a):
    """Average ranks, ties shared.  These maps are heavily tied (40 distinct
    truth values over 202800 cells), so ordinal ranking would invent an
    ordering inside each tie group and inflate the correlation."""
    f = a.ravel()
    order = np.argsort(f, kind="stable")
    s = f[order]
    r = np.empty(f.size, dtype=np.float64)
    i = 0
    while i < s.size:
        j = i
        while j + 1 < s.size and s[j + 1] == s[i]:
            j += 1
        r[order[i:j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    return r


def spearman(a, b):
    return pearson(rankdata(a), rankdata(b))


def main(argv):
    phoenix = argv[-1]
    sys.path.insert(0, os.path.join(phoenix, "tools", "parity"))
    import score_depth_controlled as S

    rng = np.random.default_rng(20260806)
    for ref_dir, cand_npy in zip(argv[1:-1:2], argv[2:-1:2]):
        d_full, _ = S.measure_d_full(ref_dir)
        truth = np.fromfile(os.path.join(ref_dir, "index5_hypothesis_index.u16le"),
                            dtype="<u2").astype(np.float64).reshape(REF_H, REF_W)
        ours = S.depth_to_index(np.load(cand_npy).astype(np.float64), d_full)
        t = area_resample(truth, *ours.shape)
        print(f"\n=== {os.path.basename(ref_dir)}  D_full={d_full}")
        print(f"  truth max index {t.max():.1f}; ours over that "
              f"{int((ours > t.max()).sum())} cells ({(ours > t.max()).mean() * 100:.2f}%), "
              f"ours max {ours.max():.1f}")
        base = spearman(t, ours)
        print(f"{'orientation':<12} {'spearman':>9} {'vs identity':>12}")
        for k, v in (("identity", ours), ("fliplr", np.fliplr(ours)),
                     ("flipud", np.flipud(ours)), ("rot180", ours[::-1, ::-1])):
            s = spearman(t, v)
            print(f"{k:<12} {s:9.4f} {(s / base if base else 0):11.0%}")
        # The flip control assumes a correct map LOSES correlation when mirrored.
        # That assumption is a property of the SCENE, not of the candidate: a
        # scene whose depth barely varies along one axis is nearly its own
        # mirror, and then high flip retention is the scene's symmetry showing
        # through, not the candidate being upside down.  Measure the reference
        # against its own flips so the retention has something to be compared to.
        print(f"{'':<12} {'truth vs flip(truth)':>21}  <- what the flip costs the TRUTH")
        for k, v in (("fliplr", np.fliplr(t)), ("flipud", np.flipud(t)),
                     ("rot180", t[::-1, ::-1])):
            print(f"{k:<12} {spearman(t, v):21.4f}")
        nulls = [spearman(t, rng.permutation(ours.ravel()).reshape(ours.shape))
                 for _ in range(9)]
        nm, ns = float(np.mean(nulls)), float(np.std(nulls))
        z = (base - nm) / ns if ns > 0 else float("inf")
        print(f"  shuffled null mean {nm:+.4f} sd {ns:.4f} -> identity z = {z:.1f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
