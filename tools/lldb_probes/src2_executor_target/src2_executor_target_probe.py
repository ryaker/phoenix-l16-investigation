import builtins
import json
import re
import struct


VISIBLE_SRC2_RETURN = 0x3ECDAD
GATE_SITE = 0x3EC462

DISPATCH_SITES = {
    0x5506: "executor_0x5440_single_tile_call",
    0x2D8F: "executor_0x2d30_range_call",
    0x2DCC: "executor_0x2d30_loop_call",
    0x5D94: "executor_0x5cd0_tile_forward_call",
}


def reset(
    label="",
    sample_limit=16,
    capture_worker=True,
    enable_dispatch=True,
    stop_after_gate=False,
    stop_after_accepted=False,
    dynamic_dispatch=False,
    dynamic_dispatch_sites=None,
    dynamic_worker=False,
    stop_after_worker=False,
):
    builtins.l16_src2_executor_target = {
        "label": label,
        "sample_limit": sample_limit,
        "capture_worker": capture_worker,
        "enable_dispatch": enable_dispatch,
        "stop_after_gate": stop_after_gate,
        "stop_after_accepted": stop_after_accepted,
        "dynamic_dispatch": dynamic_dispatch,
        "dynamic_dispatch_sites": list(dynamic_dispatch_sites or DISPATCH_SITES.keys()),
        "dynamic_worker": dynamic_worker,
        "stop_after_worker": stop_after_worker,
        "gate_hits": 0,
        "accepted_gates": [],
        "skipped_gates": [],
        "dispatch_hits": [],
        "worker_entries": [],
        "errors": [],
        "breakpoint_ids": {},
        "dispatch_enabled": False,
        "dynamic_worker_bp_id": None,
    }


def _state():
    if not hasattr(builtins, "l16_src2_executor_target"):
        reset()
    return builtins.l16_src2_executor_target


def set_breakpoint_ids(ids):
    _state()["breakpoint_ids"] = dict(ids)


def install_callbacks(debugger, ids):
    set_breakpoint_ids(ids)
    target = debugger.GetSelectedTarget()
    callbacks = {
        ids.get("gate"): "src2_executor_target_probe.gate",
        ids.get("executor_0x5440_single_tile_call"): "src2_executor_target_probe.dispatch",
        ids.get("executor_0x2d30_range_call"): "src2_executor_target_probe.dispatch",
        ids.get("executor_0x2d30_loop_call"): "src2_executor_target_probe.dispatch",
        ids.get("executor_0x5cd0_tile_forward_call"): "src2_executor_target_probe.dispatch",
    }
    for bp_id, callback in callbacks.items():
        if not bp_id:
            continue
        bp = target.FindBreakpointByID(bp_id)
        if bp and bp.IsValid():
            bp.SetScriptCallbackFunction(callback)


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    if not addr:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u64(data, off=0):
    return struct.unpack_from("<Q", data, off)[0]


def _i32(data, off=0):
    return struct.unpack_from("<i", data, off)[0]


def _f32(data, off=0):
    return struct.unpack_from("<f", data, off)[0]


def _qwords(process, addr, count):
    data = _read(process, addr, count * 8)
    if data is None:
        return None
    return [_u64(data, off) for off in range(0, count * 8, 8)]


def _f32s(process, addr, count):
    data = _read(process, addr, count * 4)
    if data is None:
        return None
    return [_f32(data, off) for off in range(0, count * 4, 4)]


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


def _load_addr(target, ptr):
    if not ptr:
        return None
    base = _libcp_base(target)
    if base is None:
        return ptr
    if ptr >= base:
        return ptr
    # Some static tables are shown as unslid module VAs. Runtime pointers should
    # normally be slid already, but keeping this fallback makes the probe robust.
    return base + ptr


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


def _descriptor(process, addr):
    data = _read(process, addr, 0x30)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "qword_00": _u64(data, 0x00),
        "qword_08": _u64(data, 0x08),
        "width_0x10": _i32(data, 0x10),
        "height_0x14": _i32(data, 0x14),
        "stride_0x18": _i32(data, 0x18),
        "data_ptr_0x20": _u64(data, 0x20),
        "qword_28": _u64(data, 0x28),
    }


def _src2_state_bundle(process, field20):
    tuple_qwords = _qwords(process, field20, 3)
    if tuple_qwords is None:
        return {"addr": field20, "read_ok": False}

    cache_ptr, tile_offset_ptr, transform_origin_ptr = tuple_qwords
    cache_state_data = _read(process, cache_ptr + 0x1E0, 8)
    cache_state_ptr = _u64(cache_state_data) if cache_state_data is not None else None

    bundle = {
        "addr": field20,
        "read_ok": True,
        "cache_ptr_0x00": cache_ptr,
        "tile_offset_ptr_0x08": tile_offset_ptr,
        "transform_origin_ptr_0x10": transform_origin_ptr,
        "tile_offset_i32_pair": None,
        "transform_origin_i32_pair": None,
        "cache_state_ptr_at_0x1e0": cache_state_ptr,
        "cache_state_read_ok": False,
    }

    tile_offset = _read(process, tile_offset_ptr, 8)
    if tile_offset is not None:
        bundle["tile_offset_i32_pair"] = [_i32(tile_offset, 0), _i32(tile_offset, 4)]

    transform_origin = _read(process, transform_origin_ptr, 8)
    if transform_origin is not None:
        bundle["transform_origin_i32_pair"] = [_i32(transform_origin, 0), _i32(transform_origin, 4)]

    if cache_state_ptr:
        state_data = _read(process, cache_state_ptr, 0x50)
        if state_data is not None:
            radial_table_ptr = _u64(state_data, 0x08)
            bundle.update(
                {
                    "cache_state_read_ok": True,
                    "radial_scale_x_f32_0x00": _f32(state_data, 0x00),
                    "radial_scale_y_f32_0x04": _f32(state_data, 0x04),
                    "radial_table_ptr_0x08": radial_table_ptr,
                    "principal_or_offset_x_f32_0x20": _f32(state_data, 0x20),
                    "principal_or_offset_y_f32_0x24": _f32(state_data, 0x24),
                    "homography_3x3_f32_0x28": [
                        _f32(state_data, off)
                        for off in (0x28, 0x2C, 0x30, 0x34, 0x38, 0x3C, 0x40, 0x44, 0x48)
                    ],
                    "radial_table_head_f32_8": _f32s(process, radial_table_ptr, 8),
                    "radial_table_tail_f32_4_at_4092": _f32s(process, radial_table_ptr + 4092 * 4, 4),
                }
            )

    return bundle


def _callback_object(process, target, ptr):
    data = _read(process, ptr, 0x30)
    if data is None:
        return {"addr": ptr, "read_ok": False}

    vptr = _u64(data, 0x00)
    vptr_load = _load_addr(target, vptr)
    slot30 = None
    if vptr_load:
        slot_data = _read(process, vptr_load + 0x30, 8)
        if slot_data is not None:
            slot30 = _u64(slot_data)
    slot30_load = _load_addr(target, slot30) if slot30 else None
    field20 = _u64(data, 0x20)
    field28 = _u64(data, 0x28)
    return {
        "addr": ptr,
        "read_ok": True,
        "vptr": vptr,
        "vptr_va": _module_va(target, vptr_load) if vptr_load else None,
        "slot30_raw": slot30,
        "slot30_load": slot30_load,
        "slot30_va": _module_va(target, slot30_load) if slot30_load else None,
        "field_0x08": _u64(data, 0x08),
        "field_0x10": _u64(data, 0x10),
        "field_0x18": _u64(data, 0x18),
        "field_0x20": field20,
        "field_0x28": field28,
        "desc_0x08": _descriptor(process, _u64(data, 0x08)),
        "desc_0x10": _descriptor(process, _u64(data, 0x10)),
        "src2_state_0x20": _src2_state_bundle(process, field20),
        "interp_table_0x28_head_f32_32": _f32s(process, field28, 32),
    }


def _callback_vptr(process, ptr):
    data = _read(process, ptr, 8)
    if data is None:
        return None
    return _u64(data, 0)


def _enable_dispatch_breakpoints(debugger):
    state = _state()
    if state["dispatch_enabled"]:
        return
    if state.get("dynamic_dispatch"):
        _create_dynamic_dispatch_breakpoints(debugger)
        state["dispatch_enabled"] = True
        return
    target = debugger.GetSelectedTarget()
    for name in DISPATCH_SITES.values():
        bp_id = state["breakpoint_ids"].get(name)
        if not bp_id:
            continue
        bp = target.FindBreakpointByID(bp_id)
        if bp and bp.IsValid():
            bp.SetEnabled(True)
    state["dispatch_enabled"] = True


def _create_dynamic_dispatch_breakpoints(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    base = _libcp_base(target)
    if base is None:
        state["errors"].append("dynamic dispatch breakpoint failed: libcp base unavailable")
        return

    lldb = builtins.__import__("lldb")
    interpreter = debugger.GetCommandInterpreter()
    for site_va in state.get("dynamic_dispatch_sites", []):
        name = DISPATCH_SITES.get(site_va)
        if not name:
            state["errors"].append(f"dynamic dispatch breakpoint skipped unknown site {hex(site_va)}")
            continue
        if state["breakpoint_ids"].get(name):
            continue

        result = lldb.SBCommandReturnObject()
        interpreter.HandleCommand(f"breakpoint set -H --address 0x{base + site_va:x}", result)
        output = result.GetOutput()
        error = result.GetError()
        if not result.Succeeded():
            state["errors"].append(
                f"dynamic dispatch breakpoint failed at {name}/{hex(site_va)}: {error or output}"
            )
            continue

        match = re.search(r"Breakpoint (\d+):", output)
        if not match:
            state["errors"].append(
                f"dynamic dispatch breakpoint id parse failed at {name}/{hex(site_va)}: {output}"
            )
            continue

        bp_id = int(match.group(1))
        state["breakpoint_ids"][name] = bp_id
        bp = target.FindBreakpointByID(bp_id)
        if bp and bp.IsValid():
            bp.SetScriptCallbackFunction("src2_executor_target_probe.dispatch")


def _disable_breakpoint(debugger, name):
    bp_id = _state()["breakpoint_ids"].get(name)
    if not bp_id:
        return
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id)
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def gate(frame, bp_loc, internal_dict):
    state = _state()
    state["gate_hits"] += 1
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    caller_va = None
    if thread.GetNumFrames() > 1:
        caller_va = _module_va(target, thread.GetFrameAtIndex(1).GetPC())

    if caller_va != VISIBLE_SRC2_RETURN:
        if len(state["skipped_gates"]) < state["sample_limit"]:
            state["skipped_gates"].append({"caller_va": caller_va, "stack": _stack(thread, 6)})
        return False

    rdx = _u(frame, "rdx")
    wrapper_data = _read(process, rdx, 0x30)
    if wrapper_data is None:
        state["errors"].append(f"gate wrapper read failed at {hex(rdx)}")
        return False

    callback_ptr = _u64(wrapper_data, 0x20)
    callback = _callback_object(process, target, callback_ptr)
    state["accepted_gates"].append(
        {
            "site_va": GATE_SITE,
            "caller_va": caller_va,
            "rdx_wrapper": rdx,
            "wrapper_qwords": [_u64(wrapper_data, off) for off in range(0, 0x30, 8)],
            "callback_ptr": callback_ptr,
            "callback": callback,
            "stack": _stack(thread, 8),
        }
    )

    debugger = target.GetDebugger()
    if state.get("stop_after_gate", False):
        return True
    if state.get("enable_dispatch", True):
        _enable_dispatch_breakpoints(debugger)
    _disable_breakpoint(debugger, "gate")
    return False


def _accepted_callback_ptrs():
    return {entry.get("callback_ptr") for entry in _state()["accepted_gates"] if entry.get("callback_ptr")}


def _accepted_vptrs():
    values = set()
    for entry in _state()["accepted_gates"]:
        callback = entry.get("callback") or {}
        vptr = callback.get("vptr")
        if vptr:
            values.add(vptr)
    return values


def _create_worker_breakpoint(target, addr):
    state = _state()
    if not state.get("capture_worker", True):
        return
    if state.get("dynamic_worker_bp_id") or not addr:
        return

    if state.get("dynamic_worker"):
        debugger = target.GetDebugger()
        lldb = builtins.__import__("lldb")
        result = lldb.SBCommandReturnObject()
        debugger.GetCommandInterpreter().HandleCommand(f"breakpoint set -H --address 0x{addr:x}", result)
        output = result.GetOutput()
        error = result.GetError()
        if not result.Succeeded():
            state["errors"].append(f"dynamic worker breakpoint failed at {hex(addr)}: {error or output}")
            return
        match = re.search(r"Breakpoint (\d+):", output)
        if not match:
            state["errors"].append(f"dynamic worker breakpoint id parse failed at {hex(addr)}: {output}")
            return
        bp = target.FindBreakpointByID(int(match.group(1)))
        if not bp or not bp.IsValid():
            state["errors"].append(f"dynamic worker breakpoint lookup failed at {hex(addr)}")
            return
    else:
        bp = target.BreakpointCreateByAddress(addr)

    bp.SetScriptCallbackFunction("src2_executor_target_probe.worker_entry")
    state["dynamic_worker_bp_id"] = bp.GetID()


def dispatch(frame, bp_loc, internal_dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    site_va = _module_va(target, frame.GetPC())
    site_name = DISPATCH_SITES.get(site_va, hex(site_va))
    rdi = _u(frame, "rdi")

    ptr_match = rdi in _accepted_callback_ptrs()
    vptr = _callback_vptr(process, rdi)
    vptr_match = vptr in _accepted_vptrs()
    accepted = ptr_match or vptr_match
    if accepted:
        callback = _callback_object(process, target, rdi)
    else:
        callback = {"addr": rdi, "read_ok": vptr is not None, "vptr": vptr}

    sample = {
        "site": site_name,
        "site_va": site_va,
        "rdi_callback_ptr": rdi,
        "accepted": accepted,
        "ptr_match": ptr_match,
        "vptr_match": vptr_match,
        "callback": callback,
        "stack": _stack(thread, 8),
    }
    if len(state["dispatch_hits"]) < state["sample_limit"]:
        state["dispatch_hits"].append(sample)

    if accepted:
        _create_worker_breakpoint(target, callback.get("slot30_load"))
        if state.get("stop_after_accepted", False):
            for name in DISPATCH_SITES.values():
                _disable_breakpoint(target.GetDebugger(), name)
            return True
    return False


def worker_entry(frame, bp_loc, internal_dict):
    state = _state()
    thread = frame.GetThread()
    target = thread.GetProcess().GetTarget()
    if len(state["worker_entries"]) < state["sample_limit"]:
        state["worker_entries"].append(
            {
                "pc": frame.GetPC(),
                "pc_va": _module_va(target, frame.GetPC()),
                "registers": {
                    name: _u(frame, name)
                    for name in ("rdi", "rsi", "rdx", "rcx", "r8", "r9", "rax", "rbx", "rbp", "rsp")
                },
                "stack": _stack(thread, 10),
            }
        )
    debugger = target.GetDebugger()
    for name in DISPATCH_SITES.values():
        _disable_breakpoint(debugger, name)
    bp_id = state.get("dynamic_worker_bp_id")
    if bp_id:
        bp = target.FindBreakpointByID(bp_id)
        if bp and bp.IsValid():
            bp.SetEnabled(False)
    return state.get("stop_after_worker", False)


def _accepted_dispatch_count():
    return len([hit for hit in _state().get("dispatch_hits", []) if hit.get("accepted")])


def continue_if_no_accepted_dispatch(debugger):
    if _accepted_dispatch_count():
        return

    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    if not process or not process.IsValid() or process.GetState() != lldb.eStateStopped:
        return

    result = lldb.SBCommandReturnObject()
    debugger.GetCommandInterpreter().HandleCommand("process continue", result)
    if not result.Succeeded():
        state = _state()
        state["errors"].append(f"conditional continue failed: {result.GetError() or result.GetOutput()}")


def continue_if_no_worker_entry(debugger):
    if _state().get("worker_entries"):
        return

    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    if not process or not process.IsValid() or process.GetState() != lldb.eStateStopped:
        return

    result = lldb.SBCommandReturnObject()
    debugger.GetCommandInterpreter().HandleCommand("process continue", result)
    if not result.Succeeded():
        state = _state()
        state["errors"].append(f"conditional worker continue failed: {result.GetError() or result.GetOutput()}")


def continue_while_stopped(debugger, max_continues=8):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    if not process or not process.IsValid():
        return

    interpreter = debugger.GetCommandInterpreter()
    for _ in range(max_continues):
        if process.GetState() != lldb.eStateStopped:
            return
        result = lldb.SBCommandReturnObject()
        interpreter.HandleCommand("process continue", result)
        if not result.Succeeded():
            state = _state()
            state["errors"].append(f"continue while stopped failed: {result.GetError() or result.GetOutput()}")
            return


def report(label=None):
    state = _state()
    if label is not None:
        state["label"] = label
    summary = {
        "label": state.get("label", ""),
        "gate_hits": state.get("gate_hits", 0),
        "accepted_gate_count": len(state.get("accepted_gates", [])),
        "accepted_dispatch_count": len([hit for hit in state.get("dispatch_hits", []) if hit.get("accepted")]),
        "worker_entry_count": len(state.get("worker_entries", [])),
        "capture_worker": state.get("capture_worker", True),
        "enable_dispatch": state.get("enable_dispatch", True),
        "stop_after_gate": state.get("stop_after_gate", False),
        "stop_after_accepted": state.get("stop_after_accepted", False),
        "dynamic_dispatch": state.get("dynamic_dispatch", False),
        "dynamic_worker": state.get("dynamic_worker", False),
        "stop_after_worker": state.get("stop_after_worker", False),
        "slot30_vas": sorted(
            {
                entry.get("callback", {}).get("slot30_va")
                for entry in state.get("accepted_gates", [])
                if entry.get("callback", {}).get("slot30_va") is not None
            }
        ),
        "worker_entry_vas": sorted(
            {
                entry.get("pc_va")
                for entry in state.get("worker_entries", [])
                if entry.get("pc_va") is not None
            }
        ),
    }
    print("L16_SRC2_EXECUTOR_TARGET_PROBE_BEGIN", state.get("label", ""))
    print("L16_SRC2_EXECUTOR_TARGET_SUMMARY", json.dumps(summary, sort_keys=True))
    print(json.dumps(state, sort_keys=True))
    print("L16_SRC2_EXECUTOR_TARGET_PROBE_END", state.get("label", ""))
