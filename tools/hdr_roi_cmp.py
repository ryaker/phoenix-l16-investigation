#!/usr/bin/env python3
"""Compare a Phoenix HDR against a Lumen master over fractional-ROI bands.

Both files are decoded with the canonical Radiance reader from hdrmean.py; the
ROI is given in FRACTIONAL image coordinates so the 2.5x resolution difference
between Phoenix (4173x3129) and Lumen (10432x7824) is handled automatically.

usage: hdr_roi_cmp.py <phoenix.hdr> <lumen.hdr> [x0 y0 x1 y1] ...
"""
import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "lldb_probes", "fusion_neutral_apply"))
import hdrmean  # noqa: E402

WR, WG, WB = 0.2155500054359436, 0.43230700492858887, 0.35214298963546753


def load(p):
    img, W, H = hdrmean.load(p)
    return np.asarray(img, np.float64)


def band(a, r):
    h, w = a.shape[:2]
    x0, y0, x1, y1 = r
    return a[int(y0 * h):int(y1 * h), int(x0 * w):int(x1 * w)]


def main():
    ap, al = load(sys.argv[1]), load(sys.argv[2])
    rest = [float(v) for v in sys.argv[3:]]
    rois = [tuple(rest[i:i + 4]) for i in range(0, len(rest), 4)] or [
        (0.0, 0.0, 1.0, 0.25), (0.0, 0.0, 1.0, 1.0)]
    print("%-26s %10s %10s %10s %10s %8s" %
          ("roi", "R", "G", "B", "luma", "achro"))
    for r in rois:
        bp, bl = band(ap, r), band(al, r)
        mp = bp.reshape(-1, bp.shape[-1])[:, :3].mean(0)
        ml = bl.reshape(-1, bl.shape[-1])[:, :3].mean(0)
        lp = WR * mp[0] + WG * mp[1] + WB * mp[2]
        ll = WR * ml[0] + WG * ml[1] + WB * ml[2]
        tag = "%.2f,%.2f-%.2f,%.2f" % r
        print("%-26s %10.5f %10.5f %10.5f %10.5f" % ("phx " + tag, *mp, lp))
        print("%-26s %10.5f %10.5f %10.5f %10.5f %8.4f" %
              ("lum " + tag, *ml, ll, ll / lp if lp else 0.0))
        print("%-26s %10.5f %10.5f %10.5f" %
              ("  ratio lum/phx", *(ml / np.where(mp == 0, 1, mp))))


if __name__ == "__main__":
    main()
