import builtins
import json
import os
import struct


GATE_BEFORE = 0x2488B9
GATE_AFTER = 0x2488BE
RECORD_STRIDE = 0x2C


def reset(
    label="",
    sample_limit=96,
    max_records=512,
    watch_hit_cap=64,
    step_cap=60000,
    watch_limit=3,
    disable_after_state5=True,
):
    builtins.l16_prefusion_promoted_record_watch = {
        "label": label,
        "sample_limit": sample_limit,
        "max_records": max_records,
        "watch_hit_cap": watch_hit_cap,
        "step_cap": step_cap,
        "watch_limit": watch_limit,
        "disable_after_state5": disable_after_state5,
        "breakpoint_ids": {},
        "counts": {
            "gate_before_hits": 0,
            "gate_after_hits": 0,
            "promotion_events": 0,
            "promoted_records_total": 0,
            "watchpoints_armed": 0,
            "watchpoint_hits": 0,
            "state5_target2_hits": 0,
        },
        "active_before_by_thread": {},
        "gate_before": [],
        "gate_after": [],
        "armed": [],
        "watchpoint_samples": [],
        "errors": [],
        "drive_steps": 0,
        "drive_hit_step_cap": False,
    }


def _state():
    if not hasattr(builtins, "l16_prefusion_promoted_record_watch"):
        reset()
    return builtins.l16_prefusion_promoted_record_watch


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


def _u64(data, off=0):
    return struct.unpack_from("<Q", data, off)[0]


def _i32_from(data, off):
    return struct.unpack_from("<i", data, off)[0]


def _sample(process, addr, size=32):
    data = _read(process, addr, size)
    if data is None:
        return None
    return {"addr": addr, "size": size, "hex": data.hex()}


def _vector_header(process, vector_addr):
    data = _read(process, vector_addr, 24)
    if data is None:
        return {"addr": vector_addr, "read_ok": False}
    begin = _u64(data, 0)
    end = _u64(data, 8)
    cap = _u64(data, 16)
    byte_len = end - begin if end >= begin else None
    cap_bytes = cap - begin if cap >= begin else None
    return {
        "addr": vector_addr,
        "read_ok": True,
        "begin": begin,
        "end": end,
        "cap": cap,
        "byte_len": byte_len,
        "record_count": byte_len // RECORD_STRIDE if byte_len is not None else None,
        "byte_len_mod_stride": byte_len % RECORD_STRIDE if byte_len is not None else None,
        "cap_bytes": cap_bytes,
        "cap_records": cap_bytes // RECORD_STRIDE if cap_bytes is not None else None,
    }


def _record_list(process, vector_addr):
    header = _vector_header(process, vector_addr)
    if not header.get("read_ok"):
        return {"vector": header, "read_ok": False, "records": []}
    count = header.get("record_count") or 0
    limited = min(count, _state()["max_records"])
    data = _read(process, header["begin"], limited * RECORD_STRIDE) if limited else b""
    if data is None:
        return {"vector": header, "read_ok": False, "records": []}
    records = []
    counts = {}
    for index in range(limited):
        off = index * RECORD_STRIDE
        state_val = _i32_from(data, off + 0x24)
        target_val = _i32_from(data, off + 0x28)
        key = f"{state_val}:{target_val}"
        counts[key] = counts.get(key, 0) + 1
        records.append(
            {
                "index": index,
                "record_addr": header["begin"] + off,
                "state_0x24": state_val,
                "target_0x28": target_val,
                "coord_i32_0x14": _i32_from(data, off + 0x14),
                "coord_i32_0x18": _i32_from(data, off + 0x18),
            }
        )
    return {
        "vector": header,
        "read_ok": True,
        "records_scanned": limited,
        "records_truncated": count > limited,
        "state_target_counts": counts,
        "records": records,
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


def _registers(frame):
    return {
        name: _u(frame, name)
        for name in (
            "rax",
            "rbx",
            "rcx",
            "rdx",
            "rsi",
            "rdi",
            "r8",
            "r9",
            "r10",
            "r11",
            "r12",
            "r13",
            "r14",
            "r15",
            "rbp",
            "rsp",
            "rip",
        )
    }


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


def _append_limited(key, packet):
    state = _state()
    if len(state[key]) < state["sample_limit"]:
        state[key].append(packet)


def _representatives(promoted, limit):
    if len(promoted) <= limit:
        return promoted
    indices = [0, len(promoted) // 2, len(promoted) - 1]
    out = []
    seen = set()
    for idx in indices:
        rec = promoted[idx]
        if rec["after"]["index"] not in seen:
            seen.add(rec["after"]["index"])
            out.append(rec)
    return out[:limit]


def _record_now(process, record_addr):
    data = _read(process, record_addr, RECORD_STRIDE)
    if data is None:
        return None
    return {
        "record_addr": record_addr,
        "state_0x24": _i32_from(data, 0x24),
        "target_0x28": _i32_from(data, 0x28),
        "coord_i32_0x14": _i32_from(data, 0x14),
        "coord_i32_0x18": _i32_from(data, 0x18),
        "record_hex": data.hex(),
    }


def _disable_breakpoint_by_name(debugger, name):
    bp_id = _state()["breakpoint_ids"].get(name)
    if not bp_id:
        return
    bp = debugger.GetSelectedTarget().FindBreakpointByID(int(bp_id))
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def install_breakpoints(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    for site, name in ((GATE_BEFORE, "gate_before_2488b9"), (GATE_AFTER, "gate_after_2488be")):
        before = target.GetNumBreakpoints()
        debugger.HandleCommand(f"breakpoint set --shlib libcp.dylib --address 0x{site:x}")
        after = target.GetNumBreakpoints()
        if after <= before:
            state["errors"].append({"site": f"0x{site:x}", "error": "breakpoint not created"})
            continue
        bp = target.GetBreakpointAtIndex(after - 1)
        if not bp or not bp.IsValid():
            state["errors"].append({"site": f"0x{site:x}", "error": "invalid breakpoint"})
            continue
        bp.SetScriptCallbackFunction("prefusion_promoted_record_watch_probe.hit")
        state["breakpoint_ids"][name] = bp.GetID()
    print("L16_PREFUSION_PROMOTED_RECORD_WATCH_INSTALLED", json.dumps(state["breakpoint_ids"], sort_keys=True))


def _before(frame, process, regs, thread_id, stack):
    state = _state()
    snapshot = _record_list(process, regs["rsi"])
    packet = {
        "site": "gate_before_2488b9",
        "thread_id": thread_id,
        "state_arg_rdi": regs["rdi"],
        "vector_arg_rsi": regs["rsi"],
        "snapshot": {
            "vector": snapshot.get("vector"),
            "read_ok": snapshot.get("read_ok"),
            "records_scanned": snapshot.get("records_scanned"),
            "records_truncated": snapshot.get("records_truncated"),
            "state_target_counts": snapshot.get("state_target_counts"),
        },
        "stack": stack[:6],
    }
    state["active_before_by_thread"][str(thread_id)] = {
        "vector_addr": regs["rsi"],
        "records": snapshot.get("records", []),
        "packet": packet,
    }
    _append_limited("gate_before", packet)


def _arm_watchpoints(frame, bp_loc, process, target, promoted):
    lldb = builtins.__import__("lldb")
    state = _state()
    if state["counts"]["watchpoints_armed"] > 0:
        return
    for item in _representatives(promoted, state["watch_limit"]):
        after = item["after"]
        record_addr = after["record_addr"]
        watch_addr = record_addr + 0x24
        arm = {
            "record_index": after["index"],
            "record_addr": record_addr,
            "watch_addr": watch_addr,
            "watch_size": 8,
            "before": item["before"],
            "after": after,
            "record_at_arm": _record_now(process, record_addr),
            "watched_bytes_at_arm": _sample(process, watch_addr, 8),
            "thread_id": frame.GetThread().GetThreadID(),
            "stack": _stack(frame.GetThread(), 8),
        }
        error = lldb.SBError()
        wp = target.WatchAddress(watch_addr, 8, True, True, error)
        if error.Success() and wp.IsValid():
            arm["watchpoint_id"] = wp.GetID()
            arm["watchpoint_error"] = None
            state["counts"]["watchpoints_armed"] += 1
        else:
            arm["watchpoint_id"] = None
            arm["watchpoint_error"] = error.GetCString()
            state["errors"].append(arm)
        state["armed"].append(arm)
    if state["counts"]["watchpoints_armed"] > 0:
        bp_loc.GetBreakpoint().SetEnabled(False)
        _disable_breakpoint_by_name(target.GetDebugger(), "gate_before_2488b9")


def _after(frame, bp_loc, process, target, regs, thread_id, stack):
    state = _state()
    active = state["active_before_by_thread"].get(str(thread_id))
    vector_addr = active.get("vector_addr") if active else regs["r13"]
    before_records = active.get("records", []) if active else []
    after_snapshot = _record_list(process, vector_addr)
    after_records = after_snapshot.get("records", [])
    promoted = []
    for before, after in zip(before_records, after_records):
        if (
            before.get("state_0x24") == 3
            and before.get("target_0x28") == 2
            and after.get("state_0x24") == 4
            and after.get("target_0x28") == 2
        ):
            promoted.append({"before": before, "after": after})
    packet = {
        "site": "gate_after_2488be",
        "thread_id": thread_id,
        "vector_addr": vector_addr,
        "matched_active_before_vector": bool(active and active.get("vector_addr") == vector_addr),
        "snapshot": {
            "vector": after_snapshot.get("vector"),
            "read_ok": after_snapshot.get("read_ok"),
            "records_scanned": after_snapshot.get("records_scanned"),
            "records_truncated": after_snapshot.get("records_truncated"),
            "state_target_counts": after_snapshot.get("state_target_counts"),
        },
        "promoted_count": len(promoted),
        "promoted_indices_first32": [item["after"]["index"] for item in promoted[:32]],
        "stack": stack[:6],
    }
    if promoted:
        state["counts"]["promotion_events"] += 1
        state["counts"]["promoted_records_total"] += len(promoted)
        _arm_watchpoints(frame, bp_loc, process, target, promoted)
    _append_limited("gate_after", packet)


def hit(frame, bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    pc_va = _module_va(target, frame.GetPC())
    regs = _registers(frame)
    stack = _stack(frame.GetThread(), 12)
    thread_id = frame.GetThread().GetThreadID()
    if pc_va == GATE_BEFORE:
        state["counts"]["gate_before_hits"] += 1
        _before(frame, process, regs, thread_id, stack)
    elif pc_va == GATE_AFTER:
        state["counts"]["gate_after_hits"] += 1
        _after(frame, bp_loc, process, target, regs, thread_id, stack)
    else:
        state["errors"].append({"error": "unexpected breakpoint", "pc_va": pc_va})
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


def _disable_watchpoints(debugger):
    target = debugger.GetSelectedTarget()
    for packet in _state()["armed"]:
        wp_id = packet.get("watchpoint_id")
        if not wp_id:
            continue
        wp = target.FindWatchpointByID(int(wp_id))
        if wp and wp.IsValid():
            wp.SetEnabled(False)


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
    record_addr = meta.get("record_addr") if meta else None
    watch_addr = meta.get("watch_addr") if meta else None
    record_now = _record_now(process, record_addr) if record_addr else None
    sample = {
        "watchpoint_id": wp_id,
        "watchpoint": meta,
        "thread_id": thread.GetThreadID(),
        "pc": frame.GetPC(),
        "libcp_va": _module_va(target, frame.GetPC()),
        "registers": _registers(frame),
        "record_now": record_now,
        "watched_bytes_at_stop": _sample(process, watch_addr, 8) if watch_addr else None,
        "stack": _stack(thread, 18),
    }
    state["watchpoint_samples"].append(sample)
    state["counts"]["watchpoint_hits"] = len(state["watchpoint_samples"])
    saw_state5_target2 = bool(
        record_now
        and record_now.get("state_0x24") == 5
        and record_now.get("target_0x28") == 2
    )
    if saw_state5_target2:
        state["counts"]["state5_target2_hits"] += 1
    if (
        len(state["watchpoint_samples"]) >= state["watch_hit_cap"]
        or (state.get("disable_after_state5") and saw_state5_target2)
    ):
        _disable_watchpoints(debugger)


def drive_until_exit_or_step_cap(debugger):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process.IsValid() and process.GetState() == lldb.eStateStopped and steps < state["step_cap"]:
        _record_watchpoint_stop(debugger)
        steps += 1
        process.Continue()
    state["drive_steps"] = steps
    state["drive_hit_step_cap"] = (
        process.IsValid()
        and process.GetState() == lldb.eStateStopped
        and steps >= state["step_cap"]
    )
    print("L16_PREFUSION_PROMOTED_RECORD_WATCH_DRIVE_STEPS", steps)


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
