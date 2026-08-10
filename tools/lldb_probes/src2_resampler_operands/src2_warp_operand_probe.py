"""Capture src2/source ImageWarpClamped<filter=2> transform operands at worker
ENTRY 0x3ed2e0. T = *( *( *(rdi+0x20) ) + 0x1e0 ). Dedup by transform CONTENT
(center+H+lut_ptr), not struct address (Lumen reuses one struct buffer per tile
and rewrites it per source). Captures every DISTINCT transform up to max, so the
anchor guidance AND all non-anchor source undistorts are recorded. See
docs/evidence/static_src2_resampler_*."""
import builtins, json, struct

def reset(label, out_path, max_captures=12):
    builtins.l16_src2 = {"label": label, "out": out_path, "max": int(max_captures),
                         "seen": {}, "captures": [], "hits": 0, "errors": []}

def _u64(proc, addr):
    e = builtins.__import__("lldb").SBError()
    b = proc.ReadMemory(addr, 8, e)
    return struct.unpack("<Q", b)[0] if e.Success() else None

def _f32s(proc, addr, n):
    e = builtins.__import__("lldb").SBError()
    b = proc.ReadMemory(addr, 4*n, e)
    return list(struct.unpack("<%df" % n, b)) if e.Success() else None

def hit(frame, bp_loc, internal_dict):
    st = builtins.l16_src2
    st["hits"] += 1
    proc = frame.GetThread().GetProcess()
    rdi = frame.FindRegister("rdi").GetValueAsUnsigned()
    p0 = _u64(proc, rdi + 0x20)
    if not p0: return False
    p1 = _u64(proc, p0)
    if not p1: return False
    T = _u64(proc, p1 + 0x1e0)
    if not T: return False
    hdr = _f32s(proc, T, 20)
    if not hdr: return False
    lp = _u64(proc, T + 0x08)
    key = (round(hdr[8],3), round(hdr[9],3),
           tuple(round(v,6) for v in hdr[10:19]), lp)
    if key in st["seen"]:
        return False
    st["seen"][key] = st["hits"]
    wtab = _u64(proc, rdi + 0x28)
    wt = _f32s(proc, wtab, 2048) if wtab else None
    rec = {"T": hex(T), "wtab": hex(wtab) if wtab else None,
           "wtab_2048": wt, "first_seen_hit": st["hits"],
           "scale_xy": [hdr[0], hdr[1]], "center_xy": [hdr[8], hdr[9]],
           "H_3x3": hdr[10:19], "lut_ptr": hex(lp) if lp else None}
    if lp:
        lut = _f32s(proc, lp, 4096)
        if lut:
            rec["lut_first8"] = lut[:8]
            rec["lut_at"] = {str(i): lut[i] for i in (0,64,256,1024,2048,4095)}
            rec["lut_min"] = min(lut); rec["lut_max"] = max(lut)
    st["captures"].append(rec)
    if len(st["captures"]) >= st["max"]:
        write_report(None, st["out"]); proc.Kill()
    return False

def write_report(debugger, path):
    st = builtins.l16_src2
    out = {k: st[k] for k in ("label","captures","hits","errors")}
    out["n_captures"] = len(st["captures"])
    open(path,"w").write(json.dumps(out, indent=1))
    print("SRC2_WARP_OPERANDS " + json.dumps({"n": len(st["captures"]), "hits": st["hits"]}))
