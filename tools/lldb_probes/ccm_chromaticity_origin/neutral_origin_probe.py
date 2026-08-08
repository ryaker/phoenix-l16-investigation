import builtins, json, struct
import lldb

def reset(out_path):
    builtins.l16_neutral = {"out": out_path, "events": [], "errors": []}

def _st():
    return builtins.l16_neutral

def _read_floats(process, addr, n):
    err = lldb.SBError()
    data = process.ReadMemory(addr, n * 4, err)
    if not err.Success():
        return None, str(err)
    return list(struct.unpack("<%df" % n, data)), None

def on_entry(frame, bp_loc, internal_dict):
    st = _st()
    try:
        process = frame.GetThread().GetProcess()
        rdi = frame.FindRegister("rdi").GetValueAsUnsigned()
        rsi = frame.FindRegister("rsi").GetValueAsUnsigned()
        st["events"].append({"phase": "entry", "this": rdi, "rsi": rsi})
        rsp = frame.FindRegister("rsp").GetValueAsUnsigned()
        err = lldb.SBError()
        rd = process.ReadMemory(rsp, 8, err)
        if err.Success():
            retaddr = struct.unpack("<Q", rd)[0]
            rb = process.GetTarget().BreakpointCreateByAddress(retaddr)
            rb.SetOneShot(True)
            rb.SetScriptCallbackFunction("neutral_origin_probe.on_return")
            builtins._l16_pending_this = rdi
    except Exception as e:
        st["errors"].append("entry:" + str(e))
    return False

def on_return(frame, bp_loc, internal_dict):
    st = _st()
    try:
        process = frame.GetThread().GetProcess()
        rdi = getattr(builtins, "_l16_pending_this", 0)
        floats, e1 = _read_floats(process, rdi + 0x60, 16)
        ev = {"phase": "return", "this": rdi}
        if floats is not None:
            ev["fields_0x60"] = [round(v, 8) for v in floats]
            ev["neutral_0x74"] = [round(v, 8) for v in floats[5:8]]
            ev["temp_tint_0x88"] = [round(v, 6) for v in floats[10:12]]
        else:
            ev["read_err"] = e1
        st["events"].append(ev)
    except Exception as e:
        st["errors"].append("return:" + str(e))
    return False

def write_report(debugger):
    st = _st()
    with open(st["out"], "w") as f:
        json.dump(st, f, indent=1)
    print("L16_NEUTRAL_REPORT", st["out"], "events:", len(st["events"]), "errors:", st["errors"][:2])
