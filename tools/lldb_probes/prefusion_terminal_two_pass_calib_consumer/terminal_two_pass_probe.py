import builtins
import json
import os


HELPER_ENTRY = 0x23C5F0
NORMALIZED_F33D0_CALL = 0x23D38D
NORMALIZED_F33D0_RETURN = 0x23D392
ASSEMBLY_CALLS = (0x23C6C0, 0x23CBA6, 0x23D226)
FIRST_HELPER_RETURN = 0x22E249
SECOND_HELPER_RETURN = 0x22E288

TERMINAL_CALLERS = {
    FIRST_HELPER_RETURN: 1,
    SECOND_HELPER_RETURN: 2,
}


def reset(label="", step_cap=200000):
    builtins.l16_terminal_two_pass = {
        "label": label,
        "step_cap": step_cap,
        "breakpoints": {},
        "active_by_thread": {},
        "pending_write_by_thread": {},
        "helper_entries": [],
        "helper_returns": [],
        "normalized_writes": [],
        "assembly_reads": [],
        "second_entry_snapshots": [],
        "counts": {
            "terminal_helper_entries": 0,
            "terminal_helper_returns": 0,
            "normalized_write_calls": 0,
            "normalized_write_returns": 0,
            "assembly_reads": 0,
            "second_pass_exact_first_write_reads": 0,
        },
        "errors": [],
        "drive_hit_step_cap": False,
    }


def _state():
    if not hasattr(builtins, "l16_terminal_two_pass"):
        reset()
    return builtins.l16_terminal_two_pass


def _register(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _module_base(target):
    lldb = builtins.__import__("lldb")
    module = target.FindModule(lldb.SBFileSpec("libcp.dylib"))
    if not module or not module.IsValid():
        return None
    base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
    if base in (0, (1 << 64) - 1):
        return None
    return base


def _module_va(target, address):
    base = _module_base(target)
    return address - base if base is not None else None


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _snapshot(process, address, size):
    data = _read(process, address, size)
    return {
        "address": address,
        "size": size,
        "read_ok": data is not None,
        "hex": data.hex() if data is not None else None,
    }


def _thread_id(frame):
    return frame.GetThread().GetThreadID()


def _stack(frame, limit=6):
    thread = frame.GetThread()
    target = thread.GetProcess().GetTarget()
    rows = []
    for index in range(min(thread.GetNumFrames(), limit)):
        item = thread.GetFrameAtIndex(index)
        rows.append(
            {
                "index": index,
                "pc": item.GetPC(),
                "libcp_va": _module_va(target, item.GetPC()),
                "function": item.GetFunctionName(),
            }
        )
    return rows


def _first_write_for_object(state, object_address):
    matches = [
        item
        for item in state["normalized_writes"]
        if item["call_ordinal"] == 1
        and item["destination_object"] == object_address
        and item.get("bank_after", {}).get("read_ok")
    ]
    return matches[-1] if matches else None


def _set_breakpoints_enabled(target, names, enabled):
    state = _state()
    for name in names:
        breakpoint = target.FindBreakpointByID(state["breakpoints"][name])
        if breakpoint and breakpoint.IsValid():
            breakpoint.SetEnabled(enabled)


def helper_entry_hit(frame, _bp_loc, _dict):
    state = _state()
    thread = frame.GetThread()
    target = thread.GetProcess().GetTarget()
    caller = thread.GetFrameAtIndex(1)
    caller_va = _module_va(target, caller.GetPC())
    ordinal = TERMINAL_CALLERS.get(caller_va)
    if ordinal is None:
        return False

    tid = _thread_id(frame)
    process = thread.GetProcess()
    packet = {
        "call_ordinal": ordinal,
        "thread_id": tid,
        "helper_rbp": _register(frame, "rbp"),
        "caller_libcp_va": caller_va,
        "arg_rdi": _register(frame, "rdi"),
        "arg_rsi": _register(frame, "rsi"),
        "arg_rdx": _register(frame, "rdx"),
        "arg_rcx": _register(frame, "rcx"),
        "arg_r8": _register(frame, "r8") & 0xFFFFFFFF,
        "arg_r9": _register(frame, "r9") & 0xFFFFFFFF,
        "stack": _stack(frame),
    }
    state["active_by_thread"][str(tid)] = packet
    state["helper_entries"].append(packet)
    state["counts"]["terminal_helper_entries"] += 1
    _set_breakpoints_enabled(
        target,
        (
            "normalized_f33d0_call",
            "normalized_f33d0_return",
            "assembly_call_23c6c0",
            "assembly_call_23cba6",
            "assembly_call_23d226",
        ),
        True,
    )

    if ordinal == 2:
        for write in state["normalized_writes"]:
            if write["call_ordinal"] != 1 or not write.get("bank_after", {}).get("read_ok"):
                continue
            address = write["destination_object"] + 0x12C
            now = _snapshot(process, address, 0x54)
            state["second_entry_snapshots"].append(
                {
                    "destination_object": write["destination_object"],
                    "key": write["destination_key"],
                    "first_write_bank_after": write["bank_after"],
                    "bank_at_second_entry": now,
                    "exact_match": now["hex"] == write["bank_after"]["hex"],
                }
            )
    return False


def normalized_f33d0_call_hit(frame, _bp_loc, _dict):
    state = _state()
    tid = _thread_id(frame)
    active = state["active_by_thread"].get(str(tid))
    if active is None or active["helper_rbp"] != _register(frame, "rbp"):
        return False

    process = frame.GetThread().GetProcess()
    destination = _register(frame, "rdi")
    source_0 = _snapshot(process, _register(frame, "rsi"), 0x24)
    source_1 = _snapshot(process, _register(frame, "rdx"), 0x24)
    source_2 = _snapshot(process, _register(frame, "rcx"), 0x0C)
    packet = {
        "call_ordinal": active["call_ordinal"],
        "thread_id": tid,
        "helper_rbp": active["helper_rbp"],
        "destination_object": destination,
        "destination_key": _snapshot(process, destination + 0x60, 4),
        "local_key": _snapshot(process, _register(frame, "rbp") - 0x4E0, 4),
        "selector": _register(frame, "r8") & 0xFFFFFFFF,
        "source_0": source_0,
        "source_1": source_1,
        "source_2": source_2,
        "expected_bank_hex": source_0["hex"] + source_1["hex"] + source_2["hex"],
        "bank_before": _snapshot(process, destination + 0x12C, 0x54),
        "stack": _stack(frame),
    }
    state["pending_write_by_thread"][str(tid)] = packet
    state["counts"]["normalized_write_calls"] += 1
    return False


def normalized_f33d0_return_hit(frame, _bp_loc, _dict):
    state = _state()
    tid = _thread_id(frame)
    packet = state["pending_write_by_thread"].pop(str(tid), None)
    if packet is None or packet["helper_rbp"] != _register(frame, "rbp"):
        return False

    process = frame.GetThread().GetProcess()
    packet["bank_after"] = _snapshot(
        process, packet["destination_object"] + 0x12C, 0x54
    )
    packet["exact_source_copy"] = (
        packet["bank_after"]["hex"] == packet["expected_bank_hex"]
    )
    packet["changed"] = (
        packet["bank_before"]["hex"] != packet["bank_after"]["hex"]
    )
    state["normalized_writes"].append(packet)
    state["counts"]["normalized_write_returns"] += 1
    return False


def assembly_entry_hit(frame, _bp_loc, _dict):
    state = _state()
    tid = _thread_id(frame)
    active = state["active_by_thread"].get(str(tid))
    if active is None:
        return False

    process = frame.GetThread().GetProcess()
    source_object = _register(frame, "rsi")
    source_bank = _snapshot(process, source_object + 0x12C, 0x54)
    first_write = _first_write_for_object(state, source_object)
    exact_first_write = bool(
        active["call_ordinal"] == 2
        and first_write is not None
        and source_bank["hex"] == first_write["bank_after"]["hex"]
    )
    packet = {
        "call_ordinal": active["call_ordinal"],
        "thread_id": tid,
        "helper_rbp": active["helper_rbp"],
        "callsite_libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
        "output_record": _register(frame, "rdi"),
        "source_object": source_object,
        "source_key": _snapshot(process, source_object + 0x60, 4),
        "selector": 1,
        "source_bank": source_bank,
        "matches_first_write": exact_first_write,
        "matched_first_write_key": (
            first_write["destination_key"] if first_write is not None else None
        ),
        "stack": _stack(frame),
    }
    state["assembly_reads"].append(packet)
    state["counts"]["assembly_reads"] += 1
    if exact_first_write:
        state["counts"]["second_pass_exact_first_write_reads"] += 1
    return False


def helper_return_hit(frame, _bp_loc, _dict):
    state = _state()
    tid = _thread_id(frame)
    active = state["active_by_thread"].get(str(tid))
    return_va = _module_va(frame.GetThread().GetProcess().GetTarget(), frame.GetPC())
    ordinal = TERMINAL_CALLERS.get(return_va)
    if active is None or ordinal != active["call_ordinal"]:
        return False

    state["helper_returns"].append(
        {
            "call_ordinal": ordinal,
            "thread_id": tid,
            "return_libcp_va": return_va,
            "tracked_write_count": sum(
                1
                for item in state["normalized_writes"]
                if item["thread_id"] == tid and item["call_ordinal"] == ordinal
            ),
            "tracked_assembly_read_count": sum(
                1
                for item in state["assembly_reads"]
                if item["thread_id"] == tid and item["call_ordinal"] == ordinal
            ),
        }
    )
    state["counts"]["terminal_helper_returns"] += 1
    state["active_by_thread"].pop(str(tid), None)
    _set_breakpoints_enabled(
        frame.GetThread().GetProcess().GetTarget(),
        (
            "normalized_f33d0_call",
            "normalized_f33d0_return",
            "assembly_call_23c6c0",
            "assembly_call_23cba6",
            "assembly_call_23d226",
        ),
        False,
    )
    return False


def _add_breakpoint(debugger, name, address, callback):
    state = _state()
    target = debugger.GetSelectedTarget()
    before = target.GetNumBreakpoints()
    debugger.HandleCommand(
        f"breakpoint set --shlib libcp.dylib --address 0x{address:x}"
    )
    if target.GetNumBreakpoints() <= before:
        state["errors"].append({"error": "breakpoint not created", "name": name})
        return
    breakpoint = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
    breakpoint.SetScriptCallbackFunction(
        f"terminal_two_pass_probe.{callback}"
    )
    state["breakpoints"][name] = breakpoint.GetID()


def install(debugger):
    specs = (
        ("helper_entry", HELPER_ENTRY, "helper_entry_hit"),
        ("normalized_f33d0_call", NORMALIZED_F33D0_CALL, "normalized_f33d0_call_hit"),
        (
            "normalized_f33d0_return",
            NORMALIZED_F33D0_RETURN,
            "normalized_f33d0_return_hit",
        ),
        ("assembly_call_23c6c0", ASSEMBLY_CALLS[0], "assembly_entry_hit"),
        ("assembly_call_23cba6", ASSEMBLY_CALLS[1], "assembly_entry_hit"),
        ("assembly_call_23d226", ASSEMBLY_CALLS[2], "assembly_entry_hit"),
        ("first_helper_return", FIRST_HELPER_RETURN, "helper_return_hit"),
        ("second_helper_return", SECOND_HELPER_RETURN, "helper_return_hit"),
    )
    for name, address, callback in specs:
        _add_breakpoint(debugger, name, address, callback)
    _set_breakpoints_enabled(
        debugger.GetSelectedTarget(),
        (
            "normalized_f33d0_call",
            "normalized_f33d0_return",
            "assembly_call_23c6c0",
            "assembly_call_23cba6",
            "assembly_call_23d226",
        ),
        False,
    )
    print("L16_TERMINAL_TWO_PASS_INSTALLED", _state()["breakpoints"])


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
        process.Continue()
    state["drive_steps"] = steps
    if process and process.IsValid():
        state["process_state"] = int(process.GetState())
        state["process_exit_status"] = process.GetExitStatus()
    print("L16_TERMINAL_TWO_PASS_DRIVE_STEPS", steps)


def payload(debugger):
    state = _state()
    packet = dict(state)
    packet["active_by_thread"] = list(state["active_by_thread"].values())
    packet["pending_write_by_thread"] = list(
        state["pending_write_by_thread"].values()
    )
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
