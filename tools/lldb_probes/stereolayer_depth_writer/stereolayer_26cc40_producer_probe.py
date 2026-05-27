import builtins
import json
import struct


SITES = {
    0x26CC40: "producer_entry",
    0x26CC97: "primary_descriptor_ready",
    0x26CCAF: "previous_slot90_return",
    0x26CCEB: "previous_wrapper_ready",
    0x26CD25: "computed_output_ready",
    0x26CD46: "final_depth_after_copy",
}


def reset(label="", sample_limit=160):
    builtins.l16_stereolayer_26cc40 = {
        "label": label,
        "sample_limit": sample_limit,
        "counts": {name: 0 for name in SITES.values()},
        "breakpoint_ids": {},
        "disabled_after_cap": [],
        "samples": [],
        "errors": [],
        "entry_by_thread": {},
    }


def _state():
    if not hasattr(builtins, "l16_stereolayer_26cc40"):
        reset()
    return builtins.l16_stereolayer_26cc40


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


def _f32(data, off=0):
    return struct.unpack_from("<f", data, off)[0]


def _read_qword(process, addr):
    data = _read(process, addr, 8)
    return _u64(data) if data is not None else None


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
            }
        )
    return frames


def _descriptor(process, addr, data_sample_bytes=32):
    data = _read(process, addr, 0x30)
    if data is None:
        return {"addr": addr, "read_ok": False}
    data_ptr = _u64(data, 0x20)
    first_f32 = []
    first_u32 = []
    if data_ptr:
        raw = _read(process, data_ptr, data_sample_bytes)
        if raw is not None:
            first_f32 = [_f32(raw, off) for off in range(0, len(raw), 4)]
            first_u32 = [_u32(raw, off) for off in range(0, len(raw), 4)]
    return {
        "addr": addr,
        "read_ok": True,
        "qwords": [_u64(data, off) for off in range(0, 0x30, 8)],
        "u32": [_u32(data, off) for off in range(0, 0x30, 4)],
        "i32": [_i32(data, off) for off in range(0, 0x30, 4)],
        "width_0x10": _u32(data, 0x10),
        "height_0x14": _u32(data, 0x14),
        "stride_0x18": _u32(data, 0x18),
        "data_ptr_0x20": data_ptr,
        "first_data_f32": first_f32,
        "first_data_u32": first_u32,
    }


def _qwords(process, addr, count):
    data = _read(process, addr, count * 8)
    if data is None:
        return None
    return [_u64(data, off) for off in range(0, count * 8, 8)]


def _vector_summary(process, addr):
    qwords = _qwords(process, addr, 3)
    if qwords is None:
        return {"addr": addr, "read_ok": False}
    begin, end, cap = qwords
    first_ptr = _read_qword(process, begin) if begin else None
    return {
        "addr": addr,
        "read_ok": True,
        "begin": begin,
        "end": end,
        "cap": cap,
        "byte_size": end - begin if end >= begin else None,
        "first_qword": first_ptr,
        "first_qword_descriptor": _descriptor(process, first_ptr)
        if first_ptr
        else None,
    }


def _stereo_object(process, obj):
    if not obj:
        return {"object": obj, "read_ok": False}
    width = _read(process, obj + 0x2A0, 4)
    height = _read(process, obj + 0x2A4, 4)
    return {
        "object": obj,
        "vtable": _read_qword(process, obj),
        "mode_0x50": _u32(_read(process, obj + 0x50, 4), 0)
        if _read(process, obj + 0x50, 4) is not None
        else None,
        "depth_width_0x2a0": _u32(width, 0) if width is not None else None,
        "depth_height_0x2a4": _u32(height, 0) if height is not None else None,
        "depth_descriptor_0x2a8": _descriptor(process, obj + 0x2A8),
        "alt_descriptor_0x2d8": _descriptor(process, obj + 0x2D8),
        "aux_descriptor_0x208": _descriptor(process, obj + 0x208),
        "source_vector_0x240": _vector_summary(process, obj + 0x240),
    }


def _disable_breakpoint(debugger, name):
    bp_id = _state()["breakpoint_ids"].get(name)
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id) if bp_id else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def _cap(name):
    if name == "producer_entry":
        return 64
    return 32


def hit(frame, bp_loc, internal_dict):
    state = _state()
    thread = frame.GetThread()
    thread_key = str(thread.GetThreadID())
    process = thread.GetProcess()
    target = process.GetTarget()
    site_va = _module_va(target, frame.GetPC())
    name = SITES.get(site_va)
    if name is None:
        state["errors"].append(f"unknown site {site_va}")
        return False

    state["counts"][name] = state["counts"].get(name, 0) + 1
    regs = _registers(frame)
    obj = regs["rdi"] if site_va == 0x26CC40 else regs["rbx"]

    if site_va == 0x26CC40:
        state["entry_by_thread"][thread_key] = {
            "object": regs["rdi"],
            "previous_layer_object": regs["rsi"],
        }

    entry = state["entry_by_thread"].get(thread_key, {})
    sample = {
        "site": name,
        "site_va": site_va,
        "thread_id": thread.GetThreadID(),
        "registers": regs,
        "entry_context": entry,
        "stack": _stack(thread),
        "object": _stereo_object(process, obj),
    }

    previous_obj = entry.get("previous_layer_object")
    if previous_obj:
        sample["previous_layer_object"] = _stereo_object(process, previous_obj)

    rbp = regs["rbp"]
    if site_va == 0x26CC40:
        sample["entry_previous_layer_rsi"] = _stereo_object(process, regs["rsi"])
    elif site_va == 0x26CC97:
        sample["primary_descriptor_stack_rbp_minus_0x40"] = _descriptor(
            process, rbp - 0x40
        )
        sample["source_record_stack_rbp_minus_0x70"] = _descriptor(process, rbp - 0x70)
    elif site_va == 0x26CCAF:
        sample["previous_slot90_return_rax"] = _descriptor(process, regs["rax"])
    elif site_va == 0x26CCEB:
        sample["previous_wrapper_stack_rbp_minus_0xf0"] = _descriptor(
            process, rbp - 0xF0
        )
    elif site_va == 0x26CD25:
        sample["computed_output_stack_rbp_minus_0xc0"] = _descriptor(
            process, rbp - 0xC0
        )
        sample["primary_descriptor_stack_rbp_minus_0x40"] = _descriptor(
            process, rbp - 0x40
        )
        sample["previous_wrapper_stack_rbp_minus_0xf0"] = _descriptor(
            process, rbp - 0xF0
        )
    elif site_va == 0x26CD46:
        sample["final_depth_descriptor_0x2a8"] = _descriptor(process, obj + 0x2A8)

    if len(state["samples"]) < state["sample_limit"]:
        state["samples"].append(sample)

    if state["counts"][name] >= _cap(name):
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
        loc = bp.GetLocationAtIndex(0)
        site_va = loc.GetAddress().GetFileAddress()
        name = SITES.get(site_va)
        if name is None:
            continue
        bp.SetScriptCallbackFunction("stereolayer_26cc40_producer_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_STEREO_26CC40_ATTACHED", ids)


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


def drive_until_exit_or_step_cap(debugger, max_steps=16000):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while (
        process.IsValid()
        and process.GetState() == lldb.eStateStopped
        and steps < max_steps
    ):
        steps += 1
        process.Continue()
    _state()["drive_steps"] = steps
    _state()["drive_hit_step_cap"] = (
        process.IsValid() and process.GetState() == lldb.eStateStopped and steps >= max_steps
    )
    print("L16_STEREO_26CC40_DRIVE_STEPS", steps)


def payload(debugger):
    packet = dict(_state())
    packet["process"] = _process_packet(debugger)
    packet["breakpoint_hit_counts"] = _breakpoint_hit_counts(debugger)
    return packet


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_STEREO_26CC40_WROTE", path)


def report(debugger):
    print("L16_STEREO_26CC40_BEGIN")
    print(json.dumps(payload(debugger), indent=2, sort_keys=True))
    print("L16_STEREO_26CC40_END")
