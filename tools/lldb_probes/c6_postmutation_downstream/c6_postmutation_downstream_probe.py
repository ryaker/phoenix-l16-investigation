import builtins
import json
import os
import struct


SITES = {
    0x3B22A6: "context_c8_reload",
    0x3B22B2: "after_second_state_code_call",
    0x3B22C3: "fallback_scale_call_3c8c00",
    0x3B22E4: "scaled_width_store",
    0x3B22EE: "scaled_height_store",
    0x3B2313: "context_4b0_read_before",
    0x3B231A: "context_4b0_read_after",
    0x3B2339: "rect_vector_builder_call",
    0x3C8D00: "rect_vector_builder_entry",
    0x3C8DD5: "builder_scaled_width_write",
    0x3C8DD8: "builder_scaled_height_write",
    0x3C8EAB: "builder_first_rect_done",
    0x3C8F42: "builder_return",
}


def reset(label="", event_limit=512, site_hit_cap=4096):
    builtins.l16_c6_postmutation_downstream = {
        "label": label,
        "event_limit": event_limit,
        "site_hit_cap": site_hit_cap,
        "sites": {f"0x{va:x}": name for va, name in SITES.items()},
        "breakpoint_ids": {},
        "counts": {
            f"0x{va:x}": {
                "name": name,
                "hits": 0,
                "recorded": 0,
                "read_errors": 0,
                "disabled_at_cap": False,
            }
            for va, name in SITES.items()
        },
        "events": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_c6_postmutation_downstream"):
        reset()
    return builtins.l16_c6_postmutation_downstream


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


def _u8(process, addr):
    data = _read(process, addr, 1)
    return data[0] if data is not None else None


def _u32(process, addr):
    data = _read(process, addr, 4)
    return struct.unpack_from("<I", data, 0)[0] if data is not None else None


def _i32(process, addr):
    data = _read(process, addr, 4)
    return struct.unpack_from("<i", data, 0)[0] if data is not None else None


def _u64(process, addr):
    data = _read(process, addr, 8)
    return struct.unpack_from("<Q", data, 0)[0] if data is not None else None


def _rect(process, addr):
    if not addr:
        return None
    data = _read(process, addr, 16)
    if data is None:
        return None
    return list(struct.unpack_from("<iiii", data, 0))


def _state_obj(process, addr):
    if not addr:
        return None
    return {
        "state_obj": addr,
        "field_0x0_u32": _u32(process, addr),
        "field_0x4_u8": _u8(process, addr + 4),
    }


def _pair_i32(process, addr):
    if not addr:
        return None
    return [_i32(process, addr), _i32(process, addr + 4)]


def _vector_rects(process, vec_addr, max_items=8):
    if not vec_addr:
        return None
    begin = _u64(process, vec_addr)
    end = _u64(process, vec_addr + 8)
    cap = _u64(process, vec_addr + 16)
    count = None
    rects = []
    if begin is not None and end is not None and end >= begin:
        count = (end - begin) // 0x10
        for index in range(min(count, max_items)):
            rects.append(_rect(process, begin + index * 0x10))
    return {
        "vector_addr": vec_addr,
        "begin": begin,
        "end": end,
        "cap": cap,
        "count_if_0x10": count,
        "rects": rects,
    }


def _libcp_base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                return base
    return None


def _module_va(target, pc):
    addr = target.ResolveLoadAddress(pc)
    if addr and addr.IsValid():
        module = addr.GetModule()
        if module and str(module.GetFileSpec().GetFilename()) != "libcp.dylib":
            return None
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


def _site_packet(frame, site_va):
    process = frame.GetThread().GetProcess()
    rbp = _u(frame, "rbp")
    if site_va == 0x3B22A6:
        ctx = _u(frame, "r15")
        state_obj = _u64(process, ctx + 0xC8)
        return {
            "ctx": ctx,
            "ctx_c8": state_obj,
            "state": _state_obj(process, state_obj),
        }
    if site_va == 0x3B22B2:
        return {"state_code_eax": _u(frame, "rax") & 0xFFFFFFFF}
    if site_va == 0x3B22C3:
        return {"ctx": _u(frame, "r15"), "branch": "fallback_scale_3c8c00"}
    if site_va == 0x3B22E4:
        return {
            "scaled_width_eax": _u(frame, "rax") & 0xFFFFFFFF,
            "raw_dims": [_i32(process, rbp - 0x1A8), _i32(process, rbp - 0x1A4)],
        }
    if site_va == 0x3B22EE:
        return {
            "scaled_height_eax": _u(frame, "rax") & 0xFFFFFFFF,
            "scaled_width_stored": _i32(process, rbp - 0x1B0),
            "raw_dims": [_i32(process, rbp - 0x1A8), _i32(process, rbp - 0x1A4)],
        }
    if site_va == 0x3B2313:
        ctx = _u(frame, "r15")
        return {"ctx": ctx, "ctx_4b0": _u32(process, ctx + 0x4B0)}
    if site_va == 0x3B231A:
        return {"r8d_after_ctx_4b0_read": _u(frame, "r8") & 0xFFFFFFFF}
    if site_va == 0x3B2339:
        return _call_packet(frame)
    if site_va == 0x3C8D00:
        return _call_packet(frame)
    if site_va == 0x3C8DD5:
        ptr = _u(frame, "r15")
        return {
            "target_pair_ptr": ptr,
            "new_width_esi": _u(frame, "rsi") & 0xFFFFFFFF,
            "old_pair": _pair_i32(process, ptr),
        }
    if site_va == 0x3C8DD8:
        ptr = _u(frame, "r15")
        return {
            "target_pair_ptr": ptr,
            "new_height_ecx": _u(frame, "rcx") & 0xFFFFFFFF,
            "pair_after_width_write": _pair_i32(process, ptr),
        }
    if site_va == 0x3C8EAB:
        vec = _u(frame, "r13")
        return {
            "builder_level_code_r14d": _u(frame, "r14") & 0xFFFFFFFF,
            "output_vector": _vector_rects(process, vec),
        }
    if site_va == 0x3C8F42:
        vec = _u(frame, "r13")
        return {"output_vector": _vector_rects(process, vec)}
    return None


def _call_packet(frame):
    process = frame.GetThread().GetProcess()
    return {
        "out_vector_rdi": _u(frame, "rdi"),
        "ctx_rsi": _u(frame, "rsi"),
        "scaled_pair_rdx": _u(frame, "rdx"),
        "raw_pair_rcx": _u(frame, "rcx"),
        "level_code_r8d": _u(frame, "r8") & 0xFFFFFFFF,
        "rect_r9": _u(frame, "r9"),
        "scaled_pair": _pair_i32(process, _u(frame, "rdx")),
        "raw_pair": _pair_i32(process, _u(frame, "rcx")),
        "rect": _rect(process, _u(frame, "r9")),
    }


def install_breakpoints(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    for va in SITES:
        before = target.GetNumBreakpoints()
        debugger.HandleCommand(f"breakpoint set --shlib libcp.dylib --address 0x{va:x}")
        after = target.GetNumBreakpoints()
        if after <= before:
            state["errors"].append({"site": f"0x{va:x}", "error": "breakpoint not created"})
            continue
        bp = target.GetBreakpointAtIndex(after - 1)
        if not bp or not bp.IsValid():
            state["errors"].append({"site": f"0x{va:x}", "error": "invalid breakpoint"})
            continue
        bp.SetScriptCallbackFunction("c6_postmutation_downstream_probe.hit")
        state["breakpoint_ids"][str(bp.GetID())] = f"0x{va:x}"
    print("INSTALLED", len(state["breakpoint_ids"]), "of", len(SITES))


def hit(frame, bp_loc, _dict):
    state = _state()
    target = frame.GetThread().GetProcess().GetTarget()
    site_va = _module_va(target, frame.GetPC())
    site_key = f"0x{site_va:x}" if site_va is not None else "unknown"
    counts = state["counts"].setdefault(
        site_key,
        {"name": "unknown", "hits": 0, "recorded": 0, "read_errors": 0, "disabled_at_cap": False},
    )
    counts["hits"] += 1

    packet = _site_packet(frame, site_va)
    if packet is None:
        counts["read_errors"] += 1

    if len(state["events"]) < state["event_limit"]:
        state["events"].append(
            {
                "site": site_key,
                "name": SITES.get(site_va, "unknown"),
                "thread_id": frame.GetThread().GetThreadID(),
                "packet": packet,
                "stack": _stack(frame.GetThread(), 10),
            }
        )
        counts["recorded"] += 1

    if counts["hits"] >= state["site_hit_cap"]:
        counts["disabled_at_cap"] = True
        bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def report_to_file(path):
    state = _state()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)
    print("WROTE", path)
