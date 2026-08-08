#!/usr/bin/env python3
"""Merge isolation: score {n}_base.hdr (no crop, no merge) AND {n}_phx.hdr
(full pipeline) against {n}_lumen.hdr on a common aligned grid.

If the base gain is ~1.0 while the merged gain is 0.70-1.37, the merge is the
sole source of the per-shot achromatic scale.  If the base already carries the
gain, the divergence is upstream (plane prep / MonoFusion / square).
"""
import numpy as np, re, os, json

OUT = "/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/runs/verify_master"
G = 192
GH = int(G * 3 / 4)


def load_rgb(path):
    with open(path, "rb") as f:
        d = f.read()
    i = d.find(b"\n\n"); j = d.index(b"\n", i + 2)
    m = re.match(r"-Y (\d+) \+X (\d+)", d[i + 2:j].decode().strip())
    H, W = int(m.group(1)), int(m.group(2))
    px = np.frombuffer(d, dtype=np.uint8, count=W * H * 4, offset=j + 1).reshape(H, W, 4)
    e = px[..., 3].astype(np.int32)
    s = np.where(e > 0, np.ldexp(1.0, e - 136), 0.0).astype(np.float32)
    return px[..., :3].astype(np.float32) * s[..., None]


def boxgrid(a, gw, gh):
    H, W = a.shape
    ys = np.arange(gh + 1) * H // gh
    xs = np.arange(gw + 1) * W // gw
    out = np.empty((gh, gw), np.float64)
    for r in range(gh):
        band = a[ys[r]:ys[r + 1]]
        out[r] = np.add.reduceat(band, xs[:-1], axis=1).sum(0) / (np.diff(xs) * band.shape[0])
    return out


def ncc(a, b):
    a = a - a.mean(); b = b - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d > 0 else 0.0


def crop_center(a, z):
    H, W = a.shape[:2]
    h, w = int(round(H * z)), int(round(W * z))
    y0, x0 = (H - h) // 2, (W - w) // 2
    return a[y0:y0 + h, x0:x0 + w]


def lg(a):
    return np.log1p(np.maximum(boxgrid(a, G, GH), 0) * 1e3)


def score(Lrgb, Prgb):
    Lg_, Pg_ = Lrgb[..., 1], Prgb[..., 1]
    best = None
    Pgrid = lg(Pg_)
    Lgrid = lg(Lg_)
    for z in np.arange(0.30, 3.01, 0.01):
        if z <= 1.0:
            c = ncc(lg(crop_center(Lg_, z)), Pgrid)
        else:
            c = ncc(Lgrid, lg(crop_center(Pg_, 1.0 / z)))
        if best is None or c > best[1]:
            best = (float(z), float(c))
    z = best[0]
    if z <= 1.0:
        La, Pa = crop_center(Lrgb, z), Prgb
    else:
        La, Pa = Lrgb, crop_center(Prgb, 1.0 / z)
    gains = []
    means = []
    for c in range(3):
        Lb = boxgrid(La[..., c], G, GH); Pb = boxgrid(Pa[..., c], G, GH)
        m = (Lb > 1e-5) & (Pb > 1e-5)
        gains.append(float(np.median(Pb[m] / Lb[m])) if m.any() else float("nan"))
        means.append((float(Lb.mean()), float(Pb.mean())))
    return dict(best_zoom=best[0], best_ncc=best[1],
                gain_r=gains[0], gain_g=gains[1], gain_b=gains[2],
                lumen_mean_g=means[1][0], phx_mean_g=means[1][1],
                lumen_mean_r=means[0][0], phx_mean_r=means[0][1],
                lumen_mean_b=means[2][0], phx_mean_b=means[2][1])


NAMES = ["u1_28", "u1_35", "u1_70", "u1_150", "u2_35"]
res = {}
for n in NAMES:
    lp = f"{OUT}/{n}_lumen.hdr"
    if not os.path.exists(lp):
        continue
    L = load_rgb(lp)
    row = {}
    for tag, suf in (("base", "_base.hdr"), ("full", "_phx.hdr")):
        pp = f"{OUT}/{n}{suf}"
        if not os.path.exists(pp) or os.path.getsize(pp) == 0:
            continue
        P = load_rgb(pp)
        row[tag] = score(L, P)
        row[tag]["shape"] = list(P.shape[:2])
        s = row[tag]
        print("%-8s %-5s  %dx%d  z=%.2f ncc=%.4f  gain R/G/B = %.4f %.4f %.4f"
              "   meanG lumen=%.6f phx=%.6f"
              % (n, tag, P.shape[1], P.shape[0], s["best_zoom"], s["best_ncc"],
                 s["gain_r"], s["gain_g"], s["gain_b"],
                 s["lumen_mean_g"], s["phx_mean_g"]))
    res[n] = row

json.dump(res, open(f"{OUT}/basecmp.json", "w"), indent=1)
print(f"\nwrote {OUT}/basecmp.json")
