import builtins
import json
import struct


SITES = {
    0x1F109C: "before_actuator_mapping",
    0x1F10A1: "after_actuator_mapping",
    0x1F10B2: "before_mirror_pose",
    0x1F10B7: "after_mirror_pose",
    0x1F1328: "before_factory_copy",
}


def reset(label="", sample_limit=256, hit_cap=256):
    builtins.l16_movable_mirror_pose = {
        "label": label,
        "sample_limit": sample_limit,
        "hit_cap": hit_cap,
        "breakpoint_ids": {},
        "breakpoint_vas": {},
        "counts": {f"0x{va:x}": 0 for va in SITES},
        "events": [],
        "errors": [],
        "drive_steps": 0,
        "drive_hit_step_cap": False,
    }


def _state():
    if not hasattr(builtins, "l16_movable_mirror_pose"):
        reset()
    return builtins.l16_movable_mirror_pose


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    if not addr:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    return data if error.Success() and len(data) == size else None


def _u32(process, addr):
    data = _read(process, addr, 4)
    return struct.unpack("<I", data)[0] if data is not None else None


def _i32(process, addr):
    data = _read(process, addr, 4)
    return struct.unpack("<i", data)[0] if data is not None else None


def _f32s(process, addr, count):
    data = _read(process, addr, 4 * count)
    return list(struct.unpack("<" + "f" * count, data)) if data is not None else None


def _f64s(process, addr, count):
    data = _read(process, addr, 8 * count)
    return list(struct.unpack("<" + "d" * count, data)) if data is not None else None


def _hex(process, addr, size):
    data = _read(process, addr, size)
    return data.hex() if data is not None else None


def _xmm_f64(frame, name="xmm0"):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    value = frame.FindRegister(name).GetData().GetDouble(error, 0)
    return value if error.Success() else None


def _libcp_base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                return base
    return None


def _module_va(target, pc):
    base = _libcp_base(target)
    return pc - base if base is not None and pc >= base else None


def _object(process, addr):
    return {
        "addr": addr,
        "camera_id_0x60": _i32(process, addr + 0x60),
        "mirror_position_0x50": _i32(process, addr + 0x50),
        "lens_position_0x54": _i32(process, addr + 0x54),
    }


def _mirror_system(process, addr):
    return {
        "addr": addr,
        "raw_0x00_0xb8": _hex(process, addr, 0xB8),
        "real_camera_orientation_0x00": _f64s(process, addr, 9),
        "real_camera_location_0x48": _f64s(process, addr + 0x48, 3),
        "point_on_rotation_axis_0x60": _f64s(process, addr + 0x60, 3),
        "rotation_axis_0x78": _f64s(process, addr + 0x78, 3),
        "mirror_normal_zero_0x90": _f64s(process, addr + 0x90, 3),
        "distance_0xa8": (_f64s(process, addr + 0xA8, 1) or [None])[0],
        "flip_img_around_x_0xb0": (_read(process, addr + 0xB0, 1) or b"\0")[0],
    }


def _packet(frame, va):
    process = frame.GetThread().GetProcess()
    rbp = _u(frame, "rbp")
    outer = _u(frame, "r14")
    packet = {
        "object": _object(process, outer),
        "rbp": rbp,
    }
    if va == 0x1F109C:
        mapping = _u(frame, "rdi")
        packet.update({
            "mapping_object": mapping,
            "mapping_raw_0x00_0x220": _hex(process, mapping, 0x220),
            "mapping_input_hall_f64": _xmm_f64(frame),
        })
    elif va == 0x1F10A1:
        packet["mapping_output_angle_degrees_f64"] = _xmm_f64(frame)
    elif va in (0x1F10B2, 0x1F10B7):
        mirror = _u(frame, "r15")
        packet.update({
            "mirror_system": _mirror_system(process, mirror),
            "rotation_output_f64x9": _f64s(process, rbp - 0x1D0, 9),
            "translation_output_f64x3": _f64s(process, rbp - 0x1F0, 3),
        })
    elif va == 0x1F1328:
        packet.update({
            "rotation_copy_f32x9": _f32s(process, _u(frame, "rdx"), 9),
            "translation_copy_f32x3": _f32s(process, _u(frame, "rcx"), 3),
        })
    return packet


def attach_existing(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    start = target.GetNumBreakpoints() - len(SITES)
    for index, va in enumerate(SITES):
        bp = target.GetBreakpointAtIndex(start + index)
        if not bp or not bp.IsValid():
            state["errors"].append(f"missing breakpoint for 0x{va:x}")
            continue
        bp.SetScriptCallbackFunction("movable_mirror_pose_probe.hit")
        state["breakpoint_ids"][f"0x{va:x}"] = bp.GetID()
        state["breakpoint_vas"][str(bp.GetID())] = va


def hit(frame, bp_loc, _dict):
    state = _state()
    bp_id = bp_loc.GetBreakpoint().GetID()
    va = state["breakpoint_vas"].get(str(bp_id))
    if va is None:
        state["errors"].append(f"unknown breakpoint id {bp_id}")
        return False
    key = f"0x{va:x}"
    state["counts"][key] += 1
    if len(state["events"]) < state["sample_limit"]:
        try:
            state["events"].append({
                "site_va": va,
                "site_name": SITES[va],
                "thread_id": frame.GetThread().GetThreadID(),
                "packet": _packet(frame, va),
            })
        except Exception as exc:
            state["errors"].append(f"0x{va:x}: {exc}")
    if state["counts"][key] >= state["hit_cap"]:
        bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def drive_until_exit_or_step_cap(debugger, max_steps=60000):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    while process.IsValid() and process.GetState() == lldb.eStateStopped and state["drive_steps"] < max_steps:
        state["drive_steps"] += 1
        process.Continue()
    state["drive_hit_step_cap"] = process.IsValid() and process.GetState() == lldb.eStateStopped


def write_report(debugger, path):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    state["process"] = {
        "state": lldb.SBDebugger.StateAsCString(process.GetState()) if process else None,
        "exit_status": process.GetExitStatus() if process else None,
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
