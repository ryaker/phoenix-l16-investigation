import builtins
import json
import struct


SITES = {
    0x26BBD0: "index_setter_26bbd0",
    0x26BE50: "caller_pre_29a140",
    0x29A1A0: "maker_after_299fd0",
    0x27786B: "xmm2_table_load_setup_27786b",
    0x27791D: "xmm2_xmm3_scalar_setup_27791d",
    0x277945: "xmm2_xmm3_broadcast_ready_277945",
}


def reset(label="", target_index=5, sample_cap=8):
    builtins.l16_scalar_origin = {
        "label": label,
        "target_index": target_index,
        "sample_cap": sample_cap,
        "target_object": None,
        "target_context": None,
        "caller_pre_breakpoint_installed": False,
        "deep_breakpoints_installed": False,
        "scalar_breakpoints_installed": False,
        "capture_complete": False,
        "terminated_after_capture": False,
        "drive_hit_step_cap": False,
        "breakpoint_ids": {},
        "counts": {name: 0 for name in SITES.values()},
        "target_counts": {},
        "setup_samples": [],
        "table_samples": [],
        "scalar_samples": [],
        "broadcast_samples": [],
        "paired_samples": [],
        "pending_table_by_thread": {},
        "pending_scalar_by_thread": {},
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_scalar_origin"):
        reset()
    return builtins.l16_scalar_origin


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


def _bytes_hex(process, addr, size):
    raw = _read(process, addr, size)
    return raw.hex() if raw is not None else None


def _u32_list(process, addr, count):
    raw = _read(process, addr, count * 4)
    if raw is None:
        return []
    return [_u32(raw, off) for off in range(0, len(raw), 4)]


def _qword_list(process, addr, count):
    raw = _read(process, addr, count * 8)
    if raw is None:
        return []
    return [_u64(raw, off) for off in range(0, len(raw), 8)]


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


def _stack(thread, max_frames=10):
    target = thread.GetProcess().GetTarget()
    out = []
    for index in range(min(thread.GetNumFrames(), max_frames)):
        frame = thread.GetFrameAtIndex(index)
        out.append(
            {
                "index": index,
                "pc": frame.GetPC(),
                "libcp_va": _module_va(target, frame.GetPC()),
                "function": frame.GetFunctionName(),
            }
        )
    return out


def _slot_key(offset):
    direction = "plus" if offset >= 0 else "minus"
    return f"rbp_{direction}_0x{abs(offset):x}"


def _stack_qwords(process, rbp, offsets):
    return {_slot_key(offset): _u64_at(process, rbp + offset) for offset in offsets}


def _descriptor(process, addr):
    raw = _read(process, addr, 0x30)
    if raw is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "width_0x10": _u32(raw, 0x10),
        "height_0x14": _u32(raw, 0x14),
        "stride_0x18": _u32(raw, 0x18),
        "field_0x1c": _u32(raw, 0x1C),
        "data_0x20": _u64(raw, 0x20),
        "aux_0x28": _u64(raw, 0x28),
        "qwords": [_u64(raw, off) for off in range(0, 0x30, 8)],
    }


def _source_local(process, addr):
    if not addr:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "control_u32_0x00": _u32_at(process, addr),
        "header_qwords_0x08_0x20": _qword_list(process, addr + 0x08, 3),
        "descriptor_0x20": _descriptor(process, addr + 0x20),
    }


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
        "bytes_0x60_0x70_hex": _bytes_hex(process, obj + 0x60, 16),
        "qwords": {f"0x{off:x}": _u64_at(process, obj + off) for off in qword_offsets},
        "dwords": {f"0x{off:x}": _u32_at(process, obj + off) for off in dword_offsets},
    }


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
        bp.SetScriptCallbackFunction("scalar_origin_probe.hit")
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


def _base_sample(thread, name, site_va, regs):
    return {
        "site": name,
        "site_va": site_va,
        "thread_id": thread.GetThreadID(),
        "target_object": _state().get("target_object"),
        "target_context": _state().get("target_context"),
        "registers": regs,
        "stack": _stack(thread),
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


def _target_object_from_stack(process, regs):
    return _u64_at(process, regs["rbp"] - 0x1C8)


def _target_stack_context(process, regs):
    rbp = regs["rbp"]
    obj = _target_object_from_stack(process, regs)
    return {
        "rbp": rbp,
        "object_from_stack_rbp_minus_0x1c8": obj,
        "object_fields": _object_fields(process, obj),
        "stack_qwords": _stack_qwords(
            process, rbp, (-0x1C8, -0x210, -0x200, -0x2E0, -0x208, -0x150)
        ),
        "record_lookup_from_r9": _record_index_for_r9(process, obj, regs.get("r9", 0)),
    }


def _target_scalar_context(frame, site_va, name):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    regs = _registers(frame)
    obj = _target_object_from_stack(process, regs)
    if not state.get("target_object") or obj != state.get("target_object"):
        return None
    sample = _base_sample(thread, name, site_va, regs)
    sample["target_stack_context"] = _target_stack_context(process, regs)
    sample["xmm_hex"] = {f"xmm{i}": _xmm_hex(frame, f"xmm{i}") for i in range(4)}
    return sample


def _capture_table_setup(frame, site_va, name):
    state = _state()
    sample = _target_scalar_context(frame, site_va, name)
    if sample is None:
        return False
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
    thread_key = str(sample["thread_id"])
    state["pending_table_by_thread"][thread_key] = sample
    if len(state["table_samples"]) < state["sample_cap"] * 4:
        state["table_samples"].append(sample)
    return False


def _capture_scalar_setup(frame, site_va, name):
    state = _state()
    sample = _target_scalar_context(frame, site_va, name)
    if sample is None:
        return False
    regs = sample["registers"]
    thread_key = str(sample["thread_id"])
    pending_table = state.get("pending_table_by_thread", {}).get(thread_key)
    sample["scalar_values_before_movd"] = {
        "xmm2_source_ecx_u32": regs["rcx"] & 0xFFFFFFFF,
        "xmm3_source_edx_u32": regs["rdx"] & 0xFFFFFFFF,
        "xmm2_expected_broadcast_u16": regs["rcx"] & 0xFFFF,
        "xmm3_expected_broadcast_u16": regs["rdx"] & 0xFFFF,
    }
    sample["matched_table_sample"] = pending_table if _same_context(sample, pending_table) else None
    state["pending_scalar_by_thread"][thread_key] = sample
    if len(state["scalar_samples"]) < state["sample_cap"] * 4:
        state["scalar_samples"].append(sample)
    return False


def _same_context(sample, prior):
    if not sample or not prior:
        return False
    regs = sample.get("registers", {})
    old = prior.get("registers", {})
    return (
        regs.get("rbp") == old.get("rbp")
        and regs.get("r9") == old.get("r9")
        and sample.get("thread_id") == prior.get("thread_id")
    )


def _capture_broadcast_ready(frame, site_va, name):
    state = _state()
    sample = _target_scalar_context(frame, site_va, name)
    if sample is None:
        return False
    thread_key = str(sample["thread_id"])
    scalar = state.get("pending_scalar_by_thread", {}).get(thread_key)
    if not _same_context(sample, scalar):
        return False
    table = scalar.get("matched_table_sample")
    sample["matched_scalar_sample"] = scalar
    sample["matched_table_sample"] = table
    state["broadcast_samples"].append(sample)
    state["paired_samples"].append(
        {
            "table": table,
            "scalar": scalar,
            "broadcast": sample,
        }
    )
    if len(state["paired_samples"]) >= state["sample_cap"]:
        state["capture_complete"] = True
        return True
    return False


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
        sample = _base_sample(thread, name, site_va, regs)
        sample["incoming_index_esi"] = incoming
        sample["setter_object"] = regs["rdi"]
        sample["target_object_after"] = state.get("target_object")
        state["setup_samples"].append(sample)
        return False

    if target_obj and site_va == 0x26BE50 and regs.get("r14") == target_obj:
        state["target_context"] = _context_from_caller(regs, target_obj)
        state["target_counts"][name] = state["target_counts"].get(name, 0) + 1
        if not state.get("deep_breakpoints_installed"):
            _install_breakpoints(target.GetDebugger(), {"maker_after_299fd0"})
            state["deep_breakpoints_installed"] = True
        state["setup_samples"].append(_base_sample(thread, name, site_va, regs))
        return False

    if site_va == 0x29A1A0 and _context_match_maker(regs):
        state["target_counts"][name] = state["target_counts"].get(name, 0) + 1
        sample = _base_sample(thread, name, site_va, regs)
        output_local = (state.get("target_context") or {}).get("output_local_rbp_minus_0xb0", 0)
        sample["output_local"] = _source_local(process, output_local)
        state["setup_samples"].append(sample)
        if not state.get("scalar_breakpoints_installed"):
            _install_breakpoints(
                target.GetDebugger(),
                {
                    "xmm2_table_load_setup_27786b",
                    "xmm2_xmm3_scalar_setup_27791d",
                    "xmm2_xmm3_broadcast_ready_277945",
                },
            )
            state["scalar_breakpoints_installed"] = True
        _disable_breakpoints(
            target.GetDebugger(),
            {
                "xmm2_table_load_setup_27786b",
                "xmm2_xmm3_scalar_setup_27791d",
                "xmm2_xmm3_broadcast_ready_277945",
            },
        )
        return False

    if site_va == 0x27786B:
        return _capture_table_setup(frame, site_va, name)
    if site_va == 0x27791D:
        return _capture_scalar_setup(frame, site_va, name)
    if site_va == 0x277945:
        return _capture_broadcast_ready(frame, site_va, name)
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
        bp.SetScriptCallbackFunction("scalar_origin_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_SCALAR_ORIGIN_ATTACHED", ids)


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


def drive_until_capture_or_exit(debugger, max_steps=4096):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process.IsValid() and process.GetState() == lldb.eStateStopped and steps < max_steps:
        if _state().get("capture_complete"):
            process.Kill()
            _state()["terminated_after_capture"] = True
            break
        steps += 1
        process.Continue()
    _state()["drive_steps"] = steps
    _state()["drive_hit_step_cap"] = (
        process.IsValid() and process.GetState() == lldb.eStateStopped and steps >= max_steps
    )
    print("L16_SCALAR_ORIGIN_DRIVE_STEPS", steps)


def payload(debugger):
    packet = dict(_state())
    packet["process"] = _process_packet(debugger)
    packet["breakpoint_hit_counts"] = _breakpoint_hit_counts(debugger)
    packet.pop("pending_table_by_thread", None)
    packet.pop("pending_scalar_by_thread", None)
    return packet


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_SCALAR_ORIGIN_WROTE", path)
