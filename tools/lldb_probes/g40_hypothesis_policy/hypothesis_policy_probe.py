"""Capture stable StereoLayer hypothesis extents at their producer stores."""

import builtins
import hashlib
import json
import struct
import time


ANCHORS = {
    0x26BEBF: ("range_from_prior_layer", "r14"),
    0x26C15D: ("range_from_depth_provider", "rbx"),
    0x26C277: ("level0_full_lookup_seed", "rbx"),
}


def reset(label, output_path):
    builtins.g40_state = {
        "label": label,
        "output_path": output_path,
        "started": time.time(),
        "packets": [],
        "errors": [],
    }


def _state():
    return builtins.g40_state


def _reg(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    return data if error.Success() and data and len(data) == size else None


def _unpack(process, address, fmt):
    size = struct.calcsize(fmt)
    data = _read(process, address, size)
    return struct.unpack(fmt, data)[0] if data else None


def _u32(process, address):
    return _unpack(process, address, "<I")


def _i32(process, address):
    return _unpack(process, address, "<i")


def _u64(process, address):
    return _unpack(process, address, "<Q")


def _flush():
    state = _state()
    report = dict(state)
    report.pop("started", None)
    report["elapsed_s"] = round(time.time() - state["started"], 3)
    with open(state["output_path"], "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")


def hit(frame, bp_loc, internal_dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    pc = frame.GetPCAddress().GetFileAddress()
    kind, layer_reg = ANCHORS.get(pc, ("unknown", "rbx"))
    layer = _reg(frame, layer_reg)
    begin = _u64(process, layer + 0xE0)
    end = _u64(process, layer + 0xE8)
    lookup_count = ((end - begin) // 4) if begin and end and end >= begin else None
    mode = _u32(process, layer + 0xC)
    raw_upper = lookup_count if kind == "level0_full_lookup_seed" else _i32(process, layer + 0x23C)
    min_lower = 0 if kind == "level0_full_lookup_seed" else _i32(process, layer + 0x238)
    rounded = _reg(frame, "rax") & 0xFFFFFFFF
    packet = {
        "anchor": "0x%x" % pc,
        "kind": kind,
        "layer_ptr": layer,
        "mode": mode,
        "width": _u32(process, layer + 0x2A0),
        "height": _u32(process, layer + 0x2A4),
        "lookup_count": lookup_count,
        "raw_max_upper": raw_upper,
        "min_lower": min_lower,
        "rounded_extent": rounded,
        "formula_rounded": (
            ((raw_upper + mode - 1) // mode) * mode
            if raw_upper is not None and mode
            else None
        ),
        "store_matches_formula": (
            rounded == ((raw_upper + mode - 1) // mode) * mode
            if raw_upper is not None and mode
            else None
        ),
    }
    state["packets"].append(packet)
    _flush()
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    attached = []
    for index in range(target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(index)
        if not bp or not bp.IsValid() or bp.GetNumLocations() < 1:
            continue
        va = bp.GetLocationAtIndex(0).GetAddress().GetFileAddress()
        if va in ANCHORS:
            bp.SetScriptCallbackFunction("hypothesis_policy_probe.hit")
            attached.append("0x%x" % va)
    print("G40_ATTACHED %s" % ",".join(attached))


def finalize(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            path = module.GetFileSpec().fullpath
            state["libcp_sha256"] = hashlib.sha256(open(path, "rb").read()).hexdigest()
            break
    process = target.GetProcess()
    state["exit_status"] = process.GetExitStatus() if process else None
    _flush()
    print("G40_WROTE %s packets=%d" % (state["output_path"], len(state["packets"])))
