"""Capture ColorFusionBayer's float blending-weight output and byte sidecar.

FusionCacheBayerC1::$_0 (0x407710) asks ColorFusionBayer::process (0x1aab40)
for two outputs.  The second output is converted by 0x1bd1e0 and inserted into
FusionCacheBayer's uint8 TileCache at +0xe0.  This probe records all three
representations at the installed call boundaries without interpreting them.
"""

import builtins
import hashlib
import json
import os
import struct


CALLBACK_ENTRY = 0x407710
AFTER_COLOR_FUSION = 0x4077C1
AFTER_QUANTIZE = 0x4077E6
COLOR_FUSION_CORE = 0x19C790
QUANTIZE_ENTRY = 0x1BD1E0


def reset(label="", report_path="", cap=6):
    builtins.l16_colorfusion_weight = {
        "label": label,
        "report_path": report_path,
        "cap": cap,
        "breakpoint_ids": {},
        "entry_events": [],
        "float_events": [],
        "byte_events": [],
        "quantize_events": [],
        "core_events": [],
        "errors": [],
    }


def _s():
    if not hasattr(builtins, "l16_colorfusion_weight"):
        reset()
    return builtins.l16_colorfusion_weight


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    if not address or address < 0x1000 or address > 0x00007FFFFFFFFFFF:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    try:
        data = process.ReadMemory(address, size, error)
    except Exception:
        return None
    return data if error.Success() and data is not None and len(data) == size else None


def _qword(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<Q", raw)[0] if raw is not None else 0


def _base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                return base
    return None


def _stack(frame, count=8):
    thread = frame.GetThread()
    target = thread.GetProcess().GetTarget()
    base = _base(target)
    out = []
    for index in range(min(count, thread.GetNumFrames())):
        item = thread.GetFrameAtIndex(index)
        pc = item.GetPC()
        out.append({
            "i": index,
            "pc": pc,
            "libcp_va": pc - base if base is not None and base <= pc < base + 0x700000 else None,
            "fn": item.GetFunctionName(),
        })
    return out


def _image(process, address, element, rows=3, cols=48):
    raw = _read(process, address, 0x30)
    if raw is None:
        return {"addr": address, "read_ok": False}
    width, height, stride = struct.unpack_from("<iii", raw, 0x10)
    data_ptr = struct.unpack_from("<Q", raw, 0x20)[0]
    out = {
        "addr": address,
        "read_ok": True,
        "width": width,
        "height": height,
        "stride": stride,
        "data_ptr": data_ptr,
        "raw_hex": raw.hex(),
    }
    if not data_ptr or width <= 0 or height <= 0 or stride <= 0:
        return out
    samples = []
    all_values = []
    for row in range(min(rows, height)):
        data = _read(process, data_ptr + row * stride * element, min(cols, width) * element)
        if data is None:
            samples.append(None)
            continue
        if element == 4:
            values = list(struct.unpack("<" + "f" * (len(data) // 4), data))
        else:
            values = list(data)
        samples.append(values)
        all_values.extend(values)
    out["sample_rows"] = samples
    if all_values:
        out["sample_stats"] = {
            "n": len(all_values),
            "min": min(all_values),
            "max": max(all_values),
            "mean": sum(all_values) / len(all_values),
        }
    first = _read(process, data_ptr, min(width, 4096) * element)
    if first is not None:
        out["first_row_sha256"] = hashlib.sha256(first).hexdigest()
    return out


def _vector(process, address, stride, item_cap=8):
    raw = _read(process, address, 24)
    if raw is None:
        return {"addr": address, "read_ok": False}
    begin, end, capacity = struct.unpack("<QQQ", raw)
    count = (end - begin) // stride if begin and end >= begin else -1
    out = {
        "addr": address,
        "read_ok": True,
        "begin": begin,
        "end": end,
        "capacity": capacity,
        "stride": stride,
        "count": count,
    }
    if 0 <= count <= 128:
        data = _read(process, begin, min(count, item_cap) * stride)
        if data is not None:
            out["items_hex"] = [
                data[index:index + stride].hex()
                for index in range(0, len(data), stride)
            ]
    return out


def _disable(frame, name):
    state = _s()
    bp_id = state["breakpoint_ids"].get(name)
    target = frame.GetThread().GetProcess().GetTarget()
    breakpoint = target.FindBreakpointByID(bp_id) if bp_id else None
    if breakpoint and breakpoint.IsValid():
        breakpoint.SetEnabled(False)


def callback_entry(frame, _bp_loc, _dict):
    state = _s()
    if len(state["entry_events"]) >= int(state["cap"]):
        return False
    process = frame.GetThread().GetProcess()
    callable_ptr = _u(frame, "rdi")
    owner = _qword(process, callable_ptr + 8)
    tile_shared = _u(frame, "rsi")
    tile = _qword(process, tile_shared)
    state["entry_events"].append({
        "thread": frame.GetThread().GetThreadID(),
        "callable": callable_ptr,
        "owner": owner,
        "color_fusion": _qword(process, owner + 0x120),
        "float_cache": _qword(process, owner + 0x128),
        "byte_cache": _qword(process, owner + 0xE0),
        "tile_shared": tile_shared,
        "tile": tile,
        "tile_float_output": _image(process, tile + 0xF0, 4),
        "stack": _stack(frame),
    })
    if len(state["entry_events"]) >= int(state["cap"]):
        _disable(frame, "callback_entry")
    return False


def after_color_fusion(frame, _bp_loc, _dict):
    state = _s()
    if len(state["float_events"]) >= int(state["cap"]):
        return False
    process = frame.GetThread().GetProcess()
    rbp = _u(frame, "rbp")
    state["float_events"].append({
        "thread": frame.GetThread().GetThreadID(),
        "owner": _u(frame, "r12"),
        "fused_output": _image(process, _u(frame, "rbx"), 4),
        "float_weight": _image(process, rbp - 0x70, 4),
        "rect_i32": list(struct.unpack("<4i", _read(process, rbp - 0x38, 16))),
        "stack": _stack(frame),
    })
    if len(state["float_events"]) >= int(state["cap"]):
        _disable(frame, "after_color_fusion")
    return False


def after_quantize(frame, _bp_loc, _dict):
    state = _s()
    if len(state["byte_events"]) >= int(state["cap"]):
        return False
    process = frame.GetThread().GetProcess()
    rbp = _u(frame, "rbp")
    float_weight = _image(process, rbp - 0x70, 4)
    byte_weight = _image(process, rbp - 0xA0, 1)
    pairs = []
    for float_row, byte_row in zip(float_weight.get("sample_rows", []), byte_weight.get("sample_rows", [])):
        if float_row is None or byte_row is None:
            continue
        pairs.extend({"float": value, "byte": byte} for value, byte in zip(float_row, byte_row))
    state["byte_events"].append({
        "thread": frame.GetThread().GetThreadID(),
        "owner": _u(frame, "r12"),
        "float_weight": float_weight,
        "byte_weight": byte_weight,
        "pairs": pairs,
        "stack": _stack(frame),
    })
    if len(state["byte_events"]) >= int(state["cap"]):
        _disable(frame, "after_quantize")
    return False


def quantize_entry(frame, _bp_loc, _dict):
    state = _s()
    if len(state["quantize_events"]) >= int(state["cap"]):
        return False
    process = frame.GetThread().GetProcess()
    stack = _stack(frame, 10)
    # Only retain the FusionCacheBayer callback caller at 0x4077e6.
    if not any(item.get("libcp_va") == AFTER_QUANTIZE for item in stack):
        return False
    state["quantize_events"].append({
        "thread": frame.GetThread().GetThreadID(),
        "dst_before": _image(process, _u(frame, "rdi"), 1),
        "float_weight": _image(process, _u(frame, "rsi"), 4, rows=6, cols=96),
        "stack": stack,
    })
    if len(state["quantize_events"]) >= int(state["cap"]):
        _disable(frame, "quantize_entry")
    return False


def core_entry(frame, _bp_loc, _dict):
    state = _s()
    if len(state["core_events"]) >= int(state["cap"]):
        return False
    process = frame.GetThread().GetProcess()
    state["core_events"].append({
        "thread": frame.GetThread().GetThreadID(),
        "out_fused": _u(frame, "rdi"),
        "out_weight": _u(frame, "rsi"),
        "source_image": _image(process, _u(frame, "rdx"), 8),
        "flow_vector": _vector(process, _u(frame, "rcx"), 0x30),
        "source_vector": _vector(process, _u(frame, "r8"), 0x30),
        "callback": _u(frame, "r9"),
        "stack": _stack(frame),
    })
    if len(state["core_events"]) >= int(state["cap"]):
        _disable(frame, "core_entry")
    return False


def install(debugger):
    target = debugger.GetSelectedTarget()
    callbacks = (
        (QUANTIZE_ENTRY, "quantize_entry"),
        (AFTER_QUANTIZE, "after_quantize"),
    )
    ids = {}
    for address, callback in callbacks:
        before = target.GetNumBreakpoints()
        debugger.HandleCommand(f"breakpoint set --shlib libcp.dylib --address 0x{address:x}")
        if target.GetNumBreakpoints() <= before:
            _s()["errors"].append(f"failed breakpoint 0x{address:x}")
            continue
        bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
        bp.SetScriptCallbackFunction(f"colorfusion_weight_probe.{callback}")
        ids[callback] = bp.GetID()
    _s()["breakpoint_ids"] = dict(ids)
    print("COLORFUSION_WEIGHT_INSTALLED", ids)


def write_report(_debugger, path=""):
    out = path or _s().get("report_path")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(dict(_s()), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("COLORFUSION_WEIGHT_WROTE", out)
