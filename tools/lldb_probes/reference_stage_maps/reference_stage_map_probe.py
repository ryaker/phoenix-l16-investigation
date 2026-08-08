import builtins
import hashlib
import json
import math
import os
import struct


SITES = {
    0x26E4D5: ("index5_hypothesis_index", 2, "u16"),
    0x26E64F: ("index5_depth", 4, "f32"),
    0x26AC18: ("upsampled_depth", 4, "f32"),
    0x41EB5A: ("gdepth_full", 4, "f32"),
}


def reset(label="", output_dir="", sites=None, stop_after_site=None):
    builtins.l16_reference_stage_maps = {
        "label": label,
        "output_dir": output_dir,
        "captures": [],
        "counts": {},
        "errors": [],
        "sites": list(SITES if sites is None else sites),
        "stop_after_site": stop_after_site,
    }


def _state():
    if not hasattr(builtins, "l16_reference_stage_maps"):
        reset()
    return builtins.l16_reference_stage_maps


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    raw = process.ReadMemory(address, size, error)
    if not error.Success() or len(raw) != size:
        return None
    return raw


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


def _base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            value = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if value != 0xFFFFFFFFFFFFFFFF:
                return value
    return None


def _write_map(process, name, descriptor, element_size, kind):
    state = _state()
    width, height = descriptor["size"]
    stride = descriptor["stride"]
    require_sizes = width > 0 and height > 0 and stride >= width and descriptor["data"]
    if not require_sizes:
        state["errors"].append(f"{name}: invalid descriptor")
        return
    extension = "f32le" if kind == "f32" else "u16le"
    path = os.path.join(state["output_dir"], f"{name}.{extension}")
    digest = hashlib.sha256()
    count = 0
    finite = 0
    minimum = None
    maximum = None
    total = 0.0
    with open(path, "wb") as handle:
        for y in range(height):
            raw = _read(
                process,
                descriptor["data"] + y * stride * element_size,
                width * element_size,
            )
            if raw is None:
                state["errors"].append(f"{name}: row {y} read failed")
                return
            handle.write(raw)
            digest.update(raw)
            if kind == "f32":
                values = struct.unpack("<" + "f" * width, raw)
                for value in values:
                    count += 1
                    if not math.isfinite(value):
                        continue
                    finite += 1
                    total += value
                    minimum = value if minimum is None else min(minimum, value)
                    maximum = value if maximum is None else max(maximum, value)
            else:
                values = struct.unpack("<" + "H" * width, raw)
                count += width
                finite += width
                row_min = min(values)
                row_max = max(values)
                minimum = row_min if minimum is None else min(minimum, row_min)
                maximum = row_max if maximum is None else max(maximum, row_max)
                total += sum(values)
    state["captures"].append(
        {
            "name": name,
            "path": path,
            "kind": kind,
            "element_size": element_size,
            "descriptor": descriptor,
            "logical_bytes": count * element_size,
            "sha256": digest.hexdigest(),
            "count": count,
            "finite_count": finite,
            "minimum": minimum,
            "maximum": maximum,
            "mean": total / finite if finite else None,
        }
    )


def hit(frame, bp_loc, internal_dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    base = _base(process.GetTarget())
    site = frame.GetPC() - base if base is not None else None
    if site not in SITES:
        state["errors"].append(f"unexpected site {site}")
        return False
    name, element_size, kind = SITES[site]
    state["counts"][name] = state["counts"].get(name, 0) + 1
    if any(item["name"] == name for item in state["captures"]):
        return False
    rbp = _u(frame, "rbp")
    if site in (0x26E4D5, 0x26E64F):
        index_raw = _read(process, _u(frame, "r12") + 8, 4)
        index = struct.unpack("<i", index_raw)[0] if index_raw else None
        if index != 5:
            return False
    if site == 0x26E4D5:
        descriptor_address = rbp - 0xE0
    elif site in (0x26E64F, 0x26AC18):
        descriptor_address = _u(frame, "r14")
    else:
        descriptor_address = rbp - 0x6E0
    descriptor = _descriptor(process, descriptor_address)
    if descriptor is None:
        state["errors"].append(f"{name}: descriptor read failed")
        return False
    _write_map(process, name, descriptor, element_size, kind)
    return site == state["stop_after_site"]


def attach(debugger):
    os.makedirs(_state()["output_dir"], exist_ok=True)
    target = debugger.GetSelectedTarget()
    found = set()
    for index in range(target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(index)
        if not bp or not bp.IsValid() or bp.GetNumLocations() < 1:
            continue
        site = bp.GetLocationAtIndex(0).GetAddress().GetFileAddress()
        if site in SITES:
            bp.SetScriptCallbackFunction("reference_stage_map_probe.hit")
            found.add(site)
    expected = set(_state()["sites"])
    if found != expected:
        _state()["errors"].append("missing sites: " + repr(sorted(expected - found)))
    print("REFERENCE_STAGE_MAPS_ATTACHED", [hex(site) for site in sorted(found)])


def write_report(debugger, path):
    process = debugger.GetSelectedTarget().GetProcess()
    state = dict(_state())
    state["process"] = {"state": process.GetState(), "exit_status": process.GetExitStatus()}
    with open(path, "w", encoding="ascii") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("REFERENCE_STAGE_MAPS_REPORT", path, len(state["captures"]), state["errors"])
