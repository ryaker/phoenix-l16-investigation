import builtins
import json
import os
import struct


CONSTRUCTOR_CALL = 0x3EAB4C
CONSTRUCTOR_RETURN = 0x3EAB51
PIPELINECACHE_STORE_BEFORE = 0x3EAB58
PIPELINECACHE_STORE_AFTER = 0x3EAB5E
BASE_INIT_RETURN = 0x4064ED
BASE_INIT_DIRECT_ZERO = 0x402D89
BASE_INIT_LOOP_ENTRY = 0x402D90
BASE_INIT_LOOP_FINALIZE = 0x402E6E
BASE_INIT_WRITE = 0x402E78
BASE_INIT_AFTER_WRITE = 0x402E7C
CONSTRUCTOR_BRANCH = 0x4066FC
FIELD20_STORE = 0x406774


def reset(label="", sample_limit=12, stop_after_store=False):
    builtins.l16_fusioncachebayer_flag_origin = {
        "label": label,
        "sample_limit": sample_limit,
        "stop_after_store": stop_after_store,
        "counts": {
            "constructor_call": 0,
            "base_init_direct_zero": 0,
            "base_init_loop_entry": 0,
            "base_init_loop_finalize": 0,
            "base_init_write": 0,
            "base_init_after_write": 0,
            "constructor_branch": 0,
            "field20_store": 0,
            "pipelinecache_store_before": 0,
            "pipelinecache_store_after": 0,
        },
        "constructor_calls": [],
        "base_init_events": [],
        "constructor_branches": [],
        "field20_stores": [],
        "pipelinecache_stores": [],
        "objects": {},
        "skipped": [],
        "errors": [],
        "breakpoint_ids": {},
    }


def _state():
    if not hasattr(builtins, "l16_fusioncachebayer_flag_origin"):
        reset()
    return builtins.l16_fusioncachebayer_flag_origin


def install_callbacks(debugger, ids):
    state = _state()
    state["breakpoint_ids"] = dict(ids)
    target = debugger.GetSelectedTarget()
    callbacks = {
        ids.get("constructor_call"): "fusioncachebayer_flag_origin_probe.constructor_call",
        ids.get("direct_zero"): "fusioncachebayer_flag_origin_probe.base_init_direct_zero",
        ids.get("loop_entry"): "fusioncachebayer_flag_origin_probe.base_init_loop_entry",
        ids.get("loop_finalize"): "fusioncachebayer_flag_origin_probe.base_init_loop_finalize",
        ids.get("write"): "fusioncachebayer_flag_origin_probe.base_init_write",
        ids.get("after_write"): "fusioncachebayer_flag_origin_probe.base_init_after_write",
        ids.get("constructor_branch"): "fusioncachebayer_flag_origin_probe.constructor_branch",
        ids.get("field20_store"): "fusioncachebayer_flag_origin_probe.field20_store",
        ids.get("store_before"): "fusioncachebayer_flag_origin_probe.pipelinecache_store_before",
        ids.get("store_after"): "fusioncachebayer_flag_origin_probe.pipelinecache_store_after",
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
    if not addr:
        return {"addr": addr, "read_ok": False}
    data = _read(process, addr, 16)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "ptr_0x0": _u64(data, 0),
        "ptr_0x8": _u64(data, 8),
    }


def _object_fields(process, obj):
    if not obj:
        return {"object": obj, "read_ok": False}
    data = _read(process, obj, 0x138)
    if data is None:
        return {"object": obj, "read_ok": False}
    return {
        "object": obj,
        "read_ok": True,
        "vtable_0x0": _u64(data, 0x0),
        "field_0x8": _u64(data, 0x8),
        "field_0x10": _u64(data, 0x10),
        "flag_0x18": data[0x18],
        "field_0x20": _u64(data, 0x20),
        "field_0xe0": _u64(data, 0xE0),
        "field_0xf0": _u64(data, 0xF0),
        "field_0x100": _u64(data, 0x100),
        "i32_0x110": _i32(data, 0x110),
        "field_0x120": _u64(data, 0x120),
        "field_0x128": _u64(data, 0x128),
    }


def _record_list(key, sample):
    state = _state()
    if len(state[key]) < state["sample_limit"]:
        state[key].append(sample)


def _object_key(obj):
    return str(obj)


def _object_state(obj):
    state = _state()
    key = _object_key(obj)
    if key not in state["objects"]:
        state["objects"][key] = {"object": obj, "events": []}
    return state["objects"][key]


def _add_object_event(obj, event):
    if not obj:
        return
    item = _object_state(obj)
    item["events"].append(event)


def _skip(site, frame, reason, return_va=None):
    state = _state()
    if len(state["skipped"]) < state["sample_limit"]:
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


def _is_constructor_for_pipelinecache(frame, site):
    return_va = _saved_return_va(frame)
    if return_va != CONSTRUCTOR_RETURN:
        _skip(site, frame, "saved_return_not_3eab51", return_va)
        return False
    return True


def constructor_call(frame, bp_loc, internal_dict):
    state = _state()
    state["counts"]["constructor_call"] += 1
    thread = frame.GetThread()
    process = thread.GetProcess()
    obj = _u(frame, "r13")
    pipelinecache = _u(frame, "r14")
    holder = _ptr(process, _u(frame, "rbp") - 0xD8)
    sample = {
        "site_va": CONSTRUCTOR_CALL,
        "object": obj,
        "pipelinecache": pipelinecache,
        "holder_from_stack_rbp_minus_0xd8": holder,
        "holder_offset_from_pipelinecache": holder - pipelinecache if holder and pipelinecache else None,
        "rdi_object": _u(frame, "rdi"),
        "rsi_shared_arg": _u(frame, "rsi"),
        "rdx_context_arg": _u(frame, "rdx"),
        "shared_arg_pair": _pair(process, _u(frame, "rsi")),
        "context_arg_pair": _pair(process, _u(frame, "rdx")),
        "stack": _stack(thread, 8),
    }
    _add_object_event(obj, {"site": "constructor_call", "sample": sample})
    _record_list("constructor_calls", sample)
    return False


def _base_init_event(frame, site, site_va):
    thread = frame.GetThread()
    process = thread.GetProcess()
    rbp = _u(frame, "rbp")
    obj = _u(frame, "r13")
    if site == "base_init_loop_entry":
        shared_arg = _u(frame, "rbx")
        shared_arg_source = "rbx_before_rbp_minus_0x330_initialization"
    else:
        shared_arg = _ptr(process, rbp - 0x330)
        shared_arg_source = "rbp_minus_0x330"
    context_arg = _ptr(process, rbp - 0x328)
    rax = _u(frame, "rax")
    r15d = _u(frame, "r15") & 0xFFFFFFFF
    sample = {
        "site": site,
        "site_va": site_va,
        "return_va": _saved_return_va(frame),
        "thread_id": thread.GetThreadID(),
        "object": obj,
        "al": rax & 0xFF,
        "eax": rax & 0xFFFFFFFF,
        "r15d": r15d,
        "shared_arg_from_stack": shared_arg,
        "shared_arg_source": shared_arg_source,
        "context_arg_from_stack": context_arg,
        "shared_arg_pair": _pair(process, shared_arg),
        "context_arg_pair": _pair(process, context_arg),
        "object_fields": _object_fields(process, obj),
        "stack": _stack(thread, 8),
    }
    _add_object_event(obj, {"site": site, "sample": sample})
    _record_list("base_init_events", sample)
    return False


def base_init_direct_zero(frame, bp_loc, internal_dict):
    state = _state()
    state["counts"]["base_init_direct_zero"] += 1
    if not _is_base_init_for_fusioncache(frame, "base_init_direct_zero"):
        return False
    return _base_init_event(frame, "base_init_direct_zero", BASE_INIT_DIRECT_ZERO)


def base_init_loop_entry(frame, bp_loc, internal_dict):
    state = _state()
    state["counts"]["base_init_loop_entry"] += 1
    if not _is_base_init_for_fusioncache(frame, "base_init_loop_entry"):
        return False
    return _base_init_event(frame, "base_init_loop_entry", BASE_INIT_LOOP_ENTRY)


def base_init_loop_finalize(frame, bp_loc, internal_dict):
    state = _state()
    state["counts"]["base_init_loop_finalize"] += 1
    if not _is_base_init_for_fusioncache(frame, "base_init_loop_finalize"):
        return False
    return _base_init_event(frame, "base_init_loop_finalize", BASE_INIT_LOOP_FINALIZE)


def base_init_write(frame, bp_loc, internal_dict):
    state = _state()
    state["counts"]["base_init_write"] += 1
    if not _is_base_init_for_fusioncache(frame, "base_init_write"):
        return False
    return _base_init_event(frame, "base_init_write", BASE_INIT_WRITE)


def base_init_after_write(frame, bp_loc, internal_dict):
    state = _state()
    state["counts"]["base_init_after_write"] += 1
    if not _is_base_init_for_fusioncache(frame, "base_init_after_write"):
        return False
    return _base_init_event(frame, "base_init_after_write", BASE_INIT_AFTER_WRITE)


def constructor_branch(frame, bp_loc, internal_dict):
    state = _state()
    state["counts"]["constructor_branch"] += 1
    if not _is_constructor_for_pipelinecache(frame, "constructor_branch"):
        return False
    thread = frame.GetThread()
    process = thread.GetProcess()
    obj = _u(frame, "r13")
    sample = {
        "site_va": CONSTRUCTOR_BRANCH,
        "return_va": _saved_return_va(frame),
        "thread_id": thread.GetThreadID(),
        "object": obj,
        "object_fields": _object_fields(process, obj),
        "flag_0x18": _u8(process, obj + 0x18),
        "field_0x20_before_branch": _ptr(process, obj + 0x20),
        "stack": _stack(thread, 8),
    }
    _add_object_event(obj, {"site": "constructor_branch", "sample": sample})
    _record_list("constructor_branches", sample)
    return False


def field20_store(frame, bp_loc, internal_dict):
    state = _state()
    state["counts"]["field20_store"] += 1
    if not _is_constructor_for_pipelinecache(frame, "field20_store"):
        return False
    thread = frame.GetThread()
    process = thread.GetProcess()
    obj = _u(frame, "r13")
    sample = {
        "site_va": FIELD20_STORE,
        "return_va": _saved_return_va(frame),
        "thread_id": thread.GetThreadID(),
        "object": obj,
        "new_field_0x20_r12": _u(frame, "r12"),
        "old_field_0x20_before_store": _ptr(process, obj + 0x20),
        "flag_0x18": _u8(process, obj + 0x18),
        "object_fields": _object_fields(process, obj),
        "stack": _stack(thread, 8),
    }
    _add_object_event(obj, {"site": "field20_store", "sample": sample})
    _record_list("field20_stores", sample)
    return False


def _pipelinecache_store(frame, site, site_va, after):
    thread = frame.GetThread()
    process = thread.GetProcess()
    obj = _u(frame, "r13")
    pipelinecache = _u(frame, "r14")
    holder = _u(frame, "rbx")
    sample = {
        "site": site,
        "site_va": site_va,
        "thread_id": thread.GetThreadID(),
        "object": obj,
        "pipelinecache": pipelinecache,
        "holder": holder,
        "holder_offset_from_pipelinecache": holder - pipelinecache if holder and pipelinecache else None,
        "holder_value": _ptr(process, holder),
        "object_fields": _object_fields(process, obj),
        "stack": _stack(thread, 8),
    }
    _add_object_event(obj, {"site": site, "sample": sample})
    _record_list("pipelinecache_stores", sample)
    return after and _state().get("stop_after_store", False)


def pipelinecache_store_before(frame, bp_loc, internal_dict):
    state = _state()
    state["counts"]["pipelinecache_store_before"] += 1
    return _pipelinecache_store(frame, "pipelinecache_store_before", PIPELINECACHE_STORE_BEFORE, False)


def pipelinecache_store_after(frame, bp_loc, internal_dict):
    state = _state()
    state["counts"]["pipelinecache_store_after"] += 1
    return _pipelinecache_store(frame, "pipelinecache_store_after", PIPELINECACHE_STORE_AFTER, True)


def _summary(state):
    flags_written = sorted(
        {
            event.get("al")
            for event in state.get("base_init_events", [])
            if event.get("site") == "base_init_write" and event.get("al") is not None
        }
    )
    flags_after_write = sorted(
        {
            event.get("object_fields", {}).get("flag_0x18")
            for event in state.get("base_init_events", [])
            if event.get("site") == "base_init_after_write"
            and event.get("object_fields", {}).get("flag_0x18") is not None
        }
    )
    branch_flags = sorted(
        {
            entry.get("flag_0x18")
            for entry in state.get("constructor_branches", [])
            if entry.get("flag_0x18") is not None
        }
    )
    holder_offsets = sorted(
        {
            entry.get("holder_offset_from_pipelinecache")
            for entry in state.get("pipelinecache_stores", [])
            if entry.get("holder_offset_from_pipelinecache") is not None
        }
    )
    field20_store_count = len(state.get("field20_stores", []))
    return {
        "label": state.get("label", ""),
        "counts": state.get("counts", {}),
        "accepted_constructor_calls": len(state.get("constructor_calls", [])),
        "accepted_base_init_events": len(state.get("base_init_events", [])),
        "accepted_constructor_branches": len(state.get("constructor_branches", [])),
        "accepted_field20_stores": field20_store_count,
        "accepted_pipelinecache_stores": len(state.get("pipelinecache_stores", [])),
        "flags_written_at_0x402e78": flags_written,
        "flags_read_after_0x402e78": flags_after_write,
        "flags_at_constructor_branch_0x4066fc": branch_flags,
        "pipelinecache_holder_offsets": holder_offsets,
        "field20_store_sample_count": field20_store_count,
    }


def snapshot(label=None):
    state = _state()
    if label is not None:
        state["label"] = label
    return {"summary": _summary(state), "state": state}


def report(label=None):
    state = _state()
    if label is not None:
        state["label"] = label
    summary = _summary(state)
    print("L16_FUSIONCACHEBAYER_FLAG_ORIGIN_PROBE_BEGIN", state.get("label", ""))
    print("L16_FUSIONCACHEBAYER_FLAG_ORIGIN_SUMMARY", json.dumps(summary, sort_keys=True))
    print(json.dumps(state, sort_keys=True))
    print("L16_FUSIONCACHEBAYER_FLAG_ORIGIN_PROBE_END", state.get("label", ""))


def report_to_file(path, label=None, require_hits=True):
    data = snapshot(label)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if require_hits and data["summary"]["accepted_constructor_calls"] == 0:
        failed_path = path + ".failed"
        with open(failed_path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, sort_keys=True, indent=2)
            handle.write("\n")
        print("L16_FUSIONCACHEBAYER_FLAG_ORIGIN_REPORT_REFUSED", path)
        print("L16_FUSIONCACHEBAYER_FLAG_ORIGIN_FAILED_REPORT_FILE", failed_path)
        raise RuntimeError("refusing to overwrite evidence report because no constructor call was captured")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, sort_keys=True, indent=2)
        handle.write("\n")
    print("L16_FUSIONCACHEBAYER_FLAG_ORIGIN_REPORT_FILE", path)
    print("L16_FUSIONCACHEBAYER_FLAG_ORIGIN_SUMMARY", json.dumps(data["summary"], sort_keys=True))
