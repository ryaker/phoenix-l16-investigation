import builtins
import json
import struct


def reset(report_path):
    builtins.l16_iramp_score_stages = {
        "report_path": report_path,
        "events": [],
        "errors": [],
    }


def _state():
    return builtins.l16_iramp_score_stages


def _reg(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    raw = process.ReadMemory(address, size, error)
    return raw if error.Success() and len(raw) == size else None


def _xmm(frame, name):
    lldb = builtins.__import__("lldb")
    data = frame.FindRegister(name).GetData()
    error = lldb.SBError()
    raw = data.ReadRawData(error, 0, 16)
    return list(struct.unpack("<4f", raw)) if error.Success() else None


def _stack_vec(process, rbp, offset):
    raw = _read(process, rbp - offset, 16)
    return list(struct.unpack("<4f", raw)) if raw else None


def hit(frame, bp_loc, internal_dict, label):
    process = frame.GetThread().GetProcess()
    rbp = _reg(frame, "rbp")
    r12 = _reg(frame, "r12")
    event = {
        "label": label,
        "pc": _reg(frame, "rip"),
        "xmm0": _xmm(frame, "xmm0"),
        "xmm1": _xmm(frame, "xmm1"),
        "xmm2": _xmm(frame, "xmm2"),
        "xmm3": _xmm(frame, "xmm3"),
        "fine_stack": _stack_vec(process, rbp, 0x80),
        "coarse_stack": _stack_vec(process, rbp, 0x70),
    }
    for name, offset in (
        ("reference_detail_0", 0x1540),
        ("reference_detail_1", 0x1550),
        ("reference_detail_2", 0x1560),
        ("reference_detail_3", 0x1570),
        ("reference_l1", 0x26D0),
    ):
        raw = _read(process, r12 + offset, 4)
        event[name] = struct.unpack("<f", raw)[0] if raw else None
    _state()["events"].append(event)
    if label == "final_geometric_mean_inputs":
        process.Kill()
    return False


def report():
    state = _state()
    with open(state["report_path"], "w") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_IRAMP_SCORE_STAGES", json.dumps(state, sort_keys=True))
