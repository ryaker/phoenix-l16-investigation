"""Compact runtime discriminator for supported focal/topology variants."""

import builtins
import json
import struct


SITES = {
    0x229EC0: "reference_state_entry",
    0x229F6E: "reference_mode_store",
    0x2481A0: "family_a_wrapper",
    0x248580: "family_b_wrapper",
    0x248960: "family_c_wrapper",
    0x24C320: "family_a",
    0x24D610: "family_b",
    0x19F790: "monofusion_mode1_worker",
    0x1A3C00: "monofusion_mode0_worker",
    0x3C90A5: "c6_clear",
    0xE6D90: "crop_entry",
    0x3B2313: "crop_return_a",
    0x3CB593: "crop_return_b",
}


def reset(label=""):
    builtins.l16_variant_route = {
        "label": label,
        "counts": {name: 0 for name in SITES.values()},
        "reference_entries": [],
        "mode_stores": [],
        "c6_clears": [],
        "crop_results": [],
        "pending_crop": {},
        "errors": [],
        "drive_steps": 0,
        "drive_hit_step_cap": False,
    }


def state():
    if not hasattr(builtins, "l16_variant_route"):
        reset()
    return builtins.l16_variant_route


def u(frame, register):
    return frame.FindRegister(register).GetValueAsUnsigned()


def read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    return data if error.Success() and len(data) == size else None


def i32(process, address):
    data = read(process, address, 4)
    return struct.unpack("<i", data)[0] if data else None


def u8(process, address):
    data = read(process, address, 1)
    return data[0] if data else None


def f32x4(process, address):
    data = read(process, address, 16)
    return list(struct.unpack("<4f", data)) if data else None


def libcp_base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            value = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if value != 0xFFFFFFFFFFFFFFFF:
                return value
    return None


def thread_key(frame):
    thread = frame.GetThread()
    return str(thread.GetThreadID())


def hit(frame, bp_loc, _dict):
    out = state()
    process = frame.GetThread().GetProcess()
    base = libcp_base(process.GetTarget())
    va = frame.GetPC() - base if base is not None else None
    name = SITES.get(va)
    if name is None:
        return False
    out["counts"][name] += 1
    if va in (0x24C320, 0x24D610) and out["counts"][name] >= 4:
        bp_loc.GetBreakpoint().SetEnabled(False)
    try:
        if va == 0x229EC0:
            callback = u(frame, "rdi")
            out["reference_entries"].append(
                {"callback": callback, "camera_key": i32(process, callback + 0x10)}
            )
        elif va == 0x229F6E:
            shared = u(frame, "rdi")
            out["mode_stores"].append(
                {"shared": shared, "mode": u(frame, "rax") & 0xFFFFFFFF}
            )
        elif va == 0x3C90A5:
            captured = u(frame, "rax")
            out["c6_clears"].append(
                {
                    "captured_image": captured,
                    "camera_key_0x60": i32(process, captured + 0x60),
                    "active_before_0x30": u8(process, captured + 0x30),
                }
            )
        elif va == 0xE6D90:
            key = thread_key(frame)
            stack = u(frame, "rsi")
            out["pending_crop"].setdefault(key, []).append(
                {
                    "output": u(frame, "rdi"),
                    "reference_camera_0x44": i32(process, stack + 0x44),
                }
            )
        elif va in (0x3B2313, 0x3CB593):
            key = thread_key(frame)
            pending = out["pending_crop"].get(key, [])
            item = pending.pop() if pending else {}
            if not pending:
                out["pending_crop"].pop(key, None)
            item["return_site"] = va
            item["crop"] = f32x4(process, item.get("output", 0))
            out["crop_results"].append(item)
    except Exception as exc:
        out["errors"].append({"site": name, "error": repr(exc)})
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    for index in range(target.GetNumBreakpoints()):
        target.GetBreakpointAtIndex(index).SetScriptCallbackFunction(
            "variant_route_probe.hit"
        )


def drive_until_exit_or_step_cap(debugger, max_steps=20000):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process.IsValid() and process.GetState() == lldb.eStateStopped and steps < max_steps:
        steps += 1
        process.Continue()
    state()["drive_steps"] = steps
    state()["drive_hit_step_cap"] = (
        process.IsValid() and process.GetState() == lldb.eStateStopped and steps >= max_steps
    )


def write_report(debugger, path):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    out = dict(state())
    out["pending_crop"] = {}
    out["process"] = {
        "state": lldb.SBDebugger.StateAsCString(process.GetState()),
        "exit_status": process.GetExitStatus(),
    }
    with open(path, "w", encoding="utf-8") as stream:
        json.dump(out, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print("L16_VARIANT_ROUTE_WROTE", path)
