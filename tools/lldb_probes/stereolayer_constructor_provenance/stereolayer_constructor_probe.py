import builtins
import json
import struct


SITES = {
    0x3FCB81: "scheduler_calls_layer_vector_268690",
    0x268690: "layer_vector_process_268690",
    0x267E80: "add_stereolayer_267e80",
    0x26B750: "stereolayer_ctor_26b750",
    0x26BBD0: "index_setter_26bbd0",
    0x26BCA0: "size_setter_26bca0",
    0x26BD90: "init_from_previous_stereo_26bd90",
    0x26BF90: "init_from_upsample_26bf90",
    0x26C220: "init_no_previous_26c220",
    0x26DD40: "compute_update_26dd40",
    0x26E120: "post_compute_update_26e120",
}


def reset(label="", target_index=5, sample_limit=360):
    builtins.l16_stereolayer_ctor_probe = {
        "label": label,
        "target_index": target_index,
        "sample_limit": sample_limit,
        "counts": {name: 0 for name in SITES.values()},
        "breakpoint_ids": {},
        "samples": [],
        "constructor_by_object": {},
        "target_objects": [],
        "disabled_after_cap": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_stereolayer_ctor_probe"):
        reset()
    return builtins.l16_stereolayer_ctor_probe


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


def _u16(data, off=0):
    return struct.unpack_from("<H", data, off)[0]


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


def _vector_summary(process, addr, stride=8):
    qwords = _qwords(process, addr, 3)
    if qwords is None:
        return {"addr": addr, "read_ok": False}
    begin, end, cap = qwords
    byte_size = end - begin if end >= begin else None
    count = byte_size // stride if byte_size is not None and stride else None
    first = []
    if begin and count:
        raw = _read(process, begin, min(byte_size, 8 * min(count, 8)))
        if raw is not None:
            first = [_u64(raw, off) for off in range(0, len(raw), 8)]
    return {
        "addr": addr,
        "read_ok": True,
        "begin": begin,
        "end": end,
        "cap": cap,
        "byte_size": byte_size,
        "stride": stride,
        "count": count,
        "first_qwords": first,
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


def _stereo_params(process, ptr):
    data = _read(process, ptr, 0x80)
    if data is None:
        return {"addr": ptr, "read_ok": False}
    return {
        "addr": ptr,
        "read_ok": True,
        "qwords": [_u64(data, off) for off in range(0, 0x80, 8)],
        "u32": [_u32(data, off) for off in range(0, 0x80, 4)],
        "i32": [_i32(data, off) for off in range(0, 0x80, 4)],
        "u16": [_u16(data, off) for off in range(0, 0x70, 2)],
        "f32": [_f32(data, off) for off in range(0, 0x80, 4)],
        "ctor_copied_0x00_0x28_u32": [_u32(data, off) for off in range(0, 0x28, 4)],
        "ctor_copied_0x30_0x70_u32": [_u32(data, off) for off in range(0x30, 0x70, 4)],
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
        "param_copy_0x10_u32": _u32s(process, obj + 0x10, 28),
        "param_copy_0x10_f32": _f32s(process, obj + 0x10, 28),
        "flag_0x54": (_u32(_read(process, obj + 0x54, 4), 0)
                      if _read(process, obj + 0x54, 4) is not None else None),
        "scalar_0x74": (_u32(_read(process, obj + 0x74, 4), 0)
                        if _read(process, obj + 0x74, 4) is not None else None),
        "ready_0x80": (_u32(_read(process, obj + 0x80, 4), 0)
                       if _read(process, obj + 0x80, 4) is not None else None),
        "work_width_0x238": (_u32(_read(process, obj + 0x238, 4), 0)
                             if _read(process, obj + 0x238, 4) is not None else None),
        "work_count_0x23c": (_u32(_read(process, obj + 0x23C, 4), 0)
                             if _read(process, obj + 0x23C, 4) is not None else None),
        "source_vector_0x240": _vector_summary(process, obj + 0x240, stride=0x10),
        "scale_vector_0x270": _vector_summary(process, obj + 0x270, stride=0x10),
        "aux_vector_0x288": _vector_summary(process, obj + 0x288, stride=0x10),
        "scale_fields_0x298_0x29c": _f32s(process, obj + 0x298, 2),
        "depth_width_0x2a0": (_u32(_read(process, obj + 0x2A0, 4), 0)
                              if _read(process, obj + 0x2A0, 4) is not None else None),
        "depth_height_0x2a4": (_u32(_read(process, obj + 0x2A4, 4), 0)
                               if _read(process, obj + 0x2A4, 4) is not None else None),
        "aux_descriptor_0x208": _descriptor(process, obj + 0x208),
        "depth_descriptor_0x2a8": _descriptor(process, obj + 0x2A8),
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
    if name in ("scheduler_calls_layer_vector_268690", "layer_vector_process_268690"):
        return 80
    if name in ("compute_update_26dd40", "post_compute_update_26e120"):
        return 80
    return 160


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

    if site_va == 0x3FCB81:
        sample["layer_vector_arg"] = regs["rdi"]
        sample["requested_index_esi"] = regs["rsi"] & 0xFFFFFFFF
        sample["owner_rbx"] = regs["rbx"]
        sample["owner_layer_vector_0xb0"] = _vector_summary(process, regs["rbx"] + 0xB0, stride=8)
    elif site_va == 0x268690:
        sample["layer_vector_arg"] = regs["rdi"]
        sample["requested_index_esi"] = regs["rsi"] & 0xFFFFFFFF
        sample["layer_vector"] = _vector_summary(process, regs["rdi"] + 0x10, stride=8)
    elif site_va == 0x267E80:
        sample["layer_vector_container"] = regs["rdi"]
        sample["layer_vector"] = _vector_summary(process, regs["rdi"] + 0x10, stride=8)
    elif site_va == 0x26B750:
        sample["ctor_object"] = regs["rdi"]
        sample["stereo_params"] = _stereo_params(process, regs["rsi"])
        state["constructor_by_object"][hex(regs["rdi"])] = sample
    elif site_va == 0x26BBD0:
        incoming_index = regs["rsi"] & 0xFFFFFFFF
        sample["incoming_index_esi"] = incoming_index
        sample["setter_object"] = _stereo_object(process, regs["rdi"])
        ctor = state["constructor_by_object"].get(hex(regs["rdi"]))
        if ctor is not None:
            sample["matching_constructor_sample_site"] = ctor["site"]
            sample["matching_constructor_params"] = ctor.get("stereo_params")
        if incoming_index == state["target_index"] and regs["rdi"] not in state["target_objects"]:
            state["target_objects"].append(regs["rdi"])
    elif site_va == 0x26BCA0:
        sample["size_setter_object"] = _stereo_object(process, regs["rdi"])
        sample["size_arg_ptr"] = regs["rsi"]
        sample["size_arg_u32"] = _u32s(process, regs["rsi"], 4)
    elif site_va in (0x26BD90, 0x26BF90):
        sample["target_object"] = _stereo_object(process, regs["rdi"])
        sample["previous_or_input_object"] = _stereo_object(process, regs["rsi"])
    elif site_va == 0x26C220:
        sample["target_object"] = _stereo_object(process, regs["rdi"])
    elif site_va in (0x26DD40, 0x26E120):
        sample["target_object"] = _stereo_object(process, regs["rdi"])

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
        bp.SetScriptCallbackFunction("stereolayer_constructor_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_STEREO_CTOR_ATTACHED", ids)


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


def drive_until_exit_or_step_cap(debugger, max_steps=24000):
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
    print("L16_STEREO_CTOR_DRIVE_STEPS", steps)


def payload(debugger):
    packet = dict(_state())
    packet["process"] = _process_packet(debugger)
    packet["breakpoint_hit_counts"] = _breakpoint_hit_counts(debugger)
    return packet


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_STEREO_CTOR_WROTE", path)


def report(debugger):
    print("L16_STEREO_CTOR_BEGIN")
    print(json.dumps(payload(debugger), indent=2, sort_keys=True))
    print("L16_STEREO_CTOR_END")
