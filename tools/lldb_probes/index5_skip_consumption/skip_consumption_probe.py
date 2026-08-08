"""Trace active and skipped index-5 pixels through local cost and final argmin."""

import builtins
import json
import struct

import lldb


SITES = {
    0x276860: "runpass_entry",
    0x277522: "mask_branch",
    0x277567: "local_ready",
}


def reset(label, source_lri):
    builtins.l16_skip_consumption = {
        "label": label,
        "source_lri": source_lri,
        "pixels": {},
        "errors": [],
        "capture_complete": False,
    }


def _state():
    return builtins.l16_skip_consumption


def _read(process, address, size):
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    if not error.Success() or len(data) != size:
        raise RuntimeError(f"read {size} at 0x{address:x}: {error}")
    return data


def _u8(process, address):
    return _read(process, address, 1)[0]


def _u16(process, address):
    return struct.unpack("<H", _read(process, address, 2))[0]


def _u32(process, address):
    return struct.unpack("<I", _read(process, address, 4))[0]


def _u64(process, address):
    return struct.unpack("<Q", _read(process, address, 8))[0]


def _u16s(process, address, count):
    return list(struct.unpack(f"<{count}H", _read(process, address, count * 2)))


def _slide(frame):
    target = frame.GetThread().GetProcess().GetTarget()
    module = target.FindModule(lldb.SBFileSpec("libcp.dylib"))
    return module.GetObjectFileHeaderAddress().GetLoadAddress(target)


def _register(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _context_key(frame):
    return f"{frame.GetThread().GetThreadID()}:{_register(frame, 'rbp')}"


def on_breakpoint(frame, _bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    site = SITES.get(frame.GetPCAddress().GetLoadAddress(target) - _slide(frame))
    if site is None:
        return False
    try:
        if site == "runpass_entry":
            obj = _register(frame, "rdi")
            if _u32(process, obj + 0x08) != 5 or _u32(process, obj + 0x0C) != 8:
                return False
            target = process.GetTarget()
            thread_id = frame.GetThread().GetThreadID()
            branch = target.BreakpointCreateByAddress(_slide(frame) + 0x277522)
            local = target.BreakpointCreateByAddress(_slide(frame) + 0x277567)
            for breakpoint in (branch, local):
                breakpoint.SetThreadID(thread_id)
                breakpoint.SetScriptCallbackFunction(
                    "skip_consumption_probe.on_breakpoint"
                )
            _bp_loc.GetBreakpoint().SetEnabled(False)
            state["target"] = obj
            state["worker_thread_id"] = thread_id
            return False

        if site == "mask_branch":
            obj = _register(frame, "r14")
            if _u32(process, obj + 0x08) != 5 or _u32(process, obj + 0x0C) != 8:
                return False
            rbp = _register(frame, "rbp")
            x = _register(frame, "r8") & 0xFFFFFFFF
            y = _u32(process, rbp - 0x248)
            mask_address = _register(frame, "rsi") + _register(frame, "rax")
            mask = _u8(process, mask_address)
            polarity = "computed" if mask == 0 else "skipped"
            if polarity in state["pixels"]:
                return False
            pixel = {
                "polarity": polarity,
                "mask": mask,
                "x": x,
                "y": y,
                "target": obj,
                "thread_id": frame.GetThread().GetThreadID(),
                "rbp": rbp,
            }
            state["pixels"][polarity] = pixel
            state.setdefault("contexts", {})[_context_key(frame)] = polarity
            if set(state["pixels"]) == {"computed", "skipped"}:
                _bp_loc.GetBreakpoint().SetEnabled(False)
            return False

        if site == "local_ready":
            polarity = state.get("contexts", {}).get(_context_key(frame))
            if polarity is None:
                return False
            pixel = state["pixels"][polarity]
            if "local_ready" in pixel:
                return False
            rbp = _register(frame, "rbp")
            count = _u16(process, rbp - 0x17A)
            temp = _u64(process, rbp - 0x2E0)
            pixel["count"] = count
            pixel["temp"] = temp
            pixel["local_ready"] = _u16s(process, temp, min(count, 32))
            if (
                set(state["pixels"]) == {"computed", "skipped"}
                and all("local_ready" in item for item in state["pixels"].values())
            ):
                _bp_loc.GetBreakpoint().SetEnabled(False)
                state["capture_complete"] = True
                process.Kill()
    except Exception as exc:
        state["errors"].append(f"{site}: {exc}")
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    for breakpoint in target.breakpoint_iter():
        breakpoint.SetScriptCallbackFunction("skip_consumption_probe.on_breakpoint")
    print("SKIP_CONSUMPTION_ATTACHED", target.GetNumBreakpoints())


def resume_until_complete(debugger):
    process = debugger.GetSelectedTarget().GetProcess()
    for _ in range(32):
        if _state()["capture_complete"]:
            return
        if process.GetState() not in (lldb.eStateStopped, lldb.eStateCrashed):
            return
        error = process.Continue()
        if not error.Success():
            _state()["errors"].append(f"continue: {error}")
            return


def write_report(debugger, path):
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    state["process"] = {
        "state": int(process.GetState()),
        "exit_status": process.GetExitStatus(),
    }
    state.pop("contexts", None)
    with open(path, "w", encoding="ascii") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("SKIP_CONSUMPTION_REPORT", path, state["capture_complete"], state["errors"])
