"""Capture the target pre-vignetting Bayer plane and its 0x18e150 reduction."""

import hashlib
import json
import os
import struct

import lldb


ROOT = "/Volumes/Dev/L16_Lumen_ReverseEngineering"
OUT_DIR = os.environ.get(
    "CF_SIGNAL_PLANE_OUT",
    ROOT + "/runs/colorfusion_f_runtime/u1_28_noise_signal_plane",
)
STATE = {"armed": False, "done": False}


def _reg(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    error = lldb.SBError()
    data = bytes(process.ReadMemory(address, size, error))
    if not error.Success() or len(data) != size:
        raise RuntimeError("read 0x%x+0x%x failed: %s" % (address, size, error))
    return data


def _u64(process, address):
    return struct.unpack("<Q", _read(process, address, 8))[0]


def _base(target):
    module = target.FindModule(lldb.SBFileSpec("libcp.dylib"))
    if not module.IsValid():
        raise RuntimeError("libcp.dylib is not loaded")
    return module.GetObjectFileHeaderAddress().GetLoadAddress(target)


def _descriptor(process, address, words):
    width, height, stride = struct.unpack("<iii", _read(process, address + 0x10, 12))
    data = _u64(process, address + 0x20)
    return {"address": address, "width": width, "height": height, "stride": stride,
            "data": data, "words": words}


def _dump(process, descriptor, name):
    size = descriptor["stride"] * descriptor["height"] * descriptor["words"] * 4
    data = _read(process, descriptor["data"], size)
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    with open(path, "wb") as handle:
        handle.write(data)
    return {"file": name, "size": size, "sha256": hashlib.sha256(data).hexdigest()}


def on_entry(frame, bp_loc, internal_dict):
    if STATE["armed"]:
        return False
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    base = _base(target)
    source = _descriptor(process, _reg(frame, "rsi"), 1)
    output_address = _reg(frame, "rdi")
    caller = frame.GetThread().GetFrameAtIndex(1)
    camera_pointer = _reg(caller, "r15")
    STATE.update({
        "armed": True,
        "thread": frame.GetThread().GetThreadID(),
        "output_address": output_address,
        "camera_key": struct.unpack("<i", _read(process, camera_pointer, 4))[0],
        "source": {**source, "dump": _dump(process, source, "target_pre_vignette_f32.bin")},
    })
    bp_loc.GetBreakpoint().SetEnabled(False)
    for thread in process:
        if thread.GetThreadID() != STATE["thread"]:
            thread.Suspend()
    return_bp = target.BreakpointCreateByAddress(base + 0x1AC257)
    return_bp.SetOneShot(True)
    return_bp.SetThreadID(STATE["thread"])
    return_bp.SetScriptCallbackFunction("noise_signal_plane_probe.on_return")
    return False


def on_return(frame, bp_loc, internal_dict):
    if STATE["done"]:
        return False
    process = frame.GetThread().GetProcess()
    output = _descriptor(process, STATE["output_address"], 4)
    STATE.update({
        "done": True,
        "output": {**output, "dump": _dump(process, output, "signal_reciprocal_vec4_f32.bin")},
    })
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "capture.json"), "w") as handle:
        json.dump(STATE, handle, indent=2, sort_keys=True)
    print("CF_SIGNAL_PLANE_CAPTURE " + os.path.join(OUT_DIR, "capture.json"))
    process.Kill()
    return False


def install(debugger):
    target = debugger.GetSelectedTarget()
    base = _base(target)
    bp = target.BreakpointCreateByAddress(base + 0x18E150)
    bp.SetScriptCallbackFunction("noise_signal_plane_probe.on_entry")
    print("CF_SIGNAL_PLANE_ARMED id=%d" % bp.GetID())

