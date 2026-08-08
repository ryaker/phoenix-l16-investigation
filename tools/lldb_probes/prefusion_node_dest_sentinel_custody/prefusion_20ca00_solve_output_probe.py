import builtins
import json
import os
import struct


ENTRY = 0x20CA14
ADD_RESIDUAL = 0x20D560
SOLVE_PRE = 0x20D611
SOLVE_POST = 0x20D616
FIRST_TRIPLE_POST = 0x20D6B6
SECOND_TRIPLE_POST = 0x20D737
RETURN = 0x20D8AC


def reset(label="", sample_limit=64):
    builtins.l16_prefusion_20ca00_solve_output = {
        "label": label,
        "sample_limit": sample_limit,
        "breakpoint_ids": {},
        "counts": {
            "entries": 0,
            "add_residual_calls": 0,
            "solve_pre_hits": 0,
            "solve_post_hits": 0,
            "first_triple_post_hits": 0,
            "second_triple_post_hits": 0,
            "returns": 0,
        },
        "frames": [],
        "errors": [],
        "_active": {},
        "_next_frame_id": 1,
    }


def _state():
    if not hasattr(builtins, "l16_prefusion_20ca00_solve_output"):
        reset()
    return builtins.l16_prefusion_20ca00_solve_output


def _read(process, addr, size):
    if not addr or size < 0:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u64(process, addr):
    data = _read(process, addr, 8)
    return struct.unpack("<Q", data)[0] if data is not None else None


def _s64(process, addr):
    data = _read(process, addr, 8)
    return struct.unpack("<q", data)[0] if data is not None else None


def _s32(process, addr):
    data = _read(process, addr, 4)
    return struct.unpack("<i", data)[0] if data is not None else None


def _f64(process, addr):
    data = _read(process, addr, 8)
    return struct.unpack("<d", data)[0] if data is not None else None


def _f32x3(process, addr):
    data = _read(process, addr, 12)
    if data is None:
        return {"addr": addr, "read_ok": False}
    return {
        "addr": addr,
        "read_ok": True,
        "values": list(struct.unpack("<3f", data)),
        "hex": data.hex(),
    }


def _module_va(target, address):
    lldb = builtins.__import__("lldb")
    module = target.FindModule(lldb.SBFileSpec("libcp.dylib"))
    if not module or not module.IsValid():
        return None
    header = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
    if header in (0, (1 << 64) - 1):
        return None
    return address - header


def _regs(frame):
    names = ("rax", "rbx", "rcx", "rdx", "rsi", "rdi", "r8", "r9", "rbp", "rsp")
    return {name: frame.FindRegister(name).GetValueAsUnsigned() for name in names}


def _frame_key(frame):
    return f"{frame.GetThread().GetThreadID()}:{frame.FindRegister('rbp').GetValueAsUnsigned()}"


def _context_fields(process, context):
    return {
        "context": context,
        "qword_0x08": _u64(process, context + 0x08) if context else None,
        "qword_0x20": _u64(process, context + 0x20) if context else None,
        "qword_0x28": _u64(process, context + 0x28) if context else None,
        "qword_0x30": _u64(process, context + 0x30) if context else None,
        "qword_0x38": _u64(process, context + 0x38) if context else None,
        "qword_0x40": _u64(process, context + 0x40) if context else None,
    }


def _snapshot(frame, site):
    process = frame.GetThread().GetProcess()
    rbp = frame.FindRegister("rbp").GetValueAsUnsigned()
    context = _u64(process, rbp - 0x2B8)
    record_begin = _u64(process, rbp - 0x2C8)
    record_offset = _s64(process, rbp - 0x2D0)
    triple_addr = None
    if record_begin is not None and record_offset is not None:
        triple_addr = record_begin + 4 * record_offset + 8
    return {
        "site": site,
        "thread_id": frame.GetThread().GetThreadID(),
        "rbp": rbp,
        "context": _context_fields(process, context),
        "gate_index": _s64(process, rbp - 0x2A0),
        "outer_count": _s64(process, rbp - 0x2D8),
        "source_record_begin": record_begin,
        "source_record_offset": record_offset,
        "source_coordinate_ptr": _u64(process, rbp - 0x2C0),
        "parameter_scalar_addr": rbp - 0xC8,
        "parameter_scalar": _f64(process, rbp - 0xC8),
        "problem_addr": rbp - 0xC0,
        "summary_addr": rbp - 0x298,
        "output_triple": _f32x3(process, triple_addr) if triple_addr else None,
        "registers": _regs(frame),
    }


def _active_frame(frame):
    state = _state()
    key = _frame_key(frame)
    record = state["_active"].get(key)
    if record is None:
        state["errors"].append({"error": "site without active frame", "key": key})
    return record


def _entry(frame):
    state = _state()
    process = frame.GetThread().GetProcess()
    regs = _regs(frame)
    key = _frame_key(frame)
    record = {
        "frame_id": state["_next_frame_id"],
        "frame_key": key,
        "thread_id": frame.GetThread().GetThreadID(),
        "rbp": regs["rbp"],
        "entry": {
            "context": _context_fields(process, regs["rdi"]),
            "start_index_ptr": regs["rsi"],
            "start_index": _s32(process, regs["rsi"]),
            "outer_count_ptr": regs["rdx"],
            "outer_count": _s32(process, regs["rdx"]),
            "registers": regs,
        },
        "add_residual_calls": [],
        "add_residual_count": 0,
        "snapshots": [],
        "completed": False,
    }
    state["_next_frame_id"] += 1
    state["_active"][key] = record
    state["counts"]["entries"] += 1


def _add_residual(frame):
    state = _state()
    record = _active_frame(frame)
    if record is None:
        return
    regs = _regs(frame)
    record["add_residual_count"] += 1
    if len(record["add_residual_calls"]) < state["sample_limit"]:
        record["add_residual_calls"].append(
            {
                "ordinal": record["add_residual_count"],
                "problem": regs["rdi"],
                "cost_function": regs["rsi"],
                "loss_function": regs["rdx"],
                "parameter": regs["rcx"],
                "parameter_value": _f64(frame.GetThread().GetProcess(), regs["rcx"]),
            }
        )
    state["counts"]["add_residual_calls"] += 1


def _site_snapshot(frame, site, count_key):
    state = _state()
    record = _active_frame(frame)
    if record is None:
        return
    record["snapshots"].append(_snapshot(frame, site))
    state["counts"][count_key] += 1


def _return(frame):
    state = _state()
    key = _frame_key(frame)
    record = state["_active"].pop(key, None)
    if record is None:
        state["errors"].append({"error": "return without active frame", "key": key})
        return
    record["return"] = _snapshot(frame, "return_20d8ac")
    record["completed"] = True
    state["frames"].append(record)
    state["counts"]["returns"] += 1


def hit(frame, bp_loc, _dict):
    target = frame.GetThread().GetProcess().GetTarget()
    pc_va = _module_va(target, frame.GetPC())
    if pc_va == ENTRY:
        _entry(frame)
    elif pc_va == ADD_RESIDUAL:
        _add_residual(frame)
    elif pc_va == SOLVE_PRE:
        _site_snapshot(frame, "solve_pre_20d611", "solve_pre_hits")
    elif pc_va == SOLVE_POST:
        _site_snapshot(frame, "solve_post_20d616", "solve_post_hits")
    elif pc_va == FIRST_TRIPLE_POST:
        _site_snapshot(frame, "first_triple_post_20d6b6", "first_triple_post_hits")
    elif pc_va == SECOND_TRIPLE_POST:
        _site_snapshot(frame, "second_triple_post_20d737", "second_triple_post_hits")
    elif pc_va == RETURN:
        _return(frame)
    else:
        _state()["errors"].append({"error": "unexpected breakpoint", "pc_va": pc_va})
    return False


def install_breakpoints(debugger, include_add_residual=True):
    state = _state()
    target = debugger.GetSelectedTarget()
    sites = [
        (ENTRY, "entry_20ca14"),
        (SOLVE_PRE, "solve_pre_20d611"),
        (SOLVE_POST, "solve_post_20d616"),
        (FIRST_TRIPLE_POST, "first_triple_post_20d6b6"),
        (SECOND_TRIPLE_POST, "second_triple_post_20d737"),
        (RETURN, "return_20d8ac"),
    ]
    if include_add_residual:
        sites.insert(1, (ADD_RESIDUAL, "add_residual_20d560"))
    for site, name in sites:
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
        bp.SetScriptCallbackFunction("prefusion_20ca00_solve_output_probe.hit")
        state["breakpoint_ids"][name] = bp.GetID()
    state["include_add_residual"] = include_add_residual
    print("L16_PREFUSION_20CA00_SOLVE_OUTPUT_INSTALLED", json.dumps(state["breakpoint_ids"], sort_keys=True))


def payload():
    state = dict(_state())
    active = state.pop("_active", {})
    state.pop("_next_frame_id", None)
    state["incomplete_frames"] = list(active.values())
    return state


def report_to_file(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload(), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("WROTE", path)
