"""Determine the exact window Lumen's AUX plane uses (dilation of src)."""
import json, sys, itertools
import numpy as np

p = sys.argv[1] if len(sys.argv) > 1 else \
    "/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/runs/highlight_restore/aux_u1_35.json"
d = json.load(open(p))
rows = d["rows"] if isinstance(d, dict) else d
OFF = {"m4": -4, "m3": -3, "m2": -2, "m1": -1,
       "p1": 1, "p2": 2, "p3": 3, "p4": 4, "p5": 5}

samples = []
for r in rows:
    w = r["w"]
    stack = {0: np.array(r["src"], np.int32)}
    ok = True
    for k, dy in OFF.items():
        v = r["nb"].get(k)
        if v is None or len(v) != w:
            ok = False
            break
        stack[dy] = np.array(v, np.int32)
    if not ok:
        continue
    samples.append((np.array(r["aux"], np.int32), stack, w, r["row"]))
print("usable samples:", len(samples), "of", len(rows))


def evaluate(dys, dxs):
    tot = bad = 0
    worst = 0
    for aux, stack, w, _ in samples:
        acc = np.full(w, -1, np.int32)
        for dy in dys:
            if dy not in stack:
                return None
            row = stack[dy]
            for dx in dxs:
                sh = np.full(w, -1, np.int32)
                if dx == 0:
                    sh = row
                elif dx > 0:
                    sh[:w - dx] = row[dx:]
                else:
                    sh[-dx:] = row[:dx]
                acc = np.maximum(acc, sh)
        m = 4
        diff = np.abs(acc[m:w - m] - aux[m:w - m])
        tot += diff.size
        bad += int((diff != 0).sum())
        worst = max(worst, int(diff.max()))
    return bad, tot, worst


cands = []
for dyset in [(0,), (-1, 0, 1), (-2, 0, 2), (-2, -1, 0, 1, 2), (-1, 0, 1, 2),
              (0, 1), (-1, 0), (0, 1, 2), (-2, -1, 0), (-2, 0, 1, 2),
              (-3, -2, -1, 0, 1, 2, 3), (-2, -1, 0, 1), (-1, 0, 1, 2, 3)]:
    for dxset in [(0,), (-1, 0, 1), (-2, 0, 2), (-2, -1, 0, 1, 2), (0, 1),
                  (-1, 0), (-1, 0, 1, 2), (-2, -1, 0, 1), (-3, -2, -1, 0, 1, 2, 3)]:
        r = evaluate(dyset, dxset)
        if r is None:
            continue
        bad, tot, worst = r
        cands.append((bad / tot, worst, dyset, dxset))
cands.sort()
for frac, worst, dy, dx in cands[:12]:
    print("mismatch=%.5f worst=%d  dy=%s dx=%s" % (frac, worst, dy, dx))
