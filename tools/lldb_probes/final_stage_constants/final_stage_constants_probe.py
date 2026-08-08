import builtins
import json
import os


SITES = {
    "sharpen_gaussian7_post": 0x35F945,
    "patch_nlm_call": 0x2F5B2C,
}


def reset(label="", nlm_sample_cap=16):
    builtins.l16_final_stage_constants = {
        "label": label,
        "nlm_sample_cap": nlm_sample_cap,
        "breakpoints": {},
        "gaussian7": [],
        "patch_nlm": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_final_stage_constants"):
        reset()
    return builtins.l16_final_stage_constants


def _register(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


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


def gaussian7_post_hit(frame, bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    output = _register(frame, "r12")
    state["gaussian7"].append(
        {
            "output": output,
            "coefficients": _snapshot(process, output, 28),
        }
    )
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def patch_nlm_hit(frame, bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    config = _register(frame, "r13")
    state["patch_nlm"].append(
        {
            "arg0_r8": _register(frame, "r8"),
            "arg1_r9": _register(frame, "r9"),
            "config": _snapshot(process, config, 24),
        }
    )
    if len(state["patch_nlm"]) >= state["nlm_sample_cap"]:
        bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def _add_breakpoint(debugger, name, address, callback):
    state = _state()
    target = debugger.GetSelectedTarget()
    before = target.GetNumBreakpoints()
    debugger.HandleCommand(
        f"breakpoint set --shlib libcp.dylib --address 0x{address:x}"
    )
    if target.GetNumBreakpoints() <= before:
        state["errors"].append({"site": name, "error": "breakpoint creation"})
        return
    breakpoint = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
    breakpoint.SetScriptCallbackFunction(f"final_stage_constants_probe.{callback}")
    state["breakpoints"][name] = breakpoint.GetID()


def install(debugger):
    callbacks = {
        "sharpen_gaussian7_post": "gaussian7_post_hit",
        "patch_nlm_call": "patch_nlm_hit",
    }
    for name, address in SITES.items():
        _add_breakpoint(debugger, name, address, callbacks[name])
    print("L16_FINAL_STAGE_CONSTANTS_INSTALLED", _state()["breakpoints"])


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
