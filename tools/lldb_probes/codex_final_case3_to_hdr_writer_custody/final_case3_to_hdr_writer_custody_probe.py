import builtins
import json
import struct


SITES = {
    0x3BCF16: "case3_call_4182a0",
    0x4182A0: "helper_4182a0_entry",
    0x418908: "helper_call_41e180",
    0x418BFD: "helper_4182a0_normal_return",
    0x418D38: "helper_4182a0_unexpected_color_space_error",
    0x418E27: "helper_4182a0_unexpected_compression_error",
    0x41E180: "helper_41e180_entry",
    0x41E599: "helper_call_2326a0_hdr_writer",
    0x41E953: "helper_41e180_ppm_branch_target",
    0x41E9EA: "helper_41e180_ppm_writer_call",
    0x41F9EB: "helper_41e180_normal_return",
    0x41FA93: "helper_41e180_unexpected_export_format",
    0x41FAD4: "helper_41e180_invalid_export_size",
    0x2326A0: "writer_2326a0_entry",
    0x232731: "writer_virtual_write_call",
    0x232733: "writer_after_virtual_write",
    0x232758: "writer_no_data_error",
}


def reset(label="", sample_cap_per_site=64):
    builtins.l16_codex_final_case3_to_hdr_writer_custody = {
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
    if not hasattr(builtins, "l16_codex_final_case3_to_hdr_writer_custody"):
        reset()
    return builtins.l16_codex_final_case3_to_hdr_writer_custody


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


def _std_string(process, addr):
    data = _read(process, addr, 24)
    if data is None:
        return None
    first = data[0]
    if first & 1:
        length = struct.unpack_from("<Q", data, 8)[0]
        ptr = struct.unpack_from("<Q", data, 16)[0]
        mode = "long"
    else:
        length = first >> 1
        ptr = addr + 1
        mode = "short"
    capped = min(length, 4096)
    raw = _read(process, ptr, capped) if capped else b""
    text = raw.decode("utf-8", errors="replace") if raw is not None else None
    return {
        "addr": addr,
        "mode": mode,
        "length": length,
        "data_ptr": ptr,
        "text_capped": text,
        "was_truncated": length > capped,
    }


def _record_view(process, addr):
    if not addr:
        return None
    return {
        "addr": addr,
        "i32_0x00": _i32(process, addr),
        "i32_0x04": _i32(process, addr + 4),
        "i32_0x08": _i32(process, addr + 8),
        "i32_0x0c": _i32(process, addr + 0xC),
        "u64_0x00": _u64(process, addr),
        "u64_0x08": _u64(process, addr + 8),
    }


def _dims_view(process, addr):
    if not addr:
        return None
    return {
        "addr": addr,
        "i32_0x00": _i32(process, addr),
        "i32_0x04": _i32(process, addr + 4),
        "i32_0x08": _i32(process, addr + 8),
        "u64_0x00": _u64(process, addr),
        "u64_0x08": _u64(process, addr + 8),
    }


def _image_descriptor(process, addr):
    if not addr:
        return None
    return {
        "addr": addr,
        "i32_0x10_width": _i32(process, addr + 0x10),
        "i32_0x14_height": _i32(process, addr + 0x14),
        "i32_0x18_stride_or_count": _i32(process, addr + 0x18),
        "i32_0x1c": _i32(process, addr + 0x1C),
        "u64_0x20_data": _u64(process, addr + 0x20),
    }


def _writer_call_descriptor(process, addr):
    if not addr:
        return None
    return {
        "addr": addr,
        "i32_0x00_width": _i32(process, addr),
        "i32_0x04_height": _i32(process, addr + 4),
        "i64_0x08_row_bytes": _u64(process, addr + 8),
        "i32_0x10_bytes_per_pixel": _i32(process, addr + 0x10),
        "u64_0x18_data": _u64(process, addr + 0x18),
    }


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


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _registers(frame):
    names = (
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
    return {name: _u(frame, name) for name in names}


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


def _case3_call_operands(process, frame):
    regs = _registers(frame)
    record = regs["r13"]
    return {
        "record_r13": record,
        "context_rdi": regs["rdi"],
        "expected_context_rbp_minus_0x7f0": _u64(process, regs["rbp"] - 0x7F0),
        "arg_rsi_record_plus_0x10": regs["rsi"],
        "arg_rdx_record_plus_0x60": regs["rdx"],
        "arg_rcx_record_plus_0x50": regs["rcx"],
        "arg_r8d_record_plus_0x68": regs["r8"] & 0xFFFFFFFF,
        "arg_r9_record_plus_0x20": regs["r9"],
        "matches_context": regs["rdi"] == _u64(process, regs["rbp"] - 0x7F0),
        "matches_record_plus_0x10": regs["rsi"] == record + 0x10,
        "matches_record_plus_0x20": regs["r9"] == record + 0x20,
        "matches_record_plus_0x50": regs["rcx"] == record + 0x50,
        "matches_record_plus_0x60": regs["rdx"] == record + 0x60,
        "record_plus_0x10_view": _record_view(process, record + 0x10),
        "record_plus_0x20_view": _record_view(process, record + 0x20),
        "record_plus_0x50_view": _record_view(process, record + 0x50),
        "record_plus_0x60_dims": _dims_view(process, record + 0x60),
    }


def _packet(frame, process, site_va):
    regs = _registers(frame)
    packet = {
        "site_va": f"0x{site_va:x}",
        "site_name": SITES[site_va],
        "registers": regs,
    }
    if site_va == 0x3BCF16:
        packet["case3_call"] = _case3_call_operands(process, frame)
    if site_va == 0x4182A0:
        packet["helper_4182a0_entry_args"] = {
            "context_rdi": regs["rdi"],
            "arg_rsi_view": _record_view(process, regs["rsi"]),
            "arg_rdx_dims": _dims_view(process, regs["rdx"]),
            "arg_rcx_view": _record_view(process, regs["rcx"]),
            "arg_r8d": regs["r8"] & 0xFFFFFFFF,
            "arg_r9_view": _record_view(process, regs["r9"]),
        }
    if site_va == 0x418908:
        packet["helper_4182a0_call_41e180"] = {
            "context_rdi": regs["rdi"],
            "arg_rsi_view": _record_view(process, regs["rsi"]),
            "dims_rdx": _dims_view(process, regs["rdx"]),
            "record50_rcx_view": _record_view(process, regs["rcx"]),
            "format_r8d": regs["r8"] & 0xFFFFFFFF,
            "record20_r9_view": _record_view(process, regs["r9"]),
        }
    if site_va == 0x41E180:
        packet["helper_41e180_entry_args"] = {
            "context_rdi": regs["rdi"],
            "arg_rsi_view": _record_view(process, regs["rsi"]),
            "dims_rdx": _dims_view(process, regs["rdx"]),
            "record50_rcx_view": _record_view(process, regs["rcx"]),
            "format_r8d": regs["r8"] & 0xFFFFFFFF,
            "record20_r9_view": _record_view(process, regs["r9"]),
        }
    if site_va == 0x41E599:
        packet["helper_41e180_hdr_writer_call"] = {
            "descriptor_rdi": _image_descriptor(process, regs["rdi"]),
            "extension_rsi_string": _std_string(process, regs["rsi"]),
            "third_arg_rdx_view": _record_view(process, regs["rdx"]),
        }
    if site_va in (0x2326A0,):
        packet["writer_entry_args"] = {
            "descriptor_rdi": _image_descriptor(process, regs["rdi"]),
            "extension_rsi_string": _std_string(process, regs["rsi"]),
            "third_arg_rdx_view": _record_view(process, regs["rdx"]),
        }
    if site_va == 0x232731:
        packet["writer_virtual_call"] = {
            "writer_object_rdi": regs["rdi"],
            "third_arg_rsi_view": _record_view(process, regs["rsi"]),
            "call_descriptor_rdx": _writer_call_descriptor(process, regs["rdx"]),
        }
    if site_va == 0x232733:
        packet["writer_return_rax"] = regs["rax"]
    return packet


def install_breakpoints(debugger, only=None):
    lldb = builtins.__import__("lldb")
    state = _state()
    target = debugger.GetSelectedTarget()
    interpreter = debugger.GetCommandInterpreter()
    selected = sorted(SITES) if only is None else list(only)
    for va in selected:
        if va not in SITES:
            state["errors"].append(f"unknown requested breakpoint VA 0x{va:x}")
            continue
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
    print("L16_CODEX_FINAL_CASE3_TO_HDR_WRITER_BPS", json.dumps(state["breakpoint_ids"], sort_keys=True))


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
    print("L16_CODEX_FINAL_CASE3_TO_HDR_WRITER_DRIVE_STEPS", steps)


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(_state(), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_CODEX_FINAL_CASE3_TO_HDR_WRITER_REPORT", path)
