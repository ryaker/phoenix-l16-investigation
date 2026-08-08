import builtins
import json
import os
import struct


CAMERA_KEY_COMPARE_VA = 0x3F5035
CREATE_STEREO_ENTRY_VA = 0x27B7A0
GRBG_COLLAPSE_WORKER_VA = 0xA50D0
SHARPEN_ENTRY_VA = 0x3589C0
SHARPEN_RETURN_VA = 0x358FCE
VEC4_LENS_WORKER_VA = 0x108080


def reset(label, output_dir, wanted_key=0):
    builtins.l16_guidance_sharpen_join = {
        "label": label,
        "output_dir": output_dir,
        "wanted_key": int(wanted_key),
        "last_key_by_thread": {},
        "selected_thread": None,
        "entry": None,
        "collapse": [],
        "sharpen": None,
        "lens_candidates": [],
        "lens_match": None,
        "terminated_after_match": False,
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_guidance_sharpen_join"):
        reset("", "")
    return builtins.l16_guidance_sharpen_join


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    if not address or size <= 0:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    raw = process.ReadMemory(address, size, error)
    return raw if error.Success() and len(raw) == size else None


def _u64(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<Q", raw)[0] if raw is not None else None


def _f32s(process, address, count):
    raw = _read(process, address, count * 4)
    return list(struct.unpack("<" + "f" * count, raw)) if raw is not None else None


def _xmm(frame, name):
    try:
        lldb = builtins.__import__("lldb")
        data = frame.FindRegister(name).GetData()
        error = lldb.SBError()
        raw = bytes(data.GetUnsignedInt8(error, index) for index in range(data.GetByteSize()))
        if error.Success() and len(raw) >= 16:
            return list(struct.unpack_from("<4f", raw))
    except Exception as exc:
        _state()["errors"].append(f"{name}: {exc}")
    return None


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


def _stack(frame, cap=10):
    base = _base(frame.GetThread().GetProcess().GetTarget())
    out = []
    thread = frame.GetThread()
    for index in range(min(cap, thread.GetNumFrames())):
        item = thread.GetFrameAtIndex(index)
        pc = item.GetPC()
        out.append({
            "pc": pc,
            "libcp_va": pc - base if base is not None and pc >= base else None,
            "function": item.GetFunctionName(),
        })
    return out


def _allocation_set(state):
    values = set()
    for item in state["collapse"]:
        for descriptor_name in ("input_descriptor", "output_descriptor"):
            descriptor = item.get(descriptor_name)
            if descriptor and descriptor.get("allocation"):
                values.add(descriptor["allocation"])
    if state["sharpen"]:
        for phase in ("entry", "return"):
            record = state["sharpen"].get(phase) or {}
            for descriptor_name in (
                "descriptor_0x20",
                "descriptor_0x70",
                "descriptor_0xa0",
            ):
                descriptor = record.get(descriptor_name)
                if descriptor and descriptor.get("allocation"):
                    values.add(descriptor["allocation"])
    return values


def hit(frame, bp_loc, internal_dict):
    state = _state()
    thread = frame.GetThread()
    thread_id = thread.GetThreadID()
    process = thread.GetProcess()
    base = _base(process.GetTarget())
    site = frame.GetPC() - base if base is not None else None

    if site == CAMERA_KEY_COMPARE_VA:
        state["last_key_by_thread"][str(thread_id)] = _u(frame, "rsi") & 0xFFFFFFFF
        return False

    if site == CREATE_STEREO_ENTRY_VA:
        key = state["last_key_by_thread"].get(str(thread_id))
        if state["selected_thread"] is None and key == state["wanted_key"]:
            state["selected_thread"] = thread_id
            state["entry"] = {
                "thread_id": thread_id,
                "source_key": key,
                "input_u16_descriptor": _descriptor(process, _u(frame, "rsi")),
                "stack": _stack(frame),
            }
        return False

    if state["entry"] is None:
        return False

    if site == GRBG_COLLAPSE_WORKER_VA:
        closure = _u(frame, "rdi")
        input_descriptor = _descriptor(process, _u64(process, closure + 0x08))
        output_descriptor = _descriptor(process, _u64(process, closure + 0x10))
        rectangle_raw = _read(process, _u(frame, "rsi"), 16)
        identity = (
            input_descriptor["allocation"] if input_descriptor else None,
            output_descriptor["allocation"] if output_descriptor else None,
        )
        if not any(item["identity"] == identity for item in state["collapse"]):
            state["collapse"].append({
                "identity": identity,
                "thread_id": thread_id,
                "closure": closure,
                "rectangle": list(struct.unpack("<4i", rectangle_raw)) if rectangle_raw else None,
                "input_descriptor": input_descriptor,
                "output_descriptor": output_descriptor,
            })
        return False

    if site == SHARPEN_ENTRY_VA:
        if thread_id != state["selected_thread"] or state["sharpen"] is not None:
            return False
        obj = _u(frame, "rdi")
        config = _u(frame, "rsi")
        state["sharpen"] = {
            "object": obj,
            "config_ptr": config,
            "config_f32": _f32s(process, config, 5),
            "saturation_xmm0": (_xmm(frame, "xmm0") or [None])[0],
            "vibrance_xmm1": (_xmm(frame, "xmm1") or [None])[0],
            "entry": {
                "descriptor_0x20": _descriptor(process, obj + 0x20),
                "descriptor_0x70": _descriptor(process, obj + 0x70),
                "descriptor_0xa0": _descriptor(process, obj + 0xA0),
                "object_raw_0x00_0xcf": (_read(process, obj, 0xD0) or b"").hex(),
                "stack": _stack(frame),
            },
            "return": None,
        }
        return False

    if site == SHARPEN_RETURN_VA:
        if thread_id != state["selected_thread"] or state["sharpen"] is None:
            return False
        obj = state["sharpen"]["object"]
        state["sharpen"]["return"] = {
            "descriptor_0x20": _descriptor(process, obj + 0x20),
            "descriptor_0x70": _descriptor(process, obj + 0x70),
            "descriptor_0xa0": _descriptor(process, obj + 0xA0),
            "object_raw_0x00_0xcf": (_read(process, obj, 0xD0) or b"").hex(),
        }
        return False

    if site == VEC4_LENS_WORKER_VA:
        closure = _u(frame, "rdi")
        source_descriptor = _descriptor(process, _u64(process, closure + 0x40))
        destination_descriptor = _descriptor(process, _u64(process, closure + 0x38))
        rectangle_raw = _read(process, _u(frame, "rsi"), 16)
        item = {
            "thread_id": thread_id,
            "closure": closure,
            "rectangle": list(struct.unpack("<4i", rectangle_raw)) if rectangle_raw else None,
            "spacing": _f32s(process, _u64(process, closure + 0x08), 2),
            "tile_shape": (
                list(struct.unpack("<2i", _read(process, _u64(process, closure + 0x10), 8)))
                if _read(process, _u64(process, closure + 0x10), 8) is not None
                else None
            ),
            "global_offset": (
                list(struct.unpack("<2i", _read(process, _u64(process, closure + 0x18), 8)))
                if _read(process, _u64(process, closure + 0x18), 8) is not None
                else None
            ),
            "source_descriptor": source_descriptor,
            "destination_descriptor": destination_descriptor,
            "stack": _stack(frame),
        }
        known = _allocation_set(state)
        observed = {
            descriptor["allocation"]
            for descriptor in (source_descriptor, destination_descriptor)
            if descriptor and descriptor.get("allocation")
        }
        item["matching_allocations"] = sorted(known & observed)
        if len(state["lens_candidates"]) < 64:
            state["lens_candidates"].append(item)
        if item["matching_allocations"] and state["sharpen"] and state["sharpen"]["return"]:
            state["lens_match"] = item
            error = process.Kill()
            state["terminated_after_match"] = error.Success()
            if not error.Success():
                state["errors"].append(f"kill failed: {error.GetCString()}")
        return False

    return False


def attach(debugger):
    os.makedirs(_state()["output_dir"], exist_ok=True)
    target = debugger.GetSelectedTarget()
    expected = {
        CAMERA_KEY_COMPARE_VA,
        CREATE_STEREO_ENTRY_VA,
        GRBG_COLLAPSE_WORKER_VA,
        SHARPEN_ENTRY_VA,
        SHARPEN_RETURN_VA,
        VEC4_LENS_WORKER_VA,
    }
    found = set()
    for index in range(target.GetNumBreakpoints()):
        breakpoint = target.GetBreakpointAtIndex(index)
        if not breakpoint or not breakpoint.IsValid() or breakpoint.GetNumLocations() < 1:
            continue
        site = breakpoint.GetLocationAtIndex(0).GetAddress().GetFileAddress()
        if site in expected:
            breakpoint.SetScriptCallbackFunction("guidance_sharpen_join_probe.hit")
            found.add(site)
    if found != expected:
        _state()["errors"].append(f"missing sites {sorted(expected - found)}")
    print("GUIDANCE_SHARPEN_JOIN_ATTACHED", [hex(site) for site in sorted(found)])


def write_report(debugger, path):
    process = debugger.GetSelectedTarget().GetProcess()
    state = dict(_state())
    state["process"] = {
        "state": process.GetState() if process and process.IsValid() else None,
        "exit_status": process.GetExitStatus() if process and process.IsValid() else None,
    }
    with open(path, "w", encoding="ascii") as output:
        json.dump(state, output, indent=2, sort_keys=True)
        output.write("\n")
    print("GUIDANCE_SHARPEN_JOIN_REPORT", path)
