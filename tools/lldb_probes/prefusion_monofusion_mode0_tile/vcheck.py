#!/usr/bin/env python3
"""Pin Lumen's patch-noise V against Phoenix's patchNoiseV on the SAME patch.

Lumen's implied Lambda = kNoiseScale * V was solved from the captured
pre/post-Wiener coefficients (Lambda = 382.979). Phoenix computes
    V = (kWhite*mu)^2 * max(1e-5, a_s*z + b_s)
with z = max((kBlack + (H - kBlack)/mu)/kWhite, kBlack/kWhite),
     H = sqrt(1 / mean(1/(I+0.1)^2)),  mu = mean(I).
This script evaluates every term on Lumen's own captured spatial target patch
so the only unknown left is (a_s, b_s).
"""
import numpy as np, sys, os

BASE = ("/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/runs/"
        "prefusion_monofusion_mode0_tile/unit1_35mm")
kBlack, kWhite = 42.0, 1023.0
kNoiseScale = 2.725372314453125
kR = 2.3183400630950928
kC = 4.0
LAMBDA = 382.979          # measured, +/- 0.089 over 181 coefficients

T = np.fromfile(os.path.join(BASE, "patch_target_spatial.f32le"),
                dtype="<f4").astype(np.float64)
print("target patch n=%d  min=%.6f max=%.6f mean=%.8f" %
      (T.size, T.min(), T.max(), T.mean()))

mu = T.mean()
H = np.sqrt(1.0 / np.mean(1.0 / (T + 0.1) ** 2))
z = max((kBlack + (H - kBlack) / mu) / kWhite, kBlack / kWhite)
white_mean = kWhite * mu
V_lumen = LAMBDA / kNoiseScale
model_lumen = V_lumen / (white_mean ** 2)

print("mu=%.8f  H=%.8f  z=%.10f  white_mean=%.6f" % (mu, H, z, white_mean))
print("Lumen: Lambda=%.4f -> V=%.6f -> required model (a*z+b) = %.10g"
      % (LAMBDA, V_lumen, model_lumen))

# Phoenix's (a_s, b_s) come from the shot's VST noise record; accept on argv.
if len(sys.argv) >= 3:
    a, b = float(sys.argv[1]), float(sys.argv[2])
    for tag, (aa, bb) in (("raw (a,b)", (a, b)),
                          ("scaled a/(R*C), b/(R*C)", (a / (kR * kC), b / (kR * kC)))):
        model = max(1e-5, aa * z + bb)
        V = white_mean * white_mean * model
        print("%-26s a=%-14.8g b=%-14.8g model=%-14.8g V=%-14.8g "
              "Lambda=%-12.6f  ratio_to_lumen=%.6f"
              % (tag, aa, bb, model, V, kNoiseScale * V,
                 (kNoiseScale * V) / LAMBDA))
    # Solve: which (a,b) pair reproduces model_lumen given z?
    print("\nsolve: a*z + b = %.10g  with z=%.10g" % (model_lumen, z))
    print("  if b=0 -> a = %.10g" % (model_lumen / z))
