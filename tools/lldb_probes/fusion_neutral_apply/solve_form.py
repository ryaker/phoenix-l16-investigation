#!/usr/bin/env python3
"""Solve the FORM of the per-camera color transform inside libcp 0x1ab2d0.

Input : pairs JSON captured by pairs.py  (in_rgb -> out_rgb, 20k+ samples)
Output: least-squares 3x3 (and affine 3x4, and diagonal) fits + residuals,
        so we can discriminate M vs M^-1 vs inv(ProPhoto->XYZ).M[^-1] vs diag.
"""
import json, sys
import numpy as np

path = sys.argv[1] if len(sys.argv) > 1 else \
    "/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/runs/fusion_neutral_apply/pairs_u1_28.json"
d = json.load(open(path))
P = np.asarray(d["pairs"], dtype=np.float64)
print("meta:", d.get("meta"))
print("npairs raw:", len(P))

X = P[:, 0:3]   # input  (full-res demosaicked, 2x2 block averaged)
Y = P[:, 3:6]   # output (half-res, color transformed)

# keep well-conditioned, non-degenerate samples
m = (X > 1e-4).all(1) & (Y > -1e3).all(1) & np.isfinite(X).all(1) & np.isfinite(Y).all(1)
X, Y = X[m], Y[m]
print("npairs used:", len(X))
print("mean in :", X.mean(0), " R/G=%.4f B/G=%.4f" % (X[:,0].mean()/X[:,1].mean(), X[:,2].mean()/X[:,1].mean()))
print("mean out:", Y.mean(0), " R/G=%.4f B/G=%.4f" % (Y[:,0].mean()/Y[:,1].mean(), Y[:,2].mean()/Y[:,1].mean()))

def rep(name, pred):
    err = pred - Y
    rel = np.abs(err).sum() / np.abs(Y).sum()
    rms = np.sqrt((err**2).mean())
    print("  %-28s relL1=%.5f  rms=%.6g" % (name, rel, rms))
    return rel

print("\n--- linear 3x3 : out = A . in ---")
A, *_ = np.linalg.lstsq(X, Y, rcond=None)   # X@A = Y  => A is 3x3 acting on rows
A = A.T                                      # so out = A @ in  (column convention)
np.set_printoptions(precision=8, suppress=True)
print("A (out = A @ in) =\n", A)
print("row sums:", A.sum(1))
rep("3x3", (A @ X.T).T)

print("\n--- affine 3x4 : out = A.in + b ---")
X1 = np.hstack([X, np.ones((len(X), 1))])
Aa, *_ = np.linalg.lstsq(X1, Y, rcond=None)
Aa = Aa.T
print("A|b =\n", Aa)
rep("3x4", (Aa[:, :3] @ X.T).T + Aa[:, 3])

print("\n--- diagonal : out = diag(g) . in ---")
g = (X * Y).sum(0) / (X * X).sum(0)
print("g =", g)
rep("diag", X * g)

print("\n--- per-channel power law : out_c = a_c * in_c^p_c ---")
for c in range(3):
    xs, ys = X[:, c], Y[:, c]
    k = (xs > 1e-3) & (ys > 1e-6)
    lx, ly = np.log(xs[k]), np.log(ys[k])
    p, la = np.polyfit(lx, ly, 1)
    print("  ch%d: a=%.6f p=%.6f  (n=%d)" % (c, np.exp(la), p, k.sum()))

np.save(path.replace(".json", "_A.npy"), A)
print("\nsaved A ->", path.replace(".json", "_A.npy"))
