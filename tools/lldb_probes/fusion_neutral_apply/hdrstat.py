#!/usr/bin/env python3
"""Global chroma of a flat (non-RLE) RGBE .hdr:  scale = ldexp(1, e-136)."""
import numpy as np, sys, re

def load(path):
    with open(path,"rb") as f:
        data = f.read()
    i = data.find(b"\n\n")
    if i < 0: raise RuntimeError("no header end")
    j = data.index(b"\n", i+2)
    dims = data[i+2:j].decode().strip()
    m = re.match(r"-Y (\d+) \+X (\d+)", dims)
    H, W = int(m.group(1)), int(m.group(2))
    px = np.frombuffer(data, dtype=np.uint8, count=W*H*4, offset=j+1).reshape(H,W,4)
    return W,H,px

for path in sys.argv[1:]:
    W,H,px = load(path)
    e = px[...,3].astype(np.int32)
    scale = np.where(e>0, np.ldexp(1.0, e-136), 0.0)
    rgb = px[...,:3].astype(np.float64) * scale[...,None]
    m = (rgb[...,1] > 1e-6)
    R,G,B = rgb[...,0][m], rgb[...,1][m], rgb[...,2][m]
    print("%s  %dx%d  valid=%.4f" % (path, W, H, m.mean()))
    print("   mean R=%.6g G=%.6g B=%.6g   R/G=%.4f  B/G=%.4f" %
          (R.mean(),G.mean(),B.mean(),R.mean()/G.mean(),B.mean()/G.mean()))
    med = np.median(np.stack([R,G,B]),1)
    print("   median R=%.6g G=%.6g B=%.6g   R/G=%.4f  B/G=%.4f" %
          (med[0],med[1],med[2],med[0]/med[1],med[2]/med[1]))
