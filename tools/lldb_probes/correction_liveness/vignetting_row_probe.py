"""Capture the first live vec4 vignetting worker store and its context."""

import builtins
import json
import struct


STORE = 0x108257


def reset(label=""):
    builtins.l16_vignetting_row = {"label": label, "packet": None}


def _base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            return module.GetObjectFileHeaderAddress().GetLoadAddress(target)
    return None


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    return data if error.Success() and len(data) == size else None


def _xmm(frame, name):
    data = frame.FindRegister(name).GetData()
    lldb = builtins.__import__("lldb")
    values = []
    for offset in range(0, 16, 4):
        error = lldb.SBError()
        value = data.GetFloat(error, offset)
        values.append(value if error.Success() else None)
    return values


def _qwords(data):
    return list(struct.unpack("<" + "Q" * (len(data) // 8), data))


def hit(frame, _bp_loc, _internal_dict):
    if builtins.l16_vignetting_row["packet"] is not None:
        return True
    process = frame.GetThread().GetProcess()
    context = _u(frame, "rdi")
    context_data = _read(process, context, 0x48)
    pointers = _qwords(context_data) if context_data else []
    pointed = {}
    for index, pointer in enumerate(pointers):
        data = _read(process, pointer, 0x60) if pointer else None
        pointed[str(index)] = {
            "address": pointer,
            "first_96_hex": data.hex() if data is not None else None,
        }
    source = _read(process, _u(frame, "rbx"), 16)
    destination_before = _read(process, _u(frame, "rdx"), 16)
    profile = pointers[4] if len(pointers) > 4 else 0
    profile_width_data = _read(process, profile + 4, 8) if profile else None
    profile_begin_data = _read(process, profile + 0x10, 8) if profile else None
    profile_width, profile_height = (
        struct.unpack("<II", profile_width_data)
        if profile_width_data
        else (None, None)
    )
    profile_begin = (
        struct.unpack("<Q", profile_begin_data)[0] if profile_begin_data else 0
    )
    profile_data = (
        _read(process, profile_begin, profile_width * profile_height * 4)
        if profile_begin and profile_width and profile_height
        else None
    )
    builtins.l16_vignetting_row["packet"] = {
        "site_va": STORE,
        "registers": {
            name: _u(frame, name)
            for name in (
                "rax",
                "rbx",
                "rcx",
                "rdx",
                "rdi",
                "rsi",
                "r8",
                "r9",
                "r10",
                "r11",
                "r12",
                "r13",
                "r14",
                "r15",
            )
        },
        "xmm0_output": _xmm(frame, "xmm0"),
        "xmm1": _xmm(frame, "xmm1"),
        "xmm2": _xmm(frame, "xmm2"),
        "context_qwords": pointers,
        "context_pointees": pointed,
        "profile_width": profile_width,
        "profile_height": profile_height,
        "profile_f32": list(
            struct.unpack(
                "<" + "f" * (len(profile_data) // 4),
                profile_data,
            )
        )
        if profile_data
        else None,
        "source_vec4": list(struct.unpack("<4f", source)) if source else None,
        "destination_before": list(struct.unpack("<4f", destination_before))
        if destination_before
        else None,
    }
    return True


def install(debugger):
    target = debugger.GetSelectedTarget()
    base = _base(target)
    if base is None:
        raise RuntimeError("libcp not loaded")
    bp = target.BreakpointCreateByAddress(base + STORE)
    bp.SetScriptCallbackFunction("vignetting_row_probe.hit")
    print("L16_VIGNETTING_ROW_BP", bp.GetID())


def write_report(path):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(builtins.l16_vignetting_row, handle, indent=2, sort_keys=True)
        handle.write("\n")
