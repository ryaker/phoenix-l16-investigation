#!/usr/bin/env python3
"""Identify Lumen's patch-noise V law from the captured patch + measured Lambda.

Ground truth: Lambda = kNoiseScale * V = 382.979 (solved from Lumen's own
pre/post-Wiener coefficients on THIS patch).  Scan the plausible unit
conventions and all 28 installed VST rows; report which combination lands on
Lambda = 382.979.
"""
import numpy as np, os, re

BASE = ("/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/runs/"
        "prefusion_monofusion_mode0_tile/unit1_35mm")
VST = "/Users/ryaker/L16_Phoenix/phoenix/engine/lri/vst_table.h"
kBlack, kWhite = 42.0, 1023.0
kNoiseScale = 2.725372314453125
kR = 2.3183400630950928
kC = 4.0
LAMBDA = 382.979

rows = []
for m in re.finditer(r"\{(\d+), ([-\d.e]+)f, ([-\d.e]+)f, ([-\d.e]+)f, ([-\d.e-]+)f\}",
                     open(VST).read()):
    rows.append((int(m.group(1)), float(m.group(4)), float(m.group(5))))

T = np.fromfile(os.path.join(BASE, "patch_target_spatial.f32le"),
                dtype="<f4").astype(np.float64)


def V_of(I, a, b, eps):
    mu = I.mean()
    H = np.sqrt(1.0 / np.mean(1.0 / (I + eps) ** 2))
    z = max((kBlack + (H - kBlack) / mu) / kWhite, kBlack / kWhite)
    model = max(1e-5, a * z + b)
    return (kWhite * mu) ** 2 * model, z, model, mu, H


def Vn_of(I, a, b, eps):
    """Normalized-domain variant: patch divided by white first."""
    return V_of(I / kWhite, a, b, eps)


print("required Lambda = %.4f -> V = %.6f" % (LAMBDA, LAMBDA / kNoiseScale))
print()
for tag, fn in (("DN patch (as captured)", V_of),
                ("normalized patch /1023", Vn_of)):
    for stag, sc in (("a,b scaled 1/(R*C)", 1.0 / (kR * kC)), ("a,b raw", 1.0)):
        best = None
        for g, a, b in rows:
            V, z, model, mu, H = fn(T, a * sc, b * sc, 0.1)
            lam = kNoiseScale * V
            r = lam / LAMBDA
            if best is None or abs(np.log(r)) < abs(np.log(best[0] / LAMBDA)):
                best = (lam, g, z, model, mu, H)
        print("%-24s %-20s best gain=%-5d Lambda=%-14.6g ratio=%-10.4g "
              "(z=%.6g model=%.6g mu=%.6g H=%.6g)"
              % (tag, stag, best[1], best[0], best[0] / LAMBDA,
                 best[2], best[3], best[4], best[5]))
        # full listing for the DN/scaled case
        if tag.startswith("DN") and stag.startswith("a,b sc"):
            for g, a, b in rows:
                V, z, model, mu, H = fn(T, a * sc, b * sc, 0.1)
                print("    gain %-5d a_s=%-13.6g b_s=%-13.6g model=%-13.6g "
                      "V=%-13.6g Lambda=%-13.6g ratio=%.4g"
                      % (g, a * sc, b * sc, model, V, kNoiseScale * V,
                         kNoiseScale * V / LAMBDA))
