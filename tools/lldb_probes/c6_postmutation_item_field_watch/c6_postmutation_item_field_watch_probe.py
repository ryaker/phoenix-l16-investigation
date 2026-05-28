import builtins
import json
import os
import struct


MUTATION_AFTER = 0x3C90A9
KEY15 = 15

DEFAULT_WATCH_SPECS = [
    {"label": "active_0x30", "offset": 0x30, "size": 1},
    {"label": "pair_0x58", "offset": 0x58, "size": 8},
    {"label": "key_0x60", "offset": 0x60, "size": 8},
    {"label": "type_0x100", "offset": 0x100, "size": 8},
]


def reset(label="", watch_specs=None, watch_hit_cap=256, step_cap=4096):
    builtins.l16_c6_postmutation_item_field_watch = {
        "label": label,
        "watch_specs": watch_specs or list(DEFAULT_WATCH_SPECS),
        "watch_hit_cap": watch_hit_cap,
        "step_cap": step_cap,
        "breakpoint_ids": {},
        "counts": {
            "mutation_after_hits": 0,
            "mutation_after_key15_hits": 0,
            "watchpoints_armed": 0,
            "watchpoint_hits": 0,
        },
        "armed": [],
        "watchpoint_samples": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_c6_postmutation_item_field_watch"):
        reset()
    return builtins.l16_c6_postmutation_item_field_watch


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


def _hex(data):
    return data.hex() if data is not None else None


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


def _stack(thread, max_frames=18):
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


def _registers(frame):
    return {
        name: _u(frame, name)
        for name in [
            "rax",
            "rbx",
            "rcx",
            "rdx",
            "rsi",
            "rdi",
            "rsp",
            "rbp",
            "r12",
            "r13",
            "r14",
            "r15",
            "rip",
        ]
    }


def _item_packet(process, item):
    if not item:
        return None
    return {
        "item_ptr": item,
        "active_addr_item_0x30": item + 0x30,
        "active_item_0x30": _u8(process, item + 0x30),
        "pair_item_0x58_0x5c": [_i32(process, item + 0x58), _i32(process, item + 0x5C)],
        "key_item_0x60": _u32(process, item + 0x60),
        "type_item_0x100": _u32(process, item + 0x100),
    }


def _watched_bytes(process, item):
    out = {}
    for spec in _state()["watch_specs"]:
        addr = item + int(spec["offset"])
        out[spec["label"]] = {
            "offset": int(spec["offset"]),
            "size": int(spec["size"]),
            "addr": addr,
            "bytes": _hex(_read(process, addr, int(spec["size"]))),
        }
    return out


def install_breakpoints(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    before = target.GetNumBreakpoints()
    debugger.HandleCommand(f"breakpoint set --shlib libcp.dylib --address 0x{MUTATION_AFTER:x}")
    after = target.GetNumBreakpoints()
    if after <= before:
        state["errors"].append({"site": f"0x{MUTATION_AFTER:x}", "error": "breakpoint not created"})
        return
    bp = target.GetBreakpointAtIndex(after - 1)
    if not bp or not bp.IsValid():
        state["errors"].append({"site": f"0x{MUTATION_AFTER:x}", "error": "invalid breakpoint"})
        return
    bp.SetScriptCallbackFunction("c6_postmutation_item_field_watch_probe.mutation_after")
    state["breakpoint_ids"][str(bp.GetID())] = f"0x{MUTATION_AFTER:x}"
    print("INSTALLED", len(state["breakpoint_ids"]), "of 1")


def mutation_after(frame, bp_loc, _dict):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    state["counts"]["mutation_after_hits"] += 1

    slot = _u(frame, "rbx")
    item = _u64(process, slot)
    packet = _item_packet(process, item)
    if not packet:
        state["errors"].append({"site": "0x3c90a9", "error": "could not read item"})
        return False
    if packet.get("key_item_0x60") != KEY15:
        return False

    state["counts"]["mutation_after_key15_hits"] += 1
    arm = {
        "site": "0x3c90a9",
        "thread_id": frame.GetThread().GetThreadID(),
        "item": packet,
        "watched_bytes_at_arm": _watched_bytes(process, item),
        "registers": _registers(frame),
        "stack": _stack(frame.GetThread(), 14),
        "watchpoints": [],
    }

    for spec in state["watch_specs"]:
        addr = item + int(spec["offset"])
        error = lldb.SBError()
        wp = target.WatchAddress(addr, int(spec["size"]), True, True, error)
        packet_wp = {
            "label": spec["label"],
            "offset": int(spec["offset"]),
            "size": int(spec["size"]),
            "addr": addr,
        }
        if error.Success() and wp.IsValid():
            packet_wp["watchpoint_id"] = wp.GetID()
            packet_wp["watchpoint_error"] = None
            state["counts"]["watchpoints_armed"] += 1
        else:
            packet_wp["watchpoint_id"] = None
            packet_wp["watchpoint_error"] = error.GetCString()
            state["errors"].append({"site": "watch", **packet_wp})
        arm["watchpoints"].append(packet_wp)

    if state["counts"]["watchpoints_armed"]:
        bp_loc.GetBreakpoint().SetEnabled(False)
    state["armed"].append(arm)
    return False


def _watchpoint_hit_counts(debugger):
    counts = {}
    target = debugger.GetSelectedTarget()
    for arm in _state()["armed"]:
        for packet in arm.get("watchpoints", []):
            wp_id = packet.get("watchpoint_id")
            if not wp_id:
                continue
            wp = target.FindWatchpointByID(int(wp_id))
            if wp and wp.IsValid():
                counts[str(wp_id)] = wp.GetHitCount()
    return counts


def _watch_meta(wp_id):
    for arm in _state()["armed"]:
        item = arm.get("item", {}).get("item_ptr")
        for packet in arm.get("watchpoints", []):
            if packet.get("watchpoint_id") == wp_id:
                return item, packet
    return None, None


def _record_watchpoint_stop(debugger):
    lldb = builtins.__import__("lldb")
    state = _state()
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    if not process or not process.IsValid():
        return
    thread = process.GetSelectedThread()
    if not thread or not thread.IsValid():
        return
    if thread.GetStopReason() != lldb.eStopReasonWatchpoint:
        return

    frame = thread.GetFrameAtIndex(0)
    wp_id = thread.GetStopReasonDataAtIndex(0) if thread.GetStopReasonDataCount() else None
    item, meta = _watch_meta(wp_id)
    active_addr = item + 0x30 if item else None
    watched_addr = meta.get("addr") if meta else None
    watched_size = meta.get("size") if meta else None
    sample = {
        "watchpoint_id": wp_id,
        "watch_label": meta.get("label") if meta else None,
        "watch_offset": meta.get("offset") if meta else None,
        "watch_size": watched_size,
        "thread_id": thread.GetThreadID(),
        "pc": frame.GetPC(),
        "libcp_va": _module_va(target, frame.GetPC()),
        "registers": _registers(frame),
        "active_byte_now": _u8(process, active_addr) if active_addr else None,
        "watched_bytes_now": _hex(_read(process, watched_addr, watched_size))
        if watched_addr and watched_size
        else None,
        "item_now": _item_packet(process, item) if item else None,
        "stack": _stack(thread, 18),
    }
    state["watchpoint_samples"].append(sample)
    state["counts"]["watchpoint_hits"] = len(state["watchpoint_samples"])

    if len(state["watchpoint_samples"]) >= state["watch_hit_cap"]:
        for arm in state["armed"]:
            for packet in arm.get("watchpoints", []):
                watch_id = packet.get("watchpoint_id")
                if not watch_id:
                    continue
                wp = target.FindWatchpointByID(int(watch_id))
                if wp and wp.IsValid():
                    wp.SetEnabled(False)


def drive_until_exit_or_step_cap(debugger):
    lldb = builtins.__import__("lldb")
    state = _state()
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    steps = 0
    hit_step_cap = False
    while process and process.IsValid():
        process = target.GetProcess()
        state_now = process.GetState()
        if state_now not in (lldb.eStateStopped, lldb.eStateSuspended):
            break
        _record_watchpoint_stop(debugger)
        if steps >= state["step_cap"]:
            hit_step_cap = True
            break
        process.Continue()
        steps += 1

    _record_watchpoint_stop(debugger)
    state["drive_steps"] = steps
    state["drive_hit_step_cap"] = hit_step_cap


def payload(debugger):
    state = dict(_state())
    state["watchpoint_hit_counts"] = _watchpoint_hit_counts(debugger)
    by_label = {}
    for sample in state.get("watchpoint_samples", []):
        label = sample.get("watch_label")
        by_label[label] = by_label.get(label, 0) + 1
    state["watchpoint_hit_counts_by_label"] = by_label
    process = debugger.GetSelectedTarget().GetProcess()
    if process and process.IsValid():
        state["process_state"] = str(process.GetState())
        state["process_exit_status"] = process.GetExitStatus()
    return state


def report_to_file(debugger, path):
    _record_watchpoint_stop(debugger)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("WROTE", path)
