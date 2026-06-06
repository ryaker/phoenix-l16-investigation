import builtins
import json
import struct


SITES = {
    0x299D06: "dispatch_call_299c70_to_5440",
    0x29A670: "worker_29a670_entry",
    0x29A7E6: "worker_29a670_exit",
    0x299D0B: "after_dispatch_299c70",
}


def reset(label="", sample_pixels=8, expected_dispatches=6):
    builtins.l16_worker_formula_probe = {
        "label": label,
        "sample_pixels": sample_pixels,
        "expected_dispatches": expected_dispatches,
        "counts": {name: 0 for name in SITES.values()},
        "breakpoint_ids": {},
        "dispatches": [],
        "worker_samples": [],
        "active_dispatch_by_callback": {},
        "active_dispatch_by_thread": {},
        "active_worker_sample_by_thread": {},
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_worker_formula_probe"):
        reset()
    return builtins.l16_worker_formula_probe


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


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


def _i32(data, off=0):
    return struct.unpack_from("<i", data, off)[0]


def _u64(data, off=0):
    return struct.unpack_from("<Q", data, off)[0]


def _read_u16(process, addr):
    data = _read(process, addr, 2)
    return _u16(data) if data is not None else None


def _read_u32(process, addr):
    data = _read(process, addr, 4)
    return _u32(data) if data is not None else None


def _read_qword(process, addr):
    data = _read(process, addr, 8)
    return _u64(data) if data is not None else None


def _qwords(process, addr, count):
    data = _read(process, addr, count * 8)
    if data is None:
        return None
    return [_u64(data, off) for off in range(0, count * 8, 8)]


def _u16s(process, addr, count):
    data = _read(process, addr, count * 2)
    if data is None:
        return None
    return [_u16(data, off) for off in range(0, count * 2, 2)]


def _u32s(process, addr, count):
    data = _read(process, addr, count * 4)
    if data is None:
        return None
    return [_u32(data, off) for off in range(0, count * 4, 4)]


def _i32s(process, addr, count):
    data = _read(process, addr, count * 4)
    if data is None:
        return None
    return [_i32(data, off) for off in range(0, count * 4, 4)]


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


def _ptr_module_va(target, ptr):
    base = _libcp_base(target)
    if base is not None and ptr and ptr >= base:
        return ptr - base
    return None


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


def _descriptor_header(process, addr):
    data = _read(process, addr, 0x30)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "width_0x10": _u32(data, 0x10),
        "height_0x14": _u32(data, 0x14),
        "stride_0x18": _u32(data, 0x18),
        "data_ptr_0x20": _u64(data, 0x20),
        "qwords": [_u64(data, off) for off in range(0, 0x30, 8)],
        "u32": [_u32(data, off) for off in range(0, 0x30, 4)],
    }


def _callback_object(process, target, addr):
    qwords = _qwords(process, addr, 5)
    if qwords is None:
        return {"addr": addr, "read_ok": False}
    slot_0x30 = _read_qword(process, qwords[0] + 0x30) if qwords[0] else None
    return {
        "addr": addr,
        "read_ok": True,
        "address_point_0x00": qwords[0],
        "address_point_0x00_va": _ptr_module_va(target, qwords[0]),
        "dest_descriptor_ptr_0x08": qwords[1],
        "source_object_ptr_0x10": qwords[2],
        "qword_0x18": qwords[3],
        "function_object_ptr_0x20": qwords[4],
        "slot_0x30_target": slot_0x30,
        "slot_0x30_target_va": _ptr_module_va(target, slot_0x30),
        "qwords": qwords,
    }


def _source_object(process, addr):
    data = _read(process, addr, 0x48)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "record_base_0x10": _u64(data, 0x10),
        "dim_width_0x30": _u32(data, 0x30),
        "dim_height_0x34": _u32(data, 0x34),
        "source_stride_0x38": _u32(data, 0x38),
        "offset_table_0x40": _u64(data, 0x40),
        "qwords": [_u64(data, off) for off in range(0, 0x48, 8)],
        "u32": [_u32(data, off) for off in range(0, 0x48, 4)],
    }


def _tile_rect(process, addr):
    vals = _i32s(process, addr, 4)
    if vals is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "x0": vals[0],
        "y0": vals[1],
        "x1": vals[2],
        "y1": vals[3],
        "raw_i32": vals,
    }


def _formula_samples(process, callback, tile, sample_pixels):
    dest = _descriptor_header(process, callback.get("dest_descriptor_ptr_0x08"))
    source = _source_object(process, callback.get("source_object_ptr_0x10"))
    packet = {"dest_descriptor": dest, "source_object": source, "pixels": []}
    if not dest.get("read_ok") or not source.get("read_ok") or not tile.get("read_ok"):
        packet["read_ok"] = False
        return packet

    record_base = source.get("record_base_0x10")
    offset_table = source.get("offset_table_0x40")
    source_stride = source.get("source_stride_0x38")
    dest_data = dest.get("data_ptr_0x20")
    dest_stride = dest.get("stride_0x18")
    x0, x1, y = tile["x0"], tile["x1"], tile["y0"]
    max_count = 4096

    for x in range(max(0, x0), max(0, min(x1, x0 + sample_pixels))):
        item = {"x": x, "y": y}
        item["source_linear_index"] = x + y * source_stride
        offset = _read_u32(process, offset_table + item["source_linear_index"] * 4)
        item["source_record_offset"] = offset
        if offset is None:
            item["read_ok"] = False
            packet["pixels"].append(item)
            continue

        rec = record_base + offset
        item["source_record_ptr"] = rec
        item["base_0x00"] = _read_u16(process, rec)
        item["count_0x02"] = _read_u16(process, rec + 2)
        item["step_0x04"] = _read_u16(process, rec + 4)
        count = item["count_0x02"]
        if item["base_0x00"] is None or count is None or item["step_0x04"] is None:
            item["read_ok"] = False
            packet["pixels"].append(item)
            continue
        if count > max_count:
            item["read_ok"] = False
            item["count_too_large"] = True
            packet["pixels"].append(item)
            continue

        values = _u16s(process, rec + 8, count) if count else []
        if values is None:
            item["read_ok"] = False
            packet["pixels"].append(item)
            continue

        selected = min(range(count), key=lambda idx: values[idx]) if count else 0
        expected = (item["base_0x00"] + item["step_0x04"] * selected) & 0xFFFF
        dest_addr = dest_data + y * dest_stride * 2 + x * 2
        item.update(
            {
                "read_ok": True,
                "values_first_16": values[:16],
                "selected_index": selected,
                "selected_value": values[selected] if count else None,
                "expected_u16": expected,
                "dest_addr": dest_addr,
                "dest_pre_u16": _read_u16(process, dest_addr),
            }
        )
        packet["pixels"].append(item)

    packet["read_ok"] = bool(packet["pixels"]) and all(
        item.get("read_ok") for item in packet["pixels"]
    )
    return packet


def _fill_post_values(process, sample):
    for item in sample.get("formula", {}).get("pixels", []):
        addr = item.get("dest_addr")
        actual = _read_u16(process, addr) if addr else None
        item["dest_post_u16"] = actual
        item["post_equals_expected"] = (
            actual == item.get("expected_u16") if actual is not None else None
        )
    values = [
        item.get("post_equals_expected")
        for item in sample.get("formula", {}).get("pixels", [])
        if item.get("post_equals_expected") is not None
    ]
    sample["all_post_values_match_expected"] = bool(values) and all(values)


def _set_bp_enabled(debugger_or_target, name, enabled):
    bp_id = _state().get("breakpoint_ids", {}).get(name)
    if not bp_id:
        return
    if hasattr(debugger_or_target, "FindBreakpointByID"):
        target = debugger_or_target
    else:
        target = debugger_or_target.GetSelectedTarget()
    bp = target.FindBreakpointByID(bp_id)
    if bp and bp.IsValid():
        bp.SetEnabled(enabled)


def _dispatch_for_callback(callback):
    state = _state()
    dispatch_id = state["active_dispatch_by_callback"].get(str(callback.get("addr")))
    if dispatch_id is None:
        return None
    if dispatch_id >= len(state["dispatches"]):
        return None
    return state["dispatches"][dispatch_id]


def hit(frame, bp_loc, internal_dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    thread_id = thread.GetThreadID()
    site_va = _module_va(target, frame.GetPC())
    name = SITES.get(site_va)
    if name is None:
        state["errors"].append(f"unknown site {site_va}")
        return False

    state["counts"][name] = state["counts"].get(name, 0) + 1
    regs = _registers(frame)

    if site_va == 0x299D06:
        callback = _callback_object(process, target, regs["rdx"])
        dispatch_id = len(state["dispatches"])
        dispatch = {
            "dispatch_id": dispatch_id,
            "thread_id": thread_id,
            "registers": regs,
            "callback": callback,
            "dispatch_config_rdi": _qwords(process, regs["rdi"], 3),
            "dispatch_tile_rsi": _u32s(process, regs["rsi"], 4),
            "stack": _stack(thread),
        }
        state["dispatches"].append(dispatch)
        state["active_dispatch_by_callback"][str(regs["rdx"])] = dispatch_id
        state["active_dispatch_by_thread"][str(thread_id)] = dispatch_id
        _set_bp_enabled(target, "worker_29a670_entry", True)
        _set_bp_enabled(target, "worker_29a670_exit", True)

    elif site_va == 0x29A670:
        callback = _callback_object(process, target, regs["rdi"])
        dispatch = _dispatch_for_callback(callback)
        if dispatch is None:
            state["errors"].append(
                f"worker entry with unmapped callback {hex(regs['rdi'])}"
            )
            return False
        if dispatch.get("worker_sample_id") is not None:
            return False
        sample_id = len(state["worker_samples"])
        tile = _tile_rect(process, regs["rsi"])
        sample = {
            "sample_id": sample_id,
            "dispatch_id": dispatch["dispatch_id"],
            "thread_id": thread_id,
            "registers": regs,
            "callback": callback,
            "tile": tile,
            "formula": _formula_samples(
                process, callback, tile, state.get("sample_pixels", 8)
            ),
            "stack": _stack(thread),
        }
        state["worker_samples"].append(sample)
        dispatch["worker_sample_id"] = sample_id
        state["active_worker_sample_by_thread"][str(thread_id)] = sample_id
        _set_bp_enabled(target, "worker_29a670_entry", False)

    elif site_va == 0x29A7E6:
        sample_id = state["active_worker_sample_by_thread"].pop(str(thread_id), None)
        if sample_id is not None and sample_id < len(state["worker_samples"]):
            _fill_post_values(process, state["worker_samples"][sample_id])
            _set_bp_enabled(target, "worker_29a670_exit", False)

    elif site_va == 0x299D0B:
        dispatch_id = state["active_dispatch_by_thread"].get(str(thread_id))
        if dispatch_id is not None and dispatch_id < len(state["dispatches"]):
            dispatch = state["dispatches"][dispatch_id]
            dispatch["after_dispatch_dest_descriptor"] = _descriptor_header(
                process, dispatch["callback"].get("dest_descriptor_ptr_0x08")
            )
            if dispatch.get("worker_sample_id") is None:
                state["errors"].append(
                    f"dispatch {dispatch_id} returned without 0x29a670 sample"
                )

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
        bp.SetScriptCallbackFunction("worker_formula_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    _set_bp_enabled(debugger, "worker_29a670_entry", False)
    _set_bp_enabled(debugger, "worker_29a670_exit", False)
    print("L16_WORKER_FORMULA_ATTACHED", ids)


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


def drive_until_exit_or_step_cap(debugger, max_steps=2000):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while (
        process.IsValid()
        and process.GetState() == lldb.eStateStopped
        and steps < max_steps
    ):
        steps += 1
        process.Continue()
    _state()["drive_steps"] = steps
    _state()["drive_hit_step_cap"] = (
        process.IsValid() and process.GetState() == lldb.eStateStopped and steps >= max_steps
    )
    print("L16_WORKER_FORMULA_DRIVE_STEPS", steps)


def _summary():
    dispatches = _state().get("dispatches", [])
    samples = _state().get("worker_samples", [])
    return {
        "dispatch_count": len(dispatches),
        "worker_sample_count": len(samples),
        "dispatches_with_worker_samples": sum(
            1 for dispatch in dispatches if dispatch.get("worker_sample_id") is not None
        ),
        "slot_0x30_target_vas": sorted(
            {
                dispatch.get("callback", {}).get("slot_0x30_target_va")
                for dispatch in dispatches
                if dispatch.get("callback", {}).get("slot_0x30_target_va") is not None
            }
        ),
        "callback_address_point_vas": sorted(
            {
                dispatch.get("callback", {}).get("address_point_0x00_va")
                for dispatch in dispatches
                if dispatch.get("callback", {}).get("address_point_0x00_va") is not None
            }
        ),
        "all_dispatches_have_worker_samples": bool(dispatches)
        and all(dispatch.get("worker_sample_id") is not None for dispatch in dispatches),
        "all_worker_samples_match_formula": bool(samples)
        and all(sample.get("all_post_values_match_expected") is True for sample in samples),
        "sample_pixel_counts": [
            len(sample.get("formula", {}).get("pixels", [])) for sample in samples
        ],
        "errors": list(_state().get("errors", [])),
    }


def payload(debugger):
    packet = dict(_state())
    packet["process"] = _process_packet(debugger)
    packet["breakpoint_hit_counts"] = _breakpoint_hit_counts(debugger)
    packet["summary"] = _summary()
    packet.pop("active_dispatch_by_callback", None)
    packet.pop("active_dispatch_by_thread", None)
    packet.pop("active_worker_sample_by_thread", None)
    return packet


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_WORKER_FORMULA_WROTE", path)


def report(debugger):
    print("L16_WORKER_FORMULA_BEGIN")
    print(json.dumps(payload(debugger), indent=2, sort_keys=True))
    print("L16_WORKER_FORMULA_END")
