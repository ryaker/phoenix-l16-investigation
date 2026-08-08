import builtins, hashlib, json, struct, os

PROJECTION_VECTOR_AFTER = 0x276A01
EXPECTED_DIMS = {(65,49),(130,98),(260,195),(520,390),(1040,780),(2080,1560)}

def reset(label="", outdir="/tmp/guid"):
    builtins.l16_guid = {"label": label, "outdir": outdir, "hits": 0,
                          "levels": [], "errors": [], "done": False}
    os.makedirs(outdir, exist_ok=True)

def _state():
    if not hasattr(builtins, "l16_guid"): reset()
    return builtins.l16_guid

def _read(process, address, size):
    if not address or size <= 0: return None
    lldb = builtins.__import__("lldb")
    err = lldb.SBError()
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
    return {"origin": list(w[0:2]), "bounds": list(w[2:4]), "size": list(w[4:6]),
            "stride": w[6], "data": w[8], "allocation": w[9]}

def hit(frame, bp_loc, internal_dict):
    st = _state(); process = frame.GetThread().GetProcess(); st["hits"] += 1
    layer = _u(frame, "r12")
    im = _read(process, layer + 0x08, 8)
    if im is None: return False
    index, mode = struct.unpack("<2I", im)
    if index > 5 or mode != 8: return False
    if any(l["index"] == index for l in st["levels"]): return False
    g = _descriptor(process, _u64(process, layer + 0x288))
    if g is None: st["errors"].append("guidance desc read failed idx=%d" % index); return False
    w, h = g["size"]; stride = g["stride"]; data = g["data"]
    # Image<vec4x8ui> = 4 bytes/pixel; dump width*4 per row at stride*4 row pitch
    rows = bytearray()
    ok = True
    for y in range(h):
        r = _read(process, data + y * stride * 4, w * 4)
        if r is None: ok = False; break
        rows += r
    if not ok:
        st["errors"].append("guidance plane read failed idx=%d" % index); return False
    path = os.path.join(st["outdir"], "guidance_level%d_%dx%d.rgba8" % (index, w, h))
    with open(path, "wb") as f: f.write(bytes(rows))
    st["levels"].append({"index": index, "w": w, "h": h, "stride": stride,
                          "sha256": hashlib.sha256(bytes(rows)).hexdigest(),
                          "bytes": len(rows), "path": path})
    observed = {(l["w"], l["h"]) for l in st["levels"]}
    if observed == EXPECTED_DIMS:
        st["done"] = process.Kill().Success()
    return False

def attach(debugger):
    target = debugger.GetSelectedTarget(); found = False
    for i in range(target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(i)
        if not bp or not bp.IsValid() or bp.GetNumLocations() < 1: continue
        if bp.GetLocationAtIndex(0).GetAddress().GetFileAddress() == PROJECTION_VECTOR_AFTER:
            bp.SetScriptCallbackFunction("guidance_pyramid_probe.hit"); found = True
    print("GUIDANCE_PYRAMID_ATTACHED", found)

def write_report(debugger, path):
    st = dict(_state())
    with open(path, "w") as f: json.dump(st, f, indent=2, sort_keys=True); f.write("\n")
    print("GUIDANCE_PYRAMID_REPORT", path, len(st["levels"]), st["errors"])
