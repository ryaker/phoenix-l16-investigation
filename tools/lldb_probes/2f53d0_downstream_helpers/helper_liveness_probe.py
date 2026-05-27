import builtins
import json
import struct


GATE = 0x3E4B09
SITES = {
    0x2F53D0: "entry_0x2f53d0",
    0x2F55BB: "call_0xab590_prebranch",
    0x2F5679: "call_0x2f4470_prebranch",
    0x2F59A1: "call_0x2f6420_loop",
    0x2F59D4: "call_0x135d0_loop",
    0x2F5ACC: "call_0x2f6420_final",
    0x2F5AFE: "call_0x135d0_final",
    0x2F5B2C: "call_0x3066d0_positive_branch",
    0x2F5BCB: "call_0x3048b0_nonpositive_branch",
    0x2F5C84: "call_0xab590_postbranch",
}


def reset(label="", site_cap=128, sample_limit=64):
    builtins.l16_2f53d0_helper_liveness = {
        "label": label,
        "site_cap": site_cap,
        "sample_limit": sample_limit,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
        "gate_hits": 0,
        "call_breakpoints_enabled": False,
        "breakpoint_ids": {},
        "counts": {name: 0 for name in SITES.values()},
        "disabled_after_cap": [],
        "samples": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_2f53d0_helper_liveness"):
        reset()
    return builtins.l16_2f53d0_helper_liveness


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


def _u32(data, off=0):
    return struct.unpack_from("<I", data, off)[0]


def _u64(data, off=0):
    return struct.unpack_from("<Q", data, off)[0]


def _i32s(data):
    return list(struct.unpack("<" + "i" * (len(data) // 4), data))


def _libcp_base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                return base
    return None


def _module_va(target, pc):
    base = _libcp_base(target)
    if base is not None and pc >= base:
        return pc - base
    return None


def _registers(frame):
    return {
        name: _u(frame, name)
        for name in (
            "rax",
            "rbx",
            "rcx",
            "rdx",
            "rdi",
            "rsi",
            "r8",
            "r9",
            "r10",
            "r11",
            "r12",
            "r13",
            "r14",
            "r15",
            "rbp",
            "rsp",
        )
    }


def _stack(thread, max_frames=10):
    target = thread.GetProcess().GetTarget()
    frames = []
    for index in range(min(thread.GetNumFrames(), max_frames)):
        frame = thread.GetFrameAtIndex(index)
        frames.append(
            {
                "index": index,
                "pc": frame.GetPC(),
                "libcp_va": _module_va(target, frame.GetPC()),
                "function": frame.GetFunctionName(),
                "rbp": _u(frame, "rbp"),
            }
        )
    return frames


def _descriptor(process, addr):
    data = _read(process, addr, 0x30)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "first_12_i32": _i32s(data),
        "qwords": [_u64(data, off) for off in range(0, 0x30, 8)],
    }


def _site_name(site_va):
    if site_va == GATE:
        return "gate_0x3e4b09"
    return SITES.get(site_va, hex(site_va))


def _enable_call_breakpoints(debugger):
    state = _state()
    if state["call_breakpoints_enabled"]:
        return
    target = debugger.GetSelectedTarget()
    for name, bp_id in state["breakpoint_ids"].items():
        if name == "gate_0x3e4b09":
            continue
        bp = target.FindBreakpointByID(bp_id)
        if bp and bp.IsValid():
            bp.SetEnabled(True)
    state["call_breakpoints_enabled"] = True


def _disable_breakpoint(debugger, name):
    bp_id = _state()["breakpoint_ids"].get(name)
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id) if bp_id else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def _create_call_breakpoints(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    base = _libcp_base(target)
    if base is None:
        state["errors"].append("libcp base unavailable")
        return
    ids = state.setdefault("breakpoint_ids", {})
    for va, name in SITES.items():
        if name in ids:
            continue
        bp = target.BreakpointCreateByAddress(base + va)
        bp.SetScriptCallbackFunction("helper_liveness_probe.site")
        ids[name] = bp.GetID()


def gate(frame, bp_loc, internal_dict):
    state = _state()
    state["gate_hits"] += 1
    debugger = frame.GetThread().GetProcess().GetTarget().GetDebugger()
    _enable_call_breakpoints(debugger)
    _disable_breakpoint(debugger, "gate_0x3e4b09")
    return False


def gate_lazy(frame, bp_loc, internal_dict):
    state = _state()
    state["gate_hits"] += 1
    debugger = frame.GetThread().GetProcess().GetTarget().GetDebugger()
    _create_call_breakpoints(debugger)
    state["call_breakpoints_enabled"] = True
    _disable_breakpoint(debugger, "gate_0x3e4b09")
    return False


def site(frame, bp_loc, internal_dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    site_va = _module_va(target, frame.GetPC())
    name = SITES.get(site_va)
    if name is None:
        state["errors"].append(f"unknown site {site_va}")
        return False

    state["counts"][name] = state["counts"].get(name, 0) + 1
    if len(state["samples"]) < state["sample_limit"]:
        regs = _registers(frame)
        sample = {
            "site": name,
            "site_va": site_va,
            "registers": regs,
            "descriptors": {
                reg: _descriptor(process, regs[reg])
                for reg in ("rdi", "rsi", "rdx", "rcx", "r8", "r9")
            },
            "stack": _stack(thread),
        }
        state["samples"].append(sample)

    if state["counts"][name] >= state["site_cap"]:
        _disable_breakpoint(target.GetDebugger(), name)
        if name not in state["disabled_after_cap"]:
            state["disabled_after_cap"].append(name)
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    count = target.GetNumBreakpoints()
    order = [("gate_0x3e4b09", gate)] + [(SITES[va], site) for va in SITES]
    if count < len(order):
        _state()["errors"].append(f"expected at least {len(order)} breakpoints")
        print("L16_2F53D0_ATTACH_ERROR", count, len(order))
        return
    ids = {}
    start = count - len(order)
    for index, (name, callback) in enumerate(order, start=start):
        bp = target.GetBreakpointAtIndex(index)
        bp.SetScriptCallbackFunction(
            f"helper_liveness_probe.{callback.__name__}"
        )
        if name != "gate_0x3e4b09":
            bp.SetEnabled(False)
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_2F53D0_HELPER_ATTACHED", ids)


def attach_lazy(debugger):
    target = debugger.GetSelectedTarget()
    count = target.GetNumBreakpoints()
    if count < 1:
        _state()["errors"].append("expected gate breakpoint")
        print("L16_2F53D0_LAZY_ATTACH_ERROR expected gate breakpoint")
        return
    bp = target.GetBreakpointAtIndex(count - 1)
    bp.SetScriptCallbackFunction("helper_liveness_probe.gate_lazy")
    ids = {"gate_0x3e4b09": bp.GetID()}
    _state()["breakpoint_ids"] = ids
    print("L16_2F53D0_HELPER_LAZY_ATTACHED", ids)


def _breakpoint_hit_counts(debugger):
    target = debugger.GetSelectedTarget()
    out = {}
    for name, bp_id in _state().get("breakpoint_ids", {}).items():
        bp = target.FindBreakpointByID(bp_id)
        out[name] = bp.GetHitCount() if bp and bp.IsValid() else None
    return out


def _process_packet(debugger):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    if not process or not process.IsValid():
        return {"valid": False}
    return {
        "valid": True,
        "state": lldb.SBDebugger.StateAsCString(process.GetState()),
        "exit_status": process.GetExitStatus(),
    }


def drive_until_exit_or_step_cap(debugger, max_steps=12000):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while (
        process.IsValid()
        and process.GetState() == lldb.eStateStopped
        and steps < max_steps
    ):
        steps += 1
        process.Continue()
    state["drive_steps"] += steps
    if process.IsValid() and process.GetState() == lldb.eStateStopped and steps >= max_steps:
        state["drive_hit_step_cap"] = True
    print("L16_2F53D0_HELPER_DRIVE_STEPS", steps)


def payload(debugger):
    return {
        "process": _process_packet(debugger),
        "breakpoint_hit_counts": _breakpoint_hit_counts(debugger),
        **_state(),
    }


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_2F53D0_HELPER_WROTE", path)


def report(debugger):
    print(json.dumps(payload(debugger), indent=2, sort_keys=True))
