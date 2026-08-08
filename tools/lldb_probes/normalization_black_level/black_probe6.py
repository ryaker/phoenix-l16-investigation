import json, struct, lldb

_STATE = {"ev": [], "out": "/tmp/black6.json"}


def reset(path):
    _STATE["ev"] = []
    _STATE["out"] = path


def _rd(proc, addr, n):
    err = lldb.SBError()
    if not addr:
        return b""
    b = proc.ReadMemory(addr, n, err)
    return b if err.Success() else b""


def _f32(proc, addr, n):
    b = _rd(proc, addr, 4 * n)
    if len(b) < 4 * n:
        return None
    return [round(x, 9) for x in struct.unpack("<%df" % n, b)]


def _i32(proc, addr, n):
    b = _rd(proc, addr, 4 * n)
    if len(b) < 4 * n:
        return None
    return list(struct.unpack("<%di" % n, b))


def _q(proc, addr):
    b = _rd(proc, addr, 8)
    return struct.unpack("<Q", b)[0] if len(b) == 8 else 0


def _xmm(frame, name):
    r = frame.FindRegister(name)
    err = lldb.SBError()
    v = r.GetData().GetFloat(err, 0)
    return round(v, 9) if err.Success() else None


def _flush():
    with open(_STATE["out"], "w", encoding="ascii") as fh:
        json.dump(_STATE["ev"], fh, indent=1)


def on_hit(frame, bp_loc, internal_dict):
    proc = frame.GetThread().GetProcess()
    t = proc.GetTarget()
    pc = frame.GetPCAddress().GetFileAddress()
    reg = lambda n: frame.FindRegister(n).GetValueAsUnsigned()
    rdi = reg("rdi")
    if pc == 0xF36F0:
        rsi = reg("rsi")
        ra = _q(proc, reg("rsp"))
        caller = t.ResolveLoadAddress(ra).GetFileAddress() if ra else 0
        mp = _q(proc, rdi + 0x1F0)
        rec = {
            "ev": "entry",
            "caller": hex(caller),
            "obj": hex(rdi),
            "dims_0x10": _i32(proc, rdi + 0x10, 2),
            "i_0x58": _i32(proc, rdi + 0x58, 2),
            "ptr_0x20": hex(_q(proc, rdi + 0x20)),
            "type": _i32(proc, rdi + 0xA8, 1),
            "trip_in": _f32(proc, rdi + 0xAC, 3),
            "means_ptr": hex(mp),
            "means": _f32(proc, mp, 8) if mp else None,
            "gains": _f32(proc, rsi, 4),
            "x0": _xmm(frame, "xmm0"),
            "span": _xmm(frame, "xmm1"),
            "N": reg("rdx") & 0xFFFFFFFF,
        }
    else:
        rec = {"ev": "exit", "obj": hex(rdi),
               "trip_out": _f32(proc, rdi + 0xAC, 3)}
    _STATE["ev"].append(rec)
    _flush()
    return False


def attach(debugger):
    t = debugger.GetSelectedTarget()
    for bp in t.breakpoint_iter():
        bp.SetScriptCallbackFunction("black_probe6.on_hit")
