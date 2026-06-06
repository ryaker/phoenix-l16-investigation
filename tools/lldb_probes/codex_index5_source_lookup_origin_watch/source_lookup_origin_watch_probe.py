import builtins
import json
import struct


SITES = {
    0x26B750: "stereolayer_ctor_26b750",
    0x26BBD0: "index_setter_26bbd0",
    0x26E4C6: "source_index_branch_26e4c6",
    0x299C70: "producer_299c70_entry",
    0x26E620: "lookup_vector_setup_26e620",
    0x267010: "descriptor_build_267010_entry",
    0x26E638: "descriptor_build_267010_after",
}


DEFAULT_WATCH_OFFSETS = [0xE0, 0xE8, 0xF0, 0xF8]


FIELD_NAMES = {
    0xE0: "lookup_begin_qword_0xe0",
    0xE8: "lookup_end_qword_0xe8",
    0xF0: "lookup_cap_qword_0xf0",
    0xF8: "source_object_base_0xf8",
    0x108: "source_record_base_ptr_0x108",
    0x128: "source_width_0x128",
    0x12C: "source_height_0x12c",
    0x130: "source_stride_0x130",
    0x138: "source_offset_table_ptr_0x138",
}


def reset(label="", target_index=5, watch_offsets=None, sample_limit=160, watch_hit_cap=80):
    builtins.l16_source_lookup_origin_watch = {
        "label": label,
        "target_index": target_index,
        "watch_offsets": list(DEFAULT_WATCH_OFFSETS if watch_offsets is None else watch_offsets),
        "sample_limit": sample_limit,
        "watch_hit_cap": watch_hit_cap,
        "target_object": None,
        "watchpoints_armed": False,
        "watchpoint_ids": {},
        "breakpoint_ids": {},
        "counts": {name: 0 for name in SITES.values()},
        "samples": [],
        "watchpoint_samples": [],
        "disabled_after_cap": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_source_lookup_origin_watch"):
        reset()
    return builtins.l16_source_lookup_origin_watch


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
    names = (
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
    return {name: _u(frame, name) for name in names}


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


def _vector_header(process, addr):
    data = _read(process, addr, 24)
    if data is None:
        return {"addr": addr, "read_ok": False}
    begin = _u64(data, 0)
    end = _u64(data, 8)
    cap = _u64(data, 16)
    count_f32 = None
    first_f32 = []
    byte_size = end - begin if end >= begin else None
    if begin and byte_size is not None and byte_size > 0 and byte_size % 4 == 0:
        count_f32 = byte_size // 4
        raw = _read(process, begin, min(32, byte_size))
        if raw is not None:
            first_f32 = [_f32(raw, off) for off in range(0, len(raw), 4)]
    return {
        "addr": addr,
        "read_ok": True,
        "begin": begin,
        "end": end,
        "cap": cap,
        "byte_size": byte_size,
        "count_f32": count_f32,
        "first_f32": first_f32,
    }


def _source_object(process, obj):
    base = obj + 0xF8 if obj else 0
    record_base = _read_qword(process, base + 0x10) if base else None
    offset_table = _read_qword(process, base + 0x40) if base else None
    record_sample = []
    offset_sample = []
    if record_base:
        raw = _read(process, record_base, 32)
        if raw is not None:
            record_sample = [_u32(raw, off) for off in range(0, len(raw), 4)]
    if offset_table:
        raw = _read(process, offset_table, 32)
        if raw is not None:
            offset_sample = [_u32(raw, off) for off in range(0, len(raw), 4)]
    width_data = _read(process, base + 0x30, 4) if base else None
    height_data = _read(process, base + 0x34, 4) if base else None
    stride_data = _read(process, base + 0x38, 4) if base else None
    return {
        "addr": base,
        "read_ok": bool(base),
        "first_qwords": [
            _read_qword(process, base + off) for off in range(0, 0x48, 8)
        ]
        if base
        else [],
        "record_base_0x10": record_base,
        "width_0x30": _u32(width_data) if width_data is not None else None,
        "height_0x34": _u32(height_data) if height_data is not None else None,
        "stride_0x38": _u32(stride_data) if stride_data is not None else None,
        "offset_table_0x40": offset_table,
        "record_base_first_u32": record_sample,
        "offset_table_first_u32": offset_sample,
    }


def _snapshot(process, obj):
    if not obj:
        return {"object": obj, "read_ok": False}
    return {
        "object": obj,
        "read_ok": True,
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
        "flag_0x78": _u32(_read(process, obj + 0x78, 4), 0)
        if _read(process, obj + 0x78, 4) is not None
        else None,
        "lookup_vector_0xe0": _vector_header(process, obj + 0xE0),
        "source_object_0xf8": _source_object(process, obj),
    }


def _append_sample(key, sample):
    state = _state()
    if len(state[key]) < state["sample_limit"]:
        state[key].append(sample)


def _disable_breakpoint(debugger, name):
    bp_id = _state()["breakpoint_ids"].get(name)
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id) if bp_id else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)
        if name not in _state()["disabled_after_cap"]:
            _state()["disabled_after_cap"].append(name)


def _arm_watchpoints(target, obj):
    state = _state()
    if state["watchpoints_armed"]:
        return
    lldb = builtins.__import__("lldb")
    for offset in state["watch_offsets"]:
        error = lldb.SBError()
        wp = target.WatchAddress(obj + offset, 8, False, True, error)
        if wp and wp.IsValid() and error.Success():
            state["watchpoint_ids"][str(wp.GetID())] = {
                "offset": offset,
                "name": FIELD_NAMES.get(offset, f"field_{offset:#x}"),
                "addr": obj + offset,
            }
        else:
            state["errors"].append(
                f"failed to arm watchpoint {offset:#x} at {obj + offset:#x}: {error.GetCString()}"
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

    if site_va == 0x26B750:
        sample["ctor_object"] = _snapshot(process, regs["rdi"])
        sample["ctor_arg_rsi"] = regs["rsi"]
    elif site_va == 0x26BBD0:
        sample["incoming_index_esi"] = regs["rsi"] & 0xFFFFFFFF
        sample["setter_object"] = _snapshot(process, regs["rdi"])
        if (regs["rsi"] & 0xFFFFFFFF) == state["target_index"]:
            state["target_object"] = regs["rdi"]
            _arm_watchpoints(target, regs["rdi"])
            sample["armed_watchpoints"] = dict(state["watchpoint_ids"])
    elif state.get("target_object"):
        obj = state["target_object"]
        sample["target_object_snapshot"] = _snapshot(process, obj)
        if site_va == 0x26E4C6:
            sample["branch_this_r12"] = regs["r12"]
            sample["branch_rdx"] = regs["rdx"]
            sample["rdx_equals_target_plus_0xf8"] = regs["rdx"] == obj + 0xF8
        elif site_va == 0x299C70:
            sample["producer_arg_rdi"] = regs["rdi"]
            sample["producer_arg_rsi"] = regs["rsi"]
            sample["rsi_equals_target_plus_0xf8"] = regs["rsi"] == obj + 0xF8
        elif site_va == 0x26E620:
            sample["lookup_setup_this_r12"] = regs["r12"]
        elif site_va == 0x267010:
            sample["source_arg_rsi"] = regs["rsi"]
            sample["lookup_arg_rdx"] = regs["rdx"]
            sample["rdx_equals_target_plus_0xe0"] = regs["rdx"] == obj + 0xE0

    _append_sample("samples", sample)
    if state["counts"][name] >= 24 and name not in ("index_setter_26bbd0",):
        _disable_breakpoint(target.GetDebugger(), name)
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
        bp.SetScriptCallbackFunction("source_lookup_origin_watch_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_SOURCE_LOOKUP_ORIGIN_ATTACHED", ids)


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
    sample = {
        "watchpoint_id": wp_id,
        "watchpoint": meta,
        "thread_id": thread.GetThreadID(),
        "pc": frame.GetPC(),
        "libcp_va": _module_va(target, frame.GetPC()),
        "registers": regs,
        "stack": _stack(thread, max_frames=24),
        "target_object_snapshot": _snapshot(process, state.get("target_object")),
    }
    _append_sample("watchpoint_samples", sample)

    if len(state["watchpoint_samples"]) >= state["watch_hit_cap"]:
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
    while process.IsValid() and process.GetState() == lldb.eStateStopped and steps < max_steps:
        _record_watchpoint_stop(debugger)
        steps += 1
        process.Continue()
    _state()["drive_steps"] = steps
    _state()["drive_hit_step_cap"] = (
        process.IsValid() and process.GetState() == lldb.eStateStopped and steps >= max_steps
    )
    print("L16_SOURCE_LOOKUP_ORIGIN_DRIVE_STEPS", steps)


def _breakpoint_hit_counts(debugger):
    target = debugger.GetSelectedTarget()
    out = {}
    for name, bp_id in _state().get("breakpoint_ids", {}).items():
        bp = target.FindBreakpointByID(bp_id)
        out[name] = bp.GetHitCount() if bp and bp.IsValid() else None
    return out


def _watchpoint_hit_counts(debugger):
    target = debugger.GetSelectedTarget()
    out = {}
    for wp_id, meta in _state().get("watchpoint_ids", {}).items():
        wp = target.FindWatchpointByID(int(wp_id))
        out[wp_id] = {
            "name": meta.get("name"),
            "offset": meta.get("offset"),
            "hit_count": wp.GetHitCount() if wp and wp.IsValid() else None,
            "enabled": wp.IsEnabled() if wp and wp.IsValid() else None,
        }
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
    print("L16_SOURCE_LOOKUP_ORIGIN_WROTE", path)
