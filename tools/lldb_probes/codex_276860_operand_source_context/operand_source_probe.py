import builtins
import json
import struct


SITES = {
    0x26BBD0: "index_setter_26bbd0",
    0x26C5E7: "guide_store_0x288_new_26c5e7",
    0x26C633: "guide_store_0x288_reuse_26c633",
    0x26CA94: "table_buffer_store_0x198_26ca94",
    0x26CBCD: "sub_buffer_store_0x1e8_26cbcd",
    0x26CC01: "xmm8_base_store_0x200_26cc01",
    0x26BE50: "caller_pre_29a140",
    0x29A1A0: "maker_after_299fd0",
    0x2774BF: "xmm8_guide_after_pmovzxbd_2774bf",
    0x2774D0: "xmm8_vector_store_2774d0",
    0x2775D5: "xmm8_vector_load_2775d5",
    0x27786B: "table_operand_site_27786b",
}


def reset(label="", target_index=5, skip_table_hits=4):
    builtins.l16_operand_source = {
        "label": label,
        "target_index": target_index,
        "skip_table_hits": skip_table_hits,
        "watch_offsets": [0x198, 0x1E8, 0x200, 0x288],
        "watch_hit_cap": 64,
        "watchpoints_armed": False,
        "watchpoint_ids": {},
        "watchpoint_samples": [],
        "target_table_hits": 0,
        "target_object": None,
        "target_context": None,
        "caller_pre_breakpoint_installed": False,
        "maker_breakpoint_installed": False,
        "operand_breakpoints_installed": False,
        "capture_complete": False,
        "terminated_after_capture": False,
        "breakpoint_ids": {},
        "counts": {name: 0 for name in SITES.values()},
        "target_counts": {},
        "disabled_after_cap": [],
        "setup_samples": [],
        "guide_samples": [],
        "store_samples": [],
        "load_samples": [],
        "producer_samples": [],
        "latest_guide_by_context": {},
        "latest_load_by_context": {},
        "latest_store_by_addr": {},
        "packet": {},
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_operand_source"):
        reset()
    return builtins.l16_operand_source


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


def _f32_list(process, addr, count):
    raw = _read(process, addr, count * 4)
    if raw is None:
        return []
    return [_f32(raw, off) for off in range(0, len(raw), 4)]


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
            }
        )
    return frames


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
        bp.SetScriptCallbackFunction("operand_source_probe.hit")
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


def _context_key(thread_id, rbp):
    return f"{thread_id}:{rbp}"


def _object_from_worker_stack(process, rbp):
    return _u64_at(process, rbp - 0x1C8)


def _object_fields(process, obj):
    if not obj:
        return {"addr": obj, "read_ok": False}
    qword_offsets = (0x108, 0x138, 0x168, 0x198, 0x1E8, 0x200, 0x288)
    dword_offsets = (0x130, 0x238)
    guide_ptr = _u64_at(process, obj + 0x288)
    return {
        "addr": obj,
        "read_ok": True,
        "u16_0x56": _u16_at(process, obj + 0x56),
        "f32_0x58": _f32_at(process, obj + 0x58),
        "bytes_0x60_0x70_hex": _bytes_hex(process, obj + 0x60, 16),
        "qwords": {f"0x{off:x}": _u64_at(process, obj + off) for off in qword_offsets},
        "dwords": {f"0x{off:x}": _u32_at(process, obj + off) for off in dword_offsets},
        "guide_descriptor_from_0x288": _descriptor_like(process, guide_ptr),
    }


def _descriptor_like(process, addr):
    if not addr:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": _read(process, addr, 0x30) is not None,
        "u32_0x10_0x1c": _u32_list(process, addr + 0x10, 4),
        "qword_0x20": _u64_at(process, addr + 0x20),
        "first_data_u8x16_hex": _bytes_hex(process, _u64_at(process, addr + 0x20) or 0, 16),
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


def _target_stack_context(process, regs):
    rbp = regs["rbp"]
    obj = _object_from_worker_stack(process, rbp)
    return {
        "rbp": rbp,
        "object_from_stack_rbp_minus_0x1c8": obj,
        "object_fields": _object_fields(process, obj),
        "stack_qwords": {
            "rbp_minus_0x1c8": obj,
            "rbp_minus_0x1e8": _u64_at(process, rbp - 0x1E8),
            "rbp_minus_0x208": _u64_at(process, rbp - 0x208),
            "rbp_minus_0x210": _u64_at(process, rbp - 0x210),
            "rbp_minus_0x250": _u64_at(process, rbp - 0x250),
            "rbp_minus_0x2e0": _u64_at(process, rbp - 0x2E0),
        },
        "record_lookup_from_r9": _record_index_for_r9(process, obj, regs.get("r9", 0)),
    }


def _xmm_bank(frame):
    return {f"xmm{i}": _xmm_hex(frame, f"xmm{i}") for i in range(16)}


def _sample(frame, site_va, name):
    thread = frame.GetThread()
    process = thread.GetProcess()
    regs = _registers(frame)
    sample = {
        "site": name,
        "site_va": site_va,
        "thread_id": thread.GetThreadID(),
        "registers": regs,
        "target_object": _state().get("target_object"),
        "target_context": _state().get("target_context"),
        "target_stack_context": _target_stack_context(process, regs),
        "xmm_hex": _xmm_bank(frame),
        "stack": _stack(thread),
    }
    obj = sample["target_stack_context"].get("object_from_stack_rbp_minus_0x1c8")
    if obj != _state().get("target_object"):
        sample["object_mismatch"] = True
    return sample


def _capture_guide(frame, site_va, name):
    sample = _sample(frame, site_va, name)
    process = frame.GetThread().GetProcess()
    regs = sample["registers"]
    source_addr = (regs["rax"] + (4 * regs["rcx"])) & 0xFFFFFFFFFFFFFFFF
    sample["guide_source"] = {
        "source_addr_rax_plus_4rcx": source_addr,
        "source_u8x4_hex": _bytes_hex(process, source_addr, 4),
        "source_u8x16_hex": _bytes_hex(process, source_addr, 16),
        "xmm0_after_pmovzxbd_hex": sample["xmm_hex"].get("xmm0"),
    }
    key = _context_key(sample["thread_id"], regs["rbp"])
    _state()["latest_guide_by_context"][key] = sample
    _state()["guide_samples"].append(sample)


def _capture_store(frame, site_va, name):
    sample = _sample(frame, site_va, name)
    process = frame.GetThread().GetProcess()
    regs = sample["registers"]
    key = _context_key(sample["thread_id"], regs["rbp"])
    dest_addr = (regs["rax"] + regs["rcx"]) & 0xFFFFFFFFFFFFFFFF
    sample["xmm8_vector_store"] = {
        "dest_addr_rax_plus_rcx": dest_addr,
        "dest_base_rax": regs["rax"],
        "dest_offset_rcx": regs["rcx"],
        "dest_before_hex": _bytes_hex(process, dest_addr, 16),
        "xmm0_store_hex": sample["xmm_hex"].get("xmm0"),
        "latest_guide_sample": _state()["latest_guide_by_context"].get(key),
    }
    _state()["latest_store_by_addr"][str(dest_addr)] = sample
    _state()["store_samples"].append(sample)


def _capture_load(frame, site_va, name):
    sample = _sample(frame, site_va, name)
    process = frame.GetThread().GetProcess()
    regs = sample["registers"]
    key = _context_key(sample["thread_id"], regs["rbp"])
    load_addr = regs["rcx"]
    sample["xmm8_vector_load"] = {
        "load_addr_rcx": load_addr,
        "load_hex": _bytes_hex(process, load_addr, 16),
        "matched_store_sample": _state()["latest_store_by_addr"].get(str(load_addr)),
    }
    _state()["latest_load_by_context"][key] = sample
    _state()["load_samples"].append(sample)


def _capture_table(frame, site_va, name):
    sample = _sample(frame, site_va, name)
    process = frame.GetThread().GetProcess()
    regs = sample["registers"]
    rbp = regs["rbp"]
    key = _context_key(sample["thread_id"], rbp)
    obj = sample["target_stack_context"].get("object_from_stack_rbp_minus_0x1c8") or 0
    vector_base = _u64_at(process, rbp - 0x208) or 0
    vector_addr = (vector_base + regs["rdx"]) & 0xFFFFFFFFFFFFFFFF
    table_base = regs["rdi"]
    table_index = regs["rcx"]
    table_addr = (table_base + (2 * table_index)) & 0xFFFFFFFFFFFFFFFF
    sample["table_load"] = {
        "table_base_rdi": table_base,
        "table_index_rcx": table_index,
        "table_addr_rdi_plus_2rcx": table_addr,
        "table_value_u16": _u16_at(process, table_addr),
        "stack_minus_0x210_eq_table_base": _u64_at(process, rbp - 0x210) == table_base,
    }
    sample["operand_sources"] = {
        "xmm8_latest_load": _state()["latest_load_by_context"].get(key),
        "sub_vector_base_rbp_minus_0x208": vector_base,
        "sub_vector_offset_rdx": regs["rdx"],
        "sub_vector_addr": vector_addr,
        "sub_vector16_hex": _bytes_hex(process, vector_addr, 16),
        "object_plus_0x60_hex": _bytes_hex(process, obj + 0x60, 16),
    }
    _state()["packet"]["table"] = sample


def _producer_write(site_va, regs):
    if site_va == 0x26C5E7:
        return {
            "object": regs["rsi"],
            "field_offset": 0x288,
            "write_value": regs["rax"],
            "value_register": "rax",
            "kind": "new_guide_descriptor",
        }
    if site_va == 0x26C633:
        return {
            "object": regs["rdx"],
            "field_offset": 0x288,
            "write_value": regs["rbx"],
            "value_register": "rbx",
            "kind": "reused_guide_descriptor",
        }
    if site_va == 0x26CA94:
        return {
            "object": regs["r13"],
            "field_offset": 0x198,
            "write_value": regs["r12"],
            "value_register": "r12",
            "kind": "table_buffer",
        }
    if site_va == 0x26CBCD:
        return {
            "object": regs["r13"],
            "field_offset": 0x1E8,
            "write_value": regs["r15"],
            "value_register": "r15",
            "kind": "subtraction_buffer",
        }
    if site_va == 0x26CC01:
        return {
            "object": regs["r13"],
            "field_offset": 0x200,
            "write_value": regs["rax"],
            "value_register": "rax",
            "kind": "xmm8_base",
        }
    return None


def _capture_producer(frame, site_va, name, write_info):
    thread = frame.GetThread()
    process = thread.GetProcess()
    regs = _registers(frame)
    obj = write_info["object"]
    field_addr = obj + write_info["field_offset"]
    sample = {
        "site": name,
        "site_va": site_va,
        "thread_id": thread.GetThreadID(),
        "registers": regs,
        "target_object": _state().get("target_object"),
        "write_object": obj,
        "field_offset": write_info["field_offset"],
        "field_addr": field_addr,
        "field_before": _u64_at(process, field_addr),
        "write_value": write_info["write_value"],
        "value_register": write_info["value_register"],
        "kind": write_info["kind"],
        "write_value_preview_hex": _bytes_hex(process, write_info["write_value"], 64),
        "write_value_descriptor_like": _descriptor_like(process, write_info["write_value"]),
        "stack": _stack(thread),
    }
    _state()["producer_samples"].append(sample)
    _state()["target_counts"][name] = _state()["target_counts"].get(name, 0) + 1


def _arm_field_watchpoints(target, obj):
    state = _state()
    if state.get("watchpoints_armed"):
        return
    lldb = builtins.__import__("lldb")
    for offset in state.get("watch_offsets", []):
        error = lldb.SBError()
        wp = target.WatchAddress(obj + offset, 8, False, True, error)
        if wp and wp.IsValid() and error.Success():
            state["watchpoint_ids"][str(wp.GetID())] = {
                "offset": offset,
                "addr": obj + offset,
                "name": f"object+0x{offset:x}",
            }
        else:
            state["errors"].append(
                f"failed to arm watchpoint {offset:#x} at {obj + offset:#x}: {error.GetCString()}"
            )
    state["watchpoints_armed"] = bool(state["watchpoint_ids"])


def _record_watchpoint_stop(debugger):
    lldb = builtins.__import__("lldb")
    state = _state()
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    thread = process.GetSelectedThread()
    if not thread or not thread.IsValid():
        return
    if thread.GetStopReason() != lldb.eStopReasonWatchpoint:
        return
    wp_id = thread.GetStopReasonDataAtIndex(0) if thread.GetStopReasonDataCount() else None
    meta = state.get("watchpoint_ids", {}).get(str(wp_id), {})
    frame = thread.GetFrameAtIndex(0)
    regs = _registers(frame)
    obj = state.get("target_object")
    offset = meta.get("offset")
    sample = {
        "watchpoint_id": wp_id,
        "watchpoint": meta,
        "thread_id": thread.GetThreadID(),
        "pc": frame.GetPC(),
        "libcp_va": _module_va(target, frame.GetPC()),
        "registers": regs,
        "field_value_at_stop": (
            _u64_at(process, obj + offset) if obj and isinstance(offset, int) else None
        ),
        "target_object_fields": _object_fields(process, obj),
        "stack": _stack(thread, max_frames=24),
    }
    state["watchpoint_samples"].append(sample)
    if len(state["watchpoint_samples"]) >= state.get("watch_hit_cap", 64):
        for watch_id in state.get("watchpoint_ids", {}):
            wp = target.FindWatchpointByID(int(watch_id))
            if wp and wp.IsValid():
                wp.SetEnabled(False)
        if "watchpoints" not in state["disabled_after_cap"]:
            state["disabled_after_cap"].append("watchpoints")


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
            _arm_field_watchpoints(target, regs["rdi"])
            if not state.get("caller_pre_breakpoint_installed"):
                _install_breakpoints(
                    target.GetDebugger(),
                    {
                        "caller_pre_29a140",
                        "guide_store_0x288_new_26c5e7",
                        "guide_store_0x288_reuse_26c633",
                        "table_buffer_store_0x198_26ca94",
                        "sub_buffer_store_0x1e8_26cbcd",
                        "xmm8_base_store_0x200_26cc01",
                    },
                )
                state["caller_pre_breakpoint_installed"] = True
        state["setup_samples"].append(
            {
                "site": name,
                "site_va": site_va,
                "thread_id": thread.GetThreadID(),
                "registers": regs,
                "incoming_index_esi": incoming,
                "setter_object": regs["rdi"],
                "setter_object_fields": _object_fields(process, regs["rdi"]),
                "armed_watchpoints": dict(state.get("watchpoint_ids", {})),
                "target_object_after": state.get("target_object"),
                "stack": _stack(thread),
            }
        )
        return False

    if target_obj and site_va == 0x26BE50 and regs.get("r14") == target_obj:
        state["target_context"] = _context_from_caller(regs, target_obj)
        state["target_counts"][name] = state["target_counts"].get(name, 0) + 1
        if not state.get("maker_breakpoint_installed"):
            _install_breakpoints(target.GetDebugger(), {"maker_after_299fd0"})
            state["maker_breakpoint_installed"] = True
        state["setup_samples"].append(
            {"site": name, "site_va": site_va, "thread_id": thread.GetThreadID(), "registers": regs}
        )
        return False

    if site_va == 0x29A1A0 and _context_match_maker(regs):
        state["target_counts"][name] = state["target_counts"].get(name, 0) + 1
        if not state.get("operand_breakpoints_installed"):
            _install_breakpoints(
                target.GetDebugger(),
                {
                    "xmm8_guide_after_pmovzxbd_2774bf",
                    "xmm8_vector_store_2774d0",
                    "xmm8_vector_load_2775d5",
                    "table_operand_site_27786b",
                },
            )
            state["operand_breakpoints_installed"] = True
        _disable_breakpoints(
            target.GetDebugger(),
            {
                "xmm8_guide_after_pmovzxbd_2774bf",
                "xmm8_vector_store_2774d0",
                "xmm8_vector_load_2775d5",
                "table_operand_site_27786b",
            },
        )
        state["setup_samples"].append(
            {"site": name, "site_va": site_va, "thread_id": thread.GetThreadID(), "registers": regs}
        )
        return False

    if not target_obj:
        return False
    producer = _producer_write(site_va, regs)
    if producer is not None:
        if producer["object"] == target_obj:
            _capture_producer(frame, site_va, name, producer)
        return False

    obj_from_stack = _object_from_worker_stack(process, regs["rbp"])
    if obj_from_stack != target_obj:
        return False

    if site_va == 0x2774BF:
        _capture_guide(frame, site_va, name)
        return False
    if site_va == 0x2774D0:
        _capture_store(frame, site_va, name)
        return False
    if site_va == 0x2775D5:
        _capture_load(frame, site_va, name)
        return False
    if site_va == 0x27786B:
        state["target_table_hits"] = state.get("target_table_hits", 0) + 1
        if state["target_table_hits"] <= state.get("skip_table_hits", 0):
            return False
        _capture_table(frame, site_va, name)
        state["capture_complete"] = True
        process.Kill()
        state["terminated_after_capture"] = True
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
        bp.SetScriptCallbackFunction("operand_source_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_OPERAND_SOURCE_ATTACHED", ids)


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


def _watchpoint_hit_counts(debugger):
    target = debugger.GetSelectedTarget()
    out = {}
    for wp_id, meta in _state().get("watchpoint_ids", {}).items():
        wp = target.FindWatchpointByID(int(wp_id))
        out[wp_id] = {
            "name": meta.get("name"),
            "offset": meta.get("offset"),
            "hit_count": wp.GetHitCount() if wp and wp.IsValid() else None,
            "enabled": wp.IsEnabled() if wp and wp.IsValid() else None,
        }
    return out


def drive_until_capture_or_exit(debugger, max_steps=24000):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while (
        process.IsValid()
        and process.GetState() == lldb.eStateStopped
        and steps < max_steps
        and not _state().get("capture_complete")
    ):
        _record_watchpoint_stop(debugger)
        steps += 1
        process.Continue()
    _state()["drive_steps"] = steps
    _state()["drive_hit_step_cap"] = (
        process.IsValid()
        and process.GetState() == lldb.eStateStopped
        and steps >= max_steps
        and not _state().get("capture_complete")
    )
    print("L16_OPERAND_SOURCE_DRIVE_STEPS", steps)


def payload(debugger):
    packet = dict(_state())
    packet["process"] = _process_packet(debugger)
    packet["watchpoint_hit_counts"] = _watchpoint_hit_counts(debugger)
    return packet


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_OPERAND_SOURCE_WROTE", path)
