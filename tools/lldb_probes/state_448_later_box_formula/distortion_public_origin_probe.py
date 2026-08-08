import builtins
import json
import struct


SITE_VA = 0x1455D5


def reset(label="", sample_limit=128, hit_cap=128):
    builtins.l16_state448_distortion_origin = {
        "label": label,
        "sample_limit": sample_limit,
        "hit_cap": hit_cap,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
        "breakpoint_id": None,
        "events": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_state448_distortion_origin"):
        reset()
    return builtins.l16_state448_distortion_origin


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    if not addr or size < 0:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u32(data, offset=0):
    return struct.unpack_from("<I", data, offset)[0]


def _i32(data, offset=0):
    return struct.unpack_from("<i", data, offset)[0]


def _u64(data, offset=0):
    return struct.unpack_from("<Q", data, offset)[0]


def _read_u32(process, addr):
    data = _read(process, addr, 4)
    return _u32(data) if data is not None else None


def _read_i32(process, addr):
    data = _read(process, addr, 4)
    return _i32(data) if data is not None else None


def _read_u64(process, addr):
    data = _read(process, addr, 8)
    return _u64(data) if data is not None else None


def _read_u32_words(process, addr, count):
    data = _read(process, addr, count * 4)
    if data is None:
        return None
    return [_u32(data, offset) for offset in range(0, len(data), 4)]


def _libcp_base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                return base
    return None


def attach_existing(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    if target.GetNumBreakpoints() < 1:
        state["errors"].append("missing existing breakpoint")
        return
    bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
    if not bp or not bp.IsValid():
        state["errors"].append("invalid existing breakpoint")
        return
    bp.SetScriptCallbackFunction("distortion_public_origin_probe.hit")
    state["breakpoint_id"] = bp.GetID()
    print("L16_STATE448_DISTORTION_ATTACHED", bp.GetID())


def hit(frame, bp_loc, internal_dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    obj = _u(frame, "r13")
    calibration = _u(frame, "rbx")
    begin = _read_u64(process, calibration + 0x70)
    end = _read_u64(process, calibration + 0x78)
    capacity = _read_u64(process, calibration + 0x80)

    vector_ok = (
        begin is not None
        and end is not None
        and capacity is not None
        and begin <= end <= capacity
        and (end - begin) % 4 == 0
        and (end - begin) // 4 <= 4096
    )
    coeff_count = (end - begin) // 4 if vector_ok else None
    coeff_words = _read_u32_words(process, begin, coeff_count) if vector_ok else None
    base = _libcp_base(target)
    event = {
        "site_va": frame.GetPC() - base if base is not None else None,
        "thread_id": frame.GetThread().GetThreadID(),
        "object": obj,
        "camera_key": _read_i32(process, obj + 0x60),
        "calibration_record": calibration,
        "polynomial_present": _read_u32(process, calibration + 0x90),
        "center_normalization_words": _read_u32_words(process, calibration + 0x60, 4),
        "coeff_begin": begin,
        "coeff_end": end,
        "coeff_capacity": capacity,
        "coeff_count": coeff_count,
        "coeff_words": coeff_words,
        "fit_cost_word": _read_u32(process, calibration + 0x88),
        "fit_cost_present": _read_u32(process, calibration + 0x8C),
    }
    if not vector_ok:
        state["errors"].append(
            f"invalid coefficient vector key={event['camera_key']} "
            f"begin={begin} end={end} capacity={capacity}"
        )
    if len(state["events"]) < state["sample_limit"]:
        state["events"].append(event)

    bp = bp_loc.GetBreakpoint()
    if bp.GetHitCount() >= state["hit_cap"]:
        bp.SetEnabled(False)
    return False


def _process_packet(debugger):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    if not process or not process.IsValid():
        return {"valid": False}
    return {
        "valid": True,
        "state": lldb.SBDebugger.StateAsCString(process.GetState()),
        "exit_status": process.GetExitStatus(),
    }


def drive_until_exit_or_step_cap(debugger, max_steps=80000):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process.IsValid() and process.GetState() == lldb.eStateStopped and steps < max_steps:
        steps += 1
        process.Continue()
    state["drive_steps"] += steps
    if process.IsValid() and process.GetState() == lldb.eStateStopped and steps >= max_steps:
        state["drive_hit_step_cap"] = True
    print("L16_STATE448_DISTORTION_DRIVE_STEPS", steps)


def write_report(debugger, path):
    state = _state()
    bp = debugger.GetSelectedTarget().FindBreakpointByID(state["breakpoint_id"])
    payload = {
        **state,
        "site_va": SITE_VA,
        "breakpoint_hit_count": bp.GetHitCount() if bp and bp.IsValid() else None,
        "process": _process_packet(debugger),
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_STATE448_DISTORTION_WROTE", path)
