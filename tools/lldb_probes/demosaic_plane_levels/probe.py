"""DemosaickLightV1 driver (libcp+0x2eb560) plane-level probe.

Purpose: settle the per-shot achromatic scale between Lumen's fmt-3 master and
Phoenix's.  Phoenix reports its anchor demosaic-out mean in DN; this captures
Lumen's own demosaic INPUT plane mean and the supplied gain triplet for EVERY
module in the shot, so the two can be compared at the identical stage on the
identical pixels.

Register roles proven by static disassembly of 0x2eb560:
  rdi/r14 = destination, rsi/rbx = source descriptor, rdx/r12 = phase selector,
  rcx/r15 = color-params (floats [0..2] are the three supplied gains; the
  prologue rejects the call unless all three are > 0).
Descriptor layout (matches the proven post-square-scale probe):
  +0x10 W, +0x14 H, +0x18 stride (pixels), +0x20 data pointer.
"""
import builtins
import struct

ROWS = 48          # rows sampled per plane
COLS = 256         # samples per row


def reset(label):
    builtins.l16_dpl = {"label": label, "hits": [], "errors": []}


def _st():
    return builtins.l16_dpl


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _rd(proc, addr, n):
    import lldb
    e = lldb.SBError()
    d = proc.ReadMemory(addr, n, e)
    if not e.Success() or len(d) != n:
        return None
    return d


def _desc(proc, addr):
    d = _rd(proc, addr, 0x30)
    if d is None:
        return None
    return dict(addr=addr,
                w=struct.unpack_from("<i", d, 0x10)[0],
                h=struct.unpack_from("<i", d, 0x14)[0],
                stride=struct.unpack_from("<i", d, 0x18)[0],
                ptr=struct.unpack_from("<Q", d, 0x20)[0],
                raw=d.hex())


def _plane_stats(proc, desc, comps, fmt):
    """Sample ROWS x COLS elements. fmt 'f' = float32, 'H' = uint16."""
    w, h, st, p = desc["w"], desc["h"], desc["stride"], desc["ptr"]
    if not p or w <= 0 or h <= 0 or st <= 0:
        return None
    esz = 4 if fmt == "f" else 2
    row_bytes = st * comps * esz
    acc = [0.0] * comps
    n = 0
    mx = -1e30
    for i in range(ROWS):
        y = (i * h) // ROWS
        raw = _rd(proc, p + y * row_bytes, min(w, COLS) * comps * esz)
        if raw is None:
            continue
        cnt = len(raw) // esz
        vals = struct.unpack("<" + fmt * cnt, raw)
        for k in range(0, cnt - comps + 1, comps):
            for c in range(comps):
                v = float(vals[k + c])
                acc[c] += v
                if v > mx:
                    mx = v
            n += 1
    if not n:
        return None
    return dict(n=n, mean=[a / n for a in acc], max=mx)


def hit(frame, bp_loc, internal_dict):
    proc = frame.GetThread().GetProcess()
    r15 = _u(frame, "rcx")
    rbx = _u(frame, "rsi")
    r14 = _u(frame, "rdi")
    g = _rd(proc, r15, 16)
    gains = list(struct.unpack("<4f", g)) if g else None
    src = _desc(proc, rbx)
    rec = dict(gains=gains, src=src, dst_addr=r14,
               dst_head=(_rd(proc, r14, 0x30) or b"").hex())
    if src:
        rec["src_f32_1"] = _plane_stats(proc, src, 1, "f")
        rec["src_u16_1"] = _plane_stats(proc, src, 1, "H")
    _st()["hits"].append(rec)
    return False


def report():
    st = _st()
    print("L16_DPL_BEGIN", st["label"])
    for i, hh in enumerate(st["hits"]):
        s = hh.get("src") or {}
        print("hit %02d gains=%s  src %dx%d stride=%d ptr=0x%x" %
              (i, ["%.6f" % v for v in (hh["gains"] or [])[:3]],
               s.get("w", -1), s.get("h", -1), s.get("stride", -1), s.get("ptr", 0)))
        for k in ("src_f32_1", "src_u16_1"):
            v = hh.get(k)
            if v:
                print("     %-9s n=%d mean=%s max=%.6f" %
                      (k, v["n"], ["%.6f" % m for m in v["mean"]], v["max"]))
        print("     dst_head=%s" % hh.get("dst_head", "")[:96])
    print("hits", len(st["hits"]), "errors", st["errors"])
    print("L16_DPL_END", st["label"])
