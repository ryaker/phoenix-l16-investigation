import builtins
import json
import math
import struct


SITES = {
    0x26E4C6: "branch_to_299c70_source_path",
    0x299C70: "producer_299c70_entry",
    0x299D06: "producer_299c70_dispatch_call",
    0x299D0B: "producer_299c70_after_dispatch",
    0x26E4D5: "after_299c70_return",
    0x26E4E0: "before_temp_to_source_move",
    0x26E4E5: "after_temp_to_source_move",
    0x26E633: "callsite_267010_from_source_descriptor",
    0x267010: "descriptor_build_267010_entry",
    0x26E638: "after_descriptor_build_267010",
}


def reset(label="", sample_entries=16):
    builtins.l16_source_index_producer_probe = {
        "label": label,
        "sample_entries": sample_entries,
        "counts": {name: 0 for name in SITES.values()},
        "breakpoint_ids": {},
        "samples": [],
        "chains": [],
        "active_chain_by_thread": {},
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_source_index_producer_probe"):
        reset()
    return builtins.l16_source_index_producer_probe


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    if not addr or size <= 0:
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


def _ptr_module_va(target, ptr):
    base = _libcp_base(target)
    if base is not None and ptr and ptr >= base:
        return ptr - base
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


def _stack(thread, max_frames=10):
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


def _descriptor_u16(process, addr, count):
    desc = _descriptor_header(process, addr)
    if not desc.get("read_ok"):
        return desc
    data_ptr = desc.get("data_ptr_0x20")
    raw = _read(process, data_ptr, count * 2)
    if raw is None:
        desc["sample_read_ok"] = False
        desc["first_u16"] = []
        return desc
    desc["sample_read_ok"] = True
    desc["first_u16"] = [_u16(raw, off) for off in range(0, len(raw), 2)]
    return desc


def _descriptor_f32(process, addr, count):
    desc = _descriptor_header(process, addr)
    if not desc.get("read_ok"):
        return desc
    data_ptr = desc.get("data_ptr_0x20")
    raw = _read(process, data_ptr, count * 4)
    if raw is None:
        desc["sample_read_ok"] = False
        desc["first_f32"] = []
        desc["first_u32"] = []
        return desc
    desc["sample_read_ok"] = True
    desc["first_f32"] = [_f32(raw, off) for off in range(0, len(raw), 4)]
    desc["first_u32"] = [_u32(raw, off) for off in range(0, len(raw), 4)]
    return desc


def _descriptor_sig(desc):
    if not desc or not desc.get("read_ok"):
        return None
    return {
        "width": desc.get("width_0x10"),
        "height": desc.get("height_0x14"),
        "stride": desc.get("stride_0x18"),
        "data_ptr": desc.get("data_ptr_0x20"),
        "first_u16": desc.get("first_u16"),
        "first_f32": desc.get("first_f32"),
        "first_u32": desc.get("first_u32"),
    }


def _sig_equal(left, right):
    left_sig = _descriptor_sig(left)
    right_sig = _descriptor_sig(right)
    if left_sig is None or right_sig is None:
        return None
    return left_sig == right_sig


def _source_object(process, addr):
    data = _read(process, addr, 0x58)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "qwords": [_u64(data, off) for off in range(0, 0x58, 8)],
        "u32": [_u32(data, off) for off in range(0, 0x58, 4)],
        "dim_width_0x30": _u32(data, 0x30),
        "dim_height_0x34": _u32(data, 0x34),
    }


def _vector_summary(process, addr, stride=4):
    qwords = _qwords(process, addr, 3)
    if qwords is None:
        return {"addr": addr, "read_ok": False}
    begin, end, cap = qwords
    byte_size = end - begin if end >= begin else None
    count = byte_size // stride if byte_size is not None and stride else None
    first_f32 = []
    if stride == 4 and begin and byte_size and byte_size > 0:
        raw = _read(process, begin, min(byte_size, 8 * 4))
        if raw is not None:
            first_f32 = [_f32(raw, off) for off in range(0, len(raw), 4)]
    return {
        "addr": addr,
        "read_ok": True,
        "begin": begin,
        "end": end,
        "cap": cap,
        "byte_size": byte_size,
        "stride": stride,
        "count": count,
        "first_f32": first_f32,
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
        "filter_mode_0x70": u32_at(0x70),
        "depth_width_0x2a0": u32_at(0x2A0),
        "depth_height_0x2a4": u32_at(0x2A4),
    }


def _callback_object(process, target, addr):
    qwords = _qwords(process, addr, 4)
    if qwords is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "address_point_0x00": qwords[0],
        "address_point_0x00_va": _ptr_module_va(target, qwords[0]),
        "dest_descriptor_ptr_0x08": qwords[1],
        "source_object_ptr_0x10": qwords[2],
        "qword_0x18": qwords[3],
        "qwords": qwords,
    }


def _new_chain(thread_id, regs, process):
    state = _state()
    chain_id = len(state["chains"])
    stereo = _stereo_object(process, regs["r12"])
    source_object_addr = regs["r12"] + 0xF8 if regs["r12"] else 0
    chain = {
        "chain_id": chain_id,
        "thread_id": thread_id,
        "stereo_index": stereo.get("index_0x8"),
        "stereo_object": stereo,
        "caller_rbp": regs["rbp"],
        "stereo_this_r12": regs["r12"],
        "object_plus_0xf8": source_object_addr,
        "object_plus_0xe0": regs["r12"] + 0xE0 if regs["r12"] else 0,
        "snapshots": {},
        "checks": {},
    }
    state["chains"].append(chain)
    state["active_chain_by_thread"][str(thread_id)] = chain_id
    return chain


def _active_chain(thread_id):
    state = _state()
    chain_id = state["active_chain_by_thread"].get(str(thread_id))
    if chain_id is None:
        return None
    if chain_id >= len(state["chains"]):
        return None
    return state["chains"][chain_id]


def _append_sample(sample):
    _state()["samples"].append(sample)


def _update_checks(chain):
    snaps = chain.get("snapshots", {})
    checks = {}
    branch = snaps.get("branch_to_299c70_source_path", {})
    entry = snaps.get("producer_299c70_entry", {})
    dispatch = snaps.get("producer_299c70_dispatch_call", {})
    after_dispatch = snaps.get("producer_299c70_after_dispatch", {})
    after_return = snaps.get("after_299c70_return", {})
    before_move = snaps.get("before_temp_to_source_move", {})
    after_move = snaps.get("after_temp_to_source_move", {})
    callsite = snaps.get("callsite_267010_from_source_descriptor", {})
    entry_267010 = snaps.get("descriptor_build_267010_entry", {})

    checks["branch_rdx_equals_this_plus_0xf8"] = (
        branch.get("rdx") == chain.get("object_plus_0xf8")
        if branch
        else None
    )
    checks["producer_entry_rsi_equals_this_plus_0xf8"] = (
        entry.get("arg_rsi") == chain.get("object_plus_0xf8")
        if entry
        else None
    )
    checks["producer_entry_rdi_equals_caller_rbp_minus_0xe0"] = (
        entry.get("arg_rdi") == chain.get("caller_rbp", 0) - 0xE0
        if entry
        else None
    )
    checks["producer_source_dims_equal_returned_temp_dims"] = (
        entry.get("source_object", {}).get("dim_width_0x30")
        == after_return.get("temp_descriptor_rbp_minus_0xe0", {}).get("width_0x10")
        and entry.get("source_object", {}).get("dim_height_0x34")
        == after_return.get("temp_descriptor_rbp_minus_0xe0", {}).get("height_0x14")
        if entry and after_return
        else None
    )
    checks["dispatch_callback_dest_equals_arg_rdi"] = (
        dispatch.get("callback", {}).get("dest_descriptor_ptr_0x08")
        == entry.get("arg_rdi")
        if dispatch and entry
        else None
    )
    checks["dispatch_callback_source_equals_arg_rsi"] = (
        dispatch.get("callback", {}).get("source_object_ptr_0x10")
        == entry.get("arg_rsi")
        if dispatch and entry
        else None
    )
    checks["after_dispatch_descriptor_equals_after_return_temp"] = _sig_equal(
        after_dispatch.get("dest_descriptor_r15"),
        after_return.get("temp_descriptor_rbp_minus_0xe0"),
    )
    checks["before_move_source_equals_after_return_temp"] = _sig_equal(
        before_move.get("source_temp_descriptor_rbp_minus_0xe0"),
        after_return.get("temp_descriptor_rbp_minus_0xe0"),
    )
    checks["after_move_dest_equals_before_move_source"] = _sig_equal(
        after_move.get("dest_source_descriptor_rbp_minus_0x80"),
        before_move.get("source_temp_descriptor_rbp_minus_0xe0"),
    )
    checks["callsite_267010_source_equals_after_move_dest"] = _sig_equal(
        callsite.get("source_descriptor_rsi_rbp_minus_0x80"),
        after_move.get("dest_source_descriptor_rbp_minus_0x80"),
    )
    checks["callsite_267010_rdx_equals_this_plus_0xe0"] = (
        callsite.get("lookup_vector_arg_rdx") == chain.get("object_plus_0xe0")
        if callsite
        else None
    )
    checks["entry_267010_source_equals_callsite_source"] = _sig_equal(
        entry_267010.get("source_descriptor_arg_rsi"),
        callsite.get("source_descriptor_rsi_rbp_minus_0x80"),
    )
    checks["entry_267010_lookup_arg_equals_callsite_lookup_arg"] = (
        entry_267010.get("lookup_vector_arg_rdx")
        == callsite.get("lookup_vector_arg_rdx")
        if entry_267010 and callsite
        else None
    )
    values = [value for value in checks.values() if value is not None]
    checks["all_available_checks_pass"] = bool(values) and all(value is True for value in values)
    chain["checks"] = checks


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
    count = state.get("sample_entries", 16)
    sample = {
        "site": name,
        "site_va": site_va,
        "thread_id": thread_id,
        "registers": regs,
        "stack": _stack(thread),
    }

    chain = _active_chain(thread_id)
    if site_va == 0x26E4C6:
        chain = _new_chain(thread_id, regs, process)
        packet = {
            "rdx": regs["rdx"],
            "source_object_from_rdx": _source_object(process, regs["rdx"]),
            "lookup_vector_this_plus_0xe0": _vector_summary(process, chain["object_plus_0xe0"]),
        }
        chain["snapshots"][name] = packet
        sample["chain_id"] = chain["chain_id"]
        sample.update(packet)
    elif chain is None:
        sample["skipped_no_active_chain"] = True
    elif site_va == 0x299C70:
        packet = {
            "arg_rdi": regs["rdi"],
            "arg_rsi": regs["rsi"],
            "dest_descriptor_arg_rdi_pre": _descriptor_u16(process, regs["rdi"], count),
            "source_object": _source_object(process, regs["rsi"]),
        }
        chain["snapshots"][name] = packet
        sample["chain_id"] = chain["chain_id"]
        sample.update(packet)
    elif site_va == 0x299D06:
        packet = {
            "dest_descriptor_r15": _descriptor_u16(process, regs["r15"], count),
            "source_object_rbx": _source_object(process, regs["rbx"]),
            "dispatch_config_rdi": _qwords(process, regs["rdi"], 3),
            "dispatch_tile_rsi": _u32s(process, regs["rsi"], 4),
            "callback": _callback_object(process, target, regs["rdx"]),
        }
        chain["snapshots"][name] = packet
        sample["chain_id"] = chain["chain_id"]
        sample.update(packet)
    elif site_va == 0x299D0B:
        packet = {
            "dest_descriptor_r15": _descriptor_u16(process, regs["r15"], count),
            "source_object_rbx": _source_object(process, regs["rbx"]),
        }
        chain["snapshots"][name] = packet
        sample["chain_id"] = chain["chain_id"]
        sample.update(packet)
    elif site_va == 0x26E4D5:
        packet = {
            "temp_descriptor_rbp_minus_0xe0": _descriptor_u16(process, regs["rbp"] - 0xE0, count),
            "dest_source_descriptor_rbp_minus_0x80_pre_move": _descriptor_u16(process, regs["rbp"] - 0x80, count),
        }
        chain["snapshots"][name] = packet
        sample["chain_id"] = chain["chain_id"]
        sample.update(packet)
    elif site_va == 0x26E4E0:
        packet = {
            "arg_rdi": regs["rdi"],
            "arg_rsi": regs["rsi"],
            "dest_source_descriptor_rbp_minus_0x80_pre_move": _descriptor_u16(process, regs["rdi"], count),
            "source_temp_descriptor_rbp_minus_0xe0": _descriptor_u16(process, regs["rsi"], count),
        }
        chain["snapshots"][name] = packet
        sample["chain_id"] = chain["chain_id"]
        sample.update(packet)
    elif site_va == 0x26E4E5:
        packet = {
            "dest_source_descriptor_rbp_minus_0x80": _descriptor_u16(process, regs["rbp"] - 0x80, count),
            "temp_descriptor_rbp_minus_0xe0_after_move": _descriptor_u16(process, regs["rbp"] - 0xE0, count),
        }
        chain["snapshots"][name] = packet
        sample["chain_id"] = chain["chain_id"]
        sample.update(packet)
    elif site_va == 0x26E633:
        packet = {
            "lookup_vector_arg_rdx": regs["rdx"],
            "lookup_vector": _vector_summary(process, regs["rdx"]),
            "source_descriptor_rsi_rbp_minus_0x80": _descriptor_u16(process, regs["rsi"], count),
        }
        chain["snapshots"][name] = packet
        sample["chain_id"] = chain["chain_id"]
        sample.update(packet)
    elif site_va == 0x267010:
        packet = {
            "dest_descriptor_arg_rdi": _descriptor_f32(process, regs["rdi"], count),
            "source_descriptor_arg_rsi": _descriptor_u16(process, regs["rsi"], count),
            "lookup_vector_arg_rdx": regs["rdx"],
            "lookup_vector": _vector_summary(process, regs["rdx"]),
        }
        chain["snapshots"][name] = packet
        sample["chain_id"] = chain["chain_id"]
        sample.update(packet)
    elif site_va == 0x26E638:
        packet = {
            "built_descriptor_rbp_minus_0x1d0": _descriptor_f32(process, regs["rbp"] - 0x1D0, count),
        }
        chain["snapshots"][name] = packet
        _update_checks(chain)
        sample["chain_id"] = chain["chain_id"]
        sample.update(packet)

    if chain is not None:
        _update_checks(chain)
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
        bp.SetScriptCallbackFunction("source_index_producer_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_SOURCE_INDEX_PRODUCER_ATTACHED", ids)


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
    print("L16_SOURCE_INDEX_PRODUCER_DRIVE_STEPS", steps)


def _summary():
    chains = _state().get("chains", [])
    return {
        "chain_count": len(chains),
        "stereo_indices": [chain.get("stereo_index") for chain in chains],
        "all_chains_pass_available_checks": bool(chains)
        and all(chain.get("checks", {}).get("all_available_checks_pass") is True for chain in chains),
        "checks_by_chain": [
            {
                "chain_id": chain.get("chain_id"),
                "stereo_index": chain.get("stereo_index"),
                "checks": chain.get("checks", {}),
            }
            for chain in chains
        ],
    }


def payload(debugger):
    packet = dict(_state())
    packet["process"] = _process_packet(debugger)
    packet["breakpoint_hit_counts"] = _breakpoint_hit_counts(debugger)
    packet["summary"] = _summary()
    packet.pop("active_chain_by_thread", None)
    return packet


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_SOURCE_INDEX_PRODUCER_WROTE", path)


def report(debugger):
    print("L16_SOURCE_INDEX_PRODUCER_BEGIN")
    print(json.dumps(payload(debugger), indent=2, sort_keys=True))
    print("L16_SOURCE_INDEX_PRODUCER_END")
