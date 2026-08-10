"""bytetile_alloc_watch_probe.py -- catch the byte-tile PRODUCER's first write.

The byte plane is materialized inside 0x3d2ca0 through Lumen's generic tile
framework (executor 0x5440/0x5670 -> worker 0x3d79a0/0x3d8590 -> deeper), too
many dispatch layers to trace by hand.  Instead: the per-tile byte buffer is a
~272-283 KB (522^2..532^2) heap allocation.  Hook malloc filtered to that size,
grab the returned buffer, arm a hardware WRITE watchpoint on its first bytes,
and let it run.  The first write is the producer's store -- capture its PC,
backtrace, and source registers.  That lands on the byte-writing instruction
directly, under all the dispatch.
"""
import builtins
import json
import os
import struct

SIZE_LO = 272000   # byte plane: 522^2=272484 .. 532^2=283024
SIZE_HI = 283200


def reset(label="", report_path="", n_watch=1, writes_cap=8):
    builtins.l16_baw = {"label": label, "report_path": report_path,
                        "n_watch": n_watch, "writes_cap": writes_cap,
                        "bp_ids": {}, "armed": 0, "pending_ret": {},
                        "allocs": [], "writes": [], "errors": []}


def _s():
    if not hasattr(builtins, "l16_baw"):
        reset()
    return builtins.l16_baw


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
                                  "r8", "r9", "r10", "r11", "r12", "r13",
                                  "r14", "r15")}


def malloc_entry(frame, bp_loc, _d):
    """malloc(size) [size already filtered by bp condition]: set a one-shot bp
    on the return address to grab the buffer pointer. Single-arm."""
    st = _s()
    if st["armed"] >= int(st["n_watch"]) or st.get("ret_pending"):
        return False
    size = _u(frame, "rdi")
    proc = frame.GetThread().GetProcess()
    target = proc.GetTarget()
    ret = struct.unpack("<Q", _read(proc, _u(frame, "rsp"), 8))[0]
    debugger = target.GetDebugger()
    before = target.GetNumBreakpoints()
    debugger.HandleCommand(f"breakpoint set --address 0x{ret:x}")
    if target.GetNumBreakpoints() > before:
        bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
        bp.SetScriptCallbackFunction("bytetile_alloc_watch_probe.malloc_ret")
        bp.SetOneShot(True)
        st["ret_pending"] = True
        st["pending_size"] = size
    return False


def malloc_ret(frame, bp_loc, _d):
    """At malloc's return: rax = buffer. Arm write watchpoint DEEP in the buffer
    (past allocator free-list metadata)."""
    st = _s()
    st["ret_pending"] = False
    if st["armed"] >= int(st["n_watch"]):
        return False
    proc = frame.GetThread().GetProcess()
    target = proc.GetTarget()
    buf = _u(frame, "rax")
    watch_at = buf + 0x8000            # deep: skip allocator metadata + early rows
    st["allocs"].append({"buf": hex(buf), "watch_at": hex(watch_at),
                         "size": st.get("pending_size")})
    lldb = builtins.__import__("lldb")
    werr = lldb.SBError()
    wp = target.WatchAddress(watch_at, 8, False, True, werr)
    if werr.Success() and wp and wp.IsValid():
        st["armed"] += 1
        st["watch_buf"] = buf
        st["watch_at"] = watch_at
        st["wp_id"] = wp.GetID()
        mb = st["bp_ids"].get("malloc")
        bp = target.FindBreakpointByID(mb) if mb else None
        if bp and bp.IsValid():
            bp.SetEnabled(False)
        print("ARMED_BYTE_WP", hex(buf), "watch_at", hex(watch_at))
    else:
        st["errors"].append("wp arm failed: " + str(werr))
    return False


def install(debugger):
    st = _s()
    target = debugger.GetSelectedTarget()
    before = target.GetNumBreakpoints()
    # in-process size condition -> fast (no python callback per malloc)
    debugger.HandleCommand(
        f"breakpoint set --name malloc --condition "
        f"'$rdi >= {SIZE_LO} && $rdi <= {SIZE_HI}'")
    if target.GetNumBreakpoints() > before:
        bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
        bp.SetScriptCallbackFunction("bytetile_alloc_watch_probe.malloc_entry")
        st["bp_ids"]["malloc"] = bp.GetID()
    print("BYTE_ALLOC_WATCH_INSTALLED", st["bp_ids"])


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
            buf = st.get("watch_buf", 0)
            now = _read(proc, st.get("watch_at", buf), 32)
            # skip allocator/system writes (not in libcp) -- keep only real
            # producer stores, but always record a compact trace for auditing.
            st.setdefault("all_hits", 0)
            st["all_hits"] += 1
            if pc_va is None:
                continue
            bt = []
            for i in range(min(12, th.GetNumFrames())):
                pc = th.GetFrameAtIndex(i).GetPC()
                v = _va(target, pc)
                bt.append(hex(v) if v is not None else
                          th.GetFrameAtIndex(i).GetFunctionName())
            st["writes"].append({
                "n": len(st["writes"]) + 1,
                "pc_va": hex(pc_va),
                "regs": {k: hex(v) for k, v in _regs(fr).items()},
                "buf_now_u8": list(now) if now else None,
                "backtrace": bt,
            })
            if len(st["writes"]) >= int(st["writes_cap"]):
                break
    st["drive_steps"] = n
    print("BYTE_ALLOC_WATCH_DRIVE", n, "writes", len(st["writes"]))


def write_report(debugger, path=""):
    out = path or _s().get("report_path")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as h:
        json.dump(dict(_s()), h, indent=2, sort_keys=True, default=str)
    print("WROTE", out)
