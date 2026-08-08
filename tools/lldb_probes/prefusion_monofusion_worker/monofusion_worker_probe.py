import builtins
import json
import struct


def reset(label="", report_path=""):
    builtins.l16_monofusion_worker = {
        "label": label,
        "report_path": report_path,
        "initializer_subtract_calls": [],
        "initializer_affine_calls": [],
        "initializer_weight_inputs": [],
        "initializer_model_lookups": [],
        "initializer_vst_scaling": [],
        "initializer_source_captures": [],
        "sensor_characterization_constructors": [],
        "worker_entries": [],
        "mode1_calls_0x19f790": [],
        "mode0_calls_0x1a3c00": [],
        "confidence_callback_calls": [],
        "_confidence_pending": {},
        "_confidence_seen": 0,
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_monofusion_worker"):
        reset()
    return builtins.l16_monofusion_worker


def install_callbacks(debugger, ids):
    target = debugger.GetSelectedTarget()
    callbacks = {
        ids["initializer_subtract"]: "monofusion_worker_probe.initializer_subtract",
        ids["initializer_affine"]: "monofusion_worker_probe.initializer_affine",
        ids["initializer_weight"]: "monofusion_worker_probe.initializer_weight",
        ids["initializer_model_lookup"]: "monofusion_worker_probe.initializer_model_lookup",
        ids["initializer_vst"]: "monofusion_worker_probe.initializer_vst",
        ids["initializer_source"]: "monofusion_worker_probe.initializer_source",
        ids["worker_entry"]: "monofusion_worker_probe.worker_entry",
        ids["mode1_call"]: "monofusion_worker_probe.mode1_call",
        ids["mode0_call"]: "monofusion_worker_probe.mode0_call",
    }
    if "sensor_characterization_ctor" in ids:
        callbacks[ids["sensor_characterization_ctor"]] = (
            "monofusion_worker_probe.sensor_characterization_ctor"
        )
    if "confidence_callback_entry" in ids:
        callbacks[ids["confidence_callback_entry"]] = (
            "monofusion_worker_probe.confidence_callback_entry"
        )
    if "confidence_callback_return" in ids:
        callbacks[ids["confidence_callback_return"]] = (
            "monofusion_worker_probe.confidence_callback_return"
        )
    for bp_id, callback in callbacks.items():
        bp = target.FindBreakpointByID(bp_id)
        if bp and bp.IsValid():
            bp.SetScriptCallbackFunction(callback)


def install_confidence_callbacks(debugger, entry_id, return_id):
    target = debugger.GetSelectedTarget()
    callbacks = {
        entry_id: "monofusion_worker_probe.confidence_callback_entry",
        return_id: "monofusion_worker_probe.confidence_callback_return",
    }
    for bp_id, callback in callbacks.items():
        bp = target.FindBreakpointByID(bp_id)
        if bp and bp.IsValid():
            bp.SetScriptCallbackFunction(callback)


def _reg(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    if not address:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    raw = process.ReadMemory(address, size, error)
    return raw if error.Success() and len(raw) == size else None


def _reg_bytes(frame, name, size=16):
    lldb = builtins.__import__("lldb")
    data = frame.FindRegister(name).GetData()
    error = lldb.SBError()
    raw = data.ReadRawData(error, 0, min(size, data.GetByteSize()))
    return raw if error.Success() else b""


def _u64(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<Q", raw)[0] if raw else None


def _f32(process, address):
    raw = _read(process, address, 4)
    return struct.unpack("<f", raw)[0] if raw else None


def _cstring(process, address, limit=512):
    if not address:
        return None
    chunks = []
    for offset in range(limit):
        raw = _read(process, address + offset, 1)
        if not raw or raw == b"\0":
            break
        chunks.append(raw)
    return b"".join(chunks).decode("utf-8", errors="replace")


def _i32x4(process, address):
    raw = _read(process, address, 16)
    return list(struct.unpack("<4i", raw)) if raw else None


def _descriptor(process, address):
    raw = _read(process, address, 0x30)
    if not raw:
        return {"address": address, "read_ok": False}
    words = struct.unpack("<8i", raw[:32])
    return {
        "address": address,
        "read_ok": True,
        "domain": list(words[:4]),
        "size": list(words[4:6]),
        "stride": words[6],
        "channel_stride": words[7],
        "data": struct.unpack_from("<Q", raw, 0x20)[0],
        "owner": struct.unpack_from("<Q", raw, 0x28)[0],
    }


def _vector_records(process, address, stride=0x30, limit=8):
    raw = _read(process, address, 24)
    if not raw:
        return {"address": address, "read_ok": False}
    begin, end, capacity = struct.unpack("<QQQ", raw)
    valid = begin <= end <= capacity and (end - begin) % stride == 0
    count = (end - begin) // stride if valid else None
    records = []
    if valid and count is not None and count <= limit:
        for index in range(count):
            record = begin + index * stride
            records.append(
                {
                    "address": record,
                    "descriptor": _descriptor(process, record),
                    "raw_hex": (_read(process, record, stride) or b"").hex(),
                }
            )
    return {
        "address": address,
        "read_ok": True,
        "begin": begin,
        "end": end,
        "capacity": capacity,
        "valid": valid,
        "stride": stride,
        "count": count,
        "records": records,
    }


def _append(key, value, limit=24):
    state = _state()
    if len(state[key]) < limit:
        state[key].append(value)


def initializer_subtract(frame, bp_loc, internal_dict):
    process = frame.GetThread().GetProcess()
    expression = _reg(frame, "rsi")
    source = _u64(process, expression)
    _append(
        "initializer_subtract_calls",
        {
            "destination": _descriptor(process, _reg(frame, "rdi")),
            "source": _descriptor(process, source),
            "subtract": _f32(process, expression + 8),
        },
    )
    return False


def initializer_affine(frame, bp_loc, internal_dict):
    process = frame.GetThread().GetProcess()
    outer = _reg(frame, "rsi")
    inner = _u64(process, outer)
    source = _u64(process, inner) if inner else None
    _append(
        "initializer_affine_calls",
        {
            "destination": _descriptor(process, _reg(frame, "rdi")),
            "source": _descriptor(process, source),
            "multiply": _f32(process, inner + 8) if inner else None,
            "add": _f32(process, outer + 8),
        },
    )
    return False


def initializer_weight(frame, bp_loc, internal_dict):
    process = frame.GetThread().GetProcess()
    rbp = _reg(frame, "rbp")
    obj = _reg(frame, "r14")
    _append(
        "initializer_weight_inputs",
        {
            "object": obj,
            "same_group_nonmono_count": struct.unpack(
                "<i", _read(process, rbp - 0x688, 4) or b"\0" * 4
            )[0],
            "sensor_response_xmm5": _reg_bytes(frame, "xmm5"),
        },
    )
    sample = _state()["initializer_weight_inputs"][-1]
    xmm5 = sample.pop("sensor_response_xmm5")
    sample["sensor_response"] = struct.unpack_from("<f", xmm5)[0]
    return False


def initializer_vst(frame, bp_loc, internal_dict):
    process = frame.GetThread().GetProcess()
    rbp = _reg(frame, "rbp")
    obj = _reg(frame, "r14")
    xmm0 = _reg_bytes(frame, "xmm0")
    xmm1 = _reg_bytes(frame, "xmm1")
    _append(
        "initializer_vst_scaling",
        {
            "object": obj,
            "selected_panchromatic_a": _f32(process, rbp - 0x70),
            "selected_panchromatic_b": _f32(process, rbp - 0x6C),
            "sensor_response": _f32(process, rbp - 0x688),
            "same_group_nonmono_count": _f32(process, rbp - 0x690),
            "scaled_a_xmm0": struct.unpack_from("<f", xmm0)[0],
            "scaled_b_xmm1": struct.unpack_from("<f", xmm1)[0],
        },
    )
    return False


def initializer_model_lookup(frame, bp_loc, internal_dict):
    xmm0 = _reg_bytes(frame, "xmm0")
    _append(
        "initializer_model_lookups",
        {
            "sensor_characterization": _reg(frame, "rbx"),
            "lookup_gain": struct.unpack_from("<f", xmm0)[0],
        },
    )
    return False


def initializer_source(frame, bp_loc, internal_dict):
    process = frame.GetThread().GetProcess()
    rbp = _reg(frame, "rbp")
    captured = _u64(process, rbp - 0x4E8)
    sensor = captured + 0xA8 if captured else 0
    _append(
        "initializer_source_captures",
        {
            "camera_key": struct.unpack(
                "<i", _read(process, rbp - 0x4D4, 4) or b"\0" * 4
            )[0],
            "captured_image": captured,
            "sensor_exposure": _u64(process, captured + 0x38) if captured else None,
            "sensor_analog_gain": _f32(process, captured + 0x40) if captured else None,
            "sensor_digital_gain": _f32(process, captured + 0x44) if captured else None,
            "sensor_type": struct.unpack(
                "<i", _read(process, sensor, 4) or b"\0" * 4
            )[0],
            "black_level": _f32(process, sensor + 4),
            "white_level": _f32(process, sensor + 8),
        },
    )
    return False


def sensor_characterization_ctor(frame, bp_loc, internal_dict):
    process = frame.GetThread().GetProcess()
    sensor_type_ptr = _reg(frame, "rsi")
    source = _reg(frame, "rdx")
    header = _read(process, source, 16)
    rows = []
    if header:
        begin, end = struct.unpack("<QQ", header)
        if begin <= end and (end - begin) % 0x20 == 0:
            for index in range(min((end - begin) // 0x20, 64)):
                raw = _read(process, begin + index * 0x20, 0x20)
                if not raw:
                    break
                rows.append(
                    {
                        "gain": struct.unpack_from("<I", raw, 0)[0],
                        "scale": struct.unpack_from("<f", raw, 4)[0],
                        "threshold": struct.unpack_from("<f", raw, 8)[0],
                        "cliff_slope": struct.unpack_from("<f", raw, 0x0C)[0],
                        "black_level": struct.unpack_from("<f", raw, 0x10)[0],
                        "white_level": struct.unpack_from("<f", raw, 0x14)[0],
                        "panchromatic_a": struct.unpack_from("<f", raw, 0x18)[0],
                        "panchromatic_b": struct.unpack_from("<f", raw, 0x1C)[0],
                        "raw_hex": raw.hex(),
                    }
                )
    callers = []
    thread = frame.GetThread()
    for index in range(1, min(thread.GetNumFrames(), 7)):
        cursor = thread.GetFrameAtIndex(index)
        if not cursor.IsValid():
            break
        callers.append(
            {
                "pc": cursor.GetPC(),
                "function": cursor.GetFunctionName(),
            }
        )
    _append(
        "sensor_characterization_constructors",
        {
            "destination": _reg(frame, "rdi"),
            "sensor_type": (
                struct.unpack("<i", _read(process, sensor_type_ptr, 4) or b"\0" * 4)[0]
            ),
            "source": source,
            "rows": rows,
            "callers": callers,
        },
        limit=8,
    )
    return False


def worker_entry(frame, bp_loc, internal_dict):
    process = frame.GetThread().GetProcess()
    obj = _reg(frame, "rdi")
    raw = _read(process, obj, 0x241)
    _append(
        "worker_entries",
        {
            "object": obj,
            "mode_0x00": raw[0] if raw else None,
            "source_records_0x08": _vector_records(process, obj + 0x08),
            "generated_image_0x20": _descriptor(process, obj + 0x20),
            "roi_0x20": list(struct.unpack_from("<4i", raw, 0x20)) if raw else None,
            "kernel_fields_0x38_0x50": (
                {
                    "stride_0x38": struct.unpack_from("<i", raw, 0x38)[0],
                    "data_0x40": struct.unpack_from("<Q", raw, 0x40)[0],
                    "owner_0x48": struct.unpack_from("<Q", raw, 0x48)[0],
                    "float_0x50": struct.unpack_from("<f", raw, 0x50)[0],
                    "float_0x54": struct.unpack_from("<f", raw, 0x54)[0],
                    "vst_a_0x58": struct.unpack_from("<f", raw, 0x58)[0],
                    "vst_b_0x5c": struct.unpack_from("<f", raw, 0x5C)[0],
                    "black_level_0x60": struct.unpack_from("<f", raw, 0x60)[0],
                    "white_level_0x64": struct.unpack_from("<f", raw, 0x64)[0],
                }
                if raw
                else None
            ),
            "flow_records_0xd8": _vector_records(process, obj + 0xD8),
            "normalization_0xf0": _u64(process, obj + 0xF0),
            "normalization_0xf8": _f32(process, obj + 0xF8),
            "normalization_0x100": (
                list(struct.unpack_from("<4f", raw, 0x100)) if raw else None
            ),
            "normalization_0x110": _f32(process, obj + 0x110),
            "flow_threshold_0x200": _f32(process, obj + 0x200),
            "source_scale_0x204": (
                list(struct.unpack_from("<3f", raw, 0x204)) if raw else None
            ),
            "output": _descriptor(process, _reg(frame, "rsi")),
            "reference": _descriptor(process, _reg(frame, "rdx")),
            "operand_rcx": _descriptor(process, _reg(frame, "rcx")),
            "roi_r9": _i32x4(process, _reg(frame, "r9")),
        },
    )
    return False


def _branch_call(frame, name):
    process = frame.GetThread().GetProcess()
    rsp = _reg(frame, "rsp")
    source_vector = _reg(frame, "r8")
    flow_vector = _reg(frame, "r9")
    return {
        "branch": name,
        "output": _descriptor(process, _reg(frame, "rdi")),
        "operand_rsi": _descriptor(process, _reg(frame, "rsi")),
        "scalar_map_rdx": _descriptor(process, _reg(frame, "rdx")),
        "destination_view_rcx": _descriptor(process, _reg(frame, "rcx")),
        "source_records_r8": _vector_records(process, source_vector),
        "flow_records_r9": _vector_records(process, flow_vector),
        "roi_stack0": _i32x4(process, _u64(process, rsp)),
        "scale_stack8": _f32(process, _u64(process, rsp + 8)),
    }


def mode1_call(frame, bp_loc, internal_dict):
    _append("mode1_calls_0x19f790", _branch_call(frame, "0x19f790"))
    return False


def mode0_call(frame, bp_loc, internal_dict):
    _append("mode0_calls_0x1a3c00", _branch_call(frame, "0x1a3c00"))
    return False


def confidence_callback_entry(frame, bp_loc, internal_dict):
    state = _state()
    state["_confidence_seen"] += 1
    if state["_confidence_seen"] > 24:
        return False

    process = frame.GetThread().GetProcess()
    target = frame.GetThread().GetProcess().GetTarget()
    thread_id = frame.GetThread().GetThreadID()
    obj = _reg(frame, "rdi")
    vtable = _u64(process, obj)
    typeinfo = _u64(process, vtable - 8) if vtable else None
    type_name_ptr = _u64(process, typeinfo + 8) if typeinfo else None
    image_base = frame.GetPC() - 0x1A4A09
    callback = _reg(frame, "rax")
    parameters = _read(process, obj + 8, 16)
    state["_confidence_pending"][str(thread_id)] = {
        "object": obj,
        "vtable": vtable,
        "typeinfo": typeinfo,
        "type_name": _cstring(process, type_name_ptr),
        "callback_address": callback,
        "callback_va": callback - image_base,
        "parameters": list(struct.unpack("<4f", parameters)) if parameters else None,
        "sum_one_minus_confidence": _f32(process, _reg(frame, "rsi")),
        "sum_confidence_squared": _f32(process, _reg(frame, "rdx")),
    }
    return False


def confidence_callback_return(frame, bp_loc, internal_dict):
    state = _state()
    thread_id = str(frame.GetThread().GetThreadID())
    sample = state["_confidence_pending"].pop(thread_id, None)
    if sample is not None:
        raw = _reg_bytes(frame, "xmm0")
        sample["result"] = struct.unpack_from("<f", raw)[0]
        _append("confidence_callback_calls", sample)
    return len(state["confidence_callback_calls"]) >= 24


def report_to_file(path=None):
    state = _state()
    output = path or state.get("report_path")
    if not output:
        print(json.dumps(state, sort_keys=True))
        return
    if not state["worker_entries"] and not state["confidence_callback_calls"]:
        print("MONOFUSION_WORKER_REPORT_REFUSED no worker or confidence entries")
        return
    report = {key: value for key, value in state.items() if not key.startswith("_")}
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("MONOFUSION_WORKER_REPORT " + output)
