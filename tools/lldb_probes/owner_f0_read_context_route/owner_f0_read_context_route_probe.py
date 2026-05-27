import builtins
import json
import struct


VISIBLE_SRC1_POST_READ_SITE = 0x3ECC74
OWNER_CACHE_RESCALE_CALL_SITE = 0x3D08CE


def reset():
    builtins.l16_owner_f0_route_setup = None
    builtins.l16_owner_f0_route_handoff = None
    builtins.l16_owner_f0_route_post = None


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
    for i in range(min(thread.GetNumFrames(), 16)):
        frame = thread.GetFrameAtIndex(i)
        pc = frame.GetPC()
        frames.append(
            {
                "index": i,
                "pc": pc,
                "libcp_va": _module_va(target, pc),
                "function": frame.GetFunctionName(),
                "rbp": _u(frame, "rbp"),
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


def _ptr(process, addr):
    data = _read(process, addr, 8)
    return _u64(data) if data else None


def _i32_quad(process, addr):
    data = _read(process, addr, 16)
    if data is None:
        return None
    return list(struct.unpack("<iiii", data))


def _find_3d01b0_frame(thread):
    target = thread.GetProcess().GetTarget()
    for i in range(thread.GetNumFrames()):
        frame = thread.GetFrameAtIndex(i)
        va = _module_va(target, frame.GetPC())
        if va is not None and 0x3D01B0 <= va < 0x3D0650:
            return i, frame, va
    return None, None, None


def _install_branch_breakpoints(target):
    base = _libcp_base(target)
    if base is None:
        return []
    ids = []
    for va in (0x3D4842, 0x3D4864):
        bp = target.BreakpointCreateByAddress(base + va)
        bp.SetScriptCallbackFunction(
            "owner_f0_read_context_route_probe.handoff_branch_cb"
        )
        ids.append({"id": bp.GetID(), "libcp_va": va, "load_address": base + va})
    return ids


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

    builtins.l16_owner_f0_route_setup = {
        "stop_rip": _u(frame, "rip"),
        "stop_libcp_va": _module_va(target, _u(frame, "rip")),
        "r14_output_wrapper": r14,
        "owner_from_wrapper": owner,
        "owner_plus_0xf0_descriptor": owner_desc_addr,
        "owner_plus_0xf0_descriptor_packet": owner_desc,
        "owner_plus_0xf0_data_ptr": owner_data_ptr,
        "owner_plus_0xf0_data_byte_size_assuming_6_bytes": owner_byte_size,
        "branch_breakpoints": _install_branch_breakpoints(target),
    }
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def _active_callable_packet(process, target, rbx):
    active = _ptr(process, rbx + 0x70) if rbx else None
    vtable = _ptr(process, active) if active else None
    slot_30 = _ptr(process, vtable + 0x30) if vtable else None
    return {
        "active_callable_ptr": active,
        "active_callable_vtable": vtable,
        "active_callable_slot_0x30": slot_30,
        "active_callable_slot_0x30_libcp_va": _module_va(target, slot_30)
        if slot_30
        else None,
    }


def handoff_branch_cb(frame, bp_loc, extra_args, internal_dict):
    if builtins.l16_owner_f0_route_handoff is not None:
        bp_loc.GetBreakpoint().SetEnabled(False)
        return False

    setup = builtins.l16_owner_f0_route_setup
    if not setup:
        return False

    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    rbp = _u(frame, "rbp")
    source_pair_addr = rbp - 0x30
    source_owner = _ptr(process, source_pair_addr)
    if source_owner != setup.get("owner_from_wrapper"):
        return False

    thread = frame.GetThread()
    r14 = _u(frame, "r14")
    rbx = _u(frame, "rbx")
    output_context = _ptr(process, r14 + 0x10)
    context_data = _read(process, output_context, 0x18) if output_context else None
    if context_data is None:
        return False
    context_dest_desc = _u64(context_data, 0x10)

    parent_index, parent_frame, parent_va = _find_3d01b0_frame(thread)
    parent_rbp = _u(parent_frame, "rbp") if parent_frame else None
    parent_output_local = (
        _ptr(process, parent_rbp - 0x148) if parent_rbp is not None else None
    )
    parent_context_addr = parent_rbp - 0x108 if parent_rbp is not None else None
    parent_context_data = (
        _read(process, parent_context_addr, 0x18) if parent_context_addr else None
    )
    parent_context_dest = (
        _u64(parent_context_data, 0x10) if parent_context_data else None
    )

    caller_frame = None
    caller_va = None
    caller_rbp = None
    if parent_index is not None and parent_index + 1 < thread.GetNumFrames():
        caller_frame = thread.GetFrameAtIndex(parent_index + 1)
        caller_va = _module_va(target, caller_frame.GetPC())
        caller_rbp = _u(caller_frame, "rbp")

    source_view = _descriptor(process, source_pair_addr, 16)
    context_dest_packet = _descriptor(process, context_dest_desc, 16)
    stop_va = _module_va(target, _u(frame, "rip"))
    active_packet = _active_callable_packet(process, target, rbx)

    builtins.l16_owner_f0_route_handoff = {
        "rip": _u(frame, "rip"),
        "libcp_va": stop_va,
        "branch": "active_callable_then_3d4e10"
        if stop_va == 0x3D4842
        else "direct_3d4e10",
        "thread_id": thread.GetThreadID(),
        "worker_rbp": rbp,
        "source_pair_addr": source_pair_addr,
        "source_owner_from_pair": source_owner,
        "source_pair_descriptor_packet": source_view,
        "closure_shifted_r14": r14,
        "rbx_source_context": rbx,
        "output_context_from_closure_plus_0x10": output_context,
        "context_qword_00": _u64(context_data, 0x00),
        "context_qword_08": _u64(context_data, 0x08),
        "context_dest_descriptor_ptr_0x10": context_dest_desc,
        "context_dest_descriptor_packet": context_dest_packet,
        "active_callable_packet": active_packet,
        "parent_3d01b0_frame_index": parent_index,
        "parent_3d01b0_current_libcp_va": parent_va,
        "parent_3d01b0_rbp": parent_rbp,
        "parent_output_descriptor_local_rbp_minus_0x148": parent_output_local,
        "parent_context_addr_rbp_minus_0x108": parent_context_addr,
        "parent_context_qword_00": _u64(parent_context_data, 0x00)
        if parent_context_data
        else None,
        "parent_context_qword_08": _u64(parent_context_data, 0x08)
        if parent_context_data
        else None,
        "parent_context_dest_descriptor_0x10": parent_context_dest,
        "output_context_matches_parent_context_addr": output_context
        == parent_context_addr,
        "context_dest_matches_parent_output_local": context_dest_desc
        == parent_output_local,
        "parent_context_dest_matches_context_dest": parent_context_dest
        == context_dest_desc,
        "caller_after_3d01b0_frame_libcp_va": caller_va,
        "caller_after_3d01b0_rbp": caller_rbp,
        "visible_src1_expected_intermediate_descriptor": caller_rbp - 0x50
        if caller_va == 0x3ECC5A and caller_rbp is not None
        else None,
        "visible_src1_expected_matches_context_dest": (caller_rbp - 0x50)
        == context_dest_desc
        if caller_va == 0x3ECC5A and caller_rbp is not None
        else None,
        "requested_roi_i32_quad_from_parent_r12": _i32_quad(
            process, _ptr(process, parent_rbp - 0x100)
        )
        if parent_rbp is not None and _ptr(process, parent_rbp - 0x100)
        else None,
        "stack": _stack(thread),
    }

    if caller_va == 0x3ECC5A:
        base = _libcp_base(target)
        if base is not None:
            post_bp = target.BreakpointCreateByAddress(base + VISIBLE_SRC1_POST_READ_SITE)
            post_bp.SetScriptCallbackFunction(
                "owner_f0_read_context_route_probe.visible_src1_post_cb"
            )
            builtins.l16_owner_f0_route_handoff[
                "visible_src1_post_breakpoint_id"
            ] = post_bp.GetID()
            builtins.l16_owner_f0_route_handoff[
                "visible_src1_post_breakpoint_load_address"
            ] = base + VISIBLE_SRC1_POST_READ_SITE
    elif caller_va == 0x3D084D:
        base = _libcp_base(target)
        if base is not None:
            post_bp = target.BreakpointCreateByAddress(
                base + OWNER_CACHE_RESCALE_CALL_SITE
            )
            post_bp.SetScriptCallbackFunction(
                "owner_f0_read_context_route_probe.owner_cache_rescale_post_cb"
            )
            builtins.l16_owner_f0_route_handoff[
                "owner_cache_rescale_post_breakpoint_id"
            ] = post_bp.GetID()
            builtins.l16_owner_f0_route_handoff[
                "owner_cache_rescale_post_breakpoint_load_address"
            ] = base + OWNER_CACHE_RESCALE_CALL_SITE

    for bp in target.breakpoint_iter():
        keep_ids = {
            builtins.l16_owner_f0_route_handoff.get("visible_src1_post_breakpoint_id"),
            builtins.l16_owner_f0_route_handoff.get(
                "owner_cache_rescale_post_breakpoint_id"
            ),
        }
        if bp.GetID() not in keep_ids:
            bp.SetEnabled(False)
    return False


def visible_src1_post_cb(frame, bp_loc, extra_args, internal_dict):
    if builtins.l16_owner_f0_route_post is not None:
        bp_loc.GetBreakpoint().SetEnabled(False)
        return True

    handoff = builtins.l16_owner_f0_route_handoff
    if not handoff:
        return False

    thread = frame.GetThread()
    if thread.GetThreadID() != handoff.get("thread_id"):
        return False

    rbp = _u(frame, "rbp")
    expected = handoff.get("context_dest_descriptor_ptr_0x10")
    visible_intermediate = rbp - 0x50
    if expected != visible_intermediate:
        return False

    process = thread.GetProcess()
    target = process.GetTarget()
    rdi = _u(frame, "rdi")
    rsi = _u(frame, "rsi")
    wrapper_ptr = _ptr(process, rsi) if rsi else None
    wrapped_desc_ptr = _ptr(process, wrapper_ptr) if wrapper_ptr else None

    builtins.l16_owner_f0_route_post = {
        "rip": _u(frame, "rip"),
        "libcp_va": _module_va(target, _u(frame, "rip")),
        "thread_id": thread.GetThreadID(),
        "visible_src1_rbp": rbp,
        "visible_src1_intermediate_descriptor_rbp_minus_0x50": visible_intermediate,
        "matches_context_dest_descriptor": visible_intermediate == expected,
        "rdi_requested_output_descriptor_for_3edb80": rdi,
        "rsi_wrapper_arg_for_3edb80": rsi,
        "wrapper_qword_00": wrapper_ptr,
        "wrapped_descriptor_ptr_from_wrapper_qword_00": wrapped_desc_ptr,
        "wrapped_descriptor_matches_intermediate": wrapped_desc_ptr
        == visible_intermediate,
        "intermediate_descriptor_packet_before_3edb80": _descriptor(
            process, visible_intermediate, 16
        ),
        "requested_output_descriptor_packet_before_3edb80": _descriptor(
            process, rdi, 16
        ),
        "stack": _stack(thread),
    }
    bp_loc.GetBreakpoint().SetEnabled(False)
    return True


def _double_pair(process, addr):
    data = _read(process, addr, 16)
    if data is None:
        return None
    return list(struct.unpack("<dd", data))


def owner_cache_rescale_post_cb(frame, bp_loc, extra_args, internal_dict):
    if builtins.l16_owner_f0_route_post is not None:
        bp_loc.GetBreakpoint().SetEnabled(False)
        return True

    handoff = builtins.l16_owner_f0_route_handoff
    if not handoff:
        return False

    thread = frame.GetThread()
    if thread.GetThreadID() != handoff.get("thread_id"):
        return False

    rbp = _u(frame, "rbp")
    expected = handoff.get("context_dest_descriptor_ptr_0x10")
    owner_cache_temp = rbp - 0x70
    if expected != owner_cache_temp:
        return False

    process = thread.GetProcess()
    target = process.GetTarget()
    rdi = _u(frame, "rdi")
    rsi = _u(frame, "rsi")
    rdx = _u(frame, "rdx")
    rcx = _u(frame, "rcx")

    builtins.l16_owner_f0_route_post = {
        "rip": _u(frame, "rip"),
        "libcp_va": _module_va(target, _u(frame, "rip")),
        "post_route": "owner_cache_rescale_call_36f800",
        "thread_id": thread.GetThreadID(),
        "owner_cache_rbp": rbp,
        "owner_cache_temp_descriptor_rbp_minus_0x70": owner_cache_temp,
        "matches_context_dest_descriptor": owner_cache_temp == expected,
        "rdi_requested_output_descriptor_for_36f800": rdi,
        "rsi_temp_descriptor_arg_for_36f800": rsi,
        "rsi_matches_temp_descriptor": rsi == owner_cache_temp,
        "rdx_offset_pair_arg_for_36f800": rdx,
        "rcx_scale_pair_arg_for_36f800": rcx,
        "offset_pair_doubles": _double_pair(process, rdx),
        "scale_pair_doubles": _double_pair(process, rcx),
        "temp_descriptor_packet_before_36f800": _descriptor(
            process, owner_cache_temp, 16
        ),
        "requested_output_descriptor_packet_before_36f800": _descriptor(
            process, rdi, 16
        ),
        "stack": _stack(thread),
    }
    bp_loc.GetBreakpoint().SetEnabled(False)
    return True


def continue_if_no_post(debugger):
    if builtins.l16_owner_f0_route_post is not None:
        return
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    if process.IsValid() and process.GetState() == lldb.eStateStopped:
        process.Continue()


def drive_until_post_or_exit(debugger, max_steps=16):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while (
        process.IsValid()
        and process.GetState() == lldb.eStateStopped
        and builtins.l16_owner_f0_route_post is None
        and steps < max_steps
    ):
        steps += 1
        process.Continue()
    print("L16_OWNER_F0_READ_CONTEXT_ROUTE_DRIVE_STEPS", steps)


def attach_setup_breakpoint(debugger):
    target = debugger.GetSelectedTarget()
    count = target.GetNumBreakpoints()
    if count == 0:
        print("L16_OWNER_F0_ROUTE attach error: expected setup breakpoint")
        return
    setup_bp = target.GetBreakpointAtIndex(count - 1)
    setup_bp.SetScriptCallbackFunction("owner_f0_read_context_route_probe.setup_cb")
    print("L16_OWNER_F0_ROUTE attached setup callback", setup_bp.GetID())


def _payload(label):
    return {
        "label": label,
        "setup_packet": builtins.l16_owner_f0_route_setup,
        "handoff_packet": builtins.l16_owner_f0_route_handoff,
        "post_packet": builtins.l16_owner_f0_route_post,
    }


def report(label):
    if not hasattr(builtins, "l16_owner_f0_route_setup"):
        reset()
    print("L16_OWNER_F0_READ_CONTEXT_ROUTE_BEGIN", label)
    print(json.dumps(_payload(label), indent=2, sort_keys=True))
    print("L16_OWNER_F0_READ_CONTEXT_ROUTE_END", label)


def write_report(label, path):
    if not hasattr(builtins, "l16_owner_f0_route_setup"):
        reset()
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(_payload(label), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_OWNER_F0_READ_CONTEXT_ROUTE_WROTE", path)
