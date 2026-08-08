import builtins
import json
import os
import struct


SITES = {0x3066D0: "parent_entry", 0x307771: "tent_input", 0x307792: "tent_output"}


def reset(label=""):
    builtins.l16_nlm_weight_formula = {
        "label": label,
        "breakpoint_ids": {},
        "counts": {name: 0 for name in SITES.values()},
        "pending": {},
        "entry": None,
        "samples": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_nlm_weight_formula"):
        reset()
    return builtins.l16_nlm_weight_formula


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _vec4_memory(process, addr):
    raw = _read(process, addr, 16)
    return list(struct.unpack("<4f", raw)) if raw is not None else None


def _xmm(frame, name):
    try:
        lldb = builtins.__import__("lldb")
        data = frame.FindRegister(name).GetData()
        error = lldb.SBError()
        raw = bytes(data.GetUnsignedInt8(error, i) for i in range(data.GetByteSize()))
        if error.Success() and len(raw) >= 16:
            return list(struct.unpack_from("<4f", raw))
    except Exception as exc:
        _state()["errors"].append(f"{name}: {exc}")
    return None


def _disable(debugger, name):
    bp_id = _state()["breakpoint_ids"].get(name)
    if bp_id is not None:
        bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id)
        if bp and bp.IsValid():
            bp.SetEnabled(False)


def site(frame, bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    debugger = process.GetTarget().GetDebugger()
    pc = frame.GetPC()
    base = None
    for module in process.GetTarget().module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(process.GetTarget())
            break
    va = pc - base if base is not None else None
    name = SITES.get(va)
    if name is None:
        state["errors"].append(f"unexpected stop pc=0x{pc:x} va={va}")
        return False

    state["counts"][name] += 1
    tid = frame.GetThread().GetThreadID()
    rbp = _u(frame, "rbp")
    if name == "parent_entry" and state["entry"] is None:
        coefficient = _u(frame, "rcx")
        state["entry"] = {
            "coefficient_ptr": coefficient,
            "coefficient": _vec4_memory(process, coefficient),
            "strength_xmm0": _xmm(frame, "xmm0"),
            "mode_r8d": _u(frame, "r8") & 0xFFFFFFFF,
            "search_divisor_r9d": _u(frame, "r9") & 0xFFFFFFFF,
        }
        _disable(debugger, name)
    elif name == "tent_input" and not state["samples"]:
        state["pending"][str(tid)] = {
            "thread_id": tid,
            "distance_broadcast": _xmm(frame, "xmm0"),
            "threshold": _vec4_memory(process, rbp - 0x280),
            "threshold_rcpps": _vec4_memory(process, rbp - 0x290),
        }
    elif name == "tent_output" and not state["samples"]:
        packet = state["pending"].pop(str(tid), None)
        if packet is not None:
            packet["weight"] = _xmm(frame, "xmm3")
            packet["rbp"] = rbp
            distance = packet.get("distance_broadcast") or []
            threshold = packet.get("threshold") or []
            if distance and threshold and distance[0] > min(threshold[:3]):
                state["samples"].append(packet)
                _disable(debugger, "tent_input")
                _disable(debugger, name)
    return False


def install(debugger):
    target = debugger.GetSelectedTarget()
    for va, name in SITES.items():
        before = target.GetNumBreakpoints()
        debugger.HandleCommand(f"breakpoint set --shlib libcp.dylib --address 0x{va:x}")
        if target.GetNumBreakpoints() <= before:
            _state()["errors"].append(f"failed to create {name}")
            continue
        bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
        bp.SetScriptCallbackFunction("nlm_weight_formula_probe.site")
        _state()["breakpoint_ids"][name] = bp.GetID()
    print("L16_NLM_WEIGHT_FORMULA_INSTALLED", _state()["breakpoint_ids"])


def drive(debugger, cap=20000):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process.IsValid() and process.GetState() == lldb.eStateStopped and steps < cap:
        steps += 1
        process.Continue()
    _state()["drive_steps"] = steps
    print("L16_NLM_WEIGHT_FORMULA_DRIVE_STEPS", steps)


def write_report(debugger, path):
    process = debugger.GetSelectedTarget().GetProcess()
    payload = {
        **_state(),
        "process": {
            "valid": bool(process and process.IsValid()),
            "exit_status": process.GetExitStatus() if process and process.IsValid() else None,
        },
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_NLM_WEIGHT_FORMULA_WROTE", path)
