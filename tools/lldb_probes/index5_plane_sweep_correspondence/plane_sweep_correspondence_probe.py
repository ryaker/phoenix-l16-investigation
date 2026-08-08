import builtins
import hashlib
import json
import os
import struct


PROJECTION_VECTOR_AFTER = 0x276A01
INDEX_TO_DEPTH = 0x267010

SITES = {
    PROJECTION_VECTOR_AFTER: "projection_vector_after_276a01",
    INDEX_TO_DEPTH: "index_to_depth_267010",
}

SAMPLE_PIXELS = ((1040, 780), (520, 390), (1560, 1170))


def reset(label="", output_dir="", expected_lookup_count=752):
    builtins.l16_plane_sweep_correspondence = {
        "label": label,
        "output_dir": output_dir,
        "expected_lookup_count": expected_lookup_count,
        "counts": {name: 0 for name in SITES.values()},
        "projection_packet": None,
        "index_map": None,
        "errors": [],
        "capture_complete": False,
        "breakpoint_ids": {},
    }


def _state():
    if not hasattr(builtins, "l16_plane_sweep_correspondence"):
        reset()
    return builtins.l16_plane_sweep_correspondence


def _read(process, address, size):
    if not address or size <= 0:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    raw = process.ReadMemory(address, size, error)
    if not error.Success() or len(raw) != size:
        return None
    return raw


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _u64(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<Q", raw)[0] if raw is not None else None


def _module_base(target):
    state = _state()
    cached = state.get("_libcp_base")
    if cached is not None:
        return cached
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                state["_libcp_base"] = base
                return base
    return None


def _module_va(target, pc):
    base = _module_base(target)
    return pc - base if base is not None and pc >= base else None


def _descriptor(process, address):
    raw = _read(process, address, 0x30)
    if raw is None:
        return None
    return {
        "address": address,
        "origin": list(struct.unpack_from("<2i", raw, 0x00)),
        "bounds": list(struct.unpack_from("<2i", raw, 0x08)),
        "size": list(struct.unpack_from("<2i", raw, 0x10)),
        "stride": struct.unpack_from("<i", raw, 0x18)[0],
        "data": struct.unpack_from("<Q", raw, 0x20)[0],
        "allocation": struct.unpack_from("<Q", raw, 0x28)[0],
        "raw_hex": raw.hex(),
    }


def _vector_f32(process, address):
    raw = _read(process, address, 0x18)
    if raw is None:
        return None
    begin, end, cap = struct.unpack("<3Q", raw)
    byte_size = end - begin if end >= begin else -1
    if byte_size < 0 or byte_size % 4 or byte_size > 1 << 20:
        return {
            "address": address,
            "begin": begin,
            "end": end,
            "cap": cap,
            "byte_size": byte_size,
            "error": "invalid vector bounds",
        }
    payload = _read(process, begin, byte_size)
    if payload is None:
        return {
            "address": address,
            "begin": begin,
            "end": end,
            "cap": cap,
            "byte_size": byte_size,
            "error": "payload read failed",
        }
    return {
        "address": address,
        "begin": begin,
        "end": end,
        "cap": cap,
        "byte_size": byte_size,
        "count": byte_size // 4,
        "raw_hex": payload.hex(),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "first": list(struct.unpack("<%df" % min(8, byte_size // 4), payload[:32])),
        "last": list(struct.unpack("<%df" % min(8, byte_size // 4), payload[-32:])),
    }


def _record_a8(process, address):
    raw = _read(process, address, 0xA8)
    if raw is None:
        return None
    return {
        "address": address,
        "raw_hex": raw.hex(),
        "k_0x00": list(struct.unpack_from("<9f", raw, 0x00)),
        "translation_0x24": list(struct.unpack_from("<3f", raw, 0x24)),
        "rotation_0x30": list(struct.unpack_from("<9f", raw, 0x30)),
        "adjustment_0x54": list(struct.unpack_from("<4f", raw, 0x54)),
    }


def _record_50(process, address):
    raw = _read(process, address, 0x50)
    if raw is None:
        return None
    return {
        "address": address,
        "raw_hex": raw.hex(),
        "matrix_0x00": list(struct.unpack_from("<16f", raw, 0x00)),
        "map_0x40": struct.unpack_from("<Q", raw, 0x40)[0],
        "scale_0x48": list(struct.unpack_from("<2f", raw, 0x48)),
    }


def _projection_packet(process, frame):
    # Selected mode-8 runPass keeps StereoLayer in r12 and passes the local
    # projection-vector destination as rbp-0x138 to 0x26a790.
    layer = _u(frame, "r12")
    index_raw = _read(process, layer + 0x8, 8)
    if index_raw is None:
        return None
    index, mode = struct.unpack("<2I", index_raw)
    if index != 5 or mode != 8:
        return None

    rbp = _u(frame, "rbp")
    vector_raw = _read(process, rbp - 0x138, 0x18)
    if vector_raw is None:
        return None
    begin, end, cap = struct.unpack("<3Q", vector_raw)
    if end < begin or end - begin != 4 * 0x50:
        return None

    images_raw = _read(process, layer + 0x240, 0x18)
    if images_raw is None:
        return None
    image_begin, image_end, image_cap = struct.unpack("<3Q", images_raw)
    if image_end < image_begin or image_end - image_begin != 5 * 0x10:
        return None
    images = []
    for ordinal in range(5):
        shared_raw = _read(process, image_begin + ordinal * 0x10, 0x10)
        if shared_raw is None:
            return None
        object_ptr, owner_ptr = struct.unpack("<2Q", shared_raw)
        images.append(
            {
                "ordinal": ordinal,
                "object": object_ptr,
                "owner": owner_ptr,
                "descriptor": _descriptor(process, object_ptr),
            }
        )

    return {
        "layer": layer,
        "index": index,
        "mode": mode,
        "guidance": _descriptor(process, _u64(process, layer + 0x288)),
        "images_vector": {
            "begin": image_begin,
            "end": image_end,
            "cap": image_cap,
            "count": 5,
        },
        "images": images,
        "projection_vector": {
            "begin": begin,
            "end": end,
            "cap": cap,
            "count": 4,
            "records": [
                _record_50(process, begin + ordinal * 0x50)
                for ordinal in range(4)
            ],
        },
    }


def _sample_u16_image(process, descriptor):
    width, height = descriptor["size"]
    stride = descriptor["stride"]
    data = descriptor["data"]
    if width != 2080 or height != 1560 or stride < width or not data:
        return None
    samples = []
    for x, y in SAMPLE_PIXELS:
        raw = _read(process, data + (y * stride + x) * 2, 2)
        if raw is None:
            return None
        samples.append({"u": x, "v": y, "hypothesis_index": struct.unpack("<H", raw)[0]})
    return samples


def hit(frame, bp_loc, internal_dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    site = _module_va(target, frame.GetPC())
    name = SITES.get(site)
    if name is None:
        state["errors"].append("unexpected site %r" % site)
        return False
    state["counts"][name] += 1
    if site == PROJECTION_VECTOR_AFTER and state["projection_packet"] is None:
        packet = _projection_packet(process, frame)
        if packet is not None:
            state["projection_packet"] = packet
            state["capture_complete"] = state["index_map"] is not None
            return state["capture_complete"]
        return False

    if site == INDEX_TO_DEPTH and state["index_map"] is None:
        source = _descriptor(process, _u(frame, "rsi"))
        lookup = _vector_f32(process, _u(frame, "rdx"))
        if not source or source["size"] != [2080, 1560]:
            return False
        if not lookup or lookup.get("count") != state["expected_lookup_count"]:
            return False
        samples = _sample_u16_image(process, source)
        if samples is None:
            state["errors"].append("index-map sample read failed")
            return False
        state["index_map"] = {
            "source_descriptor": source,
            "lookup": lookup,
            "samples": samples,
        }
        state["capture_complete"] = state["projection_packet"] is not None
        if state["capture_complete"]:
            return True
    return False


def attach(debugger):
    state = _state()
    os.makedirs(state["output_dir"], exist_ok=True)
    target = debugger.GetSelectedTarget()
    ids = {}
    for index in range(target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(index)
        if not bp or not bp.IsValid() or bp.GetNumLocations() < 1:
            continue
        site = bp.GetLocationAtIndex(0).GetAddress().GetFileAddress()
        name = SITES.get(site)
        if name is None:
            continue
        bp.SetScriptCallbackFunction("plane_sweep_correspondence_probe.hit")
        ids[name] = bp.GetID()
    state["breakpoint_ids"] = ids
    print("PLANE_SWEEP_CORRESPONDENCE_ATTACHED", json.dumps(ids, sort_keys=True))


def drive(debugger, max_steps=100000):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while (
        process.IsValid()
        and process.GetState() == lldb.eStateStopped
        and not _state()["capture_complete"]
        and steps < max_steps
    ):
        steps += 1
        process.Continue()
    _state()["drive_steps"] = steps
    print("PLANE_SWEEP_CORRESPONDENCE_DRIVE", steps)


def write_report(debugger, path):
    state = dict(_state())
    state.pop("_libcp_base", None)
    process = debugger.GetSelectedTarget().GetProcess()
    state["process"] = {
        "valid": bool(process and process.IsValid()),
        "state": process.GetState() if process and process.IsValid() else None,
        "exit_status": process.GetExitStatus() if process and process.IsValid() else None,
    }
    with open(path, "w", encoding="ascii") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(
        "PLANE_SWEEP_CORRESPONDENCE_REPORT",
        path,
        bool(state["projection_packet"]),
        bool(state["index_map"]),
        state["errors"],
    )
