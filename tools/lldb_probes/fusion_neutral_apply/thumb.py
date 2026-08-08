#!/usr/bin/env python3
"""Side-by-side gamma-encoded thumbnails of a Lumen reference and a Phoenix
render, on a COMMON display scale so brightness is directly comparable.

usage: thumb.py <tag> <shot> [<lumen_shot>]
  reads  /tmp/<shot>_<tag>.hdr   and   runs/verify_master/<lumen_shot>_lumen.hdr
  writes /tmp/thumb_<shot>_<tag>.png
"""
import sys, numpy as np
from hdrmean import load
from PIL import Image

OUT = "/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/runs/verify_master"
TW = 700


def down(A, tw):
    h, w, _ = A.shape
    th = max(1, int(round(h * tw / float(w))))
    ys = (np.arange(th) * h // th)
    xs = (np.arange(tw) * w // tw)
    return A[ys][:, xs]


def enc(A, scale):
    v = np.clip(A / scale, 0.0, 1.0)
    return (np.power(v, 1.0 / 2.2) * 255.0 + 0.5).astype(np.uint8)


def main():
    tag, shot = sys.argv[1], sys.argv[2]
    lshot = sys.argv[3] if len(sys.argv) > 3 else shot
    P, _, _ = load("/tmp/%s_%s.hdr" % (shot, tag))
    L, _, _ = load("%s/%s_lumen.hdr" % (OUT, lshot))
    p = down(P, TW)
    l = down(L, TW)
    scale = float(np.percentile(l[:, :, 1], 99.5))
    print("common display scale (Lumen G p99.5) = %.6f" % scale)
    print("Lumen  %dx%d -> %s   Phoenix %dx%d -> %s" %
          (L.shape[1], L.shape[0], l.shape[:2][::-1],
           P.shape[1], P.shape[0], p.shape[:2][::-1]))
    hh = max(l.shape[0], p.shape[0])
    canvas = np.zeros((hh, TW * 2 + 12, 3), np.uint8)
    canvas[:l.shape[0], :TW] = enc(l, scale)
    canvas[:p.shape[0], TW + 12:] = enc(p, scale)
    out = "/tmp/thumb_%s_%s.png" % (shot, tag)
    Image.fromarray(canvas).save(out)
    print("wrote", out, "(LEFT=Lumen  RIGHT=Phoenix)")


if __name__ == "__main__":
    main()
