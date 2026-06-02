import builtins
import json
import struct


SITES = {
    0x2484E4: "family_a_gate_before_2484e4",
    0x2484E9: "family_a_gate_after_2484e9",
    0x2488B9: "family_b_gate_before_2488b9",
    0x2488BE: "family_b_gate_after_2488be",
    0x241FD0: "selector_entry_241fd0",
    0x2416D0: "promoter_entry_2416d0",
    0x241828: "promoter_direct_state5_store_241828",
    0x2422A6: "selector_ge3_state5_store_2422a6",
    0x242306: "selector_state4_state5_store_242306",
}

FAMILY_BY_SITE = {
    0x2484E4: "a",
    0x2484E9: "a",
    0x2488B9: "b",
    0x2488BE: "b",
}

STORE_SITES = {0x241828, 0x2422A6, 0x242306}
CAP_SITES = STORE_SITES | {0x241FD0, 0x2416D0}


def reset(label="", sample_limit=320, hit_cap=512, max_records=512):
    builtins.l16_prefusion_record_state_gate_histogram = {
        "label": label,
        "sample_limit": sample_limit,
        "hit_cap": hit_cap,
        "max_records": max_records,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
        "breakpoint_ids": {},
        "counts": {name: 0 for name in SITES.values()},
        "disabled_after_cap": [],
        "known_vectors": {},
        "active_by_thread_family": {},
        "gate_before": [],
        "gate_after": [],
        "selector_entries": [],
        "promoter_entries": [],
        "state_stores": [],
        "samples": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_prefusion_record_state_gate_histogram"):
        reset()
    return builtins.l16_prefusion_record_state_gate_histogram


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _i32(value):
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


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


def _read_u32(process, addr):
    data = _read(process, addr, 4)
    return struct.unpack_from("<I", data, 0)[0] if data is not None else None


def _vector_header(process, addr, stride=0x2C):
    data = _read(process, addr, 24)
    if data is None:
        return {"addr": addr, "read_ok": False, "stride": stride}
    begin = _u64(data, 0)
    end = _u64(data, 8)
    cap = _u64(data, 16)
    byte_len = end - begin if end >= begin else None
    cap_bytes = cap - begin if cap >= begin else None
    return {
        "addr": addr,
        "read_ok": True,
        "begin": begin,
        "end": end,
        "cap": cap,
        "stride": stride,
        "byte_len": byte_len,
        "record_count": byte_len // stride if byte_len is not None else None,
        "byte_len_mod_stride": byte_len % stride if byte_len is not None else None,
        "cap_bytes": cap_bytes,
        "cap_records": cap_bytes // stride if cap_bytes is not None else None,
    }


def _record_histogram(process, vector_addr):
    header = _vector_header(process, vector_addr, 0x2C)
    if not header.get("read_ok"):
        return {"vector": header, "read_ok": False}
    count = header.get("record_count") or 0
    limited_count = min(count, _state()["max_records"])
    data = _read(process, header["begin"], limited_count * 0x2C) if limited_count else b""
    if data is None:
        return {"vector": header, "read_ok": False}
    state_counts = {}
    target_counts = {}
    pair_counts = {}
    first_records = []
    for idx in range(limited_count):
        base = idx * 0x2C
        state_val = struct.unpack_from("<i", data, base + 0x24)[0]
        target_val = struct.unpack_from("<i", data, base + 0x28)[0]
        state_counts[str(state_val)] = state_counts.get(str(state_val), 0) + 1
        target_counts[str(target_val)] = target_counts.get(str(target_val), 0) + 1
        pair_key = f"{state_val}:{target_val}"
        pair_counts[pair_key] = pair_counts.get(pair_key, 0) + 1
        if len(first_records) < 16:
            first_records.append(
                {
                    "index": idx,
                    "state_0x24": state_val,
                    "target_0x28": target_val,
                    "coord_i32_0x14": struct.unpack_from("<i", data, base + 0x14)[0],
                    "coord_i32_0x18": struct.unpack_from("<i", data, base + 0x18)[0],
                }
            )
    return {
        "vector": header,
        "read_ok": True,
        "records_scanned": limited_count,
        "records_truncated": count > limited_count,
        "state_counts_0x24": state_counts,
        "target_counts_0x28": target_counts,
        "state_target_counts": pair_counts,
        "first_records": first_records,
    }


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


def _append_sample(sample):
    state = _state()
    if len(state["samples"]) < state["sample_limit"]:
        state["samples"].append(sample)


def _disable_breakpoint(debugger, name):
    bp_id = _state()["breakpoint_ids"].get(name)
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id) if bp_id else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def _maybe_disable_after_cap(target, site_va, name):
    state = _state()
    if site_va not in CAP_SITES:
        return
    if state["counts"][name] < state["hit_cap"]:
        return
    debugger = target.GetDebugger()
    _disable_breakpoint(debugger, name)
    if name not in state["disabled_after_cap"]:
        state["disabled_after_cap"].append(name)


def _vector_key(vector_addr):
    return f"0x{vector_addr:x}" if vector_addr else None


def _remember_vector(thread_id, family, vector_addr, site, hist):
    if not vector_addr:
        return
    record = {
        "thread_id": thread_id,
        "family": family,
        "vector_addr": vector_addr,
        "site": site,
        "record_count": hist.get("vector", {}).get("record_count"),
        "begin": hist.get("vector", {}).get("begin"),
        "end": hist.get("vector", {}).get("end"),
    }
    _state()["known_vectors"][_vector_key(vector_addr)] = record
    _state()["active_by_thread_family"][f"{thread_id}:{family}"] = record


def _active_vector(thread_id, family):
    return _state()["active_by_thread_family"].get(f"{thread_id}:{family}")


def _match_vector(vector_addr):
    return _state()["known_vectors"].get(_vector_key(vector_addr))


def _match_record_addr(record_base):
    for info in _state()["known_vectors"].values():
        begin = info.get("begin")
        end = info.get("end")
        if begin is not None and end is not None and begin <= record_base < end:
            return {
                "family": info.get("family"),
                "vector_addr": info.get("vector_addr"),
                "record_index": (record_base - begin) // 0x2C,
                "record_offset": record_base - begin,
            }
    return None


def _gate_before(process, site_va, regs, thread_id, stack):
    family = FAMILY_BY_SITE[site_va]
    vector_addr = regs["rsi"]
    hist = _record_histogram(process, vector_addr)
    record = {
        "site": SITES[site_va],
        "family": family,
        "thread_id": thread_id,
        "gate_arg_rdi": regs["rdi"],
        "gate_arg_rsi_output_vec": vector_addr,
        "histogram": hist,
        "caller_stack": stack[:4],
    }
    _remember_vector(thread_id, family, vector_addr, SITES[site_va], hist)
    _state()["gate_before"].append(record)
    return record


def _gate_after(process, site_va, regs, thread_id, stack):
    family = FAMILY_BY_SITE[site_va]
    active = _active_vector(thread_id, family)
    vector_addr = active.get("vector_addr") if active else regs["r13"]
    hist = _record_histogram(process, vector_addr)
    record = {
        "site": SITES[site_va],
        "family": family,
        "thread_id": thread_id,
        "vector_addr": vector_addr,
        "matched_active_vector": bool(active and active.get("vector_addr") == vector_addr),
        "histogram": hist,
        "caller_stack": stack[:4],
    }
    _state()["gate_after"].append(record)
    return record


def _selector_entry(process, regs, thread_id, stack):
    vector_addr = regs["rdx"]
    match = _match_vector(vector_addr)
    record = {
        "site": "selector_entry_241fd0",
        "thread_id": thread_id,
        "state_arg_rdi": regs["rdi"],
        "arg_rsi": regs["rsi"],
        "vector_arg_rdx": vector_addr,
        "mode_ecx": _i32(regs["rcx"]),
        "arg_r8d": _i32(regs["r8"]),
        "matched_known_vector": match,
        "histogram": _record_histogram(process, vector_addr) if match else None,
        "caller_stack": stack[:5],
    }
    if match:
        _state()["selector_entries"].append(record)
    return record


def _promoter_entry(process, regs, thread_id, stack):
    vector_addr = regs["rdx"]
    match = _match_vector(vector_addr)
    record = {
        "site": "promoter_entry_2416d0",
        "thread_id": thread_id,
        "arg_rsi": regs["rsi"],
        "vector_arg_rdx": vector_addr,
        "mode_ecx": _i32(regs["rcx"]),
        "arg_r8d": _i32(regs["r8"]),
        "target_r9d": _i32(regs["r9"]),
        "matched_known_vector": match,
        "histogram": _record_histogram(process, vector_addr) if match else None,
        "caller_stack": stack[:6],
    }
    if match:
        _state()["promoter_entries"].append(record)
    return record


def _state_store(process, site_va, regs, thread_id, stack):
    if site_va == 0x241828:
        record_base = regs["rax"] + regs["rsi"]
    else:
        record_base = regs["rax"]
    state_addr = record_base + 0x24
    match = _match_record_addr(record_base)
    record = {
        "site": SITES[site_va],
        "thread_id": thread_id,
        "record_base": record_base,
        "state_addr": state_addr,
        "before_state_0x24": _i32(_read_u32(process, state_addr) or 0) if match else None,
        "before_target_0x28": _i32(_read_u32(process, state_addr + 4) or 0) if match else None,
        "matched_known_vector_record": match,
        "caller_stack": stack[:5],
    }
    if match:
        _state()["state_stores"].append(record)
    return record


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
    stack = _stack(thread)
    thread_id = thread.GetThreadID()
    sample = {
        "site": name,
        "site_va": site_va,
        "thread_id": thread_id,
        "registers": regs,
        "stack": stack,
    }

    if site_va in (0x2484E4, 0x2488B9):
        sample["gate"] = _gate_before(process, site_va, regs, thread_id, stack)
    elif site_va in (0x2484E9, 0x2488BE):
        sample["gate"] = _gate_after(process, site_va, regs, thread_id, stack)
    elif site_va == 0x241FD0:
        sample["selector"] = _selector_entry(process, regs, thread_id, stack)
    elif site_va == 0x2416D0:
        sample["promoter"] = _promoter_entry(process, regs, thread_id, stack)
    elif site_va in STORE_SITES:
        sample["state_store"] = _state_store(process, site_va, regs, thread_id, stack)

    _append_sample(sample)
    _maybe_disable_after_cap(target, site_va, name)
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    ids = {}
    for index in range(target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(index)
        if not bp or not bp.IsValid() or bp.GetNumLocations() < 1:
            continue
        site_va = bp.GetLocationAtIndex(0).GetAddress().GetFileAddress()
        name = SITES.get(site_va)
        if name is None:
            continue
        bp.SetScriptCallbackFunction("prefusion_record_state_gate_histogram_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_PREFUSION_RECORD_STATE_GATE_HISTOGRAM_ATTACHED", json.dumps(ids, sort_keys=True))


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


def drive_until_exit_or_step_cap(debugger, max_steps=60000):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process.IsValid() and process.GetState() == lldb.eStateStopped and steps < max_steps:
        steps += 1
        process.Continue()
    state["drive_steps"] += steps
    if process.IsValid() and process.GetState() == lldb.eStateStopped and steps >= max_steps:
        state["drive_hit_step_cap"] = True
    print("L16_PREFUSION_RECORD_STATE_GATE_HISTOGRAM_DRIVE_STEPS", steps)


def write_report(debugger, path):
    state = _state()
    state["breakpoint_hit_counts"] = _breakpoint_hit_counts(debugger)
    state["process"] = _process_packet(debugger)
    with open(path, "w") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
    print("L16_PREFUSION_RECORD_STATE_GATE_HISTOGRAM_REPORT", path)
