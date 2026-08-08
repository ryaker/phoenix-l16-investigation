import builtins
import json
import os
import struct


ENTRY = 0x25D090
D2A0_RETURN = 0x25D243
GEOM_RETURN = 0x25D251
ACTIVE_CLEAR_AFTER = 0x25D25F
RETURN_SITE = 0x25D278
RECORD_STRIDE = 0x2C


def reset(
    label="",
    sample_limit=96,
    max_records=768,
    max_level_entries=8,
    pair_sample_limit=6,
    step_cap=500000,
):
    builtins.l16_prefusion_block_geometry_effect = {
        "label": label,
        "sample_limit": sample_limit,
        "max_records": max_records,
        "max_level_entries": max_level_entries,
        "pair_sample_limit": pair_sample_limit,
        "step_cap": step_cap,
        "breakpoint_ids": {},
        "next_call_id": 1,
        "active_calls_by_thread": {},
        "counts": {
            "entry_hits": 0,
            "active_entry_hits": 0,
            "inactive_entry_hits": 0,
            "d2a0_return_hits": 0,
            "d2a0_success": 0,
            "d2a0_failure": 0,
            "geom_return_hits": 0,
            "geom_accept": 0,
            "geom_reject": 0,
            "active_clear_hits": 0,
            "return_hits": 0,
            "return_true": 0,
            "return_false": 0,
        },
        "by_level": {},
        "by_target": {},
        "entry_samples": [],
        "d2a0_return_samples": [],
        "geom_return_samples": [],
        "active_clear_samples": [],
        "return_samples": [],
        "errors": [],
        "drive_steps": 0,
        "drive_hit_step_cap": False,
    }


def _state():
    if not hasattr(builtins, "l16_prefusion_block_geometry_effect"):
        reset()
    return builtins.l16_prefusion_block_geometry_effect


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


def _i32(data, off=0):
    return struct.unpack_from("<i", data, off)[0]


def _u32(data, off=0):
    return struct.unpack_from("<I", data, off)[0]


def _f32(data, off=0):
    return struct.unpack_from("<f", data, off)[0]


def _libcp_base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                return base
    return None


def _module_va(target, pc):
    addr = target.ResolveLoadAddress(pc)
    if addr and addr.IsValid():
        module = addr.GetModule()
        if module and str(module.GetFileSpec().GetFilename()) != "libcp.dylib":
            return None
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
            "rsi",
            "rdi",
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
            "rip",
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


def _inc_dict(dictionary, key):
    text_key = str(key)
    dictionary[text_key] = dictionary.get(text_key, 0) + 1


def _append_limited(key, packet):
    state = _state()
    if len(state[key]) < state["sample_limit"]:
        state[key].append(packet)


def _vector_header_from_addr(process, addr, elem_size):
    data = _read(process, addr, 24)
    if data is None:
        return {"addr": addr, "read_ok": False}
    begin = _u64(data, 0)
    end = _u64(data, 8)
    cap = _u64(data, 16)
    return _vector_header_from_values(addr, begin, end, cap, elem_size)


def _vector_header_from_values(addr, begin, end, cap, elem_size):
    byte_len = end - begin if end >= begin else None
    cap_bytes = cap - begin if cap >= begin else None
    return {
        "addr": addr,
        "read_ok": True,
        "begin": begin,
        "end": end,
        "cap": cap,
        "byte_len": byte_len,
        "elem_size": elem_size,
        "elem_count": byte_len // elem_size if byte_len is not None else None,
        "byte_len_mod_elem": byte_len % elem_size if byte_len is not None else None,
        "cap_bytes": cap_bytes,
        "cap_elems": cap_bytes // elem_size if cap_bytes is not None else None,
    }


def _pair_samples(process, begin, count, elem_size=8):
    out = []
    limit = min(count or 0, _state()["pair_sample_limit"])
    data = _read(process, begin, limit * elem_size) if begin and limit else b""
    if data is None:
        return out
    for index in range(limit):
        off = index * elem_size
        out.append(
            {
                "index": index,
                "addr": begin + off,
                "i32_0": _i32(data, off),
                "i32_1": _i32(data, off + 4),
                "hex": data[off : off + elem_size].hex(),
            }
        )
    return out


def _vector_family(process, block_addr, family_off):
    root = _read(process, block_addr + family_off, 24)
    if root is None:
        return {"family_off": family_off, "read_ok": False, "levels": []}
    begin = _u64(root, 0)
    end = _u64(root, 8)
    cap = _u64(root, 16)
    root_header = _vector_header_from_values(block_addr + family_off, begin, end, cap, 24)
    count = root_header.get("elem_count") or 0
    limited = min(count, _state()["max_level_entries"])
    data = _read(process, begin, limited * 24) if begin and limited else b""
    if data is None:
        return {"family_off": family_off, "root": root_header, "read_ok": False, "levels": []}
    levels = []
    for index in range(limited):
        off = index * 24
        level_begin = _u64(data, off)
        level_end = _u64(data, off + 8)
        level_cap = _u64(data, off + 16)
        header = _vector_header_from_values(begin + off, level_begin, level_end, level_cap, 8)
        levels.append(
            {
                "level": index,
                "vector": header,
                "pair_samples": _pair_samples(process, level_begin, header.get("elem_count") or 0),
            }
        )
    return {
        "family_off": family_off,
        "root": root_header,
        "read_ok": True,
        "levels": levels,
        "levels_truncated": count > limited,
    }


def _descriptor(process, block_addr):
    data = _read(process, block_addr + 0x8, 0x24)
    if data is None:
        return {"addr": block_addr + 0x8, "read_ok": False}
    return {
        "addr": block_addr + 0x8,
        "read_ok": True,
        "f32": [_f32(data, i * 4) for i in range(9)],
        "i32": [_i32(data, i * 4) for i in range(9)],
        "hex": data.hex(),
    }


def _block_summary(process, block_addr):
    data = _read(process, block_addr, 0x60)
    if data is None:
        return {"block_addr": block_addr, "read_ok": False}
    return {
        "block_addr": block_addr,
        "read_ok": True,
        "target_0x00": _i32(data, 0x00),
        "active_0x04": data[0x04],
        "raw_0x00_0x60": data.hex(),
        "descriptor_0x08": _descriptor(process, block_addr),
        "pair_family_0x30": _vector_family(process, block_addr, 0x30),
        "pair_family_0x48": _vector_family(process, block_addr, 0x48),
    }


def _record_vector_summary(process, vector_addr, block_target):
    header = _vector_header_from_addr(process, vector_addr, RECORD_STRIDE)
    if not header.get("read_ok"):
        return {"vector": header, "read_ok": False, "records": []}
    count = header.get("elem_count") or 0
    limited = min(count, _state()["max_records"])
    data = _read(process, header["begin"], limited * RECORD_STRIDE) if header.get("begin") and limited else b""
    if data is None:
        return {"vector": header, "read_ok": False, "records": []}
    counts = {}
    match_state5_target = 0
    match_samples = []
    for index in range(limited):
        off = index * RECORD_STRIDE
        state_val = _i32(data, off + 0x24)
        target_val = _i32(data, off + 0x28)
        key = f"{state_val}:{target_val}"
        counts[key] = counts.get(key, 0) + 1
        if state_val == 5 and target_val == block_target:
            match_state5_target += 1
            if len(match_samples) < 16:
                match_samples.append(
                    {
                        "index": index,
                        "record_addr": header["begin"] + off,
                        "source_index_0x00": _i32(data, off + 0x00),
                        "pair_i32_0x14": _i32(data, off + 0x14),
                        "pair_i32_0x18": _i32(data, off + 0x18),
                        "state_0x24": state_val,
                        "target_0x28": target_val,
                        "record_hex": data[off : off + RECORD_STRIDE].hex(),
                    }
                )
    return {
        "vector": header,
        "read_ok": True,
        "records_scanned": limited,
        "records_truncated": count > limited,
        "state_target_counts": counts,
        "matching_state5_target_count": match_state5_target,
        "matching_state5_target_samples": match_samples,
    }


def _current_call(thread_id):
    calls = _state()["active_calls_by_thread"].get(str(thread_id), [])
    return calls[-1] if calls else None


def install_breakpoints(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    sites = (
        (ENTRY, "entry_25d090"),
        (D2A0_RETURN, "d2a0_return_25d243"),
        (GEOM_RETURN, "geom_return_25d251"),
        (ACTIVE_CLEAR_AFTER, "active_clear_after_25d25f"),
        (RETURN_SITE, "return_25d278"),
    )
    for site, name in sites:
        before = target.GetNumBreakpoints()
        debugger.HandleCommand(f"breakpoint set --shlib libcp.dylib --address 0x{site:x}")
        after = target.GetNumBreakpoints()
        if after <= before:
            state["errors"].append({"site": f"0x{site:x}", "error": "breakpoint not created"})
            continue
        bp = target.GetBreakpointAtIndex(after - 1)
        if not bp or not bp.IsValid():
            state["errors"].append({"site": f"0x{site:x}", "error": "invalid breakpoint"})
            continue
        bp.SetScriptCallbackFunction("block_geometry_effect_probe.hit")
        state["breakpoint_ids"][name] = bp.GetID()
    print("L16_PREFUSION_BLOCK_GEOMETRY_EFFECT_INSTALLED", json.dumps(state["breakpoint_ids"], sort_keys=True))


def _entry(frame, thread_id, regs):
    state = _state()
    process = frame.GetThread().GetProcess()
    call_id = state["next_call_id"]
    state["next_call_id"] += 1
    block = _block_summary(process, regs["rdi"])
    target = block.get("target_0x00")
    active = block.get("active_0x04")
    state["counts"]["entry_hits"] += 1
    if active:
        state["counts"]["active_entry_hits"] += 1
    else:
        state["counts"]["inactive_entry_hits"] += 1
    _inc_dict(state["by_level"], regs["rsi"] & 0xFFFFFFFF)
    _inc_dict(state["by_target"], target)
    packet = {
        "call_id": call_id,
        "thread_id": thread_id,
        "level_esi": regs["rsi"] & 0xFFFFFFFF,
        "flag_r8d": regs["r8"] & 0xFFFFFFFF,
        "block_addr": regs["rdi"],
        "record_vector_addr_rcx": regs["rcx"],
        "source_table_arg_rdx": regs["rdx"],
        "block_entry": block,
        "record_vector_entry": _record_vector_summary(process, regs["rcx"], target),
        "stack": _stack(frame.GetThread(), 12),
    }
    state["active_calls_by_thread"].setdefault(str(thread_id), []).append(packet)
    _append_limited("entry_samples", packet)


def _d2a0_return(frame, thread_id, regs):
    state = _state()
    process = frame.GetThread().GetProcess()
    call = _current_call(thread_id)
    result = regs["rax"] & 0xFF
    state["counts"]["d2a0_return_hits"] += 1
    if result:
        state["counts"]["d2a0_success"] += 1
    else:
        state["counts"]["d2a0_failure"] += 1
    packet = {
        "call_id": call.get("call_id") if call else None,
        "thread_id": thread_id,
        "d2a0_al": result,
        "block_addr": regs["r12"],
        "block_after_d2a0": _block_summary(process, regs["r12"]),
        "stack": _stack(frame.GetThread(), 12),
    }
    _append_limited("d2a0_return_samples", packet)


def _geom_return(frame, thread_id, regs):
    state = _state()
    process = frame.GetThread().GetProcess()
    call = _current_call(thread_id)
    result = regs["rax"] & 0xFF
    state["counts"]["geom_return_hits"] += 1
    if result:
        state["counts"]["geom_accept"] += 1
    else:
        state["counts"]["geom_reject"] += 1
    packet = {
        "call_id": call.get("call_id") if call else None,
        "thread_id": thread_id,
        "geom_al": result,
        "block_addr": regs["r12"],
        "block_after_geom": _block_summary(process, regs["r12"]),
        "stack": _stack(frame.GetThread(), 12),
    }
    _append_limited("geom_return_samples", packet)


def _active_clear(frame, thread_id, regs):
    state = _state()
    process = frame.GetThread().GetProcess()
    call = _current_call(thread_id)
    state["counts"]["active_clear_hits"] += 1
    packet = {
        "call_id": call.get("call_id") if call else None,
        "thread_id": thread_id,
        "block_addr": regs["r12"],
        "block_after_clear": _block_summary(process, regs["r12"]),
        "stack": _stack(frame.GetThread(), 12),
    }
    _append_limited("active_clear_samples", packet)


def _return(frame, thread_id, regs):
    state = _state()
    process = frame.GetThread().GetProcess()
    calls = state["active_calls_by_thread"].get(str(thread_id), [])
    call = calls.pop() if calls else None
    result = regs["rax"] & 0xFF
    state["counts"]["return_hits"] += 1
    if result:
        state["counts"]["return_true"] += 1
    else:
        state["counts"]["return_false"] += 1
    packet = {
        "call_id": call.get("call_id") if call else None,
        "thread_id": thread_id,
        "return_al": result,
        "block_addr": call.get("block_addr") if call else regs["r12"],
        "block_return": _block_summary(process, call.get("block_addr") if call else regs["r12"]),
        "stack": _stack(frame.GetThread(), 12),
    }
    _append_limited("return_samples", packet)


def hit(frame, bp_loc, _dict):
    target = frame.GetThread().GetProcess().GetTarget()
    pc_va = _module_va(target, frame.GetPC())
    regs = _registers(frame)
    thread_id = frame.GetThread().GetThreadID()
    if pc_va == ENTRY:
        _entry(frame, thread_id, regs)
    elif pc_va == D2A0_RETURN:
        _d2a0_return(frame, thread_id, regs)
    elif pc_va == GEOM_RETURN:
        _geom_return(frame, thread_id, regs)
    elif pc_va == ACTIVE_CLEAR_AFTER:
        _active_clear(frame, thread_id, regs)
    elif pc_va == RETURN_SITE:
        _return(frame, thread_id, regs)
    else:
        _state()["errors"].append({"error": "unexpected breakpoint", "pc_va": pc_va})
    return False


def drive_until_exit_or_step_cap(debugger):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process.IsValid() and process.GetState() == lldb.eStateStopped and steps < state["step_cap"]:
        steps += 1
        process.Continue()
    state["drive_steps"] = steps
    state["drive_hit_step_cap"] = (
        process.IsValid()
        and process.GetState() == lldb.eStateStopped
        and steps >= state["step_cap"]
    )
    print("L16_PREFUSION_BLOCK_GEOMETRY_EFFECT_DRIVE_STEPS", steps)


def payload(debugger):
    state = dict(_state())
    process = debugger.GetSelectedTarget().GetProcess()
    if process and process.IsValid():
        state["process_state"] = str(process.GetState())
        state["process_exit_status"] = process.GetExitStatus()
    return state


def report_to_file(debugger, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("WROTE", path)
