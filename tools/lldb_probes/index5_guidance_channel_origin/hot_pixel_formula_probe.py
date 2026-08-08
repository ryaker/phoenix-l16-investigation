import builtins
import hashlib
import json
import struct


CREATE_STEREO_ENTRY = 0x27B7A0
HELPER_ENTRY = 0x2E8680
WORKER_ENTRY = 0x2E8CC0
PATCH_STORE = 0x2E9B0E


def reset(label="", patch_limit=16):
    builtins.l16_guidance_hot_pixel_formula = {
        "label": label,
        "patch_limit": patch_limit,
        "create_entries": [],
        "helper_entries": [],
        "worker_entries": [],
        "patches": [],
        "capture_complete": False,
        "terminated_after_capture": False,
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_guidance_hot_pixel_formula"):
        reset()
    return builtins.l16_guidance_hot_pixel_formula


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    if not address or size <= 0:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u64(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<Q", raw)[0] if raw is not None else None


def _xmm_f32(frame, name):
    register = frame.FindRegister(name)
    data = register.GetData()
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    raw = data.ReadRawData(error, 0, data.GetByteSize())
    if not error.Success() or len(raw) < 16:
        return None
    return list(struct.unpack("<4f", raw[:16]))


def _descriptor(process, address):
    raw = _read(process, address, 0x30)
    if raw is None:
        return {"address": address, "read_ok": False}
    words = struct.unpack("<8iQQ", raw)
    return {
        "address": address,
        "read_ok": True,
        "raw": raw.hex(),
        "origin": list(words[0:2]),
        "bounds": list(words[2:4]),
        "size": list(words[4:6]),
        "stride": words[6],
        "reserved": words[7],
        "data": words[8],
        "allocation": words[9],
    }


def _libcp_base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                return base
    return None


def _module_va(frame):
    target = frame.GetThread().GetProcess().GetTarget()
    base = _libcp_base(target)
    return frame.GetPC() - base if base is not None else None


def _u16_window(process, pointer, center, radius=8):
    if not pointer or center < radius:
        return None
    raw = _read(process, pointer + 2 * (center - radius), 2 * (2 * radius + 1))
    if raw is None:
        return None
    return list(struct.unpack("<" + "H" * (2 * radius + 1), raw))


def _image_window(process, descriptor, x, y, radius=6):
    if not descriptor.get("read_ok") or not descriptor["data"]:
        return None
    # Region descriptors retain a source halo outside their logical tile. The
    # filter consumes that halo for the first/last output rows, so preserve it
    # in the receipt instead of rejecting a logical edge coordinate.
    rows = []
    for row in range(y - radius, y + radius + 1):
        address = descriptor["data"] + 2 * (row * descriptor["stride"] + x - radius)
        raw = _read(process, address, 2 * (2 * radius + 1))
        if raw is None:
            return None
        rows.append(list(struct.unpack("<" + "H" * (2 * radius + 1), raw)))
    return rows


def hit(frame, bp_loc, internal_dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    site = _module_va(frame)
    thread_id = thread.GetThreadID()

    if site == CREATE_STEREO_ENTRY:
        state["create_entries"].append({"thread_id": thread_id})
        return False
    if not state["create_entries"]:
        return False

    if site == HELPER_ENTRY:
        if len(state["helper_entries"]) < 1:
            sensor = _u(frame, "rcx")
            sensor_raw = _read(process, sensor, 0x110)
            phase = _read(process, _u(frame, "rdx"), 8)
            state["helper_entries"].append(
                {
                    "thread_id": thread_id,
                    "destination": _descriptor(process, _u(frame, "rdi")),
                    "source": _descriptor(process, _u(frame, "rsi")),
                    "phase": list(struct.unpack("<2i", phase)) if phase else None,
                    "sensor": sensor,
                    "sensor_raw_0x00_0x110": sensor_raw.hex() if sensor_raw else None,
                    "xmm0": _xmm_f32(frame, "xmm0"),
                    "xmm1": _xmm_f32(frame, "xmm1"),
                }
            )
        return False

    if site == WORKER_ENTRY:
        if len(state["worker_entries"]) < 1:
            closure = _u(frame, "rdi")
            raw = _read(process, closure, 0x38)
            if raw is None:
                state["errors"].append("worker closure read failed")
                return False
            pointers = struct.unpack_from("<6Q", raw, 8)
            lut_pointer_block = _read(process, pointers[2], 32)
            lut_pointers = list(struct.unpack("<4Q", lut_pointer_block)) if lut_pointer_block else []
            luts = []
            for pointer in lut_pointers:
                lut = _read(process, pointer, 4096)
                luts.append(
                    {
                        "pointer": pointer,
                        "sha256_1024f": hashlib.sha256(lut).hexdigest() if lut else None,
                        "values_1024f": list(struct.unpack("<1024f", lut)) if lut else None,
                        "first_16": list(struct.unpack("<16f", lut[:64])) if lut else None,
                        "last_4": list(struct.unpack("<4f", lut[-16:])) if lut else None,
                    }
                )
            rectangle = _read(process, _u(frame, "rsi"), 16)
            threshold = _read(process, pointers[3], 4)
            state["worker_entries"].append(
                {
                    "thread_id": thread_id,
                    "closure": closure,
                    "closure_raw": raw.hex(),
                    "source": _descriptor(process, pointers[0]),
                    "phase": list(struct.unpack("<2i", _read(process, pointers[1], 8))),
                    "lut_pointer_block": pointers[2],
                    "luts": luts,
                    "threshold_multiplier_input": struct.unpack("<f", threshold)[0] if threshold else None,
                    "destination": _descriptor(process, pointers[4]),
                    "counter_pointer": pointers[5],
                    "rectangle": list(struct.unpack("<4i", rectangle)) if rectangle else None,
                }
            )
        return False

    if site == PATCH_STORE:
        if len(state["patches"]) >= state["patch_limit"]:
            return False
        rbp = _u(frame, "rbp")
        closure = _u64(process, rbp - 0x1F8)
        if not closure:
            state["errors"].append("patch closure missing")
            return False
        closure_raw = _read(process, closure, 0x38)
        if closure_raw is None:
            state["errors"].append("patch closure unreadable")
            return False
        pointers = struct.unpack_from("<6Q", closure_raw, 8)
        source = _descriptor(process, pointers[0])
        destination = _descriptor(process, pointers[4])
        lut_pointer_block = _read(process, pointers[2], 32)
        lut_pointers = list(struct.unpack("<4Q", lut_pointer_block)) if lut_pointer_block else []
        patch_luts = []
        for pointer in lut_pointers:
            lut = _read(process, pointer, 4096)
            patch_luts.append(
                {
                    "pointer": pointer,
                    "sha256_1024f": hashlib.sha256(lut).hexdigest() if lut else None,
                    "values_1024f": list(struct.unpack("<1024f", lut)) if lut else None,
                }
            )
        row_pointer = _u(frame, "rsi")
        x_index = _u(frame, "r12")
        destination_address = row_pointer + 2 * x_index
        pixel_offset = (destination_address - destination["data"]) // 2
        y = pixel_offset // destination["stride"]
        x = pixel_offset % destination["stride"]
        before = _read(process, destination_address, 2)
        local_offsets = (-0x158, -0x150, -0x148, -0x110, -0x108, -0x100, -0xF8, -0xF0, -0xE8)
        ring_windows = {}
        for offset in local_offsets:
            pointer = _u64(process, rbp + offset)
            ring_windows[f"rbp{offset:+#x}"] = {
                "pointer": pointer,
                "u16_x_minus8_plus8": _u16_window(process, pointer, x_index),
            }
        ring_windows["r13"] = {
            "pointer": _u(frame, "r13"),
            "u16_x_minus8_plus8": _u16_window(process, _u(frame, "r13"), x_index),
        }
        state["patches"].append(
            {
                "thread_id": thread_id,
                "xy": [x, y],
                "x_index_r12": x_index,
                "destination_address": destination_address,
                "source_value": (
                    struct.unpack(
                        "<H",
                        _read(
                            process,
                            source["data"] + 2 * (y * source["stride"] + x),
                            2,
                        ),
                    )[0]
                ),
                "destination_before": struct.unpack("<H", before)[0] if before else None,
                "replacement_ax": _u(frame, "rax") & 0xFFFF,
                "source_window_13x13": _image_window(process, source, x, y),
                "luts": patch_luts,
                "ring_windows": ring_windows,
            }
        )
        if len(state["patches"]) >= state["patch_limit"]:
            state["capture_complete"] = True
            error = process.Kill()
            state["terminated_after_capture"] = error.Success()
            if not error.Success():
                state["errors"].append(f"kill failed: {error.GetCString()}")
        return False

    state["errors"].append(f"unexpected site {site}")
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    expected = {CREATE_STEREO_ENTRY, HELPER_ENTRY, WORKER_ENTRY, PATCH_STORE}
    found = set()
    for index in range(target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(index)
        if not bp or not bp.IsValid() or bp.GetNumLocations() < 1:
            continue
        site = bp.GetLocationAtIndex(0).GetAddress().GetFileAddress()
        if site in expected:
            bp.SetScriptCallbackFunction("hot_pixel_formula_probe.hit")
            found.add(site)
    if found != expected:
        _state()["errors"].append("missing sites: " + repr(sorted(expected - found)))
    print("L16_GUIDANCE_HOT_PIXEL_FORMULA_ATTACHED", [hex(x) for x in sorted(found)])


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
    print("L16_GUIDANCE_HOT_PIXEL_FORMULA_REPORT", path)
