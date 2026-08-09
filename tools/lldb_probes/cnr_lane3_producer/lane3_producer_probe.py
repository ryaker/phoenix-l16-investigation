"""lane3_producer_probe.py -- close the D1 CNR lane-3 producer.

D1 (verify_cnr_alpha_lane.py) proves the CNR worker formula is bit-exact ONLY
when the per-pixel alpha lane (vec4 lane 3) of the source tile is fed correctly;
Phoenix has no lane 3 and hardcodes meanA=1, giving 0/16 vs 16/16.  The lane-3
plane is written upstream by 0x308f50, dispatched from 0x307ee0.  Static
disassembly (this session) shows 0x308f50's inner loop is
    movss (guide); mulss xmm0,xmm0; movss -> dst lane 3 (+0xc, stride 0x10)
i.e. lane3 = guide^2.  The one thing static cannot say is WHICH pipeline image
is the guide (arg2/rdx of 0x307ee0).  This probe captures that at runtime:
  * both image descriptors at the 0x307ee0 dispatch (arg1 rdi = dst being
    filled, arg2 rdx = guide),
  * whether the guide-empty arm (data ptr +0x20 == 0 -> lane3:=1.0) or the
    producer arm is taken,
  * the guide's dims / stride / data ptr and a sample of its first rows,
  * the call stack, so the producing STAGE is named, not guessed,
  * a few 0x30905e stores (xmm0 = squared value) as a runtime re-confirm of the
    square.

Zero interpretation in the probe: it records bytes and registers.  The identity
argument is made afterward from the captured dims + stack + data.

Image struct layout (from disasm of 0x307ee0 / 0x308f50):
    +0x10 int32 width      +0x14 int32 height
    +0x18 int32 stride (float elements per row)
    +0x20 ptr   data (float32 plane; guide is 1 float/pixel)
"""

import builtins
import hashlib
import json
import os
import struct

TASK     = 0x34B3F0   # CNR route fn: rdi=context r14, rsi=denoise task rbx
DISPATCH = 0x307EE0   # rdi=dst image, rdx=guide image
PRODUCER = 0x308F50   # rdi=dst wrapper, rsi=&guide-struct-ptr
STORE    = 0x30905E   # right after: mulss xmm0,xmm0 ; movss xmm0,(rdx,rcx,4)

SITES = {TASK: "task_entry", DISPATCH: "dispatch", PRODUCER: "producer",
         STORE: "lane3_store"}


def reset(label="", report_path="", dispatch_cap=8, store_cap=8, task_cap=3):
    builtins.l16_lane3 = {
        "label": label,
        "report_path": report_path,
        "dispatch_cap": dispatch_cap,
        "store_cap": store_cap,
        "task_cap": task_cap,
        "breakpoint_ids": {},
        "task_events": [],
        "dispatch_events": [],
        "store_events": [],
        "disabled": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_lane3"):
        reset()
    return builtins.l16_lane3


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    if not addr:
        return None
    lldb = builtins.__import__("lldb")
    err = lldb.SBError()
    data = process.ReadMemory(addr, size, err)
    return data if err.Success() and len(data) == size else None


def _i32s(data):
    return list(struct.unpack("<" + "i" * (len(data) // 4), data))


def _f32s(data):
    return list(struct.unpack("<" + "f" * (len(data) // 4), data))


def _u64(data, off=0):
    return struct.unpack_from("<Q", data, off)[0]


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


def _xmm(frame, name):
    lldb = builtins.__import__("lldb")
    d = frame.FindRegister(name).GetData()
    err = lldb.SBError()
    raw = d.ReadRawData(err, 0, 16)
    if not (err.Success() and len(raw) == 16):
        return None
    return {"f32": _f32s(raw), "hex": raw.hex()}


def _regs(frame):
    names = ("rax", "rbx", "rcx", "rdx", "rdi", "rsi", "r8", "r9",
             "r12", "r13", "r14", "r15", "rbp", "rsp")
    return {n: _u(frame, n) for n in names}


def _descriptor(process, addr):
    """Read an image struct and decode the known fields."""
    raw = _read(process, addr, 0x30)
    if raw is None:
        return {"addr": addr, "read_ok": False}
    i32 = _i32s(raw)
    return {
        "addr": addr,
        "read_ok": True,
        "hex": raw.hex(),
        "width": i32[4],       # +0x10
        "height": i32[5],      # +0x14
        "stride": i32[6],      # +0x18
        "data_ptr": _u64(raw, 0x20),
        "i32": i32,
    }


def _plane_sample(process, desc, rows=4, max_cols=64):
    """Sample the first `rows` rows of a single-channel float32 plane."""
    if not desc.get("read_ok") or not desc.get("data_ptr"):
        return {"sampled": False, "reason": "no data ptr"}
    w = desc["width"]
    stride = desc["stride"]
    dptr = desc["data_ptr"]
    if w <= 0 or stride <= 0 or desc["height"] <= 0:
        return {"sampled": False, "reason": "bad dims", "w": w,
                "h": desc["height"], "stride": stride}
    cols = min(w, max_cols)
    out_rows = []
    all_vals = []
    nr = min(rows, desc["height"])
    for r in range(nr):
        addr = dptr + (r * stride) * 4
        raw = _read(process, addr, cols * 4)
        if raw is None:
            out_rows.append(None)
            continue
        vals = _f32s(raw)
        out_rows.append(vals)
        all_vals.extend(vals)
    stats = None
    if all_vals:
        stats = {
            "n": len(all_vals),
            "min": min(all_vals),
            "max": max(all_vals),
            "mean": sum(all_vals) / len(all_vals),
        }
    fp = None
    first_full = _read(process, dptr, min(w, 4096) * 4)
    if first_full is not None:
        fp = hashlib.sha256(first_full).hexdigest()
    return {"sampled": True, "cols": cols, "rows": out_rows,
            "stats": stats, "first_row_sha256": fp}


def _stack(thread, target, n=10):
    out = []
    for i in range(min(thread.GetNumFrames(), n)):
        f = thread.GetFrameAtIndex(i)
        out.append({"i": i, "pc": f.GetPC(), "libcp_va": _va(target, f.GetPC()),
                    "fn": f.GetFunctionName()})
    return out


def _disable(target, name):
    st = _state()
    bid = st["breakpoint_ids"].get(name)
    bp = target.FindBreakpointByID(bid) if bid else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)
    if name not in st["disabled"]:
        st["disabled"].append(name)


def _maybe_kill(frame):
    st = _state()
    if (len(st["dispatch_events"]) >= int(st["dispatch_cap"])
            and len(st["store_events"]) >= int(st["store_cap"])):
        frame.GetThread().GetProcess().Kill()


def _raw(process, addr, size):
    raw = _read(process, addr, size)
    return raw.hex() if raw is not None else None


def _task_guide(process, task_ptr):
    """Decode the denoise task's guide member from its known offsets.

    From static disasm of 0x34b3f0 (0x34b47d..): guide data=task+0x60,
    stride=task+0x58, dims=task+0x50, bounds=task+0x40, crop=task+0x20..0x2c.
    """
    raw = _read(process, task_ptr, 0x80)
    if raw is None:
        return {"read_ok": False, "task_ptr": task_ptr}
    def i32(off):
        return struct.unpack_from("<i", raw, off)[0]
    def u64(off):
        return struct.unpack_from("<Q", raw, off)[0]
    data_ptr = u64(0x60)
    dims = (i32(0x50), i32(0x54))
    stride = i32(0x58)
    bounds = [i32(0x40), i32(0x44), i32(0x48), i32(0x4c)]
    crop = [i32(0x20), i32(0x24), i32(0x28), i32(0x2c)]
    guide_desc = {
        "read_ok": True, "task_ptr": task_ptr, "task_hex": raw.hex(),
        "guide_data_ptr": data_ptr, "guide_dims": dims, "guide_stride": stride,
        "guide_bounds": bounds, "guide_crop": crop,
        "companion_ptr_0x68": u64(0x68),
    }
    # native-resolution sample of the guide plane
    if data_ptr and dims[0] > 0 and dims[1] > 0 and stride > 0:
        d = {"read_ok": True, "width": dims[0], "height": dims[1],
             "stride": stride, "data_ptr": data_ptr}
        guide_desc["native_sample"] = _plane_sample(process, d, rows=6,
                                                     max_cols=80)
    return guide_desc


def task_entry(frame, bp_loc, _d):
    st = _state()
    proc = frame.GetThread().GetProcess()
    thread = frame.GetThread()
    target = proc.GetTarget()
    regs = _regs(frame)
    ev = {
        "seq": len(st["task_events"]) + 1,
        "site_va": _va(target, frame.GetPC()),
        "context_rdi": regs["rdi"],       # r14 render context
        "task_rsi": regs["rsi"],          # denoise task
        "task_guide": _task_guide(proc, regs["rsi"]),
        # a window of the context, in case the guide ptr matches a context slot
        "context_head_hex": _raw(proc, regs["rdi"], 0x120),
        "stack": _stack(thread, target),
    }
    st["task_events"].append(ev)
    if len(st["task_events"]) >= int(st["task_cap"]):
        _disable(target, "task_entry")
    return False


def dispatch(frame, bp_loc, _d):
    st = _state()
    proc = frame.GetThread().GetProcess()
    thread = frame.GetThread()
    target = proc.GetTarget()
    regs = _regs(frame)
    guide = _descriptor(proc, regs["rdx"])   # arg2 = guide
    dst = _descriptor(proc, regs["rdi"])     # arg1 = dst being filled
    guide_empty = not bool(guide.get("data_ptr"))
    ev = {
        "seq": len(st["dispatch_events"]) + 1,
        "site_va": _va(target, frame.GetPC()),
        "thread": thread.GetThreadID(),
        "registers": regs,
        "guide_descriptor": guide,
        "dst_descriptor": dst,
        "guide_empty_arm": guide_empty,
        "xmm0": _xmm(frame, "xmm0"),
        "xmm1": _xmm(frame, "xmm1"),
        "guide_sample": None if guide_empty else _plane_sample(proc, guide),
        "stack": _stack(thread, target),
    }
    st["dispatch_events"].append(ev)
    if len(st["dispatch_events"]) >= int(st["dispatch_cap"]):
        _disable(target, "dispatch")
    _maybe_kill(frame)
    return False


def lane3_store(frame, bp_loc, _d):
    st = _state()
    proc = frame.GetThread().GetProcess()
    target = proc.GetTarget()
    regs = _regs(frame)
    dst_addr = regs["rdx"] + regs["rcx"] * 4
    stored = _read(proc, dst_addr, 4)
    ev = {
        "seq": len(st["store_events"]) + 1,
        "site_va": _va(target, frame.GetPC()),
        "squared_xmm0": _xmm(frame, "xmm0"),
        "dst_store_addr": dst_addr,
        "stored_f32": _f32s(stored) if stored else None,
    }
    st["store_events"].append(ev)
    if len(st["store_events"]) >= int(st["store_cap"]):
        _disable(target, "lane3_store")
    _maybe_kill(frame)
    return False


def install(debugger):
    st = _state()
    target = debugger.GetSelectedTarget()
    cbs = {
        TASK: "lane3_producer_probe.task_entry",
        DISPATCH: "lane3_producer_probe.dispatch",
        STORE: "lane3_producer_probe.lane3_store",
    }
    for va, cb in cbs.items():
        before = target.GetNumBreakpoints()
        debugger.HandleCommand(
            f"breakpoint set --shlib libcp.dylib --address 0x{va:x}")
        if target.GetNumBreakpoints() <= before:
            st["errors"].append(f"bp failed 0x{va:x}")
            continue
        bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
        bp.SetScriptCallbackFunction(cb)
        st["breakpoint_ids"][SITES[va]] = bp.GetID()
    print("L16_LANE3_INSTALLED", st["breakpoint_ids"])


def drive_until_exit_or_step_cap(debugger, max_steps=40000):
    lldb = builtins.__import__("lldb")
    st = _state()
    proc = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while (proc.IsValid() and proc.GetState() == lldb.eStateStopped
           and steps < max_steps):
        steps += 1
        proc.Continue()
    st["drive_steps"] = steps
    print("L16_LANE3_DRIVE_STEPS", steps)


def _bp_hits(debugger):
    target = debugger.GetSelectedTarget()
    out = {}
    for name, bid in _state().get("breakpoint_ids", {}).items():
        bp = target.FindBreakpointByID(bid)
        out[name] = bp.GetHitCount() if bp and bp.IsValid() else None
    return out


def payload(debugger):
    lldb = builtins.__import__("lldb")
    proc = debugger.GetSelectedTarget().GetProcess()
    ps = {
        "valid": proc.IsValid() if proc else False,
        "state": lldb.SBDebugger.StateAsCString(proc.GetState()) if proc else None,
        "exit_status": proc.GetExitStatus() if proc and proc.IsValid() else None,
    }
    return {"process": ps, "breakpoint_hit_counts": _bp_hits(debugger),
            **dict(_state())}


def write_report(debugger, path=""):
    out = path or _state().get("report_path")
    if not out:
        raise RuntimeError("no report path")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as h:
        json.dump(payload(debugger), h, indent=2, sort_keys=True)
        h.write("\n")
    print("WROTE", out)


def report(debugger):
    print(json.dumps(payload(debugger), indent=2, sort_keys=True))
