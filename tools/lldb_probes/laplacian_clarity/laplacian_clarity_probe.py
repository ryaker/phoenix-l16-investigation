import builtins
import json
import struct


ENTRY = 0x2E4CF0
CALLBACK = 0x2E7360


def reset(label=""):
    builtins.l16_laplacian_clarity = {
        "label": label,
        "counts": {"entry": 0, "callback": 0, "property": 0},
        "entries": [],
        "callbacks": [],
        "properties": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_laplacian_clarity"):
        reset()
    return builtins.l16_laplacian_clarity


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _xmm_f32(frame, name):
    register = frame.FindRegister(name)
    data = register.GetData()
    error = builtins.__import__("lldb").SBError()
    raw = data.ReadRawData(error, 0, data.GetByteSize())
    if not error.Success() or len(raw) < 16:
        return None
    return list(struct.unpack("<4f", raw[:16]))


def _descriptor(data, offset=0):
    if data is None or len(data) < offset + 0x30:
        return None
    return {
        "width": struct.unpack_from("<i", data, offset + 0x10)[0],
        "height": struct.unpack_from("<i", data, offset + 0x14)[0],
        "stride": struct.unpack_from("<i", data, offset + 0x18)[0],
        "data": struct.unpack_from("<Q", data, offset + 0x20)[0],
    }


def _libcpp_string(process, address):
    header = _read(process, address, 24)
    if header is None:
        return None
    short_size = header[0] >> 1
    if header[0] & 1:
        size = struct.unpack_from("<Q", header, 8)[0]
        data_ptr = struct.unpack_from("<Q", header, 16)[0]
        raw = _read(process, data_ptr, size)
    else:
        raw = header[1 : 1 + short_size]
    if raw is None:
        return None
    return raw.decode("utf-8", errors="replace")


def property_lookup(frame, bp_loc, _dict):
    state = _state()
    state["counts"]["property"] += 1
    process = frame.GetThread().GetProcess()
    address = frame.GetPCAddress().GetLoadAddress(
        process.GetTarget()
    ) - process.GetTarget().FindModule(
        builtins.__import__("lldb").SBFileSpec("libcp.dylib")
    ).GetObjectFileHeaderAddress().GetLoadAddress(process.GetTarget())
    value = _libcpp_string(process, _u(frame, "rsi"))
    if value is None:
        state["errors"].append(f"property string read failed at {address:#x}")
    elif not any(item["address"] == address for item in state["properties"]):
        state["properties"].append({"address": address, "name": value})
    return False


def entry(frame, bp_loc, _dict):
    state = _state()
    state["counts"]["entry"] += 1
    if len(state["entries"]) >= 8:
        return False
    process = frame.GetThread().GetProcess()
    config_ptr = _u(frame, "rdx")
    config = _read(process, config_ptr, 0x38)
    source_ptr = _u(frame, "rsi")
    source = _read(process, source_ptr, 0x30)
    if config is None:
        state["errors"].append("entry config read failed")
        return False
    begin, end, capacity = struct.unpack_from("<QQQ", config, 0x20)
    curve = None
    if begin and end >= begin and end - begin <= 4096 and (end - begin) % 4 == 0:
        raw_curve = _read(process, begin, end - begin)
        if raw_curve is not None:
            curve = list(struct.unpack("<" + "f" * ((end - begin) // 4), raw_curve))
    state["entries"].append(
        {
            "config_ptr": config_ptr,
            "config_f32_0x00_0x20": list(struct.unpack_from("<8f", config, 0)),
            "curve_begin": begin,
            "curve_end": end,
            "curve_capacity": capacity,
            "curve": curve,
            "xmm0": _xmm_f32(frame, "xmm0"),
            "source_descriptor": _descriptor(source),
        }
    )
    return False


def callback(frame, bp_loc, _dict):
    state = _state()
    state["counts"]["callback"] += 1
    if len(state["callbacks"]) >= 16:
        return False
    process = frame.GetThread().GetProcess()
    closure_ptr = _u(frame, "rdi")
    closure = _read(process, closure_ptr, 0x48)
    if closure is None:
        state["errors"].append("callback closure read failed")
        return False
    pointers = struct.unpack_from("<8Q", closure, 0x08)
    level_data = _read(process, pointers[0], 4)
    offset_data = _read(process, pointers[2], 4)
    scale_data = _read(process, pointers[3], 4)
    bins_data = _read(process, pointers[4], 4)
    state["callbacks"].append(
        {
            "closure": closure_ptr,
            "level": struct.unpack("<i", level_data)[0] if level_data else None,
            "curve_offset": struct.unpack("<f", offset_data)[0] if offset_data else None,
            "curve_scale": struct.unpack("<f", scale_data)[0] if scale_data else None,
            "curve_bins": struct.unpack("<i", bins_data)[0] if bins_data else None,
            "config_ptr": pointers[5],
            "destination_descriptor": _descriptor(
                _read(process, pointers[6], 0x30)
            ),
        }
    )
    return False


def install(debugger, ids):
    target = debugger.GetSelectedTarget()
    for key, callback_name in (
        ("entry", "laplacian_clarity_probe.entry"),
        ("callback", "laplacian_clarity_probe.callback"),
    ):
        bp = target.FindBreakpointByID(ids[key])
        bp.SetScriptCallbackFunction(callback_name)
    for bp_id in ids.get("properties", []):
        bp = target.FindBreakpointByID(bp_id)
        bp.SetScriptCallbackFunction("laplacian_clarity_probe.property_lookup")


def report_to_file(debugger, path):
    process = debugger.GetSelectedTarget().GetProcess()
    state = _state()
    state["process"] = {
        "valid": process.IsValid(),
        "state": process.GetState(),
        "exit_status": process.GetExitStatus(),
    }
    with open(path, "w") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
    print("WROTE", path, state["counts"])
