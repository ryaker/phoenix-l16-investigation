"""Capture the public/runtime inputs and generated IR grid for cross-talk."""

import builtins
import hashlib
import json
import os
import struct


STAGE_ENTRY = 0x341B30
STAGE_CALL = 0x341D00
BUILDER_ENTRY = 0x102AB0
BUILDER_CONVERT = 0x102DB4
CALLBACK_ENTRY = 0x1054D0


def reset(label="", output_dir="", desired_camera_id=0):
    builtins.l16_crosstalk_ir_origin = {
        "label": label,
        "output_dir": output_dir,
        "desired_camera_id": desired_camera_id,
        "active_thread": None,
        "stage": None,
        "builder": None,
        "callback": None,
        "complete": False,
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_crosstalk_ir_origin"):
        reset()
    return builtins.l16_crosstalk_ir_origin


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
    if not address or size <= 0:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    return data if error.Success() and len(data) == size else None


def _u64(process, address):
    data = _read(process, address, 8)
    return struct.unpack("<Q", data)[0] if data is not None else None


def _xmm_f32(frame, name):
    data = frame.FindRegister(name).GetData()
    error = builtins.__import__("lldb").SBError()
    values = []
    for offset in range(0, 16, 4):
        value = data.GetFloat(error, offset) if data.IsValid() else None
        values.append(value if value is not None and error.Success() else None)
    return values


def _f32(process, address, count):
    data = _read(process, address, count * 4)
    return list(struct.unpack(f"<{count}f", data)) if data is not None else None


def _dump(process, address, size, name):
    state = _state()
    data = _read(process, address, size)
    if data is None:
        state["errors"].append(f"unable to read {name} at {address:#x} size={size}")
        return None
    path = os.path.join(state["output_dir"], name)
    with open(path, "wb") as handle:
        handle.write(data)
    return {"path": path, "bytes": size, "sha256": hashlib.sha256(data).hexdigest()}


def _descriptor(process, address):
    data = _read(process, address, 0x30)
    if data is None:
        return None
    words = struct.unpack("<8iQQ", data)
    result = {
        "address": address,
        "origin": list(words[0:2]),
        "bounds": list(words[2:4]),
        "size": list(words[4:6]),
        "stride": words[6],
        "reserved": words[7],
        "data": words[8],
        "allocation": words[9],
        "raw": data.hex(),
    }
    if not (
        0 < result["size"][0] <= 16384
        and 0 < result["size"][1] <= 16384
        and result["stride"] >= result["size"][0]
        and result["data"] > 0x10000
    ):
        return None
    return result


def _dump_descriptor(process, address, name):
    descriptor = _descriptor(process, address)
    if descriptor is None:
        _state()["errors"].append(f"invalid descriptor {name} at {address:#x}")
        return None
    size = descriptor["stride"] * descriptor["size"][1] * 16
    return {
        "descriptor": descriptor,
        "artifact": _dump(process, descriptor["data"], size, name),
    }


def _backtrace(thread, base):
    frames = []
    for index in range(min(thread.GetNumFrames(), 16)):
        frame = thread.GetFrameAtIndex(index)
        pc = frame.GetPC()
        module = str(frame.GetModule().GetFileSpec().GetFilename())
        frames.append({
            "index": index,
            "module": module,
            "pc": pc,
            "libcp_offset": pc - base if module == "libcp.dylib" else None,
            "function": frame.GetFunctionName(),
        })
    return frames


def hit(frame, _bp_loc, _internal_dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    base = _base(target)
    site = frame.GetPC() - base if base is not None else None
    thread_id = thread.GetThreadID()

    if state["complete"]:
        return False

    if site == STAGE_ENTRY:
        # The selected scalar Bayer route arrives with mode edx=1. Retain the
        # first large source payload and use its thread for the downstream join.
        if _u(frame, "rdx") != 1 or state["active_thread"] is not None:
            return False
        payload = _u(frame, "rsi")
        primary = _u64(process, payload)
        captured = _u64(process, payload + 8)
        raw = _read(process, payload, 0x110)
        if not primary or not captured or raw is None:
            return False
        camera_id_raw = _read(process, captured + 0x60, 4)
        if camera_id_raw is None:
            return False
        camera_id = struct.unpack("<i", camera_id_raw)[0]
        if camera_id != state["desired_camera_id"]:
            return False
        state["active_thread"] = thread_id
        state["stage"] = {
            "payload": payload,
            "primary": primary,
            "captured_image": captured,
            "payload_raw": raw.hex(),
            "primary_head": (_read(process, primary, 0x220) or b"").hex(),
            "captured_head": (_read(process, captured, 0x220) or b"").hex(),
            "primary_rgb_f32": _f32(process, primary, 4),
            "primary_0x1c8_f32": _f32(process, primary + 0x1C8, 1),
            "captured_camera_id_0x60": camera_id,
            "captured_sensor_type_0x100": struct.unpack(
                "<i", _read(process, captured + 0x100, 4)
            )[0],
            "captured_flag_a0_280": (
                (_read(process, (_u64(process, captured + 0xA0) or 0) + 0x280, 1) or b"\0")[0]
            ),
            "backtrace": _backtrace(thread, base),
        }
        return False

    if site == STAGE_CALL and thread_id == state["active_thread"]:
        state["stage"].update({
            "call_xmm0_f32": _xmm_f32(frame, "xmm0"),
            "call_awb_r8_f32": _f32(process, _u(frame, "r8"), 4),
            "call_limit_r9_f32": _f32(process, _u(frame, "r9"), 4),
            "call_captured_image": _u(frame, "rcx"),
        })
        return False

    if site == BUILDER_ENTRY and thread_id == state["active_thread"]:
        state["builder"] = {
            "selector_camera_id": struct.unpack(
                "<i", _read(process, _u(frame, "rsi"), 4)
            )[0],
            "width": _u(frame, "rdx") & 0xFFFFFFFF,
            "height": _u(frame, "rcx") & 0xFFFFFFFF,
            "sensor_type": _u(frame, "r8") & 0xFFFFFFFF,
            "variant_flag": _u(frame, "r9") & 0xFF,
            "amount_xmm0_f32": _xmm_f32(frame, "xmm0"),
            "backtrace": _backtrace(thread, base),
        }
        return False

    if (
        site == BUILDER_CONVERT
        and thread_id == state["active_thread"]
        and state["builder"] is not None
    ):
        rbp = _u(frame, "rbp")
        state["builder"]["rgb_surface"] = _dump_descriptor(
            process, rbp - 0xF0, "ir_rgb_surface_vec4_f32.bin"
        )
        state["builder"]["convert_xmm"] = {
            name: _xmm_f32(frame, name) for name in ("xmm0", "xmm1", "xmm2")
        }
        return False

    if (
        site == CALLBACK_ENTRY
        and thread_id == state["active_thread"]
        and state["builder"] is not None
        and state["builder"].get("rgb_surface") is not None
    ):
        callback = _u(frame, "rdi")
        owner_grid_object = _u64(process, callback + 0x28)
        owner_grid_data = (
            _u64(process, owner_grid_object + 8) if owner_grid_object else None
        )
        owner_grid_shape = (
            struct.unpack("<2i", _read(process, owner_grid_object, 8))
            if owner_grid_object
            else (0, 0)
        )
        grid_holder = _u64(process, callback + 0x30)
        grid_data = _u64(process, grid_holder) if grid_holder else None
        grid_shape = _u64(process, callback + 0x38)
        width = struct.unpack("<i", _read(process, grid_shape, 4))[0] if grid_shape else 0
        state["callback"] = {
            "object": callback,
            "awb_f32": _f32(process, _u64(process, callback + 0x20), 4),
            "owner_grid_shape": list(owner_grid_shape),
            "owner_grid_artifact": (
                _dump(
                    process,
                    owner_grid_data,
                    owner_grid_shape[0] * owner_grid_shape[1] * 0x40,
                    "owner_crosstalk_grid_f32.bin",
                )
                if owner_grid_data and owner_grid_shape == (17, 13)
                else None
            ),
            "grid_width": width,
            "grid_artifact": (
                _dump(process, grid_data, 17 * 13 * 0x40, "ir_diagonal_grid_f32.bin")
                if grid_data and width == 17
                else None
            ),
        }
        state["complete"] = True
        write_report(os.path.join(state["output_dir"], "report.json"))
        error = process.Kill()
        if not error.Success():
            state["errors"].append(f"kill after capture failed: {error.GetCString()}")
        return False

    return False


def install(debugger):
    target = debugger.GetSelectedTarget()
    base = _base(target)
    if base is None:
        raise RuntimeError("libcp.dylib is not loaded")
    for site in (STAGE_ENTRY, STAGE_CALL, BUILDER_ENTRY, BUILDER_CONVERT, CALLBACK_ENTRY):
        bp = target.BreakpointCreateByAddress(base + site)
        bp.SetScriptCallbackFunction("crosstalk_ir_origin_probe.hit")


def write_report(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="ascii") as handle:
        json.dump(_state(), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_CROSSTALK_IR_ORIGIN_REPORT", path)


def assert_complete():
    state = _state()
    if state["errors"] or not state["complete"]:
        raise RuntimeError(f"capture failed: complete={state['complete']} errors={state['errors']}")
    print("L16_CROSSTALK_IR_ORIGIN_OK", state["label"])
