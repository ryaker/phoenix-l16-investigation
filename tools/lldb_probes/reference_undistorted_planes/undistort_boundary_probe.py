import builtins
import json
import struct


SITE = 0x261F01


def reset(label="", stop_after=0):
    builtins.l16_undistort_boundary = {
        "label": label,
        "hits": [],
        "hit_count": 0,
        "stop_after": stop_after,
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_undistort_boundary"):
        reset()
    return builtins.l16_undistort_boundary


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    raw = process.ReadMemory(address, size, error)
    if not error.Success() or len(raw) != size:
        return None
    return raw


def _base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            value = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if value != 0xFFFFFFFFFFFFFFFF:
                return value
    return None


def _descriptor(process, address):
    raw = _read(process, address, 0x30)
    if raw is None:
        return None
    return {
        "address": address,
        "origin": list(struct.unpack_from("<2i", raw, 0x00)),
        "bounds": list(struct.unpack_from("<2i", raw, 0x08)),
        "size": list(struct.unpack_from("<2i", raw, 0x10)),
        "stride": struct.unpack_from("<i", raw, 0x18)[0],
        "data": struct.unpack_from("<Q", raw, 0x20)[0],
        "allocation": struct.unpack_from("<Q", raw, 0x28)[0],
        "raw": raw.hex(),
    }


def hit(frame, bp_loc, internal_dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    base = _base(process.GetTarget())
    site = frame.GetPC() - base if base is not None else None
    if site != SITE:
        state["errors"].append(f"unexpected site {site}")
        return False
    state["hit_count"] += 1
    if len(state["hits"]) >= 256:
        return False
    descriptor = _descriptor(
        process, frame.FindRegister("r13").GetValueAsUnsigned()
    )
    if descriptor is None:
        state["errors"].append("destination descriptor read failed")
        return False
    state["hits"].append(
        {
            "ordinal": state["hit_count"],
            "thread": frame.GetThread().GetThreadID(),
            "destination": descriptor,
            "lens_object": frame.FindRegister("r12").GetValueAsUnsigned(),
        }
    )
    return bool(state["stop_after"] and state["hit_count"] >= state["stop_after"])


def attach(debugger):
    target = debugger.GetSelectedTarget()
    found = False
    for index in range(target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(index)
        if not bp or not bp.IsValid() or bp.GetNumLocations() < 1:
            continue
        if bp.GetLocationAtIndex(0).GetAddress().GetFileAddress() == SITE:
            bp.SetScriptCallbackFunction("undistort_boundary_probe.hit")
            found = True
    if not found:
        _state()["errors"].append("missing boundary breakpoint")
    print("UNDISTORT_BOUNDARY_ATTACHED", found)


def write_report(debugger, path):
    process = debugger.GetSelectedTarget().GetProcess()
    state = dict(_state())
    state["process"] = {
        "state": process.GetState(),
        "exit_status": process.GetExitStatus(),
    }
    with open(path, "w", encoding="ascii") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(
        "UNDISTORT_BOUNDARY_REPORT",
        path,
        state["hit_count"],
        len(state["hits"]),
        state["errors"],
    )
