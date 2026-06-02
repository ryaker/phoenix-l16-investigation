import builtins
import json
import struct


SITES = {
    0x42C140: "debug_entry_42c140",
    0x42CB35: "debug_source_lookup_callsite_42cb35",
    0x42CB5D: "debug_fieldpack_callsite_42cb5d",
    0x42CB9C: "debug_source_lookup_callsite_42cb9c",
    0x42CBC2: "debug_map_provider_callsite_42cbc2",
    0x42CC5A: "debug_callback_executor_callsite_42cc5a",
    0x4300F0: "debug_callback_a_operator_4300f0",
    0x430240: "debug_callback_b_operator_430240",
    0x3E05F5: "live_fieldpack_control_3e05f5",
    0x3EB72D: "live_map_provider_control_3eb72d",
}


def reset(label="", sample_limit=160, hit_cap=96):
    builtins.l16_higherwarpdebug_renderdebugview = {
        "label": label,
        "sample_limit": sample_limit,
        "hit_cap": hit_cap,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
        "breakpoint_ids": {},
        "counts": {name: 0 for name in SITES.values()},
        "disabled_after_cap": [],
        "samples": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_higherwarpdebug_renderdebugview"):
        reset()
    return builtins.l16_higherwarpdebug_renderdebugview


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


def _i32(data, off=0):
    return struct.unpack_from("<i", data, off)[0]


def _read_qwords(process, addr, count):
    data = _read(process, addr, count * 8)
    if data is None:
        return None
    return [_u64(data, off) for off in range(0, count * 8, 8)]


def _read_i32(process, addr):
    data = _read(process, addr, 4)
    return _i32(data) if data is not None else None


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


def _callsite_args(process, regs):
    return {
        "rdi_qwords": _read_qwords(process, regs["rdi"], 6),
        "rsi_qwords": _read_qwords(process, regs["rsi"], 6),
        "rcx_qwords": _read_qwords(process, regs["rcx"], 6),
        "r8_qwords": _read_qwords(process, regs["r8"], 6),
        "edx_i32": regs["rdx"] & 0xFFFFFFFF,
        "r8d_i32": regs["r8"] & 0xFFFFFFFF,
    }


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

    if site_va in (0x42CB5D, 0x42CBC2, 0x3E05F5, 0x3EB72D):
        sample["callsite_args"] = _callsite_args(process, regs)
    elif site_va == 0x42C140:
        sample["debug_object_qwords"] = _read_qwords(process, regs["rdi"], 8)
        sample["debug_object_mode_0x10"] = _read_i32(process, regs["rdi"] + 0x10)
    elif site_va in (0x4300F0, 0x430240):
        sample["function_object_qwords"] = _read_qwords(process, regs["rdi"], 6)

    _append_sample(sample)

    if state["counts"][name] >= state["hit_cap"]:
        _disable_breakpoint(target.GetDebugger(), name)
        if name not in state["disabled_after_cap"]:
            state["disabled_after_cap"].append(name)
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
        bp.SetScriptCallbackFunction("higherwarpdebug_renderdebugview_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_HIGHERWARPDEBUG_RENDERDEBUGVIEW_ATTACHED", json.dumps(ids, sort_keys=True))


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
    print("L16_HIGHERWARPDEBUG_RENDERDEBUGVIEW_DRIVE_STEPS", steps)


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
    print("L16_HIGHERWARPDEBUG_RENDERDEBUGVIEW_WROTE", path)
