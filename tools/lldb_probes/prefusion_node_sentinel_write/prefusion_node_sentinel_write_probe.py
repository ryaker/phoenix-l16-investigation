import builtins
import json
import math
import struct


STORE_X = 0x21B923
STORE_Y = 0x21B92A
SENTINEL_BITS = 0xBF800000
SENTINEL_FLOAT = -1.0


def reset(label="", sample_limit=128, hit_cap=512, step_cap=300000):
    builtins.l16_prefusion_node_sentinel_write = {
        "label": label,
        "sample_limit": sample_limit,
        "hit_cap": hit_cap,
        "step_cap": step_cap,
        "breakpoint_ids": {},
        "counts": {
            "store_x_hits": 0,
            "store_y_hits": 0,
            "store_x_breakpoint_disabled_after_cap": 0,
            "store_y_breakpoint_disabled_after_cap": 0,
            "store_x_pre_finite_non_sentinel": 0,
            "store_y_mid_x_is_sentinel": 0,
        },
        "store_x_samples": [],
        "store_y_samples": [],
        "errors": [],
        "drive_steps": 0,
        "drive_hit_step_cap": False,
    }


def _state():
    if not hasattr(builtins, "l16_prefusion_node_sentinel_write"):
        reset()
    return builtins.l16_prefusion_node_sentinel_write


def _read(process, addr, size):
    if not addr or size < 0:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _f32(data, off=0):
    return struct.unpack_from("<f", data, off)[0]


def _u32(data, off=0):
    return struct.unpack_from("<I", data, off)[0]


def _pair(process, addr):
    out = {"addr": addr, "read_ok": False}
    data = _read(process, addr, 8)
    if data is None:
        return out
    x = _f32(data, 0)
    y = _f32(data, 4)
    out.update(
        {
            "read_ok": True,
            "hex": data.hex(),
            "x": x,
            "y": y,
            "x_bits": _u32(data, 0),
            "y_bits": _u32(data, 4),
            "both_finite": math.isfinite(x) and math.isfinite(y),
            "is_sentinel_neg1_neg1": x == SENTINEL_FLOAT and y == SENTINEL_FLOAT,
            "x_is_sentinel": x == SENTINEL_FLOAT,
            "y_is_sentinel": y == SENTINEL_FLOAT,
        }
    )
    return out


def _registers(frame):
    regs = {}
    for name in ("rax", "rbx", "rcx", "rdx", "rsi", "rdi", "r13", "r14", "r15", "rip"):
        regs[name] = frame.FindRegister(name).GetValueAsUnsigned()
    return regs


def _libcp_base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                return base
    return None


def _module_va(target, pc):
    base = _libcp_base(target)
    if base is None:
        return None
    return pc - base


def _stack(thread, max_depth=10):
    frames = []
    target = thread.GetProcess().GetTarget()
    for idx in range(min(thread.GetNumFrames(), max_depth)):
        frame = thread.GetFrameAtIndex(idx)
        pc = frame.GetPC()
        frames.append(
            {
                "index": idx,
                "pc": pc,
                "libcp_va": _module_va(target, pc),
                "function": str(frame.GetFunctionName() or frame.GetSymbol().GetName()),
            }
        )
    return frames


def _append_limited(key, packet):
    state = _state()
    if len(state[key]) < state["sample_limit"]:
        state[key].append(packet)


def _disable_breakpoint(debugger, name, count_key):
    state = _state()
    if state["counts"][count_key]:
        return
    bp_id = state["breakpoint_ids"].get(name)
    if not bp_id:
        return
    bp = debugger.GetSelectedTarget().FindBreakpointByID(int(bp_id))
    if bp and bp.IsValid():
        bp.SetEnabled(False)
        state["counts"][count_key] = 1


def install_breakpoints(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    for site, name in ((STORE_X, "store_x_21b923"), (STORE_Y, "store_y_21b92a")):
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
        bp.SetScriptCallbackFunction("prefusion_node_sentinel_write_probe.hit")
        state["breakpoint_ids"][name] = bp.GetID()
    print("L16_PREFUSION_NODE_SENTINEL_WRITE_INSTALLED", json.dumps(state["breakpoint_ids"], sort_keys=True))


def _store_x(frame, regs):
    state = _state()
    process = frame.GetThread().GetProcess()
    addr = regs["rax"] + regs["rdx"] * 8
    pair_before = _pair(process, addr)
    if pair_before.get("both_finite") and not pair_before.get("is_sentinel_neg1_neg1"):
        state["counts"]["store_x_pre_finite_non_sentinel"] += 1
    packet = {
        "thread_id": frame.GetThread().GetThreadID(),
        "pc_va": STORE_X,
        "store_addr": addr,
        "pair_index": regs["rdx"],
        "pair_before_store": pair_before,
        "static_store_bits": SENTINEL_BITS,
        "static_store_float": SENTINEL_FLOAT,
        "registers": regs,
        "stack": _stack(frame.GetThread(), 10),
    }
    _append_limited("store_x_samples", packet)


def _store_y(frame, regs):
    state = _state()
    process = frame.GetThread().GetProcess()
    addr = regs["rcx"] - 4
    pair_mid = _pair(process, addr)
    if pair_mid.get("x_is_sentinel"):
        state["counts"]["store_y_mid_x_is_sentinel"] += 1
    packet = {
        "thread_id": frame.GetThread().GetThreadID(),
        "pc_va": STORE_Y,
        "store_addr": regs["rcx"],
        "pair_addr": addr,
        "pair_mid_store": pair_mid,
        "static_store_bits": SENTINEL_BITS,
        "static_store_float": SENTINEL_FLOAT,
        "registers": regs,
        "stack": _stack(frame.GetThread(), 10),
    }
    _append_limited("store_y_samples", packet)


def hit(frame, bp_loc, _dict):
    debugger = frame.GetThread().GetProcess().GetTarget().GetDebugger()
    state = _state()
    target = frame.GetThread().GetProcess().GetTarget()
    pc_va = _module_va(target, frame.GetPC())
    regs = _registers(frame)
    if pc_va == STORE_X:
        state["counts"]["store_x_hits"] += 1
        _store_x(frame, regs)
        if state["counts"]["store_x_hits"] >= state["hit_cap"]:
            _disable_breakpoint(debugger, "store_x_21b923", "store_x_breakpoint_disabled_after_cap")
    elif pc_va == STORE_Y:
        state["counts"]["store_y_hits"] += 1
        _store_y(frame, regs)
        if state["counts"]["store_y_hits"] >= state["hit_cap"]:
            _disable_breakpoint(debugger, "store_y_21b92a", "store_y_breakpoint_disabled_after_cap")
    else:
        state["errors"].append({"error": "unexpected breakpoint", "pc_va": pc_va})
    return False


def _breakpoint_hit_counts(debugger):
    counts = {}
    target = debugger.GetSelectedTarget()
    for name, bp_id in _state()["breakpoint_ids"].items():
        bp = target.FindBreakpointByID(int(bp_id))
        if bp and bp.IsValid():
            counts[name] = bp.GetHitCount()
    return counts


def drive_until_exit_or_step_cap(debugger):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    while process and process.IsValid() and process.GetState() != lldb.eStateExited:
        if state["drive_steps"] >= state["step_cap"]:
            state["drive_hit_step_cap"] = True
            break
        state["drive_steps"] += 1
        process.Continue()
    if process and process.IsValid() and process.GetState() == lldb.eStateExited:
        state["process_exit_status"] = process.GetExitStatus()
    state["process_state"] = int(process.GetState()) if process and process.IsValid() else None


def report_to_file(debugger, path):
    state = _state()
    state["breakpoint_hit_counts"] = _breakpoint_hit_counts(debugger)
    process = debugger.GetSelectedTarget().GetProcess()
    if process and process.IsValid() and "process_exit_status" not in state:
        state["process_exit_status"] = process.GetExitStatus()
        state["process_state"] = int(process.GetState())
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)
    print("L16_PREFUSION_NODE_SENTINEL_WRITE_JSON", path)
