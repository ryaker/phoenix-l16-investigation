import builtins


def reset():
    builtins.l16_sad = None


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def hit(frame, bp_loc, internal_dict):
    builtins.l16_sad = {
        "rbp": _u(frame, "rbp"),
        "rcx": _u(frame, "rcx"),
        "rdi": _u(frame, "rdi"),
        "r9": _u(frame, "r9"),
    }


def report(label):
    if not hasattr(builtins, "l16_sad"):
        reset()
    print("L16_SAD_PROBE_BEGIN", label)
    print("sad", builtins.l16_sad)
    print("L16_SAD_PROBE_END", label)
