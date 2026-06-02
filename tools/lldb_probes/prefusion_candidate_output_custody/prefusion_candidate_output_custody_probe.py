import builtins
import json
import struct


SITES = {
    0x2481A0: "family_a_wrapper_entry_2481a0",
    0x2484A6: "family_a_context_ready_2484a6",
    0x24C320: "family_a_scorer_entry_24c320",
    0x2484BD: "family_a_after_executor_2484bd",
    0x2484E4: "family_a_gate_call_2484e4",
    0x248580: "family_b_wrapper_entry_248580",
    0x24887B: "family_b_context_ready_24887b",
    0x24D610: "family_b_scorer_entry_24d610",
    0x248892: "family_b_after_executor_248892",
    0x2488B9: "family_b_gate_call_2488b9",
    0x2439B0: "shared_gate_entry_2439b0",
}

FAMILY_BY_SITE = {
    0x2481A0: "a",
    0x2484A6: "a",
    0x24C320: "a",
    0x2484BD: "a",
    0x2484E4: "a",
    0x248580: "b",
    0x24887B: "b",
    0x24D610: "b",
    0x248892: "b",
    0x2488B9: "b",
}

SCORER_ENTRY_SITES = {0x24C320, 0x24D610}
CAP_SITES = {0x24C320, 0x24D610, 0x2439B0}


def reset(label="", sample_limit=640, hit_cap=160):
    builtins.l16_prefusion_candidate_output_custody = {
        "label": label,
        "sample_limit": sample_limit,
        "hit_cap": hit_cap,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
        "breakpoint_ids": {},
        "counts": {name: 0 for name in SITES.values()},
        "disabled_after_cap": [],
        "contexts": {},
        "active_by_thread_family": {},
        "known_output_vectors": {},
        "gate_calls": [],
        "shared_gate_matches": [],
        "scorer_entries": {"a": [], "b": []},
        "samples": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_prefusion_candidate_output_custody"):
        reset()
    return builtins.l16_prefusion_candidate_output_custody


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


def _u32(data, off=0):
    return struct.unpack_from("<I", data, off)[0]


def _read_qword(process, addr):
    data = _read(process, addr, 8)
    return _u64(data) if data is not None else None


def _qwords(process, addr, count):
    data = _read(process, addr, count * 8)
    if data is None:
        return None
    return [_u64(data, off) for off in range(0, count * 8, 8)]


def _rect_i32(process, addr):
    data = _read(process, addr, 16)
    if data is None:
        return None
    return [struct.unpack_from("<i", data, off)[0] for off in range(0, 16, 4)]


def _vector(process, addr, stride):
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


def _stack(thread, max_frames=12):
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
                "rbp": _u(frame, "rbp"),
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


def _family_context_layout(process, family, context):
    qwords = _qwords(process, context, 22)
    if qwords is None:
        return {"context": context, "read_ok": False, "family": family}
    if family == "a":
        input_vec = qwords[1]
        bounds_rect = qwords[2]
        output_vec = qwords[3]
    else:
        input_vec = qwords[1]
        bounds_rect = qwords[3]
        output_vec = qwords[5]
    return {
        "context": context,
        "read_ok": True,
        "family": family,
        "qwords": qwords,
        "state_ptr_0x00": qwords[0],
        "input_candidate_vec_ptr_0x08": input_vec,
        "bounds_rect_ptr": bounds_rect,
        "bounds_rect_i32": _rect_i32(process, bounds_rect),
        "output_vec_ptr": output_vec,
        "input_candidate_vec_0x24": _vector(process, input_vec, 0x24),
        "output_vec_0x2c": _vector(process, output_vec, 0x2C),
    }


def _remember_context(thread_id, family, record):
    state = _state()
    key = f"{thread_id}:{family}"
    state["active_by_thread_family"][key] = record
    context_key = f"0x{record['context']:x}"
    state["contexts"][context_key] = record
    output_vec = record.get("output_vec")
    if output_vec:
        out_key = f"0x{output_vec:x}"
        state["known_output_vectors"][out_key] = {
            "family": family,
            "context": record["context"],
            "created_site": record["site"],
            "thread_id": thread_id,
        }


def _active_context(thread_id, family):
    return _state()["active_by_thread_family"].get(f"{thread_id}:{family}")


def _match_output_vec(output_vec):
    if not output_vec:
        return None
    return _state()["known_output_vectors"].get(f"0x{output_vec:x}")


def _context_ready(process, site_va, regs, thread_id):
    family = FAMILY_BY_SITE[site_va]
    obj = regs["rax"]
    context = obj + 8 if obj else 0
    output_vec = regs["r13"]
    record = {
        "site": SITES[site_va],
        "family": family,
        "thread_id": thread_id,
        "object": obj,
        "context": context,
        "object_vtable": _read_qword(process, obj),
        "object_qwords": _qwords(process, obj, 24),
        "output_vec": output_vec,
        "gate_state_arg_r14": regs["r14"],
        "output_vec_before_executor": _vector(process, output_vec, 0x2C),
        "context_layout": _family_context_layout(process, family, context),
    }
    _remember_context(thread_id, family, record)
    return record


def _after_executor(process, site_va, regs, thread_id):
    family = FAMILY_BY_SITE[site_va]
    obj = _read_qword(process, regs["rbp"] - 0x40)
    context = obj + 8 if obj else 0
    output_vec = regs["r13"]
    active = _active_context(thread_id, family)
    record = {
        "site": SITES[site_va],
        "family": family,
        "thread_id": thread_id,
        "object_from_stack": obj,
        "context": context,
        "output_vec": output_vec,
        "matches_active_output_vec": active.get("output_vec") == output_vec if active else None,
        "matches_active_context": active.get("context") == context if active else None,
        "output_vec_after_executor": _vector(process, output_vec, 0x2C),
        "context_layout": _family_context_layout(process, family, context),
    }
    return record


def _gate_call(process, site_va, regs, thread_id, stack):
    family = FAMILY_BY_SITE[site_va]
    output_vec = regs["rsi"]
    active = _active_context(thread_id, family)
    record = {
        "site": SITES[site_va],
        "family": family,
        "thread_id": thread_id,
        "gate_arg_rdi": regs["rdi"],
        "gate_arg_rsi_output_vec": output_vec,
        "matches_active_output_vec": active.get("output_vec") == output_vec if active else None,
        "matches_active_gate_state_arg": active.get("gate_state_arg_r14") == regs["rdi"] if active else None,
        "output_vec_at_gate_call": _vector(process, output_vec, 0x2C),
        "caller_stack": stack[:4],
    }
    _state()["gate_calls"].append(record)
    return record


def _shared_gate_entry(process, regs, thread_id, stack):
    output_vec = regs["rsi"]
    match = _match_output_vec(output_vec)
    record = {
        "site": "shared_gate_entry_2439b0",
        "thread_id": thread_id,
        "gate_arg_rdi": regs["rdi"],
        "gate_arg_rsi_output_vec": output_vec,
        "matched_known_output_vec": match,
        "output_vec_at_shared_gate_entry": _vector(process, output_vec, 0x2C),
        "caller_stack": stack[:5],
    }
    if match:
        _state()["shared_gate_matches"].append(record)
    return record


def _scorer_entry(process, site_va, regs, thread_id):
    family = FAMILY_BY_SITE[site_va]
    context = regs["rdi"]
    layout = _family_context_layout(process, family, context)
    output_vec = layout.get("output_vec_ptr")
    active = _active_context(thread_id, family)
    record = {
        "site": SITES[site_va],
        "family": family,
        "thread_id": thread_id,
        "context": context,
        "candidate_index_esi": _i32(regs["rsi"]),
        "matches_active_context": active.get("context") == context if active else None,
        "matches_active_output_vec": active.get("output_vec") == output_vec if active else None,
        "context_layout": layout,
    }
    entries = _state()["scorer_entries"][family]
    if len(entries) < 32:
        entries.append(record)
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

    if site_va in (0x2484A6, 0x24887B):
        sample["custody"] = _context_ready(process, site_va, regs, thread_id)
    elif site_va in SCORER_ENTRY_SITES:
        sample["custody"] = _scorer_entry(process, site_va, regs, thread_id)
    elif site_va in (0x2484BD, 0x248892):
        sample["custody"] = _after_executor(process, site_va, regs, thread_id)
    elif site_va in (0x2484E4, 0x2488B9):
        sample["custody"] = _gate_call(process, site_va, regs, thread_id, stack)
    elif site_va == 0x2439B0:
        sample["custody"] = _shared_gate_entry(process, regs, thread_id, stack)

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
        bp.SetScriptCallbackFunction("prefusion_candidate_output_custody_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_PREFUSION_CANDIDATE_OUTPUT_CUSTODY_ATTACHED", json.dumps(ids, sort_keys=True))


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
    print("L16_PREFUSION_CANDIDATE_OUTPUT_CUSTODY_DRIVE_STEPS", steps)


def payload(debugger):
    return {
        "process": _process_packet(debugger),
        "breakpoint_hit_counts": _breakpoint_hit_counts(debugger),
        **_state(),
    }


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_PREFUSION_CANDIDATE_OUTPUT_CUSTODY_WROTE", path)
