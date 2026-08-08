#!/usr/bin/env python3
"""Flat-RGBE Radiance mean, over all pixels and over nonzero-green pixels."""
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
    return a[:, :, :3] * s[:, :, None], W, H


def _main():
  for p in sys.argv[1:]:
    img, W, H = load(p)
    g = img[:, :, 1]
    nz = g > 1e-6
    print("%-58s %dx%d  all: R=%.6f G=%.6f B=%.6f | nz(%.2f%%): "
          "R=%.6f G=%.6f B=%.6f" %
          (p.split("/")[-1], W, H,
           img[:, :, 0].mean(), g.mean(), img[:, :, 2].mean(),
           100.0 * nz.mean(),
           img[:, :, 0][nz].mean(), g[nz].mean(), img[:, :, 2][nz].mean()))


if __name__ == "__main__":
    _main()
