"""One-shot liveness census for sensor/optical correction surfaces."""

import builtins
import hashlib
import json
import struct


SITES = {
    # RemoveCrossTalkGeneric callable slots. Generic executor 0x2e20 invokes
    # +0x30; the old census accidentally watched +0x38 only.
    0xFEBF0: "remove_crosstalk_vec4_false_callback_0x30",
    0x100680: "remove_crosstalk_float_false_callback_0x30",
    0x103120: "remove_crosstalk_vec4_true_callback_0x30",
    0x1054D0: "remove_crosstalk_float_true_callback_0x30",
    0x100560: "remove_crosstalk_vec4_false_secondary_0x38",
    0x1019A0: "remove_crosstalk_float_false_secondary_0x38",
    0x1053B0: "remove_crosstalk_vec4_true_secondary_0x38",
    0x106C80: "remove_crosstalk_float_true_secondary_0x38",
    # Concrete RemoveVignettingGeneric specializations and shared data builder.
    0xFBDA0: "remove_vignetting_variant_0",
    0xFC2F0: "remove_vignetting_variant_1",
    0xFC840: "remove_vignetting_variant_2",
    0x106CB0: "vignetting_data_constructor",
    0x107294: "vignetting_before_shaping",
    0x107B27: "vignetting_data_constructor_return",
    0xFBE45: "variant_0_calls_data_constructor",
    0xFC395: "variant_1_calls_data_constructor",
    0xFC8E5: "variant_2_calls_data_constructor",
    # Installed IR-correction model selectors.
    0xFE1B0: "ir_model_selector_variant_0",
    0xFE2F0: "ir_model_selector_variant_1",
    0xFE430: "ir_model_selector_variant_2",
    # Configuration-property reads.
    0x1B302E: "lens_shading_type_read_1b302e",
    0x27B2B1: "lens_shading_type_read_27b2b1",
    0x3B36AD: "lens_shading_type_read_3b36ad",
    0x3CBD41: "lens_shading_type_read_3cbd41",
    0x3CCC2D: "lens_shading_type_read_3ccc2d",
    0x3F5979: "lens_shading_type_read_3f5979",
    0x3F5C00: "lens_shading_type_read_3f5c00",
    0x403A23: "lens_shading_type_read_403a23",
    0x40B7D1: "lens_shading_type_read_40b7d1",
    0x40BE3A: "lens_shading_type_read_40be3a",
    0x42DFBF: "lens_shading_type_read_42dfbf",
    0x3B3A23: "lens_shading_multiplier_read_3b3a23",
    0x3CC389: "lens_shading_multiplier_read_3cc389",
    0x41A53F: "lens_shading_multiplier_read_41a53f",
    0x1B2F4E: "cross_talk_type_read_1b2f4e",
    0x27B244: "cross_talk_type_read_27b244",
    0x3CC019: "cross_talk_type_read_3cc019",
    0x3CCE9D: "cross_talk_type_read_3cce9d",
    0x3F5911: "cross_talk_type_read_3f5911",
    0x3F5C68: "cross_talk_type_read_3f5c68",
    0x403AF5: "cross_talk_type_read_403af5",
    0x40B839: "cross_talk_type_read_40b839",
    0x40BEA2: "cross_talk_type_read_40bea2",
    0x42DF50: "cross_talk_type_read_42df50",
    0x27B27D: "ir_correction_read_27b27d",
    0x327227: "ir_correction_read_327227",
    0x3CC04D: "ir_correction_read_3cc04d",
    0x3F5945: "ir_correction_read_3f5945",
    0x411D47: "ir_correction_read_411d47",
}


def reset(label=""):
    builtins.l16_correction_liveness = {
        "label": label,
        "counts": {name: 0 for name in SITES.values()},
        "samples": [],
        "breakpoint_ids": {},
        "pending_vignetting": {},
        "vignetting_packets": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_correction_liveness"):
        reset()
    return builtins.l16_correction_liveness


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
    return data if error.Success() and len(data) == size else None


def _i32(process, address):
    data = _read(process, address, 4)
    return struct.unpack("<i", data)[0] if data is not None else None


def _u32(process, address):
    data = _read(process, address, 4)
    return struct.unpack("<I", data)[0] if data is not None else None


def _u64(process, address):
    data = _read(process, address, 8)
    return struct.unpack("<Q", data)[0] if data is not None else None


def _xmm_f32s(frame, name):
    data = frame.FindRegister(name).GetData()
    lldb = builtins.__import__("lldb")
    result = []
    for offset in range(0, 16, 4):
        error = lldb.SBError()
        value = data.GetFloat(error, offset) if data.IsValid() else None
        result.append(value if error.Success() else None)
    return result


def _stack(thread, limit=8):
    target = thread.GetProcess().GetTarget()
    base = _base(target)
    result = []
    for index in range(min(limit, thread.GetNumFrames())):
        frame = thread.GetFrameAtIndex(index)
        pc = frame.GetPC()
        result.append(
            {
                "index": index,
                "libcp_va": pc - base if base is not None and pc >= base else None,
                "function": frame.GetFunctionName(),
            }
        )
    return result


def hit(frame, bp_loc, _internal_dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    base = _base(target)
    va = frame.GetPC() - base if base is not None else None
    name = SITES.get(va, f"unknown_{va}")
    state["counts"][name] = state["counts"].get(name, 0) + 1
    thread_key = str(thread.GetThreadID())
    if va == 0x106CB0:
        captured = _u(frame, "rsi")
        state["pending_vignetting"].setdefault(thread_key, []).append({
            "captured_image": captured,
            "camera_id": _i32(process, captured + 0x60),
            "mirror_position": _i32(process, captured + 0x50),
            "lens_position": _i32(process, captured + 0x54),
            "mode_bool": _u(frame, "rdx") & 0xFF,
            "multiplier_xmm0": _xmm_f32s(frame, "xmm0")[0],
        })
    elif va == 0x107294:
        stack = state["pending_vignetting"].get(thread_key, [])
        output = _u64(process, _u(frame, "rbp") - 0x1F8)
        if stack and output:
            width = _u32(process, output + 4)
            height = _u32(process, output + 8)
            begin = _u64(process, output + 0x10)
            byte_count = width * height * 4 if width and height else None
            data = (
                _read(process, begin, byte_count)
                if begin and byte_count and byte_count <= 1024 * 1024
                else None
            )
            stack[-1]["base_data_sha256"] = (
                hashlib.sha256(data).hexdigest() if data is not None else None
            )
            stack[-1]["base_data_hex"] = data.hex() if data is not None else None
    elif va == 0x107B27:
        stack = state["pending_vignetting"].get(thread_key, [])
        pending = stack.pop() if stack else {}
        if not stack:
            state["pending_vignetting"].pop(thread_key, None)
        output = _u(frame, "rbx")
        selected_hall_code = _i32(process, output)
        width = _u32(process, output + 4)
        height = _u32(process, output + 8)
        begin = _u64(process, output + 0x10)
        end = _u64(process, output + 0x18)
        byte_count = end - begin if begin and end and end >= begin else None
        data = (
            _read(process, begin, byte_count)
            if byte_count is not None and byte_count <= 1024 * 1024
            else None
        )
        packet = {
            **pending,
            "output": output,
            "selected_hall_code": selected_hall_code,
            "width": width,
            "height": height,
            "byte_count": byte_count,
            "float_count": byte_count // 4 if byte_count is not None else None,
            "data_sha256": hashlib.sha256(data).hexdigest()
            if data is not None
            else None,
            "data_hex": data.hex() if data is not None else None,
            "first_f32": list(struct.unpack("<" + "f" * min(8, len(data) // 4), data[:32]))
            if data
            else None,
        }
        identity = (
            packet.get("camera_id"),
            packet.get("mirror_position"),
            packet.get("mode_bool"),
            packet.get("multiplier_xmm0"),
            packet.get("data_sha256"),
        )
        existing = {
            (
                item.get("camera_id"),
                item.get("mirror_position"),
                item.get("mode_bool"),
                item.get("multiplier_xmm0"),
                item.get("data_sha256"),
            )
            for item in state["vignetting_packets"]
        }
        if identity not in existing and len(state["vignetting_packets"]) < 128:
            state["vignetting_packets"].append(packet)
    if state["counts"][name] == 1:
        state["samples"].append(
            {
                "site": name,
                "va": va,
                "registers": {
                    key: _u(frame, key)
                    for key in (
                        "rax",
                        "rbx",
                        "rcx",
                        "rdx",
                        "rdi",
                        "rsi",
                        "r8",
                        "r9",
                        "rbp",
                        "rsp",
                    )
                },
                "xmm0_f32": _xmm_f32s(frame, "xmm0"),
                "stack": _stack(frame.GetThread()),
            }
        )
    return False


def install(debugger):
    target = debugger.GetSelectedTarget()
    base = _base(target)
    if base is None:
        raise RuntimeError("libcp.dylib is not loaded")
    for va, name in SITES.items():
        bp = target.BreakpointCreateByAddress(base + va)
        if name.startswith("remove_crosstalk_"):
            # Native one-shot auto-continue avoids Python callback overhead
            # and lets LLDB retire the breakpoint atomically when worker
            # threads arrive together.
            bp.SetAutoContinue(True)
            bp.SetOneShot(True)
        else:
            bp.SetScriptCallbackFunction("correction_liveness_probe.hit")
            bp.SetOneShot(True)
        _state()["breakpoint_ids"][name] = bp.GetID()
    print("L16_CORRECTION_LIVENESS_INSTALLED", len(SITES))


def capture_current_stops(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    base = _base(target)
    observed = []
    if base is None:
        state["errors"].append("libcp base unavailable at stop capture")
        return
    for thread in process:
        if thread.GetNumFrames() < 1:
            continue
        va = thread.GetFrameAtIndex(0).GetPC() - base
        name = SITES.get(va)
        if name and name.startswith("remove_crosstalk_"):
            state["counts"][name] = max(state["counts"].get(name, 0), 1)
            observed.append({"thread_id": thread.GetThreadID(), "site": name, "va": va})
    state.setdefault("crosstalk_stop_batches", []).append(observed)
    print("L16_CROSSTALK_STOP_CAPTURE", json.dumps(observed, sort_keys=True))


def write_report(path):
    state = _state()
    lldb = builtins.__import__("lldb")
    target = lldb.debugger.GetSelectedTarget()
    for name, breakpoint_id in state["breakpoint_ids"].items():
        if not name.startswith("remove_crosstalk_"):
            continue
        breakpoint = target.FindBreakpointByID(breakpoint_id)
        if breakpoint and breakpoint.IsValid():
            state["counts"][name] = max(
                state["counts"].get(name, 0), breakpoint.GetHitCount()
            )
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_CORRECTION_LIVENESS_REPORT", path)
