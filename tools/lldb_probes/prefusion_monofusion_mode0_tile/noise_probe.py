"""Capture the exact arguments and return value of MonoFusion patch-noise
helper 0x18e940 as called from the mode-0 reducer at 0x1a464d.

Decoded signature (from libcp.dylib disassembly):
    float helper(view_t *rdi, const float *rsi, float mu /*xmm0*/)
  rsi[0]=a  rsi[1]=b  rsi[2]=black  rsi[3]=white
  view: +0x10 width, +0x14 height, +0x18 stride(elems), +0x20 data(float*)
  V = (white*mu)^2 * max(1e-5, a*z + b)
  z = max(black/white, (black + (H-black)/mu)/white)
  H = sqrt(P / sum_j 1/(I_j+0.1)^2)   over the view pixels
"""

import builtins
import json
import struct


def reset(run_dir):
    builtins.l16_noise = {"run_dir": str(run_dir), "hits": [], "pending": None}


def _s():
    return builtins.l16_noise


def _read(process, addr, size):
    lldb = builtins.__import__("lldb")
    err = lldb.SBError()
    raw = process.ReadMemory(addr, size, err)
    if not err.Success() or raw is None or len(raw) != size:
        return None
    return raw


def _f32(frame, name):
    lldb = builtins.__import__("lldb")
    reg = frame.FindRegister(name)
    err = lldb.SBError()
    data = reg.GetData()
    v = data.GetFloat(err, 0)
    return float(v) if err.Success() else None


def _window(process, base, rec, tag):
    """Read a 0x30-byte image view descriptor and its pixels."""
    raw = _read(process, base, 0x30)
    if not raw:
        return
    ints = struct.unpack_from("<8i", raw)
    ptr = struct.unpack_from("<Q", raw, 0x20)[0]
    w, h, stride = ints[4], ints[5], ints[6]
    rec[tag + "_ints"] = list(ints)
    rec[tag + "_ptr"] = ptr
    rec[tag + "_w"], rec[tag + "_h"], rec[tag + "_stride"] = w, h, stride
    if not (0 < w <= 64 and 0 < h <= 64 and stride > 0 and ptr):
        return
    px = []
    for y in range(h):
        r = _read(process, ptr + y * stride * 4, w * 4)
        if r is None:
            return
        px.extend(struct.unpack("<%df" % w, r))
    rec[tag + "_mean"] = sum(px) / len(px)
    rec[tag + "_min"] = min(px)
    rec[tag + "_max"] = max(px)
    s = 0.0
    for I in px:
        t = 1.0 / (I + 0.1)
        s += t * t
    rec[tag + "_H"] = (len(px) / s) ** 0.5


def on_muview(frame, bp_loc, internal_dict):
    """0x1a4524: the window the caller just summed is still live at -0x1600."""
    st = _s()
    if len(st["hits"]) >= 24:
        return False
    process = frame.GetThread().GetProcess()
    tid = frame.GetThread().GetThreadID()
    rbp = frame.FindRegister("rbp").GetValueAsUnsigned()
    rec = {"muview_sum_xmm0": _f32(frame, "xmm0")}
    _window(process, rbp - 0x1600, rec, "muview")
    st.setdefault("muview_by_tid", {})[tid] = rec
    return False


def on_entry(frame, bp_loc, internal_dict):
    st = _s()
    if len(st["hits"]) >= 24:
        return False
    process = frame.GetThread().GetProcess()
    tid = frame.GetThread().GetThreadID()
    rdi = frame.FindRegister("rdi").GetValueAsUnsigned()
    rsi = frame.FindRegister("rsi").GetValueAsUnsigned()
    rbp = frame.FindRegister("rbp").GetValueAsUnsigned()
    mu = _f32(frame, "xmm0")

    rec = {"tid": tid, "rdi": rdi, "rsi": rsi, "mu": mu}
    pre = st.setdefault("muview_by_tid", {}).pop(tid, None)
    if pre:
        rec.update(pre)

    raw = _read(process, rsi, 16)
    if raw:
        a, b, black, white = struct.unpack("<4f", raw)
        rec["a"] = a
        rec["b"] = b
        rec["black"] = black
        rec["white"] = white
    raw = _read(process, rsi, 64)
    if raw:
        rec["noise_struct_64"] = list(struct.unpack("<16f", raw))

    raw = _read(process, rdi, 0x30)
    if raw:
        ints = struct.unpack_from("<8i", raw)
        rec["view_ints"] = list(ints)
        ptr, ptr2 = struct.unpack_from("<2Q", raw, 0x20)
        rec["view_ptr"] = ptr
        rec["view_ptr2"] = ptr2
        w = ints[4]
        h = ints[5]
        stride = ints[6]
        rec["w"], rec["h"], rec["stride"] = w, h, stride
        if 0 < w <= 64 and 0 < h <= 64 and stride > 0 and ptr:
            px = []
            ok = True
            for y in range(h):
                r = _read(process, ptr + y * stride * 4, w * 4)
                if r is None:
                    ok = False
                    break
                px.extend(struct.unpack("<%df" % w, r))
            if ok:
                rec["patch"] = px
                rec["patch_mean"] = sum(px) / len(px)
                s = 0.0
                for I in px:
                    t = 1.0 / (I + 0.1)
                    s += t * t
                rec["H"] = (len(px) / s) ** 0.5
    st.setdefault("by_tid", {})[tid] = rec
    return False


def on_return(frame, bp_loc, internal_dict):
    st = _s()
    tid = frame.GetThread().GetThreadID()
    rec = st.setdefault("by_tid", {}).pop(tid, None)
    if rec is None:
        return False
    rec["V_returned"] = _f32(frame, "xmm0")
    st["hits"].append(rec)
    if len(st["hits"]) >= 24:
        frame.GetThread().GetProcess().Kill()
    return False


def report():
    st = _s()
    path = st["run_dir"] + "/noise_helper.json"
    slim = []
    for h in st["hits"]:
        d = {k: v for k, v in h.items() if k != "patch"}
        slim.append(d)
    with open(path, "w") as f:
        json.dump({"hits": st["hits"]}, f)
    print("WROTE", path, "hits=", len(st["hits"]))
    for i, d in enumerate(slim):
        print("HIT", i, json.dumps(d))
