import builtins
import json
import struct


SITES = {
    0x1F0D36: "after_1f0b00_vectors",
    0x1F96E0: "helper_entry_1f96e0",
    0x1F0EE5: "after_optional_helper_k_copy",
    0x1F0FED: "before_f3350_scale",
    0x1F1047: "after_f3350_scale",
    0x1F1328: "selector0_f33d0_call",
    0x1F134B: "selector1_f33d0_call",
}


def reset(label="", sample_limit=512, hit_cap=4096):
    builtins.l16_1f0ce0_k_source_trace = {
        "label": label,
        "sample_limit": sample_limit,
        "hit_cap": hit_cap,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
        "breakpoint_ids": {},
        "breakpoint_vas": {},
        "counts": {f"0x{va:x}": 0 for va in SITES},
        "events": [],
        "disabled_after_cap": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_1f0ce0_k_source_trace"):
        reset()
    return builtins.l16_1f0ce0_k_source_trace


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _i32(value):
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def _read(process, addr, size):
    if not addr:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _read_u8(process, addr):
    data = _read(process, addr, 1)
    return data[0] if data is not None else None


def _read_i32(process, addr):
    data = _read(process, addr, 4)
    return struct.unpack_from("<i", data, 0)[0] if data is not None else None


def _read_u32(process, addr):
    data = _read(process, addr, 4)
    return struct.unpack_from("<I", data, 0)[0] if data is not None else None


def _read_i32_list(process, addr, count):
    data = _read(process, addr, 4 * count)
    if data is None:
        return None
    return list(struct.unpack_from("<" + "i" * count, data, 0))


def _read_u32_list(process, addr, count):
    data = _read(process, addr, 4 * count)
    if data is None:
        return None
    return list(struct.unpack_from("<" + "I" * count, data, 0))


def _read_f32_list(process, addr, count):
    data = _read(process, addr, 4 * count)
    if data is None:
        return None
    return list(struct.unpack_from("<" + "f" * count, data, 0))


def _read_f64_list(process, addr, count):
    data = _read(process, addr, 8 * count)
    if data is None:
        return None
    return list(struct.unpack_from("<" + "d" * count, data, 0))


def _read_hex(process, addr, size):
    data = _read(process, addr, size)
    return data.hex() if data is not None else None


def _vector_header(process, addr):
    begin = _read(process, addr, 8)
    end = _read(process, addr + 8, 8)
    cap = _read(process, addr + 16, 8)
    if begin is None or end is None or cap is None:
        return None
    begin = struct.unpack_from("<Q", begin, 0)[0]
    end = struct.unpack_from("<Q", end, 0)[0]
    cap = struct.unpack_from("<Q", cap, 0)[0]
    return {
        "begin": begin,
        "end": end,
        "cap": cap,
        "byte_span": end - begin if end >= begin else None,
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
    names = (
        "rax",
        "rbx",
        "rcx",
        "rdx",
        "rdi",
        "rsi",
        "r8",
        "r9",
        "r14",
        "r15",
        "rbp",
        "rsp",
    )
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


def _object_packet(process, obj):
    if not obj:
        return None
    accessor = obj + 0x10C
    return {
        "object": obj,
        "active_u8_0x30": _read_u8(process, obj + 0x30),
        "u32_0x54": _read_u32(process, obj + 0x54),
        "i32_0x54": _read_i32(process, obj + 0x54),
        "key_i32_0x60": _read_i32(process, obj + 0x60),
        "stage_i32_0x64": _read_i32(process, obj + 0x64),
        "mode_i32_0x00": _read_i32(process, obj),
        "accessor_0x10c": {
            "raw_0x10c_0x12c": _read_hex(process, accessor, 0x20),
            "i32_0x114": _read_i32(process, obj + 0x114),
            "i32_0x118": _read_i32(process, obj + 0x118),
            "i32_0x11c": _read_i32(process, obj + 0x11C),
            "i32_0x120": _read_i32(process, obj + 0x120),
            "scale_x_f32_0x124": (_read_f32_list(process, obj + 0x124, 1) or [None])[0],
            "scale_y_f32_0x128": (_read_f32_list(process, obj + 0x128, 1) or [None])[0],
        },
    }


def _k_stack(process, rbp):
    addr = rbp - 0xB8
    return {
        "addr": addr,
        "raw_u32x9": _read_u32_list(process, addr, 9),
        "f32x9": _read_f32_list(process, addr, 9),
        "raw_hex": _read_hex(process, addr, 0x24),
    }


def _pose_stack(process, rbp):
    addr = rbp - 0x278
    return {
        "addr": addr,
        "raw_u32x9": _read_u32_list(process, addr, 9),
        "f32x9": _read_f32_list(process, addr, 9),
        "raw_hex": _read_hex(process, addr, 0x24),
    }


def _triple_stack(process, rbp):
    addr = rbp - 0x288
    return {
        "addr": addr,
        "raw_u32x3": _read_u32_list(process, addr, 3),
        "f32x3": _read_f32_list(process, addr, 3),
        "raw_hex": _read_hex(process, addr, 0x0C),
    }


def _vector_sources(process, rbp):
    k_vec = _vector_header(process, rbp - 0x30)
    aux_vec = _vector_header(process, rbp - 0x50)
    helper_vec = _vector_header(process, rbp - 0x70)
    first_k9 = None
    if k_vec and k_vec["begin"] and k_vec["end"] >= k_vec["begin"] + 72:
        first_k9 = _read_f64_list(process, k_vec["begin"], 9)
    return {
        "k_vector_rbp_minus_0x30": k_vec,
        "aux_vector_rbp_minus_0x50": aux_vec,
        "helper_vector_rbp_minus_0x70": helper_vec,
        "first_k_vector_f64x9": first_k9,
    }


def _helper_output(process, rbp):
    addr = rbp - 0x188
    return {
        "addr": addr,
        "f64x9": _read_f64_list(process, addr, 9),
    }


def _helper_record_vector(process, header_addr, max_records=4):
    header = _vector_header(process, header_addr)
    records = []
    if header and header["begin"] and header["end"] and header["end"] >= header["begin"]:
        span = header["end"] - header["begin"]
        count = span // 0x48
        for index in range(min(count, max_records)):
            addr = header["begin"] + index * 0x48
            records.append({"index": index, "addr": addr, "f64x9": _read_f64_list(process, addr, 9)})
        header["record_count_0x48"] = count
    return {"header": header, "records": records}


def _helper_scalar_vector(process, header_addr, max_values=16):
    header = _vector_header(process, header_addr)
    values = None
    if header and header["begin"] and header["end"] and header["end"] >= header["begin"]:
        count = (header["end"] - header["begin"]) // 4
        values = _read_i32_list(process, header["begin"], min(count, max_values))
        header["i32_count"] = count
    return {"header": header, "i32_values": values}


def _helper_entry(process, regs):
    src = regs["rsi"]
    return {
        "arg_rdi_output": regs["rdi"],
        "arg_rsi_source": src,
        "arg_edx_scalar": _i32(regs["rdx"]),
        "record_vector_source_plus_0x00": _helper_record_vector(process, src),
        "scalar_vector_source_plus_0x30": _helper_scalar_vector(process, src + 0x30),
    }


def _event_payload(process, regs, site_va):
    rbp = regs["rbp"]
    obj = regs["r14"]
    payload = {
        "object": _object_packet(process, obj),
        "k_stack": _k_stack(process, rbp),
    }
    if site_va == 0x1F0D36:
        payload["vector_sources"] = _vector_sources(process, rbp)
    if site_va == 0x1F96E0:
        payload["helper_entry"] = _helper_entry(process, regs)
    if site_va in (0x1F0EE5, 0x1F0FED, 0x1F1047, 0x1F1328, 0x1F134B):
        payload["pose_stack"] = _pose_stack(process, rbp)
        payload["triple_stack"] = _triple_stack(process, rbp)
    if site_va == 0x1F0EE5:
        payload["helper_output"] = _helper_output(process, rbp)
    if site_va in (0x1F1328, 0x1F134B):
        payload["selector"] = 0 if site_va == 0x1F1328 else 1
        payload["arg_rdi_object"] = regs["rdi"]
        payload["arg_rsi_k"] = regs["rsi"]
        payload["arg_rdx_pose"] = regs["rdx"]
        payload["arg_rcx_triple"] = regs["rcx"]
        payload["arg_r8d_selector"] = _i32(regs["r8"])
    return payload


def _disable_breakpoint(debugger, bp_id):
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id) if bp_id else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def attach_existing(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    if target.GetNumBreakpoints() < len(SITES):
        state["errors"].append("not enough existing breakpoints")
        print("L16_1F0CE0_TRACE_ATTACH_ERROR not enough existing breakpoints")
        return
    start = target.GetNumBreakpoints() - len(SITES)
    for index, va in enumerate(SITES):
        bp = target.GetBreakpointAtIndex(start + index)
        if not bp or not bp.IsValid():
            state["errors"].append(f"missing breakpoint for 0x{va:x}")
            continue
        bp.SetScriptCallbackFunction("k_source_trace_probe.hit")
        bp_id = bp.GetID()
        state["breakpoint_ids"][f"0x{va:x}"] = bp_id
        state["breakpoint_vas"][str(bp_id)] = va
    print("L16_1F0CE0_TRACE_ATTACHED", json.dumps(state["breakpoint_ids"], sort_keys=True))


def _append_event(event):
    state = _state()
    if len(state["events"]) < state["sample_limit"]:
        state["events"].append(event)


def hit(frame, bp_loc, internal_dict):
    state = _state()
    bp_id = bp_loc.GetBreakpoint().GetID()
    va = state["breakpoint_vas"].get(str(bp_id))
    if va is None:
        state["errors"].append(f"unknown breakpoint id {bp_id}")
        return False
    key = f"0x{va:x}"
    state["counts"][key] = state["counts"].get(key, 0) + 1
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    regs = _registers(frame)
    event = {
        "site_va": _module_va(target, frame.GetPC()),
        "site_name": SITES.get(va),
        "thread_id": thread.GetThreadID(),
        "registers": regs,
        "stack": _stack(thread),
        "trace": _event_payload(process, regs, va),
    }
    _append_event(event)
    if state["counts"][key] >= state["hit_cap"]:
        state["disabled_after_cap"].append(key)
        _disable_breakpoint(frame.GetThread().GetProcess().GetTarget().GetDebugger(), bp_id)
    return False


def drive_until_exit_or_step_cap(debugger, max_steps=60000):
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process and process.IsValid() and process.GetState() != 10 and steps < max_steps:
        process.Continue()
        steps += 1
    state["drive_steps"] = steps
    state["drive_hit_step_cap"] = steps >= max_steps and process.GetState() != 10
    print(
        "L16_1F0CE0_TRACE_DRIVE",
        json.dumps(
            {
                "steps": state["drive_steps"],
                "step_cap": state["drive_hit_step_cap"],
                "state": int(process.GetState()) if process and process.IsValid() else None,
            },
            sort_keys=True,
        ),
    )


def write_report(debugger, path):
    state = _state()
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    state["process"] = {
        "state": int(process.GetState()) if process and process.IsValid() else None,
        "exit_status": process.GetExitStatus() if process and process.IsValid() else None,
        "exit_description": process.GetExitDescription() if process and process.IsValid() else None,
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
    print("L16_1F0CE0_TRACE_REPORT", path)
