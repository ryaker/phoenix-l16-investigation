import builtins
import json
import os
import struct


ARM_SITE = 0x20D737
SCORE_RECORD_Z_COMPARE = 0x2189C4
SCORE_RECORD_Z_BRANCH = 0x2189C8
SCORE_RECORD_BODY = 0x2189CE
SCORE_RECORD_SKIP = 0x218AEB


def reset(label="", hit_cap=64, step_cap=50000, branch_trace_limit=0, select_gate_index=None):
    builtins.l16_prefusion_20ca00_record_z_watch = {
        "label": label,
        "hit_cap": hit_cap,
        "step_cap": step_cap,
        "branch_trace_limit": branch_trace_limit,
        "select_gate_index": select_gate_index,
        "breakpoint_id": None,
        "watchpoint_id": None,
        "armed": None,
        "last_hex": None,
        "samples": [],
        "branch_traces": [],
        "counts": {
            "arm_hits": 0,
            "arm_skips": 0,
            "record_z_branch_to_body": 0,
            "record_z_branch_to_skip": 0,
            "record_z_branch_traces": 0,
            "watchpoints_armed": 0,
            "watchpoint_hits": 0,
            "value_changes": 0,
            "value_unchanged": 0,
        },
        "errors": [],
        "drive_hit_step_cap": False,
    }


def _state():
    if not hasattr(builtins, "l16_prefusion_20ca00_record_z_watch"):
        reset()
    return builtins.l16_prefusion_20ca00_record_z_watch


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u64(process, address):
    data = _read(process, address, 8)
    return struct.unpack("<Q", data)[0] if data is not None else None


def _s64(process, address):
    data = _read(process, address, 8)
    return struct.unpack("<q", data)[0] if data is not None else None


def _f32(process, address):
    data = _read(process, address, 4)
    if data is None:
        return {"addr": address, "read_ok": False}
    return {
        "addr": address,
        "read_ok": True,
        "value": struct.unpack("<f", data)[0],
        "hex": data.hex(),
    }


def _module_va(target, address):
    lldb = builtins.__import__("lldb")
    module = target.FindModule(lldb.SBFileSpec("libcp.dylib"))
    if not module or not module.IsValid():
        return None
    header = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
    if header in (0, (1 << 64) - 1):
        return None
    return address - header


def _registers(frame):
    names = ("rax", "rbx", "rcx", "rdx", "rsi", "rdi", "r8", "r9", "r10", "r15", "rbp", "rsp")
    return {name: frame.FindRegister(name).GetValueAsUnsigned() for name in names}


def _pc_va(thread):
    frame = thread.GetFrameAtIndex(0)
    return _module_va(thread.GetProcess().GetTarget(), frame.GetPC())


def _rflags(frame):
    raw = frame.FindRegister("rflags").GetValueAsUnsigned()
    return {
        "raw": raw,
        "cf": raw & 1,
        "pf": (raw >> 2) & 1,
        "zf": (raw >> 6) & 1,
        "jae_taken": (raw & 1) == 0,
    }


def _step_once(thread):
    before = _pc_va(thread)
    thread.StepInstruction(False)
    after = _pc_va(thread)
    return {
        "before": before,
        "after": after,
        "stop_reason": int(thread.GetStopReason()),
    }


def _record_triple(process, z_addr):
    return {
        "x": _f32(process, z_addr - 8),
        "y": _f32(process, z_addr - 4),
        "z": _f32(process, z_addr),
    }


def _pair_from_registers(process, registers):
    base = registers.get("rbx")
    index = registers.get("rdx")
    if base is None or index is None:
        return None
    addr = base + 8 * index
    return {
        "addr": addr,
        "x": _f32(process, addr),
        "y": _f32(process, addr + 4),
    }


def _transform_window(process, rsi):
    if rsi is None:
        return None
    offsets = (
        0x00,
        0x04,
        0x08,
        0x0C,
        0x10,
        0x14,
        0x18,
        0x1C,
        0x20,
        0x24,
        0x28,
        0x2C,
        0x30,
        0x34,
        0x38,
        0x3C,
        0x40,
        0x44,
        0x48,
        0x4C,
        0x50,
    )
    return {f"+0x{offset:x}": _f32(process, rsi + offset) for offset in offsets}


def _stack(thread, limit=16):
    target = thread.GetProcess().GetTarget()
    rows = []
    for index in range(min(thread.GetNumFrames(), limit)):
        frame = thread.GetFrameAtIndex(index)
        rows.append(
            {
                "index": index,
                "pc": frame.GetPC(),
                "libcp_va": _module_va(target, frame.GetPC()),
                "function": frame.GetFunctionName(),
            }
        )
    return rows


def _trace_score_record_z_gate(thread, sample):
    state = _state()
    process = thread.GetProcess()
    frame = thread.GetFrameAtIndex(0)
    registers = _registers(frame)
    packet = {
        "thread_id": thread.GetThreadID(),
        "initial_pc_va": _pc_va(thread),
        "initial_stack": _stack(thread, 18),
        "registers_before": registers,
        "record_triple": _record_triple(process, state["armed"]["z_addr"]),
        "pair_xy": _pair_from_registers(process, registers),
        "transform_fields": _transform_window(process, registers.get("rsi")),
        "static_branch": {
            "compare_va": SCORE_RECORD_Z_COMPARE,
            "branch_va": SCORE_RECORD_Z_BRANCH,
            "instruction": "jae 0x218aeb",
            "body_va": SCORE_RECORD_BODY,
            "skip_target_va": SCORE_RECORD_SKIP,
        },
    }
    packet["compare_step"] = _step_once(thread)
    frame = thread.GetFrameAtIndex(0)
    packet["rflags_after_ucomiss"] = _rflags(frame)
    packet["branch_step"] = _step_once(thread)
    if packet["branch_step"].get("after") == SCORE_RECORD_BODY:
        state["counts"]["record_z_branch_to_body"] += 1
    elif packet["branch_step"].get("after") == SCORE_RECORD_SKIP:
        state["counts"]["record_z_branch_to_skip"] += 1
    state["counts"]["record_z_branch_traces"] += 1
    state["branch_traces"].append(packet)
    return packet


def arm_hit(frame, bp_loc, _dict):
    lldb = builtins.__import__("lldb")
    state = _state()
    state["counts"]["arm_hits"] += 1
    if state["watchpoint_id"] is not None:
        return False

    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    rbp = frame.FindRegister("rbp").GetValueAsUnsigned()
    gate_index = _s64(process, rbp - 0x2A0)
    record_begin = _u64(process, rbp - 0x2C8)
    record_offset = _s64(process, rbp - 0x2D0)
    selected_gate = state.get("select_gate_index")
    if selected_gate is not None and gate_index != selected_gate:
        state["counts"]["arm_skips"] += 1
        return False
    if record_begin is None or record_offset is None:
        state["errors"].append({"error": "record address locals unreadable", "rbp": rbp})
        return False
    triple_addr = record_begin + 4 * record_offset + 8
    z_addr = triple_addr + 8
    value = _f32(process, z_addr)
    if not value["read_ok"]:
        state["errors"].append({"error": "record z unreadable", "addr": z_addr})
        return False

    error = lldb.SBError()
    watchpoint = target.WatchAddress(z_addr, 4, True, True, error)
    if not error.Success() or not watchpoint or not watchpoint.IsValid():
        state["errors"].append({"error": "watchpoint arm failed", "detail": error.GetCString()})
        return False

    state["armed"] = {
        "thread_id": frame.GetThread().GetThreadID(),
        "rbp": rbp,
        "gate_index": gate_index,
        "record_begin": record_begin,
        "record_offset": record_offset,
        "triple_addr": triple_addr,
        "z_addr": z_addr,
        "z_at_arm": value,
        "registers": _registers(frame),
        "stack": _stack(frame.GetThread()),
    }
    state["last_hex"] = value["hex"]
    state["watchpoint_id"] = watchpoint.GetID()
    state["counts"]["watchpoints_armed"] += 1
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def install(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    before = target.GetNumBreakpoints()
    debugger.HandleCommand(f"breakpoint set --shlib libcp.dylib --address 0x{ARM_SITE:x}")
    if target.GetNumBreakpoints() <= before:
        state["errors"].append({"error": "arm breakpoint not created"})
        return
    breakpoint = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
    breakpoint.SetScriptCallbackFunction("prefusion_20ca00_record_z_watch_probe.arm_hit")
    state["breakpoint_id"] = breakpoint.GetID()
    print("L16_PREFUSION_20CA00_RECORD_Z_WATCH_INSTALLED", breakpoint.GetID())


def _record_watchpoint_stop(debugger):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    thread = process.GetSelectedThread()
    if not thread or not thread.IsValid() or thread.GetStopReason() != lldb.eStopReasonWatchpoint:
        return
    wp_id = thread.GetStopReasonDataAtIndex(0) if thread.GetStopReasonDataCount() else None
    if wp_id != state["watchpoint_id"]:
        state["errors"].append({"error": "unexpected watchpoint", "watchpoint_id": wp_id})
        return
    frame = thread.GetFrameAtIndex(0)
    current = _f32(process, state["armed"]["z_addr"])
    previous_hex = state["last_hex"]
    changed = current.get("hex") != previous_hex if current.get("read_ok") else None
    state["samples"].append(
        sample := {
            "ordinal": state["counts"]["watchpoint_hits"] + 1,
            "watchpoint_id": wp_id,
            "thread_id": thread.GetThreadID(),
            "pc": frame.GetPC(),
            "libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
            "previous_hex": previous_hex,
            "z_now": current,
            "changed": changed,
            "registers": _registers(frame),
            "stack": _stack(thread),
        }
    )
    if (
        sample.get("libcp_va") == SCORE_RECORD_Z_COMPARE
        and state.get("branch_trace_limit", 0) > 0
        and state["counts"]["record_z_branch_traces"] < state["branch_trace_limit"]
    ):
        sample["record_z_branch_trace"] = _trace_score_record_z_gate(thread, sample)
        sample["pc_after_record_z_branch_trace"] = _pc_va(thread)
    state["counts"]["watchpoint_hits"] += 1
    if changed is True:
        state["counts"]["value_changes"] += 1
    elif changed is False:
        state["counts"]["value_unchanged"] += 1
    if current.get("read_ok"):
        state["last_hex"] = current["hex"]
    if state["counts"]["watchpoint_hits"] >= state["hit_cap"]:
        watchpoint = process.GetTarget().FindWatchpointByID(state["watchpoint_id"])
        if watchpoint and watchpoint.IsValid():
            watchpoint.SetEnabled(False)


def drive_until_exit_or_step_cap(debugger):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process and process.IsValid() and process.GetState() != lldb.eStateExited:
        if steps >= state["step_cap"]:
            state["drive_hit_step_cap"] = True
            break
        steps += 1
        _record_watchpoint_stop(debugger)
        process.Continue()
    state["drive_steps"] = steps
    if process and process.IsValid():
        state["process_state"] = int(process.GetState())
        state["process_exit_status"] = process.GetExitStatus()
    print("L16_PREFUSION_20CA00_RECORD_Z_WATCH_DRIVE_STEPS", steps)


def payload(debugger):
    state = dict(_state())
    state.pop("last_hex", None)
    process = debugger.GetSelectedTarget().GetProcess()
    if process and process.IsValid():
        state["process_state"] = int(process.GetState())
        state["process_exit_status"] = process.GetExitStatus()
    return state


def report_to_file(debugger, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("WROTE", path)
