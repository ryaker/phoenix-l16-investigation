import builtins
import json

import lldb


SITES = {
    0x3412F0: "operator_entry",
    0x341311: "calibration_presence_test",
    0x34131F: "post_missing_calibration_join",
    0x34132B: "applicability_result",
    0x341333: "active_path",
    0x341444: "correct_leakage_call",
    0x10ACD0: "correct_leakage_body",
}


def reset(label=""):
    builtins.l16_hotpixel_leakage = {
        "label": label,
        "counts": {name: 0 for name in SITES.values()},
        "samples": [],
    }


def _state():
    if not hasattr(builtins, "l16_hotpixel_leakage"):
        reset()
    return builtins.l16_hotpixel_leakage


def _libcp_base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                return base
    return None


def _va(frame):
    target = frame.GetThread().GetProcess().GetTarget()
    base = _libcp_base(target)
    return frame.GetPC() - base if base is not None else None


def hit(frame, bp_loc, internal_dict):
    state = _state()
    va = _va(frame)
    name = SITES.get(va, hex(va) if va is not None else "unknown")
    state["counts"][name] = state["counts"].get(name, 0) + 1
    if len(state["samples"]) < 16:
        state["samples"].append({
            "site": name,
            "va": va,
            "rdi": frame.FindRegister("rdi").GetValueAsUnsigned(),
            "rsi": frame.FindRegister("rsi").GetValueAsUnsigned(),
            "rax": frame.FindRegister("rax").GetValueAsUnsigned(),
        })
    return False


def attach(debugger, minimum_id=1):
    target = debugger.GetSelectedTarget()
    for bp in target.breakpoint_iter():
        if bp.GetID() < minimum_id:
            continue
        bp.SetScriptCallbackFunction(__name__ + ".hit")
        bp.SetAutoContinue(True)


def write_report(path, debugger=None):
    state = _state()
    if debugger is not None:
        process = debugger.GetSelectedTarget().GetProcess()
        state["process"] = {
            "valid": process.IsValid(),
            "state": lldb.SBDebugger.StateAsCString(process.GetState()),
            "exit_status": process.GetExitStatus(),
        }
    with open(path, "w") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")


def report():
    print("HOTPIXEL_LEAKAGE " + json.dumps(_state(), sort_keys=True))
