#!/usr/bin/env python3
"""Which Wiener form does Lumen's captured patch obey?

T = patch_target_coeff, S = patch_source_coeff_pre, F = patch_source_coeff_post
(the wavecheck.py coherence test proves all three are the same patch).

Measured source weight   w_k = (F_k - T_k) / (S_k - T_k).
Form A (Codex bundle):   w = d2/(d2+lam)  ->  lam_k = d2*(1-w)/w
Form B (inverted):       w = lam/(lam+d2) ->  lam_k = d2*w/(1-w)
Whichever form makes lam_k / F_table_k CONSTANT across coefficients is the
installed one.  Report the spread for both.
"""
import numpy as np, os, re

BASE = ("/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/runs/"
        "prefusion_monofusion_mode0_tile/unit1_35mm")
TBL = "/Users/ryaker/L16_Phoenix/phoenix/engine/merge/monofusion_coeff_table.h"

txt = open(TBL).read()
body = txt.split("kMonoFusionCoeffWeights[256] =", 1)[1].split("{", 1)[1]
body = body.split("}", 1)[0]
Fk = np.array([float(v) for v in re.findall(r"([-\d.eE+]+)f", body)], np.float64)
assert Fk.size == 256, Fk.size
print("F_k table: n=%d  F[0]=%.6f F[1]=%.6f min=%.6f max=%.6f"
      % (Fk.size, Fk[0], Fk[1], Fk.min(), Fk.max()))

ld = lambda n: np.fromfile(os.path.join(BASE, n), dtype="<f4").astype(np.float64)
T, S, F = (ld("patch_target_coeff.f32le"), ld("patch_source_coeff_pre.f32le"),
           ld("patch_source_coeff_post.f32le"))
d = S - T
d2 = d * d
w = np.where(np.abs(d) > 1e-9, (F - T) / np.where(d == 0, 1, d), np.nan)

good = np.isfinite(w) & (np.abs(d) > 1e-3) & (w > 1e-6) & (w < 1 - 1e-6)
print("well-conditioned coefficients: %d / 256" % good.sum())
print("w: min=%.6g max=%.6g median=%.6g" % (w[good].min(), w[good].max(),
                                            np.median(w[good])))
sp = float(np.corrcoef(np.argsort(np.argsort(w[good])),
                       np.argsort(np.argsort(d2[good])))[0, 1])
print("spearman(w, d2) = %.4f" % sp)

for tag, lam in (("A (Codex: w=d2/(d2+lam), src weight rises with disagreement)",
                  d2 * (1 - w) / w),
                 ("B (inverted: w=lam/(lam+d2))", d2 * w / (1 - w))):
    r = lam[good] / Fk[good]
    print("\nform %s" % tag)
    print("  Lambda = lam_k/F_k : mean=%.6f std=%.6f  relspread=%.3g  "
          "min=%.6f max=%.6f" % (r.mean(), r.std(), r.std() / abs(r.mean()),
                                 r.min(), r.max()))
    # reconstruct with the mean Lambda and score against F
    L = r.mean()
    lk = L * Fk
    wA = d2 / (d2 + lk) if tag.startswith("A") else lk / (lk + d2)
    rec = T + wA * (S - T)
    e = np.abs(rec - F)
    print("  reconstruct F: maxabs=%.6g rms=%.6g  (|F|max=%.4f)"
          % (e.max(), np.sqrt((e * e).mean()), np.abs(F).max()))

kNoiseScale = 2.725372314453125
for tag, lam in (("A", d2 * (1 - w) / w), ("B", d2 * w / (1 - w))):
    L = (lam[good] / Fk[good]).mean()
    print("form %s: Lambda=%.6g -> V = Lambda/noise_scale = %.6g" %
          (tag, L, L / kNoiseScale))
