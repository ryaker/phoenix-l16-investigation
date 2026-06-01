import builtins
import json
import math
import struct


GATE = 0x3E4B09
ENTRY = 0x2FB320
AFTER_STORE = 0x2FBF05


def reset(label="", entry_cap=64, store_cap=64, sample_limit=96):
    builtins.l16_2fb320_worker = {
        "label": label,
        "entry_cap": entry_cap,
        "store_cap": store_cap,
        "sample_limit": sample_limit,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
        "gate_hits": 0,
        "dynamic_breakpoints_installed": False,
        "breakpoint_ids": {},
        "counts": {
            "entry_0x2fb320": 0,
            "after_store_0x2fbf05": 0,
        },
        "disabled_after_cap": [],
        "entry_samples": [],
        "store_samples": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_2fb320_worker"):
        reset()
    return builtins.l16_2fb320_worker


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


def _f32(data, off=0):
    return struct.unpack_from("<f", data, off)[0]


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


def _rect(process, addr):
    data = _read(process, addr, 0x10)
    if data is None:
        return {"addr": addr, "read_ok": False}
    vals = _i32s(data)
    return {
        "addr": addr,
        "read_ok": True,
        "i32": vals,
        "width": vals[2] - vals[0],
        "height": vals[3] - vals[1],
    }


def _vec4(process, addr):
    data = _read(process, addr, 0x10)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "f32": _f32s(data),
        "i32": _i32s(data),
    }


def _descriptor(process, addr):
    data = _read(process, addr, 0x30)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "rect_i32_0x00": [_i32(data, off) for off in range(0, 0x10, 4)],
        "width_0x10": _u32(data, 0x10),
        "height_0x14": _u32(data, 0x14),
        "stride_0x18": _u32(data, 0x18),
        "data_ptr_0x20": _u64(data, 0x20),
        "aux_ptr_0x28": _u64(data, 0x28),
        "qwords": [_u64(data, off) for off in range(0, 0x30, 8)],
        "first_12_i32": [_i32(data, off) for off in range(0, 0x30, 4)],
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
    out = {
        "object": obj,
        "read_ok": True,
        "vtable": vtable,
        "vtable_va": _module_va(target, vtable),
        "fields": fields,
        "field_decodes": {
            "+0x08_descriptor": _descriptor(process, fields["+0x08"]),
            "+0x10_descriptor": _descriptor(process, fields["+0x10"]),
            "+0x18_descriptor": _descriptor(process, fields["+0x18"]),
            "+0x20_vec4": _vec4(process, fields["+0x20"]),
        },
    }

    vdata = _read(process, vtable, 0x40)
    if vdata is not None:
        worker = _u64(vdata, 0x30)
        out["worker_slot_0x30"] = worker
        out["worker_slot_0x30_va"] = _module_va(target, worker)
        out["worker_matches_0x2fb320"] = out["worker_slot_0x30_va"] == ENTRY
    return out


def _stack(thread, max_frames=12):
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
                "rbp": _u(frame, "rbp"),
            }
        )
    return out


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
    _create_breakpoint(target, ENTRY, "worker_probe.entry", "entry_0x2fb320")
    _create_breakpoint(
        target, AFTER_STORE, "worker_probe.after_store", "after_store_0x2fbf05"
    )
    state["dynamic_breakpoints_installed"] = True


def gate(frame, bp_loc, internal_dict):
    state = _state()
    state["gate_hits"] += 1
    debugger = frame.GetThread().GetProcess().GetTarget().GetDebugger()
    _install_dynamic(debugger)
    _disable_breakpoint(debugger, "gate_0x3e4b09")
    return False


def entry(frame, bp_loc, internal_dict):
    state = _state()
    state["counts"]["entry_0x2fb320"] += 1
    if len(state["entry_samples"]) < state["sample_limit"]:
        thread = frame.GetThread()
        process = thread.GetProcess()
        regs = _registers(frame)
        state["entry_samples"].append(
            {
                "site": "entry_0x2fb320",
                "site_va": _module_va(process.GetTarget(), frame.GetPC()),
                "registers": regs,
                "callback": _callback(process, regs["rdi"]),
                "request_rect_rsi": _rect(process, regs["rsi"]),
                "stack": _stack(thread),
            }
        )

    if state["counts"]["entry_0x2fb320"] >= state["entry_cap"]:
        debugger = frame.GetThread().GetProcess().GetTarget().GetDebugger()
        _disable_breakpoint(debugger, "entry_0x2fb320")
        if "entry_0x2fb320" not in state["disabled_after_cap"]:
            state["disabled_after_cap"].append("entry_0x2fb320")
    return False


def after_store(frame, bp_loc, internal_dict):
    state = _state()
    state["counts"]["after_store_0x2fbf05"] += 1
    if len(state["store_samples"]) < state["sample_limit"]:
        thread = frame.GetThread()
        process = thread.GetProcess()
        regs = _registers(frame)
        dest_addr = regs["r15"] + regs["rdx"]
        callback_addr = 0
        cb_data = _read(process, regs["rbp"] - 0x1D8, 8)
        if cb_data is not None:
            callback_addr = _u64(cb_data)
        xmm0 = _xmm_f32s(frame, "xmm0")
        xmm3 = _xmm_f32s(frame, "xmm3")
        xmm4 = _xmm_f32s(frame, "xmm4")
        quotient = None
        if xmm3 and xmm4:
            quotient = [
                (xmm4[i] / xmm3[i]) if xmm3[i] not in (0.0, -0.0) else None
                for i in range(4)
            ]
        state["store_samples"].append(
            {
                "site": "after_store_0x2fbf05",
                "site_va": _module_va(process.GetTarget(), frame.GetPC()),
                "registers": regs,
                "dest_addr_r15_plus_rdx": dest_addr,
                "dest_after_vec4": _vec4(process, dest_addr),
                "xmm0_store_value": xmm0,
                "xmm3_normalizer_sum": xmm3,
                "xmm4_weighted_sum": xmm4,
                "direct_divide_xmm4_over_xmm3": quotient,
                "max_abs_store_minus_direct_divide": _max_abs_delta(xmm0, quotient),
                "callback": _callback(process, callback_addr) if callback_addr else None,
                "local_descriptors": {
                    "rbp-0x40": _descriptor(process, regs["rbp"] - 0x40),
                    "rbp-0x70": _descriptor(process, regs["rbp"] - 0x70),
                    "rbp-0x90": _descriptor(process, regs["rbp"] - 0x90),
                },
                "stack": _stack(thread),
            }
        )

    if state["counts"]["after_store_0x2fbf05"] >= state["store_cap"]:
        debugger = frame.GetThread().GetProcess().GetTarget().GetDebugger()
        _disable_breakpoint(debugger, "after_store_0x2fbf05")
        if "after_store_0x2fbf05" not in state["disabled_after_cap"]:
            state["disabled_after_cap"].append("after_store_0x2fbf05")
    return False


def _max_abs_delta(left, right):
    if not left or not right:
        return None
    vals = []
    for a, b in zip(left, right):
        if a is None or b is None or not math.isfinite(a) or not math.isfinite(b):
            continue
        vals.append(abs(a - b))
    return max(vals) if vals else None


def attach(debugger):
    target = debugger.GetSelectedTarget()
    count = target.GetNumBreakpoints()
    if count < 1:
        _state()["errors"].append("expected gate breakpoint")
        print("L16_2FB320_ATTACH_ERROR expected gate breakpoint")
        return
    bp = target.GetBreakpointAtIndex(count - 1)
    bp.SetScriptCallbackFunction("worker_probe.gate")
    _state()["breakpoint_ids"] = {"gate_0x3e4b09": bp.GetID()}
    print("L16_2FB320_ATTACHED", _state()["breakpoint_ids"])


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
    state["drive_steps"] += steps
    if process.IsValid() and process.GetState() == lldb.eStateStopped and steps >= max_steps:
        state["drive_hit_step_cap"] = True
    print("L16_2FB320_DRIVE_STEPS", steps)


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
    print("L16_2FB320_WROTE", path)


def report(debugger):
    print("L16_2FB320_BEGIN")
    print(json.dumps(payload(debugger), indent=2, sort_keys=True))
    print("L16_2FB320_END")
