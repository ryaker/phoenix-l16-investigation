import builtins
import json
import struct


SITES = {
    0x3F321A: "post_145980_box",
    0x3F352C: "pre_260e40_formula",
    0x3F3531: "post_260e40_formula",
    0x3F3599: "copy_scale_to_payload_2415d0",
    0x3F35F5: "copy_origin_to_payload_2415f0",
}


def reset(label="", sample_limit=4096, hit_cap=4096):
    builtins.l16_state448_box_formula = {
        "label": label,
        "sample_limit": sample_limit,
        "hit_cap": hit_cap,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
        "breakpoint_ids": {},
        "breakpoint_vas": {},
        "counts": {name: 0 for name in SITES.values()},
        "events": [],
        "disabled_after_cap": [],
        "errors": [],
        "sequence": 0,
    }


def _state():
    if not hasattr(builtins, "l16_state448_box_formula"):
        reset()
    return builtins.l16_state448_box_formula


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    if not addr:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u32(data, off=0):
    return struct.unpack_from("<I", data, off)[0]


def _i32(data, off=0):
    return struct.unpack_from("<i", data, off)[0]


def _u64(data, off=0):
    return struct.unpack_from("<Q", data, off)[0]


def _f32(data, off=0):
    return struct.unpack_from("<f", data, off)[0]


def _read_i32(process, addr):
    data = _read(process, addr, 4)
    return _i32(data) if data is not None else None


def _read_ptr(process, addr):
    data = _read(process, addr, 8)
    return _u64(data) if data is not None else None


def _read_i32_list(process, addr, count):
    data = _read(process, addr, 4 * count)
    if data is None:
        return None
    return [_i32(data, off) for off in range(0, len(data), 4)]


def _read_u32_words(process, addr, count):
    data = _read(process, addr, 4 * count)
    if data is None:
        return None
    return [_u32(data, off) for off in range(0, len(data), 4)]


def _read_f32_list(process, addr, count):
    data = _read(process, addr, 4 * count)
    if data is None:
        return None
    return [_f32(data, off) for off in range(0, len(data), 4)]


def _read_hex(process, addr, size):
    data = _read(process, addr, size)
    return data.hex() if data is not None else None


def _object_block(process, obj):
    data = _read(process, obj + 0x10C, 0x20) if obj else None
    if data is None:
        return {"object": obj, "read_ok": False}
    return {
        "object": obj,
        "read_ok": True,
        "i32_0x10c": _i32(data, 0x00),
        "i32_0x110": _i32(data, 0x04),
        "i32_0x114": _i32(data, 0x08),
        "i32_0x118": _i32(data, 0x0C),
        "u32_0x11c": _u32(data, 0x10),
        "u32_0x120": _u32(data, 0x14),
        "f32_0x124": _f32(data, 0x18),
        "f32_0x128": _f32(data, 0x1C),
        "raw_0x10c_0x12c": data.hex(),
    }


def _key_from_ptr(process, ptr):
    return _read_i32(process, ptr) if ptr else None


def _key_from_stack(process, rbp):
    key_ptr = _read_ptr(process, rbp - 0x818)
    return {
        "key_ptr_rbp_minus_0x818": key_ptr,
        "key": _key_from_ptr(process, key_ptr),
    }


def _libcp_base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                return base
    return None


def _module_va(target, pc):
    base = _libcp_base(target)
    if base is not None and pc >= base:
        return pc - base
    return None


def _registers(frame):
    names = ("rax", "rbx", "rcx", "rdx", "rdi", "rsi", "r8", "r14", "r15", "rbp", "rsp")
    return {name: _u(frame, name) for name in names}


def _stack(thread, max_frames=8):
    target = thread.GetProcess().GetTarget()
    frames = []
    for index in range(min(thread.GetNumFrames(), max_frames)):
        frame = thread.GetFrameAtIndex(index)
        frames.append(
            {
                "index": index,
                "pc": frame.GetPC(),
                "libcp_va": _module_va(target, frame.GetPC()),
                "function": frame.GetFunctionName(),
            }
        )
    return frames


def _packet_for_site(process, regs, name):
    rbp = regs["rbp"]
    if name == "post_145980_box":
        key_ptr = regs["r14"]
        obj = regs["rbx"]
        return {
            "key_ptr_r14": key_ptr,
            "key": _key_from_ptr(process, key_ptr),
            "object_rbx": obj,
            "object_block_0x10c": _object_block(process, obj),
            "box_addr_rbp_minus_0x520": rbp - 0x520,
            "box_i32_xyxy": _read_i32_list(process, rbp - 0x520, 4),
            "box_raw": _read_hex(process, rbp - 0x520, 0x10),
        }
    if name == "pre_260e40_formula":
        return {
            **_key_from_stack(process, rbp),
            "box_arg_rdi": regs["rdi"],
            "size_arg_rsi": regs["rsi"],
            "force_uniform_edx": regs["rdx"] & 0xFF,
            "origin_out_rcx": regs["rcx"],
            "scale_out_r8": regs["r8"],
            "box_i32_xyxy": _read_i32_list(process, regs["rdi"], 4),
            "size_i32_wh": _read_i32_list(process, regs["rsi"], 2),
            "origin_before_words": _read_u32_words(process, regs["rcx"], 2),
            "scale_before_words": _read_u32_words(process, regs["r8"], 2),
        }
    if name == "post_260e40_formula":
        return {
            **_key_from_stack(process, rbp),
            "box_addr_rbp_minus_0x520": rbp - 0x520,
            "size_addr_object_plus_0x114": regs["rbx"] + 0x114,
            "origin_out_rbp_minus_0x5d8": rbp - 0x5D8,
            "scale_out_rbp_minus_0x5d0": rbp - 0x5D0,
            "box_i32_xyxy": _read_i32_list(process, rbp - 0x520, 4),
            "size_i32_wh": _read_i32_list(process, regs["rbx"] + 0x114, 2),
            "origin_words": _read_u32_words(process, rbp - 0x5D8, 2),
            "origin_f32": _read_f32_list(process, rbp - 0x5D8, 2),
            "scale_words": _read_u32_words(process, rbp - 0x5D0, 2),
            "scale_f32": _read_f32_list(process, rbp - 0x5D0, 2),
        }
    if name == "copy_scale_to_payload_2415d0":
        return {
            "payload_addr": regs["rdi"],
            "source_addr": regs["rsi"],
            "node_key_from_payload_minus_0x04": _read_i32(process, regs["rdi"] - 4),
            "source_words": _read_u32_words(process, regs["rsi"], 2),
            "source_f32": _read_f32_list(process, regs["rsi"], 2),
            "payload_before_raw_0x00_0xa4": _read_hex(process, regs["rdi"], 0xA4),
        }
    if name == "copy_origin_to_payload_2415f0":
        return {
            "payload_addr": regs["rdi"],
            "source_addr": regs["rsi"],
            "node_key_from_payload_minus_0x04": _read_i32(process, regs["rdi"] - 4),
            "source_words": _read_u32_words(process, regs["rsi"], 2),
            "source_f32": _read_f32_list(process, regs["rsi"], 2),
            "payload_before_raw_0x00_0xa4": _read_hex(process, regs["rdi"], 0xA4),
        }
    return {}


def _append_event(event):
    state = _state()
    if len(state["events"]) < state["sample_limit"]:
        state["events"].append(event)


def _disable_breakpoint(debugger, bp_id):
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id) if bp_id else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def attach_existing(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    if target.GetNumBreakpoints() < len(SITES):
        state["errors"].append("not enough existing breakpoints")
        print("L16_STATE448_BOX_ATTACH_ERROR not enough existing breakpoints")
        return
    start = target.GetNumBreakpoints() - len(SITES)
    for index, va in enumerate(SITES):
        bp = target.GetBreakpointAtIndex(start + index)
        if not bp or not bp.IsValid():
            state["errors"].append(f"missing breakpoint for 0x{va:x}")
            continue
        bp.SetScriptCallbackFunction("box_formula_probe.hit")
        bp_id = bp.GetID()
        state["breakpoint_ids"][SITES[va]] = bp_id
        state["breakpoint_vas"][str(bp_id)] = va
    print("L16_STATE448_BOX_ATTACHED", json.dumps(state["breakpoint_ids"], sort_keys=True))


def hit(frame, bp_loc, internal_dict):
    state = _state()
    bp_id = bp_loc.GetBreakpoint().GetID()
    va = state["breakpoint_vas"].get(str(bp_id))
    if va is None:
        state["errors"].append(f"unknown breakpoint id {bp_id}")
        return False
    va = int(va)
    name = SITES[va]
    state["sequence"] += 1
    state["counts"][name] = state["counts"].get(name, 0) + 1
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    regs = _registers(frame)
    event = {
        "sequence": state["sequence"],
        "site_va": _module_va(target, frame.GetPC()),
        "site_name": name,
        "thread_id": thread.GetThreadID(),
        "registers": regs,
        "stack": _stack(thread),
    }
    try:
        event["packet"] = _packet_for_site(process, regs, name)
    except Exception as exc:
        state["errors"].append(f"packet error at 0x{va:x}: {exc}")
    _append_event(event)
    if state["counts"][name] >= state["hit_cap"]:
        _disable_breakpoint(frame.GetThread().GetProcess().GetTarget().GetDebugger(), bp_id)
        state["disabled_after_cap"].append(name)
    return False


def _breakpoint_hit_counts(debugger):
    target = debugger.GetSelectedTarget()
    out = {}
    for name, bp_id in _state().get("breakpoint_ids", {}).items():
        bp = target.FindBreakpointByID(bp_id)
        out[name] = bp.GetHitCount() if bp and bp.IsValid() else None
    return out


def _process_packet(debugger):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    if not process or not process.IsValid():
        return {"valid": False}
    return {
        "valid": True,
        "state": lldb.SBDebugger.StateAsCString(process.GetState()),
        "exit_status": process.GetExitStatus(),
    }


def drive_until_exit_or_step_cap(debugger, max_steps=80000):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process.IsValid() and process.GetState() == lldb.eStateStopped and steps < max_steps:
        steps += 1
        process.Continue()
    state["drive_steps"] += steps
    if process.IsValid() and process.GetState() == lldb.eStateStopped and steps >= max_steps:
        state["drive_hit_step_cap"] = True
    print("L16_STATE448_BOX_DRIVE_STEPS", steps)


def payload(debugger):
    return {
        "process": _process_packet(debugger),
        "breakpoint_hit_counts": _breakpoint_hit_counts(debugger),
        "sites": {f"0x{va:x}": name for va, name in SITES.items()},
        **_state(),
    }


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_STATE448_BOX_WROTE", path)
