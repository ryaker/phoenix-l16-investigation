"""bytetile_producer_probe.py -- capture the byte-tile producer's source->bytes.

0x3d2ca0 dispatches worker callbacks 0x3d79a0 (via *0x28) and 0x3d8590 (via
*0x20) that materialize the level-0 byte tile.  This probe breaks at both,
dumps their pointer args as image descriptors (sampled as u8 AND f32), and
records backtraces.  The producer's OUTPUT is u8 bytes (e.g. 255,254,135...);
its INPUT is the source that becomes those bytes -- naming the byte plane's
origin from Lumen.
"""
import builtins
import json
import os
import struct

WORKERS = {0x3D79A0: "worker_0x28", 0x3D8590: "worker_0x20"}


def reset(label="", report_path="", cap=16):
    builtins.l16_btp = {"label": label, "report_path": report_path, "cap": cap,
                        "bp_ids": {}, "events": [], "errors": []}


def _s():
    if not hasattr(builtins, "l16_btp"):
        reset()
    return builtins.l16_btp


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


def _desc(proc, addr):
    """Decode a pointer as an image descriptor and sample as u8 + f32."""
    raw = _read(proc, addr, 0x28)
    if raw is None:
        return None
    w, h, stride = struct.unpack_from("<iii", raw, 0x10)
    data = struct.unpack_from("<Q", raw, 0x20)[0]
    if not (0 < w < 20000 and 0 < h < 20000 and 0 < stride < 100000):
        return {"looks_like_image": False, "raw16": list(raw[:16])}
    out = {"looks_like_image": True, "w": w, "h": h, "stride": stride,
           "data": hex(data)}
    u8 = _read(proc, data, min(w, 24))
    if u8:
        out["u8_first"] = list(u8)
    f32 = _read(proc, data, min(w, 12) * 4)
    if f32:
        out["f32_first"] = [round(x, 4) for x in
                            struct.unpack("<" + "f" * (len(f32) // 4), f32)]
    return out


def worker(frame, bp_loc, _d):
    st = _s()
    proc = frame.GetThread().GetProcess()
    target = proc.GetTarget()
    pc_va = _va(target, frame.GetPC())
    th = frame.GetThread()
    bt = []
    for i in range(min(8, th.GetNumFrames())):
        v = _va(target, th.GetFrameAtIndex(i).GetPC())
        bt.append(hex(v) if v is not None else th.GetFrameAtIndex(i).GetFunctionName())
    regs = {n: _u(frame, n) for n in ("rdi", "rsi", "rdx", "rcx", "r8", "r9")}
    ev = {"seq": len(st["events"]) + 1, "site_va": hex(pc_va) if pc_va else None,
          "regs": {k: hex(v) for k, v in regs.items()},
          "rdi_desc": _desc(proc, regs["rdi"]),
          "rsi_desc": _desc(proc, regs["rsi"]),
          "rdx_desc": _desc(proc, regs["rdx"]),
          "rcx_desc": _desc(proc, regs["rcx"]),
          "backtrace_va": bt}
    st["events"].append(ev)
    if len(st["events"]) >= int(st["cap"]):
        for bid in st["bp_ids"].values():
            bp = target.FindBreakpointByID(bid)
            if bp and bp.IsValid():
                bp.SetEnabled(False)
        proc.Kill()
    return False


def install(debugger):
    st = _s()
    target = debugger.GetSelectedTarget()
    for va, name in WORKERS.items():
        before = target.GetNumBreakpoints()
        debugger.HandleCommand(f"breakpoint set --shlib libcp.dylib --address 0x{va:x}")
        if target.GetNumBreakpoints() > before:
            bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
            bp.SetScriptCallbackFunction("bytetile_producer_probe.worker")
            st["bp_ids"][name] = bp.GetID()
    print("BYTETILE_PRODUCER_INSTALLED", st["bp_ids"])


def drive(debugger, max_steps=120000):
    lldb = builtins.__import__("lldb")
    proc = debugger.GetSelectedTarget().GetProcess()
    n = 0
    while proc.IsValid() and proc.GetState() == lldb.eStateStopped and n < max_steps:
        n += 1
        proc.Continue()
    print("BYTETILE_PRODUCER_DRIVE", n)


def write_report(debugger, path=""):
    out = path or _s().get("report_path")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as h:
        json.dump(dict(_s()), h, indent=2, sort_keys=True, default=str)
    print("WROTE", out)
