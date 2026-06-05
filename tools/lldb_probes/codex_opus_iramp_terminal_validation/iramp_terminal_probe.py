import builtins
import json
import math
import struct


SITES = {
    0x365960: "entry_365960",
    0x3661B0: "inner_3661b0",
    0x36930F: "sentinel_cmp_36930f",
    0x369E91: "tuple_score_store_369e91",
    0x36A938: "reciprocal_36a938",
    0x36AA57: "weighted_store_36aa57",
    0x36E511: "score_mul_36e511",
}


def reset(label="", sample_cap_per_site=8):
    builtins.l16_codex_iramp_terminal = {
        "label": label,
        "sample_cap_per_site": sample_cap_per_site,
        "breakpoint_ids": {},
        "breakpoint_vas": {},
        "counts": {f"0x{va:x}": 0 for va in SITES},
        "events": [],
        "disabled_after_cap": [],
        "errors": [],
        "sequence": 0,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
    }


def _state():
    if not hasattr(builtins, "l16_codex_iramp_terminal"):
        reset()
    return builtins.l16_codex_iramp_terminal


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


def _u64(process, addr):
    data = _read(process, addr, 8)
    return struct.unpack_from("<Q", data, 0)[0] if data is not None else None


def _i32(process, addr):
    data = _read(process, addr, 4)
    return struct.unpack_from("<i", data, 0)[0] if data is not None else None


def _u32(value):
    return value & 0xFFFFFFFF


def _i32_from_u(value):
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def _f32_tuple(process, addr, count):
    data = _read(process, addr, 4 * count)
    if data is None:
        return None
    return list(struct.unpack_from("<" + "f" * count, data, 0))


def _xmm_f32s(frame, name):
    data = frame.FindRegister(name).GetData()
    error = builtins.__import__("lldb").SBError()
    out = []
    for index in range(4):
        if not data.IsValid():
            out.append(None)
            continue
        value = data.GetFloat(error, index * 4)
        out.append(value if error.Success() else None)
    return out


def _xmm_low(frame, name):
    vals = _xmm_f32s(frame, name)
    return vals[0] if vals else None


def _vector_info(process, addr, item_sizes):
    begin = _u64(process, addr)
    end = _u64(process, addr + 0x8)
    if begin is None or end is None or end < begin:
        return {"addr": addr, "begin": begin, "end": end, "diff": None}
    diff = end - begin
    info = {"addr": addr, "begin": begin, "end": end, "diff": diff}
    for item_size in item_sizes:
        key = f"count_{item_size:#x}"
        info[key] = diff // item_size if item_size and diff % item_size == 0 else None
    return info


def _roi_i32x4(process, addr):
    if not addr:
        return None
    vals = [_i32(process, addr + i * 4) for i in range(4)]
    return vals if all(v is not None for v in vals) else None


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


def _entry_packet(frame, process, regs):
    rcx = regs["rcx"]
    r8 = regs["r8"]
    r9 = regs["r9"]
    return {
        "src1_rsi": regs["rsi"],
        "src2_rdx": regs["rdx"],
        "source_vector_rcx": _vector_info(process, rcx, (8, 16)),
        "warp_vector_r8": _vector_info(process, r8, (16, 0x50)),
        "roi_r9_i32x4": _roi_i32x4(process, r9),
        "scale_xmm0": _xmm_low(frame, "xmm0"),
    }


def _inner_packet(process, regs):
    closure = regs["rdi"]
    roi = regs["rsi"]
    return {
        "closure_rdi": closure,
        "roi_rsi_i32x4": _roi_i32x4(process, roi),
        "closure_plus_0x08": _u64(process, closure + 0x8),
        "closure_plus_0x10": _u64(process, closure + 0x10),
        "closure_source_vector_0x18": _vector_info(process, closure + 0x18, (8, 16)),
        "closure_warp_vector_0x20": _vector_info(process, closure + 0x20, (16, 0x50)),
        "closure_output_image_0x38": _u64(process, closure + 0x38),
    }


def _sentinel_packet(process, regs):
    rbp = regs["rbp"]
    eax = _u32(regs["rax"])
    begin = _u64(process, rbp - 0x1800)
    end = _u64(process, rbp - 0x17F8)
    diff = end - begin if begin is not None and end is not None and end >= begin else None
    return {
        "eax_u32_hex": f"0x{eax:08x}",
        "eax_s32": _i32_from_u(eax),
        "is_0x80000000": eax == 0x80000000,
        "r12_indexmap_base": regs["r12"],
        "rsi_linear_index": regs["rsi"],
        "rcx_contributor_index": regs["rcx"],
        "rdx_contributor_byte_offset": regs["rdx"],
        "partner_begin": begin,
        "partner_end": end,
        "partner_diff": diff,
        "partner_count_0x280": diff // 0x280 if diff is not None and diff % 0x280 == 0 else None,
    }


def _tuple_packet(frame, regs):
    addr = regs["rcx"] + regs["rax"] * 4 + 0x8
    return {
        "score_xmm0": _xmm_low(frame, "xmm0"),
        "tuple_score_store_addr": addr,
        "tuple_base_rcx": regs["rcx"],
        "tuple_index_times3_rax": regs["rax"],
    }


def _reciprocal_packet(frame, regs):
    x2 = _xmm_f32s(frame, "xmm2")
    low = x2[0] if x2 else None
    return {
        "xmm2_before_rcpss": x2,
        "predicted_exact_reciprocal_low": (1.0 / low) if low not in (None, 0.0) else None,
    }


def _weighted_store_packet(frame, process, regs):
    dest_addr = regs["rsi"] + regs["rdi"]
    return {
        "dest_addr_rsi_plus_rdi": dest_addr,
        "result_xmm1_before_store": _xmm_f32s(frame, "xmm1"),
        "dest_vec4_before_store": _f32_tuple(process, dest_addr, 4),
        "byte_offset_rdi": regs["rdi"],
        "dest_base_rsi": regs["rsi"],
    }


def _score_mul_packet(frame):
    x0 = _xmm_low(frame, "xmm0")
    x1 = _xmm_low(frame, "xmm1")
    product = x0 * x1 if x0 is not None and x1 is not None else None
    return {
        "factor_xmm0": x0,
        "factor_xmm1": x1,
        "product": product,
        "sqrt_product": math.sqrt(product) if product is not None and product >= 0 else None,
    }


def _packet_for_site(frame, process, regs, site_name):
    if site_name == "entry_365960":
        return _entry_packet(frame, process, regs)
    if site_name == "inner_3661b0":
        return _inner_packet(process, regs)
    if site_name == "sentinel_cmp_36930f":
        return _sentinel_packet(process, regs)
    if site_name == "tuple_score_store_369e91":
        return _tuple_packet(frame, regs)
    if site_name == "reciprocal_36a938":
        return _reciprocal_packet(frame, regs)
    if site_name == "weighted_store_36aa57":
        return _weighted_store_packet(frame, process, regs)
    if site_name == "score_mul_36e511":
        return _score_mul_packet(frame)
    return {}


def _registers(frame):
    names = ("rax", "rbx", "rcx", "rdx", "rdi", "rsi", "r8", "r9", "r10", "r12", "r13", "r14", "r15", "rbp", "rsp")
    return {name: _u(frame, name) for name in names}


def _disable_breakpoint(debugger, bp_id):
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id) if bp_id else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def attach_existing(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    if target.GetNumBreakpoints() < len(SITES):
        state["errors"].append("not enough existing breakpoints")
        print("L16_CODEX_IRAMP_ATTACH_ERROR not enough existing breakpoints")
        return
    start = target.GetNumBreakpoints() - len(SITES)
    for index, va in enumerate(SITES):
        bp = target.GetBreakpointAtIndex(start + index)
        if not bp or not bp.IsValid():
            state["errors"].append(f"missing breakpoint for 0x{va:x}")
            continue
        bp.SetScriptCallbackFunction("iramp_terminal_probe.hit")
        bp_id = bp.GetID()
        state["breakpoint_ids"][f"0x{va:x}"] = bp_id
        state["breakpoint_vas"][str(bp_id)] = va
    print("L16_CODEX_IRAMP_ATTACHED", json.dumps(state["breakpoint_ids"], sort_keys=True))


def hit(frame, bp_loc, internal_dict):
    state = _state()
    bp_id = bp_loc.GetBreakpoint().GetID()
    va = state["breakpoint_vas"].get(str(bp_id))
    if va is None:
        state["errors"].append(f"unknown breakpoint id {bp_id}")
        return False
    key = f"0x{va:x}"
    site_name = SITES.get(va)
    state["sequence"] += 1
    state["counts"][key] = state["counts"].get(key, 0) + 1

    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    regs = _registers(frame)
    event = {
        "sequence": state["sequence"],
        "site_name": site_name,
        "site_va": _module_va(target, frame.GetPC()),
        "thread_id": thread.GetThreadID(),
        "registers": regs,
        "stack": _stack(thread),
    }
    try:
        event["packet"] = _packet_for_site(frame, process, regs, site_name)
    except Exception as exc:
        state["errors"].append(f"packet error at 0x{va:x}: {exc}")
    state["events"].append(event)

    if state["counts"][key] >= state["sample_cap_per_site"]:
        _disable_breakpoint(target.GetDebugger(), bp_id)
        state["disabled_after_cap"].append(key)
    return False


def drive_until_exit_or_step_cap(debugger, step_cap=60000):
    state = _state()
    lldb = builtins.__import__("lldb")
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    while process and process.IsValid() and process.GetState() not in (lldb.eStateExited, lldb.eStateDetached):
        if state["drive_steps"] >= step_cap:
            state["drive_hit_step_cap"] = True
            break
        state["drive_steps"] += 1
        process.Continue()


def _breakpoint_hit_counts(debugger):
    target = debugger.GetSelectedTarget()
    out = {}
    for key, bp_id in _state().get("breakpoint_ids", {}).items():
        bp = target.FindBreakpointByID(bp_id)
        out[key] = bp.GetHitCount() if bp and bp.IsValid() else None
    return out


def write_report(debugger, path):
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    state["breakpoint_hit_counts"] = _breakpoint_hit_counts(debugger)
    if process and process.IsValid():
        state["process"] = {
            "state": str(process.GetState()),
            "exit_status": process.GetExitStatus(),
            "exit_description": process.GetExitDescription(),
        }
    with open(path, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)
    print("L16_CODEX_IRAMP_REPORT", path)
