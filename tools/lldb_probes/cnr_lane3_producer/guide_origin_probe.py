"""Capture the exact byte-plane producer of the CNR lane-3 guide.

The selected route constructs a float guide in 0x406a10, passes it as r9 to
0x31acf0, and 0x33f480 installs a cropped view at task+0x60. Three installed
helpers can construct the guide from one, two, or three uint8 planes. This
probe records which helper is live, its source bytes/scalar, the final guide
descriptor at the 0x31acf0 callsite, and the task view consumed by 0x34b3f0.
"""

import builtins
import json
import os
import struct


SITES = {
    0x1BCE50: "one_plane",
    0x1BCF90: "two_plane",
    0x1BD0A0: "three_plane",
}
FINAL = 0x407458
CNR = 0x34B3F0


def reset(label="", report_path="", cap=4):
    builtins.l16_cnr_guide = {
        "label": label,
        "report_path": report_path,
        "cap": cap,
        "breakpoint_ids": {},
        "helper_counts": {name: 0 for name in SITES.values()},
        "helper_events": [],
        "final_events": [],
        "cnr_events": [],
        "errors": [],
    }


def _s():
    if not hasattr(builtins, "l16_cnr_guide"):
        reset()
    return builtins.l16_cnr_guide


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    if not addr or addr < 0x1000 or addr > 0x00007FFFFFFFFFFF:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    try:
        data = process.ReadMemory(addr, size, error)
    except Exception:
        return None
    return data if error.Success() and data is not None and len(data) == size else None


def _base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                return base
    return None


def _va(target, pc):
    base = _base(target)
    return pc - base if base is not None and pc >= base else None


def _xmm0(frame):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    raw = frame.FindRegister("xmm0").GetData().ReadRawData(error, 0, 16)
    if not error.Success() or len(raw) != 16:
        return None
    return {"hex": raw.hex(), "f32": list(struct.unpack("<4f", raw))}


def _desc(process, addr, elem_size, sample_count=96):
    raw = _read(process, addr, 0x30)
    if raw is None:
        return {"addr": addr, "read_ok": False}
    width, height, stride = struct.unpack_from("<iii", raw, 0x10)
    data_ptr = struct.unpack_from("<Q", raw, 0x20)[0]
    out = {
        "addr": addr,
        "read_ok": True,
        "width": width,
        "height": height,
        "stride": stride,
        "data_ptr": data_ptr,
        "raw_hex": raw.hex(),
    }
    if data_ptr and width > 0 and height > 0 and stride > 0:
        sample = _read(process, data_ptr, min(width, sample_count) * elem_size)
        if sample is not None:
            out["row0_hex"] = sample.hex()
            if elem_size == 1:
                out["row0_u8"] = list(sample)
            elif elem_size == 4:
                out["row0_f32"] = list(struct.unpack("<" + "f" * (len(sample) // 4), sample))
    return out


def _stack(frame, count=8):
    thread = frame.GetThread()
    target = thread.GetProcess().GetTarget()
    return [
        {
            "i": i,
            "libcp_va": _va(target, thread.GetFrameAtIndex(i).GetPC()),
            "fn": thread.GetFrameAtIndex(i).GetFunctionName(),
        }
        for i in range(min(count, thread.GetNumFrames()))
    ]


def helper(frame, _bp_loc, _dict):
    state = _s()
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    site = _va(target, frame.GetPC())
    name = SITES.get(site, hex(site) if site is not None else "unknown")
    state["helper_counts"][name] = state["helper_counts"].get(name, 0) + 1
    if state["helper_counts"][name] <= int(state["cap"]):
        event = {
            "site_va": site,
            "name": name,
            "scalar_xmm0": _xmm0(frame),
            "dst": _desc(process, _u(frame, "rdi"), 4),
            "src1": _desc(process, _u(frame, "rsi"), 1),
            "stack": _stack(frame),
        }
        if site in (0x1BCF90, 0x1BD0A0):
            event["src2"] = _desc(process, _u(frame, "rdx"), 1)
        if site == 0x1BD0A0:
            event["src3"] = _desc(process, _u(frame, "rcx"), 1)
        state["helper_events"].append(event)
    if state["helper_counts"][name] >= int(state["cap"]):
        bp_id = state["breakpoint_ids"].get(name)
        bp = target.FindBreakpointByID(bp_id) if bp_id else None
        if bp and bp.IsValid():
            bp.SetEnabled(False)
    return False


def final_call(frame, _bp_loc, _dict):
    state = _s()
    if len(state["final_events"]) < int(state["cap"]):
        process = frame.GetThread().GetProcess()
        state["final_events"].append({
            "guide_r9": _desc(process, _u(frame, "r9"), 4),
            "base_rdx": _desc(process, _u(frame, "rdx"), 4),
            "stack": _stack(frame),
        })
    return False


def cnr(frame, _bp_loc, _dict):
    state = _s()
    process = frame.GetThread().GetProcess()
    if len(state["cnr_events"]) < int(state["cap"]):
        task = _u(frame, "rsi")
        raw = _read(process, task, 0x80)
        event = {"task": task, "stack": _stack(frame)}
        if raw is not None:
            data_ptr = struct.unpack_from("<Q", raw, 0x60)[0]
            width, height, stride = struct.unpack_from("<iii", raw, 0x50)
            event["guide"] = {
                "width": width,
                "height": height,
                "stride": stride,
                "data_ptr": data_ptr,
            }
            row = _read(process, data_ptr, min(width, 96) * 4)
            if row is not None:
                event["guide"]["row0_f32"] = list(struct.unpack("<" + "f" * (len(row) // 4), row))
        state["cnr_events"].append(event)
    if len(state["cnr_events"]) >= int(state["cap"]):
        process.Kill()
    return False


def install(debugger):
    state = _s()
    target = debugger.GetSelectedTarget()
    callbacks = [(va, name, "helper") for va, name in SITES.items()]
    callbacks += [(FINAL, "final", "final_call"), (CNR, "cnr", "cnr")]
    for va, name, callback in callbacks:
        before = target.GetNumBreakpoints()
        debugger.HandleCommand(f"breakpoint set --shlib libcp.dylib --address 0x{va:x}")
        if target.GetNumBreakpoints() <= before:
            state["errors"].append(f"failed to add {name} at 0x{va:x}")
            continue
        bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
        bp.SetScriptCallbackFunction(f"guide_origin_probe.{callback}")
        state["breakpoint_ids"][name] = bp.GetID()
    print("CNR_GUIDE_ORIGIN_INSTALLED", state["breakpoint_ids"])


def write_report(_debugger, path=""):
    out = path or _s().get("report_path")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(dict(_s()), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("CNR_GUIDE_ORIGIN_WROTE", out)
