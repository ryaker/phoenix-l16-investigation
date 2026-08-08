import lldb, struct

_seen = []

def _read(process, addr, n):
    err = lldb.SBError()
    b = process.ReadMemory(addr, n, err)
    if not err.Success() or b is None or len(b) != n:
        return None
    return b

def _u64(process, addr):
    b = _read(process, addr, 8)
    return struct.unpack("<Q", b)[0] if b else None

def on_cost_worker(frame, bp_loc, extra, internal_dict):
    process = frame.GetThread().GetProcess()
    rbp = frame.FindRegister("rbp").GetValueAsUnsigned()
    obj = _u64(process, rbp - 0x1c8)
    if not obj:
        return False
    rec_base = _u64(process, obj + 0x108)
    scale = None
    if rec_base:
        b = _read(process, rec_base + 0x48, 8)
        if b:
            scale = struct.unpack("<2f", b)
    imgs = _u64(process, obj + 0x240)
    dims = None
    if imgs:
        b = _read(process, imgs + 0x10, 8)
        if b:
            dims = struct.unpack("<2i", b)
    key = (scale, dims)
    if not _seen or _seen[-1] != key:
        _seen.append(key)
        print("[perlevel] scale=%s dims=%s rec_base=%s" % (scale, dims, hex(rec_base) if rec_base else None))
    return False

def summary(debugger):
    print("=== DISTINCT (scale, dims) IN ORDER ===")
    for s, d in _seen:
        print("  scale=%s dims=%s" % (s, d))
