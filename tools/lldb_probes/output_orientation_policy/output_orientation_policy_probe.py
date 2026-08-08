"""Trace public orientation use through the final HDR writer boundary."""

import builtins
import json
import struct


SITES = {
    0x13F180: "orientation_accessor",
    0x39B68A: "transform_copy_matrix_read",
    0x402A03: "orientation_transform_ready",
    0x419102: "scaled_transform_matrix_ready",
    0x4198F1: "export_transform_output_ready",
    0x41E180: "output_helper_entry",
    0x232731: "writer_virtual_call",
}


def reset(label=""):
    builtins.l16_output_orientation_policy = {
        "label": label,
        "counts": {name: 0 for name in SITES.values()},
        "events": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_output_orientation_policy"):
        reset()
    return builtins.l16_output_orientation_policy


def _base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            value = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if value != 0xFFFFFFFFFFFFFFFF:
                return value
    return None


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    return data if error.Success() and len(data) == size else None


def _u32(process, address):
    raw = _read(process, address, 4)
    return struct.unpack("<I", raw)[0] if raw is not None else None


def _i32(process, address):
    raw = _read(process, address, 4)
    return struct.unpack("<i", raw)[0] if raw is not None else None


def _u64(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<Q", raw)[0] if raw is not None else None


def _f32s(process, address, count):
    raw = _read(process, address, count * 4)
    return list(struct.unpack("<" + "f" * count, raw)) if raw is not None else None


def _stack(thread, base, limit=12):
    result = []
    for index in range(min(thread.GetNumFrames(), limit)):
        frame = thread.GetFrameAtIndex(index)
        pc = frame.GetPC()
        result.append(
            {
                "index": index,
                "pc": pc,
                "libcp_va": pc - base if base is not None and pc >= base else None,
                "function": frame.GetFunctionName(),
            }
        )
    return result


def hit(frame, _bp_loc, _internal_dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    base = _base(process.GetTarget())
    va = frame.GetPC() - base if base is not None else None
    name = SITES.get(va, f"unknown_{va}")
    state["counts"][name] = state["counts"].get(name, 0) + 1

    try:
        event = {
            "site": name,
            "site_va": va,
            "stack": _stack(thread, base),
        }
        if va == 0x13F180:
            preferences = _u(frame, "rdi")
            event["preferences"] = preferences
            event["orientation_field"] = preferences + 0x2C
            event["orientation"] = _u32(process, preferences + 0x2C)
            present = _read(process, preferences + 0x30, 1)
            event["present"] = bool(present[0]) if present is not None else None
        elif va == 0x402A03:
            transform = _u(frame, "rdi")
            event["transform"] = transform
            event["dimensions"] = {
                "width": _i32(process, transform + 8),
                "height": _i32(process, transform + 0xC),
            }
            event["matrix3x3"] = _f32s(process, transform + 0x10, 9)
            event["crop_envelope"] = _f32s(process, transform + 0x34, 4)
        elif va == 0x39B68A:
            source = _u(frame, "rbx")
            destination = _u(frame, "r13")
            event["source_transform"] = source
            event["destination_transform"] = destination
            event["dimensions"] = {
                "width": _i32(process, source + 8),
                "height": _i32(process, source + 0xC),
            }
            event["source_matrix3x3"] = _f32s(process, source + 0x10, 9)
            event["source_crop_envelope"] = _f32s(process, source + 0x34, 4)
        elif va == 0x419102:
            matrix = _u(frame, "rdi")
            dimensions = _u64(process, _u(frame, "rbx"))
            requested = _u(frame, "r15")
            event["scaled_matrix3x3"] = _f32s(process, matrix, 9)
            event["level_dimensions"] = {
                "width": _i32(process, dimensions),
                "height": _i32(process, dimensions + 4),
            }
            event["requested_dimensions"] = {
                "width": _i32(process, requested),
                "height": _i32(process, requested + 4),
            }
        elif va == 0x4198F1:
            output = _u(frame, "rbx")
            matrix_object = _u64(process, output + 0x40)
            event["transform_output"] = {
                "address": output,
                "level_index": _i32(process, output),
                "roi": [
                    _i32(process, output + 4),
                    _i32(process, output + 8),
                    _i32(process, output + 0xC),
                    _i32(process, output + 0x10),
                ],
                "scale": _f32s(process, output + 0x14, 2),
                "matrix_object": matrix_object,
                "matrix3x3": _f32s(process, matrix_object + 8, 9),
            }
        elif va == 0x41E180:
            dims = _u(frame, "rdx")
            event["format"] = _u(frame, "r8") & 0xFFFFFFFF
            event["dimensions"] = {
                "address": dims,
                "width": _i32(process, dims),
                "height": _i32(process, dims + 4),
            }
        elif va == 0x232731:
            descriptor = _u(frame, "rdx")
            event["writer_descriptor"] = {
                "address": descriptor,
                "width": _i32(process, descriptor),
                "height": _i32(process, descriptor + 4),
                "row_bytes": _u64(process, descriptor + 8),
                "bytes_per_pixel": _i32(process, descriptor + 0x10),
                "data": _u64(process, descriptor + 0x18),
            }
        state["events"].append(event)
    except Exception as exc:
        state["errors"].append({"site": name, "error": repr(exc)})
    return False


def install(debugger):
    target = debugger.GetSelectedTarget()
    base = _base(target)
    if base is None:
        raise RuntimeError("libcp.dylib is not loaded")
    for va in SITES:
        bp = target.BreakpointCreateByAddress(base + va)
        bp.SetScriptCallbackFunction("output_orientation_policy_probe.hit")
    print("L16_OUTPUT_ORIENTATION_POLICY_INSTALLED", len(SITES))


def write_report(path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(_state(), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_OUTPUT_ORIENTATION_POLICY_REPORT", path)
