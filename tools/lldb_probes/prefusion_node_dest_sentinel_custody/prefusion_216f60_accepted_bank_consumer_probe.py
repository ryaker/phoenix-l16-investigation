import builtins
import json
import os
import struct


F33D0_CALL = 0x217BBE
F33D0_RETURN = 0x217BC3
F34E0_CALLS = (0x3F805E, 0x3F85F2)
F34E0_RETURNS = (0x3F8063, 0x3F85F7)
MATERIALIZE_CALLS = {
    0x3F816F: (0x3F805E, 0x00, 0x137C10),
    0x3F81CC: (0x3F805E, 0x24, 0x137C10),
    0x3F8217: (0x3F805E, 0x48, 0x137CF0),
    0x3F8706: (0x3F85F2, 0x00, 0x137C10),
    0x3F8763: (0x3F85F2, 0x24, 0x137C10),
    0x3F87AE: (0x3F85F2, 0x48, 0x137CF0),
}


def reset(label="", watch_hit_cap=64, step_cap=200000):
    builtins.l16_prefusion_216f60_accepted_bank_consumer = {
        "label": label,
        "step_cap": step_cap,
        "watch_hit_cap": watch_hit_cap,
        "breakpoints": {},
        "pending_f33d0": {},
        "pending_f34e0": {},
        "tracked": {},
        "f33d0_calls": [],
        "f33d0_returns": [],
        "f34e0_calls": [],
        "f34e0_returns": [],
        "materialize_calls": [],
        "watchpoint_id": None,
        "watch_armed": None,
        "watch_samples": [],
        "counts": {
            "f33d0_call_hits": 0,
            "f33d0_return_hits": 0,
            "f34e0_call_hits": 0,
            "f34e0_matches": 0,
            "f34e0_return_hits": 0,
            "f34e0_return_matches": 0,
            "materialize_call_hits": 0,
            "materialize_matches": 0,
            "watchpoints_armed": 0,
            "watchpoint_hits": 0,
            "watch_value_changes": 0,
        },
        "errors": [],
        "drive_hit_step_cap": False,
    }


def _state():
    if not hasattr(builtins, "l16_prefusion_216f60_accepted_bank_consumer"):
        reset()
    return builtins.l16_prefusion_216f60_accepted_bank_consumer


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _register(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _module_base(target):
    lldb = builtins.__import__("lldb")
    module = target.FindModule(lldb.SBFileSpec("libcp.dylib"))
    if not module or not module.IsValid():
        return None
    header = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
    if header in (0, (1 << 64) - 1):
        return None
    return header


def _module_va(target, address):
    base = _module_base(target)
    return address - base if base is not None else None


def _thread_frame_key(frame):
    return f"{frame.GetThread().GetThreadID()}:{_register(frame, 'rbp'):x}"


def _thread_key(frame):
    return str(frame.GetThread().GetThreadID())


def _snapshot(process, address, size):
    data = _read(process, address, size)
    return {
        "address": address,
        "size": size,
        "read_ok": data is not None,
        "hex": data.hex() if data is not None else None,
    }


def _stack(thread, limit=12):
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


def f33d0_call_hit(frame, bp_loc, _dict):
    state = _state()
    state["counts"]["f33d0_call_hits"] += 1
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    key = _thread_frame_key(frame)
    packet = {
        "key": key,
        "thread_id": frame.GetThread().GetThreadID(),
        "rbp": _register(frame, "rbp"),
        "libcp_va": _module_va(target, frame.GetPC()),
        "destination": _register(frame, "rdi"),
        "selector": _register(frame, "r8") & 0xFFFFFFFF,
        "source_0": _snapshot(process, _register(frame, "rsi"), 0x24),
        "source_1": _snapshot(process, _register(frame, "rdx"), 0x24),
        "source_2": _snapshot(process, _register(frame, "rcx"), 0x0C),
    }
    state["pending_f33d0"][key] = packet
    state["f33d0_calls"].append(packet)
    return False


def f33d0_return_hit(frame, bp_loc, _dict):
    state = _state()
    state["counts"]["f33d0_return_hits"] += 1
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    key = _thread_frame_key(frame)
    call = state["pending_f33d0"].pop(key, None)
    if call is None:
        state["errors"].append({"error": "unmatched f33d0 return", "key": key})
        return False
    destination = call["destination"]
    bank = destination + 0x12C
    packet = {
        "key": key,
        "thread_id": frame.GetThread().GetThreadID(),
        "libcp_va": _module_va(target, frame.GetPC()),
        "destination": destination,
        "bank": bank,
        "bank_snapshot": _snapshot(process, bank, 0x54),
        "expected_hex": (
            call["source_0"]["hex"] + call["source_1"]["hex"] + call["source_2"]["hex"]
            if call["source_0"]["read_ok"]
            and call["source_1"]["read_ok"]
            and call["source_2"]["read_ok"]
            else None
        ),
    }
    packet["exact_copy_match"] = (
        packet["expected_hex"] is not None
        and packet["bank_snapshot"]["hex"] == packet["expected_hex"]
    )
    state["tracked"][str(destination)] = {
        "destination": destination,
        "bank": bank,
        "exact_copy_match": packet["exact_copy_match"],
        "f34e0_matches": 0,
        "materialize_matches": 0,
    }
    if state["watchpoint_id"] is None:
        lldb = builtins.__import__("lldb")
        error = lldb.SBError()
        watchpoint = target.WatchAddress(bank, 8, True, True, error)
        if not error.Success() or not watchpoint or not watchpoint.IsValid():
            state["errors"].append(
                {"error": "accepted-bank watchpoint arm failed", "detail": error.GetCString()}
            )
        else:
            state["watchpoint_id"] = watchpoint.GetID()
            state["watch_armed"] = {
                "destination": destination,
                "bank": bank,
                "watch_address": bank,
                "watch_size": 8,
                "value_at_arm": _snapshot(process, bank, 8),
            }
            state["counts"]["watchpoints_armed"] += 1
    state["f33d0_returns"].append(packet)
    return False


def f34e0_call_hit(frame, bp_loc, _dict):
    state = _state()
    state["counts"]["f34e0_call_hits"] += 1
    destination = _register(frame, "rdi")
    tracked = state["tracked"].get(str(destination))
    if tracked is None:
        return False
    state["counts"]["f34e0_matches"] += 1
    tracked["f34e0_matches"] += 1
    callsite = _module_va(frame.GetThread().GetProcess().GetTarget(), frame.GetPC())
    packet = {
        "thread_id": frame.GetThread().GetThreadID(),
        "callsite": callsite,
        "destination": destination,
        "selector": _register(frame, "rsi") & 0xFFFFFFFF,
        "expected_bank": tracked["bank"],
    }
    state["pending_f34e0"][_thread_key(frame)] = packet
    state["f34e0_calls"].append(packet)
    return False


def f34e0_return_hit(frame, bp_loc, _dict):
    state = _state()
    state["counts"]["f34e0_return_hits"] += 1
    pending = state["pending_f34e0"].pop(_thread_key(frame), None)
    if pending is None:
        return False
    state["counts"]["f34e0_return_matches"] += 1
    packet = {
        **pending,
        "return_site": _module_va(frame.GetThread().GetProcess().GetTarget(), frame.GetPC()),
        "returned_bank": _register(frame, "rax"),
    }
    packet["bank_match"] = packet["returned_bank"] == packet["expected_bank"]
    state["f34e0_returns"].append(packet)
    return False


def materialize_call_hit(frame, bp_loc, _dict):
    state = _state()
    state["counts"]["materialize_call_hits"] += 1
    process = frame.GetThread().GetProcess()
    callsite = _module_va(process.GetTarget(), frame.GetPC())
    source = _register(frame, "rsi")
    match = None
    for tracked in state["tracked"].values():
        for expected_callsite, (_origin, offset, target) in MATERIALIZE_CALLS.items():
            if callsite == expected_callsite and source == tracked["bank"] + offset:
                match = (tracked, offset, target)
                break
        if match is not None:
            break
    if match is None:
        return False
    tracked, offset, target = match
    state["counts"]["materialize_matches"] += 1
    tracked["materialize_matches"] += 1
    packet = {
        "thread_id": frame.GetThread().GetThreadID(),
        "callsite": callsite,
        "target": target,
        "destination_object": tracked["destination"],
        "bank": tracked["bank"],
        "source": source,
        "bank_offset": offset,
        "rdi": _register(frame, "rdi"),
        "source_snapshot": _snapshot(process, source, 12 if offset == 0x48 else 0x24),
    }
    state["materialize_calls"].append(packet)
    return False


def _add_breakpoint(debugger, name, address, callback):
    state = _state()
    target = debugger.GetSelectedTarget()
    before = target.GetNumBreakpoints()
    debugger.HandleCommand(f"breakpoint set --shlib libcp.dylib --address 0x{address:x}")
    if target.GetNumBreakpoints() <= before:
        state["errors"].append({"error": "breakpoint not created", "name": name, "address": address})
        return
    breakpoint = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
    breakpoint.SetScriptCallbackFunction(callback)
    state["breakpoints"][name] = breakpoint.GetID()


def install(debugger):
    _add_breakpoint(
        debugger,
        "f33d0_call",
        F33D0_CALL,
        "prefusion_216f60_accepted_bank_consumer_probe.f33d0_call_hit",
    )
    _add_breakpoint(
        debugger,
        "f33d0_return",
        F33D0_RETURN,
        "prefusion_216f60_accepted_bank_consumer_probe.f33d0_return_hit",
    )
    for address in F34E0_CALLS:
        _add_breakpoint(
            debugger,
            f"f34e0_call_{address:x}",
            address,
            "prefusion_216f60_accepted_bank_consumer_probe.f34e0_call_hit",
        )
    for address in F34E0_RETURNS:
        _add_breakpoint(
            debugger,
            f"f34e0_return_{address:x}",
            address,
            "prefusion_216f60_accepted_bank_consumer_probe.f34e0_return_hit",
        )
    for address in MATERIALIZE_CALLS:
        _add_breakpoint(
            debugger,
            f"materialize_{address:x}",
            address,
            "prefusion_216f60_accepted_bank_consumer_probe.materialize_call_hit",
        )
    print("L16_PREFUSION_216F60_ACCEPTED_BANK_CONSUMER_INSTALLED", _state()["breakpoints"])


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
        thread = process.GetSelectedThread()
        if (
            thread
            and thread.IsValid()
            and thread.GetStopReason() == lldb.eStopReasonWatchpoint
        ):
            wp_id = (
                thread.GetStopReasonDataAtIndex(0)
                if thread.GetStopReasonDataCount()
                else None
            )
            if wp_id != state["watchpoint_id"]:
                state["errors"].append(
                    {"error": "unexpected watchpoint stop", "watchpoint_id": wp_id}
                )
            else:
                frame = thread.GetFrameAtIndex(0)
                armed = state["watch_armed"]
                before = (
                    state["watch_samples"][-1]["value_now"]
                    if state["watch_samples"]
                    else armed["value_at_arm"]
                )
                now = _snapshot(process, armed["watch_address"], 8)
                changed = now["hex"] != before["hex"]
                state["watch_samples"].append(
                    {
                        "ordinal": state["counts"]["watchpoint_hits"] + 1,
                        "thread_id": thread.GetThreadID(),
                        "pc": frame.GetPC(),
                        "libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
                        "value_before": before,
                        "value_now": now,
                        "changed": changed,
                        "stack": _stack(thread),
                    }
                )
                state["counts"]["watchpoint_hits"] += 1
                if changed:
                    state["counts"]["watch_value_changes"] += 1
                if state["counts"]["watchpoint_hits"] >= state["watch_hit_cap"]:
                    watchpoint = process.GetTarget().FindWatchpointByID(
                        state["watchpoint_id"]
                    )
                    if watchpoint and watchpoint.IsValid():
                        watchpoint.SetEnabled(False)
        process.Continue()
    state["drive_steps"] = steps
    if process and process.IsValid():
        state["process_state"] = int(process.GetState())
        state["process_exit_status"] = process.GetExitStatus()
    print("L16_PREFUSION_216F60_ACCEPTED_BANK_CONSUMER_DRIVE_STEPS", steps)


def payload(debugger):
    state = _state()
    packet = dict(state)
    packet["pending_f33d0"] = list(state["pending_f33d0"])
    packet["pending_f34e0"] = list(state["pending_f34e0"])
    packet["tracked"] = list(state["tracked"].values())
    process = debugger.GetSelectedTarget().GetProcess()
    if process and process.IsValid():
        packet["process_state"] = int(process.GetState())
        packet["process_exit_status"] = process.GetExitStatus()
    return packet


def report_to_file(debugger, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("WROTE", path)
