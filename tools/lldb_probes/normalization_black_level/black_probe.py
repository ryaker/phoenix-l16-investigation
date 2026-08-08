"""Read Lumen's stage-3 normalization black/white levels straight out of memory.

Breakpoint: libcp.dylib 0x352ce0 (normalization executor construction, pinned by
bundle_static_runtime_create_stereo_color_normalization_vignetting_two_body.md).
Disassembly of 0x352d31..0x352d8e:
    rax = [rdi]              ; worker payload
    rcx = [rax + 0x198]      ; sensor-characterization record
    black = f32 [rcx + 0x04]
    white = f32 [rcx + 0x08]
    span  = white - black
    scale_c = 1.0f / (f32[rax + 4*c] * span)  for c in 0,1,2
"""

import json
import struct

import lldb

_HITS = []
_OUT = "/tmp/blackprobe.json"


def reset(out_path):
    del _HITS[:]
    global _OUT
    _OUT = out_path


def _rd(proc, addr, n):
    err = lldb.SBError()
    b = proc.ReadMemory(addr, n, err)
    return b if err.Success() else None


def _f32(b, off):
    return struct.unpack_from("<f", b, off)[0]


def _u32(b, off):
    return struct.unpack_from("<I", b, off)[0]


def _u64(b, off):
    return struct.unpack_from("<Q", b, off)[0]


def on_hit(frame, bp_loc, internal_dict):
    proc = frame.GetThread().GetProcess()
    rdi = frame.FindRegister("rdi").GetValueAsUnsigned()
    rsi = frame.FindRegister("rsi").GetValueAsUnsigned()
    rec = {"rdi": hex(rdi), "rsi": hex(rsi)}

    head = _rd(proc, rdi, 0x100)
    if head:
        obj = _u64(head, 0)
        rec["obj"] = hex(obj)
        rec["r15_0x30_0x40"] = [_u32(head, o) for o in range(0x30, 0x40, 4)]
        ob = _rd(proc, obj, 0x200)
        if ob:
            rec["mult"] = [_f32(ob, 0), _f32(ob, 4), _f32(ob, 8)]
            sc = _u64(ob, 0x198)
            rec["sc_ptr"] = hex(sc)
            scb = _rd(proc, sc, 0x60)
            if scb:
                rec["sc_f32"] = [round(_f32(scb, i * 4), 9) for i in range(24)]
                rec["sc_u32"] = [_u32(scb, i * 4) for i in range(24)]
                rec["black"] = _f32(scb, 4)
                rec["white"] = _f32(scb, 8)
                rec["span"] = _f32(scb, 8) - _f32(scb, 4)
            rec["obj_ptrs_0x180_0x1c0"] = [
                hex(_u64(ob, o)) for o in range(0x180, 0x1C0, 8)
            ]
    rsib = _rd(proc, rsi, 0x40)
    if rsib:
        rec["rsi_u32"] = [_u32(rsib, i * 4) for i in range(16)]
    _HITS.append(rec)
    with open(_OUT, "w", encoding="ascii") as fh:
        json.dump(_HITS, fh, indent=1)
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    for bp in target.breakpoint_iter():
        bp.SetScriptCallbackFunction("black_probe.on_hit")
