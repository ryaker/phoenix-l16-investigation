import builtins
import json
import struct


SITES = {
    0x29ED90: "builder_entry",
    0x29EEB6: "callback_object_ready",
    0x29EECB: "dispatch_0x5440",
    0x29F5C0: "callback_vtable_slot_0x30",
    0x29F600: "worker_entry",
    0x29F9DE: "worker_store_pre",
    0x29F9E4: "worker_store_post",
}


def reset(label="", sample_limit=128):
    builtins.l16_upsample_29ed90_worker = {
        "label": label,
        "sample_limit": sample_limit,
        "counts": {name: 0 for name in SITES.values()},
        "breakpoint_ids": {},
        "disabled_after_cap": [],
        "samples": [],
        "pending_stores": {},
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_upsample_29ed90_worker"):
        reset()
    return builtins.l16_upsample_29ed90_worker


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


def _u32(data, off=0):
    return struct.unpack_from("<I", data, off)[0]


def _i32(data, off=0):
    return struct.unpack_from("<i", data, off)[0]


def _f32(data, off=0):
    return struct.unpack_from("<f", data, off)[0]


def _read_qword(process, addr):
    data = _read(process, addr, 8)
    return _u64(data) if data is not None else None


def _read_f32(process, addr):
    data = _read(process, addr, 4)
    return _f32(data) if data is not None else None


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
    return {
        name: _u(frame, name)
        for name in (
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
    }


def _xmm_f32(frame, name):
    try:
        lldb = builtins.__import__("lldb")
        value = frame.FindRegister(name)
        data = value.GetData()
        error = lldb.SBError()
        raw = bytes(data.GetUnsignedInt8(error, i) for i in range(data.GetByteSize()))
        if error.Success() and len(raw) >= 16:
            return list(struct.unpack_from("<4f", raw, 0))
    except Exception as exc:
        _state()["errors"].append(f"xmm read failed {name}: {exc}")
    return None


def _descriptor(process, addr):
    data = _read(process, addr, 0x30)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "qwords": [_u64(data, off) for off in range(0, 0x30, 8)],
        "u32": [_u32(data, off) for off in range(0, 0x30, 4)],
        "i32": [_i32(data, off) for off in range(0, 0x30, 4)],
        "f32": [_f32(data, off) for off in range(0, 0x30, 4)],
        "width_0x10": _u32(data, 0x10),
        "height_0x14": _u32(data, 0x14),
        "stride_0x18": _u32(data, 0x18),
        "data_ptr_0x20": _u64(data, 0x20),
    }


def _rect(process, addr):
    data = _read(process, addr, 0x10)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "i32": [_i32(data, off) for off in range(0, 0x10, 4)],
        "u32": [_u32(data, off) for off in range(0, 0x10, 4)],
    }


def _u32_pair(process, addr):
    data = _read(process, addr, 8)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "u32": [_u32(data, 0), _u32(data, 4)],
        "i32": [_i32(data, 0), _i32(data, 4)],
    }


def _f32_pair(process, addr):
    data = _read(process, addr, 8)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "f32": [_f32(data, 0), _f32(data, 4)],
        "u32": [_u32(data, 0), _u32(data, 4)],
    }


def _callback_payload(process, addr):
    data = _read(process, addr, 0x30)
    if data is None:
        return {"addr": addr, "read_ok": False}
    qwords = [_u64(data, off) for off in range(0, 0x30, 8)]
    return {
        "addr": addr,
        "read_ok": True,
        "qwords": qwords,
        "field_0x00_hi_descriptor": _descriptor(process, qwords[0]),
        "field_0x08_src_descriptor": _descriptor(process, qwords[1]),
        "field_0x10_coefficients_f32_pair": _f32_pair(process, qwords[2]),
        "field_0x18_scale_f32": _read_f32(process, qwords[3]),
        "field_0x20_aux_descriptor": _descriptor(process, qwords[4]),
        "field_0x28_dst_descriptor": _descriptor(process, qwords[5]),
    }


def _callback_object(process, addr):
    data = _read(process, addr, 0x38)
    if data is None:
        return {"addr": addr, "read_ok": False}
    qwords = [_u64(data, off) for off in range(0, 0x38, 8)]
    return {
        "addr": addr,
        "read_ok": True,
        "qwords": qwords,
        "vtable": qwords[0],
        "field_0x08": qwords[1],
        "field_0x10_src_descriptor": _descriptor(process, qwords[2]),
        "field_0x18_coefficients_f32_pair": _f32_pair(process, qwords[3]),
        "field_0x20_scale_f32": _read_f32(process, qwords[4]),
        "field_0x28_aux_descriptor": _descriptor(process, qwords[5]),
        "field_0x30_dst_descriptor": _descriptor(process, qwords[6]),
        "payload_from_0x08": _callback_payload(process, addr + 8),
    }


def _stack(thread, max_frames=8):
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


def _disable_breakpoint(debugger, name):
    bp_id = _state()["breakpoint_ids"].get(name)
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id) if bp_id else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def _cap(name):
    if name in ("worker_store_pre", "worker_store_post"):
        return 16
    if name in ("callback_vtable_slot_0x30", "worker_entry"):
        return 8
    return 4


def hit(frame, bp_loc, internal_dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    site_va = _module_va(target, frame.GetPC())
    name = SITES.get(site_va)
    if name is None:
        state["errors"].append(f"unknown site {site_va}")
        return False

    state["counts"][name] = state["counts"].get(name, 0) + 1
    regs = _registers(frame)
    sample = {
        "site": name,
        "site_va": site_va,
        "thread_id": thread.GetThreadID(),
        "registers": regs,
        "xmm": {
            "xmm0": _xmm_f32(frame, "xmm0"),
            "xmm1": _xmm_f32(frame, "xmm1"),
            "xmm2": _xmm_f32(frame, "xmm2"),
            "xmm3": _xmm_f32(frame, "xmm3"),
            "xmm4": _xmm_f32(frame, "xmm4"),
            "xmm6": _xmm_f32(frame, "xmm6"),
            "xmm8": _xmm_f32(frame, "xmm8"),
        },
        "stack": _stack(thread),
    }

    if site_va == 0x29ED90:
        sample["builder_args"] = {
            "dst_rdi": regs["rdi"],
            "src_rsi": regs["rsi"],
            "arg_rdx": regs["rdx"],
            "arg_rcx": regs["rcx"],
            "dst_descriptor": _descriptor(process, regs["rdi"]),
            "src_descriptor": _descriptor(process, regs["rsi"]),
            "arg_rdx_descriptor_probe": _descriptor(process, regs["rdx"]),
            "arg_rcx_descriptor": _descriptor(process, regs["rcx"]),
        }
    elif site_va == 0x29EEB6:
        sample["callback_object"] = _callback_object(process, regs["rax"])
    elif site_va == 0x29EECB:
        callback_holder = regs["rdx"]
        sample["dispatch"] = {
            "rdi_dst_or_rect": regs["rdi"],
            "rsi_tile_pair": regs["rsi"],
            "rdx_callback_holder": callback_holder,
            "rect_at_rdi": _rect(process, regs["rdi"]),
            "tile_pair_at_rsi": _u32_pair(process, regs["rsi"]),
            "callback_holder_qwords": [
                _read_qword(process, callback_holder + off) for off in range(0, 0x30, 8)
            ],
        }
    elif site_va == 0x29F5C0:
        sample["callback_object"] = _callback_object(process, regs["rdi"])
        sample["tile_rect_rsi"] = _rect(process, regs["rsi"])
        sample["row_or_tile_rdx"] = _u32_pair(process, regs["rdx"])
    elif site_va == 0x29F600:
        callback_base = regs["rdi"] - 8
        sample["callback_object_addr"] = callback_base
        sample["callback_payload"] = _callback_payload(process, regs["rdi"])
        sample["tile_rect_rsi"] = _rect(process, regs["rsi"])
        sample["row_or_tile_rdx"] = _u32_pair(process, regs["rdx"])
    elif site_va == 0x29F9DE:
        store_addr = regs["rax"] + regs["rcx"] * 4
        store_value = _xmm_f32(frame, "xmm10")
        pending = {
            "store_addr": store_addr,
            "linear_index_rcx": regs["rcx"],
            "output_x_rbx": regs["rbx"],
            "output_y_r8": regs["r8"],
            "xmm10": store_value,
            "pre_store_value": _read_f32(process, store_addr),
        }
        state["pending_stores"][str(thread.GetThreadID())] = pending
        sample["store_pre"] = pending
        sample["callback_object_addr"] = regs["rdi"] - 8
        sample["callback_payload"] = _callback_payload(process, regs["rdi"])
    elif site_va == 0x29F9E4:
        key = str(thread.GetThreadID())
        pending = state["pending_stores"].get(key)
        sample["store_post"] = pending
        if pending:
            sample["store_post"]["post_store_value"] = _read_f32(
                process, pending["store_addr"]
            )

    if len(state["samples"]) < state["sample_limit"]:
        state["samples"].append(sample)

    if state["counts"][name] >= _cap(name):
        _disable_breakpoint(target.GetDebugger(), name)
        if name not in state["disabled_after_cap"]:
            state["disabled_after_cap"].append(name)
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    ids = {}
    for index in range(target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(index)
        if not bp or not bp.IsValid() or bp.GetNumLocations() < 1:
            continue
        loc = bp.GetLocationAtIndex(0)
        site_va = loc.GetAddress().GetFileAddress()
        name = SITES.get(site_va)
        if name is None:
            continue
        bp.SetScriptCallbackFunction("upsample_29ed90_worker_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_29ED90_WORKER_ATTACHED", ids)


def _breakpoint_hit_counts(debugger):
    target = debugger.GetSelectedTarget()
    out = {}
    for name, bp_id in _state().get("breakpoint_ids", {}).items():
        bp = target.FindBreakpointByID(bp_id)
        out[name] = bp.GetHitCount() if bp and bp.IsValid() else None
    return out


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


def drive_until_exit_or_step_cap(debugger, max_steps=12000):
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
    _state()["drive_steps"] = steps
    _state()["drive_hit_step_cap"] = (
        process.IsValid() and process.GetState() == lldb.eStateStopped and steps >= max_steps
    )
    print("L16_29ED90_WORKER_DRIVE_STEPS", steps)


def payload(debugger):
    packet = dict(_state())
    packet["process"] = _process_packet(debugger)
    packet["breakpoint_hit_counts"] = _breakpoint_hit_counts(debugger)
    return packet


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_29ED90_WORKER_WROTE", path)


def report(debugger):
    print("L16_29ED90_WORKER_BEGIN")
    print(json.dumps(payload(debugger), indent=2, sort_keys=True))
    print("L16_29ED90_WORKER_END")
