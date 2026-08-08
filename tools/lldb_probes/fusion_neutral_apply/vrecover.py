#!/usr/bin/env python3
"""Recover Lumen's ACTUAL applied vignetting gain map V(x,y) for unit-1 28mm A1.

From bundle_static_runtime_prefusion_monofusion_reference_public_origin_two_body:
    z   = float32(affine(x,y) * V(x,y))
    i   = clip(trunc_i32(z + 0.5), 1, 4095)
    L   = LUT[i] = trunc_u16(sqrt(i * 1023))

We hold `affine` (a1_reference_affine.f32le) and `L`
(a1_reference_level0.u16le) verbatim out of Lumen's address space, so V is
recoverable per pixel up to the LUT quantisation.  affine is clamped at 981,
so only unclamped, well-exposed pixels are used.
"""
import numpy as np, os

BASE = "/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/runs/prefusion_monofusion_flow_origin/unit1_28mm_reference_operand"
W, H = 4160, 3120

aff = np.fromfile(os.path.join(BASE, "a1_reference_affine.f32le"),
                  dtype="<f4").astype(np.float64).reshape(H, W)
lut_out = np.fromfile(os.path.join(BASE, "a1_reference_level0.u16le"),
                      dtype="<u2").astype(np.float64).reshape(H, W)

# invert LUT: L = trunc(sqrt(i*1023))  =>  i in [L^2/1023, ((L+1)^2-1)/1023]
lo = (lut_out ** 2) / 1023.0
hi = ((lut_out + 1.0) ** 2 - 1.0) / 1023.0
i_est = 0.5 * (lo + hi)

# usable: affine unclamped and bright enough that LUT quantisation is small
m = (aff > 80.0) & (aff < 960.0) & (i_est < 4090.0)
print("usable pixels: %d / %d (%.2f%%)" % (m.sum(), m.size, 100.0 * m.sum() / m.size))

V = np.full((H, W), np.nan)
V[m] = i_est[m] / aff[m]
print("V  mean=%.6f  min=%.6f  max=%.6f  med=%.6f" %
      (np.nanmean(V), np.nanmin(V), np.nanmax(V), np.nanmedian(V)))

# Sample V on a coarse grid to expose its spatial shape.
print("\nV sampled on a 9x7 grid (x across, y down), '.' = insufficient data:")
xs = np.linspace(0, W - 1, 9).astype(int)
ys = np.linspace(0, H - 1, 7).astype(int)
hdr = "      " + "".join("%9d" % x for x in xs)
print(hdr)
R = 40
for y in ys:
    row = "%5d " % y
    for x in xs:
        y0, y1 = max(0, y - R), min(H, y + R)
        x0, x1 = max(0, x - R), min(W, x + R)
        blk = V[y0:y1, x0:x1]
        n = np.count_nonzero(~np.isnan(blk))
        row += ("%9.4f" % np.nanmedian(blk)) if n > 200 else "        ."
    print(row)

# Median V per full-frame mean, restricted to the well-behaved centre band, to
# give a robust global gain the master comparison can use.
cy0, cy1 = H // 2 - 400, H // 2 + 400
cx0, cx1 = W // 2 - 400, W // 2 + 400
print("\ncentre 800x800 median V = %.6f" % np.nanmedian(V[cy0:cy1, cx0:cx1]))
print("corner 400x400 (0,0)   median V = %.6f" % np.nanmedian(V[0:400, 0:400]))
print("corner 400x400 (max)   median V = %.6f" % np.nanmedian(V[H-400:H, W-400:W]))

np.save("/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/runs/verify_master/u1_28_A1_V.npy",
        V.astype(np.float32))
print("\nsaved runs/verify_master/u1_28_A1_V.npy")
