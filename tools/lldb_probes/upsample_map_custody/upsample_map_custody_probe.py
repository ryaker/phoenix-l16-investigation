import builtins
import json
import struct


SITES = {
    0x26A890: "upsample_ctor_entry",
    0x26AA10: "upsample_run_entry",
    0x26AA30: "prev_layer_map_slot_call",
    0x26AA39: "prev_layer_map_after_call",
    0x26ABE9: "tmp_map_build_call_0x29ed90",
    0x26ABEE: "tmp_map_build_after_0x29ed90",
    0x26ABFC: "tmp_map_copy_call_0x2673a0",
    0x26AC13: "upsample_map_copy_call_0xf340",
    0x26AC18: "upsample_map_copy_after_0xf340",
    0x26848F: "provider_virtual_call_0x26848f",
    0x3F7485: "cross_after_0x268480",
    0x3F749E: "cross_after_0x25e500",
    0x366CBE: "consumer_map_loaded",
}

EXPECTED_PROVIDER_RETURNS = {0x3F7485}
UPSAMPLE_VTABLE_VA = 0x658EB0
UPSAMPLE_SLOT_90_VA = 0x26B590


def reset(label="", site_cap=128, sample_limit=96):
    builtins.l16_upsample_map_custody = {
        "label": label,
        "site_cap": site_cap,
        "sample_limit": sample_limit,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
        "breakpoint_ids": {},
        "counts": {name: 0 for name in SITES.values()},
        "disabled_after_cap": [],
        "objects": {},
        "writer_objects": {},
        "provider_objects": {},
        "provider_target_counts": {},
        "provider_return_counts": {},
        "record_map_counts": {},
        "consumer_map_counts": {},
        "samples": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_upsample_map_custody"):
        reset()
    return builtins.l16_upsample_map_custody


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


def _f32(data, off=0):
    return struct.unpack_from("<f", data, off)[0]


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


def _read_qword(process, addr):
    data = _read(process, addr, 8)
    return _u64(data) if data is not None else None


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
                "rbp": _u(frame, "rbp"),
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
        "qwords": [_u64(data, off) for off in range(0, 0x30, 8)],
        "u32": [_u32(data, off) for off in range(0, 0x30, 4)],
        "f32": [_f32(data, off) for off in range(0, 0x30, 4)],
        "stride_0x18_u32": _u32(data, 0x18),
        "data_ptr_0x20": _u64(data, 0x20),
    }


def _upsample_object(process, obj):
    if not obj:
        return {"object": obj, "read_ok": False}
    return {
        "object": obj,
        "vtable": _read_qword(process, obj),
        "index_0x30": _u32(_read(process, obj + 0x30, 4), 0)
        if _read(process, obj + 0x30, 4) is not None
        else None,
        "map_0x90": _descriptor(process, obj + 0x90),
        "map_0xc0": _descriptor(process, obj + 0xC0),
    }


def _record50(process, addr):
    data = _read(process, addr, 0x50)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "row_f32": [_f32(data, off) for off in range(0x00, 0x40, 4)],
        "map_ptr_0x40": _u64(data, 0x40),
        "scale_x_0x48": _f32(data, 0x48),
        "scale_y_0x4c": _f32(data, 0x4C),
    }


def _caller_return_va(frame):
    thread = frame.GetThread()
    if thread.GetNumFrames() < 2:
        return None
    return _module_va(thread.GetProcess().GetTarget(), thread.GetFrameAtIndex(1).GetPC())


def _bump_count(name):
    state = _state()
    state["counts"][name] = state["counts"].get(name, 0) + 1


def _mark_object(obj, key, value=True):
    if not obj:
        return
    objects = _state()["objects"]
    packet = objects.setdefault(hex(obj), {})
    packet[key] = value


def _disable_breakpoint(debugger, name):
    bp_id = _state()["breakpoint_ids"].get(name)
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id) if bp_id else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def _site_cap(name):
    if name == "consumer_map_loaded":
        return 16
    if name.startswith("upsample_") or name.startswith("tmp_") or name.startswith("prev_"):
        return 64
    return _state()["site_cap"]


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

    regs = _registers(frame)
    caller_return = _caller_return_va(frame)
    if site_va == 0x26848F and caller_return not in EXPECTED_PROVIDER_RETURNS:
        return False

    _bump_count(name)
    sample = {
        "site": name,
        "site_va": site_va,
        "caller_return_va": caller_return,
        "registers": regs,
        "stack": _stack(thread),
    }

    if site_va == 0x26A890:
        obj = regs["rdi"]
        _mark_object(obj, "ctor_seen")
        sample["upsample_object"] = _upsample_object(process, obj)
    elif site_va == 0x26AA10:
        obj = regs["rdi"]
        prev = regs["rsi"]
        _mark_object(obj, "run_seen")
        sample["upsample_object"] = _upsample_object(process, obj)
        sample["previous_layer_object"] = prev
        sample["previous_layer_vtable"] = _read_qword(process, prev)
    elif site_va == 0x26AA30:
        prev = regs["rdi"]
        vtable = _read_qword(process, prev)
        slot = _read_qword(process, vtable + 0x90) if vtable else None
        sample["previous_layer_object"] = prev
        sample["previous_layer_vtable"] = vtable
        sample["previous_layer_vtable_va"] = _module_va(target, vtable) if vtable else None
        sample["previous_layer_slot_0x90"] = slot
        sample["previous_layer_slot_0x90_va"] = _module_va(target, slot) if slot else None
    elif site_va == 0x26AA39:
        sample["previous_layer_map_descriptor"] = _descriptor(process, regs["r14"])
    elif site_va == 0x26ABE9:
        sample["build_args"] = {
            "dst_rdi": regs["rdi"],
            "src_rsi": regs["rsi"],
            "arg_rdx": regs["rdx"],
            "arg_rcx": regs["rcx"],
            "src_descriptor": _descriptor(process, regs["rsi"]),
        }
    elif site_va == 0x26ABEE:
        sample["tmp_descriptor_after_0x29ed90"] = _descriptor(process, regs["rbp"] - 0x100)
    elif site_va == 0x26ABFC:
        sample["copy_args_0x2673a0"] = {
            "dst_rdi": regs["rdi"],
            "src_rsi": regs["rsi"],
            "src_descriptor": _descriptor(process, regs["rsi"]),
        }
    elif site_va == 0x26AC13:
        dest = regs["rdi"]
        obj = dest - 0x90
        _mark_object(obj, "writer_call_seen")
        state["writer_objects"][hex(obj)] = state["writer_objects"].get(hex(obj), 0) + 1
        sample["writer"] = {
            "object": obj,
            "dest_descriptor": dest,
            "source_descriptor": regs["rsi"],
            "dest_before": _descriptor(process, dest),
            "source_before": _descriptor(process, regs["rsi"]),
        }
    elif site_va == 0x26AC18:
        dest = regs["r14"]
        obj = dest - 0x90
        _mark_object(obj, "writer_after_seen")
        state["writer_objects"][hex(obj)] = state["writer_objects"].get(hex(obj), 0) + 1
        sample["writer_after"] = {
            "object": obj,
            "dest_descriptor": dest,
            "dest_after": _descriptor(process, dest),
        }
    elif site_va == 0x26848F:
        obj = regs["rdi"]
        vtable = regs["rax"]
        slot = _read_qword(process, vtable + 0x90) if vtable else None
        slot_va = _module_va(target, slot) if slot else None
        state["provider_target_counts"][str(slot_va)] = (
            state["provider_target_counts"].get(str(slot_va), 0) + 1
        )
        if _module_va(target, vtable) == UPSAMPLE_VTABLE_VA and slot_va == UPSAMPLE_SLOT_90_VA:
            state["provider_objects"][hex(obj)] = state["provider_objects"].get(hex(obj), 0) + 1
            _mark_object(obj, "provider_seen")
        sample["provider_virtual"] = {
            "object": obj,
            "vtable": vtable,
            "vtable_va": _module_va(target, vtable),
            "slot_0x90": slot,
            "slot_0x90_va": slot_va,
            "expected_return_descriptor": obj + 0x90,
            "descriptor": _descriptor(process, obj + 0x90),
        }
    elif site_va == 0x3F7485:
        key = hex(regs["rax"])
        state["provider_return_counts"][key] = state["provider_return_counts"].get(key, 0) + 1
        sample["provider_return_descriptor"] = _descriptor(process, regs["rax"])
        sample["provider_return_implied_object"] = regs["rax"] - 0x90
    elif site_va == 0x3F749E:
        record = _record50(process, regs["r15"])
        sample["record_at_r15"] = record
        if record.get("read_ok"):
            key = hex(record["map_ptr_0x40"])
            state["record_map_counts"][key] = state["record_map_counts"].get(key, 0) + 1
            sample["record_map_descriptor"] = _descriptor(process, record["map_ptr_0x40"])
            sample["record_map_implied_object"] = record["map_ptr_0x40"] - 0x90
    elif site_va == 0x366CBE:
        key = hex(regs["rax"])
        state["consumer_map_counts"][key] = state["consumer_map_counts"].get(key, 0) + 1
        sample["consumer_map_descriptor"] = _descriptor(process, regs["rax"])
        sample["consumer_map_implied_object"] = regs["rax"] - 0x90

    if len(state["samples"]) < state["sample_limit"]:
        state["samples"].append(sample)

    if state["counts"][name] >= _site_cap(name):
        _disable_breakpoint(target.GetDebugger(), name)
        if name not in state["disabled_after_cap"]:
            state["disabled_after_cap"].append(name)
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    count = target.GetNumBreakpoints()
    ids = {}
    for index in range(count):
        bp = target.GetBreakpointAtIndex(index)
        if not bp or not bp.IsValid() or bp.GetNumLocations() < 1:
            continue
        loc = bp.GetLocationAtIndex(0)
        site_va = loc.GetAddress().GetFileAddress()
        name = SITES.get(site_va)
        if name is None:
            continue
        bp.SetScriptCallbackFunction("upsample_map_custody_probe.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    print("L16_UPSAMPLE_MAP_ATTACHED", ids)


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
    state["drive_steps"] += steps
    if process.IsValid() and process.GetState() == lldb.eStateStopped and steps >= max_steps:
        state["drive_hit_step_cap"] = True
    print("L16_UPSAMPLE_MAP_DRIVE_STEPS", steps)


def payload(debugger):
    return {
        "process": _process_packet(debugger),
        "breakpoint_hit_counts": _breakpoint_hit_counts(debugger),
        **_state(),
    }


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_UPSAMPLE_MAP_WROTE", path)


def report(debugger):
    print("L16_UPSAMPLE_MAP_BEGIN")
    print(json.dumps(payload(debugger), indent=2, sort_keys=True))
    print("L16_UPSAMPLE_MAP_END")
