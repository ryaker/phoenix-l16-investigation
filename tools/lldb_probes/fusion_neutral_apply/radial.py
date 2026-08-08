#!/usr/bin/env python3
"""Radial profile of the Lumen/Phoenix ratio after FOV alignment.

Distinguishes a GLOBAL gain error (ratio flat vs radius) from a SHADING error
(ratio varies with radius).  Reuses align.py's centre-zoom search on the green
plane, then box-grids all three channels onto a common grid and reports the
median lumen/phoenix ratio in normalised-radius rings.

Usage: radial.py <phoenix_tag> [shot ...]      reads /tmp/<shot>_<tag>.hdr
"""
import numpy as np, re, os, sys

OUT = "/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/runs/verify_master"
NAMES = ["u1_28", "u1_35", "u1_70", "u1_150", "u2_35"]
G = 192
GH = G * 3 // 4


def load(path):
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


def grid3(img, gw, gh):
    return np.dstack([boxgrid(img[:, :, c], gw, gh) for c in range(3)])


def ncc(a, b):
    a = a - a.mean(); b = b - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d > 0 else 0.0


def crop_center(a, z):
    H, W = a.shape[:2]
    h, w = int(round(H * z)), int(round(W * z))
    y0, x0 = (H - h) // 2, (W - w) // 2
    return a[y0:y0 + h, x0:x0 + w]


tag = sys.argv[1] if len(sys.argv) > 1 else None
shots = sys.argv[2:] or NAMES
yy, xx = np.mgrid[0:GH, 0:G]
rad = np.sqrt(((yy + 0.5) / GH - 0.5) ** 2 + ((xx + 0.5) / G - 0.5) ** 2) / 0.5
EDGES = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0, 1.42]

for n in (shots if tag else []):
    pp, lp = f"/tmp/{n}_{tag}.hdr", f"{OUT}/{n}_lumen.hdr"
    if not (os.path.exists(pp) and os.path.exists(lp)):
        print("%-9s [missing]" % n); continue
    L, P = load(lp), load(pp)
    Pg = np.log1p(np.maximum(boxgrid(P[:, :, 1], G, GH), 0) * 1e3)
    best = None
    for z in np.arange(0.30, 1.61, 0.01):
        if z <= 1.0:
            c = ncc(np.log1p(np.maximum(boxgrid(crop_center(L, z)[:, :, 1], G, GH), 0) * 1e3), Pg)
            key = (z, c, True)
        else:
            a = np.log1p(np.maximum(boxgrid(crop_center(P, 1.0 / z)[:, :, 1], G, GH), 0) * 1e3)
            c = ncc(np.log1p(np.maximum(boxgrid(L[:, :, 1], G, GH), 0) * 1e3), a)
            key = (z, c, False)
        if best is None or c > best[1]:
            best = key
    z = best[0]
    if z <= 1.0:
        Lb, Pb = grid3(crop_center(L, z), G, GH), grid3(P, G, GH)
    else:
        Lb, Pb = grid3(L, G, GH), grid3(crop_center(P, 1.0 / z), G, GH)
    print("%s  zoom=%.2f ncc=%.4f" % (n, z, best[1]))
    print("  ring        n      R        G        B     (median lumen/phoenix)")
    for a, b in zip(EDGES[:-1], EDGES[1:]):
        m = (rad >= a) & (rad < b) & (Lb[:, :, 1] > 1e-5) & (Pb[:, :, 1] > 1e-5)
        if m.sum() < 8:
            continue
        r = [float(np.median(Lb[:, :, c][m] / Pb[:, :, c][m])) for c in range(3)]
        print("  %.1f-%.1f  %5d   %.4f   %.4f   %.4f" % (a, b, m.sum(), r[0], r[1], r[2]))
