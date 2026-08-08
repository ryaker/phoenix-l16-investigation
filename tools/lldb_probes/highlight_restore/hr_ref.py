"""Clean-room numpy reference for Lumen's Bayer highlight-restore stage.

Derived entirely from libcp.dylib kernel 0x30b9f0 (phase 0,0) + 0x30cce7
(odd-row block) and runtime-measured constants (runs/highlight_restore/
consts_u1_35.json, aux_u1_35.json).

Ground truth for verification: runs/highlight_restore/tiles/tileNN_{src,dst}.u16
"""
import numpy as np

F32 = np.float32

# --- runtime-measured constants -------------------------------------------
A = F32(42.0)              # black level          [rbp-0x170]
B = F32(1023.0)            # white level
GATE = 1007                # (int)(0.985*B)       [rbp-0x104]
Q_RED = 1854               # Q10(1/c0)            [rbp-0x134]
Q_BLUE = 1690              # Q10(1/c2)            [rbp-0x138]
LAP_FLOOR = -40            #                      [rbp-0x94]
WEPS = F32(0.009765625)    # weight epsilon       0x5f3e30 / 0x5f18cc
WSCALE = F32(0.0010193679481744766)   # 1/981     [rbp-0x1f0] / [rbp-0x1c0]
INV_C0 = F32(1.81064772605896)        #           [rbp-0x260] / [rbp-0x1d0]
INV_C2 = F32(1.650661587715149)       #           [rbp-0x270] / [rbp-0x1e0]
K3 = F32(3.0000100135803223)          # 0x5f3e28
KDIR = np.array([0.7688769698143005, 0.08443189412355423,
                 0.6337976455688477, 0.0], F32)   # [rbp-0xf0]
NEG09 = F32(-0.9)                                  # 0x5f3e40
THIRD = F32(1.0 / 3.0)                             # 0x5aae88

CAM = np.array([0.5522885322570801, 1.0, 0.6058176755905151, 0.0], F32)


def make_ctx(cam=CAM):
    """Everything the kernel derives from the per-camera gain vector r9.

    r9 = float[3] = (c0, c1=1, c2).  EVERY prologue constant is a function of
    it, so the six dumped tiles -- which come from different cameras -- need
    different ctx objects.  Using one camera's ctx for all of them was the
    entire source of the earlier 8-18% match rate.
    """
    c = np.asarray(cam, F32)
    inv0 = F32(1.0) / c[0]                # [rbp-0x260] / [rbp-0x1d0]
    inv2 = F32(1.0) / c[2]                # [rbp-0x270] / [rbp-0x1e0]
    ctx = {}
    ctx["c"] = c
    ctx["inv0"] = inv0
    ctx["inv2"] = inv2
    ctx["q_red"] = int(F32(1024.0) * inv0)    # [rbp-0x134]  (truncated)
    ctx["q_blue"] = int(F32(1024.0) * inv2)   # [rbp-0x138]
    ctx["norm"] = np.array([inv0 * WSCALE, WSCALE,
                            inv2 * WSCALE, 0.0], F32)          # [rbp-0xe0]
    ctx["k085"] = np.array([F32(0.85) * inv0, 0.85,
                            F32(0.85) * inv2, 0.0], F32)       # [rbp-0xd0]
    ctx["slope"] = np.array([F32(20.0 / 3.0) * c[0], F32(20.0 / 3.0) * c[1],
                             F32(20.0 / 3.0) * c[2], 0.0], F32)  # [rbp-0x180]
    ctx["denorm"] = np.array([F32(981.0) * c[0], 981.0,
                              F32(981.0) * c[2], 0.0], F32)
    ctx["c0_c1"] = F32(c[0] / c[1])       # [rbp-0x13c]
    ctx["c2_c1"] = F32(c[2] / c[1])       # [rbp-0x140]
    # unit direction [rbp-0xf0] = normalize((1/c0-0.9, 1-0.9, 1/c2-0.9))
    v = np.array([inv0 - F32(0.9), F32(0.1), inv2 - F32(0.9), 0.0], F32)
    ctx["kdir"] = (v / F32(np.sqrt(float(v[0])**2 + float(v[1])**2
                                   + float(v[2])**2))).astype(F32)
    return ctx


def rcp(x):
    return F32(1.0) / x


def rsqrt(x):
    return F32(1.0) / np.sqrt(x)


def dilate3(S):
    """AUX plane = 3x3 max filter of src (PROVEN, aux_u1_35 fit, 0 mismatch)."""
    P = np.pad(S, 1, mode="edge")
    out = P[0:-2, 0:-2]
    for dy in range(3):
        for dx in range(3):
            v = P[dy:dy + S.shape[0] + dy - dy, dx:dx + S.shape[1]]
            v = P[dy:dy + S.shape[0], dx:dx + S.shape[1]]
            out = np.maximum(out, v)
    return out


M = 4  # interior margin: taps reach +-3


def core(p, ctx):
    """Highlight core -- identical code in all four pixel blocks.

    p: (...,4) float32, normalised triple {R,G,B,0}.
    """
    w = (p - ctx["k085"]) * ctx["slope"]
    w = np.minimum(np.maximum(w, F32(0.0)), F32(1.0))
    S = w.sum(-1, dtype=F32)
    m = ((F32(1.0) - w) * p).sum(-1, dtype=F32) * rcp(K3 - S)
    r1 = p + w * (m[..., None] - p)
    r2 = p + np.minimum(S, F32(1.0))[..., None] * (np.maximum(p, r1) - p)
    r2 = r2.astype(F32)
    # 0x30c3f1: lane3 is zeroed before the max reduction
    maxc = np.maximum(np.maximum(np.maximum(r2[..., 0], r2[..., 1]),
                                 r2[..., 2]), F32(0.0))
    mean = (r2[..., 0] + r2[..., 1] + r2[..., 2]) * THIRD
    d = p + NEG09
    # 0x30c42a: blendps xmm4, xmm14, 0x8 -> lane3 of d is zeroed for n2
    n2 = (d[..., 0] * d[..., 0] + d[..., 1] * d[..., 1]
          + d[..., 2] * d[..., 2]).astype(F32)
    dot = ((d * rsqrt(n2)[..., None]) * ctx["kdir"]).sum(-1, dtype=F32)
    t = np.minimum(F32(1.0), np.maximum(F32(0.0), S - F32(1.0))) * \
        np.maximum(F32(0.0), dot)
    r3 = r2 + t[..., None] * (mean[..., None] - r2)
    u = np.maximum(S - F32(2.0), F32(0.0))
    return (r3 + u[..., None] * (maxc[..., None] - r3)).astype(F32)


class Grid(object):
    """Aligned shifted views of the source, all sized (H-2M, W-2M)."""

    def __init__(self, S):
        self.S = S
        self.H, self.W = S.shape

    def __call__(self, dy, dx):
        return self.S[M + dy:self.H - M + dy, M + dx:self.W - M + dx]


def ha_green(g, dy0, dx0, ratio, trunc):
    """Hamilton-Adams green estimate at a non-green pixel offset (dy0,dx0)."""
    C = g(dy0, dx0)
    hl = ((2 * C - g(dy0, dx0 - 2) - g(dy0, dx0 + 2)) * ratio) >> 10
    vl = ((2 * C - g(dy0 - 2, dx0) - g(dy0 + 2, dx0)) * ratio) >> 10
    gL = g(dy0, dx0 - 1); gR = g(dy0, dx0 + 1)
    gU = g(dy0 - 1, dx0); gD = g(dy0 + 1, dx0)
    cH = np.abs(hl) + np.abs(gR - gL)
    cV = np.abs(vl) + np.abs(gD - gU)
    h4 = np.maximum(hl, LAP_FLOOR) + 2 * (gL + gR)
    v4 = np.maximum(vl, LAP_FLOOR) + 2 * (gU + gD)
    sel = np.where(cH > cV, v4, h4)
    sel16 = np.where(sel < 0, 0, sel & 0xFFFF)
    if trunc:
        # green-centre blocks round-trip through cvttss2si/movzx
        return (sel16 >> 2).astype(F32)
    return sel16.astype(F32) * F32(0.25)


def wsum(gc, gs, vs, ratio):
    num = F32(0.0)
    den = F32(0.0)
    for gi, vi in zip(gs, vs):
        wi = rcp(np.abs(gi - gc) * WSCALE + WEPS)
        num = num + wi * (vi * ratio - gi)
        den = den + wi
    return num * rcp(den) + gc


def _finish(triple, lane, ctx):
    p = (triple + F32(-42.0)) * ctx["norm"]
    r = core(p.astype(F32), ctx)
    v = A + r[..., lane] * ctx["denorm"][lane]
    return np.trunc(v).astype(np.int64) & 0xFFFF


def restore_tile(src, phase, ctx=None, gc_scale=1.0):
    """phase = (py, px): pixel (y,x) is RED iff y%2==py and x%2==px."""
    if ctx is None:
        ctx = make_ctx()
    S = src.astype(np.int32)
    aux = dilate3(S)
    out = src.copy()
    g = Grid(S)
    H, W = S.shape
    Y, X = np.mgrid[M:H - M, M:W - M]
    py, px = phase
    gate = aux[M:H - M, M:W - M] >= GATE
    raw = g(0, 0).astype(F32)

    isR = (Y % 2 == py) & (X % 2 == px)
    isB = (Y % 2 != py) & (X % 2 != px)
    isGr = (Y % 2 == py) & (X % 2 != px)   # green on a red row
    isGb = (Y % 2 != py) & (X % 2 == px)   # green on a blue row

    res = np.zeros(raw.shape, np.int64)
    q_red, q_blue = ctx["q_red"], ctx["q_blue"]
    inv0, inv2 = ctx["inv0"], ctx["inv2"]

    # ---- RED centre ------------------------------------------------------
    gc = ha_green(g, 0, 0, q_red, False)
    diag = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    gs = [ha_green(g, dy, dx, q_blue, False) for dy, dx in diag]
    vs = [g(dy, dx).astype(F32) for dy, dx in diag]
    be = wsum(gc, gs, vs, inv2) * ctx["c2_c1"]
    tri = np.stack([raw, gc, be, np.zeros_like(raw)], -1)
    res = np.where(isR, _finish(tri, 0, ctx), res)

    # ---- BLUE centre -----------------------------------------------------
    gc = ha_green(g, 0, 0, q_blue, False)
    gs = [ha_green(g, dy, dx, q_red, False) for dy, dx in diag]
    re_ = wsum(gc, gs, vs, inv0) * ctx["c0_c1"]
    tri = np.stack([re_, gc, raw, np.zeros_like(raw)], -1)
    res = np.where(isB, _finish(tri, 2, ctx), res)

    # ---- GREEN centre ----------------------------------------------------
    gc = raw * F32(gc_scale)
    for mask, hq, vq in ((isGr, q_red, q_blue), (isGb, q_blue, q_red)):
        hn = [(0, -1), (0, 1)]
        vn = [(-1, 0), (1, 0)]
        gh = [ha_green(g, dy, dx, hq, True) for dy, dx in hn]
        gv = [ha_green(g, dy, dx, vq, True) for dy, dx in vn]
        vh = [g(dy, dx).astype(F32) for dy, dx in hn]
        vv = [g(dy, dx).astype(F32) for dy, dx in vn]
        if hq == q_red:
            rr = wsum(gc, gh, vh, inv0) * ctx["c0_c1"]
            bb = wsum(gc, gv, vv, inv2) * ctx["c2_c1"]
        else:
            bb = wsum(gc, gh, vh, inv2) * ctx["c2_c1"]
            rr = wsum(gc, gv, vv, inv0) * ctx["c0_c1"]
        tri = np.stack([rr, gc, bb, np.zeros_like(raw)], -1)
        res = np.where(mask, _finish(tri, 1, ctx), res)

    sub = out[M:H - M, M:W - M]
    sub[gate] = res[gate].astype(np.uint16)
    out[M:H - M, M:W - M] = sub
    return out
