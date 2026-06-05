import builtins
import json
import struct


SITES = {
    0x369320: "valid_target_369320",
    0x36931B: "sentinel_skip_36931b",
}


def reset(label="", sample_cap_per_site=12):
    builtins.l16_codex_iramp_sentinel_gate = {
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
    if not hasattr(builtins, "l16_codex_iramp_sentinel_gate"):
        reset()
    return builtins.l16_codex_iramp_sentinel_gate


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _u32(value):
    return value & 0xFFFFFFFF


def _i32_from_u(value):
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def _read(process, addr, size):
    if not addr:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u64(process, addr):
    data = _read(process, addr, 8)
    return struct.unpack_from("<Q", data, 0)[0] if data is not None else None


def _i32(process, addr):
    data = _read(process, addr, 4)
    return struct.unpack_from("<i", data, 0)[0] if data is not None else None


def _u32_mem(process, addr):
    data = _read(process, addr, 4)
    return struct.unpack_from("<I", data, 0)[0] if data is not None else None


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
        interpreter.HandleCommand(f"breakpoint set --shlib libcp.dylib --address 0x{va:x}", result)
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
    print("L16_CODEX_SENTINEL_GATE_BPS", json.dumps(state["breakpoint_ids"], sort_keys=True))


def _site_for_thread(thread):
    target = thread.GetProcess().GetTarget()
    pc = thread.GetFrameAtIndex(0).GetPC()
    va = _module_va(target, pc)
    return va, SITES.get(va, f"unknown_0x{va:x}" if va is not None else "unknown")


def _packet(frame, process, site_va):
    regs = {name: _u(frame, name) for name in ("rax", "rbx", "rcx", "rdx", "rsi", "rdi", "r8", "r9", "r12", "r13", "r14", "r15", "rbp", "rsp")}
    eax = _u32(regs["rax"])
    table_addr = regs["r12"] + regs["rsi"] * 8 if regs["r12"] else None
    table_low_u32 = _u32_mem(process, table_addr) if table_addr is not None else None
    table_high_i32 = _i32(process, table_addr + 4) if table_addr is not None else None
    partner_begin = _u64(process, regs["rbp"] - 0x1800)
    partner_end = _u64(process, regs["rbp"] - 0x17F8)
    partner_diff = partner_end - partner_begin if partner_begin is not None and partner_end is not None and partner_end >= partner_begin else None
    return {
        "site_va": f"0x{site_va:x}",
        "registers": regs,
        "eax_u32_hex": f"0x{eax:08x}",
        "eax_s32": _i32_from_u(eax),
        "eax_is_sentinel_0x80000000": eax == 0x80000000,
        "r12_table_base": regs["r12"],
        "rsi_linear_index": regs["rsi"],
        "table_addr_r12_plus_rsi_x8": table_addr,
        "table_low_u32_hex": f"0x{table_low_u32:08x}" if table_low_u32 is not None else None,
        "table_low_s32": _i32_from_u(table_low_u32) if table_low_u32 is not None else None,
        "table_high_s32": table_high_i32,
        "table_low_matches_eax": table_low_u32 == eax if table_low_u32 is not None else None,
        "rcx_contributor_index": regs["rcx"],
        "rdx_record_byte_offset": regs["rdx"],
        "record_ptr_rdi_plus_rdx": regs["rdi"] + regs["rdx"],
        "record_table_base_plus_0x30": _u64(process, regs["rdi"] + regs["rdx"] + 0x30),
        "partner_begin": partner_begin,
        "partner_end": partner_end,
        "partner_diff": partner_diff,
        "partner_count_0x280": partner_diff // 0x280 if partner_diff is not None and partner_diff % 0x280 == 0 else None,
    }


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
        state["events"].append(
            {
                "sequence": len(state["events"]) + 1,
                "thread_id": thread.GetThreadID(),
                "site_name": site_name,
                "site_va": site_va,
                "packet": _packet(frame, process, site_va),
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


def drive_until_exit_or_step_cap(debugger, step_cap=80000):
    lldb = builtins.__import__("lldb")
    state = _state()
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    interpreter = debugger.GetCommandInterpreter()
    result = lldb.SBCommandReturnObject()
    steps = 0

    while process.IsValid() and process.GetState() != lldb.eStateExited and steps < step_cap:
        stopped = False
        for thread in process:
            if thread.GetStopReason() == lldb.eStopReasonBreakpoint:
                stopped = True
                _record_stop(thread)
        interpreter.HandleCommand("process continue", result)
        if not result.Succeeded():
            state["errors"].append(result.GetError() or result.GetOutput())
            break
        steps += 1
        if not stopped and process.GetState() != lldb.eStateStopped:
            continue

    state["drive_steps"] = steps
    state["drive_hit_step_cap"] = steps >= step_cap
    state["process"] = {
        "state": str(process.GetState()) if process.IsValid() else None,
        "exit_status": process.GetExitStatus() if process.IsValid() else None,
        "exit_description": process.GetExitDescription() if process.IsValid() else None,
    }
    state["breakpoint_hit_counts"] = {}
    for va_hex, bp_id in state["breakpoint_ids"].items():
        bp = target.FindBreakpointByID(bp_id)
        if bp.IsValid():
            state["breakpoint_hit_counts"][va_hex] = bp.GetHitCount()


def write_report(debugger, path):
    state = _state()
    with open(path, "w") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
        fh.write("\n")
    print("L16_CODEX_SENTINEL_GATE_REPORT", path)
