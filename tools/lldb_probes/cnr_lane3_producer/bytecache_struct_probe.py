"""bytecache_struct_probe.py -- locate the FusionCacheBayer byte buffer and when
it is allocated/filled, so the producer write can be watchpointed precisely.

Breaks at:
  0x406643  right after the byte TileCache<u8> is stored at FusionCacheBayer+0xe0
            (r13 = FCB base). Dumps FCB, the byte cache (+0xe0), and the
            TileStorage (+0xf0/+0x100), and hunts for a data buffer that reads
            back as image-sized bytes (values in 0..255, spatially doubled).
  0x406a10  the consumer (byte plane already populated). Same dump, so the
            construction-time vs consumption-time state can be diffed: a buffer
            that is empty at 0x406643 and full at 0x406a10 is filled in between
            (the producer window).
Everything is recorded; nothing is inferred in-probe.
"""
import builtins
import json
import os
import struct

POST_STORE = 0x406643   # r13 = FCB base; byte cache just written to +0xe0
CONSUMER = 0x406A10      # extracts level-0 byte plane


def reset(label="", report_path=""):
    builtins.l16_bs = {"label": label, "report_path": report_path,
                       "bp_ids": {}, "post_store": [], "consumer": [],
                       "errors": []}


def _s():
    if not hasattr(builtins, "l16_bs"):
        reset()
    return builtins.l16_bs


def _u(f, n):
    return f.FindRegister(n).GetValueAsUnsigned()


def _read(proc, addr, size):
    if not addr or addr < 0x1000 or addr > 0x00007FFFFFFFFFFF:
        return None
    lldb = builtins.__import__("lldb")
    err = lldb.SBError()
    try:
        d = proc.ReadMemory(addr, size, err)
    except Exception:
        return None
    return d if err.Success() and d and len(d) == size else None


def _q(proc, a):
    d = _read(proc, a, 8)
    return struct.unpack("<Q", d)[0] if d else 0


def _rtti(proc, obj):
    vt = _q(proc, obj)
    if not vt:
        return None
    ti = _q(proc, vt - 8)
    nm = _q(proc, ti + 8) if ti else 0
    if not nm:
        return None
    out = b""
    for _ in range(160):
        c = _read(proc, nm + len(out), 1)
        if not c or c == b"\x00":
            break
        out += c
    return out.decode("utf-8", "replace")


def _scan_for_buffer(proc, obj_ptr, span=0x140):
    """Walk an object's qwords; for each pointer, test whether it points to a
    plausible byte-image buffer (>=64KB of bytes in 0..255, first row doubled)."""
    found = []
    raw = _read(proc, obj_ptr, span)
    if raw is None:
        return found
    for off in range(0, span, 8):
        p = struct.unpack_from("<Q", raw, off)[0]
        if not (0x100000000 < p < 0x00007FFFFFFFFFFF):
            continue
        sample = _read(proc, p, 64)
        if sample is None:
            continue
        vals = list(sample)
        # heuristic: byte image tiles are spatially doubled -> adjacent pairs equal
        doubled = sum(1 for i in range(0, 62, 2) if vals[i] == vals[i + 1])
        nonzero = sum(1 for v in vals if v != 0)
        found.append({"off": hex(off), "ptr": hex(p),
                      "first16": vals[:16], "doubled_pairs": doubled,
                      "nonzero": nonzero})
    return found


def _dump_obj(proc, tag, base):
    """Follow FCB+0xe0 (byte cache) and +0xf0 (storage), scanning each for a
    byte buffer, plus their RTTI."""
    cache_sp = _q(proc, base + 0xE0)      # shared_ptr<TileCache<u8>> -> object
    stor_sp = _q(proc, base + 0xF0)       # shared_ptr<TileStorage>
    stor2_sp = _q(proc, base + 0x100)
    cache = cache_sp
    stor = stor_sp
    return {
        "tag": tag, "fcb_base": hex(base),
        "cache_ptr": hex(cache), "cache_rtti": _rtti(proc, cache),
        "storage_ptr": hex(stor), "storage_rtti": _rtti(proc, stor),
        "storage2_ptr": hex(stor2_sp),
        "scalar_0xcc_f32": struct.unpack("<f", _read(proc, base + 0xCC, 4))[0]
        if _read(proc, base + 0xCC, 4) else None,
        "cache_buffers": _scan_for_buffer(proc, cache) if cache else [],
        "storage_buffers": _scan_for_buffer(proc, stor) if stor else [],
    }


def post_store(frame, bp_loc, _d):
    st = _s()
    proc = frame.GetThread().GetProcess()
    r13 = _u(frame, "r13")
    st["post_store"].append(_dump_obj(proc, "post_store(0x406643)", r13))
    return False


def consumer(frame, bp_loc, _d):
    st = _s()
    proc = frame.GetThread().GetProcess()
    # at 0x406a10, FCB base is the first arg (rdi) per the bundle
    rdi = _u(frame, "rdi")
    st["consumer"].append(_dump_obj(proc, "consumer(0x406a10)", rdi))
    if len(st["consumer"]) >= 2:
        proc.Kill()
    return False


def install(debugger):
    st = _s()
    target = debugger.GetSelectedTarget()
    for va, cb, name in ((POST_STORE, "post_store", "post"),
                         (CONSUMER, "consumer", "consumer")):
        before = target.GetNumBreakpoints()
        debugger.HandleCommand(
            f"breakpoint set --shlib libcp.dylib --address 0x{va:x}")
        if target.GetNumBreakpoints() > before:
            bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
            bp.SetScriptCallbackFunction(f"bytecache_struct_probe.{cb}")
            st["bp_ids"][name] = bp.GetID()
    print("BYTECACHE_STRUCT_INSTALLED", st["bp_ids"])


def drive(debugger, max_steps=80000):
    lldb = builtins.__import__("lldb")
    proc = debugger.GetSelectedTarget().GetProcess()
    n = 0
    while proc.IsValid() and proc.GetState() == lldb.eStateStopped and n < max_steps:
        n += 1
        proc.Continue()
    print("BYTECACHE_STRUCT_DRIVE", n)


def write_report(debugger, path=""):
    out = path or _s().get("report_path")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as h:
        json.dump(dict(_s()), h, indent=2, sort_keys=True, default=str)
    print("WROTE", out)
