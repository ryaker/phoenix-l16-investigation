import builtins
import json
import os
import struct


INTERP_ENTRY = 0x350BC0
LERP_RETURN = 0x350C56


def reset(label="", sample_cap=32, entry_only=False):
    builtins.l16_ccm_illuminant_selection = {
        "label": label,
        "sample_cap": sample_cap,
        "entry_only": bool(entry_only),
        "breakpoints": {},
        "pending": {},
        "samples": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_ccm_illuminant_selection"):
        reset()
    return builtins.l16_ccm_illuminant_selection


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _snapshot(process, address, size):
    data = _read(process, address, size)
    return {
        "address": address,
        "size": size,
        "read_ok": data is not None,
        "hex": data.hex() if data is not None else None,
    }


def _f32(process, address):
    data = _read(process, address, 4)
    return struct.unpack("<f", data)[0] if data is not None else None


def _u32(process, address):
    data = _read(process, address, 4)
    return struct.unpack("<I", data)[0] if data is not None else None


def entry_hit(frame, bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    thread_id = frame.GetThread().GetThreadID()
    xy = _u(frame, "rsi")
    calib = _u(frame, "rdx")
    packet = {
        "thread_id": thread_id,
        "xy": _snapshot(process, xy, 8),
        "calib": _snapshot(process, calib, 0x58),
        "illuminant_1": _u32(process, calib + 0x08),
        "illuminant_2": _u32(process, calib + 0x0C),
        "matrix_1": _snapshot(process, calib + 0x10, 36),
        "matrix_2": _snapshot(process, calib + 0x34, 36),
    }
    if state["entry_only"]:
        state["samples"].append(packet)
        bp_loc.GetBreakpoint().SetEnabled(False)
    else:
        state["pending"][str(thread_id)] = packet
    return False


def lerp_return_hit(frame, bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    thread_id = frame.GetThread().GetThreadID()
    packet = state["pending"].pop(str(thread_id), None)
    if packet is None:
        return False
    rbp = _u(frame, "rbp")
    packet["target_cct"] = _f32(process, rbp - 0x64)
    packet["calibration_cct_1"] = _f32(process, rbp - 0x68)
    packet["calibration_cct_2"] = _f32(process, rbp - 0x6C)
    packet["interpolated_matrix"] = _snapshot(process, rbp - 0x60, 36)
    state["samples"].append(packet)
    if len(state["samples"]) >= state["sample_cap"]:
        for breakpoint_id in state["breakpoints"].values():
            breakpoint = process.GetTarget().FindBreakpointByID(breakpoint_id)
            if breakpoint and breakpoint.IsValid():
                breakpoint.SetEnabled(False)
    return False


def _add(debugger, name, address, callback):
    state = _state()
    target = debugger.GetSelectedTarget()
    before = target.GetNumBreakpoints()
    debugger.HandleCommand(
        f"breakpoint set --shlib libcp.dylib --address 0x{address:x}"
    )
    if target.GetNumBreakpoints() <= before:
        state["errors"].append({"site": name, "error": "breakpoint creation"})
        return
    breakpoint = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
    breakpoint.SetScriptCallbackFunction(
        f"ccm_illuminant_selection_probe.{callback}"
    )
    state["breakpoints"][name] = breakpoint.GetID()


def install(debugger):
    _add(debugger, "entry", INTERP_ENTRY, "entry_hit")
    if not _state()["entry_only"]:
        _add(debugger, "lerp_return", LERP_RETURN, "lerp_return_hit")
    print("CCM_ILLUMINANT_SELECTION_INSTALLED", _state()["breakpoints"])


def report_to_file(debugger, path):
    state = dict(_state())
    process = debugger.GetSelectedTarget().GetProcess()
    if process and process.IsValid():
        state["process_exit_status"] = process.GetExitStatus()
        state["process_state"] = int(process.GetState())
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("WROTE", path)
