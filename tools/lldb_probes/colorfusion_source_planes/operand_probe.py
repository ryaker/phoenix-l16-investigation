"""Capture the per-source registration operands inside ColorFusionBayer::initialize.

Two breakpoints in the SOURCE loop (decoded from libcp_disasm_intel.txt):
  0x1aba80  call 0x1ad390   rdi=&out[rbp-0x3a0]  rsi=&params[rbp-0x3b0]
                            params = { rect_ptr@[rbp-0x3b0], scale f32@[rbp-0x3a8] }
                            rect@[rbp-0x280]: x/y/w/h ints + data ptr @[rbp-0x260]
  0x1aba8f  call 0x19bd20   rdi=&packed[rbp-0x370]  rsi=&desc[rbp-0x3a0] (0x1ad390 out)

Reads exact values only. No tuning. Dumps per source iteration.
"""
import builtins, json, struct

def reset(out_path):
    builtins.l16op = {"out": out_path, "at390": [], "at_bd20": [], "rects": [],
                      "hits390": 0, "hitsbd20": 0, "hitsrect": 0}

def hitrect(frame, loc, d):
    # 0x1ab813: anchor rect TL=eax/ecx BR=esi/edx; source rect r9=TL(x|y<<32) r8=BR;
    # source camera id = [rbp-0x204].
    st = builtins.l16op; st["hitsrect"] += 1
    proc = frame.GetThread().GetProcess()
    rbp = frame.FindRegister("rbp").GetValueAsUnsigned()
    def reg(n): return frame.FindRegister(n).GetValueAsUnsigned()
    def s32(v): return v - (1 << 32) if v >= (1 << 31) else v
    eax = s32(reg("rax") & 0xffffffff); ecx = s32(reg("rcx") & 0xffffffff)
    esi = s32(reg("rsi") & 0xffffffff); edx = s32(reg("rdx") & 0xffffffff)
    r9 = reg("r9"); r8 = reg("r8")
    sid = _rd(proc, rbp - 0x204, 4)
    st["rects"].append({"iter": st["hitsrect"],
        "src_id": struct.unpack("<i", sid)[0] if sid else None,
        "anchor_TL": [eax, ecx], "anchor_BR": [esi, edx],
        "src_TL": [s32(r9 & 0xffffffff), s32((r9 >> 32) & 0xffffffff)],
        "src_BR": [s32(r8 & 0xffffffff), s32((r8 >> 32) & 0xffffffff)]})
    return False

def _rd(proc, addr, n):
    import lldb
    e = lldb.SBError()
    b = proc.ReadMemory(addr, n, e)
    return bytes(b) if e.Success() and b else None

def _u64(proc, a):
    b = _rd(proc, a, 8); return struct.unpack("<Q", b)[0] if b else None

def _desc(proc, addr):
    # standard image descriptor: w@0x10 h@0x14 stride@0x18 data@0x20
    raw = _rd(proc, addr, 0x30)
    if not raw: return None
    w, h, stride = struct.unpack_from("<iii", raw, 0x10)
    data = struct.unpack_from("<Q", raw, 0x20)[0]
    return {"w": w, "h": h, "stride": stride, "data": hex(data), "raw": raw.hex()}

def hit390(frame, loc, d):
    st = builtins.l16op; st["hits390"] += 1
    proc = frame.GetThread().GetProcess()
    rbp = frame.FindRegister("rbp").GetValueAsUnsigned()
    rdi = frame.FindRegister("rdi").GetValueAsUnsigned()
    rsi = frame.FindRegister("rsi").GetValueAsUnsigned()
    params = _rd(proc, rsi, 16)
    rect_ptr = struct.unpack_from("<Q", params, 0)[0] if params else None
    scale = struct.unpack_from("<f", params, 8)[0] if params else None
    # rect window struct lives at [rbp-0x280]; dump 0x40 bytes as ints+float
    win = _rd(proc, rbp - 0x280, 0x40)
    ints = list(struct.unpack_from("<16i", win, 0)) if win else None
    rec = {"iter": st["hits390"], "rsi": hex(rsi), "rdi_out": hex(rdi),
           "rect_ptr": hex(rect_ptr) if rect_ptr else None, "scale": scale,
           "win_ints": ints}
    if rect_ptr:
        rec["rect_desc"] = _desc(proc, rect_ptr)
    st["at390"].append(rec)
    return False

def hitbd20(frame, loc, d):
    st = builtins.l16op; st["hitsbd20"] += 1
    proc = frame.GetThread().GetProcess()
    rdi = frame.FindRegister("rdi").GetValueAsUnsigned()
    rsi = frame.FindRegister("rsi").GetValueAsUnsigned()
    desc = _desc(proc, rsi)
    rec = {"iter": st["hitsbd20"], "in_desc(rsi)": desc, "out_ptr(rdi)": hex(rdi)}
    # Dump the FIRST source's pre-pack plane (the 0x1ad390 output) to derive the
    # exact cropped-phase quad->lane mapping vs the captured f16 pack oracle.
    if desc:
        import os
        w, h, stride = desc["w"], desc["h"], desc["stride"]
        data = int(desc["data"], 16)
        nbytes = stride * h * 4  # single-channel f32
        raw = _rd(proc, data, nbytes)
        if raw:
            idx = st["hitsbd20"] - 1
            outp = os.path.join(os.path.dirname(st["out"]),
                                "bd20_input_src%d_f32.bin" % idx)
            open(outp, "wb").write(raw)
            rec["dumped"] = {"file": outp, "w": w, "h": h, "stride": stride, "bytes": nbytes}
    st["at_bd20"].append(rec)
    return False

def write(path=None):
    st = builtins.l16op
    p = path or st["out"]
    open(p, "w").write(json.dumps({k: st[k] for k in
        ("at390","at_bd20","rects","hits390","hitsbd20","hitsrect")}, indent=1))
    print("SRC_OPERANDS " + json.dumps({"n390": st["hits390"], "nbd20": st["hitsbd20"],
                                        "nrect": st["hitsrect"]}))
