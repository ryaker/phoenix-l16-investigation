import builtins
import json
import struct


SITES = {
    0x3BCE77: "case1_target",
    0x3BCE7E: "case1_mutex_lock_call",
    0x3BCE83: "case1_type_check",
    0x3BCE8E: "case1_load_record_plus_0x10",
    0x3BCE92: "case1_flag_write",
    0x3BCE95: "case1_after_flag_write",
    0x3BCE9C: "case1_cond_broadcast_call",
    0x3BCEA8: "case1_mutex_unlock_call",
    0x3BCEAD: "case1_return_jump",
    0x3BEA7B: "case1_type_mismatch_target",
    0x3BCEE3: "case3_target",
    0x3BCEEB: "case3_call_3b07c0",
    0x3BCEF0: "case3_type_check",
    0x3BCF16: "case3_call_4182a0",
    0x3BCF1B: "case3_return_jump",
    0x3BEACD: "case3_type_mismatch_target",
    0x4182A0: "helper_4182a0_entry",
    0x418380: "helper_call_41e170",
    0x41847D: "helper_call_292070",
    0x4184B0: "helper_call_419080",
    0x41850B: "helper_call_3b6070",
    0x418518: "helper_call_3b07c0",
    0x4186A3: "helper_color_space_branch",
    0x4188DF: "helper_41e180_setup",
    0x418908: "helper_call_41e180",
    0x418BFD: "helper_normal_return",
    0x418D38: "helper_unexpected_color_space_error",
    0x418E27: "helper_unexpected_compression_error",
}


def reset(label="", sample_cap_per_site=64):
    builtins.l16_codex_final_compositing_case1_case3_boundary = {
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
    if not hasattr(builtins, "l16_codex_final_compositing_case1_case3_boundary"):
        reset()
    return builtins.l16_codex_final_compositing_case1_case3_boundary


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


def _f32(process, addr):
    data = _read(process, addr, 4)
    return struct.unpack_from("<f", data, 0)[0] if data is not None else None


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
        "field_i32_0x50": _i32(process, addr + 0x50),
        "field_i32_0x54": _i32(process, addr + 0x54),
        "field_i32_0x60": _i32(process, addr + 0x60),
        "field_i32_0x64": _i32(process, addr + 0x64),
        "field_i32_0x68": _i32(process, addr + 0x68),
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


def _record_view(process, addr):
    if not addr:
        return None
    return {
        "addr": addr,
        "i32_0x00": _i32(process, addr),
        "i32_0x04": _i32(process, addr + 0x4),
        "i32_0x08": _i32(process, addr + 0x8),
        "i32_0x0c": _i32(process, addr + 0xC),
        "u64_0x00": _u64(process, addr),
        "u64_0x08": _u64(process, addr + 0x8),
        "f32_0x00": _f32(process, addr),
        "f32_0x04": _f32(process, addr + 0x4),
    }


def _owner(process, target, addr):
    if not addr:
        return None
    ptr_870 = _u64(process, addr + 0x870)
    return {
        "addr": addr,
        "u8_0x4a2": _u8(process, addr + 0x4A2),
        "u8_0x4a4": _u8(process, addr + 0x4A4),
        "u8_0x720": _u8(process, addr + 0x720),
        "u8_0x721": _u8(process, addr + 0x721),
        "u8_0x722": _u8(process, addr + 0x722),
        "u32_0x724": _u32(process, addr + 0x724),
        "f32_0x8b0": _f32(process, addr + 0x8B0),
        "ptr_0x4c0": _u64(process, addr + 0x4C0),
        "ptr_0x5a0": _u64(process, addr + 0x5A0),
        "ptr_0x5d0": _u64(process, addr + 0x5D0),
        "ptr_0x640": _u64(process, addr + 0x640),
        "ptr_0x6a8": _u64(process, addr + 0x6A8),
        "ptr_0x780": _u64(process, addr + 0x780),
        "ptr_0x870": ptr_870,
        "ptr_0x870_first": _u64(process, ptr_870) if ptr_870 else None,
    }


def _case1_operands(process, frame):
    rbp = _u(frame, "rbp")
    record = _u(frame, "r13")
    flag_ptr = _u64(process, record + 0x10) if record else None
    return {
        "mutex_ptr_rbp_minus_0x800": _u64(process, rbp - 0x800),
        "cond_ptr_rbp_minus_0x820": _u64(process, rbp - 0x820),
        "record_plus_0x10_flag_ptr": flag_ptr,
        "flag_byte_at_record_plus_0x10_ptr": _u8(process, flag_ptr) if flag_ptr else None,
    }


def _case3_call_operands(process, frame):
    regs = _registers(frame)
    r13 = regs["r13"]
    return {
        "call_rdi_context": regs["rdi"],
        "expected_rdi_rbp_minus_0x7f0": _u64(process, regs["rbp"] - 0x7F0),
        "call_rsi_record_plus_0x10": regs["rsi"],
        "call_rdx_record_plus_0x60": regs["rdx"],
        "call_rcx_record_plus_0x50": regs["rcx"],
        "call_r8d_record_plus_0x68": regs["r8"] & 0xFFFFFFFF,
        "call_r9_record_plus_0x20": regs["r9"],
        "matches_record_plus_0x10": regs["rsi"] == r13 + 0x10,
        "matches_record_plus_0x60": regs["rdx"] == r13 + 0x60,
        "matches_record_plus_0x50": regs["rcx"] == r13 + 0x50,
        "matches_record_plus_0x20": regs["r9"] == r13 + 0x20,
        "record_plus_0x10_view": _record_view(process, r13 + 0x10),
        "record_plus_0x20_view": _record_view(process, r13 + 0x20),
        "record_plus_0x50_view": _record_view(process, r13 + 0x50),
        "record_plus_0x60_view": _record_view(process, r13 + 0x60),
    }


def _helper_entry_operands(process, target, frame):
    regs = _registers(frame)
    return {
        "owner_rdi": _owner(process, target, regs["rdi"]),
        "arg_rsi_view": _record_view(process, regs["rsi"]),
        "arg_rdx_view": _record_view(process, regs["rdx"]),
        "arg_rcx_view": _record_view(process, regs["rcx"]),
        "arg_r8d": regs["r8"] & 0xFFFFFFFF,
        "arg_r9_view": _record_view(process, regs["r9"]),
    }


def _helper_locals(process, frame):
    rbp = _u(frame, "rbp")
    return {
        "local_i32_rbp_minus_0x320": _i32(process, rbp - 0x320),
        "local_i32_rbp_minus_0x31c": _i32(process, rbp - 0x31C),
        "local_i32_rbp_minus_0x3b8": _i32(process, rbp - 0x3B8),
        "local_i32_rbp_minus_0x3b4": _i32(process, rbp - 0x3B4),
        "local_i32_rbp_minus_0x3c8": _i32(process, rbp - 0x3C8),
        "local_i32_rbp_minus_0x3c4": _i32(process, rbp - 0x3C4),
        "local_i32_rbp_minus_0x3c0": _i32(process, rbp - 0x3C0),
        "local_i32_rbp_minus_0x3bc": _i32(process, rbp - 0x3BC),
        "local_u64_rbp_minus_0x3e0": _u64(process, rbp - 0x3E0),
        "local_u64_rbp_minus_0x3d8": _u64(process, rbp - 0x3D8),
        "local_u64_rbp_minus_0x4f0": _u64(process, rbp - 0x4F0),
        "local_u64_rbp_minus_0x4ec": _u64(process, rbp - 0x4EC),
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

    if 0x3BCE77 <= site_va <= 0x3BEACD:
        packet["owner_r15"] = _owner(process, target, regs["r15"])
        packet["record_r13"] = _record(process, regs["r13"])
    if 0x3BCE77 <= site_va <= 0x3BCEAD:
        packet["case1_operands"] = _case1_operands(process, frame)
    if site_va == 0x3BCF16:
        packet["case3_call_operands"] = _case3_call_operands(process, frame)
    if site_va == 0x4182A0:
        packet["helper_entry_operands"] = _helper_entry_operands(process, target, frame)
    if 0x4182A0 <= site_va <= 0x418E27:
        if site_va != 0x4182A0:
            packet["helper_owner_r15"] = _owner(process, target, regs["r15"])
        packet["helper_locals"] = _helper_locals(process, frame)
    if site_va in (0x418380, 0x4184B0, 0x41850B, 0x418518, 0x4188DF, 0x418908):
        packet["call_args"] = {
            "rdi": regs["rdi"],
            "rsi": regs["rsi"],
            "rdx": regs["rdx"],
            "rcx": regs["rcx"],
            "r8": regs["r8"],
            "r9": regs["r9"],
        }
    if site_va == 0x4186A3:
        packet["color_space_selector_eax"] = regs["rax"] & 0xFFFFFFFF
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
    print("L16_CODEX_FINAL_CASE1_CASE3_BPS", json.dumps(state["breakpoint_ids"], sort_keys=True))


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
    print("L16_CODEX_FINAL_CASE1_CASE3_DRIVE_STEPS", steps)


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(_state(), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_CODEX_FINAL_CASE1_CASE3_REPORT", path)
