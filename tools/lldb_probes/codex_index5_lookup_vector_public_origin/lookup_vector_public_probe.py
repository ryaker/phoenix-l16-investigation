import builtins
import hashlib
import json
import struct


SITES = {
    0x26BBD0: "index_setter_26bbd0",
    0xF043E: "lookup_vector_after_copy_f043e",
    0x267010: "descriptor_build_267010_entry",
}


def reset(label="", target_index=5, sample_limit=32):
    builtins.l16_lookup_vector_public_probe = {
        "label": label,
        "target_index": target_index,
        "sample_limit": sample_limit,
        "target_object": None,
        "counts": {name: 0 for name in SITES.values()},
        "target_counts": {name: 0 for name in SITES.values()},
        "breakpoint_ids": {},
        "samples": [],
        "target_samples": [],
        "errors": [],
        "disabled_after_cap": [],
    }


def _state():
    if not hasattr(builtins, "l16_lookup_vector_public_probe"):
        reset()
    return builtins.l16_lookup_vector_public_probe


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


def _stack(thread, max_frames=20):
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


def _f32_preview(raw):
    if raw is None:
        return []
    count = len(raw) // 4
    return [_f32(raw, index * 4) for index in range(count)]


def _u32_preview(raw):
    if raw is None:
        return []
    count = len(raw) // 4
    return [_u32(raw, index * 4) for index in range(count)]


def _vector_dump(process, vector_addr, max_full_bytes=8192):
    header = _read(process, vector_addr, 24)
    if header is None:
        return {"addr": vector_addr, "read_ok": False}
    begin = _u64(header, 0)
    end = _u64(header, 8)
    cap = _u64(header, 16)
    byte_size = end - begin if end >= begin else None
    raw = None
    if begin and byte_size is not None and 0 <= byte_size <= max_full_bytes:
        raw = _read(process, begin, byte_size)
    first = raw[: min(len(raw), 64)] if raw is not None else None
    last = raw[-min(len(raw), 64) :] if raw is not None and raw else None
    return {
        "addr": vector_addr,
        "read_ok": True,
        "begin": begin,
        "end": end,
        "cap": cap,
        "byte_size": byte_size,
        "count_f32": (byte_size // 4 if byte_size is not None and byte_size % 4 == 0 else None),
        "raw_sha256": hashlib.sha256(raw).hexdigest() if raw is not None else None,
        "raw_hex": raw.hex() if raw is not None else None,
        "first_f32": _f32_preview(first),
        "last_f32": _f32_preview(last),
        "first_u32": _u32_preview(first),
        "last_u32": _u32_preview(last),
    }


def _source_span_dump(process, frame, byte_size):
    rbp = _u(frame, "rbp")
    source_begin = _read_qword(process, rbp - 0x30)
    raw = None
    if source_begin and byte_size is not None and 0 <= byte_size <= 8192:
        raw = _read(process, source_begin, byte_size)
    first = raw[: min(len(raw), 64)] if raw is not None else None
    last = raw[-min(len(raw), 64) :] if raw is not None and raw else None
    return {
        "source_begin_rbp_minus_0x30": source_begin,
        "byte_size": byte_size,
        "raw_sha256": hashlib.sha256(raw).hexdigest() if raw is not None else None,
        "raw_hex": raw.hex() if raw is not None else None,
        "first_f32": _f32_preview(first),
        "last_f32": _f32_preview(last),
    }


def _object_fields(process, obj):
    if not obj:
        return {"object": obj, "read_ok": False}
    return {
        "object": obj,
        "read_ok": True,
        "index_0x8": _u32(_read(process, obj + 0x8, 4), 0)
        if _read(process, obj + 0x8, 4) is not None
        else None,
        "mode_0xc": _u32(_read(process, obj + 0xC, 4), 0)
        if _read(process, obj + 0xC, 4) is not None
        else None,
        "scalar_0x18_f32": _f32(_read(process, obj + 0x18, 4), 0)
        if _read(process, obj + 0x18, 4) is not None
        else None,
        "source_record_vector_0x258": _vector_dump(process, obj + 0x258, max_full_bytes=0),
        "near_far_0x298_0x29c_f32": [
            _f32(_read(process, obj + 0x298, 4), 0)
            if _read(process, obj + 0x298, 4) is not None
            else None,
            _f32(_read(process, obj + 0x29C, 4), 0)
            if _read(process, obj + 0x29C, 4) is not None
            else None,
        ],
        "depth_width_0x2a0": _u32(_read(process, obj + 0x2A0, 4), 0)
        if _read(process, obj + 0x2A0, 4) is not None
        else None,
        "depth_height_0x2a4": _u32(_read(process, obj + 0x2A4, 4), 0)
        if _read(process, obj + 0x2A4, 4) is not None
        else None,
    }


def _append(sample, is_target=False, record_general=True):
    state = _state()
    if is_target and len(state["target_samples"]) < state["sample_limit"]:
        state["target_samples"].append(sample)
    if record_general and len(state["samples"]) < state["sample_limit"]:
        state["samples"].append(sample)


def _disable_breakpoint(debugger, name):
    bp_id = _state()["breakpoint_ids"].get(name)
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id) if bp_id else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)
        if name not in _state()["disabled_after_cap"]:
            _state()["disabled_after_cap"].append(name)


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

    target_object = state.get("target_object")
    is_target = False

    if site_va == 0x26BBD0:
        incoming_index = regs["rsi"] & 0xFFFFFFFF
        sample["incoming_index_esi"] = incoming_index
        sample["setter_object_rdi"] = regs["rdi"]
        if incoming_index == state["target_index"]:
            state["target_object"] = regs["rdi"]
            target_object = regs["rdi"]
            is_target = True
            sample["selected_target_object"] = target_object
    elif site_va == 0xF043E and target_object:
        is_target = regs["r14"] == target_object + 0xE0
        sample["r14_equals_target_plus_0xe0"] = is_target
        if is_target:
            vector = _vector_dump(process, target_object + 0xE0)
            sample["target_object_fields"] = _object_fields(process, target_object)
            sample["target_lookup_vector_0xe0"] = vector
            sample["source_span_copied_by_f02d0"] = _source_span_dump(
                process, frame, vector.get("byte_size")
            )
    elif site_va == 0x267010 and target_object:
        is_target = regs["rdx"] == target_object + 0xE0
        sample["rdx_equals_target_plus_0xe0"] = is_target
        if is_target:
            sample["target_object_fields"] = _object_fields(process, target_object)
            sample["target_lookup_vector_0xe0"] = _vector_dump(process, target_object + 0xE0)
            sample["source_descriptor_arg_rsi_qwords"] = [
                _read_qword(process, regs["rsi"] + off) for off in range(0, 0x30, 8)
            ]

    if is_target:
        state["target_counts"][name] = state["target_counts"].get(name, 0) + 1
    record_general = site_va != 0xF043E or target_object is not None
    _append(sample, is_target=is_target, record_general=record_general)

    if name == "lookup_vector_after_copy_f043e" and is_target:
        _disable_breakpoint(target.GetDebugger(), name)
    if name == "descriptor_build_267010_entry" and is_target:
        _disable_breakpoint(target.GetDebugger(), name)
    if name == "index_setter_26bbd0" and is_target:
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
        bp.SetScriptCallbackFunction("lookup_vector_public_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_LOOKUP_VECTOR_PUBLIC_ATTACHED", ids)


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
    print("L16_LOOKUP_VECTOR_PUBLIC_DRIVE_STEPS", steps)


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
    print("L16_LOOKUP_VECTOR_PUBLIC_WROTE", path)
