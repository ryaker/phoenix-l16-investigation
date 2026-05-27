import builtins
import json
import struct


SITES = {
    0x26BBD0: "index_setter_26bbd0",
    0x26BCA0: "size_setter_26bca0",
    0x276790: "runpass_action_276790",
    0x276860: "mode8_worker_entry_276860",
    0x277CCB: "mode8_worker_exit_277ccb",
    0x26AA30: "upsample_previous_slot90_call",
    0x26AA39: "upsample_previous_slot90_after",
}


WATCH_FIELDS = {
    0x2A0: "size_qword_0x2a0",
    0x2B0: "descriptor_dims_qword_0x2b0",
    0x2C0: "descriptor_stride_qword_0x2c0",
    0x2C8: "descriptor_data_ptr_qword_0x2c8",
}


def reset(label="", target_index=5, sample_limit=240, watch_hit_cap=160, watch_offsets=None):
    builtins.l16_stereolayer_index5_watch = {
        "label": label,
        "target_index": target_index,
        "sample_limit": sample_limit,
        "watch_hit_cap": watch_hit_cap,
        "watch_offsets": list(WATCH_FIELDS) if watch_offsets is None else list(watch_offsets),
        "counts": {name: 0 for name in SITES.values()},
        "breakpoint_ids": {},
        "watchpoint_ids": {},
        "watchpoints_armed": False,
        "target_object": None,
        "target_object_index": None,
        "disabled_after_cap": [],
        "samples": [],
        "watchpoint_samples": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_stereolayer_index5_watch"):
        reset()
    return builtins.l16_stereolayer_index5_watch


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


def _stack(thread, max_frames=14):
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
    return {
        "addr": addr,
        "read_ok": True,
        "begin": begin,
        "end": end,
        "cap": cap,
        "byte_size": end - begin if end >= begin else None,
        "first_qword": _read_qword(process, begin) if begin else None,
    }


def _stereo_object(process, obj):
    if not obj:
        return {"object": obj, "read_ok": False}
    width = _read(process, obj + 0x2A0, 4)
    height = _read(process, obj + 0x2A4, 4)
    return {
        "object": obj,
        "vtable": _read_qword(process, obj),
        "index_0x8": _u32(_read(process, obj + 0x8, 4), 0)
        if _read(process, obj + 0x8, 4) is not None
        else None,
        "mode_0xc": _u32(_read(process, obj + 0xC, 4), 0)
        if _read(process, obj + 0xC, 4) is not None
        else None,
        "tile_0x1c": _u32(_read(process, obj + 0x1C, 4), 0)
        if _read(process, obj + 0x1C, 4) is not None
        else None,
        "flag_0x20": _u32(_read(process, obj + 0x20, 4), 0)
        if _read(process, obj + 0x20, 4) is not None
        else None,
        "depth_width_0x2a0": _u32(width, 0) if width is not None else None,
        "depth_height_0x2a4": _u32(height, 0) if height is not None else None,
        "aux_descriptor_0x208": _descriptor(process, obj + 0x208),
        "depth_descriptor_0x2a8": _descriptor(process, obj + 0x2A8),
        "alt_descriptor_0x2d8": _descriptor(process, obj + 0x2D8),
        "source_vector_0x240": _vector_summary(process, obj + 0x240),
        "scale_vector_0x270": _vector_summary(process, obj + 0x270),
    }


def _append_sample(sample):
    state = _state()
    if len(state["samples"]) < state["sample_limit"]:
        state["samples"].append(sample)


def _append_watchpoint_sample(sample):
    state = _state()
    if len(state["watchpoint_samples"]) < state["sample_limit"]:
        state["watchpoint_samples"].append(sample)


def _disable_breakpoint(debugger, name):
    bp_id = _state()["breakpoint_ids"].get(name)
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id) if bp_id else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def _cap(name):
    if name in ("runpass_action_276790", "mode8_worker_entry_276860"):
        return 48
    if name == "mode8_worker_exit_277ccb":
        return 48
    return 128


def _arm_watchpoints(target, obj):
    state = _state()
    if state["watchpoints_armed"]:
        return
    lldb = builtins.__import__("lldb")
    for offset in state.get("watch_offsets", list(WATCH_FIELDS)):
        name = WATCH_FIELDS[offset]
        error = lldb.SBError()
        wp = target.WatchAddress(obj + offset, 8, False, True, error)
        if error.Success() and wp and wp.IsValid():
            state["watchpoint_ids"][str(wp.GetID())] = {
                "name": name,
                "addr": obj + offset,
                "offset": offset,
            }
        else:
            state["errors"].append(
                f"failed to arm watchpoint {name} at {hex(obj + offset)}: {error.GetCString()}"
            )
    state["watchpoints_armed"] = bool(state["watchpoint_ids"])


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

    if site_va == 0x26BBD0:
        sample["setter_object"] = _stereo_object(process, regs["rdi"])
        sample["incoming_index_esi"] = regs["rsi"] & 0xFFFFFFFF
        if (regs["rsi"] & 0xFFFFFFFF) == state["target_index"]:
            state["target_object"] = regs["rdi"]
            state["target_object_index"] = regs["rsi"] & 0xFFFFFFFF
            _arm_watchpoints(target, regs["rdi"])
            sample["armed_watchpoints"] = dict(state["watchpoint_ids"])
    elif site_va == 0x26BCA0:
        sample["size_setter_object"] = _stereo_object(process, regs["rdi"])
        sample["size_arg_ptr"] = regs["rsi"]
        sample["size_arg_qwords"] = _qwords(process, regs["rsi"], 2)
    elif site_va in (0x276790, 0x276860):
        layer_obj = regs["rdi"] if site_va == 0x276860 else _read_qword(process, regs["rdi"] + 0x8)
        sample["layer_object"] = _stereo_object(process, layer_obj)
    elif site_va == 0x277CCB:
        layer_obj = _read_qword(process, regs["rbp"] - 0x1C8)
        sample["layer_object"] = _stereo_object(process, layer_obj)
    elif site_va == 0x26AA30:
        sample["upsample_object"] = regs["rdi"]
        sample["previous_layer_object"] = regs["rsi"]
        sample["previous_layer_snapshot"] = _stereo_object(process, regs["rsi"])
    elif site_va == 0x26AA39:
        sample["previous_layer_object"] = regs["rbx"]
        sample["previous_layer_slot90_return"] = regs["rax"]
        sample["previous_layer_snapshot"] = _stereo_object(process, regs["rbx"])
        sample["previous_layer_return_descriptor"] = _descriptor(process, regs["rax"])

    _append_sample(sample)

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
        bp.SetScriptCallbackFunction("stereolayer_index5_watch_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_STEREO_INDEX5_WATCH_ATTACHED", ids)


def _watchpoint_hit_counts(debugger):
    target = debugger.GetSelectedTarget()
    out = {}
    for wp_id, meta in _state().get("watchpoint_ids", {}).items():
        wp = target.FindWatchpointByID(int(wp_id))
        out[wp_id] = {
            "name": meta["name"],
            "hit_count": wp.GetHitCount() if wp and wp.IsValid() else None,
            "enabled": wp.IsEnabled() if wp and wp.IsValid() else None,
        }
    return out


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


def _record_watchpoint_stop(debugger):
    lldb = builtins.__import__("lldb")
    state = _state()
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    thread = process.GetSelectedThread()
    if not thread or not thread.IsValid():
        return
    if thread.GetStopReason() != lldb.eStopReasonWatchpoint:
        return

    wp_id = thread.GetStopReasonDataAtIndex(0) if thread.GetStopReasonDataCount() else None
    meta = state["watchpoint_ids"].get(str(wp_id), {})
    frame = thread.GetFrameAtIndex(0)
    regs = _registers(frame)
    target_object = state.get("target_object")
    sample = {
        "watchpoint_id": wp_id,
        "watchpoint": meta,
        "thread_id": thread.GetThreadID(),
        "pc": frame.GetPC(),
        "libcp_va": _module_va(target, frame.GetPC()),
        "registers": regs,
        "stack": _stack(thread, max_frames=20),
        "target_object": _stereo_object(process, target_object)
        if target_object
        else None,
    }
    _append_watchpoint_sample(sample)

    watch_hits = len(state["watchpoint_samples"])
    if watch_hits >= state["watch_hit_cap"]:
        for watch_id in state["watchpoint_ids"]:
            wp = target.FindWatchpointByID(int(watch_id))
            if wp and wp.IsValid():
                wp.SetEnabled(False)
        if "watchpoints" not in state["disabled_after_cap"]:
            state["disabled_after_cap"].append("watchpoints")


def drive_until_exit_or_step_cap(debugger, max_steps=24000):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while (
        process.IsValid()
        and process.GetState() == lldb.eStateStopped
        and steps < max_steps
    ):
        _record_watchpoint_stop(debugger)
        steps += 1
        process.Continue()
    _state()["drive_steps"] = steps
    _state()["drive_hit_step_cap"] = (
        process.IsValid() and process.GetState() == lldb.eStateStopped and steps >= max_steps
    )
    print("L16_STEREO_INDEX5_WATCH_DRIVE_STEPS", steps)


def payload(debugger):
    packet = dict(_state())
    packet["process"] = _process_packet(debugger)
    packet["breakpoint_hit_counts"] = _breakpoint_hit_counts(debugger)
    packet["watchpoint_hit_counts"] = _watchpoint_hit_counts(debugger)
    return packet


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_STEREO_INDEX5_WATCH_WROTE", path)


def report(debugger):
    print("L16_STEREO_INDEX5_WATCH_BEGIN")
    print(json.dumps(payload(debugger), indent=2, sort_keys=True))
    print("L16_STEREO_INDEX5_WATCH_END")
