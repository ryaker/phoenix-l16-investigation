import builtins
import json
import struct


SITES = {
    0x23C5F0: "state_helper_23c5f0",
    0x0F33D0: "calibstage_field_copy_f33d0",
}


def reset(label="", sample_limit=1024, hit_cap=4096):
    builtins.l16_state_helper_23c5f0 = {
        "label": label,
        "sample_limit": sample_limit,
        "hit_cap": hit_cap,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
        "breakpoint_ids": {},
        "breakpoint_vas": {},
        "counts": {f"0x{va:x}": 0 for va in SITES},
        "events": [],
        "disabled_after_cap": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_state_helper_23c5f0"):
        reset()
    return builtins.l16_state_helper_23c5f0


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
    names = (
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
    return {name: _u(frame, name) for name in names}


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


def _f33d0_packet(process, regs):
    selector = _i32(regs["r8"])
    rdi = regs["rdi"]
    rsi = regs["rsi"]
    rdx = regs["rdx"]
    rcx = regs["rcx"]
    return {
        "selector_r8d": selector,
        "dest_rdi": rdi,
        "src1_rsi": rsi,
        "src2_rdx": rdx,
        "triple_rcx": rcx,
        "src1_i32_0x20": _read_i32(process, rsi + 0x20),
        "src2_i32_0x20": _read_i32(process, rdx + 0x20),
        "triple_i32": [
            _read_i32(process, rcx),
            _read_i32(process, rcx + 4),
            _read_i32(process, rcx + 8),
        ],
        "src1_f32x8": _read_f32_tuple(process, rsi, 8),
        "src2_f32x8": _read_f32_tuple(process, rdx, 8),
        "dest_pre_factory_offsets": {
            "0x180": _read_f32_tuple(process, rdi + 0x180, 8),
            "0x1a0": _read_i32(process, rdi + 0x1A0),
            "0x1a4": _read_f32_tuple(process, rdi + 0x1A4, 8),
            "0x1c4": _read_i32(process, rdi + 0x1C4),
            "0x1c8_0x1d0": [
                _read_i32(process, rdi + 0x1C8),
                _read_i32(process, rdi + 0x1CC),
                _read_i32(process, rdi + 0x1D0),
            ],
        },
        "dest_pre_current_offsets": {
            "0x12c": _read_f32_tuple(process, rdi + 0x12C, 8),
            "0x14c": _read_i32(process, rdi + 0x14C),
            "0x150": _read_f32_tuple(process, rdi + 0x150, 8),
            "0x170": _read_i32(process, rdi + 0x170),
            "0x174_0x17c": [
                _read_i32(process, rdi + 0x174),
                _read_i32(process, rdi + 0x178),
                _read_i32(process, rdi + 0x17C),
            ],
        },
    }


def _helper_packet(process, regs):
    tree = regs["rcx"]
    source = regs["rdx"]
    return {
        "r8d": _i32(regs["r8"]),
        "r9d": _i32(regs["r9"]),
        "rdi": regs["rdi"],
        "rsi": regs["rsi"],
        "rdx": source,
        "rcx": tree,
        "source_df940_i32_candidate": _read_i32(process, source + 0x60),
        "tree_qword_0x8": _read_u64(process, tree + 0x8),
        "tree_qword_0x0": _read_u64(process, tree),
    }


def _disable_breakpoint(debugger, bp_id):
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id) if bp_id else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def attach_existing(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    if target.GetNumBreakpoints() < len(SITES):
        state["errors"].append("not enough existing breakpoints")
        print("L16_STATE_HELPER_ATTACH_ERROR not enough existing breakpoints")
        return
    start = target.GetNumBreakpoints() - len(SITES)
    for index, va in enumerate(SITES):
        bp = target.GetBreakpointAtIndex(start + index)
        if not bp or not bp.IsValid():
            state["errors"].append(f"missing breakpoint for 0x{va:x}")
            continue
        bp.SetScriptCallbackFunction("state_helper_probe.hit")
        bp_id = bp.GetID()
        state["breakpoint_ids"][f"0x{va:x}"] = bp_id
        state["breakpoint_vas"][str(bp_id)] = va
    print("L16_STATE_HELPER_ATTACHED", json.dumps(state["breakpoint_ids"], sort_keys=True))


def _append_event(event):
    state = _state()
    if len(state["events"]) < state["sample_limit"]:
        state["events"].append(event)


def hit(frame, bp_loc, internal_dict):
    state = _state()
    bp_id = bp_loc.GetBreakpoint().GetID()
    va = state["breakpoint_vas"].get(str(bp_id))
    if va is None:
        state["errors"].append(f"unknown breakpoint id {bp_id}")
        return False
    key = f"0x{va:x}"
    state["counts"][key] = state["counts"].get(key, 0) + 1
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    regs = _registers(frame)
    event = {
        "site_va": _module_va(target, frame.GetPC()),
        "site_name": SITES.get(va),
        "thread_id": thread.GetThreadID(),
        "registers": regs,
        "stack": _stack(thread),
    }
    if va == 0x0F33D0:
        event["f33d0"] = _f33d0_packet(process, regs)
    elif va == 0x23C5F0:
        event["helper_23c5f0"] = _helper_packet(process, regs)
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
    print("L16_STATE_HELPER_DRIVE_STEPS", steps)


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
    print("L16_STATE_HELPER_WROTE", path)
