"""Capture src2 ImageWarpClamped<filter=2> transform operands at worker ENTRY
0x3ed2e0 (once per source). T = *( *(rdi+0x20) + 0x1e0 ). Dumps per-axis scale
T[0]/T[4], center T+0x20/0x24, 3x3 homography T+0x28..0x48, LUT base T+0x08 and
the 4096-float radial LUT. See docs/evidence/static_src2_resampler_*."""
import builtins, json, struct

def reset(label, out_path, max_captures=8):
    builtins.l16_src2 = {"label": label, "out": out_path, "max": int(max_captures),
                         "seen": {}, "captures": [], "errors": []}

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
    proc = frame.GetThread().GetProcess()
    rdi = frame.FindRegister("rdi").GetValueAsUnsigned()
    p0 = _u64(proc, rdi + 0x20)          # rax = *(rdi+0x20)
    if not p0:
        return False
    p1 = _u64(proc, p0)                  # rcx = *rax
    if not p1:
        return False
    T = _u64(proc, p1 + 0x1e0)           # T = *(rcx+0x1e0)
    if not T or T in st["seen"]:
        return False
    st["seen"][T] = True
    rec = {"T": hex(T), "rdi": hex(rdi)}
    hdr = _f32s(proc, T, 20)
    if hdr:
        rec["scale_xy"] = [hdr[0], hdr[1]]
        rec["center_xy"] = [hdr[8], hdr[9]]
        rec["H_3x3"] = hdr[10:19]
    lp = _u64(proc, T + 0x08)
    rec["lut_ptr"] = hex(lp) if lp else None
    if lp:
        lut = _f32s(proc, lp, 4096)
        if lut:
            rec["lut_first16"] = lut[:16]
            rec["lut_at"] = {str(i): lut[i] for i in (0,1,64,256,1024,2048,4095)}
            rec["lut_min"] = min(lut); rec["lut_max"] = max(lut)
    st["captures"].append(rec)
    if len(st["captures"]) >= st["max"]:
        write_report(None, st["out"]); proc.Kill()
    return False

def write_report(debugger, path):
    st = builtins.l16_src2
    out = {k: st[k] for k in ("label","captures","errors")}
    out["n_captures"] = len(st["captures"])
    open(path,"w").write(json.dumps(out, indent=1))
    print("SRC2_WARP_OPERANDS " + json.dumps({"n": len(st["captures"])}))
