import builtins
import json
import struct


SITE_GATE = 0x3E4B09
BRANCH_SITES = {
    0x3E3279: "branch_0x3e3279_to_31af30",
    0x3E34E2: "branch_0x3e34e2_to_31acf0",
    0x3E3653: "branch_0x3e3653_to_31acf0",
}
VIRTUAL_SITES = {
    0x33F3E8: "virtual_0x33f3e8_in_33f180",
    0x33F94F: "virtual_0x33f94f_in_33f480",
    0x33FFD4: "virtual_0x33ffd4_in_33fb30",
}


def reset(label="", site_cap=512, sample_limit=16):
    builtins.l16_src1_virtual_census = {
        "label": label,
        "site_cap": site_cap,
        "sample_limit": sample_limit,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
        "gate_hits": 0,
        "lower_breakpoints_enabled": False,
        "breakpoint_ids": {},
        "branch_counts": {name: 0 for name in BRANCH_SITES.values()},
        "virtual_counts": {name: 0 for name in VIRTUAL_SITES.values()},
        "disabled_after_cap": [],
        "target_counts": {},
        "samples": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_src1_virtual_census"):
        reset()
    return builtins.l16_src1_virtual_census


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


def _i32s(data):
    return list(struct.unpack("<" + "i" * (len(data) // 4), data))


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


def _read_qword(process, addr):
    data = _read(process, addr, 8)
    return _u64(data) if data is not None else None


def _site_vector_packet(site_va, regs, process):
    if site_va == 0x33F3E8:
        begin = regs["r10"]
        end = _read_qword(process, regs["rbp"] - 0xB8)
        index = regs["rbx"]
    elif site_va == 0x33F94F:
        begin = regs["r9"]
        end = regs["r15"]
        index = regs["r12"]
    elif site_va == 0x33FFD4:
        begin = regs["r9"]
        end = regs["r13"]
        index = regs["r15"]
    else:
        return None
    count = None
    if begin and end and end >= begin:
        count = (end - begin) // 8
    return {
        "begin": begin,
        "end": end,
        "count_qwords": count,
        "index": index,
    }


def _callable_packet(target, process, callable_addr):
    vtable = _read_qword(process, callable_addr)
    slot = _read_qword(process, vtable + 0x30) if vtable else None
    return {
        "callable": callable_addr,
        "vtable": vtable,
        "vtable_libcp_va": _module_va(target, vtable) if vtable else None,
        "slot_0x30": slot,
        "slot_0x30_libcp_va": _module_va(target, slot) if slot else None,
    }


def _record_packet(process, record_addr):
    data = _read(process, record_addr, 0x40)
    if data is None:
        return {"addr": record_addr, "error": "failed to read record"}
    return {
        "addr": record_addr,
        "first_16_i32": _i32s(data),
    }


def _site_name(site_va):
    if site_va == SITE_GATE:
        return "gate_0x3e4b09"
    if site_va in BRANCH_SITES:
        return BRANCH_SITES[site_va]
    return VIRTUAL_SITES.get(site_va, hex(site_va))


def _enable_lower_breakpoints(debugger):
    state = _state()
    if state["lower_breakpoints_enabled"]:
        return
    target = debugger.GetSelectedTarget()
    for name, bp_id in state["breakpoint_ids"].items():
        if name == "gate_0x3e4b09":
            continue
        bp = target.FindBreakpointByID(bp_id)
        if bp and bp.IsValid():
            bp.SetEnabled(True)
    state["lower_breakpoints_enabled"] = True


def _disable_breakpoint(debugger, name):
    target = debugger.GetSelectedTarget()
    bp_id = _state()["breakpoint_ids"].get(name)
    bp = target.FindBreakpointByID(bp_id) if bp_id is not None else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def gate(frame, bp_loc, internal_dict):
    state = _state()
    state["gate_hits"] += 1
    debugger = frame.GetThread().GetProcess().GetTarget().GetDebugger()
    _enable_lower_breakpoints(debugger)
    _disable_breakpoint(debugger, "gate_0x3e4b09")
    return False


def branch(frame, bp_loc, internal_dict):
    state = _state()
    site_va = _module_va(frame.GetThread().GetProcess().GetTarget(), frame.GetPC())
    name = _site_name(site_va)
    state["branch_counts"][name] = state["branch_counts"].get(name, 0) + 1
    if state["branch_counts"][name] >= state["site_cap"]:
        _disable_breakpoint(frame.GetThread().GetProcess().GetTarget().GetDebugger(), name)
        if name not in state["disabled_after_cap"]:
            state["disabled_after_cap"].append(name)
    return False


def virtual(frame, bp_loc, internal_dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    site_va = _module_va(target, frame.GetPC())
    name = _site_name(site_va)
    state["virtual_counts"][name] = state["virtual_counts"].get(name, 0) + 1

    regs = _registers(frame)
    callable_packet = _callable_packet(target, process, regs["rdi"])
    key = (
        name,
        callable_packet.get("vtable_libcp_va"),
        callable_packet.get("slot_0x30_libcp_va"),
    )
    key_s = "|".join(str(part) for part in key)
    state["target_counts"][key_s] = state["target_counts"].get(key_s, 0) + 1

    if len(state["samples"]) < state["sample_limit"]:
        sample = {
            "site": name,
            "site_va": site_va,
            "registers": regs,
            "callable": callable_packet,
            "vector": _site_vector_packet(site_va, regs, process),
            "record": _record_packet(process, regs["rsi"]),
            "stack": _stack(thread),
        }
        state["samples"].append(sample)

    if state["virtual_counts"][name] >= state["site_cap"]:
        _disable_breakpoint(target.GetDebugger(), name)
        if name not in state["disabled_after_cap"]:
            state["disabled_after_cap"].append(name)
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    count = target.GetNumBreakpoints()
    if count < 7:
        _state()["errors"].append("expected at least 7 breakpoints")
        print("L16_SRC1_VIRTUAL_CENSUS_ATTACH_ERROR expected at least 7 breakpoints")
        return
    order = [
        ("gate_0x3e4b09", gate),
        ("branch_0x3e3279_to_31af30", branch),
        ("branch_0x3e34e2_to_31acf0", branch),
        ("branch_0x3e3653_to_31acf0", branch),
        ("virtual_0x33f3e8_in_33f180", virtual),
        ("virtual_0x33f94f_in_33f480", virtual),
        ("virtual_0x33ffd4_in_33fb30", virtual),
    ]
    ids = {}
    start = count - len(order)
    for index, (name, callback) in enumerate(order, start=start):
        bp = target.GetBreakpointAtIndex(index)
        bp.SetScriptCallbackFunction(
            f"src1_virtual_target_census_probe.{callback.__name__}"
        )
        if name != "gate_0x3e4b09":
            bp.SetEnabled(False)
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_SRC1_VIRTUAL_CENSUS_ATTACHED", ids)


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


def drive_until_exit_or_step_cap(debugger, max_steps=12000):
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
    print("L16_SRC1_VIRTUAL_CENSUS_DRIVE_STEPS", steps)


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
    print("L16_SRC1_VIRTUAL_CENSUS_WROTE", path)


def report(debugger):
    print("L16_SRC1_VIRTUAL_CENSUS_BEGIN")
    print(json.dumps(payload(debugger), indent=2, sort_keys=True))
    print("L16_SRC1_VIRTUAL_CENSUS_END")
