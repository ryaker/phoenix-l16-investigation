import builtins
import json
import os
import struct


CONSTRUCT_DONE = 0x21797A
STORE_AFTER = 0x219387
CONSUMER_ENTRY = 0x217A68
CALLBACK_VTABLE = 0x658138


def reset(label="", store_sample_cap=64, step_cap=200000):
    builtins.l16_prefusion_216f60_score_vector_consumer = {
        "label": label,
        "store_sample_cap": store_sample_cap,
        "step_cap": step_cap,
        "breakpoints": {},
        "active": None,
        "constructs": [],
        "stores": [],
        "consumers": [],
        "counts": {
            "construct_hits": 0,
            "constructs_recorded": 0,
            "store_hits": 0,
            "matching_store_hits": 0,
            "store_samples_recorded": 0,
            "consumer_hits": 0,
            "matching_consumer_hits": 0,
            "consumers_recorded": 0,
            "store_other_closure": 0,
            "consumer_other_frame": 0,
        },
        "errors": [],
        "drive_hit_step_cap": False,
    }


def _state():
    if not hasattr(builtins, "l16_prefusion_216f60_score_vector_consumer"):
        reset()
    return builtins.l16_prefusion_216f60_score_vector_consumer


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


def _f32(process, address):
    data = _read(process, address, 4)
    if data is None:
        return {"addr": address, "read_ok": False}
    return {
        "addr": address,
        "read_ok": True,
        "value": struct.unpack("<f", data)[0],
        "hex": data.hex(),
    }


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


def _runtime_addr(target, va):
    base = _module_base(target)
    return base + va if base is not None else None


def _register(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _registers(frame):
    names = ("rax", "rbx", "rcx", "rdx", "rsi", "rdi", "r8", "r9", "r14", "r15", "rbp", "rsp")
    return {name: _register(frame, name) for name in names}


def _stack(thread, limit=10):
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


def _vector_header(process, address, stride):
    begin = _u64(process, address)
    end = _u64(process, address + 8)
    cap = _u64(process, address + 16)
    count = None
    if begin is not None and end is not None and end >= begin and stride:
        count = (end - begin) // stride
    return {
        "header": address,
        "begin": begin,
        "end": end,
        "cap": cap,
        "stride": stride,
        "count": count,
    }


def _closure_fields(process, closure):
    return {
        "vtable": _u64(process, closure),
        "+0x10": _u64(process, closure + 0x10),
        "+0x18": _u64(process, closure + 0x18),
        "+0x20": _u64(process, closure + 0x20),
        "+0x28": _u64(process, closure + 0x28),
        "+0x30": _u64(process, closure + 0x30),
        "+0x38": _u64(process, closure + 0x38),
    }


def _sample_floats(process, begin, count, limit=8):
    if begin is None or count is None:
        return []
    return [_f32(process, begin + 4 * index) for index in range(min(count, limit))]


def _min_like_winner(process, begin, count, cap=20000):
    if begin is None or count is None or count <= 0 or count > cap:
        return {"computed": False, "count": count, "cap": cap}
    winner = 0
    winner_value = _f32(process, begin)
    if not winner_value.get("read_ok"):
        return {"computed": False, "count": count, "error": "winner read failed"}
    current = winner_value["value"]
    for index in range(1, count):
        value = _f32(process, begin + 4 * index)
        if not value.get("read_ok"):
            return {"computed": False, "count": count, "error": f"read failed at {index}"}
        candidate = value["value"]
        if not (candidate >= current):
            winner = index
            winner_value = value
            current = candidate
    return {"computed": True, "count": count, "winner_index": winner, "winner": winner_value}


def _disable_breakpoint(target, name):
    state = _state()
    bp_id = state["breakpoints"].get(name)
    if bp_id is None:
        return
    bp = target.FindBreakpointByID(bp_id)
    if bp and bp.IsValid():
        bp.SetEnabled(False)


def construct_hit(frame, bp_loc, _dict):
    state = _state()
    state["counts"]["construct_hits"] += 1
    if state["active"] is not None:
        _disable_breakpoint(frame.GetThread().GetProcess().GetTarget(), "construct")
        return False

    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    rbp = _register(frame, "rbp")
    closure = _u64(process, rbp - 0x70)
    if closure is None:
        state["errors"].append({"error": "closure pointer unreadable", "rbp": rbp})
        return False

    fields = _closure_fields(process, closure)
    expected_vtable = _runtime_addr(target, CALLBACK_VTABLE)
    if fields["vtable"] != expected_vtable:
        state["errors"].append(
            {
                "error": "unexpected callback vtable",
                "closure": closure,
                "vtable": fields["vtable"],
                "expected": expected_vtable,
            }
        )
        return False

    return_vector = _vector_header(process, rbp - 0x3F0, 4)
    side_vector = _vector_header(process, rbp - 0x410, 4)
    candidate_records = _vector_header(process, rbp - 0x430, 24)
    packet = {
        "thread_id": frame.GetThread().GetThreadID(),
        "pc": frame.GetPC(),
        "libcp_va": _module_va(target, frame.GetPC()),
        "rbp": rbp,
        "closure": closure,
        "closure_fields": fields,
        "expected_vtable": expected_vtable,
        "return_vector": return_vector,
        "side_vector": side_vector,
        "candidate_records": candidate_records,
        "registers": _registers(frame),
        "stack": _stack(frame.GetThread()),
    }
    packet["field_matches"] = {
        "+0x18_is_return_vector_header": fields["+0x18"] == return_vector["header"],
        "+0x38_is_side_vector_header": fields["+0x38"] == side_vector["header"],
        "+0x10_is_candidate_record_header": fields["+0x10"] == candidate_records["header"],
    }
    state["active"] = packet
    state["constructs"].append(packet)
    state["counts"]["constructs_recorded"] += 1
    _disable_breakpoint(target, "construct")
    return False


def store_hit(frame, bp_loc, _dict):
    state = _state()
    state["counts"]["store_hits"] += 1
    active = state.get("active")
    if active is None:
        return False
    closure = _register(frame, "r14")
    if closure != active["closure"]:
        state["counts"]["store_other_closure"] += 1
        return False

    state["counts"]["matching_store_hits"] += 1
    if state["counts"]["store_samples_recorded"] >= state["store_sample_cap"]:
        _disable_breakpoint(frame.GetThread().GetProcess().GetTarget(), "store")
        return False

    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    index = _register(frame, "r15")
    vector_begin = _register(frame, "rax")
    value_address = vector_begin + 4 * index
    sample = {
        "ordinal": state["counts"]["store_samples_recorded"] + 1,
        "thread_id": frame.GetThread().GetThreadID(),
        "pc": frame.GetPC(),
        "libcp_va": _module_va(target, frame.GetPC()),
        "closure": closure,
        "index": index,
        "vector_begin_from_rax": vector_begin,
        "value_address": value_address,
        "stored_value": _f32(process, value_address),
        "registers": _registers(frame),
        "stack": _stack(frame.GetThread()),
    }
    sample["matches_constructed_return_begin"] = vector_begin == active["return_vector"]["begin"]
    state["stores"].append(sample)
    state["counts"]["store_samples_recorded"] += 1
    return False


def consumer_hit(frame, bp_loc, _dict):
    state = _state()
    state["counts"]["consumer_hits"] += 1
    active = state.get("active")
    if active is None:
        return False
    rbp = _register(frame, "rbp")
    if rbp != active["rbp"]:
        state["counts"]["consumer_other_frame"] += 1
        return False

    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    state["counts"]["matching_consumer_hits"] += 1
    return_vector = _vector_header(process, rbp - 0x3F0, 4)
    side_vector = _vector_header(process, rbp - 0x410, 4)
    candidate_records = _vector_header(process, rbp - 0x430, 24)
    winner = _min_like_winner(process, return_vector["begin"], return_vector["count"])
    packet = {
        "thread_id": frame.GetThread().GetThreadID(),
        "pc": frame.GetPC(),
        "libcp_va": _module_va(target, frame.GetPC()),
        "rbp": rbp,
        "return_vector": return_vector,
        "side_vector": side_vector,
        "candidate_records": candidate_records,
        "winner": winner,
        "first_return_values": _sample_floats(process, return_vector["begin"], return_vector["count"]),
        "store_samples_recorded": state["counts"]["store_samples_recorded"],
        "registers": _registers(frame),
        "stack": _stack(frame.GetThread()),
    }
    packet["matches_constructed_headers"] = {
        "return_header": return_vector["header"] == active["return_vector"]["header"],
        "return_begin": return_vector["begin"] == active["return_vector"]["begin"],
        "side_header": side_vector["header"] == active["side_vector"]["header"],
        "candidate_header": candidate_records["header"] == active["candidate_records"]["header"],
    }
    packet["matching_store_samples"] = [
        {
            "index": sample["index"],
            "value_address": sample["value_address"],
            "stored_value": sample["stored_value"],
        }
        for sample in state["stores"]
        if sample.get("matches_constructed_return_begin")
    ][:10]
    state["consumers"].append(packet)
    state["counts"]["consumers_recorded"] += 1
    _disable_breakpoint(target, "store")
    _disable_breakpoint(target, "consumer")
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
    _add_breakpoint(
        debugger,
        "construct",
        CONSTRUCT_DONE,
        "prefusion_216f60_score_vector_consumer_probe.construct_hit",
    )
    _add_breakpoint(
        debugger,
        "store",
        STORE_AFTER,
        "prefusion_216f60_score_vector_consumer_probe.store_hit",
    )
    _add_breakpoint(
        debugger,
        "consumer",
        CONSUMER_ENTRY,
        "prefusion_216f60_score_vector_consumer_probe.consumer_hit",
    )
    print("L16_PREFUSION_216F60_SCORE_VECTOR_CONSUMER_INSTALLED", _state()["breakpoints"])


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
    print("L16_PREFUSION_216F60_SCORE_VECTOR_CONSUMER_DRIVE_STEPS", steps)


def payload(debugger):
    state = _state()
    packet = dict(state)
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
