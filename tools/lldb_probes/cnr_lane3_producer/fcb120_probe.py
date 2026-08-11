"""fcb120_probe.py -- resolve FusionCacheBayer+0x120 (float weight source) RTTI
and fields at the byte-tile generator 0x407710.  fcb = *(rdi+8).
"""
import builtins, json, os, struct
GEN = 0x407710

def reset(label="", report_path="", cap=2):
    builtins.l16_f120 = {"label": label, "report_path": report_path, "cap": cap,
                         "hits": 0, "events": [], "bp_ids": {}, "errors": []}
def _s():
    if not hasattr(builtins, "l16_f120"): reset()
    return builtins.l16_f120
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
def _cstr(proc, a, n=240):
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
    ti = _q(proc, vt - 8); nm = _q(proc, ti + 8) if ti else 0
    return {"vtable": hex(vt), "name": _cstr(proc, nm) if nm else None}
def _scan(proc, t, base, span=0x200):
    out = []
    for off in range(0, span, 8):
        v = _q(proc, base + off)
        if not v or v < 0x1000 or v > 0x00007FFFFFFFFFFF: continue
        e = {"off": hex(off), "ptr": hex(v)}
        va = _va(t, v)
        if va is not None: e["libcp_va"] = hex(va)
        rt = _rtti(proc, v)
        if rt and rt.get("name"): e["rtti"] = rt
        out.append(e)
    return out
def gen(frame, _l, _d):
    st = _s(); st["hits"] += 1
    proc = frame.GetThread().GetProcess(); t = proc.GetTarget()
    rdi = _u(frame, "rdi"); fcb = _q(proc, rdi + 8)
    p120 = _q(proc, fcb + 0x120); p128 = _q(proc, fcb + 0x128)
    ev = {"hit": st["hits"], "rdi": hex(rdi), "fcb": hex(fcb),
          "gen_wrapper_rtti": _rtti(proc, rdi),
          "fcb+0x120": hex(p120), "rtti_120": _rtti(proc, p120),
          "fcb+0x120_fields": _scan(proc, t, p120, 0x200),
          "fcb+0x118": hex(_q(proc, fcb + 0x118)), "rtti_118": _rtti(proc, _q(proc, fcb + 0x118)),
          "fcb+0x128": hex(p128), "rtti_128": _rtti(proc, p128),
          "fcb+0x128_fields": _scan(proc, t, p128, 0x140)}
    st["events"].append(ev)
    if st["hits"] >= int(st["cap"]): proc.Kill()
    return False
def install(debugger):
    st = _s(); t = debugger.GetSelectedTarget(); b = t.GetNumBreakpoints()
    debugger.HandleCommand("breakpoint set --shlib libcp.dylib --address 0x%x" % GEN)
    if t.GetNumBreakpoints() > b:
        bp = t.GetBreakpointAtIndex(t.GetNumBreakpoints() - 1)
        bp.SetScriptCallbackFunction("fcb120_probe.gen"); st["bp_ids"]["gen"] = bp.GetID()
    print("F120_INSTALLED", st["bp_ids"])
def drive(debugger, max_steps=400000):
    lldb = builtins.__import__("lldb"); proc = debugger.GetSelectedTarget().GetProcess(); n = 0
    while proc.IsValid() and proc.GetState() == lldb.eStateStopped and n < max_steps:
        n += 1; proc.Continue()
    print("F120_DRIVE", n)
def write_report(debugger, path=""):
    out = path or _s().get("report_path"); os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as h: json.dump(dict(_s()), h, indent=2, sort_keys=True, default=str)
    print("F120_WROTE", out)
