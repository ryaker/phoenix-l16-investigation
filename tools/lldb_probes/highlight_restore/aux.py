"""Capture the AUX plane row that gates Lumen's highlight-restore kernel.

BP at libcp.dylib 0x30bdd0 == just after `call 0x314d50([rbp-0x2a0], r13)`
inside the phase-(0,0) kernel 0x30b9f0.

At that point:
  rax          = aux row pointer (u16*)
  r13          = row index within the tile
  [rbp-0x128]  = src row pointer for the SAME row (u16*)
  [rbp-0x294]  = tile width  (i32)
  [rbp-0x2b4]  = tile height (i32)
"""
import struct, json, builtins

MAX_ROWS = 60


def reset(outpath):
    builtins.l16_aux = {"out": outpath, "rows": [], "errors": []}


def _u64(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _stack(proc, frame, off, n=8):
    rbp = _u64(frame, "rbp")
    err = __import__("lldb").SBError()
    b = proc.ReadMemory(rbp - off, n, err)
    if not err.Success():
        return None
    return b


def hit(frame, bp_loc, internal_dict):
    import lldb
    st = builtins.l16_aux
    if len(st["rows"]) >= MAX_ROWS:
        try:
            bp_loc.GetBreakpoint().SetEnabled(False)
        except Exception:
            pass
        return False
    try:
        proc = frame.GetThread().GetProcess()
        aux = _u64(frame, "rax")
        row = _u64(frame, "r13") & 0xFFFFFFFF
        sb = _stack(proc, frame, 0x128, 8)
        wb = _stack(proc, frame, 0x294, 4)
        hb = _stack(proc, frame, 0x2B4, 4)
        if sb is None or wb is None or hb is None:
            return False
        src = struct.unpack("<Q", sb)[0]
        w = struct.unpack("<i", wb)[0]
        h = struct.unpack("<i", hb)[0]
        if w <= 0 or w > 4096:
            return False
        err = lldb.SBError()
        a = proc.ReadMemory(aux, 2 * w, err)
        if not err.Success():
            return False
        s = proc.ReadMemory(src, 2 * w, err)
        if not err.Success():
            return False
        av = list(struct.unpack("<%dH" % w, a))
        sv = list(struct.unpack("<%dH" % w, s))
        nb = {}
        for off, key in ((0x80, "m4"), (0x78, "m3"), (0x70, "m2"), (0x68, "m1"),
                         (0x58, "p1"), (0x50, "p2"), (0x48, "p3"), (0x40, "p4"),
                         (0x38, "p5")):
            pb = _stack(proc, frame, off, 8)
            if pb is None:
                continue
            p = struct.unpack("<Q", pb)[0]
            if p == 0:
                continue
            e2 = lldb.SBError()
            m = proc.ReadMemory(p, 2 * w, e2)
            if e2.Success():
                nb[key] = list(struct.unpack("<%dH" % w, m))
        st["rows"].append(dict(row=row, w=w, h=h, aux=av, src=sv, nb=nb,
                               aux_ptr=aux, src_ptr=src))
    except Exception as e:
        st["errors"].append(repr(e))
    return False


def drive(debugger, cap=2000000):
    import lldb
    proc = debugger.GetSelectedTarget().GetProcess()
    n = 0
    while proc.GetState() == lldb.eStateStopped and n < cap:
        proc.Continue()
        n += 1
    print("L16_AUX drive iterations=%d state=%d" % (n, proc.GetState()))


def report():
    st = builtins.l16_aux
    with open(st["out"], "w") as f:
        json.dump(st, f)
    print("L16_AUX_BEGIN")
    print("rows captured: %d  errors: %d" % (len(st["rows"]), len(st["errors"])))
    for e in st["errors"][:5]:
        print("  err", e)
    for r in st["rows"][:6]:
        a, s = r["aux"], r["src"]
        w = r["w"]
        same = sum(1 for i in range(w) if a[i] == s[i])
        print("row=%d w=%d h=%d  aux==src %d/%d  auxmax=%d srcmax=%d auxmin=%d srcmin=%d"
              % (r["row"], w, r["h"], same, w, max(a), max(s), min(a), min(s)))
        print("  aux[0:24]=", a[:24])
        print("  src[0:24]=", s[:24])
    print("L16_AUX_END")
