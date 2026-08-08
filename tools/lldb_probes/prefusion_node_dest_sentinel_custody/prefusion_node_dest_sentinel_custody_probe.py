import builtins
import json
import math
import os
import struct


COPY_CALL_A = 0x22A61A
COPY_RET_A = 0x22A61F
COPY_CALL_B = 0x22C93A
COPY_RET_B = 0x22C93F
STORE_X = 0x21B923
STORE_Y = 0x21B92A
AFTER_STORE_Y = 0x21B930
WATCH_STOP_AFTER_X_LOAD = 0x20B912
X_COMPARE_BRANCH = 0x20B91D
SENTINEL_PATH = 0x20BA90
OUTPUT_COMPARE_BRANCH = 0x20BAAB
OUTPUT_SKIP_TARGET = 0x20BAFD
OUTPUT_UPDATE_WRITE = 0x20BAC0
SECOND_20CA00_COPY_RETURN = 0x20D309
GATE_LOAD = 0x20D35E
GATE_BRANCH = 0x20D363
GATE_SKIP_TARGET = 0x20D565
SCORE_GUARD_AFTER_COMPARE = 0x218BC4
SCORE_GUARD_SKIP_TARGET = 0x218CB8
SENTINEL_FLOAT = -1.0

COPY_SRC_PC_TO_OFFSET = {
    0xE0B80: 0x00,
    0xE0B82: 0x00,
    0xE0B84: 0x04,
    0xE0B87: 0x04,
    0xE0BB0: 0x00,
    0xE0BB2: 0x00,
    0xE0BB4: 0x04,
    0xE0BB7: 0x04,
    0xE0BBA: 0x08,
    0xE0BBD: 0x08,
    0xE0BC0: 0x0C,
    0xE0BC3: 0x0C,
    0xE0BC6: 0x10,
    0xE0BC9: 0x10,
    0xE0BCC: 0x14,
    0xE0BCF: 0x14,
    0xE0BD2: 0x18,
    0xE0BD5: 0x18,
    0xE0BD8: 0x1C,
    0xE0BDB: 0x1C,
}


def reset(
    label="",
    sample_limit=128,
    max_vector_pairs=65536,
    copied_pair_addr_limit=250000,
    match_limit=16,
    watch_hit_cap=64,
    step_cap=800000,
    branch_step_20b5e0=False,
    branch_trace_limit=1,
    record_20ca00_source_index=False,
    branch_step_218bc4=False,
    trace_20ca00_gate=False,
    dest_trace_limit=1,
    dest_hit_cap=512,
    target_pair_indices=None,
):
    target_pair_indices = list(target_pair_indices or [])
    builtins.l16_prefusion_node_dest_sentinel_custody = {
        "label": label,
        "sample_limit": sample_limit,
        "max_vector_pairs": max_vector_pairs,
        "copied_pair_addr_limit": copied_pair_addr_limit,
        "match_limit": match_limit,
        "watch_hit_cap": watch_hit_cap,
        "step_cap": step_cap,
        "branch_step_20b5e0": branch_step_20b5e0,
        "branch_trace_limit": branch_trace_limit,
        "record_20ca00_source_index": record_20ca00_source_index,
        "branch_step_218bc4": branch_step_218bc4,
        "trace_20ca00_gate": trace_20ca00_gate,
        "dest_trace_limit": dest_trace_limit,
        "dest_hit_cap": dest_hit_cap,
        "target_pair_indices": target_pair_indices,
        "breakpoint_ids": {},
        "watched_addrs": {},
        "dest_watchpoints_by_id": {},
        "pending_copy_by_thread": {},
        "pending_x_by_thread": {},
        "pending_y_by_thread": {},
        "_copied_pairs_by_addr": {},
        "_copy_events_by_id": {},
        "counts": {
            "copy_call_a_hits": 0,
            "copy_call_b_hits": 0,
            "copy_ret_a_hits": 0,
            "copy_ret_b_hits": 0,
            "copy_ret_without_pending": 0,
            "copy_vectors_recorded": 0,
            "copy_vectors_with_finite_pairs": 0,
            "copy_pairs_scanned": 0,
            "copied_pair_addrs_recorded": 0,
            "copied_pair_addr_limit_hit": 0,
            "duplicate_copied_pair_addrs": 0,
            "store_x_hits": 0,
            "store_y_hits": 0,
            "after_store_y_hits": 0,
            "after_store_y_without_pending": 0,
            "after_store_pair_is_sentinel": 0,
            "sentinel_matches": 0,
            "sentinel_misses": 0,
            "sentinel_target_skips": 0,
            "sentinel_target_matches": 0,
            "watchpoints_armed": 0,
            "watchpoint_hits": 0,
            "watchpoint_20b912_hits": 0,
            "watchpoint_218bc4_hits": 0,
            "branch_traces": 0,
            "x_branch_to_sentinel_path": 0,
            "output_branch_to_skip": 0,
            "output_update_write_reached": 0,
            "guard_branch_traces": 0,
            "guard_branch_to_skip": 0,
            "guard_branch_not_to_skip": 0,
            "source_copy_20d309_hits": 0,
            "source_copy_index_matches": 0,
            "source_copy_index_mismatches": 0,
            "source_watchpoints_disabled_after_20ca00_match": 0,
            "dest_watchpoints_armed": 0,
            "dest_watch_hits": 0,
            "dest_copy_helper_hits": 0,
            "dest_gate_hits": 0,
            "dest_gate_addr_matches": 0,
            "dest_gate_sentinel_pairs": 0,
            "dest_gate_branch_to_skip": 0,
            "dest_watch_hit_cap_reached": 0,
            "dest_watchpoints_disabled_after_trace_limit": 0,
            "breakpoints_disabled_after_match_limit": 0,
            "watchpoints_disabled_after_cap": 0,
            "watchpoints_disabled_after_branch_trace_limit": 0,
        },
        "copy_calls": [],
        "copy_returns": [],
        "store_x_samples": [],
        "store_y_samples": [],
        "after_store_samples": [],
        "target_skipped_sentinel_matches": [],
        "matches": [],
        "watchpoint_samples": [],
        "branch_traces": [],
        "guard_branch_traces": [],
        "source_copy_20ca00_candidates": [],
        "dest_20ca00_armed": [],
        "dest_20ca00_watch_samples": [],
        "gate_20ca00_traces": [],
        "errors": [],
        "drive_steps": 0,
        "drive_hit_step_cap": False,
    }


def _state():
    if not hasattr(builtins, "l16_prefusion_node_dest_sentinel_custody"):
        reset()
    return builtins.l16_prefusion_node_dest_sentinel_custody


def _read(process, addr, size):
    if not addr or size < 0:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u32(data, off=0):
    return struct.unpack_from("<I", data, off)[0]


def _u64(data, off=0):
    return struct.unpack_from("<Q", data, off)[0]


def _s64(data, off=0):
    return struct.unpack_from("<q", data, off)[0]


def _f32(data, off=0):
    return struct.unpack_from("<f", data, off)[0]


def _qword(process, addr, signed=False):
    data = _read(process, addr, 8)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "value": _s64(data) if signed else _u64(data),
        "hex": data.hex(),
    }


def _pair_from_bytes(addr, data):
    x = _f32(data, 0)
    y = _f32(data, 4)
    return {
        "addr": addr,
        "read_ok": True,
        "hex": data.hex(),
        "x": x,
        "y": y,
        "x_bits": _u32(data, 0),
        "y_bits": _u32(data, 4),
        "both_finite": math.isfinite(x) and math.isfinite(y),
        "is_sentinel_neg1_neg1": x == SENTINEL_FLOAT and y == SENTINEL_FLOAT,
        "x_is_sentinel": x == SENTINEL_FLOAT,
        "y_is_sentinel": y == SENTINEL_FLOAT,
    }


def _pair(process, addr):
    data = _read(process, addr, 8)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return _pair_from_bytes(addr, data)


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
        name: frame.FindRegister(name).GetValueAsUnsigned()
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


def _rflags(frame):
    reg = frame.FindRegister("rflags")
    if not reg or not reg.IsValid():
        reg = frame.FindRegister("eflags")
    if not reg or not reg.IsValid():
        return {"read_ok": False}
    value = reg.GetValueAsUnsigned()
    return {
        "read_ok": True,
        "value": value,
        "cf": value & 1,
        "pf": (value >> 2) & 1,
        "zf": (value >> 6) & 1,
        "jae_taken": (value & 1) == 0,
        "jbe_taken": ((value & 1) == 1) or (((value >> 6) & 1) == 1),
    }


def _pc_va(thread):
    frame = thread.GetFrameAtIndex(0)
    return _module_va(thread.GetProcess().GetTarget(), frame.GetPC())


def _stack(thread, max_depth=16):
    target = thread.GetProcess().GetTarget()
    frames = []
    for index in range(min(thread.GetNumFrames(), max_depth)):
        frame = thread.GetFrameAtIndex(index)
        frames.append(
            {
                "index": index,
                "pc": frame.GetPC(),
                "libcp_va": _module_va(target, frame.GetPC()),
                "function": str(frame.GetFunctionName() or frame.GetSymbol().GetName()),
            }
        )
    return frames


def _append_limited(key, packet):
    state = _state()
    if len(state[key]) < state["sample_limit"]:
        state[key].append(packet)


def _pending_list(key, thread_id):
    state = _state()
    bucket = state[key]
    tid = str(thread_id)
    if tid not in bucket:
        bucket[tid] = []
    return bucket[tid]


def _copy_site_name(pc_va, suffix):
    if pc_va == COPY_CALL_A:
        return f"copy_a_call_{COPY_CALL_A:x}"
    if pc_va == COPY_RET_A:
        return f"copy_a_ret_{COPY_RET_A:x}"
    if pc_va == COPY_CALL_B:
        return f"copy_b_call_{COPY_CALL_B:x}"
    if pc_va == COPY_RET_B:
        return f"copy_b_ret_{COPY_RET_B:x}"
    return f"unknown_{suffix}_{pc_va:x}"


def _disable_all_breakpoints(debugger):
    target = debugger.GetSelectedTarget()
    for bp_id in _state()["breakpoint_ids"].values():
        bp = target.FindBreakpointByID(int(bp_id))
        if bp and bp.IsValid():
            bp.SetEnabled(False)
    _state()["counts"]["breakpoints_disabled_after_match_limit"] = 1


def _disable_watchpoints(debugger, reason="watchpoints_disabled_after_cap"):
    target = debugger.GetSelectedTarget()
    for packet in _state()["matches"]:
        wp_id = packet.get("watchpoint_id")
        if not wp_id:
            continue
        wp = target.FindWatchpointByID(int(wp_id))
        if wp and wp.IsValid():
            wp.SetEnabled(False)
    _state()["counts"][reason] = 1


def _disable_dest_watchpoints(debugger):
    target = debugger.GetSelectedTarget()
    for packet in _state()["dest_20ca00_armed"]:
        wp_id = packet.get("watchpoint_id")
        if not wp_id:
            continue
        wp = target.FindWatchpointByID(int(wp_id))
        if wp and wp.IsValid():
            wp.SetEnabled(False)
    _state()["counts"]["dest_watchpoints_disabled_after_trace_limit"] = 1


def install_breakpoints(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    for site, name in (
        (COPY_CALL_A, "copy_call_a_22a61a"),
        (COPY_RET_A, "copy_ret_a_22a61f"),
        (COPY_CALL_B, "copy_call_b_22c93a"),
        (COPY_RET_B, "copy_ret_b_22c93f"),
        (STORE_X, "store_x_21b923"),
        (STORE_Y, "store_y_21b92a"),
        (AFTER_STORE_Y, "after_store_y_21b930"),
    ):
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
        bp.SetScriptCallbackFunction("prefusion_node_dest_sentinel_custody_probe.hit")
        state["breakpoint_ids"][name] = bp.GetID()
    print("L16_PREFUSION_NODE_DEST_SENTINEL_CUSTODY_INSTALLED", json.dumps(state["breakpoint_ids"], sort_keys=True))


def _copy_call(frame, regs, pc_va):
    state = _state()
    thread = frame.GetThread()
    thread_id = thread.GetThreadID()
    if pc_va == COPY_CALL_A:
        state["counts"]["copy_call_a_hits"] += 1
    else:
        state["counts"]["copy_call_b_hits"] += 1
    packet = {
        "thread_id": thread_id,
        "pc_va": pc_va,
        "site": _copy_site_name(pc_va, "call"),
        "dest_vector_addr": regs["rdi"],
        "source_begin": regs["rsi"],
        "source_end": regs["rdx"],
        "source_byte_len": regs["rdx"] - regs["rsi"] if regs["rdx"] >= regs["rsi"] else None,
        "source_pair_count": (regs["rdx"] - regs["rsi"]) // 8 if regs["rdx"] >= regs["rsi"] else None,
        "registers": regs,
        "stack": _stack(thread, 12),
    }
    _pending_list("pending_copy_by_thread", thread_id).append(packet)
    _append_limited("copy_calls", packet)


def _copy_event_public(event):
    return {
        "copy_event_id": event.get("copy_event_id"),
        "copy_site": event.get("site"),
        "copy_call_site": event.get("copy_call", {}).get("site"),
        "dest_vector_addr": event.get("dest_vector_addr"),
        "dest_after": event.get("dest_after"),
        "copy_call_stack": event.get("copy_call", {}).get("stack"),
        "copy_return_stack": event.get("stack"),
        "source_pair_count": event.get("copy_call", {}).get("source_pair_count"),
    }


def _record_copied_pairs(process, event):
    state = _state()
    header = event["dest_after"]
    count = header.get("elem_count")
    begin = header.get("begin")
    summary = {
        "pairs_scanned": 0,
        "pairs_truncated": False,
        "finite_non_sentinel": 0,
        "sentinel_neg1_neg1": 0,
        "nonfinite": 0,
        "finite_samples": [],
    }
    if not header.get("read_ok") or count is None or not begin:
        summary["read_ok"] = False
        return summary
    limited = min(count, state["max_vector_pairs"])
    data = _read(process, begin, limited * 8) if limited else b""
    if data is None:
        summary["read_ok"] = False
        return summary
    summary["read_ok"] = True
    summary["pairs_scanned"] = limited
    summary["pairs_truncated"] = count > limited
    state["counts"]["copy_pairs_scanned"] += limited
    copied = state["_copied_pairs_by_addr"]
    event_id = event["copy_event_id"]
    for index in range(limited):
        off = index * 8
        pair = _pair_from_bytes(begin + off, data[off : off + 8])
        if pair["is_sentinel_neg1_neg1"]:
            summary["sentinel_neg1_neg1"] += 1
            continue
        if pair["both_finite"]:
            summary["finite_non_sentinel"] += 1
            if len(summary["finite_samples"]) < 32:
                summary["finite_samples"].append(
                    {
                        "index": index,
                        "addr": pair["addr"],
                        "x": pair["x"],
                        "y": pair["y"],
                        "hex": pair["hex"],
                    }
                )
            key = str(pair["addr"])
            if key in copied:
                state["counts"]["duplicate_copied_pair_addrs"] += 1
                continue
            if state["counts"]["copied_pair_addrs_recorded"] >= state["copied_pair_addr_limit"]:
                state["counts"]["copied_pair_addr_limit_hit"] = 1
                continue
            copied[key] = {
                "copy_event_id": event_id,
                "pair_index": index,
                "pair_at_copy": pair,
            }
            state["counts"]["copied_pair_addrs_recorded"] += 1
        else:
            summary["nonfinite"] += 1
    return summary


def _copy_ret(frame, regs, pc_va):
    state = _state()
    process = frame.GetThread().GetProcess()
    thread = frame.GetThread()
    thread_id = thread.GetThreadID()
    if pc_va == COPY_RET_A:
        state["counts"]["copy_ret_a_hits"] += 1
    else:
        state["counts"]["copy_ret_b_hits"] += 1
    pending = _pending_list("pending_copy_by_thread", thread_id)
    if not pending:
        state["counts"]["copy_ret_without_pending"] += 1
        return
    call_packet = pending.pop()
    event_id = len(state["_copy_events_by_id"]) + 1
    dest_vector_addr = call_packet.get("dest_vector_addr")
    event = {
        "copy_event_id": event_id,
        "thread_id": thread_id,
        "pc_va": pc_va,
        "site": _copy_site_name(pc_va, "ret"),
        "copy_call": call_packet,
        "dest_vector_addr": dest_vector_addr,
        "dest_after": _vector_header(process, dest_vector_addr, 8),
        "registers": regs,
        "stack": _stack(thread, 12),
    }
    event["copied_pair_summary"] = _record_copied_pairs(process, event)
    state["_copy_events_by_id"][event_id] = event
    state["counts"]["copy_vectors_recorded"] += 1
    if event["copied_pair_summary"].get("finite_non_sentinel", 0) > 0:
        state["counts"]["copy_vectors_with_finite_pairs"] += 1
    public_event = _copy_event_public(event)
    public_event["copied_pair_summary"] = event["copied_pair_summary"]
    _append_limited("copy_returns", public_event)


def _find_pending_x(thread_id, pair_addr):
    pending = _pending_list("pending_x_by_thread", thread_id)
    for index in range(len(pending) - 1, -1, -1):
        packet = pending[index]
        if packet.get("pair_addr") == pair_addr:
            return pending.pop(index)
    return None


def _store_x(frame, regs):
    state = _state()
    process = frame.GetThread().GetProcess()
    thread = frame.GetThread()
    thread_id = thread.GetThreadID()
    pair_addr = regs["rax"] + regs["rdx"] * 8
    packet = {
        "thread_id": thread_id,
        "pc_va": STORE_X,
        "pair_addr": pair_addr,
        "pair_before_x_store": _pair(process, pair_addr),
        "registers": regs,
        "stack": _stack(thread, 12),
    }
    _pending_list("pending_x_by_thread", thread_id).append(packet)
    _append_limited("store_x_samples", packet)


def _store_y(frame, regs):
    state = _state()
    process = frame.GetThread().GetProcess()
    thread = frame.GetThread()
    thread_id = thread.GetThreadID()
    pair_addr = regs["rcx"] - 4
    x_packet = _find_pending_x(thread_id, pair_addr)
    packet = {
        "thread_id": thread_id,
        "pc_va": STORE_Y,
        "store_addr": regs["rcx"],
        "pair_addr": pair_addr,
        "pair_mid_before_y_store": _pair(process, pair_addr),
        "store_x_packet": x_packet,
        "registers": regs,
        "stack": _stack(thread, 12),
    }
    _pending_list("pending_y_by_thread", thread_id).append(packet)
    _append_limited("store_y_samples", packet)


def _after_store_y(frame, regs):
    state = _state()
    process = frame.GetThread().GetProcess()
    thread = frame.GetThread()
    thread_id = thread.GetThreadID()
    pending = _pending_list("pending_y_by_thread", thread_id)
    if not pending:
        state["counts"]["after_store_y_without_pending"] += 1
        return
    store_y_packet = pending.pop()
    pair_addr = store_y_packet.get("pair_addr")
    pair_after = _pair(process, pair_addr)
    if pair_after.get("is_sentinel_neg1_neg1"):
        state["counts"]["after_store_pair_is_sentinel"] += 1
    copied = state["_copied_pairs_by_addr"].get(str(pair_addr))
    packet = {
        "thread_id": thread_id,
        "pc_va": AFTER_STORE_Y,
        "pair_addr": pair_addr,
        "pair_after_y_store": pair_after,
        "store_y_packet": store_y_packet,
        "copied_addr_seen_before_store": copied is not None,
        "registers": regs,
        "stack": _stack(thread, 12),
    }
    _append_limited("after_store_samples", packet)
    if not pair_after.get("is_sentinel_neg1_neg1"):
        return
    if copied is None:
        state["counts"]["sentinel_misses"] += 1
        return
    target_indices = set(state.get("target_pair_indices") or [])
    if target_indices and copied.get("pair_index") not in target_indices:
        state["counts"]["sentinel_target_skips"] += 1
        skipped = dict(packet)
        skipped["copied_pair"] = copied
        _append_limited("target_skipped_sentinel_matches", skipped)
        return
    if target_indices:
        state["counts"]["sentinel_target_matches"] += 1
    event = state["_copy_events_by_id"].get(copied["copy_event_id"], {})
    match = {
        "match_index": state["counts"]["sentinel_matches"] + 1,
        "pair_addr": pair_addr,
        "copied_pair": copied,
        "copy_event": _copy_event_public(event),
        "store_x_packet": store_y_packet.get("store_x_packet"),
        "store_y_packet": store_y_packet,
        "pair_after_y_store": pair_after,
        "after_store_stack": _stack(thread, 12),
    }
    _arm_watchpoint_for_match(frame, match)
    state["matches"].append(match)
    state["counts"]["sentinel_matches"] += 1
    if state["counts"]["sentinel_matches"] >= state["match_limit"]:
        _disable_all_breakpoints(frame.GetThread().GetProcess().GetTarget().GetDebugger())


def _arm_watchpoint_for_match(frame, match):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    pair_addr = match.get("pair_addr")
    if not pair_addr or str(pair_addr) in state["watched_addrs"]:
        return
    error = lldb.SBError()
    wp = target.WatchAddress(pair_addr, 8, True, True, error)
    if error.Success() and wp.IsValid():
        match["watchpoint_id"] = wp.GetID()
        match["watchpoint_error"] = None
        match["watch_addr"] = pair_addr
        match["watch_size"] = 8
        match["watch_mode"] = "read_write"
        state["watched_addrs"][str(pair_addr)] = wp.GetID()
        state["counts"]["watchpoints_armed"] += 1
    else:
        match["watchpoint_id"] = None
        match["watchpoint_error"] = error.GetCString()
        state["errors"].append({"error": "watchpoint arm failed", "match": match})


def hit(frame, bp_loc, _dict):
    target = frame.GetThread().GetProcess().GetTarget()
    pc_va = _module_va(target, frame.GetPC())
    regs = _registers(frame)
    state = _state()
    if pc_va in (COPY_CALL_A, COPY_CALL_B):
        _copy_call(frame, regs, pc_va)
    elif pc_va in (COPY_RET_A, COPY_RET_B):
        _copy_ret(frame, regs, pc_va)
    elif pc_va == STORE_X:
        state["counts"]["store_x_hits"] += 1
        _store_x(frame, regs)
    elif pc_va == STORE_Y:
        state["counts"]["store_y_hits"] += 1
        _store_y(frame, regs)
    elif pc_va == AFTER_STORE_Y:
        state["counts"]["after_store_y_hits"] += 1
        _after_store_y(frame, regs)
    else:
        state["errors"].append({"error": "unexpected breakpoint", "pc_va": pc_va})
    return False


def _watchpoint_hit_counts(debugger):
    counts = {}
    target = debugger.GetSelectedTarget()
    for packet in _state()["matches"]:
        wp_id = packet.get("watchpoint_id")
        if not wp_id:
            continue
        wp = target.FindWatchpointByID(int(wp_id))
        if wp and wp.IsValid():
            counts[str(wp_id)] = wp.GetHitCount()
    for wp_id in _state()["dest_watchpoints_by_id"]:
        wp = target.FindWatchpointByID(int(wp_id))
        if wp and wp.IsValid():
            counts[str(wp_id)] = wp.GetHitCount()
    return counts


def _source_index_packet(process, regs, watch_addr):
    header = regs.get("r15")
    begin = _qword(process, header)
    end = _qword(process, header + 8)
    out = {
        "source_header": header,
        "source_begin": begin,
        "source_end": end,
        "source_index": None,
        "source_index_ok": False,
    }
    if begin.get("read_ok") and end.get("read_ok"):
        begin_value = begin["value"]
        end_value = end["value"]
        if begin_value <= watch_addr < end_value and (watch_addr - begin_value) % 8 == 0:
            out["source_index"] = (watch_addr - begin_value) // 8
            out["source_index_ok"] = True
    return out


def _parent_gate_index_packet(thread):
    process = thread.GetProcess()
    if thread.GetNumFrames() < 2:
        return {"read_ok": False, "error": "no parent frame"}
    parent = thread.GetFrameAtIndex(1)
    parent_rbp = parent.FindRegister("rbp").GetValueAsUnsigned()
    gate_index = _qword(process, parent_rbp - 0x2A0, signed=True)
    return {
        "read_ok": gate_index.get("read_ok"),
        "parent_rbp": parent_rbp,
        "gate_index_slot": gate_index,
        "gate_index": gate_index.get("value") if gate_index.get("read_ok") else None,
        "parent_stack_frame": {
            "pc": parent.GetPC(),
            "libcp_va": _module_va(process.GetTarget(), parent.GetPC()),
            "function": str(parent.GetFunctionName() or parent.GetSymbol().GetName()),
        },
    }


def _arm_20ca00_dest_watchpoint(thread, dest_addr, candidate):
    lldb = builtins.__import__("lldb")
    state = _state()
    if not state.get("trace_20ca00_gate"):
        return
    if state["counts"]["dest_watchpoints_armed"] >= state["dest_trace_limit"]:
        return
    process = thread.GetProcess()
    target = process.GetTarget()
    _disable_watchpoints(target.GetDebugger(), "source_watchpoints_disabled_after_20ca00_match")
    error = lldb.SBError()
    wp = target.WatchAddress(dest_addr, 8, True, True, error)
    arm = {
        "type": "dest_20ca00",
        "watch_addr": dest_addr,
        "watch_size": 8,
        "watch_mode": "read_write",
        "source_candidate": candidate,
        "pair_at_arm": _pair(process, dest_addr),
    }
    if error.Success() and wp.IsValid():
        arm["watchpoint_id"] = wp.GetID()
        arm["watchpoint_error"] = None
        state["dest_watchpoints_by_id"][str(wp.GetID())] = arm
        state["counts"]["dest_watchpoints_armed"] += 1
    else:
        arm["watchpoint_id"] = None
        arm["watchpoint_error"] = error.GetCString()
        state["errors"].append({"error": "20ca00 dest watchpoint arm failed", "arm": arm})
    state["dest_20ca00_armed"].append(arm)


def _record_20ca00_source_candidate(thread, sample):
    state = _state()
    process = thread.GetProcess()
    pc_va = sample.get("libcp_va")
    source_offset = COPY_SRC_PC_TO_OFFSET.get(pc_va)
    if source_offset is None:
        return None
    stack = sample.get("stack") or []
    caller_va = stack[1].get("libcp_va") if len(stack) > 1 else None
    if caller_va != SECOND_20CA00_COPY_RETURN:
        return None

    regs = sample["registers"]
    watch_addr = sample.get("watch_addr")
    pair_offset = source_offset & ~0x7
    expected_source_pair = regs["rcx"] + pair_offset
    dest_pair_addr = regs["rdi"] + pair_offset
    source_index = _source_index_packet(process, regs, watch_addr)
    gate_index = _parent_gate_index_packet(thread)
    index_matches = (
        source_index.get("source_index_ok")
        and gate_index.get("read_ok")
        and source_index.get("source_index") == gate_index.get("gate_index")
    )
    candidate = {
        "pc_va": pc_va,
        "caller_va": caller_va,
        "source_offset": source_offset,
        "pair_offset": pair_offset,
        "source_watch_addr": watch_addr,
        "expected_source_pair": expected_source_pair,
        "source_pair_matches_watch": expected_source_pair == watch_addr,
        "dest_pair_addr": dest_pair_addr,
        "dest_pair_at_candidate": _pair(process, dest_pair_addr),
        "source_index": source_index,
        "gate_index": gate_index,
        "index_matches_gate": index_matches,
        "registers": regs,
        "stack": stack,
    }
    state["counts"]["source_copy_20d309_hits"] += 1
    if index_matches:
        state["counts"]["source_copy_index_matches"] += 1
        _arm_20ca00_dest_watchpoint(thread, dest_pair_addr, candidate)
    else:
        state["counts"]["source_copy_index_mismatches"] += 1
    _append_limited("source_copy_20ca00_candidates", candidate)
    return candidate


def _step_to(thread, target_va, max_steps):
    visited = []
    for _ in range(max_steps + 1):
        pc_va = _pc_va(thread)
        visited.append(pc_va)
        if pc_va == target_va:
            return {"hit": True, "visited": visited}
        thread.StepInstruction(False)
    return {"hit": False, "visited": visited, "last_pc_va": _pc_va(thread)}


def _step_once(thread):
    before = _pc_va(thread)
    thread.StepInstruction(False)
    return {"before": before, "after": _pc_va(thread)}


def _trace_20b5e0_branch(thread, sample):
    state = _state()
    process = thread.GetProcess()
    watch_addr = sample.get("watch_addr")
    packet = {
        "thread_id": thread.GetThreadID(),
        "match_index": sample.get("match_index"),
        "watch_addr": watch_addr,
        "pair_at_20b912": _pair(process, watch_addr) if watch_addr else None,
        "initial_stack": _stack(thread, 18),
    }

    x_step = _step_to(thread, X_COMPARE_BRANCH, 8)
    packet["step_to_x_compare_branch"] = x_step
    if not x_step.get("hit"):
        packet["error"] = "did not reach x compare branch"
        state["errors"].append(packet)
        return packet

    frame = thread.GetFrameAtIndex(0)
    packet["x_compare_branch"] = {
        "pc_va": _pc_va(thread),
        "rflags_after_ucomiss": _rflags(frame),
        "registers": _registers(frame),
    }
    packet["x_branch_step"] = _step_once(thread)
    if packet["x_branch_step"].get("after") == SENTINEL_PATH:
        state["counts"]["x_branch_to_sentinel_path"] += 1

    output_step = _step_to(thread, OUTPUT_COMPARE_BRANCH, 48)
    packet["step_to_output_compare_branch"] = output_step
    if OUTPUT_UPDATE_WRITE in output_step.get("visited", []):
        state["counts"]["output_update_write_reached"] += 1
    if not output_step.get("hit"):
        packet["error"] = "did not reach output compare branch"
        state["errors"].append(packet)
        return packet

    frame = thread.GetFrameAtIndex(0)
    packet["output_compare_branch"] = {
        "pc_va": _pc_va(thread),
        "rflags_after_ucomiss": _rflags(frame),
        "registers": _registers(frame),
    }
    packet["output_branch_step"] = _step_once(thread)
    if packet["output_branch_step"].get("after") == OUTPUT_SKIP_TARGET:
        state["counts"]["output_branch_to_skip"] += 1
    elif packet["output_branch_step"].get("after") == OUTPUT_UPDATE_WRITE:
        state["counts"]["output_update_write_reached"] += 1

    state["counts"]["branch_traces"] += 1
    _append_limited("branch_traces", packet)
    if state["counts"]["branch_traces"] >= state["branch_trace_limit"]:
        _disable_watchpoints(
            process.GetTarget().GetDebugger(),
            "watchpoints_disabled_after_branch_trace_limit",
        )
    return packet


def _trace_218bc4_branch(thread, sample):
    state = _state()
    process = thread.GetProcess()
    watch_addr = sample.get("watch_addr")
    frame = thread.GetFrameAtIndex(0)
    flags = _rflags(frame)
    packet = {
        "thread_id": thread.GetThreadID(),
        "match_index": sample.get("match_index"),
        "watch_addr": watch_addr,
        "pair_at_branch": _pair(process, watch_addr) if watch_addr else None,
        "rflags_after_ucomiss": flags,
        "initial_stack": _stack(thread, 18),
        "static_branch": {
            "instruction_va": SCORE_GUARD_AFTER_COMPARE,
            "instruction": "jae 0x218cb8",
            "skip_target_va": SCORE_GUARD_SKIP_TARGET,
        },
    }
    packet["branch_step"] = _step_once(thread)
    if packet["branch_step"].get("after") == SCORE_GUARD_SKIP_TARGET:
        state["counts"]["guard_branch_to_skip"] += 1
    else:
        state["counts"]["guard_branch_not_to_skip"] += 1
    state["counts"]["guard_branch_traces"] += 1
    _append_limited("guard_branch_traces", packet)
    if state["counts"]["guard_branch_traces"] >= state["branch_trace_limit"]:
        _disable_watchpoints(
            process.GetTarget().GetDebugger(),
            "watchpoints_disabled_after_branch_trace_limit",
        )
    return packet


def _trace_20ca00_gate(thread, sample, meta):
    state = _state()
    process = thread.GetProcess()
    current = _pc_va(thread)
    trace = {
        "thread_id": thread.GetThreadID(),
        "watch_addr": meta.get("watch_addr"),
        "initial_pc_va": current,
        "initial_stack": _stack(thread, 18),
        "pair_at_gate": _pair(process, meta.get("watch_addr")),
    }
    if current == GATE_LOAD:
        trace["step_to_gate_branch"] = _step_to(thread, GATE_BRANCH, 2)
    elif current == GATE_BRANCH:
        trace["step_to_gate_branch"] = {"hit": True, "visited": [current]}
    else:
        trace["step_to_gate_branch"] = {"hit": False, "visited": [current], "unexpected_pc": current}
    if not trace["step_to_gate_branch"].get("hit"):
        state["errors"].append({"error": "20ca00 dest gate did not reach branch", "trace": trace})
        _append_limited("gate_20ca00_traces", trace)
        return trace

    frame = thread.GetFrameAtIndex(0)
    regs = _registers(frame)
    gate_addr = regs["r15"] + regs["rax"] * 8
    trace["gate_branch"] = {
        "pc_va": _pc_va(thread),
        "registers": regs,
        "rflags_after_ucomiss": _rflags(frame),
        "computed_gate_addr": gate_addr,
        "computed_gate_addr_matches_watch": gate_addr == meta.get("watch_addr"),
    }
    if gate_addr == meta.get("watch_addr"):
        state["counts"]["dest_gate_addr_matches"] += 1
    if trace["pair_at_gate"].get("is_sentinel_neg1_neg1"):
        state["counts"]["dest_gate_sentinel_pairs"] += 1
    trace["gate_branch_step"] = _step_once(thread)
    if trace["gate_branch_step"].get("after") == GATE_SKIP_TARGET:
        state["counts"]["dest_gate_branch_to_skip"] += 1
    state["counts"]["dest_gate_hits"] += 1
    _append_limited("gate_20ca00_traces", trace)
    if state["counts"]["dest_gate_hits"] >= state["dest_trace_limit"]:
        _disable_dest_watchpoints(process.GetTarget().GetDebugger())
    return trace


def _record_20ca00_dest_watchpoint_stop(debugger, thread, frame, wp_id, meta, pc_va):
    state = _state()
    process = thread.GetProcess()
    sample = {
        "watchpoint_id": wp_id,
        "watchpoint": meta,
        "watch_addr": meta.get("watch_addr"),
        "thread_id": thread.GetThreadID(),
        "pc": frame.GetPC(),
        "libcp_va": pc_va,
        "pair_now": _pair(process, meta.get("watch_addr")),
        "registers": _registers(frame),
        "stack": _stack(thread, 18),
    }
    state["counts"]["dest_watch_hits"] += 1
    if pc_va in COPY_SRC_PC_TO_OFFSET:
        state["counts"]["dest_copy_helper_hits"] += 1
    if pc_va in (GATE_LOAD, GATE_BRANCH):
        sample["gate_trace"] = _trace_20ca00_gate(thread, sample, meta)
        sample["pc_after_gate_trace"] = _pc_va(thread)
    _append_limited("dest_20ca00_watch_samples", sample)
    if state["counts"]["dest_watch_hits"] >= state["dest_hit_cap"]:
        state["counts"]["dest_watch_hit_cap_reached"] = 1
        _disable_dest_watchpoints(debugger)


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
    pc_va = _module_va(target, frame.GetPC())
    dest_meta = state["dest_watchpoints_by_id"].get(str(wp_id))
    if dest_meta:
        _record_20ca00_dest_watchpoint_stop(debugger, thread, frame, wp_id, dest_meta, pc_va)
        return
    match = None
    for packet in state["matches"]:
        if packet.get("watchpoint_id") == wp_id:
            match = packet
            break
    watch_addr = match.get("watch_addr") if match else None
    pair_now = _pair(process, watch_addr) if watch_addr else None
    sample = {
        "watchpoint_id": wp_id,
        "match_index": match.get("match_index") if match else None,
        "watch_addr": watch_addr,
        "thread_id": thread.GetThreadID(),
        "pc": frame.GetPC(),
        "libcp_va": pc_va,
        "pair_now": pair_now,
        "registers": _registers(frame),
        "stack": _stack(thread, 18),
    }
    if pc_va == WATCH_STOP_AFTER_X_LOAD:
        state["counts"]["watchpoint_20b912_hits"] += 1
        if (
            state.get("branch_step_20b5e0")
            and pair_now
            and pair_now.get("is_sentinel_neg1_neg1")
            and state["counts"]["branch_traces"] < state["branch_trace_limit"]
        ):
            sample["branch_trace"] = _trace_20b5e0_branch(thread, sample)
            sample["pc_after_branch_trace"] = _pc_va(thread)
    if pc_va == SCORE_GUARD_AFTER_COMPARE:
        state["counts"]["watchpoint_218bc4_hits"] += 1
        sample["rflags_after_ucomiss"] = _rflags(frame)
        sample["static_branch"] = {
            "instruction_va": SCORE_GUARD_AFTER_COMPARE,
            "instruction": "jae 0x218cb8",
            "skip_target_va": SCORE_GUARD_SKIP_TARGET,
        }
        if (
            state.get("branch_step_218bc4")
            and pair_now
            and pair_now.get("is_sentinel_neg1_neg1")
            and state["counts"]["guard_branch_traces"] < state["branch_trace_limit"]
        ):
            sample["guard_branch_trace"] = _trace_218bc4_branch(thread, sample)
            sample["pc_after_guard_branch_trace"] = _pc_va(thread)
    if state.get("record_20ca00_source_index") and pair_now and pair_now.get("is_sentinel_neg1_neg1"):
        candidate = _record_20ca00_source_candidate(thread, sample)
        if candidate is not None:
            sample["source_copy_20ca00_candidate_index"] = len(state["source_copy_20ca00_candidates"])
    _append_limited("watchpoint_samples", sample)
    state["counts"]["watchpoint_hits"] += 1
    if state["counts"]["watchpoint_hits"] >= state["watch_hit_cap"]:
        _disable_watchpoints(debugger)


def drive_until_exit_or_step_cap(debugger):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process and process.IsValid() and process.GetState() != lldb.eStateExited:
        if steps >= state["step_cap"]:
            state["drive_hit_step_cap"] = True
            break
        steps += 1
        _record_watchpoint_stop(debugger)
        process.Continue()
    state["drive_steps"] = steps
    if process and process.IsValid():
        state["process_state"] = int(process.GetState())
        state["process_exit_status"] = process.GetExitStatus()
    print("L16_PREFUSION_NODE_DEST_SENTINEL_CUSTODY_DRIVE_STEPS", steps)


def payload(debugger):
    state = dict(_state())
    state.pop("_copied_pairs_by_addr", None)
    state.pop("_copy_events_by_id", None)
    state["watchpoint_hit_counts"] = _watchpoint_hit_counts(debugger)
    process = debugger.GetSelectedTarget().GetProcess()
    if process and process.IsValid():
        state["process_state"] = int(process.GetState())
        state["process_exit_status"] = process.GetExitStatus()
    return state


def report_to_file(debugger, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("WROTE", path)
