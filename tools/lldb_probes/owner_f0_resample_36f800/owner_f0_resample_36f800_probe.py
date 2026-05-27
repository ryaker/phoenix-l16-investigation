import builtins
import json
import struct


RESAMPLE_SETUP_CALL_SITE = 0x36FB1F
RESAMPLE_RETURN_SITE = 0x36FB24
SELECTED_CACHE_RESCALE_RETURN = 0x3D08D3
OWNER_F0_SINK_SETUP_SITE = 0x3ECAC3
OWNER_CACHE_RESCALE_CALL_SITE = 0x3D08CE
CALLABLE_THUNK_SITE = 0x3721D0
WORKER_ENTRY_AFTER_PROLOGUE = 0x372224
WORKER_FIRST_STORE_AFTER = 0x372488
ROW_PLAN_RETURN_SITE = 0x3722B0
ROW_FILL_CALL_SITE = 0x372395
ROW_FILL_RETURN_SITE = 0x37239A
ROW_FILL_STORE_AFTER_SITES = (0x372898, 0x372911, 0x3729E0)
GLOBAL_ROWCACHE_PLAN_SAMPLE_LIMIT = 16


def reset():
    builtins.l16_resample_36f800_route_owner_setup = None
    builtins.l16_resample_36f800_route_handoff = None
    builtins.l16_resample_36f800_route_rescale_call = None
    builtins.l16_resample_36f800_setup = None
    builtins.l16_resample_36f800_thunk = None
    builtins.l16_resample_36f800_worker_entry = None
    builtins.l16_resample_36f800_row_plan = None
    builtins.l16_resample_36f800_worker_row_plans = []
    builtins.l16_resample_36f800_worker_row_plan_keys = set()
    builtins.l16_resample_36f800_row_fill_call = None
    builtins.l16_resample_36f800_row_fill_store = None
    builtins.l16_resample_36f800_row_fill_store_counts = {}
    builtins.l16_resample_36f800_row_fill_store_segments = {}
    builtins.l16_resample_36f800_row_fill_return = None
    builtins.l16_resample_36f800_first_store = None
    builtins.l16_resample_36f800_return = None


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


def _f64s(data):
    return list(struct.unpack("<" + "d" * (len(data) // 8), data))


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


def _ptr(process, addr):
    data = _read(process, addr, 8)
    return _u64(data) if data else None


def _i32_quad(process, addr):
    data = _read(process, addr, 16)
    if data is None:
        return None
    return list(struct.unpack("<iiii", data))


def _i32s(process, addr, count):
    data = _read(process, addr, 4 * count)
    if data is None:
        return None
    return list(struct.unpack("<" + "i" * count, data))


def _s32(value):
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def _double_pair(process, addr):
    data = _read(process, addr, 16)
    return _f64s(data) if data is not None else None


def _vec4(process, addr):
    data = _read(process, addr, 16)
    return _f32s(data) if data is not None else None


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


def _row_plan(process, addr):
    data = _read(process, addr, 0x60)
    if data is None:
        return {"addr": addr, "error": "failed to read row plan"}
    source_desc = _u64(data, 0x38)
    weight_table = _u64(data, 0x58)
    return {
        "addr": addr,
        "i32_00_1c": list(struct.unpack_from("<iiiiiiii", data, 0x00)),
        "qword_20_capacity_bytes": _u64(data, 0x20),
        "qword_28_current_row_ptr": _u64(data, 0x28),
        "qword_30_buffer_ptr": _u64(data, 0x30),
        "source_descriptor_ptr_0x38": source_desc,
        "source_descriptor_packet": _descriptor(process, source_desc, 16),
        "scale_x_fixed_0x40": _i32(data, 0x40),
        "scale_y_fixed_0x44": _i32(data, 0x44),
        "start_x_fixed_0x48": _i32(data, 0x48),
        "end_x_fixed_0x4c": _i32(data, 0x4C),
        "clamped_lower_fixed_0x50": _i32(data, 0x50),
        "clamped_upper_fixed_0x54": _i32(data, 0x54),
        "weight_table_ptr_0x58": weight_table,
        "weight_table_first_four_vec4": [
            _vec4(process, weight_table + index * 16) if weight_table else None
            for index in range(4)
        ],
    }


def _ceil_div_positive(numerator, denominator):
    if denominator <= 0 or numerator <= 0:
        return 0
    return (numerator + denominator - 1) // denominator


def _segment_counts_from_plan(plan):
    if plan is None or plan.get("error"):
        return None
    step = plan.get("scale_x_fixed_0x40")
    start = plan.get("start_x_fixed_0x48")
    end = plan.get("end_x_fixed_0x4c")
    lower = plan.get("clamped_lower_fixed_0x50")
    upper = plan.get("clamped_upper_fixed_0x54")
    if None in (step, start, end, lower, upper) or step <= 0:
        return None
    current = start
    leading = _ceil_div_positive(lower - current, step)
    current += leading * step
    middle = _ceil_div_positive(upper - current, step)
    current += middle * step
    trailing = _ceil_div_positive(end - current, step)
    return {
        "leading_segment_store": leading,
        "middle_segment_store": middle,
        "trailing_segment_store": trailing,
        "total": leading + middle + trailing,
    }


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


def _find_3d01b0_frame(thread):
    target = thread.GetProcess().GetTarget()
    for i in range(thread.GetNumFrames()):
        frame = thread.GetFrameAtIndex(i)
        va = _module_va(target, frame.GetPC())
        if va is not None and 0x3D01B0 <= va < 0x3D0650:
            return i, frame, va
    return None, None, None


def _install_follow_breakpoint(target, va, callback):
    base = _libcp_base(target)
    if base is None:
        return None
    bp = target.BreakpointCreateByAddress(base + va)
    bp.SetScriptCallbackFunction(callback)
    return {"id": bp.GetID(), "libcp_va": va, "load_address": base + va}


def _disable_breakpoints_except(target, keep_ids):
    keep = {value for value in keep_ids if value is not None}
    for bp in target.breakpoint_iter():
        if bp.GetID() not in keep:
            bp.SetEnabled(False)


def owner_setup_cb(frame, bp_loc, extra_args, internal_dict):
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    r14 = _u(frame, "r14")

    owner_data = _read(process, r14, 8) if r14 else None
    owner = _u64(owner_data) if owner_data else None
    owner_desc_addr = owner + 0xF0 if owner else None
    owner_desc = _descriptor(process, owner_desc_addr, 16) if owner_desc_addr else None

    branch_breakpoints = []
    for va in (0x3D4842, 0x3D4864):
        bp = _install_follow_breakpoint(
            target, va, "owner_f0_resample_36f800_probe.handoff_branch_cb"
        )
        if bp is not None:
            branch_breakpoints.append(bp)

    builtins.l16_resample_36f800_route_owner_setup = {
        "rip": _u(frame, "rip"),
        "libcp_va": _module_va(target, _u(frame, "rip")),
        "r14_output_wrapper": r14,
        "owner_from_wrapper": owner,
        "owner_plus_0xf0_descriptor": owner_desc_addr,
        "owner_plus_0xf0_descriptor_packet": owner_desc,
        "branch_breakpoints": branch_breakpoints,
        "stack": _stack(frame.GetThread()),
    }
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def handoff_branch_cb(frame, bp_loc, extra_args, internal_dict):
    if builtins.l16_resample_36f800_route_handoff is not None:
        bp_loc.GetBreakpoint().SetEnabled(False)
        return False

    owner_setup = builtins.l16_resample_36f800_route_owner_setup
    if not owner_setup:
        return False

    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    rbp = _u(frame, "rbp")
    source_pair_addr = rbp - 0x30
    source_owner = _ptr(process, source_pair_addr)
    if source_owner != owner_setup.get("owner_from_wrapper"):
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
    caller_frame = None
    caller_va = None
    caller_rbp = None
    if parent_index is not None and parent_index + 1 < thread.GetNumFrames():
        caller_frame = thread.GetFrameAtIndex(parent_index + 1)
        caller_va = _module_va(target, caller_frame.GetPC())
        caller_rbp = _u(caller_frame, "rbp")

    if caller_va != 0x3D084D:
        return False

    active = _ptr(process, rbx + 0x70) if rbx else None
    vtable = _ptr(process, active) if active else None
    active_slot_0x30 = _ptr(process, vtable + 0x30) if vtable else None

    rescale_bp = _install_follow_breakpoint(
        target,
        OWNER_CACHE_RESCALE_CALL_SITE,
        "owner_f0_resample_36f800_probe.owner_cache_rescale_call_cb",
    )

    builtins.l16_resample_36f800_route_handoff = {
        "rip": _u(frame, "rip"),
        "libcp_va": _module_va(target, _u(frame, "rip")),
        "branch": "active_callable_then_3d4e10"
        if _module_va(target, _u(frame, "rip")) == 0x3D4842
        else "direct_3d4e10",
        "thread_id": thread.GetThreadID(),
        "worker_rbp": rbp,
        "source_pair_addr": source_pair_addr,
        "source_owner_from_pair": source_owner,
        "output_context_from_closure_plus_0x10": output_context,
        "context_dest_descriptor_ptr_0x10": context_dest_desc,
        "context_dest_descriptor_packet": _descriptor(process, context_dest_desc, 16),
        "active_callable_slot_0x30": active_slot_0x30,
        "active_callable_slot_0x30_libcp_va": _module_va(target, active_slot_0x30)
        if active_slot_0x30
        else None,
        "parent_3d01b0_frame_index": parent_index,
        "parent_3d01b0_current_libcp_va": parent_va,
        "parent_3d01b0_rbp": parent_rbp,
        "caller_after_3d01b0_frame_libcp_va": caller_va,
        "caller_after_3d01b0_rbp": caller_rbp,
        "rescale_call_breakpoint": rescale_bp,
        "stack": _stack(thread),
    }

    _disable_breakpoints_except(
        target, [rescale_bp["id"] if rescale_bp is not None else None]
    )
    return False


def owner_cache_rescale_call_cb(frame, bp_loc, extra_args, internal_dict):
    if builtins.l16_resample_36f800_route_rescale_call is not None:
        bp_loc.GetBreakpoint().SetEnabled(False)
        return False

    handoff = builtins.l16_resample_36f800_route_handoff
    if not handoff:
        return False

    thread = frame.GetThread()
    if thread.GetThreadID() != handoff.get("thread_id"):
        return False

    process = thread.GetProcess()
    target = process.GetTarget()
    rbp = _u(frame, "rbp")
    source_desc = _u(frame, "rsi")
    if source_desc != handoff.get("context_dest_descriptor_ptr_0x10"):
        return False

    setup_bp = _install_follow_breakpoint(
        target,
        RESAMPLE_SETUP_CALL_SITE,
        "owner_f0_resample_36f800_probe.resample_setup_cb",
    )

    builtins.l16_resample_36f800_route_rescale_call = {
        "rip": _u(frame, "rip"),
        "libcp_va": _module_va(target, _u(frame, "rip")),
        "thread_id": thread.GetThreadID(),
        "owner_cache_rbp": rbp,
        "rdi_dest_descriptor_for_36f800": _u(frame, "rdi"),
        "rsi_source_descriptor_for_36f800": source_desc,
        "rdx_offset_pair_for_36f800": _u(frame, "rdx"),
        "rcx_scale_pair_for_36f800": _u(frame, "rcx"),
        "offset_pair_doubles": _double_pair(process, _u(frame, "rdx")),
        "scale_pair_doubles": _double_pair(process, _u(frame, "rcx")),
        "source_descriptor_packet_before_36f800": _descriptor(
            process, source_desc, 16
        ),
        "dest_descriptor_packet_before_36f800": _descriptor(
            process, _u(frame, "rdi"), 16
        ),
        "resample_setup_breakpoint": setup_bp,
        "stack": _stack(thread),
    }

    _disable_breakpoints_except(
        target, [setup_bp["id"] if setup_bp is not None else None]
    )
    return False


def resample_setup_cb(frame, bp_loc, extra_args, internal_dict):
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()

    route = builtins.l16_resample_36f800_route_rescale_call
    if not route:
        return False

    caller_va = None
    if thread.GetNumFrames() > 1:
        caller_va = _module_va(target, thread.GetFrameAtIndex(1).GetPC())
    if caller_va != SELECTED_CACHE_RESCALE_RETURN:
        return False
    if thread.GetThreadID() != route.get("thread_id"):
        return False

    rbp = _u(frame, "rbp")
    callback_object = _ptr(process, rbp - 0x1040)
    if callback_object is None:
        return False

    vtable = _ptr(process, callback_object)
    vtable_slot_0x30 = _ptr(process, vtable + 0x30) if vtable else None
    source_desc = _ptr(process, callback_object + 0x18)
    dest_desc = _ptr(process, callback_object + 0x28)
    offset_pair = _ptr(process, callback_object + 0x8)
    scale_pair = _ptr(process, callback_object + 0x10)
    if source_desc != route.get("rsi_source_descriptor_for_36f800"):
        return False
    if dest_desc != route.get("rdi_dest_descriptor_for_36f800"):
        return False
    if offset_pair != route.get("rdx_offset_pair_for_36f800"):
        return False
    if scale_pair != route.get("rcx_scale_pair_for_36f800"):
        return False

    weight_table = _ptr(process, callback_object + 0x20)

    follow = {
        "callable_thunk": _install_follow_breakpoint(
            target,
            CALLABLE_THUNK_SITE,
            "owner_f0_resample_36f800_probe.callable_thunk_cb",
        ),
        "worker_entry": _install_follow_breakpoint(
            target,
            WORKER_ENTRY_AFTER_PROLOGUE,
            "owner_f0_resample_36f800_probe.worker_entry_cb",
        ),
        "row_plan": _install_follow_breakpoint(
            target,
            ROW_PLAN_RETURN_SITE,
            "owner_f0_resample_36f800_probe.row_plan_cb",
        ),
        "row_fill_call": _install_follow_breakpoint(
            target,
            ROW_FILL_CALL_SITE,
            "owner_f0_resample_36f800_probe.row_fill_call_cb",
        ),
        "first_store": _install_follow_breakpoint(
            target,
            WORKER_FIRST_STORE_AFTER,
            "owner_f0_resample_36f800_probe.first_store_cb",
        ),
        "return": _install_follow_breakpoint(
            target,
            RESAMPLE_RETURN_SITE,
            "owner_f0_resample_36f800_probe.return_cb",
        ),
    }
    keep_ids = [item["id"] for item in follow.values() if item is not None]

    builtins.l16_resample_36f800_setup = {
        "rip": _u(frame, "rip"),
        "libcp_va": _module_va(target, _u(frame, "rip")),
        "accepted_caller_return_libcp_va": caller_va,
        "thread_id": thread.GetThreadID(),
        "resample_rbp": rbp,
        "callback_dest_descriptor_ptr": dest_desc,
        "callback_source_descriptor_ptr": source_desc,
        "callback_offset_pair_ptr": offset_pair,
        "callback_scale_pair_ptr": scale_pair,
        "offset_pair_doubles": _double_pair(process, offset_pair),
        "scale_pair_doubles": _double_pair(process, scale_pair),
        "source_descriptor_packet": _descriptor(process, source_desc, 16),
        "dest_descriptor_packet_before_dispatch": _descriptor(process, dest_desc, 16),
        "executor_region_i32_quad_rbp_minus_0x1070": _i32_quad(
            process, rbp - 0x1070
        ),
        "executor_shape_i32_quad_rbp_minus_0x1078": _i32_quad(
            process, rbp - 0x1078
        ),
        "callback_wrapper_stack_addr_rbp_minus_0x1060": rbp - 0x1060,
        "callback_object_ptr_rbp_minus_0x1040": callback_object,
        "callback_vtable": vtable,
        "callback_vtable_slot_0x30": vtable_slot_0x30,
        "callback_vtable_slot_0x30_libcp_va": _module_va(target, vtable_slot_0x30)
        if vtable_slot_0x30
        else None,
        "callback_field_0x08_offset_pair_ptr": _ptr(process, callback_object + 0x8),
        "callback_field_0x10_scale_pair_ptr": _ptr(process, callback_object + 0x10),
        "callback_field_0x18_source_descriptor_ptr": _ptr(
            process, callback_object + 0x18
        ),
        "callback_field_0x20_weight_table_ptr": weight_table,
        "callback_field_0x28_dest_descriptor_ptr": _ptr(
            process, callback_object + 0x28
        ),
        "weight_table_first_four_vec4": [
            _vec4(process, weight_table + index * 16) if weight_table else None
            for index in range(4)
        ],
        "follow_breakpoints": follow,
        "stack": _stack(thread),
    }

    _disable_breakpoints_except(target, keep_ids)
    return False


def callable_thunk_cb(frame, bp_loc, extra_args, internal_dict):
    setup = builtins.l16_resample_36f800_setup
    if not setup or builtins.l16_resample_36f800_thunk is not None:
        return False

    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    callback_object = setup.get("callback_object_ptr_rbp_minus_0x1040")
    if _u(frame, "rdi") != callback_object:
        return False

    rdx = _u(frame, "rdx")
    builtins.l16_resample_36f800_thunk = {
        "rip": _u(frame, "rip"),
        "libcp_va": _module_va(target, _u(frame, "rip")),
        "thread_id": frame.GetThread().GetThreadID(),
        "rdi_callback_object": _u(frame, "rdi"),
        "rsi_executor_region": _u(frame, "rsi"),
        "rdx_int_pointer": rdx,
        "rdx_i32_value_loaded_by_thunk": _i32(_read(process, rdx, 4))
        if _read(process, rdx, 4) is not None
        else None,
        "stack": _stack(frame.GetThread()),
    }
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def worker_entry_cb(frame, bp_loc, extra_args, internal_dict):
    setup = builtins.l16_resample_36f800_setup
    if not setup or builtins.l16_resample_36f800_worker_entry is not None:
        return False

    target = frame.GetThread().GetProcess().GetTarget()
    callback_fields = setup.get("callback_object_ptr_rbp_minus_0x1040") + 8
    if _u(frame, "rdi") != callback_fields:
        return False

    builtins.l16_resample_36f800_worker_entry = {
        "rip": _u(frame, "rip"),
        "libcp_va": _module_va(target, _u(frame, "rip")),
        "thread_id": frame.GetThread().GetThreadID(),
        "rdi_callback_fields_object_plus_0x08": _u(frame, "rdi"),
        "rsi_executor_region": _u(frame, "rsi"),
        "rdx_executor_i32_value": _u(frame, "rdx") & 0xFFFFFFFF,
        "stack": _stack(frame.GetThread()),
    }
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def _weighted_sum(sources, weights):
    if any(item is None for item in sources) or any(item is None for item in weights):
        return None
    out = []
    for lane in range(4):
        out.append(sum(sources[i][lane] * weights[i][lane] for i in range(4)))
    return out


def _row_store_prediction(process, plan, fixed_x, source_row_base, weight_table):
    source_desc = plan.get("source_descriptor_ptr_0x38")
    source_head = _read(process, source_desc, 0x10) if source_desc else None
    if source_head is None:
        return None
    min_x = _i32(source_head, 0x00)
    max_x = _i32(source_head, 0x08) - 1
    floor_x = fixed_x >> 16
    frac_index = (fixed_x >> 10) & 0x3F
    source_indices = [
        min(max(candidate, min_x), max_x)
        for candidate in (floor_x - 1, floor_x, floor_x + 1, floor_x + 2)
    ]
    source_ptrs = [source_row_base + index * 16 for index in source_indices]
    weight_ptrs = [weight_table + frac_index * 64 + index * 16 for index in range(4)]
    source_vecs = [_vec4(process, addr) for addr in source_ptrs]
    weight_vecs = [_vec4(process, addr) for addr in weight_ptrs]
    return {
        "fixed_x": fixed_x,
        "floor_x": floor_x,
        "frac_index": frac_index,
        "source_min_x": min_x,
        "source_max_x": max_x,
        "source_indices": source_indices,
        "source_vec_ptrs": source_ptrs,
        "weight_vec_ptrs": weight_ptrs,
        "source_vec4s": source_vecs,
        "weight_vec4s": weight_vecs,
        "predicted_vec4": _weighted_sum(source_vecs, weight_vecs),
    }


def _max_abs_diff(a, b):
    if a is None or b is None:
        return None
    return max(abs(x - y) for x, y in zip(a, b))


def row_plan_cb(frame, bp_loc, extra_args, internal_dict):
    setup = builtins.l16_resample_36f800_setup
    if not setup:
        return False
    thread = frame.GetThread()
    rbp = _u(frame, "rbp")
    process = thread.GetProcess()
    callback_fields = setup.get("callback_object_ptr_rbp_minus_0x1040") + 8
    if _ptr(process, rbp - 0xF8) != callback_fields:
        return False
    target = process.GetTarget()
    plan_addr = rbp - 0xC0
    thunk = builtins.l16_resample_36f800_thunk
    executor_region = _u(frame, "rbx")
    plan_packet = _row_plan(process, plan_addr)
    packet = {
        "rip": _u(frame, "rip"),
        "libcp_va": _module_va(target, _u(frame, "rip")),
        "thread_id": thread.GetThreadID(),
        "worker_rbp": rbp,
        "plan_addr_rbp_minus_0xc0": plan_addr,
        "fixed_offset_pair_i32": _i32s(process, rbp - 0x58, 2),
        "fixed_scale_pair_i32": _i32s(process, rbp - 0x60, 2),
        "executor_region_ptr_rbx": executor_region,
        "executor_region_i32_quad": _i32_quad(process, executor_region),
        "first_thunk_executor_region_i32_quad": _i32_quad(
            process, thunk.get("rsi_executor_region")
        )
        if thunk
        else None,
        "plan_packet_after_372500": plan_packet,
        "predicted_segment_counts_from_plan": _segment_counts_from_plan(
            plan_packet
        ),
        "stack": _stack(thread),
    }
    key = tuple(packet.get("executor_region_i32_quad") or [])
    if key not in builtins.l16_resample_36f800_worker_row_plan_keys:
        builtins.l16_resample_36f800_worker_row_plan_keys.add(key)
        builtins.l16_resample_36f800_worker_row_plans.append(packet)
    if builtins.l16_resample_36f800_row_plan is None:
        builtins.l16_resample_36f800_row_plan = packet
    return False


def row_fill_call_cb(frame, bp_loc, extra_args, internal_dict):
    setup = builtins.l16_resample_36f800_setup
    if not setup or builtins.l16_resample_36f800_row_fill_call is not None:
        return False
    thread = frame.GetThread()
    if thread.GetThreadID() != setup.get("thread_id"):
        return False
    process = thread.GetProcess()
    rbp = _u(frame, "rbp")
    callback_fields = setup.get("callback_object_ptr_rbp_minus_0x1040") + 8
    if _ptr(process, rbp - 0xF8) != callback_fields:
        return False
    target = process.GetTarget()
    plan_addr = rbp - 0xC0
    return_bp = _install_follow_breakpoint(
        target,
        ROW_FILL_RETURN_SITE,
        "owner_f0_resample_36f800_probe.row_fill_return_cb",
    )
    store_bps = [
        _install_follow_breakpoint(
            target,
            va,
            "owner_f0_resample_36f800_probe.row_fill_store_cb",
        )
        for va in ROW_FILL_STORE_AFTER_SITES
    ]
    builtins.l16_resample_36f800_row_fill_call = {
        "rip": _u(frame, "rip"),
        "libcp_va": _module_va(target, _u(frame, "rip")),
        "thread_id": thread.GetThreadID(),
        "worker_rbp": rbp,
        "plan_addr_rbp_minus_0xc0": plan_addr,
        "rdi_plan_arg": _u(frame, "rdi"),
        "rsi_row_cache_arg": _u(frame, "rsi"),
        "rdx_high_word_arg": _u(frame, "rdx") & 0xFFFFFFFF,
        "r8d_source_row_key": _u(frame, "r8") & 0xFFFFFFFF,
        "plan_packet_before_372760": _row_plan(process, plan_addr),
        "return_breakpoint": return_bp,
        "store_breakpoints": store_bps,
        "stack": _stack(thread),
    }
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def row_fill_store_cb(frame, bp_loc, extra_args, internal_dict):
    setup = builtins.l16_resample_36f800_setup
    call = builtins.l16_resample_36f800_row_fill_call
    if not setup or not call:
        return False
    thread = frame.GetThread()
    if thread.GetThreadID() != setup.get("thread_id"):
        return False
    process = thread.GetProcess()
    target = process.GetTarget()
    site = _module_va(target, _u(frame, "rip"))
    if site == 0x372898:
        dest_ptr = _u(frame, "r8") - 0x10
        fixed_x = _s32(_u(frame, "rsi"))
        source_row_base = _u(frame, "r12")
        weight_table = _u(frame, "r11")
        site_name = "leading_segment_store"
    elif site == 0x372911:
        dest_ptr = _u(frame, "r8")
        fixed_x = _s32(_u(frame, "r13"))
        source_row_base = _u(frame, "r12")
        weight_table = _u(frame, "rax")
        site_name = "middle_segment_store"
    elif site == 0x3729E0:
        dest_ptr = _u(frame, "r8")
        fixed_x = _s32(_u(frame, "r13"))
        source_row_base = _u(frame, "r12")
        weight_table = _u(frame, "r10")
        site_name = "trailing_segment_store"
    else:
        return False

    counts = builtins.l16_resample_36f800_row_fill_store_counts
    counts[site_name] = counts.get(site_name, 0) + 1
    if site_name in builtins.l16_resample_36f800_row_fill_store_segments:
        return False

    plan = _row_plan(process, call.get("plan_addr_rbp_minus_0xc0"))
    prediction = _row_store_prediction(process, plan, fixed_x, source_row_base, weight_table)
    dest_vec = _vec4(process, dest_ptr)
    predicted = prediction.get("predicted_vec4") if prediction else None
    packet = {
        "rip": _u(frame, "rip"),
        "libcp_va": site,
        "site_name": site_name,
        "thread_id": thread.GetThreadID(),
        "worker_rbp": _u(frame, "rbp"),
        "dest_vec_ptr_after_store": dest_ptr,
        "dest_vec4_after_store": dest_vec,
        "source_row_base": source_row_base,
        "weight_table": weight_table,
        "row_prediction": prediction,
        "max_abs_diff_dest_vs_predicted": _max_abs_diff(dest_vec, predicted),
        "plan_packet_at_store": plan,
        "stack": _stack(thread),
    }
    builtins.l16_resample_36f800_row_fill_store_segments[site_name] = packet
    if builtins.l16_resample_36f800_row_fill_store is None:
        builtins.l16_resample_36f800_row_fill_store = packet
    return False


def row_fill_return_cb(frame, bp_loc, extra_args, internal_dict):
    setup = builtins.l16_resample_36f800_setup
    call = builtins.l16_resample_36f800_row_fill_call
    if not setup or not call or builtins.l16_resample_36f800_row_fill_return is not None:
        return False
    thread = frame.GetThread()
    if thread.GetThreadID() != setup.get("thread_id"):
        return False
    process = thread.GetProcess()
    target = process.GetTarget()
    builtins.l16_resample_36f800_row_fill_return = {
        "rip": _u(frame, "rip"),
        "libcp_va": _module_va(target, _u(frame, "rip")),
        "thread_id": thread.GetThreadID(),
        "worker_rbp": _u(frame, "rbp"),
        "rax_return_row_cache_ptr": _u(frame, "rax"),
        "original_rsi_row_cache_arg": call.get("rsi_row_cache_arg"),
        "plan_packet_after_372760": _row_plan(
            process, call.get("plan_addr_rbp_minus_0xc0")
        ),
        "store_segment_counts_inside_first_row_fill_call": dict(
            builtins.l16_resample_36f800_row_fill_store_counts
        ),
        "store_segment_first_packets_inside_first_row_fill_call": dict(
            builtins.l16_resample_36f800_row_fill_store_segments
        ),
        "stack": _stack(thread),
    }
    for bp in call.get("store_breakpoints") or []:
        if bp is not None:
            target.FindBreakpointByID(bp["id"]).SetEnabled(False)
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def first_store_cb(frame, bp_loc, extra_args, internal_dict):
    setup = builtins.l16_resample_36f800_setup
    if not setup or builtins.l16_resample_36f800_first_store is not None:
        return False

    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    rbp = _u(frame, "rbp")
    callback_fields = setup.get("callback_object_ptr_rbp_minus_0x1040") + 8
    if _ptr(process, rbp - 0xF8) != callback_fields:
        return False

    source_ptrs = [_u(frame, reg) for reg in ("rax", "rcx", "rsi", "rdi")]
    weight_ptrs = [_u(frame, reg) for reg in ("r8", "r9", "r10", "r11")]
    dest_ptr = _u(frame, "rdx")
    source_vecs = [_vec4(process, addr) for addr in source_ptrs]
    weight_vecs = [_vec4(process, addr) for addr in weight_ptrs]
    dest_vec = _vec4(process, dest_ptr)
    predicted = _weighted_sum(source_vecs, weight_vecs)

    builtins.l16_resample_36f800_first_store = {
        "rip": _u(frame, "rip"),
        "libcp_va": _module_va(target, _u(frame, "rip")),
        "thread_id": frame.GetThread().GetThreadID(),
        "worker_rbp": rbp,
        "callback_fields_local_rbp_minus_0xf8": _ptr(process, rbp - 0xF8),
        "source_vec_ptrs_rax_rcx_rsi_rdi": source_ptrs,
        "weight_vec_ptrs_r8_r9_r10_r11": weight_ptrs,
        "dest_vec_ptr_rdx_after_store": dest_ptr,
        "source_vec4s": source_vecs,
        "weight_vec4s": weight_vecs,
        "dest_vec4_after_store": dest_vec,
        "predicted_weighted_sum_vec4": predicted,
        "max_abs_diff_dest_vs_predicted": _max_abs_diff(dest_vec, predicted),
        "stack": _stack(frame.GetThread()),
    }
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def return_cb(frame, bp_loc, extra_args, internal_dict):
    setup = builtins.l16_resample_36f800_setup
    if not setup or builtins.l16_resample_36f800_return is not None:
        return False
    if frame.GetThread().GetThreadID() != setup.get("thread_id"):
        return False
    if _u(frame, "rbp") != setup.get("resample_rbp"):
        return False

    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    builtins.l16_resample_36f800_return = {
        "rip": _u(frame, "rip"),
        "libcp_va": _module_va(target, _u(frame, "rip")),
        "thread_id": frame.GetThread().GetThreadID(),
        "dest_descriptor_packet_after_dispatch": _descriptor(
            process, setup.get("callback_dest_descriptor_ptr"), 16
        ),
        "source_descriptor_packet_after_dispatch": _descriptor(
            process, setup.get("callback_source_descriptor_ptr"), 16
        ),
        "stack": _stack(frame.GetThread()),
    }
    for bp in target.breakpoint_iter():
        bp.SetEnabled(False)
    return True


def attach_setup_breakpoint(debugger):
    target = debugger.GetSelectedTarget()
    count = target.GetNumBreakpoints()
    if count == 0:
        print("L16_RESAMPLE_36F800 attach error: expected setup breakpoint")
        return
    setup_bp = target.GetBreakpointAtIndex(count - 1)
    setup_bp.SetScriptCallbackFunction(
        "owner_f0_resample_36f800_probe.owner_setup_cb"
    )
    print("L16_RESAMPLE_36F800 attached setup callback", setup_bp.GetID())


def drive_until_return_or_exit(debugger, max_steps=64):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while (
        process.IsValid()
        and process.GetState() == lldb.eStateStopped
        and builtins.l16_resample_36f800_return is None
        and steps < max_steps
    ):
        steps += 1
        process.Continue()
    print("L16_RESAMPLE_36F800_DRIVE_STEPS", steps)


def _payload(label):
    return {
        "label": label,
        "route_owner_setup_packet": builtins.l16_resample_36f800_route_owner_setup,
        "route_handoff_packet": builtins.l16_resample_36f800_route_handoff,
        "route_rescale_call_packet": builtins.l16_resample_36f800_route_rescale_call,
        "setup_packet": builtins.l16_resample_36f800_setup,
        "callable_thunk_packet": builtins.l16_resample_36f800_thunk,
        "worker_entry_packet": builtins.l16_resample_36f800_worker_entry,
        "row_plan_packet": builtins.l16_resample_36f800_row_plan,
        "worker_row_plan_packets": builtins.l16_resample_36f800_worker_row_plans,
        "row_fill_call_packet": builtins.l16_resample_36f800_row_fill_call,
        "row_fill_store_packet": builtins.l16_resample_36f800_row_fill_store,
        "row_fill_store_counts": builtins.l16_resample_36f800_row_fill_store_counts,
        "row_fill_store_segments": builtins.l16_resample_36f800_row_fill_store_segments,
        "row_fill_return_packet": builtins.l16_resample_36f800_row_fill_return,
        "first_store_packet": builtins.l16_resample_36f800_first_store,
        "return_packet": builtins.l16_resample_36f800_return,
    }


def report(label):
    if not hasattr(builtins, "l16_resample_36f800_setup"):
        reset()
    print("L16_RESAMPLE_36F800_BEGIN", label)
    print(json.dumps(_payload(label), indent=2, sort_keys=True))
    print("L16_RESAMPLE_36F800_END", label)


def write_report(label, path):
    if not hasattr(builtins, "l16_resample_36f800_setup"):
        reset()
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(_payload(label), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_RESAMPLE_36F800_WROTE", path)


def reset_global_rowcache_segments():
    builtins.l16_global_rowcache_breakpoint_ids = {}
    builtins.l16_global_rowcache_plan_hits = 0
    builtins.l16_global_rowcache_predicted_segment_totals = {
        "leading_segment_store": 0,
        "middle_segment_store": 0,
        "trailing_segment_store": 0,
        "total": 0,
    }
    builtins.l16_global_rowcache_predicted_nonzero_plan_counts = {
        "leading_segment_store": 0,
        "middle_segment_store": 0,
        "trailing_segment_store": 0,
    }
    builtins.l16_global_rowcache_store_counts = {
        "leading_segment_store": 0,
        "trailing_segment_store": 0,
    }
    builtins.l16_global_rowcache_store_samples = {}
    builtins.l16_global_rowcache_plan_samples = []
    builtins.l16_global_rowcache_nonmiddle_plan_samples = []
    builtins.l16_global_rowcache_executor_region_counts = {}
    builtins.l16_global_rowcache_thread_counts = {}
    builtins.l16_global_rowcache_errors = []


def _global_rowcache_note_error(message):
    errors = builtins.l16_global_rowcache_errors
    if len(errors) < GLOBAL_ROWCACHE_PLAN_SAMPLE_LIMIT:
        errors.append(message)


def _executor_region_key(region):
    if region is None:
        return "unreadable"
    return ",".join(str(item) for item in region)


def _record_global_plan_sample(packet, force=False):
    samples = builtins.l16_global_rowcache_plan_samples
    nonmiddle_samples = builtins.l16_global_rowcache_nonmiddle_plan_samples
    counts = packet.get("predicted_segment_counts_from_plan") or {}
    has_nonmiddle = (
        counts.get("leading_segment_store", 0) > 0
        or counts.get("trailing_segment_store", 0) > 0
    )
    if len(samples) < GLOBAL_ROWCACHE_PLAN_SAMPLE_LIMIT:
        samples.append(packet)
    if (force or has_nonmiddle) and len(nonmiddle_samples) < GLOBAL_ROWCACHE_PLAN_SAMPLE_LIMIT:
        nonmiddle_samples.append(packet)


def global_rowcache_plan_cb(frame, bp_loc, extra_args, internal_dict):
    if not hasattr(builtins, "l16_global_rowcache_plan_hits"):
        reset_global_rowcache_segments()

    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    rbp = _u(frame, "rbp")
    plan_addr = rbp - 0xC0
    executor_region = _u(frame, "rbx")
    executor_region_quad = _i32_quad(process, executor_region)
    plan_packet = _row_plan(process, plan_addr)
    segment_counts = _segment_counts_from_plan(plan_packet)

    builtins.l16_global_rowcache_plan_hits += 1
    thread_id = str(thread.GetThreadID())
    thread_counts = builtins.l16_global_rowcache_thread_counts
    thread_counts[thread_id] = thread_counts.get(thread_id, 0) + 1
    region_key = _executor_region_key(executor_region_quad)
    region_counts = builtins.l16_global_rowcache_executor_region_counts
    region_counts[region_key] = region_counts.get(region_key, 0) + 1

    if segment_counts is None:
        _global_rowcache_note_error(
            "failed to compute segment counts for plan at 0x%x" % plan_addr
        )
        return False

    totals = builtins.l16_global_rowcache_predicted_segment_totals
    nonzero_counts = builtins.l16_global_rowcache_predicted_nonzero_plan_counts
    for name in (
        "leading_segment_store",
        "middle_segment_store",
        "trailing_segment_store",
        "total",
    ):
        totals[name] = totals.get(name, 0) + segment_counts.get(name, 0)
    for name in (
        "leading_segment_store",
        "middle_segment_store",
        "trailing_segment_store",
    ):
        if segment_counts.get(name, 0) > 0:
            nonzero_counts[name] = nonzero_counts.get(name, 0) + 1

    packet = {
        "rip": _u(frame, "rip"),
        "libcp_va": _module_va(target, _u(frame, "rip")),
        "thread_id": thread.GetThreadID(),
        "worker_rbp": rbp,
        "plan_addr_rbp_minus_0xc0": plan_addr,
        "executor_region_ptr_rbx": executor_region,
        "executor_region_i32_quad": executor_region_quad,
        "plan_packet_after_372500": plan_packet,
        "predicted_segment_counts_from_plan": segment_counts,
        "stack": _stack(thread),
    }
    _record_global_plan_sample(packet)
    return False


def global_rowcache_store_cb(frame, bp_loc, extra_args, internal_dict):
    if not hasattr(builtins, "l16_global_rowcache_store_counts"):
        reset_global_rowcache_segments()

    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    site = _module_va(target, _u(frame, "rip"))
    if site == 0x372898:
        dest_ptr = _u(frame, "r8") - 0x10
        fixed_x = _s32(_u(frame, "rsi"))
        source_row_base = _u(frame, "r12")
        weight_table = _u(frame, "r11")
        site_name = "leading_segment_store"
    elif site == 0x3729E0:
        dest_ptr = _u(frame, "r8")
        fixed_x = _s32(_u(frame, "r13"))
        source_row_base = _u(frame, "r12")
        weight_table = _u(frame, "r10")
        site_name = "trailing_segment_store"
    else:
        return False

    counts = builtins.l16_global_rowcache_store_counts
    counts[site_name] = counts.get(site_name, 0) + 1
    if site_name in builtins.l16_global_rowcache_store_samples:
        return False

    helper_rbp = _u(frame, "rbp")
    worker_frame = thread.GetFrameAtIndex(1) if thread.GetNumFrames() > 1 else frame
    worker_rbp = _u(worker_frame, "rbp")
    plan = _row_plan(process, worker_rbp - 0xC0)
    prediction = _row_store_prediction(process, plan, fixed_x, source_row_base, weight_table)
    dest_vec = _vec4(process, dest_ptr)
    predicted = prediction.get("predicted_vec4") if prediction else None
    builtins.l16_global_rowcache_store_samples[site_name] = {
        "rip": _u(frame, "rip"),
        "libcp_va": site,
        "site_name": site_name,
        "thread_id": thread.GetThreadID(),
        "helper_rbp": helper_rbp,
        "worker_frame_libcp_va": _module_va(target, worker_frame.GetPC()),
        "worker_rbp": worker_rbp,
        "dest_vec_ptr_after_store": dest_ptr,
        "dest_vec4_after_store": dest_vec,
        "source_row_base": source_row_base,
        "weight_table": weight_table,
        "row_prediction": prediction,
        "max_abs_diff_dest_vs_predicted": _max_abs_diff(dest_vec, predicted),
        "plan_packet_at_store": plan,
        "stack": _stack(thread),
    }
    return False


def attach_global_rowcache_segment_breakpoints(debugger):
    target = debugger.GetSelectedTarget()
    count = target.GetNumBreakpoints()
    if count < 3:
        print("L16_GLOBAL_ROWCACHE attach error: expected 3 breakpoints")
        return
    plan_bp = target.GetBreakpointAtIndex(count - 3)
    leading_bp = target.GetBreakpointAtIndex(count - 2)
    trailing_bp = target.GetBreakpointAtIndex(count - 1)
    plan_bp.SetScriptCallbackFunction(
        "owner_f0_resample_36f800_probe.global_rowcache_plan_cb"
    )
    leading_bp.SetScriptCallbackFunction(
        "owner_f0_resample_36f800_probe.global_rowcache_store_cb"
    )
    trailing_bp.SetScriptCallbackFunction(
        "owner_f0_resample_36f800_probe.global_rowcache_store_cb"
    )
    builtins.l16_global_rowcache_breakpoint_ids = {
        "row_plan_return_0x3722b0": plan_bp.GetID(),
        "leading_store_after_0x372898": leading_bp.GetID(),
        "trailing_store_after_0x3729e0": trailing_bp.GetID(),
    }
    print("L16_GLOBAL_ROWCACHE attached breakpoints", builtins.l16_global_rowcache_breakpoint_ids)


def drive_until_global_rowcache_exit(debugger, max_steps=1024):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process.IsValid() and process.GetState() == lldb.eStateStopped and steps < max_steps:
        steps += 1
        process.Continue()
    print("L16_GLOBAL_ROWCACHE_DRIVE_STEPS", steps)


def _global_rowcache_breakpoint_counts(debugger):
    target = debugger.GetSelectedTarget()
    out = {}
    for name, bp_id in getattr(builtins, "l16_global_rowcache_breakpoint_ids", {}).items():
        bp = target.FindBreakpointByID(bp_id)
        out[name] = bp.GetHitCount() if bp and bp.IsValid() else None
    return out


def _global_rowcache_process_packet(debugger):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    if not process or not process.IsValid():
        return {"valid": False}
    return {
        "valid": True,
        "state": lldb.SBDebugger.StateAsCString(process.GetState()),
        "exit_status": process.GetExitStatus(),
    }


def _global_rowcache_payload(debugger, label):
    if not hasattr(builtins, "l16_global_rowcache_plan_hits"):
        reset_global_rowcache_segments()
    return {
        "label": label,
        "process": _global_rowcache_process_packet(debugger),
        "breakpoint_ids": builtins.l16_global_rowcache_breakpoint_ids,
        "breakpoint_hit_counts": _global_rowcache_breakpoint_counts(debugger),
        "row_plan_hits": builtins.l16_global_rowcache_plan_hits,
        "predicted_segment_totals": builtins.l16_global_rowcache_predicted_segment_totals,
        "predicted_nonzero_plan_counts": builtins.l16_global_rowcache_predicted_nonzero_plan_counts,
        "live_store_counts_for_instrumented_nonmiddle_sites": builtins.l16_global_rowcache_store_counts,
        "live_store_first_packets_for_instrumented_nonmiddle_sites": builtins.l16_global_rowcache_store_samples,
        "executor_region_counts": builtins.l16_global_rowcache_executor_region_counts,
        "thread_counts": builtins.l16_global_rowcache_thread_counts,
        "plan_samples": builtins.l16_global_rowcache_plan_samples,
        "nonmiddle_plan_samples": builtins.l16_global_rowcache_nonmiddle_plan_samples,
        "errors": builtins.l16_global_rowcache_errors,
    }


def report_global_rowcache(debugger, label):
    print("L16_GLOBAL_ROWCACHE_BEGIN", label)
    print(json.dumps(_global_rowcache_payload(debugger, label), indent=2, sort_keys=True))
    print("L16_GLOBAL_ROWCACHE_END", label)


def write_global_rowcache_report(debugger, label, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(_global_rowcache_payload(debugger, label), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_GLOBAL_ROWCACHE_WROTE", path)
