"""Catch the first ColorFusionBayer+0xc0 data-pointer write after initialize."""

import json
import os
import struct

import lldb


ROOT = "/Volumes/Dev/L16_Lumen_ReverseEngineering"
OUT = os.environ.get(
    "CF_NOISE_ORIGIN_OUT",
    ROOT + "/runs/colorfusion_f_runtime/u1_28_noise_signal_origin.json",
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


def _base(target):
    module = target.FindModule(lldb.SBFileSpec("libcp.dylib"))
    if not module.IsValid():
        raise RuntimeError("libcp.dylib is not loaded")
    return module.GetObjectFileHeaderAddress().GetLoadAddress(target)


def _backtrace(thread, base):
    target = thread.GetProcess().GetTarget()
    rows = []
    for index in range(min(thread.GetNumFrames(), 16)):
        frame = thread.GetFrameAtIndex(index)
        pc = frame.GetPCAddress().GetLoadAddress(target)
        rows.append({
            "index": index,
            "pc": "0x%x" % pc,
            "relative": "0x%x" % (pc - base) if base <= pc < base + 0x700000 else None,
            "function": frame.GetFunctionName(),
        })
    return rows


def on_initialize(frame, bp_loc, internal_dict):
    if STATE["armed"]:
        return False
    process = frame.GetThread().GetProcess()
    obj = _reg(frame, "rdi")
    address = obj + 0xC0
    error = lldb.SBError()
    watch = process.GetTarget().WatchAddress(address, 8, False, True, error)
    if not error.Success():
        raise RuntimeError("watchpoint failed: %s" % error)
    STATE.update({
        "armed": True,
        "object": "0x%x" % obj,
        "watched_address": "0x%x" % address,
        "initial_value": "0x%x" % struct.unpack("<Q", _read(process, address, 8))[0],
    })
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def capture(debugger):
    process = debugger.GetSelectedTarget().GetProcess()
    frame = process.GetSelectedThread().GetFrameAtIndex(0)
    if STATE["done"]:
        return
    target = process.GetTarget()
    base = _base(target)
    obj = int(STATE["object"], 16)
    value = struct.unpack("<Q", _read(process, obj + 0xC0, 8))[0]
    STATE.update({
        "done": True,
        "new_value": "0x%x" % value,
        "stop_pc_relative": "0x%x" % (frame.GetPCAddress().GetLoadAddress(target) - base),
        "descriptor_0xa0_hex": _read(process, obj + 0xA0, 0x30).hex(),
        "backtrace": _backtrace(frame.GetThread(), base),
    })
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as handle:
        json.dump(STATE, handle, indent=2, sort_keys=True)
    print("CF_NOISE_SIGNAL_ORIGIN " + OUT)
    process.Kill()


def install(debugger):
    target = debugger.GetSelectedTarget()
    base = _base(target)
    bp = target.BreakpointCreateByAddress(base + 0x1AB2D0)
    bp.SetScriptCallbackFunction("noise_signal_origin_probe.on_initialize")
    print("CF_NOISE_SIGNAL_ORIGIN_ARMED id=%d" % bp.GetID())
