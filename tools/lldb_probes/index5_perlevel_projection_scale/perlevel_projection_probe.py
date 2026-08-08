import builtins
import hashlib
import json
import struct


PROJECTION_VECTOR_AFTER = 0x276A01
EXPECTED_DIMS = {
    (65, 49),
    (130, 98),
    (260, 195),
    (520, 390),
    (1040, 780),
    (2080, 1560),
}


def reset(label="", source_lri=None):
    builtins.l16_perlevel_projection = {
        "label": label,
        "source_lri": source_lri,
        "hits": 0,
        "packets": [],
        "errors": [],
        "terminated_after_capture": False,
    }


def _state():
    if not hasattr(builtins, "l16_perlevel_projection"):
        reset()
    return builtins.l16_perlevel_projection


def _read(process, address, size):
    if not address or size <= 0:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    raw = process.ReadMemory(address, size, error)
    return raw if error.Success() and len(raw) == size else None


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _u64(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<Q", raw)[0] if raw is not None else None


def _i32(process, address):
    raw = _read(process, address, 4)
    return struct.unpack("<i", raw)[0] if raw is not None else None


def _descriptor(process, address):
    raw = _read(process, address, 0x30)
    if raw is None:
        return None
    words = struct.unpack("<8iQQ", raw)
    return {
        "address": address,
        "origin": list(words[0:2]),
        "bounds": list(words[2:4]),
        "size": list(words[4:6]),
        "stride": words[6],
        "data": words[8],
        "allocation": words[9],
    }


def _record_50(process, address):
    raw = _read(process, address, 0x50)
    if raw is None:
        return None
    return {
        "address": address,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "matrix": list(struct.unpack_from("<16f", raw, 0)),
        "map": struct.unpack_from("<Q", raw, 0x40)[0],
        "scale": list(struct.unpack_from("<2f", raw, 0x48)),
        "raw_hex": raw.hex(),
    }


def _camera_record(process, address):
    raw = _read(process, address, 0xA8)
    if raw is None:
        return None
    return {
        "address": address,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "k": list(struct.unpack_from("<9f", raw, 0)),
        "translation": list(struct.unpack_from("<3f", raw, 0x24)),
        "rotation": list(struct.unpack_from("<9f", raw, 0x30)),
        "adjustment": list(struct.unpack_from("<4f", raw, 0x54)),
    }


def hit(frame, bp_loc, internal_dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    state["hits"] += 1
    layer = _u(frame, "r12")
    index_mode = _read(process, layer + 0x08, 8)
    if index_mode is None:
        state["errors"].append("index/mode read failed")
        return False
    index, mode = struct.unpack("<2I", index_mode)
    if index > 5 or mode != 8:
        return False

    guidance = _descriptor(process, _u64(process, layer + 0x288))
    if guidance is None:
        state["errors"].append("guidance descriptor read failed")
        return False
    dims = tuple(guidance["size"])
    if any(item["index"] == index for item in state["packets"]):
        return False

    rbp = _u(frame, "rbp")
    vector_raw = _read(process, rbp - 0x138, 0x18)
    camera_begin = _u64(process, layer + 0x258)
    if vector_raw is None or camera_begin is None:
        state["errors"].append("projection/camera vector read failed")
        return False
    begin, end, cap = struct.unpack("<3Q", vector_raw)
    if end - begin != 4 * 0x50:
        state["errors"].append("unexpected projection record count")
        return False

    packet = {
        "ordinal": len(state["packets"]),
        "layer": layer,
        "index": index,
        "mode": mode,
        "guidance": guidance,
        "runpass_block_count_arg": _i32(process, rbp - 0x324),
        "incoming_xy": list(struct.unpack("<2i", _read(process, _u64(process, rbp - 0x150), 8))),
        "layer_dimensions_0x2b8": list(struct.unpack("<2i", _read(process, layer + 0x2B8, 8))),
        "image_coordinate_step_0x1c": _i32(process, layer + 0x1C),
        "projection_vector": {"begin": begin, "end": end, "cap": cap},
        "projection_records": [
            _record_50(process, begin + ordinal * 0x50) for ordinal in range(4)
        ],
        "camera_records": [
            _camera_record(process, camera_begin + ordinal * 0xA8)
            for ordinal in range(5)
        ],
    }
    images_raw = _read(process, layer + 0x240, 0x18)
    if images_raw is None:
        state["errors"].append("Images vector read failed")
        return False
    image_begin, image_end, image_cap = struct.unpack("<3Q", images_raw)
    packet["images_vector"] = {
        "begin": image_begin,
        "end": image_end,
        "cap": image_cap,
        "count": (image_end - image_begin) // 0x10,
    }
    packet["images"] = []
    for ordinal in range(packet["images_vector"]["count"]):
        shared = _read(process, image_begin + ordinal * 0x10, 0x10)
        if shared is None:
            state["errors"].append("Images entry read failed")
            return False
        object_ptr, owner_ptr = struct.unpack("<2Q", shared)
        packet["images"].append(
            {
                "ordinal": ordinal,
                "object": object_ptr,
                "owner": owner_ptr,
                "descriptor": _descriptor(process, object_ptr),
            }
        )
    if any(item is None for item in packet["projection_records"] + packet["camera_records"]):
        state["errors"].append("record read failed")
        return False
    state["packets"].append(packet)

    observed = {tuple(item["guidance"]["size"]) for item in state["packets"]}
    if observed == EXPECTED_DIMS:
        error = process.Kill()
        state["terminated_after_capture"] = error.Success()
        if not error.Success():
            state["errors"].append("kill failed: %s" % error.GetCString())
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    found = False
    for index in range(target.GetNumBreakpoints()):
        breakpoint = target.GetBreakpointAtIndex(index)
        if not breakpoint or not breakpoint.IsValid() or breakpoint.GetNumLocations() < 1:
            continue
        site = breakpoint.GetLocationAtIndex(0).GetAddress().GetFileAddress()
        if site == PROJECTION_VECTOR_AFTER:
            breakpoint.SetScriptCallbackFunction("perlevel_projection_probe.hit")
            found = True
    if not found:
        _state()["errors"].append("projection breakpoint missing")
    print("PERLEVEL_PROJECTION_ATTACHED", found)


def write_report(debugger, path):
    state = dict(_state())
    process = debugger.GetSelectedTarget().GetProcess()
    state["process"] = {
        "state": process.GetState(),
        "exit_status": process.GetExitStatus(),
    }
    with open(path, "w", encoding="ascii") as output:
        json.dump(state, output, indent=2, sort_keys=True)
        output.write("\n")
    print("PERLEVEL_PROJECTION_REPORT", path, len(state["packets"]), state["errors"])
