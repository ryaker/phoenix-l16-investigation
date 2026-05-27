import builtins
import json
import struct


VISIBLE_SRC2_RETURN = 0x3ECDAD
BEFORE_SOURCE_CALL = 0x3EBF5D
AFTER_SOURCE_CALL = 0x3EBF5F


def reset(label="", sample_limit=8, stop_after_after=True):
    builtins.l16_src2_descriptor_origin = {
        "label": label,
        "sample_limit": sample_limit,
        "stop_after_after": stop_after_after,
        "before_hits": 0,
        "after_hits": 0,
        "accepted_before": [],
        "accepted_after": [],
        "skipped_before": [],
        "skipped_after": [],
        "pending": {},
        "errors": [],
        "breakpoint_ids": {},
    }


def _state():
    if not hasattr(builtins, "l16_src2_descriptor_origin"):
        reset()
    return builtins.l16_src2_descriptor_origin


def install_callbacks(debugger, ids):
    state = _state()
    state["breakpoint_ids"] = dict(ids)
    target = debugger.GetSelectedTarget()
    callbacks = {
        ids.get("before"): "src2_descriptor_origin_probe.before_source_call",
        ids.get("after"): "src2_descriptor_origin_probe.after_source_call",
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


def _u64(data, off=0):
    return struct.unpack_from("<Q", data, off)[0]


def _i32(data, off=0):
    return struct.unpack_from("<i", data, off)[0]


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


def _load_addr(target, ptr):
    if not ptr:
        return None
    base = _libcp_base(target)
    if base is None:
        return ptr
    if ptr >= base:
        return ptr
    return base + ptr


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


def _saved_return_va(frame):
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    rbp = _u(frame, "rbp")
    data = _read(process, rbp + 8, 8)
    if data is None:
        return None
    return _module_va(target, _u64(data))


def _descriptor(process, addr):
    data = _read(process, addr, 0x30)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "qword_00": _u64(data, 0x00),
        "qword_08": _u64(data, 0x08),
        "width_0x10": _i32(data, 0x10),
        "height_0x14": _i32(data, 0x14),
        "stride_0x18": _i32(data, 0x18),
        "data_ptr_0x20": _u64(data, 0x20),
        "qword_28": _u64(data, 0x28),
    }


def _i32_tuple(process, addr, count):
    data = _read(process, addr, count * 4)
    if data is None:
        return None
    return [_i32(data, off) for off in range(0, count * 4, 4)]


def _ptr(process, addr):
    data = _read(process, addr, 8)
    if data is None:
        return None
    return _u64(data)


def _call_target_info(process, target, obj, rax_target):
    vptr = _ptr(process, obj)
    slot18 = None
    if vptr:
        slot18 = _ptr(process, _load_addr(target, vptr) + 0x18)
    return {
        "object": obj,
        "vptr": vptr,
        "vptr_va": _module_va(target, _load_addr(target, vptr)) if vptr else None,
        "slot18_raw": slot18,
        "slot18_load": _load_addr(target, slot18) if slot18 else None,
        "slot18_va": _module_va(target, _load_addr(target, slot18)) if slot18 else None,
        "rax_target": rax_target,
        "rax_target_va": _module_va(target, rax_target),
    }


def before_source_call(frame, bp_loc, internal_dict):
    state = _state()
    state["before_hits"] += 1
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    return_va = _saved_return_va(frame)
    if return_va != VISIBLE_SRC2_RETURN:
        if len(state["skipped_before"]) < state["sample_limit"]:
            state["skipped_before"].append({"return_va": return_va, "stack": _stack(thread, 6)})
        return False

    tid = thread.GetThreadID()
    pipeline_cache = _u(frame, "r12")
    src_desc_out = _u(frame, "rsi")
    region_ptr = _u(frame, "rdx")
    obj = _u(frame, "rdi")
    rax_target = _u(frame, "rax")
    sample = {
        "site_va": BEFORE_SOURCE_CALL,
        "return_va": return_va,
        "thread_id": tid,
        "pipeline_cache": pipeline_cache,
        "pipeline_cache_0x1d8": _ptr(process, pipeline_cache + 0x1D8),
        "pipeline_cache_0x1e0": _ptr(process, pipeline_cache + 0x1E0),
        "source_descriptor_out": src_desc_out,
        "source_descriptor_before": _descriptor(process, src_desc_out),
        "region_ptr": region_ptr,
        "region_i32_4": _i32_tuple(process, region_ptr, 4),
        "call_target": _call_target_info(process, target, obj, rax_target),
        "stack": _stack(thread, 8),
    }
    state["pending"][str(tid)] = sample
    if len(state["accepted_before"]) < state["sample_limit"]:
        state["accepted_before"].append(sample)
    return False


def after_source_call(frame, bp_loc, internal_dict):
    state = _state()
    state["after_hits"] += 1
    thread = frame.GetThread()
    process = thread.GetProcess()
    return_va = _saved_return_va(frame)
    if return_va != VISIBLE_SRC2_RETURN:
        if len(state["skipped_after"]) < state["sample_limit"]:
            state["skipped_after"].append({"return_va": return_va, "stack": _stack(thread, 6)})
        return False

    tid = str(thread.GetThreadID())
    before = state["pending"].pop(tid, None)
    src_desc_out = before["source_descriptor_out"] if before else _u(frame, "r14")
    sample = {
        "site_va": AFTER_SOURCE_CALL,
        "return_va": return_va,
        "thread_id": thread.GetThreadID(),
        "before": before,
        "source_descriptor_after": _descriptor(process, src_desc_out),
        "stack": _stack(thread, 8),
    }
    if len(state["accepted_after"]) < state["sample_limit"]:
        state["accepted_after"].append(sample)
    return state.get("stop_after_after", True)


def report(label=None):
    state = _state()
    if label is not None:
        state["label"] = label
    summary = {
        "label": state.get("label", ""),
        "before_hits": state.get("before_hits", 0),
        "after_hits": state.get("after_hits", 0),
        "accepted_before_count": len(state.get("accepted_before", [])),
        "accepted_after_count": len(state.get("accepted_after", [])),
        "slot18_vas": sorted(
            {
                entry.get("call_target", {}).get("slot18_va")
                for entry in state.get("accepted_before", [])
                if entry.get("call_target", {}).get("slot18_va") is not None
            }
        ),
        "rax_target_vas": sorted(
            {
                entry.get("call_target", {}).get("rax_target_va")
                for entry in state.get("accepted_before", [])
                if entry.get("call_target", {}).get("rax_target_va") is not None
            }
        ),
    }
    print("L16_SRC2_DESCRIPTOR_ORIGIN_PROBE_BEGIN", state.get("label", ""))
    print("L16_SRC2_DESCRIPTOR_ORIGIN_SUMMARY", json.dumps(summary, sort_keys=True))
    printable = dict(state)
    printable["pending"] = {}
    print(json.dumps(printable, sort_keys=True))
    print("L16_SRC2_DESCRIPTOR_ORIGIN_PROBE_END", state.get("label", ""))
