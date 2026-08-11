"""renderroi_h_probe.py -- identify lt::TileCache<unsigned char>::renderROI<h>
per-tile (level,x,y) lambda (body 0x3d85f0) as producer or reader of the byte
weight tiles, and capture the invoking-stage backtrace + captured-lambda state.
"""
import builtins, json, os, struct

BODY = 0x3d85f0   # renderROI<h> per-tile lambda operator() body


def reset(label="", report_path="", cap=4):
    builtins.l16_rr = {"label": label, "report_path": report_path, "cap": cap,
                       "hits": 0, "events": [], "bp_ids": {}, "errors": []}

def _s():
    if not hasattr(builtins, "l16_rr"): reset()
    return builtins.l16_rr

def _u(f, n): return f.FindRegister(n).GetValueAsUnsigned()

def _read(proc, a, n):
    if not a or a < 0x1000 or a > 0x00007FFFFFFFFFFF: return None
    lldb = builtins.__import__("lldb"); e = lldb.SBError()
    try: d = proc.ReadMemory(a, n, e)
    except Exception: return None
    return d if e.Success() and d and len(d) == n else None

def _q(proc, a):
    d = _read(proc, a, 8); return struct.unpack("<Q", d)[0] if d else 0

def _base(t):
    for m in t.module_iter():
        if str(m.GetFileSpec().GetFilename()) == "libcp.dylib":
            b = m.GetObjectFileHeaderAddress().GetLoadAddress(t)
            if b != 0xFFFFFFFFFFFFFFFF: return b
    return None

def _va(t, a):
    b = _base(t); return (a - b) if (b is not None and b <= a < b + 0x900000) else None

def _cstr(proc, a, n=200):
    out = b""
    for _ in range(n):
        c = _read(proc, a + len(out), 1)
        if not c or c == b"\x00": break
        out += c
    return out.decode("utf-8", "replace")

def _rtti(proc, obj):
    if not obj: return None
    vt = _q(proc, obj)
    if not vt: return None
    ti = _q(proc, vt - 8)
    if not ti: return {"vtable": hex(vt), "name": None}
    nm = _q(proc, ti + 8)
    return {"vtable": hex(vt), "name": _cstr(proc, nm) if nm else None}

def _img(proc, a):
    raw = _read(proc, a, 0x28)
    if not raw: return None
    w, h, stride = struct.unpack_from("<iii", raw, 0x10)
    data = struct.unpack_from("<Q", raw, 0x20)[0]
    if not (0 < w < 30000 and 0 < h < 30000 and 0 < stride < 200000): return None
    o = {"w": w, "h": h, "stride": stride, "data": hex(data)}
    u8 = _read(proc, data, 24)
    if u8: o["u8"] = list(u8)
    return o

def _scan(proc, t, base, span=0x80):
    out = []
    for off in range(0, span, 8):
        v = _q(proc, base + off)
        if not v or v < 0x1000 or v > 0x00007FFFFFFFFFFF: continue
        e = {"off": hex(off), "ptr": hex(v)}
        va = _va(t, v)
        if va is not None: e["libcp_va"] = hex(va)
        rt = _rtti(proc, v)
        if rt and rt.get("name"): e["rtti"] = rt
        im = _img(proc, v)
        if im: e["as_image"] = im
        out.append(e)
    return out

def body(frame, _l, _d):
    st = _s(); st["hits"] += 1
    proc = frame.GetThread().GetProcess(); t = proc.GetTarget()
    this = _u(frame, "rdi")            # captured lambda (already this+8 from thunk)
    lvl = _u(frame, "rsi"); xarg = _u(frame, "rdx")
    th = frame.GetThread()
    bt = []
    for i in range(min(20, th.GetNumFrames())):
        v = _va(t, th.GetFrameAtIndex(i).GetPC())
        bt.append(hex(v) if v is not None else th.GetFrameAtIndex(i).GetFunctionName())
    ev = {"hit": st["hits"], "this": hex(this),
          "arg_level_ptr": hex(lvl), "arg_x_ptr": hex(xarg),
          "level": struct.unpack("<i", _read(proc, lvl, 4))[0] if _read(proc, lvl, 4) else None,
          "x": struct.unpack("<i", _read(proc, xarg, 4))[0] if _read(proc, xarg, 4) else None,
          "captured_fields": _scan(proc, t, this, 0xa0),
          "backtrace_va": bt}
    st["events"].append(ev)
    if st["hits"] >= int(st["cap"]): proc.Kill()
    return False

def install(debugger):
    st = _s(); t = debugger.GetSelectedTarget(); b = t.GetNumBreakpoints()
    debugger.HandleCommand("breakpoint set --shlib libcp.dylib --address 0x3d85f0")
    if t.GetNumBreakpoints() > b:
        bp = t.GetBreakpointAtIndex(t.GetNumBreakpoints() - 1)
        bp.SetScriptCallbackFunction("renderroi_h_probe.body")
        st["bp_ids"]["body"] = bp.GetID()
    print("RR_INSTALLED", st["bp_ids"])

def drive(debugger, max_steps=400000):
    lldb = builtins.__import__("lldb"); proc = debugger.GetSelectedTarget().GetProcess(); n = 0
    while proc.IsValid() and proc.GetState() == lldb.eStateStopped and n < max_steps:
        n += 1; proc.Continue()
    print("RR_DRIVE", n)

def write_report(debugger, path=""):
    out = path or _s().get("report_path"); os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as h: json.dump(dict(_s()), h, indent=2, sort_keys=True, default=str)
    print("RR_WROTE", out)
