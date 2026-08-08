import builtins
import json
import os


INIT_CURRENT_RETURN = 0x1F1350
TRACKED_CAMERA_ID = 5
BANK_SIZE = 0x54
BANK_OFFSETS = {
    "current_candidate": 0x12C,
    "factory_candidate": 0x180,
}


def reset(label="", step_cap=200000):
    builtins.l16_calibstage_bank_watch = {
        "label": label,
        "step_cap": step_cap,
        "breakpoints": {},
        "watchpoints": {},
        "tracked_object": None,
        "tracked_camera_id": TRACKED_CAMERA_ID,
        "initial": None,
        "events": [],
        "errors": [],
        "drive_hit_step_cap": False,
    }


def _state():
    if not hasattr(builtins, "l16_calibstage_bank_watch"):
        reset()
    return builtins.l16_calibstage_bank_watch


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
    if base is None or address < base:
        return None
    value = address - base
    return value if value < 0x700000 else None


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


def _stack(frame, limit=8):
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


def _bank_snapshot(process, object_address, label):
    return _snapshot(
        process,
        object_address + BANK_OFFSETS[label],
        BANK_SIZE,
    )


def _arm_watchpoint(target, address, label):
    lldb = builtins.__import__("lldb")
    state = _state()
    error = lldb.SBError()
    watchpoint = target.WatchAddress(address, 8, False, True, error)
    if not error.Success() or not watchpoint or not watchpoint.IsValid():
        state["errors"].append(
            {
                "error": "watchpoint not created",
                "label": label,
                "address": address,
                "detail": error.GetCString(),
            }
        )
        return
    state["watchpoints"][str(watchpoint.GetID())] = {
        "label": label,
        "address": address,
    }


def init_current_return_hit(frame, _bp_loc, _dict):
    state = _state()
    if state["tracked_object"] is not None:
        return False

    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    object_address = _register(frame, "r14")
    key_data = _read(process, object_address + 0x60, 4)
    if key_data is None:
        return False
    camera_id = int.from_bytes(key_data, "little")
    if camera_id != TRACKED_CAMERA_ID:
        return False

    current = _bank_snapshot(process, object_address, "current_candidate")
    factory = _bank_snapshot(process, object_address, "factory_candidate")
    state["tracked_object"] = object_address
    state["initial"] = {
        "object": object_address,
        "camera_id": camera_id,
        "current_candidate": current,
        "factory_candidate": factory,
        "banks_equal": current["hex"] == factory["hex"],
        "stack": _stack(frame),
    }
    for label, offset in BANK_OFFSETS.items():
        _arm_watchpoint(target, object_address + offset, label)
    return False


def _record_watchpoint_hit(frame, watchpoint_id):
    state = _state()
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    object_address = state["tracked_object"]
    if object_address is None:
        return False

    metadata = state["watchpoints"].get(str(watchpoint_id), {})
    state["events"].append(
        {
            "watchpoint_id": watchpoint_id,
            "bank": metadata.get("label"),
            "watched_address": metadata.get("address"),
            "pc": frame.GetPC(),
            "libcp_va": _module_va(target, frame.GetPC()),
            "camera_id": _snapshot(process, object_address + 0x60, 4),
            "current_candidate": _bank_snapshot(
                process, object_address, "current_candidate"
            ),
            "factory_candidate": _bank_snapshot(
                process, object_address, "factory_candidate"
            ),
            "stack": _stack(frame),
        }
    )
def install(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    before = target.GetNumBreakpoints()
    debugger.HandleCommand(
        "breakpoint set --shlib libcp.dylib "
        f"--address 0x{INIT_CURRENT_RETURN:x}"
    )
    if target.GetNumBreakpoints() <= before:
        state["errors"].append({"error": "initialization breakpoint not created"})
        return
    breakpoint = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
    breakpoint.SetScriptCallbackFunction(
        "calibstage_bank_watch_probe.init_current_return_hit"
    )
    state["breakpoints"]["init_current_return"] = breakpoint.GetID()
    print("L16_CALIBSTAGE_BANK_WATCH_INSTALLED", state["breakpoints"])


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
            watchpoint_id = (
                thread.GetStopReasonDataAtIndex(0)
                if thread.GetStopReasonDataCount()
                else None
            )
            if str(watchpoint_id) in state["watchpoints"]:
                _record_watchpoint_hit(thread.GetFrameAtIndex(0), watchpoint_id)
        process.Continue()
    state["drive_steps"] = steps
    if process and process.IsValid():
        state["process_state"] = int(process.GetState())
        state["process_exit_status"] = process.GetExitStatus()
    print("L16_CALIBSTAGE_BANK_WATCH_DRIVE_STEPS", steps)


def report_to_file(debugger, path):
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    if process and process.IsValid():
        state["process_state"] = int(process.GetState())
        state["process_exit_status"] = process.GetExitStatus()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("WROTE", path)
