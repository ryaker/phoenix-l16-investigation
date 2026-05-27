import builtins
import struct


def reset():
    builtins.l16_owner_f0_expansion_setup = None
    builtins.l16_owner_f0_expansion_handoff = None


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


def install_handoff_breakpoint_cb(frame, bp_loc, extra_args, internal_dict):
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    r14 = _u(frame, "r14")

    owner_data = _read(process, r14, 8) if r14 else None
    owner = _u64(owner_data) if owner_data else None
    dest_desc = owner + 0xF0 if owner else None
    descriptor = _descriptor(process, dest_desc, 16) if dest_desc else None
    data_ptr = descriptor.get("data_ptr_0x20") if descriptor else None
    byte_size = None
    if descriptor and data_ptr:
        width = descriptor.get("width_0x10") or 0
        height = descriptor.get("height_0x14") or 0
        byte_size = width * height * 6

    packet = {
        "stop_rip": _u(frame, "rip"),
        "stop_libcp_va": _module_va(target, _u(frame, "rip")),
        "r14_output_wrapper": r14,
        "owner_from_wrapper": owner,
        "owner_plus_0xf0_descriptor": dest_desc,
        "owner_plus_0xf0_descriptor_packet": descriptor,
        "owner_plus_0xf0_data_ptr": data_ptr,
        "owner_plus_0xf0_data_byte_size_assuming_6_bytes": byte_size,
    }

    base = _libcp_base(target)
    if base is not None:
        handoff_bp = target.BreakpointCreateByAddress(base + 0x3D502E)
        handoff_bp.SetScriptCallbackFunction(
            "owner_f0_expansion_handoff_probe.hit_handoff_cb"
        )
        packet["handoff_breakpoint_id"] = handoff_bp.GetID()
        packet["handoff_breakpoint_load_address"] = base + 0x3D502E
    else:
        packet["handoff_breakpoint_id"] = None
        packet["handoff_breakpoint_load_address"] = None

    builtins.l16_owner_f0_expansion_setup = packet
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def hit_handoff_cb(frame, bp_loc, extra_args, internal_dict):
    if builtins.l16_owner_f0_expansion_handoff is not None:
        bp_loc.GetBreakpoint().SetEnabled(False)
        return True

    setup = builtins.l16_owner_f0_expansion_setup
    if not setup:
        return False

    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    rbp = _u(frame, "rbp")
    expanded_desc_addr = rbp - 0x90
    source_desc_addr = rbp - 0x60
    expanded_desc = _descriptor(process, expanded_desc_addr, 16)
    source_desc = _descriptor(process, source_desc_addr, 16)

    owner_data_ptr = setup.get("owner_plus_0xf0_data_ptr")
    owner_byte_size = setup.get("owner_plus_0xf0_data_byte_size_assuming_6_bytes")
    source_data_ptr = source_desc.get("data_ptr_0x20")
    if not owner_data_ptr or not owner_byte_size or not source_data_ptr:
        return False
    if source_data_ptr < owner_data_ptr or source_data_ptr >= owner_data_ptr + owner_byte_size:
        return False

    thread = frame.GetThread()
    builtins.l16_owner_f0_expansion_handoff = {
        "rip": _u(frame, "rip"),
        "libcp_va": _module_va(target, _u(frame, "rip")),
        "thread_id": thread.GetThreadID(),
        "rbp": rbp,
        "source_descriptor_rbp_minus_0x60": source_desc,
        "expanded_descriptor_rbp_minus_0x90": expanded_desc,
        "source_data_offset_from_owner_plus_0xf0": source_data_ptr - owner_data_ptr,
        "source_offset_mod_6": (source_data_ptr - owner_data_ptr) % 6,
        "expanded_element_size_from_static_site": 16,
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
        print("L16_OWNER_F0_EXPANSION attach error: expected setup breakpoint")
        return
    setup_bp = target.GetBreakpointAtIndex(count - 1)
    setup_bp.SetScriptCallbackFunction(
        "owner_f0_expansion_handoff_probe.install_handoff_breakpoint_cb"
    )
    print("L16_OWNER_F0_EXPANSION attached setup callback", setup_bp.GetID())


def continue_if_no_handoff(debugger):
    if builtins.l16_owner_f0_expansion_handoff is not None:
        return
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    if process.IsValid() and process.GetState() == lldb.eStateStopped:
        process.Continue()


def report(label):
    if not hasattr(builtins, "l16_owner_f0_expansion_setup"):
        reset()
    print("L16_OWNER_F0_EXPANSION_HANDOFF_BEGIN", label)
    print("setup_packet", builtins.l16_owner_f0_expansion_setup)
    print("handoff_packet", builtins.l16_owner_f0_expansion_handoff)
    print("L16_OWNER_F0_EXPANSION_HANDOFF_END", label)
