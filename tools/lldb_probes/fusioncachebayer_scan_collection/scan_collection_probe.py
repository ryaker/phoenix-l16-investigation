import builtins
import json
import os
import struct


CONSTRUCTOR_CALL = 0x3EAB4C
BASE_INIT_RETURN = 0x4064ED
RECORD_START = 0x402DE0
NORMALIZED_COMPARE = 0x402E10
FIELD_OR = 0x402E25
ACCEPT_FIRST = 0x402E35
ACCEPT_ADDITIONAL = 0x402E42
LOOP_END = 0x402E6A
FLAG_WRITE = 0x402E78


def reset(label="", max_records=64):
    builtins.l16_fusioncachebayer_scan_collection = {
        "label": label,
        "max_records": max_records,
        "counts": {
            "constructor_call": 0,
            "record_start": 0,
            "normalized_compare": 0,
            "field_or": 0,
            "accept_first": 0,
            "accept_additional": 0,
            "loop_end": 0,
            "flag_write": 0,
        },
        "constructor_calls": [],
        "records": [],
        "records_by_addr": {},
        "loop_end": [],
        "flag_write": [],
        "skipped": [],
        "errors": [],
        "loop_begin_by_object": {},
        "breakpoint_ids": {},
    }


def _state():
    if not hasattr(builtins, "l16_fusioncachebayer_scan_collection"):
        reset()
    return builtins.l16_fusioncachebayer_scan_collection


def install_callbacks(debugger, ids):
    state = _state()
    state["breakpoint_ids"] = dict(ids)
    target = debugger.GetSelectedTarget()
    callbacks = {
        ids.get("constructor_call"): "scan_collection_probe.constructor_call",
        ids.get("record_start"): "scan_collection_probe.record_start",
        ids.get("normalized_compare"): "scan_collection_probe.normalized_compare",
        ids.get("field_or"): "scan_collection_probe.field_or",
        ids.get("accept_first"): "scan_collection_probe.accept_first",
        ids.get("accept_additional"): "scan_collection_probe.accept_additional",
        ids.get("loop_end"): "scan_collection_probe.loop_end",
        ids.get("flag_write"): "scan_collection_probe.flag_write",
    }
    for bp_id, callback in callbacks.items():
        if not bp_id:
            continue
        bp = target.FindBreakpointByID(bp_id)
        if bp and bp.IsValid():
            bp.SetScriptCallbackFunction(callback)


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


def _u8(process, addr):
    data = _read(process, addr, 1)
    if data is None:
        return None
    return data[0]


def _u32(data, off=0):
    return struct.unpack_from("<I", data, off)[0]


def _i32(data, off=0):
    return struct.unpack_from("<i", data, off)[0]


def _u64(data, off=0):
    return struct.unpack_from("<Q", data, off)[0]


def _ptr(process, addr):
    data = _read(process, addr, 8)
    if data is None:
        return None
    return _u64(data)


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


def _saved_return_va(frame):
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    rbp = _u(frame, "rbp")
    data = _read(process, rbp + 8, 8)
    if data is None:
        return None
    return _module_va(target, _u64(data))


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
            }
        )
    return frames


def _pair(process, addr):
    data = _read(process, addr, 16)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "ptr_0x0": _u64(data, 0),
        "ptr_0x8": _u64(data, 8),
    }


def _candidate_fields(process, target, ptr):
    data = _read(process, ptr, 0x68)
    if data is None:
        return {"ptr": ptr, "read_ok": False}
    vtable = _u64(data, 0)
    return {
        "ptr": ptr,
        "read_ok": True,
        "vtable_0x0": vtable,
        "vtable_libcp_va": _module_va(target, vtable),
        "byte_0x14": data[0x14],
        "byte_0x30": data[0x30],
        "i32_0x58": _i32(data, 0x58),
        "i32_0x5c": _i32(data, 0x5C),
        "i32_0x60": _i32(data, 0x60),
        "u32_0x58": _u32(data, 0x58),
        "u32_0x5c": _u32(data, 0x5C),
        "u32_0x60": _u32(data, 0x60),
    }


def _skip(site, frame, reason, return_va=None):
    state = _state()
    if len(state["skipped"]) < 32:
        state["skipped"].append(
            {
                "site": site,
                "reason": reason,
                "return_va": return_va,
                "stack": _stack(frame.GetThread(), 6),
            }
        )


def _is_base_init_for_fusioncache(frame, site):
    return_va = _saved_return_va(frame)
    if return_va != BASE_INIT_RETURN:
        _skip(site, frame, "saved_return_not_4064ed", return_va)
        return False
    return True


def _object(frame):
    process = frame.GetThread().GetProcess()
    rbp = _u(frame, "rbp")
    obj = _ptr(process, rbp - 0x338)
    return obj or _u(frame, "r13")


def _loop_begin(obj, record_addr):
    state = _state()
    key = str(obj)
    if key not in state["loop_begin_by_object"]:
        state["loop_begin_by_object"][key] = record_addr
    return state["loop_begin_by_object"][key]


def _record_index(obj, record_addr):
    begin = _loop_begin(obj, record_addr)
    if begin is None or record_addr is None:
        return None
    return (record_addr - begin) // 0x10


def _record_key(obj, record_addr):
    return "%s:%s" % (obj, record_addr)


def _ensure_record(frame, record_addr=None):
    state = _state()
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    rbp = _u(frame, "rbp")
    obj = _object(frame)
    if record_addr is None:
        record_addr = _u(frame, "rbx")
    key = _record_key(obj, record_addr)
    if key in state["records_by_addr"]:
        return state["records_by_addr"][key]
    item_ptr = _ptr(process, record_addr)
    item_shared = _ptr(process, record_addr + 8)
    loop_end_ptr = _u(frame, "r14")
    index = _record_index(obj, record_addr)
    rec = {
        "object": obj,
        "record_addr": record_addr,
        "record_index": index,
        "loop_end_ptr": loop_end_ptr,
        "loop_remaining_records_including_this": ((loop_end_ptr - record_addr) // 0x10) if loop_end_ptr and record_addr else None,
        "item_ptr": item_ptr,
        "item_shared": item_shared,
        "candidate_fields_at_start": _candidate_fields(process, target, item_ptr),
        "target_norm_from_rbp_minus_0x128": _i32(_read(process, rbp - 0x128, 4), 0) if _read(process, rbp - 0x128, 4) else None,
        "events": [],
    }
    if len(state["records"]) < state["max_records"]:
        state["records"].append(rec)
        state["records_by_addr"][key] = rec
    return rec


def _append_event(rec, event):
    if rec is None:
        return
    rec["events"].append(event)


def constructor_call(frame, bp_loc, internal_dict):
    state = _state()
    state["counts"]["constructor_call"] += 1
    thread = frame.GetThread()
    process = thread.GetProcess()
    sample = {
        "site_va": CONSTRUCTOR_CALL,
        "object": _u(frame, "r13"),
        "pipelinecache": _u(frame, "r14"),
        "rdi_object": _u(frame, "rdi"),
        "rsi_shared_arg": _u(frame, "rsi"),
        "rdx_context_arg": _u(frame, "rdx"),
        "shared_arg_pair": _pair(process, _u(frame, "rsi")),
        "context_arg_pair": _pair(process, _u(frame, "rdx")),
        "stack": _stack(thread, 8),
    }
    if len(state["constructor_calls"]) < 8:
        state["constructor_calls"].append(sample)
    return False


def record_start(frame, bp_loc, internal_dict):
    state = _state()
    state["counts"]["record_start"] += 1
    if not _is_base_init_for_fusioncache(frame, "record_start"):
        return False
    rec = _ensure_record(frame)
    _append_event(
        rec,
        {
            "site": "record_start",
            "site_va": RECORD_START,
            "r15d_before_record": _u(frame, "r15") & 0xFFFFFFFF,
        },
    )
    return False


def normalized_compare(frame, bp_loc, internal_dict):
    state = _state()
    state["counts"]["normalized_compare"] += 1
    if not _is_base_init_for_fusioncache(frame, "normalized_compare"):
        return False
    process = frame.GetThread().GetProcess()
    rbp = _u(frame, "rbp")
    rec = _ensure_record(frame)
    current_norm_data = _read(process, rbp - 0x130, 4)
    target_norm_data = _read(process, rbp - 0x128, 4)
    current_norm = _i32(current_norm_data, 0) if current_norm_data else None
    target_norm = _i32(target_norm_data, 0) if target_norm_data else None
    _append_event(
        rec,
        {
            "site": "normalized_compare",
            "site_va": NORMALIZED_COMPARE,
            "eax_current_norm": _u(frame, "rax") & 0xFFFFFFFF,
            "current_norm_from_stack": current_norm,
            "target_norm_from_stack": target_norm,
            "norm_matches_target": current_norm == target_norm if current_norm is not None and target_norm is not None else None,
        },
    )
    return False


def field_or(frame, bp_loc, internal_dict):
    state = _state()
    state["counts"]["field_or"] += 1
    if not _is_base_init_for_fusioncache(frame, "field_or"):
        return False
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    rec = _ensure_record(frame)
    pair_addr = _u(frame, "rax")
    pair_data = _read(process, pair_addr, 8)
    or_value = _u(frame, "rcx") & 0xFFFFFFFF
    _append_event(
        rec,
        {
            "site": "field_or",
            "site_va": FIELD_OR,
            "f2750_return": pair_addr,
            "f2750_return_libcp_va": _module_va(target, pair_addr),
            "i32_0x58": _i32(pair_data, 0) if pair_data else None,
            "i32_0x5c": _i32(pair_data, 4) if pair_data else None,
            "or_value": or_value,
            "or_value_signed": struct.unpack("<i", struct.pack("<I", or_value))[0],
            "sign_bit_set": bool(or_value & 0x80000000),
            "r15d_before_accept": _u(frame, "r15") & 0xFFFFFFFF,
        },
    )
    return False


def accept_first(frame, bp_loc, internal_dict):
    state = _state()
    state["counts"]["accept_first"] += 1
    if not _is_base_init_for_fusioncache(frame, "accept_first"):
        return False
    rec = _ensure_record(frame)
    _append_event(
        rec,
        {
            "site": "accept_first",
            "site_va": ACCEPT_FIRST,
            "selected_key_eax": _u(frame, "rax") & 0xFFFFFFFF,
            "previous_r15d": _u(frame, "r15") & 0xFFFFFFFF,
        },
    )
    return False


def accept_additional(frame, bp_loc, internal_dict):
    state = _state()
    state["counts"]["accept_additional"] += 1
    if not _is_base_init_for_fusioncache(frame, "accept_additional"):
        return False
    rec = _ensure_record(frame)
    _append_event(
        rec,
        {
            "site": "accept_additional",
            "site_va": ACCEPT_ADDITIONAL,
            "candidate_key_eax": _u(frame, "rax") & 0xFFFFFFFF,
            "existing_r15d": _u(frame, "r15") & 0xFFFFFFFF,
        },
    )
    return False


def loop_end(frame, bp_loc, internal_dict):
    state = _state()
    state["counts"]["loop_end"] += 1
    if not _is_base_init_for_fusioncache(frame, "loop_end"):
        return False
    sample = {
        "site_va": LOOP_END,
        "object": _object(frame),
        "final_r15d": _u(frame, "r15") & 0xFFFFFFFF,
        "records_observed": len(state["records"]),
        "stack": _stack(frame.GetThread(), 8),
    }
    if len(state["loop_end"]) < 8:
        state["loop_end"].append(sample)
    return False


def flag_write(frame, bp_loc, internal_dict):
    state = _state()
    state["counts"]["flag_write"] += 1
    if not _is_base_init_for_fusioncache(frame, "flag_write"):
        return False
    sample = {
        "site_va": FLAG_WRITE,
        "object": _object(frame),
        "al_flag": _u(frame, "rax") & 0xFF,
        "eax": _u(frame, "rax") & 0xFFFFFFFF,
        "r15d": _u(frame, "r15") & 0xFFFFFFFF,
        "stack": _stack(frame.GetThread(), 8),
    }
    if len(state["flag_write"]) < 8:
        state["flag_write"].append(sample)
    return False


def _record_summary(rec):
    norm = None
    field = None
    accepted = None
    additional = []
    for event in rec.get("events", []):
        if event.get("site") == "normalized_compare":
            norm = event
        elif event.get("site") == "field_or":
            field = event
        elif event.get("site") == "accept_first":
            accepted = event
        elif event.get("site") == "accept_additional":
            additional.append(event)
    fields = rec.get("candidate_fields_at_start", {})
    return {
        "record_index": rec.get("record_index"),
        "item_ptr": rec.get("item_ptr"),
        "item_shared": rec.get("item_shared"),
        "vtable_libcp_va": fields.get("vtable_libcp_va"),
        "byte_0x14": fields.get("byte_0x14"),
        "byte_0x30": fields.get("byte_0x30"),
        "key_0x60": fields.get("i32_0x60"),
        "field_0x58": fields.get("i32_0x58"),
        "field_0x5c": fields.get("i32_0x5c"),
        "norm_matches_target": norm.get("norm_matches_target") if norm else None,
        "sign_bit_set": field.get("sign_bit_set") if field else None,
        "accepted_first_key": accepted.get("selected_key_eax") if accepted else None,
        "additional_candidate_keys": [item.get("candidate_key_eax") for item in additional],
    }


def _summary(state):
    record_summaries = [_record_summary(rec) for rec in state.get("records", [])]
    accepted_keys = [item["accepted_first_key"] for item in record_summaries if item.get("accepted_first_key") is not None]
    return {
        "label": state.get("label", ""),
        "counts": state.get("counts", {}),
        "constructor_calls": len(state.get("constructor_calls", [])),
        "records_observed": len(state.get("records", [])),
        "loop_final_r15d": [entry.get("final_r15d") for entry in state.get("loop_end", [])],
        "flags_written": [entry.get("al_flag") for entry in state.get("flag_write", [])],
        "accepted_first_keys": accepted_keys,
        "record_summaries": record_summaries,
    }


def snapshot(label=None):
    state = _state()
    if label is not None:
        state["label"] = label
    return {"summary": _summary(state), "state": state}


def report_to_file(path, label=None, require_records=True):
    data = snapshot(label)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if require_records and data["summary"]["records_observed"] == 0:
        failed_path = path + ".failed"
        with open(failed_path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, sort_keys=True, indent=2)
            handle.write("\n")
        print("L16_FUSIONCACHEBAYER_SCAN_COLLECTION_REPORT_REFUSED", path)
        print("L16_FUSIONCACHEBAYER_SCAN_COLLECTION_FAILED_REPORT_FILE", failed_path)
        raise RuntimeError("refusing to overwrite evidence report because no scan records were captured")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, sort_keys=True, indent=2)
        handle.write("\n")
    print("L16_FUSIONCACHEBAYER_SCAN_COLLECTION_REPORT_FILE", path)
    print("L16_FUSIONCACHEBAYER_SCAN_COLLECTION_SUMMARY", json.dumps(data["summary"], sort_keys=True))
