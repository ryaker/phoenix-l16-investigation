import builtins
import hashlib
import json
import struct


state = {
    "hits": 0,
    "capture": None,
    "errors": [],
    "dump_path": None,
}


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    return bytes(data) if error.Success() and len(data) == size else None


def _i32(process, address):
    raw = _read(process, address, 4)
    return struct.unpack("<i", raw)[0] if raw else None


def _u64(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<Q", raw)[0] if raw else None


def _stack(thread, limit=12):
    rows = []
    for index in range(min(thread.GetNumFrames(), limit)):
        frame = thread.GetFrameAtIndex(index)
        rows.append(
            {
                "index": index,
                "module": frame.GetModule().GetFileSpec().GetFilename() or "",
                "file_address": frame.GetPCAddress().GetFileAddress(),
                "symbol": frame.GetFunctionName() or frame.GetDisplayFunctionName() or "",
            }
        )
    return rows


def _capture(frame):
    state["hits"] += 1
    if state["capture"] is not None:
        return
    process = frame.GetThread().GetProcess()
    descriptor = frame.FindRegister("rdi").GetValueAsUnsigned()
    width = _i32(process, descriptor + 0x10)
    height = _i32(process, descriptor + 0x14)
    stride_pixels = _i32(process, descriptor + 0x18)
    data = _u64(process, descriptor + 0x20)
    size = (stride_pixels or 0) * (height or 0) * 16
    packet = {
        "pc_file_address": frame.GetPCAddress().GetFileAddress(),
        "descriptor": descriptor,
        "width": width,
        "height": height,
        "stride_pixels": stride_pixels,
        "data": data,
        "dump_size": size,
        "stack": _stack(frame.GetThread()),
    }
    if not state["dump_path"]:
        state["errors"].append("dump path was not configured")
    elif size <= 0 or size > 100 * 1024 * 1024:
        state["errors"].append(f"implausible export float dump size {size}")
    else:
        payload = _read(process, data, size)
        if payload is None:
            state["errors"].append("failed to read export float image")
        else:
            with open(state["dump_path"], "wb") as handle:
                handle.write(payload)
            packet["sha256"] = hashlib.sha256(payload).hexdigest()
            packet["dump_path"] = state["dump_path"]
    state["capture"] = packet


def hit(frame, bp_loc, internal_dict):
    _capture(frame)
    return False


def attach(debugger, breakpoint_id, dump_path):
    state["dump_path"] = dump_path
    breakpoint = debugger.GetSelectedTarget().FindBreakpointByID(breakpoint_id)
    breakpoint.SetScriptCallbackFunction(__name__ + ".hit")
    breakpoint.SetAutoContinue(True)


def capture_stop(debugger, dump_path):
    lldb = builtins.__import__("lldb")
    state["dump_path"] = dump_path
    process = debugger.GetSelectedTarget().GetProcess()
    for thread in process:
        if thread.GetStopReason() == lldb.eStopReasonBreakpoint:
            _capture(thread.GetFrameAtIndex(0))
            return
    state["errors"].append("process did not stop on the export writer breakpoint")


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
