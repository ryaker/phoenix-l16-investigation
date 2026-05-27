import builtins
import json
import struct


SITE_GATE = 0x3E4B09
CALL_SITES = {
    0x342D99: {
        "name": "call_0x342ca0_owner_0x1560_slot_0x30",
        "target_reg": "r9",
        "callable_reg": "rdi",
        "owner_reg": "r14",
        "owner_field": 0x1560,
        "descriptor_regs": ("rsi", "rdx", "rcx"),
    },
    0x3449F0: {
        "name": "call_0x344470_owner_0x1590_slot_0x30",
        "target_reg": "rax",
        "callable_reg": "rdi",
        "owner_saved_rbp_offset": -0x178,
        "owner_field": 0x1590,
        "descriptor_regs": ("rsi", "rdx", "rcx", "r8", "r9"),
    },
}


def reset(label="", site_cap=256, sample_limit=32):
    builtins.l16_src1_indirect_callable_targets = {
        "label": label,
        "site_cap": site_cap,
        "sample_limit": sample_limit,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
        "gate_hits": 0,
        "call_breakpoints_enabled": False,
        "breakpoint_ids": {},
        "call_counts": {cfg["name"]: 0 for cfg in CALL_SITES.values()},
        "target_counts": {},
        "disabled_after_cap": [],
        "samples": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_src1_indirect_callable_targets"):
        reset()
    return builtins.l16_src1_indirect_callable_targets


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


def _read_qword(process, addr):
    data = _read(process, addr, 8)
    return _u64(data) if data is not None else None


def _read_u32(process, addr):
    data = _read(process, addr, 4)
    return _u32(data) if data is not None else None


def _descriptor_packet(process, addr):
    data = _read(process, addr, 0x30)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "first_12_i32": _i32s(data),
        "qwords": [_u64(data, off) for off in range(0, 0x30, 8)],
    }


def _callable_packet(target, process, callable_addr, target_reg_value):
    vtable = _read_qword(process, callable_addr)
    slot = _read_qword(process, vtable + 0x30) if vtable else None
    return {
        "callable": callable_addr,
        "vtable": vtable,
        "vtable_libcp_va": _module_va(target, vtable) if vtable else None,
        "slot_0x30": slot,
        "slot_0x30_libcp_va": _module_va(target, slot) if slot else None,
        "target_reg_value": target_reg_value,
        "target_reg_libcp_va": _module_va(target, target_reg_value)
        if target_reg_value
        else None,
    }


def _owner_addr(process, regs, cfg):
    if "owner_reg" in cfg:
        return regs[cfg["owner_reg"]]
    rbp_off = cfg.get("owner_saved_rbp_offset")
    if rbp_off is not None:
        return _read_qword(process, regs["rbp"] + rbp_off)
    return None


def _owner_packet(process, owner, field):
    if not owner:
        return {"addr": owner, "read_ok": False}
    return {
        "addr": owner,
        "read_ok": True,
        "mode_0x150c": _read_u32(process, owner + 0x150C),
        "field_ptr": _read_qword(process, owner + field),
        "field_offset": field,
    }


def _site_name(site_va):
    if site_va == SITE_GATE:
        return "gate_0x3e4b09"
    cfg = CALL_SITES.get(site_va)
    return cfg["name"] if cfg else hex(site_va)


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
    target = debugger.GetSelectedTarget()
    bp_id = _state()["breakpoint_ids"].get(name)
    bp = target.FindBreakpointByID(bp_id) if bp_id is not None else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def gate(frame, bp_loc, internal_dict):
    state = _state()
    state["gate_hits"] += 1
    debugger = frame.GetThread().GetProcess().GetTarget().GetDebugger()
    _enable_call_breakpoints(debugger)
    _disable_breakpoint(debugger, "gate_0x3e4b09")
    return False


def callsite(frame, bp_loc, internal_dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    site_va = _module_va(target, frame.GetPC())
    cfg = CALL_SITES.get(site_va)
    if cfg is None:
        state["errors"].append(f"unknown site {site_va}")
        return False

    name = cfg["name"]
    regs = _registers(frame)
    target_reg_value = regs[cfg["target_reg"]]
    callable_addr = regs[cfg["callable_reg"]]
    owner_addr = _owner_addr(process, regs, cfg)
    callable_packet = _callable_packet(target, process, callable_addr, target_reg_value)

    state["call_counts"][name] = state["call_counts"].get(name, 0) + 1
    key = (
        name,
        callable_packet.get("vtable_libcp_va"),
        callable_packet.get("slot_0x30_libcp_va"),
        callable_packet.get("target_reg_libcp_va"),
    )
    key_s = "|".join(str(part) for part in key)
    state["target_counts"][key_s] = state["target_counts"].get(key_s, 0) + 1

    if len(state["samples"]) < state["sample_limit"]:
        sample = {
            "site": name,
            "site_va": site_va,
            "registers": regs,
            "callable": callable_packet,
            "owner": _owner_packet(process, owner_addr, cfg["owner_field"]),
            "descriptors": {
                reg: _descriptor_packet(process, regs[reg])
                for reg in cfg["descriptor_regs"]
            },
            "stack": _stack(thread),
        }
        state["samples"].append(sample)

    if state["call_counts"][name] >= state["site_cap"]:
        _disable_breakpoint(target.GetDebugger(), name)
        if name not in state["disabled_after_cap"]:
            state["disabled_after_cap"].append(name)
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    count = target.GetNumBreakpoints()
    if count < 3:
        _state()["errors"].append("expected at least 3 breakpoints")
        print("L16_SRC1_INDIRECT_ATTACH_ERROR expected at least 3 breakpoints")
        return
    order = [
        ("gate_0x3e4b09", gate),
        (CALL_SITES[0x342D99]["name"], callsite),
        (CALL_SITES[0x3449F0]["name"], callsite),
    ]
    ids = {}
    start = count - len(order)
    for index, (name, callback) in enumerate(order, start=start):
        bp = target.GetBreakpointAtIndex(index)
        bp.SetScriptCallbackFunction(
            f"src1_indirect_callable_targets_probe.{callback.__name__}"
        )
        if name != "gate_0x3e4b09":
            bp.SetEnabled(False)
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_SRC1_INDIRECT_ATTACHED", ids)


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
    print("L16_SRC1_INDIRECT_DRIVE_STEPS", steps)


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
    print("L16_SRC1_INDIRECT_WROTE", path)


def report(debugger):
    print("L16_SRC1_INDIRECT_BEGIN")
    print(json.dumps(payload(debugger), indent=2, sort_keys=True))
    print("L16_SRC1_INDIRECT_END")
