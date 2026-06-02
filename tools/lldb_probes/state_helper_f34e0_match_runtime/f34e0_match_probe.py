import builtins
import json
import struct


SITES = {
    0x23D392: "post_f33d0_in_23c5f0",
    0x0F34E0: "f34e0_entry",
}


def reset(label="", sample_limit=4096, hit_cap=8192):
    builtins.l16_f34e0_match = {
        "label": label,
        "sample_limit": sample_limit,
        "hit_cap": hit_cap,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
        "breakpoint_ids": {},
        "breakpoint_vas": {},
        "counts": {f"0x{va:x}": 0 for va in SITES},
        "dest_records": {},
        "dest_records_by_local_i32": {},
        "f34e0_by_caller": {},
        "f34e0_by_selector": {},
        "matched_f34e0_by_caller": {},
        "matched_f34e0_by_selector": {},
        "matched_objects": {},
        "events": [],
        "disabled_after_cap": [],
        "errors": [],
        "sequence": 0,
    }


def _state():
    if not hasattr(builtins, "l16_f34e0_match"):
        reset()
    return builtins.l16_f34e0_match


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


def _read_f32_tuple(process, addr, count):
    data = _read(process, addr, 4 * count)
    if data is None:
        return None
    return list(struct.unpack_from("<" + "f" * count, data, 0))


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
    names = ("rax", "rbx", "rcx", "rdx", "rdi", "rsi", "r8", "r9", "rbp", "rsp")
    return {name: _u(frame, name) for name in names}


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


def _caller_key(stack):
    if len(stack) < 2:
        return "None"
    va = stack[1].get("libcp_va")
    return f"0x{va:x}" if va is not None else "None"


def _inc(table, key, amount=1):
    state = _state()
    table_obj = state[table]
    table_obj[key] = table_obj.get(key, 0) + amount


def _append_event(event):
    state = _state()
    if len(state["events"]) < state["sample_limit"]:
        state["events"].append(event)


def _current_offsets(process, obj):
    return {
        "current_0x12c_f32x8": _read_f32_tuple(process, obj + 0x12C, 8),
        "current_0x14c_i32": _read_i32(process, obj + 0x14C),
        "current_0x150_f32x8": _read_f32_tuple(process, obj + 0x150, 8),
        "current_0x170_i32": _read_i32(process, obj + 0x170),
        "current_0x174_0x17c_i32": [
            _read_i32(process, obj + 0x174),
            _read_i32(process, obj + 0x178),
            _read_i32(process, obj + 0x17C),
        ],
    }


def _factory_offsets(process, obj):
    return {
        "factory_0x180_f32x8": _read_f32_tuple(process, obj + 0x180, 8),
        "factory_0x1a0_i32": _read_i32(process, obj + 0x1A0),
        "factory_0x1a4_f32x8": _read_f32_tuple(process, obj + 0x1A4, 8),
        "factory_0x1c4_i32": _read_i32(process, obj + 0x1C4),
        "factory_0x1c8_0x1d0_i32": [
            _read_i32(process, obj + 0x1C8),
            _read_i32(process, obj + 0x1CC),
            _read_i32(process, obj + 0x1D0),
        ],
    }


def _post_f33d0_event(process, regs):
    rbp = regs["rbp"]
    obj = _read_u64(process, rbp - 0x778)
    local_i32 = _read_i32(process, rbp - 0x4E0)
    event = {
        "dest_ptr_minus_0x778": obj,
        "local_i32_minus_0x4e0": local_i32,
    }
    if obj:
        event.update(_current_offsets(process, obj))
        ptr_key = f"0x{obj:x}"
        state = _state()
        records = state["dest_records"].setdefault(ptr_key, [])
        records.append(
            {
                "sequence": state["sequence"],
                "local_i32_minus_0x4e0": local_i32,
            }
        )
        local_key = str(local_i32)
        state["dest_records_by_local_i32"][local_key] = (
            state["dest_records_by_local_i32"].get(local_key, 0) + 1
        )
    return event


def _f34e0_event(process, regs, stack):
    obj = regs["rdi"]
    selector = _i32(regs["rsi"])
    ptr_key = f"0x{obj:x}"
    caller = _caller_key(stack)
    matched_records = _state()["dest_records"].get(ptr_key, [])
    matched = bool(matched_records)
    selector_key = str(selector)
    _inc("f34e0_by_caller", caller)
    _inc("f34e0_by_selector", selector_key)
    if matched:
        _inc("matched_f34e0_by_caller", caller)
        _inc("matched_f34e0_by_selector", selector_key)
        _state()["matched_objects"][ptr_key] = {
            "first_matched_sequence": _state()["sequence"],
            "last_selector": selector,
            "last_caller": caller,
            "dest_record_count": len(matched_records),
        }
    selected_bank = obj + (0x12C if selector == 1 else 0x180) if obj else None
    event = {
        "object_rdi": obj,
        "selector_esi": selector,
        "caller_return_va": caller,
        "matched_prior_23c5f0_dest": matched,
        "matched_dest_records": matched_records[:8],
        "selected_bank_by_static_f34e0_formula": selected_bank,
    }
    if matched and obj:
        event.update(_current_offsets(process, obj))
        event.update(_factory_offsets(process, obj))
    return event


def _disable_breakpoint(debugger, bp_id):
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id) if bp_id else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def attach_existing(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    if target.GetNumBreakpoints() < len(SITES):
        state["errors"].append("not enough existing breakpoints")
        print("L16_F34E0_MATCH_ATTACH_ERROR not enough existing breakpoints")
        return
    start = target.GetNumBreakpoints() - len(SITES)
    for index, va in enumerate(SITES):
        bp = target.GetBreakpointAtIndex(start + index)
        if not bp or not bp.IsValid():
            state["errors"].append(f"missing breakpoint for 0x{va:x}")
            continue
        bp.SetScriptCallbackFunction("f34e0_match_probe.hit")
        bp_id = bp.GetID()
        state["breakpoint_ids"][f"0x{va:x}"] = bp_id
        state["breakpoint_vas"][str(bp_id)] = va
    print("L16_F34E0_MATCH_ATTACHED", json.dumps(state["breakpoint_ids"], sort_keys=True))


def hit(frame, bp_loc, internal_dict):
    state = _state()
    bp_id = bp_loc.GetBreakpoint().GetID()
    va = state["breakpoint_vas"].get(str(bp_id))
    if va is None:
        state["errors"].append(f"unknown breakpoint id {bp_id}")
        return False
    state["sequence"] += 1
    key = f"0x{va:x}"
    state["counts"][key] = state["counts"].get(key, 0) + 1
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    regs = _registers(frame)
    stack = _stack(thread)
    event = {
        "sequence": state["sequence"],
        "site_va": _module_va(target, frame.GetPC()),
        "site_name": SITES.get(va),
        "thread_id": thread.GetThreadID(),
        "registers": regs,
        "stack": stack,
    }
    try:
        if va == 0x23D392:
            event["post_f33d0"] = _post_f33d0_event(process, regs)
            _append_event(event)
        elif va == 0x0F34E0:
            packet = _f34e0_event(process, regs, stack)
            event["f34e0"] = packet
            if packet.get("matched_prior_23c5f0_dest"):
                _append_event(event)
    except Exception as exc:
        state["errors"].append(f"packet error at 0x{va:x}: {exc}")
    if state["counts"][key] >= state["hit_cap"]:
        _disable_breakpoint(frame.GetThread().GetProcess().GetTarget().GetDebugger(), bp_id)
        state["disabled_after_cap"].append(key)
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
    print("L16_F34E0_MATCH_DRIVE_STEPS", steps)


def payload(debugger):
    return {
        "process": _process_packet(debugger),
        "breakpoint_hit_counts": _breakpoint_hit_counts(debugger),
        "sites": {f"0x{va:x}": name for va, name in SITES.items()},
        **_state(),
    }


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_F34E0_MATCH_WROTE", path)
