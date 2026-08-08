import builtins
import hashlib
import json
import math
import os
import struct


ENTRY_VA = 0x27B7A0
CAMERA_KEY_COMPARE_VA = 0x3F5035
POST_SOFTISP_VA = 0x27BD07
COLLAPSE_CALL_READY_VA = 0x27BCD7
COLLAPSE_CALL_DONE_VA = 0x27BCDC
PRE_COLOR_VA = 0x27BFDB
POST_COLOR_VA = 0x27BFF5
COLOR_CALLBACK_READY_VA = 0x27AE60
PACKED_READY_VA = 0x27C93B
COLLAPSE2_WORKERS = {
    0xA4AC0: [0, 0],
    0xA50D0: [1, 0],
    0xA56E0: [0, 1],
    0xA5CF0: [1, 1],
}
COLLAPSE2_AFTER = {
    0xA4F55: [0, 0],
    0xA5565: [1, 0],
    0xA5B75: [0, 1],
    0xA6185: [1, 1],
}


def reset(label, output_dir, wanted_key=0, source_lri=None, single_camera=False):
    builtins.l16_create_stereo_color_stage = {
        "label": label,
        "output_dir": output_dir,
        "wanted_key": int(wanted_key),
        "source_lri": source_lri,
        "single_camera": bool(single_camera),
        "last_key_by_thread": {},
        "selected_thread": None,
        "entry": None,
        "collapse_candidates": [],
        "pre_collapse": None,
        "post_collapse": None,
        "post_softisp": None,
        "pre_color": None,
        "color_callback": None,
        "post_color": None,
        "packed_u8": None,
        "errors": [],
        "terminated_after_capture": False,
    }


def _state():
    if not hasattr(builtins, "l16_create_stereo_color_stage"):
        reset("", "")
    return builtins.l16_create_stereo_color_stage


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


def _u64(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<Q", raw)[0] if raw is not None else None


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


def _dump_vec4f(process, descriptor, path):
    width, height = descriptor["size"]
    stride = descriptor["stride"]
    if width <= 0 or height <= 0 or stride < width or not descriptor["data"]:
        return None
    digest = hashlib.sha256()
    count = 0
    finite = 0
    sums = [0.0, 0.0, 0.0, 0.0]
    minima = [None, None, None, None]
    maxima = [None, None, None, None]
    with open(path, "wb") as output:
        for y in range(height):
            raw = _read(process, descriptor["data"] + y * stride * 16, width * 16)
            if raw is None:
                return None
            output.write(raw)
            digest.update(raw)
            values = struct.unpack("<" + "f" * (width * 4), raw)
            for offset in range(0, len(values), 4):
                pixel = values[offset : offset + 4]
                if not all(math.isfinite(value) for value in pixel):
                    continue
                finite += 1
                for channel, value in enumerate(pixel):
                    sums[channel] += value
                    minima[channel] = value if minima[channel] is None else min(minima[channel], value)
                    maxima[channel] = value if maxima[channel] is None else max(maxima[channel], value)
            count += width
    return {
        "path": path,
        "logical_bytes": count * 16,
        "sha256": digest.hexdigest(),
        "pixel_count": count,
        "finite_pixel_count": finite,
        "minimum": minima,
        "maximum": maxima,
        "mean": [value / finite for value in sums] if finite else None,
    }


def _dump_vec4u8(process, descriptor, path):
    width, height = descriptor["size"]
    stride = descriptor["stride"]
    if width <= 0 or height <= 0 or stride < width or not descriptor["data"]:
        return None
    digest = hashlib.sha256()
    with open(path, "wb") as output:
        for y in range(height):
            raw = _read(process, descriptor["data"] + y * stride * 4, width * 4)
            if raw is None:
                return None
            output.write(raw)
            digest.update(raw)
    return {
        "path": path,
        "logical_bytes": width * height * 4,
        "sha256": digest.hexdigest(),
        "pixel_count": width * height,
    }


def _dump_f32(process, descriptor, path):
    width, height = descriptor["size"]
    stride = descriptor["stride"]
    if width <= 0 or height <= 0 or stride < width or not descriptor["data"]:
        return None
    digest = hashlib.sha256()
    minimum = None
    maximum = None
    total = 0.0
    finite = 0
    with open(path, "wb") as output:
        for y in range(height):
            raw = _read(process, descriptor["data"] + y * stride * 4, width * 4)
            if raw is None:
                return None
            output.write(raw)
            digest.update(raw)
            for value in struct.unpack("<" + "f" * width, raw):
                if not math.isfinite(value):
                    continue
                finite += 1
                total += value
                minimum = value if minimum is None else min(minimum, value)
                maximum = value if maximum is None else max(maximum, value)
    return {
        "path": path,
        "logical_bytes": width * height * 4,
        "sha256": digest.hexdigest(),
        "sample_count": width * height,
        "finite_sample_count": finite,
        "minimum": minimum,
        "maximum": maximum,
        "mean": total / finite if finite else None,
    }


def hit(frame, bp_loc, internal_dict):
    state = _state()
    thread = frame.GetThread()
    thread_id = thread.GetThreadID()
    process = thread.GetProcess()
    target = process.GetTarget()
    base = _base(target)
    site = frame.GetPC() - base if base is not None else None
    if site == CAMERA_KEY_COMPARE_VA:
        state["last_key_by_thread"][str(thread_id)] = _u(frame, "rsi") & 0xFFFFFFFF
        return False
    if site == ENTRY_VA:
        source_key = state["last_key_by_thread"].get(str(thread_id))
        if state["selected_thread"] is None and source_key == state["wanted_key"]:
            rsp = _u(frame, "rsp")
            captured_image = _u(frame, "rdx")
            neutral_raw = _read(process, _u64(process, rsp + 0x18), 12)
            sensor_type_raw = _read(process, captured_image + 0xA8, 4)
            state["selected_thread"] = thread_id
            state["entry"] = {
                "thread_id": thread_id,
                "source_key": source_key,
                "input_u16_descriptor": _descriptor(process, _u(frame, "rsi")),
                "captured_image_address": captured_image,
                "sensor_type": (
                    struct.unpack("<i", sensor_type_raw)[0]
                    if sensor_type_raw is not None
                    else None
                ),
                "calib_data_1_address": _u(frame, "rcx"),
                "calib_data_2_address": _u(frame, "r8"),
                "softisp_1_address": _u64(process, rsp + 0x08),
                "softisp_2_address": _u64(process, rsp + 0x10),
                "neutral_color_address": _u64(process, rsp + 0x18),
                "neutral_color": (
                    list(struct.unpack("<3f", neutral_raw))
                    if neutral_raw is not None
                    else None
                ),
            }
        return False
    if site in COLLAPSE2_WORKERS and state["entry"] is not None:
        closure = _u(frame, "rdi")
        rectangle_raw = _read(process, _u(frame, "rsi"), 16)
        input_descriptor = _descriptor(process, _u64(process, closure + 0x08))
        output_descriptor = _descriptor(process, _u64(process, closure + 0x10))
        if input_descriptor is None or output_descriptor is None or rectangle_raw is None:
            state["errors"].append("collapse candidate descriptor/rectangle read failed")
            return False
        identity = (
            site,
            input_descriptor["allocation"],
            output_descriptor["allocation"],
        )
        if not any(item["identity"] == identity for item in state["collapse_candidates"]):
            state["collapse_candidates"].append(
                {
                    "identity": identity,
                    "worker_va": site,
                    "phase_bits": COLLAPSE2_WORKERS[site],
                    "thread_id": thread_id,
                    "rectangle": list(struct.unpack("<4i", rectangle_raw)),
                    "input_descriptor": input_descriptor,
                    "output_descriptor": output_descriptor,
                }
            )
        return False
    if site in COLLAPSE2_AFTER:
        if state["post_collapse"] is None and state["single_camera"]:
            rbp = _u(frame, "rbp")
            closure = _u64(process, rbp - 0xC8)
            input_descriptor = _descriptor(process, _u64(process, closure + 0x08))
            output_descriptor = _descriptor(process, _u64(process, closure + 0x10))
            if input_descriptor is None or output_descriptor is None:
                state["errors"].append("completed collapse descriptor read failed")
                return False
            pre_artifact = _dump_f32(
                process,
                input_descriptor,
                os.path.join(state["output_dir"], "pre_collapse.f32"),
            )
            post_artifact = _dump_vec4f(
                process,
                output_descriptor,
                os.path.join(state["output_dir"], "post_collapse.rgba32f"),
            )
            if pre_artifact is None or post_artifact is None:
                state["errors"].append("completed collapse image dump failed")
                return False
            state["pre_collapse"] = {
                "worker_after_va": site,
                "phase_bits": COLLAPSE2_AFTER[site],
                "descriptor": input_descriptor,
                "artifact": pre_artifact,
                "join": "same A1-only worker closure as completed output",
            }
            state["post_collapse"] = {
                "worker_after_va": site,
                "phase_bits": COLLAPSE2_AFTER[site],
                "descriptor": output_descriptor,
                "artifact": post_artifact,
                "join": "same A1-only worker closure as scalar input",
            }
        return False
    if thread_id != state["selected_thread"]:
        return False
    if site == COLOR_CALLBACK_READY_VA:
        rbp = _u(frame, "rbp")
        closure = rbp - 0x60
        closure_raw = _read(process, closure, 0x48)
        vtable = _u64(process, closure)
        worker = _u64(process, vtable + 0x30) if vtable else None
        yuv_offset_raw = _read(process, base + 0x670470, 16) if base else None
        state["color_callback"] = {
            "module_base": base,
            "closure": closure,
            "closure_raw": closure_raw.hex() if closure_raw is not None else None,
            "vtable": vtable,
            "vtable_va": vtable - base if vtable and base else None,
            "worker": worker,
            "worker_va": worker - base if worker and base else None,
            "output_descriptor": _descriptor(process, _u64(process, closure + 0x08)),
            "input_descriptor": _descriptor(process, _u64(process, closure + 0x10)),
            "matrix_address": _u64(process, closure + 0x18),
            "yuv_offset": (
                list(struct.unpack("<4f", yuv_offset_raw))
                if yuv_offset_raw is not None
                else None
            ),
        }
        if closure_raw is None or not vtable or not worker:
            state["errors"].append("color callback capture failed")
        return False
    rbp = _u(frame, "rbp")
    if site == COLLAPSE_CALL_READY_VA:
        descriptor = _descriptor(process, rbp - 0x3A0)
        if descriptor is None:
            state["errors"].append("parent pre-collapse descriptor read failed")
            return False
        artifact = _dump_f32(
            process,
            descriptor,
            os.path.join(state["output_dir"], "pre_collapse.f32"),
        )
        if artifact is None:
            state["errors"].append("parent pre-collapse image dump failed")
            return False
        state["pre_collapse"] = {
            "descriptor": descriptor,
            "artifact": artifact,
            "phase_bits": None,
            "join": "selected parent immediately before 0x27bcd7 -> 0xa6f20",
        }
        return False
    if site == COLLAPSE_CALL_DONE_VA:
        descriptor = _descriptor(process, rbp - 0x370)
        if descriptor is None:
            state["errors"].append("parent post-collapse descriptor read failed")
            return False
        artifact = _dump_vec4f(
            process,
            descriptor,
            os.path.join(state["output_dir"], "post_collapse.rgba32f"),
        )
        if artifact is None:
            state["errors"].append("parent post-collapse image dump failed")
            return False
        state["post_collapse"] = {
            "descriptor": descriptor,
            "artifact": artifact,
            "join": "selected parent immediately after 0x27bcd7 -> 0xa6f20",
        }
        return False
    if site == POST_SOFTISP_VA:
        descriptor = _descriptor(process, rbp - 0x2A0)
        if descriptor is None:
            state["errors"].append("post-SoftISP descriptor read failed")
            return False
        artifact = _dump_vec4f(
            process,
            descriptor,
            os.path.join(state["output_dir"], "post_softisp.rgba32f"),
        )
        if artifact is None:
            state["errors"].append("post-SoftISP image dump failed")
            return False
        state["post_softisp"] = {"descriptor": descriptor, "artifact": artifact}
        matches = [
            item
            for item in state["collapse_candidates"]
            if item["output_descriptor"]["allocation"] == descriptor["allocation"]
            and item["output_descriptor"]["data"] == descriptor["data"]
        ]
        if matches and state["pre_collapse"] is None:
            candidate = matches[0]
            pre_artifact = _dump_f32(
                process,
                candidate["input_descriptor"],
                os.path.join(state["output_dir"], "pre_collapse.f32"),
            )
            if pre_artifact is None:
                state["errors"].append("joined pre-collapse image dump failed")
            else:
                state["pre_collapse"] = {
                    **candidate,
                    "artifact": pre_artifact,
                    "join": "collapse output allocation equals selected post-SoftISP allocation",
                }
                state["post_collapse"] = {
                    "descriptor": descriptor,
                    "artifact": artifact,
                    "join": "same descriptor as selected post-SoftISP surface",
                }
        return False
    if site == PRE_COLOR_VA:
        descriptor = _descriptor(process, rbp - 0x2A0)
        matrix = _read(process, rbp - 0x240, 0x40)
        if descriptor is None or matrix is None:
            state["errors"].append("pre-color descriptor/matrix read failed")
            return False
        artifact = _dump_vec4f(
            process,
            descriptor,
            os.path.join(state["output_dir"], "pre_color.rgba32f"),
        )
        if artifact is None:
            state["errors"].append("pre-color image dump failed")
            return False
        state["pre_color"] = {
            "descriptor": descriptor,
            "matrix_raw": matrix.hex(),
            "matrix_rows": [
                list(struct.unpack_from("<4f", matrix, 16 * row))
                for row in range(4)
            ],
            "artifact": artifact,
        }
        return False
    if site == POST_COLOR_VA:
        descriptor = _descriptor(process, rbp - 0x500)
        if descriptor is None:
            state["errors"].append("post-color descriptor read failed")
            return False
        artifact = _dump_vec4f(
            process,
            descriptor,
            os.path.join(state["output_dir"], "post_color.rgba32f"),
        )
        if artifact is None:
            state["errors"].append("post-color image dump failed")
            return False
        state["post_color"] = {"descriptor": descriptor, "artifact": artifact}
        return False
    if site == PACKED_READY_VA:
        descriptor = _descriptor(process, _u(frame, "r13"))
        if descriptor is None:
            state["errors"].append("packed-u8 descriptor read failed")
            return False
        artifact = _dump_vec4u8(
            process,
            descriptor,
            os.path.join(state["output_dir"], "packed_u8.rgba8"),
        )
        if artifact is None:
            state["errors"].append("packed-u8 image dump failed")
            return False
        state["packed_u8"] = {"descriptor": descriptor, "artifact": artifact}
        error = process.Kill()
        state["terminated_after_capture"] = error.Success()
        if not error.Success():
            state["errors"].append(f"kill failed: {error.GetCString()}")
        return False
    state["errors"].append(f"unexpected site {site}")
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
        if site in (
            ENTRY_VA,
            CAMERA_KEY_COMPARE_VA,
            POST_SOFTISP_VA,
            COLLAPSE_CALL_READY_VA,
            COLLAPSE_CALL_DONE_VA,
            PRE_COLOR_VA,
            POST_COLOR_VA,
            COLOR_CALLBACK_READY_VA,
            PACKED_READY_VA,
        ) or site in COLLAPSE2_WORKERS or site in COLLAPSE2_AFTER:
            breakpoint.SetScriptCallbackFunction("create_stereo_color_stage_probe.hit")
            found.add(site)
    expected = {
        ENTRY_VA,
        CAMERA_KEY_COMPARE_VA,
        POST_SOFTISP_VA,
        COLLAPSE_CALL_READY_VA,
        COLLAPSE_CALL_DONE_VA,
        PRE_COLOR_VA,
        POST_COLOR_VA,
        COLOR_CALLBACK_READY_VA,
        PACKED_READY_VA,
    } | set(COLLAPSE2_WORKERS) | set(COLLAPSE2_AFTER)
    if found != expected:
        _state()["errors"].append(f"missing sites {sorted(expected - found)}")
    print("CREATE_STEREO_COLOR_STAGE_ATTACHED", [hex(site) for site in sorted(found)])


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
    print("CREATE_STEREO_COLOR_STAGE_REPORT", path)
