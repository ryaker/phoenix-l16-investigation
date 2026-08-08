"""Capture one top-left MonoFusion mode-0 scalar tile and all replay inputs."""

import builtins
import hashlib
import json
import struct
from pathlib import Path


def reset(label, run_dir):
    builtins.l16_monofusion_mode0_tile = {
        "label": label,
        "run_dir": str(run_dir),
        "entry": None,
        "return": None,
        "combine": None,
        "patch": None,
        "files": {},
        "errors": [],
        "_thread": None,
    }


def _state():
    return builtins.l16_monofusion_mode0_tile


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
    words = struct.unpack_from("<8i", raw)
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
        records = [_descriptor(process, begin + i * 0x30) for i in range(count)]
    return {
        "address": address,
        "read_ok": True,
        "begin": begin,
        "end": end,
        "capacity": capacity,
        "count": count,
        "records": records,
    }


def _dump(process, name, address, size, **metadata):
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
    item.update(metadata)
    _state()["files"][name] = item
    return item


def _dump_packed_f32(process, name, desc):
    width, height = desc["size"]
    rows = []
    for y in range(height):
        row = _read(process, desc["data"] + 4 * y * desc["stride"], 4 * width)
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


def install_callbacks(
    debugger, entry_id, auxiliary_mean_id, patch_pre_id, patch_wiener_id,
    patch_inverse_id, combine_id, return_id
):
    target = debugger.GetSelectedTarget()
    callbacks = {
        entry_id: "mode0_tile_probe.mode0_entry",
        auxiliary_mean_id: "mode0_tile_probe.mode0_auxiliary_mean",
        patch_pre_id: "mode0_tile_probe.mode0_patch_pre_wiener",
        patch_wiener_id: "mode0_tile_probe.mode0_patch_post_wiener",
        patch_inverse_id: "mode0_tile_probe.mode0_patch_post_inverse",
        combine_id: "mode0_tile_probe.mode0_pre_combine",
        return_id: "mode0_tile_probe.mode0_return",
    }
    for bp_id, callback in callbacks.items():
        bp = target.FindBreakpointByID(bp_id)
        if bp and bp.IsValid():
            bp.SetScriptCallbackFunction(callback)
    # The interior breakpoints (patch-loop and per-tile combine) fire on every
    # worker thread for every 16x16 patch of every tile. Leaving them armed
    # while we wait for the top-left tile costs one Python callback per patch
    # across ~8 threads, which on some captures never finishes. Arm only the
    # reducer entry; mode0_entry re-enables the rest the moment it has latched
    # the tile and thread it wants. Captured data is unchanged -- every
    # re-enabled breakpoint is downstream of the entry we are latching on.
    state = _state()
    state["_deferred_bp_ids"] = [
        auxiliary_mean_id, patch_pre_id, patch_wiener_id, patch_inverse_id,
        combine_id,
    ]
    state["_target"] = target
    for bp_id in state["_deferred_bp_ids"]:
        bp = target.FindBreakpointByID(bp_id)
        if bp and bp.IsValid():
            bp.SetEnabled(False)


def _arm_deferred():
    state = _state()
    target = state.get("_target")
    if target is None:
        return
    for bp_id in state.get("_deferred_bp_ids", []):
        bp = target.FindBreakpointByID(bp_id)
        if bp and bp.IsValid():
            bp.SetThreadID(state["_thread"])
            bp.SetEnabled(True)


def mode0_entry(frame, bp_loc, internal_dict):
    state = _state()
    if state["entry"] is not None:
        return False
    process = frame.GetThread().GetProcess()
    rsp = _reg(frame, "rsp")
    roi_ptr = _u64(process, rsp + 8)
    params_ptr = _u64(process, rsp + 16)
    roi_raw = _read(process, roi_ptr, 16)
    roi = list(struct.unpack("<4i", roi_raw)) if roi_raw else None
    # Which tile to latch. Defaults to the top-left tile (0,0) so existing
    # scripts are unchanged; set L16_MODE0_ROI="x0,y0" to latch a different
    # tile from the entry census. Only the origin is matched -- the reducer
    # picks the extent itself.
    want = state.get("_want_roi")
    if want is None:
        os_mod = builtins.__import__("os")
        parts = os_mod.environ.get("L16_MODE0_ROI", "0,0").split(",")
        want = [int(parts[0]), int(parts[1])]
        state["_want_roi"] = want
    if roi is None or roi[0] != want[0] or roi[1] != want[1]:
        return False

    output = _descriptor(process, _reg(frame, "rdi"))
    secondary_output = _descriptor(process, _reg(frame, "rsi"))
    target = _descriptor(process, _reg(frame, "rdx"))
    auxiliary = _descriptor(process, _reg(frame, "rcx"))
    sources = _vector(process, _reg(frame, "r8"))
    flows = _vector(process, _reg(frame, "r9"))
    if sources.get("count") != 1 or flows.get("count") != 1:
        state["errors"].append("expected one source and one flow")
        return False

    state["_thread"] = frame.GetThread().GetThreadID()
    state["entry"] = {
        "thread": state["_thread"],
        "output": output,
        "secondary_output": secondary_output,
        "target": target,
        "auxiliary": auxiliary,
        "sources": sources,
        "flows": flows,
        "roi": roi,
        "parameters_pointer": params_ptr,
    }
    # Other worker threads can enter the same hot function before this
    # callback returns. Once the requested tile is latched, prevent those
    # concurrent entry stops from making batch LLDB return early.
    bp_loc.SetEnabled(False)
    _arm_deferred()
    _dump_packed_f32(process, "output_pre.f32le", output)
    _dump_packed_f32(process, "secondary_pre.f32le", secondary_output)
    _dump_packed_f32(process, "target_tile.f32le", target)

    # The top-left auxiliary descriptor retains the full-image domain and its
    # data pointer is the full 4160x3120 base. This is the separate image whose
    # patch mean is passed in xmm0 to noise helper 0x18e940.
    full_w = auxiliary["domain"][2] - auxiliary["domain"][0]
    full_h = auxiliary["domain"][3] - auxiliary["domain"][1]
    # Non-top-left tiles keep the full-image auxiliary domain but shift the
    # data pointer to the tile origin; domain[0]/domain[1] go negative by
    # exactly that offset. Back the pointer up to pixel (0,0) so the dump is
    # the whole auxiliary image regardless of which tile was latched.
    aux_base = auxiliary["data"] - 4 * (
        (-auxiliary["domain"][1]) * auxiliary["stride"] - auxiliary["domain"][0]
    )
    _dump(
        process, "auxiliary_full.f32le", aux_base,
        full_h * auxiliary["stride"] * 4,
        logical_width=full_w, logical_height=full_h,
        stride=auxiliary["stride"], element="f32",
    )

    source = sources["records"][0]
    _dump(
        process, "source0_full.f32le", source["data"],
        source["size"][1] * source["stride"] * 4,
        logical_width=source["size"][0], logical_height=source["size"][1],
        stride=source["stride"], element="f32",
    )
    flow = flows["records"][0]
    _dump(
        process, "flow0_full.i16x2le", flow["data"],
        flow["size"][1] * flow["stride"] * 4,
        logical_width=flow["size"][0], logical_height=flow["size"][1],
        stride=flow["stride"], element="i16x2",
    )
    _dump(process, "parameters.bin", params_ptr, 0x60)
    return False


def mode0_auxiliary_mean(frame, bp_loc, internal_dict):
    state = _state()
    if frame.GetThread().GetThreadID() != state.get("_thread"):
        return False
    if state.get("patch") is not None:
        bp_loc.SetEnabled(False)
        return False
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    raw = frame.FindRegister("xmm0").GetData().ReadRawData(error, 0, 4)
    if error.Success() and len(raw) == 4:
        state["_pending_auxiliary_mean"] = struct.unpack("<f", raw)[0]
        state["_auxiliary_mean_location"] = bp_loc
    return False


def mode0_patch_pre_wiener(frame, bp_loc, internal_dict):
    state = _state()
    if frame.GetThread().GetThreadID() != state.get("_thread"):
        return False
    if state.get("patch") is not None:
        return False
    process = frame.GetThread().GetProcess()
    rbp = _reg(frame, "rbp")
    source_view = _descriptor(process, rbp - 0x1640)
    want = state.get("_want_patch")
    if want is None:
        os_mod = builtins.__import__("os")
        raw_want = os_mod.environ.get("L16_MODE0_PATCH")
        want = [int(value) for value in raw_want.split(",")] if raw_want else []
        state["_want_patch"] = want
    if want:
        x0, y0 = want
        flow = state["entry"]["flows"]["records"][0]
        flow_x = min(max(int(x0 / 8), 0), flow["size"][0] - 1)
        flow_y = min(max(int(y0 / 8), 0), flow["size"][1] - 1)
        raw_flow = _read(
            process,
            flow["data"] + 4 * (flow_y * flow["stride"] + flow_x),
            4,
        )
        if raw_flow is None:
            return False
        dx, dy = struct.unpack("<2h", raw_flow)
        expected_domain = [x0 + dx, y0 + dy, x0 + dx + 16, y0 + dy + 16]
        if source_view.get("domain") != expected_domain:
            return False
    variance_raw = _read(process, rbp - 0x16D4, 4)
    if variance_raw is None:
        state["errors"].append("patch_pre_wiener: variance read failed")
        return False
    state["patch"] = {
        "rbp": rbp,
        "target_origin": want or [-8, -8],
        "source_view": source_view,
        "auxiliary_mean": state.get("_pending_auxiliary_mean"),
        "variance": struct.unpack("<f", variance_raw)[0],
    }
    for name, offset in (
        ("patch_target_spatial.f32le", -0x8B0),
        ("patch_target_coeff.f32le", -0xCB0),
        ("patch_source_coeff_pre.f32le", -0x10B0),
    ):
        _dump(process, name, rbp + offset, 16 * 16 * 4)
    aux_location = state.get("_auxiliary_mean_location")
    if aux_location is not None:
        aux_location.SetEnabled(False)
    bp_loc.SetEnabled(False)
    return False


def mode0_patch_post_wiener(frame, bp_loc, internal_dict):
    state = _state()
    if frame.GetThread().GetThreadID() != state.get("_thread"):
        return False
    if state.get("patch") is None or state["patch"].get("post_wiener"):
        return False
    process = frame.GetThread().GetProcess()
    rbp = _reg(frame, "rbp")
    confidence_raw = _read(process, rbp - 0x1644, 4)
    if confidence_raw is None:
        state["errors"].append("patch_post_wiener: confidence read failed")
        return False
    state["patch"]["post_wiener"] = True
    state["patch"]["confidence"] = struct.unpack("<f", confidence_raw)[0]
    _dump(process, "patch_source_coeff_post.f32le", rbp - 0x10B0, 16 * 16 * 4)
    bp_loc.SetEnabled(False)
    return False


def mode0_patch_post_inverse(frame, bp_loc, internal_dict):
    state = _state()
    if frame.GetThread().GetThreadID() != state.get("_thread"):
        return False
    if state.get("patch") is None or state["patch"].get("post_inverse"):
        return False
    process = frame.GetThread().GetProcess()
    rbp = _reg(frame, "rbp")
    state["patch"]["post_inverse"] = True
    _dump(process, "patch_source_spatial_post.f32le", rbp - 0x10B0, 16 * 16 * 4)
    bp_loc.SetEnabled(False)
    return False


def mode0_pre_combine(frame, bp_loc, internal_dict):
    state = _state()
    if frame.GetThread().GetThreadID() != state.get("_thread"):
        return False
    if state.get("combine") is not None:
        return False
    process = frame.GetThread().GetProcess()
    rbp = _reg(frame, "rbp")
    overlap = _descriptor(process, rbp - 0x1580)
    state["combine"] = {"pc": frame.GetPC(), "overlap": overlap}
    _dump_packed_f32(process, "overlap_precombine.f32le", overlap)
    # 0x18ce90 receives these two 16-float arrays as its separable horizontal
    # and vertical overlap weights for every patch in this tile.
    _dump(process, "overlap_weight_x.f32le", rbp - 0xB0, 16 * 4)
    _dump(process, "overlap_weight_y.f32le", rbp - 0x70, 16 * 4)
    return False


def mode0_return(frame, bp_loc, internal_dict):
    state = _state()
    if frame.GetThread().GetThreadID() != state.get("_thread"):
        return False
    process = frame.GetThread().GetProcess()
    _dump_packed_f32(process, "output_post.f32le", state["entry"]["output"])
    _dump_packed_f32(
        process, "secondary_post.f32le", state["entry"]["secondary_output"]
    )
    state["return"] = {"thread": state["_thread"], "pc": frame.GetPC()}
    error = process.Kill()
    if error.Fail():
        state["errors"].append(f"kill: {error.GetCString()}")
    return False


def report_to_file(path):
    state = _state()
    if state["entry"] is None or state["return"] is None:
        print("MONOFUSION_MODE0_TILE_REPORT_REFUSED incomplete capture")
        return
    report = {key: value for key, value in state.items() if not key.startswith("_")}
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("MONOFUSION_MODE0_TILE_REPORT " + path)
