#!/usr/bin/env python3
"""Phoenix-vs-Lumen master TRANSFER CURVE on a spatially aligned grid.

Colour is closed (see the audit); what remains is achromatic and shot-varying.
This asks whether phx = k * lumen (a pure gain) or phx = f(lumen) (a tone
curve / highlight shoulder), by binning aligned tiles into lumen-luminance
deciles and reporting the ratio per decile.  A flat ratio column => pure gain.
A ratio that climbs with luminance => Lumen rolls highlights off.
"""
import numpy as np, re, os, json

OUT = "/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/runs/verify_master"
GW, GH = 256, 192


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
    ys = np.arange(GH + 1) * H // GH
    xs = np.arange(GW + 1) * W // GW
    out = np.zeros((GH, GW, 3), np.float64)
    for a in range(GH):
        band = rgb[ys[a]:ys[a + 1]]
        cs = np.add.reduceat(band, xs[:-1], axis=1)
        out[a] = cs.sum(0) / (np.diff(xs)[:, None] * band.shape[0])
    return out


NAMES = ["u1_28", "u1_35", "u1_70", "u1_150", "u2_35"]
res = {}
for n in NAMES:
    lp, pp = f"{OUT}/{n}_lumen.hdr", f"{OUT}/{n}_phx.hdr"
    if not (os.path.exists(lp) and os.path.exists(pp)):
        continue
    L, P = grid(load(lp)), grid(load(pp))
    lg, pg = L[..., 1].ravel(), P[..., 1].ravel()
    m = (lg > 1e-5) & (pg > 1e-5)
    lg, pg = lg[m], pg[m]
    order = np.argsort(lg)
    lg, pg = lg[order], pg[order]
    k = len(lg) // 10
    row = []
    for d in range(10):
        a, b = d * k, (d + 1) * k if d < 9 else len(lg)
        row.append((float(np.median(lg[a:b])), float(np.median(pg[a:b] / lg[a:b]))))
    # least-squares pure-gain fit through origin, and its residual
    kgain = float((lg * pg).sum() / (lg * lg).sum())
    resid = float(np.median(np.abs(pg - kgain * lg) / np.maximum(lg, 1e-9)))
    res[n] = dict(deciles=row, gain=kgain, rel_resid=resid)
    print(f"=== {n}   pure-gain fit k={kgain:.4f}   median |resid|/lumen = {resid*100:.1f}%")
    print("    lumenG :", "  ".join("%8.4f" % a for a, _ in row))
    print("    phx/lum:", "  ".join("%8.4f" % b for _, b in row))

json.dump(res, open(f"{OUT}/transfer.json", "w"), indent=1)
print(f"\nwrote {OUT}/transfer.json")
