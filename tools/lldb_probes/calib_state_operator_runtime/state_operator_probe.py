import builtins
import json
import struct


OPERATORS = {
    0x229DF0: "runReferenceGroupCams::$_0",
    0x229EC0: "runReferenceGroupCams::$_1",
    0x22A0E0: "runReferenceGroupCams::$_2",
    0x22A9B0: "runReferenceGroupCams::$_3",
    0x22AAF0: "runReferenceGroupCams::$_4",
    0x22AE60: "runReferenceGroupCams::$_5",
    0x22AF80: "runReferenceGroupCams::$_6",
    0x22BDF0: "runHigherGroupCams::$_7",
    0x22BEE0: "runHigherGroupCams::$_8",
    0x22C350: "runHigherGroupCams::$_9",
    0x22CD00: "runHigherGroupCams::$_10",
    0x22D250: "runHigherGroupCams::$_11",
    0x22E1D0: "runHigherGroupCams::$_12",
}


def reset(label="", hit_cap=512, sample_limit=24):
    builtins.l16_state_operator = {
        "label": label,
        "hit_cap": hit_cap,
        "sample_limit": sample_limit,
        "drive_steps": 0,
        "drive_hit_step_cap": False,
        "breakpoint_ids": {},
        "breakpoint_vas": {},
        "counts": {f"0x{va:x}": 0 for va in OPERATORS},
        "samples": {f"0x{va:x}": [] for va in OPERATORS},
        "disabled_after_cap": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_state_operator"):
        reset()
    return builtins.l16_state_operator


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


def _u64s(data):
    return list(struct.unpack("<" + "Q" * (len(data) // 8), data))


def _qword(process, addr):
    data = _read(process, addr, 8)
    return struct.unpack("<Q", data)[0] if data is not None else None


def _shared_pair(process, addr):
    data = _read(process, addr, 16)
    if data is None:
        return {"addr": addr, "read_ok": False}
    pointer, control = struct.unpack("<QQ", data)
    return {
        "addr": addr,
        "read_ok": True,
        "pointer": pointer,
        "control": control,
    }


def _vector_header(process, addr):
    data = _read(process, addr, 24)
    if data is None:
        return {"addr": addr, "read_ok": False}
    begin, end, capacity = struct.unpack("<QQQ", data)
    return {
        "addr": addr,
        "read_ok": True,
        "begin": begin,
        "end": end,
        "capacity": capacity,
        "bytes": end - begin if begin <= end else None,
    }


def _qword_prefix(process, addr, count=3):
    data = _read(process, addr, count * 8)
    return {
        "addr": addr,
        "read_ok": data is not None,
        "qwords": _u64s(data) if data is not None else None,
    }


def _state5_handles(process, closure_addr):
    inner = _qword(process, closure_addr + 8)
    if inner is None:
        return {"closure": closure_addr, "read_ok": False}
    owner = _qword(process, inner + 0x10)
    sibling = _qword(process, inner + 0x28)
    if owner is None or sibling is None:
        return {
            "closure": closure_addr,
            "inner": inner,
            "owner": owner,
            "sibling": sibling,
            "read_ok": False,
        }

    upstream = {
        "inner_30": _shared_pair(process, inner + 0x30),
        "inner_40": _shared_pair(process, inner + 0x40),
        "inner_50": _shared_pair(process, inner + 0x50),
        "inner_a0": _shared_pair(process, inner + 0xA0),
    }
    owner_pairs = {
        "owner_00": _shared_pair(process, owner + 0x00),
        "owner_28": _shared_pair(process, owner + 0x28),
        "owner_38": _shared_pair(process, owner + 0x38),
        "owner_48": _shared_pair(process, owner + 0x48),
    }
    sibling_pairs = {
        "sibling_00": _shared_pair(process, sibling + 0x00),
        "sibling_10": _shared_pair(process, sibling + 0x10),
        "sibling_20": _shared_pair(process, sibling + 0x20),
        "sibling_30": _shared_pair(process, sibling + 0x30),
    }

    def same_pair(*pairs):
        return all(pair.get("read_ok") for pair in pairs) and len(
            {(pair.get("pointer"), pair.get("control")) for pair in pairs}
        ) == 1

    mappings = {
        "inner_40_owner_00_sibling_00": same_pair(
            upstream["inner_40"], owner_pairs["owner_00"], sibling_pairs["sibling_00"]
        ),
        "inner_50_owner_28_sibling_10": same_pair(
            upstream["inner_50"], owner_pairs["owner_28"], sibling_pairs["sibling_10"]
        ),
        "inner_30_owner_38_sibling_20": same_pair(
            upstream["inner_30"], owner_pairs["owner_38"], sibling_pairs["sibling_20"]
        ),
        "inner_a0_owner_48_sibling_30": same_pair(
            upstream["inner_a0"], owner_pairs["owner_48"], sibling_pairs["sibling_30"]
        ),
    }

    top_pointer = owner_pairs["owner_00"].get("pointer")
    keyed_pointer = owner_pairs["owner_28"].get("pointer")
    return {
        "closure": closure_addr,
        "inner": inner,
        "owner": owner,
        "sibling": sibling,
        "read_ok": True,
        "upstream_pairs": upstream,
        "owner_pairs": owner_pairs,
        "sibling_pairs": sibling_pairs,
        "mapping_equalities": mappings,
        "top_record_vector": _vector_header(process, top_pointer),
        "keyed_record_tree_prefix": _qword_prefix(process, keyed_pointer),
    }


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


def _stack(thread, max_frames=16):
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


def _object_prefix(process, addr):
    data = _read(process, addr, 0x80)
    if data is None:
        return {"addr": addr, "read_ok": False}
    target = process.GetTarget()
    qwords = _u64s(data)
    return {
        "addr": addr,
        "read_ok": True,
        "qwords": qwords,
        "qword_module_vas": [
            _module_va(target, value) if value else None for value in qwords
        ],
    }


def _disable_breakpoint(debugger, bp_id):
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id) if bp_id else None
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def install(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    base = _libcp_base(target)
    if base is None:
        state["errors"].append("libcp base unavailable")
        print("L16_STATE_OPERATOR_ATTACH_ERROR libcp base unavailable")
        return
    for va, name in OPERATORS.items():
        bp = target.BreakpointCreateByAddress(base + va)
        bp.SetScriptCallbackFunction("state_operator_probe.hit")
        bp_id = bp.GetID()
        state["breakpoint_ids"][f"0x{va:x}"] = bp_id
        state["breakpoint_vas"][str(bp_id)] = va
    print("L16_STATE_OPERATOR_INSTALLED", json.dumps(state["breakpoint_ids"], sort_keys=True))


def attach_existing(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    operators = list(OPERATORS)
    if target.GetNumBreakpoints() < len(operators):
        state["errors"].append("not enough existing breakpoints")
        print("L16_STATE_OPERATOR_ATTACH_ERROR not enough existing breakpoints")
        return
    start = target.GetNumBreakpoints() - len(operators)
    for index, va in enumerate(operators):
        bp = target.GetBreakpointAtIndex(start + index)
        if not bp or not bp.IsValid():
            state["errors"].append(f"missing breakpoint for 0x{va:x}")
            continue
        bp.SetScriptCallbackFunction("state_operator_probe.hit")
        bp_id = bp.GetID()
        state["breakpoint_ids"][f"0x{va:x}"] = bp_id
        state["breakpoint_vas"][str(bp_id)] = va
    print("L16_STATE_OPERATOR_ATTACHED", json.dumps(state["breakpoint_ids"], sort_keys=True))


def attach_selected_existing(debugger, vas):
    state = _state()
    target = debugger.GetSelectedTarget()
    selected = [int(va) for va in vas]
    if target.GetNumBreakpoints() < len(selected):
        state["errors"].append("not enough existing selected breakpoints")
        print("L16_STATE_OPERATOR_ATTACH_ERROR not enough selected breakpoints")
        return
    start = target.GetNumBreakpoints() - len(selected)
    for index, va in enumerate(selected):
        if va not in OPERATORS:
            state["errors"].append(f"unknown selected operator 0x{va:x}")
            continue
        bp = target.GetBreakpointAtIndex(start + index)
        if not bp or not bp.IsValid():
            state["errors"].append(f"missing selected breakpoint for 0x{va:x}")
            continue
        bp.SetScriptCallbackFunction("state_operator_probe.hit")
        bp_id = bp.GetID()
        state["breakpoint_ids"][f"0x{va:x}"] = bp_id
        state["breakpoint_vas"][str(bp_id)] = va
    print("L16_STATE_OPERATOR_ATTACHED", json.dumps(state["breakpoint_ids"], sort_keys=True))


def hit(frame, bp_loc, internal_dict):
    state = _state()
    bp_id = bp_loc.GetBreakpoint().GetID()
    va = state["breakpoint_vas"].get(str(bp_id))
    if va is None:
        state["errors"].append(f"unknown breakpoint id {bp_id}")
        return False

    key = f"0x{va:x}"
    state["counts"][key] += 1
    if len(state["samples"][key]) < state["sample_limit"]:
        thread = frame.GetThread()
        process = thread.GetProcess()
        regs = _registers(frame)
        sample = {
            "site_va": _module_va(process.GetTarget(), frame.GetPC()),
            "operator": OPERATORS[va],
            "registers": regs,
            "object_prefix_rdi": _object_prefix(process, regs["rdi"]),
            "stack": _stack(thread),
        }
        if va == 0x22AE60:
            sample["state5_handles"] = _state5_handles(process, regs["rdi"])
        state["samples"][key].append(sample)

    if state["counts"][key] >= state["hit_cap"]:
        debugger = frame.GetThread().GetProcess().GetTarget().GetDebugger()
        _disable_breakpoint(debugger, bp_id)
        if key not in state["disabled_after_cap"]:
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
    print("L16_STATE_OPERATOR_DRIVE_STEPS", steps)


def payload(debugger):
    return {
        "process": _process_packet(debugger),
        "breakpoint_hit_counts": _breakpoint_hit_counts(debugger),
        "operators": {f"0x{va:x}": name for va, name in OPERATORS.items()},
        **_state(),
    }


def write_report(debugger, path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_STATE_OPERATOR_WROTE", path)


def report(debugger):
    print("L16_STATE_OPERATOR_BEGIN")
    print(json.dumps(payload(debugger), indent=2, sort_keys=True))
    print("L16_STATE_OPERATOR_END")
