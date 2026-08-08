import builtins
import json
import struct


state = {
    "pre_breakpoint_id": None,
    "post_breakpoint_id": None,
    "pending": {},
    "sample": None,
    "pre_hits": 0,
    "post_hits": 0,
}


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    return bytes(data) if error.Success() else None


def _xmm_bytes(frame, name):
    data = frame.FindRegister(name).GetData()
    if not data.IsValid() or data.GetByteSize() < 16:
        return None
    error = builtins.__import__("lldb").SBError()
    raw = bytes(data.ReadRawData(error, 0, 16))
    return raw if error.Success() else None


def _disable(process, breakpoint_id):
    process.GetTarget().FindBreakpointByID(breakpoint_id).SetEnabled(False)


def capture_pre(frame, bp_loc, internal_dict):
    state["pre_hits"] += 1
    if state["sample"] is not None:
        return False

    thread = frame.GetThread()
    process = thread.GetProcess()
    thread_id = thread.GetThreadID()
    source_address = frame.FindRegister("rbx").GetValueAsUnsigned()
    destination_row = frame.FindRegister("rdi").GetValueAsUnsigned()
    pixel_index = frame.FindRegister("rax").GetValueAsUnsigned()
    destination_address = destination_row + pixel_index * 4
    source = _read(process, source_address, 16)
    scale = _xmm_bytes(frame, "xmm0")
    mxcsr = frame.FindRegister("mxcsr").GetValueAsUnsigned()
    if source is None or scale is None:
        return False

    state["pending"] = {
        "thread_id": thread_id,
        "source_address": source_address,
        "destination_address": destination_address,
        "pixel_index": pixel_index,
        "source_f32": list(struct.unpack("<4f", source)),
        "scale_f32": list(struct.unpack("<4f", scale)),
        "mxcsr": mxcsr,
        "destination_before_hex": (_read(process, destination_address, 4) or b"").hex(),
    }
    _disable(process, state["pre_breakpoint_id"])
    return False


def capture_post(frame, bp_loc, internal_dict):
    state["post_hits"] += 1
    if not state["pending"] or state["sample"] is not None:
        return False
    thread = frame.GetThread()
    if thread.GetThreadID() != state["pending"]["thread_id"]:
        return False

    process = thread.GetProcess()
    packet = dict(state["pending"])
    packet["destination_after_hex"] = (
        _read(process, packet["destination_address"], 4) or b""
    ).hex()
    state["sample"] = packet
    state["pending"] = {}
    _disable(process, state["post_breakpoint_id"])
    return False


def attach(debugger, pre_breakpoint_id, post_breakpoint_id):
    state["pre_breakpoint_id"] = pre_breakpoint_id
    state["post_breakpoint_id"] = post_breakpoint_id
    target = debugger.GetSelectedTarget()
    pre = target.FindBreakpointByID(pre_breakpoint_id)
    pre.SetScriptCallbackFunction(__name__ + ".capture_pre")
    pre.SetAutoContinue(True)
    post = target.FindBreakpointByID(post_breakpoint_id)
    post.SetScriptCallbackFunction(__name__ + ".capture_post")
    post.SetAutoContinue(True)


def write_report(debugger, path):
    process = debugger.GetSelectedTarget().GetProcess()
    packet = {
        "pre_hits": state["pre_hits"],
        "post_hits": state["post_hits"],
        "sample": state["sample"],
        "process": {
            "valid": process.IsValid(),
            "state": builtins.__import__("lldb").SBDebugger.StateAsCString(process.GetState()),
            "exit_status": process.GetExitStatus(),
        },
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(packet, handle, indent=2, sort_keys=True)
        handle.write("\n")

