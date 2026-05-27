import builtins
import json
import os
import struct


SITES = {
    0x3B20CD: "constructor_call_3c9370",
    0x3C9401: "constructor_store_after_ctx_a0",
    0x3B20D2: "after_constructor_call",
    0x3C8F90: "mutation_entry_ctx_a0",
    0x3C9540: "consumer_entry_3c9540",
    0x3C9558: "consumer_identity_before",
    0x3C956F: "consumer_container_load",
    0x3C9578: "consumer_tailjmp_e6c30",
    0xE6C30: "e6c30_entry",
    0xE6CD6: "e6c30_return",
    0x3C957D: "consumer_empty_fallback",
}


def reset(label="", event_limit=256, site_hit_cap=2048):
    builtins.l16_c6_context_a0_consumer = {
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
                "disabled_at_cap": False,
                "read_errors": 0,
            }
            for va, name in SITES.items()
        },
        "ctx_a0_values": [],
        "consumer_contexts": [],
        "consumer_objects": [],
        "consumer_containers": [],
        "e6c30_thread_entry": {},
        "events": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_c6_context_a0_consumer"):
        reset()
    return builtins.l16_c6_context_a0_consumer


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


def _remember(values, value):
    if value and value not in values:
        values.append(value)
        values.sort()


def _object_packet(process, obj):
    if not obj:
        return None
    return {
        "object_ptr": obj,
        "slot_0x0_container": _u64(process, obj),
        "slot_0x8": _u64(process, obj + 0x8),
        "slot_0x10": _u64(process, obj + 0x10),
    }


def _container_packet(process, container):
    if not container:
        return None
    return {
        "container_ptr": container,
        "field_0x44_u32": _u32(process, container + 0x44),
        "item_vec_begin_0x10": _u64(process, container + 0x10),
        "item_vec_end_0x18": _u64(process, container + 0x18),
        "field_0x284_u32": _u32(process, container + 0x284),
        "field_0x288_ptr": _u64(process, container + 0x288),
        "field_0x290_ptr": _u64(process, container + 0x290),
    }


def _context_packet(frame, site_va):
    process = frame.GetThread().GetProcess()
    if site_va == 0x3B20CD:
        ctx = _u(frame, "rdi")
        return {
            "ctx": ctx,
            "source": _u(frame, "rsi"),
            "ctx_a0": _u64(process, ctx + 0xA0),
        }
    if site_va == 0x3C9401:
        ctx = _u(frame, "r14")
        obj = _u64(process, ctx + 0xA0)
        return {
            "ctx": ctx,
            "constructed_r12": _u(frame, "r12"),
            "ctx_a0": obj,
            "object": _object_packet(process, obj),
            "container": _container_packet(process, _u64(process, obj) if obj else 0),
        }
    if site_va == 0x3B20D2:
        ctx = _u(frame, "r14")
        obj = _u64(process, ctx + 0xA0)
        return {
            "ctx": ctx,
            "ctx_a0": obj,
            "object": _object_packet(process, obj),
            "container": _container_packet(process, _u64(process, obj) if obj else 0),
        }
    if site_va == 0x3C8F90:
        ctx = _u(frame, "rdi")
        obj = _u64(process, ctx + 0xA0)
        return {
            "ctx": ctx,
            "ctx_a0": obj,
            "object": _object_packet(process, obj),
            "container": _container_packet(process, _u64(process, obj) if obj else 0),
        }
    return None


def _consumer_packet(frame, site_va):
    process = frame.GetThread().GetProcess()
    if site_va == 0x3C9540:
        ctx = _u(frame, "rdi")
        obj = _u64(process, ctx + 0xA0)
        container = _u64(process, obj) if obj else 0
        return {
            "ctx": ctx,
            "ctx_a0": obj,
            "object": _object_packet(process, obj),
            "container": _container_packet(process, container),
        }
    if site_va == 0x3C9558:
        ctx = _u(frame, "rbx")
        obj = _u(frame, "rdi")
        container = _u64(process, obj) if obj else 0
        return {
            "ctx": ctx,
            "ctx_a0": obj,
            "object": _object_packet(process, obj),
            "container": _container_packet(process, container),
        }
    if site_va == 0x3C956F:
        obj = _u(frame, "rax")
        container = _u64(process, obj) if obj else 0
        return {
            "ctx": _u(frame, "rbx"),
            "ctx_a0": obj,
            "object": _object_packet(process, obj),
            "container": _container_packet(process, container),
        }
    if site_va == 0x3C9578:
        container = _u(frame, "rdi")
        return {
            "container": _container_packet(process, container),
        }
    if site_va == 0x3C957D:
        ctx = _u(frame, "rbx")
        obj = _u64(process, ctx + 0xA0)
        container = _u64(process, obj) if obj else 0
        return {
            "ctx": ctx,
            "ctx_a0": obj,
            "object": _object_packet(process, obj),
            "container": _container_packet(process, container),
        }
    if site_va == 0xE6C30:
        container = _u(frame, "rdi")
        return {
            "container": _container_packet(process, container),
        }
    if site_va == 0xE6CD6:
        tid = str(frame.GetThread().GetThreadID())
        entry = _state()["e6c30_thread_entry"].get(tid)
        return {
            "entry_container": entry,
            "return_r14b": _u(frame, "r14") & 0xFF,
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
        bp.SetScriptCallbackFunction("c6_context_a0_consumer_probe.hit")
        state["breakpoint_ids"][str(bp.GetID())] = f"0x{va:x}"
    print("INSTALLED", len(state["breakpoint_ids"]), "of", len(SITES))


def hit(frame, bp_loc, _dict):
    state = _state()
    target = frame.GetThread().GetProcess().GetTarget()
    site_va = _module_va(target, frame.GetPC())
    site_key = f"0x{site_va:x}" if site_va is not None else "unknown"
    counts = state["counts"].setdefault(
        site_key,
        {"name": "unknown", "hits": 0, "recorded": 0, "disabled_at_cap": False, "read_errors": 0},
    )
    counts["hits"] += 1

    context = _context_packet(frame, site_va)
    consumer = _consumer_packet(frame, site_va)
    if site_va == 0xE6C30 and consumer and consumer.get("container"):
        state["e6c30_thread_entry"][str(frame.GetThread().GetThreadID())] = consumer["container"]["container_ptr"]

    packets = [packet for packet in (context, consumer) if packet]
    for packet in packets:
        ctx = packet.get("ctx")
        obj = packet.get("ctx_a0")
        container = packet.get("container", {}).get("container_ptr") if packet.get("container") else None
        _remember(state["consumer_contexts"], ctx)
        _remember(state["ctx_a0_values"], obj)
        _remember(state["consumer_objects"], obj)
        _remember(state["consumer_containers"], container)

    if packets and len(state["events"]) < state["event_limit"]:
        state["events"].append(
            {
                "site": site_key,
                "name": SITES.get(site_va, "unknown"),
                "thread_id": frame.GetThread().GetThreadID(),
                "stack": _stack(frame.GetThread(), 10),
                "context": context,
                "consumer": consumer,
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
