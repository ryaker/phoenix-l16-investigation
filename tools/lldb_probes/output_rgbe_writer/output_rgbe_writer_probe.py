import builtins
import json
import struct


CAPTURE_SITE = 0x90764


def reset(label=""):
    builtins.l16_output_rgbe = {
        "label": label,
        "capture": None,
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_output_rgbe"):
        reset()
    return builtins.l16_output_rgbe


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


def hit(frame, _bp_loc, _extra_args, _internal_dict):
    state = _state()
    if state["capture"] is not None:
        return False
    process = frame.GetThread().GetProcess()
    width = _u(frame, "r8")
    float_row = _u(frame, "r14")
    packed_row = _u(frame, "r12")
    count = min(width, 128)
    float_data = _read(process, float_row, count * 3 * 4)
    packed_data = _read(process, packed_row, count * 4)
    if float_data is None or packed_data is None:
        process.Kill()
        return False
    state["capture"] = {
        "thread_id": frame.GetThread().GetThreadID(),
        "row_index_r15": _u(frame, "r15"),
        "width_r8": width,
        "input_rgb_float32": list(struct.unpack("<" + "f" * (count * 3), float_data)),
        "packed_rgbe_hex": packed_data.hex(),
        "pixel_count": count,
    }
    process.Kill()
    return False


def attach_existing(debugger):
    target = debugger.GetSelectedTarget()
    if target.GetNumBreakpoints() < 1:
        _state()["errors"].append("missing existing breakpoint")
        return
    bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
    bp.SetScriptCallbackFunction("output_rgbe_writer_probe.hit")
    print(f"OUTPUT_RGBE attached bp={bp.GetID()}")


def drive(debugger, max_steps=256):
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process.IsValid() and process.GetState() == 5 and steps < max_steps:
        if _state()["capture"] is not None:
            process.Kill()
            break
        process.Continue()
        steps += 1
    print(f"OUTPUT_RGBE drive_steps={steps}")


def write_report(path):
    with open(path, "w") as handle:
        json.dump(_state(), handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(f"OUTPUT_RGBE wrote {path}")

