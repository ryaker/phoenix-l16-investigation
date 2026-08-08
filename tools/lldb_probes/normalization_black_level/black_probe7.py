"""Temporally-ordered probe interleaving the black-level SOLVER with the
stage-3 normalization executor, to prove which black value each normalization
actually consumes.

Breakpoints (file addresses in libcp.dylib):
  0xf36f0  solver entry   (rdi = camera/frame obj, rsi = gains[3], xmm0 = x0,
                           xmm1 = span, edx = N)
  0xf3888  solver exit    (rdi still = obj; obj+0xac now holds solved black)
  0x352ce0 normalization executor entry
                          rec = [[rdi]+0x198]; rec+0x04 black, +0x08 white
                          mult = [[rdi]+0x00/0x04/0x08]

Correlation key: the SensorCharacterization record is embedded at obj+0xa8, so
rec_addr for a given camera should equal solver_obj + 0xa8.
"""

import json
import struct

import lldb

_STATE = {"ev": [], "out": "/tmp/black7.json", "seq": 0}


def reset(path):
    _STATE["ev"] = []
    _STATE["out"] = path
    _STATE["seq"] = 0


def _rd(proc, addr, n):
    if not addr:
        return b""
    err = lldb.SBError()
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
    tid = frame.GetThread().GetThreadID()
    reg = lambda n: frame.FindRegister(n).GetValueAsUnsigned()
    rdi = reg("rdi")
    _STATE["seq"] += 1
    seq = _STATE["seq"]

    if pc == 0xF36F0:
        rsi = reg("rsi")
        ra = _q(proc, reg("rsp"))
        caller = t.ResolveLoadAddress(ra).GetFileAddress() if ra else 0
        mp = _q(proc, rdi + 0x1F0)
        rec = {
            "seq": seq, "tid": tid, "ev": "solve_in", "caller": hex(caller),
            "obj": hex(rdi), "rec_addr": hex(rdi + 0xA8),
            "dims": _i32(proc, rdi + 0x10, 2),
            "phase": _i32(proc, rdi + 0x58, 2),
            "plane": hex(_q(proc, rdi + 0x20)),
            "type": _i32(proc, rdi + 0xA8, 1),
            "trip_in": _f32(proc, rdi + 0xAC, 3),
            "means": _f32(proc, mp, 4) if mp else None,
            "gains": _f32(proc, rsi, 4),
            "x0": _xmm(frame, "xmm0"), "span": _xmm(frame, "xmm1"),
            "N": reg("rdx") & 0xFFFFFFFF,
        }
    elif pc == 0xF3888:
        rec = {"seq": seq, "tid": tid, "ev": "solve_out", "obj": hex(rdi),
               "rec_addr": hex(rdi + 0xA8),
               "trip_out": _f32(proc, rdi + 0xAC, 3)}
    else:
        obj = _q(proc, rdi)
        rec_addr = _q(proc, obj + 0x198) if obj else 0
        rec = {
            "seq": seq, "tid": tid, "ev": "norm", "exec": hex(rdi),
            "obj": hex(obj), "rec_addr": hex(rec_addr),
            "implied_camera_obj": hex(rec_addr - 0xA8) if rec_addr else None,
            "type": _i32(proc, rec_addr, 1) if rec_addr else None,
            "trip": _f32(proc, rec_addr + 4, 3) if rec_addr else None,
            "mult": _f32(proc, obj, 3) if obj else None,
        }

    _STATE["ev"].append(rec)
    _flush()
    return False


def attach(debugger):
    t = debugger.GetSelectedTarget()
    for bp in t.breakpoint_iter():
        bp.SetScriptCallbackFunction("black_probe7.on_hit")
