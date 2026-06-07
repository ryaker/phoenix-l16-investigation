import builtins
import json
import struct


SITES = {
    0x26BBD0: "index_setter_26bbd0",
    0x26BE50: "caller_pre_29a140",
    0x29A1A0: "maker_after_299fd0",
    0x299C70: "later_299c70_entry",
}


def reset(label="", target_index=5, watch_count=2, watch_size=8, watch_hit_cap=32):
    builtins.l16_vector_formula = {
        "label": label,
        "target_index": target_index,
        "watch_count": watch_count,
        "watch_size": watch_size,
        "watch_hit_cap": watch_hit_cap,
        "target_object": None,
        "target_context": None,
        "caller_pre_breakpoint_installed": False,
        "deep_breakpoints_installed": False,
        "watchpoints_armed": False,
        "watchpoints_disabled_after_cap": False,
        "breakpoint_ids": {},
        "watchpoint_ids": {},
        "counts": {name: 0 for name in SITES.values()},
        "target_counts": {},
        "setup_samples": [],
        "watchpoint_samples": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_vector_formula"):
        reset()
    return builtins.l16_vector_formula


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


def _qword_list(process, addr, count):
    raw = _read(process, addr, count * 8)
    if raw is None:
        return []
    return [_u64(raw, off) for off in range(0, len(raw), 8)]


def _bytes_hex(process, addr, size):
    raw = _read(process, addr, size)
    return raw.hex() if raw is not None else None


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


def _stack(thread, max_frames=14):
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
            }
        )
    return frames


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
        "control_u32_0x00": _u32_list(process, addr, 1)[0]
        if _u32_list(process, addr, 1)
        else None,
        "header_qwords_0x08_0x20": _qword_list(process, addr + 0x08, 3),
        "descriptor_0x20": _descriptor(process, addr + 0x20),
    }


def _source_object(process, obj):
    return _source_local(process, obj + 0xF8 if obj else 0)


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
        bp.SetScriptCallbackFunction("vector_formula_probe.hit")
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


def _u16_header(process, addr):
    raw = _read(process, addr, 8)
    if raw is None:
        return None
    return [_u16(raw, off) for off in range(0, 8, 2)]


def _slot_key(offset):
    direction = "plus" if offset >= 0 else "minus"
    return f"rbp_{direction}_0x{abs(offset):x}"


def _stack_qwords(process, rbp, offsets):
    return {_slot_key(offset): _u64_at(process, rbp + offset) for offset in offsets}


def _stack_dwords(process, rbp, offsets):
    return {_slot_key(offset): _u32_at(process, rbp + offset) for offset in offsets}


def _object_fields(process, obj):
    if not obj:
        return {"addr": obj, "read_ok": False}
    qword_offsets = (
        0x108,
        0x138,
        0x148,
        0x158,
        0x168,
        0x178,
        0x180,
        0x188,
        0x198,
        0x1A8,
        0x1B0,
        0x1D0,
        0x1D8,
        0x1E0,
        0x1E8,
        0x1F8,
        0x200,
        0x240,
        0x248,
        0x288,
    )
    dword_offsets = (0x130, 0x220, 0x238, 0x23C)
    byte_offsets = (0x20, 0x160, 0x190)
    return {
        "addr": obj,
        "read_ok": True,
        "u16_0x56": _u16_at(process, obj + 0x56),
        "f32_0x58": _f32_at(process, obj + 0x58),
        "bytes_0x60_0x70_hex": _bytes_hex(process, obj + 0x60, 16),
        "qwords": {f"0x{off:x}": _u64_at(process, obj + off) for off in qword_offsets},
        "dwords": {f"0x{off:x}": _u32_at(process, obj + off) for off in dword_offsets},
        "bytes": {
            f"0x{off:x}": (
                _read(process, obj + off, 1).hex()
                if _read(process, obj + off, 1) is not None
                else None
            )
            for off in byte_offsets
        },
    }


def _origin_context(process, regs, meta):
    rbp = regs["rbp"]
    target_obj = _state().get("target_object")
    obj = _u64_at(process, rbp - 0x1C8)
    stack_qwords = _stack_qwords(
        process,
        rbp,
        (
            -0x1C8,
            -0x2E0,
            -0x1A0,
            -0x208,
            -0x300,
            -0x150,
            -0x308,
            -0x170,
            -0x158,
            -0x210,
            -0x310,
            -0x280,
            -0x160,
            -0x200,
            -0x318,
            -0x1D0,
            -0x188,
            -0x258,
            -0x250,
            -0x228,
        ),
    )
    stack_dwords = _stack_dwords(process, rbp, (-0x248, -0x1F8, -0x1D4, -0x244))
    fields = _object_fields(process, obj)
    q = fields.get("qwords", {})
    d = fields.get("dwords", {})
    watch_addr = meta.get("watch_addr", 0)
    record_offset = meta.get("record_offset", 0)
    r9_store_base = (regs["r9"] + (2 * regs["rdx"])) & 0xFFFFFFFFFFFFFFFF
    return {
        "rbp": rbp,
        "target_object": target_obj,
        "object_from_stack_rbp_minus_0x1c8": obj,
        "object_fields": fields,
        "stack_qwords": stack_qwords,
        "stack_dwords": stack_dwords,
        "relationships": {
            "object_eq_target_object": bool(target_obj and obj == target_obj),
            "stack_minus_0x200_eq_object_0x168": stack_qwords.get("rbp_minus_0x200")
            == q.get("0x168"),
            "stack_minus_0x210_eq_object_0x198": stack_qwords.get("rbp_minus_0x210")
            == q.get("0x198"),
            "stack_minus_0x1d0_eq_object_0x180": stack_qwords.get("rbp_minus_0x1d0")
            == q.get("0x180"),
            "stack_minus_0x188_eq_object_0x1b0": stack_qwords.get("rbp_minus_0x188")
            == q.get("0x1b0"),
            "r10_eq_stack_minus_0x2e0": regs["r10"] == stack_qwords.get("rbp_minus_0x2e0"),
            "r9_eq_object_record_base_plus_record_offset_plus_8": regs["r9"]
            == (q.get("0x108") or 0) + record_offset + 8,
            "watch_addr_eq_r9_plus_2rdx": watch_addr == r9_store_base,
            "object_0x130_stride": d.get("0x130"),
        },
    }


def _arm_watchpoints(process, target, output_local):
    state = _state()
    if state.get("watchpoints_armed"):
        return
    local = _source_local(process, output_local)
    header = local.get("header_qwords_0x08_0x20") or []
    desc = local.get("descriptor_0x20") or {}
    if len(header) < 3 or not desc.get("read_ok"):
        state["errors"].append("cannot arm watchpoints: source local unreadable")
        return
    record_base = header[1]
    offset_table = desc.get("aux_0x28", 0)
    offsets = _u32_list(process, offset_table, state.get("watch_count", 2))
    if not record_base or len(offsets) < state.get("watch_count", 2):
        state["errors"].append("cannot arm watchpoints: missing record base/offsets")
        return

    lldb = builtins.__import__("lldb")
    for index, offset in enumerate(offsets[: state.get("watch_count", 2)]):
        addr = record_base + offset + 8
        error = lldb.SBError()
        wp = target.WatchAddress(addr, state.get("watch_size", 8), False, True, error)
        meta = {
            "record_index": index,
            "record_offset": offset,
            "watch_addr": addr,
            "watch_size": state.get("watch_size", 8),
            "record_header_u16": _u16_header(process, record_base + offset),
            "bytes_before_hex": _bytes_hex(process, addr, state.get("watch_size", 8)),
            "payload16_before_hex": _bytes_hex(process, addr, 16),
        }
        if wp and wp.IsValid() and error.Success():
            meta["watchpoint_id"] = wp.GetID()
            meta["watchpoint_error"] = None
            state["watchpoint_ids"][str(wp.GetID())] = meta
        else:
            meta["watchpoint_id"] = None
            meta["watchpoint_error"] = error.GetCString()
            state["errors"].append({"error": "watchpoint arm failed", "watch": meta})
    state["watchpoints_armed"] = bool(state["watchpoint_ids"])


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


def _vector_context(process, frame, regs, meta):
    rax = regs["rax"]
    rdx = regs["rdx"]
    mask = 0xFFFFFFFFFFFFFFFF
    addrs = {
        "src0_rsi_plus_2rax": (regs["rsi"] + (2 * rax)) & mask,
        "src6_rdi_plus_2rdx": (regs["rdi"] + (2 * rdx)) & mask,
        "accum_r10_plus_2rdx": (regs["r10"] + (2 * rdx)) & mask,
        "side_rcx_plus_2rdx": (regs["rcx"] + (2 * rdx)) & mask,
        "payload_r9_plus_2rdx": (regs["r9"] + (2 * rdx)) & mask,
    }
    return {
        "addresses": addrs,
        "memory16_hex": {
            key: _bytes_hex(process, addr, 16) for key, addr in addrs.items()
        },
        "payload16_before_hit_hex": meta.get("payload16_before_hex"),
        "origin_context": _origin_context(process, regs, meta),
        "xmm_hex": {f"xmm{i}": _xmm_hex(frame, f"xmm{i}") for i in range(8)},
    }


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

    is_target = False
    if target_obj and site_va == 0x26BE50 and regs.get("r14") == target_obj:
        is_target = True
        state["target_context"] = _context_from_caller(regs, target_obj)
        if not state.get("deep_breakpoints_installed"):
            _install_breakpoints(target.GetDebugger(), {"maker_after_299fd0", "later_299c70_entry"})
            state["deep_breakpoints_installed"] = True
    elif site_va == 0x29A1A0:
        is_target = bool(_context_match_maker(regs))
    elif target_obj and site_va == 0x299C70:
        is_target = regs.get("rsi") == target_obj + 0xF8

    if not is_target:
        return False

    state["target_counts"][name] = state["target_counts"].get(name, 0) + 1
    sample = _base_sample(thread, name, site_va, regs)
    ctx = state.get("target_context") or {}
    output_local = ctx.get("output_local_rbp_minus_0xb0", 0)
    sample["output_local"] = _source_local(process, output_local)
    sample["source_object_0xf8"] = _source_object(process, target_obj)

    if site_va == 0x29A1A0:
        _arm_watchpoints(process, target, output_local)
        sample["armed_watchpoints"] = dict(state.get("watchpoint_ids", {}))
        _disable_breakpoints(target.GetDebugger(), {"later_299c70_entry"})
    elif site_va == 0x299C70:
        sample["rsi_equals_target_plus_0xf8"] = regs.get("rsi") == target_obj + 0xF8
        _disable_breakpoints(target.GetDebugger())

    state["setup_samples"].append(sample)
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
        bp.SetScriptCallbackFunction("vector_formula_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_VECTOR_FORMULA_ATTACHED", ids)


def _watchpoint_hit_counts(debugger):
    target = debugger.GetSelectedTarget()
    out = {}
    for wp_id in _state().get("watchpoint_ids", {}):
        wp = target.FindWatchpointByID(int(wp_id))
        out[wp_id] = wp.GetHitCount() if wp and wp.IsValid() else None
    return out


def _disable_watchpoints(debugger):
    target = debugger.GetSelectedTarget()
    for wp_id in _state().get("watchpoint_ids", {}):
        wp = target.FindWatchpointByID(int(wp_id))
        if wp and wp.IsValid():
            wp.SetEnabled(False)
    _state()["watchpoints_disabled_after_cap"] = True


def _record_watchpoint_stop(debugger):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    if not process or not process.IsValid():
        return
    target = process.GetTarget()
    for thread in process:
        if thread.GetStopReason() != lldb.eStopReasonWatchpoint:
            continue
        wp_id = thread.GetStopReasonDataAtIndex(0)
        meta = state.get("watchpoint_ids", {}).get(str(wp_id), {})
        frame = thread.GetFrameAtIndex(0)
        regs = _registers(frame)
        watch_addr = meta.get("watch_addr", 0)
        mask = 0xFFFFFFFFFFFFFFFF
        r9_store_base = (regs["r9"] + (2 * regs["rdx"])) & mask
        rcx_store_base = (regs["rcx"] + (2 * regs["rdx"])) & mask
        vector_context = _vector_context(process, frame, regs, meta)
        payload_after = vector_context["memory16_hex"]["payload_r9_plus_2rdx"]
        sample = {
            "watchpoint_id": wp_id,
            "watchpoint": dict(meta),
            "thread_id": thread.GetThreadID(),
            "pc": frame.GetPC(),
            "libcp_va": _module_va(target, frame.GetPC()),
            "function": frame.GetFunctionName(),
            "registers": regs,
            "store_address_disambiguation": {
                "watch_addr": watch_addr,
                "r9_plus_2rdx": r9_store_base,
                "rcx_plus_2rdx": rcx_store_base,
                "watch_minus_r9_plus_2rdx": watch_addr - r9_store_base,
                "watch_minus_rcx_plus_2rdx": watch_addr - rcx_store_base,
                "matches_r9_16byte_store": 0 <= watch_addr - r9_store_base < 16,
                "matches_rcx_16byte_store": 0 <= watch_addr - rcx_store_base < 16,
            },
            "vector_context": vector_context,
            "stack": _stack(thread),
        }
        state["watchpoint_samples"].append(sample)
        if payload_after is not None:
            meta["payload16_before_hex"] = payload_after
            meta["bytes_before_hex"] = payload_after[: meta.get("watch_size", 8) * 2]
    if (
        len(state.get("watchpoint_samples", [])) >= state.get("watch_hit_cap", 32)
        and not state.get("watchpoints_disabled_after_cap")
    ):
        _disable_watchpoints(debugger)


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
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process.IsValid() and process.GetState() == lldb.eStateStopped and steps < max_steps:
        _record_watchpoint_stop(debugger)
        steps += 1
        process.Continue()
    _state()["drive_steps"] = steps
    _state()["drive_hit_step_cap"] = (
        process.IsValid() and process.GetState() == lldb.eStateStopped and steps >= max_steps
    )
    print("L16_VECTOR_FORMULA_DRIVE_STEPS", steps)


def payload(debugger):
    _record_watchpoint_stop(debugger)
    packet = dict(_state())
    packet["process"] = _process_packet(debugger)
    packet["breakpoint_hit_counts"] = _breakpoint_hit_counts(debugger)
    packet["watchpoint_hit_counts"] = _watchpoint_hit_counts(debugger)
    return packet


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_VECTOR_FORMULA_WROTE", path)
