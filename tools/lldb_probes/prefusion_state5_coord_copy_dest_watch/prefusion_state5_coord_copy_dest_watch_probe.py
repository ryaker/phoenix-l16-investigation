import builtins
import json
import math
import os
import struct


COPY_CALL_A = 0x224E23
COPY_RET_A = 0x224E28
COPY_CALL_B = 0x224F03
COPY_RET_B = 0x224F08
SENTINEL_PAIR = (-1.0, -1.0)


def reset(
    label="",
    sample_limit=128,
    max_vector_pairs=65536,
    watch_limit=3,
    watch_pairs_per_copy=1,
    watch_hit_cap=64,
    step_cap=300000,
    copy_call_a=COPY_CALL_A,
    copy_ret_a=COPY_RET_A,
    copy_call_b=COPY_CALL_B,
    copy_ret_b=COPY_RET_B,
    site_label="copy_dest",
    read_call_header=True,
):
    builtins.l16_prefusion_state5_coord_copy_dest_watch = {
        "label": label,
        "sample_limit": sample_limit,
        "max_vector_pairs": max_vector_pairs,
        "watch_limit": watch_limit,
        "watch_pairs_per_copy": watch_pairs_per_copy,
        "watch_hit_cap": watch_hit_cap,
        "step_cap": step_cap,
        "read_call_header": read_call_header,
        "breakpoint_ids": {},
        "sites": {
            "call_a": {
                "va": copy_call_a,
                "name": f"{site_label}_call_a_{copy_call_a:x}",
                "count_key": "copy_call_a_hits",
            },
            "ret_a": {
                "va": copy_ret_a,
                "name": f"{site_label}_ret_a_{copy_ret_a:x}",
                "count_key": "copy_ret_a_hits",
            },
            "call_b": {
                "va": copy_call_b,
                "name": f"{site_label}_call_b_{copy_call_b:x}",
                "count_key": "copy_call_b_hits",
            },
            "ret_b": {
                "va": copy_ret_b,
                "name": f"{site_label}_ret_b_{copy_ret_b:x}",
                "count_key": "copy_ret_b_hits",
            },
        },
        "counts": {
            "copy_call_a_hits": 0,
            "copy_call_b_hits": 0,
            "copy_ret_a_hits": 0,
            "copy_ret_b_hits": 0,
            "copy_ret_without_pending": 0,
            "copy_pairs_admitted": 0,
            "watchpoints_armed": 0,
            "watchpoint_hits": 0,
            "watchpoints_disabled_after_cap": 0,
            "copy_breakpoints_disabled_after_watch_limit": 0,
        },
        "pending_by_thread": {},
        "watched_addrs": {},
        "copy_calls": [],
        "copy_returns": [],
        "armed": [],
        "watchpoint_samples": [],
        "errors": [],
        "drive_steps": 0,
        "drive_hit_step_cap": False,
    }


def _state():
    if not hasattr(builtins, "l16_prefusion_state5_coord_copy_dest_watch"):
        reset()
    return builtins.l16_prefusion_state5_coord_copy_dest_watch


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    if not addr or size < 0:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u64(data, off=0):
    return struct.unpack_from("<Q", data, off)[0]


def _f32(data, off=0):
    return struct.unpack_from("<f", data, off)[0]


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


def _vector_header(process, vector_addr, elem_size):
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
        "elem_size": elem_size,
        "elem_count": byte_len // elem_size if byte_len is not None else None,
        "byte_len_mod_elem": byte_len % elem_size if byte_len is not None else None,
        "cap_bytes": cap_bytes,
        "cap_elems": cap_bytes // elem_size if cap_bytes is not None else None,
    }


def _pair(process, pair_addr):
    data = _read(process, pair_addr, 8)
    if data is None:
        return {"addr": pair_addr, "read_ok": False}
    x = _f32(data, 0)
    y = _f32(data, 4)
    return {
        "addr": pair_addr,
        "read_ok": True,
        "x": x,
        "y": y,
        "is_sentinel_neg1_neg1": x == SENTINEL_PAIR[0] and y == SENTINEL_PAIR[1],
        "both_finite": math.isfinite(x) and math.isfinite(y),
        "hex": data.hex(),
    }


def _vector_summary(process, vector_addr):
    header = _vector_header(process, vector_addr, 8)
    summary = {
        "vector_addr": vector_addr,
        "vector": header,
        "pairs_scanned": 0,
        "pairs_truncated": False,
        "sentinel_neg1_neg1": 0,
        "finite_non_sentinel": 0,
        "nonfinite": 0,
        "non_sentinel_samples": [],
    }
    count = header.get("elem_count")
    begin = header.get("begin")
    if not header.get("read_ok") or count is None or not begin:
        return summary
    limited = min(count, _state()["max_vector_pairs"])
    data = _read(process, begin, limited * 8) if limited else b""
    if data is None:
        summary["read_ok"] = False
        return summary
    summary["read_ok"] = True
    summary["pairs_scanned"] = limited
    summary["pairs_truncated"] = count > limited
    for index in range(limited):
        off = index * 8
        x = _f32(data, off)
        y = _f32(data, off + 4)
        if x == SENTINEL_PAIR[0] and y == SENTINEL_PAIR[1]:
            summary["sentinel_neg1_neg1"] += 1
        elif math.isfinite(x) and math.isfinite(y):
            summary["finite_non_sentinel"] += 1
            if len(summary["non_sentinel_samples"]) < 32:
                summary["non_sentinel_samples"].append(
                    {
                        "index": index,
                        "addr": begin + off,
                        "x": x,
                        "y": y,
                        "hex": data[off : off + 8].hex(),
                    }
                )
        else:
            summary["nonfinite"] += 1
    return summary


def _disable_breakpoint(debugger, name):
    bp_id = _state()["breakpoint_ids"].get(name)
    if not bp_id:
        return
    bp = debugger.GetSelectedTarget().FindBreakpointByID(int(bp_id))
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def _disable_copy_breakpoints(debugger):
    for site in _state()["sites"].values():
        _disable_breakpoint(debugger, site["name"])


def _disable_watchpoints(debugger):
    target = debugger.GetSelectedTarget()
    for packet in _state()["armed"]:
        wp_id = packet.get("watchpoint_id")
        if not wp_id:
            continue
        wp = target.FindWatchpointByID(int(wp_id))
        if wp and wp.IsValid():
            wp.SetEnabled(False)


def install_breakpoints(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    sites = (
        (state["sites"]["call_a"]["va"], state["sites"]["call_a"]["name"]),
        (state["sites"]["ret_a"]["va"], state["sites"]["ret_a"]["name"]),
        (state["sites"]["call_b"]["va"], state["sites"]["call_b"]["name"]),
        (state["sites"]["ret_b"]["va"], state["sites"]["ret_b"]["name"]),
    )
    for site, name in sites:
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
        bp.SetScriptCallbackFunction("prefusion_state5_coord_copy_dest_watch_probe.hit")
        state["breakpoint_ids"][name] = bp.GetID()
    print(
        "L16_PREFUSION_STATE5_COORD_COPY_DEST_WATCH_INSTALLED",
        json.dumps(state["breakpoint_ids"], sort_keys=True),
    )


def _pending_list(thread_id):
    state = _state()
    key = str(thread_id)
    if key not in state["pending_by_thread"]:
        state["pending_by_thread"][key] = []
    return state["pending_by_thread"][key]


def _copy_call(frame, thread_id, regs, pc_va):
    state = _state()
    process = frame.GetThread().GetProcess()
    if pc_va == state["sites"]["call_a"]["va"]:
        state["counts"][state["sites"]["call_a"]["count_key"]] += 1
        site = state["sites"]["call_a"]["name"]
    else:
        state["counts"][state["sites"]["call_b"]["count_key"]] += 1
        site = state["sites"]["call_b"]["name"]
    packet = {
        "site": site,
        "thread_id": thread_id,
        "pc_va": pc_va,
        "dest_vector_addr": regs["rdi"],
        "source_begin": regs["rsi"],
        "source_end": regs["rdx"],
        "source_byte_len": regs["rdx"] - regs["rsi"] if regs["rdx"] >= regs["rsi"] else None,
        "source_pair_count": (regs["rdx"] - regs["rsi"]) // 8 if regs["rdx"] >= regs["rsi"] else None,
        "dest_header_before": _vector_header(process, regs["rdi"], 8)
        if state.get("read_call_header", True)
        else {"read_ok": "skipped"},
        "registers": regs,
        "stack": _stack(frame.GetThread(), 12),
    }
    _pending_list(thread_id).append(packet)
    _append_limited("copy_calls", packet)


def _arm_watchpoints_from_dest_copy(process, target, return_packet):
    lldb = builtins.__import__("lldb")
    state = _state()
    candidates = return_packet.get("dest_after", {}).get("non_sentinel_samples", [])[
        : state["watch_pairs_per_copy"]
    ]
    for pair_info in candidates:
        if state["counts"]["watchpoints_armed"] >= state["watch_limit"]:
            break
        addr = pair_info.get("addr")
        if not addr or str(addr) in state["watched_addrs"]:
            continue
        arm = {
            "copy_return_sample_index": len(state["copy_returns"]),
            "copy_site": return_packet.get("site"),
            "copy_call_site": return_packet.get("copy_call", {}).get("site"),
            "dest_vector_addr": return_packet.get("dest_vector_addr"),
            "pair_index": pair_info.get("index"),
            "watch_addr": addr,
            "watch_size": 8,
            "watch_mode": "read_write",
            "pair_at_arm": _pair(process, addr),
            "copy_call_stack": return_packet.get("copy_call", {}).get("stack"),
            "copy_return_stack": return_packet.get("stack"),
        }
        error = lldb.SBError()
        wp = target.WatchAddress(addr, 8, True, True, error)
        if error.Success() and wp.IsValid():
            arm["watchpoint_id"] = wp.GetID()
            arm["watchpoint_error"] = None
            state["watched_addrs"][str(addr)] = wp.GetID()
            state["counts"]["watchpoints_armed"] += 1
        else:
            arm["watchpoint_id"] = None
            arm["watchpoint_error"] = error.GetCString()
            state["errors"].append({"error": "watchpoint arm failed", "arm": arm})
        state["armed"].append(arm)
    if state["counts"]["watchpoints_armed"] >= state["watch_limit"]:
        state["counts"]["copy_breakpoints_disabled_after_watch_limit"] = 1
        _disable_copy_breakpoints(target.GetDebugger())


def _copy_ret(frame, thread_id, regs, pc_va):
    state = _state()
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    if pc_va == state["sites"]["ret_a"]["va"]:
        state["counts"][state["sites"]["ret_a"]["count_key"]] += 1
        site = state["sites"]["ret_a"]["name"]
    else:
        state["counts"][state["sites"]["ret_b"]["count_key"]] += 1
        site = state["sites"]["ret_b"]["name"]
    pending = _pending_list(thread_id)
    if not pending:
        state["counts"]["copy_ret_without_pending"] += 1
        return
    call_packet = pending.pop()
    dest_vector_addr = call_packet.get("dest_vector_addr")
    packet = {
        "site": site,
        "thread_id": thread_id,
        "pc_va": pc_va,
        "copy_call": call_packet,
        "dest_vector_addr": dest_vector_addr,
        "dest_after": _vector_summary(process, dest_vector_addr),
        "registers": regs,
        "stack": _stack(frame.GetThread(), 12),
    }
    if packet["dest_after"].get("finite_non_sentinel", 0) > 0:
        state["counts"]["copy_pairs_admitted"] += 1
    _append_limited("copy_returns", packet)
    _arm_watchpoints_from_dest_copy(process, target, packet)


def hit(frame, bp_loc, _dict):
    target = frame.GetThread().GetProcess().GetTarget()
    pc_va = _module_va(target, frame.GetPC())
    regs = _registers(frame)
    thread_id = frame.GetThread().GetThreadID()
    state = _state()
    if pc_va in (state["sites"]["call_a"]["va"], state["sites"]["call_b"]["va"]):
        _copy_call(frame, thread_id, regs, pc_va)
    elif pc_va in (state["sites"]["ret_a"]["va"], state["sites"]["ret_b"]["va"]):
        _copy_ret(frame, thread_id, regs, pc_va)
    else:
        _state()["errors"].append({"error": "unexpected breakpoint", "pc_va": pc_va})
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
    watch_addr = meta.get("watch_addr") if meta else None
    sample = {
        "watchpoint_id": wp_id,
        "watchpoint": meta,
        "thread_id": thread.GetThreadID(),
        "pc": frame.GetPC(),
        "libcp_va": _module_va(target, frame.GetPC()),
        "pair_now": _pair(process, watch_addr) if watch_addr else None,
        "registers": _registers(frame),
        "stack": _stack(thread, 18),
    }
    state["watchpoint_samples"].append(sample)
    state["counts"]["watchpoint_hits"] = len(state["watchpoint_samples"])
    if len(state["watchpoint_samples"]) >= state["watch_hit_cap"]:
        state["counts"]["watchpoints_disabled_after_cap"] = 1
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
    print("L16_PREFUSION_STATE5_COORD_COPY_DEST_WATCH_DRIVE_STEPS", steps)


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
