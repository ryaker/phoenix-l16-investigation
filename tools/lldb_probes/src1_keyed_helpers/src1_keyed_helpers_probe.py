import builtins
import json
import struct


SITES = {
    0x1BDC80: "cache_entry_1bdc80",
    0x1BDCFB: "cache_count_after_e78e0_1bdcfb",
    0x1BDE2B: "cache_lazy_builder_call_1bde2b",
    0x1BDE5E: "cache_return_node_1bde5e",
    0x1BE750: "stack_entry_1be750",
    0x1BE770: "stack_count_after_e78e0_1be770",
    0x1BE7FF: "stack_lazy_builder_call_1be7ff",
    0x1BE82E: "stack_return_node_1be82e",
}


def reset(label="", site_cap=1024, sample_limit=160):
    builtins.l16_src1_keyed_helpers = {
        "label": label,
        "site_cap": site_cap,
        "sample_limit": sample_limit,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
        "breakpoint_ids": {},
        "counts": {name: 0 for name in SITES.values()},
        "disabled_after_cap": [],
        "invocations": {},
        "samples": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_src1_keyed_helpers"):
        reset()
    return builtins.l16_src1_keyed_helpers


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _i32(value):
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def _read(process, addr, size):
    if not addr:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u64(data, off=0):
    return struct.unpack_from("<Q", data, off)[0]


def _i32_at(process, addr):
    data = _read(process, addr, 4)
    if data is None:
        return None
    return struct.unpack_from("<i", data, 0)[0]


def _u64_at(process, addr):
    data = _read(process, addr, 8)
    return _u64(data) if data is not None else None


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


def _node_packet(process, node):
    if not node:
        return {"node": node, "read_ok": False}
    return {
        "node": node,
        "read_ok": True,
        "tree_key_0x20": _i32_at(process, node + 0x20),
        "payload_0x28": _u64_at(process, node + 0x28),
        "payload_0x30": _u64_at(process, node + 0x30),
        "payload_0x38": _u64_at(process, node + 0x38),
        "payload_0x40": _u64_at(process, node + 0x40),
    }


def _invocation(helper, key, container, out):
    state = _state()
    invocation_key = f"{helper}:{hex(container)}:{hex(out)}:{key}"
    invocations = state["invocations"]
    if invocation_key not in invocations:
        invocations[invocation_key] = {
            "helper": helper,
            "key": invocation_key,
            "rbp_values": [],
            "entry_key": None,
            "container": None,
            "out": None,
            "counts_seen": [],
            "lazy_builder_calls": 0,
            "return_nodes": [],
        }
    return invocations[invocation_key]


def _disable_breakpoint(debugger, name):
    target = debugger.GetSelectedTarget()
    bp_id = _state()["breakpoint_ids"].get(name)
    bp = target.FindBreakpointByID(bp_id) if bp_id is not None else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def _append_sample(sample):
    state = _state()
    if len(state["samples"]) < state["sample_limit"]:
        state["samples"].append(sample)


def hit(frame, bp_loc, internal_dict):
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
    regs = _registers(frame)
    helper = "cache" if site_va in (0x1BDC80, 0x1BDCFB, 0x1BDE2B, 0x1BDE5E) else "stack"
    event = {"site": name, "site_va": site_va, "helper": helper}

    if site_va in (0x1BDC80, 0x1BE750):
        invocation = _invocation(helper, _i32(regs["rdx"]), regs["rsi"], regs["rdi"])
        invocation["entry_key"] = _i32(regs["rdx"])
        invocation["container"] = regs["rsi"]
        invocation["out"] = regs["rdi"]
        event.update({"entry_key": _i32(regs["rdx"]), "container": regs["rsi"], "out": regs["rdi"]})
    elif site_va in (0x1BDCFB, 0x1BE770):
        invocation = _invocation(helper, _i32(regs["rbx"]), regs["r12"], regs["r15"])
        count = regs["rax"] & 0xFFFFFFFF
        invocation["entry_key"] = _i32(regs["rbx"])
        invocation["container"] = regs["r12"]
        invocation["out"] = regs["r15"]
        invocation["counts_seen"].append(count)
        event.update({"entry_key": _i32(regs["rbx"]), "count": count, "container": regs["r12"], "out": regs["r15"]})
    elif site_va in (0x1BDE2B, 0x1BE7FF):
        invocation = _invocation(helper, _i32(regs["rbx"]), regs["r12"], regs["r15"])
        invocation["entry_key"] = _i32(regs["rbx"])
        invocation["container"] = regs["r12"]
        invocation["out"] = regs["r15"]
        invocation["lazy_builder_calls"] += 1
        event.update({"entry_key": _i32(regs["rbx"]), "container": regs["r12"], "out": regs["r15"]})
    elif site_va in (0x1BDE5E, 0x1BE82E):
        invocation = _invocation(helper, _i32(regs["rbx"]), regs["r12"], regs["r15"])
        node = regs["rax"] if site_va == 0x1BDE5E else regs["rcx"]
        packet = _node_packet(process, node)
        invocation["entry_key"] = _i32(regs["rbx"])
        invocation["container"] = regs["r12"]
        invocation["out"] = regs["r15"]
        invocation["return_nodes"].append(packet)
        event.update({"entry_key": _i32(regs["rbx"]), "node": packet, "out": regs["r15"]})
    else:
        invocation = None

    if invocation is not None:
        rbp = regs["rbp"]
        if rbp not in invocation["rbp_values"]:
            invocation["rbp_values"].append(rbp)

    if state["counts"][name] >= state["site_cap"]:
        _disable_breakpoint(target.GetDebugger(), name)
        if name not in state["disabled_after_cap"]:
            state["disabled_after_cap"].append(name)

    _append_sample({**event, "registers": regs, "stack": _stack(thread)})
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    count = target.GetNumBreakpoints()
    if count < len(SITES):
        _state()["errors"].append("expected at least 8 breakpoints")
        print("L16_SRC1_KEYED_HELPERS_ATTACH_ERROR expected at least 8 breakpoints")
        return
    ids = {}
    start = count - len(SITES)
    for index, (site_va, name) in enumerate(SITES.items(), start=start):
        bp = target.GetBreakpointAtIndex(index)
        bp.SetScriptCallbackFunction("src1_keyed_helpers_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_SRC1_KEYED_HELPERS_ATTACHED", ids)


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
    rows = []
    for _, invocation in sorted(_state()["invocations"].items()):
        rows.append(
            {
                "helper": invocation.get("helper"),
                "key": invocation.get("key"),
                "rbp_values": invocation.get("rbp_values"),
                "entry_key": invocation.get("entry_key"),
                "container": invocation.get("container"),
                "out": invocation.get("out"),
                "counts_seen_unique": sorted(set(invocation.get("counts_seen", []))),
                "lazy_builder_calls": invocation.get("lazy_builder_calls", 0),
                "return_tree_keys": sorted(
                    set(
                        node.get("tree_key_0x20")
                        for node in invocation.get("return_nodes", [])
                        if node.get("tree_key_0x20") is not None
                    )
                ),
                "return_payload_0x28_nonzero": any(node.get("payload_0x28") for node in invocation.get("return_nodes", [])),
                "return_payload_0x38_nonzero": any(node.get("payload_0x38") for node in invocation.get("return_nodes", [])),
            }
        )
    return rows


def drive_until_exit_or_step_cap(debugger, max_steps=24000):
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
    print("L16_SRC1_KEYED_HELPERS_DRIVE_STEPS", steps)


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
    print("L16_SRC1_KEYED_HELPERS_WROTE", path)
