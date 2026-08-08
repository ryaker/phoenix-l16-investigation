import builtins
import hashlib
import json
import os
import struct


SITES = {
    0x3085A0: "worker_entry",
    0x3088A8: "helper_pre",
    0x3088AD: "helper_post",
    0x308DC8: "transform_tail",
    0x308E40: "store_odd",
    0x308E85: "store_pair_first",
    0x308EAD: "store_pair_second",
}

STORE_SITES = {0x308E40, 0x308E85, 0x308EAD}


def reset(label="", report_path="", worker_cap=4, store_cap=12):
    builtins.l16_cnr_formula = {
        "label": label,
        "report_path": report_path,
        "worker_cap": worker_cap,
        "store_cap": store_cap,
        "sequence": 0,
        "breakpoint_ids": {},
        "entry_events": [],
        "samples": [],
        "samples_by_rbp": {},
        "pending_entry_by_thread": {},
        "store_samples": [],
        "disabled": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_cnr_formula"):
        reset()
    return builtins.l16_cnr_formula


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    if not addr:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    return data if error.Success() and len(data) == size else None


def _u64(data, offset=0):
    return struct.unpack_from("<Q", data, offset)[0]


def _i32s(data):
    return list(struct.unpack("<" + "i" * (len(data) // 4), data))


def _f32s(data):
    return list(struct.unpack("<" + "f" * (len(data) // 4), data))


def _f64s(data):
    return list(struct.unpack("<" + "d" * (len(data) // 8), data))


def _hex(data):
    return data.hex() if data is not None else None


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


def _xmm_raw(frame, name):
    lldb = builtins.__import__("lldb")
    data = frame.FindRegister(name).GetData()
    error = lldb.SBError()
    raw = data.ReadRawData(error, 0, 16)
    return raw if error.Success() and len(raw) == 16 else None


def _xmm(frame, name):
    raw = _xmm_raw(frame, name)
    if raw is None:
        return None
    return {"f32": _f32s(raw), "f64": _f64s(raw), "hex": raw.hex()}


def _mem(process, addr, size):
    raw = _read(process, addr, size)
    if raw is None:
        return {"addr": addr, "read_ok": False, "size": size}
    return {
        "addr": addr,
        "read_ok": True,
        "size": size,
        "hex": raw.hex(),
        "i32": _i32s(raw[: (len(raw) // 4) * 4]),
        "f32": _f32s(raw[: (len(raw) // 4) * 4]),
        "f64": _f64s(raw[: (len(raw) // 8) * 8]),
        "qwords": [_u64(raw, offset) for offset in range(0, len(raw) - 7, 8)],
    }


def _f32(value):
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def _tile_stats(raw):
    sum_sq = [0.0, 0.0, 0.0, 0.0]
    sum_cross = [0.0, 0.0, 0.0, 0.0]
    sum_alpha_products = [0.0, 0.0, 0.0, 0.0]
    alpha_sum = 0.0
    count = len(raw) // 16
    for offset in range(0, len(raw), 16):
        p = list(struct.unpack_from("<4f", raw, offset))
        products = [
            _f32(p[0] * p[0]),
            _f32(p[1] * p[1]),
            _f32(p[2] * p[2]),
            _f32(p[3] * p[3]),
        ]
        crosses = [
            _f32(p[0] * p[1]),
            _f32(p[0] * p[2]),
            _f32(p[1] * p[2]),
            0.0,
        ]
        alpha_products = [
            _f32(p[3] * p[0]),
            _f32(p[3] * p[1]),
            _f32(p[3] * p[2]),
            _f32(p[3] * p[3]),
        ]
        for index in range(4):
            sum_sq[index] = _f32(sum_sq[index] + products[index])
            sum_cross[index] = _f32(sum_cross[index] + crosses[index])
            sum_alpha_products[index] = _f32(
                sum_alpha_products[index] + alpha_products[index]
            )
        alpha_sum = _f32(alpha_sum + p[3])
    return {
        "count": count,
        "sum_sq_f32": sum_sq,
        "sum_cross_f32": sum_cross,
        "sum_alpha_products_f32": sum_alpha_products,
        "alpha_sum_f32": alpha_sum,
    }


def _tile(process, desc_addr, rect_addr, max_bytes=0x40000):
    desc_raw = _read(process, desc_addr, 0x30)
    rect_raw = _read(process, rect_addr, 16)
    if desc_raw is None or rect_raw is None:
        return {"read_ok": False, "desc_addr": desc_addr, "rect_addr": rect_addr}
    desc_i32 = _i32s(desc_raw)
    desc_qwords = [_u64(desc_raw, offset) for offset in range(0, 0x30, 8)]
    rect = _i32s(rect_raw)
    stride = desc_i32[6]
    data_ptr = desc_qwords[4]
    x0, y0, x1, y1 = rect
    width = x1 - x0
    height = y1 - y0
    total = width * height * 16
    if width <= 0 or height <= 0 or stride <= 0 or total > max_bytes:
        return {
            "read_ok": False,
            "desc_addr": desc_addr,
            "rect_addr": rect_addr,
            "rect": rect,
            "stride": stride,
            "data_ptr": data_ptr,
            "reason": "invalid-or-too-large",
            "total_bytes": total,
        }
    rows = []
    for y in range(y0, y1):
        addr = data_ptr + ((y * stride + x0) * 16)
        row = _read(process, addr, width * 16)
        if row is None:
            return {
                "read_ok": False,
                "desc_addr": desc_addr,
                "rect_addr": rect_addr,
                "rect": rect,
                "stride": stride,
                "data_ptr": data_ptr,
                "failed_row": y,
            }
        rows.append(row)
    raw = b"".join(rows)
    return {
        "read_ok": True,
        "desc_addr": desc_addr,
        "rect_addr": rect_addr,
        "rect": rect,
        "stride": stride,
        "data_ptr": data_ptr,
        "width": width,
        "height": height,
        "total_bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "hex": raw.hex(),
        "stats": _tile_stats(raw),
    }


def _descriptor(process, addr):
    return _mem(process, addr, 0x30)


def _rect(process, addr):
    raw = _read(process, addr, 16)
    return {
        "addr": addr,
        "read_ok": raw is not None,
        "i32": _i32s(raw) if raw else None,
    }


def _stack(thread, max_frames=8):
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


def _disable(debugger, name):
    state = _state()
    bp_id = state["breakpoint_ids"].get(name)
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id) if bp_id else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)
    if name not in state["disabled"]:
        state["disabled"].append(name)


def _sample_for_rbp(rbp):
    state = _state()
    key = str(rbp)
    index = state["samples_by_rbp"].get(key)
    if index is not None and index < len(state["samples"]):
        return state["samples"][index]
    sample = {"rbp": rbp, "events": []}
    state["samples_by_rbp"][key] = len(state["samples"])
    state["samples"].append(sample)
    return sample


def _maybe_finish(frame):
    state = _state()
    complete = [
        sample
        for sample in state["samples"]
        if sample.get("helper_pre") and sample.get("helper_post") and sample.get("transform_tail")
    ]
    if (
        len(complete) >= int(state.get("worker_cap", 4))
        and len(state.get("store_samples", [])) >= int(state.get("store_cap", 12))
    ):
        frame.GetThread().GetProcess().Kill()


def worker_entry(frame, bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    thread = frame.GetThread()
    target = process.GetTarget()
    regs = _registers(frame)
    state["sequence"] += 1
    event = {
        "seq": state["sequence"],
        "site": "worker_entry",
        "site_va": _module_va(target, frame.GetPC()),
        "thread_id": thread.GetThreadID(),
        "registers": regs,
        "current_descriptor": _descriptor(process, regs["rdi"]),
        "source_descriptor": _descriptor(process, regs["rsi"]),
        "work_rect": _rect(process, regs["rdx"]),
        "param_block": _mem(process, regs["rcx"], 0x50),
        "source_tile": _tile(process, regs["rsi"], regs["rdx"]),
        "stack": _stack(thread),
    }
    state["entry_events"].append(event)
    state["pending_entry_by_thread"][str(thread.GetThreadID())] = event
    if len(state["entry_events"]) >= int(state.get("worker_cap", 4)):
        _disable(target.GetDebugger(), "worker_entry")
    return False


def helper_pre(frame, bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    thread = frame.GetThread()
    target = process.GetTarget()
    rbp = _u(frame, "rbp")
    sample = _sample_for_rbp(rbp)
    sample["thread_id"] = thread.GetThreadID()
    sample["entry"] = state["pending_entry_by_thread"].get(str(thread.GetThreadID()))
    sample["helper_pre"] = {
        "site_va": _module_va(target, frame.GetPC()),
        "registers": _registers(frame),
        "matrix_input_9d": _mem(process, rbp - 0x70, 0x48),
        "noise_vector": _mem(process, rbp - 0x230, 0x10),
        "rsqrt_diag_stack": _mem(process, rbp - 0x210, 0x30),
        "helper_object_pre": _mem(process, rbp - 0x1E8, 0xB0),
        "work_rect": _rect(process, _u(frame, "r15")),
    }
    if len(state["samples"]) >= int(state.get("worker_cap", 4)):
        _disable(target.GetDebugger(), "helper_pre")
    return False


def helper_post(frame, bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    rbp = _u(frame, "rbp")
    sample = _sample_for_rbp(rbp)
    sample["helper_post"] = {
        "site_va": _module_va(target, frame.GetPC()),
        "registers": _registers(frame),
        "helper_object_post": _mem(process, rbp - 0x1E8, 0xB0),
    }
    complete_posts = sum(1 for item in state["samples"] if item.get("helper_post"))
    if complete_posts >= int(state.get("worker_cap", 4)):
        _disable(target.GetDebugger(), "helper_post")
    return False


def transform_tail(frame, bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    rbp = _u(frame, "rbp")
    sample = _sample_for_rbp(rbp)
    sample["transform_tail"] = {
        "site_va": _module_va(target, frame.GetPC()),
        "registers": _registers(frame),
        "row_from_p0_xmm2": _xmm(frame, "xmm2"),
        "row_from_p1_xmm1": _xmm(frame, "xmm1"),
        "row_from_p2_xmm0": _xmm(frame, "xmm0"),
        "helper_object_post": _mem(process, rbp - 0x1E8, 0xB0),
        "work_rect": _rect(process, _u(frame, "r15")),
    }
    complete_tails = sum(1 for item in state["samples"] if item.get("transform_tail"))
    if complete_tails >= int(state.get("worker_cap", 4)):
        _disable(target.GetDebugger(), "transform_tail")
    _maybe_finish(frame)
    return False


def store(frame, bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    pc_va = _module_va(target, frame.GetPC())
    if pc_va == 0x308E40:
        address = _u(frame, "rcx")
    elif pc_va == 0x308E85:
        address = _u(frame, "rdi") - 0x10
    else:
        address = _u(frame, "rdi")
    before = _read(process, address, 16)
    event = {
        "site": SITES.get(pc_va),
        "site_va": pc_va,
        "rbp": _u(frame, "rbp"),
        "address": address,
        "pixel_before": _f32s(before) if before else None,
        "pixel_before_hex": _hex(before),
        "pixel_after_xmm3": _xmm(frame, "xmm3"),
        "row_from_p0_xmm2": _xmm(frame, "xmm2"),
        "row_from_p1_xmm1": _xmm(frame, "xmm1"),
        "row_from_p2_xmm0": _xmm(frame, "xmm0"),
    }
    state["store_samples"].append(event)
    sample = _sample_for_rbp(event["rbp"])
    sample.setdefault("store_sample_indices", []).append(len(state["store_samples"]) - 1)
    if len(state["store_samples"]) >= int(state.get("store_cap", 12)):
        for va in STORE_SITES:
            _disable(target.GetDebugger(), SITES[va])
    _maybe_finish(frame)
    return False


def install(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    callbacks = {
        0x3085A0: "cnr_formula_probe.worker_entry",
        0x3088A8: "cnr_formula_probe.helper_pre",
        0x3088AD: "cnr_formula_probe.helper_post",
        0x308DC8: "cnr_formula_probe.transform_tail",
        0x308E40: "cnr_formula_probe.store",
        0x308E85: "cnr_formula_probe.store",
        0x308EAD: "cnr_formula_probe.store",
    }
    for va, callback in callbacks.items():
        before = target.GetNumBreakpoints()
        debugger.HandleCommand(f"breakpoint set --shlib libcp.dylib --address 0x{va:x}")
        if target.GetNumBreakpoints() <= before:
            state["errors"].append(f"breakpoint creation failed for 0x{va:x}")
            continue
        bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
        bp.SetScriptCallbackFunction(callback)
        state["breakpoint_ids"][SITES[va]] = bp.GetID()
    print("L16_CNR_FORMULA_INSTALLED", state["breakpoint_ids"])


def _breakpoint_hit_counts(debugger):
    target = debugger.GetSelectedTarget()
    out = {}
    for name, bp_id in _state().get("breakpoint_ids", {}).items():
        bp = target.FindBreakpointByID(bp_id)
        out[name] = bp.GetHitCount() if bp and bp.IsValid() else None
    return out


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
    state["drive_hit_step_cap"] = (
        process.IsValid() and process.GetState() == lldb.eStateStopped and steps >= max_steps
    )
    print("L16_CNR_FORMULA_DRIVE_STEPS", steps)


def payload(debugger):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    process_state = {
        "valid": process.IsValid() if process else False,
        "state": lldb.SBDebugger.StateAsCString(process.GetState()) if process else None,
        "exit_status": process.GetExitStatus() if process and process.IsValid() else None,
    }
    state = dict(_state())
    state.pop("samples_by_rbp", None)
    state.pop("pending_entry_by_thread", None)
    return {
        "process": process_state,
        "breakpoint_hit_counts": _breakpoint_hit_counts(debugger),
        **state,
    }


def write_report(debugger, path=""):
    out = path or _state().get("report_path")
    if not out:
        raise RuntimeError("no report path")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("WROTE", out)


def report(debugger):
    print(json.dumps(payload(debugger), indent=2, sort_keys=True))
