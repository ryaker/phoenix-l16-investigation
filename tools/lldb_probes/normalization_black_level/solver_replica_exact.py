#!/usr/bin/env python3
"""Bit-exact float32 replica of the libcp black-level solver at 0xf36f0.

Transcribed instruction-for-instruction from the x86_64 disassembly of
libcp.dylib 0xf36f0..0xf3888.  Immediates read out of __TEXT at the addresses
the code references:

  0x5a8200 = 0.25      guard: mean of the four channel means
  0x5a8128 = 1.0       reciprocal numerator
  0x5a8120 = -0.5      weight on the (ch0, ch3) limb
  0x5aae64 = 1000000.0 initial best cost
  0x5a81f0 = abs mask (0x7fffffff x4)

Cost minimised over the grid b_k = x0 + k*(span/N), k in [0, N):

  cost(b) = | (m1 + m2)/(2*g1) - b*(1/g1)
              - 0.5 * ( m0/g0 + m3/g2 - b*(1/g0) - b*(1/g2) ) |

Note g3 is never read.  Ties keep the earliest k (strict cmpltss).
"""
import json
import os

import numpy as np

BASE = ("/Volumes/Dev/L16_Lumen_ReverseEngineering/runs/"
        "normalization_black_level")
F = np.float32


def solve(means, gains, x0, span, n, prior):
    """Return the black level the solver leaves at obj+0xac."""
    m = [F(v) for v in means[:4]]
    g = [F(v) for v in gains[:4]]
    x0, span, n = F(x0), F(span), int(n)

    s = F(m[1] + m[0])          # f376b..f3775: ((m1+m0)+m2)+m3
    s = F(s + m[2])
    s = F(s + m[3])
    if F(s * F(0.25)) < x0:     # f3781 ucomiss / jb -> leave obj+0xac alone
        return F(prior)
    if n <= 0:                  # f378a test/jle -> store x0
        return x0

    g1x2 = F(g[1] + g[1])
    a0 = F(F(m[2] + m[1]) / g1x2)          # xmm11
    r1 = F(F(1.0) / g[1])                  # xmm12
    r0 = F(F(1.0) / g[0])                  # xmm14
    r2 = F(F(1.0) / g[2])                  # xmm13
    step = F(span / F(np.float32(n)))      # xmm1 = span / (float)N
    b0 = F(F(m[0] / g[0]) + F(m[3] / g[2]))  # xmm10

    best_c, best_b = F(1000000.0), x0
    for k in range(n):
        b = F(F(F(np.float32(k)) * step) + x0)
        t2 = F(a0 - F(b * r1))
        t4 = F(F(b0 - F(b * r0)) - F(b * r2))
        t4 = F(F(t4 * F(-0.5)) + t2)
        c = F(abs(t4))
        if c < best_c:
            best_b = b
        best_c = F(min(c, best_c))
    return best_b


def load():
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
                    out.append((d, en, F(e["trip_out"][0])))
    return out


def main():
    recs = load()
    ok = 0
    print("%-9s %-10s %-10s %s" % ("run", "observed", "replica", "match"))
    for label, en, obs in recs:
        got = solve(en["means"], en["gains"], en["x0"], en["span"], en["N"],
                    en["trip_in"][0])
        hit = got.tobytes() == obs.tobytes()
        ok += hit
        print("%-9s %-10.6f %-10.6f %s" % (
            label, float(obs), float(got), "ok" if hit else "MISMATCH"))
    print("\nbit-exact %d/%d" % (ok, len(recs)))
    return ok, len(recs)


if __name__ == "__main__":
    main()
