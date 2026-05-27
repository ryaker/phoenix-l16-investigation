import builtins
import json
import struct


SITE_VTABLE_SETUP = 0x3D0408
SITE_EXECUTOR_DISPATCH = 0x3D042B
SITE_THUNK = 0x3D53C0
SITE_LOOP_CALL = 0x3D5468

SITE_NAMES = {
    SITE_VTABLE_SETUP: "vtable_setup_0x3d0408",
    SITE_EXECUTOR_DISPATCH: "executor_dispatch_0x3d042b",
    SITE_THUNK: "thunk_0x3d53c0",
    SITE_LOOP_CALL: "loop_call_0x3d5468",
}


def reset(sample_limit=8):
    builtins.l16_3d5400_liveness = {
        "sample_limit": sample_limit,
        "breakpoint_ids": {},
        "counts": {name: 0 for name in SITE_NAMES.values()},
        "samples": {name: [] for name in SITE_NAMES.values()},
        "first_loop_call_hit": False,
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_3d5400_liveness"):
        reset()
    return builtins.l16_3d5400_liveness


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    if not addr:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u64(data, off=0):
    return struct.unpack_from("<Q", data, off)[0]


def _i32(data, off=0):
    return struct.unpack_from("<i", data, off)[0]


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


def _stack(thread):
    target = thread.GetProcess().GetTarget()
    frames = []
    for index in range(min(thread.GetNumFrames(), 10)):
        frame = thread.GetFrameAtIndex(index)
        frames.append(
            {
                "index": index,
                "pc": frame.GetPC(),
                "libcp_va": _module_va(target, frame.GetPC()),
                "function": frame.GetFunctionName(),
                "rbp": _u(frame, "rbp"),
            }
        )
    return frames


def _callback_object(target, process, addr):
    data = _read(process, addr, 0x30)
    if data is None:
        return {"addr": addr, "error": "failed to read callback object"}
    vtable = _u64(data, 0x00)
    return {
        "addr": addr,
        "qword_00_vtable": vtable,
        "qword_00_vtable_libcp_va": _module_va(target, vtable),
        "qword_08": _u64(data, 0x08),
        "qword_10": _u64(data, 0x10),
        "qword_18": _u64(data, 0x18),
        "qword_20": _u64(data, 0x20),
        "qword_28": _u64(data, 0x28),
    }


def _pair_record(process, addr):
    data = _read(process, addr, 0x20)
    if data is None:
        return {"addr": addr, "error": "failed to read pair record"}
    return {
        "addr": addr,
        "qword_00": _u64(data, 0x00),
        "qword_08": _u64(data, 0x08),
        "qword_10": _u64(data, 0x10),
        "qword_18": _u64(data, 0x18),
    }


def _sample(frame, site_va):
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    registers = {
        "rdi": _u(frame, "rdi"),
        "rsi": _u(frame, "rsi"),
        "rdx": _u(frame, "rdx"),
        "rcx": _u(frame, "rcx"),
        "rax": _u(frame, "rax"),
        "rbp": _u(frame, "rbp"),
        "rsp": _u(frame, "rsp"),
        "r15": _u(frame, "r15"),
    }
    sample = {
        "site_va": site_va,
        "site_name": SITE_NAMES.get(site_va, hex(site_va)),
        "registers": registers,
        "stack": _stack(frame.GetThread()),
    }

    if site_va == SITE_EXECUTOR_DISPATCH:
        sample["callback_object_at_rcx"] = _callback_object(target, process, registers["rcx"])
    elif site_va == SITE_THUNK:
        sample["callback_object_at_rdi"] = _callback_object(target, process, registers["rdi"])
    elif site_va == SITE_LOOP_CALL:
        sample["pair_record_at_rsi"] = _pair_record(process, registers["rsi"])

    return sample


def hit(frame, bp_loc, internal_dict):
    state = _state()
    site_va = _module_va(frame.GetThread().GetProcess().GetTarget(), frame.GetPC())
    name = SITE_NAMES.get(site_va, "unknown")
    state["counts"][name] = state["counts"].get(name, 0) + 1
    if len(state["samples"].setdefault(name, [])) < state["sample_limit"]:
        state["samples"][name].append(_sample(frame, site_va))
    if site_va == SITE_LOOP_CALL:
        state["first_loop_call_hit"] = True
        return True
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    count = target.GetNumBreakpoints()
    if count < 4:
        _state()["errors"].append("expected at least 4 breakpoints")
        print("L16_3D5400_ATTACH_ERROR expected at least 4 breakpoints")
        return
    ids = {}
    for index, site_va in enumerate(
        [SITE_VTABLE_SETUP, SITE_EXECUTOR_DISPATCH, SITE_THUNK, SITE_LOOP_CALL],
        start=count - 4,
    ):
        bp = target.GetBreakpointAtIndex(index)
        bp.SetScriptCallbackFunction("selected_cache_3d5400_liveness_probe.hit")
        ids[SITE_NAMES[site_va]] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_3D5400_ATTACHED", ids)


def drive_until_stable_stop_or_exit(debugger, max_steps=16):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process.IsValid() and process.GetState() == lldb.eStateStopped and steps < max_steps:
        if _state().get("first_loop_call_hit"):
            break
        steps += 1
        process.Continue()
    print("L16_3D5400_DRIVE_STEPS", steps)


def _breakpoint_hit_counts(debugger):
    target = debugger.GetSelectedTarget()
    out = {}
    for name, bp_id in _state().get("breakpoint_ids", {}).items():
        bp = target.FindBreakpointByID(bp_id)
        out[name] = bp.GetHitCount() if bp and bp.IsValid() else None
    return out


def _process_packet(debugger):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    if not process or not process.IsValid():
        return {"valid": False}
    return {
        "valid": True,
        "state": lldb.SBDebugger.StateAsCString(process.GetState()),
        "exit_status": process.GetExitStatus(),
    }


def payload(debugger, label):
    return {
        "label": label,
        "process": _process_packet(debugger),
        "breakpoint_hit_counts": _breakpoint_hit_counts(debugger),
        **_state(),
    }


def write_report(debugger, label, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger, label), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_3D5400_WROTE", path)


def report(debugger, label):
    print("L16_3D5400_BEGIN", label)
    print(json.dumps(payload(debugger, label), indent=2, sort_keys=True))
    print("L16_3D5400_END", label)
