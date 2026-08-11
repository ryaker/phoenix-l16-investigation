"""Capture one ColorFusion source patch before/after the in-place transform."""

import hashlib
import json
import os
import struct

import lldb


ROOT = "/Volumes/Dev/L16_Lumen_ReverseEngineering"
OUT_DIR = os.environ.get(
    "CF_TRANSFORM_OUT", ROOT + "/runs/colorfusion_f_runtime/u1_28_transform"
)
STATE = {"armed": False, "done": False, "thread": 0, "buffer": 0}


def _reg(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    error = lldb.SBError()
    data = bytes(process.ReadMemory(address, size, error))
    if not error.Success() or len(data) != size:
        raise RuntimeError("read 0x%x+0x%x failed: %s" % (address, size, error))
    return data


def _u64(process, address):
    return struct.unpack("<Q", _read(process, address, 8))[0]


def _descriptor(process, address, element_words):
    width, height, stride = struct.unpack("<iii", _read(process, address + 0x10, 12))
    data = _u64(process, address + 0x20)
    record = {
        "address": "0x%x" % address,
        "width": width,
        "height": height,
        "stride": stride,
        "data": "0x%x" % data,
        "element_words": element_words,
    }
    if data and 0 < width <= 10000 and 0 < height <= 10000 and stride >= width:
        sample = _read(process, data, 4 * element_words)
        record["first_element"] = {
            "float": list(struct.unpack("<%df" % element_words, sample)),
            "bits": ["0x%08x" % value for value in struct.unpack("<%dI" % element_words, sample)],
        }
    return record


def _dump_descriptor(process, descriptor, name):
    data = int(descriptor["data"], 16)
    size = descriptor["stride"] * descriptor["height"] * descriptor["element_words"] * 4
    return _write(name, _read(process, data, size))


def _neighborhood(process, descriptor, x, y):
    width = descriptor["width"]
    height = descriptor["height"]
    stride = descriptor["stride"]
    data = int(descriptor["data"], 16)
    words = descriptor["element_words"]
    values = []
    for py in (y, y + 1):
        for px in (x, x + 1):
            if px < 0 or py < 0 or px >= width or py >= height:
                continue
            raw = _read(process, data + (py * stride + px) * words * 4, words * 4)
            values.append({
                "x": px,
                "y": py,
                "float": list(struct.unpack("<%df" % words, raw)),
                "bits": ["0x%08x" % value for value in struct.unpack("<%dI" % words, raw)],
            })
    return values


def _write(name, data):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    with open(path, "wb") as handle:
        handle.write(data)
    return {
        "file": name,
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _f32_record(data):
    return {
        "float": list(struct.unpack("<4f", data)),
        "bits": ["0x%08x" % value for value in struct.unpack("<4I", data)],
    }


def _module_base(target):
    module = target.FindModule(lldb.SBFileSpec("libcp.dylib"))
    if not module.IsValid():
        raise RuntimeError("libcp.dylib is not loaded")
    return module.GetObjectFileHeaderAddress().GetLoadAddress(target)


def _capture_camera_selection(frame, base):
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    for index in range(frame.GetThread().GetNumFrames()):
        candidate = frame.GetThread().GetFrameAtIndex(index)
        relative = candidate.GetPCAddress().GetLoadAddress(target) - base
        if not (0x1AAB40 <= relative < 0x1AAF90):
            continue
        owner = _reg(candidate, "r12")
        begin = _u64(process, owner + 0x148)
        end = _u64(process, owner + 0x150)
        if end < begin or (end - begin) % 4 or end - begin > 64:
            raise RuntimeError("invalid source ID vector")
        count = (end - begin) // 4
        source_ids = list(struct.unpack("<%di" % count, _read(process, begin, count * 4)))
        return {
            "process_frame_relative": "0x%x" % relative,
            "target_camera_id": struct.unpack("<i", _read(process, owner + 0x140, 4))[0],
            "source_camera_ids": source_ids,
            "mode_0x198": _read(process, owner + 0x198, 1)[0],
            "initialized_0x199": _read(process, owner + 0x199, 1)[0],
        }
    raise RuntimeError("ColorFusionBayer process frame not found")


def on_entry(frame, bp_loc, internal_dict):
    if STATE["done"] or STATE["armed"]:
        return False
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    base = _module_base(target)
    return_address = base + 0x19D062
    buffer_address = _reg(frame, "rbx")
    before = _read(process, buffer_address, 0x1000)
    rbp = _reg(frame, "rbp")
    provider_owner = _u64(process, rbp - 0x53E8)
    provider = _u64(process, provider_owner + 0x20)
    provider_vtable = _u64(process, provider)
    provider_target = _u64(process, provider_vtable + 0x30)
    context = _u64(process, provider + 0x8)
    patch_x, patch_y = struct.unpack("<ii", _read(process, rbp - 0x52C8, 8))
    signal = _descriptor(process, context + 0xA0, 4)
    shading = _descriptor(process, context + 0xD0, 1)
    signal["patch_neighborhood"] = _neighborhood(process, signal, patch_x, patch_y)
    shading["patch_neighborhood"] = _neighborhood(process, shading, patch_x, patch_y)
    shading["dump"] = _dump_descriptor(process, shading, "shading_plane_f32.bin")
    STATE.update({
        "armed": True,
        "thread": frame.GetThread().GetThreadID(),
        "buffer": buffer_address,
        "before": _write("source_before_vec4_f32.bin", before),
        "pre_relative": "0x19d05a",
        "return_relative": "0x19d062",
        "noise_factor_52c0": _f32_record(_read(process, rbp - 0x52C0, 0x10)),
        "noise_factor_53c0": _f32_record(_read(process, rbp - 0x53C0, 0x10)),
        "noise_product": _f32_record(
            struct.pack(
                "<4f",
                *[
                    struct.unpack("<f", struct.pack("<f", left * right))[0]
                    for left, right in zip(
                        struct.unpack("<4f", _read(process, rbp - 0x52C0, 0x10)),
                        struct.unpack("<4f", _read(process, rbp - 0x53C0, 0x10)),
                    )
                ],
            )
        ),
        "noise_provider": {
            "owner": "0x%x" % provider_owner,
            "object": "0x%x" % provider,
            "vtable": "0x%x" % provider_vtable,
            "slot_0x30": "0x%x" % provider_target,
            "slot_0x30_relative": "0x%x" % (provider_target - base),
            "context": "0x%x" % context,
            "patch_coordinate": [patch_x, patch_y],
            "model_a": _f32_record(_read(process, context + 0x10, 0x10)),
            "model_b": _f32_record(_read(process, context + 0x20, 0x10)),
            "black_level": _f32_record(_read(process, context + 0x30, 0x10))['float'][0],
            "white_level": _f32_record(_read(process, context + 0x34, 0x10))['float'][0],
            "closure_inv_white": struct.unpack("<f", _read(process, provider + 0x10, 4))[0],
            "closure_white_squared": struct.unpack("<f", _read(process, provider + 0x14, 4))[0],
            "signal_descriptor_0xa0": signal,
            "shading_descriptor_0xd0": shading,
        },
    })
    try:
        STATE["camera_selection"] = _capture_camera_selection(frame, base)
    except Exception as error:
        STATE["camera_selection_error"] = str(error)
    bp_loc.GetBreakpoint().SetEnabled(False)
    # All-stop LLDB can report several workers at this hot callsite in one
    # stop. Freeze the non-selected workers so the chosen stack buffer cannot
    # be advanced or reused before its return breakpoint is serviced.
    for thread in process:
        if thread.GetThreadID() != STATE["thread"]:
            thread.Suspend()
    return_bp = target.BreakpointCreateByAddress(return_address)
    return_bp.SetOneShot(True)
    return_bp.SetThreadID(STATE["thread"])
    return_bp.SetScriptCallbackFunction("transform_attach_probe.on_return")
    return False


def on_return(frame, bp_loc, internal_dict):
    if STATE["done"] or frame.GetThread().GetThreadID() != STATE["thread"]:
        return False
    process = frame.GetThread().GetProcess()
    after = _read(process, STATE["buffer"], 0x1000)
    STATE["after"] = _write("source_after_vec4_f32.bin", after)
    STATE["done"] = True
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "capture.json"), "w") as handle:
        json.dump(STATE, handle, indent=2, sort_keys=True)
    print("CF_TRANSFORM_CAPTURE " + os.path.join(OUT_DIR, "capture.json"))
    process.Kill()
    return False


def install(debugger):
    target = debugger.GetSelectedTarget()
    base = _module_base(target)
    # Stop at the source-module caller immediately before `mov rbx,rdi; call
    # 0x18fe00`, then delete this hot breakpoint before resuming. This avoids
    # concurrent workers contaminating the selected stack buffer.
    bp = target.BreakpointCreateByAddress(base + 0x19D05A)
    bp.SetScriptCallbackFunction("transform_attach_probe.on_entry")
    print("CF_TRANSFORM_ARMED id=%d address=0x%x" % (bp.GetID(), base + 0x19D05A))
