"""LLDB callback for replaying the masked 0x298ff0 min/max pool."""

import builtins
import hashlib
import json
import struct
from pathlib import Path

import lldb


SITE = 0x26D8AC


def reset(label, source_lri, output_dir=None):
    builtins.l16_range_pool = {
        "label": label,
        "source_lri": source_lri,
        "output_dir": output_dir,
        "packets": [],
        "errors": [],
        "terminated_after_capture": False,
    }


def _state():
    return builtins.l16_range_pool


def _u64(process, address):
    error = lldb.SBError()
    value = process.ReadUnsignedFromMemory(address, 8, error)
    if not error.Success():
        raise RuntimeError(f"read u64 0x{address:x}: {error}")
    return value


def _u32(process, address):
    error = lldb.SBError()
    value = process.ReadUnsignedFromMemory(address, 4, error)
    if not error.Success():
        raise RuntimeError(f"read u32 0x{address:x}: {error}")
    return value


def _read(process, address, size):
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    if not error.Success() or len(data) != size:
        raise RuntimeError(f"read {size} bytes at 0x{address:x}: {error}")
    return data


def _descriptor(process, address):
    return {
        "address": address,
        "width": _u32(process, address + 0x10),
        "height": _u32(process, address + 0x14),
        "stride": _u32(process, address + 0x18),
        "data": _u64(process, address + 0x20),
    }


def _clamp(value, upper):
    return min(max(value, 0), upper - 1)


def _neighborhood(source, mask, width, height, stride, x, y):
    values = []
    mask_values = []
    coordinates = []
    for dy in (-1, 0, 1, 2):
        sy = _clamp(y + dy, height)
        for dx in (-1, 0, 1, 2):
            sx = _clamp(x + dx, width)
            offset = sy * stride + sx
            mask_value = mask[offset]
            value = struct.unpack_from("<H", source, 2 * offset)[0]
            coordinates.append([sx, sy])
            mask_values.append(mask_value)
            if mask_value != 0:
                values.append(value)
    return {
        "coordinates": coordinates,
        "mask_values": mask_values,
        "included_values": values,
        "expected_low": min(values) if values else 0xFFFF,
        "expected_high": max(values) if values else 0,
    }


def _output_word(process, descriptor, x, y):
    offset = y * descriptor["stride"] + x
    return struct.unpack("<H", _read(process, descriptor["data"] + 2 * offset, 2))[0]


def _dump_descriptor(process, descriptor, name, element_size):
    output_dir = _state().get("output_dir")
    if not output_dir:
        return None
    rows = []
    for y in range(descriptor["height"]):
        address = descriptor["data"] + y * descriptor["stride"] * element_size
        rows.append(_read(process, address, descriptor["width"] * element_size))
    raw = b"".join(rows)
    path = Path(output_dir) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return {
        "path": str(path),
        "size": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def _candidate_points(mask, width, height, stride):
    points = [
        (0, 0, "top_left"),
        (width - 1, 0, "top_right"),
        (0, height - 1, "bottom_left"),
        (width - 1, height - 1, "bottom_right"),
        (width // 2, height // 2, "center"),
    ]
    found = set()
    step_x = max(width // 80, 1)
    step_y = max(height // 60, 1)
    for y in range(0, height, step_y):
        for x in range(0, width, step_x):
            values = []
            for dy in (-1, 0, 1, 2):
                sy = _clamp(y + dy, height)
                for dx in (-1, 0, 1, 2):
                    sx = _clamp(x + dx, width)
                    values.append(mask[sy * stride + sx])
            valid_count = sum(value != 0 for value in values)
            if 0 < valid_count < 16 and "mixed_mask" not in found:
                points.append((x, y, "mixed_mask"))
                found.add("mixed_mask")
            if valid_count == 0 and "all_invalid" not in found:
                points.append((x, y, "all_invalid"))
                found.add("all_invalid")
            if len(found) == 2:
                return points
    return points


def on_breakpoint(frame, _bp_loc, _dict):
    state = _state()
    try:
        process = frame.GetThread().GetProcess()
        rbp = frame.FindRegister("rbp").GetValueAsUnsigned()
        target = frame.FindRegister("r13").GetValueAsUnsigned()
        source_desc = _descriptor(process, rbp - 0xB0)
        mask_desc = _descriptor(process, rbp - 0x140)
        low_desc = _descriptor(process, rbp - 0xE0)
        high_desc = _descriptor(process, rbp - 0x110)
        width, height, stride = source_desc["width"], source_desc["height"], source_desc["stride"]
        if not width or not height or stride < width:
            raise RuntimeError(f"invalid source descriptor {source_desc}")
        if (mask_desc["width"], mask_desc["height"], mask_desc["stride"]) != (width, height, stride):
            raise RuntimeError(f"mask descriptor mismatch {mask_desc}")
        if (low_desc["width"], low_desc["height"], high_desc["width"], high_desc["height"]) != (
            width,
            height,
            width,
            height,
        ):
            raise RuntimeError("output descriptor mismatch")

        source = _read(process, source_desc["data"], 2 * stride * height)
        mask = _read(process, mask_desc["data"], stride * height)
        samples = []
        for x, y, kind in _candidate_points(mask, width, height, stride):
            replay = _neighborhood(source, mask, width, height, stride, x, y)
            replay.update(
                {
                    "kind": kind,
                    "x": x,
                    "y": y,
                    "observed_low": _output_word(process, low_desc, x, y),
                    "observed_high": _output_word(process, high_desc, x, y),
                }
            )
            samples.append(replay)

        packet = {
            "target": target,
            "target_dimensions": [_u32(process, target + 0x2A0), _u32(process, target + 0x2A4)],
            "padding_0x10": _u32(process, target + 0x10),
            "kernel_size_0x14": _u32(process, target + 0x14),
            "source": source_desc,
            "mask": mask_desc,
            "range_low": low_desc,
            "range_high": high_desc,
            "samples": samples,
        }
        key = tuple(packet["target_dimensions"])
        if key not in {tuple(item["target_dimensions"]) for item in state["packets"]}:
            stem = f"{width}x{height}"
            packet["files"] = {
                "prior_depth": _dump_descriptor(
                    process, source_desc, f"prior_depth_{stem}.u16le", 2
                ),
                "prior_skip": _dump_descriptor(
                    process, mask_desc, f"prior_skip_{stem}.u8", 1
                ),
                "range_low": _dump_descriptor(
                    process, low_desc, f"range_low_{stem}.u16le", 2
                ),
                "range_high": _dump_descriptor(
                    process, high_desc, f"range_high_{stem}.u16le", 2
                ),
            }
            state["packets"].append(packet)
        if len(state["packets"]) >= 5:
            state["terminated_after_capture"] = True
            process.Kill()
            return False
    except Exception as exc:
        state["errors"].append(str(exc))
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    breakpoint = target.FindBreakpointByID(1)
    breakpoint.SetScriptCallbackFunction("range_pool_probe.on_breakpoint")
    print("RANGE_POOL_ATTACHED", breakpoint.IsValid())


def write_report(debugger, path):
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    state["process"] = {
        "state": int(process.GetState()),
        "exit_status": process.GetExitStatus(),
    }
    with open(path, "w", encoding="ascii") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("RANGE_POOL_REPORT", path, len(state["packets"]), state["errors"])
