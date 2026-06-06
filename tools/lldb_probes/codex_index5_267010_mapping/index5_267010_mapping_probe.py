import builtins
import json
import math
import struct


SITES = {
    0x267010: "descriptor_build_267010_entry",
    0x26E638: "after_descriptor_build_267010",
}


def reset(label="", sample_entries=16):
    builtins.l16_index5_267010_mapping_probe = {
        "label": label,
        "sample_entries": sample_entries,
        "counts": {name: 0 for name in SITES.values()},
        "breakpoint_ids": {},
        "samples": [],
        "pending_by_thread": {},
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_index5_267010_mapping_probe"):
        reset()
    return builtins.l16_index5_267010_mapping_probe


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
            "r12",
            "r14",
            "rbp",
            "rsp",
        )
    }


def _descriptor_header(process, addr):
    data = _read(process, addr, 0x30)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "width_0x10": _u32(data, 0x10),
        "height_0x14": _u32(data, 0x14),
        "stride_0x18": _u32(data, 0x18),
        "data_ptr_0x20": _u64(data, 0x20),
        "qwords": [_u64(data, off) for off in range(0, 0x30, 8)],
        "u32": [_u32(data, off) for off in range(0, 0x30, 4)],
    }


def _descriptor_u16_sample(process, addr, count):
    desc = _descriptor_header(process, addr)
    if not desc.get("read_ok"):
        return desc
    data_ptr = desc.get("data_ptr_0x20")
    raw = _read(process, data_ptr, count * 2)
    if raw is None:
        desc["first_u16"] = []
        desc["sample_read_ok"] = False
        return desc
    desc["sample_read_ok"] = True
    desc["first_u16"] = [_u16(raw, off) for off in range(0, len(raw), 2)]
    return desc


def _descriptor_f32_sample(process, addr, count):
    desc = _descriptor_header(process, addr)
    if not desc.get("read_ok"):
        return desc
    data_ptr = desc.get("data_ptr_0x20")
    raw = _read(process, data_ptr, count * 4)
    if raw is None:
        desc["first_f32"] = []
        desc["first_u32"] = []
        desc["sample_read_ok"] = False
        return desc
    desc["sample_read_ok"] = True
    desc["first_f32"] = [_f32(raw, off) for off in range(0, len(raw), 4)]
    desc["first_u32"] = [_u32(raw, off) for off in range(0, len(raw), 4)]
    return desc


def _lookup_vector(process, addr, source_u16_values):
    data = _read(process, addr, 0x18)
    if data is None:
        return {"addr": addr, "read_ok": False}
    begin = _u64(data, 0)
    end = _u64(data, 8)
    cap = _u64(data, 16)
    byte_size = end - begin if end >= begin else None
    count = byte_size // 4 if byte_size is not None else None
    entries = []
    for value in source_u16_values:
        packet = {"index": value}
        if count is None or value >= count:
            packet["in_range"] = False
        else:
            raw = _read(process, begin + value * 4, 4)
            packet["in_range"] = raw is not None
            if raw is not None:
                packet["u32"] = _u32(raw)
                packet["f32"] = _f32(raw)
        entries.append(packet)
    first_raw = _read(process, begin, min(byte_size or 0, 8 * 4)) if begin else None
    first_f32 = []
    if first_raw is not None:
        first_f32 = [_f32(first_raw, off) for off in range(0, len(first_raw), 4)]
    return {
        "addr": addr,
        "read_ok": True,
        "begin": begin,
        "end": end,
        "cap": cap,
        "byte_size": byte_size,
        "count": count,
        "first_f32": first_f32,
        "entries_for_source_u16": entries,
    }


def _stereo_object(process, obj):
    if not obj:
        return {"object": obj, "read_ok": False}
    def u32_at(offset):
        data = _read(process, obj + offset, 4)
        return _u32(data) if data is not None else None
    return {
        "object": obj,
        "read_ok": True,
        "vtable": _read_qword(process, obj),
        "index_0x8": u32_at(0x8),
        "mode_0xc": u32_at(0xC),
        "tile_0x1c": u32_at(0x1C),
        "flag_0x54": u32_at(0x54),
        "flag_0x78": u32_at(0x78),
        "depth_width_0x2a0": u32_at(0x2A0),
        "depth_height_0x2a4": u32_at(0x2A4),
    }


def _object_guess(process, regs):
    if regs.get("r12"):
        return regs["r12"]
    rbp = regs.get("rbp", 0)
    return _read_qword(process, rbp - 0x5C8) if rbp else None


def _append(sample):
    state = _state()
    state["samples"].append(sample)


def _disable_breakpoint(debugger, name):
    bp_id = _state()["breakpoint_ids"].get(name)
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id) if bp_id else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def _compare(expected, actual):
    if expected is None or actual is None:
        return None
    if math.isnan(expected) and math.isnan(actual):
        return True
    return expected == actual


def hit(frame, bp_loc, internal_dict):
    state = _state()
    thread = frame.GetThread()
    thread_id = thread.GetThreadID()
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
        "thread_id": thread_id,
        "registers": regs,
    }

    count = state.get("sample_entries", 16)

    if site_va == 0x267010:
        obj = _object_guess(process, regs)
        source = _descriptor_u16_sample(process, regs["rsi"], count)
        vector = _lookup_vector(process, regs["rdx"], source.get("first_u16", []))
        stereo = _stereo_object(process, obj)
        sample["stereo_object"] = stereo
        sample["source_descriptor_arg_rsi"] = source
        sample["lookup_vector_arg_rdx"] = vector
        state["pending_by_thread"][str(thread_id)] = {
            "stereo_index": stereo.get("index_0x8"),
            "source_first_u16": source.get("first_u16", []),
            "lookup_f32_for_source": [
                entry.get("f32") for entry in vector.get("entries_for_source_u16", [])
            ],
        }
    elif site_va == 0x26E638:
        obj = _object_guess(process, regs)
        built = _descriptor_f32_sample(process, regs["rbp"] - 0x1D0, count)
        stereo = _stereo_object(process, obj)
        pending = state["pending_by_thread"].get(str(thread_id), {})
        lookup_values = pending.get("lookup_f32_for_source", [])
        built_values = built.get("first_f32", [])
        comparisons = [
            _compare(expected, actual)
            for expected, actual in zip(lookup_values, built_values)
        ]
        sample["stereo_object"] = stereo
        sample["built_stack_descriptor_rbp_minus_0x1d0"] = built
        sample["pending_entry"] = pending
        sample["lookup_matches_built_first_values"] = comparisons
        sample["all_compared_values_match"] = bool(comparisons) and all(
            result is True for result in comparisons
        )

    _append(sample)

    if state["counts"][name] >= 8:
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
        bp.SetScriptCallbackFunction("index5_267010_mapping_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_INDEX5_267010_MAPPING_ATTACHED", ids)


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
    print("L16_INDEX5_267010_MAPPING_DRIVE_STEPS", steps)


def payload(debugger):
    packet = dict(_state())
    packet.pop("pending_by_thread", None)
    packet["process"] = _process_packet(debugger)
    packet["breakpoint_hit_counts"] = _breakpoint_hit_counts(debugger)
    return packet


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_INDEX5_267010_MAPPING_WROTE", path)


def report(debugger):
    print("L16_INDEX5_267010_MAPPING_BEGIN")
    print(json.dumps(payload(debugger), indent=2, sort_keys=True))
    print("L16_INDEX5_267010_MAPPING_END")
