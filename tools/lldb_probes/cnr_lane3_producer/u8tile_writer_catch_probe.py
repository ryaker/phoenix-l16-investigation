"""u8tile_writer_catch_probe.py -- NAME the upstream writer of the byte plane.

Strategy (race-free, self-correcting):
  * hook malloc; when size is in the 522x522 u8-tile band, plant a ONE-SHOT
    breakpoint at the caller return address (*(rsp)) -- NOT SBThread.StepOut,
    which is fragile under Rosetta batch lldb.
  * the one-shot ret callback reads rax = fresh buffer, arms a 1-byte WRITE
    watchpoint at buf+watch_off, then lets the process run.
  * on the first write, VERIFY buf[0:64] is the doubled-u8 weight pattern
    (b[2i]==b[2i+1] for most pairs, values 0..255, not float32).  If it is,
    the faulting stack's first libcp frame above the mem-op is the PRODUCER:
    record full backtrace + store operands + source bytes, then kill.
    If not (float/garbage), DISARM and hunt the next candidate allocation.

Bounded: stops at the first verified byte write.
"""
import builtins
import json
import os
import struct

SIZE_LO = 272420   # 522*522 = 272484 u8 tile (distinct from ~274k float buffers)
SIZE_HI = 272560


def reset(label="", report_path="", watch_off=0x400):
    builtins.l16_wc = {"label": label, "report_path": report_path,
                       "watch_off": int(watch_off), "bp_ids": {},
                       "pending": False, "armed": False, "done": False,
                       "buf": None, "watch_at": None, "ret_bp_id": None,
                       "wp": None, "cands": [], "rejected": [], "hit": None,
                       "all_watch_hits": 0, "errors": []}


def _s():
    if not hasattr(builtins, "l16_wc"):
        reset()
    return builtins.l16_wc


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


def _stack(th, target, count=20):
    out = []
    for i in range(min(count, th.GetNumFrames())):
        fr = th.GetFrameAtIndex(i)
        v = _va(target, fr.GetPC())
        out.append({"i": i, "libcp_va": hex(v) if v is not None else None,
                    "fn": fr.GetFunctionName()})
    return out


def _looks_doubled_u8(b):
    """b: 64 bytes. True iff it looks like a DENSE horizontally-doubled u8 map.

    The proven byte-weight signature is adjacent-equal pairs (2x upsample) over
    a dense, high-entropy u8 field (e.g. 255,255,254,254,...).  Reject sparse
    zero/pointer buffers (which trivially satisfy equal-pairs via 0==0) and
    float32 buffers (which almost never have equal adjacent bytes)."""
    if not b or len(b) < 32:
        return False, "short"
    n = len(b)
    nz = sum(1 for x in b if x != 0)
    distinct = len(set(b))
    # doubled: try both phase alignments, take the better
    p0 = sum(1 for i in range(n // 2) if b[2 * i] == b[2 * i + 1])
    p1 = sum(1 for i in range((n - 1) // 2) if b[2 * i + 1] == b[2 * i + 2])
    pairs = n // 2
    eq = max(p0, p1)
    why = "eq=%d/%d nz=%d/%d distinct=%d" % (eq, pairs, nz, n, distinct)
    # A flat bright weight region (255,255,254,254,...) is a VALID target with
    # very few distinct values, so do NOT gate on distinctness.  Float buffers
    # fail the equal-pairs test; sparse zero/pointer buffers fail density.
    if nz < int(n * 0.6):
        return False, "sparse " + why
    if eq < int(pairs * 0.85):
        return False, "unpaired " + why
    return True, why


def malloc_entry(frame, _bp_loc, _d):
    st = _s()
    if st["done"] or st["pending"] or st["armed"]:
        return False
    size = _u(frame, "rdi")
    if not (SIZE_LO <= size <= SIZE_HI):
        return False
    proc = frame.GetThread().GetProcess()
    target = proc.GetTarget()
    rsp = _u(frame, "rsp")
    ret = _read(proc, rsp, 8)
    if not ret:
        st["errors"].append("no ret addr at malloc rsp")
        return False
    ret_addr = struct.unpack("<Q", ret)[0]
    before = target.GetNumBreakpoints()
    bp = target.BreakpointCreateByAddress(ret_addr)
    if not bp or not bp.IsValid():
        st["errors"].append("ret bp create failed @%x" % ret_addr)
        return False
    bp.SetScriptCallbackFunction("u8tile_writer_catch_probe.malloc_ret")
    bp.SetOneShot(True)
    st["ret_bp_id"] = bp.GetID()
    st["pending"] = True
    st["cands"].append({"size": size, "ret_addr": hex(ret_addr)})
    _ = before
    return False


def malloc_ret(frame, _bp_loc, _d):
    st = _s()
    if not st["pending"] or st["armed"] or st["done"]:
        return False
    proc = frame.GetThread().GetProcess()
    target = proc.GetTarget()
    buf = _u(frame, "rax")
    st["pending"] = False
    if not buf or buf < 0x1000:
        st["errors"].append("bad rax in malloc_ret")
        return False
    watch_at = buf + st["watch_off"]
    lldb = builtins.__import__("lldb")
    err = lldb.SBError()
    wp = target.WatchAddress(watch_at, 1, False, True, err)
    if err.Success() and wp and wp.IsValid():
        st["armed"] = True
        st["buf"] = buf
        st["watch_at"] = watch_at
        st["wp"] = wp.GetID()
    else:
        st["errors"].append("wp arm failed: " + str(err))
    return False


def _disarm(target):
    st = _s()
    if st.get("wp") is not None:
        target.DeleteWatchpoint(st["wp"])
    st["wp"] = None
    st["armed"] = False
    st["buf"] = None
    st["watch_at"] = None


def install(debugger):
    st = _s()
    target = debugger.GetSelectedTarget()
    before = target.GetNumBreakpoints()
    debugger.HandleCommand("breakpoint set -n malloc")
    if target.GetNumBreakpoints() > before:
        bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
        bp.SetScriptCallbackFunction("u8tile_writer_catch_probe.malloc_entry")
        st["bp_ids"]["malloc"] = bp.GetID()
    print("WC_INSTALLED", st["bp_ids"])


def drive(debugger, max_iter=2000000):
    lldb = builtins.__import__("lldb")
    target = debugger.GetSelectedTarget()
    proc = target.GetProcess()
    st = _s()
    n = 0
    while proc.IsValid() and proc.GetState() == lldb.eStateStopped and n < max_iter:
        n += 1
        proc.Continue()
        if proc.GetState() != lldb.eStateStopped:
            break
        th = proc.GetSelectedThread()
        if th.GetStopReason() != lldb.eStopReasonWatchpoint:
            continue
        st["all_watch_hits"] += 1
        fr0 = th.GetFrameAtIndex(0)
        buf = st.get("buf")
        # verify the region AROUND the just-written watch byte (guaranteed live
        # data, header-agnostic, fill-order-agnostic), plus the buffer head.
        wa = st.get("watch_at") or (buf + st["watch_off"] if buf else 0)
        around = _read(proc, wa - 48, 96) if wa else None
        head = _read(proc, buf, 64) if buf else None
        ok_a, why_a = _looks_doubled_u8(list(around) if around else None)
        ok_h, why_h = _looks_doubled_u8(list(head) if head else None)
        ok = ok_a or ok_h
        why = "around[%s] head[%s]" % (why_a, why_h)
        if not ok:
            # Deadlock-free: any non-doubled write -> disarm and hunt the next
            # candidate.  (Tiles are filled directly by the 2x upsample; the
            # first watched write of a real byte tile is already doubled.)
            st["rejected"].append({"buf": hex(buf) if buf else None,
                                   "why": why})
            _disarm(target)
            st["pending"] = False
            continue
        # verified byte-tile write -> capture producer
        prod_i, prod_va = None, None
        for i in range(min(20, th.GetNumFrames())):
            v = _va(target, th.GetFrameAtIndex(i).GetPC())
            if v is not None:
                prod_i, prod_va = i, v
                break
        src = _u(fr0, "rsi")
        st["hit"] = {
            "buf": hex(buf),
            "head_u8": list(head) if head else None,
            "around_u8": list(around) if around else None,
            "verify": why,
            "top_pc_va": hex(_va(target, fr0.GetPC())) if _va(target, fr0.GetPC()) is not None else None,
            "top_fn": fr0.GetFunctionName(),
            "producer_frame_i": prod_i,
            "producer_va": hex(prod_va) if prod_va is not None else None,
            "memop_dst": hex(_u(fr0, "rdi")),
            "memop_src": hex(src),
            "memop_len": hex(_u(fr0, "rdx")),
            "src_bytes": list(_read(proc, src, 48) or b""),
            "regs": _regs(fr0),
            "backtrace": _stack(th, target),
        }
        st["done"] = True
        proc.Kill()
        break
    st["drive_iter"] = n
    print("WC_DRIVE", n, "hit", bool(st.get("hit")), "rejected", len(st["rejected"]))


def write_report(debugger, path=""):
    out = path or _s().get("report_path")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as h:
        json.dump(dict(_s()), h, indent=2, sort_keys=True, default=str)
    print("WC_WROTE", out)
