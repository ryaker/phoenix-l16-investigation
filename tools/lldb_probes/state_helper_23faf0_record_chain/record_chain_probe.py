import builtins
import json
import struct


SITES = {
    0x23CBAB: "after_264440",
    0x23CBC1: "after_23faf0",
    0x23CE5E: "after_node_field_writes",
    0x23D025: "after_node_a0_write",
}


def reset(label="", sample_limit=4096, hit_cap=4096):
    builtins.l16_23faf0_record_chain = {
        "label": label,
        "sample_limit": sample_limit,
        "hit_cap": hit_cap,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
        "breakpoint_ids": {},
        "breakpoint_vas": {},
        "counts": {f"0x{va:x}": 0 for va in SITES},
        "by_site_local_i32": {name: {} for name in SITES.values()},
        "events": [],
        "disabled_after_cap": [],
        "errors": [],
        "sequence": 0,
    }


def _state():
    if not hasattr(builtins, "l16_23faf0_record_chain"):
        reset()
    return builtins.l16_23faf0_record_chain


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


def _read_f64_tuple(process, addr, count):
    data = _read(process, addr, 8 * count)
    if data is None:
        return None
    return list(struct.unpack_from("<" + "d" * count, data, 0))


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
    names = ("rax", "rbx", "rcx", "rdx", "rdi", "rsi", "r13", "r14", "r15", "rbp", "rsp")
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


def _record_packet(process, addr):
    if not addr:
        return None
    return {
        "addr": addr,
        "f32_0x00x8": _read_f32_tuple(process, addr, 8),
        "i32_0x20": _read_i32(process, addr + 0x20),
        "i32_0x24_0x2c": [
            _read_i32(process, addr + 0x24),
            _read_i32(process, addr + 0x28),
            _read_i32(process, addr + 0x2C),
        ],
        "f32_0x30x8": _read_f32_tuple(process, addr + 0x30, 8),
        "i32_0x50": _read_i32(process, addr + 0x50),
        "f32_0x54x4": _read_f32_tuple(process, addr + 0x54, 4),
        "f32_0x68x4": _read_f32_tuple(process, addr + 0x68, 4),
        "f32_0x80x4": _read_f32_tuple(process, addr + 0x80, 4),
        "f32_0x90x4": _read_f32_tuple(process, addr + 0x90, 4),
        "i32_0xa0": _read_i32(process, addr + 0xA0),
    }


def _node_packet(process, addr):
    if not addr:
        return None
    return {
        "addr": addr,
        "left_0x00": _read_u64(process, addr),
        "right_0x08": _read_u64(process, addr + 0x8),
        "parent_0x10": _read_u64(process, addr + 0x10),
        "i32_0x18": _read_i32(process, addr + 0x18),
        "i32_0x1c": _read_i32(process, addr + 0x1C),
        "i32_0x20": _read_i32(process, addr + 0x20),
        "f64_0x28x2": _read_f64_tuple(process, addr + 0x28, 2),
        "f64_0x38x2": _read_f64_tuple(process, addr + 0x38, 2),
        "f64_0x48x2": _read_f64_tuple(process, addr + 0x48, 2),
        "f64_0x58x2": _read_f64_tuple(process, addr + 0x58, 2),
        "f64_0x68": _read_f64_tuple(process, addr + 0x68, 1),
        "f32_0x70x4": _read_f32_tuple(process, addr + 0x70, 4),
        "u64_0x80": _read_u64(process, addr + 0x80),
        "f64_0x88x2": _read_f64_tuple(process, addr + 0x88, 2),
        "f64_0x98": _read_f64_tuple(process, addr + 0x98, 1),
        "i32_0xa0": _read_i32(process, addr + 0xA0),
    }


def _inc_local(site_name, local_i32):
    table = _state()["by_site_local_i32"][site_name]
    key = str(local_i32)
    table[key] = table.get(key, 0) + 1


def _append_event(event):
    state = _state()
    if len(state["events"]) < state["sample_limit"]:
        state["events"].append(event)


def _packet_for_site(process, regs, site_name):
    rbp = regs["rbp"]
    local_i32 = _read_i32(process, rbp - 0x2D0)
    _inc_local(site_name, local_i32)
    base = {
        "local_i32_minus_0x2d0": local_i32,
        "helper_record_rbp_minus_0x420": _record_packet(process, rbp - 0x420),
        "compose_output_rbp_minus_0x378": _record_packet(process, rbp - 0x378),
        "source_object_ptr_minus_0x430": _read_u64(process, rbp - 0x430),
    }
    if site_name == "after_node_field_writes":
        base["tree_node_rbx"] = _node_packet(process, regs["rbx"])
    if site_name == "after_node_a0_write":
        base["tree_node_r13"] = _node_packet(process, regs["r13"])
    return base


def _disable_breakpoint(debugger, bp_id):
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id) if bp_id else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def attach_existing(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    if target.GetNumBreakpoints() < len(SITES):
        state["errors"].append("not enough existing breakpoints")
        print("L16_23FAF0_CHAIN_ATTACH_ERROR not enough existing breakpoints")
        return
    start = target.GetNumBreakpoints() - len(SITES)
    for index, va in enumerate(SITES):
        bp = target.GetBreakpointAtIndex(start + index)
        if not bp or not bp.IsValid():
            state["errors"].append(f"missing breakpoint for 0x{va:x}")
            continue
        bp.SetScriptCallbackFunction("record_chain_probe.hit")
        bp_id = bp.GetID()
        state["breakpoint_ids"][f"0x{va:x}"] = bp_id
        state["breakpoint_vas"][str(bp_id)] = va
    print("L16_23FAF0_CHAIN_ATTACHED", json.dumps(state["breakpoint_ids"], sort_keys=True))


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
    site_name = SITES.get(va)
    event = {
        "sequence": state["sequence"],
        "site_va": _module_va(target, frame.GetPC()),
        "site_name": site_name,
        "thread_id": thread.GetThreadID(),
        "registers": regs,
        "stack": _stack(thread),
    }
    try:
        event["packet"] = _packet_for_site(process, regs, site_name)
    except Exception as exc:
        state["errors"].append(f"packet error at 0x{va:x}: {exc}")
    _append_event(event)
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
    print("L16_23FAF0_CHAIN_DRIVE_STEPS", steps)


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
    print("L16_23FAF0_CHAIN_WROTE", path)
