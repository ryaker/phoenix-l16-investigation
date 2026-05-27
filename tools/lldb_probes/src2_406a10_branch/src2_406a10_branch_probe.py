import builtins
import json
import struct


CALLER_AFTER_406A10 = 0x3EBF5F
VISIBLE_SRC2_RETURN = 0x3ECDAD
ENTRY_AFTER_PROLOGUE = 0x406A2D
BRANCH_31B110 = 0x40721B
BRANCH_31ACF0 = 0x407458


def reset(label="", sample_limit=8, stop_after_after=True):
    builtins.l16_src2_406a10_branch = {
        "label": label,
        "sample_limit": sample_limit,
        "stop_after_after": stop_after_after,
        "entry_hits": 0,
        "branch_31b110_hits": 0,
        "branch_31acf0_hits": 0,
        "after_hits": 0,
        "accepted_entries": [],
        "accepted_branches": [],
        "accepted_after": [],
        "skipped_entries": [],
        "skipped_after": [],
        "pending": {},
        "errors": [],
        "breakpoint_ids": {},
    }


def _state():
    if not hasattr(builtins, "l16_src2_406a10_branch"):
        reset()
    return builtins.l16_src2_406a10_branch


def install_callbacks(debugger, ids):
    state = _state()
    state["breakpoint_ids"] = dict(ids)
    target = debugger.GetSelectedTarget()
    callbacks = {
        ids.get("entry"): "src2_406a10_branch_probe.entry_406a10",
        ids.get("branch_31b110"): "src2_406a10_branch_probe.branch_31b110",
        ids.get("branch_31acf0"): "src2_406a10_branch_probe.branch_31acf0",
        ids.get("after"): "src2_406a10_branch_probe.after_406a10",
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


def _u64(data, off=0):
    return struct.unpack_from("<Q", data, off)[0]


def _i32(data, off=0):
    return struct.unpack_from("<i", data, off)[0]


def _f32(data, off=0):
    return struct.unpack_from("<f", data, off)[0]


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


def _ptr(process, addr):
    data = _read(process, addr, 8)
    if data is None:
        return None
    return _u64(data)


def _i32_tuple(process, addr, count):
    data = _read(process, addr, count * 4)
    if data is None:
        return None
    return [_i32(data, off) for off in range(0, count * 4, 4)]


def _f32_tuple(process, addr, count):
    data = _read(process, addr, count * 4)
    if data is None:
        return None
    return [_f32(data, off) for off in range(0, count * 4, 4)]


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


def _object_fields(process, obj):
    i32_0x110 = _read(process, obj + 0x110, 4)
    return {
        "object": obj,
        "flag_0x18": _u8(process, obj + 0x18),
        "field_0x8": _ptr(process, obj + 0x8),
        "field_0x20": _ptr(process, obj + 0x20),
        "field_0xe0": _ptr(process, obj + 0xE0),
        "i32_0x110": _i32(i32_0x110, 0) if i32_0x110 is not None else None,
        "field_0x128": _ptr(process, obj + 0x128),
    }


def _entry_ref(entry):
    if entry is None:
        return None
    return {
        "site_va": entry.get("site_va"),
        "return_va": entry.get("return_va"),
        "thread_id": entry.get("thread_id"),
        "object_fields": entry.get("object_fields"),
        "source_descriptor_out": entry.get("source_descriptor_out"),
        "source_descriptor_before": entry.get("source_descriptor_before"),
        "region_ptr": entry.get("region_ptr"),
        "region_i32_4": entry.get("region_i32_4"),
    }


def _record_branch(frame, helper_va, helper_name):
    state = _state()
    if helper_va == 0x31B110:
        state["branch_31b110_hits"] += 1
    elif helper_va == 0x31ACF0:
        state["branch_31acf0_hits"] += 1

    return_va = _saved_return_va(frame)
    tid = str(frame.GetThread().GetThreadID())
    pending = state["pending"].get(tid)
    if return_va != CALLER_AFTER_406A10 or pending is None:
        return False

    process = frame.GetThread().GetProcess()
    sample = {
        "site_va": BRANCH_31B110 if helper_va == 0x31B110 else BRANCH_31ACF0,
        "helper_va": helper_va,
        "helper_name": helper_name,
        "thread_id": frame.GetThread().GetThreadID(),
        "return_va": return_va,
        "rdi": _u(frame, "rdi"),
        "rsi": _u(frame, "rsi"),
        "rdx": _u(frame, "rdx"),
        "rcx": _u(frame, "rcx"),
        "r8": _u(frame, "r8"),
        "r9": _u(frame, "r9"),
        "output_descriptor_before_helper": _descriptor(process, _u(frame, "rsi")),
        "rdx_descriptor": _descriptor(process, _u(frame, "rdx")),
        "rcx_descriptor": _descriptor(process, _u(frame, "rcx")),
        "r8_i32_4": _i32_tuple(process, _u(frame, "r8"), 4),
        "r8_f32_4": _f32_tuple(process, _u(frame, "r8"), 4),
        "r9_descriptor": _descriptor(process, _u(frame, "r9")),
        "entry_ref": _entry_ref(pending),
        "stack": _stack(frame.GetThread(), 8),
    }
    pending.setdefault("branches", []).append(sample)
    if len(state["accepted_branches"]) < state["sample_limit"]:
        state["accepted_branches"].append(sample)
    return False


def entry_406a10(frame, bp_loc, internal_dict):
    state = _state()
    state["entry_hits"] += 1
    return_va = _saved_return_va(frame)
    thread = frame.GetThread()
    process = thread.GetProcess()
    if return_va != CALLER_AFTER_406A10:
        if len(state["skipped_entries"]) < state["sample_limit"]:
            state["skipped_entries"].append({"return_va": return_va, "stack": _stack(thread, 6)})
        return False

    obj = _u(frame, "r15")
    out_desc = _u(frame, "r14")
    region_ptr = _u(frame, "r12")
    sample = {
        "site_va": ENTRY_AFTER_PROLOGUE,
        "return_va": return_va,
        "thread_id": thread.GetThreadID(),
        "object_fields": _object_fields(process, obj),
        "source_descriptor_out": out_desc,
        "source_descriptor_before": _descriptor(process, out_desc),
        "region_ptr": region_ptr,
        "region_i32_4": _i32_tuple(process, region_ptr, 4),
        "branches": [],
        "stack": _stack(thread, 8),
    }
    state["pending"][str(thread.GetThreadID())] = sample
    if len(state["accepted_entries"]) < state["sample_limit"]:
        state["accepted_entries"].append(sample)
    return False


def branch_31b110(frame, bp_loc, internal_dict):
    return _record_branch(frame, 0x31B110, "0x31b110")


def branch_31acf0(frame, bp_loc, internal_dict):
    return _record_branch(frame, 0x31ACF0, "0x31acf0")


def after_406a10(frame, bp_loc, internal_dict):
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
    pending = state["pending"].pop(tid, None)
    out_desc = pending["source_descriptor_out"] if pending else _u(frame, "r14")
    sample = {
        "site_va": CALLER_AFTER_406A10,
        "return_va": return_va,
        "thread_id": thread.GetThreadID(),
        "entry": pending,
        "source_descriptor_after": _descriptor(process, out_desc),
        "stack": _stack(thread, 8),
    }
    if len(state["accepted_after"]) < state["sample_limit"]:
        state["accepted_after"].append(sample)
    return state.get("stop_after_after", True)


def report(label=None):
    state = _state()
    if label is not None:
        state["label"] = label
    branch_vas = sorted(
        {
            entry.get("helper_va")
            for entry in state.get("accepted_branches", [])
            if entry.get("helper_va") is not None
        }
    )
    flags = sorted(
        {
            entry.get("object_fields", {}).get("flag_0x18")
            for entry in state.get("accepted_entries", [])
            if entry.get("object_fields", {}).get("flag_0x18") is not None
        }
    )
    summary = {
        "label": state.get("label", ""),
        "entry_hits": state.get("entry_hits", 0),
        "branch_31b110_hits": state.get("branch_31b110_hits", 0),
        "branch_31acf0_hits": state.get("branch_31acf0_hits", 0),
        "after_hits": state.get("after_hits", 0),
        "accepted_entry_count": len(state.get("accepted_entries", [])),
        "accepted_branch_count": len(state.get("accepted_branches", [])),
        "accepted_after_count": len(state.get("accepted_after", [])),
        "accepted_branch_vas": branch_vas,
        "accepted_object_flag_0x18_values": flags,
    }
    print("L16_SRC2_406A10_BRANCH_PROBE_BEGIN", state.get("label", ""))
    print("L16_SRC2_406A10_BRANCH_SUMMARY", json.dumps(summary, sort_keys=True))
    printable = dict(state)
    printable["pending"] = {}
    print(json.dumps(printable, sort_keys=True))
    print("L16_SRC2_406A10_BRANCH_PROBE_END", state.get("label", ""))
