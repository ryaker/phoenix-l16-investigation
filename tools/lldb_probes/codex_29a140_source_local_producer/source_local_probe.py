import builtins
import json
import struct


SITES = {
    0x26BBD0: "index_setter_26bbd0",
    0x26BE50: "caller_pre_29a140",
    0x29A140: "maker_29a140_entry",
    0x29A182: "maker_after_299eb0",
    0x29A192: "maker_after_header_copy_28f490",
    0x29A1A0: "maker_after_299fd0",
    0x26BE55: "caller_post_29a140",
    0x26BE73: "caller_pre_header_move_28f420",
    0x26BE89: "caller_pre_descriptor_move_f340",
    0x26E4C6: "later_source_index_branch",
    0x299C70: "later_299c70_entry",
    0x267010: "later_267010_entry",
}


def reset(label="", target_index=5, sample_limit=260):
    builtins.l16_29a140_source_local = {
        "label": label,
        "target_index": target_index,
        "target_object": None,
        "target_setter_hits": 0,
        "caller_pre_breakpoint_installed": False,
        "deep_breakpoints_installed": False,
        "target_context": None,
        "header_src_return_ptr": None,
        "sample_limit": sample_limit,
        "counts": {name: 0 for name in SITES.values()},
        "target_counts": {},
        "breakpoint_ids": {},
        "samples": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_29a140_source_local"):
        reset()
    return builtins.l16_29a140_source_local


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


def _u16(data, off=0):
    return struct.unpack_from("<H", data, off)[0]


def _u32(data, off=0):
    return struct.unpack_from("<I", data, off)[0]


def _u64(data, off=0):
    return struct.unpack_from("<Q", data, off)[0]


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
    names = (
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
    return {name: _u(frame, name) for name in names}


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


def _u16_list(process, addr, count):
    raw = _read(process, addr, count * 2)
    if raw is None:
        return []
    return [_u16(raw, off) for off in range(0, len(raw), 2)]


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


def _descriptor(process, addr):
    raw = _read(process, addr, 0x30)
    if raw is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "u32_0x00": _u32(raw, 0x00),
        "u32_0x04": _u32(raw, 0x04),
        "u32_0x08": _u32(raw, 0x08),
        "u32_0x0c": _u32(raw, 0x0C),
        "width_0x10": _u32(raw, 0x10),
        "height_0x14": _u32(raw, 0x14),
        "stride_0x18": _u32(raw, 0x18),
        "field_0x1c": _u32(raw, 0x1C),
        "data_0x20": _u64(raw, 0x20),
        "aux_0x28": _u64(raw, 0x28),
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
        "qwords_0x00_0x50": _qword_list(process, addr, 10),
        "header_qwords_0x08_0x20": _qword_list(process, addr + 0x08, 3),
        "record_base_0x10": _qword_list(process, addr + 0x10, 1)[0]
        if _qword_list(process, addr + 0x10, 1)
        else None,
        "descriptor_0x20": _descriptor(process, addr + 0x20),
    }


def _source_object(process, obj):
    return _source_local(process, obj + 0xF8 if obj else 0)


def _input_descriptor(process, addr):
    desc = _descriptor(process, addr)
    if desc.get("read_ok"):
        desc["first_u16_values"] = _u16_list(process, desc.get("data_0x20", 0), 16)
    return desc


def _append_sample(sample):
    state = _state()
    if len(state["samples"]) < state["sample_limit"]:
        state["samples"].append(sample)


def _set_target_breakpoints_enabled(debugger, enabled):
    state = _state()
    target = debugger.GetSelectedTarget()
    for name, bp_id in state.get("breakpoint_ids", {}).items():
        if name == "index_setter_26bbd0":
            continue
        bp = target.FindBreakpointByID(bp_id)
        if bp and bp.IsValid():
            bp.SetEnabled(enabled)
    state["deep_breakpoints_installed"] = enabled


def _install_breakpoints(debugger, names):
    state = _state()
    target = debugger.GetSelectedTarget()
    base = _libcp_base(target)
    if base is None:
        state["errors"].append("cannot install target breakpoints: libcp base missing")
        return
    ids = state.setdefault("breakpoint_ids", {})
    for va, name in SITES.items():
        if name not in names or name in ids:
            continue
        bp = target.BreakpointCreateByAddress(base + va)
        if not bp or not bp.IsValid():
            state["errors"].append(f"failed to install breakpoint {name} {va:#x}")
            continue
        bp.SetScriptCallbackFunction("source_local_probe.hit")
        ids[name] = bp.GetID()


def _install_caller_pre_breakpoint(debugger):
    state = _state()
    if state.get("caller_pre_breakpoint_installed"):
        return
    _install_breakpoints(debugger, {"caller_pre_29a140"})
    state["caller_pre_breakpoint_installed"] = True


def _install_deep_breakpoints(debugger):
    state = _state()
    if state.get("deep_breakpoints_installed"):
        return
    _install_breakpoints(
        debugger,
        {
            "maker_29a140_entry",
            "maker_after_299eb0",
            "maker_after_header_copy_28f490",
            "maker_after_299fd0",
            "caller_post_29a140",
            "caller_pre_header_move_28f420",
            "caller_pre_descriptor_move_f340",
            "later_source_index_branch",
            "later_299c70_entry",
            "later_267010_entry",
        },
    )
    state["deep_breakpoints_installed"] = True


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


def _context_match_entry(regs):
    ctx = _state().get("target_context") or {}
    return (
        ctx
        and regs.get("rdi") == ctx.get("output_local_rbp_minus_0xb0")
        and regs.get("rsi") == ctx.get("input_descriptor_rbp_minus_0x60")
        and regs.get("rdx") == ctx.get("source_arg_target_plus_0x208")
        and (regs.get("rcx") & 0xFFFFFFFF) == 8
    )


def _base_sample(thread, name, site_va, regs):
    target_obj = _state().get("target_object")
    return {
        "site": name,
        "site_va": site_va,
        "thread_id": thread.GetThreadID(),
        "target_object": target_obj,
        "target_context": _state().get("target_context"),
        "registers": regs,
        "stack": _stack(thread),
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
            state["target_setter_hits"] = state.get("target_setter_hits", 0) + 1
            state["target_object"] = regs["rdi"]
            _install_caller_pre_breakpoint(target.GetDebugger())
        sample = _base_sample(thread, name, site_va, regs)
        sample["incoming_index_esi"] = incoming
        sample["setter_object"] = regs["rdi"]
        sample["target_object_after"] = state.get("target_object")
        sample["target_setter_hits_after"] = state.get("target_setter_hits", 0)
        _append_sample(sample)
        return False

    is_target = False
    if target_obj and site_va == 0x26BE50 and regs.get("r14") == target_obj:
        is_target = True
        state["target_context"] = _context_from_caller(regs, target_obj)
        _install_deep_breakpoints(target.GetDebugger())
    elif target_obj and site_va in (0x26BE55, 0x26BE73, 0x26BE89):
        is_target = regs.get("r14") == target_obj
    elif site_va == 0x29A140:
        is_target = bool(_context_match_entry(regs))
    elif site_va in (0x29A182, 0x29A192, 0x29A1A0):
        is_target = bool(_context_match_maker(regs))
    elif target_obj and site_va == 0x26E4C6:
        is_target = regs.get("r12") == target_obj or regs.get("rdx") == target_obj + 0xF8
    elif target_obj and site_va == 0x299C70:
        is_target = regs.get("rsi") == target_obj + 0xF8
    elif target_obj and site_va == 0x267010:
        is_target = regs.get("rdx") == target_obj + 0xE0

    if not is_target:
        return False

    state["target_counts"][name] = state["target_counts"].get(name, 0) + 1
    sample = _base_sample(thread, name, site_va, regs)
    ctx = state.get("target_context") or {}
    output_local = ctx.get("output_local_rbp_minus_0xb0", 0)
    input_desc = ctx.get("input_descriptor_rbp_minus_0x60", 0)

    sample["source_object_0xf8"] = _source_object(process, target_obj)
    sample["output_local"] = _source_local(process, output_local)
    sample["input_descriptor"] = _input_descriptor(process, input_desc)

    if site_va == 0x26BE50:
        sample["call_args"] = {
            "rdi_is_output_local": regs["rdi"] == output_local,
            "rsi_is_input_descriptor": regs["rsi"] == input_desc,
            "rdx_is_target_plus_0x208": regs["rdx"] == target_obj + 0x208,
            "ecx_low32": regs["rcx"] & 0xFFFFFFFF,
        }
    elif site_va == 0x29A140:
        sample["entry_args"] = {
            "rdi_is_output_local": regs["rdi"] == output_local,
            "rsi_is_input_descriptor": regs["rsi"] == input_desc,
            "rdx_is_target_plus_0x208": regs["rdx"] == target_obj + 0x208,
            "ecx_low32": regs["rcx"] & 0xFFFFFFFF,
        }
    elif site_va == 0x29A182:
        state["header_src_return_ptr"] = regs["rax"]
        sample["header_src_return_ptr"] = regs["rax"]
        sample["header_src_qwords_0x40"] = _qword_list(process, regs["rax"], 8)
        sample["header_src_bytes_0x40_hex"] = _bytes_hex(process, regs["rax"], 0x40)
    elif site_va == 0x29A192:
        sample["header_src_return_ptr"] = state.get("header_src_return_ptr")
        sample["header_src_qwords_0x40"] = _qword_list(
            process, state.get("header_src_return_ptr") or 0, 8
        )
        sample["copied_header_qwords_at_output_plus_0x08"] = _qword_list(
            process, output_local + 0x08, 8
        )
    elif site_va == 0x29A1A0:
        sample["header_src_return_ptr"] = state.get("header_src_return_ptr")
        sample["post_299fd0_record_samples"] = _record_samples_from_source_local(
            process, output_local
        )
    elif site_va == 0x26BE55:
        sample["post_return_record_samples"] = _record_samples_from_source_local(
            process, output_local
        )
    elif site_va == 0x26BE73:
        sample["move_28f420"] = {
            "dest_is_target_plus_0x100": regs["rdi"] == target_obj + 0x100,
            "src_is_output_plus_0x08": regs["rsi"] == output_local + 0x08,
            "dest_rdi": regs["rdi"],
            "src_rsi": regs["rsi"],
        }
    elif site_va == 0x26BE89:
        sample["move_f340"] = {
            "dest_is_target_plus_0x118": regs["rdi"] == target_obj + 0x118,
            "src_is_output_plus_0x20": regs["rsi"] == output_local + 0x20,
            "dest_rdi": regs["rdi"],
            "src_rsi": regs["rsi"],
        }
    elif site_va == 0x299C70:
        sample["rsi_equals_target_plus_0xf8"] = regs["rsi"] == target_obj + 0xF8
    elif site_va == 0x267010:
        sample["rdx_equals_target_plus_0xe0"] = regs["rdx"] == target_obj + 0xE0

    _append_sample(sample)
    return False


def _record_samples_from_source_local(process, addr):
    header_qwords = _qword_list(process, addr + 0x08, 3)
    desc = _descriptor(process, addr + 0x20)
    if len(header_qwords) < 3 or not desc.get("read_ok"):
        return {"available": False}
    record_base = header_qwords[1]
    offset_table = desc.get("aux_0x28", 0)
    stride = desc.get("stride_0x18", 0)
    samples = []
    offsets = _u32_list(process, offset_table, min(8, max(stride, 0))) if offset_table else []
    for off in offsets[:4]:
        raw = _read(process, record_base + off, 8)
        if raw is None:
            samples.append({"offset": off, "read_ok": False})
            continue
        samples.append(
            {
                "offset": off,
                "read_ok": True,
                "u16_0x00": _u16(raw, 0x00),
                "u16_0x02": _u16(raw, 0x02),
                "u16_0x04": _u16(raw, 0x04),
                "u16_0x06": _u16(raw, 0x06),
            }
        )
    return {
        "available": True,
        "record_base": record_base,
        "offset_table": offset_table,
        "stride": stride,
        "first_offsets": offsets,
        "records": samples,
    }


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
        bp.SetScriptCallbackFunction("source_local_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_29A140_ATTACHED", ids)


def drive_until_exit_or_step_cap(debugger, max_steps=12000):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process.IsValid() and process.GetState() == lldb.eStateStopped and steps < max_steps:
        steps += 1
        process.Continue()
    _state()["drive_steps"] = steps
    _state()["drive_hit_step_cap"] = (
        process.IsValid() and process.GetState() == lldb.eStateStopped and steps >= max_steps
    )
    print("L16_29A140_DRIVE_STEPS", steps)


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


def payload(debugger):
    packet = dict(_state())
    packet["process"] = _process_packet(debugger)
    packet["breakpoint_hit_counts"] = _breakpoint_hit_counts(debugger)
    return packet


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_29A140_WROTE", path)
