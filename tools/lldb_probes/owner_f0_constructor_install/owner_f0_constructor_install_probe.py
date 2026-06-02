import builtins
import json
import struct


SITES = {
    0x3EA7D0: "constructor_entry_3ea7d0",
    0x3EA8FC: "visible_payload_lookup_callsite_3ea8fc",
    0x3EA980: "owner_f0_callable_install_callsite_3ea980",
    0x3EA985: "owner_f0_callable_install_return_3ea985",
    0x3EC960: "owner_f0_sink_entry_3ec960",
    0x3ECAC3: "owner_f0_sink_after_3e5720_3ecac3",
}


def reset(label="", sample_limit=192, hit_cap=96):
    builtins.l16_owner_f0_constructor_install = {
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
    if not hasattr(builtins, "l16_owner_f0_constructor_install"):
        reset()
    return builtins.l16_owner_f0_constructor_install


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


def _read_qword(process, addr):
    data = _read(process, addr, 8)
    return _u64(data) if data is not None else None


def _qwords(process, addr, count):
    data = _read(process, addr, count * 8)
    if data is None:
        return None
    return [_u64(data, off) for off in range(0, count * 8, 8)]


def _descriptor(process, addr):
    data = _read(process, addr, 0x30)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "qwords": [_u64(data, off) for off in range(0, 0x30, 8)],
        "u32": [_u32(data, off) for off in range(0, 0x30, 4)],
        "width_0x10": _u32(data, 0x10),
        "height_0x14": _u32(data, 0x14),
        "stride_0x18": _u32(data, 0x18),
        "data_ptr_0x20": _u64(data, 0x20),
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


def _owner_from_sink_arg(process, sink_arg):
    owner = _read_qword(process, sink_arg) if sink_arg else None
    return {
        "sink_arg": sink_arg,
        "owner": owner,
        "owner_f0_descriptor": _descriptor(process, owner + 0xF0) if owner else None,
        "sink_arg_qwords": _qwords(process, sink_arg, 4) if sink_arg else None,
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

    if site_va == 0x3EA7D0:
        sample["constructor_object"] = regs["rdi"]
        sample["constructor_object_qwords"] = _qwords(process, regs["rdi"], 12)
    elif site_va == 0x3EA980:
        sample["target_object"] = regs["rdi"]
        sample["stack_callable"] = regs["rsi"]
        sample["stack_callable_qwords"] = _qwords(process, regs["rsi"], 4)
        sample["target_before_qwords_0x50"] = _qwords(process, regs["rdi"] + 0x50, 6)
    elif site_va == 0x3EA985:
        owner = regs["r14"]
        sample["target_object"] = owner
        sample["target_after_qwords_0x50"] = _qwords(process, owner + 0x50, 6)
        sample["active_callable_ptr_0x70"] = _read_qword(process, owner + 0x70)
    elif site_va in (0x3EC960, 0x3ECAC3):
        sample["sink_context"] = _owner_from_sink_arg(process, regs["rsi"] if site_va == 0x3EC960 else regs["r14"])

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
        bp.SetScriptCallbackFunction("owner_f0_constructor_install_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_OWNER_F0_CONSTRUCTOR_INSTALL_ATTACHED", json.dumps(ids, sort_keys=True))


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
    print("L16_OWNER_F0_CONSTRUCTOR_INSTALL_DRIVE_STEPS", steps)


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
    print("L16_OWNER_F0_CONSTRUCTOR_INSTALL_WROTE", path)
