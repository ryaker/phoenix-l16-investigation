import builtins
import json
import os
import struct


GATE_BEFORE = 0x2488B9
GATE_AFTER = 0x2488BE
ENTRY_2416D0 = 0x2416D0
PRE_EXEC_241BBF = 0x241BBF
POST_EXEC_241BD7 = 0x241BD7
BITSET_STORE_AFTER_241CD6 = 0x241CD6
FALLBACK_STORE1_AFTER_241D3B = 0x241D3B
FALLBACK_STORE2_AFTER_241D6A = 0x241D6A
FALLBACK_STORE3_AFTER_241D85 = 0x241D85
RECORD_STRIDE = 0x2C


def reset(label="", sample_limit=96, max_records=512, step_cap=300000, store_sample_limit=96):
    builtins.l16_prefusion_state5_acceptance = {
        "label": label,
        "sample_limit": sample_limit,
        "max_records": max_records,
        "step_cap": step_cap,
        "store_sample_limit": store_sample_limit,
        "breakpoint_ids": {},
        "counts": {
            "gate_before_hits": 0,
            "gate_after_hits": 0,
            "promotion_events": 0,
            "promoted_records_total": 0,
            "entry_2416d0_hits": 0,
            "entry_2416d0_target2_hits": 0,
            "entry_2416d0_promoted_overlap_hits": 0,
            "pre_exec_hits": 0,
            "post_exec_hits": 0,
            "store_hits": 0,
            "store_promoted_overlap_hits": 0,
        },
        "active_before_by_thread": {},
        "active_call_by_thread": {},
        "promotions": [],
        "entry_samples": [],
        "pre_exec_samples": [],
        "post_exec_samples": [],
        "store_samples": [],
        "errors": [],
        "drive_steps": 0,
        "drive_hit_step_cap": False,
    }


def _state():
    if not hasattr(builtins, "l16_prefusion_state5_acceptance"):
        reset()
    return builtins.l16_prefusion_state5_acceptance


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    if not addr or size < 0:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u64(data, off=0):
    return struct.unpack_from("<Q", data, off)[0]


def _i32(data, off=0):
    return struct.unpack_from("<i", data, off)[0]


def _u32(data, off=0):
    return struct.unpack_from("<I", data, off)[0]


def _vector_header(process, vector_addr, stride):
    data = _read(process, vector_addr, 24)
    if data is None:
        return {"addr": vector_addr, "read_ok": False}
    begin = _u64(data, 0)
    end = _u64(data, 8)
    cap = _u64(data, 16)
    byte_len = end - begin if end >= begin else None
    cap_bytes = cap - begin if cap >= begin else None
    return {
        "addr": vector_addr,
        "read_ok": True,
        "begin": begin,
        "end": end,
        "cap": cap,
        "byte_len": byte_len,
        "count": byte_len // stride if byte_len is not None else None,
        "byte_len_mod_stride": byte_len % stride if byte_len is not None else None,
        "cap_bytes": cap_bytes,
        "cap_count": cap_bytes // stride if cap_bytes is not None else None,
    }


def _record_list(process, vector_addr):
    header = _vector_header(process, vector_addr, RECORD_STRIDE)
    if not header.get("read_ok"):
        return {"vector": header, "read_ok": False, "records": []}
    count = header.get("count") or 0
    limited = min(count, _state()["max_records"])
    data = _read(process, header["begin"], limited * RECORD_STRIDE) if limited else b""
    if data is None:
        return {"vector": header, "read_ok": False, "records": []}
    records = []
    counts = {}
    for index in range(limited):
        off = index * RECORD_STRIDE
        state_val = _i32(data, off + 0x24)
        target_val = _i32(data, off + 0x28)
        key = f"{state_val}:{target_val}"
        counts[key] = counts.get(key, 0) + 1
        records.append(
            {
                "index": index,
                "record_addr": header["begin"] + off,
                "state_0x24": state_val,
                "target_0x28": target_val,
                "coord_i32_0x14": _i32(data, off + 0x14),
                "coord_i32_0x18": _i32(data, off + 0x18),
            }
        )
    return {
        "vector": header,
        "read_ok": True,
        "records_scanned": limited,
        "records_truncated": count > limited,
        "state_target_counts": counts,
        "records": records,
    }


def _record_now(process, record_addr):
    data = _read(process, record_addr, RECORD_STRIDE)
    if data is None:
        return None
    return {
        "record_addr": record_addr,
        "state_0x24": _i32(data, 0x24),
        "target_0x28": _i32(data, 0x28),
        "coord_i32_0x14": _i32(data, 0x14),
        "coord_i32_0x18": _i32(data, 0x18),
        "first_i32_0x00": _i32(data, 0x00),
        "record_hex": data.hex(),
    }


def _int_vector(process, vector_addr, limit=128):
    header = _vector_header(process, vector_addr, 4)
    if not header.get("read_ok"):
        return {"vector": header, "read_ok": False, "values": []}
    count = min(header.get("count") or 0, limit)
    data = _read(process, header["begin"], count * 4) if count else b""
    if data is None:
        return {"vector": header, "read_ok": False, "values": []}
    return {
        "vector": header,
        "read_ok": True,
        "values": [_i32(data, i * 4) for i in range(count)],
        "values_truncated": (header.get("count") or 0) > count,
    }


def _bitset_entries(process, vector_addr, max_entries=16, max_words_per_entry=4):
    header = _vector_header(process, vector_addr, 24)
    if not header.get("read_ok"):
        return {"vector": header, "read_ok": False, "entries": []}
    count = min(header.get("count") or 0, max_entries)
    data = _read(process, header["begin"], count * 24) if count else b""
    if data is None:
        return {"vector": header, "read_ok": False, "entries": []}
    entries = []
    for index in range(count):
        off = index * 24
        word_ptr = _u64(data, off)
        bit_count = _u64(data, off + 8)
        cap_words = _u64(data, off + 16)
        word_count = min((bit_count + 63) // 64, cap_words, max_words_per_entry)
        words = []
        if word_ptr and word_count:
            word_data = _read(process, word_ptr, word_count * 8)
            if word_data is not None:
                words = [_u64(word_data, i * 8) for i in range(word_count)]
        entries.append(
            {
                "index": index,
                "word_ptr": word_ptr,
                "bit_count": bit_count,
                "cap_words": cap_words,
                "sampled_words": words,
            }
        )
    return {
        "vector": header,
        "read_ok": True,
        "entries": entries,
        "entries_truncated": (header.get("count") or 0) > count,
    }


def _bitset_membership(entries, selected_count, limit=64):
    out = []
    for selected_order in range(min(selected_count or 0, limit)):
        word_index = selected_order // 64
        bit = selected_order & 63
        hit_entries = []
        for entry in entries:
            words = entry.get("sampled_words") or []
            if word_index < len(words) and (words[word_index] >> bit) & 1:
                hit_entries.append(entry["index"])
        out.append({"selected_order": selected_order, "hit_entries": hit_entries})
    return out


def _libcp_base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                return base
    return None


def _module_va(target, pc):
    addr = target.ResolveLoadAddress(pc)
    if addr and addr.IsValid():
        module = addr.GetModule()
        if module and str(module.GetFileSpec().GetFilename()) != "libcp.dylib":
            return None
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
        "rsi",
        "rdi",
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
        "rip",
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


def _append_limited(key, packet):
    state = _state()
    if len(state[key]) < state["sample_limit"]:
        state[key].append(packet)


def _active_promoted_indices_for_vector(vector_begin):
    indices = set()
    for promotion in _state()["promotions"]:
        if promotion.get("vector_begin") == vector_begin:
            indices.update(promotion.get("promoted_indices", []))
    return sorted(indices)


def _selected_promoted_overlap(selected_indices, vector_begin):
    promoted = set(_active_promoted_indices_for_vector(vector_begin))
    selected = set(selected_indices or [])
    return sorted(promoted.intersection(selected))


def _locals_snapshot(process, rbp, vector_ptr=None):
    selected_count_data = _read(process, rbp - 0xA8, 4)
    selected_count = _i32(selected_count_data, 0) if selected_count_data else None
    selected_vector = _int_vector(process, rbp - 0xA0, _state()["max_records"])
    bitset_vector = _bitset_entries(process, rbp - 0x108)
    callback_ptr_data = _read(process, rbp - 0x40, 8)
    callback_ptr = _u64(callback_ptr_data, 0) if callback_ptr_data else None
    callback_fields = None
    if callback_ptr:
        data = _read(process, callback_ptr, 0x48)
        if data is not None:
            callback_fields = {
                "vtable": _u64(data, 0),
                "field_0x08": _u64(data, 0x08),
                "field_0x10": _u64(data, 0x10),
                "field_0x18": _u64(data, 0x18),
                "field_0x20": _u64(data, 0x20),
                "field_0x28": _u64(data, 0x28),
                "field_0x30": _u64(data, 0x30),
                "field_0x38": _u64(data, 0x38),
                "field_0x40": _u64(data, 0x40),
            }
    vec_ptr = vector_ptr
    if vec_ptr is None:
        vec_ptr_data = _read(process, rbp - 0x148, 8)
        vec_ptr = _u64(vec_ptr_data, 0) if vec_ptr_data else None
    record_vector = _record_list(process, vec_ptr) if vec_ptr else None
    vector_begin = (record_vector or {}).get("vector", {}).get("begin")
    selected_values = selected_vector.get("values", [])
    return {
        "rbp": rbp,
        "record_vector_ptr": vec_ptr,
        "record_vector_summary": {
            "vector": (record_vector or {}).get("vector"),
            "read_ok": (record_vector or {}).get("read_ok"),
            "records_scanned": (record_vector or {}).get("records_scanned"),
            "records_truncated": (record_vector or {}).get("records_truncated"),
            "state_target_counts": (record_vector or {}).get("state_target_counts"),
        },
        "selected_count_cell": selected_count,
        "selected_vector": selected_vector,
        "bitset_vector": bitset_vector,
        "bitset_membership_first64": _bitset_membership(
            bitset_vector.get("entries", []), selected_count or len(selected_values)
        ),
        "callback_ptr": callback_ptr,
        "callback_fields": callback_fields,
        "promoted_indices_for_vector": _active_promoted_indices_for_vector(vector_begin),
        "selected_promoted_overlap": _selected_promoted_overlap(selected_values, vector_begin),
    }


def install_breakpoints(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    sites = [
        (GATE_BEFORE, "gate_before_2488b9"),
        (GATE_AFTER, "gate_after_2488be"),
        (ENTRY_2416D0, "entry_2416d0"),
        (PRE_EXEC_241BBF, "pre_exec_241bbf"),
        (POST_EXEC_241BD7, "post_exec_241bd7"),
        (BITSET_STORE_AFTER_241CD6, "bitset_store_after_241cd6"),
        (FALLBACK_STORE1_AFTER_241D3B, "fallback_store1_after_241d3b"),
        (FALLBACK_STORE2_AFTER_241D6A, "fallback_store2_after_241d6a"),
        (FALLBACK_STORE3_AFTER_241D85, "fallback_store3_after_241d85"),
    ]
    for site, name in sites:
        before = target.GetNumBreakpoints()
        debugger.HandleCommand(f"breakpoint set --shlib libcp.dylib --address 0x{site:x}")
        after = target.GetNumBreakpoints()
        if after <= before:
            state["errors"].append({"site": f"0x{site:x}", "error": "breakpoint not created"})
            continue
        bp = target.GetBreakpointAtIndex(after - 1)
        if not bp or not bp.IsValid():
            state["errors"].append({"site": f"0x{site:x}", "error": "invalid breakpoint"})
            continue
        bp.SetScriptCallbackFunction("state5_acceptance_probe.hit")
        state["breakpoint_ids"][name] = bp.GetID()
    print("L16_STATE5_ACCEPTANCE_INSTALLED", json.dumps(state["breakpoint_ids"], sort_keys=True))


def _gate_before(frame, process, regs, thread_id):
    snapshot = _record_list(process, regs["rsi"])
    packet = {
        "site": "gate_before_2488b9",
        "thread_id": thread_id,
        "vector_arg_rsi": regs["rsi"],
        "snapshot": {
            "vector": snapshot.get("vector"),
            "read_ok": snapshot.get("read_ok"),
            "records_scanned": snapshot.get("records_scanned"),
            "records_truncated": snapshot.get("records_truncated"),
            "state_target_counts": snapshot.get("state_target_counts"),
        },
    }
    _state()["active_before_by_thread"][str(thread_id)] = {
        "vector_addr": regs["rsi"],
        "records": snapshot.get("records", []),
        "packet": packet,
    }


def _gate_after(frame, process, regs, thread_id):
    state = _state()
    active = state["active_before_by_thread"].get(str(thread_id))
    vector_addr = active.get("vector_addr") if active else regs["r13"]
    before_records = active.get("records", []) if active else []
    after_snapshot = _record_list(process, vector_addr)
    promoted = []
    for before, after in zip(before_records, after_snapshot.get("records", [])):
        if (
            before.get("state_0x24") == 3
            and before.get("target_0x28") == 2
            and after.get("state_0x24") == 4
            and after.get("target_0x28") == 2
        ):
            promoted.append({"before": before, "after": after})
    if promoted:
        state["counts"]["promotion_events"] += 1
        state["counts"]["promoted_records_total"] += len(promoted)
        packet = {
            "site": "gate_after_2488be",
            "thread_id": thread_id,
            "vector_addr": vector_addr,
            "vector_begin": after_snapshot.get("vector", {}).get("begin"),
            "promoted_count": len(promoted),
            "promoted_indices": [item["after"]["index"] for item in promoted],
            "snapshot": {
                "vector": after_snapshot.get("vector"),
                "read_ok": after_snapshot.get("read_ok"),
                "records_scanned": after_snapshot.get("records_scanned"),
                "records_truncated": after_snapshot.get("records_truncated"),
                "state_target_counts": after_snapshot.get("state_target_counts"),
            },
        }
        state["promotions"].append(packet)


def _entry_2416d0(frame, process, regs, thread_id, stack):
    state = _state()
    state["counts"]["entry_2416d0_hits"] += 1
    target = regs["r9"] & 0xFFFFFFFF
    if target & 0x80000000:
        target -= 0x100000000
    if target == 2:
        state["counts"]["entry_2416d0_target2_hits"] += 1
    snapshot = _record_list(process, regs["rdx"])
    vector_begin = snapshot.get("vector", {}).get("begin")
    selected = [
        rec["index"]
        for rec in snapshot.get("records", [])
        if rec.get("target_0x28") == target and rec.get("state_0x24") == 4
    ]
    overlap = _selected_promoted_overlap(selected, vector_begin)
    if overlap:
        state["counts"]["entry_2416d0_promoted_overlap_hits"] += 1
    call_id = f"{thread_id}:{state['counts']['entry_2416d0_hits']}"
    state["active_call_by_thread"][str(thread_id)] = {
        "call_id": call_id,
        "target": target,
        "vector_ptr": regs["rdx"],
        "vector_begin": vector_begin,
        "selected_indices": selected,
        "selected_promoted_overlap": overlap,
    }
    if target == 2 or overlap:
        packet = {
            "call_id": call_id,
            "thread_id": thread_id,
            "target_r9d": target,
            "record_vector_ptr_rdx": regs["rdx"],
            "record_vector": {
                "vector": snapshot.get("vector"),
                "read_ok": snapshot.get("read_ok"),
                "records_scanned": snapshot.get("records_scanned"),
                "records_truncated": snapshot.get("records_truncated"),
                "state_target_counts": snapshot.get("state_target_counts"),
            },
            "selected_indices_state4_target": selected[:128],
            "selected_indices_truncated": len(selected) > 128,
            "promoted_indices_for_vector": _active_promoted_indices_for_vector(vector_begin),
            "selected_promoted_overlap": overlap,
            "registers": regs,
            "stack": stack[:8],
        }
        _append_limited("entry_samples", packet)


def _pre_or_post_exec(kind, frame, process, regs, thread_id, stack):
    state = _state()
    call = state["active_call_by_thread"].get(str(thread_id), {})
    snapshot = _locals_snapshot(process, regs["rbp"], call.get("vector_ptr"))
    packet = {
        "site": kind,
        "call_id": call.get("call_id"),
        "thread_id": thread_id,
        "target": call.get("target"),
        "registers": regs,
        "locals": snapshot,
        "stack": stack[:8],
    }
    if kind == "pre_exec_241bbf":
        state["counts"]["pre_exec_hits"] += 1
        if call.get("target") == 2 or snapshot.get("selected_promoted_overlap"):
            _append_limited("pre_exec_samples", packet)
    else:
        state["counts"]["post_exec_hits"] += 1
        if call.get("target") == 2 or snapshot.get("selected_promoted_overlap"):
            _append_limited("post_exec_samples", packet)


def _store_sample(site, frame, process, regs, thread_id, stack):
    state = _state()
    call = state["active_call_by_thread"].get(str(thread_id), {})
    rbp = regs["rbp"]
    vec_ptr = call.get("vector_ptr")
    if not vec_ptr:
        vec_ptr_data = _read(process, rbp - 0x148, 8)
        vec_ptr = _u64(vec_ptr_data, 0) if vec_ptr_data else None
    record_vector = _record_list(process, vec_ptr) if vec_ptr else {}
    vector_begin = record_vector.get("vector", {}).get("begin")
    record_addr = None
    selected_order = None
    selected_index = None
    if site == "bitset_store_after_241cd6":
        record_offset = regs["rax"]
        selected_order = regs["rcx"]
        selected_index = record_offset // RECORD_STRIDE if record_offset % RECORD_STRIDE == 0 else None
        record_addr = vector_begin + record_offset if vector_begin is not None else None
    elif site == "fallback_store1_after_241d3b":
        record_addr = regs["rdx"] - 0x24
        selected_order = 0
        selected_index = (record_addr - vector_begin) // RECORD_STRIDE if vector_begin else None
    elif site == "fallback_store2_after_241d6a":
        record_addr = regs["rdi"] - 0x24
        selected_order = regs["rsi"]
        selected_index = (record_addr - vector_begin) // RECORD_STRIDE if vector_begin else None
    elif site == "fallback_store3_after_241d85":
        record_addr = regs["rdi"] - 0x24
        selected_order = regs["rsi"] + 1
        selected_index = (record_addr - vector_begin) // RECORD_STRIDE if vector_begin else None
    promoted = set(_active_promoted_indices_for_vector(vector_begin))
    is_promoted = selected_index in promoted
    state["counts"]["store_hits"] += 1
    if is_promoted:
        state["counts"]["store_promoted_overlap_hits"] += 1
    if len(state["store_samples"]) < state["store_sample_limit"] and (
        is_promoted or call.get("target") == 2
    ):
        state["store_samples"].append(
            {
                "site": site,
                "call_id": call.get("call_id"),
                "thread_id": thread_id,
                "target": call.get("target"),
                "selected_order": selected_order,
                "selected_index": selected_index,
                "is_promoted_index": is_promoted,
                "promoted_indices_for_vector": sorted(promoted),
                "record_addr": record_addr,
                "record_now": _record_now(process, record_addr) if record_addr else None,
                "locals": _locals_snapshot(process, rbp, vec_ptr),
                "registers": regs,
                "stack": stack[:8],
            }
        )


def hit(frame, bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    pc_va = _module_va(target, frame.GetPC())
    regs = _registers(frame)
    thread_id = frame.GetThread().GetThreadID()
    stack = _stack(frame.GetThread(), 12)
    if pc_va == GATE_BEFORE:
        state["counts"]["gate_before_hits"] += 1
        _gate_before(frame, process, regs, thread_id)
    elif pc_va == GATE_AFTER:
        state["counts"]["gate_after_hits"] += 1
        _gate_after(frame, process, regs, thread_id)
    elif pc_va == ENTRY_2416D0:
        _entry_2416d0(frame, process, regs, thread_id, stack)
    elif pc_va == PRE_EXEC_241BBF:
        _pre_or_post_exec("pre_exec_241bbf", frame, process, regs, thread_id, stack)
    elif pc_va == POST_EXEC_241BD7:
        _pre_or_post_exec("post_exec_241bd7", frame, process, regs, thread_id, stack)
    elif pc_va == BITSET_STORE_AFTER_241CD6:
        _store_sample("bitset_store_after_241cd6", frame, process, regs, thread_id, stack)
    elif pc_va == FALLBACK_STORE1_AFTER_241D3B:
        _store_sample("fallback_store1_after_241d3b", frame, process, regs, thread_id, stack)
    elif pc_va == FALLBACK_STORE2_AFTER_241D6A:
        _store_sample("fallback_store2_after_241d6a", frame, process, regs, thread_id, stack)
    elif pc_va == FALLBACK_STORE3_AFTER_241D85:
        _store_sample("fallback_store3_after_241d85", frame, process, regs, thread_id, stack)
    else:
        state["errors"].append({"error": "unexpected breakpoint", "pc_va": pc_va})
    return False


def drive_until_exit_or_step_cap(debugger):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process.IsValid() and process.GetState() == lldb.eStateStopped and steps < state["step_cap"]:
        steps += 1
        process.Continue()
    state["drive_steps"] = steps
    state["drive_hit_step_cap"] = (
        process.IsValid()
        and process.GetState() == lldb.eStateStopped
        and steps >= state["step_cap"]
    )
    print("L16_STATE5_ACCEPTANCE_DRIVE_STEPS", steps)


def payload(debugger):
    state = dict(_state())
    process = debugger.GetSelectedTarget().GetProcess()
    if process and process.IsValid():
        state["process_state"] = str(process.GetState())
        state["process_exit_status"] = process.GetExitStatus()
    return state


def report_to_file(debugger, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("WROTE", path)
