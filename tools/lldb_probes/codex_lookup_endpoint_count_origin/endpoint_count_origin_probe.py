import builtins
import hashlib
import json
import struct


SITES = {
    0x26BA90: "setup_entry_26ba90",
    0x26BB3C: "setup_after_endpoint_store_26bb3c",
    0x26BBD0: "index_setter_26bbd0",
    0xF043E: "lookup_copy_after_f043e",
}


def reset(label="", target_index=5, sample_limit=128):
    builtins.l16_endpoint_count_origin_probe = {
        "label": label,
        "target_index": target_index,
        "sample_limit": sample_limit,
        "counts": {name: 0 for name in SITES.values()},
        "target_counts": {name: 0 for name in SITES.values()},
        "breakpoint_ids": {},
        "samples": [],
        "target_samples": [],
        "objects": {},
        "target_object": None,
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_endpoint_count_origin_probe"):
        reset()
    return builtins.l16_endpoint_count_origin_probe


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


def _vector_dump(process, vector_addr, max_full_bytes=65536):
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
    return {
        "addr": vector_addr,
        "read_ok": True,
        "begin": begin,
        "end": end,
        "cap": cap,
        "byte_size": byte_size,
        "raw_sha256": hashlib.sha256(raw).hexdigest() if raw is not None else None,
        "raw_hex": raw.hex() if raw is not None else None,
    }


def _f32_list(process, addr, count):
    data = _read(process, addr, count * 4)
    if data is None:
        return None
    return [_f32(data, off) for off in range(0, count * 4, 4)]


def _u32_list(process, addr, count):
    data = _read(process, addr, count * 4)
    if data is None:
        return None
    return [_u32(data, off) for off in range(0, count * 4, 4)]


def _object_fields(process, obj):
    if not obj:
        return {"object": obj, "read_ok": False}
    return {
        "object": obj,
        "read_ok": True,
        "index_0x8": _u32_list(process, obj + 0x8, 1)[0]
        if _u32_list(process, obj + 0x8, 1)
        else None,
        "mode_0xc": _u32_list(process, obj + 0xC, 1)[0]
        if _u32_list(process, obj + 0xC, 1)
        else None,
        "param_copy_0x10_f32": _f32_list(process, obj + 0x10, 28),
        "scalar_0x18_f32": _f32_list(process, obj + 0x18, 1)[0]
        if _f32_list(process, obj + 0x18, 1)
        else None,
        "tile_0x1c_u32": _u32_list(process, obj + 0x1C, 1)[0]
        if _u32_list(process, obj + 0x1C, 1)
        else None,
        "source_vector_0x240": _vector_dump(process, obj + 0x240),
        "source_record_vector_0x258": _vector_dump(process, obj + 0x258),
        "scale_vector_0x270": _vector_dump(process, obj + 0x270),
        "aux_vector_0x288": _vector_dump(process, obj + 0x288),
        "near_far_0x298_0x29c_f32": _f32_list(process, obj + 0x298, 2),
        "depth_width_0x2a0": _u32_list(process, obj + 0x2A0, 1)[0]
        if _u32_list(process, obj + 0x2A0, 1)
        else None,
        "depth_height_0x2a4": _u32_list(process, obj + 0x2A4, 1)[0]
        if _u32_list(process, obj + 0x2A4, 1)
        else None,
        "lookup_vector_0xe0": _vector_dump(process, obj + 0xE0),
    }


def _input_vectors(process, regs):
    return {
        "input_source_vector_rsi": _vector_dump(process, regs["rsi"]),
        "input_source_record_vector_rdx": _vector_dump(process, regs["rdx"]),
        "input_scale_vector_rcx": _vector_dump(process, regs["rcx"]),
    }


def _object_key(obj):
    return hex(obj)


def _remember_object(obj, key, value):
    state = _state()
    entry = state["objects"].setdefault(_object_key(obj), {"object": obj})
    entry[key] = value


def _append(sample, is_target=False):
    state = _state()
    if len(state["samples"]) < state["sample_limit"]:
        state["samples"].append(sample)
    if is_target and len(state["target_samples"]) < state["sample_limit"]:
        state["target_samples"].append(sample)


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
    is_target = False

    if site_va == 0x26BA90:
        obj = regs["rdi"]
        sample["setup_object_rdi"] = obj
        sample["setup_inputs"] = _input_vectors(process, regs)
        _remember_object(obj, "setup_entry", sample)
    elif site_va == 0x26BB3C:
        obj = regs["rbx"]
        sample["setup_object_rbx"] = obj
        sample["object_fields_after_setup"] = _object_fields(process, obj)
        _remember_object(obj, "setup_after_endpoint_store", sample)
    elif site_va == 0x26BBD0:
        obj = regs["rdi"]
        incoming_index = regs["rsi"] & 0xFFFFFFFF
        sample["setter_object_rdi"] = obj
        sample["incoming_index_esi"] = incoming_index
        sample["object_fields_at_index_setter"] = _object_fields(process, obj)
        _remember_object(obj, "index_setter", sample)
        if incoming_index == state["target_index"]:
            state["target_object"] = obj
            is_target = True
    elif site_va == 0xF043E:
        obj = state.get("target_object")
        sample["target_object"] = obj
        if obj:
            is_target = regs["r14"] == obj + 0xE0
            sample["r14_equals_target_plus_0xe0"] = is_target
            if is_target:
                sample["target_fields_at_lookup_copy"] = _object_fields(process, obj)
                _remember_object(obj, "lookup_copy_after", sample)

    if is_target:
        state["target_counts"][name] = state["target_counts"].get(name, 0) + 1
    _append(sample, is_target=is_target)
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
        bp.SetScriptCallbackFunction("endpoint_count_origin_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_ENDPOINT_COUNT_ORIGIN_ATTACHED", ids)


def drive_until_exit_or_step_cap(debugger, max_steps=16000):
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
    print("L16_ENDPOINT_COUNT_ORIGIN_DRIVE_STEPS", steps)


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
    print("L16_ENDPOINT_COUNT_ORIGIN_WROTE", path)
