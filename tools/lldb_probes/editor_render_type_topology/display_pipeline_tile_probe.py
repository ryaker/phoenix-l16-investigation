import builtins
import hashlib
import json
import struct


state = {"before": None, "after": None, "errors": []}


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    return bytes(data) if error.Success() and len(data) == size else None


def _descriptor(process, address, dump_path):
    raw = _read(process, address, 0x30)
    if raw is None:
        state["errors"].append(f"failed to read descriptor at {address:#x}")
        return None
    rect = struct.unpack_from("<4i", raw, 0)
    width, height, stride = struct.unpack_from("<3i", raw, 0x10)
    data = struct.unpack_from("<Q", raw, 0x20)[0]
    size = stride * height * 16
    packet = {
        "address": address,
        "rect": list(rect),
        "width": width,
        "height": height,
        "stride_pixels": stride,
        "data": data,
        "dump_size": size,
        "raw_hex": raw.hex(),
    }
    if size <= 0 or size > 100 * 1024 * 1024:
        state["errors"].append(f"implausible tile dump size {size}")
        return packet
    payload = _read(process, data, size)
    if payload is None:
        state["errors"].append(f"failed to read tile payload at {data:#x}")
        return packet
    with open(dump_path, "wb") as handle:
        handle.write(payload)
    packet["sha256"] = hashlib.sha256(payload).hexdigest()
    packet["dump_path"] = dump_path
    return packet


def _breakpoint_frame(debugger):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    for thread in process:
        if thread.GetStopReason() in (
            lldb.eStopReasonBreakpoint,
            lldb.eStopReasonPlanComplete,
            lldb.eStopReasonTrace,
        ):
            return thread.GetFrameAtIndex(0)
    return None


def capture_before(debugger, dump_path):
    frame = _breakpoint_frame(debugger)
    if frame is None:
        state["errors"].append("no stopped frame before 0x31b110")
        return
    descriptor = frame.FindRegister("rsi").GetValueAsUnsigned()
    state["before"] = {
        "pc_file_address": frame.GetPCAddress().GetFileAddress(),
        "adapter_rdi": frame.FindRegister("rdi").GetValueAsUnsigned(),
        "descriptor": _descriptor(frame.GetThread().GetProcess(), descriptor, dump_path),
    }


def capture_after(debugger, dump_path):
    frame = _breakpoint_frame(debugger)
    if frame is None:
        state["errors"].append("no stopped frame after 0x31b110")
        return
    descriptor = state["before"]["descriptor"]["address"] if state["before"] else 0
    state["after"] = {
        "pc_file_address": frame.GetPCAddress().GetFileAddress(),
        "descriptor": _descriptor(frame.GetThread().GetProcess(), descriptor, dump_path),
    }


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
