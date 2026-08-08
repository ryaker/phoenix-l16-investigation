# G-43 direction-vector probe. Arms at index-5 (2080x1560) via the v2 dynamic-bp
# template, then captures per-pixel base pointers at the recurrence pre-loop
# setup 0x27799b (hit once per pixel, NOT per disparity -> cheap with a cap).
# In the recurrence loop 0x2779b0: rsi/rdi = predecessor path-cost bases,
# rcx = current Line buf write base, r9 = Cost-volume payload base, r10 = local
# matching-cost temp; rdx steps disparities. Consecutive-pixel deltas in r9
# (scan step) and (rcx - rsi) (predecessor offset) enumerate the scan direction.
import builtins
import json
import struct
import time

ANCHOR = 0x276860
SETUP = 0x27799B   # pre-loop setup: base ptrs live, once per pixel


def reset(label="", cap_w=2080, cap_h=1560, pixel_cap=120, progress_path=None):
    builtins.l16dir = {
        "label": label, "cap_w": cap_w, "cap_h": cap_h,
        "pixel_cap": pixel_cap, "progress_path": progress_path,
        "t0": time.time(), "anchor_hits": 0, "armed": False,
        "ecx_index5_seq": [], "stride_0x158": None, "hyp_0xe0": None,
        "caps": [], "done": False, "setup_bp": None, "anchor_bp": None,
        "_dims": {}, "_base": None, "errors": [],
    }


def _s():
    if not hasattr(builtins, "l16dir"):
        reset()
    return builtins.l16dir


def _u(frame, n):
    return frame.FindRegister(n).GetValueAsUnsigned()


def _rd(process, addr, size):
    if not addr or size <= 0:
        return None
    lldb = builtins.__import__("lldb")
    e = lldb.SBError()
    d = process.ReadMemory(addr, size, e)
    return d if (e.Success() and d and len(d) == size) else None


def _u32(p, a):
    d = _rd(p, a, 4)
    return struct.unpack_from("<I", d)[0] if d else None


def _u64(p, a):
    d = _rd(p, a, 8)
    return struct.unpack_from("<Q", d)[0] if d else None


def _base(target):
    st = _s()
    if st["_base"] is not None:
        return st["_base"]
    for m in target.module_iter():
        if str(m.GetFileSpec().GetFilename()) == "libcp.dylib":
            b = m.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if b != 0xFFFFFFFFFFFFFFFF:
                st["_base"] = b
                return b
    return None


def _va(target, pc):
    b = _base(target)
    return pc - b if (b is not None and pc >= b) else None


def _flush():
    st = _s()
    p = st.get("progress_path")
    if not p:
        return
    snap = {k: st[k] for k in ("label", "anchor_hits", "armed", "done",
            "ecx_index5_seq", "stride_0x158", "hyp_0xe0")}
    snap["elapsed_s"] = round(time.time() - st["t0"], 1)
    snap["n_caps"] = len(st["caps"])
    snap["caps_tail"] = st["caps"][-6:]
    try:
        with open(p, "w", encoding="utf-8") as h:
            json.dump(snap, h, indent=2, sort_keys=True)
    except Exception as exc:  # noqa
        st["errors"].append("flush:%s" % exc)


def hit(frame, bp_loc, internal_dict):
    st = _s()
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    va = _va(target, frame.GetPC())
    if va == ANCHOR:
        st["anchor_hits"] += 1
        rdi = _u(frame, "rdi")
        ecx = _u(frame, "rcx") & 0xFFFFFFFF
        ecx_s = ecx - (1 << 32) if ecx >= (1 << 31) else ecx
        dims = st["_dims"].get(rdi)
        if dims is None:
            guide = _u64(process, rdi + 0x288)
            dims = (_u32(process, (guide or 0) + 0x10),
                    _u32(process, (guide or 0) + 0x14))
            st["_dims"][rdi] = dims
        if dims == (st["cap_w"], st["cap_h"]):
            if len(st["ecx_index5_seq"]) < 200:
                st["ecx_index5_seq"].append(ecx_s)
            if not st["armed"]:
                st["armed"] = True
                st["stride_0x158"] = _u64(process, rdi + 0x158)
                b0 = _u64(process, rdi + 0xE0)
                b1 = _u64(process, rdi + 0xE8)
                st["hyp_0xe0"] = ((b1 - b0) // 4) if (b0 and b1) else None
                bp = target.BreakpointCreateByAddress(_base(target) + SETUP)
                bp.SetScriptCallbackFunction("g43_dir_probe.hit")
                st["setup_bp"] = bp.GetID()
                _flush()
        return False
    if va == SETUP:
        if st["done"]:
            return False
        cap = {
            "n": len(st["caps"]),
            "anchor_n_at_cap": st["anchor_hits"],
            "rsi": _u(frame, "rsi"), "rdi": _u(frame, "rdi"),
            "rcx": _u(frame, "rcx"), "r9": _u(frame, "r9"),
            "r10": _u(frame, "r10"), "r13": _u(frame, "r13"),
            "rbx": _u(frame, "rbx"), "rax": _u(frame, "rax"),
            "rdx": _u(frame, "rdx") & 0xFFFFFFFF,
            "tid": thread.GetThreadID(),
        }
        st["caps"].append(cap)
        if len(st["caps"]) % 20 == 0:
            _flush()
        if len(st["caps"]) >= st["pixel_cap"]:
            st["done"] = True
            bp = target.FindBreakpointByID(st["setup_bp"])
            if bp and bp.IsValid():
                bp.SetEnabled(False)
            _flush()
            process.Kill()
            return True
        return False
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    for i in range(target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(i)
        if not bp or not bp.IsValid() or bp.GetNumLocations() < 1:
            continue
        va = bp.GetLocationAtIndex(0).GetAddress().GetFileAddress()
        if va == ANCHOR:
            bp.SetScriptCallbackFunction("g43_dir_probe.hit")
            _s()["anchor_bp"] = bp.GetID()
    print("L16_G43DIR_ATTACHED")


def drive(debugger, max_steps=20000000):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while (process.IsValid() and process.GetState() == lldb.eStateStopped
           and steps < max_steps and not _s()["done"]):
        steps += 1
        process.Continue()
    _flush()
    print("L16_G43DIR_DRIVE_DONE steps=%s" % steps)


def write_report(debugger, path):
    import hashlib
    st = dict(_s())
    target = debugger.GetSelectedTarget()
    for m in target.module_iter():
        if str(m.GetFileSpec().GetFilename()) == "libcp.dylib":
            try:
                st["libcp_sha256"] = hashlib.sha256(
                    open(m.GetFileSpec().fullpath, "rb").read()).hexdigest()
            except Exception as exc:  # noqa
                st["libcp_sha256"] = "err:%s" % exc
    with open(path, "w", encoding="utf-8") as h:
        json.dump(st, h, indent=2, sort_keys=True)
        h.write("\n")
    print("L16_G43DIR_WROTE %s" % path)
