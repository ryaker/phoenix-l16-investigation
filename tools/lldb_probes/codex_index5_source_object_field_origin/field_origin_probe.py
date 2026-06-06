import builtins
import json
import struct


SITES = {
    0x26BBD0: "index_setter_26bbd0",
    0x26BE50: "pre_make_source_29a140_call",
    0x26BE55: "post_make_source_29a140",
    0x26BE62: "after_source_control_store",
    0x26BE73: "pre_header_move_28f420_call",
    0x26BE78: "post_header_move_28f420",
    0x26BE89: "pre_descriptor_move_f340_call",
    0x26BE8E: "post_descriptor_move_f340",
    0x26BE96: "pre_header_local_destroy",
    0x26E4C6: "later_source_index_branch",
    0x299C70: "later_299c70_entry",
    0x267010: "later_267010_entry",
}


def reset(label="", target_index=5, sample_limit=240):
    builtins.l16_source_object_field_origin = {
        "label": label,
        "target_index": target_index,
        "target_object": None,
        "target_breakpoints_enabled": False,
        "sample_limit": sample_limit,
        "counts": {name: 0 for name in SITES.values()},
        "target_counts": {},
        "breakpoint_ids": {},
        "samples": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_source_object_field_origin"):
        reset()
    return builtins.l16_source_object_field_origin


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


def _stack(thread, max_frames=16):
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


def _u32_list(process, addr, count):
    raw = _read(process, addr, count * 4)
    if raw is None:
        return []
    return [_u32(raw, off) for off in range(0, len(raw), 4)]


def _qword_list(process, addr, count):
    raw = _read(process, addr, count * 8)
    if raw is None:
        return []
    return [_u64(raw, off) for off in range(0, len(raw), 8)]


def _descriptor(process, addr):
    raw = _read(process, addr, 0x30)
    if raw is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "u32_0x00": _u32(raw, 0x00),
        "u32_0x04": _u32(raw, 0x04),
        "u32_0x08": _u32(raw, 0x08),
        "u32_0x0c": _u32(raw, 0x0C),
        "width_0x10": _u32(raw, 0x10),
        "height_0x14": _u32(raw, 0x14),
        "stride_0x18": _u32(raw, 0x18),
        "field_0x1c": _u32(raw, 0x1C),
        "data_0x20": _u64(raw, 0x20),
        "aux_0x28": _u64(raw, 0x28),
    }


def _source_object(process, obj):
    base = obj + 0xF8 if obj else 0
    if not base:
        return {"addr": base, "read_ok": False}
    return {
        "addr": base,
        "read_ok": True,
        "qwords_0x00_0x50": _qword_list(process, base, 10),
        "control_u32_0x00": _u32_list(process, base, 1)[0]
        if _u32_list(process, base, 1)
        else None,
        "header_qword_0x08": _qword_list(process, base + 0x08, 1)[0]
        if _qword_list(process, base + 0x08, 1)
        else None,
        "record_base_0x10": _qword_list(process, base + 0x10, 1)[0]
        if _qword_list(process, base + 0x10, 1)
        else None,
        "header_qword_0x18": _qword_list(process, base + 0x18, 1)[0]
        if _qword_list(process, base + 0x18, 1)
        else None,
        "descriptor_0x20": _descriptor(process, base + 0x20),
    }


def _stack_locals(process, rbp):
    return {
        "local_b0_u32": _u32_list(process, rbp - 0xB0, 1)[0]
        if _u32_list(process, rbp - 0xB0, 1)
        else None,
        "local_b0_qwords": _qword_list(process, rbp - 0xB0, 6),
        "local_a8_header_qwords": _qword_list(process, rbp - 0xA8, 3),
        "local_90_descriptor": _descriptor(process, rbp - 0x90),
        "local_60_descriptor": _descriptor(process, rbp - 0x60),
    }


def _append_sample(sample):
    state = _state()
    if len(state["samples"]) < state["sample_limit"]:
        state["samples"].append(sample)


def _set_target_breakpoints_enabled(debugger, enabled):
    state = _state()
    target = debugger.GetSelectedTarget()
    for name, bp_id in state.get("breakpoint_ids", {}).items():
        if name == "index_setter_26bbd0":
            continue
        bp = target.FindBreakpointByID(bp_id)
        if bp and bp.IsValid():
            bp.SetEnabled(enabled)
    state["target_breakpoints_enabled"] = enabled


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
    target_obj = state.get("target_object")

    if site_va == 0x26BBD0:
        incoming = regs["rsi"] & 0xFFFFFFFF
        if incoming == state["target_index"]:
            state["target_object"] = regs["rdi"]
            if not state.get("target_breakpoints_enabled"):
                _set_target_breakpoints_enabled(target.GetDebugger(), True)
        sample = {
            "site": name,
            "site_va": site_va,
            "thread_id": thread.GetThreadID(),
            "incoming_index_esi": incoming,
            "setter_object": regs["rdi"],
            "target_object_after": state.get("target_object"),
            "registers": regs,
            "stack": _stack(thread),
        }
        _append_sample(sample)
        return False

    is_target_body = target_obj and regs.get("r14") == target_obj
    is_target_later = False
    if target_obj and site_va == 0x26E4C6:
        is_target_later = regs.get("r12") == target_obj or regs.get("rdx") == target_obj + 0xF8
    elif target_obj and site_va == 0x299C70:
        is_target_later = regs.get("rsi") == target_obj + 0xF8
    elif target_obj and site_va == 0x267010:
        is_target_later = regs.get("rdx") == target_obj + 0xE0

    if not (is_target_body or is_target_later):
        return False

    state["target_counts"][name] = state["target_counts"].get(name, 0) + 1
    sample = {
        "site": name,
        "site_va": site_va,
        "thread_id": thread.GetThreadID(),
        "target_object": target_obj,
        "registers": regs,
        "stack": _stack(thread),
        "source_object_0xf8": _source_object(process, target_obj),
    }

    if is_target_body:
        sample["stack_locals"] = _stack_locals(process, regs["rbp"])
        sample["r14_equals_target"] = True
    if site_va == 0x26BE73:
        sample["move_28f420_dest_rdi"] = regs["rdi"]
        sample["move_28f420_src_rsi"] = regs["rsi"]
        sample["dest_is_target_plus_0x100"] = regs["rdi"] == target_obj + 0x100
        sample["src_is_rbp_minus_0xa8"] = regs["rsi"] == regs["rbp"] - 0xA8
    elif site_va == 0x26BE89:
        sample["move_f340_dest_rdi"] = regs["rdi"]
        sample["move_f340_src_rsi"] = regs["rsi"]
        sample["dest_is_target_plus_0x118"] = regs["rdi"] == target_obj + 0x118
        sample["src_is_rbp_minus_0x90"] = regs["rsi"] == regs["rbp"] - 0x90
    elif site_va == 0x26E4C6:
        sample["rdx_equals_target_plus_0xf8"] = regs["rdx"] == target_obj + 0xF8
    elif site_va == 0x299C70:
        sample["rsi_equals_target_plus_0xf8"] = regs["rsi"] == target_obj + 0xF8
    elif site_va == 0x267010:
        sample["rdx_equals_target_plus_0xe0"] = regs["rdx"] == target_obj + 0xE0

    _append_sample(sample)
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
        bp.SetScriptCallbackFunction("field_origin_probe.hit")
        if name != "index_setter_26bbd0":
            bp.SetEnabled(False)
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_FIELD_ORIGIN_ATTACHED", ids)


def drive_until_exit_or_step_cap(debugger, max_steps=12000):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process.IsValid() and process.GetState() == lldb.eStateStopped and steps < max_steps:
        steps += 1
        process.Continue()
    _state()["drive_steps"] = steps
    _state()["drive_hit_step_cap"] = (
        process.IsValid() and process.GetState() == lldb.eStateStopped and steps >= max_steps
    )
    print("L16_FIELD_ORIGIN_DRIVE_STEPS", steps)


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


def payload(debugger):
    packet = dict(_state())
    packet["process"] = _process_packet(debugger)
    packet["breakpoint_hit_counts"] = _breakpoint_hit_counts(debugger)
    return packet


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_FIELD_ORIGIN_WROTE", path)
