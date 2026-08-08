import builtins
import json
import os
import struct


SITES = {
    0x2FBF05: {
        "name": "after_store_0x2fb320_radius2",
        "worker": 0x2FB320,
        "radius": 2,
        "x_reg": "rdi",
        "y_reg": "r9",
        "dest_base_reg": "r15",
        "dest_offset_reg": "rdx",
        "sum_weight_xmm": "xmm3",
        "sum_weighted_xmm": "xmm4",
    },
    0x2FDB5A: {
        "name": "after_store_0x2fd070_radius4",
        "worker": 0x2FD070,
        "radius": 4,
        "x_reg": "r8",
        "y_stack_qword": -0x1E8,
        "dest_base_reg": "rax",
        "dest_offset_reg": "rsi",
        "sum_weight_xmm": "xmm1",
        "sum_weighted_xmm": "xmm7",
    },
}


def reset(label="", site_cap=16, sample_limit=16):
    builtins.l16_selected_bilateral_formula = {
        "label": label,
        "site_cap": site_cap,
        "sample_limit": sample_limit,
        "breakpoint_ids": {},
        "counts": {meta["name"]: 0 for meta in SITES.values()},
        "disabled_after_cap": [],
        "samples": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_selected_bilateral_formula"):
        reset()
    return builtins.l16_selected_bilateral_formula


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


def _u32(data, off=0):
    return struct.unpack_from("<I", data, off)[0]


def _i32(data, off=0):
    return struct.unpack_from("<i", data, off)[0]


def _u64(data, off=0):
    return struct.unpack_from("<Q", data, off)[0]


def _qword(process, addr):
    data = _read(process, addr, 8)
    return _u64(data) if data is not None else None


def _i32s(data):
    return list(struct.unpack("<" + "i" * (len(data) // 4), data))


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


def _xmm_f32s(frame, name):
    try:
        lldb = builtins.__import__("lldb")
        data = frame.FindRegister(name).GetData()
        error = lldb.SBError()
        raw = bytes(data.GetUnsignedInt8(error, i) for i in range(data.GetByteSize()))
        if error.Success() and len(raw) >= 16:
            return list(struct.unpack_from("<4f", raw, 0))
    except Exception as exc:
        _state()["errors"].append(f"xmm read failed {name}: {exc}")
    return None


def _all_xmms(frame):
    return {f"xmm{index}": _xmm_f32s(frame, f"xmm{index}") for index in range(16)}


def _vec4(process, addr):
    data = _read(process, addr, 0x10)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "f32": _f32s(data),
        "i32": _i32s(data),
        "hex": data.hex(),
    }


def _descriptor(process, addr):
    data = _read(process, addr, 0x30)
    if data is None:
        return {"addr": addr, "read_ok": False}
    rect = [_i32(data, off) for off in range(0, 0x10, 4)]
    return {
        "addr": addr,
        "read_ok": True,
        "rect_i32_0x00": rect,
        "width_0x10": _u32(data, 0x10),
        "height_0x14": _u32(data, 0x14),
        "stride_0x18": _u32(data, 0x18),
        "data_ptr_0x20": _u64(data, 0x20),
        "aux_ptr_0x28": _u64(data, 0x28),
        "qwords": [_u64(data, off) for off in range(0, 0x30, 8)],
        "i32": _i32s(data),
    }


def _callback(process, obj):
    data = _read(process, obj, 0x28)
    if data is None:
        return {"object": obj, "read_ok": False}
    target = process.GetTarget()
    vtable = _u64(data, 0)
    fields = {
        "+0x08": _u64(data, 0x08),
        "+0x10": _u64(data, 0x10),
        "+0x18": _u64(data, 0x18),
        "+0x20": _u64(data, 0x20),
    }
    packet = {
        "object": obj,
        "read_ok": True,
        "vtable": vtable,
        "vtable_va": _module_va(target, vtable),
        "fields": fields,
        "field_decodes": {
            "+0x08_range_scale_descriptor": _descriptor(process, fields["+0x08"]),
            "+0x10_source_descriptor": _descriptor(process, fields["+0x10"]),
            "+0x18_destination_descriptor": _descriptor(process, fields["+0x18"]),
            "+0x20_coefficient_vec4": _vec4(process, fields["+0x20"]),
        },
    }
    vdata = _read(process, vtable, 0x40)
    if vdata is not None:
        worker = _u64(vdata, 0x30)
        packet["worker_slot_0x30"] = worker
        packet["worker_slot_0x30_va"] = _module_va(target, worker)
    return packet


def _stack(thread, max_frames=12):
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
                "rbp": _u(frame, "rbp"),
            }
        )
    return frames


def _neighborhood(process, base, stride, x, y, radius):
    rows = []
    read_ok = True
    for dy in range(-radius, radius + 1):
        row = []
        for dx in range(-radius, radius + 1):
            addr = base + ((y + dy) * stride + (x + dx)) * 16
            vec = _vec4(process, addr)
            if not vec["read_ok"]:
                read_ok = False
            row.append({"dx": dx, "dy": dy, "addr": addr, "vec4": vec})
        rows.append(row)
    return {"read_ok": read_ok, "radius": radius, "rows": rows}


def _descriptor_pixel(process, descriptor, x, y):
    base = descriptor.get("data_ptr_0x20") or 0
    stride = int(descriptor.get("stride_0x18") or 0)
    return _vec4(process, base + (y * stride + x) * 16)


def _sample_packet(frame, meta, regs):
    thread = frame.GetThread()
    process = thread.GetProcess()
    rbp = regs["rbp"]
    callback_addr = _qword(process, rbp - 0x1D8) or 0
    callback = _callback(process, callback_addr) if callback_addr else None

    source_desc = _descriptor(process, rbp - 0x60)
    scale_desc = _descriptor(process, rbp - 0x90)
    radius = meta["radius"]
    x = int(regs[meta["x_reg"]])
    if "y_reg" in meta:
        y = int(regs[meta["y_reg"]])
    else:
        y = int(_qword(process, rbp + meta["y_stack_qword"]) or 0)

    source_base = source_desc.get("data_ptr_0x20") or 0
    source_stride = int(source_desc.get("stride_0x18") or 0)
    scale_base = scale_desc.get("data_ptr_0x20") or 0
    scale_stride = int(scale_desc.get("stride_0x18") or 0)

    callback_decodes = callback.get("field_decodes", {}) if callback else {}
    callback_scale_desc = callback_decodes.get("+0x08_range_scale_descriptor", {})
    callback_source_desc = callback_decodes.get("+0x10_source_descriptor", {})
    callback_dest_desc = callback_decodes.get("+0x18_destination_descriptor", {})

    center_addr = source_base + (y * source_stride + x) * 16
    scale_addr = scale_base + (y * scale_stride + x) * 16
    dest_addr = regs[meta["dest_base_reg"]] + regs[meta["dest_offset_reg"]]

    xmms = _all_xmms(frame)
    return {
        "site": meta["name"],
        "site_va": _module_va(process.GetTarget(), frame.GetPC()),
        "worker_va": meta["worker"],
        "radius": radius,
        "x": x,
        "y": y,
        "registers": regs,
        "xmms": xmms,
        "observed_store_xmm0": xmms.get("xmm0"),
        "observed_sum_weight": xmms.get(meta["sum_weight_xmm"]),
        "observed_sum_weighted": xmms.get(meta["sum_weighted_xmm"]),
        "callback": callback,
        "local_source_descriptor_rbp_minus_0x60": source_desc,
        "local_range_scale_descriptor_rbp_minus_0x90": scale_desc,
        "source_center": _vec4(process, center_addr),
        "range_scale_vec4": _vec4(process, scale_addr),
        "callback_source_at_xy": _descriptor_pixel(
            process, callback_source_desc, x, y
        ),
        "callback_range_scale_at_xy": _descriptor_pixel(
            process, callback_scale_desc, x, y
        ),
        "callback_destination_after_at_xy": _descriptor_pixel(
            process, callback_dest_desc, x, y
        ),
        "source_neighborhood": _neighborhood(
            process, source_base, source_stride, x, y, radius
        ),
        "dest_addr": dest_addr,
        "dest_after_vec4": _vec4(process, dest_addr),
        "stack": _stack(thread),
    }


def _disable_breakpoint(debugger, name):
    bp_id = _state()["breakpoint_ids"].get(name)
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id) if bp_id else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def site(frame, bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    site_va = _module_va(target, frame.GetPC())
    meta = SITES.get(site_va)
    if meta is None:
        state["errors"].append(f"unknown site 0x{site_va:x}")
        return False

    name = meta["name"]
    state["counts"][name] = state["counts"].get(name, 0) + 1
    per_site_samples = [sample for sample in state["samples"] if sample.get("site") == name]
    if len(per_site_samples) < state["sample_limit"]:
        try:
            state["samples"].append(_sample_packet(frame, meta, _registers(frame)))
        except Exception as exc:
            state["errors"].append(f"{name}: sample failed: {exc}")

    if state["counts"][name] >= state["site_cap"]:
        _disable_breakpoint(target.GetDebugger(), name)
        if name not in state["disabled_after_cap"]:
            state["disabled_after_cap"].append(name)
    return False


def install(debugger, selection="both"):
    state = _state()
    target = debugger.GetSelectedTarget()
    selected = {item.strip().lower() for item in str(selection).split(",") if item.strip()}
    if not selected or "both" in selected:
        selected = {"0x2fb320", "0x2fd070", "radius2", "radius4"}

    installed = {}
    for va, meta in sorted(SITES.items()):
        wanted = (
            f"0x{meta['worker']:x}" in selected
            or f"radius{meta['radius']}" in selected
        )
        if not wanted:
            continue
        before = target.GetNumBreakpoints()
        debugger.HandleCommand(f"breakpoint set --shlib libcp.dylib --address 0x{va:x}")
        if target.GetNumBreakpoints() <= before:
            state["errors"].append(f"breakpoint creation failed for {meta['name']}")
            continue
        bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
        bp.SetScriptCallbackFunction("selected_bilateral_formula_probe.site")
        state["breakpoint_ids"][meta["name"]] = bp.GetID()
        installed[meta["name"]] = bp.GetID()
    print("L16_SELECTED_BILATERAL_FORMULA_INSTALLED", installed)


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


def drive_until_exit_or_step_cap(debugger, max_steps=20000):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while (
        process.IsValid()
        and process.GetState() == lldb.eStateStopped
        and steps < max_steps
    ):
        steps += 1
        process.Continue()
    state["drive_steps"] = state.get("drive_steps", 0) + steps
    if process.IsValid() and process.GetState() == lldb.eStateStopped and steps >= max_steps:
        state["drive_hit_step_cap"] = True
    else:
        state["drive_hit_step_cap"] = state.get("drive_hit_step_cap", False)
    print("L16_SELECTED_BILATERAL_FORMULA_DRIVE_STEPS", steps)


def payload(debugger):
    return {
        "process": _process_packet(debugger),
        "breakpoint_hit_counts": _breakpoint_hit_counts(debugger),
        **_state(),
    }


def write_report(debugger, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_SELECTED_BILATERAL_FORMULA_WROTE", path)


def report(debugger):
    print("L16_SELECTED_BILATERAL_FORMULA_BEGIN")
    print(json.dumps(payload(debugger), indent=2, sort_keys=True))
    print("L16_SELECTED_BILATERAL_FORMULA_END")
