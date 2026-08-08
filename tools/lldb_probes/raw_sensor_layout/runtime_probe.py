import builtins
import json
import struct


def reset(label, expected_planes, report_path):
    builtins.l16_raw_sensor_layout = {
        "label": label,
        "expected_planes": expected_planes,
        "report_path": report_path,
        "packed_handler_calls": 0,
        "jpeg_handler_calls": 0,
        "unpack_calls": 0,
        "packed_events": [],
        "unpack_events": [],
        "errors": [],
        "kill_requested": False,
    }


def _state():
    return builtins.l16_raw_sensor_layout


def _reg(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    raw = process.ReadMemory(address, size, error)
    if not error.Success() or len(raw) != size:
        return None
    return raw


def packed_handler(frame, bp_loc, internal_dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    state["packed_handler_calls"] += 1
    if len(state["packed_events"]) < 16:
        size_raw = _read(process, _reg(frame, "rcx"), 8)
        state["packed_events"].append(
            {
                "data_offset": _reg(frame, "rdx"),
                "row_stride": _reg(frame, "r8") & 0xFFFFFFFF,
                "flag_r9": _reg(frame, "r9") & 0xFF,
                "requested_size": list(struct.unpack("<ii", size_raw)) if size_raw else None,
            }
        )
    if state["packed_handler_calls"] == state["expected_planes"]:
        state["kill_requested"] = True
        process.Kill()
    return False


def jpeg_handler(frame, bp_loc, internal_dict):
    _state()["jpeg_handler_calls"] += 1
    return False


def unpack_entry(frame, bp_loc, internal_dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    state["unpack_calls"] += 1
    if len(state["unpack_events"]) < 16:
        image = _reg(frame, "rdi")
        header = _read(process, image + 0x10, 0x18)
        first_ten = _read(process, _reg(frame, "rsi"), 10)
        if header is None or first_ten is None:
            state["errors"].append("unpack entry memory read failed")
        else:
            width, height, image_stride = struct.unpack_from("<iii", header)
            packed = int.from_bytes(first_ten, "little")
            state["unpack_events"].append(
                {
                    "width": width,
                    "height": height,
                    "image_stride": image_stride,
                    "packed_row_stride": _reg(frame, "rdx") & 0xFFFFFFFF,
                    "horizontal_flag": _reg(frame, "rcx") & 0xFF,
                    "vertical_flag": _reg(frame, "r8") & 0xFF,
                    "first_10_bytes": first_ten.hex(),
                    "first_8_pixels": [
                        (packed >> (10 * index)) & 0x3FF for index in range(8)
                    ],
                }
            )
    if state["unpack_calls"] == state["expected_planes"]:
        state["kill_requested"] = True
        process.Kill()
    return False


def capture_stopped(debugger, packed_id):
    state = _state()
    target = debugger.GetSelectedTarget()
    breakpoint = target.FindBreakpointByID(packed_id)
    process = target.GetProcess()
    thread = process.GetSelectedThread()
    frame = thread.GetFrameAtIndex(0)
    size_raw = _read(process, _reg(frame, "rcx"), 8)
    state["packed_handler_calls"] = breakpoint.GetHitCount()
    state["packed_events"].append(
        {
            "data_offset": _reg(frame, "rdx"),
            "row_stride": _reg(frame, "r8") & 0xFFFFFFFF,
            "flag_r9": _reg(frame, "r9") & 0xFF,
            "requested_size": list(struct.unpack("<ii", size_raw)) if size_raw else None,
        }
    )
    state["captured_stopped_frame"] = True


def report():
    state = _state()
    packet = {key: value for key, value in state.items() if key != "report_path"}
    with open(state["report_path"], "w", encoding="utf-8") as handle:
        json.dump(packet, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("RAW_SENSOR_LAYOUT_REPORT " + state["report_path"])
