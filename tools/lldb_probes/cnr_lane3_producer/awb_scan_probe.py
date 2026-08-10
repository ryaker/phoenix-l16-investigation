"""awb_scan_probe.py -- find the CNR guide's source image by scanning live Lumen.

At the CNR body 0x34b3f0 (inside setWhiteBalance's $_22 lambda) sweep the stack,
the functor (rdi), and the task (rsi) for anything shaped like an image
descriptor (w@+0x10, h@+0x14, stride@+0x18, data@+0x20), sampling each as both
u16 and f32.  Capture the guide (task+0x60) at the same hit.  Offline we then
match the half-res guide to a downsample of whichever image fits -- checking
Lumen, not inferring.
"""
import builtins
import json
import os
import struct

CNRBODY = 0x34B3F0


def reset(label="", report_path="", cap=2):
    builtins.l16_scan = {"label": label, "report_path": report_path, "cap": cap,
                          "breakpoint_ids": {}, "events": [], "errors": []}


def _s():
    if not hasattr(builtins, "l16_scan"):
        reset()
    return builtins.l16_scan


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


def _plausible_ptr(v):
    return (0x100000000 < v < 0x00007FFFFFFFFFFF)


def _try_descriptor(proc, addr):
    """If addr looks like an image struct, decode + sample. Else None."""
    raw = _read(proc, addr, 0x28)
    if raw is None:
        return None
    w, h, stride = struct.unpack_from("<iii", raw, 0x10)
    data = struct.unpack_from("<Q", raw, 0x20)[0]
    if not (8 <= w <= 8192 and 8 <= h <= 8192 and w <= stride <= 4 * w + 64):
        return None
    if not _plausible_ptr(data):
        return None
    out = {"desc_addr": addr, "width": w, "height": h, "stride": stride,
           "data_ptr": data}
    # sample as u16 (2-byte elems) and f32 (4-byte elems), first 2 rows
    u16 = _read(proc, data, min(w, 32) * 2)
    if u16:
        vals = list(struct.unpack("<" + "H" * (len(u16) // 2), u16))
        out["as_u16_row0"] = vals[:16]
        out["u16_max"] = max(vals)
    f32 = _read(proc, data, min(w, 32) * 4)
    if f32:
        vals = list(struct.unpack("<" + "f" * (len(f32) // 4), f32))
        out["as_f32_row0"] = [round(v, 5) for v in vals[:16]]
    return out


def _scan(proc, start, count_qwords):
    """Scan a memory window; for each plausible pointer, test it and its target
    as an image descriptor."""
    found = []
    blob = _read(proc, start, count_qwords * 8)
    if blob is None:
        return found
    seen = set()
    for i in range(count_qwords):
        v = struct.unpack_from("<Q", blob, i * 8)[0]
        for cand in (start + i * 8, v):  # descriptor-inline, or pointer-to-descriptor
            if cand in seen or not _plausible_ptr(cand):
                continue
            seen.add(cand)
            desc = _try_descriptor(proc, cand)
            if desc:
                found.append(desc)
    return found


def _guide(proc, task):
    raw = _read(proc, task, 0x80)
    if raw is None:
        return None
    data = struct.unpack_from("<Q", raw, 0x60)[0]
    w, h = struct.unpack_from("<ii", raw, 0x50)
    stride = struct.unpack_from("<i", raw, 0x58)[0]
    g = {"data_ptr": data, "dims": [w, h], "stride": stride}
    if data and 0 < w < 20000 and stride > 0:
        rows = []
        for r in range(min(4, h)):
            row = _read(proc, data + (r * stride) * 4, min(w, 32) * 4)
            if row:
                rows.append([round(x, 5) for x in
                             struct.unpack("<" + "f" * (len(row) // 4), row)])
        g["rows_f32"] = rows
    return g


def _dump_buffer(proc, data_ptr, nbytes, path):
    """Read nbytes from data_ptr in chunks; write to raw file. Returns bytes."""
    got = 0
    with open(path, "wb") as fh:
        off = 0
        while off < nbytes:
            chunk = _read(proc, data_ptr + off, min(0x8000, nbytes - off))
            if chunk is None:
                break
            fh.write(chunk)
            off += len(chunk)
            got += len(chunk)
    return got


def cnr_body(frame, bp_loc, _d):
    st = _s()
    proc = frame.GetThread().GetProcess()
    target = proc.GetTarget()
    rsp = _u(frame, "rsp")
    rdi = _u(frame, "rdi")
    rsi = _u(frame, "rsi")
    outdir = os.path.dirname(st["report_path"])
    seq = len(st["events"]) + 1
    # rescan for candidates
    cands = _scan(proc, rsp, 0x200) + _scan(proc, rdi, 0x40) + _scan(proc, rsi, 0x20)
    # dedup by data_ptr
    uniq = {}
    for c in cands:
        uniq.setdefault(c["data_ptr"], c)
    # guide (task+0x60)
    graw = _read(proc, rsi, 0x80)
    guide_meta = None
    if graw:
        gdata = struct.unpack_from("<Q", graw, 0x60)[0]
        gw, gh = struct.unpack_from("<ii", graw, 0x50)
        gstride = struct.unpack_from("<i", graw, 0x58)[0]
        if gdata and 0 < gw < 4000 and gstride > 0:
            gp = os.path.join(outdir, f"guide_seq{seq}_{gw}x{gh}_str{gstride}.f32")
            n = _dump_buffer(proc, gdata, gh * gstride * 4, gp)
            guide_meta = {"path": gp, "w": gw, "h": gh, "stride": gstride,
                          "bytes": n, "data_ptr": gdata}
    # dump every tile-local candidate (dims < 700) and the full image
    dumped = []
    for dp, c in uniq.items():
        w, h, stride = c["width"], c["height"], c["stride"]
        # dump tile-local (small) as-is; for the 4160 full image dump a smaller crop
        if w <= 700 and h <= 700:
            elem = 4  # assume f32 storage for tile-local pipeline buffers
            p = os.path.join(outdir, f"cand_seq{seq}_{w}x{h}_str{stride}_{dp:x}.raw")
            n = _dump_buffer(proc, dp, h * stride * elem, p)
            dumped.append({**c, "path": p, "bytes": n, "assumed_elem": elem})
        elif w >= 2000:
            # full-sensor u16 image: dump first 600 rows for characterization
            elem = 2
            p = os.path.join(outdir, f"full_seq{seq}_{w}x{h}_str{stride}_{dp:x}.u16")
            n = _dump_buffer(proc, dp, 600 * stride * elem, p)
            dumped.append({**c, "path": p, "bytes": n, "assumed_elem": elem,
                           "partial_rows": 600})
    st["events"].append({"seq": seq, "guide": guide_meta, "dumped": dumped,
                          "candidates": list(uniq.values())})
    if seq >= int(st["cap"]):
        bid = st["breakpoint_ids"].get("cnr")
        bp = target.FindBreakpointByID(bid) if bid else None
        if bp and bp.IsValid():
            bp.SetEnabled(False)
        proc.Kill()
    return False


def install(debugger):
    st = _s()
    target = debugger.GetSelectedTarget()
    before = target.GetNumBreakpoints()
    debugger.HandleCommand("breakpoint set --shlib libcp.dylib --address 0x34b3f0")
    if target.GetNumBreakpoints() > before:
        bp = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
        bp.SetScriptCallbackFunction("awb_scan_probe.cnr_body")
        st["breakpoint_ids"]["cnr"] = bp.GetID()
    print("AWB_SCAN_INSTALLED", st["breakpoint_ids"])


def drive(debugger, max_steps=60000):
    lldb = builtins.__import__("lldb")
    proc = debugger.GetSelectedTarget().GetProcess()
    n = 0
    while proc.IsValid() and proc.GetState() == lldb.eStateStopped and n < max_steps:
        n += 1
        proc.Continue()
    print("AWB_SCAN_DRIVE", n)


def write_report(debugger, path=""):
    out = path or _s().get("report_path")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as h:
        json.dump(dict(_s()), h, indent=2, sort_keys=True, default=str)
    print("WROTE", out)
