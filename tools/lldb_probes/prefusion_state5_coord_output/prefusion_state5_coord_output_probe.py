import builtins
import json
import math
import os
import struct


ENTRY = 0x2457C0
STATE5_STORE_PATH = 0x24593B
RETURN_OK = 0x2459D0
FEATURE_SIZE_MISMATCH = 0x245963
TOTAL_FEATURES_SIZE_MISMATCH = 0x2459DF
RECORD_STRIDE = 0x2C
SENTINEL_PAIR = (-1.0, -1.0)


def reset(
    label="",
    sample_limit=256,
    max_output_pairs=65536,
    step_cap=300000,
    store_hit_hard_cap=64,
):
    builtins.l16_prefusion_state5_coord_output = {
        "label": label,
        "sample_limit": sample_limit,
        "max_output_pairs": max_output_pairs,
        "step_cap": step_cap,
        "store_hit_hard_cap": store_hit_hard_cap,
        "breakpoint_ids": {},
        "next_call_id": 1,
        "active_calls_by_thread": {},
        "counts": {
            "entry_hits": 0,
            "return_ok_hits": 0,
            "state5_store_path_hits": 0,
            "state5_store_path_target2_hits": 0,
            "feature_size_mismatch_hits": 0,
            "total_features_size_mismatch_hits": 0,
            "store_hit_hard_cap_disabled": 0,
        },
        "store_by_level": {},
        "store_by_target": {},
        "call_entries": [],
        "state5_store_path_samples": [],
        "return_summaries": [],
        "mismatch_samples": [],
        "errors": [],
        "drive_steps": 0,
        "drive_hit_step_cap": False,
    }


def _state():
    if not hasattr(builtins, "l16_prefusion_state5_coord_output"):
        reset()
    return builtins.l16_prefusion_state5_coord_output


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


def _append_limited(key, packet):
    state = _state()
    if len(state[key]) < state["sample_limit"]:
        state[key].append(packet)


def _inc_dict_int(dictionary, key):
    text_key = str(key)
    dictionary[text_key] = dictionary.get(text_key, 0) + 1


def _vector_header(process, vector_addr, elem_size):
    data = _read(process, vector_addr, 24)
    if data is None:
        return {"addr": vector_addr, "read_ok": False}
    begin = _u64(data, 0)
    end = _u64(data, 8)
    cap = _u64(data, 16)
    byte_len = end - begin if end >= begin else None
    cap_bytes = cap - begin if cap >= begin else None
    return {
        "addr": vector_addr,
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


def _record(process, record_addr):
    data = _read(process, record_addr, RECORD_STRIDE)
    if data is None:
        return {"record_addr": record_addr, "read_ok": False}
    return {
        "record_addr": record_addr,
        "read_ok": True,
        "index_or_id_0x00": _i32(data, 0x00),
        "coord_f32_0x04": _f32(data, 0x04),
        "coord_f32_0x08": _f32(data, 0x08),
        "coord_i32_0x14": _i32(data, 0x14),
        "coord_i32_0x18": _i32(data, 0x18),
        "state_0x24": _i32(data, 0x24),
        "target_0x28": _i32(data, 0x28),
        "record_hex": data.hex(),
    }


def _pair(process, pair_addr):
    data = _read(process, pair_addr, 8)
    if data is None:
        return {"addr": pair_addr, "read_ok": False}
    x = _f32(data, 0)
    y = _f32(data, 4)
    return {
        "addr": pair_addr,
        "read_ok": True,
        "x": x,
        "y": y,
        "is_sentinel_neg1_neg1": x == SENTINEL_PAIR[0] and y == SENTINEL_PAIR[1],
        "both_finite": math.isfinite(x) and math.isfinite(y),
        "hex": data.hex(),
    }


def _output_vector_summary(process, state_addr):
    header = _vector_header(process, state_addr + 0x1E8, 8)
    summary = {
        "state_addr": state_addr,
        "vector": header,
        "pairs_scanned": 0,
        "pairs_truncated": False,
        "sentinel_neg1_neg1": 0,
        "finite_non_sentinel": 0,
        "nonfinite": 0,
        "non_sentinel_samples": [],
    }
    count = header.get("elem_count")
    begin = header.get("begin")
    if not header.get("read_ok") or count is None or not begin:
        return summary
    limited = min(count, _state()["max_output_pairs"])
    data = _read(process, begin, limited * 8) if limited else b""
    if data is None:
        summary["read_ok"] = False
        return summary
    summary["read_ok"] = True
    summary["pairs_scanned"] = limited
    summary["pairs_truncated"] = count > limited
    for index in range(limited):
        off = index * 8
        x = _f32(data, off)
        y = _f32(data, off + 4)
        if x == SENTINEL_PAIR[0] and y == SENTINEL_PAIR[1]:
            summary["sentinel_neg1_neg1"] += 1
        elif math.isfinite(x) and math.isfinite(y):
            summary["finite_non_sentinel"] += 1
            if len(summary["non_sentinel_samples"]) < 32:
                summary["non_sentinel_samples"].append(
                    {
                        "index": index,
                        "addr": begin + off,
                        "x": x,
                        "y": y,
                        "hex": data[off : off + 8].hex(),
                    }
                )
        else:
            summary["nonfinite"] += 1
    return summary


def _current_call(thread_id):
    calls = _state()["active_calls_by_thread"].get(str(thread_id), [])
    return calls[-1] if calls else None


def _disable_breakpoint(debugger, name):
    bp_id = _state()["breakpoint_ids"].get(name)
    if not bp_id:
        return
    bp = debugger.GetSelectedTarget().FindBreakpointByID(int(bp_id))
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def install_breakpoints(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    sites = (
        (ENTRY, "entry_2457c0"),
        (STATE5_STORE_PATH, "state5_store_path_24593b"),
        (RETURN_OK, "return_ok_2459d0"),
        (FEATURE_SIZE_MISMATCH, "feature_size_mismatch_245963"),
        (TOTAL_FEATURES_SIZE_MISMATCH, "total_features_size_mismatch_2459df"),
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
        bp.SetScriptCallbackFunction("prefusion_state5_coord_output_probe.hit")
        state["breakpoint_ids"][name] = bp.GetID()
    print("L16_PREFUSION_STATE5_COORD_OUTPUT_INSTALLED", json.dumps(state["breakpoint_ids"], sort_keys=True))


def _entry(frame, thread_id, regs):
    state = _state()
    process = frame.GetThread().GetProcess()
    call_id = state["next_call_id"]
    state["next_call_id"] += 1
    state["counts"]["entry_hits"] += 1
    packet = {
        "call_id": call_id,
        "thread_id": thread_id,
        "state_addr": regs["rdi"],
        "entry_output_vector": _vector_header(process, regs["rdi"] + 0x1E8, 8),
        "stack": _stack(frame.GetThread(), 8),
    }
    state["active_calls_by_thread"].setdefault(str(thread_id), []).append(packet)
    _append_limited("call_entries", packet)


def _state5_store_path(frame, thread_id, regs):
    state = _state()
    process = frame.GetThread().GetProcess()
    output_addr = regs["rdx"] + regs["r12"] * 8
    record = _record(process, regs["rax"])
    pair = _pair(process, output_addr)
    target = record.get("target_0x28")
    level = regs["rbx"]
    call = _current_call(thread_id)
    state["counts"]["state5_store_path_hits"] += 1
    if target == 2:
        state["counts"]["state5_store_path_target2_hits"] += 1
    _inc_dict_int(state["store_by_level"], level)
    _inc_dict_int(state["store_by_target"], target)
    packet = {
        "call_id": call.get("call_id") if call else None,
        "thread_id": thread_id,
        "state_addr": regs["r14"],
        "level_rbx": level,
        "output_index_r12": regs["r12"],
        "output_addr": output_addr,
        "record": record,
        "output_pair_before_store": pair,
        "stack": _stack(frame.GetThread(), 8),
    }
    _append_limited("state5_store_path_samples", packet)
    if state["counts"]["state5_store_path_hits"] >= state["store_hit_hard_cap"]:
        state["counts"]["store_hit_hard_cap_disabled"] = 1
        _disable_breakpoint(frame.GetThread().GetProcess().GetTarget().GetDebugger(), "state5_store_path_24593b")


def _return_ok(frame, thread_id, regs):
    state = _state()
    process = frame.GetThread().GetProcess()
    state["counts"]["return_ok_hits"] += 1
    calls = state["active_calls_by_thread"].get(str(thread_id), [])
    call = calls.pop() if calls else None
    packet = {
        "call_id": call.get("call_id") if call else None,
        "thread_id": thread_id,
        "state_addr": regs["r14"],
        "return_output_vector": _output_vector_summary(process, regs["r14"]),
        "stack": _stack(frame.GetThread(), 8),
    }
    _append_limited("return_summaries", packet)


def _mismatch(frame, thread_id, regs, pc_va):
    state = _state()
    if pc_va == FEATURE_SIZE_MISMATCH:
        state["counts"]["feature_size_mismatch_hits"] += 1
        site = "feature_size_mismatch_245963"
    else:
        state["counts"]["total_features_size_mismatch_hits"] += 1
        site = "total_features_size_mismatch_2459df"
    _append_limited(
        "mismatch_samples",
        {
            "site": site,
            "thread_id": thread_id,
            "state_addr_r14": regs["r14"],
            "registers": regs,
            "stack": _stack(frame.GetThread(), 8),
        },
    )


def hit(frame, bp_loc, _dict):
    target = frame.GetThread().GetProcess().GetTarget()
    pc_va = _module_va(target, frame.GetPC())
    regs = _registers(frame)
    thread_id = frame.GetThread().GetThreadID()
    if pc_va == ENTRY:
        _entry(frame, thread_id, regs)
    elif pc_va == STATE5_STORE_PATH:
        _state5_store_path(frame, thread_id, regs)
    elif pc_va == RETURN_OK:
        _return_ok(frame, thread_id, regs)
    elif pc_va in (FEATURE_SIZE_MISMATCH, TOTAL_FEATURES_SIZE_MISMATCH):
        _mismatch(frame, thread_id, regs, pc_va)
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
    print("L16_PREFUSION_STATE5_COORD_OUTPUT_DRIVE_STEPS", steps)


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
