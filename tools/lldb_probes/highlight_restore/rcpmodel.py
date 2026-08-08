"""Does emulating x86 rcpps/rsqrtps (12-bit approximations) close the +-1 DN
residual between hr_ref and Lumen's captured tiles?

Lumen's kernel uses rcpss/rcpps/rsqrtps throughout; hr_ref currently uses exact
IEEE division.  Relative error of the hardware ops is <= 1.5*2^-12, which is
exactly the size of the observed residual, so this is the prime suspect.
"""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hr_ref

F32 = np.float32
R = "/Users/ryaker/Dev/L16_Lumen_ReverseEngineering/runs/highlight_restore"


def quant(y, bits, mode):
    """Keep `bits` explicit mantissa bits of the f32 y."""
    u = np.asarray(y, F32).view(np.uint32).astype(np.uint64)
    drop = np.uint64(23 - bits)
    if mode == "trunc":
        u = (u >> drop) << drop
    else:  # round to nearest even-ish
        half = np.uint64(1) << (drop - np.uint64(1))
        u = ((u + half) >> drop) << drop
    return u.astype(np.uint32).view(np.float32)


MODES = {
    "exact":      (lambda x: F32(1.0) / x,
                   lambda x: F32(1.0) / np.sqrt(x)),
    "trunc12":    (lambda x: quant(F32(1.0) / x, 12, "trunc"),
                   lambda x: quant(F32(1.0) / np.sqrt(x), 12, "trunc")),
    "round12":    (lambda x: quant(F32(1.0) / x, 12, "round"),
                   lambda x: quant(F32(1.0) / np.sqrt(x), 12, "round")),
    "round11":    (lambda x: quant(F32(1.0) / x, 11, "round"),
                   lambda x: quant(F32(1.0) / np.sqrt(x), 11, "round")),
    "round14":    (lambda x: quant(F32(1.0) / x, 14, "round"),
                   lambda x: quant(F32(1.0) / np.sqrt(x), 14, "round")),
}

meta = json.load(open(os.path.join(R, "u1_35.json")))["dumps"]
M = hr_ref.M
which = [int(a) for a in sys.argv[1:]] or [0, 2]

for name, (rc, rs) in MODES.items():
    hr_ref.rcp = rc
    hr_ref.rsqrt = rs
    line = []
    for d in meta:
        if d["idx"] not in which:
            continue
        w, h = d["w"], d["h"]
        src = np.fromfile(d["src"], np.uint16).reshape(h, w)
        dst = np.fromfile(d["dst"], np.uint16).reshape(h, w)
        ctx = hr_ref.make_ctx(np.asarray(d["cam"][:4], F32))
        out = hr_ref.restore_tile(src, tuple(d["phase"]), ctx)
        diff = np.abs(out[M:h - M, M:w - M].astype(np.int64)
                      - dst[M:h - M, M:w - M].astype(np.int64))
        line.append("t%d exact=%.4f%% max=%d" %
                    (d["idx"], 100.0 * (diff == 0).mean(), int(diff.max())))
    print("%-9s %s" % (name, "  ".join(line)))
