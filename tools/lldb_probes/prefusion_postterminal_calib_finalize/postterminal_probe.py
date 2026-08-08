import builtins
import json
import os


SITES = {
    "terminal_state_return": 0x2277B8,
    "overlay_entry": 0x227B00,
    "processing_lambda_post_calib": 0x3FE50A,
    "finalizer_entry": 0x226240,
    "processing_lambda_post_finalize": 0x3FE53D,
    "processing_machine_return": 0x3FBCB3,
    "initresamp_state_join": 0x3EB719,
}


def reset(label="", step_cap=200000):
    builtins.l16_postterminal_finalize = {
        "label": label,
        "step_cap": step_cap,
        "breakpoints": {},
        "terminal_state_returns": [],
        "overlay_entries": [],
        "processing_lambda_post_calib": [],
        "finalizer_entries": [],
        "processing_lambda_post_finalize": [],
        "processing_machine_returns": [],
        "initresamp_state_joins": [],
        "sibling_watchpoint_id": None,
        "sibling_watch_armed": None,
        "sibling_watch_samples": [],
        "sibling_watch_hit_cap": 64,
        "errors": [],
        "drive_hit_step_cap": False,
        "sequence": 0,
    }


def _state():
    if not hasattr(builtins, "l16_postterminal_finalize"):
        reset()
    return builtins.l16_postterminal_finalize


def _register(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _next_sequence():
    state = _state()
    state["sequence"] += 1
    return state["sequence"]


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


def terminal_state_return_hit(frame, _bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    owner = _register(frame, "r15")
    state["terminal_state_returns"].append(
        {
            "sequence": _next_sequence(),
            "owner": owner,
            "overlay_flag": _snapshot(process, owner + 0x10D, 1),
            "stack": _stack(frame),
        }
    )
    return False


def overlay_entry_hit(frame, _bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    owner = _register(frame, "rdi")
    state["overlay_entries"].append(
        {
            "sequence": _next_sequence(),
            "owner": owner,
            "overlay_flag": _snapshot(process, owner + 0x10D, 1),
            "stack": _stack(frame),
        }
    )
    return False


def processing_lambda_post_calib_hit(frame, _bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    state_root = _register(frame, "r12")
    owner = _register(frame, "r14")
    state["processing_lambda_post_calib"].append(
        {
            "sequence": _next_sequence(),
            "state_root": state_root,
            "owner": owner,
            "sibling_before": _snapshot(process, owner + 0x28, 8),
            "stack": _stack(frame),
        }
    )
    return False


def finalizer_entry_hit(frame, _bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    caller_va = _module_va(
        process.GetTarget(), frame.GetThread().GetFrameAtIndex(1).GetPC()
    )
    if caller_va != 0x3FE53D:
        return False
    owner = _register(frame, "rdi")
    tid = frame.GetThread().GetThreadID()
    packet = {
        "sequence": _next_sequence(),
        "thread_id": tid,
        "caller_libcp_va": caller_va,
        "owner": owner,
        "overlay_flag": _snapshot(process, owner + 0x10D, 1),
        "sibling_before": _snapshot(process, owner + 0x28, 8),
        "stack": _stack(frame),
    }
    state["finalizer_entries"].append(packet)
    return False


def processing_lambda_post_finalize_hit(frame, _bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    owner = _register(frame, "r14")
    packet = {
        "sequence": _next_sequence(),
        "owner": owner,
        "sibling_after": _snapshot(process, owner + 0x28, 8),
        "stack": _stack(frame),
    }
    state["processing_lambda_post_finalize"].append(packet)
    if state["sibling_watchpoint_id"] is None:
        lldb = builtins.__import__("lldb")
        error = lldb.SBError()
        target = process.GetTarget()
        watchpoint = target.WatchAddress(owner + 0x28, 8, True, True, error)
        if not error.Success() or not watchpoint or not watchpoint.IsValid():
            state["errors"].append(
                {
                    "error": "sibling slot watchpoint arm failed",
                    "detail": error.GetCString(),
                }
            )
        else:
            state["sibling_watchpoint_id"] = watchpoint.GetID()
            state["sibling_watch_armed"] = {
                "owner": owner,
                "address": owner + 0x28,
                "value_at_arm": packet["sibling_after"],
            }
    return False


def processing_machine_return_hit(frame, _bp_loc, _dict):
    state = _state()
    state["processing_machine_returns"].append(
        {
            "sequence": _next_sequence(),
            "processing_owner": _register(frame, "r13"),
            "stack": _stack(frame),
        }
    )
    return False


def initresamp_state_join_hit(frame, _bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    pipeline_cache = _register(frame, "r14")
    state_root = _register(frame, "rsi")
    state["initresamp_state_joins"].append(
        {
            "sequence": _next_sequence(),
            "pipeline_cache": pipeline_cache,
            "state_root_argument": state_root,
            "pipeline_state_slot": _snapshot(process, pipeline_cache + 0x180, 8),
            "record_vector": _snapshot(process, pipeline_cache + 0x258, 24),
            "stack": _stack(frame),
        }
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
    breakpoint.SetScriptCallbackFunction(f"postterminal_probe.{callback}")
    state["breakpoints"][name] = breakpoint.GetID()


def install(debugger):
    callbacks = {
        "terminal_state_return": "terminal_state_return_hit",
        "overlay_entry": "overlay_entry_hit",
        "processing_lambda_post_calib": "processing_lambda_post_calib_hit",
        "finalizer_entry": "finalizer_entry_hit",
        "processing_lambda_post_finalize": "processing_lambda_post_finalize_hit",
        "processing_machine_return": "processing_machine_return_hit",
        "initresamp_state_join": "initresamp_state_join_hit",
    }
    for name, address in SITES.items():
        _add_breakpoint(debugger, name, address, callbacks[name])
    print("L16_POSTTERMINAL_FINALIZE_INSTALLED", _state()["breakpoints"])


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
            if watchpoint_id == state["sibling_watchpoint_id"]:
                frame = thread.GetFrameAtIndex(0)
                armed = state["sibling_watch_armed"]
                before = (
                    state["sibling_watch_samples"][-1]["value_now"]
                    if state["sibling_watch_samples"]
                    else armed["value_at_arm"]
                )
                now = _snapshot(process, armed["address"], 8)
                state["sibling_watch_samples"].append(
                    {
                        "ordinal": len(state["sibling_watch_samples"]) + 1,
                        "thread_id": thread.GetThreadID(),
                        "pc": frame.GetPC(),
                        "libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
                        "value_before": before,
                        "value_now": now,
                        "changed": before["hex"] != now["hex"],
                        "stack": _stack(frame, 12),
                    }
                )
                if (
                    len(state["sibling_watch_samples"])
                    >= state["sibling_watch_hit_cap"]
                ):
                    watchpoint = process.GetTarget().FindWatchpointByID(
                        state["sibling_watchpoint_id"]
                    )
                    if watchpoint and watchpoint.IsValid():
                        watchpoint.SetEnabled(False)
        process.Continue()
    state["drive_steps"] = steps
    if process and process.IsValid():
        state["process_state"] = int(process.GetState())
        state["process_exit_status"] = process.GetExitStatus()
    print("L16_POSTTERMINAL_FINALIZE_DRIVE_STEPS", steps)


def payload(debugger):
    state = _state()
    packet = dict(state)
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
