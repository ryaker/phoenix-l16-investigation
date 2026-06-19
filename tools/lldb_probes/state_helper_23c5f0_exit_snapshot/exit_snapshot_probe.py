import builtins
import json
import struct


SITES = {
    0x23C5F0: "entry_23c5f0",
    0x23D392: "post_f33d0_in_23c5f0",
    0x23D5A8: "pre_destroy_exit_23c5f0",
}


def reset(label="", sample_limit=2048, hit_cap=4096):
    builtins.l16_23c5f0_exit_snapshot = {
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
        "next_invocation_id": 1,
        "thread_invocation_stack": {},
    }


def _state():
    if not hasattr(builtins, "l16_23c5f0_exit_snapshot"):
        reset()
    return builtins.l16_23c5f0_exit_snapshot


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _i32_value(value):
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


def _read_hex(process, addr, size):
    data = _read(process, addr, size)
    return data.hex() if data is not None else None


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


def _node_packet(process, addr):
    return {
        "addr": addr,
        "left_0x00": _read_u64(process, addr),
        "right_0x08": _read_u64(process, addr + 0x8),
        "parent_0x10": _read_u64(process, addr + 0x10),
        "i32_0x18": _read_i32(process, addr + 0x18),
        "i32_0x1c": _read_i32(process, addr + 0x1C),
        "i32_0x20": _read_i32(process, addr + 0x20),
        "i32_0x24": _read_i32(process, addr + 0x24),
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
        "raw_0x00_0x40": _read_hex(process, addr, 0x40),
    }


def _tree_snapshot(process, rbp, max_nodes=64):
    header = {
        "slot_minus_0x150": _read_u64(process, rbp - 0x150),
        "root_minus_0x148": _read_u64(process, rbp - 0x148),
        "size_minus_0x140": _read_u64(process, rbp - 0x140),
    }
    root = header["root_minus_0x148"]
    nodes = []
    queue = [root] if root else []
    seen = set()
    while queue and len(nodes) < max_nodes:
        addr = queue.pop(0)
        if not addr or addr in seen:
            continue
        seen.add(addr)
        packet = _node_packet(process, addr)
        nodes.append(packet)
        for child_key in ("left_0x00", "right_0x08"):
            child = packet.get(child_key)
            if child and child not in seen:
                queue.append(child)
    return {
        "header": header,
        "visited_count": len(nodes),
        "truncated": bool(queue),
        "nodes": nodes,
    }


def _entry_packet(process, regs):
    rsp = regs["rsp"]
    rdx = regs["rdx"]
    return {
        "return_address": _read_u64(process, rsp),
        "stack_arg0": _read_u64(process, rsp + 0x8),
        "stack_arg1": _read_u64(process, rsp + 0x10),
        "stack_arg2": _read_u64(process, rsp + 0x18),
        "r8d": _i32_value(regs["r8"]),
        "r9d": _i32_value(regs["r9"]),
        "rdx_i32_0x60_candidate": _read_i32(process, rdx + 0x60),
        "rdx_i32_0x64_candidate": _read_i32(process, rdx + 0x64),
        "rdx_i32_0x100_candidate": _read_i32(process, rdx + 0x100),
        "rdi": regs["rdi"],
        "rsi": regs["rsi"],
        "rdx": rdx,
        "rcx": regs["rcx"],
    }


def _current_calib_offsets(process, dest):
    return {
        "0x12c": _read_f32_tuple(process, dest + 0x12C, 8),
        "raw_0x12c_0x14c": _read_hex(process, dest + 0x12C, 0x20),
        "0x14c": _read_i32(process, dest + 0x14C),
        "0x150": _read_f32_tuple(process, dest + 0x150, 8),
        "raw_0x150_0x170": _read_hex(process, dest + 0x150, 0x20),
        "0x170": _read_i32(process, dest + 0x170),
        "0x174_0x17c": [
            _read_i32(process, dest + 0x174),
            _read_i32(process, dest + 0x178),
            _read_i32(process, dest + 0x17C),
        ],
        "raw_0x12c_0x180": _read_hex(process, dest + 0x12C, 0x54),
    }


def _post_f33d0_packet(process, regs):
    rbp = regs["rbp"]
    dest = _read_u64(process, rbp - 0x778)
    src1 = rbp - 0x768
    src2 = rbp - 0x738
    triple = rbp - 0x744
    return {
        "rbp": rbp,
        "loop_key_i32_minus_0x4e0": _read_i32(process, rbp - 0x4E0),
        "dest_ptr_minus_0x778": dest,
        "dest_current_offsets_post": _current_calib_offsets(process, dest)
        if dest
        else None,
        "src1_stack_minus_0x768_i32_0x20": _read_i32(process, src1 + 0x20),
        "src2_stack_minus_0x738_i32_0x20": _read_i32(process, src2 + 0x20),
        "triple_stack_minus_0x744": [
            _read_i32(process, triple),
            _read_i32(process, triple + 4),
            _read_i32(process, triple + 8),
        ],
        "src1_stack_f32x8": _read_f32_tuple(process, src1, 8),
        "src1_stack_raw_0x00_0x24": _read_hex(process, src1, 0x24),
        "src2_stack_f32x8": _read_f32_tuple(process, src2, 8),
        "src2_stack_raw_0x00_0x24": _read_hex(process, src2, 0x24),
        "triple_stack_raw_0x00_0x0c": _read_hex(process, triple, 0xC),
    }


def _exit_packet(process, regs):
    rbp = regs["rbp"]
    return {
        "rbp": rbp,
        "saved_rdi_minus_0x7b8": _read_u64(process, rbp - 0x7B8),
        "saved_rdx_minus_0x790": _read_u64(process, rbp - 0x790),
        "saved_rcx_minus_0x798": _read_u64(process, rbp - 0x798),
        "saved_r8d_minus_0x7a8": _read_i32(process, rbp - 0x7A8),
        "saved_r9d_minus_0x7a0": _read_i32(process, rbp - 0x7A0),
        "saved_stack_arg0_minus_0x780": _read_u64(process, rbp - 0x780),
        "tree_before_final_destroy": _tree_snapshot(process, rbp),
    }


def _push_invocation(thread_id):
    state = _state()
    invocation_id = state["next_invocation_id"]
    state["next_invocation_id"] += 1
    stack = state["thread_invocation_stack"].setdefault(str(thread_id), [])
    stack.append(invocation_id)
    return invocation_id


def _current_invocation(thread_id):
    stack = _state()["thread_invocation_stack"].get(str(thread_id), [])
    return stack[-1] if stack else None


def _pop_invocation(thread_id):
    stack = _state()["thread_invocation_stack"].get(str(thread_id), [])
    return stack.pop() if stack else None


def _disable_breakpoint(debugger, bp_id):
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id) if bp_id else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def attach_existing(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    if target.GetNumBreakpoints() < len(SITES):
        state["errors"].append("not enough existing breakpoints")
        print("L16_23C5F0_ATTACH_ERROR not enough existing breakpoints")
        return
    start = target.GetNumBreakpoints() - len(SITES)
    for index, va in enumerate(SITES):
        bp = target.GetBreakpointAtIndex(start + index)
        if not bp or not bp.IsValid():
            state["errors"].append(f"missing breakpoint for 0x{va:x}")
            continue
        bp.SetScriptCallbackFunction("exit_snapshot_probe.hit")
        bp_id = bp.GetID()
        state["breakpoint_ids"][f"0x{va:x}"] = bp_id
        state["breakpoint_vas"][str(bp_id)] = va
    print("L16_23C5F0_ATTACHED", json.dumps(state["breakpoint_ids"], sort_keys=True))


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
    thread_id = thread.GetThreadID()
    if va == 0x23C5F0:
        invocation_id = _push_invocation(thread_id)
    else:
        invocation_id = _current_invocation(thread_id)
    event = {
        "site_va": _module_va(target, frame.GetPC()),
        "site_name": SITES.get(va),
        "invocation_id": invocation_id,
        "thread_id": thread_id,
        "registers": regs,
        "stack": _stack(thread),
    }
    try:
        if va == 0x23C5F0:
            event["entry"] = _entry_packet(process, regs)
        elif va == 0x23D392:
            event["post_f33d0"] = _post_f33d0_packet(process, regs)
        elif va == 0x23D5A8:
            event["exit"] = _exit_packet(process, regs)
            popped = _pop_invocation(thread_id)
            event["popped_invocation_id"] = popped
            if popped != invocation_id:
                state["errors"].append(
                    f"invocation stack mismatch thread {thread_id}: current {invocation_id} popped {popped}"
                )
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
    print("L16_23C5F0_DRIVE_STEPS", steps)


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
    print("L16_23C5F0_WROTE", path)
