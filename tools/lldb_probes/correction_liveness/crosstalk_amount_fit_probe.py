"""Capture the live image-to-IR-table fit that produces object+0x1c8."""

import builtins
import hashlib
import json
import os
import struct


PRODUCER_PRE_CCT = 0x33E91E
PRODUCER_POST_CCT = 0x33E92E
PRODUCER_PRE_FIT = 0x33E9E1
PRODUCER_STORE = 0x33E9E6
NORMALIZE_ENTRY = 0xFCF90
FIT_ENTRY = 0xFD940
FIT_CANDIDATE_SCORE = 0xFDD04
FIT_CANDIDATE_DONE = 0xFDD36
FIT_C_COMPARE = 0xFDFC4
FIT_RETURN = 0xFE007


def reset(label="", output_dir="", desired_camera_id=0):
    builtins.l16_crosstalk_amount_fit = {
        "label": label,
        "output_dir": output_dir,
        "desired_camera_id": desired_camera_id,
        "active_thread": None,
        "producer": None,
        "fit": None,
        "complete": False,
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_crosstalk_amount_fit"):
        reset()
    return builtins.l16_crosstalk_amount_fit


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


def _i32(process, address):
    data = _read(process, address, 4)
    return struct.unpack("<i", data)[0] if data is not None else None


def _f32(process, address, count=1):
    data = _read(process, address, count * 4)
    return list(struct.unpack(f"<{count}f", data)) if data is not None else None


def _xmm_f32(frame, name):
    data = frame.FindRegister(name).GetData()
    error = builtins.__import__("lldb").SBError()
    result = []
    for offset in range(0, 16, 4):
        value = data.GetFloat(error, offset) if data.IsValid() else None
        result.append(value if value is not None and error.Success() else None)
    return result


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


def _dump_descriptor(process, address, name, element_bytes=16):
    descriptor = _descriptor(process, address)
    if descriptor is None:
        _state()["errors"].append(f"invalid descriptor {name} at {address:#x}")
        return None
    size = descriptor["stride"] * descriptor["size"][1] * element_bytes
    data = _read(process, descriptor["data"], size)
    if data is None:
        _state()["errors"].append(f"unable to dump {name} at {descriptor['data']:#x}")
        return None
    path = os.path.join(_state()["output_dir"], name)
    with open(path, "wb") as handle:
        handle.write(data)
    return {
        "descriptor": descriptor,
        "artifact": {
            "path": path,
            "bytes": size,
            "sha256": hashlib.sha256(data).hexdigest(),
        },
    }


def _u64_vector(process, address, name):
    raw = _read(process, address, 0x18)
    if raw is None:
        return None
    begin, end, capacity = struct.unpack("<QQQ", raw)
    count = (end - begin) // 8 if begin and end >= begin else -1
    result = {
        "address": address,
        "begin": begin,
        "end": end,
        "capacity": capacity,
        "count": count,
        "raw": raw.hex(),
        "artifact": None,
    }
    if count <= 0:
        return result
    data = _read(process, begin, count * 8)
    if data is None:
        _state()["errors"].append(f"unable to dump {name} at {begin:#x}")
        return result
    path = os.path.join(_state()["output_dir"], name)
    with open(path, "wb") as handle:
        handle.write(data)
    result["artifact"] = {
        "path": path,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }
    return result


def _dump_nested_u64_vectors(process, address):
    raw = _read(process, address, 0x18)
    if raw is None:
        return None
    begin, end, capacity = struct.unpack("<QQQ", raw)
    count = (end - begin) // 0x18 if begin and end >= begin else -1
    result = {
        "address": address,
        "begin": begin,
        "end": end,
        "capacity": capacity,
        "count": count,
        "raw": raw.hex(),
        "vectors": [],
    }
    if count <= 0:
        return result
    for index in range(count):
        result["vectors"].append(
            _u64_vector(
                process,
                begin + index * 0x18,
                f"histogram_{index}_u64.bin",
            )
        )
    return result


def hit(frame, _bp_loc, _internal_dict):
    state = _state()
    if state["complete"]:
        return False
    thread = frame.GetThread()
    process = thread.GetProcess()
    base = _base(process.GetTarget())
    site = frame.GetPC() - base if base is not None else None
    thread_id = thread.GetThreadID()

    if site == PRODUCER_PRE_CCT:
        captured = _u(frame, "r14")
        camera_id = _i32(process, captured + 0x60)
        if camera_id != state["desired_camera_id"] or state["active_thread"] is not None:
            return False
        primary = _u(frame, "rbx")
        state["active_thread"] = thread_id
        state["producer"] = {
            "primary": primary,
            "captured_image": captured,
            "camera_id": camera_id,
            "chromaticity_xy_primary_0xc": _f32(process, primary + 0xC, 2),
            "sensor_exposure_0x38_u64": _u64(process, captured + 0x38),
            "sensor_analog_gain_0x40_f32": _f32(process, captured + 0x40, 1),
            "sensor_type_0xa8": _i32(process, captured + 0xA8),
            "captured_field_0x100": _i32(process, captured + 0x100),
            "bayer_override_0x58": [_i32(process, captured + 0x58), _i32(process, captured + 0x5C)],
            "dimensions": [_i32(process, captured + 0x10), _i32(process, captured + 0x14)],
            "black_white_0xac": _f32(process, captured + 0xAC, 2),
            "histograms_0x1d8": _dump_nested_u64_vectors(process, captured + 0x1D8),
        }
        return False

    if thread_id != state["active_thread"]:
        return False

    if site == PRODUCER_POST_CCT:
        rbp = _u(frame, "rbp")
        state["producer"]["xy_to_cct_tint"] = _f32(process, rbp - 0x1C8, 2)
        return False

    if site == PRODUCER_PRE_FIT:
        rbp = _u(frame, "rbp")
        state["producer"].update({
            "fit_cct_xmm0": _xmm_f32(frame, "xmm0"),
            "fit_exposure_energy_xmm1": _xmm_f32(frame, "xmm1"),
            "fit_rect": [_i32(process, rbp - 0x1D8 + i * 4) for i in range(4)],
        })
        return False

    if site == FIT_ENTRY:
        state["fit"] = {
            "input_image": _dump_descriptor(process, _u(frame, "rdi"), "fit_input_vec4_f32.bin"),
            "camera_group_selector": _u(frame, "rsi") & 0xFFFFFFFF,
            "sensor_type": _u(frame, "rdx") & 0xFFFFFFFF,
            "variant_flag": _u(frame, "rcx") & 0xFF,
            "cct_xmm0": _xmm_f32(frame, "xmm0"),
            "exposure_energy_xmm1": _xmm_f32(frame, "xmm1"),
            "candidates": [],
            "c_table": None,
        }
        return False

    if site == NORMALIZE_ENTRY:
        state["normalize"] = {
            "numerator_image": _dump_descriptor(
                process, _u(frame, "rsi"), "fit_numerator_f32.bin", 4
            ),
            "denominator_image": _dump_descriptor(
                process, _u(frame, "rdx"), "fit_denominator_f32.bin", 4
            ),
            "selector_ecx": _u(frame, "rcx") & 0xFFFFFFFF,
            "selector_r8d": _u(frame, "r8") & 0xFFFFFFFF,
        }
        return False

    if site == FIT_CANDIDATE_SCORE and state["fit"] is not None:
        rbp = _u(frame, "rbp")
        state["fit"]["candidates"].append({
            "index": _u(frame, "rbx") & 0xFFFFFFFF,
            "amount": (_f32(process, rbp - 0x240, 1) or [None])[0],
            "score": (_xmm_f32(frame, "xmm0") or [None])[0],
            "best_before": (_f32(process, rbp - 0x230, 1) or [None])[0],
            "selected_before": (_f32(process, rbp - 0x220, 1) or [None])[0],
        })
        return False

    if site == FIT_CANDIDATE_DONE and state["fit"] is not None:
        rbp = _u(frame, "rbp")
        candidate = state["fit"]["candidates"][-1]
        candidate["best_after"] = (_xmm_f32(frame, "xmm3") or [None])[0]
        candidate["selected_after"] = (_f32(process, rbp - 0x220, 1) or [None])[0]
        return False

    if site == FIT_C_COMPARE and state["fit"] is not None:
        rbp = _u(frame, "rbp")
        state["fit"]["c_table"] = {
            "score": (_xmm_f32(frame, "xmm0") or [None])[0],
            "best_ab_score": (_f32(process, rbp - 0x230, 1) or [None])[0],
            "selected_before": (_f32(process, rbp - 0x220, 1) or [None])[0],
        }
        return False

    if site == FIT_RETURN and state["fit"] is not None:
        state["fit"]["return_xmm0"] = _xmm_f32(frame, "xmm0")
        return False

    if site == PRODUCER_STORE and state["fit"] is not None:
        state["producer"]["stored_amount_xmm0"] = _xmm_f32(frame, "xmm0")
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
    for site in (
        PRODUCER_PRE_CCT,
        PRODUCER_POST_CCT,
        PRODUCER_PRE_FIT,
        PRODUCER_STORE,
        NORMALIZE_ENTRY,
        FIT_ENTRY,
        FIT_CANDIDATE_SCORE,
        FIT_CANDIDATE_DONE,
        FIT_C_COMPARE,
        FIT_RETURN,
    ):
        bp = target.BreakpointCreateByAddress(base + site)
        bp.SetScriptCallbackFunction("crosstalk_amount_fit_probe.hit")


def write_report(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="ascii") as handle:
        json.dump(_state(), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_CROSSTALK_AMOUNT_FIT_REPORT", path)


def assert_complete():
    state = _state()
    if not state["complete"]:
        raise RuntimeError(f"capture incomplete: {state}")
    if state["errors"]:
        raise RuntimeError(f"capture errors: {state['errors']}")
    if len(state["fit"]["candidates"]) != 20:
        raise RuntimeError(f"expected 20 candidates: {state['fit']['candidates']}")
