"""gen_introspect_probe.py -- name the upstream byte-plane source by reading the
FusionCacheBayer byte-cache GENERATOR's captured state at runtime.

Static proof (this session): FusionCacheBayer+0xe0 is a passive TileCache<uchar>
VIEW; +0x70 holds a generator functor instance G (the ctor $_1 callable over
shared_ptr<Tile<uchar>>).  The consumer path 0x406a10 -> 0x3d2ca0 only GATHERS
pre-existing tiles from the shared TileStorage (FCB+0xf0/+0x100).  Therefore the
byte writer is upstream and reachable only through what G captured.

This probe breaks once at 0x406a10 (rdi = FusionCacheBayer), then:
  * reads FCB+0xcc scalar, FCB+0xe0 byte view, +0x70 generator instance G,
    +0xf0/+0x100 TileStorage;
  * RTTI-names G's vtable and TileStorage;
  * scans G[0..0x120] qwords: for each pointer, RTTI-resolves it (vtable->
    typeinfo->name) AND decodes it as an lt image descriptor (w,h,stride,data)
    sampling u8/u16/f32 -- surfacing the captured upstream source plane.
It is bounded: 2 hits then kill.
"""
import builtins
import json
import os
import struct

CONSUMER = 0x406A10


def reset(label="", report_path="", cap=2):
    builtins.l16_gi = {"label": label, "report_path": report_path, "cap": cap,
                       "hits": 0, "events": [], "bp_ids": {}, "errors": []}


def _s():
    if not hasattr(builtins, "l16_gi"):
        reset()
    return builtins.l16_gi


def _u(f, n):
    return f.FindRegister(n).GetValueAsUnsigned()


def _read(proc, addr, size):
    if not addr or addr < 0x1000 or addr > 0x00007FFFFFFFFFFF:
        return None
    lldb = builtins.__import__("lldb")
    err = lldb.SBError()
    try:
        d = proc.ReadMemory(addr, size, err)
    except Exception:
        return None
    return d if err.Success() and d and len(d) == size else None


def _q(proc, addr):
    d = _read(proc, addr, 8)
    return struct.unpack("<Q", d)[0] if d else 0


def _base(target):
    for m in target.module_iter():
        if str(m.GetFileSpec().GetFilename()) == "libcp.dylib":
            b = m.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if b != 0xFFFFFFFFFFFFFFFF:
                return b
    return None


def _va(target, a):
    b = _base(target)
    return (a - b) if (b is not None and b <= a < b + 0x900000) else None


def _cstr(proc, addr, n=256):
    out = b""
    for _ in range(n):
        c = _read(proc, addr + len(out), 1)
        if not c or c == b"\x00":
            break
        out += c
    return out.decode("utf-8", "replace")


def _rtti(proc, obj):
    """obj -> vtable -> typeinfo -> mangled name."""
    if not obj:
        return None
    vt = _q(proc, obj)
    if not vt:
        return None
    ti = _q(proc, vt - 8)
    if not ti:
        return {"vtable": hex(vt), "name": None}
    nm = _q(proc, ti + 8)
    return {"vtable": hex(vt), "name": _cstr(proc, nm) if nm else None}


def _as_image(proc, addr):
    """Decode addr as an lt image descriptor; sample data as u8/u16/f32."""
    raw = _read(proc, addr, 0x28)
    if raw is None:
        return None
    w, h, stride = struct.unpack_from("<iii", raw, 0x10)
    data = struct.unpack_from("<Q", raw, 0x20)[0]
    if not (0 < w < 30000 and 0 < h < 30000 and 0 < stride < 200000):
        return None
    out = {"w": w, "h": h, "stride": stride, "data": hex(data)}
    u8 = _read(proc, data, 24)
    if u8:
        out["u8"] = list(u8)
    f = _read(proc, data, 32)
    if f:
        out["u16"] = list(struct.unpack("<16H", f))
        out["f32"] = [round(x, 5) for x in struct.unpack("<8f", f)]
    return out


def _scan(proc, target, base_addr, span=0x120):
    fields = []
    for off in range(0, span, 8):
        v = _q(proc, base_addr + off)
        if not v or v < 0x1000 or v > 0x00007FFFFFFFFFFF:
            continue
        entry = {"off": hex(off), "ptr": hex(v)}
        va = _va(target, v)
        if va is not None:
            entry["libcp_va"] = hex(va)
        rt = _rtti(proc, v)
        if rt and rt.get("name"):
            entry["rtti"] = rt
        img = _as_image(proc, v)
        if img:
            entry["as_image"] = img
        # follow one level: pointer-to-pointer (shared_ptr payloads)
        inner = _q(proc, v)
        if inner and 0x1000 < inner < 0x00007FFFFFFFFFFF:
            irt = _rtti(proc, v)  # already have
            iimg = _as_image(proc, v)
            _ = irt, iimg
        fields.append(entry)
    return fields


def consumer(frame, _bp_loc, _d):
    st = _s()
    st["hits"] += 1
    proc = frame.GetThread().GetProcess()
    target = proc.GetTarget()
    fcb = _u(frame, "rdi")
    scalar_cc = _read(proc, fcb + 0xCC, 4)
    scalar_dc = _read(proc, fcb + 0xDC, 4)
    byte_view = _q(proc, fcb + 0xE0)
    gen = _q(proc, byte_view + 0x70) if byte_view else 0
    storage_ptr = _q(proc, fcb + 0xF0)
    storage_cb = _q(proc, fcb + 0x100)
    th = frame.GetThread()
    bt = []
    for i in range(min(16, th.GetNumFrames())):
        pc = th.GetFrameAtIndex(i).GetPC()
        v = _va(target, pc)
        bt.append(hex(v) if v is not None else th.GetFrameAtIndex(i).GetFunctionName())
    ev = {
        "hit": st["hits"],
        "fcb": hex(fcb),
        "scalar_cc": struct.unpack("<f", scalar_cc)[0] if scalar_cc else None,
        "scalar_dc": struct.unpack("<f", scalar_dc)[0] if scalar_dc else None,
        "byte_view": hex(byte_view),
        "byte_view_rtti": _rtti(proc, byte_view),
        "generator": hex(gen),
        "generator_rtti": _rtti(proc, gen),
        "generator_fields": _scan(proc, target, gen) if gen else [],
        "byte_view_fields": _scan(proc, target, byte_view, 0x90) if byte_view else [],
        "storage_ptr": hex(storage_ptr),
        "storage_rtti": _rtti(proc, storage_ptr),
        "storage_fields": _scan(proc, target, storage_ptr, 0x80) if storage_ptr else [],
        "storage_cb": hex(storage_cb),
        "backtrace_va": bt,
    }
    st["events"].append(ev)
    if st["hits"] >= int(st["cap"]):
        proc.Kill()
    return False


def install(debugger):
    st = _s()
    target = debugger.GetSelectedTarget()
    before = target.GetNumBreakpoints()
    debugger.HandleCommand("breakpoint set --shlib libcp.dylib --address 0x406a10")
    if target.GetNumBreakpoints() > before:
        bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
        bp.SetScriptCallbackFunction("gen_introspect_probe.consumer")
        st["bp_ids"]["consumer"] = bp.GetID()
    print("GEN_INTROSPECT_INSTALLED", st["bp_ids"])


def drive(debugger, max_steps=400000):
    lldb = builtins.__import__("lldb")
    proc = debugger.GetSelectedTarget().GetProcess()
    n = 0
    while proc.IsValid() and proc.GetState() == lldb.eStateStopped and n < max_steps:
        n += 1
        proc.Continue()
    print("GEN_INTROSPECT_DRIVE", n)


def write_report(debugger, path=""):
    out = path or _s().get("report_path")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as h:
        json.dump(dict(_s()), h, indent=2, sort_keys=True, default=str)
    print("GEN_INTROSPECT_WROTE", out)
