import builtins
import json
import struct


def reset(label="", report_path=""):
    builtins.l16_monofusion_identity = {
        "label": label,
        "report_path": report_path,
        "field20_stores": [],
        "initialize_entries": [],
        "initialize_commits": [],
        "process_entries": [],
        "process_returns": [],
        "wide_adapter_calls": [],
        "tele_adapter_calls": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_monofusion_identity"):
        reset()
    return builtins.l16_monofusion_identity


def install_callbacks(debugger, ids):
    target = debugger.GetSelectedTarget()
    callbacks = {
        ids["field20_store"]: "monofusion_runtime_probe.field20_store",
        ids["initialize_entry"]: "monofusion_runtime_probe.initialize_entry",
        ids["initialize_commit"]: "monofusion_runtime_probe.initialize_commit",
        ids["process_entry"]: "monofusion_runtime_probe.process_entry",
        ids["process_return"]: "monofusion_runtime_probe.process_return",
        ids["wide_adapter"]: "monofusion_runtime_probe.wide_adapter",
        ids["tele_adapter"]: "monofusion_runtime_probe.tele_adapter",
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


def _u64(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<Q", raw)[0] if raw else None


def _i32(process, address):
    raw = _read(process, address, 4)
    return struct.unpack("<i", raw)[0] if raw else None


def _u8(process, address):
    raw = _read(process, address, 1)
    return raw[0] if raw else None


def _vector_i32(process, address, limit=32):
    header = _read(process, address, 24)
    if not header:
        return {"read_ok": False}
    begin, end, capacity = struct.unpack("<QQQ", header)
    valid = begin <= end <= capacity and (end - begin) % 4 == 0
    count = (end - begin) // 4 if valid else None
    values = []
    if valid and count and count <= limit:
        raw = _read(process, begin, count * 4)
        if raw:
            values = list(struct.unpack(f"<{count}i", raw))
    return {
        "read_ok": True,
        "begin": begin,
        "end": end,
        "capacity": capacity,
        "valid": valid,
        "count": count,
        "values": values,
    }


def _vector_stride(process, address, stride, limit=16):
    header = _read(process, address, 24)
    if not header:
        return {"read_ok": False}
    begin, end, capacity = struct.unpack("<QQQ", header)
    valid = begin <= end <= capacity and (end - begin) % stride == 0
    count = (end - begin) // stride if valid else None
    records = []
    if valid and count and count <= limit:
        raw = _read(process, begin, count * stride)
        if raw:
            records = [raw[index * stride : (index + 1) * stride].hex() for index in range(count)]
    return {
        "read_ok": True,
        "begin": begin,
        "end": end,
        "capacity": capacity,
        "valid": valid,
        "stride": stride,
        "count": count,
        "records_hex": records,
    }


def _descriptor(process, address):
    raw = _read(process, address, 0x30)
    if not raw:
        return {"address": address, "read_ok": False}
    i = struct.unpack("<8i", raw[:32])
    return {
        "address": address,
        "read_ok": True,
        "domain": list(i[:4]),
        "size": list(i[4:6]),
        "stride": i[6],
        "channel_stride": i[7],
        "data": struct.unpack_from("<Q", raw, 0x20)[0],
        "owner": struct.unpack_from("<Q", raw, 0x28)[0],
        "raw_hex": raw.hex(),
    }


def _mono(process, obj):
    if not obj:
        return {"object": obj, "read_ok": False}
    raw = _read(process, obj, 0x241)
    if not raw:
        return {"object": obj, "read_ok": False}
    return {
        "object": obj,
        "read_ok": True,
        "initialized_0x240": raw[0x240],
        "raw_image_factory_0xa8": struct.unpack_from("<Q", raw, 0xA8)[0],
        "target_camera_id_0xb8": struct.unpack_from("<i", raw, 0xB8)[0],
        "negative_override_ids_0xc0": _vector_i32(process, obj + 0xC0),
        "record_vector_0x08": _vector_stride(process, obj + 0x08, 0x30),
        "record_vector_0xd8": _vector_stride(process, obj + 0xD8, 0x30),
        "scale_0x50": struct.unpack_from("<f", raw, 0x50)[0],
        "scale_0x54": struct.unpack_from("<f", raw, 0x54)[0],
        "matrix_0x114": list(struct.unpack_from("<18f", raw, 0x114)),
        "output_image_0x20": _descriptor(process, obj + 0x20),
    }


def _append(key, value, limit=16):
    state = _state()
    if len(state[key]) < limit:
        state[key].append(value)


def field20_store(frame, bp_loc, internal_dict):
    process = frame.GetThread().GetProcess()
    fusion = _reg(frame, "r13")
    mono = _reg(frame, "r12")
    _append(
        "field20_stores",
        {
            "fusion_cache_bayer": fusion,
            "mono_fusion": mono,
            "flag_0x18": _u8(process, fusion + 0x18),
            "old_field_0x20": _u64(process, fusion + 0x20),
            "mono_before_store": _mono(process, mono),
        },
    )
    return False


def initialize_entry(frame, bp_loc, internal_dict):
    process = frame.GetThread().GetProcess()
    obj = _reg(frame, "rdi")
    _append("initialize_entries", _mono(process, obj))
    return False


def initialize_commit(frame, bp_loc, internal_dict):
    process = frame.GetThread().GetProcess()
    obj = _reg(frame, "r14")
    _append("initialize_commits", _mono(process, obj))
    return False


def process_entry(frame, bp_loc, internal_dict):
    process = frame.GetThread().GetProcess()
    obj = _reg(frame, "rdi")
    sample = {
        "mono": _mono(process, obj),
        "output_rsi_before": _descriptor(process, _reg(frame, "rsi")),
        "operand_rdx": _descriptor(process, _reg(frame, "rdx")),
        "operand_rcx": _descriptor(process, _reg(frame, "rcx")),
        "roi_r8": list(struct.unpack("<4i", _read(process, _reg(frame, "r8"), 16) or b"\0" * 16)),
    }
    _append("process_entries", sample)
    return False


def process_return(frame, bp_loc, internal_dict):
    process = frame.GetThread().GetProcess()
    rbp = _reg(frame, "rbp")
    fusion = _reg(frame, "r15")
    mono = _u64(process, fusion + 0x20) if fusion else None
    _append(
        "process_returns",
        {
            "fusion_cache_bayer": fusion,
            "mono": _mono(process, mono),
            "output_rbp_minus_0x190": _descriptor(process, rbp - 0x190),
            "operand_rbp_minus_0x160": _descriptor(process, rbp - 0x160),
            "operand_rbp_minus_0xc0": _descriptor(process, rbp - 0xC0),
        },
    )
    return False


def wide_adapter(frame, bp_loc, internal_dict):
    process = frame.GetThread().GetProcess()
    rbp = _reg(frame, "rbp")
    _append(
        "wide_adapter_calls",
        {
            "destination": _reg(frame, "rdi"),
            "output_descriptor": _reg(frame, "rsi"),
            "mono_descriptor": _reg(frame, "rdx"),
            "mono_is_rbp_minus_0x190": _reg(frame, "rdx") == rbp - 0x190,
            "mono": _descriptor(process, _reg(frame, "rdx")),
            "anchor": _descriptor(process, _reg(frame, "r9")),
        },
    )
    return False


def tele_adapter(frame, bp_loc, internal_dict):
    process = frame.GetThread().GetProcess()
    _append(
        "tele_adapter_calls",
        {
            "destination": _reg(frame, "rdi"),
            "output_descriptor": _reg(frame, "rsi"),
            "source": _descriptor(process, _reg(frame, "rdx")),
            "anchor": _descriptor(process, _reg(frame, "r9")),
        },
    )
    return False


def report_to_file(path=None):
    state = _state()
    output = path or state["report_path"]
    with open(output, "w") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({
        "label": state["label"],
        "field20_stores": len(state["field20_stores"]),
        "initialize_commits": len(state["initialize_commits"]),
        "process_entries": len(state["process_entries"]),
        "wide_adapter_calls": len(state["wide_adapter_calls"]),
        "tele_adapter_calls": len(state["tele_adapter_calls"]),
        "report": output,
    }, sort_keys=True))
