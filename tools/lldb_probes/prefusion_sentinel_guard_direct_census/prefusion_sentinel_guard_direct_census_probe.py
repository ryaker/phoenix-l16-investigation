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


def reset(label="", sample_limit=256, guard_total_cap=250000, step_cap=800000):
    builtins.l16_prefusion_sentinel_guard_direct_census = {
        "label": label,
        "sample_limit": sample_limit,
        "guard_total_cap": guard_total_cap,
        "step_cap": step_cap,
        "breakpoint_ids": {},
        "pending_by_thread": {},
        "sentinel_addrs": {},
        "counts": {
            "store_y_hits": 0,
            "after_store_hits": 0,
            "after_store_without_pending": 0,
            "after_store_pair_is_sentinel": 0,
            "unique_sentinel_addrs": 0,
            "guard_hits": 0,
            "guard_known_sentinel_addr_hits": 0,
            "guard_known_sentinel_pair_hits": 0,
            "guard_known_sentinel_skip_by_flags": 0,
            "guard_known_sentinel_not_skip_by_flags": 0,
            "guard_breakpoint_disabled_after_total_cap": 0,
        },
        "store_y_samples": [],
        "after_store_samples": [],
        "guard_known_sentinel_samples": [],
        "guard_unknown_sentinel_samples": [],
        "errors": [],
        "drive_steps": 0,
        "drive_hit_step_cap": False,
    }


def _state():
    if not hasattr(builtins, "l16_prefusion_sentinel_guard_direct_census"):
        reset()
    return builtins.l16_prefusion_sentinel_guard_direct_census


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


def _disable_guard_breakpoint(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    bp_id = state["breakpoint_ids"].get("guard_after_compare_218bc4")
    if not bp_id:
        return
    bp = target.FindBreakpointByID(int(bp_id))
    if bp and bp.IsValid():
        bp.SetEnabled(False)
    state["counts"]["guard_breakpoint_disabled_after_total_cap"] = 1


def install_breakpoints(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    for site, name in (
        (STORE_Y, "store_y_21b92a"),
        (AFTER_STORE_Y, "after_store_y_21b930"),
        (GUARD_AFTER_COMPARE, "guard_after_compare_218bc4"),
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
        bp.SetScriptCallbackFunction("prefusion_sentinel_guard_direct_census_probe.hit")
        state["breakpoint_ids"][name] = bp.GetID()
    print("L16_PREFUSION_SENTINEL_GUARD_DIRECT_CENSUS_INSTALLED", json.dumps(state["breakpoint_ids"], sort_keys=True))


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
        state["sentinel_addrs"][str(pair_addr)] = {
            "addr": pair_addr,
            "first_seen_index": state["counts"]["after_store_pair_is_sentinel"],
            "pair_at_collection": pair_after,
        }
        state["counts"]["unique_sentinel_addrs"] = len(state["sentinel_addrs"])
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


def _guard_after_compare(frame, regs):
    state = _state()
    process = frame.GetThread().GetProcess()
    operand_addr = regs["rdx"] + regs["rbx"] * 8
    known = str(operand_addr) in state["sentinel_addrs"]
    if known:
        state["counts"]["guard_known_sentinel_addr_hits"] += 1
    pair = _pair(process, operand_addr)
    flags = _rflags(frame)
    packet = {
        "thread_id": frame.GetThread().GetThreadID(),
        "pc_va": GUARD_AFTER_COMPARE,
        "operand_addr": operand_addr,
        "known_sentinel_addr": known,
        "operand_pair": pair,
        "rflags_after_ucomiss": flags,
        "static_branch": {
            "instruction_va": GUARD_AFTER_COMPARE,
            "instruction": "jae 0x218cb8",
            "skip_target_va": GUARD_SKIP_TARGET,
        },
        "registers": regs,
        "stack": _stack(frame.GetThread(), 18),
    }
    if known and pair.get("is_sentinel_neg1_neg1"):
        state["counts"]["guard_known_sentinel_pair_hits"] += 1
        if flags.get("jae_taken"):
            state["counts"]["guard_known_sentinel_skip_by_flags"] += 1
        else:
            state["counts"]["guard_known_sentinel_not_skip_by_flags"] += 1
        _append_limited("guard_known_sentinel_samples", packet)
    elif pair.get("is_sentinel_neg1_neg1"):
        _append_limited("guard_unknown_sentinel_samples", packet)
    if state["counts"]["guard_hits"] >= state["guard_total_cap"]:
        _disable_guard_breakpoint(process.GetTarget().GetDebugger())


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
    elif pc_va == GUARD_AFTER_COMPARE:
        state["counts"]["guard_hits"] += 1
        _guard_after_compare(frame, regs)
    else:
        state["errors"].append({"error": "unexpected breakpoint", "pc_va": pc_va})
    return False


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
        process.Continue()
    state["drive_steps"] = steps
    if process and process.IsValid():
        state["process_state"] = int(process.GetState())
        state["process_exit_status"] = process.GetExitStatus()


def payload(debugger):
    state = dict(_state())
    process = debugger.GetSelectedTarget().GetProcess()
    if process and process.IsValid():
        state["process_state"] = int(process.GetState())
        state["process_exit_status"] = process.GetExitStatus()
    return state


def report_to_file(debugger, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload(debugger), fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("L16_PREFUSION_SENTINEL_GUARD_DIRECT_CENSUS_JSON", path)
