#!/usr/bin/env python3
"""Test: is the 2080x1560 RGBA-half image == CFA-binned linearized Bayer (no WB, no CCM)?"""
import numpy as np
d = "/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/runs/fusion_neutral_apply/dump_u1_28"
np.set_printoptions(precision=6, suppress=True)

bay = np.fromfile(d+"/in_bayer_u16.raw", dtype="<u2").reshape(3120,4160).astype(np.float64)
img = np.fromfile(d+"/post_out_rgba16f.raw", dtype="<f2").reshape(1560,2080,4).astype(np.float64)

# 2x2 CFA quads.  phases: (0,0)=G  (0,1)=X  (1,0)=Y  (1,1)=G
g0 = bay[0::2,0::2]; x = bay[0::2,1::2]; y = bay[1::2,0::2]; g1 = bay[1::2,1::2]
G = 0.5*(g0+g1)
print("quad shapes", g0.shape, "img", img.shape)

R_img, G_img, B_img, A_img = img[...,0], img[...,1], img[...,2], img[...,3]
print("A vs G: max|A-G| = %.6g   corr=%.6f" % (np.abs(A_img-G_img).max(),
      np.corrcoef(A_img.ravel(), G_img.ravel())[0,1]))

# fit out = (raw - black) * s  per channel, against each candidate CFA assignment
def fit(raw, out, nm):
    m = (out > 1e-4) & (out < 1.5)
    A = np.stack([raw[m], np.ones(m.sum())], 1)
    (s, b), res, *_ = np.linalg.lstsq(A, out[m], rcond=None)
    pred = raw*s + b
    rel = np.abs(pred[m]-out[m]).sum()/np.abs(out[m]).sum()
    print("  %-14s slope=%.8f  intercept=%.6f  black=%.3f  1/slope=%.2f  relL1=%.5f  corr=%.6f"
          % (nm, s, b, -b/s, 1/s, rel, np.corrcoef(raw[m], out[m])[0,1]))
    return s, b

print("\n-- assignment A:  R<-x(0,1)  G<-avg  B<-y(1,0)")
fit(x, R_img, "R vs x"); fit(G, G_img, "G vs Gavg"); fit(y, B_img, "B vs y")
print("\n-- assignment B:  R<-y(1,0)  B<-x(0,1)")
fit(y, R_img, "R vs y"); fit(x, B_img, "B vs x")

print("\n-- global means")
print("   raw-42 means: x=%.3f G=%.3f y=%.3f   x/G=%.4f y/G=%.4f" %
      ((x.mean()-42),(G.mean()-42),(y.mean()-42),(x.mean()-42)/(G.mean()-42),(y.mean()-42)/(G.mean()-42)))
print("   img means   : R=%.6f G=%.6f B=%.6f    R/G=%.4f B/G=%.4f" %
      (R_img.mean(),G_img.mean(),B_img.mean(),R_img.mean()/G_img.mean(),B_img.mean()/G_img.mean()))
