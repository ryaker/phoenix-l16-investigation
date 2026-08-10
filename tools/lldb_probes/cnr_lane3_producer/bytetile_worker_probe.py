"""bytetile_worker_probe.py -- name the FusionCacheBayer byte-tile producer.

0x3d2ca0 (level-0 extract) materializes byte tiles by dispatching workers through
executors 0x5440/0x5670 and invoking them via call *0x20(rax) / *0x28(rax).
This probe breaks at those virtual-call sites, captures the worker object (rax),
its RTTI, and the exact vtable target (the producer callback), plus the executor
args.  From Lumen; nothing inferred.
"""
import builtins
import json
import os
import struct

# virtual-call sites inside 0x3d2ca0 (call *0x20/0x28(rax)); rax = worker object
SITES = {
    0x3D2ED7: "vcall_0x28_a",
    0x3D2EE4: "vcall_0x20_a",
    0x3D2F31: "vcall_0x28_b",
    0x3D2F44: "vcall_0x20_b",
}
SLOT = {0x3D2ED7: 0x28, 0x3D2EE4: 0x20, 0x3D2F31: 0x28, 0x3D2F44: 0x20}


def reset(label="", report_path="", cap=12):
    builtins.l16_btw = {"label": label, "report_path": report_path, "cap": cap,
                        "bp_ids": {}, "events": [], "errors": []}


def _s():
    if not hasattr(builtins, "l16_btw"):
        reset()
    return builtins.l16_btw


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


def _q(proc, a):
    d = _read(proc, a, 8)
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


def _cstr(proc, addr, n=180):
    out = b""
    for _ in range(n):
        c = _read(proc, addr + len(out), 1)
        if not c or c == b"\x00":
            break
        out += c
    return out.decode("utf-8", "replace")


def _rtti(proc, obj):
    vt = _q(proc, obj)
    if not vt:
        return None
    ti = _q(proc, vt - 8)
    nm = _q(proc, ti + 8) if ti else 0
    return _cstr(proc, nm) if nm else None


def _desc(proc, addr):
    raw = _read(proc, addr, 0x28)
    if raw is None:
        return None
    w, h, stride = struct.unpack_from("<iii", raw, 0x10)
    data = struct.unpack_from("<Q", raw, 0x20)[0]
    out = {"w": w, "h": h, "stride": stride, "data": hex(data)}
    if data and 0 < w < 20000 and stride > 0:
        s = _read(proc, data, min(w, 24))
        if s:
            out["u8_first"] = list(s)
    return out


def vcall(frame, bp_loc, _d):
    st = _s()
    proc = frame.GetThread().GetProcess()
    target = proc.GetTarget()
    pc_va = _va(target, frame.GetPC())
    rax = _u(frame, "rax")
    slot = SLOT.get(pc_va, 0)
    # call *slot(rax): target = *(rax+slot) (single deref). rax is the worker.
    tgt = _q(proc, rax + slot)
    vt = _q(proc, rax)  # if rax is polymorphic, *rax is its vtable
    regs = {n: _u(frame, n) for n in ("rdi", "rsi", "rdx", "rcx", "r8")}
    ev = {
        "seq": len(st["events"]) + 1,
        "site_va": hex(pc_va) if pc_va else None,
        "worker_rax": hex(rax), "worker_rtti": _rtti(proc, rax),
        "target_va": hex(_va(target, tgt)) if tgt and _va(target, tgt) else hex(tgt),
        "obj_vtable_va": hex(_va(target, vt)) if vt and _va(target, vt) else hex(vt),
        "regs": {k: hex(v) for k, v in regs.items()},
    }
    st["events"].append(ev)
    if len(st["events"]) >= int(st["cap"]):
        for name, bid in st["bp_ids"].items():
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
            bp.SetScriptCallbackFunction("bytetile_worker_probe.vcall")
            st["bp_ids"][name] = bp.GetID()
    print("BYTETILE_WORKER_INSTALLED", st["bp_ids"])


def drive(debugger, max_steps=120000):
    lldb = builtins.__import__("lldb")
    proc = debugger.GetSelectedTarget().GetProcess()
    n = 0
    while proc.IsValid() and proc.GetState() == lldb.eStateStopped and n < max_steps:
        n += 1
        proc.Continue()
    print("BYTETILE_WORKER_DRIVE", n)


def write_report(debugger, path=""):
    out = path or _s().get("report_path")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as h:
        json.dump(dict(_s()), h, indent=2, sort_keys=True, default=str)
    print("WROTE", out)
