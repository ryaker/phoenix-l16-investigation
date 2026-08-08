import builtins
import json
import struct


SITES = {
    0x26BBD0: "index_setter_26bbd0",
    0x26BE35: "caller_pre_26d750",
    0x26BE3A: "caller_post_26d750",
    0x26BE50: "caller_pre_29a140",
    0x26D750: "builder_26d750_entry",
    0x26D7AA: "builder_after_seed_descriptor",
    0x26D7F5: "builder_after_267120",
    0x26D8AC: "builder_after_298ff0",
    0x26D9BC: "builder_after_output_store",
    0x26DA56: "builder_return",
}


def reset(label="", target_index=5, sample_limit=260, store_sample_cap=16):
    builtins.l16_26d750_source_range_builder = {
        "label": label,
        "target_index": target_index,
        "target_object": None,
        "target_context": None,
        "target_breakpoints_installed": False,
        "deep_breakpoints_installed": False,
        "sample_limit": sample_limit,
        "store_sample_cap": store_sample_cap,
        "counts": {name: 0 for name in SITES.values()},
        "target_counts": {},
        "breakpoint_ids": {},
        "disabled_after_cap": [],
        "samples": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_26d750_source_range_builder"):
        reset()
    return builtins.l16_26d750_source_range_builder


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


def _u32_at(process, addr):
    raw = _read(process, addr, 4)
    return _u32(raw) if raw is not None else None


def _u64_at(process, addr):
    raw = _read(process, addr, 8)
    return _u64(raw) if raw is not None else None


def _bytes_hex(process, addr, size):
    raw = _read(process, addr, size)
    return raw.hex() if raw is not None else None


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
    desc = {
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
    desc["first_pairs"] = _first_pairs(process, desc, 8)
    desc["first_u16"] = _u16_list(process, desc["data_0x20"], 16) if desc["data_0x20"] else []
    desc["first_u32"] = _u32_list(process, desc["data_0x20"], 8) if desc["data_0x20"] else []
    return desc


def _first_pairs(process, desc, count):
    data = desc.get("data_0x20", 0)
    stride = desc.get("stride_0x18", 0)
    if not data or stride <= 0:
        return []
    raw = _read(process, data, min(count, stride) * 4)
    if raw is None:
        return []
    pairs = []
    for off in range(0, len(raw), 4):
        pairs.append(
            {
                "index": off // 4,
                "u16_0x00": _u16(raw, off),
                "u16_0x02": _u16(raw, off + 2),
                "u32": _u32(raw, off),
            }
        )
    return pairs


def _target_fields(process, obj):
    if not obj:
        return {}
    return {
        "index_0x40": _u32_at(process, obj + 0x40),
        "mode_0x0c": _u32_at(process, obj + 0x0C),
        "field_0x10": _u32_at(process, obj + 0x10),
        "field_0x14": _u32_at(process, obj + 0x14),
        "field_0x18_f32": _f32(_read(process, obj + 0x18, 4)) if _read(process, obj + 0x18, 4) else None,
        "byte_0x54": _u32_at(process, obj + 0x54) & 0xFF
        if _u32_at(process, obj + 0x54) is not None
        else None,
        "min_lower_0x238": _u32_at(process, obj + 0x238),
        "max_upper_0x23c": _u32_at(process, obj + 0x23C),
        "dims_0x2a0": _u32_at(process, obj + 0x2A0),
        "dims_0x2a4": _u32_at(process, obj + 0x2A4),
        "near_0x298_f32": _f32(_read(process, obj + 0x298, 4)) if _read(process, obj + 0x298, 4) else None,
        "far_0x29c_f32": _f32(_read(process, obj + 0x29C, 4)) if _read(process, obj + 0x29C, 4) else None,
        "descriptor_0x208": _descriptor(process, obj + 0x208),
        "descriptor_0x2a8": _descriptor(process, obj + 0x2A8),
    }


def _context_from_caller(process, regs, target_obj):
    source_layer = regs["rdx"] - 0x208 if regs["rdx"] >= 0x208 else 0
    stack_arg = _u64_at(process, regs["rsp"])
    return {
        "target_object": target_obj,
        "caller_rbp": regs["rbp"],
        "output_descriptor_rbp_minus_0x60": regs["rbp"] - 0x60,
        "source_layer": source_layer,
        "source_descriptor_plus_0x2a8": regs["rsi"],
        "source_mask_plus_0x208": regs["rdx"],
        "target_max_upper_ptr": regs["r9"],
        "target_min_lower_ptr": stack_arg,
        "mode_ecx": regs["rcx"] & 0xFFFFFFFF,
    }


def _builder_locals(process, rbp):
    return {
        "local_0x58_descriptor": _descriptor(process, rbp - 0x58),
        "local_0x80_qwords": _qword_list(process, rbp - 0x80, 4),
        "local_0xb0_descriptor": _descriptor(process, rbp - 0xB0),
        "local_0xe0_descriptor": _descriptor(process, rbp - 0xE0),
        "local_0x110_descriptor": _descriptor(process, rbp - 0x110),
        "local_0x140_descriptor": _descriptor(process, rbp - 0x140),
        "range_low_base_0xc0": _u64_at(process, rbp - 0xC0),
        "range_low_stride_0xc8": _u32_at(process, rbp - 0xC8),
        "range_high_base_0xf0": _u64_at(process, rbp - 0xF0),
        "range_high_stride_0xf8": _u32_at(process, rbp - 0xF8),
        "vector_bounds_0x70_0x68": _qword_list(process, rbp - 0x70, 2),
        "selected_size_0xa0": _u64_at(process, rbp - 0xA0),
    }


def _store_formula(process, regs):
    rbp = regs["rbp"]
    target = regs["r13"]
    output_desc = _descriptor(process, regs["r15"])
    stride = output_desc.get("stride_0x18", 0) or 0
    data = output_desc.get("data_0x20", 0) or 0
    x = regs["rdi"] & 0xFFFFFFFF
    y = regs["r10"] & 0xFFFFFFFF
    lower = regs["r12"] & 0xFFFF
    count = regs["rdx"] & 0xFFFF
    upper = regs["rsi"] & 0xFFFF
    store_addr = data + 4 * (x + y * stride) if data and stride else 0
    low_base = _u64_at(process, rbp - 0xC0) or 0
    low_stride = _u32_at(process, rbp - 0xC8) or 0
    high_base = _u64_at(process, rbp - 0xF0) or 0
    high_stride = _u32_at(process, rbp - 0xF8) or 0
    source_size = _u64_at(process, rbp - 0xA0) or 0
    source_width = source_size & 0xFFFFFFFF
    source_height = (source_size >> 32) & 0xFFFFFFFF
    target_width = _u32_at(process, target + 0x2A0) or 0
    target_height = _u32_at(process, target + 0x2A4) or 0
    mapped_x = 0
    mapped_y = 0
    if source_width > 1 and target_width > 1:
        mapped_x = int((x * (source_width - 1)) / (target_width - 1))
    if source_height > 1 and target_height > 1:
        mapped_y = int((y * (source_height - 1)) / (target_height - 1))
    target_offset = _u32_at(process, target + 0x10) or 0
    vector_begin = _u64_at(process, rbp - 0x70) or 0
    vector_end = _u64_at(process, rbp - 0x68) or 0
    max_index = ((vector_end - vector_begin) // 4 - 1) if vector_end >= vector_begin else None
    low_word = None
    high_word = None
    if low_base and low_stride:
        low_word = _u16_list(process, low_base + 2 * (mapped_x + mapped_y * low_stride), 1)
        low_word = low_word[0] if low_word else None
    if high_base and high_stride:
        high_word = _u16_list(process, high_base + 2 * (mapped_x + mapped_y * high_stride), 1)
        high_word = high_word[0] if high_word else None
    expected_lower = None
    expected_upper = None
    expected_count = None
    if low_word is not None:
        expected_lower = max(low_word - target_offset, 0)
    if high_word is not None and max_index is not None:
        expected_upper = min(high_word + target_offset, max_index)
    if expected_lower is not None and expected_upper is not None:
        expected_count = expected_upper - expected_lower
    return {
        "x": x,
        "y": y,
        "source_width": source_width,
        "source_height": source_height,
        "target_width": target_width,
        "target_height": target_height,
        "mapped_x": mapped_x,
        "mapped_y": mapped_y,
        "target_offset_0x10": target_offset,
        "low_word": low_word,
        "high_word": high_word,
        "max_index": max_index,
        "expected_lower": expected_lower,
        "expected_upper": expected_upper,
        "expected_count": expected_count,
        "reg_lower_r12w": lower,
        "reg_upper_esiw": upper,
        "reg_count_dx": count,
        "store_addr": store_addr,
        "stored_pair": _first_pairs(
            process,
            {
                "data_0x20": store_addr,
                "stride_0x18": 1,
            },
            1,
        ),
        "output_descriptor": output_desc,
        "range_low_base_0xc0": low_base,
        "range_low_stride_0xc8": low_stride,
        "range_high_base_0xf0": high_base,
        "range_high_stride_0xf8": high_stride,
        "formula_matches_registers": expected_lower == lower and expected_upper == upper and expected_count == count,
    }


def _append_sample(sample):
    state = _state()
    if len(state["samples"]) < state["sample_limit"]:
        state["samples"].append(sample)


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
        bp.SetScriptCallbackFunction("source_range_builder_probe.hit")
        ids[name] = bp.GetID()


def _disable_site(debugger, name):
    state = _state()
    bp_id = state.get("breakpoint_ids", {}).get(name)
    if not bp_id:
        return
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id)
    if bp and bp.IsValid() and bp.IsEnabled():
        bp.SetEnabled(False)
        state["disabled_after_cap"].append(name)


def _install_target_breakpoints(debugger):
    state = _state()
    if state.get("target_breakpoints_installed"):
        return
    _install_breakpoints(debugger, {"caller_pre_26d750"})
    state["target_breakpoints_installed"] = True


def _install_deep_breakpoints(debugger):
    state = _state()
    if state.get("deep_breakpoints_installed"):
        return
    _install_breakpoints(
        debugger,
        {
            "caller_post_26d750",
            "caller_pre_29a140",
            "builder_26d750_entry",
            "builder_after_seed_descriptor",
            "builder_after_267120",
            "builder_after_298ff0",
            "builder_after_output_store",
            "builder_return",
        },
    )
    state["deep_breakpoints_installed"] = True


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
            _install_target_breakpoints(target.GetDebugger())
        sample = _base_sample(thread, name, site_va, regs)
        sample["incoming_index_esi"] = incoming
        sample["setter_object"] = regs["rdi"]
        sample["target_fields"] = _target_fields(process, regs["rdi"])
        _append_sample(sample)
        return False

    is_target = False
    if site_va == 0x26BE35 and target_obj and regs.get("r14") == target_obj:
        is_target = True
        state["target_context"] = _context_from_caller(process, regs, target_obj)
        _install_deep_breakpoints(target.GetDebugger())
    elif site_va in (0x26BE3A, 0x26BE50) and target_obj:
        is_target = regs.get("r14") == target_obj
    elif site_va == 0x26D750 and target_obj:
        ctx = state.get("target_context") or {}
        is_target = (
            regs.get("rdi") == target_obj
            and regs.get("r8") == ctx.get("output_descriptor_rbp_minus_0x60")
            and regs.get("rsi") == ctx.get("source_descriptor_plus_0x2a8")
            and regs.get("rdx") == ctx.get("source_mask_plus_0x208")
        )
    elif site_va in (0x26D7AA, 0x26D7F5, 0x26D8AC, 0x26D9BC, 0x26DA56) and target_obj:
        is_target = regs.get("r13") == target_obj

    if not is_target:
        return False

    state["target_counts"][name] = state["target_counts"].get(name, 0) + 1
    if name == "builder_after_output_store" and state["target_counts"][name] > state["store_sample_cap"]:
        _disable_site(target.GetDebugger(), name)
        return False

    sample = _base_sample(thread, name, site_va, regs)
    ctx = state.get("target_context") or {}
    source_layer = ctx.get("source_layer", 0)
    output_desc_addr = ctx.get("output_descriptor_rbp_minus_0x60", 0)
    sample["target_fields"] = _target_fields(process, target_obj)
    sample["source_layer"] = {
        "addr": source_layer,
        "fields": _target_fields(process, source_layer) if source_layer else {},
    }
    sample["caller_output_descriptor"] = _descriptor(process, output_desc_addr)

    if site_va == 0x26BE35:
        sample["call_args"] = {
            "rdi_is_target": regs["rdi"] == target_obj,
            "rsi_is_source_plus_0x2a8": regs["rsi"] == source_layer + 0x2A8,
            "rdx_is_source_plus_0x208": regs["rdx"] == source_layer + 0x208,
            "r8_is_output_local": regs["r8"] == output_desc_addr,
            "r9_is_target_plus_0x23c": regs["r9"] == target_obj + 0x23C,
            "stack_arg_is_target_plus_0x238": _u64_at(process, regs["rsp"]) == target_obj + 0x238,
            "ecx_low32": regs["rcx"] & 0xFFFFFFFF,
        }
    elif site_va == 0x26D750:
        sample["entry_args"] = {
            "rdi_is_target": regs["rdi"] == target_obj,
            "rsi_is_source_plus_0x2a8": regs["rsi"] == source_layer + 0x2A8,
            "rdx_is_source_plus_0x208": regs["rdx"] == source_layer + 0x208,
            "r8_is_output_local": regs["r8"] == output_desc_addr,
            "r9_is_target_plus_0x23c": regs["r9"] == target_obj + 0x23C,
            "stack_arg_is_target_plus_0x238": _u64_at(process, regs["rsp"] + 8) == target_obj + 0x238,
            "ecx_low32": regs["rcx"] & 0xFFFFFFFF,
        }
    elif site_va in (0x26D7AA, 0x26D7F5, 0x26D8AC, 0x26DA56):
        sample["builder_locals"] = _builder_locals(process, regs["rbp"])
        sample["builder_output_descriptor_r15"] = _descriptor(process, regs["r15"])
    elif site_va == 0x26D9BC:
        sample["store_formula"] = _store_formula(process, regs)
    elif site_va == 0x26BE3A:
        sample["post_call_descriptor"] = _descriptor(process, output_desc_addr)
    elif site_va == 0x26BE50:
        sample["pre_29a140_descriptor"] = _descriptor(process, regs["rsi"])
        sample["rsi_is_output_descriptor"] = regs["rsi"] == output_desc_addr
        sample["rdx_is_target_plus_0x208"] = regs["rdx"] == target_obj + 0x208
        sample["ecx_low32"] = regs["rcx"] & 0xFFFFFFFF

    _append_sample(sample)
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
        bp.SetScriptCallbackFunction("source_range_builder_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_26D750_SOURCE_RANGE_BUILDER_ATTACHED", json.dumps(ids, sort_keys=True))


def drive_until_exit_or_step_cap(debugger, step_cap=120000):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process.IsValid() and process.GetState() != lldb.eStateExited and steps < step_cap:
        error = process.Continue()
        if not error.Success():
            state["errors"].append(error.GetCString() or "process.Continue failed")
            break
        steps += 1
    state["drive_steps"] = steps
    state["drive_hit_step_cap"] = steps >= step_cap
    state["process"] = {
        "valid": process.IsValid(),
        "state": lldb.SBDebugger.StateAsCString(process.GetState()) if process.IsValid() else None,
        "exit_status": process.GetExitStatus() if process.IsValid() else None,
        "exit_description": process.GetExitDescription() if process.IsValid() else None,
    }
    print("L16_26D750_SOURCE_RANGE_BUILDER_DRIVE_STEPS", steps)


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(_state(), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_26D750_SOURCE_RANGE_BUILDER_REPORT", path)
