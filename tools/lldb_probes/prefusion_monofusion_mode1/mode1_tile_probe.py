"""Capture one complete MonoFusion mode-1 call at entry and return."""

import builtins
import hashlib
import json
import struct
from pathlib import Path


def reset(label, run_dir):
    builtins.l16_monofusion_mode1 = {
        "label": label,
        "run_dir": str(run_dir),
        "captured": False,
        "pending_thread": None,
        "patch_captured": False,
        "entry": None,
        "patch": None,
        "gate": None,
        "edge_pending_thread": None,
        "edge_requirement": "any",
        "edge_partial_id": None,
        "edge_ready_id": None,
        "edge_suspended_threads": [],
        "edge": None,
        "invalid_pending_thread": None,
        "invalid_entry_id": None,
        "invalid_ready_id": None,
        "invalid_suspended_threads": [],
        "invalid": None,
        "combine": None,
        "return": None,
        "files": {},
        "errors": [],
    }


def _state():
    return builtins.l16_monofusion_mode1


def _reg(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    if not address or size < 0:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    raw = process.ReadMemory(address, size, error)
    if not error.Success() or len(raw) != size:
        _state()["errors"].append(
            f"read 0x{address:x}+0x{size:x}: {error.GetCString()}"
        )
        return None
    return raw


def _u64(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<Q", raw)[0] if raw else 0


def _descriptor(process, address):
    raw = _read(process, address, 0x30)
    if raw is None:
        return {"address": address, "read_ok": False}
    words = struct.unpack("<8i", raw[:0x20])
    return {
        "address": address,
        "read_ok": True,
        "domain": list(words[:4]),
        "size": list(words[4:6]),
        "stride": words[6],
        "channel_stride": words[7],
        "data": struct.unpack_from("<Q", raw, 0x20)[0],
        "owner": struct.unpack_from("<Q", raw, 0x28)[0],
        "raw_hex": raw.hex(),
    }


def _vector(process, address):
    raw = _read(process, address, 24)
    if raw is None:
        return {"address": address, "read_ok": False}
    begin, end, capacity = struct.unpack("<QQQ", raw)
    valid = begin <= end <= capacity and (end - begin) % 0x30 == 0
    count = (end - begin) // 0x30 if valid else None
    records = []
    if count is not None and count <= 8:
        for index in range(count):
            records.append(_descriptor(process, begin + index * 0x30))
    return {
        "address": address,
        "read_ok": True,
        "begin": begin,
        "end": end,
        "capacity": capacity,
        "count": count,
        "records": records,
    }


def _dump(process, name, address, size):
    raw = _read(process, address, size)
    if raw is None:
        return None
    path = Path(_state()["run_dir"]) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    item = {
        "path": str(path),
        "address": address,
        "size": size,
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    _state()["files"][name] = item
    return item


def _dump_f32_descriptor(process, name, desc, full_domain=False):
    if not desc.get("read_ok") or not desc.get("data"):
        return None
    width = desc["domain"][2] - desc["domain"][0] if full_domain else desc["size"][0]
    height = desc["domain"][3] - desc["domain"][1] if full_domain else desc["size"][1]
    size = max(0, height) * max(0, desc["stride"]) * 4
    address = desc["data"]
    if full_domain:
        address += (desc["domain"][1] * desc["stride"] + desc["domain"][0]) * 4
    item = _dump(process, name, address, size)
    if item is not None:
        item.update({"logical_width": width, "logical_height": height})
    return item


def _dump_f32_packed(process, name, desc):
    if not desc.get("read_ok") or not desc.get("data"):
        return None
    width, height = desc["size"]
    rows = []
    for y in range(height):
        row = _read(process, desc["data"] + y * desc["stride"] * 4, width * 4)
        if row is None:
            return None
        rows.append(row)
    raw = b"".join(rows)
    path = Path(_state()["run_dir"]) / name
    path.write_bytes(raw)
    item = {
        "path": str(path),
        "address": desc["data"],
        "size": len(raw),
        "logical_width": width,
        "logical_height": height,
        "sha256": hashlib.sha256(raw).hexdigest(),
    }
    _state()["files"][name] = item
    return item


def mode1_entry(frame, bp_loc, internal_dict):
    state = _state()
    if state["captured"]:
        return False
    process = frame.GetThread().GetProcess()
    rsp = _reg(frame, "rsp")
    output = _descriptor(process, _reg(frame, "rdi"))
    operand = _descriptor(process, _reg(frame, "rsi"))
    scalar_map = _descriptor(process, _reg(frame, "rdx"))
    destination_view = _descriptor(process, _reg(frame, "rcx"))
    sources = _vector(process, _reg(frame, "r8"))
    flows = _vector(process, _reg(frame, "r9"))
    # The breakpoint is at the callee entry, after CALL pushed its return address.
    roi_ptr = _u64(process, rsp + 8)
    params_ptr = _u64(process, rsp + 16)
    roi_raw = _read(process, roi_ptr, 16)

    state["captured"] = True
    state["pending_thread"] = frame.GetThread().GetThreadID()
    state["entry"] = {
        "thread": state["pending_thread"],
        "output": output,
        "operand_rsi": operand,
        "scalar_map": scalar_map,
        "destination_view": destination_view,
        "sources": sources,
        "flows": flows,
        "roi_ptr": roi_ptr,
        "roi": list(struct.unpack("<4i", roi_raw)) if roi_raw else None,
        "params_ptr": params_ptr,
    }

    _dump_f32_descriptor(process, "output_pre.f32", output)
    _dump_f32_descriptor(process, "scalar_map.f32", scalar_map)
    _dump_f32_descriptor(process, "reference_full.f32", destination_view, True)
    if sources.get("records"):
        _dump_f32_descriptor(process, "source0_full.f32", sources["records"][0], True)
    if flows.get("records"):
        flow = flows["records"][0]
        flow_size = flow["size"][1] * flow["stride"] * 4
        _dump(process, "flow0.i16x2", flow["data"], flow_size)
    _dump(process, "parameters.bin", params_ptr, 0x60)
    return False


def mode1_return(frame, bp_loc, internal_dict):
    state = _state()
    if frame.GetThread().GetThreadID() != state.get("pending_thread"):
        return False
    process = frame.GetThread().GetProcess()
    output = state["entry"]["output"]
    _dump_f32_descriptor(process, "output_post.f32", output)
    rbp = _reg(frame, "rbp")
    state["return"] = {
        "thread": frame.GetThread().GetThreadID(),
        "pc": frame.GetPC(),
        "rbp": rbp,
        "confidence_sum": struct.unpack(
            "<2f", _read(process, rbp - 0x1CB8, 8)
        ),
    }
    return True


def patch_pre_wiener(frame, bp_loc, internal_dict):
    state = _state()
    if (
        frame.GetThread().GetThreadID() != state.get("pending_thread")
        or state["patch_captured"]
    ):
        return False
    process = frame.GetThread().GetProcess()
    rbp = _reg(frame, "rbp")
    state["patch_captured"] = True
    bp_loc.SetEnabled(False)
    state["patch"] = {"rbp": rbp}
    source_original = _descriptor(process, rbp - 0x1CF0)
    state["patch"]["source_original"] = source_original
    _dump_f32_packed(process, "patch_source_original.f32", source_original)
    for name, offset in (
        ("patch_target_spatial.f32", -0x8B0),
        ("patch_target_coeff.f32", -0xCB0),
        ("patch_source_raw.f32", -0x10B0),
        ("patch_residual_raw.f32", -0x1CB0),
    ):
        _dump(process, name, rbp + offset, 16 * 16 * 4)
    return False


def residual_gate(frame, bp_loc, internal_dict):
    state = _state()
    if frame.GetThread().GetThreadID() != state.get("pending_thread"):
        return False
    if state["gate"] is not None:
        return False
    confidence_raw = _read(frame.GetThread().GetProcess(), _reg(frame, "rbp") - 0x1EF4, 4)
    gate_raw = frame.FindRegister("xmm1").GetData()
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    gate_bytes = gate_raw.ReadRawData(error, 0, 4)
    state["gate"] = {
        "confidence": struct.unpack("<f", confidence_raw)[0],
        "residual_scale": struct.unpack("<f", gate_bytes)[0],
    }
    bp_loc.SetEnabled(False)
    return False


def residual_gate_only(frame, bp_loc, internal_dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    confidence_raw = _read(process, _reg(frame, "rbp") - 0x1EF4, 4)
    gate_raw = frame.FindRegister("xmm1").GetData()
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    gate_bytes = gate_raw.ReadRawData(error, 0, 4)
    state["gate"] = {
        "thread": frame.GetThread().GetThreadID(),
        "confidence": struct.unpack("<f", confidence_raw)[0],
        "residual_scale": struct.unpack("<f", gate_bytes)[0],
    }
    return True


def edge_partial_entry(frame, bp_loc, internal_dict):
    state = _state()
    if state["edge_pending_thread"] is not None:
        return False
    process = frame.GetThread().GetProcess()
    rbp = _reg(frame, "rbp")
    source = _descriptor(process, rbp - 0x1CF0)
    lowpass = _descriptor(process, rbp - 0x1D40)
    requirement = state.get("edge_requirement", "any")
    if requirement == "horizontal" and source.get("size", [16, 16])[0] >= 16:
        return False
    if requirement == "vertical" and source.get("size", [16, 16])[1] >= 16:
        return False
    state["edge_pending_thread"] = frame.GetThread().GetThreadID()
    state["edge"] = {
        "entry_pc": frame.GetPC(),
        "rbp": rbp,
        "source_at_entry": source,
        "lowpass_at_entry": lowpass,
    }
    _dump_f32_packed(process, "edge_source_partial.f32", source)
    _dump_f32_packed(process, "edge_lowpass_partial.f32", lowpass)
    return True


def edge_partial_ready(frame, bp_loc, internal_dict):
    state = _state()
    if frame.GetThread().GetThreadID() != state.get("edge_pending_thread"):
        return False
    process = frame.GetThread().GetProcess()
    rbp = _reg(frame, "rbp")
    state["edge"].update({"ready_pc": frame.GetPC()})
    for name, offset in (
        ("edge_target_spatial.f32", -0x8B0),
        ("edge_lowpass_block.f32", -0x10B0),
        ("edge_residual_block.f32", -0x1CB0),
    ):
        _dump(process, name, rbp + offset, 16 * 16 * 4)
    return True


def patch_post_wiener(frame, bp_loc, internal_dict):
    state = _state()
    if frame.GetThread().GetThreadID() != state.get("pending_thread"):
        return False
    if state.get("patch", {}).get("post_wiener"):
        return False
    process = frame.GetThread().GetProcess()
    rbp = _reg(frame, "rbp")
    confidence_raw = _read(process, rbp - 0x1EF4, 4)
    state["patch"]["post_wiener"] = True
    bp_loc.SetEnabled(False)
    state["patch"]["confidence"] = (
        struct.unpack("<f", confidence_raw)[0] if confidence_raw else None
    )
    _dump(process, "patch_source_filtered.f32", rbp - 0x10B0, 16 * 16 * 4)
    return False


def pre_combine(frame, bp_loc, internal_dict):
    state = _state()
    if frame.GetThread().GetThreadID() != state.get("pending_thread"):
        return False
    if state["combine"] is not None:
        return False
    process = frame.GetThread().GetProcess()
    rbp = _reg(frame, "rbp")
    filtered = _descriptor(process, rbp - 0x1E30)
    residual = _descriptor(process, rbp - 0x1E70)
    state["combine"] = {"filtered": filtered, "residual": residual}
    _dump_f32_descriptor(process, "filtered_overlap.f32", filtered)
    _dump_f32_descriptor(process, "residual_overlap.f32", residual)
    return False


def install(debugger, entry_id, pre_id, post_id, gate_id, combine_id, return_id):
    target = debugger.GetSelectedTarget()
    callbacks = {
        entry_id: "mode1_tile_probe.mode1_entry",
        pre_id: "mode1_tile_probe.patch_pre_wiener",
        post_id: "mode1_tile_probe.patch_post_wiener",
        gate_id: "mode1_tile_probe.residual_gate",
        combine_id: "mode1_tile_probe.pre_combine",
        return_id: "mode1_tile_probe.mode1_return",
    }
    for bp_id, callback in callbacks.items():
        target.FindBreakpointByID(bp_id).SetScriptCallbackFunction(callback)


def install_gate_only(debugger, gate_id):
    debugger.GetSelectedTarget().FindBreakpointByID(gate_id).SetScriptCallbackFunction(
        "mode1_tile_probe.residual_gate_only"
    )


def install_tile(debugger, entry_id, combine_id, return_id):
    target = debugger.GetSelectedTarget()
    callbacks = {
        entry_id: "mode1_tile_probe.mode1_entry",
        combine_id: "mode1_tile_probe.pre_combine",
        return_id: "mode1_tile_probe.mode1_return",
    }
    for bp_id, callback in callbacks.items():
        target.FindBreakpointByID(bp_id).SetScriptCallbackFunction(callback)


def install_edge(debugger, partial_id, ready_id):
    target = debugger.GetSelectedTarget()
    _state()["edge_partial_id"] = partial_id
    _state()["edge_ready_id"] = ready_id
    target.FindBreakpointByID(partial_id).SetScriptCallbackFunction(
        "mode1_tile_probe.edge_partial_entry"
    )
    target.FindBreakpointByID(ready_id).SetScriptCallbackFunction(
        "mode1_tile_probe.edge_partial_ready"
    )
    target.FindBreakpointByID(ready_id).SetEnabled(False)


def require_edge_axis(axis):
    if axis not in ("any", "horizontal", "vertical"):
        raise ValueError(f"invalid edge axis: {axis}")
    _state()["edge_requirement"] = axis


def prepare_edge_resume(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    pending = state.get("edge_pending_thread")
    if pending is None:
        raise RuntimeError("partial-source arm did not stop")
    target.FindBreakpointByID(state["edge_partial_id"]).SetEnabled(False)
    ready = target.FindBreakpointByID(state["edge_ready_id"])
    ready.SetThreadID(pending)
    ready.SetEnabled(True)
    suspended = []
    for index in range(process.GetNumThreads()):
        thread = process.GetThreadAtIndex(index)
        if thread.GetThreadID() != pending and thread.Suspend():
            suspended.append(thread.GetThreadID())
    state["edge_suspended_threads"] = suspended


def continue_until_edge(debugger, max_stops=4096):
    process = debugger.GetSelectedTarget().GetProcess()
    for _ in range(max_stops):
        if _state().get("edge_pending_thread") is not None:
            return
        error = process.Continue()
        if not error.Success():
            raise RuntimeError(error.GetCString())
    raise RuntimeError(f"edge requirement not met after {max_stops} stops")


def _xmm_f32(frame, name):
    data = frame.FindRegister(name).GetData()
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    raw = data.ReadRawData(error, 0, 4)
    if not error.Success():
        raise RuntimeError(error.GetCString())
    return struct.unpack("<f", raw)[0]


def invalid_overlap_entry(frame, bp_loc, internal_dict):
    state = _state()
    if state["invalid_pending_thread"] is not None:
        return False
    state["invalid_pending_thread"] = frame.GetThread().GetThreadID()
    process = frame.GetThread().GetProcess()
    rbp = _reg(frame, "rbp")
    state["invalid"] = {
        "entry_pc": frame.GetPC(),
        "rbp": rbp,
        "x_before": _xmm_f32(frame, "xmm2"),
        "y_before": _xmm_f32(frame, "xmm3"),
    }
    for name, offset in (
        ("invalid_target.f32", -0x8B0),
        ("invalid_filtered_pre.f32", -0x14B0),
        ("invalid_residual_pre.f32", -0x18B0),
    ):
        _dump(process, name, rbp + offset, 16 * 16 * 4)
    return True


def invalid_overlap_ready(frame, bp_loc, internal_dict):
    state = _state()
    if frame.GetThread().GetThreadID() != state.get("invalid_pending_thread"):
        return False
    process = frame.GetThread().GetProcess()
    rbp = _reg(frame, "rbp")
    state["invalid"].update(
        {
            "ready_pc": frame.GetPC(),
            "x_after": _xmm_f32(frame, "xmm2"),
            "y_after": _xmm_f32(frame, "xmm3"),
        }
    )
    for name, offset in (
        ("invalid_filtered_post.f32", -0x14B0),
        ("invalid_residual_post.f32", -0x18B0),
    ):
        _dump(process, name, rbp + offset, 16 * 16 * 4)
    return True


def install_invalid(debugger, entry_id, ready_id):
    target = debugger.GetSelectedTarget()
    state = _state()
    state["invalid_entry_id"] = entry_id
    state["invalid_ready_id"] = ready_id
    target.FindBreakpointByID(entry_id).SetScriptCallbackFunction(
        "mode1_tile_probe.invalid_overlap_entry"
    )
    target.FindBreakpointByID(ready_id).SetScriptCallbackFunction(
        "mode1_tile_probe.invalid_overlap_ready"
    )
    target.FindBreakpointByID(ready_id).SetEnabled(False)


def prepare_invalid_resume(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    pending = state.get("invalid_pending_thread")
    if pending is None:
        raise RuntimeError("invalid-overlap arm did not stop")
    target.FindBreakpointByID(state["invalid_entry_id"]).SetEnabled(False)
    ready = target.FindBreakpointByID(state["invalid_ready_id"])
    ready.SetThreadID(pending)
    ready.SetEnabled(True)
    suspended = []
    for index in range(process.GetNumThreads()):
        thread = process.GetThreadAtIndex(index)
        if thread.GetThreadID() != pending and thread.Suspend():
            suspended.append(thread.GetThreadID())
    state["invalid_suspended_threads"] = suspended


def report(path):
    state = dict(_state())
    state.pop("run_dir", None)
    Path(path).write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    print(json.dumps(state, indent=2, sort_keys=True))
