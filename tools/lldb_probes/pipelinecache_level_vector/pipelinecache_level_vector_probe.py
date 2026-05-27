import builtins
import json
import struct


SITES = {
    0x3EA7D0: "ctor_entry_3ea7d0",
    0x3EA803: "ctor_after_embedded_init_3ea803",
    0x3EB494: "initresamp_vector_begin_load_3eb494",
    0x3EB4A2: "src1_level1_dim_read_3eb4a2",
    0x3EB4D5: "src1_level1_dim_store_3eb4d5",
    0x3EB4DF: "src1_inner_store_3eb4df",
    0x3EB51A: "src2_level1_dim_read_3eb51a",
    0x3EB54D: "src2_level1_dim_store_3eb54d",
    0x3EB557: "src2_inner_store_3eb557",
    0x3EB5B8: "ratio_fields_written_3eb5b8",
}


def reset(label="", sample_limit=320):
    builtins.l16_pipelinecache_level_vector = {
        "label": label,
        "sample_limit": sample_limit,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
        "breakpoint_ids": {},
        "counts": {name: 0 for name in SITES.values()},
        "pc_records": {},
        "events": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_pipelinecache_level_vector"):
        reset()
    return builtins.l16_pipelinecache_level_vector


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _i32(value):
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def _f32_at(process, addr):
    data = _read(process, addr, 4)
    if data is None:
        return None
    return struct.unpack_from("<f", data, 0)[0]


def _read(process, addr, size):
    if not addr:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u64_at(process, addr):
    data = _read(process, addr, 8)
    if data is None:
        return None
    return struct.unpack_from("<Q", data, 0)[0]


def _i32_at(process, addr):
    data = _read(process, addr, 4)
    if data is None:
        return None
    return struct.unpack_from("<i", data, 0)[0]


def _vec2i_at(process, addr):
    data = _read(process, addr, 8)
    if data is None:
        return None
    return list(struct.unpack_from("<ii", data, 0))


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


def _stack(thread, max_frames=8):
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


def _vector_header(process, header_addr, max_elems=8):
    if not header_addr:
        return None
    begin = _u64_at(process, header_addr)
    end = _u64_at(process, header_addr + 8)
    cap = _u64_at(process, header_addr + 16)
    if begin is None or end is None or cap is None:
        return None
    byte_count = end - begin if end >= begin else None
    elem_count = byte_count // 8 if byte_count is not None and byte_count % 8 == 0 else None
    out = {
        "header_addr": header_addr,
        "begin": begin,
        "end": end,
        "cap": cap,
        "byte_count": byte_count,
        "elem_count": elem_count,
        "elements": [],
    }
    if elem_count is None or elem_count < 0 or elem_count > 100000:
        return out
    for index in range(min(elem_count, max_elems)):
        pair = _vec2i_at(process, begin + index * 8)
        out["elements"].append({"index": index, "pair": pair})
    return out


def _pc_record(pc):
    text = str(pc)
    state = _state()
    if text not in state["pc_records"]:
        state["pc_records"][text] = {
            "pc": pc,
            "source_vectors": [],
            "post_ctor_vectors": [],
            "initresamp_vectors": [],
            "src1_dim_reads": [],
            "src1_dim_stores": [],
            "src1_inner_stores": [],
            "src2_dim_reads": [],
            "src2_dim_stores": [],
            "src2_inner_stores": [],
            "ratio_fields": [],
        }
    return state["pc_records"][text]


def _append_limited(target, value, limit=16):
    if len(target) < limit:
        target.append(value)


def _append_event(event):
    state = _state()
    if len(state["events"]) < state["sample_limit"]:
        state["events"].append(event)


def _level1_dims_from_begin(process, begin):
    if not begin:
        return None
    return {
        "from_begin": begin,
        "level1_w": _i32_at(process, begin + 8),
        "level1_h": _i32_at(process, begin + 12),
        "level0_w": _i32_at(process, begin),
        "level0_h": _i32_at(process, begin + 4),
    }


def _wrapper_snapshot(process, owner_ptr):
    if not owner_ptr:
        return None
    return {
        "owner_ptr": owner_ptr,
        "inner_ptr": owner_ptr + 0x20,
        "header_qword": _u64_at(process, owner_ptr + 0x20),
        "pipelinecache_backref": _u64_at(process, owner_ptr + 0x28),
        "width_0x50": _i32_at(process, owner_ptr + 0x50),
        "height_0x54": _i32_at(process, owner_ptr + 0x54),
        "flag_0x58": _i32_at(process, owner_ptr + 0x58),
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

    regs = _registers(frame)
    stack = _stack(thread)
    state["counts"][name] = state["counts"].get(name, 0) + 1
    event = {"site": name, "site_va": site_va, "registers": regs, "stack": stack}

    if site_va == 0x3EA7D0:
        pc = regs["rdi"]
        source = _vector_header(process, regs["rsi"])
        entry = {
            "source_header": source,
            "rdx_pair": _vec2i_at(process, regs["rdx"]),
            "args": {
                "rsi": regs["rsi"],
                "rdx": regs["rdx"],
                "rcx": regs["rcx"],
                "r8": regs["r8"],
                "r9": regs["r9"],
            },
        }
        _append_limited(_pc_record(pc)["source_vectors"], entry)
        event.update({"pc": pc, **entry})

    elif site_va == 0x3EA803:
        pc = regs["r14"]
        vector = _vector_header(process, pc + 0x8)
        derived = _vector_header(process, pc + 0x20)
        entry = {
            "pc_w_h": _vec2i_at(process, pc),
            "pc_level_vector": vector,
            "pc_derived_vector_0x20": derived,
        }
        _append_limited(_pc_record(pc)["post_ctor_vectors"], entry)
        event.update({"pc": pc, **entry})

    elif site_va in (0x3EB494, 0x3EB4A2, 0x3EB51A):
        pc = regs["r14"]
        begin = _u64_at(process, pc + 0x8)
        entry = {
            "pc_level_vector": _vector_header(process, pc + 0x8),
            "begin_loaded_or_expected": begin,
            "level_dims_from_begin": _level1_dims_from_begin(process, begin),
            "rbx": regs["rbx"],
        }
        record = _pc_record(pc)
        if site_va == 0x3EB494:
            _append_limited(record["initresamp_vectors"], entry)
        elif site_va == 0x3EB4A2:
            _append_limited(record["src1_dim_reads"], entry)
        else:
            _append_limited(record["src2_dim_reads"], entry)
        event.update({"pc": pc, **entry})

    elif site_va in (0x3EB4D5, 0x3EB54D):
        pc = regs["r14"]
        entry = {
            "ecx_width": _i32(regs["rcx"]),
            "edx_height": _i32(regs["rdx"]),
            "owner_before_store": _wrapper_snapshot(process, regs["rax"]),
            "pc_level_vector": _vector_header(process, pc + 0x8),
        }
        if site_va == 0x3EB4D5:
            _append_limited(_pc_record(pc)["src1_dim_stores"], entry)
        else:
            _append_limited(_pc_record(pc)["src2_dim_stores"], entry)
        event.update({"pc": pc, **entry})

    elif site_va in (0x3EB4DF, 0x3EB557):
        pc = regs["r14"]
        entry = {
            "inner_ptr_to_store": regs["rsi"],
            "owner_ptr": regs["rax"],
            "owner_snapshot": _wrapper_snapshot(process, regs["rax"]),
            "field_addr": pc + (0x238 if site_va == 0x3EB4DF else 0x248),
            "field_current_value_before_store": _u64_at(process, pc + (0x238 if site_va == 0x3EB4DF else 0x248)),
        }
        if site_va == 0x3EB4DF:
            _append_limited(_pc_record(pc)["src1_inner_stores"], entry)
        else:
            _append_limited(_pc_record(pc)["src2_inner_stores"], entry)
        event.update({"pc": pc, **entry})

    elif site_va == 0x3EB5B8:
        pc = regs["r14"]
        entry = {
            "ratio_0x1e8": _f32_at(process, pc + 0x1E8),
            "ratio_0x1ec": _f32_at(process, pc + 0x1EC),
            "pc_level_vector": _vector_header(process, pc + 0x8),
        }
        _append_limited(_pc_record(pc)["ratio_fields"], entry)
        event.update({"pc": pc, **entry})

    _append_event(event)
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    count = target.GetNumBreakpoints()
    if count < len(SITES):
        _state()["errors"].append("expected at least 10 breakpoints")
        print("L16_PIPELINECACHE_LEVEL_VECTOR_ATTACH_ERROR expected at least 10 breakpoints")
        return
    ids = {}
    start = count - len(SITES)
    for index, (site_va, name) in enumerate(SITES.items(), start=start):
        bp = target.GetBreakpointAtIndex(index)
        bp.SetScriptCallbackFunction("pipelinecache_level_vector_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_PIPELINECACHE_LEVEL_VECTOR_ATTACHED", ids)


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


def _unique_level_vectors():
    seen = {}
    for record in _state()["pc_records"].values():
        for field in ("post_ctor_vectors", "initresamp_vectors", "src1_dim_reads", "src2_dim_reads", "ratio_fields"):
            for item in record.get(field, []):
                vector = item.get("pc_level_vector")
                if not vector:
                    continue
                key = tuple(tuple(elem["pair"]) if elem["pair"] is not None else None for elem in vector.get("elements", []))
                seen[str(key)] = {
                    "elem_count": vector.get("elem_count"),
                    "elements": vector.get("elements"),
                }
    return list(seen.values())


def _wrapper_dim_summary():
    rows = []
    for pc_text, record in sorted(_state()["pc_records"].items(), key=lambda item: int(item[0])):
        for label, field in (("src1", "src1_inner_stores"), ("src2", "src2_inner_stores")):
            for item in record.get(field, []):
                owner = item.get("owner_snapshot") or {}
                rows.append(
                    {
                        "pc": int(pc_text),
                        "which": label,
                        "inner_ptr": item.get("inner_ptr_to_store"),
                        "owner_ptr": item.get("owner_ptr"),
                        "pipelinecache_backref": owner.get("pipelinecache_backref"),
                        "width": owner.get("width_0x50"),
                        "height": owner.get("height_0x54"),
                    }
                )
    return rows


def _setup_captured():
    for record in _state()["pc_records"].values():
        if (
            record.get("post_ctor_vectors")
            and record.get("src1_inner_stores")
            and record.get("src2_inner_stores")
            and record.get("ratio_fields")
        ):
            return True
    return False


def drive_until_exit_or_step_cap(debugger, max_steps=30000):
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
    print("L16_PIPELINECACHE_LEVEL_VECTOR_DRIVE_STEPS", steps)


def drive_until_setup_captured_or_step_cap(debugger, max_steps=2000):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while (
        process.IsValid()
        and process.GetState() == lldb.eStateStopped
        and steps < max_steps
        and not _setup_captured()
    ):
        steps += 1
        process.Continue()
    state["drive_steps"] += steps
    if process.IsValid() and process.GetState() == lldb.eStateStopped and steps >= max_steps and not _setup_captured():
        state["drive_hit_step_cap"] = True
    print("L16_PIPELINECACHE_LEVEL_VECTOR_SETUP_DRIVE_STEPS", steps, "captured", _setup_captured())


def payload(debugger):
    return {
        "process": _process_packet(debugger),
        "breakpoint_hit_counts": _breakpoint_hit_counts(debugger),
        "unique_level_vectors": _unique_level_vectors(),
        "wrapper_dim_summary": _wrapper_dim_summary(),
        **_state(),
    }


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_PIPELINECACHE_LEVEL_VECTOR_WROTE", path)
