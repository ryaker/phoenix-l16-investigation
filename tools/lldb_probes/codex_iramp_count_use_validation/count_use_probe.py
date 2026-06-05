import builtins
import json
import struct


SITE_VA = 0x366A65
SITE_NAME = "count_use_366a65"


def reset(label="", sample_cap=16):
    builtins.l16_codex_iramp_count_use = {
        "label": label,
        "sample_cap": sample_cap,
        "breakpoint_id": None,
        "events": [],
        "errors": [],
        "count": 0,
        "disabled_after_cap": False,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
    }


def _state():
    if not hasattr(builtins, "l16_codex_iramp_count_use"):
        reset()
    return builtins.l16_codex_iramp_count_use


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _signed_u64(value):
    return value - 0x10000000000000000 if value & (1 << 63) else value


def _read(process, addr, size):
    if not addr:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u64(process, addr):
    data = _read(process, addr, 8)
    return struct.unpack_from("<Q", data, 0)[0] if data is not None else None


def _i32(process, addr):
    data = _read(process, addr, 4)
    return struct.unpack_from("<i", data, 0)[0] if data is not None else None


def _roi_i32x4(process, addr):
    if not addr:
        return None
    vals = [_i32(process, addr + i * 4) for i in range(4)]
    return vals if all(v is not None for v in vals) else None


def _libcp_base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                return base
    return None


def _module_va(target, pc):
    base = _libcp_base(target)
    if base is not None and pc >= base:
        return pc - base
    return None


def _stack(thread, max_frames=8):
    target = thread.GetProcess().GetTarget()
    frames = []
    for index in range(min(thread.GetNumFrames(), max_frames)):
        frame = thread.GetFrameAtIndex(index)
        frames.append(
            {
                "index": index,
                "pc": frame.GetPC(),
                "libcp_va": _module_va(target, frame.GetPC()),
                "function": frame.GetFunctionName(),
            }
        )
    return frames


def _packet(frame, process):
    regs = {name: _u(frame, name) for name in ("rax", "rbx", "rcx", "rsi", "r15", "rbp", "rsp")}
    closure = regs["r15"]
    vector_header_ptr = _u64(process, closure + 0x18)
    begin = _u64(process, vector_header_ptr) if vector_header_ptr is not None else None
    end = _u64(process, vector_header_ptr + 0x8) if vector_header_ptr is not None else None
    diff = end - begin if begin is not None and end is not None and end >= begin else None
    return {
        "registers": regs,
        "closure_r15": closure,
        "closure_plus_0x18_vector_header_ptr": vector_header_ptr,
        "vector_begin_from_header": begin,
        "vector_end_from_header": end,
        "vector_diff": diff,
        "computed_count_0x10": diff // 0x10 if diff is not None and diff % 0x10 == 0 else None,
        "rbx_after_sar_signed": _signed_u64(regs["rbx"]),
        "rax_begin_register": regs["rax"],
        "rcx_end_register": regs["rcx"],
        "roi_rsi_i32x4": _roi_i32x4(process, regs["rsi"]),
    }


def attach_existing(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    fallback = None
    fallback_count = 0
    for bp in target.breakpoint_iter():
        fallback = bp
        fallback_count += 1
        for loc in bp:
            if _module_va(target, loc.GetAddress().GetLoadAddress(target)) == SITE_VA:
                state["breakpoint_id"] = bp.GetID()
                print("L16_CODEX_COUNT_USE_ATTACHED", bp.GetID())
                return
    if fallback_count == 1 and fallback is not None:
        state["breakpoint_id"] = fallback.GetID()
        print("L16_CODEX_COUNT_USE_ATTACHED_FALLBACK", fallback.GetID())
        return
    state["errors"].append("breakpoint 0x366a65 not found")
    print("L16_CODEX_COUNT_USE_ATTACH_FAILED")


def _record_stop(thread):
    state = _state()
    process = thread.GetProcess()
    frame = thread.GetFrameAtIndex(0)
    state["count"] += 1
    if len(state["events"]) < state["sample_cap"]:
        state["events"].append(
            {
                "sequence": len(state["events"]) + 1,
                "thread_id": thread.GetThreadID(),
                "site_name": SITE_NAME,
                "site_va": SITE_VA,
                "packet": _packet(frame, process),
                "stack": _stack(thread),
            }
        )
    if len(state["events"]) >= state["sample_cap"] and state["breakpoint_id"] is not None:
        bp = process.GetTarget().FindBreakpointByID(state["breakpoint_id"])
        if bp.IsValid():
            bp.SetEnabled(False)
            state["disabled_after_cap"] = True


def drive_until_exit_or_step_cap(debugger, step_cap=60000):
    lldb = builtins.__import__("lldb")
    state = _state()
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    interpreter = debugger.GetCommandInterpreter()
    result = lldb.SBCommandReturnObject()

    steps = 0
    while process.IsValid() and process.GetState() != lldb.eStateExited and steps < step_cap:
        stopped = False
        for thread in process:
            if thread.GetStopReason() == lldb.eStopReasonBreakpoint:
                stopped = True
                _record_stop(thread)
        interpreter.HandleCommand("process continue", result)
        if not result.Succeeded():
            state["errors"].append(result.GetError() or result.GetOutput())
            break
        steps += 1
        if not stopped and process.GetState() != lldb.eStateStopped:
            continue

    state["drive_steps"] = steps
    state["drive_hit_step_cap"] = steps >= step_cap
    state["process"] = {
        "state": str(process.GetState()) if process.IsValid() else None,
        "exit_status": process.GetExitStatus() if process.IsValid() else None,
        "exit_description": process.GetExitDescription() if process.IsValid() else None,
    }


def write_report(debugger, path):
    state = _state()
    target = debugger.GetSelectedTarget()
    if state.get("breakpoint_id") is not None:
        bp = target.FindBreakpointByID(state["breakpoint_id"])
        if bp.IsValid():
            state["breakpoint_hit_count"] = bp.GetHitCount()
    with open(path, "w") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("L16_CODEX_COUNT_USE_REPORT", path)
