import builtins
import json
import os
import struct


COMPARE = 0x22D8FB
RETAIN_EXISTING = 0x22D901
MATERIALIZE_CANDIDATE = 0x22D9A0
EXISTING_ENTRY = 0x22DCC3
CANDIDATE_STORE = 0x22DB7C
TRANSFER_CALL = 0x22DF45
TRANSFER_RETURN = 0x22DF4A


def reset(label=""):
    builtins.l16_wide_minimum_selector = {
        "label": label,
        "breakpoints": {},
        "pending": {},
        "events": [],
        "completed_routes": [],
        "counts": {
            "compares": 0,
            "materialize_branches": 0,
            "retain_branches": 0,
            "candidate_stores": 0,
            "existing_entries": 0,
            "transfer_calls": 0,
            "transfer_returns": 0,
        },
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_wide_minimum_selector"):
        reset()
    return builtins.l16_wide_minimum_selector


def _register(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _key(frame):
    return f"{frame.GetThread().GetThreadID()}:{_register(frame, 'rbp'):x}"


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


def _u64(process, address):
    data = _read(process, address, 8)
    return struct.unpack("<Q", data)[0] if data is not None else None


def _module_base(target):
    lldb = builtins.__import__("lldb")
    module = target.FindModule(lldb.SBFileSpec("libcp.dylib"))
    if not module or not module.IsValid():
        return None
    address = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
    return None if address in (0, (1 << 64) - 1) else address


def _va(frame):
    target = frame.GetThread().GetProcess().GetTarget()
    base = _module_base(target)
    return frame.GetPC() - base if base is not None else None


def _disable_when_complete(target):
    state = _state()
    routes = set(state["completed_routes"])
    if routes != {"materialize_candidate", "retain_existing_and_transfer"}:
        return
    for breakpoint_id in state["breakpoints"].values():
        target.FindBreakpointByID(breakpoint_id).SetEnabled(False)


def compare_hit(frame, _bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    key = _key(frame)
    if key in state["pending"]:
        state["errors"].append({"error": "compare replaced pending event", "key": key})
    flags = _register(frame, "rflags")
    node = _register(frame, "r12")
    state["pending"][key] = {
        "thread_id": frame.GetThread().GetThreadID(),
        "rbp": _register(frame, "rbp"),
        "compare_va": _va(frame),
        "candidate_score": _snapshot(process, _register(frame, "rbp") - 0x2A0, 4),
        "existing_node": node,
        "existing_node_key": _snapshot(process, node + 0x20, 4),
        "existing_score": _snapshot(process, node + 0x28, 4),
        "jbe_predicted": bool(flags & 0x1 or flags & 0x40),
    }
    state["counts"]["compares"] += 1
    return False


def materialize_hit(frame, _bp_loc, _dict):
    state = _state()
    event = state["pending"].get(_key(frame))
    if event is None:
        return False
    event["route"] = "materialize_candidate"
    event["route_va"] = _va(frame)
    state["counts"]["materialize_branches"] += 1
    return False


def retain_hit(frame, _bp_loc, _dict):
    state = _state()
    event = state["pending"].get(_key(frame))
    if event is None:
        return False
    event["route"] = "retain_existing_and_transfer"
    event["route_va"] = _va(frame)
    state["counts"]["retain_branches"] += 1
    return False


def existing_entry_hit(frame, _bp_loc, _dict):
    state = _state()
    event = state["pending"].get(_key(frame))
    if event is None or event.get("route") != "retain_existing_and_transfer":
        return False
    event["existing_entry_va"] = _va(frame)
    event["selected_node"] = _register(frame, "rbx")
    state["counts"]["existing_entries"] += 1
    return False


def candidate_store_hit(frame, _bp_loc, _dict):
    state = _state()
    key = _key(frame)
    event = state["pending"].get(key)
    if event is None or event.get("route") != "materialize_candidate":
        return False
    process = frame.GetThread().GetProcess()
    node = _register(frame, "r15")
    event["effect_va"] = _va(frame)
    event["destination_node"] = node
    event["destination_node_key"] = _snapshot(process, node + 0x20, 4)
    event["stored_score"] = _snapshot(process, node + 0x28, 4)
    event["candidate_source_object"] = _u64(process, _register(frame, "rbp") - 0x280)
    if event["candidate_source_object"] is not None:
        event["candidate_source_object_id"] = _snapshot(
            process, event["candidate_source_object"] + 0x60, 4
        )
    state["counts"]["candidate_stores"] += 1
    state["events"].append(event)
    state["completed_routes"].append(event["route"])
    del state["pending"][key]
    _disable_when_complete(process.GetTarget())
    return False


def transfer_call_hit(frame, _bp_loc, _dict):
    state = _state()
    event = state["pending"].get(_key(frame))
    if event is None or event.get("route") != "retain_existing_and_transfer":
        return False
    process = frame.GetThread().GetProcess()
    node = _u64(process, _register(frame, "rbp") - 0x2C0)
    destination = _register(frame, "rdi")
    event["transfer_call_va"] = _va(frame)
    event["selected_node_local"] = node
    event["destination_object"] = destination
    event["destination_object_id"] = _snapshot(process, destination + 0x60, 4)
    event["selector"] = _register(frame, "r8") & 0xFFFFFFFF
    event["source_addresses"] = [
        _register(frame, "rsi"),
        _register(frame, "rdx"),
        _register(frame, "rcx"),
    ]
    event["source_0"] = _snapshot(process, _register(frame, "rsi"), 0x24)
    event["source_1"] = _snapshot(process, _register(frame, "rdx"), 0x24)
    event["source_2"] = _snapshot(process, _register(frame, "rcx"), 0x0C)
    event["bank_before"] = _snapshot(process, destination + 0x12C, 0x54)
    state["counts"]["transfer_calls"] += 1
    return False


def transfer_return_hit(frame, _bp_loc, _dict):
    state = _state()
    key = _key(frame)
    event = state["pending"].get(key)
    if event is None or "destination_object" not in event:
        return False
    process = frame.GetThread().GetProcess()
    event["effect_va"] = _va(frame)
    event["bank_after"] = _snapshot(
        process, event["destination_object"] + 0x12C, 0x54
    )
    state["counts"]["transfer_returns"] += 1
    state["events"].append(event)
    state["completed_routes"].append(event["route"])
    del state["pending"][key]
    _disable_when_complete(process.GetTarget())
    return False


def _add(debugger, name, address, callback):
    target = debugger.GetSelectedTarget()
    before = target.GetNumBreakpoints()
    debugger.HandleCommand(f"breakpoint set --shlib libcp.dylib --address 0x{address:x}")
    if target.GetNumBreakpoints() <= before:
        _state()["errors"].append({"error": "breakpoint not created", "name": name})
        return
    breakpoint = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
    breakpoint.SetScriptCallbackFunction(
        f"wide_minimum_selector_probe.{callback}"
    )
    _state()["breakpoints"][name] = breakpoint.GetID()


def install(debugger):
    for name, address, callback in (
        ("compare", COMPARE, "compare_hit"),
        ("retain", RETAIN_EXISTING, "retain_hit"),
        ("materialize", MATERIALIZE_CANDIDATE, "materialize_hit"),
        ("existing_entry", EXISTING_ENTRY, "existing_entry_hit"),
        ("candidate_store", CANDIDATE_STORE, "candidate_store_hit"),
        ("transfer_call", TRANSFER_CALL, "transfer_call_hit"),
        ("transfer_return", TRANSFER_RETURN, "transfer_return_hit"),
    ):
        _add(debugger, name, address, callback)


def report_to_file(debugger, path):
    state = dict(_state())
    process = debugger.GetSelectedTarget().GetProcess()
    state["pending"] = list(state["pending"].values())
    state["process_state"] = int(process.GetState()) if process.IsValid() else None
    state["process_exit_status"] = (
        process.GetExitStatus() if process.IsValid() else None
    )
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("WROTE", path)
