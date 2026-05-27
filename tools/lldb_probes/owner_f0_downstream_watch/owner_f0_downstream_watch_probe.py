import builtins
import struct


def reset():
    builtins.l16_owner_f0_watch_setup = None
    builtins.l16_owner_f0_watch_hit = None


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    error = builtins.__import__("lldb").SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u64(data, off=0):
    return struct.unpack_from("<Q", data, off)[0]


def _i32(data, off=0):
    return struct.unpack_from("<i", data, off)[0]


def _module_va(target, pc):
    for module in target.module_iter():
        name = str(module.GetFileSpec().GetFilename())
        if name == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF and pc >= base:
                return pc - base
    return None


def _libcp_base(target):
    for module in target.module_iter():
        name = str(module.GetFileSpec().GetFilename())
        if name == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                return base
    return None


def _stack(thread):
    target = thread.GetProcess().GetTarget()
    frames = []
    for i in range(min(thread.GetNumFrames(), 12)):
        frame = thread.GetFrameAtIndex(i)
        pc = frame.GetPC()
        frames.append(
            {
                "index": i,
                "pc": pc,
                "libcp_va": _module_va(target, pc),
                "function": frame.GetFunctionName(),
            }
        )
    return frames


def _descriptor(process, addr):
    data = _read(process, addr, 0x30)
    if data is None:
        return {"addr": addr, "error": "failed to read descriptor"}
    data_ptr = _u64(data, 0x20)
    first = _read(process, data_ptr, 16) if data_ptr else None
    return {
        "addr": addr,
        "qword_00": _u64(data, 0x00),
        "qword_08": _u64(data, 0x08),
        "width_0x10": _i32(data, 0x10),
        "height_0x14": _i32(data, 0x14),
        "stride_0x18": _i32(data, 0x18),
        "data_ptr_0x20": data_ptr,
        "qword_28": _u64(data, 0x28),
        "first_16_bytes": list(first) if first is not None else None,
    }


def install_watchpoint(frame, bp_loc, internal_dict):
    lldb = builtins.__import__("lldb")
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    r14 = _u(frame, "r14")

    owner_data = _read(process, r14, 8) if r14 else None
    owner = _u64(owner_data) if owner_data else None
    dest_desc = owner + 0xF0 if owner else None
    descriptor = _descriptor(process, dest_desc) if dest_desc else None
    data_ptr = descriptor.get("data_ptr_0x20") if descriptor else None

    packet = {
        "stop_rip": _u(frame, "rip"),
        "stop_libcp_va": _module_va(target, _u(frame, "rip")),
        "r14_output_wrapper": r14,
        "owner_from_wrapper": owner,
        "dest_descriptor_owner_plus_0xf0": dest_desc,
        "dest_descriptor": descriptor,
        "watch_address": data_ptr,
        "watch_size": 8,
    }

    if data_ptr:
        error = lldb.SBError()
        wp = target.WatchAddress(data_ptr, 8, True, True, error)
        if error.Success() and wp.IsValid():
            packet["watchpoint_id"] = wp.GetID()
            packet["watchpoint_error"] = None
        else:
            packet["watchpoint_id"] = None
            packet["watchpoint_error"] = error.GetCString()
    else:
        packet["watchpoint_id"] = None
        packet["watchpoint_error"] = "missing data pointer"

    base = _libcp_base(target)
    if base is not None:
        conversion_bp = target.BreakpointCreateByAddress(base + 0xC0410)
        conversion_bp.SetScriptCallbackFunction(
            "owner_f0_downstream_watch_probe.hit_conversion_entry_cb"
        )
        packet["conversion_breakpoint_id"] = conversion_bp.GetID()
        packet["conversion_breakpoint_load_address"] = base + 0xC0410
    else:
        packet["conversion_breakpoint_id"] = None
        packet["conversion_breakpoint_load_address"] = None

    builtins.l16_owner_f0_watch_setup = packet
    bp_loc.GetBreakpoint().SetEnabled(False)


def install_watchpoint_cb(frame, bp_loc, extra_args, internal_dict):
    install_watchpoint(frame, bp_loc, internal_dict)
    return False


def hit_watchpoint(frame, wp_loc, extra_args, internal_dict):
    if builtins.l16_owner_f0_watch_hit is not None:
        return True

    process = frame.GetThread().GetProcess()
    thread = frame.GetThread()
    target = process.GetTarget()
    setup = builtins.l16_owner_f0_watch_setup or {}
    watch_address = setup.get("watch_address")
    first = _read(process, watch_address, 16) if watch_address else None

    builtins.l16_owner_f0_watch_hit = {
        "rip": _u(frame, "rip"),
        "libcp_va": _module_va(target, _u(frame, "rip")),
        "thread_id": thread.GetThreadID(),
        "watch_address": watch_address,
        "first_16_bytes_at_hit": list(first) if first is not None else None,
        "registers": {
            name: _u(frame, name)
            for name in [
                "rax",
                "rbx",
                "rcx",
                "rdx",
                "rsi",
                "rdi",
                "rsp",
                "rbp",
                "r12",
                "r13",
                "r14",
                "r15",
            ]
        },
        "stack": _stack(thread),
    }
    return True


def hit_conversion_entry_cb(frame, bp_loc, extra_args, internal_dict):
    if builtins.l16_owner_f0_watch_hit is not None:
        bp_loc.GetBreakpoint().SetEnabled(False)
        return True

    setup = builtins.l16_owner_f0_watch_setup
    if not setup:
        return False

    descriptor = setup.get("dest_descriptor") or {}
    data_ptr = descriptor.get("data_ptr_0x20")
    stride = descriptor.get("stride_0x18")
    height = descriptor.get("height_0x14")
    if not data_ptr or not stride or not height:
        return False

    source_row = _u(frame, "rsi")
    byte_size = stride * height * 6
    if source_row < data_ptr or source_row >= data_ptr + byte_size:
        return False

    process = frame.GetThread().GetProcess()
    thread = frame.GetThread()
    target = process.GetTarget()
    first = _read(process, source_row, 16)
    offset = source_row - data_ptr

    builtins.l16_owner_f0_watch_hit = {
        "hit_kind": "conversion_entry_source_range_match",
        "rip": _u(frame, "rip"),
        "libcp_va": _module_va(target, _u(frame, "rip")),
        "thread_id": thread.GetThreadID(),
        "source_row_rsi": source_row,
        "dest_row_rdi": _u(frame, "rdi"),
        "width_edx": _u(frame, "rdx"),
        "mode_cl": _u(frame, "rcx") & 0xFF,
        "source_offset_bytes": offset,
        "source_offset_pixels_at_6_bytes": offset // 6,
        "source_offset_mod_6": offset % 6,
        "first_16_bytes_at_source": list(first) if first is not None else None,
        "registers": {
            name: _u(frame, name)
            for name in [
                "rax",
                "rbx",
                "rcx",
                "rdx",
                "rsi",
                "rdi",
                "rsp",
                "rbp",
                "r12",
                "r13",
                "r14",
                "r15",
            ]
        },
        "stack": _stack(thread),
    }
    bp_loc.GetBreakpoint().SetEnabled(False)
    return True


def capture_selected_stop(debugger):
    lldb = builtins.__import__("lldb")
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    if not process.IsValid():
        return

    thread = process.GetSelectedThread()
    if not thread.IsValid() or thread.GetNumFrames() == 0:
        return

    if thread.GetStopReason() != lldb.eStopReasonWatchpoint:
        return

    frame = thread.GetFrameAtIndex(0)
    setup = builtins.l16_owner_f0_watch_setup or {}
    watch_address = setup.get("watch_address")
    first = _read(process, watch_address, 16) if watch_address else None

    builtins.l16_owner_f0_watch_hit = {
        "rip": _u(frame, "rip"),
        "libcp_va": _module_va(target, _u(frame, "rip")),
        "thread_id": thread.GetThreadID(),
        "watch_address": watch_address,
        "first_16_bytes_at_hit": list(first) if first is not None else None,
        "registers": {
            name: _u(frame, name)
            for name in [
                "rax",
                "rbx",
                "rcx",
                "rdx",
                "rsi",
                "rdi",
                "rsp",
                "rbp",
                "r12",
                "r13",
                "r14",
                "r15",
            ]
        },
        "stack": _stack(thread),
    }


def continue_if_no_hit(debugger):
    if builtins.l16_owner_f0_watch_hit is not None:
        return
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    if process.IsValid() and process.GetState() == builtins.__import__(
        "lldb"
    ).eStateStopped:
        process.Continue()


def attach_setup_breakpoint(debugger):
    target = debugger.GetSelectedTarget()
    count = target.GetNumBreakpoints()
    if count == 0:
        print("L16_OWNER_F0 attach error: expected setup breakpoint")
        return
    setup_bp = target.GetBreakpointAtIndex(count - 1)
    setup_bp.SetScriptCallbackFunction(
        "owner_f0_downstream_watch_probe.install_watchpoint_cb"
    )
    print("L16_OWNER_F0 attached setup callback to breakpoint", setup_bp.GetID())


def report(label):
    if not hasattr(builtins, "l16_owner_f0_watch_setup"):
        reset()
    print("L16_OWNER_F0_DOWNSTREAM_WATCH_BEGIN", label)
    print("setup_packet", builtins.l16_owner_f0_watch_setup)
    print("hit_packet", builtins.l16_owner_f0_watch_hit)
    print("L16_OWNER_F0_DOWNSTREAM_WATCH_END", label)
