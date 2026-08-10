"""Capture FusionCacheBayer's selected five-float tuning packet.

The breakpoint is immediately after the constructor copies the selected
installed row to FusionCacheBayer+0xc8.  It stops on the first matching
construction so the renderer's later multithreaded tile work is never
instrumented.
"""

import builtins
import json
import struct


SITE = 0x4037DC


def reset(label, output_path):
    builtins.l16_fusioncache_tuning = {
        "label": label,
        "output_path": output_path,
        "site_va": SITE,
        "events": [],
        "errors": [],
    }


def _state():
    return builtins.l16_fusioncache_tuning


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    if not error.Success() or len(data) != size:
        raise RuntimeError(f"read failed at 0x{address:x}: {error}")
    return data


def _libcp_base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                return base
    return None


def _stack(frame, limit=8):
    target = frame.GetThread().GetProcess().GetTarget()
    base = _libcp_base(target)
    out = []
    for index in range(min(limit, frame.GetThread().GetNumFrames())):
        item = frame.GetThread().GetFrameAtIndex(index)
        pc = item.GetPC()
        out.append({
            "index": index,
            "pc": pc,
            "libcp_va": pc - base if base is not None and pc >= base else None,
            "function": item.GetFunctionName(),
        })
    return out


def capture(frame, bp_loc, internal_dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    try:
        owner = _u(frame, "r13")
        captured = _u(frame, "r15")
        packet = _read(process, owner + 0xC8, 24)
        captured_data = _read(process, captured, 0xAC)
        state["events"].append({
            "owner": owner,
            "captured_image": captured,
            "packet_words_hex": [
                f"0x{word:08x}" for word in struct.unpack("<6I", packet)
            ],
            "packet_f32": list(struct.unpack("<6f", packet)),
            "captured_camera_id_0x60": struct.unpack_from("<i", captured_data, 0x60)[0],
            "captured_sensor_analog_gain_0x40": struct.unpack_from("<f", captured_data, 0x40)[0],
            "captured_sensor_type_0xa8": struct.unpack_from("<i", captured_data, 0xA8)[0],
            "stack": _stack(frame),
        })
    except Exception as exc:
        state["errors"].append(repr(exc))
    return True


def install(debugger, breakpoint_id):
    bp = debugger.GetSelectedTarget().FindBreakpointByID(breakpoint_id)
    bp.SetScriptCallbackFunction("fusioncache_tuning_probe.capture")


def report():
    state = _state()
    process = builtins.__import__("lldb").debugger.GetSelectedTarget().GetProcess()
    state["process"] = {
        "valid": process.IsValid(),
        "state": str(process.GetState()),
        "stopped_after_capture": process.GetState() == 5,
    }
    with open(state["output_path"], "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
    print(json.dumps({
        "output_path": state["output_path"],
        "events": len(state["events"]),
        "errors": state["errors"],
    }, sort_keys=True))
