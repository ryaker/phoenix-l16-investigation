"""Dense guidance-buffer dump: at DIRECT_PACK_SOURCE (float vec4f guidance) dump
the FULL Image<vec4x32f> plane to a raw file, so the CreateStereoImage guidance
can be validated per-pixel (not 5 samples) across all four focal tiers / both
bodies. Reuses the proven site VAs from guidance_component_branch_probe."""
import builtins
import json
import struct

DIRECT_PACK_SOURCE_VA = 0x27C062  # source_vec4f_rbx = guidance Image<vec4x32f>
CAMERA_KEY_COMPARE_VA = 0x3F5035  # source_camera_key in esi
POST_GUIDANCE_TRANSFORM_VA = 0x27C6D2

# Dump EVERY guidance plane produced during the render (one per camera in the
# tier set), each tagged by index, instead of only the first + kill. Caller
# passes an output prefix; files are <prefix>_k<N>.rgbaf + a manifest json.
_OUT = {"prefix": None, "max": 16}


def reset(prefix, max_planes=16):
    _OUT["prefix"] = prefix
    _OUT["max"] = int(max_planes)
    builtins.l16_guid_dense = {"planes": [], "errors": [], "last_key": None}


def _state():
    if not hasattr(builtins, "l16_guid_dense"):
        builtins.l16_guid_dense = {"planes": [], "errors": [], "last_key": None}
    return builtins.l16_guid_dense


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    if not addr or size <= 0:
        return None
    import lldb
    err = lldb.SBError()
    data = process.ReadMemory(addr, size, err)
    return data if err.Success() and len(data) == size else None


def hit(frame, bp_loc, internal_dict):
    st = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    pc = frame.GetPC()
    base = None
    for m in target.module_iter():
        if str(m.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = m.GetObjectFileHeaderAddress().GetLoadAddress(target)
            break
    site = pc - base if base else None
    if site == CAMERA_KEY_COMPARE_VA:
        # source_camera_key = esi; identifies which camera's guidance is next.
        st["last_key"] = _u(frame, "rsi") & 0xFFFFFFFF
        return False
    if site == DIRECT_PACK_SOURCE_VA:
        idx = len(st["planes"])
        if idx >= _OUT["max"]:
            return False
        desc = _u(frame, "rbx")
        hdr = _read(process, desc, 0x30)
        if hdr is None:
            st["errors"].append("no header")
            return False
        w = struct.unpack("<8iQQ", hdr)  # origin(2) bounds(2) size(2) stride res data alloc
        width, height, stride, data = w[4], w[5], w[6], w[8]
        total = height * stride * 16
        blob = _read(process, data, total)
        if blob is None:
            st["errors"].append(f"buffer read failed k{idx} total={total}")
            return False
        fn = f"{_OUT['prefix']}_p{idx}.rgbaf"
        with open(fn, "wb") as fh:
            fh.write(blob)
        st["planes"].append({"index": idx, "camera_key": st.get("last_key"),
                             "width": width, "height": height, "stride": stride,
                             "file": fn})
        if len(st["planes"]) >= _OUT["max"]:
            process.Kill()  # captured the tier set; stop before the long render
        return False
    # do NOT kill at POST_GUIDANCE_TRANSFORM -- let the whole render run so we
    # capture EVERY camera's guidance plane, not just the first.
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    found = []
    for i in range(target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(i)
        if not bp or not bp.IsValid() or bp.GetNumLocations() < 1:
            continue
        site = bp.GetLocationAtIndex(0).GetAddress().GetFileAddress()
        if site in (CAMERA_KEY_COMPARE_VA, DIRECT_PACK_SOURCE_VA):
            bp.SetScriptCallbackFunction("guidance_dense_dump_probe.hit")
            found.append(hex(site))
    print("L16_GUID_DENSE_ATTACHED", found)


def write_report(debugger, path):
    st = dict(_state())
    with open(path, "w") as fh:
        json.dump(st, fh, indent=1)
    print("L16_GUID_DENSE_REPORT", path, "n_planes=", len(st.get("planes", [])))
