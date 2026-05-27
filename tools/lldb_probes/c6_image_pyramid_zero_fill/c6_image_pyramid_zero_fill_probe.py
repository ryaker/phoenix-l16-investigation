import builtins
import json
import os
import struct


SITES = {
    0x3B2ABD: "ctx_538_image_pyramid_sharedptr_stored",
    0x3B2EEA: "image_pyramid_level_image_observed",
    0x3B2F54: "level_descriptor_zero_fill_call",
    0x3B2F59: "after_level_descriptor_zero_fill",
}


def reset(label="", event_limit=256, site_hit_cap=4096):
    builtins.l16_c6_image_pyramid_zero_fill = {
        "label": label,
        "event_limit": event_limit,
        "site_hit_cap": site_hit_cap,
        "static_direct_call": "0x3b2f54 -> 0xf7c0",
        "sites": {f"0x{va:x}": name for va, name in SITES.items()},
        "breakpoint_ids": {},
        "counts": {
            f"0x{va:x}": {
                "name": name,
                "hits": 0,
                "filtered_hits": 0,
                "recorded": 0,
                "read_errors": 0,
                "disabled_at_cap": False,
            }
            for va, name in SITES.items()
        },
        "events": [],
        "contexts": {},
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_c6_image_pyramid_zero_fill"):
        reset()
    return builtins.l16_c6_image_pyramid_zero_fill


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _i32_reg(value):
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


def _i32(process, addr):
    data = _read(process, addr, 4)
    return struct.unpack_from("<i", data, 0)[0] if data is not None else None


def _u32(process, addr):
    data = _read(process, addr, 4)
    return struct.unpack_from("<I", data, 0)[0] if data is not None else None


def _u64(process, addr):
    data = _read(process, addr, 8)
    return struct.unpack_from("<Q", data, 0)[0] if data is not None else None


def _sample(process, addr, size=32):
    data = _read(process, addr, size)
    if data is None:
        return None
    return {
        "addr": addr,
        "size": size,
        "hex": data.hex(),
        "all_zero": all(byte == 0 for byte in data),
    }


def _descriptor(process, addr):
    if not addr:
        return None
    return {
        "addr": addr,
        "x0": _i32(process, addr),
        "y0": _i32(process, addr + 0x4),
        "x1": _i32(process, addr + 0x8),
        "y1": _i32(process, addr + 0xC),
        "width": _i32(process, addr + 0x10),
        "height": _i32(process, addr + 0x14),
        "stride_pixels": _i32(process, addr + 0x18),
        "field_0x1c": _i32(process, addr + 0x1C),
        "data_ptr": _u64(process, addr + 0x20),
        "origin_ptr": _u64(process, addr + 0x28),
        "sample_32": _sample(process, _u64(process, addr + 0x20), 32),
    }


def _vector_header(process, header_addr, stride, max_items=8):
    begin = _u64(process, header_addr)
    end = _u64(process, header_addr + 8)
    cap = _u64(process, header_addr + 16)
    count = None
    items = []
    if begin is not None and end is not None and end >= begin and stride:
        byte_count = end - begin
        if byte_count % stride == 0:
            count = byte_count // stride
            if 0 <= count <= 100000:
                for index in range(min(count, max_items)):
                    items.append(
                        {
                            "index": index,
                            "raw_u64": [
                                _u64(process, begin + index * stride),
                                _u64(process, begin + index * stride + 8),
                            ],
                        }
                    )
    return {
        "header_addr": header_addr,
        "begin": begin,
        "end": end,
        "cap": cap,
        "stride": stride,
        "count": count,
        "items": items,
    }


def _shared_ptr(process, addr):
    if not addr:
        return None
    pointee = _u64(process, addr)
    return {
        "addr": addr,
        "pointee": pointee,
        "control": _u64(process, addr + 8),
        "private_image_vector": _vector_header(process, pointee, 0x10) if pointee else None,
    }


def _context_summary(process, ctx):
    if not ctx:
        return None
    return {
        "ctx": ctx,
        "ctx_0x4b0": _u32(process, ctx + 0x4B0),
        "ctx_0x538": _shared_ptr(process, ctx + 0x538),
    }


def _remember_context(process, ctx):
    if ctx:
        _state()["contexts"][str(ctx)] = _context_summary(process, ctx)


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

    if site_va == 0x3B2ABD:
        ctx = _u(frame, "r13")
        _remember_context(process, ctx)
        return {"ctx": ctx, "ctx_summary": _context_summary(process, ctx)}

    if site_va == 0x3B2EEA:
        ctx = _u64(process, rbp - 0x738)
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "level_index": _u(frame, "r12") & 0xFFFFFFFF,
            "image_ptr": _u(frame, "r14"),
            "width": _i32_reg(_u(frame, "r13")),
            "height": _i32_reg(_u(frame, "rbx")),
            "stride_bytes": _i32_reg(_u(frame, "r15")),
            "data_ptr": _u(frame, "rax"),
            "data_sample_before_descriptor": _sample(process, _u(frame, "rax"), 32),
        }

    if site_va == 0x3B2F54:
        desc_addr = _u(frame, "rdi")
        ctx = _u64(process, rbp - 0x738)
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "level_index_next_increment_source": _u(frame, "r12") & 0xFFFFFFFF,
            "call_target_static": "0xf7c0",
            "rsi_bytes_per_pixel": _u(frame, "rsi") & 0xFFFFFFFF,
            "descriptor": _descriptor(process, desc_addr),
        }

    if site_va == 0x3B2F59:
        desc_addr = _u(frame, "rbx")
        ctx = _u64(process, rbp - 0x738)
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "level_index_after_increment_pending": _u(frame, "r12") & 0xFFFFFFFF,
            "descriptor_after_zero_fill": _descriptor(process, desc_addr),
        }

    return None


def _should_record(frame, site_va):
    return True


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
        bp.SetScriptCallbackFunction("c6_image_pyramid_zero_fill_probe.hit")
        state["breakpoint_ids"][str(bp.GetID())] = f"0x{va:x}"
    print("INSTALLED", len(state["breakpoint_ids"]), "of", len(SITES))


def hit(frame, bp_loc, _dict):
    state = _state()
    target = frame.GetThread().GetProcess().GetTarget()
    site_va = _module_va(target, frame.GetPC())
    site_key = f"0x{site_va:x}" if site_va is not None else "unknown"
    counts = state["counts"].setdefault(
        site_key,
        {
            "name": SITES.get(site_va, "unknown"),
            "hits": 0,
            "filtered_hits": 0,
            "recorded": 0,
            "read_errors": 0,
            "disabled_at_cap": False,
        },
    )
    counts["hits"] += 1

    if not _should_record(frame, site_va):
        return False

    counts["filtered_hits"] += 1
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

    if counts["filtered_hits"] >= state["site_hit_cap"]:
        counts["disabled_at_cap"] = True
        bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def report_to_file(path):
    state = _state()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("WROTE", path)
