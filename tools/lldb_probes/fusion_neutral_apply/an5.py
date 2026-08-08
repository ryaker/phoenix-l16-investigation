#!/usr/bin/env python3
import numpy as np, sys
d = sys.argv[1] if len(sys.argv)>1 else "/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/runs/fusion_neutral_apply/dump_u1_28"
np.set_printoptions(precision=6, suppress=True)

bay = np.fromfile(d+"/in_bayer_u16.raw", dtype="<u2").reshape(3120,4160)
pre = np.fromfile(d+"/pre_out_rgba16f.raw", dtype="<f2").reshape(1560,2080,4).astype(np.float64)
post= np.fromfile(d+"/post_out_rgba16f.raw",dtype="<f2").reshape(1560,2080,4).astype(np.float64)

print("== bayer u16 ==")
print(" min %d max %d mean %.2f" % (bay.min(), bay.max(), bay.mean()))
for (n,(a,b)) in zip("ph00 ph01 ph10 ph11".split(), [(0,0),(0,1),(1,0),(1,1)]):
    s = bay[a::2, b::2]
    print("  %s mean=%.3f  p1=%d p99=%d" % (n, s.mean(), np.percentile(s,1), np.percentile(s,99)))

print("\n== out half4 ==")
for nm,A in (("pre",pre),("post",post)):
    m = A.reshape(-1,4)
    print(" %s  mean=%s  max=%s  frac_nonzero=%.4f" % (nm, m.mean(0), m.max(0), (m[:,1]>0).mean()))
diff = np.abs(post-pre)
print(" |post-pre| max=%.6g  nchanged_px=%d / %d" % (diff.max(), (diff.max(2)>0).sum(), 1560*2080))
ch = diff.max(2)>0
if ch.any():
    ys,xs = np.nonzero(ch)
    print("  changed bbox y[%d..%d] x[%d..%d]" % (ys.min(),ys.max(),xs.min(),xs.max()))

g = post[:,:,1]
m = g>1e-5
print("\n post valid px: %d (%.3f)" % (m.sum(), m.mean()))
if m.sum():
    R,G,B,A = [post[:,:,c][m] for c in range(4)]
    print("  means R=%.6f G=%.6f B=%.6f A=%.6f   R/G=%.4f B/G=%.4f" %
          (R.mean(),G.mean(),B.mean(),A.mean(),R.mean()/G.mean(),B.mean()/G.mean()))
