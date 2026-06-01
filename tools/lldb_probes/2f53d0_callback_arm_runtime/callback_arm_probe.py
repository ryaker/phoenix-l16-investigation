import builtins
import json
import struct


GATE = 0x3E4B09

CALLSITES = {
    0x2F6518: {
        "label": "call_0x5440_arm_2f6ad0",
        "expected_vtable": 0x65A4E0,
        "expected_worker": 0x2F6AD0,
        "object_slot": -0x160,
        "storage_slot": -0x180,
    },
    0x2F6597: {
        "label": "call_0x5440_arm_2f78e0",
        "expected_vtable": 0x65A568,
        "expected_worker": 0x2F78E0,
        "object_slot": -0x130,
        "storage_slot": -0x150,
    },
    0x2F6616: {
        "label": "call_0x5440_arm_2f97e0",
        "expected_vtable": 0x65A668,
        "expected_worker": 0x2F97E0,
        "object_slot": -0xD0,
        "storage_slot": -0xF0,
    },
    0x2F6695: {
        "label": "call_0x5440_arm_2f87e0",
        "expected_vtable": 0x65A5E8,
        "expected_worker": 0x2F87E0,
        "object_slot": -0x100,
        "storage_slot": -0x120,
    },
    0x2F6766: {
        "label": "call_0x5440_arm_2fa5d0",
        "expected_vtable": 0x65A6E8,
        "expected_worker": 0x2FA5D0,
        "object_slot": -0xA0,
        "storage_slot": -0xC0,
    },
    0x2F67E2: {
        "label": "call_0x5440_arm_2fb320",
        "expected_vtable": 0x65A768,
        "expected_worker": 0x2FB320,
        "object_slot": -0x70,
        "storage_slot": -0x90,
    },
    0x2F685E: {
        "label": "call_0x5440_arm_2fd070",
        "expected_vtable": 0x65A868,
        "expected_worker": 0x2FD070,
        "object_slot": -0x190,
        "storage_slot": -0x1B0,
    },
    0x2F68D0: {
        "label": "call_0x5440_arm_2fc140",
        "expected_vtable": 0x65A7E8,
        "expected_worker": 0x2FC140,
        "object_slot": -0x40,
        "storage_slot": -0x60,
    },
}

WORKER_SITES = {
    0x2F78E0: "worker_entry_2f78e0",
    0x2F8584: "normalizer_mulps_2f8584",
    0x2F859F: "normalizer_rcpps_2f859f",
    0x2F85A5: "normalizer_store_2f85a5",
}


def reset(label="", callsite_cap=256, worker_cap=64, sample_limit=96):
    builtins.l16_2f53d0_callback_arm = {
        "label": label,
        "callsite_cap": callsite_cap,
        "worker_cap": worker_cap,
        "sample_limit": sample_limit,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
        "gate_hits": 0,
        "dynamic_breakpoints_installed": False,
        "breakpoint_ids": {},
        "callsite_counts": {info["label"]: 0 for info in CALLSITES.values()},
        "worker_counts": {label: 0 for label in WORKER_SITES.values()},
        "disabled_after_cap": [],
        "callsite_samples": [],
        "worker_samples": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_2f53d0_callback_arm"):
        reset()
    return builtins.l16_2f53d0_callback_arm


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


def _descriptor(process, addr):
    data = _read(process, addr, 0x30)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "first_12_i32": _i32s(data),
        "qwords": [_u64(data, off) for off in range(0, 0x30, 8)],
    }


def _callback_object(process, rbp, info):
    object_slot = rbp + info["object_slot"]
    object_slot_data = _read(process, object_slot, 8)
    if object_slot_data is None:
        return {"object_slot": object_slot, "read_ok": False}

    obj = _u64(object_slot_data)
    out = {
        "object_slot": object_slot,
        "storage_addr": rbp + info["storage_slot"],
        "object": obj,
        "read_ok": bool(obj),
    }
    if not obj:
        return out

    data = _read(process, obj, 0x28)
    if data is None:
        out["object_read_ok"] = False
        return out

    target = process.GetTarget()
    vtable = _u64(data, 0)
    vtable_va = _module_va(target, vtable)
    out.update(
        {
            "object_read_ok": True,
            "vtable": vtable,
            "vtable_va": vtable_va,
            "expected_vtable": info["expected_vtable"],
            "vtable_matches_expected": vtable_va == info["expected_vtable"],
            "fields": {
                "+0x08": _u64(data, 0x08),
                "+0x10": _u64(data, 0x10),
                "+0x18": _u64(data, 0x18),
                "+0x20": _u64(data, 0x20),
            },
        }
    )

    vdata = _read(process, vtable, 0x40)
    if vdata is not None:
        worker = _u64(vdata, 0x30)
        worker_va = _module_va(target, worker)
        out.update(
            {
                "worker_slot_0x30": worker,
                "worker_slot_0x30_va": worker_va,
                "expected_worker": info["expected_worker"],
                "worker_matches_expected": worker_va == info["expected_worker"],
            }
        )
    return out


def _sample_limit_reached(kind):
    state = _state()
    key = "callsite_samples" if kind == "callsite" else "worker_samples"
    return len(state[key]) >= state["sample_limit"]


def _disable_breakpoint(debugger, name):
    bp_id = _state()["breakpoint_ids"].get(name)
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id) if bp_id else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def _create_breakpoint(target, va, callback, name):
    base = _libcp_base(target)
    if base is None:
        _state()["errors"].append("libcp base unavailable")
        return None
    bp = target.BreakpointCreateByAddress(base + va)
    bp.SetScriptCallbackFunction(callback)
    _state()["breakpoint_ids"][name] = bp.GetID()
    return bp


def _install_dynamic(debugger):
    state = _state()
    if state["dynamic_breakpoints_installed"]:
        return
    target = debugger.GetSelectedTarget()
    for va, info in CALLSITES.items():
        _create_breakpoint(
            target,
            va,
            "callback_arm_probe.callsite",
            info["label"],
        )
    for va, label in WORKER_SITES.items():
        _create_breakpoint(
            target,
            va,
            "callback_arm_probe.worker",
            label,
        )
    state["dynamic_breakpoints_installed"] = True


def gate(frame, bp_loc, internal_dict):
    state = _state()
    state["gate_hits"] += 1
    debugger = frame.GetThread().GetProcess().GetTarget().GetDebugger()
    _install_dynamic(debugger)
    _disable_breakpoint(debugger, "gate_0x3e4b09")
    return False


def callsite(frame, bp_loc, internal_dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    site_va = _module_va(target, frame.GetPC())
    info = CALLSITES.get(site_va)
    if info is None:
        state["errors"].append(f"unknown callsite {site_va}")
        return False

    label = info["label"]
    state["callsite_counts"][label] = state["callsite_counts"].get(label, 0) + 1
    if not _sample_limit_reached("callsite"):
        regs = _registers(frame)
        sample = {
            "site": label,
            "site_va": site_va,
            "registers": regs,
            "callback": _callback_object(process, regs["rbp"], info),
            "arg_descriptors": {
                reg: _descriptor(process, regs[reg])
                for reg in ("rdi", "rsi", "rdx")
            },
            "stack": _stack(thread),
        }
        state["callsite_samples"].append(sample)

    if state["callsite_counts"][label] >= state["callsite_cap"]:
        _disable_breakpoint(target.GetDebugger(), label)
        if label not in state["disabled_after_cap"]:
            state["disabled_after_cap"].append(label)
    return False


def worker(frame, bp_loc, internal_dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    site_va = _module_va(target, frame.GetPC())
    label = WORKER_SITES.get(site_va)
    if label is None:
        state["errors"].append(f"unknown worker site {site_va}")
        return False

    state["worker_counts"][label] = state["worker_counts"].get(label, 0) + 1
    if not _sample_limit_reached("worker"):
        regs = _registers(frame)
        sample = {
            "site": label,
            "site_va": site_va,
            "registers": regs,
            "arg_descriptors": {
                reg: _descriptor(process, regs[reg])
                for reg in ("rdi", "rsi", "rdx", "rcx", "r8", "r9", "r12")
            },
            "stack": _stack(thread),
        }
        if site_va in (0x2F8584, 0x2F859F, 0x2F85A5):
            source = regs.get("rcx", 0)
            if source:
                data = _read(process, source - 0x20, 0x60)
                if data is not None:
                    sample["source_window_rcx_minus_0x20_f32"] = _f32s(data)
        state["worker_samples"].append(sample)

    if state["worker_counts"][label] >= state["worker_cap"]:
        _disable_breakpoint(target.GetDebugger(), label)
        if label not in state["disabled_after_cap"]:
            state["disabled_after_cap"].append(label)
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    count = target.GetNumBreakpoints()
    if count < 1:
        _state()["errors"].append("expected gate breakpoint")
        print("L16_CALLBACK_ARM_ATTACH_ERROR expected gate breakpoint")
        return
    bp = target.GetBreakpointAtIndex(count - 1)
    bp.SetScriptCallbackFunction("callback_arm_probe.gate")
    _state()["breakpoint_ids"] = {"gate_0x3e4b09": bp.GetID()}
    print("L16_CALLBACK_ARM_ATTACHED", _state()["breakpoint_ids"])


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


def drive_until_exit_or_step_cap(debugger, max_steps=16000):
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
    print("L16_CALLBACK_ARM_DRIVE_STEPS", steps)


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
    print("L16_CALLBACK_ARM_WROTE", path)


def report(debugger):
    print("L16_CALLBACK_ARM_BEGIN")
    print(json.dumps(payload(debugger), indent=2, sort_keys=True))
    print("L16_CALLBACK_ARM_END")
