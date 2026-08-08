#!/usr/bin/env python3
import numpy as np, itertools
np.set_printoptions(precision=6, suppress=True)

g = np.array([0.58212674, 1.0, 0.62939054])          # gains as supplied to demosaic driver
M = np.array([[ 0.82463306,  0.16996610, -0.03037914],
              [ 0.25420183,  1.09188354, -0.34608528],
              [-0.11276632, -0.53306979,  1.47104609]])
PP = np.array([[0.79767489, 0.13519169, 0.03135340],
               [0.28804019, 0.71187413, 0.00008570],
               [0.0,        0.0,        0.82520998]])
print("M row sums   ", M.sum(1))
print("PP row sums  ", PP.sum(1))
print("PP^-1 . M  (=> the pure CCM, rows should sum ~1):\n", np.linalg.inv(PP) @ M)
print("   row sums", (np.linalg.inv(PP) @ M).sum(1))

raw   = np.array([0.5249, 1.0, 0.6471])   # anchor-cam Bayer means, black-subtracted
master= np.array([0.5521, 1.0, 0.6330])   # Lumen ca.hdr global mean chroma
phxna = np.array([0.5248, 1.0, 0.6079])   # Phoenix PHX_NO_AWB render
print("\nraw    ", raw, "\nmaster ", master, "\nphx_noawb", phxna)

def chroma(v): return np.array([v[0]/v[1], 1.0, v[2]/v[1]])
def err(v, t=master):
    c = chroma(v); return np.abs(c-t)[[0,2]] / t[[0,2]]

Minv = np.linalg.inv(M)
cands = {
 "raw (identity)"          : raw,
 "raw*g"                   : raw*g,
 "raw/g"                   : raw/g,
 "M.raw"                   : M@raw,
 "M.(raw*g)"               : M@(raw*g),
 "M.(raw/g)"               : M@(raw/g),
 "Minv.raw"                : Minv@raw,
 "Minv.(raw*g)"            : Minv@(raw*g),
 "PPinv.M.(raw*g)"         : np.linalg.inv(PP)@M@(raw*g),
 "PPinv.M.raw"             : np.linalg.inv(PP)@M@raw,
 "phx_noawb (identity)"    : phxna,
 "M.phx_noawb"             : M@phxna,
 "Minv.phx_noawb"          : Minv@phxna,
 "PPinv.M.phx_noawb"       : np.linalg.inv(PP)@M@phxna,
}
print("\n%-24s %-28s  errR%%   errB%%" % ("form","chroma (R/G,1,B/G)"))
for k,v in cands.items():
    c = chroma(v); e = err(v)*100
    print("%-24s %-28s %6.1f %6.1f" % (k, "(%.4f, 1, %.4f)"%(c[0],c[2]), e[0], e[1]))
