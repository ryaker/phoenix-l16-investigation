"""Capture ColorFusion's direct RestoreHighlightsBayer input/output join."""

import hashlib
import json
import os
import struct

import lldb


ROOT = "/Volumes/Dev/L16_Lumen_ReverseEngineering"
OUT_DIR = os.environ.get("CF_HIGHLIGHT_OUT", ROOT + "/runs/colorfusion_f_runtime/highlight_join")
STATE = {"armed": False, "done": False, "kernel_ids": []}


def _reg(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _xmm_f32(frame, name):
    error = lldb.SBError()
    raw = frame.FindRegister(name).GetData().ReadRawData(error, 0, 4)
    if not error.Success():
        raise RuntimeError("read %s failed" % name)
    return struct.unpack("<f", raw)[0]


def _read(process, address, size):
    error = lldb.SBError()
    data = bytes(process.ReadMemory(address, size, error))
    if not error.Success() or len(data) != size:
        raise RuntimeError("read 0x%x+0x%x failed: %s" % (address, size, error))
    return data


def _base(target):
    module = target.FindModule(lldb.SBFileSpec("libcp.dylib"))
    if not module.IsValid():
        raise RuntimeError("libcp.dylib is not loaded")
    return module.GetObjectFileHeaderAddress().GetLoadAddress(target)


def _descriptor(process, address):
    raw = _read(process, address, 0x30)
    return {
        "address": "0x%x" % address,
        "origin": list(struct.unpack_from("<2i", raw, 0)),
        "bounds": list(struct.unpack_from("<2i", raw, 8)),
        "width": struct.unpack_from("<i", raw, 0x10)[0],
        "height": struct.unpack_from("<i", raw, 0x14)[0],
        "stride": struct.unpack_from("<i", raw, 0x18)[0],
        "data": struct.unpack_from("<Q", raw, 0x20)[0],
    }


def _dump_plane(process, descriptor, name):
    width = descriptor["width"]
    height = descriptor["height"]
    stride = descriptor["stride"]
    pointer = descriptor["data"]
    rows = bytearray()
    for y in range(height):
        rows += _read(process, pointer + 2 * stride * y, 2 * width)
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    with open(path, "wb") as handle:
        handle.write(rows)
    return {"file": name, "size": len(rows), "sha256": hashlib.sha256(rows).hexdigest()}


def on_call(frame, bp_loc, internal_dict):
    if STATE["armed"]:
        return False
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    base = _base(target)
    source = _descriptor(process, _reg(frame, "rsi"))
    destination_address = _reg(frame, "rdi")
    phase = list(struct.unpack("<2i", _read(process, _reg(frame, "rdx"), 8)))
    context_pointer = _reg(frame, "rcx")
    STATE.update({
        "armed": True,
        "thread": frame.GetThread().GetThreadID(),
        "destination_address": destination_address,
        "phase": phase,
        "black": _xmm_f32(frame, "xmm0"),
        "white": _xmm_f32(frame, "xmm1"),
        "context": "0x%x" % context_pointer,
        "context_first_256": _read(process, context_pointer, 0x100).hex(),
        "source": {**source, "dump": _dump_plane(process, source, "post_hotpixel_u16.bin")},
    })
    bp_loc.GetBreakpoint().SetEnabled(False)
    for identifier in STATE["kernel_ids"]:
        target.FindBreakpointByID(identifier).SetEnabled(True)
    returned = target.BreakpointCreateByAddress(base + 0x1AC1B1)
    returned.SetOneShot(True)
    returned.SetThreadID(STATE["thread"])
    returned.SetScriptCallbackFunction("highlight_join_probe.on_return")
    return False


def on_kernel(frame, bp_loc, internal_dict):
    if "gain_vector" in STATE:
        bp_loc.GetBreakpoint().SetEnabled(False)
        return False
    process = frame.GetThread().GetProcess()
    pointer = _reg(frame, "r9")
    raw = _read(process, pointer, 0x40)
    STATE["gain_vector_pointer"] = "0x%x" % pointer
    STATE["gain_vector"] = list(struct.unpack("<16f", raw))
    STATE["gain_vector_bits"] = ["0x%08x" % word for word in struct.unpack("<16I", raw)]
    for identifier in STATE["kernel_ids"]:
        process.GetTarget().FindBreakpointByID(identifier).SetEnabled(False)
    return False


def on_return(frame, bp_loc, internal_dict):
    if STATE["done"]:
        return False
    process = frame.GetThread().GetProcess()
    destination = _descriptor(process, STATE["destination_address"])
    STATE["destination"] = {
        **destination,
        "dump": _dump_plane(process, destination, "post_highlight_u16.bin"),
    }
    STATE["done"] = True
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "capture.json"), "w") as handle:
        json.dump(STATE, handle, indent=2, sort_keys=True)
    print("CF_HIGHLIGHT_CAPTURE " + os.path.join(OUT_DIR, "capture.json"))
    process.Kill()
    return False


def install(debugger):
    target = debugger.GetSelectedTarget()
    base = _base(target)
    call = target.BreakpointCreateByAddress(base + 0x1AC1AC)
    call.SetScriptCallbackFunction("highlight_join_probe.on_call")
    for relative in (0x30B9F0, 0x30DCC0, 0x30FF60, 0x3121F0):
        kernel = target.BreakpointCreateByAddress(base + relative)
        kernel.SetScriptCallbackFunction("highlight_join_probe.on_kernel")
        kernel.SetEnabled(False)
        STATE["kernel_ids"].append(kernel.GetID())
    print("CF_HIGHLIGHT_ARMED call=%d kernels=%s" % (call.GetID(), STATE["kernel_ids"]))
