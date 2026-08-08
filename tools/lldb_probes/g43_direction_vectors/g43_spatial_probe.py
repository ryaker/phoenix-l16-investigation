"""Capture exact spatial predecessors for the four SGM paths in each sweep."""
import builtins
import hashlib
import json
import struct


ANCHOR = 0x276860
CURRENT_INDEX = 0x2774B5
PREDECESSOR_LOAD = 0x27787A


def reset(label, desired_sign, report_cap=32):
    builtins.l16g43sp = {
        "label": label,
        "desired_sign": desired_sign,
        "report_cap": report_cap,
        "anchor_hits": 0,
        "armed": False,
        "done": False,
        "layer_ptr": None,
        "guidance_width": None,
        "guidance_height": None,
        "guidance_stride": None,
        "direction_offsets_i32": None,
        "captures": [],
        "errors": [],
        "_base": None,
        "anchor_bp": None,
        "current_bp": None,
        "predecessor_bp": None,
        "_current_by_tid": {},
    }


def _s():
    return builtins.l16g43sp


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _rd(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    return data if error.Success() and data and len(data) == size else None


def _u32(process, address):
    data = _rd(process, address, 4)
    return struct.unpack("<I", data)[0] if data else None


def _i32(process, address):
    data = _rd(process, address, 4)
    return struct.unpack("<i", data)[0] if data else None


def _u64(process, address):
    data = _rd(process, address, 8)
    return struct.unpack("<Q", data)[0] if data else None


def _i32x(process, address, count):
    data = _rd(process, address, 4 * count)
    return list(struct.unpack("<%di" % count, data)) if data else None


def _signed32(value):
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def _base(target):
    state = _s()
    if state["_base"] is not None:
        return state["_base"]
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                state["_base"] = base
                return base
    return None


def _va(target, pc):
    base = _base(target)
    return pc - base if base is not None else None


def hit(frame, bp_loc, internal_dict):
    state = _s()
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    va = _va(target, frame.GetPC())
    if va == ANCHOR:
        state["anchor_hits"] += 1
        layer = _u(frame, "rdi")
        sign = _signed32(_u(frame, "rcx"))
        guidance = _u64(process, layer + 0x288)
        width = _u32(process, (guidance or 0) + 0x10)
        height = _u32(process, (guidance or 0) + 0x14)
        if (
            not state["armed"]
            and sign == state["desired_sign"]
            and (width, height) == (2080, 1560)
        ):
            direction_ptr = _u(frame, "r8")
            state.update({
                "armed": True,
                "layer_ptr": layer,
                "guidance_width": width,
                "guidance_height": height,
                "guidance_stride": _u32(process, guidance + 0x18),
                "direction_offsets_i32": _i32x(process, direction_ptr, 4),
            })
            bp = target.BreakpointCreateByAddress(_base(target) + PREDECESSOR_LOAD)
            bp.SetScriptCallbackFunction("g43_spatial_probe.hit")
            state["predecessor_bp"] = bp.GetID()
            bp = target.BreakpointCreateByAddress(_base(target) + CURRENT_INDEX)
            bp.SetScriptCallbackFunction("g43_spatial_probe.hit")
            state["current_bp"] = bp.GetID()
            anchor = target.FindBreakpointByID(state["anchor_bp"])
            if anchor and anchor.IsValid():
                anchor.SetEnabled(False)
        return False
    if va == CURRENT_INDEX:
        current_index = _u(frame, "rcx")
        stride = state["guidance_stride"]
        state["_current_by_tid"][str(frame.GetThread().GetThreadID())] = {
            "index": current_index,
            "x": current_index % stride,
            "y": current_index // stride,
        }
        return False
    if va != PREDECESSOR_LOAD or state["done"]:
        return False

    current = state["_current_by_tid"].get(str(frame.GetThread().GetThreadID()))
    stride = state["guidance_stride"]
    if current is None or stride is None:
        state["errors"].append("predecessor load without joined current index")
        return False
    x, y = current["x"], current["y"]
    if x < 2 or y < 2 or x >= state["guidance_width"] - 2 or y >= state["guidance_height"] - 2:
        return False

    current_index = current["index"]
    predecessor_index = _u(frame, "rdx") // 16
    delta = predecessor_index - current_index
    dy = min(range(-2, 3), key=lambda candidate: abs(delta - candidate * stride))
    dx = delta - dy * stride
    capture = {
        "path_index": _u(frame, "r14"),
        "direction_component_r11": _signed32(_u(frame, "r11")),
        "current_x": x,
        "current_y": y,
        "current_index": current_index,
        "predecessor_index": predecessor_index,
        "delta_index": delta,
        "dx": dx,
        "dy": dy,
    }
    state["captures"].append(capture)
    paths = {item["path_index"] for item in state["captures"]}
    if len(state["captures"]) >= state["report_cap"] and paths == {0, 1, 2, 3}:
        state["done"] = True
        process.Kill()
        return True
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    for index in range(target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(index)
        if not bp or not bp.IsValid() or bp.GetNumLocations() < 1:
            continue
        if bp.GetLocationAtIndex(0).GetAddress().GetFileAddress() == ANCHOR:
            bp.SetScriptCallbackFunction("g43_spatial_probe.hit")
            _s()["anchor_bp"] = bp.GetID()
    print("L16_G43_SPATIAL_ATTACHED")


def drive(debugger, max_steps=20000000):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process.IsValid() and process.GetState() == lldb.eStateStopped and steps < max_steps:
        steps += 1
        process.Continue()
    print("L16_G43_SPATIAL_DRIVE_DONE steps=%d" % steps)


def write_report(debugger, path):
    state = dict(_s())
    target = debugger.GetSelectedTarget()
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            state["libcp_sha256"] = hashlib.sha256(
                open(module.GetFileSpec().fullpath, "rb").read()
            ).hexdigest()
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_G43_SPATIAL_WROTE %s" % path)
