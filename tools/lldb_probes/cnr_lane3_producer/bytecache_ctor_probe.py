"""bytecache_ctor_probe.py -- name the FusionCacheBayer byte-cache producer.

The byte TileCache<unsigned char> at FusionCacheBayer+0xe0 is built at 0x40663e
by calling the TileCache ctor 0x3d1f80 with a producer callback (leaq 0x66b298
-> rax, leaq 0x6756c0 -> rdx).  This probe breaks at 0x3d1f80, symbolicates its
argument pointers and the descriptor/vtable they reference, so the producer
callback (the FusionCacheBayer ctor $_1 over shared_ptr<Tile<unsigned char>>)
is named from Lumen rather than guessed.  It then also breaks at the named
producer (resolved at runtime) to capture what it reads and writes.
"""
import builtins
import json
import os
import struct

BYTE_CACHE_CTOR = 0x3D1F80   # rcx=&(FCB+0xf0) storage, rax=0x66b298, rdx=0x6756c0


def reset(label="", report_path="", cap=2):
    builtins.l16_bcc = {"label": label, "report_path": report_path, "cap": cap,
                        "bp_ids": {}, "ctor_events": [], "producer_events": [],
                        "producer_installed": False, "errors": []}


def _s():
    if not hasattr(builtins, "l16_bcc"):
        reset()
    return builtins.l16_bcc


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


def _sym(target, addr):
    if not addr:
        return None
    lldb = builtins.__import__("lldb")
    sa = target.ResolveLoadAddress(addr)
    if not sa or not sa.IsValid():
        return None
    sym = sa.GetSymbol()
    return {"va": _va(target, addr),
            "symbol": sym.GetName() if sym and sym.IsValid() else None}


def _cstr(proc, addr, n=200):
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
    return {"name": _cstr(proc, nm) if nm else None}


def ctor(frame, bp_loc, _d):
    st = _s()
    proc = frame.GetThread().GetProcess()
    target = proc.GetTarget()
    regs = {n: _u(frame, n) for n in ("rdi", "rsi", "rdx", "rcx", "r8", "r9")}
    rax = _u(frame, "rax")
    # descriptor at rax (0x66b298) + a few qwords, each symbolicated
    desc = []
    for i in range(6):
        v = _q(proc, rax + i * 8)
        desc.append({"i": i, "val_va": _va(target, v), "sym": _sym(target, v)})
    ev = {
        "seq": len(st["ctor_events"]) + 1,
        "regs": {k: hex(v) for k, v in regs.items()}, "rax": hex(rax),
        "sym_rax": _sym(target, rax),
        "sym_rdx": _sym(target, regs["rdx"]),
        "sym_rsi": _sym(target, regs["rsi"]),
        "rtti_rdi": _rtti(proc, regs["rdi"]),
        "rax_descriptor": desc,
        # storage arg rcx = &(FCB+0xf0); read the TileStorage ptr
        "storage_ptr": hex(_q(proc, regs["rcx"])),
    }
    # try to install a breakpoint on the most likely producer code pointer:
    # the descriptor slot that resolves to a libcp function.
    if not st["producer_installed"]:
        cand = None
        for d in desc:
            if d["val_va"] is not None:
                cand = _q(proc, rax + d["i"] * 8)
                st["producer_pick"] = {"slot": d["i"], "va": d["val_va"],
                                       "sym": d["sym"]}
                break
        # also consider rdx directly
        if cand is None and _va(target, regs["rdx"]) is not None:
            cand = regs["rdx"]
            st["producer_pick"] = {"slot": "rdx", "va": _va(target, regs["rdx"]),
                                   "sym": _sym(target, regs["rdx"])}
        if cand:
            debugger = target.GetDebugger()
            before = target.GetNumBreakpoints()
            debugger.HandleCommand(f"breakpoint set --address 0x{cand:x}")
            if target.GetNumBreakpoints() > before:
                bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
                bp.SetScriptCallbackFunction("bytecache_ctor_probe.producer")
                st["bp_ids"]["producer"] = bp.GetID()
                st["producer_installed"] = True
    st["ctor_events"].append(ev)
    if len(st["ctor_events"]) >= int(st["cap"]):
        bid = st["bp_ids"].get("ctor")
        bp = target.FindBreakpointByID(bid) if bid else None
        if bp and bp.IsValid():
            bp.SetEnabled(False)
    return False


def producer(frame, bp_loc, _d):
    st = _s()
    proc = frame.GetThread().GetProcess()
    target = proc.GetTarget()
    regs = {n: _u(frame, n) for n in ("rdi", "rsi", "rdx", "rcx", "r8", "r9")}
    th = frame.GetThread()
    bt = []
    for i in range(min(10, th.GetNumFrames())):
        pc = th.GetFrameAtIndex(i).GetPC()
        bt.append(hex(_va(target, pc)) if _va(target, pc) is not None
                  else th.GetFrameAtIndex(i).GetFunctionName())
    ev = {"seq": len(st["producer_events"]) + 1,
          "regs": {k: hex(v) for k, v in regs.items()},
          "rtti_rdi": _rtti(proc, regs["rdi"]),
          "rtti_rsi": _rtti(proc, regs["rsi"]),
          "backtrace_va": bt}
    st["producer_events"].append(ev)
    if len(st["producer_events"]) >= 4:
        bid = st["bp_ids"].get("producer")
        bp = target.FindBreakpointByID(bid) if bid else None
        if bp and bp.IsValid():
            bp.SetEnabled(False)
        proc.Kill()
    return False


def install(debugger):
    st = _s()
    target = debugger.GetSelectedTarget()
    before = target.GetNumBreakpoints()
    debugger.HandleCommand("breakpoint set --shlib libcp.dylib --address 0x3d1f80")
    if target.GetNumBreakpoints() > before:
        bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
        bp.SetScriptCallbackFunction("bytecache_ctor_probe.ctor")
        st["bp_ids"]["ctor"] = bp.GetID()
    print("BYTECACHE_CTOR_INSTALLED", st["bp_ids"])


def drive(debugger, max_steps=80000):
    lldb = builtins.__import__("lldb")
    proc = debugger.GetSelectedTarget().GetProcess()
    n = 0
    while proc.IsValid() and proc.GetState() == lldb.eStateStopped and n < max_steps:
        n += 1
        proc.Continue()
    print("BYTECACHE_CTOR_DRIVE", n)


def write_report(debugger, path=""):
    out = path or _s().get("report_path")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as h:
        json.dump(dict(_s()), h, indent=2, sort_keys=True, default=str)
    print("WROTE", out)
