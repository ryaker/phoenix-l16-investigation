"""Capture finished cost records for one zero and one nonzero Skip-mask pixel."""

import builtins
import json
import struct

import lldb


def reset(label, source_lri):
    builtins.l16_skip_final = {
        "label": label,
        "source_lri": source_lri,
        "pixels": {},
        "errors": [],
        "capture_complete": False,
    }


def _state():
    return builtins.l16_skip_final


def _read(process, address, size):
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    if not error.Success() or len(data) != size:
        raise RuntimeError(f"read {size} at 0x{address:x}: {error}")
    return data


def _u32(process, address):
    return struct.unpack("<I", _read(process, address, 4))[0]


def _u64(process, address):
    return struct.unpack("<Q", _read(process, address, 8))[0]


def _record(process, source, x, y):
    record_base = _u64(process, source + 0x10)
    stride = _u32(process, source + 0x38)
    offset_table = _u64(process, source + 0x40)
    linear = x + y * stride
    offset = _u32(process, offset_table + 4 * linear)
    address = record_base + offset
    base, count, step, rounded = struct.unpack("<4H", _read(process, address, 8))
    costs = list(struct.unpack(f"<{count}H", _read(process, address + 8, 2 * count)))
    lane = min(range(count), key=costs.__getitem__) if count else 0
    return {
        "address": address,
        "base": base,
        "count": count,
        "step": step,
        "rounded": rounded,
        "costs": costs,
        "selected_lane": lane,
        "selected_absolute_index": (base + step * lane) & 0xFFFF,
    }


def on_breakpoint(frame, _bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    try:
        source = frame.FindRegister("rsi").GetValueAsUnsigned()
        target = source - 0xF8
        if _u32(process, target + 0x08) != 5 or _u32(process, target + 0x0C) != 8:
            return False
        width = _u32(process, target + 0x218)
        height = _u32(process, target + 0x21C)
        mask_stride = _u32(process, target + 0x220)
        mask_data = _u64(process, target + 0x228)
        first_row = _read(process, mask_data, width)
        zero_x = first_row.index(0)
        nonzero_x = next(index for index, value in enumerate(first_row) if value != 0)
        for polarity, x in (("computed", zero_x), ("skipped", nonzero_x)):
            mask = first_row[x]
            state["pixels"][polarity] = {
                "x": x,
                "y": 0,
                "mask": mask,
                "record": _record(process, source, x, 0),
            }
        state["target"] = target
        state["source"] = source
        state["dimensions"] = [width, height]
        state["mask_stride"] = mask_stride
        state["capture_complete"] = True
        process.Kill()
    except Exception as exc:
        state["errors"].append(str(exc))
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    for breakpoint in target.breakpoint_iter():
        breakpoint.SetScriptCallbackFunction("final_argmin_probe.on_breakpoint")


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
    print("SKIP_FINAL_REPORT", path, state["capture_complete"], state["errors"])
