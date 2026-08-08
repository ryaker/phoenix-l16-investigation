"""Trace LELR record decoding and live ViewPreferences consumers."""

import builtins
import json
import struct


SITES = {
    0x13CDA3: "record_type_dispatch",
    0x13EDA0: "view_preferences_merge",
    0xE549E: "header_merge_record",
    0xE5F8C: "capture_stack_headers_merged",
    0x13F100: "ev_offset_accessor",
    0x13F110: "display_gain_accessor",
    0x13F120: "display_integration_accessor",
    0x13F130: "image_gain_accessor",
    0x13F140: "image_integration_accessor",
    0x13F150: "crop_accessor",
    0x13F160: "disable_cropping_accessor",
    0x13F170: "awb_gains_accessor",
    0x13F180: "orientation_accessor",
    0x13F190: "aspect_ratio_accessor",
    0xE7690: "gps_accessor",
    0xF3FC0: "exposure_normalization_entry",
    0xF40BC: "exposure_normalization_return",
    0xE6D90: "crop_policy_entry",
    0x3B2313: "crop_policy_return_3b230e",
    0x3CB593: "crop_policy_return_3cb58e",
}

ACCESSOR_LAYOUT = {
    0x13F100: ("ev_offset", "f32", 4),
    0x13F110: ("display_gain", "f32", 4),
    0x13F120: ("display_integration_time_ns", "u64", 8),
    0x13F130: ("image_gain", "f32", 4),
    0x13F140: ("image_integration_time_ns", "u64", 8),
    0x13F150: ("crop", "f32x4", 16),
    0x13F160: ("disable_cropping", "bool", 1),
    0x13F170: ("awb_gains_rgb", "f32x3", 12),
    0x13F180: ("orientation", "u32", 4),
    0x13F190: ("aspect_ratio", "u32", 4),
}


def reset(label=""):
    builtins.l16_lri_consumed_roles = {
        "label": label,
        "counts": {name: 0 for name in SITES.values()},
        "record_dispatches": [],
        "preference_merges": [],
        "merged_preferences": [],
        "accessor_samples": [],
        "exposure_normalization": [],
        "crop_policy": [],
        "pending_exposure": {},
        "pending_crop": {},
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_lri_consumed_roles"):
        reset()
    return builtins.l16_lri_consumed_roles


def _base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            value = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if value != 0xFFFFFFFFFFFFFFFF:
                return value
    return None


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    if error.Success() and len(data) == size:
        return data
    return None


def _scalar(process, address, kind):
    sizes = {"bool": 1, "u32": 4, "u64": 8, "f32": 4}
    raw = _read(process, address, sizes[kind])
    if raw is None:
        return None
    if kind == "bool":
        return bool(raw[0])
    if kind == "u32":
        return struct.unpack("<I", raw)[0]
    if kind == "u64":
        return struct.unpack("<Q", raw)[0]
    return struct.unpack("<f", raw)[0]


def _vector(process, address, count):
    raw = _read(process, address, count * 4)
    return list(struct.unpack("<" + "f" * count, raw)) if raw is not None else None


def _xmm0(frame):
    data = frame.FindRegister("xmm0").GetData()
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    value = data.GetFloat(error, 0) if data.IsValid() else None
    return value if error.Success() else None


def _optional(process, address, kind, present_offset):
    return {
        "present": _scalar(process, address + present_offset, "bool"),
        "value": _scalar(process, address, kind),
    }


def _preferences(process, address):
    return {
        "address": address,
        "f_number": _optional(process, address + 0x00, "f32", 0x04),
        "ev_offset": _optional(process, address + 0x08, "f32", 0x04),
        "disable_cropping": _optional(process, address + 0x10, "bool", 0x01),
        "awb_gains_rgb": {
            "present": _scalar(process, address + 0x20, "bool"),
            "value": _vector(process, address + 0x14, 3),
        },
        "awb_mode": _optional(process, address + 0x24, "u32", 0x04),
        "orientation": _optional(process, address + 0x2C, "u32", 0x04),
        "image_gain": _optional(process, address + 0x34, "f32", 0x04),
        "image_integration_time_ns": _optional(process, address + 0x40, "u64", 0x08),
        "display_gain": _optional(process, address + 0x50, "f32", 0x04),
        "display_integration_time_ns": _optional(process, address + 0x58, "u64", 0x08),
        "user_rating": _optional(process, address + 0x68, "u32", 0x04),
        "aspect_ratio": _optional(process, address + 0x70, "u32", 0x04),
        "crop": {
            "present": _scalar(process, address + 0x88, "bool"),
            "value": _vector(process, address + 0x78, 4),
        },
    }


def hit(frame, _bp_loc, _internal_dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    base = _base(process.GetTarget())
    va = frame.GetPC() - base if base is not None else None
    name = SITES.get(va, f"unknown_{va}")
    state["counts"][name] = state["counts"].get(name, 0) + 1
    thread_key = str(thread.GetThreadID())

    try:
        if va == 0x13CDA3 and len(state["record_dispatches"]) < 64:
            rbp = _u(frame, "rbp")
            state["record_dispatches"].append(
                {
                    "type": _u(frame, "rax") & 0xFF,
                    "message_size": _scalar(process, rbp - 0x10064, "u32"),
                }
            )
        elif va == 0x13EDA0 and len(state["preference_merges"]) < 16:
            source = _u(frame, "rsi")
            state["preference_merges"].append(
                {
                    "destination": _u(frame, "rdi"),
                    "source": source,
                    "source_has_bits": _scalar(process, source + 0x10, "u32"),
                }
            )
        elif va == 0xE549E:
            record_index = state["counts"][name] - 1
            if record_index < 32:
                record = _u(frame, "rbx")
                pointer_matches = []
                first_flash = struct.pack("<f", 314.7666320800781)
                for offset in range(0x18, 0x140, 8):
                    pointer = _scalar(process, record + offset, "u64")
                    if not pointer:
                        continue
                    candidate = _read(process, pointer, 0x80)
                    if candidate is not None and first_flash in candidate:
                        pointer_matches.append(
                            {
                                "record_offset": offset,
                                "pointer": pointer,
                                "first_flash_offset": candidate.find(first_flash),
                                "data_hex": candidate.hex(),
                            }
                        )
                state.setdefault("header_records", []).append(
                    {
                        "index": record_index,
                        "record": record,
                        "has_bits": _scalar(process, record + 0x10, "u32"),
                        "flash_pointer_matches": pointer_matches,
                    }
                )
        elif va == 0xE5F8C and len(state["merged_preferences"]) < 4:
            capture_stack = _u(frame, "r13")
            packet = _preferences(process, capture_stack + 0x78)
            raw = _read(process, capture_stack, 0x300)
            packet["capture_stack"] = capture_stack
            packet["capture_stack_0x300_hex"] = raw.hex() if raw is not None else None
            state["merged_preferences"].append(packet)
        elif va in ACCESSOR_LAYOUT:
            field, kind, size = ACCESSOR_LAYOUT[va]
            if state["counts"][name] <= 8:
                address = _u(frame, "rdi")
                present = _scalar(process, address + size, "bool")
                if kind == "f32x4":
                    value = _vector(process, address, 4)
                elif kind == "f32x3":
                    value = _vector(process, address, 3)
                else:
                    value = _scalar(process, address, kind)
                state["accessor_samples"].append(
                    {"field": field, "address": address, "present": present, "value": value}
                )
        elif va == 0xF3FC0:
            captured = _u(frame, "rdi")
            state["pending_exposure"].setdefault(thread_key, []).append(
                {
                    "captured_image": captured,
                    "sensor_exposure": _scalar(process, captured + 0x38, "u64"),
                    "sensor_analog_gain": _scalar(process, captured + 0x40, "f32"),
                }
            )
        elif va == 0xF40BC:
            pending = state["pending_exposure"].get(thread_key, [])
            item = pending.pop() if pending else {}
            if not pending:
                state["pending_exposure"].pop(thread_key, None)
            item["result"] = _xmm0(frame)
            if len(state["exposure_normalization"]) < 128:
                state["exposure_normalization"].append(item)
        elif va == 0xE6D90:
            state["pending_crop"].setdefault(thread_key, []).append(
                {"output": _u(frame, "rdi"), "capture_stack": _u(frame, "rsi")}
            )
        elif va in (0x3B2313, 0x3CB593):
            pending = state["pending_crop"].get(thread_key, [])
            item = pending.pop() if pending else {}
            if not pending:
                state["pending_crop"].pop(thread_key, None)
            item["return_site"] = va
            item["result"] = _vector(process, item.get("output", 0), 4)
            if len(state["crop_policy"]) < 16:
                state["crop_policy"].append(item)
    except Exception as exc:
        state["errors"].append({"site": name, "error": repr(exc)})
    return False


def install(debugger):
    target = debugger.GetSelectedTarget()
    base = _base(target)
    if base is None:
        raise RuntimeError("libcp.dylib is not loaded")
    for va in SITES:
        bp = target.BreakpointCreateByAddress(base + va)
        bp.SetScriptCallbackFunction("lri_consumed_block_roles_probe.hit")
    print("L16_LRI_CONSUMED_BLOCK_ROLES_INSTALLED", len(SITES))


def write_report(path):
    state = _state()
    state["pending_exposure"] = {}
    state["pending_crop"] = {}
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_LRI_CONSUMED_BLOCK_ROLES_REPORT", path)
