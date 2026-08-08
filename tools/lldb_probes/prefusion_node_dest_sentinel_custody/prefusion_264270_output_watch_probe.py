import builtins
import json
import os
import struct


F33D0_CALL = 0x217BBE
F33D0_RETURN = 0x217BC3
ASSEMBLY_ENTRY = 0x264270
ASSEMBLY_RETURN = 0x2643C6
COMPOSER_RETURN = 0x2404B8
WIDE_RETURN = 0x239C3F
WIDE_STORE_RETURN = 0x239D46
TELE_HELPER_DONE = 0x20DC8D
TELE_CALLER_POST = 0x20B24E
TELE_NODE_POST = 0x20B272
WIDE_DECISION_COMPARE = 0x22D8FB
WIDE_DECISION_UPDATE = 0x22D901
WIDE_DECISION_SKIP = 0x22D9A0
WIDE_DECISION_STORE = 0x22DB7C
WIDE_UPDATE_NEW_NODE = 0x22DA50
WIDE_UPDATE_MISSING = 0x22DCB0
WIDE_UPDATE_EXISTING = 0x22DCC3
WIDE_UPDATE_CONTINUE = 0x22DCF0
WIDE_CALIB_TRANSFER_CALL = 0x22DF45
WIDE_CALIB_TRANSFER_RETURN = 0x22DF4A
TERMINAL_COMPOSER_CALL = 0x23CBBC
TERMINAL_COMPOSER_RETURN = 0x23CBC1
TERMINAL_NODE_FIELDS = 0x23CE5E
TERMINAL_NODE_COPY_RETURN = 0x2009C3
TERMINAL_TRANSFORM_RETURN = 0x23D15D
TERMINAL_NORMALIZED_CONVERT_CALL = 0x23D2EE
TERMINAL_NORMALIZED_CONVERT_RETURN = 0x23D2F3
TERMINAL_NORMALIZED_COMPOSE_CALL = 0x23D34D
TERMINAL_NORMALIZED_COMPOSE_RETURN = 0x23D352
TERMINAL_NORMALIZED_F33D0_CALL = 0x23D38D
TERMINAL_NORMALIZED_F33D0_RETURN = 0x23D392
TERMINAL_SECOND_HELPER_CALL = 0x22E283
TERMINAL_SECOND_ASSEMBLY_CALLS = (0x23C6C0, 0x23CBA6, 0x23D226)


def reset(label="", hit_cap=64, step_cap=200000):
    builtins.l16_prefusion_264270_output_watch = {
        "label": label,
        "hit_cap": hit_cap,
        "step_cap": step_cap,
        "breakpoints": {},
        "pending_f33d0": {},
        "accepted_objects": {},
        "active_assembly": {},
        "assembly_entries": [],
        "assembly_returns": [],
        "watchpoint_id": None,
        "watch_armed": None,
        "watch_samples": [],
        "composer_active": None,
        "composer_return": None,
        "composer_watchpoint_id": None,
        "composer_watch_armed": None,
        "composer_watch_samples": [],
        "post_transform": None,
        "storage_watchpoint_id": None,
        "storage_watch_armed": None,
        "storage_watch_samples": [],
        "decision_local_watchpoint_id": None,
        "decision_local_watch_armed": None,
        "decision_local_watch_samples": [],
        "wide_calib_transfer": None,
        "calib_transfer_watchpoint_id": None,
        "calib_transfer_watch_armed": None,
        "calib_transfer_watch_samples": [],
        "terminal_selected_record_handoff": None,
        "terminal_node_watchpoint_id": None,
        "terminal_node_watch_armed": None,
        "terminal_node_watch_samples": [],
        "terminal_node_copy_active": None,
        "terminal_node_copy": None,
        "terminal_node_copy_watchpoint_id": None,
        "terminal_node_copy_watch_armed": None,
        "terminal_node_copy_watch_samples": [],
        "terminal_transform_active": None,
        "terminal_transform": None,
        "terminal_post_transform_watchpoint_id": None,
        "terminal_post_transform_watch_armed": None,
        "terminal_post_transform_watch_samples": [],
        "terminal_normalized_pipeline": None,
        "terminal_normalized_postwrite_consumer": None,
        "counts": {
            "f33d0_calls": 0,
            "f33d0_returns": 0,
            "assembly_entry_hits": 0,
            "assembly_matches": 0,
            "assembly_return_hits": 0,
            "assembly_return_matches": 0,
            "watchpoints_armed": 0,
            "watchpoint_hits": 0,
            "watch_value_changes": 0,
            "composer_returns": 0,
            "composer_watchpoints_armed": 0,
            "composer_watchpoint_hits": 0,
            "composer_watch_value_changes": 0,
            "post_transform_captures": 0,
            "storage_watchpoints_armed": 0,
            "storage_watchpoint_hits": 0,
            "storage_watch_value_changes": 0,
            "wide_decision_captures": 0,
            "decision_local_watchpoints_armed": 0,
            "decision_local_watchpoint_hits": 0,
            "wide_calib_transfer_calls": 0,
            "wide_calib_transfer_returns": 0,
            "calib_transfer_watchpoints_armed": 0,
            "calib_transfer_watchpoint_hits": 0,
            "terminal_composer_handoffs": 0,
            "terminal_composer_returns": 0,
            "terminal_node_materializations": 0,
            "terminal_node_watchpoints_armed": 0,
            "terminal_node_watchpoint_hits": 0,
            "terminal_node_copy_returns": 0,
            "terminal_node_copy_watchpoints_armed": 0,
            "terminal_node_copy_watchpoint_hits": 0,
            "terminal_transform_returns": 0,
            "terminal_post_transform_watchpoints_armed": 0,
            "terminal_post_transform_watchpoint_hits": 0,
            "terminal_normalized_convert_calls": 0,
            "terminal_normalized_convert_returns": 0,
            "terminal_normalized_compose_calls": 0,
            "terminal_normalized_compose_returns": 0,
            "terminal_normalized_f33d0_calls": 0,
            "terminal_normalized_f33d0_returns": 0,
            "terminal_second_helper_calls": 0,
            "terminal_second_assembly_calls": 0,
            "terminal_second_exact_postwrite_reads": 0,
        },
        "errors": [],
        "drive_hit_step_cap": False,
    }


def _state():
    if not hasattr(builtins, "l16_prefusion_264270_output_watch"):
        reset()
    return builtins.l16_prefusion_264270_output_watch


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


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


def _frame_key(frame):
    return f"{frame.GetThread().GetThreadID()}:{_register(frame, 'rbp'):x}"


def _snapshot(process, address, size):
    data = _read(process, address, size)
    return {
        "address": address,
        "size": size,
        "read_ok": data is not None,
        "hex": data.hex() if data is not None else None,
    }


def _registers(frame):
    names = ("rax", "rbx", "rcx", "rdx", "rsi", "rdi", "r8", "r9", "r12", "r13", "r14", "r15", "rbp", "rsp")
    return {name: _register(frame, name) for name in names}


def _register_blob(frame, name):
    error = builtins.__import__("lldb").SBError()
    value = frame.FindRegister(name)
    data = value.GetData()
    raw = data.ReadRawData(error, 0, data.GetByteSize())
    if not error.Success() or raw is None:
        return {"read_ok": False, "hex": None}
    return {"read_ok": True, "hex": bytes(raw).hex()}


def _stack(thread, limit=12):
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


def f33d0_call_hit(frame, bp_loc, _dict):
    state = _state()
    state["counts"]["f33d0_calls"] += 1
    process = frame.GetThread().GetProcess()
    key = _frame_key(frame)
    state["pending_f33d0"][key] = {
        "destination": _register(frame, "rdi"),
        "selector": _register(frame, "r8") & 0xFFFFFFFF,
        "source_0": _snapshot(process, _register(frame, "rsi"), 0x24),
        "source_1": _snapshot(process, _register(frame, "rdx"), 0x24),
        "source_2": _snapshot(process, _register(frame, "rcx"), 0x0C),
    }
    return False


def f33d0_return_hit(frame, bp_loc, _dict):
    state = _state()
    state["counts"]["f33d0_returns"] += 1
    key = _frame_key(frame)
    call = state["pending_f33d0"].pop(key, None)
    if call is None:
        state["errors"].append({"error": "unmatched f33d0 return", "key": key})
        return False
    process = frame.GetThread().GetProcess()
    bank = _snapshot(process, call["destination"] + 0x12C, 0x54)
    expected = call["source_0"]["hex"] + call["source_1"]["hex"] + call["source_2"]["hex"]
    state["accepted_objects"][str(call["destination"])] = {
        "destination": call["destination"],
        "bank": bank,
        "exact_copy_match": bank["hex"] == expected,
    }
    return False


def assembly_entry_hit(frame, bp_loc, _dict):
    state = _state()
    state["counts"]["assembly_entry_hits"] += 1
    source_object = _register(frame, "rsi")
    accepted = state["accepted_objects"].get(str(source_object))
    if accepted is None or state["watchpoint_id"] is not None:
        return False
    state["counts"]["assembly_matches"] += 1
    packet = {
        "key": _frame_key(frame),
        "thread_id": frame.GetThread().GetThreadID(),
        "rbp": _register(frame, "rbp"),
        "libcp_va": _module_va(frame.GetThread().GetProcess().GetTarget(), frame.GetPC()),
        "output_record": _register(frame, "rdi"),
        "source_object": source_object,
        "selector": _register(frame, "rdx") & 0xFFFFFFFF,
        "source_bank": accepted["bank"],
        "source_exact_copy_match": accepted["exact_copy_match"],
        "stack": _stack(frame.GetThread()),
    }
    state["active_assembly"][packet["key"]] = packet
    state["assembly_entries"].append(packet)
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def assembly_return_hit(frame, bp_loc, _dict):
    state = _state()
    state["counts"]["assembly_return_hits"] += 1
    key = _frame_key(frame)
    packet = state["active_assembly"].pop(key, None)
    if packet is None:
        return False
    state["counts"]["assembly_return_matches"] += 1
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    output = packet["output_record"]
    returned = {
        **packet,
        "return_libcp_va": _module_va(target, frame.GetPC()),
        "output_snapshot": _snapshot(process, output, 0x80),
    }
    state["assembly_returns"].append(returned)

    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    watchpoint = target.WatchAddress(output, 8, True, True, error)
    if not error.Success() or not watchpoint or not watchpoint.IsValid():
        state["errors"].append(
            {"error": "output watchpoint arm failed", "detail": error.GetCString()}
        )
        return False
    state["watchpoint_id"] = watchpoint.GetID()
    state["watch_armed"] = {
        "output_record": output,
        "watch_address": output,
        "watch_size": 8,
        "value_at_arm": _snapshot(process, output, 8),
        "source_object": packet["source_object"],
        "selector": packet["selector"],
    }
    state["counts"]["watchpoints_armed"] += 1
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def composer_return_hit(frame, bp_loc, _dict):
    state = _state()
    active = state.get("composer_active")
    if active is None or active["key"] != _frame_key(frame):
        return False
    state["counts"]["composer_returns"] += 1
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    destination = active["destination"]
    packet = {
        **active,
        "return_libcp_va": _module_va(target, frame.GetPC()),
        "returned_rax": _register(frame, "rax"),
        "destination_snapshot": _snapshot(process, destination, 0x80),
    }
    state["composer_return"] = packet
    bp_loc.GetBreakpoint().SetEnabled(False)

    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    watchpoint = target.WatchAddress(destination, 8, True, True, error)
    if not error.Success() or not watchpoint or not watchpoint.IsValid():
        state["errors"].append(
            {"error": "composer watchpoint arm failed", "detail": error.GetCString()}
        )
        return False
    state["composer_watchpoint_id"] = watchpoint.GetID()
    state["composer_watch_armed"] = {
        "destination": destination,
        "watch_address": destination,
        "watch_size": 8,
        "value_at_arm": _snapshot(process, destination, 8),
    }
    state["counts"]["composer_watchpoints_armed"] += 1
    return False


def _enable_breakpoints(target, names):
    state = _state()
    for name in names:
        breakpoint = target.FindBreakpointByID(state["breakpoints"][name])
        breakpoint.SetEnabled(True)


def _arm_storage_watch(target, address, size, kind):
    state = _state()
    process = target.GetProcess()
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    watchpoint = target.WatchAddress(address, size, True, True, error)
    if not error.Success() or not watchpoint or not watchpoint.IsValid():
        state["errors"].append(
            {"error": "storage watchpoint arm failed", "detail": error.GetCString()}
        )
        return
    state["storage_watchpoint_id"] = watchpoint.GetID()
    state["storage_watch_armed"] = {
        "kind": kind,
        "watch_address": address,
        "watch_size": size,
        "value_at_arm": _snapshot(process, address, size),
    }
    state["counts"]["storage_watchpoints_armed"] += 1


def wide_return_hit(frame, bp_loc, _dict):
    state = _state()
    post = state.get("post_transform")
    if post is None or post["kind"] != "wide" or post["caller_key"] != _frame_key(frame):
        return False
    post["wide_return"] = {
        "libcp_va": _module_va(frame.GetThread().GetProcess().GetTarget(), frame.GetPC()),
        "score_xmm0": _register_blob(frame, "xmm0"),
        "caller_rbp": _register(frame, "rbp"),
    }
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def wide_store_return_hit(frame, bp_loc, _dict):
    state = _state()
    post = state.get("post_transform")
    if post is None or post["kind"] != "wide" or post["caller_key"] != _frame_key(frame):
        return False
    process = frame.GetThread().GetProcess()
    destination = _register(frame, "rax")
    post["wide_store"] = {
        "libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
        "destination": destination,
        "stored_score": _snapshot(process, destination, 4),
        "caller_score_local": _snapshot(process, _register(frame, "rbp") - 0x5C, 4),
    }
    state["counts"]["post_transform_captures"] += 1
    _arm_storage_watch(process.GetTarget(), destination, 4, "wide_score")
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def tele_helper_done_hit(frame, bp_loc, _dict):
    state = _state()
    post = state.get("post_transform")
    if post is None or post["kind"] != "tele" or post["helper_key"] != _frame_key(frame):
        return False
    process = frame.GetThread().GetProcess()
    post["tele_helper_done"] = {
        "libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
        "destination": _register(frame, "rdi"),
        "matrix": _snapshot(process, _register(frame, "rdi"), 0x30),
    }
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def tele_caller_post_hit(frame, bp_loc, _dict):
    state = _state()
    post = state.get("post_transform")
    if post is None or post["kind"] != "tele" or post["caller_key"] != _frame_key(frame):
        return False
    process = frame.GetThread().GetProcess()
    post["tele_caller_post"] = {
        "libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
        "local_matrix": _snapshot(process, _register(frame, "rbp") - 0x1E0, 0x30),
        "node": _register(frame, "r14"),
    }
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def tele_node_post_hit(frame, bp_loc, _dict):
    state = _state()
    post = state.get("post_transform")
    if post is None or post["kind"] != "tele" or post["caller_key"] != _frame_key(frame):
        return False
    process = frame.GetThread().GetProcess()
    node = _register(frame, "r14")
    post["tele_node_store"] = {
        "libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
        "node": node,
        "node_key": _snapshot(process, node + 0x1C, 4),
        "node_matrix": _snapshot(process, node + 0x20, 0x30),
    }
    state["counts"]["post_transform_captures"] += 1
    _arm_storage_watch(process.GetTarget(), node + 0x20, 8, "tele_matrix")
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def wide_decision_compare_hit(frame, bp_loc, _dict):
    state = _state()
    post = state.get("post_transform")
    if post is None or post.get("wide_state_key") != _frame_key(frame):
        return False
    process = frame.GetThread().GetProcess()
    flags = _register(frame, "rflags")
    post["wide_decision_compare"] = {
        "libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
        "score": _snapshot(process, _register(frame, "rbp") - 0x2A0, 4),
        "existing_node": _register(frame, "r12"),
        "existing_score": _snapshot(process, _register(frame, "r12") + 0x28, 4),
        "rflags": flags,
        "jbe_predicted": bool(flags & 0x1 or flags & 0x40),
    }
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def wide_decision_update_hit(frame, bp_loc, _dict):
    state = _state()
    post = state.get("post_transform")
    if post is None or post.get("wide_state_key") != _frame_key(frame):
        return False
    post["wide_decision_route"] = {
        "route": "retain_existing_and_transfer",
        "libcp_va": _module_va(frame.GetThread().GetProcess().GetTarget(), frame.GetPC()),
    }
    state["counts"]["wide_decision_captures"] += 1
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    address = _register(frame, "rbp") - 0x2A0
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    watchpoint = target.WatchAddress(address, 4, True, True, error)
    if not error.Success() or not watchpoint or not watchpoint.IsValid():
        state["errors"].append(
            {"error": "decision local watchpoint arm failed", "detail": error.GetCString()}
        )
    else:
        state["decision_local_watchpoint_id"] = watchpoint.GetID()
        state["decision_local_watch_armed"] = {
            "watch_address": address,
            "watch_size": 4,
            "value_at_arm": _snapshot(process, address, 4),
        }
        state["counts"]["decision_local_watchpoints_armed"] += 1
    _enable_breakpoints(
        target,
        (
            "wide_update_new_node",
            "wide_update_missing",
            "wide_update_existing",
            "wide_update_continue",
        ),
    )
    bp_loc.GetBreakpoint().SetEnabled(False)
    state_bp = target.FindBreakpointByID(
        state["breakpoints"]["wide_decision_skip"]
    )
    state_bp.SetEnabled(False)
    return False


def wide_decision_skip_hit(frame, bp_loc, _dict):
    state = _state()
    post = state.get("post_transform")
    if post is None or post.get("wide_state_key") != _frame_key(frame):
        return False
    post["wide_decision_route"] = {
        "route": "materialize_candidate",
        "libcp_va": _module_va(frame.GetThread().GetProcess().GetTarget(), frame.GetPC()),
    }
    bp_loc.GetBreakpoint().SetEnabled(False)
    target = frame.GetThread().GetProcess().GetTarget()
    target.FindBreakpointByID(state["breakpoints"]["wide_decision_update"]).SetEnabled(False)
    return False


def wide_decision_store_hit(frame, bp_loc, _dict):
    state = _state()
    post = state.get("post_transform")
    if post is None or post.get("wide_state_key") != _frame_key(frame):
        return False
    process = frame.GetThread().GetProcess()
    destination_node = _register(frame, "r15")
    rbp = _register(frame, "rbp")
    object_data = _read(process, rbp - 0x280, 8)
    post["wide_decision_store"] = {
        "libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
        "destination_node": destination_node,
        "destination_node_key": _snapshot(process, destination_node + 0x20, 4),
        "candidate_source_object": (
            struct.unpack("<Q", object_data)[0] if object_data is not None else None
        ),
        "stored_score": _snapshot(process, destination_node + 0x28, 4),
        "local_score": _snapshot(process, _register(frame, "rbp") - 0x2A0, 4),
    }
    state["counts"]["wide_decision_captures"] += 1
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def wide_update_path_hit(frame, bp_loc, _dict):
    state = _state()
    post = state.get("post_transform")
    if post is None or post.get("wide_state_key") != _frame_key(frame):
        return False
    va = _module_va(frame.GetThread().GetProcess().GetTarget(), frame.GetPC())
    if "wide_update_path" not in post:
        labels = {
            WIDE_UPDATE_NEW_NODE: "new_node",
            WIDE_UPDATE_MISSING: "missing_entry",
            WIDE_UPDATE_EXISTING: "existing_entry",
            WIDE_UPDATE_CONTINUE: "existing_continue",
        }
        post["wide_update_path"] = {"libcp_va": va, "path": labels[va]}
    target = frame.GetThread().GetProcess().GetTarget()
    if va == WIDE_UPDATE_EXISTING:
        target.FindBreakpointByID(
            state["breakpoints"]["wide_decision_store"]
        ).SetEnabled(False)
        _enable_breakpoints(
            target, ("wide_calib_transfer_call", "wide_calib_transfer_return")
        )
    for name in (
        "wide_update_new_node",
        "wide_update_missing",
        "wide_update_existing",
        "wide_update_continue",
    ):
        target.FindBreakpointByID(state["breakpoints"][name]).SetEnabled(False)
    return False


def wide_calib_transfer_call_hit(frame, bp_loc, _dict):
    state = _state()
    post = state.get("post_transform")
    if post is None or post.get("wide_state_key") != _frame_key(frame):
        return False
    process = frame.GetThread().GetProcess()
    rbp = _register(frame, "rbp")
    node_data = _read(process, rbp - 0x2C0, 8)
    if node_data is None:
        state["errors"].append({"error": "wide calibration node local unreadable"})
        return False
    node = struct.unpack("<Q", node_data)[0]
    destination = _register(frame, "rdi")
    source_0 = _register(frame, "rsi")
    source_1 = _register(frame, "rdx")
    source_2 = _register(frame, "rcx")
    selector = _register(frame, "r8") & 0xFFFFFFFF
    state["wide_calib_transfer"] = {
        "call_libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
        "node": node,
        "node_key": _snapshot(process, node + 0x20, 4),
        "destination_object": destination,
        "selector": selector,
        "source_0": _snapshot(process, source_0, 0x24),
        "source_1": _snapshot(process, source_1, 0x24),
        "source_2": _snapshot(process, source_2, 0x0C),
        "source_addresses": [source_0, source_1, source_2],
        "bank_before": _snapshot(process, destination + 0x12C, 0x54),
    }
    state["counts"]["wide_calib_transfer_calls"] += 1
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def wide_calib_transfer_return_hit(frame, bp_loc, _dict):
    state = _state()
    post = state.get("post_transform")
    transfer = state.get("wide_calib_transfer")
    if (
        post is None
        or transfer is None
        or post.get("wide_state_key") != _frame_key(frame)
    ):
        return False
    process = frame.GetThread().GetProcess()
    transfer["return_libcp_va"] = _module_va(process.GetTarget(), frame.GetPC())
    transfer["bank_after"] = _snapshot(
        process, transfer["destination_object"] + 0x12C, 0x54
    )
    state["counts"]["wide_calib_transfer_returns"] += 1
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    address = transfer["destination_object"] + 0x12C
    watchpoint = process.GetTarget().WatchAddress(address, 8, True, True, error)
    if not error.Success() or not watchpoint or not watchpoint.IsValid():
        state["errors"].append(
            {
                "error": "calibration transfer watchpoint arm failed",
                "detail": error.GetCString(),
            }
        )
    else:
        state["calib_transfer_watchpoint_id"] = watchpoint.GetID()
        state["calib_transfer_watch_armed"] = {
            "watch_address": address,
            "watch_size": 8,
            "value_at_arm": _snapshot(process, address, 8),
            "destination_object": transfer["destination_object"],
            "selected_node": transfer["node"],
        }
        state["counts"]["calib_transfer_watchpoints_armed"] += 1
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def terminal_composer_call_hit(frame, bp_loc, _dict):
    state = _state()
    handoff = state.get("terminal_selected_record_handoff")
    if handoff is None or handoff.get("caller_key") != _frame_key(frame):
        return False
    process = frame.GetThread().GetProcess()
    handoff.update(
        {
            "call_libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
            "destination": _register(frame, "rdi"),
            "left_record": _register(frame, "rsi"),
            "right_record": _register(frame, "rdx"),
            "right_snapshot": _snapshot(process, _register(frame, "rdx"), 0x80),
            "destination_before": _snapshot(process, _register(frame, "rdi"), 0xA4),
        }
    )
    state["counts"]["terminal_composer_handoffs"] += 1
    _enable_breakpoints(
        process.GetTarget(),
        ("terminal_composer_return", "terminal_node_fields"),
    )
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def terminal_composer_return_hit(frame, bp_loc, _dict):
    state = _state()
    handoff = state.get("terminal_selected_record_handoff")
    if handoff is None or handoff.get("caller_key") != _frame_key(frame):
        return False
    process = frame.GetThread().GetProcess()
    handoff["return_libcp_va"] = _module_va(process.GetTarget(), frame.GetPC())
    handoff["destination_after"] = _snapshot(
        process, handoff["destination"], 0xA4
    )
    state["counts"]["terminal_composer_returns"] += 1
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def terminal_node_fields_hit(frame, bp_loc, _dict):
    state = _state()
    handoff = state.get("terminal_selected_record_handoff")
    if handoff is None or handoff.get("caller_key") != _frame_key(frame):
        return False
    process = frame.GetThread().GetProcess()
    node = _register(frame, "rbx")
    rbp = _register(frame, "rbp")
    handoff["node_fields_libcp_va"] = _module_va(
        process.GetTarget(), frame.GetPC()
    )
    handoff["local_key"] = _snapshot(process, rbp - 0x2D0, 4)
    handoff["node"] = node
    handoff["node_key"] = _snapshot(process, node + 0x20, 4)
    handoff["node_mapped_fields"] = _snapshot(process, node + 0x28, 0x40)
    handoff["destination_at_node"] = _snapshot(
        process, handoff["destination"], 0xA4
    )
    state["counts"]["terminal_node_materializations"] += 1
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    address = node + 0x28
    watchpoint = process.GetTarget().WatchAddress(address, 8, True, True, error)
    if not error.Success() or not watchpoint or not watchpoint.IsValid():
        state["errors"].append(
            {
                "error": "terminal node watchpoint arm failed",
                "detail": error.GetCString(),
            }
        )
    else:
        state["terminal_node_watchpoint_id"] = watchpoint.GetID()
        state["terminal_node_watch_armed"] = {
            "watch_address": address,
            "watch_size": 8,
            "value_at_arm": _snapshot(process, address, 8),
            "node": node,
        }
        state["counts"]["terminal_node_watchpoints_armed"] += 1
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def terminal_node_copy_return_hit(frame, bp_loc, _dict):
    state = _state()
    active = state.get("terminal_node_copy_active")
    if active is None or active.get("frame_key") != _frame_key(frame):
        return False
    process = frame.GetThread().GetProcess()
    copied_node = _register(frame, "r15")
    copied = {
        "return_libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
        "source_node": active["source_node"],
        "allocated_node": active["allocated_node"],
        "copied_node": copied_node,
        "source_payload": _snapshot(process, active["source_node"] + 0x20, 0x84),
        "copied_payload": _snapshot(process, copied_node + 0x20, 0x84),
    }
    state["terminal_node_copy"] = copied
    state["counts"]["terminal_node_copy_returns"] += 1

    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    address = copied_node + 0x28
    watchpoint = process.GetTarget().WatchAddress(address, 8, True, True, error)
    if not error.Success() or not watchpoint or not watchpoint.IsValid():
        state["errors"].append(
            {
                "error": "terminal copied-node watchpoint arm failed",
                "detail": error.GetCString(),
            }
        )
    else:
        state["terminal_node_copy_watchpoint_id"] = watchpoint.GetID()
        state["terminal_node_copy_watch_armed"] = {
            "watch_address": address,
            "watch_size": 8,
            "value_at_arm": _snapshot(process, address, 8),
            "copied_node": copied_node,
        }
        state["counts"]["terminal_node_copy_watchpoints_armed"] += 1
    state["terminal_node_copy_active"] = None
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def terminal_transform_return_hit(frame, bp_loc, _dict):
    state = _state()
    active = state.get("terminal_transform_active")
    if active is None or active.get("frame_key") != _frame_key(frame):
        return False
    process = frame.GetThread().GetProcess()
    node_copy = state["terminal_node_copy"]
    transformed = {
        "return_libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
        "source_node": node_copy["source_node"],
        "copied_node": node_copy["copied_node"],
        "source_payload_after": _snapshot(
            process, node_copy["source_node"] + 0x20, 0x84
        ),
        "copied_payload_before": node_copy["copied_payload"],
        "copied_payload_after": _snapshot(
            process, node_copy["copied_node"] + 0x20, 0x84
        ),
    }
    state["terminal_transform"] = transformed
    state["counts"]["terminal_transform_returns"] += 1

    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    address = node_copy["copied_node"] + 0x70
    watchpoint = process.GetTarget().WatchAddress(address, 8, True, True, error)
    if not error.Success() or not watchpoint or not watchpoint.IsValid():
        state["errors"].append(
            {
                "error": "terminal post-transform watchpoint arm failed",
                "detail": error.GetCString(),
            }
        )
    else:
        state["terminal_post_transform_watchpoint_id"] = watchpoint.GetID()
        state["terminal_post_transform_watch_armed"] = {
            "watch_address": address,
            "watch_size": 8,
            "value_at_arm": _snapshot(process, address, 8),
            "copied_node": node_copy["copied_node"],
        }
        state["counts"]["terminal_post_transform_watchpoints_armed"] += 1
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def terminal_normalized_convert_call_hit(frame, bp_loc, _dict):
    state = _state()
    active = state.get("terminal_transform_active")
    if active is None or active.get("frame_key") != _frame_key(frame):
        return False
    process = frame.GetThread().GetProcess()
    pipeline = {
        "caller_key": _frame_key(frame),
        "convert_call_libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
        "transformed_node": state["terminal_transform"]["copied_node"],
        "convert_destination": _register(frame, "rdi"),
        "convert_source": _register(frame, "rsi"),
        "convert_aux": _register(frame, "rdx"),
        "local_key": _snapshot(
            process, _register(frame, "rbp") - 0x4E0, 4
        ),
        "convert_source_snapshot": _snapshot(
            process, _register(frame, "rsi"), 0x7C
        ),
        "convert_destination_before": _snapshot(
            process, _register(frame, "rdi"), 0xA4
        ),
    }
    state["terminal_normalized_pipeline"] = pipeline
    state["counts"]["terminal_normalized_convert_calls"] += 1
    _enable_breakpoints(
        process.GetTarget(), ("terminal_normalized_convert_return",)
    )
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def terminal_normalized_convert_return_hit(frame, bp_loc, _dict):
    state = _state()
    pipeline = state.get("terminal_normalized_pipeline")
    if pipeline is None or pipeline.get("caller_key") != _frame_key(frame):
        return False
    process = frame.GetThread().GetProcess()
    pipeline["convert_return_libcp_va"] = _module_va(
        process.GetTarget(), frame.GetPC()
    )
    pipeline["convert_returned_rax"] = _register(frame, "rax")
    pipeline["convert_destination_after"] = _snapshot(
        process, pipeline["convert_destination"], 0xA4
    )
    state["counts"]["terminal_normalized_convert_returns"] += 1
    _enable_breakpoints(
        process.GetTarget(), ("terminal_normalized_compose_call",)
    )
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def terminal_normalized_compose_call_hit(frame, bp_loc, _dict):
    state = _state()
    pipeline = state.get("terminal_normalized_pipeline")
    if pipeline is None or pipeline.get("caller_key") != _frame_key(frame):
        return False
    process = frame.GetThread().GetProcess()
    pipeline["compose_call_libcp_va"] = _module_va(
        process.GetTarget(), frame.GetPC()
    )
    pipeline["compose_destination"] = _register(frame, "rdi")
    pipeline["compose_left"] = _register(frame, "rsi")
    pipeline["compose_right"] = _register(frame, "rdx")
    pipeline["compose_left_snapshot"] = _snapshot(
        process, _register(frame, "rsi"), 0xA4
    )
    pipeline["compose_right_snapshot"] = _snapshot(
        process, _register(frame, "rdx"), 0xA4
    )
    pipeline["compose_destination_before"] = _snapshot(
        process, _register(frame, "rdi"), 0xA4
    )
    state["counts"]["terminal_normalized_compose_calls"] += 1
    _enable_breakpoints(
        process.GetTarget(), ("terminal_normalized_compose_return",)
    )
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def terminal_normalized_compose_return_hit(frame, bp_loc, _dict):
    state = _state()
    pipeline = state.get("terminal_normalized_pipeline")
    if pipeline is None or pipeline.get("caller_key") != _frame_key(frame):
        return False
    process = frame.GetThread().GetProcess()
    pipeline["compose_return_libcp_va"] = _module_va(
        process.GetTarget(), frame.GetPC()
    )
    pipeline["compose_returned_rax"] = _register(frame, "rax")
    pipeline["compose_destination_after"] = _snapshot(
        process, pipeline["compose_destination"], 0xA4
    )
    state["counts"]["terminal_normalized_compose_returns"] += 1
    _enable_breakpoints(
        process.GetTarget(), ("terminal_normalized_f33d0_call",)
    )
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def terminal_normalized_f33d0_call_hit(frame, bp_loc, _dict):
    state = _state()
    pipeline = state.get("terminal_normalized_pipeline")
    if pipeline is None or pipeline.get("caller_key") != _frame_key(frame):
        return False
    process = frame.GetThread().GetProcess()
    pipeline["f33d0_call_libcp_va"] = _module_va(
        process.GetTarget(), frame.GetPC()
    )
    pipeline["f33d0_destination_object"] = _register(frame, "rdi")
    pipeline["f33d0_destination_key"] = _snapshot(
        process, _register(frame, "rdi") + 0x60, 4
    )
    pipeline["f33d0_selector"] = _register(frame, "r8") & 0xFFFFFFFF
    pipeline["f33d0_source_1"] = _register(frame, "rsi")
    pipeline["f33d0_source_2"] = _register(frame, "rdx")
    pipeline["f33d0_source_3"] = _register(frame, "rcx")
    pipeline["f33d0_source_1_snapshot"] = _snapshot(
        process, _register(frame, "rsi"), 0x24
    )
    pipeline["f33d0_source_2_snapshot"] = _snapshot(
        process, _register(frame, "rdx"), 0x24
    )
    pipeline["f33d0_source_3_snapshot"] = _snapshot(
        process, _register(frame, "rcx"), 0x0C
    )
    pipeline["f33d0_bank_before"] = _snapshot(
        process, _register(frame, "rdi") + 0x12C, 0x54
    )
    state["counts"]["terminal_normalized_f33d0_calls"] += 1
    _enable_breakpoints(
        process.GetTarget(), ("terminal_normalized_f33d0_return",)
    )
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def terminal_normalized_f33d0_return_hit(frame, bp_loc, _dict):
    state = _state()
    pipeline = state.get("terminal_normalized_pipeline")
    if pipeline is None or pipeline.get("caller_key") != _frame_key(frame):
        return False
    process = frame.GetThread().GetProcess()
    pipeline["f33d0_return_libcp_va"] = _module_va(
        process.GetTarget(), frame.GetPC()
    )
    pipeline["f33d0_bank_after"] = _snapshot(
        process, pipeline["f33d0_destination_object"] + 0x12C, 0x54
    )
    pipeline["outer_caller_libcp_va"] = _module_va(
        process.GetTarget(), frame.GetThread().GetFrameAtIndex(1).GetPC()
    )
    state["terminal_normalized_postwrite_consumer"] = {
        "destination_object": pipeline["f33d0_destination_object"],
        "destination_key": pipeline["f33d0_destination_key"],
        "bank_after_write": pipeline["f33d0_bank_after"],
        "second_helper_call": None,
        "assembly_calls": [],
        "matched_read": None,
    }
    state["counts"]["terminal_normalized_f33d0_returns"] += 1
    _enable_breakpoints(process.GetTarget(), ("terminal_second_helper_call",))
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def terminal_second_helper_call_hit(frame, bp_loc, _dict):
    state = _state()
    custody = state.get("terminal_normalized_postwrite_consumer")
    if custody is None:
        return False
    process = frame.GetThread().GetProcess()
    custody["second_helper_call"] = {
        "libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
        "bank_at_call": _snapshot(
            process, custody["destination_object"] + 0x12C, 0x54
        ),
        "destination_key_at_call": _snapshot(
            process, custody["destination_object"] + 0x60, 4
        ),
        "stack": _stack(frame.GetThread()),
    }
    state["counts"]["terminal_second_helper_calls"] += 1
    _enable_breakpoints(
        process.GetTarget(),
        (
            "terminal_second_assembly_23c6c0",
            "terminal_second_assembly_23cba6",
            "terminal_second_assembly_23d226",
        ),
    )
    bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def terminal_second_assembly_hit(frame, bp_loc, _dict):
    state = _state()
    custody = state.get("terminal_normalized_postwrite_consumer")
    if custody is None or custody.get("second_helper_call") is None:
        return False
    process = frame.GetThread().GetProcess()
    source_object = _register(frame, "rsi")
    packet = {
        "libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
        "source_object": source_object,
        "source_key": _snapshot(process, source_object + 0x60, 4),
        "source_bank": _snapshot(process, source_object + 0x12C, 0x54),
        "matches_destination_object": (
            source_object == custody["destination_object"]
        ),
        "stack": _stack(frame.GetThread()),
    }
    packet["exact_postwrite_bank"] = bool(
        packet["matches_destination_object"]
        and packet["source_bank"]["hex"] == custody["bank_after_write"]["hex"]
    )
    custody["assembly_calls"].append(packet)
    state["counts"]["terminal_second_assembly_calls"] += 1
    if packet["exact_postwrite_bank"]:
        custody["matched_read"] = packet
        state["counts"]["terminal_second_exact_postwrite_reads"] += 1
        for name in (
            "terminal_second_assembly_23c6c0",
            "terminal_second_assembly_23cba6",
            "terminal_second_assembly_23d226",
        ):
            process.GetTarget().FindBreakpointByID(
                state["breakpoints"][name]
            ).SetEnabled(False)
    return False


def _add_breakpoint(debugger, name, address, callback):
    state = _state()
    target = debugger.GetSelectedTarget()
    before = target.GetNumBreakpoints()
    debugger.HandleCommand(f"breakpoint set --shlib libcp.dylib --address 0x{address:x}")
    if target.GetNumBreakpoints() <= before:
        state["errors"].append({"error": "breakpoint not created", "name": name})
        return
    breakpoint = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
    breakpoint.SetScriptCallbackFunction(callback)
    state["breakpoints"][name] = breakpoint.GetID()


def install(debugger):
    specs = (
        ("f33d0_call", F33D0_CALL, "f33d0_call_hit"),
        ("f33d0_return", F33D0_RETURN, "f33d0_return_hit"),
        ("assembly_entry", ASSEMBLY_ENTRY, "assembly_entry_hit"),
        ("assembly_return", ASSEMBLY_RETURN, "assembly_return_hit"),
        ("composer_return", COMPOSER_RETURN, "composer_return_hit"),
        ("wide_return", WIDE_RETURN, "wide_return_hit"),
        ("wide_store_return", WIDE_STORE_RETURN, "wide_store_return_hit"),
        ("tele_helper_done", TELE_HELPER_DONE, "tele_helper_done_hit"),
        ("tele_caller_post", TELE_CALLER_POST, "tele_caller_post_hit"),
        ("tele_node_post", TELE_NODE_POST, "tele_node_post_hit"),
        ("wide_decision_compare", WIDE_DECISION_COMPARE, "wide_decision_compare_hit"),
        ("wide_decision_update", WIDE_DECISION_UPDATE, "wide_decision_update_hit"),
        ("wide_decision_skip", WIDE_DECISION_SKIP, "wide_decision_skip_hit"),
        ("wide_decision_store", WIDE_DECISION_STORE, "wide_decision_store_hit"),
        ("wide_update_new_node", WIDE_UPDATE_NEW_NODE, "wide_update_path_hit"),
        ("wide_update_missing", WIDE_UPDATE_MISSING, "wide_update_path_hit"),
        ("wide_update_existing", WIDE_UPDATE_EXISTING, "wide_update_path_hit"),
        ("wide_update_continue", WIDE_UPDATE_CONTINUE, "wide_update_path_hit"),
        (
            "wide_calib_transfer_call",
            WIDE_CALIB_TRANSFER_CALL,
            "wide_calib_transfer_call_hit",
        ),
        (
            "wide_calib_transfer_return",
            WIDE_CALIB_TRANSFER_RETURN,
            "wide_calib_transfer_return_hit",
        ),
        (
            "terminal_composer_call",
            TERMINAL_COMPOSER_CALL,
            "terminal_composer_call_hit",
        ),
        (
            "terminal_composer_return",
            TERMINAL_COMPOSER_RETURN,
            "terminal_composer_return_hit",
        ),
        (
            "terminal_node_fields",
            TERMINAL_NODE_FIELDS,
            "terminal_node_fields_hit",
        ),
        (
            "terminal_node_copy_return",
            TERMINAL_NODE_COPY_RETURN,
            "terminal_node_copy_return_hit",
        ),
        (
            "terminal_transform_return",
            TERMINAL_TRANSFORM_RETURN,
            "terminal_transform_return_hit",
        ),
        (
            "terminal_normalized_convert_call",
            TERMINAL_NORMALIZED_CONVERT_CALL,
            "terminal_normalized_convert_call_hit",
        ),
        (
            "terminal_normalized_convert_return",
            TERMINAL_NORMALIZED_CONVERT_RETURN,
            "terminal_normalized_convert_return_hit",
        ),
        (
            "terminal_normalized_compose_call",
            TERMINAL_NORMALIZED_COMPOSE_CALL,
            "terminal_normalized_compose_call_hit",
        ),
        (
            "terminal_normalized_compose_return",
            TERMINAL_NORMALIZED_COMPOSE_RETURN,
            "terminal_normalized_compose_return_hit",
        ),
        (
            "terminal_normalized_f33d0_call",
            TERMINAL_NORMALIZED_F33D0_CALL,
            "terminal_normalized_f33d0_call_hit",
        ),
        (
            "terminal_normalized_f33d0_return",
            TERMINAL_NORMALIZED_F33D0_RETURN,
            "terminal_normalized_f33d0_return_hit",
        ),
        (
            "terminal_second_helper_call",
            TERMINAL_SECOND_HELPER_CALL,
            "terminal_second_helper_call_hit",
        ),
        (
            "terminal_second_assembly_23c6c0",
            TERMINAL_SECOND_ASSEMBLY_CALLS[0],
            "terminal_second_assembly_hit",
        ),
        (
            "terminal_second_assembly_23cba6",
            TERMINAL_SECOND_ASSEMBLY_CALLS[1],
            "terminal_second_assembly_hit",
        ),
        (
            "terminal_second_assembly_23d226",
            TERMINAL_SECOND_ASSEMBLY_CALLS[2],
            "terminal_second_assembly_hit",
        ),
    )
    for name, address, callback in specs:
        _add_breakpoint(
            debugger,
            name,
            address,
            f"prefusion_264270_output_watch_probe.{callback}",
        )
    composer_bp = debugger.GetSelectedTarget().FindBreakpointByID(
        _state()["breakpoints"]["composer_return"]
    )
    composer_bp.SetEnabled(False)
    for name in (
        "wide_return",
        "wide_store_return",
        "tele_helper_done",
        "tele_caller_post",
        "tele_node_post",
        "wide_decision_compare",
        "wide_decision_update",
        "wide_decision_skip",
        "wide_decision_store",
        "wide_update_new_node",
        "wide_update_missing",
        "wide_update_existing",
        "wide_update_continue",
        "wide_calib_transfer_call",
        "wide_calib_transfer_return",
        "terminal_composer_call",
        "terminal_composer_return",
        "terminal_node_fields",
        "terminal_node_copy_return",
        "terminal_transform_return",
        "terminal_normalized_convert_call",
        "terminal_normalized_convert_return",
        "terminal_normalized_compose_call",
        "terminal_normalized_compose_return",
        "terminal_normalized_f33d0_call",
        "terminal_normalized_f33d0_return",
        "terminal_second_helper_call",
        "terminal_second_assembly_23c6c0",
        "terminal_second_assembly_23cba6",
        "terminal_second_assembly_23d226",
    ):
        debugger.GetSelectedTarget().FindBreakpointByID(
            _state()["breakpoints"][name]
        ).SetEnabled(False)
    print("L16_PREFUSION_264270_OUTPUT_WATCH_INSTALLED", _state()["breakpoints"])


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
        thread = process.GetSelectedThread()
        if thread and thread.IsValid() and thread.GetStopReason() == lldb.eStopReasonWatchpoint:
            wp_id = thread.GetStopReasonDataAtIndex(0) if thread.GetStopReasonDataCount() else None
            if wp_id == state["watchpoint_id"]:
                frame = thread.GetFrameAtIndex(0)
                armed = state["watch_armed"]
                before = (
                    state["watch_samples"][-1]["value_now"]
                    if state["watch_samples"]
                    else armed["value_at_arm"]
                )
                now = _snapshot(process, armed["watch_address"], 8)
                changed = now["hex"] != before["hex"]
                state["watch_samples"].append(
                    {
                        "ordinal": state["counts"]["watchpoint_hits"] + 1,
                        "thread_id": thread.GetThreadID(),
                        "pc": frame.GetPC(),
                        "libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
                        "value_before": before,
                        "value_now": now,
                        "changed": changed,
                        "registers": _registers(frame),
                        "stack": _stack(thread),
                    }
                )
                state["counts"]["watchpoint_hits"] += 1
                if changed:
                    state["counts"]["watch_value_changes"] += 1
                if state["counts"]["watchpoint_hits"] >= state["hit_cap"]:
                    watchpoint = process.GetTarget().FindWatchpointByID(state["watchpoint_id"])
                    if watchpoint and watchpoint.IsValid():
                        watchpoint.SetEnabled(False)
                    state["composer_active"] = {
                        "key": _frame_key(frame),
                        "thread_id": thread.GetThreadID(),
                        "rbp": _register(frame, "rbp"),
                        "destination": _register(frame, "r12"),
                        "input_record": _register(frame, "rbx"),
                        "first_consumer_libcp_va": _module_va(
                            process.GetTarget(), frame.GetPC()
                        ),
                    }
                    composer_bp = process.GetTarget().FindBreakpointByID(
                        state["breakpoints"]["composer_return"]
                    )
                    composer_bp.SetEnabled(True)
            elif wp_id == state["composer_watchpoint_id"]:
                frame = thread.GetFrameAtIndex(0)
                armed = state["composer_watch_armed"]
                before = (
                    state["composer_watch_samples"][-1]["value_now"]
                    if state["composer_watch_samples"]
                    else armed["value_at_arm"]
                )
                now = _snapshot(process, armed["watch_address"], 8)
                changed = now["hex"] != before["hex"]
                state["composer_watch_samples"].append(
                    {
                        "ordinal": state["counts"]["composer_watchpoint_hits"] + 1,
                        "thread_id": thread.GetThreadID(),
                        "pc": frame.GetPC(),
                        "libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
                        "value_before": before,
                        "value_now": now,
                        "changed": changed,
                        "registers": _registers(frame),
                        "stack": _stack(thread),
                    }
                )
                state["counts"]["composer_watchpoint_hits"] += 1
                if changed:
                    state["counts"]["composer_watch_value_changes"] += 1
                watchpoint = process.GetTarget().FindWatchpointByID(
                    state["composer_watchpoint_id"]
                )
                if watchpoint and watchpoint.IsValid():
                    watchpoint.SetEnabled(False)
                process.GetTarget().FindBreakpointByID(
                    state["breakpoints"]["wide_decision_store"]
                ).SetEnabled(False)
                route_va = _module_va(process.GetTarget(), frame.GetPC())
                parent = thread.GetFrameAtIndex(1)
                if route_va == 0x23A181:
                    state["post_transform"] = {
                        "kind": "wide",
                        "helper_key": _frame_key(frame),
                        "caller_key": _frame_key(parent),
                        "composer_destination": armed["destination"],
                    }
                    _enable_breakpoints(
                        process.GetTarget(), ("wide_return", "wide_store_return")
                    )
                elif route_va == 0x20DBF3:
                    state["post_transform"] = {
                        "kind": "tele",
                        "helper_key": _frame_key(frame),
                        "caller_key": _frame_key(parent),
                        "composer_destination": armed["destination"],
                    }
                    _enable_breakpoints(
                        process.GetTarget(),
                        ("tele_helper_done", "tele_caller_post", "tele_node_post"),
                    )
                else:
                    state["errors"].append(
                        {"error": "unknown composer consumer route", "libcp_va": route_va}
                    )
            elif wp_id == state["storage_watchpoint_id"]:
                frame = thread.GetFrameAtIndex(0)
                armed = state["storage_watch_armed"]
                before = (
                    state["storage_watch_samples"][-1]["value_now"]
                    if state["storage_watch_samples"]
                    else armed["value_at_arm"]
                )
                now = _snapshot(process, armed["watch_address"], armed["watch_size"])
                changed = now["hex"] != before["hex"]
                state["storage_watch_samples"].append(
                    {
                        "ordinal": state["counts"]["storage_watchpoint_hits"] + 1,
                        "kind": armed["kind"],
                        "thread_id": thread.GetThreadID(),
                        "pc": frame.GetPC(),
                        "libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
                        "value_before": before,
                        "value_now": now,
                        "changed": changed,
                        "registers": _registers(frame),
                        "stack": _stack(thread),
                    }
                )
                state["counts"]["storage_watchpoint_hits"] += 1
                if changed:
                    state["counts"]["storage_watch_value_changes"] += 1
                watchpoint = process.GetTarget().FindWatchpointByID(
                    state["storage_watchpoint_id"]
                )
                if watchpoint and watchpoint.IsValid():
                    watchpoint.SetEnabled(False)
                if armed["kind"] == "wide_score":
                    parent = thread.GetFrameAtIndex(1)
                    state["post_transform"]["wide_state_key"] = _frame_key(parent)
                    _enable_breakpoints(
                        process.GetTarget(),
                        (
                            "wide_decision_compare",
                            "wide_decision_update",
                            "wide_decision_skip",
                            "wide_decision_store",
                        ),
                    )
            elif wp_id == state["decision_local_watchpoint_id"]:
                frame = thread.GetFrameAtIndex(0)
                armed = state["decision_local_watch_armed"]
                now = _snapshot(process, armed["watch_address"], armed["watch_size"])
                state["decision_local_watch_samples"].append(
                    {
                        "ordinal": state["counts"]["decision_local_watchpoint_hits"] + 1,
                        "thread_id": thread.GetThreadID(),
                        "pc": frame.GetPC(),
                        "libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
                        "value_before": armed["value_at_arm"],
                        "value_now": now,
                        "changed": now["hex"] != armed["value_at_arm"]["hex"],
                        "registers": _registers(frame),
                        "stack": _stack(thread),
                    }
                )
                state["counts"]["decision_local_watchpoint_hits"] += 1
                watchpoint = process.GetTarget().FindWatchpointByID(
                    state["decision_local_watchpoint_id"]
                )
                if watchpoint and watchpoint.IsValid():
                    watchpoint.SetEnabled(False)
            elif wp_id == state["calib_transfer_watchpoint_id"]:
                frame = thread.GetFrameAtIndex(0)
                parent = thread.GetFrameAtIndex(1)
                armed = state["calib_transfer_watch_armed"]
                now = _snapshot(process, armed["watch_address"], armed["watch_size"])
                state["calib_transfer_watch_samples"].append(
                    {
                        "ordinal": state["counts"]["calib_transfer_watchpoint_hits"] + 1,
                        "thread_id": thread.GetThreadID(),
                        "pc": frame.GetPC(),
                        "libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
                        "value_before": armed["value_at_arm"],
                        "value_now": now,
                        "changed": now["hex"] != armed["value_at_arm"]["hex"],
                        "registers": _registers(frame),
                        "stack": _stack(thread),
                    }
                )
                state["counts"]["calib_transfer_watchpoint_hits"] += 1
                state["terminal_selected_record_handoff"] = {
                    "caller_key": _frame_key(parent),
                    "assembly_output": _register(frame, "rbx"),
                    "source_object": _register(frame, "r15"),
                }
                _enable_breakpoints(
                    process.GetTarget(), ("terminal_composer_call",)
                )
                watchpoint = process.GetTarget().FindWatchpointByID(
                    state["calib_transfer_watchpoint_id"]
                )
                if watchpoint and watchpoint.IsValid():
                    watchpoint.SetEnabled(False)
            elif wp_id == state["terminal_node_watchpoint_id"]:
                frame = thread.GetFrameAtIndex(0)
                armed = state["terminal_node_watch_armed"]
                now = _snapshot(process, armed["watch_address"], armed["watch_size"])
                state["terminal_node_watch_samples"].append(
                    {
                        "ordinal": state["counts"]["terminal_node_watchpoint_hits"] + 1,
                        "thread_id": thread.GetThreadID(),
                        "pc": frame.GetPC(),
                        "libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
                        "value_before": armed["value_at_arm"],
                        "value_now": now,
                        "changed": now["hex"] != armed["value_at_arm"]["hex"],
                        "registers": _registers(frame),
                        "stack": _stack(thread),
                    }
                )
                state["counts"]["terminal_node_watchpoint_hits"] += 1
                state["terminal_node_copy_active"] = {
                    "frame_key": _frame_key(frame),
                    "source_node": armed["node"],
                    "allocated_node": _register(frame, "r12"),
                }
                _enable_breakpoints(
                    process.GetTarget(), ("terminal_node_copy_return",)
                )
                watchpoint = process.GetTarget().FindWatchpointByID(
                    state["terminal_node_watchpoint_id"]
                )
                if watchpoint and watchpoint.IsValid():
                    watchpoint.SetEnabled(False)
            elif wp_id == state["terminal_node_copy_watchpoint_id"]:
                frame = thread.GetFrameAtIndex(0)
                caller = thread.GetFrameAtIndex(2)
                armed = state["terminal_node_copy_watch_armed"]
                now = _snapshot(process, armed["watch_address"], armed["watch_size"])
                state["terminal_node_copy_watch_samples"].append(
                    {
                        "ordinal": state["counts"]["terminal_node_copy_watchpoint_hits"] + 1,
                        "thread_id": thread.GetThreadID(),
                        "pc": frame.GetPC(),
                        "libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
                        "value_before": armed["value_at_arm"],
                        "value_now": now,
                        "changed": now["hex"] != armed["value_at_arm"]["hex"],
                        "registers": _registers(frame),
                        "stack": _stack(thread),
                    }
                )
                state["counts"]["terminal_node_copy_watchpoint_hits"] += 1
                state["terminal_transform_active"] = {
                    "frame_key": _frame_key(caller),
                }
                _enable_breakpoints(
                    process.GetTarget(), ("terminal_transform_return",)
                )
                watchpoint = process.GetTarget().FindWatchpointByID(
                    state["terminal_node_copy_watchpoint_id"]
                )
                if watchpoint and watchpoint.IsValid():
                    watchpoint.SetEnabled(False)
            elif wp_id == state["terminal_post_transform_watchpoint_id"]:
                frame = thread.GetFrameAtIndex(0)
                armed = state["terminal_post_transform_watch_armed"]
                now = _snapshot(process, armed["watch_address"], armed["watch_size"])
                state["terminal_post_transform_watch_samples"].append(
                    {
                        "ordinal": state["counts"]["terminal_post_transform_watchpoint_hits"] + 1,
                        "thread_id": thread.GetThreadID(),
                        "pc": frame.GetPC(),
                        "libcp_va": _module_va(process.GetTarget(), frame.GetPC()),
                        "value_before": armed["value_at_arm"],
                        "value_now": now,
                        "changed": now["hex"] != armed["value_at_arm"]["hex"],
                        "registers": _registers(frame),
                        "stack": _stack(thread),
                    }
                )
                state["counts"]["terminal_post_transform_watchpoint_hits"] += 1
                _enable_breakpoints(
                    process.GetTarget(), ("terminal_normalized_convert_call",)
                )
                watchpoint = process.GetTarget().FindWatchpointByID(
                    state["terminal_post_transform_watchpoint_id"]
                )
                if watchpoint and watchpoint.IsValid():
                    watchpoint.SetEnabled(False)
            else:
                state["errors"].append({"error": "unexpected watchpoint", "watchpoint_id": wp_id})
        process.Continue()
    state["drive_steps"] = steps
    if process and process.IsValid():
        state["process_state"] = int(process.GetState())
        state["process_exit_status"] = process.GetExitStatus()
    print("L16_PREFUSION_264270_OUTPUT_WATCH_DRIVE_STEPS", steps)


def payload(debugger):
    state = _state()
    packet = dict(state)
    packet["pending_f33d0"] = list(state["pending_f33d0"])
    packet["accepted_objects"] = list(state["accepted_objects"].values())
    packet["active_assembly"] = list(state["active_assembly"])
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
