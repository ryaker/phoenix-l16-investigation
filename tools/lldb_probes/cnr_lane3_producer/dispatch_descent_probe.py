"""dispatch_descent_probe.py -- descend the byte-tile materialization dispatch.

Worker 0x3d79a0 dispatches inward via `call *rax` at 0x3d7a60.  Capture the
resolved next-layer target (rax) and the arg descriptors, so the tree can be
walked layer by layer to the byte-writing leaf.  Also captures 0x3d8030 (called
twice by 0x3d79a0) as a candidate.
"""
import builtins
import json
import os
import struct

SITES = {0x3D7A60: "vcall_rax_inner"}


def reset(label="", report_path="", cap=10):
    builtins.l16_dd = {"label": label, "report_path": report_path, "cap": cap,
                       "bp_ids": {}, "events": [], "errors": []}


def _s():
    if not hasattr(builtins, "l16_dd"):
        reset()
    return builtins.l16_dd


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
    raw = _read(proc, addr, 0x28)
    if raw is None:
        return None
    w, h, stride = struct.unpack_from("<iii", raw, 0x10)
    data = struct.unpack_from("<Q", raw, 0x20)[0]
    if not (0 < w < 20000 and 0 < h < 20000 and 0 < stride < 200000):
        return {"img": False}
    out = {"img": True, "w": w, "h": h, "stride": stride, "data": hex(data)}
    u8 = _read(proc, data, 16)
    if u8:
        out["u8"] = list(u8)
    return out


def vcall(frame, bp_loc, _d):
    st = _s()
    proc = frame.GetThread().GetProcess()
    target = proc.GetTarget()
    rax = _u(frame, "rax")   # call *rax -> target function is rax itself
    regs = {n: _u(frame, n) for n in ("rdi", "rsi", "rdx", "rcx", "r8")}
    ev = {"seq": len(st["events"]) + 1,
          "site_va": hex(_va(target, frame.GetPC())),
          "target_rax_va": hex(_va(target, rax)) if _va(target, rax) is not None else hex(rax),
          "regs": {k: hex(v) for k, v in regs.items()},
          "rdi_desc": _desc(proc, regs["rdi"]),
          "rsi_desc": _desc(proc, regs["rsi"]),
          "rdx_desc": _desc(proc, regs["rdx"])}
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
    for va, name in SITES.items():
        before = target.GetNumBreakpoints()
        debugger.HandleCommand(f"breakpoint set --shlib libcp.dylib --address 0x{va:x}")
        if target.GetNumBreakpoints() > before:
            bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
            bp.SetScriptCallbackFunction("dispatch_descent_probe.vcall")
            st["bp_ids"][name] = bp.GetID()
    print("DISPATCH_DESCENT_INSTALLED", st["bp_ids"])


def drive(debugger, max_steps=120000):
    lldb = builtins.__import__("lldb")
    proc = debugger.GetSelectedTarget().GetProcess()
    n = 0
    while proc.IsValid() and proc.GetState() == lldb.eStateStopped and n < max_steps:
        n += 1
        proc.Continue()
    print("DISPATCH_DESCENT_DRIVE", n)


def write_report(debugger, path=""):
    out = path or _s().get("report_path")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as h:
        json.dump(dict(_s()), h, indent=2, sort_keys=True, default=str)
    print("WROTE", out)
