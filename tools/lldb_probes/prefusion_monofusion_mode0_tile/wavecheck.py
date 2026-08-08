#!/usr/bin/env python3
"""Coherence + label test on Lumen's captured MonoFusion patch dumps.

Ports Phoenix's fwd2d/inv2d (installed 5/3 lifting lattice) and asks:
  1. fwd2d(patch_target_spatial)      ==  patch_target_coeff ?
  2. inv2d(patch_source_coeff_post)   ==  patch_source_spatial_post ?
  3. fwd2d(patch_source_spatial_post) ==  patch_source_coeff_post ?
If (1) holds, "target_spatial" and "target_coeff" are the SAME patch and the
probe's labels are internally consistent.  If (2)/(3) hold, the post buffers
pair up too.  Any failure means the dumps come from different patch iterations
and every conclusion drawn from mixing them is void.
"""
import numpy as np, os

BASE = ("/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/runs/"
        "prefusion_monofusion_mode0_tile/unit1_35mm")
kB = 16
S2 = np.float32(1.4142135381698608)
I2 = np.float32(0.7071067690849304)
I22 = np.float32(0.3535533845424652)
HALF = np.float32(0.4999999701976776)


def fwd1d(line, m):
    h = m // 2
    e = line[0:2 * h:2].copy(); o = line[1:2 * h:2].copy()
    d = np.empty(h, np.float32); s = np.empty(h, np.float32)
    for i in range(h):
        right = e[i + 1] if i + 1 < h else e[h - 1]
        d[i] = np.float32(o[i] * I2) - np.float32((np.float32(e[i] + right)) * I22)
    for i in range(h):
        left = d[i - 1] if i > 0 else d[0]
        s[i] = np.float32(S2 * e[i]) + np.float32(np.float32(left + d[i]) * HALF)
    line[0:2 * h:2] = s; line[1:2 * h:2] = d


def inv1d(line, m):
    h = m // 2
    s = line[0:2 * h:2].copy(); d = line[1:2 * h:2].copy()
    e = np.empty(h, np.float32); o = np.empty(h, np.float32)
    for i in range(h):
        left = d[i - 1] if i > 0 else d[0]
        e[i] = np.float32(s[i] * I2) - np.float32(np.float32(left + d[i]) * I22)
    for i in range(h):
        right = e[i + 1] if i + 1 < h else e[h - 1]
        o[i] = np.float32(S2 * d[i]) + np.float32(np.float32(e[i] + right) * HALF)
    line[0:2 * h:2] = e; line[1:2 * h:2] = o


def apply_line(p, base, stride, count, op):
    idx = base + np.arange(count) * stride
    line = p[idx].copy()
    op(line, count)
    p[idx] = line


def fwd2d(p):
    p = p.copy()
    for s in (1, 2, 4, 8):
        c = kB // s
        for yi in range(c):
            apply_line(p, (yi * s) * kB, s, c, fwd1d)
        for xi in range(c):
            apply_line(p, xi * s, s * kB, c, fwd1d)
    return p


def inv2d(p):
    p = p.copy()
    for s in (8, 4, 2, 1):
        c = kB // s
        for xi in range(c):
            apply_line(p, xi * s, s * kB, c, inv1d)
        for yi in range(c):
            apply_line(p, (yi * s) * kB, s, c, inv1d)
    return p


def ld(n):
    return np.fromfile(os.path.join(BASE, n), dtype="<f4")


ts, tc = ld("patch_target_spatial.f32le"), ld("patch_target_coeff.f32le")
ssp, scp = ld("patch_source_spatial_post.f32le"), ld("patch_source_coeff_post.f32le")
spre = ld("patch_source_coeff_pre.f32le")


def rep(tag, a, b):
    d = np.abs(a.astype(np.float64) - b.astype(np.float64))
    print("%-46s maxabs=%-14.6g rms=%-14.6g  scale=%.6g"
          % (tag, d.max(), np.sqrt((d * d).mean()), np.abs(b).max()))


rep("fwd2d(target_spatial) vs target_coeff", fwd2d(ts), tc)
rep("inv2d(source_coeff_post) vs source_spatial_post", inv2d(scp), ssp)
rep("fwd2d(source_spatial_post) vs source_coeff_post", fwd2d(ssp), scp)
rep("inv2d(source_coeff_pre) vs source_spatial_post", inv2d(spre), ssp)
rep("inv2d(target_coeff) vs target_spatial", inv2d(tc), ts)
print()
print("DC: target_coeff=%.6f source_pre=%.6f source_post=%.6f"
      % (tc[0], spre[0], scp[0]))
print("means: target_spatial=%.6f source_spatial_post=%.6f"
      % (ts.mean(), ssp.mean()))
print("fwd2d(constant 1) DC = %.8f" % fwd2d(np.ones(256, np.float32))[0])
