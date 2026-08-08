import builtins
import json
import struct


CREATE_STEREO_ENTRY = 0x27B7A0
DECISION = 0x2E9AFD


def reset(label="", limit=96):
    builtins.l16_hot_pixel_decision = {
        "label": label,
        "limit": limit,
        "create_entries": 0,
        "decisions": [],
        "capture_complete": False,
        "terminated_after_capture": False,
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_hot_pixel_decision"):
        reset()
    return builtins.l16_hot_pixel_decision


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    raw = process.ReadMemory(address, size, error)
    if not error.Success() or len(raw) != size:
        return None
    return raw


def _u64(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<Q", raw)[0] if raw else None


def _window(process, pointer, x, radius=5):
    if not pointer or x < radius:
        return None
    raw = _read(process, pointer + 2 * (x - radius), 2 * (2 * radius + 1))
    if raw is None:
        return None
    return list(struct.unpack("<" + "H" * (2 * radius + 1), raw))


def _base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            address = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if address != 0xFFFFFFFFFFFFFFFF:
                return address
    return None


def hit(frame, bp_loc, internal_dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    base = _base(process.GetTarget())
    site = frame.GetPC() - base if base is not None else None
    if site == CREATE_STEREO_ENTRY:
        state["create_entries"] += 1
        return False
    if site != DECISION or not state["create_entries"]:
        return False

    rbp = _u(frame, "rbp")
    x = _u(frame, "r12")
    rows = {
        "-4": _u64(process, rbp - 0x150),
        "-2": _u64(process, rbp - 0x0F0),
        "-1": _u64(process, rbp - 0x100),
        "0": _u(frame, "r13"),
        "1": _u64(process, rbp - 0x108),
        "2": _u64(process, rbp - 0x0F8),
        "4": _u64(process, rbp - 0x158),
    }
    windows = {key: _window(process, pointer, x) for key, pointer in rows.items()}
    if any(window is None for window in windows.values()):
        state["errors"].append("marker window read failed")
        return False
    state["decisions"].append(
        {
            "thread_id": thread.GetThreadID(),
            "x": x,
            "x_parity": x & 1,
            "phase_selector": _u(frame, "rdx") & 1,
            "accept_al": _u(frame, "rax") & 0xFF,
            "center_marker": windows["0"][5],
            "marker_windows_x_minus5_plus5": windows,
        }
    )
    if len(state["decisions"]) >= state["limit"]:
        state["capture_complete"] = True
        error = process.Kill()
        state["terminated_after_capture"] = error.Success()
        if not error.Success():
            state["errors"].append("kill failed: " + str(error.GetCString()))
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    expected = {CREATE_STEREO_ENTRY, DECISION}
    found = set()
    for index in range(target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(index)
        if not bp or not bp.IsValid() or bp.GetNumLocations() < 1:
            continue
        site = bp.GetLocationAtIndex(0).GetAddress().GetFileAddress()
        if site in expected:
            bp.SetScriptCallbackFunction("hot_pixel_decision_probe.hit")
            found.add(site)
    if found != expected:
        _state()["errors"].append("missing sites: " + repr(sorted(expected - found)))
    print("L16_HOT_PIXEL_DECISION_ATTACHED", [hex(site) for site in sorted(found)])


def write_report(debugger, path):
    process = debugger.GetSelectedTarget().GetProcess()
    state = dict(_state())
    state["process"] = {"state": process.GetState(), "exit_status": process.GetExitStatus()}
    with open(path, "w", encoding="ascii") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_HOT_PIXEL_DECISION_REPORT", path)
