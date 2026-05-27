import builtins
import json
import os
import struct


SITES = {
    0x3B20CD: "constructor_call_3c9370",
    0x3B20D2: "after_constructor_call",
    0x3C9401: "constructor_store_after_ctx_a0",
    0x3C8F90: "mutation_entry_ctx_a0",
    0x1BDBAB: "keylist_getter_first",
    0x1BDBDD: "keylist_getter_append",
    0x3C9043: "mutation_loop_key_first",
    0x3C9098: "mutation_loop_key_guard",
    0x3C90A5: "mutation_store_before",
    0x3C90A9: "mutation_store_after",
    0x3B2143: "post_mutation_context_walk",
}

KEY15 = 15


def reset(label="", event_limit=256, site_hit_cap=4096):
    builtins.l16_c6_mutation_identity = {
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
        "tracked_item_ptrs": [],
        "events": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_c6_mutation_identity"):
        reset()
    return builtins.l16_c6_mutation_identity


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


def _item_for_site(frame, site_va):
    process = frame.GetThread().GetProcess()
    if site_va in (0x1BDBAB, 0x1BDBDD, 0x3C9043, 0x3C9098, 0x3B2143):
        return _u(frame, "rdi")
    if site_va == 0x3C90A5:
        return _u(frame, "rax")
    if site_va == 0x3C90A9:
        slot = _u(frame, "rbx")
        return _u64(process, slot)
    return None


def _context_packet(frame, site_va):
    process = frame.GetThread().GetProcess()
    if site_va == 0x3B20CD:
        ctx = _u(frame, "rdi")
        source = _u(frame, "rsi")
        return {"ctx": ctx, "source": source, "ctx_a0_before": _u64(process, ctx + 0xA0)}
    if site_va == 0x3B20D2:
        ctx = _u(frame, "r14")
        return {"ctx": ctx, "ctx_a0_after": _u64(process, ctx + 0xA0)}
    if site_va == 0x3C9401:
        ctx = _u(frame, "r14")
        constructed = _u(frame, "r12")
        return {"ctx": ctx, "constructed_r12": constructed, "ctx_a0_after": _u64(process, ctx + 0xA0)}
    if site_va == 0x3C8F90:
        ctx = _u(frame, "rdi")
        return {"ctx": ctx, "ctx_a0_at_entry": _u64(process, ctx + 0xA0)}
    return None


def _track_item(state, item):
    if not item:
        return
    ptrs = state["tracked_item_ptrs"]
    if item not in ptrs:
        ptrs.append(item)
        ptrs.sort()


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
        bp.SetScriptCallbackFunction("c6_mutation_identity_probe.hit")
        state["breakpoint_ids"][str(bp.GetID())] = f"0x{va:x}"
    print("INSTALLED", len(state["breakpoint_ids"]), "of", len(SITES))


def hit(frame, bp_loc, _dict):
    state = _state()
    target = frame.GetThread().GetProcess().GetTarget()
    process = frame.GetThread().GetProcess()
    site_va = _module_va(target, frame.GetPC())
    site_key = f"0x{site_va:x}" if site_va is not None else "unknown"
    counts = state["counts"].setdefault(
        site_key,
        {"name": "unknown", "hits": 0, "recorded": 0, "key15_hits": 0, "read_errors": 0, "disabled_at_cap": False},
    )
    counts["hits"] += 1

    item = _item_for_site(frame, site_va)
    packet = _item_packet(process, item) if item else None
    context = _context_packet(frame, site_va)
    record = context is not None

    if item and packet is None:
        counts["read_errors"] += 1
    if packet is not None:
        key = packet.get("key_item_0x60")
        if key == KEY15:
            counts["key15_hits"] += 1
            _track_item(state, packet.get("item_ptr"))
            record = True
        elif packet.get("item_ptr") in state["tracked_item_ptrs"]:
            record = True

    if record and len(state["events"]) < state["event_limit"]:
        event = {
            "site": site_key,
            "name": SITES.get(site_va, "unknown"),
            "thread_id": frame.GetThread().GetThreadID(),
            "stack": _stack(frame.GetThread(), 10),
        }
        if context is not None:
            event["context"] = context
        if packet is not None:
            event["item"] = packet
        state["events"].append(event)
        counts["recorded"] += 1

    if counts["hits"] >= state["site_hit_cap"] and counts["key15_hits"] == 0 and context is None:
        counts["disabled_at_cap"] = True
        bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def report_to_file(path):
    state = _state()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)
    print("WROTE", path)
