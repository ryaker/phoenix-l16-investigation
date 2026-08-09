"""Dump Lumen's StereoLayer Images[0..4] full planes (anchor + 4 sources).

Guidance (Images[0]) is at layer+0x288; the full Images vector is at
layer+0x240 (begin) / +0x248 (end), elements are descriptor POINTERS (8B).
Descriptor is 0x30 bytes: origin[2i], bounds[2i], size[2i]=w,h, stride, data,
allocation.  Byte-exact port verification for the stereo source operands.
"""
import builtins, hashlib, json, struct, os

BP = 0x276A01  # PROJECTION_VECTOR_AFTER (same as guidance_pyramid_probe)

def reset(label="", outdir="/tmp/srcplanes"):
    builtins.l16_src = {"label": label, "outdir": outdir, "hits": 0,
                         "planes": [], "vec_dumps": [], "errors": [], "done": False}
    os.makedirs(outdir, exist_ok=True)

def _state():
    if not hasattr(builtins, "l16_src"): reset()
    return builtins.l16_src

def _read(process, address, size):
    if not address or size <= 0: return None
    lldb = builtins.__import__("lldb"); err = lldb.SBError()
    raw = process.ReadMemory(address, size, err)
    return raw if err.Success() and raw is not None and len(raw) == size else None

def _u(frame, name): return frame.FindRegister(name).GetValueAsUnsigned()
def _u64(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<Q", raw)[0] if raw is not None else None

def _descriptor(process, address):
    raw = _read(process, address, 0x30)
    if raw is None: return None
    w = struct.unpack("<8iQQ", raw)
    return {"size": list(w[4:6]), "stride": w[6], "data": w[8]}

def hit(frame, bp_loc, internal_dict):
    st = _state(); process = frame.GetThread().GetProcess(); st["hits"] += 1
    layer = _u(frame, "r12")
    im = _read(process, layer + 0x08, 8)
    if im is None: return False
    index, mode = struct.unpack("<2I", im)
    if index != 5 or mode != 8: return False   # only the 2080x1560 full level
    if st["planes"]: return False               # once
    # raw vector region for layout confirmation
    reg = _read(process, layer + 0x240, 0x30)
    st["vec_dumps"].append({"layer": layer, "region_0x240": reg.hex() if reg else None})
    begin = _u64(process, layer + 0x240); end = _u64(process, layer + 0x248)
    if not begin or not end or end < begin:
        st["errors"].append("bad Images vec begin=%r end=%r" % (begin, end)); return False
    count = (end - begin) // 8
    for k in range(min(count, 10)):
        dptr = _u64(process, begin + 8 * k)
        d = _descriptor(process, dptr) if dptr else None
        if not d: st["errors"].append("img %d desc read fail (ptr=%r)" % (k, dptr)); continue
        w, h = d["size"]; stride = d["stride"]; data = d["data"]
        if not (0 < w <= 2080 and 0 < h <= 1560 and stride >= w and data):
            st["errors"].append("img %d insane desc %r" % (k, d)); continue
        rows = bytearray(); ok = True
        for y in range(h):
            r = _read(process, data + y * stride * 4, w * 4)
            if r is None: ok = False; break
            rows += r
        if not ok: st["errors"].append("img %d plane read fail" % k); continue
        path = os.path.join(st["outdir"], "src_image%d_%dx%d.rgba8" % (k, w, h))
        with open(path, "wb") as f: f.write(bytes(rows))
        st["planes"].append({"k": k, "w": w, "h": h, "stride": stride,
                              "sha256": hashlib.sha256(bytes(rows)).hexdigest(),
                              "bytes": len(rows), "path": path})
    st["done"] = process.Kill().Success()
    return False

def attach(debugger):
    target = debugger.GetSelectedTarget(); found = False
    for i in range(target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(i)
        if not bp or not bp.IsValid() or bp.GetNumLocations() < 1: continue
        if bp.GetLocationAtIndex(0).GetAddress().GetFileAddress() == BP:
            bp.SetScriptCallbackFunction("source_planes_probe.hit"); found = True
    print("SOURCE_PLANES_ATTACHED", found)

def write_report(debugger, path):
    st = dict(_state())
    with open(path, "w") as f: json.dump(st, f, indent=2, sort_keys=True); f.write("\n")
    print("SOURCE_PLANES_REPORT", path, len(st["planes"]), st["errors"][:3])
