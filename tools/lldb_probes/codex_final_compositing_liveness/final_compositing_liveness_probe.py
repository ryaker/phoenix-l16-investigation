import builtins
import json
import struct


SITES = {
    0x3BF8BC: "collector_insert_call_edge",
    0x3BFC40: "insert_entry",
    0x3BFE60: "drain_entry",
    0x3BCC51: "orchestrator_drain_call_edge",
    0x3BCCC0: "post_gather_filter_loop",
}


def reset(label="", sample_cap_per_site=12):
    builtins.l16_codex_final_compositing_liveness = {
        "label": label,
        "sample_cap_per_site": sample_cap_per_site,
        "breakpoint_ids": {},
        "breakpoint_vas": {},
        "counts": {f"0x{va:x}": 0 for va in SITES},
        "events": [],
        "errors": [],
        "disabled_after_cap": [],
        "drive_steps": 0,
        "drive_hit_step_cap": False,
    }


def _state():
    if not hasattr(builtins, "l16_codex_final_compositing_liveness"):
        reset()
    return builtins.l16_codex_final_compositing_liveness


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


def _stack(thread, max_frames=10):
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


def _container(process, addr):
    if not addr:
        return None
    prev_ptr = _u64(process, addr)
    next_ptr = _u64(process, addr + 0x8)
    count = _u64(process, addr + 0x10)
    return {
        "addr": addr,
        "ptr_0x00": prev_ptr,
        "ptr_0x08": next_ptr,
        "count_u64_0x10": count,
        "stop_u8_0x18": _u8(process, addr + 0x18),
        "mutex_addr_0x20": addr + 0x20,
        "condvar_addr_0x60": addr + 0x60,
        "ptr_0x00_is_sentinel": prev_ptr == addr if prev_ptr is not None else None,
        "ptr_0x08_is_sentinel": next_ptr == addr if next_ptr is not None else None,
    }


def _record(process, addr):
    if not addr:
        return None
    return {
        "addr": addr,
        "field_i32_0x00": _i32(process, addr),
        "field_i32_0x04": _i32(process, addr + 0x4),
        "field_i32_0x14": _i32(process, addr + 0x14),
        "field_i32_0x20": _i32(process, addr + 0x20),
        "field_i32_0x24": _i32(process, addr + 0x24),
        "field_i32_0x28": _i32(process, addr + 0x28),
        "field_u64_0x08": _u64(process, addr + 0x8),
        "field_u64_0x10": _u64(process, addr + 0x10),
        "field_u64_0x30": _u64(process, addr + 0x30),
        "field_u64_0x38": _u64(process, addr + 0x38),
        "field_u64_0x60": _u64(process, addr + 0x60),
        "field_u64_0x68": _u64(process, addr + 0x68),
    }


def _node(process, addr):
    if not addr:
        return None
    return {
        "addr": addr,
        "prev_ptr_0x00": _u64(process, addr),
        "next_ptr_0x08": _u64(process, addr + 0x8),
        "payload_0x10": _record(process, addr + 0x10),
    }


def _vector(process, addr):
    if not addr:
        return None
    begin = _u64(process, addr)
    end = _u64(process, addr + 0x8)
    cap = _u64(process, addr + 0x10)
    byte_len = end - begin if begin is not None and end is not None and end >= begin else None
    byte_cap = cap - begin if begin is not None and cap is not None and cap >= begin else None
    return {
        "addr": addr,
        "begin": begin,
        "end": end,
        "cap": cap,
        "byte_len": byte_len,
        "byte_cap": byte_cap,
        "count_0x70": byte_len // 0x70
        if byte_len is not None and byte_len % 0x70 == 0
        else None,
        "first_record": _record(process, begin) if begin and byte_len and byte_len >= 0x70 else None,
    }


def _libcp_target(target, pointer):
    va = _module_va(target, pointer) if pointer else None
    return f"0x{va:x}" if va is not None else None


def _packet(frame, process, site_va):
    target = process.GetTarget()
    regs = _registers(frame)
    packet = {
        "site_va": f"0x{site_va:x}",
        "site_name": SITES[site_va],
        "registers": regs,
    }

    if site_va in (0x3BF8BC, 0x3BFC40):
        packet["rdi_container"] = _container(process, regs["rdi"])
        packet["rsi_record"] = _record(process, regs["rsi"])
    elif site_va == 0x3BFE60:
        packet["rdi_container"] = _container(process, regs["rdi"])
        packet["rsi_vector"] = _vector(process, regs["rsi"])
    elif site_va == 0x3BCC51:
        packet["r14_container"] = _container(process, regs["r14"])
        packet["rbx_vector"] = _vector(process, regs["rbx"])
        packet["stack_vector_rbp_minus_0x440"] = _vector(process, regs["rbp"] - 0x440)
    elif site_va == 0x3BCCC0:
        record_addr = regs["r13"] + regs["rbx"]
        packet["loop_record_r13_plus_rbx"] = _record(process, record_addr)
        packet["next_record_plus_0x70"] = _record(process, record_addr + 0x70)
        packet["gather_vector_rbp_minus_0x440"] = _vector(process, regs["rbp"] - 0x440)
        packet["filtered_vector_rbp_minus_0x3e0"] = _vector(process, regs["rbp"] - 0x3E0)
    return packet


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
            state["breakpoint_vas"][str(new_ids[-1])] = f"0x{va:x}"
    for bp in target.breakpoint_iter():
        for loc in bp:
            loc_va = _module_va(target, loc.GetAddress().GetLoadAddress(target))
            if loc_va in SITES:
                state["breakpoint_ids"][f"0x{loc_va:x}"] = bp.GetID()
                state["breakpoint_vas"][str(bp.GetID())] = f"0x{loc_va:x}"
    print("L16_CODEX_FINAL_COMPOSITING_BPS", json.dumps(state["breakpoint_ids"], sort_keys=True))


def _site_for_thread(thread):
    target = thread.GetProcess().GetTarget()
    pc = thread.GetFrameAtIndex(0).GetPC()
    va = _module_va(target, pc)
    return va, SITES.get(va, f"unknown_0x{va:x}" if va is not None else "unknown")


def _record_stop(thread):
    state = _state()
    process = thread.GetProcess()
    target = process.GetTarget()
    frame = thread.GetFrameAtIndex(0)
    site_va, site_name = _site_for_thread(thread)
    if site_va not in SITES:
        state["errors"].append(f"unexpected stop at {site_name}")
        return

    key = f"0x{site_va:x}"
    state["counts"][key] += 1
    if state["counts"][key] <= state["sample_cap_per_site"]:
        try:
            packet = _packet(frame, process, site_va)
        except Exception as exc:
            packet = {"error": repr(exc)}
            state["errors"].append(f"packet error at {key}: {exc!r}")
        state["events"].append(
            {
                "sequence": len(state["events"]) + 1,
                "thread_id": thread.GetThreadID(),
                "site_name": site_name,
                "site_va": site_va,
                "packet": packet,
                "stack": _stack(thread),
            }
        )
    if state["counts"][key] >= state["sample_cap_per_site"]:
        bp_id = state["breakpoint_ids"].get(key)
        if bp_id is not None:
            bp = target.FindBreakpointByID(bp_id)
            if bp.IsValid() and bp.IsEnabled():
                bp.SetEnabled(False)
                state["disabled_after_cap"].append(key)


def drive_until_exit_or_step_cap(debugger, step_cap=120000):
    lldb = builtins.__import__("lldb")
    state = _state()
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
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
    for va_hex, bp_id in state["breakpoint_ids"].items():
        bp = target.FindBreakpointByID(bp_id)
        if bp.IsValid():
            state["breakpoint_hit_counts"][va_hex] = bp.GetHitCount()
    print("L16_CODEX_FINAL_COMPOSITING_DRIVE_STEPS", steps)


def write_report(debugger, path):
    state = _state()
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_CODEX_FINAL_COMPOSITING_REPORT", path)
