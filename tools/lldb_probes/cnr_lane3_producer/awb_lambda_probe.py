"""awb_lambda_probe.py -- capture the setWhiteBalance $_22 lambda's inputs live.

RTTI proved the CNR lane-3 guide is produced inside
  lt::Internal::Pipeline::setWhiteBalance(PipelineBase::AWB)::$_22
  void(SoftISP::Stats&, Image<unsigned short> const&, CapturedImage const&,
       Rectangle<int> const&)
The guide (task+0x60, half-res [~0.48,1.0]) must derive from one of those inputs.
This probe CHECKS LUMEN directly: at the CNR body 0x34b3f0 the functor (rdi) is
in hand; we read its libc++ __func vtable and resolve operator() = vtable[4],
break there, and capture the live args:
  rsi = SoftISP::Stats&      rdx = Image<unsigned short>&
  rcx = CapturedImage&       r8  = Rectangle<int>&
plus the guide (task+0x60) at the same 0x34b3f0 hit, so guide-vs-Image<u16> can
be matched offline.  Nothing inferred; bytes recorded.
"""

import builtins
import hashlib
import json
import os
import struct

CNRBODY = 0x34B3F0   # rdi=setWhiteBalance $_22 functor, rsi=denoise task
VT_OPERATOR_SLOT = 4  # libc++ __func vtable: __clone,__clone,destroy,dealloc,operator()


def reset(label="", report_path="", cap=4):
    builtins.l16_awb = {
        "label": label, "report_path": report_path, "cap": cap,
        "breakpoint_ids": {}, "op_bp_installed": False,
        "cnr_events": [], "op_events": [], "errors": [],
    }


def _s():
    if not hasattr(builtins, "l16_awb"):
        reset()
    return builtins.l16_awb


def _u(f, n):
    return f.FindRegister(n).GetValueAsUnsigned()


def _read(proc, addr, size):
    if not addr or addr < 0x1000 or addr > 0x00007FFFFFFFFFFF:
        return None
    lldb = builtins.__import__("lldb")
    err = lldb.SBError()
    try:
        data = proc.ReadMemory(addr, size, err)
    except Exception:
        return None
    return data if err.Success() and data and len(data) == size else None


def _q(proc, addr):
    d = _read(proc, addr, 8)
    return struct.unpack("<Q", d)[0] if d else 0


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


def _cstr(proc, addr, maxlen=200):
    if not addr:
        return None
    out = b""
    for _ in range(maxlen):
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
    if not ti:
        return {"vtable": vt}
    nm = _q(proc, ti + 8)
    return {"vtable": vt, "name": _cstr(proc, nm)}


def _regs(f):
    return {n: _u(f, n) for n in ("rdi", "rsi", "rdx", "rcx", "r8", "r9",
                                  "rbp", "rsp")}


def _img16(proc, addr, sample_rows=6, cols=80):
    """Decode an Image<unsigned short>: +0x10 w,+0x14 h,+0x18 stride,+0x20 data.
    stride is in ELEMENTS; elements are 2-byte uint16."""
    raw = _read(proc, addr, 0x30)
    if raw is None:
        return {"addr": addr, "read_ok": False}
    w, h, stride = struct.unpack_from("<iii", raw, 0x10)
    data = struct.unpack_from("<Q", raw, 0x20)[0]
    out = {"addr": addr, "read_ok": True, "width": w, "height": h,
           "stride": stride, "data_ptr": data}
    if data and 0 < w < 20000 and 0 < h < 20000 and stride > 0:
        rows = []
        allv = []
        for r in range(min(sample_rows, h)):
            row = _read(proc, data + (r * stride) * 2, min(w, cols) * 2)
            if row is None:
                rows.append(None)
                continue
            vals = list(struct.unpack("<" + "H" * (len(row) // 2), row))
            rows.append(vals)
            allv.extend(vals)
        out["rows_u16"] = rows
        if allv:
            out["stats"] = {"min": min(allv), "max": max(allv),
                            "mean": sum(allv) / len(allv), "n": len(allv)}
    return out


def _guide_native(proc, task):
    raw = _read(proc, task, 0x80)
    if raw is None:
        return {"read_ok": False}
    data = struct.unpack_from("<Q", raw, 0x60)[0]
    w, h = struct.unpack_from("<ii", raw, 0x50)
    stride = struct.unpack_from("<i", raw, 0x58)[0]
    g = {"read_ok": True, "data_ptr": data, "dims": [w, h], "stride": stride}
    if data and 0 < w < 20000 and stride > 0:
        rows = []
        allv = []
        for r in range(min(6, h)):
            row = _read(proc, data + (r * stride) * 4, min(w, 80) * 4)
            if row is None:
                continue
            vals = list(struct.unpack("<" + "f" * (len(row) // 4), row))
            rows.append(vals)
            allv.extend(vals)
        g["rows_f32"] = rows
        if allv:
            g["stats"] = {"min": min(allv), "max": max(allv),
                          "mean": sum(allv) / len(allv)}
    return g


def op_call(frame, bp_loc, _d):
    """setWhiteBalance $_22 operator(): capture the live inputs."""
    st = _s()
    proc = frame.GetThread().GetProcess()
    target = proc.GetTarget()
    regs = _regs(frame)
    ev = {
        "seq": len(st["op_events"]) + 1,
        "site_va": _va(target, frame.GetPC()),
        "regs": regs,
        "rtti_this_rdi": _rtti(proc, regs["rdi"]),
        "rtti_rsi_stats": _rtti(proc, regs["rsi"]),
        "rtti_rdx_image": _rtti(proc, regs["rdx"]),
        "rtti_rcx_captured": _rtti(proc, regs["rcx"]),
        "image_u16_rdx": _img16(proc, regs["rdx"]),
        "rectangle_r8": struct.unpack("<4i", _read(proc, regs["r8"], 16))
        if _read(proc, regs["r8"], 16) else None,
    }
    st["op_events"].append(ev)
    if len(st["op_events"]) >= int(st["cap"]):
        bid = st["breakpoint_ids"].get("operator")
        bp = target.FindBreakpointByID(bid) if bid else None
        if bp and bp.IsValid():
            bp.SetEnabled(False)
        proc.Kill()
    return False


def cnr_body(frame, bp_loc, _d):
    """0x34b3f0: resolve operator() from functor vtable, install its bp once;
    capture the guide for same-tile matching."""
    st = _s()
    proc = frame.GetThread().GetProcess()
    target = proc.GetTarget()
    regs = _regs(frame)
    functor = regs["rdi"]
    task = regs["rsi"]
    st["cnr_events"].append({
        "seq": len(st["cnr_events"]) + 1,
        "functor": functor, "task": task,
        "rtti_functor": _rtti(proc, functor),
        "guide": _guide_native(proc, task),
    })
    if not st["op_bp_installed"]:
        vtable = _q(proc, functor)
        opaddr = _q(proc, vtable + VT_OPERATOR_SLOT * 8)
        st["operator_addr"] = opaddr
        st["operator_va"] = _va(target, opaddr)
        if opaddr:
            debugger = target.GetDebugger()
            before = target.GetNumBreakpoints()
            debugger.HandleCommand(f"breakpoint set --address 0x{opaddr:x}")
            if target.GetNumBreakpoints() > before:
                bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
                bp.SetScriptCallbackFunction("awb_lambda_probe.op_call")
                st["breakpoint_ids"]["operator"] = bp.GetID()
                st["op_bp_installed"] = True
    if len(st["cnr_events"]) >= 3:
        bid = st["breakpoint_ids"].get("cnr")
        bp = target.FindBreakpointByID(bid) if bid else None
        if bp and bp.IsValid():
            bp.SetEnabled(False)
    return False


def install(debugger):
    st = _s()
    target = debugger.GetSelectedTarget()
    before = target.GetNumBreakpoints()
    debugger.HandleCommand("breakpoint set --shlib libcp.dylib --address 0x34b3f0")
    if target.GetNumBreakpoints() > before:
        bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
        bp.SetScriptCallbackFunction("awb_lambda_probe.cnr_body")
        st["breakpoint_ids"]["cnr"] = bp.GetID()
    print("AWB_LAMBDA_INSTALLED", st["breakpoint_ids"])


def drive(debugger, max_steps=60000):
    lldb = builtins.__import__("lldb")
    st = _s()
    proc = debugger.GetSelectedTarget().GetProcess()
    n = 0
    while proc.IsValid() and proc.GetState() == lldb.eStateStopped and n < max_steps:
        n += 1
        proc.Continue()
    st["drive_steps"] = n
    print("AWB_LAMBDA_DRIVE", n)


def write_report(debugger, path=""):
    out = path or _s().get("report_path")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as h:
        json.dump(dict(_s()), h, indent=2, sort_keys=True, default=str)
    print("WROTE", out)
