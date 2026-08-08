import builtins
import json
import struct


def reset(label, profile, report_path):
    builtins.l16_monofusion_mode_selector = {
        "label": label,
        "profile": profile,
        "report_path": report_path,
        "selector_calls": [],
        "constructor_stores": [],
        "worker_modes": [],
        "mode0_calls": 0,
        "mode1_calls": 0,
        "errors": [],
        "_pending": {},
    }


def _state():
    return builtins.l16_monofusion_mode_selector


def _reg(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    raw = process.ReadMemory(address, size, error)
    return raw if error.Success() and len(raw) == size else None


def selector_entry(frame, bp_loc, internal_dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    thread_id = str(frame.GetThread().GetThreadID())
    config = _reg(frame, "r14")
    raw = _read(process, config, 8)
    if raw is None:
        state["errors"].append("selector config unreadable")
        return False
    state["_pending"][thread_id] = {
        "config": config,
        "enum_i32": struct.unpack_from("<i", raw)[0],
        "byte_4": raw[4],
        "raw_8": raw.hex(),
    }
    return False


def selector_return(frame, bp_loc, internal_dict):
    state = _state()
    thread_id = str(frame.GetThread().GetThreadID())
    packet = state["_pending"].pop(thread_id, None)
    if packet is None:
        state["errors"].append("selector return without entry")
        return False
    packet["returned_mode"] = _reg(frame, "rax") & 0xFF
    packet["allocated_object"] = _reg(frame, "r12")
    state["selector_calls"].append(packet)
    return False


def constructor_store(frame, bp_loc, internal_dict):
    state = _state()
    if len(state["constructor_stores"]) < 8:
        state["constructor_stores"].append(
            {
                "object": _reg(frame, "r14"),
                "stored_mode": _reg(frame, "r8") & 0xFF,
            }
        )
    return False


def worker_mode(frame, bp_loc, internal_dict):
    state = _state()
    if len(state["worker_modes"]) < 32:
        process = frame.GetThread().GetProcess()
        obj = _reg(frame, "rbx")
        raw = _read(process, obj, 1)
        state["worker_modes"].append(raw[0] if raw else None)
    return False


def mode0_call(frame, bp_loc, internal_dict):
    _state()["mode0_calls"] += 1
    return False


def mode1_call(frame, bp_loc, internal_dict):
    _state()["mode1_calls"] += 1
    return False


def install(debugger, ids):
    callbacks = {
        ids["selector_entry"]: "mode_selector_probe.selector_entry",
        ids["selector_return"]: "mode_selector_probe.selector_return",
        ids["constructor_store"]: "mode_selector_probe.constructor_store",
        ids["worker_mode"]: "mode_selector_probe.worker_mode",
        ids["mode0_call"]: "mode_selector_probe.mode0_call",
        ids["mode1_call"]: "mode_selector_probe.mode1_call",
    }
    target = debugger.GetSelectedTarget()
    for bp_id, callback in callbacks.items():
        target.FindBreakpointByID(bp_id).SetScriptCallbackFunction(callback)


def report():
    state = _state()
    output = state["report_path"]
    packet = {key: value for key, value in state.items() if not key.startswith("_")}
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(packet, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("MONOFUSION_MODE_SELECTOR_REPORT " + output)
