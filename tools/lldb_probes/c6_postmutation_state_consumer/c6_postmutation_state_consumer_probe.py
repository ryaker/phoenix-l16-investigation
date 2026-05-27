import builtins
import json
import os
import struct


SITES = {
    0x3B20FE: "post_mutation_ctx_a0_accessor_call",
    0x3B2103: "post_accessor_object_load",
    0x3B2111: "container_item_vector_accessor_call",
    0x3B2143: "item_vector_key_getter",
    0x3B21D9: "derived_state_write_call",
    0x3B21EC: "context_c8_store",
    0x3B2207: "derived_state_code_call",
    0x3B2213: "context_4b0_store",
}

KEY15 = 15


def reset(label="", event_limit=512, site_hit_cap=4096):
    builtins.l16_c6_postmutation_state_consumer = {
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
                "key15_hits": 0,
                "read_errors": 0,
                "disabled_at_cap": False,
            }
            for va, name in SITES.items()
        },
        "tracked_key15_item_ptrs": [],
        "events": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_c6_postmutation_state_consumer"):
        reset()
    return builtins.l16_c6_postmutation_state_consumer


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


def _item_packet(process, item):
    if not item:
        return None
    return {
        "item_ptr": item,
        "active_item_0x30": _u8(process, item + 0x30),
        "pair_item_0x58_0x5c": [_i32(process, item + 0x58), _i32(process, item + 0x5C)],
        "key_item_0x60": _u32(process, item + 0x60),
        "type_item_0x100": _u32(process, item + 0x100),
    }


def _container_packet(process, container):
    if not container:
        return None
    begin = _u64(process, container + 0x10)
    end = _u64(process, container + 0x18)
    span = None
    count_0x10 = None
    if begin is not None and end is not None and end >= begin:
        span = end - begin
        count_0x10 = span // 0x10
    return {
        "container_ptr": container,
        "field_0x44_u32": _u32(process, container + 0x44),
        "item_vec_begin_0x10": begin,
        "item_vec_end_0x18": end,
        "item_vec_span": span,
        "item_vec_count_if_stride_0x10": count_0x10,
        "field_0x284_u32": _u32(process, container + 0x284),
        "field_0x288_ptr": _u64(process, container + 0x288),
        "field_0x290_ptr": _u64(process, container + 0x290),
    }


def _state_obj_packet(process, state_obj):
    if not state_obj:
        return None
    return {
        "state_obj": state_obj,
        "field_0x0_u32": _u32(process, state_obj),
        "field_0x4_u8": _u8(process, state_obj + 4),
    }


def _site_packet(frame, site_va):
    process = frame.GetThread().GetProcess()
    if site_va == 0x3B20FE:
        ctx = _u(frame, "rdi")
        obj = _u64(process, ctx + 0xA0)
        return {"ctx": ctx, "ctx_a0": obj}
    if site_va == 0x3B2103:
        field_addr = _u(frame, "rax")
        obj = _u64(process, field_addr)
        container = _u64(process, obj) if obj else 0
        return {
            "field_addr": field_addr,
            "ctx_a0": obj,
            "object_slot_0x0_container": container,
            "container": _container_packet(process, container),
        }
    if site_va == 0x3B2111:
        container = _u(frame, "rdi")
        return {"container": _container_packet(process, container)}
    if site_va == 0x3B2143:
        item = _u(frame, "rdi")
        return {"item": _item_packet(process, item)}
    if site_va == 0x3B21D9:
        state_obj = _u(frame, "rdi")
        return {
            "state_obj": state_obj,
            "input_esi": _u(frame, "rsi") & 0xFFFFFFFF,
            "input_edx_low_byte": _u(frame, "rdx") & 0xFF,
            "before_state": _state_obj_packet(process, state_obj),
        }
    if site_va == 0x3B21EC:
        ctx = _u(frame, "r15")
        state_obj = _u(frame, "r12")
        return {
            "ctx": ctx,
            "old_ctx_c8": _u64(process, ctx + 0xC8),
            "new_state_obj_r12": state_obj,
            "new_state": _state_obj_packet(process, state_obj),
        }
    if site_va == 0x3B2207:
        state_obj = _u(frame, "rdi")
        return {"state": _state_obj_packet(process, state_obj)}
    if site_va == 0x3B2213:
        ctx = _u(frame, "r15")
        return {
            "ctx": ctx,
            "new_context_0x4b0_ecx": _u(frame, "rcx") & 0xFFFFFFFF,
            "old_context_0x4b0": _u32(process, ctx + 0x4B0),
        }
    return None


def _track_key15(state, packet):
    item = packet.get("item") if packet else None
    if not item:
        return False
    if item.get("key_item_0x60") != KEY15:
        return False
    ptr = item.get("item_ptr")
    if ptr and ptr not in state["tracked_key15_item_ptrs"]:
        state["tracked_key15_item_ptrs"].append(ptr)
        state["tracked_key15_item_ptrs"].sort()
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
        bp.SetScriptCallbackFunction("c6_postmutation_state_consumer_probe.hit")
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
            "name": "unknown",
            "hits": 0,
            "recorded": 0,
            "key15_hits": 0,
            "read_errors": 0,
            "disabled_at_cap": False,
        },
    )
    counts["hits"] += 1

    packet = _site_packet(frame, site_va)
    if packet is None:
        counts["read_errors"] += 1
    if _track_key15(state, packet):
        counts["key15_hits"] += 1

    should_record = (
        counts["recorded"] < 32
        or counts["key15_hits"] > 0
        or site_va in (0x3B21D9, 0x3B21EC, 0x3B2207, 0x3B2213)
    )
    if should_record and len(state["events"]) < state["event_limit"]:
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
