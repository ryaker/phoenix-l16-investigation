import builtins
import json
import struct


def reset(label="", report_path=""):
    builtins.l16_monofusion_color_wrapper = {
        "label": label,
        "report_path": report_path,
        "entry": None,
        "tile": None,
        "errors": [],
        "_pending": {},
    }


def _state():
    if not hasattr(builtins, "l16_monofusion_color_wrapper"):
        reset()
    return builtins.l16_monofusion_color_wrapper


def _reg(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    if not address:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    raw = process.ReadMemory(address, size, error)
    if not error.Success() or len(raw) != size:
        _state()["errors"].append(
            {"address": address, "size": size, "error": str(error)}
        )
        return None
    return raw


def _descriptor(process, address):
    raw = _read(process, address, 0x30)
    if raw is None:
        return {"address": address, "read_ok": False}
    words = struct.unpack_from("<8i", raw)
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


def _sample_rgba(process, descriptor, x, y):
    address = descriptor["data"] + 16 * (y * descriptor["stride"] + x)
    raw = _read(process, address, 16)
    return list(struct.unpack("<4f", raw)) if raw is not None else None


def _sample_scalar(process, descriptor, x, y):
    address = descriptor["data"] + 4 * (y * descriptor["stride"] + x)
    raw = _read(process, address, 4)
    return struct.unpack("<f", raw)[0] if raw is not None else None


def install_callbacks(debugger, entry_id, post_worker_id, exit_id):
    target = debugger.GetSelectedTarget()
    callbacks = {
        entry_id: "color_wrapper_probe.wrapper_entry",
        post_worker_id: "color_wrapper_probe.post_worker",
        exit_id: "color_wrapper_probe.wrapper_exit",
    }
    for bp_id, callback in callbacks.items():
        bp = target.FindBreakpointByID(bp_id)
        if bp and bp.IsValid():
            bp.SetScriptCallbackFunction(callback)


def wrapper_entry(frame, bp_loc, internal_dict):
    state = _state()
    if state["entry"] is not None:
        return False
    process = frame.GetThread().GetProcess()
    obj = _reg(frame, "rdi")
    raw = _read(process, obj, 0x160)
    if raw is None:
        return False
    normalization = struct.unpack_from("<Q", raw, 0xF0)[0]
    normalization_raw = _read(process, normalization, 16)
    state["entry"] = {
        "object": obj,
        "destination": _descriptor(process, _reg(frame, "rsi")),
        "operand_rdx": _descriptor(process, _reg(frame, "rdx")),
        "operand_rcx": _descriptor(process, _reg(frame, "rcx")),
        "roi": list(struct.unpack("<4i", _read(process, _reg(frame, "r8"), 16))),
        "normalization_pointer_0xf0": normalization,
        "normalization_payload": (
            {
                "sensor_type": struct.unpack_from("<i", normalization_raw, 0)[0],
                "black_level": struct.unpack_from("<f", normalization_raw, 4)[0],
                "white_level": struct.unpack_from("<f", normalization_raw, 8)[0],
                "cliff_slope": struct.unpack_from("<f", normalization_raw, 12)[0],
            }
            if normalization_raw is not None
            else None
        ),
        "normalization_span_0xf8": struct.unpack_from("<f", raw, 0xF8)[0],
        "response_0x100": list(struct.unpack_from("<4f", raw, 0x100)),
        "response_scale_0x110": struct.unpack_from("<f", raw, 0x110)[0],
        "forward_matrix_0x114": list(struct.unpack_from("<9f", raw, 0x114)),
        "inverse_matrix_0x138": list(struct.unpack_from("<9f", raw, 0x138)),
    }
    return False


def post_worker(frame, bp_loc, internal_dict):
    state = _state()
    if state["tile"] is not None:
        return False
    process = frame.GetThread().GetProcess()
    rgba = _descriptor(process, _reg(frame, "r14"))
    scalar = _descriptor(process, _reg(frame, "rbp") - 0x60)
    width, height = rgba.get("size", [0, 0])
    if width <= 0 or height <= 0:
        state["errors"].append({"site": "post_worker", "reason": "empty tile"})
        return False
    points = [(0, 0), (width // 2, height // 2), (width - 1, height - 1)]
    samples = []
    for x, y in points:
        samples.append(
            {
                "xy": [x, y],
                "pre_rgba": _sample_rgba(process, rgba, x, y),
                "fused_scalar": _sample_scalar(process, scalar, x, y),
            }
        )
    tile = {"rgba": rgba, "scalar": scalar, "samples": samples}
    state["tile"] = tile
    state["_pending"][str(frame.GetThread().GetThreadID())] = tile
    return False


def wrapper_exit(frame, bp_loc, internal_dict):
    state = _state()
    key = str(frame.GetThread().GetThreadID())
    tile = state["_pending"].pop(key, None)
    if tile is None:
        return False
    process = frame.GetThread().GetProcess()
    for sample in tile["samples"]:
        x, y = sample["xy"]
        sample["post_rgba"] = _sample_rgba(process, tile["rgba"], x, y)
    error = process.Kill()
    if error.Fail():
        state["errors"].append({"site": "kill", "error": str(error)})
    return False


def report_to_file(path=None):
    state = _state()
    output = path or state.get("report_path")
    if not output:
        print(json.dumps(state, sort_keys=True))
        return
    if state["entry"] is None or state["tile"] is None:
        print("MONOFUSION_COLOR_WRAPPER_REPORT_REFUSED incomplete capture")
        return
    report = {key: value for key, value in state.items() if not key.startswith("_")}
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("MONOFUSION_COLOR_WRAPPER_REPORT " + output)
