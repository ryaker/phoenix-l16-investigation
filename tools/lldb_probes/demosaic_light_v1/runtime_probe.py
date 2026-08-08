import builtins
import json
import struct


def reset(label, report_path):
    builtins.l16_demosaic_v1 = {
        "label": label,
        "report_path": report_path,
        "captures": [],
        "errors": [],
    }


def _state():
    return builtins.l16_demosaic_v1


def _context(debugger):
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    thread = process.GetSelectedThread()
    return target, process, thread, thread.GetSelectedFrame()


def _reg(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _xmm(frame, name):
    data = frame.FindRegister(name).GetData()
    error = builtins.__import__("lldb").SBError()
    values = []
    for offset in range(0, 16, 4):
        value = data.GetFloat(error, offset)
        values.append(value if error.Success() else None)
    return values


def _read(process, address, size):
    error = builtins.__import__("lldb").SBError()
    raw = process.ReadMemory(address, size, error)
    if not error.Success() or len(raw) != size:
        _state()["errors"].append(f"read failed at 0x{address:x} size={size}")
        return None
    return raw


def _f32(process, address):
    raw = _read(process, address, 4)
    return struct.unpack("<f", raw)[0] if raw is not None else None


def _pointer(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<Q", raw)[0] if raw is not None else 0


def _sample3(process, base, byte_offset):
    return [
        _f32(process, base + byte_offset - 4),
        _f32(process, base + byte_offset),
        _f32(process, base + byte_offset + 4),
    ]


def _window(process, base, byte_offset):
    return [
        _f32(process, base + byte_offset + delta)
        for delta in (-4, 0, 4, 8, 12)
    ]


def _floats(process, address, count):
    raw = _read(process, address, 4 * count)
    return list(struct.unpack(f"<{count}f", raw)) if raw is not None else None


def _arm(target, load_address, thread_id):
    breakpoint = target.BreakpointCreateByAddress(load_address)
    breakpoint.SetIsHardware(True)
    breakpoint.SetThreadID(thread_id)
    return breakpoint.GetID()


def capture_entry(debugger, entry_breakpoint_id):
    target, process, thread, frame = _context(debugger)
    pc = frame.GetPC()
    slide = pc - 0x2EEF80
    byte_offset = _reg(frame, "rcx")
    rbp = _reg(frame, "rbp")
    pointers = {
        "A0": _pointer(process, rbp - 0x248),
        "A1": _reg(frame, "r10"),
        "A2": _reg(frame, "r8"),
        "A3": _pointer(process, rbp - 0x258),
        "B0": _pointer(process, rbp - 0x250),
        "B1": _reg(frame, "r11"),
        "B2": _reg(frame, "rdi"),
        "B3": _reg(frame, "r14"),
    }
    packet = {
        "stage": "entry_2eef80",
        "pc": pc,
        "thread_id": thread.GetThreadID(),
        "byte_offset": byte_offset,
        "epsilon": _xmm(frame, "xmm9")[0],
        "pointers": pointers,
        "samples": {
            name: _sample3(process, pointer, byte_offset)
            for name, pointer in pointers.items()
        },
        "windows": {
            name: _window(process, pointer, byte_offset)
            for name, pointer in pointers.items()
        },
    }
    _state()["captures"].append(packet)
    target.FindBreakpointByID(entry_breakpoint_id).SetEnabled(False)
    _state()["preadd_breakpoint_id"] = _arm(
        target, slide + 0x2EF04D, thread.GetThreadID()
    )


def capture_preadd(debugger):
    target, process, thread, frame = _context(debugger)
    packet = {
        "stage": "preadd_2ef04d",
        "pc": frame.GetPC(),
        "thread_id": thread.GetThreadID(),
        "xmm1": _xmm(frame, "xmm1"),
        "xmm2": _xmm(frame, "xmm2"),
        "xmm3": _xmm(frame, "xmm3"),
    }
    _state()["captures"].append(packet)
    target.FindBreakpointByID(_state()["preadd_breakpoint_id"]).SetEnabled(False)
    slide = frame.GetPC() - 0x2EF04D
    _state()["final_breakpoint_id"] = _arm(
        target, slide + 0x2EF05E, thread.GetThreadID()
    )


def capture_final(debugger):
    target, process, thread, frame = _context(debugger)
    packet = {
        "stage": "final_2ef05e",
        "pc": frame.GetPC(),
        "thread_id": thread.GetThreadID(),
        "xmm1": _xmm(frame, "xmm1"),
        "xmm2": _xmm(frame, "xmm2"),
        "xmm3": _xmm(frame, "xmm3"),
    }
    _state()["captures"].append(packet)
    target.FindBreakpointByID(_state()["final_breakpoint_id"]).SetEnabled(False)
    slide = frame.GetPC() - 0x2EF05E
    _state()["quad_breakpoint_id"] = _arm(
        target, slide + 0x2EF480, thread.GetThreadID()
    )


def capture_quad(debugger):
    target, process, thread, frame = _context(debugger)
    output_index = _reg(frame, "r13")
    row0 = _reg(frame, "r9") + output_index * 4
    row1 = _reg(frame, "r15") + output_index * 4
    packet = {
        "stage": "quad_2ef480",
        "pc": frame.GetPC(),
        "thread_id": thread.GetThreadID(),
        "output_index": output_index,
        "row0_rgba2": _floats(process, row0, 8),
        "row1_rgba2": _floats(process, row1, 8),
    }
    _state()["captures"].append(packet)
    target.FindBreakpointByID(_state()["quad_breakpoint_id"]).SetEnabled(False)


def report(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    packet = {key: value for key, value in state.items() if key != "report_path"}
    packet["process"] = {
        "exit_status": process.GetExitStatus(),
        "exit_description": process.GetExitDescription(),
    }
    with open(state["report_path"], "w", encoding="utf-8") as handle:
        json.dump(packet, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("DEMOSAIC_V1_REPORT " + state["report_path"])
