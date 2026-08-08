#!/usr/bin/env python3
"""Analyze captured Lumen highlight-restore src/dst tile pairs."""
import json
import sys
import numpy as np

RUN = "/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/runs/highlight_restore"
meta = json.load(open(RUN + "/u1_35.json"))
dumps = meta["dumps"]
C = np.array([0.5522885322570801, 1.0, 0.6058176755905151])
A, B = 42.0, 1023.0

print("dumps:", [(d["idx"], d["w"], d["h"], d["phase"],
                  round(d["src_stats"]["frac1020"], 4)) for d in dumps])


def load(d):
    w, h = d["w"], d["h"]
    s = np.fromfile(d["src"], dtype="<u2").reshape(h, w).astype(np.int32)
    t = np.fromfile(d["dst"], dtype="<u2").reshape(h, w).astype(np.int32)
    return s, t


for d in dumps:
    s, t = load(d)
    h, w = s.shape
    diff = t - s
    ch = diff != 0
    print("\n=== tile %d  %dx%d phase=%s ===" % (d["idx"], w, h, d["phase"]))
    print("  changed: %d / %d (%.3f%%)" % (ch.sum(), s.size, 100.0 * ch.mean()))
    print("  src max %d  dst max %d" % (s.max(), t.max()))
    # changed pixels by CFA parity (y%2, x%2)
    yy, xx = np.mgrid[0:h, 0:w]
    for py in (0, 1):
        for px in (0, 1):
            m = (yy % 2 == py) & (xx % 2 == px)
            n = (ch & m).sum()
            print("    parity(y%%2=%d,x%%2=%d): changed=%6d  srcmax=%4d dstmax=%4d"
                  % (py, px, n, s[m].max(), t[m].max()))
    # distribution of src value among changed pixels
    sv = s[ch]
    if sv.size:
        print("    src of changed: min=%d p05=%d med=%d p95=%d max=%d"
              % (sv.min(), np.percentile(sv, 5), np.median(sv),
                 np.percentile(sv, 95), sv.max()))
        print("    dst of changed: min=%d med=%d max=%d"
              % (t[ch].min(), np.median(t[ch]), t[ch].max()))
        print("    delta: min=%d med=%d max=%d"
              % (diff[ch].min(), np.median(diff[ch]), diff[ch].max()))
    # does any pixel below the 0.985*B threshold change without a saturated neighbour?
    satm = s >= 1007
    from scipy import ndimage  # noqa
    print("    #src>=1007: %d   #src>=1023: %d" % (satm.sum(), (s >= 1023).sum()))

print("\n--- neighbourhood test on the most saturated tile ---")
d = max(dumps, key=lambda x: x["src_stats"]["frac1020"])
s, t = load(d)
h, w = s.shape
ch = (t - s) != 0
# radius at which a changed pixel has a saturated neighbour
sat = s >= 1007
ys, xs = np.nonzero(ch)
rad = []
for i in range(0, len(ys), max(1, len(ys) // 3000)):
    y, x = ys[i], xs[i]
    found = None
    for r in range(0, 13):
        y0, y1 = max(0, y - r), min(h, y + r + 1)
        x0, x1 = max(0, x - r), min(w, x + r + 1)
        if sat[y0:y1, x0:x1].any():
            found = r
            break
    rad.append(found if found is not None else 99)
rad = np.array(rad)
print("  distance from changed pixel to nearest src>=1007:")
for r in range(0, 13):
    print("    r=%2d : %d" % (r, (rad == r).sum()), end="")
print("\n    r>=99:", (rad == 99).sum())
