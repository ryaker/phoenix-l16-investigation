import builtins
import json
import struct


SITES = {
    0x26AC18: "upsample_depth_descriptor_ready",
    0x26E64F: "index5_descriptor_ready",
    0x3D9050: "depth_cache_update_entry",
    0x3D90C9: "depth_cache_update_post",
    0x3DC280: "depth_cache_event_entry",
    0x3DC2CB: "depth_cache_tile_pre",
    0x3DC2CE: "depth_cache_tile_post",
    0x3DC2E2: "depth_cache_selected_input",
    0x3DC32F: "depth_cache_publish_pre",
    0x3DC332: "depth_cache_publish_post",
    0x41E180: "gdepth_writer_entry",
    0x41E8C5: "depth_provider_pre",
    0x41E8DC: "depth_provider_post",
    0x41EB5A: "gdepth_descriptor_ready",
    0x41EC91: "gdepth_extrema_ready",
    0x41F1AD: "gdepth_near_stream",
    0x41F1D0: "gdepth_far_stream",
}


def reset(label="", step_cap=300000):
    builtins.l16_index5_gdepth_export = {
        "label": label,
        "step_cap": step_cap,
        "breakpoints": {},
        "counts": {},
        "samples": [],
        "cache_watchpoints": {},
        "cache_watch_samples": [],
        "errors": [],
        "drive_hit_step_cap": False,
    }


def _state():
    if not hasattr(builtins, "l16_index5_gdepth_export"):
        reset()
    return builtins.l16_index5_gdepth_export


def _reg(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _module_base(target):
    lldb = builtins.__import__("lldb")
    module = target.FindModule(lldb.SBFileSpec("libcp.dylib"))
    if not module or not module.IsValid():
        return None
    value = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
    return None if value in (0, (1 << 64) - 1) else value


def _module_va(target, address):
    base = _module_base(target)
    return address - base if base is not None else None


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u32(data, offset=0):
    return struct.unpack_from("<I", data, offset)[0]


def _i32(data, offset=0):
    return struct.unpack_from("<i", data, offset)[0]


def _u64(data, offset=0):
    return struct.unpack_from("<Q", data, offset)[0]


def _f32(data, offset=0):
    return struct.unpack_from("<f", data, offset)[0]


def _descriptor(process, address, sample_count=16):
    raw = _read(process, address, 0x30)
    if raw is None:
        return {"address": address, "read_ok": False}
    data_ptr = _u64(raw, 0x20)
    sample_raw = _read(process, data_ptr, sample_count * 4) if data_ptr else None
    return {
        "address": address,
        "read_ok": True,
        "width": _u32(raw, 0x10),
        "height": _u32(raw, 0x14),
        "stride": _i32(raw, 0x18),
        "data_ptr": data_ptr,
        "first_f32": [
            _f32(sample_raw, offset)
            for offset in range(0, len(sample_raw), 4)
        ]
        if sample_raw is not None
        else [],
        "raw_hex": raw.hex(),
    }


def _source_image(process, address, sample_count=16):
    raw = _read(process, address, 0x48)
    if raw is None:
        return {"address": address, "read_ok": False}
    data_ptr = _u64(raw, 0x38)
    sample_raw = _read(process, data_ptr, sample_count * 4) if data_ptr else None
    return {
        "address": address,
        "read_ok": True,
        "roi": [_i32(raw, offset) for offset in range(0x18, 0x28, 4)],
        "width": _u32(raw, 0x28),
        "height": _u32(raw, 0x2C),
        "stride": _i32(raw, 0x30),
        "data_ptr": data_ptr,
        "first_f32": [
            _f32(sample_raw, offset)
            for offset in range(0, len(sample_raw), 4)
        ]
        if sample_raw is not None
        else [],
        "raw_hex": raw.hex(),
    }


def _stack(frame, limit=10):
    target = frame.GetThread().GetProcess().GetTarget()
    rows = []
    for index in range(min(frame.GetThread().GetNumFrames(), limit)):
        item = frame.GetThread().GetFrameAtIndex(index)
        rows.append(
            {
                "index": index,
                "pc": item.GetPC(),
                "libcp_va": _module_va(target, item.GetPC()),
                "function": item.GetFunctionName(),
            }
        )
    return rows


def _arm_cache_watchpoints(process, cache):
    state = _state()
    if state["cache_watchpoints"]:
        return
    lldb = builtins.__import__("lldb")
    for name, address in (
        ("cache_descriptor_0x18_data", cache + 0x38),
        ("cache_descriptor_0x48_data", cache + 0x68),
    ):
        error = lldb.SBError()
        watchpoint = process.GetTarget().WatchAddress(
            address, 8, False, True, error
        )
        if not error.Success() or not watchpoint or not watchpoint.IsValid():
            state["errors"].append(
                {
                    "error": "cache watchpoint arm failed",
                    "name": name,
                    "detail": error.GetCString(),
                }
            )
            continue
        state["cache_watchpoints"][str(watchpoint.GetID())] = {
            "name": name,
            "address": address,
            "cache": cache,
        }


def hit(frame, _bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    site_va = _module_va(target, frame.GetPC())
    name = SITES.get(site_va)
    if name is None:
        state["errors"].append({"error": "unknown site", "site_va": site_va})
        return False
    state["counts"][name] = state["counts"].get(name, 0) + 1
    sample = {
        "site": name,
        "site_va": site_va,
        "thread_id": frame.GetThread().GetThreadID(),
        "stack": _stack(frame),
    }
    rbp = _reg(frame, "rbp")
    if site_va == 0x26AC18:
        sample.update(
            {
                "upsample_object": _reg(frame, "r12"),
                "descriptor": _descriptor(process, _reg(frame, "r14")),
            }
        )
    elif site_va == 0x26E64F:
        obj = _reg(frame, "r12")
        index_raw = _read(process, obj + 8, 4)
        sample["object"] = obj
        sample["object_index"] = _u32(index_raw) if index_raw is not None else None
        sample["descriptor"] = _descriptor(process, _reg(frame, "r14"))
    elif site_va == 0x3DC280:
        event_ptr = _reg(frame, "rsi")
        index_ptr = _reg(frame, "rdx")
        event_raw = _read(process, event_ptr, 4)
        index_raw = _read(process, index_ptr, 4)
        sample.update(
            {
                "callback": _reg(frame, "rdi"),
                "event": _u32(event_raw) if event_raw is not None else None,
                "index": _u32(index_raw) if index_raw is not None else None,
            }
        )
    elif site_va in (0x3DC2CB, 0x3DC2CE):
        cache = _reg(frame, "rbx")
        target_raw = (
            _read(process, _reg(frame, "rax") + 0x30, 8)
            if site_va == 0x3DC2CB
            else None
        )
        sample.update(
            {
                "cache": cache,
                "tile_callback": _reg(frame, "rdi"),
                "tile_target": _u64(target_raw) if target_raw is not None else None,
                "tile_target_va": _module_va(target, _u64(target_raw))
                if target_raw is not None
                else None,
                "cache_descriptor_0x18": _descriptor(process, cache + 0x18),
                "cache_descriptor_0x48": _descriptor(process, cache + 0x48),
            }
        )
    elif site_va == 0x3DC2E2:
        selected = _reg(frame, "rax")
        cache = _reg(frame, "rbx")
        _arm_cache_watchpoints(process, cache)
        sample.update(
            {
                "cache": cache,
                "selected_input": selected,
                "selected_descriptor": _descriptor(process, selected),
                "selected_source_image": _source_image(process, selected),
                "cache_source_0x18": _source_image(process, cache),
                "cache_descriptor_0x48": _descriptor(process, cache + 0x48),
            }
        )
    elif site_va in (0x3DC32F, 0x3DC332):
        cache = _reg(frame, "rbx")
        sample.update(
            {
                "cache": cache,
                "publisher_object": _reg(frame, "rdi"),
                "publisher_target": _u64(
                    _read(process, _reg(frame, "rax") + 0x30, 8)
                )
                if site_va == 0x3DC32F
                and _read(process, _reg(frame, "rax") + 0x30, 8) is not None
                else None,
                "cache_descriptor_0x18": _descriptor(process, cache + 0x18),
                "cache_descriptor_0x48": _descriptor(process, cache + 0x48),
            }
        )
    elif site_va == 0x3D9050:
        cache = _reg(frame, "rdi")
        selected = _reg(frame, "rsi")
        sample.update(
            {
                "cache": cache,
                "selected_input": selected,
                "selected_descriptor": _descriptor(process, selected),
                "selected_source_image": _source_image(process, selected),
                "cache_source_0x18": _source_image(process, cache),
                "cache_descriptor_0x48": _descriptor(process, cache + 0x48),
            }
        )
    elif site_va == 0x3D90C9:
        cache = _reg(frame, "r15")
        sample.update(
            {
                "cache": cache,
                "cache_source_0x18": _source_image(process, cache),
                "cache_descriptor_0x48": _descriptor(process, cache + 0x48),
            }
        )
    elif site_va == 0x41E180:
        sample.update(
            {
                "writer_owner": _reg(frame, "rdi"),
                "output_stream": _reg(frame, "rsi"),
                "size_pointer": _reg(frame, "rdx"),
                "provider_wrapper": _reg(frame, "rcx"),
                "export_format": _reg(frame, "r8") & 0xFFFFFFFF,
            }
        )
    elif site_va == 0x41E8C5:
        provider_object = _reg(frame, "rsi")
        context_raw = _read(process, provider_object + 8, 8)
        context = _u64(context_raw) if context_raw is not None else 0
        source_raw = _read(process, context + 0x698, 8) if context else None
        source = _u64(source_raw) if source_raw is not None else 0
        sample.update(
            {
                "writer_owner": _reg(frame, "r13"),
                "provider_object": provider_object,
                "provider_context": context,
                "provider_target": _reg(frame, "rax"),
                "provider_target_va": _module_va(target, _reg(frame, "rax")),
                "source_descriptor_pointer": source,
                "source_image": _source_image(process, source)
                if source
                else None,
                "provider_output": rbp - 0x710,
            }
        )
    elif site_va == 0x41E8DC:
        sample["provider_descriptor"] = _descriptor(process, rbp - 0x710)
    elif site_va == 0x41EB5A:
        sample["gdepth_descriptor"] = _descriptor(process, rbp - 0x6E0)
    elif site_va == 0x41EC91:
        near_raw = _read(process, rbp - 0x850, 4)
        far_raw = _read(process, rbp - 0x870, 4)
        sample["near"] = _f32(near_raw) if near_raw is not None else None
        sample["far"] = _f32(far_raw) if far_raw is not None else None
        sample["gdepth_descriptor"] = _descriptor(process, rbp - 0x6E0)
    elif site_va == 0x41F1AD:
        raw = _read(process, rbp - 0x850, 4)
        sample["streamed_near"] = _f32(raw) if raw is not None else None
    elif site_va == 0x41F1D0:
        raw = _read(process, rbp - 0x870, 4)
        sample["streamed_far"] = _f32(raw) if raw is not None else None
    state["samples"].append(sample)
    return False


def install(debugger):
    target = debugger.GetSelectedTarget()
    for address, name in SITES.items():
        before = target.GetNumBreakpoints()
        debugger.HandleCommand(
            f"breakpoint set --shlib libcp.dylib --address 0x{address:x}"
        )
        if target.GetNumBreakpoints() <= before:
            _state()["errors"].append(
                {"error": "breakpoint not created", "site": name}
            )
            continue
        breakpoint = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
        breakpoint.SetScriptCallbackFunction("gdepth_export_probe.hit")
        _state()["breakpoints"][name] = breakpoint.GetID()


def drive_until_exit_or_step_cap(debugger):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process and process.IsValid():
        state = process.GetState()
        if state in (lldb.eStateExited, lldb.eStateDetached, lldb.eStateInvalid):
            break
        if state == lldb.eStateStopped:
            if steps >= _state()["step_cap"]:
                _state()["drive_hit_step_cap"] = True
                break
            thread = process.GetSelectedThread()
            if (
                thread
                and thread.IsValid()
                and thread.GetStopReason() == lldb.eStopReasonWatchpoint
                and thread.GetStopReasonDataCount()
            ):
                watchpoint_id = str(thread.GetStopReasonDataAtIndex(0))
                meta = _state()["cache_watchpoints"].get(watchpoint_id)
                if meta is not None:
                    frame = thread.GetFrameAtIndex(0)
                    cache = meta["cache"]
                    _state()["cache_watch_samples"].append(
                        {
                            "ordinal": len(_state()["cache_watch_samples"]) + 1,
                            "watchpoint_id": int(watchpoint_id),
                            "name": meta["name"],
                            "address": meta["address"],
                            "thread_id": thread.GetThreadID(),
                            "pc": frame.GetPC(),
                            "libcp_va": _module_va(
                                process.GetTarget(), frame.GetPC()
                            ),
                            "cache_descriptor_0x18": _descriptor(
                                process, cache + 0x18
                            ),
                            "cache_descriptor_0x48": _descriptor(
                                process, cache + 0x48
                            ),
                            "stack": _stack(frame, 12),
                        }
                    )
            process.Continue()
            steps += 1
            continue
        if state in (lldb.eStateRunning, lldb.eStateStepping):
            process.SendAsyncInterrupt()
            continue
        break


def report_to_file(debugger, path):
    process = debugger.GetSelectedTarget().GetProcess()
    state = dict(_state())
    state["process_state"] = process.GetState() if process and process.IsValid() else None
    state["process_exit_status"] = (
        process.GetExitStatus() if process and process.IsValid() else None
    )
    with open(path, "w") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
    print("INDEX5_GDEPTH_EXPORT_REPORT", path, state["counts"], state["errors"])
