import builtins
import json
import struct


BRANCH_ACTIVE_CALLABLE = 0x3D4842
BRANCH_DIRECT = 0x3D4864
CALLER_EXACT_SIZE = 0x3D0732
CALLER_OWNER_CACHE_RESCALE = 0x3D084D
CALLER_VISIBLE_SRC1 = 0x3ECC5A
OWNER_CACHE_RESCALE_CALL_SITE = 0x3D08CE
VISIBLE_SRC1_POST_READ_SITE = 0x3ECC74


def reset(limit=128):
    builtins.l16_owner_f0_route_census = {
        "limit": limit,
        "setup": None,
        "accepted_packets": [],
        "unique_packets": [],
        "unique_keys": {},
        "counts": {
            "total_branch_hits": 0,
            "accepted_hits": 0,
            "rejected_before_setup": 0,
            "rejected_source_owner_mismatch": 0,
            "branch_counts": {},
            "caller_counts": {},
            "slot_counts": {},
            "branch_caller_counts": {},
        },
        "cap_reached": False,
    }


def _state():
    if not hasattr(builtins, "l16_owner_f0_route_census"):
        reset()
    return builtins.l16_owner_f0_route_census


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


def _inc(mapping, key):
    key = "None" if key is None else str(key)
    mapping[key] = mapping.get(key, 0) + 1


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


def _descriptor_summary(process, addr):
    data = _read(process, addr, 0x30)
    if data is None:
        return {"addr": addr, "error": "failed to read descriptor"}
    return {
        "addr": addr,
        "qword_00": _u64(data, 0x00),
        "qword_08": _u64(data, 0x08),
        "width_0x10": _i32(data, 0x10),
        "height_0x14": _i32(data, 0x14),
        "stride_0x18": _i32(data, 0x18),
        "i32_0x1c": _i32(data, 0x1C),
        "data_ptr_0x20": _u64(data, 0x20),
        "qword_28": _u64(data, 0x28),
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


def _install_branch_breakpoints(target):
    base = _libcp_base(target)
    if base is None:
        return []
    ids = []
    for va in (BRANCH_ACTIVE_CALLABLE, BRANCH_DIRECT):
        bp = target.BreakpointCreateByAddress(base + va)
        bp.SetScriptCallbackFunction(
            "owner_f0_route_census_probe.handoff_branch_cb"
        )
        ids.append({"id": bp.GetID(), "libcp_va": va, "load_address": base + va})
    return ids


def setup_cb(frame, bp_loc, extra_args, internal_dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    r14 = _u(frame, "r14")

    owner_data = _read(process, r14, 8) if r14 else None
    owner = _u64(owner_data) if owner_data else None
    owner_desc_addr = owner + 0xF0 if owner else None
    owner_desc = _descriptor(process, owner_desc_addr, 16) if owner_desc_addr else None

    state["setup"] = {
        "stop_rip": _u(frame, "rip"),
        "stop_libcp_va": _module_va(target, _u(frame, "rip")),
        "r14_output_wrapper": r14,
        "owner_from_wrapper": owner,
        "owner_plus_0xf0_descriptor": owner_desc_addr,
        "owner_plus_0xf0_descriptor_packet": owner_desc,
        "owner_plus_0xf0_data_ptr": owner_desc.get("data_ptr_0x20")
        if owner_desc
        else None,
        "owner_plus_0xf0_data_byte_size_assuming_6_bytes": _descriptor_byte_span(
            owner_desc, 6
        )
        if owner_desc
        else None,
        "branch_breakpoints": _install_branch_breakpoints(target),
    }
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def _packet_key(packet):
    return "|".join(
        [
            "branch=%s" % packet.get("branch"),
            "caller=0x%x" % packet.get("caller_after_3d01b0_frame_libcp_va")
            if packet.get("caller_after_3d01b0_frame_libcp_va") is not None
            else "caller=None",
            "slot=0x%x"
            % packet.get("active_callable_packet", {}).get(
                "active_callable_slot_0x30_libcp_va"
            )
            if packet.get("active_callable_packet", {}).get(
                "active_callable_slot_0x30_libcp_va"
            )
            is not None
            else "slot=None",
            "ctxdest_shape=%sx%s"
            % (
                packet.get("context_dest_descriptor_packet", {}).get("width_0x10"),
                packet.get("context_dest_descriptor_packet", {}).get("height_0x14"),
            ),
            "roi=%s" % packet.get("requested_roi_i32_quad_from_parent_r12"),
        ]
    )


def _disable_branch_breakpoints(target, state):
    setup = state.get("setup") or {}
    branch_ids = {
        entry.get("id") for entry in setup.get("branch_breakpoints", []) if entry
    }
    for bp in target.breakpoint_iter():
        if bp.GetID() in branch_ids:
            bp.SetEnabled(False)


def handoff_branch_cb(frame, bp_loc, extra_args, internal_dict):
    state = _state()
    counts = state["counts"]
    counts["total_branch_hits"] += 1

    setup = state.get("setup")
    if not setup:
        counts["rejected_before_setup"] += 1
        return False

    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    rbp = _u(frame, "rbp")
    source_pair_addr = rbp - 0x30
    source_owner = _ptr(process, source_pair_addr)
    if source_owner != setup.get("owner_from_wrapper"):
        counts["rejected_source_owner_mismatch"] += 1
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

    caller_va = None
    caller_rbp = None
    if parent_index is not None and parent_index + 1 < thread.GetNumFrames():
        caller_frame = thread.GetFrameAtIndex(parent_index + 1)
        caller_va = _module_va(target, caller_frame.GetPC())
        caller_rbp = _u(caller_frame, "rbp")

    stop_va = _module_va(target, _u(frame, "rip"))
    branch = (
        "active_callable_then_3d4e10"
        if stop_va == BRANCH_ACTIVE_CALLABLE
        else "direct_3d4e10"
    )
    active_packet = _active_callable_packet(process, target, rbx)
    parent_roi_ptr = _ptr(process, parent_rbp - 0x100) if parent_rbp is not None else None

    packet = {
        "sequence": counts["accepted_hits"],
        "rip": _u(frame, "rip"),
        "libcp_va": stop_va,
        "branch": branch,
        "thread_id": thread.GetThreadID(),
        "worker_rbp": rbp,
        "source_pair_addr": source_pair_addr,
        "source_owner_from_pair": source_owner,
        "source_owner_matches_setup_owner": source_owner
        == setup.get("owner_from_wrapper"),
        "source_pair_descriptor_packet": _descriptor_summary(process, source_pair_addr),
        "closure_shifted_r14": r14,
        "rbx_source_context": rbx,
        "output_context_from_closure_plus_0x10": output_context,
        "context_qword_00": _u64(context_data, 0x00),
        "context_qword_08": _u64(context_data, 0x08),
        "context_dest_descriptor_ptr_0x10": context_dest_desc,
        "context_dest_descriptor_packet": _descriptor_summary(
            process, context_dest_desc
        ),
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
        "requested_roi_i32_quad_from_parent_r12": _i32_quad(process, parent_roi_ptr)
        if parent_roi_ptr
        else None,
        "stack": _stack(thread),
    }

    counts["accepted_hits"] += 1
    _inc(counts["branch_counts"], branch)
    _inc(counts["caller_counts"], caller_va)
    _inc(
        counts["slot_counts"],
        active_packet.get("active_callable_slot_0x30_libcp_va"),
    )
    _inc(counts["branch_caller_counts"], "%s|%s" % (branch, caller_va))

    key = _packet_key(packet)
    state["unique_keys"][key] = state["unique_keys"].get(key, 0) + 1
    if state["unique_keys"][key] == 1:
        state["unique_packets"].append(packet)
    if len(state["accepted_packets"]) < state["limit"]:
        state["accepted_packets"].append(packet)

    if counts["accepted_hits"] >= state["limit"]:
        state["cap_reached"] = True
        _disable_branch_breakpoints(target, state)
        return True
    return False


def attach_setup_breakpoint(debugger):
    target = debugger.GetSelectedTarget()
    count = target.GetNumBreakpoints()
    if count == 0:
        print("L16_OWNER_F0_ROUTE_CENSUS attach error: expected setup breakpoint")
        return
    setup_bp = target.GetBreakpointAtIndex(count - 1)
    setup_bp.SetScriptCallbackFunction("owner_f0_route_census_probe.setup_cb")
    print("L16_OWNER_F0_ROUTE_CENSUS attached setup callback", setup_bp.GetID())


def drive_until_census_or_exit(debugger, max_steps=256):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while (
        process.IsValid()
        and process.GetState() == lldb.eStateStopped
        and not _state().get("cap_reached")
        and steps < max_steps
    ):
        steps += 1
        process.Continue()
    print("L16_OWNER_F0_ROUTE_CENSUS_DRIVE_STEPS", steps)


def _payload(label):
    state = _state()
    return {
        "label": label,
        "limit": state["limit"],
        "setup_packet": state["setup"],
        "counts": state["counts"],
        "cap_reached": state["cap_reached"],
        "unique_key_hit_counts": state["unique_keys"],
        "unique_packets": state["unique_packets"],
        "accepted_packets_sample": state["accepted_packets"],
    }


def report(label):
    print("L16_OWNER_F0_ROUTE_CENSUS_BEGIN", label)
    print(json.dumps(_payload(label), indent=2, sort_keys=True))
    print("L16_OWNER_F0_ROUTE_CENSUS_END", label)


def write_report(label, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(_payload(label), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_OWNER_F0_ROUTE_CENSUS_WROTE", path)


def reset_direct_post():
    builtins.l16_owner_f0_direct_post = {
        "setup": None,
        "direct_handoff": None,
        "post_packet": None,
        "counts": {
            "total_branch_hits": 0,
            "accepted_direct_hits": 0,
            "rejected_before_setup": 0,
            "rejected_non_direct_branch": 0,
            "rejected_source_owner_mismatch": 0,
        },
    }


def _direct_state():
    if not hasattr(builtins, "l16_owner_f0_direct_post"):
        reset_direct_post()
    return builtins.l16_owner_f0_direct_post


def _install_direct_branch_breakpoints(target):
    base = _libcp_base(target)
    if base is None:
        return []
    ids = []
    for va in (BRANCH_ACTIVE_CALLABLE, BRANCH_DIRECT):
        bp = target.BreakpointCreateByAddress(base + va)
        bp.SetScriptCallbackFunction(
            "owner_f0_route_census_probe.direct_post_handoff_cb"
        )
        ids.append({"id": bp.GetID(), "libcp_va": va, "load_address": base + va})
    return ids


def direct_post_setup_cb(frame, bp_loc, extra_args, internal_dict):
    state = _direct_state()
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    r14 = _u(frame, "r14")

    owner_data = _read(process, r14, 8) if r14 else None
    owner = _u64(owner_data) if owner_data else None
    owner_desc_addr = owner + 0xF0 if owner else None
    owner_desc = _descriptor(process, owner_desc_addr, 16) if owner_desc_addr else None

    state["setup"] = {
        "stop_rip": _u(frame, "rip"),
        "stop_libcp_va": _module_va(target, _u(frame, "rip")),
        "r14_output_wrapper": r14,
        "owner_from_wrapper": owner,
        "owner_plus_0xf0_descriptor": owner_desc_addr,
        "owner_plus_0xf0_descriptor_packet": owner_desc,
        "owner_plus_0xf0_data_ptr": owner_desc.get("data_ptr_0x20")
        if owner_desc
        else None,
        "owner_plus_0xf0_data_byte_size_assuming_6_bytes": _descriptor_byte_span(
            owner_desc, 6
        )
        if owner_desc
        else None,
        "branch_breakpoints": _install_direct_branch_breakpoints(target),
    }
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def direct_post_handoff_cb(frame, bp_loc, extra_args, internal_dict):
    state = _direct_state()
    counts = state["counts"]
    counts["total_branch_hits"] += 1

    setup = state.get("setup")
    if not setup:
        counts["rejected_before_setup"] += 1
        return False
    if state.get("direct_handoff") is not None:
        bp_loc.GetBreakpoint().SetEnabled(False)
        return False

    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    stop_va = _module_va(target, _u(frame, "rip"))
    if stop_va != BRANCH_DIRECT:
        counts["rejected_non_direct_branch"] += 1
        return False

    rbp = _u(frame, "rbp")
    source_pair_addr = rbp - 0x30
    source_owner = _ptr(process, source_pair_addr)
    if source_owner != setup.get("owner_from_wrapper"):
        counts["rejected_source_owner_mismatch"] += 1
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

    caller_va = None
    caller_rbp = None
    if parent_index is not None and parent_index + 1 < thread.GetNumFrames():
        caller_frame = thread.GetFrameAtIndex(parent_index + 1)
        caller_va = _module_va(target, caller_frame.GetPC())
        caller_rbp = _u(caller_frame, "rbp")

    parent_roi_ptr = _ptr(process, parent_rbp - 0x100) if parent_rbp is not None else None
    handoff = {
        "rip": _u(frame, "rip"),
        "libcp_va": stop_va,
        "branch": "direct_3d4e10",
        "thread_id": thread.GetThreadID(),
        "worker_rbp": rbp,
        "source_pair_addr": source_pair_addr,
        "source_owner_from_pair": source_owner,
        "source_owner_matches_setup_owner": source_owner
        == setup.get("owner_from_wrapper"),
        "source_pair_descriptor_packet": _descriptor_summary(process, source_pair_addr),
        "closure_shifted_r14": r14,
        "rbx_source_context": rbx,
        "output_context_from_closure_plus_0x10": output_context,
        "context_qword_00": _u64(context_data, 0x00),
        "context_qword_08": _u64(context_data, 0x08),
        "context_dest_descriptor_ptr_0x10": context_dest_desc,
        "context_dest_descriptor_packet": _descriptor_summary(
            process, context_dest_desc
        ),
        "active_callable_packet": _active_callable_packet(process, target, rbx),
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
        "requested_roi_i32_quad_from_parent_r12": _i32_quad(process, parent_roi_ptr)
        if parent_roi_ptr
        else None,
        "stack": _stack(thread),
    }
    state["direct_handoff"] = handoff
    counts["accepted_direct_hits"] += 1

    base = _libcp_base(target)
    if base is not None:
        post_bp = target.BreakpointCreateByAddress(
            base + OWNER_CACHE_RESCALE_CALL_SITE
        )
        post_bp.SetScriptCallbackFunction(
            "owner_f0_route_census_probe.direct_post_owner_cache_cb"
        )
        handoff["owner_cache_rescale_post_breakpoint_id"] = post_bp.GetID()
        handoff["owner_cache_rescale_post_breakpoint_load_address"] = (
            base + OWNER_CACHE_RESCALE_CALL_SITE
        )

    keep_id = handoff.get("owner_cache_rescale_post_breakpoint_id")
    for bp in target.breakpoint_iter():
        if bp.GetID() != keep_id:
            bp.SetEnabled(False)
    return False


def _double_pair(process, addr):
    data = _read(process, addr, 16)
    if data is None:
        return None
    return list(struct.unpack("<dd", data))


def direct_post_owner_cache_cb(frame, bp_loc, extra_args, internal_dict):
    state = _direct_state()
    if state.get("post_packet") is not None:
        bp_loc.GetBreakpoint().SetEnabled(False)
        return True

    handoff = state.get("direct_handoff")
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

    state["post_packet"] = {
        "rip": _u(frame, "rip"),
        "libcp_va": _module_va(target, _u(frame, "rip")),
        "post_route": "direct_branch_owner_cache_rescale_call_36f800",
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


def attach_direct_post_setup_breakpoint(debugger):
    target = debugger.GetSelectedTarget()
    count = target.GetNumBreakpoints()
    if count == 0:
        print("L16_OWNER_F0_DIRECT_POST attach error: expected setup breakpoint")
        return
    setup_bp = target.GetBreakpointAtIndex(count - 1)
    setup_bp.SetScriptCallbackFunction("owner_f0_route_census_probe.direct_post_setup_cb")
    print("L16_OWNER_F0_DIRECT_POST attached setup callback", setup_bp.GetID())


def drive_until_direct_post_or_exit(debugger, max_steps=256):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while (
        process.IsValid()
        and process.GetState() == lldb.eStateStopped
        and _direct_state().get("post_packet") is None
        and steps < max_steps
    ):
        steps += 1
        process.Continue()
    print("L16_OWNER_F0_DIRECT_POST_DRIVE_STEPS", steps)


def _direct_payload(label):
    state = _direct_state()
    return {
        "label": label,
        "setup_packet": state["setup"],
        "counts": state["counts"],
        "direct_handoff_packet": state["direct_handoff"],
        "post_packet": state["post_packet"],
    }


def direct_post_report(label):
    print("L16_OWNER_F0_DIRECT_POST_BEGIN", label)
    print(json.dumps(_direct_payload(label), indent=2, sort_keys=True))
    print("L16_OWNER_F0_DIRECT_POST_END", label)


def direct_post_write_report(label, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(_direct_payload(label), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_OWNER_F0_DIRECT_POST_WROTE", path)


def reset_global_route_census(sample_limit=256):
    builtins.l16_owner_f0_global_route_census = {
        "sample_limit": sample_limit,
        "branch_breakpoints": [],
        "sample_packets": [],
        "unique_packets": [],
        "unique_keys": {},
        "counts": {
            "total_branch_hits": 0,
            "branch_counts": {},
            "caller_counts": {},
            "slot_counts": {},
            "branch_caller_slot_counts": {},
            "caller_parent_chain_counts": {},
            "full_stack_prefix_counts": {},
            "context_dest_shape_counts": {},
            "source_owner_counts": {},
            "context_equality_counts": {},
            "read_error_counts": {},
        },
        "sample_cap_reached": False,
        "unique_packet_cap_reached": False,
    }


def _global_state():
    if not hasattr(builtins, "l16_owner_f0_global_route_census"):
        reset_global_route_census()
    return builtins.l16_owner_f0_global_route_census


def _hex_or_none(value):
    return "None" if value is None else "0x%x" % value


def _shape_key(desc):
    if not desc or desc.get("error"):
        return "unreadable"
    return "%sx%s stride %s" % (
        desc.get("width_0x10"),
        desc.get("height_0x14"),
        desc.get("stride_0x18"),
    )


def _stack_va_label(va):
    if va is None:
        return "None"
    # _module_va is only meaningful for PCs inside libcp. External frames can
    # produce huge positive deltas, so keep stack signatures explicitly bounded.
    if va < 0 or va >= 0x700000:
        return "external"
    return "0x%x" % va


def _stack_prefix_key(packet, limit=12):
    stack = packet.get("stack") or []
    return " > ".join(_stack_va_label(frame.get("libcp_va")) for frame in stack[:limit])


def _caller_parent_chain_key(packet, limit=8):
    caller = packet.get("caller_after_3d01b0_frame_libcp_va")
    stack = packet.get("stack") or []
    tail = []
    seen_caller = False
    for frame in stack:
        va = frame.get("libcp_va")
        if va == caller:
            seen_caller = True
            continue
        if not seen_caller:
            continue
        label = _stack_va_label(va)
        tail.append(label)
        if label == "external" or len(tail) >= limit:
            break
    active = packet.get("active_callable_packet") or {}
    return "|".join(
        [
            "branch=%s" % packet.get("branch"),
            "caller=%s" % _hex_or_none(caller),
            "slot=%s"
            % _hex_or_none(active.get("active_callable_slot_0x30_libcp_va")),
            "parent_chain=%s" % (" > ".join(tail) if tail else "None"),
        ]
    )


def _global_packet_key(packet):
    active = packet.get("active_callable_packet") or {}
    return "|".join(
        [
            "branch=%s" % packet.get("branch"),
            "caller=%s"
            % _hex_or_none(packet.get("caller_after_3d01b0_frame_libcp_va")),
            "slot=%s"
            % _hex_or_none(active.get("active_callable_slot_0x30_libcp_va")),
            "shape=%s" % _shape_key(packet.get("context_dest_descriptor_packet")),
            "checks=%s/%s/%s"
            % (
                packet.get("output_context_matches_parent_context_addr"),
                packet.get("context_dest_matches_parent_output_local"),
                packet.get("parent_context_dest_matches_context_dest"),
            ),
            "source_owner=%s" % _hex_or_none(packet.get("source_owner_from_pair")),
        ]
    )


def _global_process_packet(frame):
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    thread = frame.GetThread()
    rbp = _u(frame, "rbp")
    r14 = _u(frame, "r14")
    rbx = _u(frame, "rbx")
    stop_va = _module_va(target, _u(frame, "rip"))
    branch = (
        "active_callable_then_3d4e10"
        if stop_va == BRANCH_ACTIVE_CALLABLE
        else "direct_3d4e10"
    )

    source_pair_addr = rbp - 0x30 if rbp else None
    source_owner = _ptr(process, source_pair_addr) if source_pair_addr else None
    output_context = _ptr(process, r14 + 0x10) if r14 else None
    context_data = _read(process, output_context, 0x18) if output_context else None
    context_dest_desc = _u64(context_data, 0x10) if context_data else None

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

    caller_va = None
    caller_rbp = None
    if parent_index is not None and parent_index + 1 < thread.GetNumFrames():
        caller_frame = thread.GetFrameAtIndex(parent_index + 1)
        caller_va = _module_va(target, caller_frame.GetPC())
        caller_rbp = _u(caller_frame, "rbp")

    parent_roi_ptr = (
        _ptr(process, parent_rbp - 0x100) if parent_rbp is not None else None
    )
    active_packet = _active_callable_packet(process, target, rbx)
    context_dest_packet = (
        _descriptor_summary(process, context_dest_desc) if context_dest_desc else None
    )

    return {
        "rip": _u(frame, "rip"),
        "libcp_va": stop_va,
        "branch": branch,
        "thread_id": thread.GetThreadID(),
        "worker_rbp": rbp,
        "source_pair_addr": source_pair_addr,
        "source_owner_from_pair": source_owner,
        "closure_shifted_r14": r14,
        "rbx_source_context": rbx,
        "output_context_from_closure_plus_0x10": output_context,
        "context_read_ok": context_data is not None,
        "context_qword_00": _u64(context_data, 0x00) if context_data else None,
        "context_qword_08": _u64(context_data, 0x08) if context_data else None,
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
        "requested_roi_i32_quad_from_parent_r12": _i32_quad(process, parent_roi_ptr)
        if parent_roi_ptr
        else None,
        "stack": _stack(thread),
    }


def global_route_branch_cb(frame, bp_loc, extra_args, internal_dict):
    state = _global_state()
    counts = state["counts"]
    counts["total_branch_hits"] += 1
    packet = _global_process_packet(frame)
    packet["sequence"] = counts["total_branch_hits"] - 1

    active = packet.get("active_callable_packet") or {}
    _inc(counts["branch_counts"], packet.get("branch"))
    _inc(counts["caller_counts"], packet.get("caller_after_3d01b0_frame_libcp_va"))
    _inc(counts["slot_counts"], active.get("active_callable_slot_0x30_libcp_va"))
    _inc(
        counts["branch_caller_slot_counts"],
        "%s|caller=%s|slot=%s"
        % (
            packet.get("branch"),
            _hex_or_none(packet.get("caller_after_3d01b0_frame_libcp_va")),
            _hex_or_none(active.get("active_callable_slot_0x30_libcp_va")),
        ),
    )
    _inc(counts["caller_parent_chain_counts"], _caller_parent_chain_key(packet))
    _inc(counts["full_stack_prefix_counts"], _stack_prefix_key(packet))
    _inc(
        counts["context_dest_shape_counts"],
        _shape_key(packet.get("context_dest_descriptor_packet")),
    )
    _inc(
        counts["source_owner_counts"],
        _hex_or_none(packet.get("source_owner_from_pair")),
    )
    _inc(
        counts["context_equality_counts"],
        "%s/%s/%s"
        % (
            packet.get("output_context_matches_parent_context_addr"),
            packet.get("context_dest_matches_parent_output_local"),
            packet.get("parent_context_dest_matches_context_dest"),
        ),
    )
    if not packet.get("context_read_ok"):
        _inc(counts["read_error_counts"], "context")
    if not packet.get("context_dest_descriptor_packet"):
        _inc(counts["read_error_counts"], "context_dest_descriptor")

    limit = state["sample_limit"]
    if len(state["sample_packets"]) < limit:
        state["sample_packets"].append(packet)
    else:
        state["sample_cap_reached"] = True

    key = _global_packet_key(packet)
    state["unique_keys"][key] = state["unique_keys"].get(key, 0) + 1
    if state["unique_keys"][key] == 1:
        if len(state["unique_packets"]) < limit:
            state["unique_packets"].append(packet)
        else:
            state["unique_packet_cap_reached"] = True
    return False


def attach_global_route_breakpoints(debugger):
    target = debugger.GetSelectedTarget()
    count = target.GetNumBreakpoints()
    if count >= 2:
        state = _global_state()
        state["branch_breakpoints"] = []
        for index, va in zip(
            range(count - 2, count), (BRANCH_ACTIVE_CALLABLE, BRANCH_DIRECT)
        ):
            bp = target.GetBreakpointAtIndex(index)
            bp.SetScriptCallbackFunction(
                "owner_f0_route_census_probe.global_route_branch_cb"
            )
            state["branch_breakpoints"].append(
                {"id": bp.GetID(), "libcp_va": va, "load_address": None}
            )
        print(
            "L16_OWNER_F0_GLOBAL_ROUTE_CENSUS attached pending branch callbacks",
            state["branch_breakpoints"],
        )
        return

    base = _libcp_base(target)
    if base is None:
        print("L16_OWNER_F0_GLOBAL_ROUTE_CENSUS attach error: no libcp base")
        return

    state = _global_state()
    state["branch_breakpoints"] = []
    for va in (BRANCH_ACTIVE_CALLABLE, BRANCH_DIRECT):
        bp = target.BreakpointCreateByAddress(base + va)
        bp.SetScriptCallbackFunction(
            "owner_f0_route_census_probe.global_route_branch_cb"
        )
        state["branch_breakpoints"].append(
            {"id": bp.GetID(), "libcp_va": va, "load_address": base + va}
        )
    print(
        "L16_OWNER_F0_GLOBAL_ROUTE_CENSUS attached branch callbacks",
        state["branch_breakpoints"],
    )


def drive_until_global_route_exit(debugger, max_steps=256):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while (
        process.IsValid()
        and process.GetState() == lldb.eStateStopped
        and steps < max_steps
    ):
        steps += 1
        process.Continue()
    print("L16_OWNER_F0_GLOBAL_ROUTE_CENSUS_DRIVE_STEPS", steps)


def _process_packet(debugger):
    if debugger is None:
        return None
    process = debugger.GetSelectedTarget().GetProcess()
    if not process.IsValid():
        return {"valid": False}
    return {
        "valid": True,
        "state": process.GetState(),
        "exit_status": process.GetExitStatus(),
        "exit_description": process.GetExitDescription(),
    }


def _global_payload(label, debugger=None):
    state = _global_state()
    return {
        "label": label,
        "sample_limit": state["sample_limit"],
        "branch_breakpoints": state["branch_breakpoints"],
        "counts": state["counts"],
        "sample_cap_reached": state["sample_cap_reached"],
        "unique_packet_cap_reached": state["unique_packet_cap_reached"],
        "unique_key_hit_counts": state["unique_keys"],
        "unique_packets": state["unique_packets"],
        "sample_packets": state["sample_packets"],
        "process": _process_packet(debugger),
    }


def global_route_report(label, debugger=None):
    print("L16_OWNER_F0_GLOBAL_ROUTE_CENSUS_BEGIN", label)
    print(json.dumps(_global_payload(label, debugger), indent=2, sort_keys=True))
    print("L16_OWNER_F0_GLOBAL_ROUTE_CENSUS_END", label)


def global_route_write_report(label, path, debugger=None):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(_global_payload(label, debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_OWNER_F0_GLOBAL_ROUTE_CENSUS_WROTE", path)


def reset_global_post_family():
    builtins.l16_owner_f0_global_post_family = {
        "branch_breakpoints": [],
        "counts": {
            "total_branch_hits": 0,
            "target_family_branch_hits": 0,
            "ignored_non_target_caller": 0,
            "post_breakpoint_hits": 0,
        },
        "families": {
            "exact_size_3d0732": {
                "caller_libcp_va": CALLER_EXACT_SIZE,
                "handoff_packet": None,
                "post_packet": None,
                "complete": False,
            },
            "owner_cache_rescale_3d084d": {
                "caller_libcp_va": CALLER_OWNER_CACHE_RESCALE,
                "handoff_packet": None,
                "post_packet": None,
                "complete": False,
            },
            "visible_src1_3ecc5a": {
                "caller_libcp_va": CALLER_VISIBLE_SRC1,
                "handoff_packet": None,
                "post_packet": None,
                "complete": False,
            },
        },
    }


def _post_family_state():
    if not hasattr(builtins, "l16_owner_f0_global_post_family"):
        reset_global_post_family()
    return builtins.l16_owner_f0_global_post_family


def _post_family_key(caller_va):
    if caller_va == CALLER_EXACT_SIZE:
        return "exact_size_3d0732"
    if caller_va == CALLER_OWNER_CACHE_RESCALE:
        return "owner_cache_rescale_3d084d"
    if caller_va == CALLER_VISIBLE_SRC1:
        return "visible_src1_3ecc5a"
    return None


def _post_family_all_complete(state=None):
    state = state or _post_family_state()
    return all(entry.get("complete") for entry in state["families"].values())


def _install_global_post_breakpoint(target, va, callback_name):
    base = _libcp_base(target)
    if base is None:
        return None
    bp = target.BreakpointCreateByAddress(base + va)
    bp.SetScriptCallbackFunction(callback_name)
    return {"id": bp.GetID(), "libcp_va": va, "load_address": base + va}


def global_post_family_branch_cb(frame, bp_loc, extra_args, internal_dict):
    state = _post_family_state()
    state["counts"]["total_branch_hits"] += 1
    packet = _global_process_packet(frame)
    caller_va = packet.get("caller_after_3d01b0_frame_libcp_va")
    key = _post_family_key(caller_va)
    if key is None:
        state["counts"]["ignored_non_target_caller"] += 1
        return False

    family = state["families"][key]
    if family.get("handoff_packet") is not None:
        return _post_family_all_complete(state)

    state["counts"]["target_family_branch_hits"] += 1
    family["handoff_packet"] = packet

    target = frame.GetThread().GetProcess().GetTarget()
    if key == "exact_size_3d0732":
        family["post_packet"] = {
            "post_route": "exact_size_path_no_post_call_after_3d01b0",
            "static_basis": "caller 0x3d0732 is the instruction after call 0x3d072d to 0x3d01b0 and immediately jumps to 0x3d08dc cleanup",
            "caller_after_3d01b0_frame_libcp_va": caller_va,
            "thread_id": frame.GetThread().GetThreadID(),
            "context_dest_descriptor_ptr_0x10": packet.get(
                "context_dest_descriptor_ptr_0x10"
            ),
            "context_dest_descriptor_packet": packet.get(
                "context_dest_descriptor_packet"
            ),
        }
        family["complete"] = True
    elif key == "owner_cache_rescale_3d084d":
        family["post_breakpoint"] = _install_global_post_breakpoint(
            target,
            OWNER_CACHE_RESCALE_CALL_SITE,
            "owner_f0_route_census_probe.global_post_owner_cache_cb",
        )
    elif key == "visible_src1_3ecc5a":
        family["post_breakpoint"] = _install_global_post_breakpoint(
            target,
            VISIBLE_SRC1_POST_READ_SITE,
            "owner_f0_route_census_probe.global_post_visible_src1_cb",
        )
    return _post_family_all_complete(state)


def global_post_owner_cache_cb(frame, bp_loc, extra_args, internal_dict):
    state = _post_family_state()
    state["counts"]["post_breakpoint_hits"] += 1
    family = state["families"]["owner_cache_rescale_3d084d"]
    handoff = family.get("handoff_packet")
    if not handoff or family.get("complete"):
        bp_loc.GetBreakpoint().SetEnabled(False)
        return _post_family_all_complete(state)

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
    family["post_packet"] = {
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
    family["complete"] = True
    bp_loc.GetBreakpoint().SetEnabled(False)
    return _post_family_all_complete(state)


def global_post_visible_src1_cb(frame, bp_loc, extra_args, internal_dict):
    state = _post_family_state()
    state["counts"]["post_breakpoint_hits"] += 1
    family = state["families"]["visible_src1_3ecc5a"]
    handoff = family.get("handoff_packet")
    if not handoff or family.get("complete"):
        bp_loc.GetBreakpoint().SetEnabled(False)
        return _post_family_all_complete(state)

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

    family["post_packet"] = {
        "rip": _u(frame, "rip"),
        "libcp_va": _module_va(target, _u(frame, "rip")),
        "post_route": "visible_src1_call_3edb80",
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
    family["complete"] = True
    bp_loc.GetBreakpoint().SetEnabled(False)
    return _post_family_all_complete(state)


def attach_global_post_family_breakpoints(debugger):
    target = debugger.GetSelectedTarget()
    count = target.GetNumBreakpoints()
    if count >= 2:
        state = _post_family_state()
        state["branch_breakpoints"] = []
        for index, va in zip(
            range(count - 2, count), (BRANCH_ACTIVE_CALLABLE, BRANCH_DIRECT)
        ):
            bp = target.GetBreakpointAtIndex(index)
            bp.SetScriptCallbackFunction(
                "owner_f0_route_census_probe.global_post_family_branch_cb"
            )
            state["branch_breakpoints"].append(
                {"id": bp.GetID(), "libcp_va": va, "load_address": None}
            )
        print(
            "L16_OWNER_F0_GLOBAL_POST_FAMILY attached pending branch callbacks",
            state["branch_breakpoints"],
        )
        return

    base = _libcp_base(target)
    if base is None:
        print("L16_OWNER_F0_GLOBAL_POST_FAMILY attach error: no libcp base")
        return

    state = _post_family_state()
    state["branch_breakpoints"] = []
    for va in (BRANCH_ACTIVE_CALLABLE, BRANCH_DIRECT):
        bp = target.BreakpointCreateByAddress(base + va)
        bp.SetScriptCallbackFunction(
            "owner_f0_route_census_probe.global_post_family_branch_cb"
        )
        state["branch_breakpoints"].append(
            {"id": bp.GetID(), "libcp_va": va, "load_address": base + va}
        )
    print(
        "L16_OWNER_F0_GLOBAL_POST_FAMILY attached branch callbacks",
        state["branch_breakpoints"],
    )


def drive_until_global_post_family_or_exit(debugger, max_steps=256):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while (
        process.IsValid()
        and process.GetState() == lldb.eStateStopped
        and not _post_family_all_complete()
        and steps < max_steps
    ):
        steps += 1
        process.Continue()
    print("L16_OWNER_F0_GLOBAL_POST_FAMILY_DRIVE_STEPS", steps)


def _global_post_family_payload(label, debugger=None):
    state = _post_family_state()
    return {
        "label": label,
        "branch_breakpoints": state["branch_breakpoints"],
        "counts": state["counts"],
        "all_complete": _post_family_all_complete(state),
        "families": state["families"],
        "process": _process_packet(debugger),
    }


def global_post_family_report(label, debugger=None):
    print("L16_OWNER_F0_GLOBAL_POST_FAMILY_BEGIN", label)
    print(
        json.dumps(
            _global_post_family_payload(label, debugger), indent=2, sort_keys=True
        )
    )
    print("L16_OWNER_F0_GLOBAL_POST_FAMILY_END", label)


def global_post_family_write_report(label, path, debugger=None):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(
            _global_post_family_payload(label, debugger), handle, indent=2, sort_keys=True
        )
        handle.write("\n")
    print("L16_OWNER_F0_GLOBAL_POST_FAMILY_WROTE", path)
