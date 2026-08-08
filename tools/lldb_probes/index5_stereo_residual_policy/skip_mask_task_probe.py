import builtins
import json
import struct


MASK_ENTRY_VA = 0x26DB40
RANDOM_WORKER_VA = 0x28FED0
EXPECTED_UNIQUE_TASKS = 768


def reset(label=""):
    builtins.l16_skip_mask_tasks = {
        "label": label,
        "mask_entries": [],
        "worker_breakpoint_id": None,
        "worker_tasks": [],
        "terminated_after_capture": False,
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_skip_mask_tasks"):
        reset()
    return builtins.l16_skip_mask_tasks


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    if not addr:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u32(process, addr):
    data = _read(process, addr, 4)
    return struct.unpack("<I", data)[0] if data is not None else None


def _u64(process, addr):
    data = _read(process, addr, 8)
    return struct.unpack("<Q", data)[0] if data is not None else None


def _rect(process, addr):
    data = _read(process, addr, 16)
    return list(struct.unpack("<4i", data)) if data is not None else None


def _libcp_base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                return base
    return None


def _module_va(target, pc):
    base = _libcp_base(target)
    return pc - base if base is not None and pc >= base else None


def _install_worker(target):
    state = _state()
    if state["worker_breakpoint_id"] is not None:
        return
    base = _libcp_base(target)
    if base is None:
        state["errors"].append("libcp base unavailable")
        return
    bp = target.BreakpointCreateByAddress(base + RANDOM_WORKER_VA)
    if not bp or not bp.IsValid():
        state["errors"].append("random-worker breakpoint creation failed")
        return
    bp.SetScriptCallbackFunction("skip_mask_task_probe.hit")
    state["worker_breakpoint_id"] = bp.GetID()


def hit(frame, bp_loc, _dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    site = _module_va(target, frame.GetPC())

    if site == MASK_ENTRY_VA:
        obj = _u(frame, "rsi")
        packet = {
            "object": obj,
            "index_0x08": _u32(process, obj + 0x08),
            "sampling_pattern_0x50": _u32(process, obj + 0x50),
            "width_0x2a0": _u32(process, obj + 0x2A0),
            "height_0x2a4": _u32(process, obj + 0x2A4),
        }
        state["mask_entries"].append(packet)
        if packet["index_0x08"] == 5 and packet["sampling_pattern_0x50"] == 2:
            _install_worker(target)
        return False

    if site == RANDOM_WORKER_VA:
        callback = _u(frame, "rdi")
        task = {
            "rect": _rect(process, _u(frame, "rsi")),
            "step": _u32(process, _u64(process, callback + 0x08) or 0),
            "destination_descriptor": _u64(process, callback + 0x10),
        }
        state["worker_tasks"].append(task)
        unique_rects = {
            tuple(item["rect"])
            for item in state["worker_tasks"]
            if item["rect"] is not None
        }
        if len(unique_rects) >= EXPECTED_UNIQUE_TASKS:
            state["terminated_after_capture"] = True
            process.Kill()
        return False

    state["errors"].append(f"unexpected site {site}")
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    found = False
    for index in range(target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(index)
        if not bp or not bp.IsValid() or bp.GetNumLocations() < 1:
            continue
        va = bp.GetLocationAtIndex(0).GetAddress().GetFileAddress()
        if va == MASK_ENTRY_VA:
            bp.SetScriptCallbackFunction("skip_mask_task_probe.hit")
            found = True
    if not found:
        _state()["errors"].append("mask-entry breakpoint not found")


def _process(debugger):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    if not process or not process.IsValid():
        return {"valid": False}
    return {
        "valid": True,
        "state": lldb.SBDebugger.StateAsCString(process.GetState()),
        "exit_status": process.GetExitStatus(),
    }


def write_report(debugger, path):
    packet = dict(_state())
    packet["process"] = _process(debugger)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(packet, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_SKIP_MASK_TASKS_WROTE", path)
