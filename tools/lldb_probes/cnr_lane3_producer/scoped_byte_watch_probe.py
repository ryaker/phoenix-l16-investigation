"""scoped_byte_watch_probe.py -- last-shot byte-producer catch, all fixes combined.

Scope a size-filtered malloc hook to WITHIN a single 0x406a10 consumer call, arm
write watchpoints on up to 4 size-matched allocations in parallel (deep offset),
and at each first write verify BYTE content (dense 0..255, spatially doubled) to
reject the float/u16 buffers of the same byte-size that beat earlier runs.  The
byte-content write's PC/backtrace is the producer.
"""
import builtins
import json
import os
import struct

CONSUMER = 0x406A10
LUT = 0x1BCE50
SIZE_LO = 272000
SIZE_HI = 283200
MAX_ARM = 4


def reset(label="", report_path="", watch_off=0x9000):
    builtins.l16_sbw = {"label": label, "report_path": report_path,
                        "watch_off": watch_off, "bp_ids": {}, "in_consumer": 0,
                        "arms": [], "wp_ids": [], "hits": [], "producer": None,
                        "errors": []}


def _s():
    if not hasattr(builtins, "l16_sbw"):
        reset()
    return builtins.l16_sbw


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


def _regs(f):
    return {n: _u(f, n) for n in ("rax", "rbx", "rcx", "rdx", "rdi", "rsi",
                                  "r8", "r9", "r12", "r13", "r14", "r15")}


def _is_byteish(b):
    """Heuristic: bytes 0..255 image data is spatially doubled (adjacent pairs
    equal) and NOT float (no 0x0000803f=1.0f pattern)."""
    if not b or len(b) < 16:
        return False
    if any(b[i:i+4] == bytes([0, 0, 128, 63]) for i in range(len(b) - 3)):
        return False
    doubled = sum(1 for i in range(0, len(b) - 1, 2) if b[i] == b[i + 1])
    return doubled >= (len(b) // 2) * 0.5


def consumer_enter(frame, bp_loc, _d):
    _s()["in_consumer"] += 1
    return False


def malloc_entry(frame, bp_loc, _d):
    st = _s()
    if not st["in_consumer"] or len(st["arms"]) >= MAX_ARM:
        return False
    proc = frame.GetThread().GetProcess()
    target = proc.GetTarget()
    ret = struct.unpack("<Q", _read(proc, _u(frame, "rsp"), 8))[0]
    debugger = target.GetDebugger()
    before = target.GetNumBreakpoints()
    debugger.HandleCommand(f"breakpoint set --address 0x{ret:x}")
    if target.GetNumBreakpoints() > before:
        bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
        bp.SetScriptCallbackFunction("scoped_byte_watch_probe.malloc_ret")
        bp.SetOneShot(True)
    return False


def malloc_ret(frame, bp_loc, _d):
    st = _s()
    if len(st["arms"]) >= MAX_ARM:
        return False
    proc = frame.GetThread().GetProcess()
    target = proc.GetTarget()
    buf = _u(frame, "rax")
    watch_at = buf + int(st["watch_off"])
    lldb = builtins.__import__("lldb")
    werr = lldb.SBError()
    wp = target.WatchAddress(watch_at, 8, False, True, werr)
    if werr.Success() and wp and wp.IsValid():
        st["arms"].append({"buf": hex(buf), "watch_at": watch_at})
        st["wp_ids"].append(wp.GetID())
    return False


def install(debugger):
    st = _s()
    target = debugger.GetSelectedTarget()
    specs = [(CONSUMER, "scoped_byte_watch_probe.consumer_enter", "consumer"),
             (LUT, "scoped_byte_watch_probe.consumer_enter", "lut")]
    for va, cb, name in specs:
        before = target.GetNumBreakpoints()
        debugger.HandleCommand(f"breakpoint set --shlib libcp.dylib --address 0x{va:x}")
        if target.GetNumBreakpoints() > before:
            bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
            bp.SetScriptCallbackFunction(cb)
            st["bp_ids"][name] = bp.GetID()
    before = target.GetNumBreakpoints()
    debugger.HandleCommand(
        f"breakpoint set --name malloc --condition '$rdi >= {SIZE_LO} && $rdi <= {SIZE_HI}'")
    if target.GetNumBreakpoints() > before:
        bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
        bp.SetScriptCallbackFunction("scoped_byte_watch_probe.malloc_entry")
        st["bp_ids"]["malloc"] = bp.GetID()
    print("SCOPED_BYTE_INSTALLED", st["bp_ids"])


def drive(debugger, max_steps=400000):
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
            pc_va = _va(target, fr.GetPC())
            # identify which watchpoint fired -> its address
            wp_id = th.GetStopReasonDataAtIndex(0) if th.GetStopReasonDataCount() else -1
            wp = target.FindWatchpointByID(wp_id) if wp_id >= 0 else None
            watch_at = wp.GetWatchAddress() if wp and wp.IsValid() else None
            now = _read(proc, watch_at, 32) if watch_at else None
            if pc_va is None:
                continue
            byteish = _is_byteish(now)
            bt = []
            for i in range(min(14, th.GetNumFrames())):
                pc = th.GetFrameAtIndex(i).GetPC()
                v = _va(target, pc)
                bt.append(hex(v) if v is not None else
                          th.GetFrameAtIndex(i).GetFunctionName())
            rec = {"n": len(st["hits"]) + 1, "pc_va": hex(pc_va),
                   "byteish": byteish, "u8": list(now) if now else None,
                   "regs": {k: hex(v) for k, v in _regs(fr).items()},
                   "backtrace": bt}
            st["hits"].append(rec)
            if byteish and st["producer"] is None:
                st["producer"] = rec
                print("BYTE_PRODUCER", rec["pc_va"], rec["backtrace"][:6])
            if len(st["hits"]) >= 24 or st["producer"] is not None and len(st["hits"]) >= 6:
                break
    st["drive_steps"] = n
    print("SCOPED_BYTE_DRIVE", n, "hits", len(st["hits"]),
          "producer", st["producer"]["pc_va"] if st["producer"] else None)


def write_report(debugger, path=""):
    out = path or _s().get("report_path")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as h:
        json.dump(dict(_s()), h, indent=2, sort_keys=True, default=str)
    print("WROTE", out)
