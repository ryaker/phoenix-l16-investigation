import builtins
import json
import math
import os
import struct


STORE_Y = 0x21B92A
AFTER_STORE_Y = 0x21B930
GUARD_AFTER_COMPARE = 0x218BC4
GUARD_SKIP_TARGET = 0x218CB8
SENTINEL_FLOAT = -1.0


def reset(
    label="",
    sample_limit=256,
    arm_limit=3,
    skip_sentinel_pairs=0,
    watch_hit_cap=512,
    step_cap=800000,
    branch_trace_limit=0,
):
    builtins.l16_prefusion_sentinel_score_guard = {
        "label": label,
        "sample_limit": sample_limit,
        "arm_limit": arm_limit,
        "skip_sentinel_pairs": skip_sentinel_pairs,
        "watch_hit_cap": watch_hit_cap,
        "step_cap": step_cap,
        "branch_trace_limit": branch_trace_limit,
        "breakpoint_ids": {},
        "pending_by_thread": {},
        "watched_addrs": {},
        "counts": {
            "store_y_hits": 0,
            "after_store_hits": 0,
            "after_store_without_pending": 0,
            "after_store_pair_is_sentinel": 0,
            "sentinel_pairs_skipped_before_arm": 0,
            "watchpoints_armed": 0,
            "watchpoint_hits": 0,
            "watchpoint_guard_hits": 0,
            "watchpoint_guard_known_sentinel_hits": 0,
            "watchpoint_guard_skip_by_flags": 0,
            "watchpoint_guard_not_skip_by_flags": 0,
            "guard_branch_traces": 0,
            "guard_branch_to_skip": 0,
            "guard_branch_not_to_skip": 0,
            "breakpoints_disabled_after_arm_limit": 0,
            "watchpoints_disabled_after_cap": 0,
            "watchpoints_disabled_after_branch_trace_limit": 0,
        },
        "store_y_samples": [],
        "after_store_samples": [],
        "armed": [],
        "watchpoint_samples": [],
        "guard_samples": [],
        "guard_branch_traces": [],
        "errors": [],
        "drive_steps": 0,
        "drive_hit_step_cap": False,
    }


def _state():
    if not hasattr(builtins, "l16_prefusion_sentinel_score_guard"):
        reset()
    return builtins.l16_prefusion_sentinel_score_guard


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
    frame = thread.GetFrameAtIndex(0)
    return _module_va(thread.GetProcess().GetTarget(), frame.GetPC())


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


def _disable_breakpoints(debugger):
    target = debugger.GetSelectedTarget()
    for bp_id in _state()["breakpoint_ids"].values():
        bp = target.FindBreakpointByID(int(bp_id))
        if bp and bp.IsValid():
            bp.SetEnabled(False)
    _state()["counts"]["breakpoints_disabled_after_arm_limit"] = 1


def _disable_watchpoints(debugger):
    target = debugger.GetSelectedTarget()
    for packet in _state()["armed"]:
        wp_id = packet.get("watchpoint_id")
        if not wp_id:
            continue
        wp = target.FindWatchpointByID(int(wp_id))
        if wp and wp.IsValid():
            wp.SetEnabled(False)
    _state()["counts"]["watchpoints_disabled_after_cap"] = 1


def _disable_watchpoints_after_branch_limit(debugger):
    _disable_watchpoints(debugger)
    state = _state()
    state["counts"]["watchpoints_disabled_after_cap"] = 0
    state["counts"]["watchpoints_disabled_after_branch_trace_limit"] = 1


def _step_once(thread):
    before = _pc_va(thread)
    thread.StepInstruction(False)
    return {"before": before, "after": _pc_va(thread)}


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
        bp.SetScriptCallbackFunction("prefusion_sentinel_score_guard_probe.hit")
        state["breakpoint_ids"][name] = bp.GetID()
    print("L16_PREFUSION_SENTINEL_SCORE_GUARD_INSTALLED", json.dumps(state["breakpoint_ids"], sort_keys=True))


def _pending_list(thread_id):
    state = _state()
    key = str(thread_id)
    if key not in state["pending_by_thread"]:
        state["pending_by_thread"][key] = []
    return state["pending_by_thread"][key]


def _store_y(frame, regs):
    state = _state()
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


def _arm_watchpoint(frame, pending, pair_after):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    pair_addr = pending.get("pair_addr")
    if not pair_addr or str(pair_addr) in state["watched_addrs"]:
        return
    if state["counts"]["watchpoints_armed"] >= state["arm_limit"]:
        return
    arm = {
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
        state["counts"]["watchpoints_armed"] += 1
    else:
        arm["watchpoint_id"] = None
        arm["watchpoint_error"] = error.GetCString()
        state["errors"].append({"error": "watchpoint arm failed", "arm": arm})
    state["armed"].append(arm)
    if state["counts"]["watchpoints_armed"] >= state["arm_limit"]:
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
    if not pair_after.get("is_sentinel_neg1_neg1"):
        return
    if state["counts"]["after_store_pair_is_sentinel"] <= state["skip_sentinel_pairs"]:
        state["counts"]["sentinel_pairs_skipped_before_arm"] += 1
        return
    _arm_watchpoint(frame, store_packet, pair_after)


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
    pc_va = _module_va(target, frame.GetPC())
    pair_now = _pair(process, watch_addr) if watch_addr else None
    sample = {
        "watchpoint_id": wp_id,
        "watchpoint": meta,
        "thread_id": thread.GetThreadID(),
        "pc": frame.GetPC(),
        "libcp_va": pc_va,
        "pair_now": pair_now,
        "registers": _registers(frame),
        "stack": _stack(thread, 18),
    }
    if pc_va == GUARD_AFTER_COMPARE:
        flags = _rflags(frame)
        sample["rflags_after_ucomiss"] = flags
        sample["static_branch"] = {
            "instruction_va": GUARD_AFTER_COMPARE,
            "instruction": "jae 0x218cb8",
            "skip_target_va": GUARD_SKIP_TARGET,
        }
        state["counts"]["watchpoint_guard_hits"] += 1
        if pair_now and pair_now.get("is_sentinel_neg1_neg1"):
            state["counts"]["watchpoint_guard_known_sentinel_hits"] += 1
            if flags.get("jae_taken"):
                state["counts"]["watchpoint_guard_skip_by_flags"] += 1
            else:
                state["counts"]["watchpoint_guard_not_skip_by_flags"] += 1
            if state["branch_trace_limit"] and state["counts"]["guard_branch_traces"] < state["branch_trace_limit"]:
                branch_trace = {
                    "thread_id": thread.GetThreadID(),
                    "watch_addr": watch_addr,
                    "pair_at_branch": pair_now,
                    "rflags_after_ucomiss": flags,
                    "initial_stack": sample["stack"],
                }
                branch_trace["branch_step"] = _step_once(thread)
                if branch_trace["branch_step"].get("after") == GUARD_SKIP_TARGET:
                    state["counts"]["guard_branch_to_skip"] += 1
                else:
                    state["counts"]["guard_branch_not_to_skip"] += 1
                state["counts"]["guard_branch_traces"] += 1
                sample["branch_trace"] = branch_trace
                sample["pc_after_branch_trace"] = _pc_va(thread)
                _append_limited("guard_branch_traces", branch_trace)
                if state["counts"]["guard_branch_traces"] >= state["branch_trace_limit"]:
                    _disable_watchpoints_after_branch_limit(debugger)
        _append_limited("guard_samples", sample)
    _append_limited("watchpoint_samples", sample)
    state["counts"]["watchpoint_hits"] += 1
    if (
        state["counts"]["watchpoint_hits"] >= state["watch_hit_cap"]
        and not state["counts"]["watchpoints_disabled_after_branch_trace_limit"]
    ):
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
    print("L16_PREFUSION_SENTINEL_SCORE_GUARD_JSON", path)
