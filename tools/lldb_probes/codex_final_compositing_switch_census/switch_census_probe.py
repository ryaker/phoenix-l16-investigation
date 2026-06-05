import builtins
import json
import struct


SWITCH_SITE = 0x3BCE59
ORCHESTRATOR_DRAIN_CALL = 0x3BCC51
INVALID_CASE_SITE = 0x3BE8E7

CASE_TARGETS = {
    0: 0x3BE5CE,
    1: 0x3BCE77,
    2: 0x3BD308,
    3: 0x3BCEE3,
    4: 0x3BCF20,
    5: 0x3BD1C1,
    6: 0x3BD327,
    7: 0x3BD24F,
    8: 0x3BD27B,
    9: 0x3BD334,
    10: 0x3BCEB2,
    11: 0x3BD453,
    12: 0x3BD360,
    13: 0x3BD482,
    14: 0x3BE60E,
    15: 0x3BE8A6,
    16: 0x3BD2F7,
}

SITES = {
    ORCHESTRATOR_DRAIN_CALL: "orchestrator_drain_call_edge",
    SWITCH_SITE: "switch_record_type_load",
    INVALID_CASE_SITE: "switch_invalid_gt_16_target",
    **{va: f"case_{case}_target" for case, va in CASE_TARGETS.items()},
}

TARGET_TO_CASE = {va: case for case, va in CASE_TARGETS.items()}


def reset(label="", sample_limit=512):
    builtins.l16_codex_final_compositing_switch_census = {
        "label": label,
        "sample_limit": sample_limit,
        "breakpoint_ids": {},
        "counts": {f"0x{va:x}": 0 for va in SITES},
        "switch_type_counts": {},
        "case_target_counts": {},
        "case_type_mismatches": [],
        "events": [],
        "errors": [],
        "drive_steps": 0,
        "drive_hit_step_cap": False,
    }


def _state():
    if not hasattr(builtins, "l16_codex_final_compositing_switch_census"):
        reset()
    return builtins.l16_codex_final_compositing_switch_census


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


def _libcp_base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                return base
    return None


def _module_va(target, pc):
    base = _libcp_base(target)
    if base is not None and pc >= base:
        return pc - base
    return None


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _registers(frame):
    return {
        name: _u(frame, name)
        for name in (
            "rax",
            "rbx",
            "rcx",
            "rdx",
            "rdi",
            "rsi",
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
        )
    }


def _record(process, addr):
    if not addr:
        return None
    return {
        "addr": addr,
        "field_i32_0x00": _i32(process, addr),
        "field_i32_0x04": _i32(process, addr + 0x4),
        "field_i32_0x10": _i32(process, addr + 0x10),
        "field_i32_0x14": _i32(process, addr + 0x14),
        "field_i32_0x20": _i32(process, addr + 0x20),
        "field_i32_0x24": _i32(process, addr + 0x24),
        "field_i32_0x30": _i32(process, addr + 0x30),
        "field_i32_0x34": _i32(process, addr + 0x34),
        "field_i32_0x38": _i32(process, addr + 0x38),
        "field_i32_0x3c": _i32(process, addr + 0x3C),
        "field_u64_0x08": _u64(process, addr + 0x8),
        "field_u64_0x10": _u64(process, addr + 0x10),
        "field_u64_0x20": _u64(process, addr + 0x20),
        "field_u64_0x30": _u64(process, addr + 0x30),
        "field_u64_0x40": _u64(process, addr + 0x40),
        "field_u64_0x50": _u64(process, addr + 0x50),
        "field_u64_0x60": _u64(process, addr + 0x60),
    }


def _vector(process, addr):
    if not addr:
        return None
    begin = _u64(process, addr)
    end = _u64(process, addr + 0x8)
    cap = _u64(process, addr + 0x10)
    byte_len = end - begin if begin is not None and end is not None and end >= begin else None
    return {
        "addr": addr,
        "begin": begin,
        "end": end,
        "cap": cap,
        "byte_len": byte_len,
        "count_0x70": byte_len // 0x70
        if byte_len is not None and byte_len % 0x70 == 0
        else None,
    }


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


def install_breakpoints(debugger):
    lldb = builtins.__import__("lldb")
    state = _state()
    target = debugger.GetSelectedTarget()
    interpreter = debugger.GetCommandInterpreter()
    for va in SITES:
        before_ids = {bp.GetID() for bp in target.breakpoint_iter()}
        result = lldb.SBCommandReturnObject()
        interpreter.HandleCommand(
            f"breakpoint set --shlib libcp.dylib --address 0x{va:x}", result
        )
        if not result.Succeeded():
            state["errors"].append(result.GetError() or result.GetOutput())
            continue
        after_ids = {bp.GetID() for bp in target.breakpoint_iter()}
        new_ids = sorted(after_ids - before_ids)
        if new_ids:
            state["breakpoint_ids"][f"0x{va:x}"] = new_ids[-1]
    print("L16_CODEX_FINAL_SWITCH_BPS", json.dumps(state["breakpoint_ids"], sort_keys=True))


def _increment(mapping, key):
    mapping[str(key)] = mapping.get(str(key), 0) + 1


def _packet(frame, process, site_va):
    regs = _registers(frame)
    record = _record(process, regs["r13"])
    packet = {
        "site_va": f"0x{site_va:x}",
        "site_name": SITES[site_va],
        "registers": regs,
        "current_record_r13": record,
    }
    if site_va == ORCHESTRATOR_DRAIN_CALL:
        packet["stack_vector_rbp_minus_0x440"] = _vector(process, regs["rbp"] - 0x440)
        packet["r14_container_count_u64_0x10"] = _u64(process, regs["r14"] + 0x10)
    elif site_va in (SWITCH_SITE, *TARGET_TO_CASE.keys(), INVALID_CASE_SITE):
        packet["gather_vector_rbp_minus_0x440"] = _vector(process, regs["rbp"] - 0x440)
        packet["filtered_vector_rbp_minus_0x3e0"] = _vector(process, regs["rbp"] - 0x3E0)
        packet["case_index_for_target"] = TARGET_TO_CASE.get(site_va)
    return packet


def _record_stop(thread):
    state = _state()
    process = thread.GetProcess()
    target = process.GetTarget()
    frame = thread.GetFrameAtIndex(0)
    site_va = _module_va(target, frame.GetPC())
    if site_va not in SITES:
        state["errors"].append(f"unexpected stop at {site_va and hex(site_va)}")
        return

    key = f"0x{site_va:x}"
    state["counts"][key] += 1
    try:
        packet = _packet(frame, process, site_va)
    except Exception as exc:
        packet = {"error": repr(exc)}
        state["errors"].append(f"packet error at {key}: {exc!r}")

    rec = packet.get("current_record_r13") or {}
    rec_type = rec.get("field_i32_0x00")
    if site_va == SWITCH_SITE:
        _increment(state["switch_type_counts"], rec_type)
    if site_va in TARGET_TO_CASE:
        case_index = TARGET_TO_CASE[site_va]
        _increment(state["case_target_counts"], case_index)
        if rec_type != case_index:
            state["case_type_mismatches"].append(
                {
                    "site_va": key,
                    "case_index": case_index,
                    "record_type": rec_type,
                    "sequence": len(state["events"]) + 1,
                }
            )
    if site_va == INVALID_CASE_SITE:
        _increment(state["case_target_counts"], "invalid_gt_16")

    if len(state["events"]) < state["sample_limit"]:
        state["events"].append(
            {
                "sequence": len(state["events"]) + 1,
                "thread_id": thread.GetThreadID(),
                "site_name": SITES[site_va],
                "site_va": site_va,
                "packet": packet,
                "stack": _stack(thread),
            }
        )


def drive_until_exit_or_step_cap(debugger, step_cap=120000):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process.IsValid() and process.GetState() != lldb.eStateExited and steps < step_cap:
        for thread in process:
            if thread.GetStopReason() == lldb.eStopReasonBreakpoint:
                _record_stop(thread)
        error = process.Continue()
        if not error.Success():
            state["errors"].append(error.GetCString() or "process.Continue failed")
            break
        steps += 1

    state["drive_steps"] = steps
    state["drive_hit_step_cap"] = steps >= step_cap
    state["process"] = {
        "valid": process.IsValid(),
        "state": lldb.SBDebugger.StateAsCString(process.GetState())
        if process.IsValid()
        else None,
        "exit_status": process.GetExitStatus() if process.IsValid() else None,
        "exit_description": process.GetExitDescription() if process.IsValid() else None,
    }
    state["breakpoint_hit_counts"] = {}
    target = debugger.GetSelectedTarget()
    for va_hex, bp_id in state["breakpoint_ids"].items():
        bp = target.FindBreakpointByID(bp_id)
        if bp.IsValid():
            state["breakpoint_hit_counts"][va_hex] = bp.GetHitCount()
    print("L16_CODEX_FINAL_SWITCH_DRIVE_STEPS", steps)


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(_state(), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_CODEX_FINAL_SWITCH_REPORT", path)
