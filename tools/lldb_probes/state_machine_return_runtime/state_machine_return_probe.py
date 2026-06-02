import builtins
import json
import struct


PRE_CALL = 0x22F3F6
POST_CALL = 0x22F3FF

OPERATORS = {
    0x229DF0: "runReferenceGroupCams::$_0",
    0x229EC0: "runReferenceGroupCams::$_1",
    0x22A0E0: "runReferenceGroupCams::$_2",
    0x22A9B0: "runReferenceGroupCams::$_3",
    0x22AAF0: "runReferenceGroupCams::$_4",
    0x22AE60: "runReferenceGroupCams::$_5",
    0x22AF80: "runReferenceGroupCams::$_6",
    0x22BDF0: "runHigherGroupCams::$_7",
    0x22BEE0: "runHigherGroupCams::$_8",
    0x22C350: "runHigherGroupCams::$_9",
    0x22CD00: "runHigherGroupCams::$_10",
    0x22D250: "runHigherGroupCams::$_11",
    0x22E1D0: "runHigherGroupCams::$_12",
}


def reset(label="", sample_limit=512, hit_cap=2048):
    builtins.l16_state_machine_return = {
        "label": label,
        "sample_limit": sample_limit,
        "hit_cap": hit_cap,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
        "breakpoint_ids": {},
        "breakpoint_vas": {},
        "counts": {
            "pre_call_0x22f3f6": 0,
            "post_call_0x22f3ff": 0,
        },
        "transition_counts": {},
        "active_pre_call_by_thread": {},
        "events": [],
        "disabled_after_cap": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_state_machine_return"):
        reset()
    return builtins.l16_state_machine_return


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


def _read_i32(process, addr):
    data = _read(process, addr, 4)
    return struct.unpack_from("<i", data, 0)[0] if data is not None else None


def _read_u64(process, addr):
    data = _read(process, addr, 8)
    return struct.unpack_from("<Q", data, 0)[0] if data is not None else None


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
            }
        )
    return frames


def _state_slots(process, regs):
    state_machine = regs.get("r14", 0)
    state_slot = regs.get("r12", 0)
    return {
        "state_machine": state_machine,
        "state_slot_ptr": state_slot,
        "state_slot_value_i32": _read_i32(process, state_slot),
        "state_machine_plus_0x68_i32": _read_i32(process, state_machine + 0x68)
        if state_machine
        else None,
        "state_machine_plus_0x6c_i32": _read_i32(process, state_machine + 0x6C)
        if state_machine
        else None,
    }


def _function_object(process, target, function_object):
    vtable = _read_u64(process, function_object)
    slot30 = _read_u64(process, vtable + 0x30) if vtable else None
    slot30_va = _module_va(target, slot30) if slot30 else None
    return {
        "function_object": function_object,
        "vtable": vtable,
        "slot_0x30": slot30,
        "slot_0x30_va": slot30_va,
        "operator_name": OPERATORS.get(slot30_va),
    }


def _disable_breakpoint(debugger, bp_id):
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id) if bp_id else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def attach_existing(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    if target.GetNumBreakpoints() < 2:
        state["errors"].append("not enough existing breakpoints")
        print("L16_STATE_MACHINE_RETURN_ATTACH_ERROR not enough existing breakpoints")
        return
    sites = [PRE_CALL, POST_CALL]
    start = target.GetNumBreakpoints() - len(sites)
    for index, va in enumerate(sites):
        bp = target.GetBreakpointAtIndex(start + index)
        if not bp or not bp.IsValid():
            state["errors"].append(f"missing breakpoint for 0x{va:x}")
            continue
        bp.SetScriptCallbackFunction("state_machine_return_probe.hit")
        bp_id = bp.GetID()
        state["breakpoint_ids"][f"0x{va:x}"] = bp_id
        state["breakpoint_vas"][str(bp_id)] = va
    print(
        "L16_STATE_MACHINE_RETURN_ATTACHED",
        json.dumps(state["breakpoint_ids"], sort_keys=True),
    )


def _append_event(event):
    state = _state()
    if len(state["events"]) < state["sample_limit"]:
        state["events"].append(event)


def _pre_call(frame, bp_id):
    state = _state()
    state["counts"]["pre_call_0x22f3f6"] += 1
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    regs = _registers(frame)
    thread_key = str(thread.GetThreadID())
    event = {
        "kind": "pre_call",
        "thread_id": thread.GetThreadID(),
        "site_va": _module_va(target, frame.GetPC()),
        "registers": regs,
        "state_slots": _state_slots(process, regs),
        "function_object": _function_object(process, target, regs["rdi"]),
        "stack": _stack(thread),
    }
    state["active_pre_call_by_thread"].setdefault(thread_key, []).append(event)
    _append_event(event)
    if state["counts"]["pre_call_0x22f3f6"] >= state["hit_cap"]:
        _disable_breakpoint(frame.GetThread().GetProcess().GetTarget().GetDebugger(), bp_id)
        state["disabled_after_cap"].append("pre_call_0x22f3f6")


def _post_call(frame, bp_id):
    state = _state()
    state["counts"]["post_call_0x22f3ff"] += 1
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    regs = _registers(frame)
    returned_state = _i32(regs["rax"])
    thread_key = str(thread.GetThreadID())
    active_list = state["active_pre_call_by_thread"].get(thread_key) or []
    pre = active_list.pop() if active_list else None
    if pre is None:
        state["errors"].append(f"post-call without pre-call on thread {thread_key}")
    operator_va = (
        pre.get("function_object", {}).get("slot_0x30_va") if pre else None
    )
    operator_name = OPERATORS.get(operator_va)
    transition_key = f"{operator_va and hex(operator_va)}->{returned_state}"
    state["transition_counts"][transition_key] = (
        state["transition_counts"].get(transition_key, 0) + 1
    )
    event = {
        "kind": "post_call",
        "thread_id": thread.GetThreadID(),
        "site_va": _module_va(target, frame.GetPC()),
        "returned_state_i32": returned_state,
        "operator_va": operator_va,
        "operator_name": operator_name,
        "pre_call_state_slots": pre.get("state_slots") if pre else None,
        "pre_call_function_object": pre.get("function_object") if pre else None,
        "registers": regs,
        "state_slots_before_store": _state_slots(process, regs),
        "stack": _stack(thread),
    }
    _append_event(event)
    if state["counts"]["post_call_0x22f3ff"] >= state["hit_cap"]:
        _disable_breakpoint(frame.GetThread().GetProcess().GetTarget().GetDebugger(), bp_id)
        state["disabled_after_cap"].append("post_call_0x22f3ff")


def hit(frame, bp_loc, internal_dict):
    state = _state()
    bp_id = bp_loc.GetBreakpoint().GetID()
    va = state["breakpoint_vas"].get(str(bp_id))
    if va == PRE_CALL:
        _pre_call(frame, bp_id)
    elif va == POST_CALL:
        _post_call(frame, bp_id)
    else:
        state["errors"].append(f"unknown breakpoint id {bp_id}")
    return False


def _breakpoint_hit_counts(debugger):
    target = debugger.GetSelectedTarget()
    out = {}
    for key, bp_id in _state().get("breakpoint_ids", {}).items():
        bp = target.FindBreakpointByID(bp_id)
        out[key] = bp.GetHitCount() if bp and bp.IsValid() else None
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
    print("L16_STATE_MACHINE_RETURN_DRIVE_STEPS", steps)


def payload(debugger):
    return {
        "process": _process_packet(debugger),
        "breakpoint_hit_counts": _breakpoint_hit_counts(debugger),
        "operators": {f"0x{va:x}": name for va, name in OPERATORS.items()},
        **_state(),
    }


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_STATE_MACHINE_RETURN_WROTE", path)


def report(debugger):
    print("L16_STATE_MACHINE_RETURN_BEGIN")
    print(json.dumps(payload(debugger), indent=2, sort_keys=True))
    print("L16_STATE_MACHINE_RETURN_END")
