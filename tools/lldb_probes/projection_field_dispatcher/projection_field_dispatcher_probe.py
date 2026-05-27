import builtins
import json
import struct


SITES = {
    0x3F6170: "dispatcher_entry_3f6170",
    0x3F61B8: "dispatcher_class_compare_3f61b8",
    0x3F61CA: "same_branch_call_3f61ca",
    0x3F61E1: "cross_branch_call_3f61e1",
    0x3F6200: "same_entry_3f6200",
    0x3F6940: "cross_entry_3f6940",
}


def reset(label="", sample_limit=320):
    builtins.l16_projection_field_dispatcher = {
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
    if not hasattr(builtins, "l16_projection_field_dispatcher"):
        reset()
    return builtins.l16_projection_field_dispatcher


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


def _key_bucket(key):
    state = _state()
    key_text = str(key)
    if key_text not in state["by_key"]:
        state["by_key"][key_text] = {
            "key": key,
            "entry": 0,
            "class_compare": 0,
            "same_branch_call": 0,
            "cross_branch_call": 0,
            "same_entry": 0,
            "cross_entry": 0,
            "key_classes": [],
            "state_classes": [],
            "entry_callers": {},
            "state_ptrs": [],
        }
    return state["by_key"][key_text]


def _append_unique(bucket, field, value):
    if value is None:
        return
    if value not in bucket[field]:
        bucket[field].append(value)


def _append_sample(sample):
    state = _state()
    if len(state["samples"]) < state["sample_limit"]:
        state["samples"].append(sample)


def _record_caller(bucket, stack):
    if len(stack) < 2:
        return
    caller = stack[1].get("libcp_va")
    caller_text = "None" if caller is None else hex(caller)
    bucket["entry_callers"][caller_text] = bucket["entry_callers"].get(caller_text, 0) + 1


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
    key = None
    if site_va == 0x3F6170:
        key = _i32(regs["rdx"])
        bucket = _key_bucket(key)
        bucket["entry"] += 1
        _append_unique(bucket, "state_ptrs", regs["rsi"])
        _record_caller(bucket, stack)
        event.update({"key": key, "state": regs["rsi"], "out": regs["rdi"], "caller": stack[1].get("libcp_va") if len(stack) > 1 else None})
    elif site_va == 0x3F61B8:
        key = _i32(regs["r13"])
        bucket = _key_bucket(key)
        bucket["class_compare"] += 1
        _append_unique(bucket, "key_classes", _i32(regs["r12"]))
        _append_unique(bucket, "state_classes", _i32_at(process, regs["rbp"] - 0x38))
        event.update({"key": key, "key_class": _i32(regs["r12"]), "state_class": _i32_at(process, regs["rbp"] - 0x38)})
    elif site_va == 0x3F61CA:
        key = _i32(regs["r13"])
        bucket = _key_bucket(key)
        bucket["same_branch_call"] += 1
        event.update({"key": key})
    elif site_va == 0x3F61E1:
        key = _i32(regs["r13"])
        bucket = _key_bucket(key)
        bucket["cross_branch_call"] += 1
        event.update({"key": key})
    elif site_va == 0x3F6200:
        key = _i32(regs["rdx"])
        bucket = _key_bucket(key)
        bucket["same_entry"] += 1
        event.update({"key": key, "state": regs["rsi"], "out": regs["rdi"]})
    elif site_va == 0x3F6940:
        key = _i32(regs["rdx"])
        bucket = _key_bucket(key)
        bucket["cross_entry"] += 1
        event.update({"key": key, "state": regs["rsi"], "out": regs["rdi"]})

    _append_sample({**event, "registers": regs, "stack": stack})
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    count = target.GetNumBreakpoints()
    if count < len(SITES):
        _state()["errors"].append("expected at least 6 breakpoints")
        print("L16_PROJECTION_FIELD_DISPATCHER_ATTACH_ERROR expected at least 6 breakpoints")
        return
    ids = {}
    start = count - len(SITES)
    for index, (site_va, name) in enumerate(SITES.items(), start=start):
        bp = target.GetBreakpointAtIndex(index)
        bp.SetScriptCallbackFunction("projection_field_dispatcher_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_PROJECTION_FIELD_DISPATCHER_ATTACHED", ids)


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
                "entry": bucket["entry"],
                "class_compare": bucket["class_compare"],
                "same_branch_call": bucket["same_branch_call"],
                "cross_branch_call": bucket["cross_branch_call"],
                "same_entry": bucket["same_entry"],
                "cross_entry": bucket["cross_entry"],
                "key_classes": sorted(bucket["key_classes"]),
                "state_classes": sorted(bucket["state_classes"]),
                "entry_callers": dict(sorted(bucket["entry_callers"].items())),
                "state_ptr_count": len(bucket["state_ptrs"]),
            }
        )
    return rows


def drive_until_exit_or_step_cap(debugger, max_steps=24000):
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
    print("L16_PROJECTION_FIELD_DISPATCHER_DRIVE_STEPS", steps)


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
    print("L16_PROJECTION_FIELD_DISPATCHER_WROTE", path)
