#!/usr/bin/env python3
"""What slice of the hypothesis ladder does each side actually occupy?

For every capture that has both a reference and a candidate, prints where
Lumen's indices live and where mine live, on the SAME ladder.  A per-pixel band
that is placed correctly but on the wrong PART of the ladder is invisible to a
correlation score and fatal to a within-4 score, so the two distributions have
to be looked at side by side rather than summarised into one agreement number.
"""
import sys, os, glob
import numpy as np

REF_W, REF_H = 2080, 1560
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))


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


def q(a):
    return (float(a.min()), float(np.percentile(a, 5)), float(np.percentile(a, 50)),
            float(np.percentile(a, 95)), float(a.max()))


def main(argv):
    root = argv[1]
    runs = os.path.join(root, "runs")
    sys.path.insert(0, os.path.join(argv[2], "tools", "parity"))
    import score_depth_controlled as S

    names = S.discover_captures(runs)
    print(f"{'capture':<28} {'D_full':>7} | {'LUMEN min/p5/p50/p95/max':^34} | "
          f"{'OURS min/p5/p50/p95/max':^34}")
    for name in names:
        ref_dir = os.path.join(runs, "reference_stage_maps", name)
        cand = S.find_candidate(runs, name)
        if not cand:
            continue
        try:
            d_full, _spread = S.measure_d_full(ref_dir)
        except Exception as e:
            print(f"{name:<28} D_FULL UNMEASURABLE ({e})")
            continue
        truth = np.fromfile(os.path.join(ref_dir, "index5_hypothesis_index.u16le"),
                            dtype="<u2").astype(np.float64).reshape(REF_H, REF_W)
        ours = S.depth_to_index(np.load(cand[0]).astype(np.float64), d_full)
        if ours.shape != (390, 520):
            print(f"{name:<28} WRONG-RECIPE {ours.shape}")
            continue
        t = area_resample(truth, *ours.shape)
        lt, ot = q(t), q(ours)
        print(f"{name:<28} {d_full:>7} | " +
              "/".join(f"{v:6.1f}" for v in lt) + " | " +
              "/".join(f"{v:6.1f}" for v in ot))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
