import builtins
import hashlib
import json
import os
import struct


SITE = 0x3E79ED
CAMERA_NAMES = {
    0: "A1", 1: "A2", 2: "A3", 3: "A4", 4: "A5",
    5: "B1", 6: "B2", 7: "B3", 8: "B4", 9: "B5",
    10: "C1", 11: "C2", 12: "C3", 13: "C4", 14: "C5", 15: "C6",
}


def reset(label="", output_dir=""):
    builtins.l16_source_cache_tiles = {
        "label": label,
        "output_dir": output_dir,
        "hit_count": 0,
        "cache_objects": {},
        "tiles": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_source_cache_tiles"):
        reset()
    return builtins.l16_source_cache_tiles


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    raw = process.ReadMemory(address, size, error)
    if not error.Success() or len(raw) != size:
        return None
    return raw


def _base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            value = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if value != 0xFFFFFFFFFFFFFFFF:
                return value
    return None


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


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
        "raw": raw.hex(),
    }


def _write_tile(process, cache, camera_key, tile_index, descriptor):
    state = _state()
    width, height = descriptor["size"]
    stride = descriptor["stride"]
    if width <= 0 or height <= 0 or stride < width or not descriptor["data"]:
        state["errors"].append(f"invalid tile descriptor {descriptor}")
        return None
    level, tile_x, tile_y = tile_index
    camera_name = CAMERA_NAMES.get(camera_key, f"key{camera_key}")
    name = f"{camera_name}_cache_{cache:x}_l{level}_x{tile_x}_y{tile_y}.rgba16f"
    path = os.path.join(state["output_dir"], name)
    digest = hashlib.sha256()
    with open(path, "wb") as handle:
        for y in range(height):
            raw = _read(
                process,
                descriptor["data"] + y * stride * 8,
                width * 8,
            )
            if raw is None:
                state["errors"].append(f"{name}: row {y} read failed")
                return None
            handle.write(raw)
            digest.update(raw)
    return {
        "path": path,
        "logical_bytes": width * height * 8,
        "sha256": digest.hexdigest(),
    }


def hit(frame, bp_loc, internal_dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    base = _base(process.GetTarget())
    site = frame.GetPC() - base if base is not None else None
    if site != SITE:
        state["errors"].append(f"unexpected site {site}")
        return False
    state["hit_count"] += 1

    cache = _u(frame, "rbx") - 0xF8
    shared_tile = _u(frame, "r15")
    tile_pointer_raw = _read(process, shared_tile, 8)
    if tile_pointer_raw is None:
        state["errors"].append("shared tile pointer read failed")
        return False
    tile = struct.unpack("<Q", tile_pointer_raw)[0]
    tile_image = tile + 0xF0
    tile_raw = _read(process, tile, 0x108)
    cache_raw = _read(process, cache, 0x180)
    descriptor = _descriptor(process, tile_image)
    if tile_raw is None or cache_raw is None or descriptor is None:
        state["errors"].append("cache/tile metadata read failed")
        return False

    level = struct.unpack_from("<i", tile_raw, 0x18)[0]
    tile_x = struct.unpack_from("<i", tile_raw, 0x1C)[0]
    tile_y = struct.unpack_from("<i", tile_raw, 0x20)[0]
    tile_index = (level, tile_x, tile_y)
    cache_key = f"0x{cache:x}"
    camera_key = struct.unpack_from("<i", cache_raw, 0x90)[0]
    if cache_key not in state["cache_objects"]:
        state["cache_objects"][cache_key] = {
            "address": cache,
            "camera_key": camera_key,
            "camera_name": CAMERA_NAMES.get(camera_key),
            "raw": cache_raw.hex(),
            "tile_size_fields": list(struct.unpack_from("<2i", cache_raw, 0x10)),
            "field_a8": list(struct.unpack_from("<2i", cache_raw, 0xA8)),
        }
    if level != 0:
        return False
    if any(
        item["cache"] == cache and item["tile_index"] == list(tile_index)
        for item in state["tiles"]
    ):
        return False

    payload = _write_tile(process, cache, camera_key, tile_index, descriptor)
    if payload is not None:
        state["tiles"].append(
            {
                "ordinal": state["hit_count"],
                "cache": cache,
                "camera_key": camera_key,
                "camera_name": CAMERA_NAMES.get(camera_key),
                "tile": tile,
                "tile_index": list(tile_index),
                "tile_origin_fields": list(struct.unpack_from("<2i", tile_raw, 0x100)),
                "descriptor": descriptor,
                **payload,
            }
        )
    return False


def attach(debugger):
    os.makedirs(_state()["output_dir"], exist_ok=True)
    target = debugger.GetSelectedTarget()
    found = False
    for index in range(target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(index)
        if not bp or not bp.IsValid() or bp.GetNumLocations() < 1:
            continue
        if bp.GetLocationAtIndex(0).GetAddress().GetFileAddress() == SITE:
            bp.SetScriptCallbackFunction("source_cache_tile_probe.hit")
            found = True
    if not found:
        _state()["errors"].append("missing SourceImageCache tile breakpoint")
    print("SOURCE_CACHE_TILE_ATTACHED", found)


def write_report(debugger, path):
    process = debugger.GetSelectedTarget().GetProcess()
    state = dict(_state())
    state["process"] = {
        "state": process.GetState(),
        "exit_status": process.GetExitStatus(),
    }
    with open(path, "w", encoding="ascii") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(
        "SOURCE_CACHE_TILE_REPORT",
        path,
        state["hit_count"],
        len(state["cache_objects"]),
        len(state["tiles"]),
        state["errors"],
    )
