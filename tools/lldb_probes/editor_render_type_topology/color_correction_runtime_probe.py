import builtins
import hashlib
import json
import os
import struct


state = {
    "errors": [],
    "breakpoint_ids": {},
    "gate": None,
    "entry": None,
    "first_conversion_call": None,
    "converter": None,
    "first_conversion_result": None,
    "correction_predicate": None,
    "correction_result": None,
    "auxiliary_gate": None,
}


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    return bytes(data) if error.Success() and len(data) == size else None


def _u64(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<Q", raw)[0] if raw else None


def _frame(process, expected_pc):
    lldb = builtins.__import__("lldb")
    for thread in process:
        if thread.GetStopReason() == lldb.eStopReasonBreakpoint:
            frame = thread.GetFrameAtIndex(0)
            if frame.GetPCAddress().GetFileAddress() == expected_pc:
                return frame
    state["errors"].append(f"did not stop at expected address {expected_pc:#x}")
    return None


def _libcp_base(target):
    for module in target.module_iter():
        if module.GetFileSpec().GetFilename() == "libcp.dylib":
            return module.GetObjectFileHeaderAddress().GetLoadAddress(target)
    return None


def _descriptor(process, address):
    raw = _read(process, address, 0x30)
    if raw is None:
        return None
    return {
        "address": address,
        "raw_hex": raw.hex(),
        "rect": list(struct.unpack_from("<4i", raw, 0)),
        "width": struct.unpack_from("<i", raw, 0x10)[0],
        "height": struct.unpack_from("<i", raw, 0x14)[0],
        "stride_pixels": struct.unpack_from("<i", raw, 0x18)[0],
        "channels_marker": struct.unpack_from("<i", raw, 0x1C)[0],
        "data": struct.unpack_from("<Q", raw, 0x20)[0],
        "owner": struct.unpack_from("<Q", raw, 0x28)[0],
    }


def _dump_image(process, descriptor_address, path):
    descriptor = _descriptor(process, descriptor_address)
    if descriptor is None:
        state["errors"].append(f"failed to read descriptor at {descriptor_address:#x}")
        return None
    size = descriptor["stride_pixels"] * descriptor["height"] * 16
    if size <= 0 or size > 100 * 1024 * 1024:
        state["errors"].append(f"implausible image size {size}")
        return descriptor
    payload = _read(process, descriptor["data"], size)
    if payload is None:
        state["errors"].append(f"failed to read image at {descriptor['data']:#x}")
        return descriptor
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as handle:
        handle.write(payload)
    descriptor.update(
        {
            "dump_path": path,
            "dump_size": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "first_pixel_f32": list(struct.unpack_from("<4f", payload, 0)),
        }
    )
    return descriptor


def _set_breakpoint(target, base, name, file_address):
    bp = target.BreakpointCreateByAddress(base + file_address)
    state["breakpoint_ids"][name] = bp.GetID()
    return bp


def _disable(target, name):
    bp_id = state["breakpoint_ids"].get(name)
    if bp_id is not None:
        target.FindBreakpointByID(bp_id).SetEnabled(False)


def arm(debugger, gate_id):
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    frame = _frame(process, 0x3BB867)
    if frame is None:
        return
    base = _libcp_base(target)
    if base is None:
        state["errors"].append("libcp base unavailable at display gate")
        return
    state["breakpoint_ids"]["gate"] = gate_id
    state["gate"] = {
        "adapter": frame.FindRegister("rdi").GetValueAsUnsigned(),
        "descriptor": frame.FindRegister("rsi").GetValueAsUnsigned(),
    }
    _disable(target, "gate")
    _set_breakpoint(target, base, "entry", 0x346FD0)


def capture_entry(debugger, output_dir):
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    frame = _frame(process, 0x346FD0)
    if frame is None:
        return
    base = _libcp_base(target)
    payload = frame.FindRegister("rdi").GetValueAsUnsigned()
    owner = _u64(process, payload)
    payload_raw = _read(process, payload, 0xD0)
    owner_raw = _read(process, owner, 0x200) if owner else None
    os.makedirs(output_dir, exist_ok=True)
    input_path = os.path.join(output_dir, "color_correction_input_f32.raw")
    main_descriptor = _dump_image(process, payload + 0x70, input_path)
    state["entry"] = {
        "pc_file_address": 0x346FD0,
        "payload": payload,
        "payload_raw_hex": payload_raw.hex() if payload_raw else None,
        "owner": owner,
        "owner_raw_hex": owner_raw.hex() if owner_raw else None,
        "main_descriptor": main_descriptor,
        "auxiliary_descriptor": _descriptor(process, payload + 0xA0),
        "correction_object": owner + 0x80 if owner else None,
        "correction_object_raw_hex": (
            (_read(process, owner + 0x80, 0x80) or b"").hex() if owner else None
        ),
    }
    _disable(target, "entry")
    for name, address in (
        ("first_conversion_call", 0x3470B9),
        ("first_conversion_result", 0x3470BE),
        ("correction_predicate", 0x3470CA),
        ("correction_result", 0x347130),
        ("auxiliary_gate", 0x3471C1),
    ):
        _set_breakpoint(target, base, name, address)


def capture_first_conversion_call(debugger):
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    frame = _frame(process, 0x3470B9)
    if frame is None:
        return
    base = _libcp_base(target)
    destination = frame.FindRegister("rdi").GetValueAsUnsigned()
    source = frame.FindRegister("rsi").GetValueAsUnsigned()
    input_config = frame.FindRegister("rdx").GetValueAsUnsigned()
    output_config = frame.FindRegister("rcx").GetValueAsUnsigned()
    state["first_conversion_call"] = {
        "pc_file_address": 0x3470B9,
        "destination": _descriptor(process, destination),
        "source": _descriptor(process, source),
        "input_config": input_config,
        "input_config_raw_hex": (
            (_read(process, input_config, 0x34) or b"").hex()
        ),
        "output_config": output_config,
        "output_config_raw_hex": (_read(process, output_config, 0x34) or b"").hex(),
        "flag_r8": frame.FindRegister("r8").GetValueAsUnsigned(),
    }
    _disable(target, "first_conversion_call")
    _set_breakpoint(target, base, "converter", 0xBF4A0)


def capture_converter(debugger):
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    frame = _frame(process, 0xBF4A0)
    if frame is None:
        return
    base = _libcp_base(target)
    callback = frame.FindRegister("rdi").GetValueAsUnsigned()
    callback_raw = _read(process, callback, 0x38)
    if callback_raw is None:
        state["errors"].append("failed to read converter callback")
        return
    selected_pointer = struct.unpack_from("<Q", callback_raw, 8)[0]
    selected_function = _u64(process, selected_pointer)
    adaptation_pointer = struct.unpack_from("<Q", callback_raw, 0x30)[0]
    adaptation = _read(process, adaptation_pointer, 9 * 4)
    state["converter"] = {
        "pc_file_address": 0xBF4A0,
        "callback": callback,
        "callback_raw_hex": callback_raw.hex(),
        "selected_pointer": selected_pointer,
        "selected_function": selected_function,
        "selected_function_file_address": selected_function - base,
        "destination": struct.unpack_from("<Q", callback_raw, 0x10)[0],
        "source": struct.unpack_from("<Q", callback_raw, 0x18)[0],
        "input_config": struct.unpack_from("<Q", callback_raw, 0x20)[0],
        "output_config": struct.unpack_from("<Q", callback_raw, 0x28)[0],
        "adaptation": adaptation_pointer,
        "adaptation_hex": adaptation.hex() if adaptation else None,
    }
    _disable(target, "converter")
    _set_breakpoint(target, base, "converter_identity_branch", 0xAC410)
    _set_breakpoint(target, base, "converter_matrix_branch", 0xAC600)


def capture_converter_branch(debugger):
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    lldb = builtins.__import__("lldb")
    frame = None
    pc = None
    for thread in process:
        if thread.GetStopReason() == lldb.eStopReasonBreakpoint:
            candidate = thread.GetFrameAtIndex(0)
            candidate_pc = candidate.GetPCAddress().GetFileAddress()
            if candidate_pc in (0xAC410, 0xAC600):
                frame = candidate
                pc = candidate_pc
                break
    if frame is None:
        state["errors"].append("did not stop at selected converter branch")
        return
    state["converter"]["branch_pc_file_address"] = pc
    if pc == 0xAC600:
        rbp = frame.FindRegister("rbp").GetValueAsUnsigned()
        rows = [_read(process, rbp - offset, 16) for offset in (0x90, 0xB0, 0xA0)]
        if any(row is None for row in rows):
            state["errors"].append("failed to capture converter matrix rows")
        else:
            state["converter"]["matrix_rows_hex"] = [row.hex() for row in rows]
            state["converter"]["matrix_rows_f32"] = [
                list(struct.unpack("<4f", row)) for row in rows
            ]
    _disable(target, "converter_identity_branch")
    _disable(target, "converter_matrix_branch")


def capture_first_conversion_result(debugger, output_dir):
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    frame = _frame(process, 0x3470BE)
    if frame is None or state["entry"] is None:
        return
    payload = state["entry"]["payload"]
    path = os.path.join(output_dir, "color_correction_after_convert_f32.raw")
    state["first_conversion_result"] = {
        "pc_file_address": 0x3470BE,
        "main_descriptor": _dump_image(process, payload + 0x70, path),
    }
    _disable(target, "first_conversion_result")


def capture_correction_predicate(debugger, output_dir):
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    frame = _frame(process, 0x3470CA)
    if frame is None or state["entry"] is None:
        return
    correction = state["entry"]["correction_object"]
    raw = _read(process, correction, 0x80)
    dimensions = list(struct.unpack_from("<3i", raw, 0)) if raw else None
    map_begin = struct.unpack_from("<Q", raw, 0x10)[0] if raw else 0
    map_end = struct.unpack_from("<Q", raw, 0x18)[0] if raw else 0
    map_payload = (
        _read(process, map_begin, map_end - map_begin)
        if map_begin and map_end >= map_begin
        else None
    )
    map_path = os.path.join(output_dir, "color_correction_hsv_map_vec4_f32.raw")
    if map_payload is not None:
        os.makedirs(output_dir, exist_ok=True)
        with open(map_path, "wb") as handle:
            handle.write(map_payload)
    state["correction_predicate"] = {
        "pc_file_address": 0x3470CA,
        "result_al": frame.FindRegister("rax").GetValueAsUnsigned() & 0xFF,
        "object": correction,
        "object_raw_hex": raw.hex() if raw else None,
        "dimensions_i32": dimensions,
        "map_begin": map_begin,
        "map_end": map_end,
        "map_capacity": struct.unpack_from("<Q", raw, 0x20)[0] if raw else 0,
        "map_path": map_path if map_payload is not None else None,
        "map_size": len(map_payload) if map_payload is not None else None,
        "map_vec4_count": len(map_payload) // 16 if map_payload is not None else None,
        "map_sha256": (
            hashlib.sha256(map_payload).hexdigest()
            if map_payload is not None
            else None
        ),
        "map_first_vec4_f32": (
            list(struct.unpack_from("<4f", map_payload, 0))
            if map_payload and len(map_payload) >= 16
            else None
        ),
        "map_last_vec4_f32": (
            list(struct.unpack_from("<4f", map_payload, len(map_payload) - 16))
            if map_payload and len(map_payload) >= 16
            else None
        ),
    }
    _disable(target, "correction_predicate")


def capture_correction_result(debugger, output_dir):
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    frame = _frame(process, 0x347130)
    if frame is None or state["entry"] is None:
        return
    payload = state["entry"]["payload"]
    path = os.path.join(output_dir, "color_correction_after_optional_f32.raw")
    state["correction_result"] = {
        "pc_file_address": 0x347130,
        "main_descriptor": _dump_image(process, payload + 0x70, path),
    }
    _disable(target, "correction_result")


def capture_auxiliary_gate(debugger):
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    frame = _frame(process, 0x3471C1)
    if frame is None or state["entry"] is None:
        return
    payload = state["entry"]["payload"]
    data_pointer = _u64(process, payload + 0xC0)
    state["auxiliary_gate"] = {
        "pc_file_address": 0x3471C1,
        "descriptor": _descriptor(process, payload + 0xA0),
        "data_pointer": data_pointer,
        "route_taken": bool(data_pointer),
    }
    _disable(target, "auxiliary_gate")


def write_report(debugger, path):
    process = debugger.GetSelectedTarget().GetProcess()
    packet = dict(state)
    packet["process"] = {
        "valid": process.IsValid(),
        "state": builtins.__import__("lldb").SBDebugger.StateAsCString(process.GetState()),
        "exit_status": process.GetExitStatus(),
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(packet, handle, indent=2, sort_keys=True)
        handle.write("\n")
