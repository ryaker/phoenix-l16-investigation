"""Capture ColorFusion's target hot-pixel worker closure at 0x2e8cc0."""

import hashlib
import json
import os
import struct

import lldb


ROOT = "/Volumes/Dev/L16_Lumen_ReverseEngineering"
OUT_DIR = os.environ.get("CF_HOTPIXEL_OUT", ROOT + "/runs/colorfusion_f_runtime/hotpixel_lut")
STATE = {"armed": False, "done": False, "worker_breakpoint_id": 0, "camera_key": None}


def _reg(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


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


def on_colorfusion(frame, bp_loc, internal_dict):
    if STATE["armed"]:
        return False
    process = frame.GetThread().GetProcess()
    camera_pointer = _reg(frame, "rdx")
    STATE["camera_key"] = struct.unpack("<i", _read(process, camera_pointer, 4))[0]
    STATE["armed"] = True
    bp_loc.GetBreakpoint().SetEnabled(False)
    process.GetTarget().FindBreakpointByID(STATE["worker_breakpoint_id"]).SetEnabled(True)
    return False


def on_worker(frame, bp_loc, internal_dict):
    if STATE["done"]:
        return False
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    if not STATE["armed"]:
        return False
    closure = _reg(frame, "rdi")
    pointers = struct.unpack("<6Q", _read(process, closure + 8, 48))
    phase = list(struct.unpack("<2i", _read(process, pointers[1], 8)))
    lut_pointers = struct.unpack("<4Q", _read(process, pointers[2], 32))
    os.makedirs(OUT_DIR, exist_ok=True)
    luts = []
    for lane, pointer in enumerate(lut_pointers):
        raw = _read(process, pointer, 4096)
        name = "hotpixel_lut_lane%d.f32le" % lane
        with open(os.path.join(OUT_DIR, name), "wb") as handle:
            handle.write(raw)
        luts.append({
            "lane": lane,
            "file": name,
            "pointer": "0x%x" % pointer,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "first_8": list(struct.unpack("<8f", raw[:32])),
        })
    packet = {
        "worker_relative": "0x2e8cc0",
        "camera_key": STATE["camera_key"],
        "phase": phase,
        "threshold_multiplier": struct.unpack("<f", _read(process, pointers[3], 4))[0],
        "luts": luts,
    }
    with open(os.path.join(OUT_DIR, "capture.json"), "w") as handle:
        json.dump(packet, handle, indent=2, sort_keys=True)
    STATE["done"] = True
    print("CF_HOTPIXEL_CAPTURE " + os.path.join(OUT_DIR, "capture.json"))
    process.Kill()
    return False


def install(debugger):
    target = debugger.GetSelectedTarget()
    base = _base(target)
    worker = target.BreakpointCreateByAddress(base + 0x2E8CC0)
    worker.SetScriptCallbackFunction("hotpixel_lut_probe.on_worker")
    worker.SetEnabled(False)
    STATE["worker_breakpoint_id"] = worker.GetID()
    colorfusion = target.BreakpointCreateByAddress(base + 0x1AC010)
    colorfusion.SetScriptCallbackFunction("hotpixel_lut_probe.on_colorfusion")
    print("CF_HOTPIXEL_ARMED colorfusion=%d worker=%d" % (colorfusion.GetID(), worker.GetID()))
