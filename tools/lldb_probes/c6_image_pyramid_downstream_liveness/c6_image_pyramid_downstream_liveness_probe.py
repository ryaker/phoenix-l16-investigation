import builtins
import json
import os
import struct
import traceback


ZERO_FILL_SITES = {
    0x3B2ABD: "zero_fill_route_ctx_538_store",
    0x3B2F59: "zero_fill_route_after_descriptor_zero_fill",
}

DOWNSTREAM_SITES = {
    0x3B7470: "histogram_consumer_entry",
    0x3B7490: "histogram_consumer_wrap_ctx_538",
    0x3B74E0: "histogram_consumer_last_level_data_observed",
    0x3B7546: "histogram_consumer_mode_branch_result",
    0x3B77B0: "last_level_materializer_entry",
    0x3B7839: "last_level_materializer_mask_verdict",
    0x3B78C5: "last_level_materializer_wrap_ctx_538",
    0x3B7919: "last_level_materializer_level_data_observed",
    0x3B7988: "last_level_materializer_mode_branch_result",
    0x3B79BE: "last_level_materializer_mode0_helper_call_27e0d0",
    0x3B79D6: "last_level_materializer_mode1_f540_call",
    0x3B7AB4: "last_level_materializer_done",
    0x3B9820: "region_consumer_entry",
    0x3B9846: "region_consumer_wrap_ctx_538",
    0x3B988F: "region_consumer_input_level_data_observed",
    0x3B9C46: "region_consumer_calls_materializer",
    0x3B9C51: "region_consumer_deeper_level_index",
    0x3B9C82: "region_consumer_deeper_level_data_observed",
    0x3B9F0C: "region_consumer_d7a10_call",
    0x3B9F89: "region_consumer_virtual_5a0_call",
    0x3BDD9B: "direct_consumer_ctx_538_read",
    0x3BDDD3: "direct_consumer_first_image_data_observed",
    0x3BDE8D: "direct_consumer_f540_call",
    0x3BF3B3: "virtual_consumer_wrap_ctx_538",
    0x3BF419: "virtual_consumer_5a0_call",
}

SITES = {}
SITES.update(ZERO_FILL_SITES)
SITES.update(DOWNSTREAM_SITES)


def reset(label="", event_limit=768, site_hit_cap=2048):
    builtins.l16_c6_image_pyramid_downstream_liveness = {
        "label": label,
        "event_limit": event_limit,
        "site_hit_cap": site_hit_cap,
        "scope": (
            "C6 ImagePyramid downstream liveness only. A hit proves runtime "
            "execution at the named VA under this render profile; it does not "
            "by itself prove final image contribution."
        ),
        "sites": {f"0x{va:x}": name for va, name in SITES.items()},
        "zero_fill_sites": {f"0x{va:x}": name for va, name in ZERO_FILL_SITES.items()},
        "downstream_sites": {f"0x{va:x}": name for va, name in DOWNSTREAM_SITES.items()},
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
        "contexts": {},
        "context_site_hits": {},
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_c6_image_pyramid_downstream_liveness"):
        reset()
    return builtins.l16_c6_image_pyramid_downstream_liveness


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


def _u8(process, addr):
    data = _read(process, addr, 1)
    return data[0] if data is not None else None


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


def _rect(process, addr):
    data = _read(process, addr, 16)
    if data is None:
        return None
    return list(struct.unpack_from("<iiii", data, 0))


def _descriptor(process, addr):
    if not addr:
        return None
    data_ptr = _u64(process, addr + 0x20)
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
        "data_ptr": data_ptr,
        "origin_ptr": _u64(process, addr + 0x28),
        "sample_32": _sample(process, data_ptr, 32),
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
                    item_addr = begin + index * stride
                    items.append(
                        {
                            "index": index,
                            "addr": item_addr,
                            "raw_u64": [
                                _u64(process, item_addr),
                                _u64(process, item_addr + 8),
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
        "ctx_0x4b4": _u32(process, ctx + 0x4B4),
        "ctx_0x4b8": _u32(process, ctx + 0x4B8),
        "ctx_0x538": _shared_ptr(process, ctx + 0x538),
        "ctx_0x5a0": _u64(process, ctx + 0x5A0),
        "ctx_0x640": _u64(process, ctx + 0x640),
        "ctx_0x721": _u8(process, ctx + 0x721),
        "ctx_0x722": _u8(process, ctx + 0x722),
    }


def _remember_context(process, ctx):
    if ctx:
        _state()["contexts"][str(ctx)] = _context_summary(process, ctx)


def _note_ctx_site(ctx, site_key):
    if not ctx:
        return
    hits = _state()["context_site_hits"].setdefault(str(ctx), {})
    hits[site_key] = hits.get(site_key, 0) + 1


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

    if site_va == 0x3B2F59:
        ctx = _u64(process, rbp - 0x738)
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "descriptor_after_zero_fill": _descriptor(process, _u(frame, "rbx")),
            "level_index_after_increment_pending": _u(frame, "r12") & 0xFFFFFFFF,
        }

    if site_va in (0x3B7470, 0x3B77B0, 0x3B9820):
        ctx = _u(frame, "rsi") if site_va == 0x3B7470 else _u(frame, "rdi")
        _remember_context(process, ctx)
        packet = {"ctx": ctx, "ctx_summary": _context_summary(process, ctx)}
        if site_va == 0x3B7470:
            packet["output_arg_rdi"] = _u(frame, "rdi")
        if site_va == 0x3B9820:
            packet["input_rect_rsi"] = _u(frame, "rsi")
            packet["input_rect"] = _rect(process, _u(frame, "rsi"))
            packet["input_level_edx"] = _u(frame, "rdx") & 0xFFFFFFFF
        return packet

    if site_va == 0x3B7490:
        ctx = _u(frame, "r15")
        _remember_context(process, ctx)
        return {"ctx": ctx, "ctx_538": _shared_ptr(process, ctx + 0x538)}

    if site_va == 0x3B74E0:
        ctx = _u(frame, "r15")
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "level_index": (_u32(process, ctx + 0x4B0) or 0) - 1,
            "image_ptr": _u(frame, "rbx"),
            "width": _i32_reg(_u(frame, "r12")),
            "height": _i32_reg(_u(frame, "r13")),
            "stride_bytes": _i32_reg(_u(frame, "r14")),
            "data_ptr": _u(frame, "rax"),
            "data_sample_32": _sample(process, _u(frame, "rax"), 32),
        }

    if site_va == 0x3B7546:
        ctx = _u(frame, "r15")
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "mode_eax": _u(frame, "rax") & 0xFFFFFFFF,
            "level_descriptor": _descriptor(process, rbp - 0x68),
        }

    if site_va == 0x3B7839:
        ctx = _u(frame, "r13")
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "level_index": _i32_reg(_u(frame, "r14")),
            "all_mask_bytes_were_2_bl": _u(frame, "rbx") & 0xFF,
        }

    if site_va == 0x3B78C5:
        ctx = _u(frame, "r13")
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "level_index": _i32_reg(_u(frame, "r14")),
            "ctx_538": _shared_ptr(process, ctx + 0x538),
        }

    if site_va == 0x3B7919:
        ctx = _u64(process, rbp - 0x130)
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "level_index": _i32(process, rbp - 0x2C),
            "image_ptr": _u(frame, "r12"),
            "width": _i32_reg(_u(frame, "r13")),
            "height": _i32_reg(_u(frame, "rbx")),
            "stride_bytes": _i32_reg(_u(frame, "r14")),
            "data_ptr": _u(frame, "rax"),
            "data_sample_32": _sample(process, _u(frame, "rax"), 32),
        }

    if site_va == 0x3B7988:
        ctx = _u(frame, "r14")
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "mode_eax": _u(frame, "rax") & 0xFFFFFFFF,
            "level_index": _i32(process, rbp - 0x2C),
            "level_descriptor": _descriptor(process, rbp - 0x120),
        }

    if site_va == 0x3B79BE:
        ctx = _u(frame, "r14")
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "static_call_target": "0x27e0d0",
            "level_descriptor": _descriptor(process, rbp - 0x120),
        }

    if site_va == 0x3B79D6:
        ctx = _u(frame, "r14")
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "static_call_target": "0xf540",
            "source_descriptor": _descriptor(process, rbp - 0x120),
            "destination_descriptor": _descriptor(process, rbp - 0xC0),
            "bytes_per_pixel_edx": _u(frame, "rdx") & 0xFFFFFFFF,
        }

    if site_va == 0x3B7AB4:
        ctx = _u(frame, "r14")
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "level_index": _i32(process, rbp - 0x2C),
            "level_descriptor_after_materializer": _descriptor(process, rbp - 0x120),
        }

    if site_va == 0x3B9846:
        ctx = _u(frame, "r15")
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "level_index": _i32(process, rbp - 0x1A4),
            "ctx_538": _shared_ptr(process, ctx + 0x538),
        }

    if site_va == 0x3B988F:
        ctx = _u(frame, "r15")
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "level_index": _i32(process, rbp - 0x1A4),
            "image_ptr": _u(frame, "rbx"),
            "width": _i32_reg(_u(frame, "r12")),
            "height": _i32_reg(_u(frame, "r14")),
            "stride_bytes": _i32_reg(_u(frame, "r13")),
            "data_ptr": _u(frame, "rax"),
            "data_sample_32": _sample(process, _u(frame, "rax"), 32),
        }

    if site_va == 0x3B9C46:
        ctx = _u(frame, "rdi")
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "static_call_target": "0x3b77b0",
            "current_level_ebx": _u(frame, "rbx") & 0xFFFFFFFF,
        }

    if site_va == 0x3B9C51:
        ctx = _u64(process, rbp - 0x1A0)
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "requested_level_ebx": _u(frame, "rbx") & 0xFFFFFFFF,
            "image_pyramid_wrapper": rbp - 0x40,
        }

    if site_va == 0x3B9C82:
        ctx = _u64(process, rbp - 0x1A0)
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "level_index_ebx": _u(frame, "rbx") & 0xFFFFFFFF,
            "image_ptr": _u(frame, "r15"),
            "width": _i32_reg(_u(frame, "r13")),
            "height": _i32_reg(_u(frame, "r12")),
            "stride_bytes": _i32_reg(_u(frame, "r14")),
            "data_ptr": _u(frame, "rax"),
            "data_sample_32": _sample(process, _u(frame, "rax"), 32),
        }

    if site_va == 0x3B9F0C:
        ctx = _u64(process, rbp - 0x1A0)
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "static_call_target": "0xd7a10",
            "input_level": _i32(process, rbp - 0x1A4),
            "destination_descriptor_rdi": _descriptor(process, _u(frame, "rdi")),
            "source_descriptor_rsi": _descriptor(process, _u(frame, "rsi")),
        }

    if site_va == 0x3B9F89:
        ctx = _u64(process, rbp - 0x1A0)
        _remember_context(process, ctx)
        receiver = _u(frame, "rdi")
        return {
            "ctx": ctx,
            "receiver_ctx_5a0": receiver,
            "call_target_rax": _u(frame, "rax"),
            "image_pyramid_wrapper": rbp - 0x40,
            "rect_arg": _rect(process, rbp - 0x140),
            "level_arg": _i32(process, rbp - 0x2C),
        }

    if site_va == 0x3BDD9B:
        ctx = _u(frame, "rax")
        _remember_context(process, ctx)
        return {"ctx": ctx, "ctx_538": _shared_ptr(process, ctx + 0x538)}

    if site_va == 0x3BDDD3:
        ctx = _u64(process, rbp - 0x7F0)
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "image_ptr": _u(frame, "rbx"),
            "width": _i32_reg(_u(frame, "r12")),
            "height": _i32_reg(_u(frame, "r15")),
            "stride_bytes": _i32_reg(_u(frame, "r14")),
            "data_ptr": _u(frame, "rax"),
            "data_sample_32": _sample(process, _u(frame, "rax"), 32),
        }

    if site_va == 0x3BDE8D:
        ctx = _u(frame, "rdi")
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "static_call_target": "0xf540",
            "mode_r14d": _u(frame, "r14") & 0xFFFFFFFF,
            "destination_descriptor": _descriptor(process, rbp - 0x650),
            "source_descriptor_addr": _u(frame, "rsi"),
            "source_descriptor": _descriptor(process, _u(frame, "rsi")),
            "bytes_per_pixel_edx": _u(frame, "rdx") & 0xFFFFFFFF,
        }

    if site_va == 0x3BF3B3:
        ctx = _u(frame, "r13")
        _remember_context(process, ctx)
        rect_rec = _u(frame, "r14")
        return {
            "ctx": ctx,
            "level_r15d": _u(frame, "r15") & 0xFFFFFFFF,
            "record_ptr_r14": rect_rec,
            "record_rect_0x14": _rect(process, rect_rec + 0x14),
            "ctx_538": _shared_ptr(process, ctx + 0x538),
            "ctx_5a0": _u64(process, ctx + 0x5A0),
        }

    if site_va == 0x3BF419:
        ctx = _u(frame, "r13")
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "receiver_ctx_5a0": _u(frame, "rdi"),
            "call_target_rax": _u(frame, "rax"),
            "image_pyramid_wrapper_rsi": _u(frame, "rsi"),
            "rect_arg_rdx": _u(frame, "rdx"),
            "rect_arg": _rect(process, _u(frame, "rdx")),
            "level_arg_rcx": _u(frame, "rcx"),
            "level_arg": _i32(process, _u(frame, "rcx")),
        }

    return None


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
        bp.SetScriptCallbackFunction("c6_image_pyramid_downstream_liveness_probe.hit")
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
            "recorded": 0,
            "read_errors": 0,
            "disabled_at_cap": False,
        },
    )
    counts["hits"] += 1

    packet = None
    try:
        packet = _site_packet(frame, site_va)
    except Exception:
        counts["read_errors"] += 1
        state["errors"].append(
            {
                "site": site_key,
                "error": traceback.format_exc(limit=4),
            }
        )

    if packet is None:
        counts["read_errors"] += 1
    else:
        ctx = packet.get("ctx")
        if ctx:
            _note_ctx_site(ctx, site_key)

    if len(state["events"]) < state["event_limit"]:
        state["events"].append(
            {
                "sequence": len(state["events"]),
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


def _derive_summary(state):
    zero_fill_keys = {f"0x{va:x}" for va in ZERO_FILL_SITES}
    downstream_keys = {f"0x{va:x}" for va in DOWNSTREAM_SITES}
    hit_sites = sorted(
        site for site, item in state["counts"].items() if item.get("hits", 0) > 0
    )
    zero_fill_contexts = set()
    downstream_contexts = set()
    for ctx, sites in state["context_site_hits"].items():
        if any(site in zero_fill_keys for site in sites):
            zero_fill_contexts.add(ctx)
        if any(site in downstream_keys for site in sites):
            downstream_contexts.add(ctx)
    return {
        "hit_sites": hit_sites,
        "zero_fill_hit_sites": sorted(site for site in hit_sites if site in zero_fill_keys),
        "downstream_hit_sites": sorted(site for site in hit_sites if site in downstream_keys),
        "contexts_with_zero_fill_site_hits": sorted(zero_fill_contexts),
        "contexts_with_downstream_site_hits": sorted(downstream_contexts),
        "contexts_with_both_zero_fill_and_downstream_site_hits": sorted(
            zero_fill_contexts & downstream_contexts
        ),
    }


def report_to_file(path):
    state = _state()
    state["derived_summary"] = _derive_summary(state)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("WROTE", path)
