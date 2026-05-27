import builtins
import json
import os
import struct


SITES = {
    0x3B2339: "rect_vector_builder_call",
    0x3B237C: "rect_vector_return_first_tuple_load",
    0x3B23BF: "level_loop_after_state_code",
    0x3B23D1: "level_loop_body_entry",
    0x3B2426: "ctx_4c0_delta_dims_append_end_store",
    0x3B2462: "ctx_520_origin_append_end_store",
    0x3B24A8: "ctx_4d8_scaled_dims_append_end_store",
    0x3B2580: "ctx_508_grid_record_append_end_store",
    0x3B2829: "ctx_560_record_vector_append_end_store",
    0x3B291A: "ctx_4f0_output_dims_append_end_store",
    0x3B29E1: "level_loop_backedge_decision",
    0x3B2A94: "image_pyramid_builder_call_from_ctx_4c0",
    0x3982B0: "image_pyramid_builder_entry",
    0x398342: "image_level_private_create_call",
    0x39839D: "image_pyramid_private_sharedptr_create_call",
    0x3983A2: "image_pyramid_builder_return",
    0x3B2A99: "after_image_pyramid_builder_return",
    0x3B2ABD: "ctx_538_image_pyramid_sharedptr_stored",
    0x3B2E55: "ctx_6c8_object_store_after",
    0x3B2E7A: "image_pyramid_wrapper_ctor_call",
    0x3B2E8B: "image_pyramid_level_count_return",
    0x3B2EEA: "image_pyramid_level_image_observed",
    0x3B303F: "ctx_678_store_after",
    0x3B30CF: "ctx_6a8_store_after",
    0x3B3159: "ctx_688_store_after",
    0x3B3213: "ctx_698_store_after",
    0x3B3444: "ctx_6b8_store_after",
}


def reset(label="", event_limit=1024, site_hit_cap=4096):
    builtins.l16_c6_rect_vector_consumer = {
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
        "contexts": {},
        "events": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_c6_rect_vector_consumer"):
        reset()
    return builtins.l16_c6_rect_vector_consumer


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


def _pair_i32(process, addr):
    if not addr:
        return None
    data = _read(process, addr, 8)
    if data is None:
        return None
    return list(struct.unpack_from("<ii", data, 0))


def _rect_i32(process, addr):
    if not addr:
        return None
    data = _read(process, addr, 16)
    if data is None:
        return None
    return list(struct.unpack_from("<iiii", data, 0))


def _bytes_packet(process, addr, size):
    data = _read(process, addr, size)
    if data is None:
        return None
    return {
        "addr": addr,
        "size": size,
        "hex": data.hex(),
        "i32": list(struct.unpack_from("<" + "i" * (size // 4), data, 0)) if size % 4 == 0 else None,
        "u64": list(struct.unpack_from("<" + "Q" * (size // 8), data, 0)) if size % 8 == 0 else None,
    }


def _vector_header(process, header_addr, stride, reader, max_items=10):
    if not header_addr:
        return None
    begin = _u64(process, header_addr)
    end = _u64(process, header_addr + 8)
    cap = _u64(process, header_addr + 16)
    byte_count = None
    count = None
    items = []
    if begin is not None and end is not None and end >= begin:
        byte_count = end - begin
        if stride and byte_count % stride == 0:
            count = byte_count // stride
            if 0 <= count <= 100000:
                for index in range(min(count, max_items)):
                    items.append({"index": index, "value": reader(process, begin + index * stride)})
    return {
        "header_addr": header_addr,
        "begin": begin,
        "end": end,
        "cap": cap,
        "stride": stride,
        "byte_count": byte_count,
        "count": count,
        "items": items,
    }


def _pair_vector(process, header_addr, max_items=10):
    return _vector_header(process, header_addr, 8, _pair_i32, max_items)


def _rect_vector(process, header_addr, max_items=10):
    return _vector_header(process, header_addr, 16, _rect_i32, max_items)


def _raw_vector(process, header_addr, stride, max_items=4):
    return _vector_header(
        process,
        header_addr,
        stride,
        lambda proc, addr: _bytes_packet(proc, addr, stride),
        max_items,
    )


def _shared_ptr(process, addr):
    if not addr:
        return None
    pointee = _u64(process, addr)
    control = _u64(process, addr + 8)
    return {
        "addr": addr,
        "pointee": pointee,
        "control": control,
        "pyramid_private": _pyramid_private(process, pointee),
    }


def _pyramid_private(process, ptr):
    if not ptr:
        return None
    return {
        "private_ptr": ptr,
        "image_vector_header": _raw_vector(process, ptr, 0x10, 8),
        "field_0x18_u64": _u64(process, ptr + 0x18),
    }


def _context_summary(process, ctx):
    if not ctx:
        return None
    return {
        "ctx": ctx,
        "ctx_0xc8": _u64(process, ctx + 0xC8),
        "ctx_0x4b0": _u32(process, ctx + 0x4B0),
        "ctx_0x4b4": _i32(process, ctx + 0x4B4),
        "ctx_0x4b8": _i32(process, ctx + 0x4B8),
        "vector_0x4c0_delta_dims": _pair_vector(process, ctx + 0x4C0),
        "vector_0x4d8_scaled_dims": _pair_vector(process, ctx + 0x4D8),
        "vector_0x4f0_output_dims": _pair_vector(process, ctx + 0x4F0),
        "vector_0x508_grid_records": _raw_vector(process, ctx + 0x508, 0x30, 5),
        "vector_0x520_origins": _pair_vector(process, ctx + 0x520),
        "image_pyramid_sharedptr_0x538": _shared_ptr(process, ctx + 0x538),
        "vector_0x560_records": _raw_vector(process, ctx + 0x560, 0x18, 5),
        "object_0x678": _u64(process, ctx + 0x678),
        "object_0x688": _u64(process, ctx + 0x688),
        "object_0x698": _u64(process, ctx + 0x698),
        "object_0x6a8": _u64(process, ctx + 0x6A8),
        "object_0x6b8": _u64(process, ctx + 0x6B8),
        "object_0x6c8": _u64(process, ctx + 0x6C8),
    }


def _remember_context(process, ctx):
    if not ctx:
        return
    state = _state()
    state["contexts"][str(ctx)] = _context_summary(process, ctx)


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


def _call_args(frame):
    process = frame.GetThread().GetProcess()
    return {
        "rdi": _u(frame, "rdi"),
        "rsi": _u(frame, "rsi"),
        "rdx": _u(frame, "rdx"),
        "rcx": _u(frame, "rcx"),
        "r8": _u(frame, "r8"),
        "r9": _u(frame, "r9"),
        "pair_at_rdx": _pair_i32(process, _u(frame, "rdx")),
        "pair_at_rcx": _pair_i32(process, _u(frame, "rcx")),
        "rect_at_r9": _rect_i32(process, _u(frame, "r9")),
    }


def _loop_locals(frame):
    process = frame.GetThread().GetProcess()
    rbp = _u(frame, "rbp")
    return {
        "tuple_local_0x760": _rect_i32(process, rbp - 0x760),
        "tuple_next_0x200": _rect_i32(process, rbp - 0x200),
        "raw_dims_0x1a8": _pair_i32(process, rbp - 0x1A8),
        "scaled_dims_for_pyramid_0x76c_0x768": [_i32(process, rbp - 0x76C), _i32(process, rbp - 0x768)],
        "output_dims_0x748_0x740": [_i32(process, rbp - 0x748), _i32(process, rbp - 0x740)],
    }


def _site_packet(frame, site_va):
    process = frame.GetThread().GetProcess()
    rbp = _u(frame, "rbp")

    if site_va == 0x3B2339:
        ctx = _u(frame, "rsi")
        _remember_context(process, ctx)
        return {"call": _call_args(frame), "ctx": _context_summary(process, ctx)}

    if site_va == 0x3B237C:
        ctx = _u(frame, "r15")
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "rect_vector_local": _rect_vector(process, rbp - 0x1D8),
            "first_tuple_source": _rect_i32(process, _u64(process, rbp - 0x1D8) or 0),
            "loop_locals": _loop_locals(frame),
            "ctx_summary": _context_summary(process, ctx),
        }

    if site_va == 0x3B23BF:
        ctx = _u(frame, "r15")
        state_code = _u(frame, "rax") & 0xFFFFFFFF
        level_index = _u(frame, "rbx") & 0xFFFFFFFF
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "level_index_rbx": level_index,
            "state_code_eax": state_code,
            "body_will_be_skipped_if_signed_index_lt_state_code": _i32_reg(level_index) < _i32_reg(state_code),
            "loop_locals": _loop_locals(frame),
        }

    if site_va == 0x3B23D1:
        ctx = _u(frame, "r15")
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "level_index": _u(frame, "rcx") & 0xFFFFFFFF,
            "body": "entered",
            "loop_locals": _loop_locals(frame),
        }

    if site_va == 0x3B2426:
        ctx = _u(frame, "r15")
        new_end = _u(frame, "rax")
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "new_end_rax": new_end,
            "appended_delta_dims": _pair_i32(process, new_end - 8),
            "ctx_vector_before_end_store": _pair_vector(process, ctx + 0x4C0),
        }

    if site_va == 0x3B2462:
        ctx = _u(frame, "r15")
        new_end = _u(frame, "rax")
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "new_end_rax": new_end,
            "appended_origin": _pair_i32(process, new_end - 8),
            "ctx_vector_before_end_store": _pair_vector(process, ctx + 0x520),
        }

    if site_va == 0x3B24A8:
        ctx = _u(frame, "r15")
        new_end = _u(frame, "rax")
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "new_end_rax": new_end,
            "appended_scaled_dims": _pair_i32(process, new_end - 8),
            "ctx_vector_before_end_store": _pair_vector(process, ctx + 0x4D8),
        }

    if site_va == 0x3B2580:
        ctx = _u(frame, "r14")
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "record_ptr_rbx": _u(frame, "rbx"),
            "record_0x30_after_ctor": _bytes_packet(process, _u(frame, "rbx"), 0x30),
            "ctx_vector_before_end_add": _raw_vector(process, ctx + 0x508, 0x30, 5),
        }

    if site_va == 0x3B2829:
        ctx = _u(frame, "r14")
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "record_ptr_r13": _u(frame, "r13"),
            "record_0x18_after_population": _bytes_packet(process, _u(frame, "r13"), 0x18),
            "ctx_vector_before_end_add": _raw_vector(process, ctx + 0x560, 0x18, 5),
        }

    if site_va == 0x3B291A:
        ctx = _u(frame, "r15")
        new_end = _u(frame, "rax")
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "new_end_rax": new_end,
            "appended_output_dims": _pair_i32(process, new_end - 8),
            "ctx_vector_before_end_store": _pair_vector(process, ctx + 0x4F0),
        }

    if site_va == 0x3B29E1:
        ctx = _u(frame, "r15")
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "next_level_index_edi": _u(frame, "rdi") & 0xFFFFFFFF,
            "loop_continues_if_signed_edi_lt_5": _i32_reg(_u(frame, "rdi")) < 5,
            "loop_locals_after_halving": _loop_locals(frame),
        }

    if site_va == 0x3B2A94:
        ctx = _u(frame, "r13")
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "out_sharedptr_rdi": _u(frame, "rdi"),
            "source_pair_vector_rsi": _pair_vector(process, _u(frame, "rsi")),
            "edx": _u(frame, "rdx") & 0xFFFFFFFF,
            "ctx_summary": _context_summary(process, ctx),
        }

    if site_va == 0x3982B0:
        return {
            "out_sharedptr_rdi": _u(frame, "rdi"),
            "source_pair_vector_rsi": _pair_vector(process, _u(frame, "rsi")),
            "edx": _u(frame, "rdx") & 0xFFFFFFFF,
        }

    if site_va == 0x398342:
        return {
            "level_index_r14": _u(frame, "r14"),
            "width_esi": _i32_reg(_u(frame, "rsi")),
            "height_edx": _i32_reg(_u(frame, "rdx")),
            "format_or_flags_ecx": _u(frame, "rcx") & 0xFFFFFFFF,
            "r8": _u(frame, "r8"),
            "source_pair_from_rax_r14": _pair_i32(process, _u(frame, "rax") + 8 * _u(frame, "r14")),
            "private_ptr_rbx": _u(frame, "rbx"),
        }

    if site_va == 0x39839D:
        return {
            "out_sharedptr_r14": _u(frame, "r14"),
            "private_ptr_rsi": _u(frame, "rsi"),
            "private_snapshot": _pyramid_private(process, _u(frame, "rsi")),
            "edx": _u(frame, "rdx") & 0xFFFFFFFF,
        }

    if site_va == 0x3983A2:
        return {
            "out_sharedptr_r14": _u(frame, "r14"),
            "out_sharedptr_snapshot": _shared_ptr(process, _u(frame, "r14")),
        }

    if site_va == 0x3B2A99:
        ctx = _u(frame, "r13")
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "local_out_sharedptr": _shared_ptr(process, rbp - 0x260),
            "ctx_summary": _context_summary(process, ctx),
        }

    if site_va == 0x3B2ABD:
        ctx = _u(frame, "r13")
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "ctx_538_after_store": _shared_ptr(process, ctx + 0x538),
            "ctx_summary": _context_summary(process, ctx),
        }

    if site_va == 0x3B2E55:
        ctx = _u(frame, "r13")
        _remember_context(process, ctx)
        return {"ctx": ctx, "ctx_6c8": _u64(process, ctx + 0x6C8), "ctx_summary": _context_summary(process, ctx)}

    if site_va == 0x3B2E7A:
        ctx = _u(frame, "rbx")
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "wrapper_out_rdi": _u(frame, "rdi"),
            "sharedptr_rsi": _shared_ptr(process, _u(frame, "rsi")),
        }

    if site_va == 0x3B2E8B:
        ctx = _u(frame, "rbx")
        _remember_context(process, ctx)
        return {
            "ctx": ctx,
            "level_count_eax": _u(frame, "rax") & 0xFFFFFFFF,
            "ctx_4b0": _u32(process, ctx + 0x4B0),
            "matches_ctx_4b0": (_u(frame, "rax") & 0xFFFFFFFF) == _u32(process, ctx + 0x4B0),
        }

    if site_va == 0x3B2EEA:
        ctx_from_stack = _u64(process, rbp - 0x738)
        if ctx_from_stack:
            _remember_context(process, ctx_from_stack)
        return {
            "ctx_from_rbp_0x738": ctx_from_stack,
            "level_index_r12": _u(frame, "r12") & 0xFFFFFFFF,
            "image_ptr_r14": _u(frame, "r14"),
            "width_r13d": _i32_reg(_u(frame, "r13")),
            "height_ebx": _i32_reg(_u(frame, "rbx")),
            "stride_r15d": _i32_reg(_u(frame, "r15")),
            "data_ptr_rax": _u(frame, "rax"),
        }

    if site_va == 0x3B303F:
        ctx = _u(frame, "rbx")
        _remember_context(process, ctx)
        return {"ctx": ctx, "ctx_678": _u64(process, ctx + 0x678), "ctx_summary": _context_summary(process, ctx)}

    if site_va == 0x3B30CF:
        ctx = _u(frame, "rbx")
        _remember_context(process, ctx)
        return {"ctx": ctx, "ctx_6a8": _u64(process, ctx + 0x6A8), "ctx_summary": _context_summary(process, ctx)}

    if site_va == 0x3B3159:
        ctx = _u(frame, "r12")
        _remember_context(process, ctx)
        return {"ctx": ctx, "ctx_688": _u64(process, ctx + 0x688), "ctx_summary": _context_summary(process, ctx)}

    if site_va == 0x3B3213:
        ctx = _u(frame, "rbx")
        _remember_context(process, ctx)
        return {"ctx": ctx, "ctx_698": _u64(process, ctx + 0x698), "ctx_summary": _context_summary(process, ctx)}

    if site_va == 0x3B3444:
        ctx = _u(frame, "rbx")
        _remember_context(process, ctx)
        return {"ctx": ctx, "ctx_6b8": _u64(process, ctx + 0x6B8), "ctx_summary": _context_summary(process, ctx)}

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
        bp.SetScriptCallbackFunction("c6_rect_vector_consumer_probe.hit")
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
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("WROTE", path)
