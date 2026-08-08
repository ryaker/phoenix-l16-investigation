import builtins
import hashlib
import json
import os
import struct


state = {
    "errors": [],
    "breakpoint_ids": {},
    "gate": None,
    "wrapper": None,
    "process": None,
    "worker": None,
    "intermediate": None,
    "converter": None,
    "post_conversion": None,
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
        "data": struct.unpack_from("<Q", raw, 0x20)[0],
        "owner": struct.unpack_from("<Q", raw, 0x28)[0],
    }


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
    wrapper = target.BreakpointCreateByAddress(base + 0x34AD50)
    state["breakpoint_ids"] = {"gate": gate_id, "wrapper": wrapper.GetID()}
    state["gate"] = {
        "descriptor": frame.FindRegister("rsi").GetValueAsUnsigned(),
        "adapter": frame.FindRegister("rdi").GetValueAsUnsigned(),
    }
    target.FindBreakpointByID(gate_id).SetEnabled(False)


def capture_wrapper(debugger):
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    frame = _frame(process, 0x34AD50)
    if frame is None:
        return
    callback = frame.FindRegister("rdi").GetValueAsUnsigned()
    payload = frame.FindRegister("rsi").GetValueAsUnsigned()
    owner = _u64(process, callback + 8)
    image_owner = _u64(process, payload)
    tmo = _u64(process, owner + 0x1668) if owner else None
    state["wrapper"] = {
        "callback": callback,
        "payload": payload,
        "pipeline_owner": owner,
        "image_owner": image_owner,
        "expected_destination": payload + 0x70,
        "expected_source": payload + 0x70,
        "expected_color_space": image_owner + 0x48 if image_owner else None,
        "tone_mapper": tmo,
    }
    target.FindBreakpointByID(state["breakpoint_ids"]["wrapper"]).SetEnabled(False)
    base = _libcp_base(target)
    process_bp = target.BreakpointCreateByAddress(base + 0x2D7780)
    state["breakpoint_ids"]["process"] = process_bp.GetID()


def capture_process(debugger, output_dir):
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    frame = _frame(process, 0x2D7780)
    if frame is None:
        return
    base = _libcp_base(target)
    tmo = frame.FindRegister("rdi").GetValueAsUnsigned()
    destination = frame.FindRegister("rsi").GetValueAsUnsigned()
    source = frame.FindRegister("rdx").GetValueAsUnsigned()
    color_space = frame.FindRegister("rcx").GetValueAsUnsigned()
    tmo_raw = _read(process, tmo, 0x18)
    color_raw = _read(process, color_space, 0x34)
    if tmo_raw is None or color_raw is None:
        state["errors"].append("failed to read ACRE object or color-space packet")
        return
    lut = struct.unpack_from("<Q", tmo_raw, 0x10)[0]
    lut_raw = _read(process, lut, 1025 * 4)
    if lut_raw is None:
        state["errors"].append("failed to read ACRE 1025-sample LUT")
        return
    os.makedirs(output_dir, exist_ok=True)
    lut_path = os.path.join(output_dir, "acre_lut_1025_f32.raw")
    with open(lut_path, "wb") as handle:
        handle.write(lut_raw)
    lut_values = struct.unpack("<1025f", lut_raw)
    state["process"] = {
        "tone_mapper": tmo,
        "tone_mapper_raw_hex": tmo_raw.hex(),
        "tone_mapper_vtable_file_address": (
            struct.unpack_from("<Q", tmo_raw, 0)[0] - base if base else None
        ),
        "ev_offset_f32": struct.unpack_from("<f", tmo_raw, 8)[0],
        "lut": lut,
        "lut_file_address": lut - base if base else None,
        "lut_path": lut_path,
        "lut_sha256": hashlib.sha256(lut_raw).hexdigest(),
        "lut_count": len(lut_values),
        "lut_first_f32": list(lut_values[:8]),
        "lut_last_f32": list(lut_values[-8:]),
        "destination": _descriptor(process, destination),
        "source": _descriptor(process, source),
        "color_space": color_space,
        "color_space_raw_hex": color_raw.hex(),
    }
    target.FindBreakpointByID(state["breakpoint_ids"]["process"]).SetEnabled(False)
    worker_bp = target.BreakpointCreateByAddress(base + 0x2D7A30)
    state["breakpoint_ids"]["worker"] = worker_bp.GetID()


def capture_worker(debugger):
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    frame = _frame(process, 0x2D7A30)
    if frame is None:
        return
    callback = frame.FindRegister("rdi").GetValueAsUnsigned()
    rectangle = frame.FindRegister("rsi").GetValueAsUnsigned()
    callback_raw = _read(process, callback, 0x28)
    rectangle_raw = _read(process, rectangle, 0x10)
    if callback_raw is None or rectangle_raw is None:
        state["errors"].append("failed to read ACRE callback or rectangle")
        return
    state["worker"] = {
        "callback": callback,
        "callback_raw_hex": callback_raw.hex(),
        "callback_vtable": struct.unpack_from("<Q", callback_raw, 0)[0],
        "source": struct.unpack_from("<Q", callback_raw, 8)[0],
        "destination": struct.unpack_from("<Q", callback_raw, 0x10)[0],
        "tone_mapper": struct.unpack_from("<Q", callback_raw, 0x18)[0],
        "color_space": struct.unpack_from("<Q", callback_raw, 0x20)[0],
        "rectangle": list(struct.unpack("<4i", rectangle_raw)),
        "worker_index_rdx": frame.FindRegister("rdx").GetValueAsUnsigned(),
    }
    target.FindBreakpointByID(state["breakpoint_ids"]["worker"]).SetEnabled(False)
    base = _libcp_base(target)
    intermediate_bp = target.BreakpointCreateByAddress(base + 0x2D7F60)
    state["breakpoint_ids"]["intermediate"] = intermediate_bp.GetID()


def capture_intermediate(debugger, output_dir):
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    frame = _frame(process, 0x2D7F60)
    if frame is None:
        return
    descriptor_address = frame.FindRegister("rbp").GetValueAsUnsigned() - 0x90
    descriptor = _descriptor(process, descriptor_address)
    rectangle = state["worker"]["rectangle"] if state["worker"] else None
    if descriptor is None or rectangle is None:
        state["errors"].append("failed to resolve ACRE intermediate descriptor")
        return
    x0, y0, x1, y1 = rectangle
    rows = []
    for y in range(y0, y1):
        address = descriptor["data"] + (y * descriptor["stride_pixels"] + x0) * 16
        row = _read(process, address, (x1 - x0) * 16)
        if row is None:
            state["errors"].append(f"failed to read ACRE intermediate row {y}")
            return
        rows.append(row)
    payload = b"".join(rows)
    os.makedirs(output_dir, exist_ok=True)
    dump_path = os.path.join(output_dir, "acre_intermediate_first_256x256_f32.raw")
    with open(dump_path, "wb") as handle:
        handle.write(payload)
    state["intermediate"] = {
        "pc_file_address": 0x2D7F60,
        "descriptor": descriptor,
        "rectangle": rectangle,
        "dump_path": dump_path,
        "dump_size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "first_pixel_f32": list(struct.unpack_from("<4f", payload, 0)),
    }
    target.FindBreakpointByID(
        state["breakpoint_ids"]["intermediate"]
    ).SetEnabled(False)
    base = _libcp_base(target)
    converter_bp = target.BreakpointCreateByAddress(base + 0xBF4A0)
    state["breakpoint_ids"]["converter"] = converter_bp.GetID()


def capture_converter(debugger):
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    frame = _frame(process, 0xBF4A0)
    if frame is None:
        return
    callback = frame.FindRegister("rdi").GetValueAsUnsigned()
    callback_raw = _read(process, callback, 0x38)
    if callback_raw is None:
        state["errors"].append("failed to capture color-converter callback")
        return
    selected_pointer = struct.unpack_from("<Q", callback_raw, 8)[0]
    selected_function = _u64(process, selected_pointer)
    base = _libcp_base(target)
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
        "destination_config": struct.unpack_from("<Q", callback_raw, 0x20)[0],
        "source_config": struct.unpack_from("<Q", callback_raw, 0x28)[0],
        "adaptation": adaptation_pointer,
        "adaptation_hex": adaptation.hex() if adaptation else None,
    }
    target.FindBreakpointByID(state["breakpoint_ids"]["converter"]).SetEnabled(False)
    branch_identity = target.BreakpointCreateByAddress(base + 0xAC410)
    branch_matrix = target.BreakpointCreateByAddress(base + 0xAC600)
    state["breakpoint_ids"]["converter_identity_branch"] = branch_identity.GetID()
    state["breakpoint_ids"]["converter_matrix_branch"] = branch_matrix.GetID()


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
            return
        state["converter"]["matrix_rows_hex"] = [row.hex() for row in rows]
        state["converter"]["matrix_rows_f32"] = [
            list(struct.unpack("<4f", row)) for row in rows
        ]
    for name in ("converter_identity_branch", "converter_matrix_branch"):
        target.FindBreakpointByID(state["breakpoint_ids"][name]).SetEnabled(False)
    base = _libcp_base(target)
    post_bp = target.BreakpointCreateByAddress(base + 0x2D8018)
    state["breakpoint_ids"]["post_conversion"] = post_bp.GetID()


def capture_post_conversion(debugger, output_dir):
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    frame = _frame(process, 0x2D8018)
    if frame is None:
        return
    descriptor_address = frame.FindRegister("rbp").GetValueAsUnsigned() - 0x90
    descriptor = _descriptor(process, descriptor_address)
    rectangle = state["worker"]["rectangle"] if state["worker"] else None
    if descriptor is None or rectangle is None:
        state["errors"].append("failed to resolve post-conversion descriptor")
        return
    x0, y0, x1, y1 = rectangle
    rows = []
    for y in range(y0, y1):
        address = descriptor["data"] + (y * descriptor["stride_pixels"] + x0) * 16
        row = _read(process, address, (x1 - x0) * 16)
        if row is None:
            state["errors"].append(f"failed to read post-conversion row {y}")
            return
        rows.append(row)
    payload = b"".join(rows)
    os.makedirs(output_dir, exist_ok=True)
    dump_path = os.path.join(output_dir, "acre_post_conversion_first_256x256_f32.raw")
    with open(dump_path, "wb") as handle:
        handle.write(payload)
    state["post_conversion"] = {
        "pc_file_address": 0x2D8018,
        "descriptor": descriptor,
        "rectangle": rectangle,
        "dump_path": dump_path,
        "dump_size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "first_pixel_f32": list(struct.unpack_from("<4f", payload, 0)),
    }
    target.FindBreakpointByID(
        state["breakpoint_ids"]["post_conversion"]
    ).SetEnabled(False)


def write_report(debugger, path):
    process = debugger.GetSelectedTarget().GetProcess()
    packet = dict(state)
    packet["process_exit"] = {
        "valid": process.IsValid(),
        "state": builtins.__import__("lldb").SBDebugger.StateAsCString(process.GetState()),
        "exit_status": process.GetExitStatus(),
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(packet, handle, indent=2, sort_keys=True)
        handle.write("\n")
