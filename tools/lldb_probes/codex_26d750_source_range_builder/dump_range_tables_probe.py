"""Dump Lumen's full per-level range_low/range_high tables (the pooled coarse
index bounds that become each pixel's band). Break at builder_after_output_store
(0x26d9bc); on the FIRST hit per unique target-dims (= per level), read the
range_low/range_high table bases+strides and source dims from the builder frame
and write the full u16 arrays to disk, plus target dims and pad offset."""
import builtins
import json
import struct

OUTDIR = "/Volumes/Dev/L16_Lumen_ReverseEngineering/runs/codex_26d750_source_range_builder/tele_tables"
# 0x26d9bc = builder output store (per-pixel). Fires many times per level but the
# rbp-locals (range_low/high base+stride, source dims) are valid here; we dump on
# the FIRST hit per source-dims key and then skip. Slow but correct.
STORE_SITE = 0x26D9BC


ENTRY_SITE = 0x26D750  # builder entry: fires once per level -> re-enable the store bp


def reset(label=""):
    builtins.l16_rt = {"label": label, "levels": {}, "errors": [], "done": False,
                       "store_bp_id": None}


def on_entry(frame, bp_loc, _dict):
    # builder entered for a new level -> re-enable the (self-disabling) store bp
    st = _s()
    try:
        target = frame.GetThread().GetProcess().GetTarget()
        bid = st.get("store_bp_id")
        if bid is not None:
            bp = target.FindBreakpointByID(bid)
            if bp:
                bp.SetEnabled(True)
    except Exception as e:
        st["errors"].append("entry:" + repr(e))
    return False


def _s():
    if not hasattr(builtins, "l16_rt"):
        reset()
    return builtins.l16_rt


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    import lldb
    if not addr or size <= 0:
        return None
    err = lldb.SBError()
    d = process.ReadMemory(addr, size, err)
    return d if err.Success() and len(d) == size else None


def _u32at(process, addr):
    d = _read(process, addr, 4)
    return struct.unpack("<I", d)[0] if d else None


def _u64at(process, addr):
    d = _read(process, addr, 8)
    return struct.unpack("<Q", d)[0] if d else None


def _libcp_base(target):
    for m in target.module_iter():
        if str(m.GetFileSpec().GetFilename()) == "libcp.dylib":
            b = m.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if b != 0xFFFFFFFFFFFFFFFF:
                return b
    return None


def on_store(frame, bp_loc, _dict):
    import os
    st = _s()
    try:
        process = frame.GetThread().GetProcess()
        rbp = _u(frame, "rbp")
        low_base = _u64at(process, rbp - 0xC0) or 0
        low_stride = _u32at(process, rbp - 0xC8) or 0
        high_base = _u64at(process, rbp - 0xF0) or 0
        high_stride = _u32at(process, rbp - 0xF8) or 0
        ssize = _u64at(process, rbp - 0xA0) or 0
        sw = ssize & 0xFFFFFFFF
        sh = (ssize >> 32) & 0xFFFFFFFF
        # key by SOURCE dims (unique per level; avoids depending on which reg holds target here)
        key = "%dx%d" % (sw, sh)
        pad = 1
        if key in st["levels"] or not (low_base and high_base and sw and sh) or sw > 4096 or sh > 4096:
            return False
        os.makedirs(OUTDIR, exist_ok=True)
        # Fast path: when stride == width the table is contiguous -> one ReadMemory.
        if low_stride == sw and high_stride == sw:
            low_rows = _read(process, low_base, sw * sh * 2)
            high_rows = _read(process, high_base, sw * sh * 2)
            if low_rows is None or high_rows is None:
                st["errors"].append("contig read fail %s" % key)
                return False
        else:
            low_rows = bytearray()
            high_rows = bytearray()
            for r in range(sh):
                lr = _read(process, low_base + 2 * r * low_stride, sw * 2)
                hr = _read(process, high_base + 2 * r * high_stride, sw * 2)
                if lr is None or hr is None:
                    st["errors"].append("row read fail %s r%d" % (key, r))
                    return False
                low_rows += lr
                high_rows += hr
        open("%s/range_low_%s.u16" % (OUTDIR, key), "wb").write(low_rows)
        open("%s/range_high_%s.u16" % (OUTDIR, key), "wb").write(high_rows)
        # Also dump the RAW coarse INDEX the pool read: descriptor at [rbp-0xb0]
        # (built by 0x267120, consumed by 0x298ff0). descriptor.data=+0x20, stride=+0x18.
        try:
            idx_data = _u64at(process, rbp - 0xB0 + 0x20)
            idx_stride = _u32at(process, rbp - 0xB0 + 0x18) or sw
            for esz, tag in ((2, "u16"), (4, "u32")):
                buf = bytearray()
                ok = True
                for r in range(sh):
                    row = _read(process, idx_data + esz * r * idx_stride, sw * esz)
                    if row is None:
                        ok = False; break
                    buf += row
                if ok:
                    open("%s/index_%s.%s" % (OUTDIR, key, tag), "wb").write(buf)
            print("RT_INDEX %s data=0x%x stride=%d" % (key, idx_data or 0, idx_stride), flush=True)
        except Exception as e3:
            st["errors"].append("idx:" + repr(e3))
        st["levels"][key] = {"src_w": sw, "src_h": sh,
                             "pad_0x10": pad, "low_stride": low_stride, "high_stride": high_stride}
        print("RT_LEVEL %s src=%dx%d pad=%d" % (key, sw, sh, pad), flush=True)
    except Exception as e:
        st["errors"].append(repr(e))
    return False


def attach(debugger):
    # Breakpoints set via `breakpoint set --shlib libcp.dylib --address` in the
    # driver (resolve at load). Assign callbacks by matching the file address
    # low-12-bits (offset within libcp) to STORE/ENTRY.
    st = _s()
    target = debugger.GetSelectedTarget()
    n = 0
    for i in range(target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(i)
        loc0 = bp.GetLocationAtIndex(0)
        off = None
        if loc0:
            fa = loc0.GetAddress().GetFileAddress()
            off = fa & 0xFFFFF  # offsets 0x26d750/0x26d9bc fit in 20 bits
        if off == (STORE_SITE & 0xFFFFF):
            bp.SetScriptCallbackFunction("dump_range_tables_probe.on_store")
            st["store_bp_id"] = bp.GetID(); n += 1
        elif off == (ENTRY_SITE & 0xFFFFF):
            bp.SetScriptCallbackFunction("dump_range_tables_probe.on_entry"); n += 1
    print("RT_ATTACHED callbacks_set=%d store_id=%s" % (n, st.get("store_bp_id")), flush=True)


def write_report(debugger, path):
    st = _s()
    json.dump(st, open(path, "w"), indent=1, default=str)
    print("RT_REPORT", path, len(st["levels"]), st["errors"][:3], flush=True)
