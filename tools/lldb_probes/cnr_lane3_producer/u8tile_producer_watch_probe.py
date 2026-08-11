"""u8tile_producer_watch_probe.py -- catch the UPSTREAM writer of the byte plane.

Prior probes proved the byte TileCache<uchar> (+0xe0) is a passive pyramid VIEW
over a shared lt::TileStorage; its $_1 generator is a trivial no-op; tiles are
already resident before FusionCacheBayer's consumer (0x406a10) runs.  So the
byte VALUES are deposited upstream.  The u8 tile is a 522x522 stride-522 buffer
(272484 bytes) holding a 2x-upsampled half-res u8 weight map.

This probe hooks malloc, waits for an allocation whose size == 522*522 (the u8
tile), arms ONE hardware WRITE watchpoint on a byte mid-buffer, then continues.
On the FIRST write it records the faulting PC and, crucially, walks PAST any
system frame (memmove/memset) to the first libcp frame -- the producer -- with
full backtrace, the mem-op source operand (rsi) + a byte sample of the source,
and the destination.  Bounded: arm once, capture N writes, then kill.
"""
import builtins
import json
import os
import struct

SIZE_LO = 270000                     # 522*522 = 272484 u8 tile; float/u16 far larger
SIZE_HI = 300000


def reset(label="", report_path="", writes_cap=6, watch_off=0x8800):
    builtins.l16_u8p = {"label": label, "report_path": report_path,
                        "writes_cap": writes_cap, "watch_off": watch_off,
                        "bp_ids": {}, "armed": False, "buf": None,
                        "watch_at": None, "cand_allocs": [], "writes": [],
                        "all_hits": 0, "errors": []}


def _s():
    if not hasattr(builtins, "l16_u8p"):
        reset()
    return builtins.l16_u8p


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
    return {n: hex(_u(f, n)) for n in ("rax", "rbx", "rcx", "rdx", "rdi",
                                       "rsi", "r8", "r9", "r12", "r13",
                                       "r14", "r15")}


def _stack(th, target, count=16):
    out = []
    for i in range(min(count, th.GetNumFrames())):
        fr = th.GetFrameAtIndex(i)
        pc = fr.GetPC()
        v = _va(target, pc)
        out.append({"i": i, "libcp_va": hex(v) if v is not None else None,
                    "fn": fr.GetFunctionName()})
    return out


def malloc_entry(frame, _bp_loc, _d):
    st = _s()
    if st["armed"]:
        return False
    size = _u(frame, "rdi")
    if not (SIZE_LO <= size <= SIZE_HI):
        return False
    # Grab the return pointer by stepping out to the caller, reading rax.
    proc = frame.GetThread().GetProcess()
    target = proc.GetTarget()
    th = frame.GetThread()
    err = builtins.__import__("lldb").SBError()
    th.StepOut()
    ret = th.GetFrameAtIndex(0)
    buf = ret.FindRegister("rax").GetValueAsUnsigned()
    if not buf:
        st["errors"].append("no rax after stepout size=%d" % size)
        return False
    watch_at = buf + int(st["watch_off"])
    st["cand_allocs"].append({"buf": hex(buf), "size": size,
                              "watch_at": hex(watch_at)})
    wp = target.WatchAddress(watch_at, 1, False, True, err)
    if err.Success() and wp and wp.IsValid():
        st["armed"] = True
        st["buf"] = buf
        st["watch_at"] = watch_at
        bid = st["bp_ids"].get("malloc")
        bp = target.FindBreakpointByID(bid) if bid else None
        if bp and bp.IsValid():
            bp.SetEnabled(False)
        print("U8P_ARMED", hex(watch_at), "size", size)
    else:
        st["errors"].append("wp arm failed: " + str(err))
    return True   # stop so driver can resume cleanly


def install(debugger):
    st = _s()
    target = debugger.GetSelectedTarget()
    before = target.GetNumBreakpoints()
    debugger.HandleCommand("breakpoint set -n malloc")
    if target.GetNumBreakpoints() > before:
        bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
        bp.SetScriptCallbackFunction("u8tile_producer_watch_probe.malloc_entry")
        st["bp_ids"]["malloc"] = bp.GetID()
    print("U8P_INSTALLED", st["bp_ids"])


def drive(debugger, max_steps=4000000):
    lldb = builtins.__import__("lldb")
    target = debugger.GetSelectedTarget()
    proc = target.GetProcess()
    n = 0
    while proc.IsValid() and proc.GetState() == lldb.eStateStopped and n < max_steps:
        n += 1
        proc.Continue()
        if proc.GetState() != lldb.eStateStopped:
            break
        th = proc.GetSelectedThread()
        if th.GetStopReason() != lldb.eStopReasonWatchpoint:
            continue
        st = _s()
        st["all_hits"] += 1
        fr0 = th.GetFrameAtIndex(0)
        pc0 = fr0.GetPC()
        va0 = _va(target, pc0)
        # find first libcp frame (the producer), skipping system memmove/memset
        prod_i, prod_va = None, None
        for i in range(min(16, th.GetNumFrames())):
            v = _va(target, th.GetFrameAtIndex(i).GetPC())
            if v is not None:
                prod_i, prod_va = i, v
                break
        src = _u(fr0, "rsi")
        dst = _u(fr0, "rdi")
        ln = _u(fr0, "rdx")
        src_bytes = _read(proc, src, 32)
        now = _read(proc, st.get("watch_at", 0), 16)
        st["writes"].append({
            "n": len(st["writes"]) + 1,
            "top_pc_va": hex(va0) if va0 is not None else None,
            "top_fn": fr0.GetFunctionName(),
            "producer_frame_i": prod_i,
            "producer_va": hex(prod_va) if prod_va is not None else None,
            "memop_dst": hex(dst), "memop_src": hex(src), "memop_len": hex(ln),
            "src_bytes": list(src_bytes) if src_bytes else None,
            "watch_now": list(now) if now else None,
            "regs": _regs(fr0),
            "backtrace": _stack(th, target),
        })
        if len(st["writes"]) >= int(st["writes_cap"]):
            proc.Kill()
            break
    _s()["drive_steps"] = n
    print("U8P_DRIVE", n, "writes", len(_s()["writes"]))


def write_report(debugger, path=""):
    out = path or _s().get("report_path")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as h:
        json.dump(dict(_s()), h, indent=2, sort_keys=True, default=str)
    print("U8P_WROTE", out)
