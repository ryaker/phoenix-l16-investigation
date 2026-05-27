import builtins
import json


SITE_GATE = 0x3E4B09
SITE_ENTRY = 0x1BE270
SITE_INITIAL_LOOKUP = 0x1BE291
SITE_COUNT_AFTER = 0x1BE2FB
SITE_LOOP_LOOKUP = 0x1BE306

SITES = {
    SITE_GATE: "gate_0x3e4b09",
    SITE_ENTRY: "builder_entry_1be270",
    SITE_INITIAL_LOOKUP: "initial_lookup_1be291",
    SITE_COUNT_AFTER: "count_after_e78e0_1be2fb",
    SITE_LOOP_LOOKUP: "loop_lookup_1be306",
}


def reset(label="", site_cap=512, sample_limit=96):
    builtins.l16_src1_source_builder_indices = {
        "label": label,
        "site_cap": site_cap,
        "sample_limit": sample_limit,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
        "gate_hits": 0,
        "lower_breakpoints_enabled": False,
        "breakpoint_ids": {},
        "counts": {name: 0 for name in SITES.values()},
        "disabled_after_cap": [],
        "invocations": {},
        "samples": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_src1_source_builder_indices"):
        reset()
    return builtins.l16_src1_source_builder_indices


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _i32(value):
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


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


def _stack(thread, max_frames=12):
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


def _invocation(frame):
    state = _state()
    key = hex(_u(frame, "rbp"))
    invocations = state["invocations"]
    if key not in invocations:
        invocations[key] = {
            "rbp": _u(frame, "rbp"),
            "object": None,
            "entry_key": None,
            "initial_lookup_keys": [],
            "counts_seen": [],
            "loop_indices": [],
            "loop_keys": [],
        }
    return invocations[key]


def _append_sample(sample):
    state = _state()
    if len(state["samples"]) < state["sample_limit"]:
        state["samples"].append(sample)


def _disable_breakpoint(debugger, name):
    target = debugger.GetSelectedTarget()
    bp_id = _state()["breakpoint_ids"].get(name)
    bp = target.FindBreakpointByID(bp_id) if bp_id is not None else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def _enable_lower_breakpoints(debugger):
    state = _state()
    if state["lower_breakpoints_enabled"]:
        return
    target = debugger.GetSelectedTarget()
    for name, bp_id in state["breakpoint_ids"].items():
        if name == "gate_0x3e4b09":
            continue
        bp = target.FindBreakpointByID(bp_id)
        if bp and bp.IsValid():
            bp.SetEnabled(True)
    state["lower_breakpoints_enabled"] = True


def _record_hit(frame, site_va, name):
    state = _state()
    state["counts"][name] = state["counts"].get(name, 0) + 1

    regs = _registers(frame)
    invocation = _invocation(frame)
    event = {"site": name, "site_va": site_va}

    if site_va == SITE_ENTRY:
        invocation["object"] = regs["rdi"]
        invocation["entry_key"] = _i32(regs["rsi"])
        event.update({"object": regs["rdi"], "key": _i32(regs["rsi"])})
    elif site_va == SITE_INITIAL_LOOKUP:
        invocation["object"] = regs["r15"]
        invocation["initial_lookup_keys"].append(_i32(regs["r14"]))
        event.update({"object": regs["r15"], "source_index": 0, "key": _i32(regs["r14"])})
    elif site_va == SITE_COUNT_AFTER:
        count = regs["rax"] & 0xFFFFFFFF
        loop_index = regs["rbx"]
        invocation["object"] = regs["r15"]
        invocation["counts_seen"].append(count)
        event.update({"object": regs["r15"], "loop_index": loop_index, "count": count, "key": _i32(regs["r14"])})
    elif site_va == SITE_LOOP_LOOKUP:
        loop_index = regs["rbx"]
        key = _i32(regs["r14"])
        invocation["object"] = regs["r15"]
        invocation["loop_indices"].append(loop_index)
        invocation["loop_keys"].append(key)
        event.update({"object": regs["r15"], "loop_index": loop_index, "key": key})

    if state["counts"][name] >= state["site_cap"]:
        _disable_breakpoint(frame.GetThread().GetProcess().GetTarget().GetDebugger(), name)
        if name not in state["disabled_after_cap"]:
            state["disabled_after_cap"].append(name)

    _append_sample(
        {
            **event,
            "registers": regs,
            "stack": _stack(frame.GetThread()),
        }
    )


def gate(frame, bp_loc, internal_dict):
    state = _state()
    state["gate_hits"] += 1
    debugger = frame.GetThread().GetProcess().GetTarget().GetDebugger()
    _enable_lower_breakpoints(debugger)
    _disable_breakpoint(debugger, "gate_0x3e4b09")
    return False


def hit(frame, bp_loc, internal_dict):
    target = frame.GetThread().GetProcess().GetTarget()
    site_va = _module_va(target, frame.GetPC())
    name = SITES.get(site_va)
    if name is None:
        _state()["errors"].append(f"unknown site {site_va}")
        return False
    _record_hit(frame, site_va, name)
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    count = target.GetNumBreakpoints()
    if count < len(SITES):
        _state()["errors"].append("expected at least 5 breakpoints")
        print("L16_SRC1_SOURCE_BUILDER_ATTACH_ERROR expected at least 5 breakpoints")
        return
    order = [
        ("gate_0x3e4b09", gate),
        ("builder_entry_1be270", hit),
        ("initial_lookup_1be291", hit),
        ("count_after_e78e0_1be2fb", hit),
        ("loop_lookup_1be306", hit),
    ]
    ids = {}
    start = count - len(order)
    for index, (name, callback) in enumerate(order, start=start):
        bp = target.GetBreakpointAtIndex(index)
        bp.SetScriptCallbackFunction(
            f"src1_source_builder_indices_probe.{callback.__name__}"
        )
        if name != "gate_0x3e4b09":
            bp.SetEnabled(False)
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_SRC1_SOURCE_BUILDER_ATTACHED", ids)


def attach_no_gate(debugger):
    target = debugger.GetSelectedTarget()
    count = target.GetNumBreakpoints()
    if count < 4:
        _state()["errors"].append("expected at least 4 breakpoints")
        print("L16_SRC1_SOURCE_BUILDER_ATTACH_ERROR expected at least 4 breakpoints")
        return
    order = [
        ("builder_entry_1be270", hit),
        ("initial_lookup_1be291", hit),
        ("count_after_e78e0_1be2fb", hit),
        ("loop_lookup_1be306", hit),
    ]
    ids = {}
    start = count - len(order)
    for index, (name, callback) in enumerate(order, start=start):
        bp = target.GetBreakpointAtIndex(index)
        bp.SetScriptCallbackFunction(
            f"src1_source_builder_indices_probe.{callback.__name__}"
        )
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    _state()["lower_breakpoints_enabled"] = True
    print("L16_SRC1_SOURCE_BUILDER_ATTACHED_NO_GATE", ids)


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


def _summary():
    invocations = _state()["invocations"]
    out = []
    for key, invocation in sorted(invocations.items()):
        loop_indices = invocation.get("loop_indices", [])
        counts_seen = invocation.get("counts_seen", [])
        out.append(
            {
                "rbp": invocation.get("rbp"),
                "object": invocation.get("object"),
                "entry_key": invocation.get("entry_key"),
                "initial_lookup_keys": sorted(set(invocation.get("initial_lookup_keys", []))),
                "counts_seen_unique": sorted(set(counts_seen)),
                "loop_index_min": min(loop_indices) if loop_indices else None,
                "loop_index_max": max(loop_indices) if loop_indices else None,
                "loop_indices_unique": sorted(set(loop_indices)),
                "loop_keys_unique": sorted(set(invocation.get("loop_keys", []))),
                "loop_lookup_count": len(loop_indices),
            }
        )
    return out


def drive_until_exit_or_step_cap(debugger, max_steps=16000):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process.IsValid() and process.GetState() == lldb.eStateStopped and steps < max_steps:
        steps += 1
        process.Continue()
    state["drive_steps"] += steps
    if process.IsValid() and process.GetState() == lldb.eStateStopped and steps >= max_steps:
        state["drive_hit_step_cap"] = True
    print("L16_SRC1_SOURCE_BUILDER_DRIVE_STEPS", steps)


def payload(debugger):
    return {
        "process": _process_packet(debugger),
        "breakpoint_hit_counts": _breakpoint_hit_counts(debugger),
        "summary": _summary(),
        **_state(),
    }


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_SRC1_SOURCE_BUILDER_WROTE", path)


def report(debugger):
    print("L16_SRC1_SOURCE_BUILDER_BEGIN")
    print(json.dumps(payload(debugger), indent=2, sort_keys=True))
    print("L16_SRC1_SOURCE_BUILDER_END")
