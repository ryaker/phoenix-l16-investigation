import builtins
import json
import struct


CTOR_VA = 0x225160
CREATE_STEREO_CALL_VA = 0x3F5086
CREATE_STEREO_RETURN_VA = 0x3F508B


def reset(label=""):
    builtins.l16_guidance_channel_origin = {
        "label": label,
        "inner_object": None,
        "root_address": None,
        "breakpoint_id": None,
        "create_stereo_breakpoint_ids": [],
        "create_stereo_events": [],
        "root_watchpoint_id": None,
        "payload_watchpoint_id": None,
        "watchpoint_armed": False,
        "watchpoint_stops": 0,
        "zero_writes": 0,
        "capture_complete": False,
        "terminated_after_capture": False,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
        "root_event": None,
        "event": None,
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_guidance_channel_origin"):
        reset()
    return builtins.l16_guidance_channel_origin


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    if not addr or size <= 0:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u64(process, addr):
    raw = _read(process, addr, 8)
    return struct.unpack_from("<Q", raw)[0] if raw is not None else None


def _i32(process, addr):
    raw = _read(process, addr, 4)
    return struct.unpack_from("<i", raw)[0] if raw is not None else None


def _hex(process, addr, size):
    raw = _read(process, addr, size)
    return raw.hex() if raw is not None else None


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


def _stack(thread, max_frames=32):
    target = thread.GetProcess().GetTarget()
    out = []
    for index in range(min(thread.GetNumFrames(), max_frames)):
        frame = thread.GetFrameAtIndex(index)
        out.append(
            {
                "index": index,
                "pc": frame.GetPC(),
                "libcp_va": _module_va(target, frame.GetPC()),
                "function": frame.GetFunctionName(),
            }
        )
    return out


def _node_snapshot(process, node):
    if not node:
        return {"addr": node, "read_ok": False}
    payload = _u64(process, node + 0x28)
    control = _u64(process, node + 0x30)
    return {
        "addr": node,
        "read_ok": True,
        "left_0x00": _u64(process, node),
        "right_0x08": _u64(process, node + 0x08),
        "parent_0x10": _u64(process, node + 0x10),
        "key_0x20": _i32(process, node + 0x20),
        "payload_ptr_0x28": payload,
        "payload_control_0x30": control,
        "raw_0x00_0x40": _hex(process, node, 0x40),
        "payload_qwords_0x00_0x80": [
            _u64(process, payload + offset) for offset in range(0, 0x80, 8)
        ]
        if payload
        else None,
        "payload_raw_0x00_0x100": _hex(process, payload, 0x100) if payload else None,
    }


def _arm_root_watchpoint(target, inner):
    state = _state()
    if state["watchpoint_armed"]:
        return
    lldb = builtins.__import__("lldb")
    root_address = inner + 0x78
    error = lldb.SBError()
    wp = target.WatchAddress(root_address, 8, False, True, error)
    if not wp or not wp.IsValid() or not error.Success():
        state["errors"].append(
            f"failed root watchpoint at {root_address:#x}: {error.GetCString()}"
        )
        return
    state["inner_object"] = inner
    state["root_address"] = root_address
    state["root_watchpoint_id"] = wp.GetID()
    state["watchpoint_armed"] = True


def hit(frame, bp_loc, internal_dict):
    state = _state()
    target = frame.GetThread().GetProcess().GetTarget()
    site_va = _module_va(target, frame.GetPC())
    if site_va != CTOR_VA:
        state["errors"].append(f"unexpected constructor site {site_va}")
        return False
    _arm_root_watchpoint(target, _u(frame, "rdi"))
    bp = bp_loc.GetBreakpoint()
    if bp and bp.IsValid():
        bp.SetEnabled(False)
    return False


def create_stereo_hit(frame, bp_loc, internal_dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    site_va = _module_va(target, frame.GetPC())
    if site_va == CREATE_STEREO_CALL_VA:
        output = _u(frame, "rdi")
        state["create_stereo_events"].append(
            {
                "thread_id": thread.GetThreadID(),
                "call_site": site_va,
                "output_descriptor": output,
                "before_raw_0x00_0x30": _hex(process, output, 0x30),
                "after_raw_0x00_0x30": None,
                "stack": _stack(thread, 12),
            }
        )
        return False
    if site_va == CREATE_STEREO_RETURN_VA:
        thread_id = thread.GetThreadID()
        for event in reversed(state["create_stereo_events"]):
            if (
                event["thread_id"] == thread_id
                and event["after_raw_0x00_0x30"] is None
            ):
                event["return_site"] = site_va
                event["after_raw_0x00_0x30"] = _hex(
                    process, event["output_descriptor"], 0x30
                )
                event["return_xmm0_bits"] = _u(frame, "xmm0")
                break
        else:
            state["errors"].append(
                f"unpaired CreateStereoImage return on thread {thread_id}"
            )
        return False
    state["errors"].append(f"unexpected CreateStereoImage site {site_va}")
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    for index in range(target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(index)
        if not bp or not bp.IsValid() or bp.GetNumLocations() < 1:
            continue
        site = bp.GetLocationAtIndex(0).GetAddress().GetFileAddress()
        if site == CTOR_VA:
            bp.SetScriptCallbackFunction("guidance_channel_origin_probe.hit")
            _state()["breakpoint_id"] = bp.GetID()
        elif site in (CREATE_STEREO_CALL_VA, CREATE_STEREO_RETURN_VA):
            bp.SetScriptCallbackFunction(
                "guidance_channel_origin_probe.create_stereo_hit"
            )
            _state()["create_stereo_breakpoint_ids"].append(bp.GetID())
    if _state()["breakpoint_id"] is None:
        _state()["errors"].append("constructor breakpoint not found")
    if len(_state()["create_stereo_breakpoint_ids"]) != 2:
        _state()["errors"].append("CreateStereoImage breakpoints not found")
    print(
        "L16_GUIDANCE_ORIGIN_ATTACHED",
        _state()["breakpoint_id"],
        _state()["create_stereo_breakpoint_ids"],
    )


def _record_watchpoint_stop(debugger):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    thread = process.GetSelectedThread()
    if not thread or not thread.IsValid():
        return
    if thread.GetStopReason() != lldb.eStopReasonWatchpoint:
        return
    state["watchpoint_stops"] += 1
    wp_id = thread.GetStopReasonDataAtIndex(0) if thread.GetStopReasonDataCount() else None
    root = _u64(process, state["root_address"])
    if not root:
        state["zero_writes"] += 1
        return
    frame = thread.GetFrameAtIndex(0)
    target = process.GetTarget()
    event = {
        "watchpoint_id": wp_id,
        "thread_id": thread.GetThreadID(),
        "pc": frame.GetPC(),
        "libcp_va": _module_va(target, frame.GetPC()),
        "registers": _registers(frame),
        "stack": _stack(thread),
        "inner_object": state["inner_object"],
        "root_address": state["root_address"],
        "root_value": root,
        "node": _node_snapshot(process, root),
    }
    if wp_id == state.get("root_watchpoint_id"):
        state["root_event"] = event
        root_wp = target.FindWatchpointByID(wp_id)
        if root_wp and root_wp.IsValid():
            root_wp.SetEnabled(False)
        error = lldb.SBError()
        payload_wp = target.WatchAddress(root + 0x28, 8, False, True, error)
        if not payload_wp or not payload_wp.IsValid() or not error.Success():
            state["errors"].append(
                f"failed payload watchpoint at {root + 0x28:#x}: {error.GetCString()}"
            )
            return
        state["payload_watchpoint_id"] = payload_wp.GetID()
        return
    if wp_id == state.get("payload_watchpoint_id"):
        if not event["node"]["payload_ptr_0x28"]:
            state["zero_writes"] += 1
            return
        payload = event["node"]["payload_ptr_0x28"]
        payload_descriptor = _hex(process, payload, 0x30)
        event["cached_descriptor_raw_0x00_0x30"] = payload_descriptor
        completed = [
            item
            for item in state["create_stereo_events"]
            if item["after_raw_0x00_0x30"] is not None
        ]
        event["create_stereo_completed_count"] = len(completed)
        event["matches_latest_create_stereo_output"] = bool(
            completed
            and completed[-1]["after_raw_0x00_0x30"] == payload_descriptor
        )
        event["matching_create_stereo_event_indexes"] = [
            index
            for index, item in enumerate(state["create_stereo_events"])
            if item["after_raw_0x00_0x30"] == payload_descriptor
        ]
        state["event"] = event
        state["capture_complete"] = True


def drive_until_capture(debugger, max_steps=24000):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while (
        process.IsValid()
        and process.GetState() == lldb.eStateStopped
        and steps < max_steps
        and not state["capture_complete"]
    ):
        _record_watchpoint_stop(debugger)
        if state["capture_complete"]:
            break
        steps += 1
        process.Continue()
    state["drive_steps"] = steps
    state["drive_hit_step_cap"] = (
        process.IsValid()
        and process.GetState() == lldb.eStateStopped
        and steps >= max_steps
        and not state["capture_complete"]
    )
    if state["capture_complete"] and process.IsValid():
        error = process.Kill()
        state["terminated_after_capture"] = error.Success()
    print(
        "L16_GUIDANCE_ORIGIN_DRIVE",
        steps,
        state["capture_complete"],
        state["terminated_after_capture"],
    )


def _process_packet(debugger):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    if not process or not process.IsValid():
        return {"valid": False}
    return {
        "valid": True,
        "state": lldb.SBDebugger.StateAsCString(process.GetState()),
        "exit_status": process.GetExitStatus(),
    }


def payload(debugger):
    packet = dict(_state())
    packet["process"] = _process_packet(debugger)
    target = debugger.GetSelectedTarget()
    packet["watchpoint_hit_counts"] = {}
    for name in ("root_watchpoint_id", "payload_watchpoint_id"):
        wp_id = packet.get(name)
        if wp_id is not None:
            wp = target.FindWatchpointByID(wp_id)
            packet["watchpoint_hit_counts"][name] = (
                wp.GetHitCount() if wp and wp.IsValid() else None
            )
    return packet


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_GUIDANCE_ORIGIN_WROTE", path)
