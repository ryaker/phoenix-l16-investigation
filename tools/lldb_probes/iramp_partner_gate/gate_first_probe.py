import builtins


def reset():
    builtins.l16_gate_first = None


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def hit(frame, bp_loc, internal_dict):
    rdi = _u(frame, "rdi")
    r9 = _u(frame, "r9")
    diff = r9 - rdi if r9 >= rdi else None
    builtins.l16_gate_first = {
        "rbp": _u(frame, "rbp"),
        "begin": rdi,
        "end": r9,
        "diff": diff,
        "npartners": diff // 0x280 if diff is not None else None,
        "aligned_0x280": (diff % 0x280 == 0) if diff is not None else None,
    }


def report(label):
    if not hasattr(builtins, "l16_gate_first"):
        reset()
    print("L16_GATE_FIRST_PROBE_BEGIN", label)
    print("gate", builtins.l16_gate_first)
    print("L16_GATE_FIRST_PROBE_END", label)
