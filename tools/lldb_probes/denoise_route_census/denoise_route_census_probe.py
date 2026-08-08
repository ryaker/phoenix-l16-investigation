import builtins
import json
import os
import struct


SET_DENOISING = {
    0x344340: "setDenoising_36_0x344340",
    0x344430: "setDenoising_37_0x344430",
    0x344E50: "setDenoising_38_0x344e50",
    0x344F20: "setDenoising_39_0x344f20",
    0x344FF0: "setDenoising_40_0x344ff0",
    0x3450C0: "setDenoising_41_0x3450c0",
    0x3451B0: "setDenoising_42_0x3451b0",
    0x345280: "setDenoising_43_0x345280",
    0x345350: "setDenoising_44_0x345350",
    0x345420: "setDenoising_45_0x345420",
    0x3454F0: "setDenoising_46_0x3454f0",
    0x3455E0: "setDenoising_47_0x3455e0",
    0x3456B0: "setDenoising_48_0x3456b0",
    0x345780: "setDenoising_49_0x345780",
    0x345850: "setDenoising_50_0x345850",
    0x345920: "setDenoising_51_0x345920",
    0x345A10: "setDenoising_52_0x345a10",
    0x345AE0: "setDenoising_53_0x345ae0",
    0x345BB0: "setDenoising_54_0x345bb0",
    0x345C80: "setDenoising_55_0x345c80",
}

CNR_CLOSURES = {
    0x34B3B0: "setCNR_0x34b3b0",
    0x34B8A0: "setCNR_0x34b8a0",
    0x34B970: "setCNR_0x34b970",
    0x34B3F0: "CNR_effective_0x34b3f0",
}

ALGORITHMS = {
    0x2F53D0: "helper_chain_0x2f53d0",
    0x2F6420: "callback_selector_0x2f6420",
    0x2F6AD0: "bilateral_arm_0x2f6ad0",
    0x2F78E0: "bilateral_arm_0x2f78e0",
    0x2F87E0: "bilateral_arm_0x2f87e0",
    0x2F97E0: "bilateral_arm_0x2f97e0",
    0x2FA5D0: "bilateral_arm_0x2fa5d0",
    0x2FB320: "bilateral_arm_0x2fb320",
    0x2FC140: "bilateral_arm_0x2fc140",
    0x2FD070: "bilateral_arm_0x2fd070",
    0x3048B0: "ImageDenoiseNLM_0x3048b0",
    0x304B10: "ImageDenoiseNLM_callback_0x304b10",
    0x3066D0: "ImageDenoiseNLM_positive_0x3066d0",
    0x3070A0: "PatchNLM_adapter_0x3070a0",
    0x3070E0: "PatchNLM_body_0x3070e0",
    0x307D90: "PatchNLM_normalize_0x307d90",
    0x307EE0: "ColorNoiseReduction_body_0x307ee0",
    0x308520: "ColorNoiseReduction_callback_0x308520",
    0x3085A0: "ColorNoiseReduction_worker_0x3085a0",
}

SITES = {}
for _group, _items in (
    ("set_denoising", SET_DENOISING),
    ("cnr", CNR_CLOSURES),
    ("algorithm", ALGORITHMS),
):
    for _va, _name in _items.items():
        SITES[_va] = {"name": _name, "group": _group}


def reset(label="", site_cap=128, sample_limit=4, event_limit=512):
    builtins.l16_denoise_route_census = {
        "label": label,
        "site_cap": site_cap,
        "sample_limit": sample_limit,
        "event_limit": event_limit,
        "sequence": 0,
        "breakpoint_ids": {},
        "counts": {site["name"]: 0 for site in SITES.values()},
        "group_counts": {"set_denoising": 0, "cnr": 0, "algorithm": 0},
        "disabled_after_cap": [],
        "events": [],
        "samples": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_denoise_route_census"):
        reset()
    return builtins.l16_denoise_route_census


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _reg_f32(frame, name):
    lldb = builtins.__import__("lldb")
    reg = frame.FindRegister(name)
    try:
        error = lldb.SBError()
        value = reg.GetData().GetFloat(error, 0)
        if error.Success():
            return float(value)
    except Exception:
        pass
    try:
        value = reg.GetChildAtIndex(0).GetValue()
        if value is not None:
            return float(value)
    except Exception:
        pass
    return None


def _reg_text(frame, name):
    reg = frame.FindRegister(name)
    return {
        "value": reg.GetValue(),
        "summary": reg.GetSummary(),
        "num_children": reg.GetNumChildren(),
    }


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


def _mem_packet(process, addr, size=0x40):
    data = _read(process, addr, size)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "size": size,
        "hex": data.hex(),
        "i32": _i32s(data[: (len(data) // 4) * 4]),
        "f32": _f32s(data[: (len(data) // 4) * 4]),
        "qwords": [_u64(data, off) for off in range(0, len(data) - 7, 8)],
    }


def _read_qword(process, addr):
    data = _read(process, addr, 8)
    return _u64(data) if data is not None else None


def _callable_packet(target, process, addr):
    vtable = _read_qword(process, addr)
    slot = _read_qword(process, vtable + 0x30) if vtable else None
    return {
        "addr": addr,
        "vtable": vtable,
        "vtable_va": _module_va(target, vtable) if vtable else None,
        "slot_0x30": slot,
        "slot_0x30_va": _module_va(target, slot) if slot else None,
    }


def _descriptor(process, addr):
    data = _read(process, addr, 0x30)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "i32": _i32s(data),
        "qwords": [_u64(data, off) for off in range(0, 0x30, 8)],
    }


def _cnr_entry_packet(process, regs):
    obj = regs["rdi"]
    record = regs["rsi"]
    out = {
        "object": obj,
        "record": record,
        "record_0x00": _mem_packet(process, record, 0xA0),
        "object_0x40": _mem_packet(process, obj + 0x40, 0x80),
        "object_0xA8": _mem_packet(process, obj + 0xA8, 0x40),
        "object_params": {
            "f32_0x15d8": None,
            "f32_0x1624": None,
        },
    }
    for off, key in ((0x15D8, "f32_0x15d8"), (0x1624, "f32_0x1624")):
        data = _read(process, obj + off, 4)
        if data is not None:
            out["object_params"][key] = struct.unpack("<f", data)[0]
    return out


def _cnr_body_packet(frame, process, regs):
    stack_arg = _read(process, regs["rsp"] + 8, 4)
    return {
        "xmm0_f32": _reg_f32(frame, "xmm0"),
        "xmm1_f32": _reg_f32(frame, "xmm1"),
        "xmm0_reg": _reg_text(frame, "xmm0"),
        "xmm1_reg": _reg_text(frame, "xmm1"),
        "r9d": regs["r9"] & 0xFFFFFFFF,
        "stack_i32_arg0": struct.unpack("<i", stack_arg)[0] if stack_arg else None,
        "rdi_descriptor": _descriptor(process, regs["rdi"]),
        "rsi_descriptor": _descriptor(process, regs["rsi"]),
        "rdx_descriptor": _descriptor(process, regs["rdx"]),
        "rcx_mem": _mem_packet(process, regs["rcx"], 0x20),
        "r8_mem": _mem_packet(process, regs["r8"], 0x40),
    }


def _patch_nlm_packet(process, regs):
    return {
        "callback_or_config": _mem_packet(process, regs["rdi"], 0x50),
        "roi_or_rect": _mem_packet(process, regs["rsi"], 0x20),
        "descriptor_rdi_plus_8": _descriptor(process, _read_qword(process, regs["rdi"] + 0x8) or 0),
        "descriptor_rdi_plus_28": _descriptor(process, _read_qword(process, regs["rdi"] + 0x28) or 0),
        "config_words": _mem_packet(process, _read_qword(process, regs["rdi"]) or 0, 0x20),
    }


def _site_packet(frame, site_va, regs):
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    packet = {
        "callable_rdi": _callable_packet(target, process, regs["rdi"]),
        "rdi_mem": _mem_packet(process, regs["rdi"], 0x40),
        "rsi_mem": _mem_packet(process, regs["rsi"], 0x40),
        "descriptors": {
            reg: _descriptor(process, regs[reg])
            for reg in ("rdi", "rsi", "rdx", "rcx", "r8", "r9")
        },
    }
    if site_va == 0x34B3F0:
        packet["cnr_effective_entry"] = _cnr_entry_packet(process, regs)
    if site_va == 0x307EE0:
        packet["cnr_body_entry"] = _cnr_body_packet(frame, process, regs)
    if site_va == 0x3070E0:
        packet["patch_nlm_entry"] = _patch_nlm_packet(process, regs)
    return packet


def _disable_breakpoint(debugger, name):
    bp_id = _state()["breakpoint_ids"].get(name)
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id) if bp_id else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def site(frame, bp_loc, _dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    site_va = _module_va(target, frame.GetPC())
    meta = SITES.get(site_va)
    if meta is None:
        state["errors"].append(f"unknown site 0x{site_va:x}")
        return False

    name = meta["name"]
    group = meta["group"]
    state["sequence"] += 1
    state["counts"][name] = state["counts"].get(name, 0) + 1
    state["group_counts"][group] = state["group_counts"].get(group, 0) + 1

    if len(state["events"]) < state["event_limit"]:
        state["events"].append(
            {
                "seq": state["sequence"],
                "site": name,
                "site_va": site_va,
                "group": group,
                "thread_id": thread.GetThreadID(),
                "return_address": _read_qword(process, _u(frame, "rsp")),
                "return_address_va": _module_va(target, _read_qword(process, _u(frame, "rsp")) or 0),
            }
        )

    per_site_samples = [
        item for item in state["samples"] if item.get("site") == name
    ]
    if len(per_site_samples) < state["sample_limit"]:
        regs = _registers(frame)
        state["samples"].append(
            {
                "seq": state["sequence"],
                "site": name,
                "site_va": site_va,
                "group": group,
                "registers": regs,
                "packet": _site_packet(frame, site_va, regs),
                "stack": _stack(thread),
            }
        )

    if state["counts"][name] >= state["site_cap"]:
        _disable_breakpoint(target.GetDebugger(), name)
        if name not in state["disabled_after_cap"]:
            state["disabled_after_cap"].append(name)
    return False


def _site_enabled(meta, filters):
    if not filters:
        return True
    if meta["group"] in filters:
        return True
    name = meta["name"].lower()
    return any(item in name for item in filters)


def install(debugger, group_filter=""):
    state = _state()
    target = debugger.GetSelectedTarget()
    callbacks = {}
    filters = {
        item.strip().lower()
        for item in str(group_filter).split(",")
        if item.strip()
    }
    for va, meta in sorted(SITES.items()):
        if not _site_enabled(meta, filters):
            continue
        before = target.GetNumBreakpoints()
        debugger.HandleCommand(
            f"breakpoint set --shlib libcp.dylib --address 0x{va:x}"
        )
        if target.GetNumBreakpoints() <= before:
            state["errors"].append(f"breakpoint creation failed for {meta['name']}")
            continue
        bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
        bp.SetScriptCallbackFunction("denoise_route_census_probe.site")
        state["breakpoint_ids"][meta["name"]] = bp.GetID()
        callbacks[meta["name"]] = bp.GetID()
    print("L16_DENOISE_ROUTE_CENSUS_INSTALLED", callbacks)


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
    print("L16_DENOISE_ROUTE_CENSUS_DRIVE_STEPS", steps)


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
    print("WROTE", path)


def report(debugger):
    print(json.dumps(payload(debugger), indent=2, sort_keys=True))
