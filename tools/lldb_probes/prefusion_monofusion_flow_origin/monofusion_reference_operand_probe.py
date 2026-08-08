"""Capture MonoFusion's generated A1 flow-reference operand boundary."""

import builtins
import hashlib
import json
import os
import struct


def reset(label, output_dir):
    builtins.l16_monofusion_reference_operand = {
        "label": label,
        "output_dir": output_dir,
        "entries": [],
        "returns": [],
        "affine_entries": [],
        "affine_returns": [],
        "demosaic_entry": None,
        "demosaic_guide_rows": [],
        "final_reference": None,
        "errors": [],
        "_pending": {},
    }


def _state():
    return builtins.l16_monofusion_reference_operand


def _reg(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    value = process.ReadMemory(address, size, error)
    if not error.Success() or len(value) != size:
        return None
    return value


def _u64(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<Q", raw)[0] if raw else None


def _i64(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<q", raw)[0] if raw else None


def _descriptor(process, address):
    raw = _read(process, address, 0x30)
    if raw is None:
        return {"address": address, "read_ok": False}
    domain = struct.unpack_from("<4i", raw, 0)
    size = struct.unpack_from("<2i", raw, 0x10)
    stride, channel_stride = struct.unpack_from("<2i", raw, 0x18)
    return {
        "address": address,
        "read_ok": True,
        "domain": list(domain),
        "size": list(size),
        "stride": stride,
        "channel_stride": channel_stride,
        "data": struct.unpack_from("<Q", raw, 0x20)[0],
        "owner": struct.unpack_from("<Q", raw, 0x28)[0],
        "raw_hex": raw.hex(),
    }


def _dump_plane(process, descriptor, channels, path):
    if not descriptor.get("read_ok"):
        return {"read_ok": False}
    width, height = descriptor["size"]
    stride = descriptor["stride"]
    if width <= 0 or height <= 0 or stride < width:
        return {"read_ok": False, "reason": "invalid descriptor"}
    digest = hashlib.sha256()
    byte_count = 0
    with open(path, "wb") as handle:
        for y in range(height):
            raw = _read(
                process,
                descriptor["data"] + y * stride * channels * 4,
                width * channels * 4,
            )
            if raw is None:
                return {"read_ok": False, "reason": f"row {y} unreadable"}
            handle.write(raw)
            digest.update(raw)
            byte_count += len(raw)
    return {
        "read_ok": True,
        "path": path,
        "byte_count": byte_count,
        "sha256": digest.hexdigest(),
        "storage": f"little-endian float32 x{channels}",
    }


def _dump_u16(process, descriptor, path):
    if not descriptor.get("read_ok"):
        return {"read_ok": False}
    width, height = descriptor["size"]
    stride = descriptor["stride"]
    if width <= 0 or height <= 0 or stride < width:
        return {"read_ok": False, "reason": "invalid descriptor"}
    digest = hashlib.sha256()
    byte_count = 0
    with open(path, "wb") as handle:
        for y in range(height):
            raw = _read(process, descriptor["data"] + y * stride * 2, width * 2)
            if raw is None:
                return {"read_ok": False, "reason": f"row {y} unreadable"}
            handle.write(raw)
            digest.update(raw)
            byte_count += len(raw)
    return {
        "read_ok": True,
        "path": path,
        "byte_count": byte_count,
        "sha256": digest.hexdigest(),
        "storage": "little-endian uint16",
    }


def demosaic_entry(frame, _bp_loc, _dict):
    state = _state()
    if state["demosaic_entry"] is not None:
        return False
    stack = _stack(frame)
    if not any(
        item.get("libcp_va") is not None
        and 0x1B17C0 <= item["libcp_va"] < 0x1B2B00
        for item in stack
    ):
        return False
    process = frame.GetThread().GetProcess()
    source = _descriptor(process, _reg(frame, "rsi"))
    if source.get("size") != [4160, 3120]:
        return False
    phase_raw = _read(process, _reg(frame, "rdx"), 8)
    gains_raw = _read(process, _reg(frame, "rcx"), 12)
    state["demosaic_entry"] = {
        "source": source,
        "source_dump": _dump_plane(
            process,
            source,
            1,
            os.path.join(state["output_dir"], "a1_demosaic_input.f32le"),
        ),
        "phase": list(struct.unpack("<2i", phase_raw)) if phase_raw else None,
        "gains": list(struct.unpack("<3f", gains_raw)) if gains_raw else None,
        "output": _reg(frame, "rdi"),
        "stack": stack,
    }
    target = process.GetTarget()
    slide = frame.GetPC() - 0x2EB560
    bp = target.BreakpointCreateByAddress(slide + 0x2EEF6E)
    bp.SetScriptCallbackFunction(
        "monofusion_reference_operand_probe.demosaic_guide_row"
    )
    state["_guide_row_breakpoint"] = bp.GetID()
    return False


def demosaic_guide_row(frame, _bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    rbp = _reg(frame, "rbp")
    output = _descriptor(process, state["demosaic_entry"]["output"])
    output_row = _reg(frame, "r9")
    output_begin = output.get("data", 0)
    output_end = output_begin + 4160 * 3120 * 4 * 4
    if not (output_begin <= output_row < output_end):
        return False
    local_y = _i64(process, rbp - 0x260)
    rectangle_address = _u64(process, rbp - 0x280)
    rectangle_raw = _read(process, rectangle_address, 16)
    if rectangle_raw is None:
        state["errors"].append(
            f"demosaic rectangle unreadable at 0x{rectangle_address:x}"
        )
        return False
    x0, y0, x1, y1 = struct.unpack("<4i", rectangle_raw)
    output_y = y0 + local_y
    targets = (0, 100, 1560, 3118)
    if output_y not in targets:
        return False
    if any(
        item["output_y"] == output_y
        and item["x0"] == x0
        and item["x1"] == x1
        for item in state["demosaic_guide_rows"]
    ):
        return False

    words = x1 - x0
    if words <= 0 or x0 < 0 or x1 > 4160:
        state["errors"].append(
            f"invalid demosaic tile [{x0},{x1}) x [{y0},{y1})"
        )
        return False

    pointers = {
        "A0": _u64(process, rbp - 0x248),
        "A1": _reg(frame, "r10"),
        "A2": _reg(frame, "r8"),
        "A3": _u64(process, rbp - 0x258),
        "B0": _u64(process, rbp - 0x250),
        "B1": _reg(frame, "r11"),
        "B2": _reg(frame, "rdi"),
        "B3": _reg(frame, "r14"),
    }
    rows = {}
    for name, pointer in pointers.items():
        raw = _read(process, pointer, words * 4)
        if raw is None:
            state["errors"].append(
                f"demosaic guide row {output_y} [{x0},{x1}) {name} "
                f"unreadable at 0x{pointer:x}"
            )
            continue
        path = os.path.join(
            state["output_dir"],
            f"a1_demosaic_{name}_row_{output_y}_x{x0}_{x1}.f32le",
        )
        with open(path, "wb") as handle:
            handle.write(raw)
        halo_raw = _read(process, pointer - 8 * 4, (words + 16) * 4)
        halo_path = os.path.join(
            state["output_dir"],
            f"a1_demosaic_{name}_row_{output_y}_x{x0}_{x1}_halo8.f32le",
        )
        if halo_raw is None:
            state["errors"].append(
                f"demosaic halo row {output_y} [{x0},{x1}) {name} "
                f"unreadable at 0x{pointer - 8 * 4:x}"
            )
        else:
            with open(halo_path, "wb") as handle:
                handle.write(halo_raw)
        rows[name] = {
            "pointer": pointer,
            "path": path,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "words": words,
            "halo_path": halo_path if halo_raw is not None else None,
            "halo_sha256": (
                hashlib.sha256(halo_raw).hexdigest()
                if halo_raw is not None else None
            ),
            "halo_words": words + 16 if halo_raw is not None else None,
        }
    state["demosaic_guide_rows"].append({
        "output_y": output_y,
        "local_y": local_y,
        "x0": x0,
        "x1": x1,
        "tile_y0": y0,
        "tile_y1": y1,
        "rows": rows,
        "stack": _stack(frame),
    })

    complete = True
    for target_y in targets:
        intervals = sorted(
            (item["x0"], item["x1"])
            for item in state["demosaic_guide_rows"]
            if item["output_y"] == target_y
        )
        cursor = 0
        for begin, end in intervals:
            if begin > cursor:
                break
            cursor = max(cursor, end)
        if cursor < 4160:
            complete = False
            break
    if complete:
        bp = process.GetTarget().FindBreakpointByID(state["_guide_row_breakpoint"])
        if bp and bp.IsValid():
            bp.SetEnabled(False)
    return False


def _stack(frame, limit=6):
    target = frame.GetThread().GetProcess().GetTarget()
    base = None
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            break
    result = []
    for index in range(min(limit, frame.GetThread().GetNumFrames())):
        item = frame.GetThread().GetFrameAtIndex(index)
        pc = item.GetPC()
        result.append({
            "pc": pc,
            "libcp_va": pc - base if base is not None and pc >= base else None,
            "function": item.GetFunctionName(),
        })
    return result


def scalar_entry(frame, _bp_loc, _dict):
    state = _state()
    if state["entries"]:
        return False
    process = frame.GetThread().GetProcess()
    expression = _reg(frame, "rsi")
    outer = _u64(process, expression)
    middle = _u64(process, outer) if outer else None
    source_address = _u64(process, middle) if middle else None
    source = _descriptor(process, source_address) if source_address else {"read_ok": False}
    output = _reg(frame, "rdi")
    os.makedirs(state["output_dir"], exist_ok=True)
    weights_raw = _read(process, middle + 0x10, 16) if middle else None
    scalar_raw = _read(process, expression + 0x08, 4)
    packet = {
        "expression": expression,
        "outer": outer,
        "middle": middle,
        "source": source,
        "weights": list(struct.unpack("<4f", weights_raw)) if weights_raw else None,
        "scalar": struct.unpack("<f", scalar_raw)[0] if scalar_raw else None,
        "output": output,
        "stack": _stack(frame),
    }
    packet["source_dump"] = _dump_plane(
        process,
        source,
        4,
        os.path.join(state["output_dir"], "a1_reference_source.f32x4le"),
    )
    state["entries"].append(packet)
    state["_pending"][str(frame.GetThread().GetThreadID())] = output
    return False


def scalar_return(frame, _bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    output = state["_pending"].pop(str(frame.GetThread().GetThreadID()), None)
    if output is None:
        return False
    descriptor = _descriptor(process, output)
    packet = {
        "output": descriptor,
        "output_dump": _dump_plane(
            process,
            descriptor,
            1,
            os.path.join(state["output_dir"], "a1_reference_scalar.f32le"),
        ),
    }
    state["returns"].append(packet)
    return False


def affine_entry(frame, _bp_loc, _dict):
    state = _state()
    if state["affine_entries"]:
        return False
    process = frame.GetThread().GetProcess()
    expression = _reg(frame, "rsi")
    outer = _u64(process, expression)
    source_address = _u64(process, outer) if outer else None
    source = _descriptor(process, source_address) if source_address else {"read_ok": False}
    scale_raw = _read(process, outer + 0x08, 4) if outer else None
    cap_raw = _read(process, expression + 0x08, 4)
    output = _reg(frame, "rdi")
    state["affine_entries"].append({
        "expression": expression,
        "outer": outer,
        "source": source,
        "source_matches_scalar_output": bool(
            state["returns"] and source_address == state["returns"][0]["output"]["address"]
        ),
        "scale": struct.unpack("<f", scale_raw)[0] if scale_raw else None,
        "cap": struct.unpack("<f", cap_raw)[0] if cap_raw else None,
        "output": output,
        "stack": _stack(frame),
    })
    state["_pending"]["affine:" + str(frame.GetThread().GetThreadID())] = output
    return False


def affine_return(frame, _bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    key = "affine:" + str(frame.GetThread().GetThreadID())
    output = state["_pending"].pop(key, None)
    if output is None:
        return False
    descriptor = _descriptor(process, output)
    state["affine_returns"].append({
        "output": descriptor,
        "output_dump": _dump_plane(
            process,
            descriptor,
            1,
            os.path.join(state["output_dir"], "a1_reference_affine.f32le"),
        ),
    })
    return False


def final_reference(frame, _bp_loc, _dict):
    state = _state()
    if state["final_reference"] is not None or not state["returns"]:
        return False
    process = frame.GetThread().GetProcess()
    vector = _reg(frame, "rsi")
    raw = _read(process, vector, 24)
    if raw is None:
        state["errors"].append("reference vector unreadable at flow producer")
        return False
    begin, end, capacity = struct.unpack("<QQQ", raw)
    count = (end - begin) // 0x30 if begin <= end <= capacity else -1
    descriptor = _descriptor(process, begin) if count > 0 else {"read_ok": False}
    state["final_reference"] = {
        "vector": vector,
        "begin": begin,
        "end": end,
        "capacity": capacity,
        "count": count,
        "level0": descriptor,
        "level0_dump": _dump_u16(
            process,
            descriptor,
            os.path.join(state["output_dir"], "a1_reference_level0.u16le"),
        ),
        "stack": _stack(frame),
    }
    process.Kill()
    return True


def attach(debugger):
    target = debugger.GetSelectedTarget()
    callbacks = {
        1: "monofusion_reference_operand_probe.scalar_entry",
        2: "monofusion_reference_operand_probe.scalar_return",
        3: "monofusion_reference_operand_probe.affine_entry",
        4: "monofusion_reference_operand_probe.affine_return",
        5: "monofusion_reference_operand_probe.final_reference",
        6: "monofusion_reference_operand_probe.demosaic_entry",
    }
    for bp_id, callback in callbacks.items():
        bp = target.FindBreakpointByID(bp_id)
        if not bp or not bp.IsValid():
            _state()["errors"].append(f"invalid breakpoint {bp_id}")
            continue
        bp.SetScriptCallbackFunction(callback)


def write_report(path):
    state = dict(_state())
    state.pop("_pending", None)
    with open(path, "w", encoding="ascii") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
