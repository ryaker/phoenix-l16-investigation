"""Capture the 3x3 integer costs and exact guarded float refinement outputs."""

import builtins
import hashlib
import json
import struct
import time


SITES = {
    0x369B1F: "costs_ready",
    0x369C72: "raw_offsets_ready",
    0x369CB0: "accepted_offsets_ready",
}


def reset(label, output_path, cap=24):
    builtins.g49_state = {
        "label": label,
        "output_path": output_path,
        "cap": cap,
        "started": time.time(),
        "packets": [],
        "current_by_thread": {},
        "counts": {name: 0 for name in SITES.values()},
        "breakpoint_ids": [],
        "errors": [],
        "done": False,
    }


def _state():
    return builtins.g49_state


def _reg(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    return data if error.Success() and data and len(data) == size else None


def _xmm(frame, name):
    lldb = builtins.__import__("lldb")
    data = frame.FindRegister(name).GetData()
    error = lldb.SBError()
    raw = bytes(data.GetUnsignedInt8(error, index) for index in range(data.GetByteSize()))
    if not error.Success() or len(raw) < 16:
        return None
    return list(struct.unpack_from("<4f", raw))


def _flush():
    state = _state()
    report = dict(state)
    report.pop("started", None)
    report["elapsed_s"] = round(time.time() - state["started"], 3)
    with open(state["output_path"], "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")


def _disable_all(target):
    for bp_id in _state()["breakpoint_ids"]:
        bp = target.FindBreakpointByID(bp_id)
        if bp and bp.IsValid():
            bp.SetEnabled(False)


def hit(frame, bp_loc, internal_dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    va = frame.GetPCAddress().GetFileAddress()
    name = SITES.get(va)
    if name is None:
        state["errors"].append("unexpected VA 0x%x" % va)
        return False
    state["counts"][name] += 1
    tid = str(frame.GetThread().GetThreadID())
    rbp = _reg(frame, "rbp")

    if name == "costs_ready":
        raw = _read(process, rbp - 0x1A0, 9 * 4)
        if raw is None:
            state["errors"].append("unreadable 3x3 cost table")
            return False
        state["current_by_thread"][tid] = {
            "thread_id": int(tid),
            "costs_u32_row_major": list(struct.unpack("<9I", raw)),
            "coarse_r11_i32": struct.unpack("<i", struct.pack("<I", _reg(frame, "r11") & 0xFFFFFFFF))[0],
            "coarse_stack_0x4360_i64": struct.unpack(
                "<q", _read(process, rbp - 0x4360, 8)
            )[0],
        }
    elif name == "raw_offsets_ready":
        packet = state["current_by_thread"].get(tid)
        if packet is not None:
            packet["raw_offset_x"] = _xmm(frame, "xmm4")[0]
            packet["raw_offset_y"] = _xmm(frame, "xmm5")[0]
            packet["denominator_after_div"] = _xmm(frame, "xmm1")[0]
    elif name == "accepted_offsets_ready":
        packet = state["current_by_thread"].pop(tid, None)
        if packet is None:
            state["errors"].append("accepted offset without matching costs")
            return False
        packet["accepted_offset_x"] = _xmm(frame, "xmm4")[0]
        packet["accepted_offset_y"] = _xmm(frame, "xmm5")[0]
        packet["coord_bases"] = {
            "xmm9": _xmm(frame, "xmm9")[0],
            "xmm8": _xmm(frame, "xmm8")[0],
            "xmm3": _xmm(frame, "xmm3")[0],
            "xmm10": _xmm(frame, "xmm10")[0],
        }
        state["packets"].append(packet)
        _flush()
        if len(state["packets"]) >= state["cap"]:
            state["done"] = True
            _disable_all(target)
            process.Kill()
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    attached = []
    for index in range(target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(index)
        if not bp or not bp.IsValid() or bp.GetNumLocations() < 1:
            continue
        va = bp.GetLocationAtIndex(0).GetAddress().GetFileAddress()
        if va in SITES:
            bp.SetScriptCallbackFunction("subpixel_refinement_probe.hit")
            _state()["breakpoint_ids"].append(bp.GetID())
            attached.append("0x%x" % va)
    print("G49_ATTACHED %s" % ",".join(attached))


def finalize(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            path = module.GetFileSpec().fullpath
            state["libcp_sha256"] = hashlib.sha256(open(path, "rb").read()).hexdigest()
            break
    _flush()
    print("G49_WROTE %s packets=%d" % (state["output_path"], len(state["packets"])))
