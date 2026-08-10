"""Trace completed tiles inserted into FusionCacheBayer backing storage."""

import builtins
import json
import os
import struct


CTOR_POST_BASE = 0x4064ED
TILE_COMPLETE = 0x3D00F0
CONSUMER = 0x406A10
FINAL_GUIDE_CALL = 0x407458


def reset(label="", report_path="", cap=24):
    builtins.l16_cnr_storage_writer = {
        "label": label,
        "report_path": report_path,
        "cap": cap,
        "owners": {},
        "complete_counts": {"float": 0, "byte": 0},
        "complete_events": [],
        "consumer_events": [],
        "final_hits": 0,
        "errors": [],
    }


def _s():
    if not hasattr(builtins, "l16_cnr_storage_writer"):
        reset()
    return builtins.l16_cnr_storage_writer


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    if not address or address < 0x1000 or address > 0x00007FFFFFFFFFFF:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    try:
        data = process.ReadMemory(address, size, error)
    except Exception:
        return None
    return data if error.Success() and data is not None and len(data) == size else None


def _qword(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<Q", raw)[0] if raw is not None else 0


def _base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                return base
    return None


def _stack(frame, count=24):
    thread = frame.GetThread()
    target = thread.GetProcess().GetTarget()
    base = _base(target)
    out = []
    for index in range(min(count, thread.GetNumFrames())):
        item = thread.GetFrameAtIndex(index)
        pc = item.GetPC()
        out.append({
            "i": index,
            "pc": pc,
            "libcp_va": pc - base if base is not None and base <= pc < base + 0x700000 else None,
            "fn": item.GetFunctionName(),
        })
    return out


def _pointer_graph(process, tile, raw):
    out = []
    for offset in range(0, min(len(raw), 0x100), 8):
        value = struct.unpack_from("<Q", raw, offset)[0]
        if value in (tile, 0) or value < 0x1000 or value > 0x00007FFFFFFFFFFF:
            continue
        sample = _read(process, value, 64)
        if sample is not None:
            out.append({"offset": offset, "ptr": value, "sample_hex": sample.hex()})
    return out


def constructor_post_base(frame, _bp_loc, _dict):
    state = _s()
    process = frame.GetThread().GetProcess()
    owner = _u(frame, "r13")
    if not owner:
        return False
    state["owners"][str(owner)] = {
        "owner": owner,
        "float_storage": _qword(process, owner + 0x100),
        "byte_storage": _qword(process, owner + 0xF0),
        "selected_hits": 0,
    }
    return False


def _storage_owner(storage):
    for item in _s()["owners"].values():
        if storage == item.get("byte_storage"):
            return item, "byte"
        if storage == item.get("float_storage"):
            return item, "float"
    return None, None


def tile_complete(frame, _bp_loc, _dict):
    state = _s()
    process = frame.GetThread().GetProcess()
    tile = _u(frame, "rdi")
    storage = _qword(process, tile + 0x38)
    owner, role = _storage_owner(storage)
    if role is None:
        return False
    state["complete_counts"][role] += 1
    if len(state["complete_events"]) >= int(state["cap"]):
        return False
    raw = _read(process, tile, 0x100)
    event = {
        "role": role,
        "owner": owner["owner"],
        "owner_selected_hits": owner["selected_hits"],
        "storage": storage,
        "tile": tile,
        "completion_mode": _u(frame, "rsi") & 0xFFFFFFFF,
        "stack": _stack(frame),
    }
    if raw is not None:
        event["tile_raw_hex"] = raw.hex()
        event["pointer_graph"] = _pointer_graph(process, tile, raw)
    state["complete_events"].append(event)
    return False


def consumer(frame, _bp_loc, _dict):
    state = _s()
    process = frame.GetThread().GetProcess()
    owner_address = _u(frame, "rdi")
    owner = state["owners"].get(str(owner_address))
    if owner is None:
        owner = {
            "owner": owner_address,
            "float_storage": _qword(process, owner_address + 0x100),
            "byte_storage": _qword(process, owner_address + 0xF0),
            "selected_hits": 0,
        }
        state["owners"][str(owner_address)] = owner
    owner["selected_hits"] += 1
    if len(state["consumer_events"]) < 8:
        state["consumer_events"].append({
            "owner": owner_address,
            "float_storage": owner["float_storage"],
            "byte_storage": owner["byte_storage"],
            "stack": _stack(frame, 12),
        })
    return False


def final_guide_call(frame, _bp_loc, _dict):
    state = _s()
    state["final_hits"] += 1
    selected_owners = {
        int(key) for key, value in state["owners"].items() if value["selected_hits"]
    }
    selected_completions = sum(
        1 for event in state["complete_events"] if event["owner"] in selected_owners
    )
    if state["final_hits"] >= 4 and selected_completions:
        frame.GetThread().GetProcess().Kill()
    return False


def install(debugger):
    target = debugger.GetSelectedTarget()
    callbacks = (
        (CTOR_POST_BASE, "constructor_post_base"),
        (TILE_COMPLETE, "tile_complete"),
        (CONSUMER, "consumer"),
        (FINAL_GUIDE_CALL, "final_guide_call"),
    )
    ids = {}
    for address, callback in callbacks:
        before = target.GetNumBreakpoints()
        debugger.HandleCommand(
            f"breakpoint set --shlib libcp.dylib --address 0x{address:x}"
        )
        if target.GetNumBreakpoints() <= before:
            _s()["errors"].append(f"failed breakpoint 0x{address:x}")
            continue
        bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
        bp.SetScriptCallbackFunction(f"storage_writer_probe.{callback}")
        ids[callback] = bp.GetID()
    print("CNR_STORAGE_WRITER_INSTALLED", ids)


def write_report(_debugger, path=""):
    out = path or _s().get("report_path")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(dict(_s()), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("CNR_STORAGE_WRITER_WROTE", out)
