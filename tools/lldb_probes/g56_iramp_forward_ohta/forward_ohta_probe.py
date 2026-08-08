import builtins
import json
import struct


SITES = {
    0x36705F: "direct_contributor",
    0x368D6F: "src2_reference",
}


def reset(path=None, label=None):
    builtins.l16_g56_packets = {}
    builtins.l16_g56_path = path
    builtins.l16_g56_label = label


def _write(path, label):
    payload = {"label": label, "packets": builtins.l16_g56_packets}
    with open(path, "w") as output:
        json.dump(payload, output, indent=2, sort_keys=True)


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _xmm_f32s(frame, name):
    data = frame.FindRegister(name).GetData()
    error = builtins.__import__("lldb").SBError()
    values = []
    for index in range(4):
        value = data.GetFloat(error, index * 4) if data.IsValid() else None
        values.append(value if error.Success() else None)
    return values


def _f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def _mul(a, b):
    return _f32(_f32(a) * _f32(b))


def _add(a, b):
    return _f32(_f32(a) + _f32(b))


def _transform(source, columns):
    output = []
    for lane in range(4):
        value = _add(_mul(source[0], columns[0][lane]), _mul(source[1], columns[1][lane]))
        output.append(_add(value, _mul(source[2], columns[2][lane])))
    output[3] = source[3]
    return output


def _base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            address = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if address != 0xFFFFFFFFFFFFFFFF:
                return address
    return None


def hit(frame, _bp_loc, _internal_dict):
    if not hasattr(builtins, "l16_g56_packets"):
        reset()
    target = frame.GetThread().GetProcess().GetTarget()
    base = _base(target)
    va = _u(frame, "rip") - base if base is not None else None
    role = SITES.get(va, f"unknown_{va}")
    if role in builtins.l16_g56_packets:
        return False

    source = _xmm_f32s(frame, "xmm3")
    output = _xmm_f32s(frame, "xmm4")
    columns = [_xmm_f32s(frame, name) for name in ("xmm0", "xmm1", "xmm2")]
    predicted = _transform(source, columns)
    builtins.l16_g56_packets[role] = {
        "role": role,
        "rip": _u(frame, "rip"),
        "source_xmm3": source,
        "column_r_xmm0": columns[0],
        "column_g_xmm1": columns[1],
        "column_b_xmm2": columns[2],
        "output_xmm4": output,
        "predicted_float32": predicted,
        "output_bits": [struct.pack("<f", value).hex() for value in output],
        "predicted_bits": [struct.pack("<f", value).hex() for value in predicted],
    }
    if len(builtins.l16_g56_packets) == len(SITES):
        path = getattr(builtins, "l16_g56_path", None)
        label = getattr(builtins, "l16_g56_label", None)
        if path is not None:
            _write(path, label)
        print("L16_G56_FORWARD_OHTA_CAPTURED", label, sorted(builtins.l16_g56_packets))
        frame.GetThread().GetProcess().Kill()
    return False


def install(debugger):
    target = debugger.GetSelectedTarget()
    base = _base(target)
    if base is None:
        raise RuntimeError("libcp.dylib is not loaded")
    for va in SITES:
        breakpoint = target.BreakpointCreateByAddress(base + va)
        breakpoint.SetOneShot(True)
        breakpoint.SetScriptCallbackFunction("forward_ohta_probe.hit")
    print("L16_G56_FORWARD_OHTA_INSTALLED", len(SITES))


def report(path, label):
    if not hasattr(builtins, "l16_g56_packets"):
        reset()
    _write(path, label)
    print("L16_G56_FORWARD_OHTA", label, sorted(builtins.l16_g56_packets))
