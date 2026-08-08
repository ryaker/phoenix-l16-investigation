#!/usr/bin/env python3
"""Heatmap of the L/P ratio field.  Blue=Lumen darker(<0.8) .. white=1.0 .. red=Lumen brighter.
usage: ratiopng.py <tag> <shot> [<lumen_shot>]   -> /Users/ryaker/tmpimg/ratio_<shot>_<tag>.png
"""
import sys, numpy as np
from hdrmean import load
from PIL import Image

OUT = "/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/runs/verify_master"
TW = 380


def down(A, tw):
    h, w, _ = A.shape
    th = max(1, int(round(h * tw / float(w))))
    return A[(np.arange(th) * h // th)][:, (np.arange(tw) * w // tw)]


def main():
    tag, shot = sys.argv[1], sys.argv[2]
    lshot = sys.argv[3] if len(sys.argv) > 3 else shot
    P, _, _ = load("/tmp/%s_%s.hdr" % (shot, tag))
    L, _, _ = load("%s/%s_lumen.hdr" % (OUT, lshot))
    p = down(P, TW).astype(np.float64)
    l = down(L, TW).astype(np.float64)
    H = min(p.shape[0], l.shape[0])
    pg, lg = p[:H, :, 1], l[:H, :, 1]
    # local median smoothing via block reduce then upsample keeps it readable
    r = np.where(pg > 1e-5, lg / np.maximum(pg, 1e-12), np.nan)
    K = 5
    hh, ww = (H // K) * K, (TW // K) * K
    rb = np.nanmedian(r[:hh, :ww].reshape(hh // K, K, ww // K, K), axis=(1, 3))
    v = np.clip((rb - 0.6) / 0.5, 0, 1)          # 0.6 -> 0, 1.1 -> 1
    img = np.zeros(rb.shape + (3,), np.uint8)
    img[:, :, 0] = np.nan_to_num(v * 255)                 # R rises with ratio
    img[:, :, 1] = np.nan_to_num((1 - np.abs(v - 0.8) / 0.8) * 255)
    img[:, :, 2] = np.nan_to_num((1 - v) * 255)           # B high where Lumen darker
    out = "/Users/ryaker/tmpimg/ratio_%s_%s.png" % (shot, tag)
    Image.fromarray(img).resize((ww, hh), Image.NEAREST).save(out)
    fin = np.isfinite(rb)
    print("ratio field %dx%d  min=%.3f med=%.3f max=%.3f" %
          (rb.shape[1], rb.shape[0], np.nanmin(rb), np.nanmedian(rb), np.nanmax(rb)))
    print("BLUE = Lumen much darker than Phoenix; WHITE/RED = match")
    print("wrote", out)


if __name__ == "__main__":
    main()
