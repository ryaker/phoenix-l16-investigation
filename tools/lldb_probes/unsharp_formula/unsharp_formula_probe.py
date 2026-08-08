import builtins
import json
import os
import struct


SITES = {
    0x35F5C0: "constructor",
    0x35F945: "gaussian7_return",
    0x35F99D: "gaussian3_return",
    0x35F9F2: "gaussian5_return",
    0x3608D7: "combine_store",
    **{va: f"property_{va:x}" for va in (
        0x318F67, 0x318F79, 0x318F9C, 0x318FBF, 0x318FE2,
        0x319005, 0x319028, 0x31904B, 0x31906E, 0x319091,
        0x3190B4, 0x3190D7, 0x3190FA, 0x31911D,
        0x319378, 0x31939B, 0x3193BE, 0x3193E1, 0x319400,
        0x319436, 0x319459,
    )},
}


def reset(label="", constructor_cap=32):
    builtins.l16_unsharp_formula = {
        "label": label,
        "constructor_cap": constructor_cap,
        "breakpoint_ids": {},
        "counts": {name: 0 for name in SITES.values()},
        "constructors": [],
        "constructor_config_counts": {},
        "constructor_by_thread": {},
        "generated_kernels": [],
        "combine": None,
        "properties": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_unsharp_formula"):
        reset()
    return builtins.l16_unsharp_formula


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    return data if error.Success() and len(data) == size else None


def _f32s(process, addr, count):
    raw = _read(process, addr, count * 4)
    return list(struct.unpack("<" + "f" * count, raw)) if raw is not None else None


def _xmm(frame, name):
    try:
        lldb = builtins.__import__("lldb")
        data = frame.FindRegister(name).GetData()
        error = lldb.SBError()
        raw = bytes(data.GetUnsignedInt8(error, i) for i in range(data.GetByteSize()))
        if error.Success() and len(raw) >= 16:
            return list(struct.unpack_from("<4f", raw))
    except Exception as exc:
        _state()["errors"].append(f"{name}: {exc}")
    return None


def _u64(process, addr):
    raw = _read(process, addr, 8)
    return struct.unpack("<Q", raw)[0] if raw is not None else None


def _cstring(process, addr, cap=512):
    raw = _read(process, addr, cap)
    if raw is None:
        return None
    return raw.split(b"\0", 1)[0].decode("ascii", "replace")


def _libcpp_string(process, addr):
    header = _read(process, addr, 24)
    if header is None:
        return None
    if header[0] & 1:
        size = struct.unpack_from("<Q", header, 8)[0]
        ptr = struct.unpack_from("<Q", header, 16)[0]
        raw = _read(process, ptr, size)
    else:
        raw = header[1:1 + (header[0] >> 1)]
    return raw.decode("utf-8", "replace") if raw is not None else None


def _object_rtti(process, obj):
    vtable = _u64(process, obj) if obj else None
    typeinfo = _u64(process, vtable - 8) if vtable else None
    name_ptr = _u64(process, typeinfo + 8) if typeinfo else None
    return {"object": obj, "vtable": vtable, "typeinfo": typeinfo, "name": _cstring(process, name_ptr) if name_ptr else None}


def _stack(frame, cap=10):
    out = []
    target = frame.GetThread().GetProcess().GetTarget()
    base = None
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            break
    thread = frame.GetThread()
    for index in range(min(cap, thread.GetNumFrames())):
        item = thread.GetFrameAtIndex(index)
        pc = item.GetPC()
        out.append({"pc": pc, "libcp_va": pc - base if base is not None and pc >= base else None, "function": item.GetFunctionName()})
    return out


def _disable(debugger, name):
    bp_id = _state()["breakpoint_ids"].get(name)
    if bp_id is not None:
        bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id)
        if bp and bp.IsValid():
            bp.SetEnabled(False)


def site(frame, bp_loc, _dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    debugger = process.GetTarget().GetDebugger()
    pc = frame.GetPC()
    base = None
    for module in process.GetTarget().module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(process.GetTarget())
            break
    name = SITES.get(pc - base if base is not None else None)
    if name is None:
        state["errors"].append(f"unexpected pc 0x{pc:x}")
        return False
    state["counts"][name] += 1

    if name.startswith("property_"):
        value = _libcpp_string(process, _u(frame, "rsi"))
        state["properties"].append({"address": pc - base, "name": value})
        _disable(debugger, name)
    elif name == "constructor" and len(state["constructors"]) < state["constructor_cap"]:
        config = _u(frame, "rsi")
        raw = _read(process, config, 20)
        key = raw.hex() if raw is not None else "unreadable"
        state["constructor_by_thread"][str(frame.GetThread().GetThreadID())] = key
        state["constructor_config_counts"][key] = state["constructor_config_counts"].get(key, 0) + 1
        if not any(item.get("config_hex_0x00_0x10") == key for item in state["constructors"]):
            state["constructors"].append({
                "object": _u(frame, "rdi"),
                "config_ptr": config,
                "config_hex_0x00_0x10": key,
                "config_f32_0x00_0x10": _f32s(process, config, 5),
                "stack": _stack(frame),
            })
    elif name.startswith("gaussian"):
        taps = int(name[len("gaussian"):name.index("_return")])
        output = _u(frame, "r12")
        raw = _read(process, output, taps * 4)
        caller = frame.GetThread().GetFrameAtIndex(1)
        config = _u(caller, "r14")
        config_raw = _read(process, config, 20)
        config_key = config_raw.hex() if config_raw is not None else None
        caller_pc = caller.GetPC()
        role = "positive" if caller_pc == (base + 0x35F810) else "negative" if caller_pc == (base + 0x35F878) else "unknown"
        identity = (config_key, taps, role, raw.hex() if raw is not None else None)
        if not any(
            (item.get("config_hex_0x00_0x10"), item.get("taps"), item.get("role"), item.get("coefficients_hex")) == identity
            for item in state["generated_kernels"]
        ):
            state["generated_kernels"].append({
                "config_hex_0x00_0x10": config_key,
                "taps": taps,
                "role": role,
                "coefficients_hex": raw.hex() if raw is not None else None,
                "coefficients": list(struct.unpack("<" + "f" * taps, raw)) if raw is not None else None,
            })
    elif name == "combine_store" and state["combine"] is None:
        obj = _u(frame, "rbx")
        state["combine"] = {
            "object": obj,
            "amount_0x68": (_f32s(process, obj + 0x68, 1) or [None])[0],
            "base_xmm2": _xmm(frame, "xmm2"),
            "difference_xmm3": _xmm(frame, "xmm3"),
            "output_xmm4": _xmm(frame, "xmm4"),
            "base_source_rtti": _object_rtti(process, _u64(process, obj + 0x38)),
            "dog_positive_rtti": _object_rtti(process, _u64(process, obj + 0x48)),
            "dog_negative_rtti": _object_rtti(process, _u64(process, obj + 0x58)),
            "stack": _stack(frame),
        }
        _disable(debugger, name)
    return False


def install(debugger):
    target = debugger.GetSelectedTarget()
    for va, name in SITES.items():
        before = target.GetNumBreakpoints()
        debugger.HandleCommand(f"breakpoint set --shlib libcp.dylib --address 0x{va:x}")
        if target.GetNumBreakpoints() <= before:
            _state()["errors"].append(f"failed to create {name}")
            continue
        bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
        bp.SetScriptCallbackFunction("unsharp_formula_probe.site")
        _state()["breakpoint_ids"][name] = bp.GetID()
    print("L16_UNSHARP_FORMULA_INSTALLED", _state()["breakpoint_ids"])


def drive(debugger, cap=20000):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process.IsValid() and process.GetState() == lldb.eStateStopped and steps < cap:
        steps += 1
        process.Continue()
    _state()["drive_steps"] = steps


def write_report(debugger, path):
    process = debugger.GetSelectedTarget().GetProcess()
    payload = {**_state(), "process": {"exit_status": process.GetExitStatus() if process and process.IsValid() else None}}
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_UNSHARP_FORMULA_WROTE", path)
