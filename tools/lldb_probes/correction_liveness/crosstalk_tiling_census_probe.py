"""Census every scalar cross-talk helper invocation to pin full-frame tiling.

The admitted formula bundle captured a single 260x260 packet with zero
coordinate offset.  That leaves the frame-level tile decomposition, the
per-tile source-view origin, and the per-tile coordinate offset unproven.
This probe records the helper arguments for every eligible invocation so the
tiling can be derived from the installed run rather than assumed.
"""

import builtins
import json
import os
import struct


HELPER_ENTRY = 0x1019D0
MAX_RECORDS = 4096


def reset(label="", output_dir=""):
    builtins.l16_crosstalk_tiling = {
        "label": label,
        "output_dir": output_dir,
        "records": [],
        "truncated": False,
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_crosstalk_tiling"):
        reset()
    return builtins.l16_crosstalk_tiling


def _base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            value = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if value != 0xFFFFFFFFFFFFFFFF:
                return value
    return None


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    if not address or size <= 0:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    return data if error.Success() and len(data) == size else None


def _u64(process, address):
    data = _read(process, address, 8)
    return struct.unpack("<Q", data)[0] if data is not None else None


def _descriptor(process, address):
    data = _read(process, address, 0x30)
    if data is None:
        return None
    words = struct.unpack("<8iQQ", data)
    result = {
        "origin": list(words[0:2]),
        "bounds": list(words[2:4]),
        "size": list(words[4:6]),
        "stride": words[6],
        "reserved": words[7],
        "data": words[8],
        "allocation": words[9],
    }
    if not (
        0 < result["size"][0] <= 16384
        and 0 < result["size"][1] <= 16384
        and result["stride"] >= result["size"][0]
        and result["data"] > 0x10000
    ):
        return None
    return result


def hit(frame, _bp_loc, _internal_dict):
    state = _state()
    if len(state["records"]) >= MAX_RECORDS:
        state["truncated"] = True
        return False
    thread = frame.GetThread()
    process = thread.GetProcess()
    start_raw = _read(process, _u(frame, "rdx"), 8)
    end_raw = _read(process, _u(frame, "rcx"), 8)
    if start_raw is None or end_raw is None:
        return False
    start = list(struct.unpack("<2i", start_raw))
    end = list(struct.unpack("<2i", end_raw))
    offset_raw = _read(process, _u(frame, "r8"), 8)
    scale_raw = _read(process, _u(frame, "r9"), 8)
    rsp = _u(frame, "rsp")
    stack_arguments = [_u64(process, rsp + delta) for delta in (8, 0x10, 0x18)]
    matrices = _read(process, stack_arguments[1], 0x100) if stack_arguments[1] else None
    parity = _read(process, stack_arguments[0], 32) if stack_arguments[0] else None
    state["records"].append({
        "thread": thread.GetThreadID(),
        "start": start,
        "end": end,
        "offset_f32": list(struct.unpack("<2f", offset_raw)) if offset_raw else None,
        "scale_f32": list(struct.unpack("<2f", scale_raw)) if scale_raw else None,
        "source": _descriptor(process, _u(frame, "rdi")),
        "destination": _descriptor(process, _u(frame, "rsi")),
        "parity_i32": list(struct.unpack("<8i", parity)) if parity else None,
        "matrices_sha_prefix": matrices[:16].hex() if matrices else None,
    })
    return False


def install(debugger):
    target = debugger.GetSelectedTarget()
    base = _base(target)
    if base is None:
        raise RuntimeError("libcp.dylib is not loaded")
    bp = target.BreakpointCreateByAddress(base + HELPER_ENTRY)
    bp.SetScriptCallbackFunction("crosstalk_tiling_census_probe.hit")


def write_report(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    state = _state()
    with open(path, "w", encoding="ascii") as handle:
        json.dump(state, handle, indent=1, sort_keys=True)
        handle.write("\n")
    print("L16_CROSSTALK_TILING_REPORT", path, len(state["records"]))
