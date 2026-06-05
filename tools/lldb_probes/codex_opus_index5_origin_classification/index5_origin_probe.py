import builtins
import json
import struct


SITES = {
    0x26AA30: "upsample_previous_slot90_call",
    0x26AA39: "upsample_previous_slot90_after",
    0x29ED90: "upsample_29ed90_entry",
    0x26DD40: "stereo_update_26dd40_entry",
    0x26DDD7: "stereo_update_calls_26e120",
    0x26E120: "stereo_post_update_26e120_entry",
    0x267010: "descriptor_build_267010_entry",
    0x26E633: "stereo_calls_descriptor_build_267010",
    0x26E638: "stereo_after_descriptor_build_267010",
    0x26E64A: "stereo_moves_stack_descriptor_to_index5",
    0x26E64F: "stereo_after_index5_descriptor_move",
}


def reset(label="", sample_limit=240):
    builtins.l16_index5_origin_probe = {
        "label": label,
        "sample_limit": sample_limit,
        "counts": {name: 0 for name in SITES.values()},
        "breakpoint_ids": {},
        "samples": [],
        "disabled_after_cap": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_index5_origin_probe"):
        reset()
    return builtins.l16_index5_origin_probe


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


def _stack(thread, max_frames=18):
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


def _qwords(process, addr, count):
    data = _read(process, addr, count * 8)
    if data is None:
        return None
    return [_u64(data, off) for off in range(0, count * 8, 8)]


def _u32s(process, addr, count):
    data = _read(process, addr, count * 4)
    if data is None:
        return None
    return [_u32(data, off) for off in range(0, count * 4, 4)]


def _f32s(process, addr, count):
    data = _read(process, addr, count * 4)
    if data is None:
        return None
    return [_f32(data, off) for off in range(0, count * 4, 4)]


def _vector_summary(process, addr, stride=0x10):
    qwords = _qwords(process, addr, 3)
    if qwords is None:
        return {"addr": addr, "read_ok": False}
    begin, end, cap = qwords
    byte_size = end - begin if end >= begin else None
    count = byte_size // stride if byte_size is not None and stride else None
    first_qwords = []
    if begin and byte_size and byte_size > 0:
        raw = _read(process, begin, min(byte_size, 8 * 8))
        if raw is not None:
            first_qwords = [_u64(raw, off) for off in range(0, len(raw), 8)]
    return {
        "addr": addr,
        "read_ok": True,
        "begin": begin,
        "end": end,
        "cap": cap,
        "byte_size": byte_size,
        "stride": stride,
        "count": count,
        "first_qwords": first_qwords,
    }


def _descriptor(process, addr, sample_floats=8):
    data = _read(process, addr, 0x30)
    if data is None:
        return {"addr": addr, "read_ok": False}
    data_ptr = _u64(data, 0x20)
    first_f32 = []
    first_u32 = []
    if data_ptr and sample_floats:
        raw = _read(process, data_ptr, sample_floats * 4)
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


def _stereo_object(process, obj):
    if not obj:
        return {"object": obj, "read_ok": False}
    return {
        "object": obj,
        "vtable": _read_qword(process, obj),
        "index_0x8": (_u32(_read(process, obj + 0x8, 4), 0)
                      if _read(process, obj + 0x8, 4) is not None else None),
        "mode_0xc": (_u32(_read(process, obj + 0xC, 4), 0)
                     if _read(process, obj + 0xC, 4) is not None else None),
        "tile_0x1c": (_u32(_read(process, obj + 0x1C, 4), 0)
                      if _read(process, obj + 0x1C, 4) is not None else None),
        "flag_0x54": (_u32(_read(process, obj + 0x54, 4), 0)
                      if _read(process, obj + 0x54, 4) is not None else None),
        "flag_0x78_0x79": _u32s(process, obj + 0x78, 1),
        "filter_mode_0x70": (_u32(_read(process, obj + 0x70, 4), 0)
                             if _read(process, obj + 0x70, 4) is not None else None),
        "scalar_0x74": (_u32(_read(process, obj + 0x74, 4), 0)
                        if _read(process, obj + 0x74, 4) is not None else None),
        "mask_width_0x220": (_u32(_read(process, obj + 0x220, 4), 0)
                             if _read(process, obj + 0x220, 4) is not None else None),
        "mask_ptr_0x228": _read_qword(process, obj + 0x228),
        "work_dims_0x238_0x23c": _u32s(process, obj + 0x238, 2),
        "source_vector_0xe0": _vector_summary(process, obj + 0xE0, stride=4),
        "base_descriptor_0xf8": _descriptor(process, obj + 0xF8),
        "aux_descriptor_0x208": _descriptor(process, obj + 0x208),
        "aux_vector_0x288": _vector_summary(process, obj + 0x288, stride=0x10),
        "scale_fields_0x298_0x29c": _f32s(process, obj + 0x298, 2),
        "depth_width_0x2a0": (_u32(_read(process, obj + 0x2A0, 4), 0)
                              if _read(process, obj + 0x2A0, 4) is not None else None),
        "depth_height_0x2a4": (_u32(_read(process, obj + 0x2A4, 4), 0)
                               if _read(process, obj + 0x2A4, 4) is not None else None),
        "index5_descriptor_0x2a8": _descriptor(process, obj + 0x2A8),
        "alt_descriptor_0x2d8": _descriptor(process, obj + 0x2D8),
    }


def _append(sample):
    state = _state()
    if len(state["samples"]) < state["sample_limit"]:
        state["samples"].append(sample)


def _disable_breakpoint(debugger, name):
    bp_id = _state()["breakpoint_ids"].get(name)
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id) if bp_id else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def _cap(name):
    if name in ("upsample_previous_slot90_call", "upsample_previous_slot90_after"):
        return 4
    if name == "upsample_29ed90_entry":
        return 4
    return 16


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
    rbp = regs["rbp"]
    sample = {
        "site": name,
        "site_va": site_va,
        "thread_id": thread.GetThreadID(),
        "registers": regs,
        "stack": _stack(thread),
    }

    if site_va == 0x26AA30:
        sample["upsample_object_rdi"] = regs["rdi"]
        sample["previous_layer_object_rsi"] = regs["rsi"]
        sample["previous_layer_snapshot"] = _stereo_object(process, regs["rsi"])
    elif site_va == 0x26AA39:
        sample["previous_layer_object_rbx"] = regs["rbx"]
        sample["slot90_return_rax"] = regs["rax"]
        sample["previous_layer_snapshot"] = _stereo_object(process, regs["rbx"])
        sample["returned_descriptor"] = _descriptor(process, regs["rax"])
    elif site_va == 0x29ED90:
        sample["arg_rdi_descriptor"] = _descriptor(process, regs["rdi"])
        sample["arg_rsi_descriptor"] = _descriptor(process, regs["rsi"])
        sample["arg_rdx_descriptor"] = _descriptor(process, regs["rdx"])
        sample["arg_rcx_descriptor"] = _descriptor(process, regs["rcx"])
        sample["arg_r8_descriptor"] = _descriptor(process, regs["r8"])
    elif site_va in (0x26DD40, 0x26DDD7, 0x26E120):
        sample["stereo_object"] = _stereo_object(process, regs["rdi"])
    elif site_va in (0x267010, 0x26E633):
        sample["dest_descriptor_arg_rdi"] = _descriptor(process, regs["rdi"])
        sample["source_descriptor_arg_rsi"] = _descriptor(process, regs["rsi"])
        sample["third_arg_rdx_vector"] = _vector_summary(process, regs["rdx"], stride=4)
        object_guess = regs["r12"] if regs["r12"] else _read_qword(process, rbp - 0x5C8)
        sample["stereo_object_guess"] = _stereo_object(process, object_guess)
    elif site_va == 0x26E638:
        object_guess = regs["r12"] if regs["r12"] else _read_qword(process, rbp - 0x5C8)
        sample["built_stack_descriptor_rbp_minus_0x1d0"] = _descriptor(process, rbp - 0x1D0)
        sample["stereo_object_guess"] = _stereo_object(process, object_guess)
    elif site_va == 0x26E64A:
        sample["dest_index5_descriptor_rdi"] = _descriptor(process, regs["rdi"])
        sample["source_stack_descriptor_rsi"] = _descriptor(process, regs["rsi"])
        sample["stereo_object_r12"] = _stereo_object(process, regs["r12"])
    elif site_va == 0x26E64F:
        sample["index5_descriptor_after_move_r14"] = _descriptor(process, regs["r14"])
        sample["stack_descriptor_after_move"] = _descriptor(process, rbp - 0x1D0)
        sample["stereo_object_r12"] = _stereo_object(process, regs["r12"])

    _append(sample)

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
        bp.SetScriptCallbackFunction("index5_origin_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_INDEX5_ORIGIN_ATTACHED", ids)


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


def drive_until_exit_or_step_cap(debugger, max_steps=12000):
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
    print("L16_INDEX5_ORIGIN_DRIVE_STEPS", steps)


def payload(debugger):
    packet = dict(_state())
    packet["process"] = _process_packet(debugger)
    packet["breakpoint_hit_counts"] = _breakpoint_hit_counts(debugger)
    return packet


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_INDEX5_ORIGIN_WROTE", path)


def report(debugger):
    print("L16_INDEX5_ORIGIN_BEGIN")
    print(json.dumps(payload(debugger), indent=2, sort_keys=True))
    print("L16_INDEX5_ORIGIN_END")
