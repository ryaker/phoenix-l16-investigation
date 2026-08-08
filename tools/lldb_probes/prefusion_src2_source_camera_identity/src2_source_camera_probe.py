import builtins
import json
import struct


KEY_READY = 0x406B48
LOOKUP_READY = 0x406B5E
VISIBLE_SRC2_RETURN = 0x3EBF5F


def reset(label=""):
    builtins.l16_src2_source_camera = {
        "label": label,
        "key_hits": 0,
        "lookup_hits": 0,
        "accepted": [],
        "pending": {},
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_src2_source_camera"):
        reset()
    return builtins.l16_src2_source_camera


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    if not addr:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u32(data, offset=0):
    return struct.unpack_from("<I", data, offset)[0]


def _u64(data, offset=0):
    return struct.unpack_from("<Q", data, offset)[0]


def _libcp_base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                return base
    return None


def _module_va(target, address):
    base = _libcp_base(target)
    if base is not None and address >= base:
        return address - base
    return None


def _saved_return_va(frame):
    process = frame.GetThread().GetProcess()
    raw = _read(process, _u(frame, "rbp") + 8, 8)
    if raw is None:
        return None
    return _module_va(process.GetTarget(), _u64(raw))


def _ptr(process, address):
    raw = _read(process, address, 8)
    return _u64(raw) if raw is not None else None


def install_callbacks(debugger, key_id, lookup_id):
    target = debugger.GetSelectedTarget()
    key_bp = target.FindBreakpointByID(key_id)
    lookup_bp = target.FindBreakpointByID(lookup_id)
    key_bp.SetScriptCallbackFunction("src2_source_camera_probe.key_ready")
    lookup_bp.SetScriptCallbackFunction("src2_source_camera_probe.lookup_ready")


def key_ready(frame, bp_loc, internal_dict):
    state = _state()
    state["key_hits"] += 1
    if _saved_return_va(frame) != VISIBLE_SRC2_RETURN:
        return False
    thread = frame.GetThread()
    process = thread.GetProcess()
    obj = _u(frame, "r15")
    key = _u(frame, "rax") & 0xFFFFFFFF
    factory = _ptr(process, obj + 0x8)
    state["pending"][str(thread.GetThreadID())] = {
        "key": key,
        "fusion_cache_bayer": obj,
        "raw_image_factory": factory,
        "flag_0x18": (_read(process, obj + 0x18, 1) or b"\0")[0],
    }
    return False


def lookup_ready(frame, bp_loc, internal_dict):
    state = _state()
    state["lookup_hits"] += 1
    if _saved_return_va(frame) != VISIBLE_SRC2_RETURN:
        return False
    thread = frame.GetThread()
    pending = state["pending"].pop(str(thread.GetThreadID()), None)
    if pending is None:
        return False

    process = thread.GetProcess()
    target = process.GetTarget()
    rbp = _u(frame, "rbp")
    shared = _read(process, rbp - 0x100, 16)
    if shared is None:
        state["errors"].append("cannot read lookup shared_ptr")
        return True
    captured = _u64(shared, 0)
    control = _u64(shared, 8)
    object_raw = _read(process, captured, 0x68)
    control_vptr = _ptr(process, control)
    pending.update(
        {
            "captured_image": captured,
            "shared_control": control,
            "control_vptr": control_vptr,
            "control_vptr_va": _module_va(target, control_vptr) if control_vptr else None,
            "captured_camera_id_0x60": _u32(object_raw, 0x60) if object_raw else None,
            "captured_active_0x30": object_raw[0x30] if object_raw else None,
        }
    )
    state["accepted"].append(pending)
    return True


def report():
    state = _state()
    print("L16_SRC2_SOURCE_CAMERA_BEGIN " + state["label"])
    print(json.dumps(state, sort_keys=True))
    print("L16_SRC2_SOURCE_CAMERA_END " + state["label"])
