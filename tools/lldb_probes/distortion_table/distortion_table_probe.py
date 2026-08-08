import builtins
import hashlib
import json
import struct


SAMPLE_SCALE_SITE = 0x145738
PRE_TABLE_SITE = 0x144CB4
POST_TABLE_SITE = 0x144DE3


def reset(label=""):
    builtins.l16_distortion_table = {
        "label": label,
        "sample_scale": None,
        "pre": None,
        "post": None,
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_distortion_table"):
        reset()
    return builtins.l16_distortion_table


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    import lldb

    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    if not error.Success() or len(data) != size:
        _state()["errors"].append(
            f"read failed address=0x{address:x} size={size}: {error}"
        )
        return None
    return data


def _u64(process, address):
    data = _read(process, address, 8)
    return struct.unpack("<Q", data)[0] if data else None


def _i32(process, address):
    data = _read(process, address, 4)
    return struct.unpack("<i", data)[0] if data else None


def _f32(process, address):
    data = _read(process, address, 4)
    return struct.unpack("<f", data)[0] if data else None


def _raw_state(process, address, size):
    data = _read(process, address, size)
    if data is None:
        return None
    return {
        "address": address,
        "size": size,
        "raw_hex": data.hex(),
        "u32": list(struct.unpack("<" + "I" * (size // 4), data)),
        "f32": list(struct.unpack("<" + "f" * (size // 4), data)),
    }


def _vector(process, address):
    header = _read(process, address, 24)
    if header is None:
        return None
    begin, end, capacity = struct.unpack("<QQQ", header)
    if end < begin or end - begin > 0x10000 or (end - begin) % 4:
        return {
            "begin": begin,
            "end": end,
            "capacity": capacity,
            "error": "invalid vector extent",
        }
    raw = _read(process, begin, end - begin) if end > begin else b""
    return {
        "begin": begin,
        "end": end,
        "capacity": capacity,
        "count": (end - begin) // 4,
        "values": list(struct.unpack("<" + "f" * ((end - begin) // 4), raw))
        if raw is not None
        else None,
    }


def _table(process, pointer):
    raw = _read(process, pointer, 4096 * 4) if pointer else None
    if raw is None:
        return None
    return {
        "pointer": pointer,
        "count": 4096,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "raw_hex": raw.hex(),
        "values": list(struct.unpack("<4096f", raw)),
    }


def sample_scale_hit(frame, _bp_loc, _extra_args, _internal_dict):
    state = _state()
    if state["sample_scale"] is not None:
        return False
    process = frame.GetThread().GetProcess()
    rbp = _u(frame, "rbp")
    obj = _u(frame, "r13")
    state["sample_scale"] = {
        "thread_id": frame.GetThread().GetThreadID(),
        "object": obj,
        "camera_key_object_0x60": _i32(process, obj + 0x60),
        "forward_scale_rbp_minus_13c": _f32(process, rbp - 0x13C),
        "inverse_scale_rbp_minus_140": _f32(process, rbp - 0x140),
        "interpolator_state_rbp_minus_128": _raw_state(
            process, rbp - 0x128, 0xA0
        ),
    }
    return False


def pre_hit(frame, _bp_loc, _extra_args, _internal_dict):
    state = _state()
    if state["pre"] is not None:
        return False
    process = frame.GetThread().GetProcess()
    rbp = _u(frame, "rbp")
    obj = _u(frame, "r15")
    output_vector = _u64(process, _u(frame, "r14"))
    state["pre"] = {
        "thread_id": frame.GetThread().GetThreadID(),
        "rbp": rbp,
        "object": obj,
        "camera_key_object_0x60": _i32(process, obj + 0x60),
        "table_scalar_rbp_minus_b4": _f32(process, rbp - 0xB4),
        "distorted_radius_samples_rbp_minus_70": _vector(
            process, rbp - 0x70
        ),
        "uniform_radius_samples_rbp_minus_58": _vector(
            process, rbp - 0x58
        ),
        "output_table_pointer": output_vector,
    }
    return False


def post_hit(frame, _bp_loc, _extra_args, _internal_dict):
    state = _state()
    pre = state["pre"]
    if pre is None or state["post"] is not None:
        return False
    if frame.GetThread().GetThreadID() != pre["thread_id"]:
        return False
    process = frame.GetThread().GetProcess()
    pointer = _u64(process, _u(frame, "r14"))
    if pointer != pre["output_table_pointer"]:
        return False
    state["post"] = {
        "thread_id": frame.GetThread().GetThreadID(),
        "table": _table(process, pointer),
    }
    process.Kill()
    return False


def attach_existing(debugger):
    target = debugger.GetSelectedTarget()
    count = target.GetNumBreakpoints()
    if count < 3:
        _state()["errors"].append("expected three existing breakpoints")
        return
    sample = target.GetBreakpointAtIndex(count - 3)
    pre = target.GetBreakpointAtIndex(count - 2)
    post = target.GetBreakpointAtIndex(count - 1)
    sample.SetScriptCallbackFunction("distortion_table_probe.sample_scale_hit")
    pre.SetScriptCallbackFunction("distortion_table_probe.pre_hit")
    post.SetScriptCallbackFunction("distortion_table_probe.post_hit")
    print(
        f"DISTORTION_TABLE attached sample={sample.GetID()} "
        f"pre={pre.GetID()} post={post.GetID()}"
    )


def drive(debugger, max_steps=512):
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process.IsValid() and process.GetState() == 5 and steps < max_steps:
        if _state()["post"] is not None:
            process.Kill()
            break
        process.Continue()
        steps += 1
    print(f"DISTORTION_TABLE drive_steps={steps}")


def write_report(path):
    with open(path, "w") as handle:
        json.dump(_state(), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"DISTORTION_TABLE wrote {path}")
