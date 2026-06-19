import builtins
import json
import os
import struct


CALL_SITE = 0xE59A4
RETURN_SITE = 0xE59A9


def reset(label="", max_events=256):
    builtins.l16_f2770_origin = {
        "label": label,
        "max_events": max_events,
        "counts": {"pre": 0, "post": 0},
        "events": [],
        "pending": {},
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_f2770_origin"):
        reset()
    return builtins.l16_f2770_origin


def install_callbacks(debugger, ids):
    target = debugger.GetSelectedTarget()
    for name, callback in {
        "pre": "f2770_origin_probe.pre_call",
        "post": "f2770_origin_probe.post_call",
    }.items():
        bp_id = ids.get(name)
        if not bp_id:
            continue
        bp = target.FindBreakpointByID(bp_id)
        if bp and bp.IsValid():
            bp.SetScriptCallbackFunction(callback)


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


def _hex(data, off, size):
    if off + size > len(data):
        return None
    return data[off : off + size].hex()


def _f32_tuple(data, off, count):
    if off + 4 * count > len(data):
        return None
    return list(struct.unpack_from("<" + "f" * count, data, off))


def _u8(data, off):
    return data[off]


def _u16(data, off):
    return struct.unpack_from("<H", data, off)[0]


def _u32(data, off):
    return struct.unpack_from("<I", data, off)[0]


def _i32(data, off):
    return struct.unpack_from("<i", data, off)[0]


def _u64(data, off):
    return struct.unpack_from("<Q", data, off)[0]


def _f32(data, off):
    return struct.unpack_from("<f", data, off)[0]


def _libcp_base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                return base
    return None


def _module_va(target, pc):
    base = _libcp_base(target)
    if base is not None and pc >= base:
        return pc - base
    return None


def _stack(thread, max_frames=8):
    target = thread.GetProcess().GetTarget()
    frames = []
    for index in range(min(thread.GetNumFrames(), max_frames)):
        frame = thread.GetFrameAtIndex(index)
        frames.append(
            {
                "index": index,
                "pc": frame.GetPC(),
                "libcp_va": _module_va(target, frame.GetPC()),
                "function": frame.GetFunctionName(),
            }
        )
    return frames


def _input_fields(process, target, ptr):
    data = _read(process, ptr, 0x68)
    if data is None:
        return {"ptr": ptr, "read_ok": False}
    p20 = _u64(data, 0x20)
    p28 = _u64(data, 0x28)
    p40 = _u64(data, 0x40)
    nested20 = _nested_0x20(process, p20)
    optional28 = _optional_override(process, p28)
    return {
        "ptr": ptr,
        "read_ok": True,
        "u32_0x10_flags": _u32(data, 0x10),
        "ptr_0x20": p20,
        "ptr_0x28": p28,
        "u32_0x30": _u32(data, 0x30),
        "u32_0x34": _u32(data, 0x34),
        "u32_0x38": _u32(data, 0x38),
        "u32_0x3c": _u32(data, 0x3C),
        "ptr_0x40": p40,
        "u32_0x48": _u32(data, 0x48),
        "u16_0x4c": _u16(data, 0x4C),
        "byte_0x4c": _u8(data, 0x4C),
        "byte_0x4d": _u8(data, 0x4D),
        "u32_0x50": _u32(data, 0x50),
        "u32_0x54": _u32(data, 0x54),
        "byte_0x60": _u8(data, 0x60),
        "nested_0x20": nested20,
        "optional_0x28": optional28,
    }


def _nested_0x20(process, ptr):
    data = _read(process, ptr, 0x40)
    if data is None:
        return {"ptr": ptr, "read_ok": False}
    out = {
        "ptr": ptr,
        "read_ok": True,
        "ptr_0x18": _u64(data, 0x18),
        "ptr_0x20": _u64(data, 0x20),
        "ptr_0x28": _u64(data, 0x28),
        "u32_0x30": _u32(data, 0x30),
        "u32_0x34": _u32(data, 0x34),
        "u64_0x38": _u64(data, 0x38),
    }
    for name, child_ptr in (("child_0x18", out["ptr_0x18"]), ("child_0x20", out["ptr_0x20"]), ("child_0x28", out["ptr_0x28"])):
        child = _read(process, child_ptr, 0x20)
        if child is None:
            out[name] = {"ptr": child_ptr, "read_ok": False}
        else:
            out[name] = {
                "ptr": child_ptr,
                "read_ok": True,
                "u64_0x18": _u64(child, 0x18),
                "i32_0x18_lo": _i32(child, 0x18),
                "i32_0x1c_hi": _i32(child, 0x1C),
            }
    return out


def _optional_override(process, ptr):
    data = _read(process, ptr, 0x20)
    if data is None:
        return {"ptr": ptr, "read_ok": False}
    return {
        "ptr": ptr,
        "read_ok": True,
        "u64_0x18": _u64(data, 0x18),
        "i32_0x18_lo": _i32(data, 0x18),
        "i32_0x1c_hi": _i32(data, 0x1C),
    }


def _output_fields(process, target, ptr):
    data = _read(process, ptr, 0x1D4)
    if data is None:
        return {"ptr": ptr, "read_ok": False}
    vtable = _u64(data, 0)
    return {
        "ptr": ptr,
        "read_ok": True,
        "vtable_0x0": vtable,
        "vtable_libcp_va": _module_va(target, vtable),
        "byte_0x30": _u8(data, 0x30),
        "u32_0x40": _u32(data, 0x40),
        "byte_0x4c": _u8(data, 0x4C),
        "byte_0x4d": _u8(data, 0x4D),
        "u32_0x50": _u32(data, 0x50),
        "u32_0x54": _u32(data, 0x54),
        "i32_0x58": _i32(data, 0x58),
        "i32_0x5c": _i32(data, 0x5C),
        "u32_0x60": _u32(data, 0x60),
        "u32_0x64": _u32(data, 0x64),
        "u32_0x100": _u32(data, 0x100),
        "u32_0x104": _u32(data, 0x104),
        "byte_0x108": _u8(data, 0x108),
        "i32_0x10c": _i32(data, 0x10C),
        "i32_0x110": _i32(data, 0x110),
        "i32_0x114": _i32(data, 0x114),
        "i32_0x118": _i32(data, 0x118),
        "u32_0x11c": _u32(data, 0x11C),
        "u32_0x120": _u32(data, 0x120),
        "f32_0x124": _f32(data, 0x124),
        "f32_0x128": _f32(data, 0x128),
        "raw_0x10c_0x12c": _hex(data, 0x10C, 0x20),
        "stage1_0x12c_f32x8": _f32_tuple(data, 0x12C, 8),
        "stage1_raw_0x12c_0x14c": _hex(data, 0x12C, 0x20),
        "stage1_raw_0x150_0x170": _hex(data, 0x150, 0x20),
        "stage1_raw_0x12c_0x180": _hex(data, 0x12C, 0x54),
        "stage0_0x180_f32x8": _f32_tuple(data, 0x180, 8),
        "stage0_raw_0x180_0x1a0": _hex(data, 0x180, 0x20),
        "stage0_raw_0x1a4_0x1c4": _hex(data, 0x1A4, 0x20),
        "stage0_raw_0x180_0x1d4": _hex(data, 0x180, 0x54),
    }


def _key(frame):
    return "%s:%s" % (_u(frame, "rbp"), _u(frame, "rbx"))


def pre_call(frame, bp_loc, _dict):
    state = _state()
    state["counts"]["pre"] += 1
    if len(state["events"]) >= state["max_events"]:
        return False
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    rbp = _u(frame, "rbp")
    event = {
        "ordinal": state["counts"]["pre"],
        "site": "pre_call_0xe59a4",
        "rbp": rbp,
        "dst_item_ptr_rbx": _u(frame, "rbx"),
        "input_ptr_r14": _u(frame, "r14"),
        "third_arg_rdx": _u(frame, "rdx"),
        "loop_index_rbp_minus_0x2f0": _u64(_read(process, rbp - 0x2F0, 8), 0) if _read(process, rbp - 0x2F0, 8) else None,
        "owner_r13": _u(frame, "r13"),
        "input_fields": _input_fields(process, target, _u(frame, "r14")),
        "stack": _stack(frame.GetThread(), 8),
    }
    state["pending"][_key(frame)] = len(state["events"])
    state["events"].append(event)
    return False


def post_call(frame, bp_loc, _dict):
    state = _state()
    state["counts"]["post"] += 1
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    key = _key(frame)
    index = state["pending"].pop(key, None)
    out = _output_fields(process, target, _u(frame, "rbx"))
    if index is None or index >= len(state["events"]):
        if len(state["errors"]) < 32:
            state["errors"].append({"site": "post_call_0xe59a9", "reason": "no_pending_pre", "output_fields": out})
        return False
    state["events"][index]["post_site"] = "post_call_0xe59a9"
    state["events"][index]["output_fields"] = out
    return False


def report_to_file(path):
    state = _state()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)
    print("WROTE", path, "events", len(state["events"]), "counts", state["counts"])
