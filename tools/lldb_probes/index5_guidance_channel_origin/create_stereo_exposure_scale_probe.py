import builtins
import hashlib
import json
import os
import struct


BEFORE_VA = 0x27D803
AFTER_VA = 0x27D808
MONO_BEFORE_VA = 0x27DB43
MONO_AFTER_VA = 0x27DB48
CORRECTION_VA = 0xE6A89
HELPER_RETURN_VA = 0x27D7E8
MONO_HELPER_RETURN_VA = 0x27DB2B
VECTOR_PRE_VA = 0x19E910
VECTOR_POST_VA = 0x19E91B
SCALE_RETURN_VA = 0x27D808
MONO_VECTOR_PRE_VA = 0x27F084
MONO_VECTOR_POST_VA = 0x27F098
MONO_SCALE_RETURN_VA = 0x27DB48
DYNAMIC_SITES = {
    "vector_pre": VECTOR_PRE_VA,
    "vector_post": VECTOR_POST_VA,
    "mono_vector_pre": MONO_VECTOR_PRE_VA,
    "mono_vector_post": MONO_VECTOR_POST_VA,
}


def reset(label, output_dir, source_lri, expected_keys):
    builtins.l16_create_stereo_exposure = {
        "label": label,
        "output_dir": output_dir,
        "source_lri": source_lri,
        "expected_keys": sorted(int(value) for value in expected_keys),
        "packets": {},
        "pending": {},
        "corrections": {},
        "reserved_keys": [],
        "errors": [],
        "terminated_after_capture": False,
    }


def _state():
    if not hasattr(builtins, "l16_create_stereo_exposure"):
        reset("", "", "", [])
    return builtins.l16_create_stereo_exposure


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    if not address or size <= 0:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    raw = process.ReadMemory(address, size, error)
    return raw if error.Success() and len(raw) == size else None


def _base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            value = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if value != 0xFFFFFFFFFFFFFFFF:
                return value
    return None


def _unpack(process, address, fmt):
    raw = _read(process, address, struct.calcsize(fmt))
    return struct.unpack(fmt, raw)[0] if raw is not None else None


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
        "raw": raw.hex(),
    }


def _image_bytes(process, descriptor, bytes_per_pixel=16):
    width, height = descriptor["size"]
    stride = descriptor["stride"]
    if width <= 0 or height <= 0 or stride < width or not descriptor["data"]:
        return None
    rows = []
    for y in range(height):
        raw = _read(
            process,
            descriptor["data"] + y * stride * bytes_per_pixel,
            width * bytes_per_pixel,
        )
        if raw is None:
            return None
        rows.append(raw)
    return b"".join(rows)


def _captured_fields(process, address):
    if not address:
        return None
    return {
        "address": address,
        "camera_key": _unpack(process, address + 0x60, "<i"),
        "camera_class": _unpack(process, address + 0x64, "<i"),
        "sensor_exposure": _unpack(process, address + 0x38, "<Q"),
        "sensor_analog_gain": _unpack(process, address + 0x40, "<f"),
        "capture_stack": _unpack(process, address + 0xA0, "<Q"),
        "relative_brightness_gate_pair": [
            _unpack(process, address + 0x58, "<i"),
            _unpack(process, address + 0x5C, "<i"),
        ],
    }


def _target_fields(process, owner, wanted_key):
    begin = _unpack(process, owner + 0x10, "<Q")
    end = _unpack(process, owner + 0x18, "<Q")
    if begin is None or end is None or end < begin or (end - begin) % 16:
        return None
    matches = []
    for cursor in range(begin, end, 16):
        candidate = _unpack(process, cursor, "<Q")
        fields = _captured_fields(process, candidate)
        if fields and fields["camera_class"] == 0 and fields["camera_key"] == wanted_key:
            matches.append(fields)
    return matches[0] if len(matches) == 1 else None


def _arm(process, state, name, thread_id):
    base = _base(process.GetTarget())
    breakpoint = (
        process.GetTarget().BreakpointCreateByAddress(base + DYNAMIC_SITES[name])
        if base is not None
        else None
    )
    if not breakpoint or not breakpoint.IsValid():
        state["errors"].append(f"{name.replace('_', '-')} breakpoint unavailable")
        return False
    breakpoint.SetThreadID(thread_id)
    breakpoint.SetOneShot(True)
    breakpoint.SetScriptCallbackFunction("create_stereo_exposure_scale_probe.hit")
    breakpoint.SetEnabled(True)
    return True


def _disable(process, state, name):
    return None


def _reserve_packet(frame, process, state, thread_key, captured_offset, path):
    closure = _u(frame, "r15")
    captured = _unpack(process, closure + captured_offset, "<Q")
    source = _captured_fields(process, captured)
    if source is None:
        state["errors"].append("source CapturedImage read failed")
        return
    key = source["camera_key"]
    if key not in state["expected_keys"] or str(key) in state["packets"]:
        return
    if key in state["reserved_keys"] or thread_key in state["pending"]:
        return
    owner = source["capture_stack"]
    target_key = _unpack(process, owner + 0x44, "<i") if owner else None
    target = _target_fields(process, owner, target_key) if owner is not None else None
    descriptor = _descriptor(process, _u(frame, "rdi"))
    bytes_per_pixel = 16 if path == "vec4" else 4
    before = _image_bytes(process, descriptor, bytes_per_pixel) if descriptor else None
    scalar = _unpack(process, _u(frame, "rbp") - 0x30, "<f")
    correction = state["corrections"].get(str(key))
    if path == "mono" and correction is None:
        correction = {
            "applied": False,
            "source_key": key,
            "target_key": target_key,
            "gate_pair": source["relative_brightness_gate_pair"],
        }
    if (
        target is None
        or descriptor is None
        or before is None
        or scalar is None
        or correction is None
    ):
        state["errors"].append(f"key {key}: exposure packet capture failed")
        return
    pre_path = os.path.join(state["output_dir"], f"key_{key}_pre.bin")
    with open(pre_path, "wb") as output:
        output.write(before)
    state["reserved_keys"].append(key)
    state["pending"][thread_key] = {
        "key": key,
        "path": path,
        "source": source,
        "target": target,
        "target_key": target_key,
        "scalar": scalar,
        "scalar_bits": struct.unpack("<I", struct.pack("<f", scalar))[0],
        "relative_brightness_correction": correction,
        "descriptor_before": descriptor,
        "pre_path": pre_path,
        "pre_sha256": hashlib.sha256(before).hexdigest(),
        "logical_bytes": len(before),
        "bytes_per_pixel": bytes_per_pixel,
    }


def hit(frame, bp_loc, internal_dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    base = _base(process.GetTarget())
    site = frame.GetPC() - base if base is not None else None
    thread_key = str(thread.GetThreadID())
    if site == CORRECTION_VA:
        rbp = _u(frame, "rbp")
        return_address = _unpack(process, rbp + 0x8, "<Q")
        if base is None or return_address not in (
            base + HELPER_RETURN_VA,
            base + MONO_HELPER_RETURN_VA,
        ):
            return False
        source_key_address = _unpack(process, rbp - 0x88, "<Q")
        source_key = _unpack(process, source_key_address, "<i")
        target = _captured_fields(process, _u(frame, "r13"))
        source_brightness = _unpack(process, rbp - 0x70, "<f")
        target_record = _u(frame, "rax")
        target_brightness = _unpack(process, target_record + 0x38, "<f")
        if None in (source_key, target, source_brightness, target_brightness):
            state["errors"].append("relative-brightness correction capture failed")
            return False
        correction = {
            "applied": True,
            "source_key": source_key,
            "target_key": target["camera_key"],
            "source_relative_brightness": source_brightness,
            "target_relative_brightness": target_brightness,
            "source_relative_brightness_bits": struct.unpack(
                "<I", struct.pack("<f", source_brightness)
            )[0],
            "target_relative_brightness_bits": struct.unpack(
                "<I", struct.pack("<f", target_brightness)
            )[0],
        }
        previous = state["corrections"].get(str(source_key))
        if previous is not None and previous != correction:
            state["errors"].append(
                f"key {source_key}: conflicting relative-brightness correction"
            )
        state["corrections"][str(source_key)] = correction
        return False
    if site == BEFORE_VA:
        _reserve_packet(frame, process, state, thread_key, 0x28, "vec4")
        return False
    if site == MONO_BEFORE_VA:
        _reserve_packet(frame, process, state, thread_key, 0x20, "mono")
        return False
    if site == VECTOR_PRE_VA:
        pending = state["pending"].get(thread_key)
        if pending is None or "worker_vector" in pending:
            return False
        _disable(process, state, "vector_pre")
        helper_rbp = _u(frame, "rbp")
        return_address = _unpack(process, helper_rbp + 0x8, "<Q")
        if base is None or return_address != base + SCALE_RETURN_VA:
            return False
        source_address = _u(frame, "rdx") - 0x10
        destination_address = _u(frame, "rdi") - 0x10
        source_vector = _read(process, source_address, 0x10)
        if source_vector is None:
            state["errors"].append(f"key {pending['key']}: source vector read failed")
            return False
        pending["worker_vector"] = {
            "source_address": source_address,
            "destination_address": destination_address,
            "source_hex": source_vector.hex(),
        }
        _arm(process, state, "vector_post", thread.GetThreadID())
        return False
    if site == VECTOR_POST_VA:
        pending = state["pending"].get(thread_key)
        if pending is None or "worker_vector" not in pending:
            return False
        _disable(process, state, "vector_post")
        destination = _read(
            process, pending["worker_vector"]["destination_address"], 0x10
        )
        if destination is None:
            state["errors"].append(
                f"key {pending['key']}: destination vector read failed"
            )
            return False
        pending["worker_vector"]["destination_hex"] = destination.hex()
        return False
    if site == MONO_VECTOR_PRE_VA:
        pending = state["pending"].get(thread_key)
        if pending is None or pending.get("path") != "mono" or "worker_vector" in pending:
            return False
        _disable(process, state, "mono_vector_pre")
        helper_rbp = _u(frame, "rbp")
        return_address = _unpack(process, helper_rbp + 0x8, "<Q")
        if base is None or return_address != base + MONO_SCALE_RETURN_VA:
            return False
        index = _u(frame, "rcx")
        source_address = _u(frame, "rdi") - 0xC + index * 4
        destination_address = _u(frame, "r8") + _u(frame, "r10") - 0xC + index * 4
        source_value = _read(process, source_address, 4)
        if source_value is None:
            state["errors"].append(f"key {pending['key']}: mono source read failed")
            return False
        pending["worker_vector"] = {
            "source_address": source_address,
            "destination_address": destination_address,
            "source_hex": source_value.hex(),
        }
        _arm(process, state, "mono_vector_post", thread.GetThreadID())
        return False
    if site == MONO_VECTOR_POST_VA:
        pending = state["pending"].get(thread_key)
        if pending is None or pending.get("path") != "mono":
            return False
        _disable(process, state, "mono_vector_post")
        destination = _read(
            process, pending["worker_vector"]["destination_address"], 4
        )
        if destination is None:
            state["errors"].append(f"key {pending['key']}: mono destination read failed")
            return False
        pending["worker_vector"]["destination_hex"] = destination.hex()
        return False
    if site in (AFTER_VA, MONO_AFTER_VA):
        pending = state["pending"].pop(thread_key, None)
        if pending is None:
            return False
        key = pending["key"]
        descriptor = _descriptor(process, pending["descriptor_before"]["address"])
        after = (
            _image_bytes(process, descriptor, pending["bytes_per_pixel"])
            if descriptor
            else None
        )
        if after is None:
            state["errors"].append(f"key {key}: post-scale image read failed")
            return False
        post_path = os.path.join(state["output_dir"], f"key_{key}_post.bin")
        with open(post_path, "wb") as output:
            output.write(after)
        pending["descriptor_after"] = descriptor
        pending["post_path"] = post_path
        pending["post_sha256"] = hashlib.sha256(after).hexdigest()
        state["packets"][str(key)] = pending
        if sorted(int(value) for value in state["packets"]) == state["expected_keys"]:
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
        if site in (BEFORE_VA, AFTER_VA, MONO_BEFORE_VA, MONO_AFTER_VA, CORRECTION_VA):
            breakpoint.SetScriptCallbackFunction("create_stereo_exposure_scale_probe.hit")
            found.add(site)
    expected = {
        BEFORE_VA,
        AFTER_VA,
        MONO_BEFORE_VA,
        MONO_AFTER_VA,
        CORRECTION_VA,
    }
    if found != expected:
        _state()["errors"].append(f"missing sites {sorted(expected - found)}")
    print("CREATE_STEREO_EXPOSURE_ATTACHED", [hex(site) for site in sorted(found)])


def write_report(debugger, path):
    process = debugger.GetSelectedTarget().GetProcess()
    state = dict(_state())
    state["process"] = {"state": process.GetState(), "exit_status": process.GetExitStatus()}
    with open(path, "w", encoding="ascii") as output:
        json.dump(state, output, indent=2, sort_keys=True)
        output.write("\n")
    print("CREATE_STEREO_EXPOSURE_REPORT", path)
