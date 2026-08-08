import builtins
import hashlib
import json
import os
import struct


state = {
    "descriptor": None,
    "adapter": None,
    "events": [],
    "errors": [],
    "breakpoint_ids": {},
    "output_dir": None,
}


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    return bytes(data) if error.Success() and len(data) == size else None


def _u64(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<Q", raw)[0] if raw else None


def _descriptor_snapshot(process, address, dump_path):
    raw = _read(process, address, 0x30)
    if raw is None:
        return None
    width, height, stride = struct.unpack_from("<3i", raw, 0x10)
    data = struct.unpack_from("<Q", raw, 0x20)[0]
    size = stride * height * 16
    packet = {
        "address": address,
        "rect": list(struct.unpack_from("<4i", raw, 0)),
        "width": width,
        "height": height,
        "stride_pixels": stride,
        "data": data,
        "dump_size": size,
    }
    if size <= 0 or size > 100 * 1024 * 1024:
        state["errors"].append(f"implausible stage image size {size}")
        return packet
    payload = _read(process, data, size)
    if payload is None:
        state["errors"].append(f"failed to read stage image at {data:#x}")
        return packet
    with open(dump_path, "wb") as handle:
        handle.write(payload)
    packet["sha256"] = hashlib.sha256(payload).hexdigest()
    packet["first_pixel_f32"] = list(struct.unpack_from("<4f", payload, 0))
    packet["dump_path"] = dump_path
    return packet


def _libcp_base(target):
    for module in target.module_iter():
        if module.GetFileSpec().GetFilename() == "libcp.dylib":
            return module.GetObjectFileHeaderAddress().GetLoadAddress(target)
    return None


def arm(debugger, gate_id, virtual_id, after_id, return_id, output_dir):
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    lldb = builtins.__import__("lldb")
    stopped = None
    for thread in process:
        if thread.GetStopReason() == lldb.eStopReasonBreakpoint:
            stopped = thread.GetFrameAtIndex(0)
            break
    if stopped is None or stopped.GetPCAddress().GetFileAddress() != 0x3BB867:
        state["errors"].append("did not stop at display 0x31b110 gate")
        return
    state["descriptor"] = stopped.FindRegister("rsi").GetValueAsUnsigned()
    state["adapter"] = stopped.FindRegister("rdi").GetValueAsUnsigned()
    state["breakpoint_ids"] = {
        "gate": gate_id,
        "virtual": virtual_id,
        "after": after_id,
        "return": return_id,
    }
    state["output_dir"] = output_dir
    os.makedirs(output_dir, exist_ok=True)
    target.FindBreakpointByID(gate_id).SetEnabled(False)
    target.FindBreakpointByID(virtual_id).SetEnabled(True)
    target.FindBreakpointByID(after_id).SetEnabled(True)
    target.FindBreakpointByID(return_id).SetEnabled(True)


def drive_to_return(debugger, step_cap=128):
    lldb = builtins.__import__("lldb")
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    base = _libcp_base(target)
    for _ in range(step_cap):
        error = process.Continue()
        if not error.Success():
            state["errors"].append(error.GetCString() or "continue failed")
            return
        frame = None
        for thread in process:
            if thread.GetStopReason() == lldb.eStopReasonBreakpoint:
                frame = thread.GetFrameAtIndex(0)
                break
        if frame is None:
            state["errors"].append("display pipeline exited without return breakpoint")
            return
        pc = frame.GetPCAddress().GetFileAddress()
        if pc == 0x3BB86C:
            state["return_pc_file_address"] = pc
            target.FindBreakpointByID(state["breakpoint_ids"]["virtual"]).SetEnabled(False)
            target.FindBreakpointByID(state["breakpoint_ids"]["after"]).SetEnabled(False)
            target.FindBreakpointByID(state["breakpoint_ids"]["return"]).SetEnabled(False)
            return
        if pc == 0x33FFD6:
            if not state["events"]:
                state["errors"].append("stage return without stage entry")
                return
            event = state["events"][-1]
            index = event["pipeline_vector_index_r15"]
            target_va = event["target_file_address"]
            payload = frame.FindRegister("rbp").GetValueAsUnsigned() - 0x180
            dump_path = os.path.join(
                state["output_dir"], f"display_stage_{index:02d}_{target_va:06x}.raw"
            )
            event["after_image"] = _descriptor_snapshot(
                process, payload + 0x70, dump_path
            )
            continue
        if pc != 0x33FFD4:
            state["errors"].append(f"unexpected stop at {pc:#x}")
            return
        callback = frame.FindRegister("rdi").GetValueAsUnsigned()
        vtable = _u64(process, callback)
        target_address = _u64(process, vtable + 0x30) if vtable else None
        owner = _u64(process, callback + 0x8)
        tone_mapper = _u64(process, owner + 0x1668) if owner else None
        tone_vtable = _u64(process, tone_mapper) if tone_mapper else None
        state["events"].append(
            {
                "sequence": len(state["events"]),
                "pipeline_vector_index_r15": frame.FindRegister("r15").GetValueAsUnsigned(),
                "record_rbx": frame.FindRegister("rbx").GetValueAsUnsigned(),
                "callback_rdi": callback,
                "vtable": vtable,
                "vtable_file_address": vtable - base if vtable and base else None,
                "target": target_address,
                "target_file_address": (
                    target_address - base if target_address and base else None
                ),
                "pipeline_owner": owner,
                "pipeline_fields_0x1600_hex": (
                    (_read(process, owner + 0x1600, 0x80) or b"").hex()
                    if owner else None
                ),
                "tone_mapper": tone_mapper,
                "tone_mapper_vtable": tone_vtable,
                "tone_mapper_vtable_file_address": (
                    tone_vtable - base if tone_vtable and base else None
                ),
                "tone_mapper_object_hex": (
                    (_read(process, tone_mapper, 0x100) or b"").hex()
                    if tone_mapper else None
                ),
            }
        )
    state["errors"].append(f"display pipeline exceeded step cap {step_cap}")


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
