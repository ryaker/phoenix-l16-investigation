"""bytebuf_reuse_watch_probe.py -- catch the byte producer via buffer reuse.

At LUT helper 0x1BCE50 the confirmed byte plane is src1 = rsi, buffer at +0x20.
Per-tile byte buffers are freed and re-allocated, so arming a WRITE watchpoint
on this buffer and continuing catches the NEXT tile's producer writing bytes
into the recycled block.  Writes are filtered to libcp PCs and byte-valued
content, so allocator/float/u16 noise is dropped.
"""
import builtins
import json
import os
import struct

LUT = 0x1BCE50   # src1(byte)=rsi, descriptor +0x20 = byte buffer


def reset(label="", report_path="", writes_cap=10, watch_off=0x9000):
    builtins.l16_bru = {"label": label, "report_path": report_path,
                        "writes_cap": writes_cap, "watch_off": watch_off,
                        "bp_ids": {}, "armed": False, "seed": None,
                        "writes": [], "errors": []}


def _s():
    if not hasattr(builtins, "l16_bru"):
        reset()
    return builtins.l16_bru


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


def lut(frame, bp_loc, _d):
    st = _s()
    if st["armed"]:
        return False
    proc = frame.GetThread().GetProcess()
    target = proc.GetTarget()
    rsi = _u(frame, "rsi")
    desc = _read(proc, rsi, 0x28)
    if desc is None:
        return False
    w, h, stride = struct.unpack_from("<iii", desc, 0x10)
    data = struct.unpack_from("<Q", desc, 0x20)[0]
    if not (data and 0 < w < 20000 and 0 < stride < 200000):
        return False
    watch_at = data + int(st["watch_off"])
    sample = _read(proc, data, 24)
    st["seed"] = {"buf": hex(data), "w": w, "h": h, "stride": stride,
                  "watch_at": hex(watch_at), "u8_now": list(sample) if sample else None}
    lldb = builtins.__import__("lldb")
    werr = lldb.SBError()
    wp = target.WatchAddress(watch_at, 8, False, True, werr)
    if werr.Success() and wp and wp.IsValid():
        st["armed"] = True
        st["watch_at"] = watch_at
        bid = st["bp_ids"].get("lut")
        bp = target.FindBreakpointByID(bid) if bid else None
        if bp and bp.IsValid():
            bp.SetEnabled(False)
        print("ARMED_BYTEBUF_WP", hex(watch_at))
    else:
        st["errors"].append("wp arm failed: " + str(werr))
    return False


def install(debugger):
    st = _s()
    target = debugger.GetSelectedTarget()
    before = target.GetNumBreakpoints()
    debugger.HandleCommand("breakpoint set --shlib libcp.dylib --address 0x1bce50")
    if target.GetNumBreakpoints() > before:
        bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
        bp.SetScriptCallbackFunction("bytebuf_reuse_watch_probe.lut")
        st["bp_ids"]["lut"] = bp.GetID()
    print("BYTEBUF_REUSE_INSTALLED", st["bp_ids"])


def drive(debugger, max_steps=300000):
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
            now = _read(proc, st.get("watch_at", 0), 32)
            st.setdefault("all_hits", 0)
            st["all_hits"] += 1
            if pc_va is None:   # skip allocator/system
                continue
            bt = []
            for i in range(min(12, th.GetNumFrames())):
                pc = th.GetFrameAtIndex(i).GetPC()
                v = _va(target, pc)
                bt.append(hex(v) if v is not None else
                          th.GetFrameAtIndex(i).GetFunctionName())
            st["writes"].append({
                "n": len(st["writes"]) + 1, "pc_va": hex(pc_va),
                "regs": {k: hex(v) for k, v in _regs(fr).items()},
                "buf_now_u8": list(now) if now else None, "backtrace": bt})
            if len(st["writes"]) >= int(st["writes_cap"]):
                break
    st["drive_steps"] = n
    print("BYTEBUF_REUSE_DRIVE", n, "writes", len(st["writes"]))


def write_report(debugger, path=""):
    out = path or _s().get("report_path")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as h:
        json.dump(dict(_s()), h, indent=2, sort_keys=True, default=str)
    print("WROTE", out)
