"""Capture PatchNLM task geometry and pre-normalization boundary accumulators."""

import builtins
import json
import os
import struct


SITES = {
    0x3066D0: "parent",
    0x3070E0: "worker",
    0x307D90: "normalize_entry",
    0x307E9E: "normalize_return",
}


def reset(label=""):
    builtins.l16_nlm_topology_boundary = {
        "label": label,
        "breakpoint_ids": {},
        "counts": {name: 0 for name in SITES.values()},
        "parent": None,
        "workers": {},
        "normalizers": [],
        "pending_normalizers": {},
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_nlm_topology_boundary"):
        reset()
    return builtins.l16_nlm_topology_boundary


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u64(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<Q", raw)[0] if raw is not None else None


def _i32(process, address):
    raw = _read(process, address, 4)
    return struct.unpack("<i", raw)[0] if raw is not None else None


def _vec4(process, address):
    raw = _read(process, address, 16)
    return list(struct.unpack("<4f", raw)) if raw is not None else None


def _descriptor(process, address):
    raw = _read(process, address + 0x10, 0x18)
    if raw is None:
        return None
    width, height, _unk, stride, data = struct.unpack("<4iQ", raw)
    return {
        "address": address,
        "width": width,
        "height": height,
        "stride": stride,
        "data": data,
    }


def _corners(process, descriptor):
    if not descriptor or descriptor["data"] == 0:
        return None
    width = descriptor["width"]
    height = descriptor["height"]
    stride = descriptor["stride"]
    points = ((0, 0), (1, 0), (width - 2, 0), (width - 1, 0),
              (0, height - 1), (width - 1, height - 1))
    result = {}
    for x, y in points:
        if x < 0 or y < 0:
            continue
        address = descriptor["data"] + 16 * (y * stride + x)
        result[f"{x},{y}"] = _vec4(process, address)
    return result


def _disable(debugger, name):
    bp_id = _state()["breakpoint_ids"].get(name)
    if bp_id is None:
        return
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id)
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def site(frame, _bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    debugger = process.GetTarget().GetDebugger()
    pc = frame.GetPC()
    base = None
    for module in process.GetTarget().module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(process.GetTarget())
            break
    va = pc - base if base is not None else None
    name = SITES.get(va)
    if name is None:
        state["errors"].append(f"unexpected stop pc=0x{pc:x} va={va}")
        return False

    state["counts"][name] += 1
    tid = frame.GetThread().GetThreadID()

    if name == "parent" and state["parent"] is None:
        state["parent"] = {
            "arg_rdi": _u(frame, "rdi"),
            "arg_rsi": _u(frame, "rsi"),
            "arg_rdx": _u(frame, "rdx"),
            "coefficient_ptr": _u(frame, "rcx"),
            "window_r8d": _u(frame, "r8") & 0xFFFFFFFF,
            "step_r9d": _u(frame, "r9") & 0xFFFFFFFF,
        }
    elif name == "worker":
        callback = _u(frame, "rdi")
        task_ptr = _u64(process, callback)
        task_index = _i32(process, task_ptr) if task_ptr else None
        if task_index is not None and str(task_index) not in state["workers"]:
            rect_raw = _read(process, _u(frame, "rsi"), 16)
            rect = list(struct.unpack("<4i", rect_raw)) if rect_raw is not None else None
            image_ptr = _u64(process, callback + 0x08)
            random_vec_ptr = _u64(process, callback + 0x10)
            coefficient_ptr = _u64(process, callback + 0x18)
            step_ptr = _u64(process, callback + 0x20)
            source_ptr = _u64(process, callback + 0x28)
            window_ptr = _u64(process, callback + 0x30)
            range_ptr = _u64(process, callback + 0x38)
            accum_ptr = _u64(process, callback + 0x40)
            random_begin = _u64(process, random_vec_ptr) if random_vec_ptr else None
            random_end = _u64(process, random_vec_ptr + 8) if random_vec_ptr else None
            packet = {
                "task_index": task_index,
                "rect": rect,
                "image": _descriptor(process, image_ptr) if image_ptr else None,
                "source": _descriptor(process, source_ptr) if source_ptr else None,
                "range_scale": _descriptor(process, range_ptr) if range_ptr else None,
                "coefficient": _vec4(process, coefficient_ptr) if coefficient_ptr else None,
                "step": _i32(process, step_ptr) if step_ptr else None,
                "window": _i32(process, window_ptr) if window_ptr else None,
                "random_begin": random_begin,
                "random_end": random_end,
                "random_prefix": list(_read(process, random_begin, 16) or b""),
                "accumulator_address": accum_ptr,
            }
            state["workers"][str(task_index)] = packet
        if all(str(index) in state["workers"] for index in range(4)):
            _disable(debugger, name)

    elif name == "normalize_entry" and not state["normalizers"]:
        owner = _u(frame, "rdi")
        output_ptr = _u64(process, owner + 0x08)
        preserve_ptr = _u64(process, owner + 0x10)
        weight_ptr = _u64(process, owner + 0x18)
        output = _descriptor(process, output_ptr) if output_ptr else None
        preserve = _descriptor(process, preserve_ptr) if preserve_ptr else None
        weight = _descriptor(process, weight_ptr) if weight_ptr else None
        packet = {
            "thread_id": tid,
            "row_start": _i32(process, _u(frame, "rsi")),
            "row_end": _i32(process, _u(frame, "rdx")),
            "output": output,
            "preserve": preserve,
            "weight": weight,
            "before": {
                "output": _corners(process, output),
                "preserve": _corners(process, preserve),
                "weight": _corners(process, weight),
            },
        }
        state["pending_normalizers"][str(tid)] = packet
        _disable(debugger, name)

    elif name == "normalize_return":
        packet = state["pending_normalizers"].pop(str(tid), None)
        if packet is not None:
            packet["after_output"] = _corners(process, packet["output"])
            state["normalizers"].append(packet)
            _disable(debugger, name)
    return False


def install(debugger, selected="all"):
    target = debugger.GetSelectedTarget()
    for va, name in SITES.items():
        if selected != "all" and name != selected:
            continue
        before = target.GetNumBreakpoints()
        debugger.HandleCommand(f"breakpoint set --shlib libcp.dylib --address 0x{va:x}")
        if target.GetNumBreakpoints() <= before:
            _state()["errors"].append(f"failed to create {name}")
            continue
        bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
        bp.SetScriptCallbackFunction("nlm_topology_boundary_probe.site")
        _state()["breakpoint_ids"][name] = bp.GetID()
    print("L16_NLM_TOPOLOGY_BOUNDARY_INSTALLED", selected,
          _state()["breakpoint_ids"], flush=True)


def drive(debugger, cap=50000):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process.IsValid() and process.GetState() == lldb.eStateStopped and steps < cap:
        steps += 1
        process.Continue()
    _state()["drive_steps"] = steps
    print("L16_NLM_TOPOLOGY_BOUNDARY_DRIVE_STEPS", steps)


def write_report(debugger, path):
    process = debugger.GetSelectedTarget().GetProcess()
    payload = {
        **_state(),
        "process": {
            "valid": bool(process and process.IsValid()),
            "exit_status": process.GetExitStatus() if process and process.IsValid() else None,
        },
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_NLM_TOPOLOGY_BOUNDARY_WROTE", path)
