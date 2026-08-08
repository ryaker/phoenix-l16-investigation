"""Dump every distinct SensorData/SensorCharacterization record Lumen feeds to
the stage-3 normalization executor (libcp.dylib 0x352ce0), including the
vst_model vector, so the per-module black_level rule can be identified.

Record layout recovered from 0x352d31..0x352d8e:
    rec = [[rdi]+0x198]
    rec+0x00 u32  type
    rec+0x04 f32  black_level
    rec+0x08 f32  white_level
    rec+0x0c f32  cliff_slope
    rec+0x18 ptr  vst_model begin
    rec+0x20 ptr  vst_model end
"""

import json
import struct

import lldb

_STATE = {"out": "/tmp/blackprobe3.json", "recs": {}}


def reset(out_path):
    _STATE["out"] = out_path
    _STATE["recs"] = {}


def _rd(proc, addr, n):
    err = lldb.SBError()
    b = proc.ReadMemory(addr, n, err)
    return b if err.Success() else None


def _f(b, o):
    return struct.unpack_from("<f", b, o)[0]


def _q(b, o):
    return struct.unpack_from("<Q", b, o)[0]


def on_hit(frame, bp_loc, internal_dict):
    proc = frame.GetThread().GetProcess()
    rdi = frame.FindRegister("rdi").GetValueAsUnsigned()
    head = _rd(proc, rdi, 8)
    if not head:
        return False
    obj = _q(head, 0)
    ob = _rd(proc, obj, 0x1A0)
    if not ob:
        return False
    rec_addr = _q(ob, 0x198)
    key = "0x%x" % rec_addr
    if key in _STATE["recs"]:
        return False
    rb = _rd(proc, rec_addr, 0x80)
    if not rb:
        return False
    beg, end = _q(rb, 0x18), _q(rb, 0x20)
    vst = None
    if end > beg and (end - beg) < (1 << 20):
        vb = _rd(proc, beg, end - beg)
        if vb:
            n = (end - beg) // 4
            vst = [round(_f(vb, i * 4), 9) for i in range(n)]
    _STATE["recs"][key] = {
        "type_u32": struct.unpack_from("<I", rb, 0)[0],
        "black": _f(rb, 4),
        "white": _f(rb, 8),
        "cliff_slope": _f(rb, 0xC),
        "vst_bytes": end - beg,
        "vst": vst,
        "rec_f32_0x00_0x80": [round(_f(rb, i * 4), 9) for i in range(32)],
        "rec_u32_0x00_0x80": [struct.unpack_from("<I", rb, i * 4)[0] for i in range(32)],
        "mult": [_f(ob, 0), _f(ob, 4), _f(ob, 8)],
    }
    with open(_STATE["out"], "w", encoding="ascii") as fh:
        json.dump(_STATE["recs"], fh, indent=1)
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    for bp in target.breakpoint_iter():
        bp.SetScriptCallbackFunction("black_probe3.on_hit")
