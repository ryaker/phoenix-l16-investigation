import builtins
import json
import struct


SITES = {
    0x3E0330: "constructor_entry_3e0330",
    0x3E03E3: "loop_key_loaded_3e03e3",
    0x3E0406: "object_flag_loaded_3e0406",
    0x3E0410: "active_flag_test_3e0410",
    0x3E0418: "active_flag_pass_3e0418",
    0x3E0450: "class_compare_3e0450",
    0x3E0456: "cross_class_pass_3e0456",
    0x3E05F5: "dispatcher_call_3e05f5",
    0x3E05FA: "dispatcher_return_3e05fa",
}


def reset(label="", sample_limit=320):
    builtins.l16_direct_payload_candidate_gate = {
        "label": label,
        "sample_limit": sample_limit,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
        "breakpoint_ids": {},
        "counts": {name: 0 for name in SITES.values()},
        "by_key": {},
        "samples": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_direct_payload_candidate_gate"):
        reset()
    return builtins.l16_direct_payload_candidate_gate


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


def _i32_at(process, addr):
    data = _read(process, addr, 4)
    if data is None:
        return None
    return struct.unpack_from("<i", data, 0)[0]


def _u8_at(process, addr):
    data = _read(process, addr, 1)
    if data is None:
        return None
    return data[0]


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
                "rbp": _u(frame, "rbp"),
            }
        )
    return frames


def _bucket(key):
    state = _state()
    text = str(key)
    if text not in state["by_key"]:
        state["by_key"][text] = {
            "key": key,
            "loop_key_loaded": 0,
            "object_flag_loaded": 0,
            "active_flag_test": 0,
            "active_flag_zero": 0,
            "active_flag_nonzero": 0,
            "active_flag_pass": 0,
            "class_compare": 0,
            "same_class_skip": 0,
            "cross_class_pass": 0,
            "dispatcher_call": 0,
            "dispatcher_return": 0,
            "active_flags": [],
            "key_classes": [],
            "state_classes": [],
            "object_ptrs": [],
        }
    return state["by_key"][text]


def _append_unique(bucket, field, value):
    if value is None:
        return
    if value not in bucket[field]:
        bucket[field].append(value)


def _append_sample(sample):
    state = _state()
    if len(state["samples"]) < state["sample_limit"]:
        state["samples"].append(sample)


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

    regs = _registers(frame)
    stack = _stack(thread)
    state["counts"][name] = state["counts"].get(name, 0) + 1
    event = {"site": name, "site_va": site_va}

    if site_va == 0x3E0330:
        event.update({"self": regs["rdi"], "arg_rsi": regs["rsi"], "caller": stack[1].get("libcp_va") if len(stack) > 1 else None})
    else:
        key = _i32(regs["r13"])
        bucket = _bucket(key)
        event["key"] = key
        if site_va == 0x3E03E3:
            bucket["loop_key_loaded"] += 1
            event["key_ptr"] = regs["r14"]
            event["key_from_ptr"] = _i32_at(process, regs["r14"])
        elif site_va == 0x3E0406:
            flag = regs["rbx"] & 0xFF
            object_ptr = regs["rax"]
            bucket["object_flag_loaded"] += 1
            _append_unique(bucket, "active_flags", flag)
            _append_unique(bucket, "object_ptrs", object_ptr)
            event.update({"active_flag_bl": flag, "object_ptr": object_ptr, "object_flag_byte": _u8_at(process, object_ptr + 0x30)})
        elif site_va == 0x3E0410:
            flag = regs["rbx"] & 0xFF
            bucket["active_flag_test"] += 1
            if flag:
                bucket["active_flag_nonzero"] += 1
            else:
                bucket["active_flag_zero"] += 1
            _append_unique(bucket, "active_flags", flag)
            event.update({"active_flag_bl": flag})
        elif site_va == 0x3E0418:
            bucket["active_flag_pass"] += 1
        elif site_va == 0x3E0450:
            key_class = _i32(regs["rbx"])
            state_class = _i32_at(process, regs["rbp"] - 0xA8)
            bucket["class_compare"] += 1
            if state_class is not None and key_class == state_class:
                bucket["same_class_skip"] += 1
            _append_unique(bucket, "key_classes", key_class)
            _append_unique(bucket, "state_classes", state_class)
            event.update({"key_class": key_class, "state_class": state_class})
        elif site_va == 0x3E0456:
            bucket["cross_class_pass"] += 1
        elif site_va == 0x3E05F5:
            bucket["dispatcher_call"] += 1
        elif site_va == 0x3E05FA:
            bucket["dispatcher_return"] += 1

    _append_sample({**event, "registers": regs, "stack": stack})
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    count = target.GetNumBreakpoints()
    if count < len(SITES):
        _state()["errors"].append("expected at least 8 breakpoints")
        print("L16_DIRECT_PAYLOAD_CANDIDATE_GATE_ATTACH_ERROR expected at least 8 breakpoints")
        return
    ids = {}
    start = count - len(SITES)
    for index, (site_va, name) in enumerate(SITES.items(), start=start):
        bp = target.GetBreakpointAtIndex(index)
        bp.SetScriptCallbackFunction("direct_payload_candidate_gate_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_DIRECT_PAYLOAD_CANDIDATE_GATE_ATTACHED", ids)


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


def _summary():
    rows = []
    for key_text, bucket in sorted(_state()["by_key"].items(), key=lambda item: int(item[0])):
        rows.append(
            {
                "key": bucket["key"],
                "loop_key_loaded": bucket["loop_key_loaded"],
                "object_flag_loaded": bucket["object_flag_loaded"],
                "active_flag_test": bucket["active_flag_test"],
                "active_flag_zero": bucket["active_flag_zero"],
                "active_flag_nonzero": bucket["active_flag_nonzero"],
                "active_flag_pass": bucket["active_flag_pass"],
                "class_compare": bucket["class_compare"],
                "same_class_skip": bucket["same_class_skip"],
                "cross_class_pass": bucket["cross_class_pass"],
                "dispatcher_call": bucket["dispatcher_call"],
                "dispatcher_return": bucket["dispatcher_return"],
                "active_flags": sorted(bucket["active_flags"]),
                "key_classes": sorted(bucket["key_classes"]),
                "state_classes": sorted(bucket["state_classes"]),
                "object_ptr_count": len(bucket["object_ptrs"]),
            }
        )
    return rows


def drive_until_exit_or_step_cap(debugger, max_steps=30000):
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
    print("L16_DIRECT_PAYLOAD_CANDIDATE_GATE_DRIVE_STEPS", steps)


def payload(debugger):
    return {
        "process": _process_packet(debugger),
        "breakpoint_hit_counts": _breakpoint_hit_counts(debugger),
        "summary": _summary(),
        **_state(),
    }


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_DIRECT_PAYLOAD_CANDIDATE_GATE_WROTE", path)
