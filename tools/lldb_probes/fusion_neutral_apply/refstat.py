#!/usr/bin/env python3
"""Channel statistics for the installed Lumen A1 reference operands.

These files were captured by Codex (bundle_corrective_static_runtime_
demosaicklightv1_fullframe_two_body.md) directly out of Lumen's own address
space on the unit-1 28mm canonical shot.  They therefore give Lumen's true
demosaic-stage levels with no new lldb cost.
"""
import numpy as np, os, sys

BASE = "/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/runs/prefusion_monofusion_flow_origin/unit1_28mm_reference_operand"
W, H = 4160, 3120


def stat(name, a):
    a = a.astype(np.float64)
    print("%-26s n=%-10d min=%-12.6g max=%-12.6g mean=%-12.8g med=%-12.6g" %
          (name, a.size, a.min(), a.max(), a.mean(), np.median(a)))


def main():
    p = os.path.join(BASE, "a1_reference_level0.u16le")
    u = np.fromfile(p, dtype="<u2")
    print("== level0 u16 (raw bayer, %d px) ==" % u.size)
    stat("level0.u16", u)
    # CFA phase means (assume 2x2 tiling over W x H)
    g = u.reshape(H, W)
    for (dy, dx, tag) in ((0, 0, "p00"), (0, 1, "p01"), (1, 0, "p10"), (1, 1, "p11")):
        stat("level0." + tag, g[dy::2, dx::2])

    for fn in ("a1_demosaic_input.f32le", "a1_reference_scalar.f32le",
               "a1_reference_affine.f32le"):
        p = os.path.join(BASE, fn)
        a = np.fromfile(p, dtype="<f4")
        print("== %s (%d words) ==" % (fn, a.size))
        stat(fn, a)
        if a.size == W * H:
            gg = a.reshape(H, W)
            for (dy, dx, tag) in ((0, 0, "p00"), (0, 1, "p01"),
                                  (1, 0, "p10"), (1, 1, "p11")):
                stat(fn + "." + tag, gg[dy::2, dx::2])

    p = os.path.join(BASE, "a1_reference_source.f32x4le")
    a = np.fromfile(p, dtype="<f4")
    print("== a1_reference_source.f32x4le (%d words = %d px x4) ==" %
          (a.size, a.size // 4))
    a = a.reshape(-1, 4)
    for c, tag in enumerate("RGBA"):
        stat("source." + tag, a[:, c])


main()
