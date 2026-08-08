"""Capture MonoFusion's reduced flow producer and live mode-0 consumption."""

import builtins
import collections
import hashlib
import json
import os
import struct


def reset(label=""):
    builtins.l16_monofusion_flow_origin = {
        "label": label,
        "producer_entries": [],
        "producer_returns": [],
        "vector_copies": [],
        "worker_entries": [],
        "flow_uses": [],
        "variant_hits": [],
        "intermediate_stages": [],
        "threshold_map_entries": [],
        "threshold_map_builds": [],
        "flow_rejection_checks": [],
        "pyramid_inputs": [],
        "prediction_entries": [],
        "prediction_returns": [],
        "quadratic_fits": [],
        "terminated_after_samples": False,
        "errors": [],
        "_pending": {},
        "_producer_active": False,
        "_producer_filter_size": None,
        "_stop_after_stages": False,
        "_stop_after_variant_operands": False,
        "_breakpoint_ids": {},
        "_dump_dir": None,
        "_prediction_pending": {},
        "_prediction_caller_va": None,
        "_prediction_targets": None,
        "_quadratic_pending": {},
    }


def _state():
    if not hasattr(builtins, "l16_monofusion_flow_origin"):
        reset()
    return builtins.l16_monofusion_flow_origin


def _reg(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    if not address or size < 0:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    raw = process.ReadMemory(address, size, error)
    return raw if error.Success() and len(raw) == size else None


def _i32(process, address):
    raw = _read(process, address, 4)
    return struct.unpack("<i", raw)[0] if raw else None


def _f32(process, address):
    raw = _read(process, address, 4)
    return struct.unpack("<f", raw)[0] if raw else None


def _u64(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<Q", raw)[0] if raw else None


def _xmm_f32(frame, name):
    lldb = builtins.__import__("lldb")
    data = frame.FindRegister(name).GetData()
    error = lldb.SBError()
    value = data.GetFloat(error, 0) if data.IsValid() else None
    return value if error.Success() else None


def prediction_entry(frame, _bp_loc, _dict):
    state = _state()
    if not state["_producer_active"] or len(state["prediction_entries"]) >= 32:
        return False
    stack = _stack(frame, 4)
    caller_va = stack[1]["libcp_va"] if len(stack) > 1 else None
    if state["_prediction_caller_va"] is not None and caller_va != state["_prediction_caller_va"]:
        return False
    grid = [_xmm_f32(frame, "xmm0"), _xmm_f32(frame, "xmm1")]
    if state["_prediction_targets"] is not None:
        integer_grid = [int(grid[0]), int(grid[1])]
        if integer_grid not in state["_prediction_targets"]:
            return False
    process = frame.GetThread().GetProcess()
    output = _reg(frame, "rdi")
    previous_flow = _descriptor(process, _reg(frame, "rcx"))
    sequence = len(state["prediction_entries"])
    packet = {
        "sequence": sequence,
        "grid": grid,
        "scale_r8": _reg(frame, "r8") & 0xFFFFFFFF,
        "reference_patch": _descriptor(process, _reg(frame, "rsi")),
        "source": _descriptor(process, _reg(frame, "rdx")),
        "previous_flow": previous_flow,
        "previous_flow_summary": _float_flow_summary(process, previous_flow),
        "output": output,
        "stack": stack,
    }
    state["prediction_entries"].append(packet)
    state["_prediction_pending"][str(frame.GetThread().GetThreadID())] = {
        "output": output,
        "sequence": sequence,
    }
    return False


def prediction_return(frame, _bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    pending = state["_prediction_pending"].pop(str(frame.GetThread().GetThreadID()), None)
    if pending is None:
        return False
    output = pending["output"] if pending else None
    raw = _read(process, output, 8) if output else None
    state["prediction_returns"].append({
        "sequence": pending["sequence"] if pending else None,
        "output": list(struct.unpack("<2i", raw)) if raw else None,
    })
    target_count = len(state["_prediction_targets"]) if state["_prediction_targets"] else 32
    if len(state["prediction_returns"]) >= target_count:
        state["terminated_after_samples"] = True
        process.Kill()
        return True
    return False


def quadratic_entry(frame, _bp_loc, _dict):
    state = _state()
    if len(state["quadratic_fits"]) >= 32:
        return False
    process = frame.GetThread().GetProcess()
    output = _reg(frame, "rdi")
    raw = _read(process, _reg(frame, "rsi"), 36)
    sequence = len(state["quadratic_fits"]) + len(state["_quadratic_pending"])
    state["_quadratic_pending"][str(frame.GetThread().GetThreadID())] = {
        "sequence": sequence,
        "output": output,
        "input": list(struct.unpack("<9f", raw)) if raw else None,
        "stack": _stack(frame, 4),
    }
    return False


def quadratic_return(frame, _bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    pending = state["_quadratic_pending"].pop(str(frame.GetThread().GetThreadID()), None)
    if pending is None:
        return False
    raw = _read(process, pending["output"], 8)
    pending["result"] = list(struct.unpack("<2f", raw)) if raw else None
    state["quadratic_fits"].append(pending)
    if len(state["quadratic_fits"]) >= 32:
        state["terminated_after_samples"] = True
        process.Kill()
        return True
    return False


def _descriptor(process, address):
    raw = _read(process, address, 0x30)
    if raw is None:
        return {"address": address, "read_ok": False}
    words = struct.unpack("<8i", raw[:0x20])
    return {
        "address": address,
        "read_ok": True,
        "domain": list(words[:4]),
        "size": list(words[4:6]),
        "stride": words[6],
        "channel_stride": words[7],
        "data": struct.unpack_from("<Q", raw, 0x20)[0],
        "owner": struct.unpack_from("<Q", raw, 0x28)[0],
        "raw_hex": raw.hex(),
    }


def _descriptor_vector(process, address, limit=8):
    raw = _read(process, address, 24)
    if raw is None:
        return {"address": address, "read_ok": False}
    begin, end, capacity = struct.unpack("<QQQ", raw)
    valid = begin <= end <= capacity and (end - begin) % 0x30 == 0
    count = (end - begin) // 0x30 if valid else None
    records = []
    if valid and count is not None and count <= limit:
        records = [_descriptor(process, begin + index * 0x30) for index in range(count)]
    return {
        "address": address,
        "read_ok": True,
        "begin": begin,
        "end": end,
        "capacity": capacity,
        "valid": valid,
        "count": count,
        "records": records,
    }


def _dump_u16_plane(process, descriptor, path):
    if not descriptor.get("read_ok"):
        return {"read_ok": False}
    width, height = descriptor["size"]
    stride = descriptor["stride"]
    if width <= 0 or height <= 0 or stride < width:
        return {"read_ok": False, "reason": "invalid dimensions"}
    rows = []
    for y in range(height):
        raw = _read(process, descriptor["data"] + y * stride * 2, width * 2)
        if raw is None:
            return {"read_ok": False, "reason": f"row {y} unreadable"}
        rows.append(raw)
    payload = b"".join(rows)
    with open(path, "wb") as handle:
        handle.write(payload)
    return {
        "read_ok": True,
        "path": path,
        "byte_count": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _dump_f32x2_plane(process, descriptor, path):
    if not descriptor.get("read_ok"):
        return {"read_ok": False}
    width, height = descriptor["size"]
    stride = descriptor["stride"]
    if width <= 0 or height <= 0 or stride < width:
        return {"read_ok": False, "reason": "invalid dimensions"}
    rows = []
    for y in range(height):
        raw = _read(process, descriptor["data"] + y * stride * 8, width * 8)
        if raw is None:
            return {"read_ok": False, "reason": f"row {y} unreadable"}
        rows.append(raw)
    payload = b"".join(rows)
    with open(path, "wb") as handle:
        handle.write(payload)
    return {
        "read_ok": True,
        "path": path,
        "byte_count": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _scalar_samples(process, descriptor):
    if not descriptor.get("read_ok"):
        return {"read_ok": False}
    width, height = descriptor["size"]
    stride = descriptor["stride"]
    if width <= 0 or height <= 0 or stride < width:
        return {"read_ok": False, "reason": "invalid dimensions"}
    coordinates = [
        (0, 0),
        (width - 1, 0),
        (0, height - 1),
        (width - 1, height - 1),
        (width // 2, height // 2),
        (width // 4, height // 4),
        ((3 * width) // 4, (3 * height) // 4),
    ]
    samples = []
    for x, y in coordinates:
        raw = _read(process, descriptor["data"] + (y * stride + x) * 4, 4)
        samples.append({
            "pixel": [x, y],
            "value": struct.unpack("<f", raw)[0] if raw else None,
        })
    return {"read_ok": all(item["value"] is not None for item in samples), "samples": samples}


def _flow_summary(process, descriptor):
    if not descriptor.get("read_ok"):
        return {"read_ok": False}
    width, height = descriptor["size"]
    stride = descriptor["stride"]
    if width <= 0 or height <= 0 or stride < width or width * height > 2_000_000:
        return {"read_ok": False, "reason": "invalid dimensions"}
    raw = _read(process, descriptor["data"], stride * height * 4)
    if raw is None:
        return {"read_ok": False, "reason": "data unreadable"}

    min_x = 32767
    max_x = -32768
    min_y = 32767
    max_y = -32768
    nonzero = 0
    pairs = collections.Counter()
    for y in range(height):
        row = y * stride * 4
        for x in range(width):
            dx, dy = struct.unpack_from("<hh", raw, row + x * 4)
            min_x = min(min_x, dx)
            max_x = max(max_x, dx)
            min_y = min(min_y, dy)
            max_y = max(max_y, dy)
            nonzero += int(dx != 0 or dy != 0)
            pairs[(dx, dy)] += 1

    coordinates = [
        (0, 0),
        (width - 1, 0),
        (0, height - 1),
        (width - 1, height - 1),
        (width // 2, height // 2),
        (width // 4, height // 4),
        ((3 * width) // 4, (3 * height) // 4),
    ]
    samples = []
    for x, y in coordinates:
        dx, dy = struct.unpack_from("<hh", raw, (y * stride + x) * 4)
        samples.append({"grid": [x, y], "flow": [dx, dy]})
    return {
        "read_ok": True,
        "storage": "packed little-endian int16 dx, int16 dy",
        "byte_count": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "min": [min_x, min_y],
        "max": [max_x, max_y],
        "nonzero_pairs": nonzero,
        "pair_count": width * height,
        "unique_pairs": len(pairs),
        "most_common_pairs": [
            {"flow": list(pair), "count": count}
            for pair, count in pairs.most_common(24)
        ],
        "samples": samples,
    }


def _float_flow_summary(process, descriptor):
    if not descriptor.get("read_ok"):
        return {"read_ok": False}
    width, height = descriptor["size"]
    stride = descriptor["stride"]
    if width <= 0 or height <= 0 or stride < width or width * height > 2_000_000:
        return {"read_ok": False, "reason": "invalid dimensions"}
    raw = _read(process, descriptor["data"], stride * height * 8)
    if raw is None:
        return {"read_ok": False, "reason": "data unreadable"}

    min_x = float("inf")
    max_x = float("-inf")
    min_y = float("inf")
    max_y = float("-inf")
    finite = 0
    sentinel = 0
    for y in range(height):
        row = y * stride * 8
        for x in range(width):
            dx, dy = struct.unpack_from("<ff", raw, row + x * 8)
            if dx <= -999_000.0 and dy <= -999_000.0:
                sentinel += 1
            if abs(dx) != float("inf") and abs(dy) != float("inf") and dx == dx and dy == dy:
                finite += 1
                min_x = min(min_x, dx)
                max_x = max(max_x, dx)
                min_y = min(min_y, dy)
                max_y = max(max_y, dy)

    coordinates = [
        (0, 0),
        (width - 1, 0),
        (0, height - 1),
        (width - 1, height - 1),
        (width // 2, height // 2),
        (width // 4, height // 4),
        ((3 * width) // 4, (3 * height) // 4),
    ]
    samples = []
    for x, y in coordinates:
        dx, dy = struct.unpack_from("<ff", raw, (y * stride + x) * 8)
        samples.append({"grid": [x, y], "flow": [dx, dy]})
    return {
        "read_ok": True,
        "storage": "little-endian float32 dx, float32 dy",
        "byte_count": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "min": [min_x, min_y] if finite else None,
        "max": [max_x, max_y] if finite else None,
        "finite_pairs": finite,
        "pair_count": width * height,
        "invalid_sentinel_pairs": sentinel,
        "samples": samples,
    }


def _stack(frame, limit=8):
    result = []
    thread = frame.GetThread()
    target = thread.GetProcess().GetTarget()
    base = None
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            break
    for index in range(min(limit, thread.GetNumFrames())):
        item = thread.GetFrameAtIndex(index)
        pc = item.GetPC()
        result.append({
            "pc": pc,
            "libcp_va": pc - base if base is not None and pc >= base else None,
            "function": item.GetFunctionName(),
        })
    return result


def producer_entry(frame, _bp_loc, _dict):
    process = frame.GetThread().GetProcess()
    output = _reg(frame, "rdi")
    config = _reg(frame, "rcx")
    config_owner = _u64(process, config + 8)
    threshold_map = _descriptor(process, config_owner + 0x20) if config_owner else {"read_ok": False}
    sample = {
        "output_address": output,
        "output_before": _descriptor(process, output),
        "pyramids_rsi": _descriptor_vector(process, _reg(frame, "rsi")),
        "operand_rdx": _descriptor(process, _reg(frame, "rdx")),
        "config_rcx_hex": (_read(process, config, 0x100) or b"").hex(),
        "config_owner": config_owner,
        "flow_threshold_0x200": _f32(process, config_owner + 0x200) if config_owner else None,
        "threshold_map": threshold_map,
        "threshold_map_samples": _scalar_samples(process, threshold_map),
        "stack": _stack(frame),
    }
    state = _state()
    state["producer_entries"].append(sample)
    state["_pending"][str(frame.GetThread().GetThreadID())] = output
    operand_size = sample["operand_rdx"].get("size")
    state["_producer_active"] = (
        state["_producer_filter_size"] is None
        or operand_size == state["_producer_filter_size"]
    )
    return False


def configure_producer_filter(size):
    _state()["_producer_filter_size"] = list(map(int, size))


def producer_return(frame, _bp_loc, _dict):
    process = frame.GetThread().GetProcess()
    output = _state()["_pending"].pop(str(frame.GetThread().GetThreadID()), None)
    descriptor = _descriptor(process, output) if output else {"read_ok": False}
    _state()["producer_returns"].append({
        "output": descriptor,
        "flow": _flow_summary(process, descriptor),
    })
    _state()["_producer_active"] = False
    return False


def vector_copy(frame, _bp_loc, _dict):
    process = frame.GetThread().GetProcess()
    source = _descriptor(process, _reg(frame, "rsi"))
    destination = _descriptor(process, _reg(frame, "rdi"))
    _state()["vector_copies"].append({
        "destination_before": destination,
        "source": source,
        "source_flow": _flow_summary(process, source),
    })
    return False


def worker_entry(frame, _bp_loc, _dict):
    process = frame.GetThread().GetProcess()
    obj = _reg(frame, "rdi")
    vector = _descriptor_vector(process, obj + 0xD8)
    records = []
    for descriptor in vector.get("records", []):
        records.append({"descriptor": descriptor, "flow": _flow_summary(process, descriptor)})
    _state()["worker_entries"].append({
        "object": obj,
        "flow_vector": vector,
        "flow_records": records,
        "stack": _stack(frame),
    })
    return False


def threshold_map_entry(frame, _bp_loc, _dict):
    process = frame.GetThread().GetProcess()
    obj = _reg(frame, "rdi")
    descriptor = _descriptor(process, obj + 0x20)
    _state()["threshold_map_entries"].append({
        "object": obj,
        "flow_threshold_0x200": _f32(process, obj + 0x200),
        "descriptor": descriptor,
        "samples": _scalar_samples(process, descriptor),
        "stack": _stack(frame, 6),
    })
    _state()["terminated_after_samples"] = True
    process.Kill()
    return True


def threshold_map_build(frame, _bp_loc, _dict):
    state = _state()
    if state["threshold_map_builds"]:
        return False
    process = frame.GetThread().GetProcess()
    owner = _reg(frame, "r14")
    captured = _reg(frame, "rcx")
    rectangle_raw = _read(process, _reg(frame, "rdx"), 16)
    state["threshold_map_builds"].append({
        "owner": owner,
        "reference_camera_index_0xb8": _i32(process, owner + 0xB8),
        "captured_image": captured,
        "sensor_analog_gain_0x40": _f32(process, captured + 0x40),
        "mirror_position_0x50": _i32(process, captured + 0x50),
        "calibration_index_0x60": _i32(process, captured + 0x60),
        "input": _descriptor(process, _reg(frame, "rsi")),
        "output": _descriptor(process, _reg(frame, "rdi")),
        "rectangle": list(struct.unpack("<4f", rectangle_raw)) if rectangle_raw else None,
        "multiplier_xmm0": _xmm_f32(frame, "xmm0"),
        "inverse_r8": _reg(frame, "r8") & 0xFF,
        "stack": _stack(frame, 6),
    })
    return False


def flow_rejection_check(frame, _bp_loc, _dict):
    state = _state()
    if not state["_producer_active"] or len(state["flow_rejection_checks"]) >= 64:
        return False
    process = frame.GetThread().GetProcess()
    obj = _reg(frame, "rdi")
    map_owner = _u64(process, obj + 0x08)
    coordinates_raw = _read(process, _reg(frame, "rdx"), 8)
    width = _i32(process, map_owner + 0x30) if map_owner else None
    height = _i32(process, map_owner + 0x34) if map_owner else None
    stride = _i32(process, map_owner + 0x38) if map_owner else None
    data = _u64(process, map_owner + 0x40) if map_owner else None
    coordinates = list(struct.unpack("<2f", coordinates_raw)) if coordinates_raw else None
    sampled_pixel = None
    sampled_value = None
    if coordinates and width and height and stride and data:
        x = min(max(int(width * coordinates[0]), 0), width - 1)
        y = min(max(int(height * coordinates[1]), 0), height - 1)
        sampled_pixel = [x, y]
        sampled_value = _f32(process, data + (y * stride + x) * 4)
    state["flow_rejection_checks"].append({
        "coordinates": coordinates,
        "minimum_sad": _f32(process, _reg(frame, "rsi")),
        "threshold_multiplier": _f32(process, obj + 0x10),
        "map_size": [width, height],
        "map_stride": stride,
        "sampled_pixel": sampled_pixel,
        "sampled_value": sampled_value,
        "stack": _stack(frame, 4),
    })
    if len(state["flow_rejection_checks"]) >= 64:
        state["terminated_after_samples"] = True
        process.Kill()
        return True
    return False


def flow_use(frame, _bp_loc, _dict):
    state = _state()
    if len(state["flow_uses"]) >= 32:
        return False
    process = frame.GetThread().GetProcess()
    rbp = _reg(frame, "rbp")
    data = _reg(frame, "rcx")
    index = _reg(frame, "rdx")
    raw = _read(process, data + index * 4, 4)
    dx, dy = struct.unpack("<hh", raw) if raw else (None, None)
    grid_x = _reg(frame, "r13") & 0xFFFFFFFF
    if grid_x & 0x80000000:
        grid_x -= 0x100000000
    state["flow_uses"].append({
        "flow_data": data,
        "linear_index": index,
        "grid": [grid_x, _i32(process, rbp - 0x16C8)],
        "patch_base": [_i32(process, rbp - 0x16B0), _i32(process, rbp - 0x16C4)],
        "output_block_origin": [_reg(frame, "r14") & 0xFFFFFFFF, _i32(process, rbp - 0x16C0)],
        "flow": [dx, dy],
    })
    if len(state["flow_uses"]) >= 32 and state["producer_returns"] and state["worker_entries"]:
        state["terminated_after_samples"] = True
        process.Kill()
        return True
    return False


VARIANTS = {
    0x1939B0: "ComputeFlowField<u16,8,8,true>",
    0x1940A0: "ComputeFlowField<u16,8,4,true>",
    0x1952E0: "ComputeFlowField<u16,16,8,true>",
    0x196850: "ComputeFlowField<u16,16,4,true>",
    0x1978F0: "ComputeFlowFieldWithOverlap<u16,16,2,false>",
    0x198560: "ComputeFlowFieldWithOverlap<u16,16,1,false>",
}


INTERMEDIATE_STAGES = {
    0x19955E: ("initial_8x8_search_r8", -0x370),
    0x199840: ("refine_8x8_search_r4", -0x3A0),
    0x1998E9: ("refine_16x16_search_r8", -0x3D0),
    0x199995: ("refine_16x16_search_r4", -0x400),
    0x199AF0: ("overlap_16x16_search_r2", -0x430),
}


def intermediate_stage(frame, _bp_loc, _dict):
    state = _state()
    if not state["_producer_active"]:
        return False
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    base = None
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            break
    va = frame.GetPC() - base if base is not None else None
    if va not in INTERMEDIATE_STAGES:
        state["errors"].append(f"unknown intermediate stage VA {va}")
        return False
    name, rbp_offset = INTERMEDIATE_STAGES[va]
    if not state["pyramid_inputs"] and state["_dump_dir"]:
        reference = _descriptor_vector(process, _reg(frame, "r12"))
        source = _descriptor_vector(process, _reg(frame, "rbp") - 0x528)
        os.makedirs(state["_dump_dir"], exist_ok=True)
        for role, vector in (("reference", reference), ("source", source)):
            for index, item in enumerate(vector.get("records", [])):
                item["dump"] = _dump_u16_plane(
                    process,
                    item,
                    os.path.join(state["_dump_dir"], f"{role}_level{index}.u16le"),
                )
        state["pyramid_inputs"].append({"reference": reference, "source": source})
    descriptor = _descriptor(process, _reg(frame, "rbp") + rbp_offset)
    dump = None
    if state["_dump_dir"]:
        dump = _dump_f32x2_plane(
            process, descriptor, os.path.join(state["_dump_dir"], f"{name}.f32x2le")
        )
    state["intermediate_stages"].append({
        "va": va,
        "stage": name,
        "descriptor": descriptor,
        "flow": _float_flow_summary(process, descriptor),
        "dump": dump,
        "stack": _stack(frame, 4),
    })
    if state["_stop_after_stages"] and va == 0x199AF0:
        state["terminated_after_samples"] = True
        process.Kill()
        return True
    return False


def variant_hit(frame, _bp_loc, _dict):
    state = _state()
    if not state["_producer_active"]:
        return False
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    base = None
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            break
    va = frame.GetPC() - base if base is not None else None
    raw_rect = _read(process, _reg(frame, "rsi"), 16)
    obj = _reg(frame, "rdi")
    raw_object = _read(process, obj, 0x100)
    if any(item["va"] == va for item in state["variant_hits"]):
        return False
    operand_descriptors = {}
    for name, offset in (
        ("reference", 0x08),
        ("source", 0x10),
        ("previous_flow", 0x18),
        ("output", 0x30),
    ):
        pointer = _u64(process, obj + offset)
        descriptor = _descriptor(process, pointer) if pointer else {"read_ok": False}
        if state["_dump_dir"] and name in ("reference", "source"):
            safe_variant = VARIANTS.get(va, f"va_{va:x}").replace("<", "_").replace(">", "_").replace(",", "_")
            descriptor["dump"] = _dump_u16_plane(
                process,
                descriptor,
                os.path.join(state["_dump_dir"], f"{safe_variant}_{name}.u16le"),
            )
        operand_descriptors[name] = descriptor
    scale_pointer = _u64(process, obj + 0x20)
    packet = {
        "va": va,
        "variant": VARIANTS.get(va, "unknown"),
        "rectangle": list(struct.unpack("<4i", raw_rect)) if raw_rect else None,
        "worker_index_edx": _reg(frame, "rdx") & 0xFFFFFFFF,
        "object_sha256_0x100": hashlib.sha256(raw_object).hexdigest() if raw_object else None,
        "object_hex_0x100": raw_object.hex() if raw_object else None,
        "operands": operand_descriptors,
        "scale_pointer_0x20": scale_pointer,
        "scale_value": _i32(process, scale_pointer) if scale_pointer else None,
        "stack": _stack(frame),
    }
    state["variant_hits"].append(packet)
    if state["_stop_after_variant_operands"] and va == 0x1978F0:
        state["terminated_after_samples"] = True
        process.Kill()
        return True
    return False


def attach(debugger, ids):
    callbacks = {
        ids["producer_entry"]: "monofusion_flow_origin_probe.producer_entry",
        ids["producer_return"]: "monofusion_flow_origin_probe.producer_return",
        ids["vector_copy"]: "monofusion_flow_origin_probe.vector_copy",
        ids["worker_entry"]: "monofusion_flow_origin_probe.worker_entry",
        ids["flow_use"]: "monofusion_flow_origin_probe.flow_use",
    }
    for va in VARIANTS:
        callbacks[ids[f"variant_{va:x}"]] = "monofusion_flow_origin_probe.variant_hit"
    for va in INTERMEDIATE_STAGES:
        callbacks[ids[f"stage_{va:x}"]] = "monofusion_flow_origin_probe.intermediate_stage"
    target = debugger.GetSelectedTarget()
    for bp_id, callback in callbacks.items():
        bp = target.FindBreakpointByID(bp_id)
        if not bp or not bp.IsValid():
            _state()["errors"].append(f"invalid breakpoint {bp_id} for {callback}")
            continue
        bp.SetScriptCallbackFunction(callback)
        _state()["_breakpoint_ids"][callback] = bp_id
        if callback == "monofusion_flow_origin_probe.variant_hit":
            for va in VARIANTS:
                if ids[f"variant_{va:x}"] == bp_id:
                    _state()["_breakpoint_ids"][f"variant_{va:x}"] = bp_id


def attach_stages(debugger, ids):
    state = _state()
    state["_stop_after_stages"] = True
    callbacks = {ids["producer_entry"]: "monofusion_flow_origin_probe.producer_entry"}
    for va in INTERMEDIATE_STAGES:
        callbacks[ids[f"stage_{va:x}"]] = "monofusion_flow_origin_probe.intermediate_stage"
    target = debugger.GetSelectedTarget()
    for bp_id, callback in callbacks.items():
        bp = target.FindBreakpointByID(bp_id)
        if not bp or not bp.IsValid():
            state["errors"].append(f"invalid breakpoint {bp_id} for {callback}")
            continue
        bp.SetScriptCallbackFunction(callback)


def attach_variant_operands(debugger, ids):
    state = _state()
    state["_stop_after_variant_operands"] = True
    callbacks = {ids["producer_entry"]: "monofusion_flow_origin_probe.producer_entry"}
    for va in VARIANTS:
        callbacks[ids[f"variant_{va:x}"]] = "monofusion_flow_origin_probe.variant_hit"
    target = debugger.GetSelectedTarget()
    for bp_id, callback in callbacks.items():
        bp = target.FindBreakpointByID(bp_id)
        if not bp or not bp.IsValid():
            state["errors"].append(f"invalid breakpoint {bp_id} for {callback}")
            continue
        bp.SetScriptCallbackFunction(callback)


def set_dump_dir(path):
    _state()["_dump_dir"] = path


def attach_threshold_map(debugger, bp_id):
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id)
    if not bp or not bp.IsValid():
        _state()["errors"].append(f"invalid threshold-map breakpoint {bp_id}")
        return
    bp.SetScriptCallbackFunction("monofusion_flow_origin_probe.threshold_map_entry")


def attach_threshold_map_build(debugger, bp_id):
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id)
    if not bp or not bp.IsValid():
        _state()["errors"].append(f"invalid threshold-map-build breakpoint {bp_id}")
        return
    bp.SetScriptCallbackFunction("monofusion_flow_origin_probe.threshold_map_build")


def attach_flow_rejection_checks(debugger, callback_id, producer_id):
    target = debugger.GetSelectedTarget()
    callbacks = {
        callback_id: "monofusion_flow_origin_probe.flow_rejection_check",
        producer_id: "monofusion_flow_origin_probe.producer_entry",
    }
    for bp_id, callback in callbacks.items():
        bp = target.FindBreakpointByID(bp_id)
        if not bp or not bp.IsValid():
            _state()["errors"].append(f"invalid flow-rejection breakpoint {bp_id}")
            continue
        bp.SetScriptCallbackFunction(callback)


def attach_prediction(debugger, entry_id, return_id, producer_id):
    target = debugger.GetSelectedTarget()
    callbacks = {
        producer_id: "monofusion_flow_origin_probe.producer_entry",
        entry_id: "monofusion_flow_origin_probe.prediction_entry",
        return_id: "monofusion_flow_origin_probe.prediction_return",
    }
    for bp_id, callback in callbacks.items():
        bp = target.FindBreakpointByID(bp_id)
        if not bp or not bp.IsValid():
            _state()["errors"].append(f"invalid prediction breakpoint {bp_id}")
            continue
        bp.SetScriptCallbackFunction(callback)


def configure_prediction_targets(caller_va, targets):
    state = _state()
    state["_prediction_caller_va"] = caller_va
    state["_prediction_targets"] = [list(map(int, item)) for item in targets]


def attach_quadratic(debugger, entry_id, return_id):
    target = debugger.GetSelectedTarget()
    callbacks = {
        entry_id: "monofusion_flow_origin_probe.quadratic_entry",
        return_id: "monofusion_flow_origin_probe.quadratic_return",
    }
    for bp_id, callback in callbacks.items():
        bp = target.FindBreakpointByID(bp_id)
        if not bp or not bp.IsValid():
            _state()["errors"].append(f"invalid quadratic breakpoint {bp_id}")
            continue
        bp.SetScriptCallbackFunction(callback)


def write_report(path):
    state = _state()
    report = {key: value for key, value in state.items() if not key.startswith("_")}
    with open(path, "w", encoding="ascii") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("MONOFUSION_FLOW_ORIGIN_REPORT", path)
