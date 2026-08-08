"""Lumen Bayer stage 2 'highlight restore' (libcp 0x343e10) runtime probe.

Static facts already established:
  0x343e10  ROI wrapper.  rbx = stage ctx.
            rcx = [rbx];  rdx = [rcx + 0x198]  (parameter block)
            xmm0 = PARAM_A = [rdx + 0x4]
            xmm1 = PARAM_B = [rdx + 0x8]
            rdi = &dst view (rbp-0x70), rsi = &src view (rbp-0x40),
            rdx = phase pair (2 x i32) from 0xf2750
            call 0x30b770  @ 0x343ef8 ; returns dst at rbp-0x70
  view layout: +0x10 w, +0x14 h, +0x18 stride(px), +0x20 u16* base
  0x30b9f0  phase-(0,0) kernel; r9 = const float[3] (per-channel vector)
"""
import builtins
import json
import struct

ROW_STEP = 8          # sample every Nth row for stats
MAX_PAIRS = 6000      # paired src/dst samples per invocation
DUMP_DIR = None       # set by reset(); full-tile dumps land here
DUMP_MIN_SAT = 0.02   # dump tiles whose src frac>=1020 exceeds this
DUMP_MAX = 6          # at most this many tiles dumped


def reset(label, outpath, dumpdir=None):
    global DUMP_DIR
    DUMP_DIR = dumpdir
    builtins.l16_hr = {"label": label, "out": outpath, "hits": [], "kernel": [],
                       "errors": [], "pending": {}, "dumps": []}


def _st():
    return builtins.l16_hr


def _u(frame, name):
    r = frame.FindRegister(name)
    return r.GetValueAsUnsigned() if r.IsValid() else None


def _xmm_f0(frame, name):
    import lldb
    r = frame.FindRegister(name)
    if not r.IsValid():
        return None
    e = lldb.SBError()
    b = r.GetData().ReadRawData(e, 0, 4)
    if not e.Success():
        return None
    return struct.unpack("<f", b)[0]


def _rd(proc, addr, n):
    import lldb
    e = lldb.SBError()
    if not addr or n <= 0:
        return None
    d = proc.ReadMemory(addr, n, e)
    if not e.Success() or len(d) != n:
        return None
    return d


def _view(proc, addr):
    d = _rd(proc, addr, 0x30)
    if d is None:
        return None
    return dict(w=struct.unpack_from("<i", d, 0x10)[0],
                h=struct.unpack_from("<i", d, 0x14)[0],
                stride=struct.unpack_from("<i", d, 0x18)[0],
                ptr=struct.unpack_from("<Q", d, 0x20)[0],
                raw=d.hex())


def _rows(proc, v):
    out = {}
    if not v or v["w"] <= 0 or v["h"] <= 0 or not v["ptr"]:
        return out
    nb = v["w"] * 2
    for y in range(0, v["h"], ROW_STEP):
        b = _rd(proc, v["ptr"] + 2 * v["stride"] * y, nb)
        if b is None:
            break
        out[y] = b
    return out


def _plane(proc, v):
    """Read the full w*h plane, packed tightly (stride removed)."""
    if not v or v["w"] <= 0 or v["h"] <= 0 or not v["ptr"]:
        return None
    nb = v["w"] * 2
    out = bytearray()
    for y in range(v["h"]):
        b = _rd(proc, v["ptr"] + 2 * v["stride"] * y, nb)
        if b is None:
            return None
        out += b
    return bytes(out)


def _stats(rows, w):
    n = 0
    s = 0
    mx = 0
    c1000 = 0
    c1020 = 0
    for b in rows.values():
        a = struct.unpack_from("<%dH" % w, b, 0)
        n += w
        s += sum(a)
        m = max(a)
        if m > mx:
            mx = m
        for v in a:
            if v >= 1000:
                c1000 += 1
                if v >= 1020:
                    c1020 += 1
    return dict(n=n, mean=(s / n if n else 0.0), max=mx,
                frac1000=(c1000 / n if n else 0.0),
                frac1020=(c1020 / n if n else 0.0))


def hit_params(frame, bp_loc, internal_dict):
    """BP @ 0x343ee3 : rdx = parameter block."""
    st = _st()
    try:
        proc = frame.GetThread().GetProcess()
        rdx = _u(frame, "rdx")
        blk = _rd(proc, rdx, 0x80)
        st["pending"][frame.GetThread().GetThreadID()] = dict(
            param_addr=rdx,
            param_f32=list(struct.unpack_from("<32f", blk)) if blk else None,
            param_hex=blk.hex() if blk else None)
    except Exception as ex:
        st["errors"].append("params: %r" % (ex,))
    return False


def hit_call(frame, bp_loc, internal_dict):
    """BP @ 0x343ef8 : just before call 0x30b770."""
    st = _st()
    try:
        proc = frame.GetThread().GetProcess()
        tid = frame.GetThread().GetThreadID()
        rec = st["pending"].get(tid, {})
        rec["seq"] = len(st["hits"])
        rec["tid"] = tid
        rec["A"] = _xmm_f0(frame, "xmm0")
        rec["B"] = _xmm_f0(frame, "xmm1")
        ph = _rd(proc, _u(frame, "rdx"), 8)
        rec["phase"] = list(struct.unpack("<2i", ph)) if ph else None
        # rcx (4th arg to 0x30b770) -> r14 -> kernel r9 = per-camera gain vec
        rcx = _u(frame, "rcx")
        cb = _rd(proc, rcx, 0x40)
        rec["cam_addr"] = rcx
        rec["cam"] = list(struct.unpack_from("<16f", cb)) if cb else None
        src = _view(proc, _u(frame, "rsi"))
        rec["src"] = src
        rows = _rows(proc, src)
        rec["src_stats"] = _stats(rows, src["w"]) if src else None
        rec["_srcrows"] = rows
        st["pending"][tid] = rec
    except Exception as ex:
        st["errors"].append("call: %r" % (ex,))
    return False


def hit_ret(frame, bp_loc, internal_dict):
    """BP @ 0x343efd : dst view is at [rbp-0x70]."""
    st = _st()
    try:
        proc = frame.GetThread().GetProcess()
        tid = frame.GetThread().GetThreadID()
        rec = st["pending"].pop(tid, None)
        if rec is None:
            st["errors"].append("ret without call on tid %s" % tid)
            return False
        rbp = _u(frame, "rbp")
        dst = _view(proc, rbp - 0x70)
        rec["dst"] = dst
        drows = _rows(proc, dst)
        rec["dst_stats"] = _stats(drows, dst["w"]) if dst else None
        srows = rec.pop("_srcrows", {})
        pairs = []
        dark = []
        if dst and rec.get("src") and dst["w"] == rec["src"]["w"]:
            w = dst["w"]
            for y in sorted(srows):
                if y not in drows:
                    continue
                sa = struct.unpack_from("<%dH" % w, srows[y], 0)
                da = struct.unpack_from("<%dH" % w, drows[y], 0)
                for x in range(0, w, 3):
                    sv, dv = sa[x], da[x]
                    if sv >= 700 or dv != sv:
                        if len(pairs) < MAX_PAIRS:
                            pairs.append((x, y, sv, dv))
                    elif len(dark) < 400 and (x % 300 == 0):
                        dark.append((x, y, sv, dv))
                if len(pairs) >= MAX_PAIRS:
                    break
        rec["pairs"] = pairs
        rec["dark"] = dark
        rec["n_changed"] = sum(1 for p in pairs if p[2] != p[3])
        # --- full-tile dump for formula fitting ---
        ss = rec.get("src_stats") or {}
        if (DUMP_DIR and dst and rec.get("src")
                and len(st["dumps"]) < DUMP_MAX
                and ss.get("frac1020", 0.0) >= DUMP_MIN_SAT):
            import os
            idx = len(st["dumps"])
            sv, dv = rec["src"], dst
            sb = _plane(proc, sv)
            db = _plane(proc, dv)
            if sb and db:
                os.makedirs(DUMP_DIR, exist_ok=True)
                sp = os.path.join(DUMP_DIR, "tile%02d_src.u16" % idx)
                dp = os.path.join(DUMP_DIR, "tile%02d_dst.u16" % idx)
                open(sp, "wb").write(sb)
                open(dp, "wb").write(db)
                st["dumps"].append(dict(idx=idx, src=sp, dst=dp,
                                        w=sv["w"], h=sv["h"],
                                        dw=dv["w"], dh=dv["h"],
                                        phase=rec.get("phase"),
                                        cam=rec.get("cam"),
                                        cam_addr=rec.get("cam_addr"),
                                        A=rec.get("A"), B=rec.get("B"),
                                        src_stats=ss))
                rec["dump"] = idx
        st["hits"].append(rec)
    except Exception as ex:
        st["errors"].append("ret: %r" % (ex,))
    return False


def hit_kernel(frame, bp_loc, internal_dict):
    """BP @ 0x30ba48 : xmm6 = [r9]; capture the 3-float vector."""
    st = _st()
    if len(st["kernel"]) >= 8:
        try:
            bp_loc.GetBreakpoint().SetEnabled(False)
        except Exception:
            pass
        return False
    try:
        proc = frame.GetThread().GetProcess()
        r9 = _u(frame, "r9")
        b = _rd(proc, r9, 0x40)
        st["kernel"].append(dict(
            r9=r9,
            f32=list(struct.unpack_from("<16f", b)) if b else None,
            hex=b.hex() if b else None,
            A=_xmm_f0(frame, "xmm0"),
            rdi=_u(frame, "rdi"), rsi=_u(frame, "rsi"),
            rdx=_u(frame, "rdx"), rcx=_u(frame, "rcx"), r8=_u(frame, "r8")))
    except Exception as ex:
        st["errors"].append("kernel: %r" % (ex,))
    return False


def drive(debugger, cap=400000):
    """Keep the inferior running until it exits, whatever stops it."""
    import lldb
    proc = debugger.GetSelectedTarget().GetProcess()
    n = 0
    while proc.IsValid() and proc.GetState() == lldb.eStateStopped and n < cap:
        proc.Continue()
        n += 1
    print("drive: continues=%d state=%s" % (n, proc.GetState()))


def report():
    st = _st()
    out = st["out"]
    with open(out, "w") as f:
        json.dump(dict(label=st["label"], hits=st["hits"], dumps=st["dumps"],
                       kernel=st["kernel"], errors=st["errors"]), f)
    print("dumps:", len(st["dumps"]))
    for d in st["dumps"]:
        print("  DUMP", d["idx"], d["w"], d["h"], "phase", d["phase"],
              "sat", round(d["src_stats"]["frac1020"], 4))
    print("L16_HR_BEGIN")
    print("label:", st["label"], " hits:", len(st["hits"]),
          " kernel:", len(st["kernel"]), " errors:", len(st["errors"]))
    for e in st["errors"][:10]:
        print("  ERR", e)
    for k in st["kernel"][:3]:
        print("  KERNEL r9=%#x f32[0:6]=%s" % (k["r9"], k["f32"][:6]))
    for h in st["hits"]:
        print("  hit %2d tid=%s A=%s B=%s phase=%s" %
              (h.get("seq"), h.get("tid"), h.get("A"), h.get("B"), h.get("phase")))
        p = h.get("param_f32") or []
        print("       param[0:12]=%s" % ([round(v, 6) for v in p[:12]],))
        print("       src %s  stats=%s" %
              ({k: h["src"][k] for k in ("w", "h", "stride")} if h.get("src") else None,
               h.get("src_stats")))
        print("       dst stats=%s  n_changed=%s/%s" %
              (h.get("dst_stats"), h.get("n_changed"), len(h.get("pairs") or [])))
        for pr in (h.get("pairs") or [])[:12]:
            print("         pair x=%d y=%d src=%d dst=%d" % pr)
    print("L16_HR_END")
    print("wrote", out)
