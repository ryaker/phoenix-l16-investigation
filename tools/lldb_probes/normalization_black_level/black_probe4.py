import json, struct

_STATE = {"out": None, "ev": []}

BASES = {}


def reset(out_path):
    _STATE["out"] = out_path
    _STATE["ev"] = []


def _rd(proc, addr, n):
    err = __import__("lldb").SBError()
    if not addr:
        return b""
    b = proc.ReadMemory(addr, n, err)
    return b if err.Success() else b""


def _f(b, o):
    return struct.unpack_from("<f", b, o)[0] if len(b) >= o + 4 else None


def _u(b, o):
    return struct.unpack_from("<I", b, o)[0] if len(b) >= o + 4 else None


def _fileoff(frame):
    import lldb
    a = frame.GetPCAddress()
    m = a.GetModule()
    if not m:
        return None
    return a.GetFileAddress()


def on_hit(frame, bp_loc, internal_dict):
    proc = frame.GetThread().GetProcess()
    pc = _fileoff(frame)
    reg = lambda n: frame.FindRegister(n).GetValueAsUnsigned()
    rec = {"pc": hex(pc) if pc else None}
    if pc in (0x31BCEF, 0x31BD26):
        p = reg("rax")
    elif pc == 0x31BD29:
        p = reg("r13")
        rec["r12"] = hex(reg("r12"))
    else:
        p = reg("rax")
    rec["ptr"] = hex(p)
    b = _rd(proc, p, 0x20)
    if b:
        rec["type"] = _u(b, 0)
        rec["black"] = _f(b, 4)
        rec["white"] = _f(b, 8)
        rec["cliff"] = _f(b, 0xC)
    rec["eax"] = reg("rax") & 0xFFFFFFFF
    rec["r14"] = hex(reg("r14"))
    _STATE["ev"].append(rec)
    with open(_STATE["out"], "w", encoding="ascii") as fh:
        json.dump(_STATE["ev"], fh, indent=1)
    return False


def attach(debugger):
    t = debugger.GetSelectedTarget()
    for bp in t.breakpoint_iter():
        bp.SetScriptCallbackFunction("black_probe4.on_hit")
