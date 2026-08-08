#!/usr/bin/env python3
"""Spatially-aligned Lumen-vs-Phoenix master comparison.

Both masters are 4:3, so box-downsample each to a common 128x96 grid and
compare per-tile.  Distinguishes a GLOBAL chroma error (flat ratio map) from a
SPATIAL one (vignetting / color-shading, radially varying ratio map).
"""
import numpy as np, sys, re, os, json

OUT = "/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/runs/verify_master"
GW, GH = 128, 96


def load(path):
    with open(path, "rb") as f:
        data = f.read()
    i = data.find(b"\n\n")
    j = data.index(b"\n", i + 2)
    m = re.match(r"-Y (\d+) \+X (\d+)", data[i + 2:j].decode().strip())
    H, W = int(m.group(1)), int(m.group(2))
    px = np.frombuffer(data, dtype=np.uint8, count=W * H * 4, offset=j + 1).reshape(H, W, 4)
    e = px[..., 3].astype(np.int32)
    s = np.where(e > 0, np.ldexp(1.0, e - 136), 0.0)
    return px[..., :3].astype(np.float32) * s[..., None].astype(np.float32)


def grid(rgb):
    H, W, _ = rgb.shape
    ys = (np.arange(GH + 1) * H // GH)
    xs = (np.arange(GW + 1) * W // GW)
    out = np.zeros((GH, GW, 3), np.float64)
    for a in range(GH):
        band = rgb[ys[a]:ys[a + 1]]
        cs = np.add.reduceat(band, xs[:-1], axis=1)
        cnt = np.diff(xs)[None, :, None] * band.shape[0]
        out[a] = cs.sum(0) / cnt[0]
    return out


NAMES = ["u1_28", "u1_35", "u1_70", "u1_150", "u2_35"]
res = {}
for n in NAMES:
    lp, pp = f"{OUT}/{n}_lumen.hdr", f"{OUT}/{n}_phx.hdr"
    if not (os.path.exists(lp) and os.path.exists(pp)):
        continue
    L, P = grid(load(lp)), grid(load(pp))
    m = (L[..., 1] > 1e-5) & (P[..., 1] > 1e-5)
    # per-tile channel ratio phoenix/lumen
    r = np.where(m[..., None] & (L > 1e-6), P / np.maximum(L, 1e-12), np.nan)
    # spatial radius
    yy, xx = np.mgrid[0:GH, 0:GW]
    rad = np.sqrt(((yy - GH / 2) / (GH / 2)) ** 2 + ((xx - GW / 2) / (GW / 2)) ** 2)
    stat = {}
    for ci, cn in enumerate("RGB"):
        v = r[..., ci][m]
        stat[cn] = dict(med=float(np.nanmedian(v)),
                        p10=float(np.nanpercentile(v, 10)),
                        p90=float(np.nanpercentile(v, 90)))
    # center vs edge (radius < 0.3 vs > 0.9) on the chroma ratios
    cmask = m & (rad < 0.35)
    emask = m & (rad > 0.95)

    def chroma(A, msk):
        R, G, B = A[..., 0][msk], A[..., 1][msk], A[..., 2][msk]
        return float(np.median(R / G)), float(np.median(B / G))

    lc, le = chroma(L, cmask), chroma(L, emask)
    pc, pe = chroma(P, cmask), chroma(P, emask)
    res[n] = dict(ratio=stat, lum_ctr=lc, lum_edge=le, phx_ctr=pc, phx_edge=pe,
                  ntiles=int(m.sum()))
    print(f"=== {n}  tiles={m.sum()}/{GW*GH}")
    print("   phx/lumen tile ratio  R med=%.4f [%.4f..%.4f]  G med=%.4f [%.4f..%.4f]  B med=%.4f [%.4f..%.4f]"
          % (stat['R']['med'], stat['R']['p10'], stat['R']['p90'],
             stat['G']['med'], stat['G']['p10'], stat['G']['p90'],
             stat['B']['med'], stat['B']['p10'], stat['B']['p90']))
    print("   center  R/G lum=%.4f phx=%.4f (%+.1f%%)   B/G lum=%.4f phx=%.4f (%+.1f%%)"
          % (lc[0], pc[0], 100 * (pc[0] / lc[0] - 1), lc[1], pc[1], 100 * (pc[1] / lc[1] - 1)))
    print("   edge    R/G lum=%.4f phx=%.4f (%+.1f%%)   B/G lum=%.4f phx=%.4f (%+.1f%%)"
          % (le[0], pe[0], 100 * (pe[0] / le[0] - 1), le[1], pe[1], 100 * (pe[1] / le[1] - 1)))

json.dump(res, open(f"{OUT}/spatial.json", "w"), indent=1)
print(f"\nwrote {OUT}/spatial.json")
