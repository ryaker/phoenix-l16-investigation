"""Capture one scalar-true cross-talk helper packet and output tile."""

import builtins
import hashlib
import json
import os
import struct


CALLBACK_ENTRY = 0x1054D0
HELPER_ENTRY = 0x1019D0
HELPER_RETURN = 0x106C58
LOOP_ENTRY = 0x1026E0
CANDIDATES_READY = 0x1028B0
LIMITER_READY = 0x102906
STORES_COMPLETE = 0x102992
TRACE_SITES = (LOOP_ENTRY, CANDIDATES_READY, LIMITER_READY, STORES_COMPLETE)
TRACE_POINTS = {
    (0, 0), (0, 2), (0, 4), (0, 194),
}
TRACE_TERMINAL_POINT = (0, 194)


def reset(label="", output_dir="", target_helper_index=0):
    builtins.l16_crosstalk_formula = {
        "label": label,
        "output_dir": output_dir,
        "target_helper_index": int(target_helper_index),
        "eligible_helper_count": 0,
        "selected_helper_index": None,
        "active_thread": None,
        "callback_objects": {},
        "callback_object": None,
        "helper": None,
        "trace": [],
        "trace_breakpoints": [],
        "complete": False,
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_crosstalk_formula"):
        reset()
    return builtins.l16_crosstalk_formula


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
    if not address or size <= 0:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    return data if error.Success() and len(data) == size else None


def _u64(process, address):
    data = _read(process, address, 8)
    return struct.unpack("<Q", data)[0] if data is not None else None


def _i64(process, address):
    data = _read(process, address, 8)
    return struct.unpack("<q", data)[0] if data is not None else None


def _xmm_f32(frame, name):
    data = frame.FindRegister(name).GetData()
    error = builtins.__import__("lldb").SBError()
    result = []
    for index in range(4):
        value = data.GetFloat(error, index * 4) if data.IsValid() else None
        result.append(value if value is not None and error.Success() else None)
    return result


def _float_window(process, address, center_index, radius=2):
    start_index = center_index - radius
    data = _read(process, address + 4 * start_index, (2 * radius + 1) * 4)
    if data is None:
        return None
    return {
        "start_index": start_index,
        "f32": list(struct.unpack(f"<{2 * radius + 1}f", data)),
    }


def _install_trace_breakpoints(target, base, thread_id):
    state = _state()
    for site in TRACE_SITES:
        bp = target.BreakpointCreateByAddress(base + site)
        bp.SetThreadID(thread_id)
        bp.SetScriptCallbackFunction("crosstalk_scalar_formula_probe.hit")
        state["trace_breakpoints"].append(bp.GetID())


def _descriptor(process, address):
    data = _read(process, address, 0x30)
    if data is None:
        return None
    words = struct.unpack("<8iQQ", data)
    result = {
        "address": address,
        "origin": list(words[0:2]),
        "bounds": list(words[2:4]),
        "size": list(words[4:6]),
        "stride": words[6],
        "reserved": words[7],
        "data": words[8],
        "allocation": words[9],
        "raw": data.hex(),
    }
    if not (
        0 < result["size"][0] <= 16384
        and 0 < result["size"][1] <= 16384
        and result["stride"] >= result["size"][0]
        and result["data"] > 0x10000
    ):
        return None
    return result


def _dump(process, address, size, name):
    state = _state()
    data = _read(process, address, size)
    if data is None:
        state["errors"].append(f"unable to read {name} at {address:#x} size={size}")
        return None
    path = os.path.join(state["output_dir"], name)
    with open(path, "wb") as handle:
        handle.write(data)
    return {"path": path, "bytes": size, "sha256": hashlib.sha256(data).hexdigest()}


def _dump_descriptor(process, descriptor, name):
    if descriptor is None:
        return None
    byte_count = descriptor["stride"] * descriptor["size"][1] * 4
    artifact = _dump(process, descriptor["data"], byte_count, name)
    return {"descriptor": descriptor, "artifact": artifact}


def hit(frame, _bp_loc, _internal_dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    base = _base(target)
    site = frame.GetPC() - base if base is not None else None
    thread_id = thread.GetThreadID()

    if state["complete"]:
        return False

    if (
        site in TRACE_SITES
        and state["helper"] is not None
        and thread_id == state["active_thread"]
    ):
        rbp = _u(frame, "rbp")
        lane_index = _u(frame, "r11")
        row_index = _i64(process, rbp - 0x180)
        if site == LOOP_ENTRY and row_index is not None and row_index > max(y for y, _ in TRACE_POINTS):
            for breakpoint_id in state["trace_breakpoints"]:
                target.FindBreakpointByID(breakpoint_id).SetEnabled(False)
            return False
        if (row_index, lane_index) in TRACE_POINTS:
            registers = {
                name: _u(frame, name)
                for name in (
                    "rax", "rbx", "rcx", "rdx", "rsi", "rdi", "r8", "r9",
                    "r10", "r11", "r12", "r13", "r14", "r15", "rbp", "rsp",
                )
            }
            pointer_windows = {}
            for name in ("rbx", "rcx", "rdx", "rsi", "rdi", "r8", "r9", "r15"):
                pointer_windows[name] = _float_window(
                    process, registers[name], lane_index, radius=3
                )
            stack_f32 = _read(process, rbp - 0x1d8, 0x1b0)
            event = {
                "site": site,
                "row_index": row_index,
                "lane_index": lane_index,
                "registers": registers,
                "xmm_f32": {
                    f"xmm{index}": _xmm_f32(frame, f"xmm{index}")
                    for index in range(16)
                },
                "pointer_windows": pointer_windows,
                "stack_f32_hex": stack_f32.hex() if stack_f32 is not None else None,
                "limit_packet_f32": (
                    list(struct.unpack("<4f", _read(process, registers["r12"], 16)))
                    if _read(process, registers["r12"], 16) is not None
                    else None
                ),
            }
            state["trace"].append(event)
            if site == STORES_COMPLETE and (row_index, lane_index) == TRACE_TERMINAL_POINT:
                for breakpoint_id in state["trace_breakpoints"]:
                    target.FindBreakpointByID(breakpoint_id).SetEnabled(False)
        return False

    if site == CALLBACK_ENTRY:
        address = _u(frame, "rdi")
        raw = _read(process, address, 0x70)
        pointers = {}
        if raw is not None:
            for offset in range(8, 0x70, 8):
                pointer = struct.unpack_from("<Q", raw, offset)[0]
                sample = _read(process, pointer, 0x100) if pointer else None
                pointers[hex(offset)] = {
                    "pointer": pointer,
                    "sample_hex": sample.hex() if sample is not None else None,
                }
        state["callback_objects"][str(thread_id)] = {
            "address": address,
            "raw": raw.hex() if raw is not None else None,
            "pointers": pointers,
        }
        return False

    if site == HELPER_ENTRY and state["helper"] is None:
        start_raw = _read(process, _u(frame, "rdx"), 8)
        end_raw = _read(process, _u(frame, "rcx"), 8)
        if start_raw is None or end_raw is None:
            return False
        start = struct.unpack("<2i", start_raw)
        end = struct.unpack("<2i", end_raw)
        if end[0] - start[0] < 256 or end[1] - start[1] < 256:
            return False
        helper_index = state["eligible_helper_count"]
        state["eligible_helper_count"] += 1
        if helper_index != state["target_helper_index"]:
            return False
        state["active_thread"] = thread_id
        state["selected_helper_index"] = helper_index
        state["callback_object"] = state["callback_objects"].get(str(thread_id))
        callback_address = (
            state["callback_object"]["address"] if state["callback_object"] else None
        )
        grid_a = None
        grid_b = None
        channel_vector = None
        if callback_address:
            grid_a_address = _u64(process, callback_address + 0x28)
            grid_b_holder = _u64(process, callback_address + 0x30)
            grid_b_shape = _u64(process, callback_address + 0x38)
            if grid_a_address:
                width_data = _read(process, grid_a_address, 8)
                data_address = _u64(process, grid_a_address + 8)
                if width_data and data_address:
                    width, height = struct.unpack("<2i", width_data)
                    grid_a = {
                        "width": width,
                        "height": height,
                        "artifact": _dump(
                            process,
                            data_address,
                            width * height * 0x40,
                            "callback_grid_a_f32.bin",
                        ),
                    }
            if grid_b_holder and grid_b_shape:
                data_address = _u64(process, grid_b_holder)
                width = struct.unpack("<i", _read(process, grid_b_shape, 4))[0]
                height = 13
                if data_address and width == 17:
                    grid_b = {
                        "width": width,
                        "height": height,
                        "artifact": _dump(
                            process,
                            data_address,
                            width * height * 0x40,
                            "callback_grid_b_f32.bin",
                        ),
                    }
            vector_address = _u64(process, callback_address + 0x20)
            vector_data = _read(process, vector_address, 16) if vector_address else None
            if vector_data:
                channel_vector = list(struct.unpack("<4f", vector_data))
        rsp = _u(frame, "rsp")
        source = _descriptor(process, _u(frame, "rdi"))
        destination = _descriptor(process, _u(frame, "rsi"))
        stack_arguments = [_u64(process, rsp + offset) for offset in (8, 0x10, 0x18)]
        helper = {
            "registers": {
                name: _u(frame, name)
                for name in ("rdi", "rsi", "rdx", "rcx", "r8", "r9", "rsp")
            },
            "start_i32": list(start),
            "end_i32": list(end),
            "coordinate_offset_f32": (
                (_read(process, _u(frame, "r8"), 8) or b"").hex()
            ),
            "coordinate_scale_f32": (
                (_read(process, _u(frame, "r9"), 8) or b"").hex()
            ),
            "stack_arguments": stack_arguments,
            "callback_grid_a": grid_a,
            "callback_grid_b": grid_b,
            "callback_channel_vector_f32": channel_vector,
            "parity_i32": (
                (_read(process, stack_arguments[0], 32) or b"").hex()
                if stack_arguments[0]
                else None
            ),
            "matrices_artifact": _dump(
                process, stack_arguments[1], 0x100, "prepared_matrices.bin"
            ),
            "blend_limit_artifact": _dump(
                process, stack_arguments[2], 16, "blend_limit.bin"
            ),
            "source_before": _dump_descriptor(process, source, "source_before_f32.bin"),
            "destination_before": _dump_descriptor(
                process, destination, "destination_before_f32.bin"
            ),
        }
        state["helper"] = helper
        _install_trace_breakpoints(target, base, thread_id)
        return False

    if (
        site == HELPER_RETURN
        and state["helper"] is not None
        and thread_id == state["active_thread"]
    ):
        destination = _descriptor(process, state["helper"]["registers"]["rsi"])
        state["helper"]["destination_after"] = _dump_descriptor(
            process, destination, "destination_after_f32.bin"
        )
        state["complete"] = True
        write_report(os.path.join(state["output_dir"], "report.json"))
        error = process.Kill()
        if not error.Success():
            state["errors"].append(f"kill after capture failed: {error.GetCString()}")
        return False

    return False


def install(debugger):
    target = debugger.GetSelectedTarget()
    base = _base(target)
    if base is None:
        raise RuntimeError("libcp.dylib is not loaded")
    for site in (CALLBACK_ENTRY, HELPER_ENTRY, HELPER_RETURN):
        bp = target.BreakpointCreateByAddress(base + site)
        bp.SetScriptCallbackFunction("crosstalk_scalar_formula_probe.hit")


def write_report(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="ascii") as handle:
        json.dump(_state(), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_CROSSTALK_FORMULA_REPORT", path)


def assert_complete():
    state = _state()
    if state["errors"] or not state["complete"]:
        raise RuntimeError(f"capture failed: complete={state['complete']} errors={state['errors']}")
    print("L16_CROSSTALK_FORMULA_OK", state["label"])
