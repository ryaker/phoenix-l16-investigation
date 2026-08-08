#!/usr/bin/env python3
"""Do the Lumen and Phoenix masters actually show the SAME field of view?

The per-shot achromatic gain (phx/lumen = 0.73 wide, 1.47 @70mm, 1.08 @150mm)
could be a real normalisation difference OR an artefact of comparing different
crops.  Lumen always writes 10432x7824; Phoenix's canvas and crop are tier- and
focal-dependent.  This box-downsamples both to a common grid, then searches over
a zoom factor z (phoenix FOV = z x lumen FOV, about the centre) for the zoom that
maximises normalised cross-correlation of log-luminance.  z ~ 1.0 => same FOV and
the gain is real.  z != 1 => the gain measurement was contaminated by framing.
"""
import numpy as np, re, os, json

OUT = "/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/runs/verify_master"
G = 192


def load(path):
    with open(path, "rb") as f:
        d = f.read()
    i = d.find(b"\n\n"); j = d.index(b"\n", i + 2)
    m = re.match(r"-Y (\d+) \+X (\d+)", d[i + 2:j].decode().strip())
    H, W = int(m.group(1)), int(m.group(2))
    px = np.frombuffer(d, dtype=np.uint8, count=W * H * 4, offset=j + 1).reshape(H, W, 4)
    e = px[..., 3].astype(np.int32)
    s = np.where(e > 0, np.ldexp(1.0, e - 136), 0.0)
    return px[..., 1].astype(np.float32) * s.astype(np.float32)   # green plane


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
    """Central sub-window covering a fraction z of each axis."""
    H, W = a.shape
    h, w = int(round(H * z)), int(round(W * z))
    y0, x0 = (H - h) // 2, (W - w) // 2
    return a[y0:y0 + h, x0:x0 + w]


NAMES = ["u1_28", "u1_35", "u1_70", "u1_150", "u2_35"]
res = {}
for n in NAMES:
    lp, pp = f"{OUT}/{n}_lumen.hdr", f"{OUT}/{n}_phx.hdr"
    if not (os.path.exists(lp) and os.path.exists(pp)):
        continue
    Lf, Pf = load(lp), load(pp)
    Pg = np.log1p(np.maximum(boxgrid(Pf, G, int(G * 3 / 4)), 0) * 1e3)
    best = None
    for z in np.arange(0.30, 1.61, 0.01):
        if z <= 1.0:
            sub = crop_center(Lf, z)
            Lg = np.log1p(np.maximum(boxgrid(sub, G, int(G * 3 / 4)), 0) * 1e3)
            c = ncc(Lg, Pg)
        else:
            sub = crop_center(Pf, 1.0 / z)
            Pg2 = np.log1p(np.maximum(boxgrid(sub, G, int(G * 3 / 4)), 0) * 1e3)
            Lg = np.log1p(np.maximum(boxgrid(Lf, G, int(G * 3 / 4)), 0) * 1e3)
            c = ncc(Lg, Pg2)
        if best is None or c > best[1]:
            best = (float(z), float(c))
    # NCC at z = 1 for reference
    Lg1 = np.log1p(np.maximum(boxgrid(Lf, G, int(G * 3 / 4)), 0) * 1e3)
    c1 = ncc(Lg1, Pg)
    # gain measured on the BEST-aligned pair
    z = best[0]
    if z <= 1.0:
        Lb = boxgrid(crop_center(Lf, z), G, int(G * 3 / 4)); Pb = boxgrid(Pf, G, int(G * 3 / 4))
    else:
        Lb = boxgrid(Lf, G, int(G * 3 / 4)); Pb = boxgrid(crop_center(Pf, 1.0 / z), G, int(G * 3 / 4))
    m = (Lb > 1e-5) & (Pb > 1e-5)
    gain = float(np.median(Pb[m] / Lb[m]))
    res[n] = dict(best_zoom=best[0], best_ncc=best[1], ncc_at_1=c1, gain_aligned=gain)
    print("%-8s  best zoom=%.2f ncc=%.4f   ncc@z=1.00 %.4f   aligned median gain=%.4f"
          % (n, best[0], best[1], c1, gain))

json.dump(res, open(f"{OUT}/align.json", "w"), indent=1)
print(f"\nwrote {OUT}/align.json")
