import builtins
import json
import struct


state = {
    "marker_breakpoint_id": None,
    "marker_hits": 0,
    "watchpoint_id": None,
    "source_dump_path": None,
    "target": None,
    "write": None,
    "errors": [],
}


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    return bytes(data) if error.Success() else None


def _u32(process, address):
    raw = _read(process, address, 4)
    return struct.unpack("<I", raw)[0] if raw else None


def _u64(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<Q", raw)[0] if raw else None


def _f32(process, address):
    raw = _read(process, address, 4)
    return struct.unpack("<f", raw)[0] if raw else None


def _module_base(target, name):
    lldb = builtins.__import__("lldb")
    module = target.FindModule(lldb.SBFileSpec(name))
    if not module.IsValid() or module.GetNumSections() == 0:
        return None
    return module.GetObjectFileHeaderAddress().GetLoadAddress(target)


def _snapshot(process, address, size, libcp_base=None):
    raw = _read(process, address, size) if address else None
    first_u64 = struct.unpack_from("<Q", raw, 0)[0] if raw and len(raw) >= 8 else None
    first_file_address = None
    if first_u64 is not None and libcp_base is not None and first_u64 >= libcp_base:
        candidate = first_u64 - libcp_base
        if candidate < 0x1000000:
            first_file_address = candidate
    return {
        "address": address,
        "raw_hex": raw.hex() if raw else None,
        "first_u64": first_u64,
        "first_u64_libcp_file_address": first_file_address,
    }


def _xmm_bytes(frame, name):
    data = frame.FindRegister(name).GetData()
    if not data.IsValid() or data.GetByteSize() < 16:
        return None
    error = builtins.__import__("lldb").SBError()
    raw = bytes(data.ReadRawData(error, 0, 16))
    return raw if error.Success() else None


def _stack(thread, limit=18):
    frames = []
    for index in range(min(thread.GetNumFrames(), limit)):
        frame = thread.GetFrameAtIndex(index)
        module = frame.GetModule().GetFileSpec().GetFilename() or ""
        address = frame.GetPCAddress()
        file_address = address.GetFileAddress()
        frames.append(
            {
                "index": index,
                "module": module,
                "file_address": file_address,
                "symbol": frame.GetFunctionName() or frame.GetDisplayFunctionName() or "",
            }
        )
    return frames


def marker_hit(frame, bp_loc, internal_dict):
    state["marker_hits"] += 1
    if state["watchpoint_id"] is not None:
        return False
    lldb = builtins.__import__("lldb")
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    address = frame.FindRegister("rdi").GetValueAsUnsigned()
    state["target"] = {
        "address": address,
        "level": frame.FindRegister("esi").GetValueAsUnsigned() & 0xFFFFFFFF,
        "x": frame.FindRegister("edx").GetValueAsUnsigned() & 0xFFFFFFFF,
        "y": frame.FindRegister("ecx").GetValueAsUnsigned() & 0xFFFFFFFF,
        "before_hex": (_read(process, address, 4) or b"").hex(),
    }
    error = lldb.SBError()
    watchpoint = target.WatchAddress(address, 4, False, True, error)
    if not watchpoint.IsValid() or not error.Success():
        state["errors"].append(
            f"watchpoint failed at {address:#x}: {error.GetCString()}"
        )
        return False
    state["watchpoint_id"] = watchpoint.GetID()
    target.FindBreakpointByID(state["marker_breakpoint_id"]).SetEnabled(False)
    return False


def attach(debugger, marker_breakpoint_id, source_dump_path=None):
    state["marker_breakpoint_id"] = marker_breakpoint_id
    state["source_dump_path"] = source_dump_path
    breakpoint = debugger.GetSelectedTarget().FindBreakpointByID(marker_breakpoint_id)
    breakpoint.SetScriptCallbackFunction(__name__ + ".marker_hit")
    breakpoint.SetAutoContinue(True)


def capture_watch_stop(debugger):
    process = debugger.GetSelectedTarget().GetProcess()
    target = process.GetTarget()
    lldb = builtins.__import__("lldb")
    if process.GetState() != lldb.eStateStopped:
        state["errors"].append(
            "process did not stop on the output write watchpoint"
        )
        return
    stopped = None
    for thread in process:
        if thread.GetStopReason() == lldb.eStopReasonWatchpoint:
            stopped = thread
            break
    if stopped is None:
        state["errors"].append("stopped process has no watchpoint thread")
        return
    frame = stopped.GetFrameAtIndex(0)
    address = state["target"]["address"]
    pc = frame.GetPCAddress().GetFileAddress()
    rax = frame.FindRegister("rax").GetValueAsUnsigned()
    rdi = frame.FindRegister("rdi").GetValueAsUnsigned()
    source_address = None
    if pc == 0x27E1CD:
        source_address = rax - 0x10
    elif pc == 0x27E1E4:
        source_address = rax
    elif pc == 0x27E237:
        source_address = rdi
    source = _read(process, source_address, 16) if source_address else None
    xmm1 = _xmm_bytes(frame, "xmm1")
    xmm2 = _xmm_bytes(frame, "xmm2")
    parent = stopped.GetFrameAtIndex(1)
    parent_owner = parent.FindRegister("r15").GetValueAsUnsigned()
    libcp_base = _module_base(target, "libcp.dylib")
    render_function_shared = _read(process, parent_owner + 0x8A0, 16)
    render_function_object = (
        struct.unpack_from("<Q", render_function_shared, 0)[0]
        if render_function_shared
        else None
    )
    parent_record_address = parent.FindRegister("r13").GetValueAsUnsigned()
    parent_record_raw = _read(process, parent_record_address, 0x70)
    descriptor_address = parent.FindRegister("r14").GetValueAsUnsigned()
    cache_688 = _u64(process, parent_owner + 0x688)
    cache_6b8 = _u64(process, parent_owner + 0x6B8)
    level_adapter_begin = _u64(process, parent_owner + 0x870)
    level_adapter_end = _u64(process, parent_owner + 0x878)
    level_adapter_capacity = _u64(process, parent_owner + 0x880)
    level_adapter_count = None
    level_adapter_entries = []
    if (
        level_adapter_begin is not None
        and level_adapter_end is not None
        and level_adapter_begin <= level_adapter_end
        and (level_adapter_end - level_adapter_begin) % 8 == 0
    ):
        level_adapter_count = (level_adapter_end - level_adapter_begin) // 8
        if level_adapter_count <= 64:
            for index in range(level_adapter_count):
                entry = _u64(process, level_adapter_begin + index * 8)
                packet = _snapshot(process, entry, 0x100, libcp_base)
                packet["index"] = index
                level_adapter_entries.append(packet)
    descriptor = {
        "address": descriptor_address,
        "width": _u32(process, descriptor_address + 0x10),
        "height": _u32(process, descriptor_address + 0x14),
        "stride_pixels": _u32(process, descriptor_address + 0x18),
        "data": _u64(process, descriptor_address + 0x20),
    }
    dump_size = (descriptor["stride_pixels"] or 0) * (descriptor["height"] or 0) * 16
    descriptor["dump_size"] = dump_size
    descriptor["dump_path"] = None
    if state["source_dump_path"] and 0 < dump_size <= 100 * 1024 * 1024:
        payload = _read(process, descriptor["data"], dump_size)
        if payload is not None:
            with open(state["source_dump_path"], "wb") as handle:
                handle.write(payload)
            descriptor["dump_path"] = state["source_dump_path"]
        else:
            state["errors"].append("failed to read source image payload")
    elif state["source_dump_path"]:
        state["errors"].append(f"refusing implausible source dump size {dump_size}")
    state["write"] = {
        "thread_id": stopped.GetThreadID(),
        "pc_file_address": pc,
        "module": frame.GetModule().GetFileSpec().GetFilename() or "",
        "symbol": frame.GetFunctionName() or frame.GetDisplayFunctionName() or "",
        "after_hex": (_read(process, address, 4) or b"").hex(),
        "source_address": source_address,
        "source_f32": list(struct.unpack("<4f", source)) if source else None,
        "scale_f32": list(struct.unpack("<4f", xmm1)) if xmm1 else None,
        "packed_xmm2_hex": xmm2.hex() if xmm2 else None,
        "mxcsr": frame.FindRegister("mxcsr").GetValueAsUnsigned(),
        "source_descriptor": descriptor,
        "parent_record": {
            "address": parent_record_address,
            "type_u32_0x00": _u32(process, parent_record_address),
            "priority_u32_0x04": _u32(process, parent_record_address + 0x4),
            "raw_hex": parent_record_raw.hex() if parent_record_raw else None,
        },
        "parent_renderer": {
            "address": parent_owner,
            "libcp_load_address": libcp_base,
            "rendering_mode_u32_0x774": _u32(process, parent_owner + 0x774),
            "depth_ready_i32_0x888": _u32(process, parent_owner + 0x888),
            "cache_0x688": _snapshot(process, cache_688, 0x200, libcp_base),
            "cache_0x6b8": _snapshot(process, cache_6b8, 0x100, libcp_base),
            "mode0_request_scale_f32_owner_0x48": _f32(
                process, parent_owner + 0x48
            ),
            "mode0_dof_threshold_f32_cache_0x6b8_0x98": _f32(
                process, cache_6b8 + 0x98
            ) if cache_6b8 else None,
            "level_adapters_0x870": {
                "begin": level_adapter_begin,
                "end": level_adapter_end,
                "capacity": level_adapter_capacity,
                "count": level_adapter_count,
                "entries": level_adapter_entries,
            },
            "display_vector_0x8c0_hex": (
                (_read(process, parent_owner + 0x8C0, 0x30) or b"").hex()
            ),
            "render_function_shared_0x8a0_hex": (
                render_function_shared.hex() if render_function_shared else None
            ),
            "render_function_object": render_function_object,
            "render_function_object_hex": (
                (_read(process, render_function_object, 0x60) or b"").hex()
                if render_function_object
                else None
            ),
        },
        "stack": _stack(stopped),
    }
    watchpoint = process.GetTarget().FindWatchpointByID(state["watchpoint_id"])
    if watchpoint.IsValid():
        watchpoint.SetEnabled(False)


def resume_if_stopped(debugger):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    if process.GetState() == lldb.eStateStopped:
        process.Continue()


def write_report(debugger, path):
    process = debugger.GetSelectedTarget().GetProcess()
    packet = dict(state)
    packet["process"] = {
        "valid": process.IsValid(),
        "state": builtins.__import__("lldb").SBDebugger.StateAsCString(process.GetState()),
        "exit_status": process.GetExitStatus(),
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(packet, handle, indent=2, sort_keys=True)
        handle.write("\n")
