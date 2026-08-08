import builtins
import json
import os
import struct


MUTATION_AFTER = 0x3C90A9
KEY15 = 15


def reset(label="", force_enabled=False):
    builtins.l16_c6_is_enabled_differential = {
        "label": label,
        "force_enabled": bool(force_enabled),
        "breakpoint_id": None,
        "mutation_after_hits": 0,
        "key15_hits": 0,
        "transactions": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_c6_is_enabled_differential"):
        reset()
    return builtins.l16_c6_is_enabled_differential


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u8(process, address):
    data = _read(process, address, 1)
    return data[0] if data is not None else None


def _u32(process, address):
    data = _read(process, address, 4)
    return struct.unpack("<I", data)[0] if data is not None else None


def _u64(process, address):
    data = _read(process, address, 8)
    return struct.unpack("<Q", data)[0] if data is not None else None


def install(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    before = target.GetNumBreakpoints()
    debugger.HandleCommand(
        f"breakpoint set --shlib libcp.dylib --address 0x{MUTATION_AFTER:x}"
    )
    if target.GetNumBreakpoints() <= before:
        state["errors"].append({"site": "install", "error": "breakpoint creation"})
        return
    breakpoint = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
    breakpoint.SetScriptCallbackFunction(
        "c6_is_enabled_differential_probe.mutation_after_hit"
    )
    state["breakpoint_id"] = breakpoint.GetID()
    print("C6_IS_ENABLED_DIFFERENTIAL_INSTALLED", breakpoint.GetID())


def mutation_after_hit(frame, bp_loc, _dict):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = frame.GetThread().GetProcess()
    state["mutation_after_hits"] += 1

    slot = _u(frame, "rbx")
    item = _u64(process, slot)
    if not item:
        state["errors"].append({"site": "0x3c90a9", "error": "item pointer read"})
        return False
    key = _u32(process, item + 0x60)
    if key != KEY15:
        return False

    state["key15_hits"] += 1
    transaction = {
        "item": item,
        "key": key,
        "active_before": _u8(process, item + 0x30),
        "force_enabled": state["force_enabled"],
    }
    if state["force_enabled"]:
        error = lldb.SBError()
        count = process.WriteMemory(item + 0x30, b"\x01", error)
        transaction["write_count"] = count
        transaction["write_error"] = None if error.Success() else error.GetCString()
        if not error.Success() or count != 1:
            state["errors"].append(
                {
                    "site": "0x3c90a9",
                    "error": transaction["write_error"] or f"short write {count}",
                }
            )
    transaction["active_after"] = _u8(process, item + 0x30)
    state["transactions"].append(transaction)
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def report_to_file(debugger, path):
    state = dict(_state())
    process = debugger.GetSelectedTarget().GetProcess()
    if process and process.IsValid():
        state["process_exit_status"] = process.GetExitStatus()
        state["process_state"] = int(process.GetState())
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("WROTE", path)
