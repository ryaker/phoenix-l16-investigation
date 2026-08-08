import builtins
import json


ENTRY = 0x2E4CF0


def reset(label, offsets):
    builtins.l16_laplacian_unused_fields = {
        "label": label,
        "offsets": list(offsets),
        "config_ptr": None,
        "entry_hits": 0,
        "armed": [],
        "watchpoint_hits": [],
        "errors": [],
    }


def _state():
    return builtins.l16_laplacian_unused_fields


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _module_va(target, pc):
    module = target.FindModule(builtins.__import__("lldb").SBFileSpec("libcp.dylib"))
    base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
    return pc - base


def entry(frame, bp_loc, _dict):
    state = _state()
    state["entry_hits"] += 1
    if state["armed"]:
        return False

    lldb = builtins.__import__("lldb")
    target = frame.GetThread().GetProcess().GetTarget()
    config_ptr = _u(frame, "rdx")
    state["config_ptr"] = config_ptr
    for offset in state["offsets"]:
        error = lldb.SBError()
        watchpoint = target.WatchAddress(config_ptr + offset, 4, True, False, error)
        if not error.Success() or not watchpoint or not watchpoint.IsValid():
            state["errors"].append(
                {
                    "offset": offset,
                    "error": error.GetCString() or "invalid watchpoint",
                }
            )
            continue
        state["armed"].append(
            {
                "offset": offset,
                "address": config_ptr + offset,
                "watchpoint_id": watchpoint.GetID(),
            }
        )
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def install(debugger, bp_id):
    breakpoint = debugger.GetSelectedTarget().FindBreakpointByID(bp_id)
    breakpoint.SetScriptCallbackFunction(
        "unused_config_fields_watch_probe.entry"
    )


def _record_watchpoint_stop(debugger):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    thread = process.GetSelectedThread()
    if thread.GetStopReason() != lldb.eStopReasonWatchpoint:
        return
    watchpoint_id = thread.GetStopReasonDataAtIndex(0)
    frame = thread.GetFrameAtIndex(0)
    state["watchpoint_hits"].append(
        {
            "watchpoint_id": watchpoint_id,
            "thread_id": thread.GetThreadID(),
            "pc": frame.GetPC(),
            "libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
        }
    )


def drive_until_exit(debugger, cap=1000):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    stops = 0
    while process.IsValid() and process.GetState() == lldb.eStateStopped:
        _record_watchpoint_stop(debugger)
        stops += 1
        if stops >= cap:
            _state()["errors"].append("watchpoint stop cap reached")
            break
        process.Continue()
    _state()["drive_stops"] = stops


def report_to_file(debugger, path):
    state = _state()
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    state["process"] = {
        "valid": process.IsValid(),
        "state": process.GetState(),
        "exit_status": process.GetExitStatus(),
    }
    state["watchpoint_hit_counts"] = {
        str(item["watchpoint_id"]): target.FindWatchpointByID(
            item["watchpoint_id"]
        ).GetHitCount()
        for item in state["armed"]
    }
    with open(path, "w") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
    print("WROTE", path, "hits", len(state["watchpoint_hits"]))
