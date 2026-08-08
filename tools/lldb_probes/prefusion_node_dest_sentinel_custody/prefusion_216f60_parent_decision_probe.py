import builtins
import json
import math
import os
import struct


CONSUMER_ENTRY = 0x217A68
SIDE_MAX_BRANCH = 0x217AC9
CENTER_SIDE_BRANCH = 0x217AD6
SCORE_RATIO_BRANCH = 0x217AF9
ACCEPTED_RECORD = 0x217AFF
F33D0_CALL = 0x217BBE
F33D0_RETURN = 0x217BC3
CLEANUP = 0x217BF8


def reset(label="", packet_cap=64, step_cap=200000):
    builtins.l16_prefusion_216f60_parent_decision = {
        "label": label,
        "packet_cap": packet_cap,
        "step_cap": step_cap,
        "breakpoints": {},
        "active": {},
        "packets": [],
        "counts": {
            "consumer_hits": 0,
            "packets_started": 0,
            "packets_finalized": 0,
            "side_max_branches": 0,
            "center_side_branches": 0,
            "score_ratio_branches": 0,
            "accepted_record_hits": 0,
            "f33d0_calls": 0,
            "f33d0_returns": 0,
            "cleanup_hits": 0,
            "unmatched_hits": 0,
        },
        "errors": [],
        "drive_hit_step_cap": False,
    }


def _state():
    if not hasattr(builtins, "l16_prefusion_216f60_parent_decision"):
        reset()
    return builtins.l16_prefusion_216f60_parent_decision


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u64(process, address):
    data = _read(process, address, 8)
    return struct.unpack("<Q", data)[0] if data is not None else None


def _i32_register(frame, name):
    value = frame.FindRegister(name).GetValueAsUnsigned() & 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def _register(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _module_base(target):
    lldb = builtins.__import__("lldb")
    module = target.FindModule(lldb.SBFileSpec("libcp.dylib"))
    if not module or not module.IsValid():
        return None
    header = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
    if header in (0, (1 << 64) - 1):
        return None
    return header


def _module_va(target, address):
    base = _module_base(target)
    return address - base if base is not None else None


def _vector_header(process, address, stride):
    begin = _u64(process, address)
    end = _u64(process, address + 8)
    cap = _u64(process, address + 16)
    count = None
    if begin is not None and end is not None and end >= begin:
        count = (end - begin) // stride
    return {
        "header": address,
        "begin": begin,
        "end": end,
        "cap": cap,
        "stride": stride,
        "count": count,
    }


def _f32(process, address):
    data = _read(process, address, 4)
    if data is None:
        return {"address": address, "read_ok": False}
    return {
        "address": address,
        "read_ok": True,
        "value": struct.unpack("<f", data)[0],
        "hex": data.hex(),
    }


def _f32_value(process, address):
    value = _f32(process, address)
    return value["value"] if value.get("read_ok") else None


def _float32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def _record(process, address):
    data = _read(process, address, 24)
    if data is None:
        return {"address": address, "read_ok": False}
    return {
        "address": address,
        "read_ok": True,
        "hex": data.hex(),
        "u32": list(struct.unpack("<6I", data)),
        "f32": list(struct.unpack("<6f", data)),
        "f64_0": struct.unpack("<d", data[:8])[0],
        "f64_2": struct.unpack("<d", data[16:24])[0],
    }


def _winner(process, begin, count, cap=20000):
    if begin is None or count is None or count <= 0 or count > cap:
        return {"computed": False, "count": count}
    current = _f32_value(process, begin)
    if current is None:
        return {"computed": False, "count": count}
    index = 0
    for candidate_index in range(1, count):
        candidate = _f32_value(process, begin + 4 * candidate_index)
        if candidate is None:
            return {"computed": False, "count": count, "failed_index": candidate_index}
        if not (candidate >= current):
            index = candidate_index
            current = candidate
    return {
        "computed": True,
        "count": count,
        "index": index,
        "score": _f32(process, begin + 4 * index),
    }


def _stack(thread, limit=8):
    target = thread.GetProcess().GetTarget()
    rows = []
    for index in range(min(thread.GetNumFrames(), limit)):
        frame = thread.GetFrameAtIndex(index)
        rows.append(
            {
                "index": index,
                "pc": frame.GetPC(),
                "libcp_va": _module_va(target, frame.GetPC()),
                "function": frame.GetFunctionName(),
            }
        )
    return rows


def _key(frame):
    return f"{frame.GetThread().GetThreadID()}:{_register(frame, 'rbp'):x}"


def _flags(frame):
    rflags = _register(frame, "rflags")
    return {
        "rflags": rflags,
        "cf": bool(rflags & 0x1),
        "zf": bool(rflags & 0x40),
        "pf": bool(rflags & 0x4),
    }


def _active_packet(frame):
    packet = _state()["active"].get(_key(frame))
    if packet is None:
        _state()["counts"]["unmatched_hits"] += 1
    return packet


def consumer_hit(frame, bp_loc, _dict):
    state = _state()
    state["counts"]["consumer_hits"] += 1
    if state["counts"]["packets_started"] >= state["packet_cap"]:
        return False

    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    rbp = _register(frame, "rbp")
    key = _key(frame)
    if key in state["active"]:
        state["errors"].append({"error": "active frame reused", "key": key})
        return False

    return_vector = _vector_header(process, rbp - 0x3F0, 4)
    side_vector = _vector_header(process, rbp - 0x410, 4)
    candidate_records = _vector_header(process, rbp - 0x430, 24)
    winner = _winner(process, return_vector["begin"], return_vector["count"])
    center_index = _i32_register(frame, "ebx")
    optional_gate_count = _i32_register(frame, "r12d")

    winner_index = winner.get("index")
    winner_score = (winner.get("score") or {}).get("value")
    winner_side = None
    center_side = None
    center_score = None
    selected_record = None
    if winner_index is not None:
        winner_side = _f32(process, side_vector["begin"] + 4 * winner_index)
        selected_record = _record(process, candidate_records["begin"] + 24 * winner_index)
    if (
        isinstance(center_index, int)
        and center_index >= 0
        and return_vector["count"] is not None
        and center_index < return_vector["count"]
    ):
        center_side = _f32(process, side_vector["begin"] + 4 * center_index)
        center_score = _f32(process, return_vector["begin"] + 4 * center_index)

    center_scaled = None
    if center_score is not None and center_score.get("read_ok"):
        center_scaled = _float32(center_score["value"] * _float32(0.8))

    predicted = {
        "side_max_pass": (
            winner_side is not None
            and winner_side.get("read_ok")
            and math.isfinite(winner_side["value"])
            and winner_side["value"] <= _float32(0.25)
        ),
        "center_side_pass": (
            winner_side is not None
            and winner_side.get("read_ok")
            and center_side is not None
            and center_side.get("read_ok")
            and not (winner_side["value"] > center_side["value"])
        ),
        "score_ratio_required": optional_gate_count > 0,
        "score_ratio_pass": (
            optional_gate_count <= 0
            or (
                winner_score is not None
                and center_scaled is not None
                and math.isfinite(winner_score)
                and not (center_scaled < winner_score)
            )
        ),
    }
    predicted["accepted"] = (
        predicted["side_max_pass"]
        and predicted["center_side_pass"]
        and predicted["score_ratio_pass"]
    )

    packet = {
        "ordinal": state["counts"]["packets_started"] + 1,
        "key": key,
        "thread_id": frame.GetThread().GetThreadID(),
        "rbp": rbp,
        "consumer_pc": frame.GetPC(),
        "consumer_libcp_va": _module_va(target, frame.GetPC()),
        "center_index": center_index,
        "optional_gate_count": optional_gate_count,
        "return_vector": return_vector,
        "side_vector": side_vector,
        "candidate_records": candidate_records,
        "winner": winner,
        "winner_side": winner_side,
        "center_side": center_side,
        "center_score": center_score,
        "center_score_times_0_8_f32": center_scaled,
        "selected_record": selected_record,
        "predicted": predicted,
        "branches": [],
        "accepted_record_hit": False,
        "f33d0_call": None,
        "f33d0_return": None,
        "finalized": False,
        "stack": _stack(frame.GetThread()),
    }
    state["active"][key] = packet
    state["packets"].append(packet)
    state["counts"]["packets_started"] += 1
    return False


def _branch_hit(frame, name, branch_kind):
    packet = _active_packet(frame)
    if packet is None:
        return False
    flags = _flags(frame)
    if branch_kind == "jb":
        taken = flags["cf"]
    elif branch_kind == "ja":
        taken = not flags["cf"] and not flags["zf"]
    else:
        raise ValueError(branch_kind)
    packet["branches"].append(
        {
            "name": name,
            "libcp_va": _module_va(frame.GetThread().GetProcess().GetTarget(), frame.GetPC()),
            "kind": branch_kind,
            "flags": flags,
            "taken": taken,
        }
    )
    return False


def side_max_branch_hit(frame, bp_loc, _dict):
    _state()["counts"]["side_max_branches"] += 1
    return _branch_hit(frame, "side_max_reject", "jb")


def center_side_branch_hit(frame, bp_loc, _dict):
    _state()["counts"]["center_side_branches"] += 1
    return _branch_hit(frame, "center_side_reject", "ja")


def score_ratio_branch_hit(frame, bp_loc, _dict):
    _state()["counts"]["score_ratio_branches"] += 1
    return _branch_hit(frame, "score_ratio_reject", "jb")


def accepted_record_hit(frame, bp_loc, _dict):
    state = _state()
    state["counts"]["accepted_record_hits"] += 1
    packet = _active_packet(frame)
    if packet is None:
        return False
    packet["accepted_record_hit"] = True
    packet["accepted_winner_index_from_rcx"] = _register(frame, "rcx")
    return False


def f33d0_call_hit(frame, bp_loc, _dict):
    state = _state()
    state["counts"]["f33d0_calls"] += 1
    packet = _active_packet(frame)
    if packet is None:
        return False
    process = frame.GetThread().GetProcess()
    packet["f33d0_call"] = {
        "libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
        "rdi": _register(frame, "rdi"),
        "rsi": _register(frame, "rsi"),
        "rdx": _register(frame, "rdx"),
        "rcx": _register(frame, "rcx"),
        "r8": _register(frame, "r8"),
        "rsi_24_bytes": _record(process, _register(frame, "rsi")),
    }
    return False


def f33d0_return_hit(frame, bp_loc, _dict):
    state = _state()
    state["counts"]["f33d0_returns"] += 1
    packet = _active_packet(frame)
    if packet is None:
        return False
    process = frame.GetThread().GetProcess()
    output_rdx = _read(process, _register(frame, "rbp") - 0x4C8, 12)
    output_rcx = _read(process, _register(frame, "rbp") - 0x4D4, 12)
    packet["f33d0_return"] = {
        "libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
        "rax": _register(frame, "rax"),
        "output_rdx_local": output_rdx.hex() if output_rdx is not None else None,
        "output_rcx_local": output_rcx.hex() if output_rcx is not None else None,
    }
    return False


def cleanup_hit(frame, bp_loc, _dict):
    state = _state()
    state["counts"]["cleanup_hits"] += 1
    key = _key(frame)
    packet = state["active"].pop(key, None)
    if packet is None:
        state["counts"]["unmatched_hits"] += 1
        return False
    packet["finalized"] = True
    packet["observed_accepted"] = packet["accepted_record_hit"]
    packet["observed_f33d0_complete"] = (
        packet["f33d0_call"] is not None and packet["f33d0_return"] is not None
    )
    state["counts"]["packets_finalized"] += 1
    return False


def _add_breakpoint(debugger, name, address, callback):
    state = _state()
    target = debugger.GetSelectedTarget()
    before = target.GetNumBreakpoints()
    debugger.HandleCommand(f"breakpoint set --shlib libcp.dylib --address 0x{address:x}")
    if target.GetNumBreakpoints() <= before:
        state["errors"].append({"error": "breakpoint not created", "name": name, "address": address})
        return
    breakpoint = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
    breakpoint.SetScriptCallbackFunction(callback)
    state["breakpoints"][name] = breakpoint.GetID()


def install(debugger):
    specs = (
        ("consumer", CONSUMER_ENTRY, "consumer_hit"),
        ("side_max", SIDE_MAX_BRANCH, "side_max_branch_hit"),
        ("center_side", CENTER_SIDE_BRANCH, "center_side_branch_hit"),
        ("score_ratio", SCORE_RATIO_BRANCH, "score_ratio_branch_hit"),
        ("accepted_record", ACCEPTED_RECORD, "accepted_record_hit"),
        ("f33d0_call", F33D0_CALL, "f33d0_call_hit"),
        ("f33d0_return", F33D0_RETURN, "f33d0_return_hit"),
        ("cleanup", CLEANUP, "cleanup_hit"),
    )
    for name, address, callback in specs:
        _add_breakpoint(
            debugger,
            name,
            address,
            f"prefusion_216f60_parent_decision_probe.{callback}",
        )
    print("L16_PREFUSION_216F60_PARENT_DECISION_INSTALLED", _state()["breakpoints"])


def drive_until_exit_or_step_cap(debugger):
    lldb = builtins.__import__("lldb")
    state = _state()
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process and process.IsValid() and process.GetState() != lldb.eStateExited:
        if steps >= state["step_cap"]:
            state["drive_hit_step_cap"] = True
            break
        steps += 1
        process.Continue()
    state["drive_steps"] = steps
    if process and process.IsValid():
        state["process_state"] = int(process.GetState())
        state["process_exit_status"] = process.GetExitStatus()
    print("L16_PREFUSION_216F60_PARENT_DECISION_DRIVE_STEPS", steps)


def payload(debugger):
    state = _state()
    packet = dict(state)
    packet["active"] = list(state["active"].keys())
    process = debugger.GetSelectedTarget().GetProcess()
    if process and process.IsValid():
        packet["process_state"] = int(process.GetState())
        packet["process_exit_status"] = process.GetExitStatus()
    return packet


def report_to_file(debugger, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(debugger), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("WROTE", path)
