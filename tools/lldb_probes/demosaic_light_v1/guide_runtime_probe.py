import builtins
import json
import struct


def reset(report_path):
    builtins.l16_demosaic_guide = {
        "report_path": report_path,
        "captures": [],
        "errors": [],
    }


def _state():
    return builtins.l16_demosaic_guide


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


def _u64(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<Q", raw)[0] if raw is not None else 0


def _f32(process, address):
    raw = _read(process, address, 4)
    return struct.unpack("<f", raw)[0] if raw is not None else None


def _arm(target, load_address, thread_id):
    breakpoint = target.BreakpointCreateByAddress(load_address)
    breakpoint.SetIsHardware(True)
    breakpoint.SetThreadID(thread_id)
    return breakpoint.GetID()


def _disable(target, breakpoint_id):
    target.FindBreakpointByID(breakpoint_id).SetEnabled(False)


def capture_stencil(debugger, entry_breakpoint_id):
    target, process, thread, frame = _context(debugger)
    slide = frame.GetPC() - 0x2EC660
    rbp = _reg(frame, "rbp")
    index = _reg(frame, "rbx") * 4

    def values(registers=(), slots=()):
        pointers = [_reg(frame, name) for name in registers]
        pointers.extend(_u64(process, rbp - slot) for slot in slots)
        return [_f32(process, pointer + index) for pointer in pointers]

    _state()["captures"].append(
        {
            "stage": "stencil_2ec660",
            "thread_id": thread.GetThreadID(),
            "center": values(slots=(0x90,)),
            "axial1": values(("r11", "rdi"), (0x98, 0xA8)),
            "diagonal1": values(("r10", "rsi", "rcx", "r9")),
            "axial2": values(slots=(0xD0, 0xE8, 0xB0, 0xB8)),
            "knight": values(("r14", "r8", "r15", "r13"), (0xE0, 0xC8, 0xD8, 0xC0)),
        }
    )
    _disable(target, entry_breakpoint_id)
    _state()["stencil_out_bp"] = _arm(
        target, slide + 0x2EC746, thread.GetThreadID()
    )


def capture_stencil_output(debugger):
    target, process, thread, frame = _context(debugger)
    slide = frame.GetPC() - 0x2EC746
    _state()["captures"].append(
        {
            "stage": "stencil_output_2ec746",
            "thread_id": thread.GetThreadID(),
            "output": _xmm(frame, "xmm0")[0],
        }
    )
    _disable(target, _state()["stencil_out_bp"])
    _state()["stage2_in_bp"] = _arm(target, slide + 0x2ECA16, thread.GetThreadID())


def capture_stage2(debugger):
    target, process, thread, frame = _context(debugger)
    slide = frame.GetPC() - 0x2ECA16
    _state()["captures"].append(
        {
            "stage": "stage2_input_2eca16",
            "thread_id": thread.GetThreadID(),
            "far_s": _xmm(frame, "xmm3"),
            "mid_guide": _xmm(frame, "xmm2"),
            "center_s": _xmm(frame, "xmm1")[0],
            "epsilon": _xmm(frame, "xmm8")[0],
        }
    )
    _disable(target, _state()["stage2_in_bp"])
    _state()["stage2_out_bp"] = _arm(target, slide + 0x2ECA7A, thread.GetThreadID())


def capture_stage2_output(debugger):
    target, process, thread, frame = _context(debugger)
    slide = frame.GetPC() - 0x2ECA7A
    _state()["captures"].append(
        {
            "stage": "stage2_output_2eca7a",
            "thread_id": thread.GetThreadID(),
            "output": _xmm(frame, "xmm3")[0],
        }
    )
    _disable(target, _state()["stage2_out_bp"])
    _state()["stage3_in_bp"] = _arm(target, slide + 0x2ECD4F, thread.GetThreadID())


def capture_stage3(debugger):
    target, process, thread, frame = _context(debugger)
    slide = frame.GetPC() - 0x2ECD4F
    center_guide_address = _reg(frame, "rdi") + _reg(frame, "r9") * 4
    _state()["captures"].append(
        {
            "stage": "stage3_input_2ecd4f",
            "thread_id": thread.GetThreadID(),
            "far_s": _xmm(frame, "xmm2"),
            "far_guide": _xmm(frame, "xmm3"),
            "adjacent_guide": _xmm(frame, "xmm5"),
            "center_s": _xmm(frame, "xmm1")[0],
            "center_guide": _f32(process, center_guide_address),
            "epsilon": _xmm(frame, "xmm0")[0],
        }
    )
    _disable(target, _state()["stage3_in_bp"])
    _state()["stage3_out_bp"] = _arm(target, slide + 0x2ECDBC, thread.GetThreadID())


def capture_stage3_output(debugger):
    target, process, thread, frame = _context(debugger)
    _state()["captures"].append(
        {
            "stage": "stage3_output_2ecdbc",
            "thread_id": thread.GetThreadID(),
            "output": _xmm(frame, "xmm4")[0],
        }
    )
    _disable(target, _state()["stage3_out_bp"])


def report(debugger):
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    packet = {key: value for key, value in state.items() if key != "report_path"}
    packet["process"] = {
        "exit_status": process.GetExitStatus(),
        "exit_description": process.GetExitDescription(),
    }
    with open(state["report_path"], "w", encoding="utf-8") as handle:
        json.dump(packet, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("DEMOSAIC_GUIDE_REPORT " + state["report_path"])
