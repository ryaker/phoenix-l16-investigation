import builtins
import json
import struct


SITES = {
    0x3F7040: "entry_0x3f7040",
    0x3F719D: "same_call_0x268480",
    0x3F71A2: "same_after_0x268480",
    0x3F71BB: "same_after_0x25e500",
    0x3F7480: "cross_call_0x268480",
    0x3F7485: "cross_after_0x268480",
    0x3F749E: "cross_after_0x25e500",
    0x26848F: "provider_virtual_call_0x26848f",
}

EXPECTED_PROVIDER_RETURNS = {0x3F71A2, 0x3F7485}
KNOWN_SLOT_RETURNS = {
    0x26FB50: 0x2A8,
    0x26B590: 0x90,
}


def reset(label="", site_cap=128, sample_limit=64):
    builtins.l16_iramp_map_provider = {
        "label": label,
        "site_cap": site_cap,
        "sample_limit": sample_limit,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
        "breakpoint_ids": {},
        "counts": {name: 0 for name in SITES.values()},
        "ignored_provider_virtual_calls": 0,
        "provider_target_counts": {},
        "map_return_counts": {},
        "record_map_counts": {},
        "disabled_after_cap": [],
        "samples": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_iramp_map_provider"):
        reset()
    return builtins.l16_iramp_map_provider


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
    base = _libcp_base(target)
    if base is not None and pc >= base:
        return pc - base
    return None


def _read_qword(process, addr):
    data = _read(process, addr, 8)
    return _u64(data) if data is not None else None


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


def _provider_context(target, process, context_addr):
    tmp = _read_qword(process, context_addr + 0x18) if context_addr else None
    obj = _read_qword(process, tmp - 0x8) if tmp else None
    vtable = _read_qword(process, obj) if obj else None
    slot = _read_qword(process, vtable + 0x90) if vtable else None
    slot_va = _module_va(target, slot) if slot else None
    expected_offset = KNOWN_SLOT_RETURNS.get(slot_va)
    return {
        "context_addr": context_addr,
        "context_plus_0x18": tmp,
        "object": obj,
        "vtable": vtable,
        "vtable_libcp_va": _module_va(target, vtable) if vtable else None,
        "slot_0x90": slot,
        "slot_0x90_libcp_va": slot_va,
        "known_slot_return_offset": expected_offset,
        "known_slot_expected_return": obj + expected_offset
        if obj and expected_offset is not None
        else None,
    }


def _record50(process, addr):
    data = _read(process, addr, 0x50)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "row_f32": [_f32(data, off) for off in range(0x00, 0x40, 4)],
        "map_ptr_0x40": _u64(data, 0x40),
        "scale_x_0x48": _f32(data, 0x48),
        "scale_y_0x4c": _f32(data, 0x4C),
    }


def _provider_virtual_packet(frame, regs):
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    vtable = regs["rax"]
    obj = regs["rdi"]
    slot = _read_qword(process, vtable + 0x90) if vtable else None
    slot_va = _module_va(target, slot) if slot else None
    expected_offset = KNOWN_SLOT_RETURNS.get(slot_va)
    return {
        "object": obj,
        "vtable": vtable,
        "vtable_libcp_va": _module_va(target, vtable) if vtable else None,
        "slot_0x90": slot,
        "slot_0x90_libcp_va": slot_va,
        "known_slot_return_offset": expected_offset,
        "known_slot_expected_return": obj + expected_offset
        if obj and expected_offset is not None
        else None,
    }


def _caller_return_va(frame):
    thread = frame.GetThread()
    if thread.GetNumFrames() < 2:
        return None
    return _module_va(thread.GetProcess().GetTarget(), thread.GetFrameAtIndex(1).GetPC())


def _disable_breakpoint(debugger, name):
    bp_id = _state()["breakpoint_ids"].get(name)
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id) if bp_id else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def _bump_count(name):
    state = _state()
    state["counts"][name] = state["counts"].get(name, 0) + 1


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
    caller_return = _caller_return_va(frame)
    if site_va == 0x26848F and caller_return not in EXPECTED_PROVIDER_RETURNS:
        state["ignored_provider_virtual_calls"] += 1
        return False

    _bump_count(name)
    sample = {
        "site": name,
        "site_va": site_va,
        "caller_return_va": caller_return,
        "registers": regs,
        "stack": _stack(thread),
    }

    if site_va in (0x3F719D, 0x3F7480):
        sample["provider_context_at_rdi"] = _provider_context(target, process, regs["rdi"])
    elif site_va == 0x26848F:
        packet = _provider_virtual_packet(frame, regs)
        sample["provider_virtual"] = packet
        key = str(packet.get("slot_0x90_libcp_va"))
        state["provider_target_counts"][key] = state["provider_target_counts"].get(key, 0) + 1
    elif site_va in (0x3F71A2, 0x3F7485):
        key = hex(regs["rax"])
        state["map_return_counts"][key] = state["map_return_counts"].get(key, 0) + 1
        sample["map_return_rax"] = regs["rax"]
    elif site_va in (0x3F71BB, 0x3F749E):
        record = _record50(process, regs["r15"])
        sample["record_at_r15"] = record
        if record.get("read_ok"):
            key = hex(record["map_ptr_0x40"])
            state["record_map_counts"][key] = state["record_map_counts"].get(key, 0) + 1

    if len(state["samples"]) < state["sample_limit"]:
        state["samples"].append(sample)

    if state["counts"][name] >= state["site_cap"]:
        _disable_breakpoint(target.GetDebugger(), name)
        if name not in state["disabled_after_cap"]:
            state["disabled_after_cap"].append(name)
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    count = target.GetNumBreakpoints()
    if count < len(SITES):
        _state()["errors"].append(f"expected at least {len(SITES)} breakpoints")
        print("L16_MAP_PROVIDER_ATTACH_ERROR", count, len(SITES))
        return
    ids = {}
    start = count - len(SITES)
    for index, (site_va, name) in enumerate(SITES.items(), start=start):
        bp = target.GetBreakpointAtIndex(index)
        bp.SetScriptCallbackFunction("map_provider_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_MAP_PROVIDER_ATTACHED", ids)


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
    while (
        process.IsValid()
        and process.GetState() == lldb.eStateStopped
        and steps < max_steps
    ):
        steps += 1
        process.Continue()
    state["drive_steps"] += steps
    if process.IsValid() and process.GetState() == lldb.eStateStopped and steps >= max_steps:
        state["drive_hit_step_cap"] = True
    print("L16_MAP_PROVIDER_DRIVE_STEPS", steps)


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
    print("L16_MAP_PROVIDER_WROTE", path)


def report(debugger):
    print("L16_MAP_PROVIDER_BEGIN")
    print(json.dumps(payload(debugger), indent=2, sort_keys=True))
    print("L16_MAP_PROVIDER_END")
