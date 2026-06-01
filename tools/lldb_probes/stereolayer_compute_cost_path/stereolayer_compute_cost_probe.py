import builtins
import json
import struct


SITES = {
    0x26B038: "compute_setup_caller_a_26b038",
    0x26F383: "compute_setup_caller_b_26f383",
    0x26F571: "compute_write_guard_caller_26f571",
    0x272100: "compute_setup_helper_272100",
    0x272640: "compute_write_guard_272640",
    0x274B10: "compute_lambda_operator_274b10",
    0x2727F0: "compute_worker_entry_2727f0",
    0x2729B0: "compute_state_builder_callsite_2729b0",
    0x272C84: "compute_count4_cost_callsite_272c84",
    0x272CA9: "compute_general_cost_callsite_272ca9",
    0x276790: "runpass_action_control_276790",
    0x276860: "runpass_mode8_control_276860",
    0x277E70: "runpass_default_control_277e70",
    0x27710F: "runpass_count4_cost_callsite_27710f",
    0x2773DC: "runpass_general_cost_callsite_2773dc",
}


def reset(label="", sample_limit=160, hit_cap=64):
    builtins.l16_stereolayer_compute_cost = {
        "label": label,
        "sample_limit": sample_limit,
        "hit_cap": hit_cap,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
        "breakpoint_ids": {},
        "counts": {name: 0 for name in SITES.values()},
        "disabled_after_cap": [],
        "samples": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_stereolayer_compute_cost"):
        reset()
    return builtins.l16_stereolayer_compute_cost


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


def _u64(data, off=0):
    return struct.unpack_from("<Q", data, off)[0]


def _u32(data, off=0):
    return struct.unpack_from("<I", data, off)[0]


def _i32(data, off=0):
    return struct.unpack_from("<i", data, off)[0]


def _read_qword(process, addr):
    data = _read(process, addr, 8)
    return _u64(data) if data is not None else None


def _read_u32(process, addr):
    data = _read(process, addr, 4)
    return _u32(data) if data is not None else None


def _libcp_base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                return base
    return None


def _module_va(target, pc):
    base = _libcp_base(target)
    if base is not None and pc >= base:
        return pc - base
    return None


def _registers(frame):
    return {
        name: _u(frame, name)
        for name in (
            "rax",
            "rbx",
            "rcx",
            "rdx",
            "rdi",
            "rsi",
            "r8",
            "r9",
            "r10",
            "r11",
            "r12",
            "r13",
            "r14",
            "r15",
            "rbp",
            "rsp",
        )
    }


def _stack(thread, max_frames=12):
    target = thread.GetProcess().GetTarget()
    frames = []
    for index in range(min(thread.GetNumFrames(), max_frames)):
        frame = thread.GetFrameAtIndex(index)
        frames.append(
            {
                "index": index,
                "pc": frame.GetPC(),
                "libcp_va": _module_va(target, frame.GetPC()),
                "function": frame.GetFunctionName(),
                "rbp": _u(frame, "rbp"),
            }
        )
    return frames


def _qwords(process, addr, count):
    data = _read(process, addr, count * 8)
    if data is None:
        return None
    return [_u64(data, off) for off in range(0, count * 8, 8)]


def _rect(process, addr):
    data = _read(process, addr, 0x10)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "i32": [_i32(data, off) for off in range(0, 0x10, 4)],
        "u32": [_u32(data, off) for off in range(0, 0x10, 4)],
        "qwords": [_u64(data, off) for off in range(0, 0x10, 8)],
    }


def _vector(process, addr):
    values = _qwords(process, addr, 3)
    if values is None:
        return {"addr": addr, "read_ok": False}
    begin, end, cap = values
    return {
        "addr": addr,
        "read_ok": True,
        "begin": begin,
        "end": end,
        "cap": cap,
        "byte_size": end - begin if end >= begin else None,
        "first_qwords": _qwords(process, begin, 4) if begin else None,
    }


def _descriptor(process, addr):
    data = _read(process, addr, 0x30)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "qwords": [_u64(data, off) for off in range(0, 0x30, 8)],
        "u32": [_u32(data, off) for off in range(0, 0x30, 4)],
        "width_0x10": _u32(data, 0x10),
        "height_0x14": _u32(data, 0x14),
        "stride_0x18": _u32(data, 0x18),
        "data_ptr_0x20": _u64(data, 0x20),
    }


def _stereo_object(process, obj):
    if not obj:
        return {"object": obj, "read_ok": False}
    return {
        "object": obj,
        "read_ok": True,
        "vtable": _read_qword(process, obj),
        "index_0x8": _read_u32(process, obj + 0x8),
        "mode_0xc": _read_u32(process, obj + 0xC),
        "tile_0x1c": _read_u32(process, obj + 0x1C),
        "flag_0x20": _read_u32(process, obj + 0x20),
        "source_vector_0x240": _vector(process, obj + 0x240),
        "scale_vector_0x270": _vector(process, obj + 0x270),
        "depth_descriptor_0x2a8": _descriptor(process, obj + 0x2A8),
    }


def _disable_breakpoint(debugger, name):
    bp_id = _state()["breakpoint_ids"].get(name)
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id) if bp_id else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def _append_sample(sample):
    state = _state()
    if len(state["samples"]) < state["sample_limit"]:
        state["samples"].append(sample)


def hit(frame, bp_loc, internal_dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    site_va = _module_va(target, frame.GetPC())
    name = SITES.get(site_va)
    if name is None:
        state["errors"].append(f"unknown site {site_va}")
        return False

    state["counts"][name] = state["counts"].get(name, 0) + 1
    regs = _registers(frame)
    sample = {
        "site": name,
        "site_va": site_va,
        "thread_id": thread.GetThreadID(),
        "registers": regs,
        "stack": _stack(thread),
    }

    if site_va == 0x274B10:
        layer = _read_qword(process, regs["rdi"] + 0x8)
        sample["function_object"] = regs["rdi"]
        sample["captured_layer"] = _stereo_object(process, layer)
        sample["rect_arg"] = _rect(process, regs["rsi"])
        sample["tile_arg_edx"] = regs["rdx"] & 0xFFFFFFFF
    elif site_va == 0x2727F0:
        sample["layer_object"] = _stereo_object(process, regs["rdi"])
        sample["rect_arg"] = _rect(process, regs["rsi"])
        sample["tile_arg_edx"] = regs["rdx"] & 0xFFFFFFFF
    elif site_va in (0x276790,):
        layer = _read_qword(process, regs["rdi"] + 0x8)
        sample["captured_layer"] = _stereo_object(process, layer)
    elif site_va in (0x276860, 0x277E70):
        sample["layer_object"] = _stereo_object(process, regs["rdi"])

    _append_sample(sample)

    if state["counts"][name] >= state["hit_cap"]:
        _disable_breakpoint(target.GetDebugger(), name)
        if name not in state["disabled_after_cap"]:
            state["disabled_after_cap"].append(name)
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    ids = {}
    for index in range(target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(index)
        if not bp or not bp.IsValid() or bp.GetNumLocations() < 1:
            continue
        site_va = bp.GetLocationAtIndex(0).GetAddress().GetFileAddress()
        name = SITES.get(site_va)
        if name is None:
            continue
        bp.SetScriptCallbackFunction("stereolayer_compute_cost_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_STEREOLAYER_COMPUTE_COST_ATTACHED", json.dumps(ids, sort_keys=True))


def _breakpoint_hit_counts(debugger):
    target = debugger.GetSelectedTarget()
    out = {}
    for name, bp_id in _state().get("breakpoint_ids", {}).items():
        bp = target.FindBreakpointByID(bp_id)
        out[name] = bp.GetHitCount() if bp and bp.IsValid() else None
    return out


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


def drive_until_exit_or_step_cap(debugger, max_steps=60000):
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
    print("L16_STEREOLAYER_COMPUTE_COST_DRIVE_STEPS", steps)


def payload(debugger):
    return {
        "process": _process_packet(debugger),
        "breakpoint_hit_counts": _breakpoint_hit_counts(debugger),
        **_state(),
    }


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_STEREOLAYER_COMPUTE_COST_WROTE", path)
