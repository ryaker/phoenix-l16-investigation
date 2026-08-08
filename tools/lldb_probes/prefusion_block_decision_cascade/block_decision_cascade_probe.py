import builtins
import json
import struct


SITES = {
    0x245416: ("heavy_244560", "after_block300_call"),
    0x24543B: ("heavy_244560", "after_block360_call"),
    0x245447: ("heavy_244560", "after_block360_active_check"),
    0x24545A: ("heavy_244560", "after_block300_active_check"),
    0x24548D: ("heavy_244560", "decision_join"),
    0x2454A7: ("heavy_244560", "sentinel_fill_path"),
    0x245610: ("heavy_244560", "coord_output_call"),
    0x246D42: ("heavy_245a40", "after_block300_call"),
    0x246D65: ("heavy_245a40", "after_block360_call"),
    0x246D71: ("heavy_245a40", "after_block360_active_check"),
    0x246D81: ("heavy_245a40", "after_block300_active_check"),
    0x246DB0: ("heavy_245a40", "decision_join"),
    0x246E98: ("heavy_245a40", "sentinel_fill_path"),
    0x24717B: ("heavy_245a40", "coord_output_call"),
}


def reset(label="", sample_limit=256, step_cap=500000):
    builtins.l16_prefusion_block_decision_cascade = {
        "label": label,
        "sample_limit": sample_limit,
        "step_cap": step_cap,
        "breakpoint_ids": {},
        "counts": {
            "site_hits": {},
            "decision_join_hits": 0,
            "decision_abort": 0,
            "decision_continue": 0,
            "sentinel_fill_path_hits": 0,
            "coord_output_call_hits": 0,
        },
        "decisions": [],
        "samples": [],
        "errors": [],
        "drive_steps": 0,
        "drive_hit_step_cap": False,
    }


def _state():
    if not hasattr(builtins, "l16_prefusion_block_decision_cascade"):
        reset()
    return builtins.l16_prefusion_block_decision_cascade


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    if not addr or size < 0:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u64(data, off=0):
    return struct.unpack_from("<Q", data, off)[0]


def _i32(data, off=0):
    return struct.unpack_from("<i", data, off)[0]


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
    addr = target.ResolveLoadAddress(pc)
    if addr and addr.IsValid():
        module = addr.GetModule()
        if module and str(module.GetFileSpec().GetFilename()) != "libcp.dylib":
            return None
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
            "rsi",
            "rdi",
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
            "rip",
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
            }
        )
    return frames


def _vector_header(process, addr, elem_size):
    data = _read(process, addr, 24)
    if data is None:
        return {"addr": addr, "read_ok": False}
    begin = _u64(data, 0)
    end = _u64(data, 8)
    cap = _u64(data, 16)
    byte_len = end - begin if end >= begin else None
    cap_bytes = cap - begin if cap >= begin else None
    return {
        "addr": addr,
        "read_ok": True,
        "begin": begin,
        "end": end,
        "cap": cap,
        "byte_len": byte_len,
        "elem_size": elem_size,
        "elem_count": byte_len // elem_size if byte_len is not None else None,
        "cap_bytes": cap_bytes,
        "cap_elems": cap_bytes // elem_size if cap_bytes is not None else None,
    }


def _block(process, addr):
    data = _read(process, addr, 0x60)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "target_0x00": _i32(data, 0),
        "active_0x04": data[4],
        "descriptor": {
            "f32_0x08": _f32(data, 0x08),
            "f32_0x0c": _f32(data, 0x0C),
            "f32_0x10": _f32(data, 0x10),
            "f32_0x14": _f32(data, 0x14),
            "f32_0x18": _f32(data, 0x18),
            "f32_0x1c": _f32(data, 0x1C),
            "f32_0x20": _f32(data, 0x20),
            "f32_0x24": _f32(data, 0x24),
            "f32_0x28": _f32(data, 0x28),
        },
        "family_0x30_root": _vector_header(process, addr + 0x30, 24),
        "family_0x48_root": _vector_header(process, addr + 0x48, 24),
    }


def _state_addr(family, regs):
    if family == "heavy_244560":
        return regs["r14"]
    if family == "heavy_245a40":
        return regs["rbx"] or regs["rax"]
    return 0


def _state_summary(process, family, regs):
    state_addr = _state_addr(family, regs)
    if not state_addr:
        return {"state_addr": 0, "read_ok": False}
    return {
        "state_addr": state_addr,
        "block300": _block(process, state_addr + 0x300),
        "block360": _block(process, state_addr + 0x360),
        "coord_vector_0x1e8": _vector_header(process, state_addr + 0x1E8, 8),
    }


def install_breakpoints(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    for site, (_, name) in sorted(SITES.items()):
        before = target.GetNumBreakpoints()
        debugger.HandleCommand(f"breakpoint set --shlib libcp.dylib --address 0x{site:x}")
        after = target.GetNumBreakpoints()
        if after <= before:
            state["errors"].append({"site": f"0x{site:x}", "error": "breakpoint not created"})
            continue
        bp = target.GetBreakpointAtIndex(after - 1)
        if not bp or not bp.IsValid():
            state["errors"].append({"site": f"0x{site:x}", "error": "invalid breakpoint"})
            continue
        bp.SetScriptCallbackFunction("block_decision_cascade_probe.hit")
        state["breakpoint_ids"][f"{name}_0x{site:x}"] = bp.GetID()
    print("L16_PREFUSION_BLOCK_DECISION_CASCADE_INSTALLED", json.dumps(state["breakpoint_ids"], sort_keys=True))


def hit(frame, bp_loc, _dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    regs = _registers(frame)
    va = _module_va(target, regs["rip"])
    family, role = SITES.get(va, ("unknown", "unknown"))
    key = f"{family}:{role}:0x{va:x}"
    state["counts"]["site_hits"][key] = state["counts"]["site_hits"].get(key, 0) + 1
    state_summary = _state_summary(process, family, regs)
    packet = {
        "site": f"0x{va:x}",
        "family": family,
        "role": role,
        "thread_id": thread.GetThreadID(),
        "registers": regs,
        "al": regs["rax"] & 0xFF,
        "ebx": regs["rbx"] & 0xFFFFFFFF,
        "r14d": regs["r14"] & 0xFFFFFFFF,
        "state": state_summary,
        "stack": _stack(thread, 10),
    }
    if role == "decision_join":
        state["counts"]["decision_join_hits"] += 1
        abort_flag = packet["ebx"] if family == "heavy_244560" else packet["r14d"]
        active300 = state_summary.get("block300", {}).get("active_0x04")
        active360 = state_summary.get("block360", {}).get("active_0x04")
        decision = {
            "site": packet["site"],
            "family": family,
            "thread_id": packet["thread_id"],
            "abort_flag": abort_flag,
            "active300": active300,
            "active360": active360,
            "state_addr": state_summary.get("state_addr"),
            "coord_pair_count": state_summary.get("coord_vector_0x1e8", {}).get("elem_count"),
        }
        if abort_flag:
            state["counts"]["decision_abort"] += 1
        else:
            state["counts"]["decision_continue"] += 1
        if len(state["decisions"]) < state["sample_limit"]:
            state["decisions"].append(decision)
    elif role == "sentinel_fill_path":
        state["counts"]["sentinel_fill_path_hits"] += 1
    elif role == "coord_output_call":
        state["counts"]["coord_output_call_hits"] += 1
    if len(state["samples"]) < state["sample_limit"]:
        state["samples"].append(packet)
    return False


def drive_until_exit_or_step_cap(debugger):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    while process.IsValid() and process.GetState() == lldb.eStateStopped:
        if state["drive_steps"] >= state["step_cap"]:
            state["drive_hit_step_cap"] = True
            break
        state["drive_steps"] += 1
        process.Continue()


def report_to_file(debugger, path):
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    state["process_exit_status"] = process.GetExitStatus() if process.IsValid() else None
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
    print("L16_PREFUSION_BLOCK_DECISION_CASCADE_REPORT", path)
