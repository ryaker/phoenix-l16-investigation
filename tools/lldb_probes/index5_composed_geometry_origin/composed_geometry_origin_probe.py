import builtins
import json
import struct


SITES = {
    0xE59A9: "after_capturedimage_construct",
    0x3FF1BC: "after_state_e0_record",
    0x3FF1D6: "after_23faf0_compose",
    0x3FF43C: "before_stereolayer_install",
}


def reset(label="", sample_limit=64, hit_cap=64):
    builtins.l16_index5_composed_geometry_origin = {
        "label": label,
        "sample_limit": sample_limit,
        "hit_cap": hit_cap,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
        "breakpoint_ids": {},
        "breakpoint_vas": {},
        "counts": {f"0x{va:x}": 0 for va in SITES},
        "capturedimage_objects": [],
        "events": [],
        "errors": [],
        "sequence": 0,
    }


def _state():
    if not hasattr(builtins, "l16_index5_composed_geometry_origin"):
        reset()
    return builtins.l16_index5_composed_geometry_origin


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    if not addr:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u32(process, addr):
    data = _read(process, addr, 4)
    return struct.unpack_from("<I", data)[0] if data is not None else None


def _u64(process, addr):
    data = _read(process, addr, 8)
    return struct.unpack_from("<Q", data)[0] if data is not None else None


def _f32s(process, addr, count):
    data = _read(process, addr, count * 4)
    return list(struct.unpack_from("<" + "f" * count, data)) if data is not None else None


def _hex(process, addr, size):
    data = _read(process, addr, size)
    return data.hex() if data is not None else None


def _record(process, addr):
    if not addr:
        return None
    return {
        "addr": addr,
        "raw_0x00_0xa4": _hex(process, addr, 0xA4),
        "primary_matrix_0x00": _f32s(process, addr, 9),
        "translation_0x24": _f32s(process, addr + 0x24, 3),
        "rotation_0x30": _f32s(process, addr + 0x30, 9),
        "adjustment_0x54": _f32s(process, addr + 0x54, 4),
        "aux_vector_header_0x68": [
            _u64(process, addr + 0x68),
            _u64(process, addr + 0x70),
            _u64(process, addr + 0x78),
        ],
        "distortion_coeffs_0x68": _vector(process, addr + 0x68),
        "secondary_matrix_0x80": _f32s(process, addr + 0x80, 9),
    }


def _vector(process, header_addr):
    begin = _u64(process, header_addr)
    end = _u64(process, header_addr + 8)
    cap = _u64(process, header_addr + 16)
    if begin is None or end is None or cap is None or end < begin:
        return {"addr": header_addr, "read_ok": False}
    size = end - begin
    return {
        "addr": header_addr,
        "begin": begin,
        "end": end,
        "cap": cap,
        "byte_size": size,
        "raw_hex": _hex(process, begin, size) if size else "",
        "read_ok": size == 0 or _read(process, begin, size) is not None,
    }


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


def _registers(frame):
    names = ("rax", "rbx", "rcx", "rdx", "rdi", "rsi", "r8", "r13", "r14", "r15", "rbp")
    return {name: _u(frame, name) for name in names}


def _stack(thread, max_frames=8):
    target = thread.GetProcess().GetTarget()
    return [
        {
            "index": index,
            "pc": thread.GetFrameAtIndex(index).GetPC(),
            "libcp_va": _module_va(target, thread.GetFrameAtIndex(index).GetPC()),
            "function": thread.GetFrameAtIndex(index).GetFunctionName(),
        }
        for index in range(min(thread.GetNumFrames(), max_frames))
    ]


def _packet(process, regs, name):
    if name == "after_capturedimage_construct":
        obj = regs["rbx"]
        control_block = obj - 0x20 if obj else None
        control_vtable = _u64(process, control_block) if control_block else None
        return {
            "capturedimage_object": obj,
            "control_block": control_block,
            "control_block_vtable": control_vtable,
            "control_block_vtable_libcp_va": _module_va(
                process.GetTarget(), control_vtable
            )
            if control_vtable
            else None,
            "camera_id_0x60": _u32(process, obj + 0x60) if obj else None,
            "calib_stage_0x64": _u32(process, obj + 0x64) if obj else None,
        }
    rbp = regs["rbp"]
    obj = _u64(process, rbp - 0xC0)
    packet = {
        "camera_key": _u32(process, regs["r15"]),
        "state_e0_object": obj,
        "state_e0_object_fields": {
            "active_0x30": _u32(process, obj + 0x30) & 0xFF if obj else None,
            "lens_position_0x54": _u32(process, obj + 0x54) if obj else None,
            "camera_id_0x60": _u32(process, obj + 0x60) if obj else None,
            "calib_stage_0x64": _u32(process, obj + 0x64) if obj else None,
            "sensor_size_0x114": [
                _u32(process, obj + 0x114),
                _u32(process, obj + 0x118),
            ]
            if obj
            else None,
        },
    }
    if name == "after_state_e0_record":
        packet.update(
            {
                "state_448_node": regs["r13"],
                "state_448_node_record": _record(process, regs["r13"] + 0x20),
                "state_e0_calibstage_record": _record(process, rbp - 0x210),
                "compose_output_before": _record(process, rbp - 0x168),
            }
        )
    elif name == "after_23faf0_compose":
        packet.update(
            {
                "state_448_node_record": _record(process, regs["r13"]),
                "state_e0_calibstage_record": _record(process, rbp - 0x210),
                "compose_output_after": _record(process, rbp - 0x168),
            }
        )
    elif name == "before_stereolayer_install":
        images = _vector(process, rbp - 0x40)
        first_image = _u64(process, images["begin"]) if images.get("begin") else None
        optional_image = _u64(process, regs["rdx"])
        packet.update(
            {
                "images_vector": images,
                "first_image_descriptor": {
                    "addr": first_image,
                    "raw_0x00_0x30": _hex(process, first_image, 0x30),
                },
                "optional_image_shared": regs["rdx"],
                "optional_image_descriptor": {
                    "addr": optional_image,
                    "raw_0x00_0x30": _hex(process, optional_image, 0x30),
                },
                "composed_geometry_vector": _vector(process, rbp - 0x60),
                "image_flags_vector": _vector(process, rbp - 0x80),
            }
        )
    return packet


def attach_existing(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    if target.GetNumBreakpoints() < len(SITES):
        state["errors"].append("not enough existing breakpoints")
        return
    start = target.GetNumBreakpoints() - len(SITES)
    for index, va in enumerate(SITES):
        bp = target.GetBreakpointAtIndex(start + index)
        bp.SetScriptCallbackFunction("composed_geometry_origin_probe.hit")
        state["breakpoint_ids"][f"0x{va:x}"] = bp.GetID()
        state["breakpoint_vas"][str(bp.GetID())] = va


def hit(frame, bp_loc, internal_dict):
    state = _state()
    bp_id = bp_loc.GetBreakpoint().GetID()
    va = state["breakpoint_vas"].get(str(bp_id))
    if va is None:
        state["errors"].append(f"unknown breakpoint id {bp_id}")
        return False
    key = f"0x{va:x}"
    state["counts"][key] += 1
    state["sequence"] += 1
    thread = frame.GetThread()
    process = thread.GetProcess()
    regs = _registers(frame)
    name = SITES[va]
    event = {
        "sequence": state["sequence"],
        "site_va": _module_va(process.GetTarget(), frame.GetPC()),
        "site_name": name,
        "thread_id": thread.GetThreadID(),
        "registers": regs,
        "stack": _stack(thread),
    }
    try:
        event["packet"] = _packet(process, regs, name)
        if name == "after_capturedimage_construct":
            state["capturedimage_objects"].append(
                event["packet"]["capturedimage_object"]
            )
    except Exception as exc:
        state["errors"].append(f"{name}: {exc}")
    if len(state["events"]) < state["sample_limit"]:
        state["events"].append(event)
    if state["counts"][key] >= state["hit_cap"]:
        bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def drive_until_exit_or_step_cap(debugger, max_steps=60000):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process.IsValid() and process.GetState() == lldb.eStateStopped and steps < max_steps:
        steps += 1
        process.Continue()
    state["drive_steps"] = steps
    state["drive_hit_step_cap"] = (
        process.IsValid() and process.GetState() == lldb.eStateStopped and steps >= max_steps
    )


def _process(debugger):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    return {
        "valid": bool(process and process.IsValid()),
        "state": lldb.SBDebugger.StateAsCString(process.GetState()) if process else None,
        "exit_status": process.GetExitStatus() if process else None,
    }


def payload(debugger):
    target = debugger.GetSelectedTarget()
    hits = {}
    for key, bp_id in _state()["breakpoint_ids"].items():
        bp = target.FindBreakpointByID(bp_id)
        hits[key] = bp.GetHitCount() if bp and bp.IsValid() else None
    return {
        "process": _process(debugger),
        "breakpoint_hit_counts": hits,
        "sites": {f"0x{va:x}": name for va, name in SITES.items()},
        **_state(),
    }


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
