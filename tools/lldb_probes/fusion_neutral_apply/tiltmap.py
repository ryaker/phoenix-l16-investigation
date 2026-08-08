#!/usr/bin/env python3
"""Is the Phoenix-vs-Lumen channel error a GLOBAL gain or a SPATIAL shading?

Downsamples both masters onto a common GxG grid of block means and reports the
per-block per-channel ratio lumen/phoenix. A flat map => global per-channel
gain. A radial/gradient map => lens or color shading.

usage: tiltmap.py <phoenix.hdr> <lumen.hdr> [grid]
"""
import numpy as np, sys


def load(path):
    with open(path, "rb") as f:
        raw = f.read()
    i = raw.find(b"\n\n")
    j = raw.index(b"\n", i + 2)
    dims = raw[i + 2:j].split()
    H = int(dims[1]); W = int(dims[3])
    a = np.frombuffer(raw, dtype=np.uint8, count=W * H * 4,
                      offset=j + 1).reshape(H, W, 4).astype(np.float32)
    s = np.ldexp(1.0, a[:, :, 3].astype(np.int32) - 136)
    return a[:, :, :3] * s[:, :, None]


def blocks(img, G):
    H, W, _ = img.shape
    ys = np.linspace(0, H, G + 1).astype(int)
    xs = np.linspace(0, W, G + 1).astype(int)
    out = np.zeros((G, G, 3), np.float64)
    for r in range(G):
        for c in range(G):
            out[r, c] = img[ys[r]:ys[r + 1], xs[c]:xs[c + 1]].reshape(-1, 3).mean(0)
    return out


G = int(sys.argv[3]) if len(sys.argv) > 3 else 8
p = blocks(load(sys.argv[1]), G)
l = blocks(load(sys.argv[2]), G)
r = l / np.maximum(p, 1e-9)

for ci, cn in enumerate("RGB"):
    m = r[:, :, ci]
    print(f"--- {cn}  lumen/phoenix   mean={m.mean():.4f} "
          f"min={m.min():.4f} max={m.max():.4f} relspread={(m.max()-m.min())/m.mean():.4f}")
    for row in m:
        print("   " + " ".join(f"{v:6.3f}" for v in row))

# chroma-only view: divide out the per-block luma error so pure shading shows
print("\n=== chroma-only (each channel ratio / that block's G ratio)")
for ci, cn in enumerate("RB"):
    idx = 0 if cn == "R" else 2
    m = r[:, :, idx] / r[:, :, 1]
    print(f"--- {cn}/G  mean={m.mean():.4f} min={m.min():.4f} max={m.max():.4f} "
          f"relspread={(m.max()-m.min())/m.mean():.4f}")
    for row in m:
        print("   " + " ".join(f"{v:6.3f}" for v in row))
