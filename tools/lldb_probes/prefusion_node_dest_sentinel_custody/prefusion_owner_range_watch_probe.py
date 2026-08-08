import builtins
import json
import os
import struct


ARM_SITE = 0x20C4BA


def reset(label="", hit_cap=512, step_cap=10000):
    builtins.l16_prefusion_owner_range_watch = {
        "label": label,
        "hit_cap": hit_cap,
        "step_cap": step_cap,
        "breakpoint_id": None,
        "watchpoint_id": None,
        "owner": None,
        "watch_addr": None,
        "range_at_arm": None,
        "last_hex": None,
        "samples": [],
        "counts": {
            "arm_hits": 0,
            "watchpoints_armed": 0,
            "watchpoint_hits": 0,
            "value_changes": 0,
            "value_unchanged": 0,
        },
        "errors": [],
        "drive_hit_step_cap": False,
    }


def _state():
    if not hasattr(builtins, "l16_prefusion_owner_range_watch"):
        reset()
    return builtins.l16_prefusion_owner_range_watch


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _range(process, address):
    data = _read(process, address, 8)
    if data is None:
        return {"addr": address, "read_ok": False}
    low, high = struct.unpack("<2f", data)
    return {
        "addr": address,
        "read_ok": True,
        "low": low,
        "high": high,
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
    names = ("rax", "rbx", "rcx", "rdx", "rsi", "rdi", "r8", "r9", "r15", "rbp", "rsp")
    return {name: frame.FindRegister(name).GetValueAsUnsigned() for name in names}


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


def arm_hit(frame, bp_loc, _dict):
    lldb = builtins.__import__("lldb")
    state = _state()
    if state["watchpoint_id"] is not None:
        return False
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    owner = frame.FindRegister("r15").GetValueAsUnsigned()
    watch_addr = owner + 0x78
    packet = _range(process, watch_addr)
    state["counts"]["arm_hits"] += 1
    if not packet["read_ok"]:
        state["errors"].append({"error": "owner range unreadable", "owner": owner})
        return False

    error = lldb.SBError()
    watchpoint = target.WatchAddress(watch_addr, 8, True, True, error)
    if not error.Success() or not watchpoint or not watchpoint.IsValid():
        state["errors"].append({"error": "watchpoint arm failed", "detail": error.GetCString()})
        return False

    state["owner"] = owner
    state["watch_addr"] = watch_addr
    state["range_at_arm"] = packet
    state["last_hex"] = packet["hex"]
    state["watchpoint_id"] = watchpoint.GetID()
    state["counts"]["watchpoints_armed"] += 1
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def install(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    before = target.GetNumBreakpoints()
    debugger.HandleCommand(f"breakpoint set --shlib libcp.dylib --address 0x{ARM_SITE:x}")
    require = target.GetNumBreakpoints() > before
    if not require:
        state["errors"].append({"error": "arm breakpoint not created"})
        return
    breakpoint = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
    breakpoint.SetScriptCallbackFunction("prefusion_owner_range_watch_probe.arm_hit")
    state["breakpoint_id"] = breakpoint.GetID()
    print("L16_PREFUSION_OWNER_RANGE_WATCH_INSTALLED", breakpoint.GetID())


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
    current = _range(process, state["watch_addr"])
    previous_hex = state["last_hex"]
    changed = current.get("hex") != previous_hex if current.get("read_ok") else None
    sample = {
        "ordinal": state["counts"]["watchpoint_hits"] + 1,
        "watchpoint_id": wp_id,
        "thread_id": thread.GetThreadID(),
        "pc": frame.GetPC(),
        "libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
        "previous_hex": previous_hex,
        "range_now": current,
        "changed": changed,
        "registers": _registers(frame),
        "stack": _stack(thread),
    }
    state["samples"].append(sample)
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
    print("L16_PREFUSION_OWNER_RANGE_WATCH_DRIVE_STEPS", steps)


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
