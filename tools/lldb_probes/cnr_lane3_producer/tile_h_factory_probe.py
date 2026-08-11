"""tile_h_factory_probe.py -- name the byte-tile PRODUCER.

Static RE (this session) found two make_shared<lt::Tile<unsigned char>> sites
that operator new(0x138) the __shared_ptr_emplace<Tile<h>> (vtable 0x66ab48) and
call the Tile<h> ctor 0x3d7710 to fill from a source:
  * factory A = 0x3d2610  (call ctor at 0x3d2754)
  * factory B = 0x3d7b40  (call ctor at ~0x3d7c9x)
Hook both entries; capture the caller backtrace (the producer stage), the source
descriptor, and -- via a return breakpoint -- the freshly built tile's data to
verify the doubled-u8 weight signature.
"""
import builtins, json, os, struct

FACTORIES = (0x3d7710, 0x3d2610, 0x3d7b40)


def reset(label="", report_path="", cap=8):
    builtins.l16_tf = {"label": label, "report_path": report_path, "cap": cap,
                       "hits": 0, "events": [], "bp_ids": {}, "errors": []}

def _s():
    if not hasattr(builtins, "l16_tf"): reset()
    return builtins.l16_tf

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

def _cstr(proc, a, n=220):
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
    nm = _q(proc, ti + 8) if ti else 0
    return {"vtable": hex(vt), "name": _cstr(proc, nm) if nm else None}

def _desc(proc, a):
    raw = _read(proc, a, 0x28)
    if not raw: return None
    w, h, stride = struct.unpack_from("<iii", raw, 0x10)
    data = struct.unpack_from("<Q", raw, 0x20)[0]
    o = {"w": w, "h": h, "stride": stride, "data": hex(data)}
    s = _read(proc, data, 24)
    if s: o["u8"] = list(s)
    return o

def entry(frame, _l, _d):
    st = _s(); st["hits"] += 1
    proc = frame.GetThread().GetProcess(); t = proc.GetTarget()
    th = frame.GetThread()
    bt = []
    for i in range(min(22, th.GetNumFrames())):
        fr = th.GetFrameAtIndex(i)
        v = _va(t, fr.GetPC())
        # try to RTTI-name the frame's `this` (rdi at call boundaries is lost;
        # instead resolve any nearby cache object via frame args is unreliable)
        bt.append(hex(v) if v is not None else fr.GetFunctionName())
    which = _va(t, frame.GetPC())
    regs = {n: hex(_u(frame, n)) for n in ("rdi", "rsi", "rdx", "rcx", "r8", "r13", "r15")}
    # heuristics: rsi/rcx/r15 often carry source descriptor / dims
    srcs = {}
    for rn in ("rsi", "rcx", "r13", "r15", "rdi"):
        a = _u(frame, rn)
        dd = _desc(proc, a)
        if dd: srcs[rn] = dd
    ev = {"hit": st["hits"], "factory_va": hex(which) if which is not None else None,
          "regs": regs, "src_descriptors": srcs, "backtrace_va": bt}
    st["events"].append(ev)
    if st["hits"] >= int(st["cap"]): proc.Kill()
    return False

def install(debugger):
    st = _s(); t = debugger.GetSelectedTarget()
    for addr in FACTORIES:
        b = t.GetNumBreakpoints()
        debugger.HandleCommand("breakpoint set --shlib libcp.dylib --address 0x%x" % addr)
        if t.GetNumBreakpoints() > b:
            bp = t.GetBreakpointAtIndex(t.GetNumBreakpoints() - 1)
            bp.SetScriptCallbackFunction("tile_h_factory_probe.entry")
            st["bp_ids"][hex(addr)] = bp.GetID()
    print("TF_INSTALLED", st["bp_ids"])

def drive(debugger, max_steps=400000):
    lldb = builtins.__import__("lldb"); proc = debugger.GetSelectedTarget().GetProcess(); n = 0
    while proc.IsValid() and proc.GetState() == lldb.eStateStopped and n < max_steps:
        n += 1; proc.Continue()
    print("TF_DRIVE", n)

def write_report(debugger, path=""):
    out = path or _s().get("report_path"); os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as h: json.dump(dict(_s()), h, indent=2, sort_keys=True, default=str)
    print("TF_WROTE", out)
