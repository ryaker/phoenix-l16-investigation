import builtins
import hashlib
import json
import os
import struct


BEFORE_VA = 0x27BC40
AFTER_VA = 0x27BC45


def reset(label, output_dir, source_lri):
    builtins.l16_create_stereo_mono_replication = {
        "label": label,
        "output_dir": output_dir,
        "source_lri": source_lri,
        "packet": None,
        "pending": {},
        "errors": [],
        "terminated_after_capture": False,
    }


def _state():
    if not hasattr(builtins, "l16_create_stereo_mono_replication"):
        reset("", "", "")
    return builtins.l16_create_stereo_mono_replication


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    if not address or size <= 0:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    raw = process.ReadMemory(address, size, error)
    return raw if error.Success() and len(raw) == size else None


def _unpack(process, address, fmt):
    raw = _read(process, address, struct.calcsize(fmt))
    return struct.unpack(fmt, raw)[0] if raw is not None else None


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
        "data": words[8],
        "allocation": words[9],
        "raw": raw.hex(),
    }


def _image_bytes(process, descriptor, bytes_per_pixel):
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


def hit(frame, bp_loc, internal_dict):
    state = _state()
    if state["packet"] is not None:
        return False
    thread = frame.GetThread()
    process = thread.GetProcess()
    base = _base(process.GetTarget())
    site = frame.GetPC() - base if base is not None else None
    thread_key = str(thread.GetThreadID())
    if site == BEFORE_VA:
        captured = _u(frame, "r14")
        camera_key = _unpack(process, captured + 0x60, "<i")
        source_descriptor = _descriptor(process, _u(frame, "rsi"))
        output_address = _u(frame, "rdi")
        source = (
            _image_bytes(process, source_descriptor, 4)
            if source_descriptor is not None
            else None
        )
        if camera_key != 1 or source is None:
            state["errors"].append(
                f"unexpected mono conversion input key={camera_key}"
            )
            return False
        source_path = os.path.join(state["output_dir"], "source_f32.bin")
        with open(source_path, "wb") as output:
            output.write(source)
        state["pending"][thread_key] = {
            "camera_key": camera_key,
            "source_descriptor": source_descriptor,
            "output_descriptor_address": output_address,
            "source_path": source_path,
            "source_sha256": hashlib.sha256(source).hexdigest(),
        }
        return False
    if site == AFTER_VA:
        pending = state["pending"].pop(thread_key, None)
        if pending is None:
            return False
        output_descriptor = _descriptor(
            process, pending["output_descriptor_address"]
        )
        output = (
            _image_bytes(process, output_descriptor, 16)
            if output_descriptor is not None
            else None
        )
        if output is None:
            state["errors"].append("mono vec4 output capture failed")
            return False
        output_path = os.path.join(state["output_dir"], "output_vec4f.bin")
        with open(output_path, "wb") as destination:
            destination.write(output)
        pending["output_descriptor"] = output_descriptor
        pending["output_path"] = output_path
        pending["output_sha256"] = hashlib.sha256(output).hexdigest()
        state["packet"] = pending
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
        if site in (BEFORE_VA, AFTER_VA):
            breakpoint.SetScriptCallbackFunction(
                "create_stereo_mono_replication_probe.hit"
            )
            found.add(site)
    expected = {BEFORE_VA, AFTER_VA}
    if found != expected:
        _state()["errors"].append(f"missing sites {sorted(expected - found)}")
    print("CREATE_STEREO_MONO_REPLICATION_ATTACHED", [hex(x) for x in sorted(found)])


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
    print("CREATE_STEREO_MONO_REPLICATION_REPORT", path)
