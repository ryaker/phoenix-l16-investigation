import builtins
import json
import struct


SITES = {
    0x26BBD0: "index_setter_26bbd0",
    0x26BE50: "caller_pre_29a140",
    0x29A1A0: "maker_after_299fd0",
    0x27786B: "table_load_setup_27786b",
}

STEP_SITES = {
    0x277903: "xmm4_ready_277903",
    0x277917: "product_ready_277917",
    0x27791B: "preadd_int_27791b",
    0x27791D: "postadd_scalar_27791d",
    0x277945: "broadcast_ready_277945",
}


def reset(label="", target_index=5, skip_table_hits=0):
    builtins.l16_xmm3_term_step = {
        "label": label,
        "target_index": target_index,
        "skip_table_hits": skip_table_hits,
        "target_table_hits": 0,
        "target_object": None,
        "target_context": None,
        "caller_pre_breakpoint_installed": False,
        "maker_breakpoint_installed": False,
        "table_breakpoint_installed": False,
        "capture_complete": False,
        "terminated_after_capture": False,
        "step_hit_cap": False,
        "breakpoint_ids": {},
        "counts": {name: 0 for name in {**SITES, **STEP_SITES}.values()},
        "target_counts": {},
        "setup_samples": [],
        "packet": {},
        "step_trace": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_xmm3_term_step"):
        reset()
    return builtins.l16_xmm3_term_step


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    if not addr or size <= 0:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u16(data, off=0):
    return struct.unpack_from("<H", data, off)[0]


def _u32(data, off=0):
    return struct.unpack_from("<I", data, off)[0]


def _u64(data, off=0):
    return struct.unpack_from("<Q", data, off)[0]


def _f32(data, off=0):
    return struct.unpack_from("<f", data, off)[0]


def _u16_at(process, addr):
    raw = _read(process, addr, 2)
    return _u16(raw) if raw is not None else None


def _u32_at(process, addr):
    raw = _read(process, addr, 4)
    return _u32(raw) if raw is not None else None


def _u64_at(process, addr):
    raw = _read(process, addr, 8)
    return _u64(raw) if raw is not None else None


def _f32_at(process, addr):
    raw = _read(process, addr, 4)
    return _f32(raw) if raw is not None else None


def _u32_list(process, addr, count):
    raw = _read(process, addr, count * 4)
    if raw is None:
        return []
    return [_u32(raw, off) for off in range(0, len(raw), 4)]


def _xmm_hex(frame, name):
    lldb = builtins.__import__("lldb")
    reg = frame.FindRegister(name)
    if not reg or not reg.IsValid():
        return None
    data = reg.GetData()
    if not data or data.GetByteSize() < 16:
        return None
    error = lldb.SBError()
    out = bytearray()
    for offset in range(16):
        out.append(data.GetUnsignedInt8(error, offset))
        if not error.Success():
            return None
    return bytes(out).hex()


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


def _install_breakpoints(debugger, names):
    state = _state()
    target = debugger.GetSelectedTarget()
    base = _libcp_base(target)
    if base is None:
        state["errors"].append("cannot install breakpoints: libcp base missing")
        return
    ids = state.setdefault("breakpoint_ids", {})
    for va, name in SITES.items():
        if name not in names or name in ids:
            continue
        bp = target.BreakpointCreateByAddress(base + va)
        if not bp or not bp.IsValid():
            state["errors"].append(f"failed to install breakpoint {name} {va:#x}")
            continue
        bp.SetScriptCallbackFunction("xmm3_term_step_probe.hit")
        ids[name] = bp.GetID()


def _disable_breakpoints(debugger, keep_names=()):
    keep = set(keep_names)
    target = debugger.GetSelectedTarget()
    for name, bp_id in _state().get("breakpoint_ids", {}).items():
        if name in keep:
            continue
        bp = target.FindBreakpointByID(bp_id)
        if bp and bp.IsValid():
            bp.SetEnabled(False)


def _context_from_caller(regs, target_obj):
    rbp = regs["rbp"]
    return {
        "target_object": target_obj,
        "caller_rbp": rbp,
        "output_local_rbp_minus_0xb0": rbp - 0xB0,
        "input_descriptor_rbp_minus_0x60": rbp - 0x60,
        "source_arg_target_plus_0x208": target_obj + 0x208,
    }


def _context_match_maker(regs):
    ctx = _state().get("target_context") or {}
    return (
        ctx
        and regs.get("rbx") == ctx.get("output_local_rbp_minus_0xb0")
        and regs.get("r12") == ctx.get("input_descriptor_rbp_minus_0x60")
        and regs.get("r15") == ctx.get("source_arg_target_plus_0x208")
    )


def _object_fields(process, obj):
    if not obj:
        return {"addr": obj, "read_ok": False}
    qword_offsets = (0x108, 0x138, 0x168, 0x198, 0x1E8, 0x200)
    dword_offsets = (0x130, 0x238)
    return {
        "addr": obj,
        "read_ok": True,
        "u16_0x56": _u16_at(process, obj + 0x56),
        "f32_0x58": _f32_at(process, obj + 0x58),
        "bytes_0x60_0x70_hex": (_read(process, obj + 0x60, 16) or b"").hex(),
        "qwords": {f"0x{off:x}": _u64_at(process, obj + off) for off in qword_offsets},
        "dwords": {f"0x{off:x}": _u32_at(process, obj + off) for off in dword_offsets},
    }


def _record_index_for_r9(process, obj, r9, max_offsets=128):
    fields = _object_fields(process, obj)
    q = fields.get("qwords", {})
    record_base = q.get("0x108") or 0
    offset_table = q.get("0x138") or 0
    offsets = _u32_list(process, offset_table, max_offsets) if offset_table else []
    for index, offset in enumerate(offsets):
        if record_base + offset + 8 == r9:
            return {"record_index": index, "record_offset": offset, "record_base": record_base}
    return {
        "record_index": None,
        "record_offset": None,
        "record_base": record_base,
        "searched_offsets": len(offsets),
    }


def _target_context(process, regs):
    rbp = regs["rbp"]
    obj = _u64_at(process, rbp - 0x1C8)
    return {
        "rbp": rbp,
        "object_from_stack_rbp_minus_0x1c8": obj,
        "object_fields": _object_fields(process, obj),
        "stack_qwords": {
            "rbp_minus_0x1c8": obj,
            "rbp_minus_0x210": _u64_at(process, rbp - 0x210),
        },
        "record_lookup_from_r9": _record_index_for_r9(process, obj, regs.get("r9", 0)),
    }


def _sample(frame, site_va, name):
    thread = frame.GetThread()
    process = thread.GetProcess()
    regs = _registers(frame)
    obj = _u64_at(process, regs["rbp"] - 0x1C8)
    sample = {
        "site": name,
        "site_va": site_va,
        "thread_id": thread.GetThreadID(),
        "target_object": _state().get("target_object"),
        "target_context": _state().get("target_context"),
        "registers": regs,
        "target_stack_context": _target_context(process, regs),
        "xmm_hex": {f"xmm{i}": _xmm_hex(frame, f"xmm{i}") for i in range(5)},
    }
    if obj != _state().get("target_object"):
        sample["object_mismatch"] = True
    return sample


def _capture_table(frame, site_va, name):
    sample = _sample(frame, site_va, name)
    process = frame.GetThread().GetProcess()
    regs = sample["registers"]
    table_base = regs["rdi"]
    table_index = regs["rcx"]
    table_addr = (table_base + (2 * table_index)) & 0xFFFFFFFFFFFFFFFF
    sample["table_load"] = {
        "table_base_rdi": table_base,
        "table_index_rcx": table_index,
        "table_addr_rdi_plus_2rcx": table_addr,
        "table_value_u16": _u16_at(process, table_addr),
        "stack_minus_0x210_eq_table_base": _u64_at(process, regs["rbp"] - 0x210)
        == table_base,
    }
    _state()["packet"]["table"] = sample


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
    target_obj = state.get("target_object")

    if site_va == 0x26BBD0:
        incoming = regs["rsi"] & 0xFFFFFFFF
        if incoming == state["target_index"]:
            state["target_object"] = regs["rdi"]
            if not state.get("caller_pre_breakpoint_installed"):
                _install_breakpoints(target.GetDebugger(), {"caller_pre_29a140"})
                state["caller_pre_breakpoint_installed"] = True
        sample = {
            "site": name,
            "site_va": site_va,
            "thread_id": thread.GetThreadID(),
            "registers": regs,
            "incoming_index_esi": incoming,
            "setter_object": regs["rdi"],
            "target_object_after": state.get("target_object"),
        }
        state["setup_samples"].append(sample)
        return False

    if target_obj and site_va == 0x26BE50 and regs.get("r14") == target_obj:
        state["target_context"] = _context_from_caller(regs, target_obj)
        state["target_counts"][name] = state["target_counts"].get(name, 0) + 1
        if not state.get("maker_breakpoint_installed"):
            _install_breakpoints(target.GetDebugger(), {"maker_after_299fd0"})
            state["maker_breakpoint_installed"] = True
        state["setup_samples"].append({"site": name, "site_va": site_va, "thread_id": thread.GetThreadID(), "registers": regs})
        return False

    if site_va == 0x29A1A0 and _context_match_maker(regs):
        state["target_counts"][name] = state["target_counts"].get(name, 0) + 1
        state["setup_samples"].append({"site": name, "site_va": site_va, "thread_id": thread.GetThreadID(), "registers": regs})
        if not state.get("table_breakpoint_installed"):
            _install_breakpoints(target.GetDebugger(), {"table_load_setup_27786b"})
            state["table_breakpoint_installed"] = True
        _disable_breakpoints(target.GetDebugger(), {"table_load_setup_27786b"})
        return False

    if site_va == 0x27786B:
        state["target_table_hits"] = state.get("target_table_hits", 0) + 1
        if state["target_table_hits"] <= state.get("skip_table_hits", 0):
            return False
        _capture_table(frame, site_va, name)
        return True
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    ids = {}
    for index in range(target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(index)
        if not bp or not bp.IsValid() or bp.GetNumLocations() < 1:
            continue
        loc = bp.GetLocationAtIndex(0)
        site_va = loc.GetAddress().GetFileAddress()
        name = SITES.get(site_va)
        if name is None:
            continue
        bp.SetScriptCallbackFunction("xmm3_term_step_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_XMM3_TERM_ATTACHED", ids)


def _selected_frame(debugger):
    process = debugger.GetSelectedTarget().GetProcess()
    thread = process.GetSelectedThread()
    if not thread or not thread.IsValid():
        thread = process.GetThreadAtIndex(0)
    return thread.GetFrameAtIndex(0)


def _current_va(debugger):
    frame = _selected_frame(debugger)
    return _module_va(debugger.GetSelectedTarget(), frame.GetPC())


def _capture_current(debugger):
    frame = _selected_frame(debugger)
    site_va = _module_va(debugger.GetSelectedTarget(), frame.GetPC())
    name = STEP_SITES.get(site_va)
    if name is None:
        _state()["errors"].append(f"cannot capture unexpected pc {site_va}")
        return
    _state()["counts"][name] = _state()["counts"].get(name, 0) + 1
    _state()["packet"][name.split("_277")[0]] = _sample(frame, site_va, name)


def _step_to(debugger, expected_va, max_steps=64):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    thread = process.GetSelectedThread()
    if not thread or not thread.IsValid():
        thread = process.GetThreadAtIndex(0)
    steps = 0
    while process.IsValid() and process.GetState() == lldb.eStateStopped and steps < max_steps:
        pc = _module_va(debugger.GetSelectedTarget(), thread.GetFrameAtIndex(0).GetPC())
        _state()["step_trace"].append(pc)
        if pc == expected_va:
            return True
        thread.StepInstruction(False)
        steps += 1
    _state()["step_hit_cap"] = True
    _state()["errors"].append(f"failed to step to {expected_va:#x}; current={_current_va(debugger)}")
    return False


def drive_step_packet(debugger):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    if not process or not process.IsValid() or process.GetState() != lldb.eStateStopped:
        _state()["errors"].append("process not stopped for step packet")
        return
    if _current_va(debugger) != 0x27786B:
        _state()["errors"].append(f"initial stop is not table site: {_current_va(debugger)}")
        return
    plan = (
        0x277903,
        0x277917,
        0x27791B,
        0x27791D,
        0x277945,
    )
    for va in plan:
        if not _step_to(debugger, va):
            return
        _capture_current(debugger)
    _state()["capture_complete"] = True
    process.Kill()
    _state()["terminated_after_capture"] = True
    print("L16_XMM3_TERM_STEPPED", len(_state().get("step_trace", [])))


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


def payload(debugger):
    packet = dict(_state())
    packet["process"] = _process_packet(debugger)
    return packet


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_XMM3_TERM_WROTE", path)
