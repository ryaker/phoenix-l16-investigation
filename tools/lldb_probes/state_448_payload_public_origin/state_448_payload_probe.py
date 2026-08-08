import builtins
import json
import struct


SITES = {
    0x3F30EE: {
        "name": "first_payload_0x00_0x20_call_241590",
        "helper": "0x241590",
        "src_len": 0x24,
        "dst_offsets": "0x00..0x20",
    },
    0x3F3128: {
        "name": "first_payload_0x24_0x2c_call_2415b0",
        "helper": "0x2415b0",
        "src_len": 0x0C,
        "dst_offsets": "0x24..0x2c",
    },
    0x3F3599: {
        "name": "later_payload_0x30_0x34_call_2415d0",
        "helper": "0x2415d0",
        "src_len": 0x08,
        "dst_offsets": "0x30..0x34",
    },
    0x3F35F5: {
        "name": "later_payload_0x38_0x3c_call_2415f0",
        "helper": "0x2415f0",
        "src_len": 0x08,
        "dst_offsets": "0x38..0x3c",
    },
}


def reset(label="", sample_limit=4096, hit_cap=4096):
    builtins.l16_state_448_payload_public = {
        "label": label,
        "sample_limit": sample_limit,
        "hit_cap": hit_cap,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
        "breakpoint_ids": {},
        "breakpoint_vas": {},
        "counts": {f"0x{va:x}": 0 for va in SITES},
        "events": [],
        "disabled_after_cap": [],
        "errors": [],
        "sequence": 0,
    }


def _state():
    if not hasattr(builtins, "l16_state_448_payload_public"):
        reset()
    return builtins.l16_state_448_payload_public


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


def _read_i32(process, addr):
    data = _read(process, addr, 4)
    return struct.unpack_from("<i", data, 0)[0] if data is not None else None


def _read_u32_words(process, addr, size):
    data = _read(process, addr, size)
    if data is None or len(data) % 4:
        return None
    return list(struct.unpack_from("<" + "I" * (len(data) // 4), data))


def _read_hex(process, addr, size):
    data = _read(process, addr, size)
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


def _registers(frame):
    names = ("rax", "rbx", "rcx", "rdx", "rdi", "rsi", "r12", "r13", "r14", "r15", "rbp", "rsp")
    return {name: _u(frame, name) for name in names}


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


def _packet_for_site(process, regs, site):
    dst = regs["rdi"]
    src = regs["rsi"]
    src_len = site["src_len"]
    return {
        "helper": site["helper"],
        "dst_offsets": site["dst_offsets"],
        "payload_addr": dst,
        "source_addr": src,
        "node_key_from_payload_minus_0x04": _read_i32(process, dst - 4),
        "source_words_u32": _read_u32_words(process, src, src_len),
        "source_raw": _read_hex(process, src, src_len),
        "payload_before_raw_0x00_0xa4": _read_hex(process, dst, 0xA4),
    }


def _append_event(event):
    state = _state()
    if len(state["events"]) < state["sample_limit"]:
        state["events"].append(event)


def _disable_breakpoint(debugger, bp_id):
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id) if bp_id else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def attach_existing(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    if target.GetNumBreakpoints() < len(SITES):
        state["errors"].append("not enough existing breakpoints")
        print("L16_STATE448_ATTACH_ERROR not enough existing breakpoints")
        return
    start = target.GetNumBreakpoints() - len(SITES)
    for index, va in enumerate(SITES):
        bp = target.GetBreakpointAtIndex(start + index)
        if not bp or not bp.IsValid():
            state["errors"].append(f"missing breakpoint for 0x{va:x}")
            continue
        bp.SetScriptCallbackFunction("state_448_payload_probe.hit")
        bp_id = bp.GetID()
        state["breakpoint_ids"][f"0x{va:x}"] = bp_id
        state["breakpoint_vas"][str(bp_id)] = va
    print("L16_STATE448_ATTACHED", json.dumps(state["breakpoint_ids"], sort_keys=True))


def hit(frame, bp_loc, internal_dict):
    state = _state()
    bp_id = bp_loc.GetBreakpoint().GetID()
    va = state["breakpoint_vas"].get(str(bp_id))
    if va is None:
        state["errors"].append(f"unknown breakpoint id {bp_id}")
        return False
    va = int(va)
    site = SITES[va]
    state["sequence"] += 1
    key = f"0x{va:x}"
    state["counts"][key] = state["counts"].get(key, 0) + 1
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    regs = _registers(frame)
    event = {
        "sequence": state["sequence"],
        "site_va": _module_va(target, frame.GetPC()),
        "site_name": site["name"],
        "thread_id": thread.GetThreadID(),
        "registers": regs,
        "stack": _stack(thread),
    }
    try:
        event["packet"] = _packet_for_site(process, regs, site)
    except Exception as exc:
        state["errors"].append(f"packet error at 0x{va:x}: {exc}")
    _append_event(event)
    if state["counts"][key] >= state["hit_cap"]:
        _disable_breakpoint(frame.GetThread().GetProcess().GetTarget().GetDebugger(), bp_id)
        state["disabled_after_cap"].append(key)
    return False


def _breakpoint_hit_counts(debugger):
    target = debugger.GetSelectedTarget()
    out = {}
    for key, bp_id in _state().get("breakpoint_ids", {}).items():
        bp = target.FindBreakpointByID(bp_id)
        out[key] = bp.GetHitCount() if bp and bp.IsValid() else None
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


def drive_until_exit_or_step_cap(debugger, max_steps=80000):
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
    print("L16_STATE448_DRIVE_STEPS", steps)


def payload(debugger):
    return {
        "process": _process_packet(debugger),
        "breakpoint_hit_counts": _breakpoint_hit_counts(debugger),
        "sites": {f"0x{va:x}": site["name"] for va, site in SITES.items()},
        **_state(),
    }


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_STATE448_WROTE", path)
