# G-42 residual: re-pin the local matching-cost proof to the exact index-5
# StereoLayer<false> level (guidance 2080x1560, tile 1). Coarse->fine, the
# runPass 0x276860 is entered once per level with guidance dims that encode the
# level: tile 32->65x49 (idx0) ... tile 1->2080x1560 (idx5). Hot per-pixel bps
# stay DISABLED until the anchor sees the exact index-5 guidance dims, so the
# render reaches index-5 at Rosetta speed; then 12 (operand,cost) pairs are
# captured and the process is killed.
#
# NEW vs v1: every anchor hit appends a census row (mode, guidance dims, ts) and
# FLUSHES a small progress JSON, so the long reach-to-index-5 render is
# observable by polling instead of blind. Enable condition is EXACT dims
# (configurable) rather than a relaxed mode8-count fallback.
import builtins
import json
import struct
import time

ANCHOR = 0x276860        # runPass mode-8 control (rdi = StereoLayer)
WORKER_ENTRY = 0x2732F0  # local matching-cost worker entry
OP_SITE = 0x2735BF       # operands ready: xmm1/xmm2/xmm3 = source patches
COST_SITE = 0x2736A9     # addw %si,(%rcx): esi=cost, rcx=accumulator ptr

HOT = ("worker_entry_2732f0", "operands_2735bf", "cost_accum_2736a9")
SITES = {
    ANCHOR: "anchor_runpass_mode8_276860",
    WORKER_ENTRY: "worker_entry_2732f0",
    OP_SITE: "operands_2735bf",
    COST_SITE: "cost_accum_2736a9",
}


def reset(label="", pair_cap=12, exact_w=2080, exact_h=1560,
          progress_path=None):
    builtins.l16_g42v2 = {
        "label": label, "pair_cap": pair_cap,
        "exact_w": exact_w, "exact_h": exact_h,
        "progress_path": progress_path,
        "counts": {name: 0 for name in SITES.values()},
        "anchor_ok": False, "anchor_level": None, "anchor_trip_dims": None,
        "census": [], "t0": time.time(),
        "worker_first_stack": None, "latest_op_by_thread": {},
        "pairs": [], "errors": [], "hot_enabled": False,
        "capture_complete": False, "breakpoint_ids": {},
    }


def _state():
    if not hasattr(builtins, "l16_g42v2"):
        reset()
    return builtins.l16_g42v2


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    if not addr or size <= 0:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _hex(process, addr, size):
    d = _read(process, addr, size)
    return d.hex() if d is not None else None


def _u16(process, addr):
    d = _read(process, addr, 2)
    return struct.unpack_from("<H", d)[0] if d is not None else None


def _u32(process, addr):
    d = _read(process, addr, 4)
    return struct.unpack_from("<I", d)[0] if d is not None else None


def _u64(process, addr):
    d = _read(process, addr, 8)
    return struct.unpack_from("<Q", d)[0] if d is not None else None


def _xmm(frame, name):
    lldb = builtins.__import__("lldb")
    reg = frame.FindRegister(name)
    if not reg or not reg.IsValid():
        return None
    data = reg.GetData()
    if not data or data.GetByteSize() < 16:
        return None
    error = lldb.SBError()
    out = bytearray()
    for i in range(16):
        out.append(data.GetUnsignedInt8(error, i))
        if not error.Success():
            return None
    return bytes(out).hex()


def _libcp_base(target):
    st = _state()
    cached = st.get("_libcp_base")
    if cached is not None:
        return cached
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                st["_libcp_base"] = base
                return base
    return None


def _va(target, pc):
    base = _libcp_base(target)
    if base is not None and pc >= base:
        return pc - base
    return None


def _stack(thread, target, maxf=16):
    out = []
    for i in range(min(thread.GetNumFrames(), maxf)):
        f = thread.GetFrameAtIndex(i)
        out.append({"i": i, "pc": f.GetPC(), "libcp_va": _va(target, f.GetPC()),
                    "fn": f.GetFunctionName()})
    return out


def _set_enabled(target, names, enabled):
    ids = _state().get("breakpoint_ids", {})
    for name in names:
        bid = ids.get(name)
        if bid is None:
            continue
        bp = target.FindBreakpointByID(bid)
        if bp and bp.IsValid():
            bp.SetEnabled(enabled)


def _flush_progress():
    st = _state()
    path = st.get("progress_path")
    if not path:
        return
    snap = {
        "label": st["label"], "elapsed_s": round(time.time() - st["t0"], 1),
        "anchor_ok": st["anchor_ok"], "anchor_level": st["anchor_level"],
        "anchor_trip_dims": st["anchor_trip_dims"],
        "hot_enabled": st["hot_enabled"], "pairs_captured": len(st["pairs"]),
        "capture_complete": st["capture_complete"],
        "counts": st["counts"],
        "max_guidance_seen": st.get("max_gw", 0),
        "dims_hist": st.get("dims_hist", {}),
        "transitions": st.get("transitions", []),
    }
    try:
        with open(path, "w", encoding="utf-8") as h:
            json.dump(snap, h, indent=2, sort_keys=True)
    except Exception as exc:  # noqa
        st["errors"].append(f"flush:{exc}")


def _anchor_hit(frame, process, target):
    st = _state()
    rdi = _u(frame, "rdi")
    # Per-hit speed: read guidance dims from MEMORY only when the layer object
    # (rdi) is new; otherwise reuse the cached dims. Rosetta SB ReadMemory is
    # ~250ms; register-only per-hit keeps the anchor sweep at census speed.
    cache = st.setdefault("_dims_cache", {})
    cached = cache.get(rdi)
    if cached is None:
        mode = _u32(process, rdi + 0xC)
        guide = _u64(process, rdi + 0x288)
        gw = _u32(process, (guide or 0) + 0x10)
        gh = _u32(process, (guide or 0) + 0x14)
        cache[rdi] = (mode, gw, gh)
    else:
        mode, gw, gh = cached
    key = "%sx%s@m%s" % (gw, gh, mode)
    hist = st.setdefault("dims_hist", {})
    hist[key] = hist.get(key, 0) + 1
    if (gw or 0) > st.get("max_gw", 0):
        st["max_gw"] = gw or 0
    changed = (key != st.get("_last_key"))
    if changed:
        st["_last_key"] = key
        st.setdefault("transitions", []).append(
            {"t": round(time.time() - st["t0"], 1), "key": key,
             "layer": rdi, "gw": gw, "gh": gh, "mode": mode,
             "anchor_n": st["counts"].get("anchor_runpass_mode8_276860")})
    # O(1) per-hit: flush only on level change or ~every 400 hits (heartbeat)
    n = st["counts"].get("anchor_runpass_mode8_276860", 0)
    if changed or (n % 400 == 0):
        _flush_progress()
    if st["anchor_ok"]:
        return
    if mode == 8 and gw == st["exact_w"] and gh == st["exact_h"]:
        st["anchor_ok"] = True
        st["anchor_level"] = "index5_2080x1560"
        st["anchor_trip_dims"] = {"w": gw, "h": gh}
        # Create the hot capture bps ONLY now (index-5), by libcp load address.
        # Pre-setting them at coarse levels throttles the Rosetta process even
        # while disabled, so we defer their existence until the target level.
        base = _libcp_base(target)
        addr_map = {WORKER_ENTRY: "worker_entry_2732f0",
                    OP_SITE: "operands_2735bf", COST_SITE: "cost_accum_2736a9"}
        ids = st.setdefault("breakpoint_ids", {})
        for off, nm in addr_map.items():
            bp = target.BreakpointCreateByAddress(base + off)
            bp.SetScriptCallbackFunction("g42_cost_probe_v2.hit")
            ids[nm] = bp.GetID()
        st["hot_enabled"] = True
        _flush_progress()


def _capture_operands(frame, process):
    st = _state()
    rbp = _u(frame, "rbp")
    rdi = _u(frame, "rdi")
    k = _u64(process, rbp - 0x90)
    src_obj = _u64(process, rbp - 0x98)
    accum_ptr = _u64(process, rbp - 0xA8)
    weight_ptr = _u64(process, rdi + 0x80)
    sample = {
        "thread": frame.GetThread().GetThreadID(),
        "context_rdi": rdi, "source_index_k": k, "source_obj_rsi": src_obj,
        "source_bound_x0": _u32(process, (src_obj or 0) + 0x0),
        "source_bound_y0": _u32(process, (src_obj or 0) + 0x4),
        "source_bound_x1": _u32(process, (src_obj or 0) + 0x8),
        "source_bound_y1": _u32(process, (src_obj or 0) + 0xC),
        "source_stride_0x18": _u32(process, (src_obj or 0) + 0x18),
        "source_data_ptr_0x20": _u64(process, (src_obj or 0) + 0x20),
        "accum_ptr": accum_ptr,
        "accum_u16_before": _u16(process, accum_ptr) if accum_ptr else None,
        "src_patch0_xmm3": _xmm(frame, "xmm3"),
        "src_patch1_xmm1": _xmm(frame, "xmm1"),
        "src_patch2_xmm2": _xmm(frame, "xmm2"),
        "ref_patch0_0x50": _hex(process, rdi + 0x50, 16),
        "ref_patch1_0x60": _hex(process, rdi + 0x60, 16),
        "ref_patch2_0x70": _hex(process, rdi + 0x70, 16),
        "cap_0x40": _hex(process, rdi + 0x40, 16),
        "weight8_hex": _hex(process, (weight_ptr or 0) + 8 * (k or 0), 8),
        "weight_base_0x80": weight_ptr,
        "round_const_xmm8": _xmm(frame, "xmm8"),
        "maxcap_xmm9": _xmm(frame, "xmm9"),
        "zero_xmm12": _xmm(frame, "xmm12"),
    }
    st["latest_op_by_thread"][str(sample["thread"])] = sample


def _capture_cost(frame, process, target):
    st = _state()
    tid = frame.GetThread().GetThreadID()
    op = st["latest_op_by_thread"].get(str(tid))
    if op is None:
        return
    esi = _u(frame, "rsi") & 0xFFFFFFFF
    rcx = _u(frame, "rcx")
    pair = dict(op)
    pair["cost_esi"] = esi
    pair["cost_accum_ptr_rcx"] = rcx
    pair["accum_u16_at_cost_before"] = _u16(process, rcx)
    pair["accum_ptr_matches"] = (rcx == op.get("accum_ptr"))
    pair["guidance_dims_at_capture"] = st["anchor_trip_dims"]
    st["pairs"].append(pair)
    st["latest_op_by_thread"].pop(str(tid), None)
    if len(st["pairs"]) >= st["pair_cap"]:
        st["capture_complete"] = True
        _set_enabled(target, HOT, False)
        st["hot_enabled"] = False
        _flush_progress()


def hit(frame, bp_loc, internal_dict):
    st = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    va = _va(target, frame.GetPC())
    name = SITES.get(va)
    if name is None:
        st["errors"].append(f"unknown site {va}")
        return False
    st["counts"][name] = st["counts"].get(name, 0) + 1
    if va == ANCHOR:
        _anchor_hit(frame, process, target)
        return False
    if not st["anchor_ok"]:
        return False
    if va == WORKER_ENTRY:
        if st["worker_first_stack"] is None:
            st["worker_first_stack"] = _stack(thread, target)
            _set_enabled(target, ("worker_entry_2732f0",), False)
        return False
    if va == OP_SITE:
        _capture_operands(frame, process)
        return False
    if va == COST_SITE:
        _capture_cost(frame, process, target)
        if st["capture_complete"]:
            process.Kill()
            return True
        return False
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    ids = {}
    for i in range(target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(i)
        if not bp or not bp.IsValid() or bp.GetNumLocations() < 1:
            continue
        va = bp.GetLocationAtIndex(0).GetAddress().GetFileAddress()
        name = SITES.get(va)
        if name is None:
            continue
        bp.SetScriptCallbackFunction("g42_cost_probe_v2.hit")
        ids[name] = bp.GetID()
    _state()["breakpoint_ids"] = ids
    _set_enabled(target, HOT, False)
    print("L16_G42V2_ATTACHED", json.dumps(ids, sort_keys=True))


def drive(debugger, max_steps=5000000):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while (process.IsValid() and process.GetState() == lldb.eStateStopped
           and steps < max_steps and not _state().get("capture_complete")):
        steps += 1
        process.Continue()
    _state()["drive_steps"] = steps
    _flush_progress()
    print("L16_G42V2_DRIVE_STEPS", steps)


def _proc(debugger):
    lldb = builtins.__import__("lldb")
    p = debugger.GetSelectedTarget().GetProcess()
    if not p or not p.IsValid():
        return {"valid": False}
    return {"valid": True, "state": lldb.SBDebugger.StateAsCString(p.GetState()),
            "exit_status": p.GetExitStatus()}


def _libcp_sha(debugger):
    import hashlib
    target = debugger.GetSelectedTarget()
    for m in target.module_iter():
        if str(m.GetFileSpec().GetFilename()) == "libcp.dylib":
            path = m.GetFileSpec().fullpath
            try:
                return hashlib.sha256(open(path, "rb").read()).hexdigest()
            except Exception as exc:  # noqa
                return f"err:{exc}"
    return None


def write_report(debugger, path):
    st = dict(_state())
    st["process"] = _proc(debugger)
    st["libcp_sha256"] = _libcp_sha(debugger)
    with open(path, "w", encoding="utf-8") as h:
        json.dump(st, h, indent=2, sort_keys=True)
        h.write("\n")
    print("L16_G42V2_WROTE", path)
