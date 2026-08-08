"""Verify hr_ref against the six captured Lumen tile pairs."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hr_ref

R = "/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/runs/highlight_restore"
meta = json.load(open(os.path.join(R, "u1_35.json")))["dumps"]
M = hr_ref.M

phases = sys.argv[1:] or ["asis"]
for d in meta:
    w, h = d["w"], d["h"]
    src = np.fromfile(d["src"], np.uint16).reshape(h, w)
    dst = np.fromfile(d["dst"], np.uint16).reshape(h, w)
    ref_dst = dst[M:h - M, M:w - M].astype(np.int64)
    ref_src = src[M:h - M, M:w - M].astype(np.int64)
    changed = ref_dst != ref_src
    cam = d.get("cam")
    if not cam:
        raise SystemExit("tile %d has no per-camera gain vector -- re-run probe"
                         % d["idx"])
    ctx = hr_ref.make_ctx(np.asarray(cam[:4], np.float32))
    best = None
    for py in (0, 1):
        for px in (0, 1):
            out = hr_ref.restore_tile(src, (py, px), ctx)
            got = out[M:h - M, M:w - M].astype(np.int64)
            diff = np.abs(got - ref_dst)
            exact = int((diff == 0).sum())
            near = int((diff <= 1).sum())
            tot = diff.size
            key = (-exact, py, px)
            if best is None or key < best[0]:
                best = (key, py, px, exact, near, tot, diff, got)
    _, py, px, exact, near, tot, diff, got = best
    ch = int(changed.sum())
    print("tile%d %dx%d meta_phase=%s -> best (%d,%d)  exact=%.4f%% |d|<=1=%.4f%%"
          " changed=%d/%d  maxdiff=%d" %
          (d["idx"], w, h, d["phase"], py, px, 100.0 * exact / tot,
           100.0 * near / tot, ch, tot, int(diff.max())))
    if ch:
        dc = diff[changed]
        print("    on changed px: exact=%.3f%% <=1=%.3f%% <=4=%.3f%% max=%d mean=%.2f"
              % (100.0 * (dc == 0).mean(), 100.0 * (dc <= 1).mean(),
                 100.0 * (dc <= 4).mean(), int(dc.max()), float(dc.mean())))
    unc = ~changed
    if unc.sum():
        du = diff[unc]
        print("    on unchanged px: exact=%.3f%% max=%d" %
              (100.0 * (du == 0).mean(), int(du.max())))
