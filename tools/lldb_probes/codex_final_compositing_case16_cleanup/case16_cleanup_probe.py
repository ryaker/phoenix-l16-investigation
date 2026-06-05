import builtins
import json
import struct


SITES = {
    0x3BD2F7: "case16_target",
    0x3BD2FE: "case16_helper_call",
    0x3BD303: "case16_helper_return",
    0x3ADAD0: "helper_entry",
    0x3ADAFB: "helper_populate_call",
    0x3ADB00: "helper_after_populate_read_0x180",
    0x3ADB0B: "helper_object_null_branch",
    0x3ADB16: "helper_local_count_branch",
    0x3ADB6E: "helper_callback_call",
    0x3ADB9B: "helper_release_shared_0x40",
    0x3ADBAA: "helper_release_shared_0x30",
    0x3ADBB9: "helper_release_shared_0x08",
    0x3ADC3F: "helper_bad_function_throw",
    0x3ADC74: "helper_cleanup_path",
    0x3ADC78: "helper_cleanup_call",
    0x3ADCC3: "helper_delete_local_base",
    0x3ADCDF: "helper_return",
}


def reset(label="", sample_cap_per_site=64):
    builtins.l16_codex_final_compositing_case16_cleanup = {
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
    if not hasattr(builtins, "l16_codex_final_compositing_case16_cleanup"):
        reset()
    return builtins.l16_codex_final_compositing_case16_cleanup


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


def _i32(process, addr):
    data = _read(process, addr, 4)
    return struct.unpack_from("<i", data, 0)[0] if data is not None else None


def _u32(process, addr):
    data = _read(process, addr, 4)
    return struct.unpack_from("<I", data, 0)[0] if data is not None else None


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
    resolved = target.ResolveLoadAddress(pc)
    module = resolved.GetModule()
    if module.IsValid() and str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
        base = _libcp_base(target)
        if base is not None and pc >= base:
            return pc - base
    return None


def _libcp_target(target, pointer):
    va = _module_va(target, pointer) if pointer else None
    return f"0x{va:x}" if va is not None else None


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
        "field_i32_0x28": _i32(process, addr + 0x28),
        "field_i32_0x30": _i32(process, addr + 0x30),
        "field_i32_0x34": _i32(process, addr + 0x34),
        "field_i32_0x38": _i32(process, addr + 0x38),
        "field_i32_0x3c": _i32(process, addr + 0x3C),
        "field_u64_0x08": _u64(process, addr + 0x8),
        "field_u64_0x10": _u64(process, addr + 0x10),
        "field_u64_0x20": _u64(process, addr + 0x20),
        "field_u64_0x28": _u64(process, addr + 0x28),
        "field_u64_0x30": _u64(process, addr + 0x30),
        "field_u64_0x38": _u64(process, addr + 0x38),
        "field_u64_0x40": _u64(process, addr + 0x40),
        "field_u64_0x50": _u64(process, addr + 0x50),
        "field_u64_0x60": _u64(process, addr + 0x60),
        "field_u64_0x68": _u64(process, addr + 0x68),
    }


def _owner(process, target, addr):
    if not addr:
        return None
    ctx_d0 = addr + 0xD0
    return {
        "addr": addr,
        "context_plus_0xd0": ctx_d0,
        "u8_0x4a2": _u8(process, addr + 0x4A2),
        "u8_0x4a4": _u8(process, addr + 0x4A4),
        "u8_0x721": _u8(process, addr + 0x721),
        "u8_0x722": _u8(process, addr + 0x722),
        "u32_0x724": _u32(process, addr + 0x724),
        "ptr_0x0d0": _u64(process, addr + 0xD0),
        "ptr_0x180_from_context_d0": _u64(process, ctx_d0 + 0x180),
        "ptr_0x5d0": _u64(process, addr + 0x5D0),
        "ptr_0x5a0": _u64(process, addr + 0x5A0),
        "ptr_0x640": _u64(process, addr + 0x640),
    }


def _context(process, target, addr):
    if not addr:
        return None
    ptr_180 = _u64(process, addr + 0x180)
    vtable = _u64(process, ptr_180)
    slot_30 = _u64(process, vtable + 0x30) if vtable else None
    return {
        "addr": addr,
        "ptr_0x180": ptr_180,
        "ptr_0x180_vtable": vtable,
        "ptr_0x180_slot_0x30": slot_30,
        "ptr_0x180_slot_0x30_libcp_va": _libcp_target(target, slot_30),
        "raw_u64_0x000": _u64(process, addr),
        "raw_u64_0x008": _u64(process, addr + 0x8),
        "raw_u64_0x020": _u64(process, addr + 0x20),
        "raw_u64_0x030": _u64(process, addr + 0x30),
        "raw_u64_0x038": _u64(process, addr + 0x38),
        "raw_u64_0x180": ptr_180,
    }


def _helper_locals(process, rbp):
    if not rbp:
        return None
    q_60 = _u64(process, rbp - 0x60)
    q_58 = _u64(process, rbp - 0x58)
    q_50 = _u64(process, rbp - 0x50)
    q_48 = _u64(process, rbp - 0x48)
    q_40 = _u64(process, rbp - 0x40)
    q_38 = _u64(process, rbp - 0x38)
    ptr_array_bytes = q_50 - q_58 if q_58 is not None and q_50 is not None and q_50 >= q_58 else None
    return {
        "rbp_minus_0x60": q_60,
        "rbp_minus_0x58": q_58,
        "rbp_minus_0x50": q_50,
        "rbp_minus_0x48": q_48,
        "rbp_minus_0x40": q_40,
        "rbp_minus_0x38": q_38,
        "ptr_array_byte_len_0x50_minus_0x58": ptr_array_bytes,
        "ptr_array_count_8": ptr_array_bytes // 8
        if ptr_array_bytes is not None and ptr_array_bytes % 8 == 0
        else None,
        "first_pointed_record": _record(process, _u64(process, q_58)) if q_58 else None,
    }


def _case16_local(process, frame):
    regs = _registers(frame)
    rbp = regs["rbp"]
    local_context = _u64(process, rbp - 0x840)
    return {
        "rbp_minus_0x840_u64": local_context,
        "owner_plus_0xd0": regs["r15"] + 0xD0 if regs["r15"] else None,
        "matches_owner_plus_0xd0": local_context == regs["r15"] + 0xD0
        if local_context is not None and regs["r15"]
        else None,
    }


def _stack(thread, max_frames=12):
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


def _site_for_thread(thread):
    target = thread.GetProcess().GetTarget()
    pc = thread.GetFrameAtIndex(0).GetPC()
    va = _module_va(target, pc)
    return va, SITES.get(va, f"unknown_0x{va:x}" if va is not None else "unknown")


def _packet(frame, process, site_va):
    target = process.GetTarget()
    regs = _registers(frame)
    packet = {
        "site_va": f"0x{site_va:x}",
        "site_name": SITES[site_va],
        "registers": regs,
    }

    if site_va in (0x3BD2F7, 0x3BD2FE, 0x3BD303):
        packet["case16_owner_r15"] = _owner(process, target, regs["r15"])
        packet["case16_record_r13"] = _record(process, regs["r13"])
        packet["case16_local_context"] = _case16_local(process, frame)
        packet["context_from_local"] = _context(process, target, _u64(process, regs["rbp"] - 0x840))
        if site_va == 0x3BD2FE:
            packet["helper_arg_rdi_context"] = _context(process, target, regs["rdi"])
        if site_va == 0x3BD303:
            packet["helper_return_rax"] = regs["rax"]
    else:
        packet["helper_context_r12"] = _context(process, target, regs["r12"])
        packet["helper_locals"] = _helper_locals(process, regs["rbp"])
        if site_va == 0x3ADAD0:
            packet["helper_arg_rdi_context"] = _context(process, target, regs["rdi"])
        elif site_va == 0x3ADAFB:
            packet["populate_arg_rdi_context"] = _context(process, target, regs["rdi"])
            packet["populate_arg_rsi_local_vector"] = regs["rsi"]
        elif site_va in (0x3ADB00, 0x3ADB0B):
            packet["context_ptr_0x180_from_r12"] = _u64(process, regs["r12"] + 0x180)
            packet["current_rdi"] = regs["rdi"]
        elif site_va == 0x3ADB16:
            packet["local_count_qword_rbp_minus_0x38"] = _u64(process, regs["rbp"] - 0x38)
        elif site_va == 0x3ADB6E:
            packet["callback_object_rdi"] = regs["rdi"]
            packet["callback_arg_rsi"] = regs["rsi"]
            packet["callback_arg_i32"] = _i32(process, regs["rsi"])
            packet["callback_arg_rdx"] = regs["rdx"]
            packet["callback_arg_rdx_record_tail_i32"] = _i32(process, regs["rdx"])
            packet["callback_target_rax"] = regs["rax"]
            packet["callback_target_rax_libcp_va"] = _libcp_target(target, regs["rax"])
        elif site_va in (0x3ADB9B, 0x3ADBAA, 0x3ADBB9):
            packet["release_shared_arg_rdi"] = regs["rdi"]
        elif site_va == 0x3ADC3F:
            packet["bad_function_throw_rdi"] = regs["rdi"]
        elif site_va == 0x3ADC78:
            packet["cleanup_call_arg_rdi"] = regs["rdi"]
        elif site_va == 0x3ADCDF:
            packet["return_rax"] = regs["rax"]
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
    print("L16_CODEX_FINAL_CASE16_CLEANUP_BPS", json.dumps(state["breakpoint_ids"], sort_keys=True))


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
    print("L16_CODEX_FINAL_CASE16_CLEANUP_DRIVE_STEPS", steps)


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(_state(), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_CODEX_FINAL_CASE16_CLEANUP_REPORT", path)
