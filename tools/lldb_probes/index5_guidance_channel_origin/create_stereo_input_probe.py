import builtins
import hashlib
import json
import math
import os
import struct


ENTRY_VA = 0x27B7A0
CAMERA_KEY_COMPARE_VA = 0x3F5035


def reset(label, output_dir, wanted_key=0, source_lri=None):
    builtins.l16_create_stereo_input = {
        "label": label,
        "output_dir": output_dir,
        "wanted_key": int(wanted_key),
        "source_lri": source_lri,
        "last_source_key": None,
        "camera_key_pairs": [],
        "entries": [],
        "capture": None,
        "errors": [],
        "terminated_after_capture": False,
    }


def _state():
    if not hasattr(builtins, "l16_create_stereo_input"):
        reset("", "")
    return builtins.l16_create_stereo_input


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    if not address or size <= 0:
        return None
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
        "reserved": words[7],
        "data": words[8],
        "allocation": words[9],
        "raw": raw.hex(),
    }


def _dump_u16(process, descriptor, path):
    width, height = descriptor["size"]
    stride = descriptor["stride"]
    if width <= 0 or height <= 0 or stride < width or not descriptor["data"]:
        return None
    digest = hashlib.sha256()
    count = 0
    minimum = None
    maximum = None
    total = 0
    samples = {}
    sample_xy = {
        "top_left": (0, 0),
        "quarter": (width // 4, height // 4),
        "center": (width // 2, height // 2),
        "three_quarter": (3 * width // 4, 3 * height // 4),
        "bottom_right": (width - 1, height - 1),
    }
    with open(path, "wb") as output:
        for y in range(height):
            raw = _read(process, descriptor["data"] + y * stride * 2, width * 2)
            if raw is None:
                return None
            output.write(raw)
            digest.update(raw)
            values = struct.unpack("<" + "H" * width, raw)
            row_min = min(values)
            row_max = max(values)
            minimum = row_min if minimum is None else min(minimum, row_min)
            maximum = row_max if maximum is None else max(maximum, row_max)
            total += sum(values)
            count += width
            for name, (x, sy) in sample_xy.items():
                if y == sy:
                    samples[name] = {"xy": [x, y], "value": values[x]}
    return {
        "path": path,
        "logical_bytes": count * 2,
        "sha256": digest.hexdigest(),
        "count": count,
        "minimum": minimum,
        "maximum": maximum,
        "mean": total / count if count else math.nan,
        "samples": samples,
    }


def hit(frame, bp_loc, internal_dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    base = _base(target)
    site = frame.GetPC() - base if base is not None else None
    if site == CAMERA_KEY_COMPARE_VA:
        source_key = _u(frame, "rsi") & 0xFFFFFFFF
        anchor_raw = _read(process, _u(frame, "rdi"), 4)
        anchor_key = struct.unpack("<I", anchor_raw)[0] if anchor_raw else None
        state["last_source_key"] = source_key
        state["camera_key_pairs"].append(
            {"source_key": source_key, "anchor_key": anchor_key}
        )
        return False
    if site != ENTRY_VA:
        state["errors"].append(f"unexpected site {site}")
        return False
    entry = {
        "source_key": state.get("last_source_key"),
        "input_descriptor_address": _u(frame, "rsi"),
        "captured_image_address": _u(frame, "rdx"),
        "calib_data_1_address": _u(frame, "rcx"),
        "calib_data_2_address": _u(frame, "r8"),
    }
    state["entries"].append(entry)
    if state["capture"] is not None or entry["source_key"] != state["wanted_key"]:
        return False
    descriptor = _descriptor(process, entry["input_descriptor_address"])
    if descriptor is None:
        state["errors"].append("input descriptor read failed")
        return False
    path = os.path.join(state["output_dir"], "create_stereo_input.u16le")
    artifact = _dump_u16(process, descriptor, path)
    if artifact is None:
        state["errors"].append("input image dump failed")
        return False
    state["capture"] = {
        "source_key": entry["source_key"],
        "descriptor": descriptor,
        "artifact": artifact,
    }
    error = process.Kill()
    state["terminated_after_capture"] = error.Success()
    if not error.Success():
        state["errors"].append(f"kill failed: {error.GetCString()}")
    return False


def attach(debugger):
    os.makedirs(_state()["output_dir"], exist_ok=True)
    target = debugger.GetSelectedTarget()
    found = set()
    for index in range(target.GetNumBreakpoints()):
        breakpoint = target.GetBreakpointAtIndex(index)
        if not breakpoint or not breakpoint.IsValid() or breakpoint.GetNumLocations() < 1:
            continue
        site = breakpoint.GetLocationAtIndex(0).GetAddress().GetFileAddress()
        if site in (ENTRY_VA, CAMERA_KEY_COMPARE_VA):
            breakpoint.SetScriptCallbackFunction("create_stereo_input_probe.hit")
            found.add(site)
    expected = {ENTRY_VA, CAMERA_KEY_COMPARE_VA}
    if found != expected:
        _state()["errors"].append(f"missing sites {sorted(expected - found)}")
    print("CREATE_STEREO_INPUT_ATTACHED", [hex(site) for site in sorted(found)])


def write_report(debugger, path):
    process = debugger.GetSelectedTarget().GetProcess()
    state = dict(_state())
    state["process"] = {
        "state": process.GetState(),
        "exit_status": process.GetExitStatus(),
    }
    with open(path, "w", encoding="ascii") as output:
        json.dump(state, output, indent=2, sort_keys=True)
        output.write("\n")
    print("CREATE_STEREO_INPUT_REPORT", path)
