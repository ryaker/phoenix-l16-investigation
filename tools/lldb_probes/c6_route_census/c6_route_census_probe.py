import builtins
import json
import os
import struct


CALLSITES = [
    0xDF8F3,
    0xE3273,
    0xE327E,
    0xE32F3,
    0xE4063,
    0xE5FD9,
    0xE6020,
    0xE609A,
    0xE680F,
    0xE688F,
    0xE69DF,
    0xE6BE0,
    0xE745F,
    0xE75F3,
    0xE7763,
    0xFB329,
    0xFB95F,
    0xFE5FC,
    0x144C80,
    0x145703,
    0x1459D9,
    0x1A8E00,
    0x1A8E21,
    0x1A8E5F,
    0x1A8EFF,
    0x1A8F1C,
    0x1A8F5A,
    0x1B7E82,
    0x1B7E8D,
    0x1BDBAB,
    0x1BDBDD,
    0x20B044,
    0x20B17D,
    0x227D5E,
    0x227D77,
    0x227E30,
    0x2280DE,
    0x22819C,
    0x22EEB7,
    0x22EECF,
    0x22EEEB,
    0x22F717,
    0x22F72F,
    0x22F74B,
    0x27D7CE,
    0x27DB11,
    0x31BCE0,
    0x31BD00,
    0x3B2143,
    0x3C9043,
    0x3C9098,
    0x3F30CA,
    0x3F3104,
    0x402DF7,
    0x402E30,
    0x402E3D,
    0x40D18D,
    0x40D219,
]

KEY15 = 15


def reset(label="", site_hit_cap=4096, sample_limit=24, key15_limit=256, selected_sites=None):
    sites = selected_sites if selected_sites is not None else CALLSITES
    builtins.l16_c6_route_census = {
        "label": label,
        "site_hit_cap": site_hit_cap,
        "sample_limit": sample_limit,
        "key15_limit": key15_limit,
        "selected_sites": [f"0x{va:x}" for va in sites],
        "breakpoint_ids": {},
        "counts": {
            f"0x{va:x}": {
                "hits": 0,
                "key15_hits": 0,
                "active0_hits": 0,
                "active1_hits": 0,
                "read_errors": 0,
                "disabled_at_cap": False,
            }
            for va in sites
        },
        "unique_keys_by_site": {f"0x{va:x}": [] for va in sites},
        "samples": [],
        "key15_hits": [],
        "errors": [],
        "install": {"requested": len(sites), "installed": 0},
    }


def _state():
    if not hasattr(builtins, "l16_c6_route_census"):
        reset()
    return builtins.l16_c6_route_census


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    if not addr:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u8(process, addr):
    data = _read(process, addr, 1)
    return data[0] if data is not None else None


def _u32(process, addr):
    data = _read(process, addr, 4)
    return struct.unpack_from("<I", data, 0)[0] if data is not None else None


def _i32(process, addr):
    data = _read(process, addr, 4)
    return struct.unpack_from("<i", data, 0)[0] if data is not None else None


def _libcp_base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                return base
    return None


def _module_va(target, pc):
    addr = target.ResolveLoadAddress(pc)
    if addr and addr.IsValid():
        module = addr.GetModule()
        if module and str(module.GetFileSpec().GetFilename()) != "libcp.dylib":
            return None
    base = _libcp_base(target)
    if base is not None and pc >= base:
        return pc - base
    return None


def _stack(thread, max_frames=10):
    target = thread.GetProcess().GetTarget()
    frames = []
    for index in range(min(thread.GetNumFrames(), max_frames)):
        frame = thread.GetFrameAtIndex(index)
        frames.append(
            {
                "index": index,
                "pc": frame.GetPC(),
                "libcp_va": _module_va(target, frame.GetPC()),
                "function": frame.GetFunctionName(),
            }
        )
    return frames


def _packet(frame, site_va, item):
    process = frame.GetThread().GetProcess()
    key = _u32(process, item + 0x60)
    active = _u8(process, item + 0x30)
    return {
        "site_va": site_va,
        "site": f"0x{site_va:x}",
        "item_ptr": item,
        "key_item_0x60": key,
        "active_item_0x30": active,
        "pair_item_0x58_0x5c": [_i32(process, item + 0x58), _i32(process, item + 0x5C)],
        "type_item_0x100": _u32(process, item + 0x100),
        "thread_id": frame.GetThread().GetThreadID(),
    }


def install_breakpoints(debugger):
    state = _state()
    target = debugger.GetSelectedTarget()
    sites = [int(site, 16) for site in state.get("selected_sites", [])]
    for va in sites:
        before = target.GetNumBreakpoints()
        debugger.HandleCommand(f"breakpoint set --shlib libcp.dylib --address 0x{va:x}")
        after = target.GetNumBreakpoints()
        if after <= before:
            state["errors"].append({"site": f"0x{va:x}", "error": "breakpoint not created"})
            continue
        bp = target.GetBreakpointAtIndex(after - 1)
        if not bp or not bp.IsValid():
            state["errors"].append({"site": f"0x{va:x}", "error": "invalid breakpoint"})
            continue
        bp.SetScriptCallbackFunction("c6_route_census_probe.callsite")
        state["breakpoint_ids"][str(bp.GetID())] = f"0x{va:x}"
        state["install"]["installed"] += 1
    print("INSTALLED", state["install"]["installed"], "of", state["install"]["requested"])


def callsite(frame, bp_loc, _dict):
    state = _state()
    target = frame.GetThread().GetProcess().GetTarget()
    site_va = _module_va(target, frame.GetPC())
    site_key = f"0x{site_va:x}" if site_va is not None else "unknown"
    site_counts = state["counts"].setdefault(
        site_key,
        {
            "hits": 0,
            "key15_hits": 0,
            "active0_hits": 0,
            "active1_hits": 0,
            "read_errors": 0,
            "disabled_at_cap": False,
        },
    )
    site_counts["hits"] += 1

    item = _u(frame, "rdi")
    packet = _packet(frame, site_va, item) if item else None
    if packet is None or packet["key_item_0x60"] is None:
        site_counts["read_errors"] += 1
    else:
        key = packet["key_item_0x60"]
        active = packet["active_item_0x30"]
        keys = state["unique_keys_by_site"].setdefault(site_key, [])
        if key not in keys:
            keys.append(key)
            keys.sort()
        if active == 0:
            site_counts["active0_hits"] += 1
        elif active == 1:
            site_counts["active1_hits"] += 1
        if len(state["samples"]) < state["sample_limit"]:
            state["samples"].append(packet)
        if key == KEY15:
            site_counts["key15_hits"] += 1
            if len(state["key15_hits"]) < state["key15_limit"]:
                packet["stack"] = _stack(frame.GetThread(), 12)
                state["key15_hits"].append(packet)

    if site_counts["hits"] >= state["site_hit_cap"] and site_counts["key15_hits"] == 0:
        site_counts["disabled_at_cap"] = True
        bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def report_to_file(path):
    state = _state()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)
    print(
        "WROTE",
        path,
        "installed",
        state["install"]["installed"],
        "key15_records",
        len(state["key15_hits"]),
    )
