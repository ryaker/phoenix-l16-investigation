#!/usr/bin/env python3
"""float32 replica search for the libcp black-level solver (0xf36f0).

Pairs every solver entry/exit record captured by black_probe6 across the
eight-run corpus, rebuilds the 40-step candidate grid in float32, and scores
a family of candidate cost functions by how many recorded invocations each
one reproduces exactly.

No claim is made here about which cost is correct; the script reports match
counts and lets the numbers decide.
"""
import json
import os

import numpy as np

BASE = ("/Volumes/Dev/L16_Lumen_ReverseEngineering/runs/"
        "normalization_black_level")
F32 = np.float32


def load():
    """Return [(label, entry_record, observed_black_f32), ...]."""
    out = []
    for d in sorted(os.listdir(BASE)):
        p = os.path.join(BASE, d, "solve.json")
        if not os.path.exists(p):
            continue
        pend = {}
        with open(p) as fh:
            ev = json.load(fh)
        for e in ev:
            if e["ev"] == "entry":
                pend[e["obj"]] = e
            else:
                en = pend.pop(e["obj"], None)
                if en is not None:
                    out.append((d, en, F32(e["trip_out"][0])))
    return out


def grid(en):
    """Rebuild the candidate grid: x0 + k*(span/N), k in [0, N)."""
    x0, span, n = F32(en["x0"]), F32(en["span"]), int(en["N"])
    step = F32(span / F32(n))
    return [F32(x0 + F32(k) * step) for k in range(n)]


def _var(vals):
    if len(vals) < 2:
        return F32(0)
    mu = F32(sum(vals) / F32(len(vals)))
    return F32(sum(F32((v - mu) ** 2) for v in vals) / F32(len(vals)))


def _sum(vals):
    t = F32(0)
    for v in vals:
        t = F32(t + v)
    return t


def cost_variants(m, g, b):
    """name -> float32 cost of candidate black level b."""
    act = [i for i in range(4) if g[i] != 0]
    d = [F32(m[i] - b) for i in range(4)]
    out = {}
    out["var_d"] = _var([d[i] for i in act])
    out["var_d_g"] = _var([F32(d[i] * g[i]) for i in act])
    out["var_d_over_g"] = _var([F32(d[i] / g[i]) for i in act])
    out["var_g_over_d"] = _var([F32(g[i] / d[i]) for i in act if d[i] != 0])
    if d[1] != 0:
        r = [F32(d[i] / d[1]) for i in range(4)]
        oth = [i for i in act if i != 1]
        out["sq_ratio_g"] = _sum([F32((r[i] - g[i]) ** 2) for i in oth])
        out["sq_ratio_invg"] = _sum(
            [F32((r[i] - F32(F32(1) / g[i])) ** 2) for i in oth])
        out["sq_ratio_g_norm"] = _sum(
            [F32((F32(r[i] * g[i]) - F32(1)) ** 2) for i in oth])
    return out


def main():
    recs = load()
    names, tally, detail = None, {}, {}
    print("%-9s %-7s %-4s %s" % ("run", "black", "k", "means / gains"))
    for label, en, obs in recs:
        m = [F32(x) for x in en["means"][:4]]
        g = [F32(x) for x in en["gains"][:4]]
        gr = grid(en)
        k_obs = min(range(len(gr)), key=lambda k: abs(float(gr[k] - obs)))
        print("%-9s %-7.2f %-4d %s | %s" % (
            label, float(obs), k_obs,
            " ".join("%.3f" % float(v) for v in m),
            " ".join("%.4f" % float(v) for v in g)))
        per_b = [cost_variants(m, g, b) for b in gr]
        if names is None:
            names = sorted(per_b[0])
            tally = {n: 0 for n in names}
            detail = {n: [] for n in names}
        for n in names:
            if n not in per_b[0]:
                continue
            k = min(range(len(gr)), key=lambda i: float(per_b[i][n]))
            detail[n].append((label, k, k_obs))
            if k == k_obs:
                tally[n] += 1
    print("\n%d invocations\n" % len(recs))
    for n in sorted(tally, key=lambda x: -tally[x]):
        print("%-18s exact %2d/%d" % (n, tally[n], len(recs)))
    return tally, detail, recs


if __name__ == "__main__":
    main()
