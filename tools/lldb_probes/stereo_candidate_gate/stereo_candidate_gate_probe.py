import builtins
import json
import struct


SITES = {
    0x3F2C40: "constructor_entry_3f2c40",
    0x3F30A4: "loop_key_loaded_3f30a4",
    0x3F30BA: "object_flag_compare_3f30ba",
    0x3F30C0: "active_flag_pass_3f30c0",
    0x3F30CA: "first_getter_call_3f30ca",
    0x3F3104: "second_getter_call_3f3104",
}


def reset(label="", sample_limit=320):
    builtins.l16_stereo_candidate_gate = {
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
    if not hasattr(builtins, "l16_stereo_candidate_gate"):
        reset()
    return builtins.l16_stereo_candidate_gate


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


def _stack(thread, max_frames=8):
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
            "object_flag_compare": 0,
            "active_flag_zero": 0,
            "active_flag_nonzero": 0,
            "active_flag_pass": 0,
            "first_getter_call": 0,
            "second_getter_call": 0,
            "active_flags": [],
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


def _key_from_loop(process, regs):
    key = _i32_at(process, regs["r12"])
    if key is not None:
        return key
    return _i32(regs["rdx"])


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

    if site_va == 0x3F2C40:
        event.update({"self": regs["rdi"], "arg_rsi": regs["rsi"], "caller": stack[1].get("libcp_va") if len(stack) > 1 else None})
    else:
        key = _key_from_loop(process, regs)
        bucket = _bucket(key)
        event["key"] = key
        event["key_ptr"] = regs["r12"]

        if site_va == 0x3F30A4:
            bucket["loop_key_loaded"] += 1
            event["key_from_ptr"] = _i32_at(process, regs["r12"])
        elif site_va == 0x3F30BA:
            flag = _u8_at(process, regs["rdi"] + 0x30)
            bucket["object_flag_compare"] += 1
            if flag:
                bucket["active_flag_nonzero"] += 1
            else:
                bucket["active_flag_zero"] += 1
            _append_unique(bucket, "active_flags", flag)
            _append_unique(bucket, "object_ptrs", regs["rdi"])
            event.update({"object_ptr": regs["rdi"], "object_flag_byte": flag})
        elif site_va == 0x3F30C0:
            bucket["active_flag_pass"] += 1
        elif site_va == 0x3F30CA:
            bucket["first_getter_call"] += 1
            event["object_ptr"] = regs["rdi"]
        elif site_va == 0x3F3104:
            bucket["second_getter_call"] += 1
            event["object_ptr"] = regs["rdi"]

    _append_sample({**event, "registers": regs, "stack": stack})
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    count = target.GetNumBreakpoints()
    if count < len(SITES):
        _state()["errors"].append("expected at least 6 breakpoints")
        print("L16_STEREO_CANDIDATE_GATE_ATTACH_ERROR expected at least 6 breakpoints")
        return
    ids = {}
    start = count - len(SITES)
    for index, (site_va, name) in enumerate(SITES.items(), start=start):
        bp = target.GetBreakpointAtIndex(index)
        bp.SetScriptCallbackFunction("stereo_candidate_gate_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_STEREO_CANDIDATE_GATE_ATTACHED", ids)


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
                "object_flag_compare": bucket["object_flag_compare"],
                "active_flag_zero": bucket["active_flag_zero"],
                "active_flag_nonzero": bucket["active_flag_nonzero"],
                "active_flag_pass": bucket["active_flag_pass"],
                "first_getter_call": bucket["first_getter_call"],
                "second_getter_call": bucket["second_getter_call"],
                "active_flags": sorted(bucket["active_flags"]),
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
    print("L16_STEREO_CANDIDATE_GATE_DRIVE_STEPS", steps)


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
    print("L16_STEREO_CANDIDATE_GATE_WROTE", path)
