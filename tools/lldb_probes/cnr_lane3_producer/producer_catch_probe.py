"""producer_catch_probe.py -- catch the instruction that WRITES the CNR guide.

At 0x34b3f0 the guide buffer (task+0x60) is already filled.  We grab its
address, arm a hardware WRITE watchpoint on it, and continue.  When a later tile
re-allocates a guide at that just-freed address and fills it, the watchpoint
stops on the exact producing instruction -- we record PC/libcp_va, registers,
and a backtrace.  This is the writer, captured from Lumen, not inferred.
"""
import builtins
import json
import os
import struct

CNRBODY = 0x34B3F0


def reset(label="", report_path="", writes_cap=12):
    builtins.l16_pc = {"label": label, "report_path": report_path,
                        "writes_cap": writes_cap, "guide_addr": 0,
                        "armed": False, "bp_ids": {}, "wp_id": None,
                        "writes": [], "guide_first": None, "errors": []}


def _s():
    if not hasattr(builtins, "l16_pc"):
        reset()
    return builtins.l16_pc


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


def _libcp_base(target):
    for m in target.module_iter():
        if str(m.GetFileSpec().GetFilename()) == "libcp.dylib":
            b = m.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if b != 0xFFFFFFFFFFFFFFFF:
                return b
    return None


def _va(target, pc):
    b = _libcp_base(target)
    return (pc - b) if (b is not None and pc >= b) else None


def _regs(f):
    return {n: _u(f, n) for n in ("rax", "rbx", "rcx", "rdx", "rdi", "rsi",
                                  "r8", "r9", "r10", "r11", "r12", "r13",
                                  "r14", "r15", "rbp", "rsp")}


def cnr_body(frame, bp_loc, _d):
    st = _s()
    proc = frame.GetThread().GetProcess()
    target = proc.GetTarget()
    task = _u(frame, "rsi")
    graw = _read(proc, task, 0x68)
    if graw is None:
        return False
    guide = struct.unpack_from("<Q", graw, 0x60)[0]
    if not guide or st["armed"]:
        return False
    # record the guide's first values now
    g0 = _read(proc, guide, 64)
    st["guide_first"] = {"addr": guide,
                         "f32": list(struct.unpack("<16f", g0)) if g0 else None}
    st["guide_addr"] = guide
    # arm hardware write watchpoint on the first 8 bytes of the guide buffer
    lldb = builtins.__import__("lldb")
    werr = lldb.SBError()
    wp = target.WatchAddress(guide, 8, False, True, werr)
    if werr.Success() and wp and wp.IsValid():
        st["wp_id"] = wp.GetID()
        st["armed"] = True
        # disable the cnr bp so we free-run to the watchpoint
        bid = st["bp_ids"].get("cnr")
        bp = target.FindBreakpointByID(bid) if bid else None
        if bp and bp.IsValid():
            bp.SetEnabled(False)
        print("ARMED_WP", hex(guide), "id", st["wp_id"])
    else:
        st["errors"].append("watchpoint arm failed: " + str(werr))
    return False


def install(debugger):
    st = _s()
    target = debugger.GetSelectedTarget()
    before = target.GetNumBreakpoints()
    debugger.HandleCommand("breakpoint set --shlib libcp.dylib --address 0x34b3f0")
    if target.GetNumBreakpoints() > before:
        bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
        bp.SetScriptCallbackFunction("producer_catch_probe.cnr_body")
        st["bp_ids"]["cnr"] = bp.GetID()
    print("PRODUCER_CATCH_INSTALLED", st["bp_ids"])


def drive(debugger, max_steps=200000):
    lldb = builtins.__import__("lldb")
    st = _s()
    target = debugger.GetSelectedTarget()
    proc = target.GetProcess()
    n = 0
    while proc.IsValid() and proc.GetState() == lldb.eStateStopped and n < max_steps:
        n += 1
        proc.Continue()
        if proc.GetState() != lldb.eStateStopped:
            break
        th = proc.GetSelectedThread()
        if th.GetStopReason() == lldb.eStopReasonWatchpoint:
            fr = th.GetFrameAtIndex(0)
            pc = fr.GetPC()
            bt = []
            for i in range(min(th.GetNumFrames(), 8)):
                f = th.GetFrameAtIndex(i)
                bt.append({"i": i, "pc": f.GetPC(),
                           "libcp_va": _va(target, f.GetPC()),
                           "fn": f.GetFunctionName()})
            g = st["guide_addr"]
            gnow = _read(proc, g, 32)
            st["writes"].append({
                "n": len(st["writes"]) + 1,
                "pc": pc, "libcp_va": _va(target, pc),
                "regs": _regs(fr), "backtrace": bt,
                "guide_now_f32": list(struct.unpack("<8f", gnow)) if gnow else None,
            })
            if len(st["writes"]) >= int(st["writes_cap"]):
                break
    st["drive_steps"] = n
    print("PRODUCER_CATCH_DRIVE", n, "writes", len(st["writes"]))


def write_report(debugger, path=""):
    out = path or _s().get("report_path")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as h:
        json.dump(dict(_s()), h, indent=2, sort_keys=True, default=str)
    print("WROTE", out)
