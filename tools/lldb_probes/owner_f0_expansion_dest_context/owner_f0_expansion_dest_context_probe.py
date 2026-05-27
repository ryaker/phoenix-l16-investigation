import builtins
import struct


def reset():
    builtins.l16_owner_f0_dest_setup = None
    builtins.l16_owner_f0_dest_entry = None
    builtins.l16_owner_f0_dest_handoff = None


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


def _f32s(data):
    return list(struct.unpack("<" + "f" * (len(data) // 4), data))


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


def _descriptor(process, addr, first_size=16):
    data = _read(process, addr, 0x30)
    if data is None:
        return {"addr": addr, "error": "failed to read descriptor"}
    data_ptr = _u64(data, 0x20)
    first = _read(process, data_ptr, first_size) if data_ptr else None
    return {
        "addr": addr,
        "qword_00": _u64(data, 0x00),
        "qword_08": _u64(data, 0x08),
        "width_0x10": _i32(data, 0x10),
        "height_0x14": _i32(data, 0x14),
        "stride_0x18": _i32(data, 0x18),
        "i32_0x1c": _i32(data, 0x1C),
        "data_ptr_0x20": data_ptr,
        "qword_28": _u64(data, 0x28),
        "first_bytes": list(first) if first is not None else None,
        "first_vec4": _f32s(first) if first is not None and first_size == 16 else None,
    }


def _descriptor_byte_span(desc, element_size):
    stride = desc.get("stride_0x18") or 0
    height = desc.get("height_0x14") or 0
    return stride * height * element_size


def setup_cb(frame, bp_loc, extra_args, internal_dict):
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    r14 = _u(frame, "r14")

    owner_data = _read(process, r14, 8) if r14 else None
    owner = _u64(owner_data) if owner_data else None
    owner_desc_addr = owner + 0xF0 if owner else None
    owner_desc = _descriptor(process, owner_desc_addr, 16) if owner_desc_addr else None
    owner_data_ptr = owner_desc.get("data_ptr_0x20") if owner_desc else None
    owner_byte_size = _descriptor_byte_span(owner_desc, 6) if owner_desc else None

    packet = {
        "stop_rip": _u(frame, "rip"),
        "stop_libcp_va": _module_va(target, _u(frame, "rip")),
        "r14_output_wrapper": r14,
        "owner_from_wrapper": owner,
        "owner_plus_0xf0_descriptor": owner_desc_addr,
        "owner_plus_0xf0_descriptor_packet": owner_desc,
        "owner_plus_0xf0_data_ptr": owner_data_ptr,
        "owner_plus_0xf0_data_byte_size_assuming_6_bytes": owner_byte_size,
    }

    base = _libcp_base(target)
    if base is not None:
        entry_bp = target.BreakpointCreateByAddress(base + 0x3D4E10)
        entry_bp.SetScriptCallbackFunction(
            "owner_f0_expansion_dest_context_probe.entry_cb"
        )
        packet["entry_breakpoint_id"] = entry_bp.GetID()
        packet["entry_breakpoint_load_address"] = base + 0x3D4E10
    else:
        packet["entry_breakpoint_id"] = None
        packet["entry_breakpoint_load_address"] = None

    builtins.l16_owner_f0_dest_setup = packet
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def entry_cb(frame, bp_loc, extra_args, internal_dict):
    if builtins.l16_owner_f0_dest_entry is not None:
        bp_loc.GetBreakpoint().SetEnabled(False)
        return False

    setup = builtins.l16_owner_f0_dest_setup
    if not setup:
        return False

    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    rdi = _u(frame, "rdi")
    rsi = _u(frame, "rsi")

    source_pair = _read(process, rsi, 0x30) if rsi else None
    source_owner = _u64(source_pair, 0) if source_pair else None
    if source_owner != setup.get("owner_from_wrapper"):
        return False

    output_context = rdi
    context_data = _read(process, output_context, 0x18) if output_context else None
    if context_data is None:
        return False
    dest_base_desc_addr = _u64(context_data, 0x10)
    dest_base_desc = _descriptor(process, dest_base_desc_addr, 16)

    thread = frame.GetThread()
    builtins.l16_owner_f0_dest_entry = {
        "rip": _u(frame, "rip"),
        "libcp_va": _module_va(target, _u(frame, "rip")),
        "thread_id": thread.GetThreadID(),
        "output_context_rdi": output_context,
        "source_pair_rsi": rsi,
        "source_owner_from_pair": source_owner,
        "context_qword_00": _u64(context_data, 0x00),
        "context_qword_08": _u64(context_data, 0x08),
        "context_dest_descriptor_ptr_0x10": dest_base_desc_addr,
        "context_dest_descriptor_packet_entry": dest_base_desc,
        "stack": _stack(thread),
    }

    base = _libcp_base(target)
    if base is not None:
        handoff_bp = target.BreakpointCreateByAddress(base + 0x3D502E)
        handoff_bp.SetScriptCallbackFunction(
            "owner_f0_expansion_dest_context_probe.handoff_cb"
        )
        builtins.l16_owner_f0_dest_entry["handoff_breakpoint_id"] = handoff_bp.GetID()
        builtins.l16_owner_f0_dest_entry["handoff_breakpoint_load_address"] = (
            base + 0x3D502E
        )
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def handoff_cb(frame, bp_loc, extra_args, internal_dict):
    if builtins.l16_owner_f0_dest_handoff is not None:
        bp_loc.GetBreakpoint().SetEnabled(False)
        return True

    setup = builtins.l16_owner_f0_dest_setup
    entry = builtins.l16_owner_f0_dest_entry
    if not setup or not entry:
        return False

    thread = frame.GetThread()
    if thread.GetThreadID() != entry.get("thread_id"):
        return False

    process = thread.GetProcess()
    target = process.GetTarget()
    rbp = _u(frame, "rbp")
    dest_view_addr = rbp - 0x90
    source_view_addr = rbp - 0x60
    dest_view = _descriptor(process, dest_view_addr, 16)
    source_view = _descriptor(process, source_view_addr, 16)
    dest_base_addr = entry.get("context_dest_descriptor_ptr_0x10")
    dest_base_now = _descriptor(process, dest_base_addr, 16)

    owner_data_ptr = setup.get("owner_plus_0xf0_data_ptr")
    owner_byte_size = setup.get("owner_plus_0xf0_data_byte_size_assuming_6_bytes")
    source_data_ptr = source_view.get("data_ptr_0x20")
    if not owner_data_ptr or not owner_byte_size or not source_data_ptr:
        return False
    if source_data_ptr < owner_data_ptr or source_data_ptr >= owner_data_ptr + owner_byte_size:
        return False

    base_ptr = dest_base_now.get("qword_28") or dest_base_now.get("data_ptr_0x20")
    base_span = _descriptor_byte_span(dest_base_now, 16)
    dest_data_ptr = dest_view.get("data_ptr_0x20")
    dest_offset = None
    dest_inside_base = None
    if base_ptr and base_span and dest_data_ptr:
        dest_offset = dest_data_ptr - base_ptr
        dest_inside_base = base_ptr <= dest_data_ptr < base_ptr + base_span

    builtins.l16_owner_f0_dest_handoff = {
        "rip": _u(frame, "rip"),
        "libcp_va": _module_va(target, _u(frame, "rip")),
        "thread_id": thread.GetThreadID(),
        "rbp": rbp,
        "source_descriptor_rbp_minus_0x60": source_view,
        "dest_view_descriptor_rbp_minus_0x90": dest_view,
        "context_dest_descriptor_packet_handoff": dest_base_now,
        "source_data_offset_from_owner_plus_0xf0": source_data_ptr - owner_data_ptr,
        "source_offset_mod_6": (source_data_ptr - owner_data_ptr) % 6,
        "dest_view_offset_from_context_base": dest_offset,
        "dest_view_offset_mod_16": dest_offset % 16 if dest_offset is not None else None,
        "dest_view_data_inside_context_base": dest_inside_base,
        "dest_view_qword_28_matches_context_qword_28": dest_view.get("qword_28")
        == dest_base_now.get("qword_28"),
        "dest_view_element_size_from_static_site": 16,
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


def attach_setup_breakpoint(debugger):
    target = debugger.GetSelectedTarget()
    count = target.GetNumBreakpoints()
    if count == 0:
        print("L16_OWNER_F0_DEST_CONTEXT attach error: expected setup breakpoint")
        return
    setup_bp = target.GetBreakpointAtIndex(count - 1)
    setup_bp.SetScriptCallbackFunction("owner_f0_expansion_dest_context_probe.setup_cb")
    print("L16_OWNER_F0_DEST_CONTEXT attached setup callback", setup_bp.GetID())


def continue_if_no_handoff(debugger):
    if builtins.l16_owner_f0_dest_handoff is not None:
        return
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    if process.IsValid() and process.GetState() == lldb.eStateStopped:
        process.Continue()


def report(label):
    if not hasattr(builtins, "l16_owner_f0_dest_setup"):
        reset()
    print("L16_OWNER_F0_DEST_CONTEXT_BEGIN", label)
    print("setup_packet", builtins.l16_owner_f0_dest_setup)
    print("entry_packet", builtins.l16_owner_f0_dest_entry)
    print("handoff_packet", builtins.l16_owner_f0_dest_handoff)
    print("L16_OWNER_F0_DEST_CONTEXT_END", label)
