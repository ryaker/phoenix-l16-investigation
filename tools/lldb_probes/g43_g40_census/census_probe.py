# G-43 (SGM directional-path census) + G-40 (per-level hypothesis counts).
# Anchor-only probe on the runPass worker 0x276860. At each entry the SysV args
# are: rdi=StereoLayer (r12), rsi=dims*, edx=scale, ecx=pass/line index, r8=arg.
# Per DISTINCT StereoLayer object we record: guidance dims (+0x288 -> +0x10/+14),
# size fields (+0x2a0/+0x2a4), hypothesis count (+0x23c, doubled -> u16 temp), the
# Line buf (+0x168), split Line buf (+0x148), Min cost buf (+0x198) pointers, mode
# (+0xc), tile-ish (+0x2b8/+0x2bc), and the SET + ordered list of ecx pass indices.
# The 0x276860 bp self-disables after `level_cap` distinct layers are fully
# sampled (`per_level_detail` ecx samples each) to bound the number of LLDB stops.
import builtins
import json
import struct
import time

ANCHOR = 0x276860


def reset(label="", level_cap=6, per_level_detail=600, progress_path=None):
    builtins.l16cen = {
        "label": label, "level_cap": level_cap,
        "per_level_detail": per_level_detail, "progress_path": progress_path,
        "t0": time.time(), "anchor_hits": 0, "layers": {}, "order": [],
        "detail_done": 0, "disabled": False, "bp_id": None,
        "errors": [], "_base": None,
    }


def _s():
    if not hasattr(builtins, "l16cen"):
        reset()
    return builtins.l16cen


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _rd(process, addr, size):
    if not addr or size <= 0:
        return None
    lldb = builtins.__import__("lldb")
    e = lldb.SBError()
    d = process.ReadMemory(addr, size, e)
    return d if (e.Success() and d and len(d) == size) else None


def _u16(p, a):
    d = _rd(p, a, 2)
    return struct.unpack_from("<H", d)[0] if d else None


def _u32(p, a):
    d = _rd(p, a, 4)
    return struct.unpack_from("<I", d)[0] if d else None


def _i32(p, a):
    d = _rd(p, a, 4)
    return struct.unpack_from("<i", d)[0] if d else None


def _i32x(p, a, count):
    d = _rd(p, a, 4 * count)
    return list(struct.unpack_from("<%di" % count, d)) if d else None


def _u64(p, a):
    d = _rd(p, a, 8)
    return struct.unpack_from("<Q", d)[0] if d else None


def _flush():
    st = _s()
    path = st.get("progress_path")
    if not path:
        return
    snap = {"label": st["label"], "elapsed_s": round(time.time() - st["t0"], 1),
            "anchor_hits": st["anchor_hits"], "disabled": st["disabled"],
            "n_layers": len(st["layers"]), "order": st["order"],
            "layers": st["layers"]}
    try:
        with open(path, "w", encoding="utf-8") as h:
            json.dump(snap, h, indent=2, sort_keys=True)
    except Exception as exc:  # noqa
        st["errors"].append("flush:%s" % exc)


def hit(frame, bp_loc, internal_dict):
    st = _s()
    st["anchor_hits"] += 1
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    rdi = _u(frame, "rdi")
    ecx = _u(frame, "rcx") & 0xFFFFFFFF
    ecx_s = ecx - (1 << 32) if ecx >= (1 << 31) else ecx
    edx = _u(frame, "rdx") & 0xFFFFFFFF
    r8 = _u(frame, "r8")
    rsi = _u(frame, "rsi")
    # dims-struct (rsi arg) contents, read from memory only once per distinct
    # pointer (cache) to keep the anchor sweep at census speed.
    rcache = st.setdefault("_rsi_cache", {})
    dims = rcache.get(rsi)
    if dims is None:
        dims = (_u32(process, rsi + 0), _u32(process, rsi + 4))
        rcache[rsi] = dims
    key = str(rdi)
    lay = st["layers"].get(key)
    if lay is None:
        guide = _u64(process, rdi + 0x288)
        lay = {
            "layer_ptr": rdi, "first_hit_t": round(time.time() - st["t0"], 1),
            "first_anchor_n": st["anchor_hits"],
            "mode_0xc": _u32(process, rdi + 0xC),
            "guidance_ptr_0x288": guide,
            "guidance_w": _u32(process, (guide or 0) + 0x10),
            "guidance_h": _u32(process, (guide or 0) + 0x14),
            "size_0x2a0": _u32(process, rdi + 0x2A0),
            "size_0x2a4": _u32(process, rdi + 0x2A4),
            "dims_0x2b8": _u32(process, rdi + 0x2B8),
            "dims_0x2bc": _u32(process, rdi + 0x2BC),
            "hyp_count_0x23c": _i32(process, rdi + 0x23C),
            "vec0xe0_begin": _u64(process, rdi + 0xE0),
            "vec0xe0_end": _u64(process, rdi + 0xE8),
            "vec0xe0_count_f32": (
                (_u64(process, rdi + 0xE8) - _u64(process, rdi + 0xE0)) // 4
                if (_u64(process, rdi + 0xE0) and _u64(process, rdi + 0xE8))
                else None),
            "linebuf_0x168": _u64(process, rdi + 0x168),
            "linebuf_split_0x148": _u64(process, rdi + 0x148),
            "mincost_0x198": _u64(process, rdi + 0x198),
            "pixelbuf_0x1e8": _u64(process, rdi + 0x1E8),
            "pixelbuf_0x200": _u64(process, rdi + 0x200),
            "direction_ptr_r8": r8,
            "direction_offsets_i32": _i32x(process, r8, 4),
            "call_count": 0, "ecx_set": [], "ecx_first40": [],
            "ecx_counts": {}, "edx_set": [], "r8_low_set": [],
            "ecx_runs": [], "dir_tuples": [],
            "ecx_seq120": [],
        }
        st["layers"][key] = lay
        st["order"].append({"ptr": rdi, "w": lay["guidance_w"],
                            "h": lay["guidance_h"], "hyp": lay["hyp_count_0x23c"],
                            "at_anchor_n": st["anchor_hits"]})
        _flush()
    lay["call_count"] += 1
    ecx_key = str(ecx_s)
    lay["ecx_counts"][ecx_key] = lay["ecx_counts"].get(ecx_key, 0) + 1
    if not lay["ecx_runs"] or lay["ecx_runs"][-1][0] != ecx_s:
        lay["ecx_runs"].append([ecx_s, 1])
    else:
        lay["ecx_runs"][-1][1] += 1
    tup = [ecx_s, dims[0], dims[1], edx]
    if tup not in lay["dir_tuples"] and len(lay["dir_tuples"]) < 40:
        lay["dir_tuples"].append(tup)
    if len(lay["ecx_seq120"]) < 120:
        lay["ecx_seq120"].append(ecx_s)
    if len(lay["ecx_first40"]) < 40:
        lay["ecx_first40"].append(ecx_s)
    if ecx_s not in lay["ecx_set"] and len(lay["ecx_set"]) < 4200:
        lay["ecx_set"].append(ecx_s)
    if edx not in lay["edx_set"] and len(lay["edx_set"]) < 40:
        lay["edx_set"].append(edx)
    r8l = r8 & 0xFFFFFFFF
    if r8l not in lay["r8_low_set"] and len(lay["r8_low_set"]) < 40:
        lay["r8_low_set"].append(r8l)
    # bound total stops: characterize only the first `level_cap` DISTINCT
    # layers (coarse->fine, sequential). Disable once the newest-seen layer has
    # >= per_level_detail calls AND we have >= level_cap layers, so the render
    # then runs free instead of servicing ~160k finer-level stops.
    if not st["disabled"] and len(st["layers"]) >= st["level_cap"]:
        newest_key = str(st["order"][-1]["ptr"])
        if st["layers"][newest_key]["call_count"] >= st["per_level_detail"]:
            bp = target.FindBreakpointByID(st["bp_id"]) if st["bp_id"] else None
            if bp and bp.IsValid():
                bp.SetEnabled(False)
            st["disabled"] = True
            _flush()
            process.Kill()
            return True
    if st["anchor_hits"] % 500 == 0:
        _flush()
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    for i in range(target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(i)
        if not bp or not bp.IsValid() or bp.GetNumLocations() < 1:
            continue
        va = bp.GetLocationAtIndex(0).GetAddress().GetFileAddress()
        if va == ANCHOR:
            bp.SetScriptCallbackFunction("census_probe.hit")
            _s()["bp_id"] = bp.GetID()
    print("L16_CENSUS_ATTACHED bp_id=%s" % _s().get("bp_id"))


def drive(debugger, max_steps=20000000):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while (process.IsValid() and process.GetState() == lldb.eStateStopped
           and steps < max_steps):
        steps += 1
        process.Continue()
    _s()["drive_steps"] = steps
    _flush()
    print("L16_CENSUS_DRIVE_STEPS %s" % steps)


def write_report(debugger, path):
    import hashlib
    st = dict(_s())
    lldb = builtins.__import__("lldb")
    target = debugger.GetSelectedTarget()
    p = target.GetProcess()
    st["proc_state"] = lldb.SBDebugger.StateAsCString(p.GetState()) if p else None
    st["exit_status"] = p.GetExitStatus() if p else None
    for m in target.module_iter():
        if str(m.GetFileSpec().GetFilename()) == "libcp.dylib":
            try:
                st["libcp_sha256"] = hashlib.sha256(
                    open(m.GetFileSpec().fullpath, "rb").read()).hexdigest()
            except Exception as exc:  # noqa
                st["libcp_sha256"] = "err:%s" % exc
    with open(path, "w", encoding="utf-8") as h:
        json.dump(st, h, indent=2, sort_keys=True)
        h.write("\n")
    print("L16_CENSUS_WROTE %s" % path)
