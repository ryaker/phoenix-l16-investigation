import builtins
import json
import math
import os
import struct


STORE_Y = 0x21B92A
AFTER_STORE_Y = 0x21B930
SECOND_COPY_RETURN = 0x20D309
GATE_LOAD = 0x20D35E
GATE_BRANCH = 0x20D363
GATE_SKIP_TARGET = 0x20D565
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
    sample_limit=256,
    source_arm_limit=3,
    source_hit_cap=4096,
    dest_trace_limit=3,
    dest_hit_cap=512,
    step_cap=1200000,
):
    builtins.l16_prefusion_20ca00_copied_sentinel_gate = {
        "label": label,
        "sample_limit": sample_limit,
        "source_arm_limit": source_arm_limit,
        "source_hit_cap": source_hit_cap,
        "dest_trace_limit": dest_trace_limit,
        "dest_hit_cap": dest_hit_cap,
        "step_cap": step_cap,
        "breakpoint_ids": {},
        "pending_by_thread": {},
        "watched_addrs": {},
        "watchpoints_by_id": {},
        "counts": {
            "store_y_hits": 0,
            "after_store_hits": 0,
            "after_store_without_pending": 0,
            "after_store_pair_is_sentinel": 0,
            "source_watchpoints_armed": 0,
            "source_watch_hits": 0,
            "source_watch_hit_cap_reached": 0,
            "source_copy_20d309_hits": 0,
            "source_copy_index_matches": 0,
            "source_copy_index_mismatches": 0,
            "source_watchpoints_disabled_after_match": 0,
            "source_watchpoints_disabled_after_cap": 0,
            "breakpoints_disabled_after_source_limit": 0,
            "dest_watchpoints_armed": 0,
            "dest_watch_hits": 0,
            "dest_watch_hit_cap_reached": 0,
            "dest_copy_helper_hits": 0,
            "dest_gate_hits": 0,
            "dest_gate_addr_matches": 0,
            "dest_gate_sentinel_pairs": 0,
            "dest_gate_branch_to_skip": 0,
            "dest_watchpoints_disabled_after_trace_limit": 0,
            "non_watchpoint_stops": 0,
        },
        "store_y_samples": [],
        "after_store_samples": [],
        "source_armed": [],
        "source_watch_samples": [],
        "copy_candidates": [],
        "dest_armed": [],
        "dest_watch_samples": [],
        "gate_traces": [],
        "non_watchpoint_stops": [],
        "errors": [],
        "drive_steps": 0,
        "drive_hit_step_cap": False,
    }


def _state():
    if not hasattr(builtins, "l16_prefusion_20ca00_copied_sentinel_gate"):
        reset()
    return builtins.l16_prefusion_20ca00_copied_sentinel_gate


def _read(process, addr, size):
    if not addr or size < 0:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _f32(data, off=0):
    return struct.unpack_from("<f", data, off)[0]


def _u32(data, off=0):
    return struct.unpack_from("<I", data, off)[0]


def _u64(data, off=0):
    return struct.unpack_from("<Q", data, off)[0]


def _s64(data, off=0):
    return struct.unpack_from("<q", data, off)[0]


def _pair(process, addr):
    out = {"addr": addr, "read_ok": False}
    data = _read(process, addr, 8)
    if data is None:
        return out
    x = _f32(data, 0)
    y = _f32(data, 4)
    out.update(
        {
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
    )
    return out


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


def _registers(frame):
    regs = {}
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
    ):
        regs[name] = frame.FindRegister(name).GetValueAsUnsigned()
    return regs


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


def _pc_va(thread):
    return _module_va(thread.GetProcess().GetTarget(), thread.GetFrameAtIndex(0).GetPC())


def _stack(thread, max_depth=18):
    target = thread.GetProcess().GetTarget()
    frames = []
    for idx in range(min(thread.GetNumFrames(), max_depth)):
        frame = thread.GetFrameAtIndex(idx)
        frames.append(
            {
                "index": idx,
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


def install_breakpoints(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    for site, name in ((STORE_Y, "store_y_21b92a"), (AFTER_STORE_Y, "after_store_y_21b930")):
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
        bp.SetScriptCallbackFunction("prefusion_20ca00_copied_sentinel_gate_probe.hit")
        state["breakpoint_ids"][name] = bp.GetID()
    print("L16_PREFUSION_20CA00_COPIED_SENTINEL_GATE_INSTALLED", json.dumps(state["breakpoint_ids"], sort_keys=True))


def _pending_list(thread_id):
    state = _state()
    key = str(thread_id)
    if key not in state["pending_by_thread"]:
        state["pending_by_thread"][key] = []
    return state["pending_by_thread"][key]


def _disable_breakpoints(debugger):
    target = debugger.GetSelectedTarget()
    for bp_id in _state()["breakpoint_ids"].values():
        bp = target.FindBreakpointByID(int(bp_id))
        if bp and bp.IsValid():
            bp.SetEnabled(False)
    _state()["counts"]["breakpoints_disabled_after_source_limit"] = 1


def _disable_source_watchpoints(debugger, reason="source_watchpoints_disabled_after_match"):
    target = debugger.GetSelectedTarget()
    for packet in _state()["source_armed"]:
        wp_id = packet.get("watchpoint_id")
        if not wp_id:
            continue
        wp = target.FindWatchpointByID(int(wp_id))
        if wp and wp.IsValid():
            wp.SetEnabled(False)
    _state()["counts"][reason] = 1


def _disable_dest_watchpoints(debugger):
    target = debugger.GetSelectedTarget()
    for packet in _state()["dest_armed"]:
        wp_id = packet.get("watchpoint_id")
        if not wp_id:
            continue
        wp = target.FindWatchpointByID(int(wp_id))
        if wp and wp.IsValid():
            wp.SetEnabled(False)
    _state()["counts"]["dest_watchpoints_disabled_after_trace_limit"] = 1


def _store_y(frame, regs):
    process = frame.GetThread().GetProcess()
    thread_id = frame.GetThread().GetThreadID()
    pair_addr = regs["rcx"] - 4
    packet = {
        "thread_id": thread_id,
        "pc_va": STORE_Y,
        "store_addr": regs["rcx"],
        "pair_addr": pair_addr,
        "pair_before_y_store": _pair(process, pair_addr),
        "registers": regs,
        "stack": _stack(frame.GetThread(), 12),
    }
    _pending_list(thread_id).append(packet)
    _append_limited("store_y_samples", packet)


def _arm_source_watchpoint(frame, pending, pair_after):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    pair_addr = pending.get("pair_addr")
    if not pair_addr or str(pair_addr) in state["watched_addrs"]:
        return
    if state["counts"]["source_watchpoints_armed"] >= state["source_arm_limit"]:
        return
    arm = {
        "type": "source",
        "thread_id": frame.GetThread().GetThreadID(),
        "watch_addr": pair_addr,
        "watch_size": 8,
        "watch_mode": "read_write",
        "pair_at_arm": pair_after,
        "store_y_packet": pending,
        "after_store_stack": _stack(frame.GetThread(), 12),
    }
    error = lldb.SBError()
    wp = target.WatchAddress(pair_addr, 8, True, True, error)
    if error.Success() and wp.IsValid():
        arm["watchpoint_id"] = wp.GetID()
        arm["watchpoint_error"] = None
        state["watched_addrs"][str(pair_addr)] = wp.GetID()
        state["watchpoints_by_id"][str(wp.GetID())] = arm
        state["counts"]["source_watchpoints_armed"] += 1
    else:
        arm["watchpoint_id"] = None
        arm["watchpoint_error"] = error.GetCString()
        state["errors"].append({"error": "source watchpoint arm failed", "arm": arm})
    state["source_armed"].append(arm)
    if state["counts"]["source_watchpoints_armed"] >= state["source_arm_limit"]:
        _disable_breakpoints(target.GetDebugger())


def _after_store_y(frame, regs):
    state = _state()
    process = frame.GetThread().GetProcess()
    thread_id = frame.GetThread().GetThreadID()
    pending = _pending_list(thread_id)
    if not pending:
        state["counts"]["after_store_without_pending"] += 1
        return
    store_packet = pending.pop()
    pair_addr = store_packet.get("pair_addr")
    pair_after = _pair(process, pair_addr)
    if pair_after.get("is_sentinel_neg1_neg1"):
        state["counts"]["after_store_pair_is_sentinel"] += 1
    packet = {
        "thread_id": thread_id,
        "pc_va": AFTER_STORE_Y,
        "pair_addr": pair_addr,
        "pair_after_y_store": pair_after,
        "store_y_packet": store_packet,
        "registers": regs,
        "stack": _stack(frame.GetThread(), 12),
    }
    _append_limited("after_store_samples", packet)
    if pair_after.get("is_sentinel_neg1_neg1"):
        _arm_source_watchpoint(frame, store_packet, pair_after)


def hit(frame, bp_loc, _dict):
    target = frame.GetThread().GetProcess().GetTarget()
    pc_va = _module_va(target, frame.GetPC())
    regs = _registers(frame)
    state = _state()
    if pc_va == STORE_Y:
        state["counts"]["store_y_hits"] += 1
        _store_y(frame, regs)
    elif pc_va == AFTER_STORE_Y:
        state["counts"]["after_store_hits"] += 1
        _after_store_y(frame, regs)
    else:
        state["errors"].append({"error": "unexpected breakpoint", "pc_va": pc_va})
    return False


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


def _arm_dest_watchpoint(thread, dest_addr, candidate):
    lldb = builtins.__import__("lldb")
    state = _state()
    target = thread.GetProcess().GetTarget()
    _disable_source_watchpoints(target.GetDebugger())
    if state["counts"]["dest_watchpoints_armed"] >= state["dest_trace_limit"]:
        return
    error = lldb.SBError()
    wp = target.WatchAddress(dest_addr, 8, True, True, error)
    arm = {
        "type": "dest",
        "watch_addr": dest_addr,
        "watch_size": 8,
        "watch_mode": "read_write",
        "copy_candidate": candidate,
        "pair_at_arm": _pair(thread.GetProcess(), dest_addr),
    }
    if error.Success() and wp.IsValid():
        arm["watchpoint_id"] = wp.GetID()
        arm["watchpoint_error"] = None
        state["watchpoints_by_id"][str(wp.GetID())] = arm
        state["counts"]["dest_watchpoints_armed"] += 1
    else:
        arm["watchpoint_id"] = None
        arm["watchpoint_error"] = error.GetCString()
        state["errors"].append({"error": "dest watchpoint arm failed", "arm": arm})
    state["dest_armed"].append(arm)


def _record_copy_candidate(thread, sample, meta):
    state = _state()
    process = thread.GetProcess()
    pc_va = sample.get("libcp_va")
    source_offset = COPY_SRC_PC_TO_OFFSET.get(pc_va)
    if source_offset is None:
        return None
    stack = sample.get("stack") or []
    caller_va = stack[1].get("libcp_va") if len(stack) > 1 else None
    if caller_va != SECOND_COPY_RETURN:
        return None

    regs = sample["registers"]
    watch_addr = meta.get("watch_addr")
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
        "source_watchpoint": meta,
    }
    state["counts"]["source_copy_20d309_hits"] += 1
    if index_matches:
        state["counts"]["source_copy_index_matches"] += 1
        _arm_dest_watchpoint(thread, dest_pair_addr, candidate)
    else:
        state["counts"]["source_copy_index_mismatches"] += 1
    _append_limited("copy_candidates", candidate)
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


def _stop_reason_packet(thread):
    target = thread.GetProcess().GetTarget()
    frame = thread.GetFrameAtIndex(0) if thread.GetNumFrames() else None
    data = []
    for idx in range(thread.GetStopReasonDataCount()):
        data.append(thread.GetStopReasonDataAtIndex(idx))
    return {
        "thread_id": thread.GetThreadID(),
        "stop_reason": int(thread.GetStopReason()),
        "stop_reason_data": data,
        "pc": frame.GetPC() if frame else None,
        "libcp_va": _module_va(target, frame.GetPC()) if frame else None,
        "function": str(frame.GetFunctionName() or frame.GetSymbol().GetName()) if frame else None,
        "stack": _stack(thread, 18) if frame else [],
    }


def _trace_gate(thread, sample, meta):
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
        state["errors"].append({"error": "dest gate did not reach branch", "trace": trace})
        _append_limited("gate_traces", trace)
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
    _append_limited("gate_traces", trace)
    if state["counts"]["dest_gate_hits"] >= state["dest_trace_limit"]:
        _disable_dest_watchpoints(process.GetTarget().GetDebugger())
    return trace


def _record_watchpoint_stop(debugger):
    lldb = builtins.__import__("lldb")
    state = _state()
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    if not process or not process.IsValid():
        return False
    thread = process.GetSelectedThread()
    if not thread or not thread.IsValid():
        return False
    stop_data = []
    for idx in range(thread.GetStopReasonDataCount()):
        stop_data.append(thread.GetStopReasonDataAtIndex(idx))
    wp_id = None
    if thread.GetStopReason() == lldb.eStopReasonWatchpoint and stop_data:
        wp_id = stop_data[0]
    else:
        for value in stop_data:
            if str(value) in state["watchpoints_by_id"]:
                wp_id = value
                break
    if wp_id is None:
        return False
    frame = thread.GetFrameAtIndex(0)
    meta = state["watchpoints_by_id"].get(str(wp_id))
    pc_va = _module_va(target, frame.GetPC())
    sample = {
        "watchpoint_id": wp_id,
        "watchpoint": meta,
        "watch_addr": meta.get("watch_addr") if meta else None,
        "watch_type": meta.get("type") if meta else None,
        "thread_id": thread.GetThreadID(),
        "pc": frame.GetPC(),
        "libcp_va": pc_va,
        "stop_reason": int(thread.GetStopReason()),
        "stop_reason_data": stop_data,
        "pair_now": _pair(process, meta.get("watch_addr")) if meta else None,
        "registers": _registers(frame),
        "stack": _stack(thread, 18),
    }
    if not meta:
        state["errors"].append({"error": "watchpoint metadata missing", "sample": sample})
        return True

    if meta.get("type") == "source":
        state["counts"]["source_watch_hits"] += 1
        if state["counts"]["source_watch_hits"] <= state["source_hit_cap"]:
            _append_limited("source_watch_samples", sample)
        else:
            state["counts"]["source_watch_hit_cap_reached"] = 1
            _disable_source_watchpoints(debugger, "source_watchpoints_disabled_after_cap")
        _record_copy_candidate(thread, sample, meta)
    elif meta.get("type") == "dest":
        state["counts"]["dest_watch_hits"] += 1
        if pc_va in COPY_SRC_PC_TO_OFFSET:
            state["counts"]["dest_copy_helper_hits"] += 1
        if pc_va in (GATE_LOAD, GATE_BRANCH):
            sample["gate_trace"] = _trace_gate(thread, sample, meta)
            sample["pc_after_gate_trace"] = _pc_va(thread)
        _append_limited("dest_watch_samples", sample)
        if state["counts"]["dest_watch_hits"] >= state["dest_hit_cap"]:
            state["counts"]["dest_watch_hit_cap_reached"] = 1
            _disable_dest_watchpoints(debugger)
    else:
        state["errors"].append({"error": "unknown watchpoint type", "sample": sample})
    return True


def _watchpoint_hit_counts(debugger):
    counts = {}
    target = debugger.GetSelectedTarget()
    for wp_id in _state()["watchpoints_by_id"]:
        wp = target.FindWatchpointByID(int(wp_id))
        if wp and wp.IsValid():
            counts[str(wp_id)] = wp.GetHitCount()
    return counts


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
        handled_watchpoint = _record_watchpoint_stop(debugger)
        if process.GetState() == lldb.eStateStopped and not handled_watchpoint:
            thread = process.GetSelectedThread()
            packet = _stop_reason_packet(thread) if thread and thread.IsValid() else {"error": "no selected thread"}
            state["counts"]["non_watchpoint_stops"] += 1
            _append_limited("non_watchpoint_stops", packet)
            break
        process.Continue()
    state["drive_steps"] = steps
    if process and process.IsValid():
        state["process_state"] = int(process.GetState())
        state["process_exit_status"] = process.GetExitStatus()


def payload(debugger):
    state = dict(_state())
    state["watchpoint_hit_counts"] = _watchpoint_hit_counts(debugger)
    process = debugger.GetSelectedTarget().GetProcess()
    if process and process.IsValid():
        state["process_state"] = int(process.GetState())
        state["process_exit_status"] = process.GetExitStatus()
    return state


def report_to_file(debugger, path):
    _record_watchpoint_stop(debugger)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload(debugger), fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("L16_PREFUSION_20CA00_COPIED_SENTINEL_GATE_JSON", path)
