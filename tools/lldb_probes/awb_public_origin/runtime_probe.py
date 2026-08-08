import builtins
import json
import struct


def reset(label, report_path):
    builtins.l16_awb_origin = {
        "label": label,
        "report_path": report_path,
        "captures": [],
        "errors": [],
    }


def _state():
    return builtins.l16_awb_origin


def _context(debugger):
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    thread = process.GetSelectedThread()
    return target, process, thread, thread.GetSelectedFrame()


def _reg(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    error = builtins.__import__("lldb").SBError()
    raw = process.ReadMemory(address, size, error)
    if not error.Success() or len(raw) != size:
        _state()["errors"].append(f"read failed at 0x{address:x} size={size}")
        return None
    return raw


def _floats(process, address, count):
    raw = _read(process, address, 4 * count)
    return list(struct.unpack(f"<{count}f", raw)) if raw is not None else None


def _ints(process, address, count):
    raw = _read(process, address, 4 * count)
    return list(struct.unpack(f"<{count}i", raw)) if raw is not None else None


def capture_driver(debugger, entry_breakpoint_id):
    target, process, thread, frame = _context(debugger)
    slide = frame.GetPC() - 0x2EB560
    _state()["captures"].append(
        {
            "stage": "demosaic_driver_2eb560",
            "thread_id": thread.GetThreadID(),
            "phase": _ints(process, _reg(frame, "rdx"), 2),
            "reciprocal_gains": _floats(process, _reg(frame, "rcx"), 4),
        }
    )
    target.FindBreakpointByID(entry_breakpoint_id).SetEnabled(False)
    breakpoint = target.BreakpointCreateByAddress(slide + 0x3ECA61)
    breakpoint.SetIsHardware(True)
    _state()["post_square_breakpoint_id"] = breakpoint.GetID()


def capture_post_square(debugger):
    target, process, thread, frame = _context(debugger)
    rbp = _reg(frame, "rbp")
    _state()["captures"].append(
        {
            "stage": "post_square_3eca61",
            "thread_id": thread.GetThreadID(),
            "reciprocal_gains": _floats(process, rbp - 0xC0, 4),
        }
    )
    target.FindBreakpointByID(_state()["post_square_breakpoint_id"]).SetEnabled(False)


def report(debugger):
    state = _state()
    packet = {key: value for key, value in state.items() if key != "report_path"}
    with open(state["report_path"], "w", encoding="utf-8") as handle:
        json.dump(packet, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("AWB_PUBLIC_ORIGIN_REPORT " + state["report_path"])
