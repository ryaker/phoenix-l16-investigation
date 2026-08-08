"""Capture raw G-42 cost, normalized cost, and first G-43 consumption."""

import builtins
import json
import struct

import lldb


SITES = {
    0x2773E1: "after_g42",
    0x277567: "after_normalize",
    0x2779B0: "sgm_recurrence",
}


def reset(label, source_lri):
    builtins.l16_sgm_cost_input = {
        "label": label,
        "source_lri": source_lri,
        "events": [],
        "errors": [],
        "capture_complete": False,
    }


def _state():
    return builtins.l16_sgm_cost_input


def _u64(process, address):
    error = lldb.SBError()
    value = process.ReadUnsignedFromMemory(address, 8, error)
    if not error.Success():
        raise RuntimeError(f"read u64 0x{address:x}: {error}")
    return value


def _u32(process, address):
    error = lldb.SBError()
    value = process.ReadUnsignedFromMemory(address, 4, error)
    if not error.Success():
        raise RuntimeError(f"read u32 0x{address:x}: {error}")
    return value


def _f32(process, address):
    error = lldb.SBError()
    data = process.ReadMemory(address, 4, error)
    if not error.Success():
        raise RuntimeError(f"read f32 0x{address:x}: {error}")
    return struct.unpack("<f", data)[0]


def _u16s(process, address, count):
    error = lldb.SBError()
    data = process.ReadMemory(address, 2 * count, error)
    if not error.Success() or len(data) != 2 * count:
        raise RuntimeError(f"read {count} u16 at 0x{address:x}: {error}")
    return list(struct.unpack(f"<{count}H", data))


def _event(frame, name):
    process = frame.GetThread().GetProcess()
    rbp = frame.FindRegister("rbp").GetValueAsUnsigned()
    thread_id = frame.GetThread().GetThreadID()
    return process, rbp, thread_id, {
        "site": name,
        "thread_id": thread_id,
        "rbp": rbp,
    }


def on_breakpoint(frame, _bp_loc, _dict):
    state = _state()
    name = SITES.get(frame.GetPCAddress().GetLoadAddress(frame.GetThread().GetProcess().GetTarget()) - _module_slide(frame))
    if name is None:
        return False
    try:
        process, rbp, thread_id, event = _event(frame, name)
        if name == "after_g42":
            if any(item["site"] == "after_g42" for item in state["events"]):
                return False
            temp = _u64(process, rbp - 0x2E0)
            count = frame.FindRegister("r12").GetValueAsUnsigned()
            projection_begin = _u64(process, rbp - 0x138)
            projection_end = _u64(process, rbp - 0x130)
            projection_count = (projection_end - projection_begin) // 0x50
            capture_count = min(max(count, 8), 256)
            event.update(
                {
                    "temp": temp,
                    "count_r12": count,
                    "capture_count": capture_count,
                    "projection_count": projection_count,
                    "factor": _f32(process, rbp - 0x2E4),
                    "cost_u16": _u16s(process, temp, capture_count),
                }
            )
            state["target_thread"] = thread_id
            state["target_rbp"] = rbp
            state["temp"] = temp
            state["events"].append(event)
            return False

        if thread_id != state.get("target_thread") or rbp != state.get("target_rbp"):
            return False
        raw = next(item for item in state["events"] if item["site"] == "after_g42")
        if name == "after_normalize":
            if any(item["site"] == name for item in state["events"]):
                return False
            event.update(
                {
                    "temp": state["temp"],
                    "cost_u16": _u16s(process, state["temp"], raw["capture_count"]),
                }
            )
            state["events"].append(event)
            return False

        if name == "sgm_recurrence":
            if not any(item["site"] == "after_normalize" for item in state["events"]):
                return False
            r10 = frame.FindRegister("r10").GetValueAsUnsigned()
            rdx = frame.FindRegister("rdx").GetValueAsUnsigned()
            event.update(
                {
                    "r10": r10,
                    "rdx": rdx,
                    "r10_is_temp": r10 == state["temp"],
                    "local_cost_lanes": _u16s(process, r10 + 2 * rdx, 8),
                }
            )
            state["events"].append(event)
            state["capture_complete"] = True
            process.Kill()
    except Exception as exc:
        state["errors"].append(f"{name}: {exc}")
    return False


def _module_slide(frame):
    target = frame.GetThread().GetProcess().GetTarget()
    module = target.FindModule(lldb.SBFileSpec("libcp.dylib"))
    return module.GetObjectFileHeaderAddress().GetLoadAddress(target)


def attach(debugger):
    target = debugger.GetSelectedTarget()
    for breakpoint in target.breakpoint_iter():
        breakpoint.SetScriptCallbackFunction("sgm_cost_input_probe.on_breakpoint")
    print("SGM_COST_INPUT_ATTACHED", target.GetNumBreakpoints())


def write_report(debugger, path):
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    state["process"] = {
        "state": int(process.GetState()),
        "exit_status": process.GetExitStatus(),
    }
    for key in ("target_thread", "target_rbp", "temp"):
        state.pop(key, None)
    with open(path, "w", encoding="ascii") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("SGM_COST_INPUT_REPORT", path, state["capture_complete"], state["errors"])
