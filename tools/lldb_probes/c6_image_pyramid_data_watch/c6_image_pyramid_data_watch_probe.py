import builtins
import json
import os
import struct


ZERO_FILL_AFTER = 0x3B2F59


def reset(label="", target_level=0, watch_size=8, watch_hit_cap=32, step_cap=24000):
    builtins.l16_c6_image_pyramid_data_watch = {
        "label": label,
        "target_level": target_level,
        "watch_size": watch_size,
        "watch_hit_cap": watch_hit_cap,
        "step_cap": step_cap,
        "sites": {"0x3b2f59": "after_level_descriptor_zero_fill"},
        "breakpoint_ids": {},
        "counts": {
            "zero_fill_after_hits": 0,
            "target_level_hits": 0,
            "watchpoints_armed": 0,
            "watchpoint_hits": 0,
        },
        "armed": [],
        "watchpoint_samples": [],
        "errors": [],
        "drive_steps": 0,
        "drive_hit_step_cap": False,
    }


def _state():
    if not hasattr(builtins, "l16_c6_image_pyramid_data_watch"):
        reset()
    return builtins.l16_c6_image_pyramid_data_watch


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


def _i32(process, addr):
    data = _read(process, addr, 4)
    return struct.unpack_from("<i", data, 0)[0] if data is not None else None


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


def _stack(thread, max_frames=16):
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


def install_breakpoint(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    before = target.GetNumBreakpoints()
    debugger.HandleCommand(f"breakpoint set --shlib libcp.dylib --address 0x{ZERO_FILL_AFTER:x}")
    after = target.GetNumBreakpoints()
    if after <= before:
        state["errors"].append({"site": "0x3b2f59", "error": "breakpoint not created"})
        return
    bp = target.GetBreakpointAtIndex(after - 1)
    if not bp or not bp.IsValid():
        state["errors"].append({"site": "0x3b2f59", "error": "invalid breakpoint"})
        return
    bp.SetScriptCallbackFunction("c6_image_pyramid_data_watch_probe.zero_fill_after")
    state["breakpoint_ids"][str(bp.GetID())] = "0x3b2f59"
    print("INSTALLED", len(state["breakpoint_ids"]), "of 1")


def zero_fill_after(frame, bp_loc, _dict):
    lldb = builtins.__import__("lldb")
    state = _state()
    state["counts"]["zero_fill_after_hits"] += 1

    level = _u(frame, "r12") & 0xFFFFFFFF
    if level != state["target_level"]:
        return False

    state["counts"]["target_level_hits"] += 1
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    desc_addr = _u(frame, "rbx")
    descriptor = _descriptor(process, desc_addr)
    data_ptr = descriptor.get("data_ptr") if descriptor else None
    packet = {
        "site": "0x3b2f59",
        "level": level,
        "descriptor": descriptor,
        "thread_id": frame.GetThread().GetThreadID(),
        "stack": _stack(frame.GetThread(), 12),
    }

    if data_ptr:
        error = lldb.SBError()
        wp = target.WatchAddress(data_ptr, state["watch_size"], True, True, error)
        if error.Success() and wp.IsValid():
            packet["watchpoint_id"] = wp.GetID()
            packet["watch_address"] = data_ptr
            packet["watch_size"] = state["watch_size"]
            packet["watchpoint_error"] = None
            state["counts"]["watchpoints_armed"] += 1
            bp_loc.GetBreakpoint().SetEnabled(False)
        else:
            packet["watchpoint_id"] = None
            packet["watch_address"] = data_ptr
            packet["watch_size"] = state["watch_size"]
            packet["watchpoint_error"] = error.GetCString()
            state["errors"].append(packet)
    else:
        packet["watchpoint_id"] = None
        packet["watchpoint_error"] = "missing descriptor data pointer"
        state["errors"].append(packet)

    state["armed"].append(packet)
    return False


def _watchpoint_hit_counts(debugger):
    counts = {}
    target = debugger.GetSelectedTarget()
    for packet in _state()["armed"]:
        wp_id = packet.get("watchpoint_id")
        if not wp_id:
            continue
        wp = target.FindWatchpointByID(int(wp_id))
        if wp and wp.IsValid():
            counts[str(wp_id)] = wp.GetHitCount()
    return counts


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
    meta = None
    for packet in state["armed"]:
        if packet.get("watchpoint_id") == wp_id:
            meta = packet
            break
    watch_addr = meta.get("watch_address") if meta else None
    sample = {
        "watchpoint_id": wp_id,
        "watchpoint": meta,
        "thread_id": thread.GetThreadID(),
        "pc": frame.GetPC(),
        "libcp_va": _module_va(target, frame.GetPC()),
        "registers": _registers(frame),
        "watched_bytes_at_stop": _sample(process, watch_addr, min(32, state["watch_size"] or 32)),
        "stack": _stack(thread, 18),
    }
    state["watchpoint_samples"].append(sample)
    state["counts"]["watchpoint_hits"] = len(state["watchpoint_samples"])

    if len(state["watchpoint_samples"]) >= state["watch_hit_cap"]:
        for packet in state["armed"]:
            wp_id = packet.get("watchpoint_id")
            if not wp_id:
                continue
            wp = target.FindWatchpointByID(int(wp_id))
            if wp and wp.IsValid():
                wp.SetEnabled(False)


def drive_until_exit_or_step_cap(debugger):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while (
        process.IsValid()
        and process.GetState() == lldb.eStateStopped
        and steps < state["step_cap"]
    ):
        _record_watchpoint_stop(debugger)
        steps += 1
        process.Continue()
    state["drive_steps"] = steps
    state["drive_hit_step_cap"] = (
        process.IsValid()
        and process.GetState() == lldb.eStateStopped
        and steps >= state["step_cap"]
    )
    print("L16_C6_IMAGE_PYRAMID_DATA_WATCH_DRIVE_STEPS", steps)


def payload(debugger):
    state = dict(_state())
    state["watchpoint_hit_counts"] = _watchpoint_hit_counts(debugger)
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
