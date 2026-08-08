import json
import struct


state = {"breakpoint_id": None, "hits": 0, "samples": []}


def _u64(process, address):
    error = __import__("lldb").SBError()
    value = process.ReadUnsignedFromMemory(address, 8, error)
    return value if error.Success() else None


def _bytes(process, address, size):
    error = __import__("lldb").SBError()
    data = process.ReadMemory(address, size, error)
    return bytes(data) if error.Success() else b""


def hit(frame, bp_loc, internal_dict):
    global state
    state["hits"] += 1
    if state["samples"]:
        return False
    process = frame.GetThread().GetProcess()
    rax = frame.FindRegister("rax").GetValueAsUnsigned()
    rdi = frame.FindRegister("rdi").GetValueAsUnsigned()
    rsi = frame.FindRegister("rsi").GetValueAsUnsigned()
    edx = frame.FindRegister("edx").GetValueAsUnsigned() & 0xFFFFFFFF
    source = _bytes(process, rsi, 64)
    destination = _bytes(process, rdi, 16)
    sample = {
        "callable_pointer": rax,
        "target": _u64(process, rax),
        "destination": rdi,
        "source": rsi,
        "width": edx,
        "source_first_16_f32": list(struct.unpack("<16f", source)) if len(source) == 64 else [],
        "destination_first_16_hex_before": destination.hex(),
    }
    state["samples"].append(sample)
    target = process.GetTarget()
    target.FindBreakpointByID(state["breakpoint_id"]).SetEnabled(False)
    return False


def attach(debugger, breakpoint_id):
    state["breakpoint_id"] = breakpoint_id
    breakpoint = debugger.GetSelectedTarget().FindBreakpointByID(breakpoint_id)
    breakpoint.SetScriptCallbackFunction(__name__ + ".hit")
    breakpoint.SetAutoContinue(True)


def write_report(debugger, path):
    process = debugger.GetSelectedTarget().GetProcess()
    packet = dict(state)
    packet["process"] = {
        "valid": process.IsValid(),
        "state": __import__("lldb").SBDebugger.StateAsCString(process.GetState()),
        "exit_status": process.GetExitStatus(),
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(packet, handle, indent=2, sort_keys=True)
        handle.write("\n")
