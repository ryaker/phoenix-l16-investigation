"""Census of every MonoFusion mode-0 reducer entry (0x1a3c00).

Answers one question with a receipt instead of inference: for a given capture,
how many times is the mode-0 reducer entered, with what ROI, and with how many
source/flow operands? The mode0_tile_probe capture aborts silently when the
top-left tile never arrives with exactly one source and one flow; this probe
records what actually arrives.
"""

import builtins
import json
import struct


def reset(label, out_path, limit=400):
    builtins.l16_mode0_census = {
        "label": label,
        "out_path": str(out_path),
        "limit": int(limit),
        "hits": [],
        "errors": [],
    }


def _state():
    return builtins.l16_mode0_census


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    if not address:
        return None
    raw = process.ReadMemory(address, size, error)
    if not error.Success() or len(raw) != size:
        return None
    return raw


def _u64(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<Q", raw)[0] if raw else 0


def _desc(process, address):
    raw = _read(process, address, 0x30)
    if raw is None:
        return None
    w = struct.unpack_from("<8i", raw)
    return {
        "domain": list(w[:4]),
        "size": list(w[4:6]),
        "stride": w[6],
        "channel_stride": w[7],
        "data": struct.unpack_from("<Q", raw, 0x20)[0],
    }


def _vec(process, address):
    raw = _read(process, address, 24)
    if raw is None:
        return {"count": None}
    begin, end, cap = struct.unpack("<QQQ", raw)
    ok = begin <= end <= cap and (end - begin) % 0x30 == 0
    count = (end - begin) // 0x30 if ok else None
    recs = []
    if count is not None and count <= 8:
        recs = [_desc(process, begin + i * 0x30) for i in range(count)]
    return {"count": count, "records": recs}


def install(debugger, bp_id):
    target = debugger.GetSelectedTarget()
    bp = target.FindBreakpointByID(bp_id)
    if bp and bp.IsValid():
        bp.SetScriptCallbackFunction("mode0_entry_census.on_entry")


def on_entry(frame, bp_loc, internal_dict):
    state = _state()
    if len(state["hits"]) >= state["limit"]:
        frame.GetThread().GetProcess().Kill()
        return False
    process = frame.GetThread().GetProcess()
    rsp = frame.FindRegister("rsp").GetValueAsUnsigned()
    roi_ptr = _u64(process, rsp + 8)
    roi_raw = _read(process, roi_ptr, 16)
    roi = list(struct.unpack("<4i", roi_raw)) if roi_raw else None
    sources = _vec(process, frame.FindRegister("r8").GetValueAsUnsigned())
    flows = _vec(process, frame.FindRegister("r9").GetValueAsUnsigned())
    target = _desc(process, frame.FindRegister("rdx").GetValueAsUnsigned())
    aux = _desc(process, frame.FindRegister("rcx").GetValueAsUnsigned())
    state["hits"].append({
        "n": len(state["hits"]),
        "thread": frame.GetThread().GetThreadID(),
        "roi": roi,
        "n_sources": sources["count"],
        "n_flows": flows["count"],
        "target_size": target["size"] if target else None,
        "target_domain": target["domain"] if target else None,
        "target_data": target["data"] if target else None,
        "aux_domain": aux["domain"] if aux else None,
        "aux_data": aux["data"] if aux else None,
        "source_sizes": [r["size"] for r in sources.get("records", []) if r],
        "source_data": [r["data"] for r in sources.get("records", []) if r],
    })
    return False


def flush():
    state = _state()
    with open(state["out_path"], "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("MODE0_ENTRY_CENSUS %s hits=%d" % (state["out_path"], len(state["hits"])))
