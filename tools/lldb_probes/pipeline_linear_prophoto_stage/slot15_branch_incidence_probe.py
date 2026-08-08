import builtins
import hashlib
import json
import os
import struct


EXPECTED_CONFIG = bytes.fromhex(
    "6c344c3fb16f0a3e6c6c003d017a933e623d363fd6b9b338"
    "0000000000000000f640533f8dfbb03ed08cb73e0500000005000000"
)

SITES = {
    0x34A6AD: ("Bayer", "equal_copy"),
    0x34A6B4: ("Bayer", "unequal_convert"),
    0x34A81D: ("BayerFloat", "equal_copy"),
    0x34A824: ("BayerFloat", "unequal_convert"),
    0x34A98D: ("Color", "equal_copy"),
    0x34A994: ("Color", "unequal_convert"),
}


def reset(label="", sample_cap=48, hit_cap=20000, one_shot_equal=False):
    builtins.l16_slot15_branch_incidence = {
        "label": label,
        "sample_cap": int(sample_cap),
        "hit_cap": int(hit_cap),
        "one_shot_equal": bool(one_shot_equal),
        "breakpoints": {},
        "counts": {
            wrapper: {"equal_copy": 0, "unequal_convert": 0}
            for wrapper in ("Bayer", "BayerFloat", "Color")
        },
        "config_counts": {},
        "samples": [],
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_slot15_branch_incidence"):
        reset()
    return builtins.l16_slot15_branch_incidence


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    if not address:
        return None
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u64(data):
    return struct.unpack("<Q", data)[0]


def _libcp_base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) != "libcp.dylib":
            continue
        base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
        if base != 0xFFFFFFFFFFFFFFFF:
            return base
    return None


def _module_va(target, address):
    base = _libcp_base(target)
    if base is None or address < base:
        return None
    return address - base


def _stack(thread, limit=10):
    target = thread.GetProcess().GetTarget()
    result = []
    for index in range(min(thread.GetNumFrames(), limit)):
        frame = thread.GetFrameAtIndex(index)
        result.append(
            {
                "index": index,
                "pc": frame.GetPC(),
                "libcp_va": _module_va(target, frame.GetPC()),
                "function": frame.GetFunctionName(),
            }
        )
    return result


def _decode_config(data):
    values = struct.unpack("<9f2f2I", data)
    return {
        "matrix": list(values[:9]),
        "white_xy": list(values[9:11]),
        "source_selector": values[11],
        "target_selector": values[12],
    }


def branch_hit(frame, bp_loc, _dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    site_va = _module_va(target, frame.GetPC())
    site = SITES.get(site_va)
    if site is None:
        state["errors"].append({"error": "unknown site", "site_va": site_va})
        return False

    wrapper, outcome = site
    state["counts"][wrapper][outcome] += 1

    holder = _u(frame, "rbx")
    holder_data = _read(process, holder, 8)
    image = _u64(holder_data) if holder_data is not None else 0
    config = _read(process, image + 0x48, 0x34) if image else None
    if config is None:
        state["errors"].append(
            {
                "error": "config read failed",
                "wrapper": wrapper,
                "outcome": outcome,
                "holder": holder,
                "image": image,
            }
        )
        digest = "unreadable"
    else:
        digest = hashlib.sha256(config).hexdigest()
        key = f"{wrapper}|{outcome}|{digest}"
        state["config_counts"][key] = state["config_counts"].get(key, 0) + 1

    sample_key = (wrapper, outcome, digest)
    sampled_keys = {
        (item["wrapper"], item["outcome"], item["config_sha256"])
        for item in state["samples"]
    }
    if len(state["samples"]) < state["sample_cap"] and sample_key not in sampled_keys:
        state["samples"].append(
            {
                "site_va": site_va,
                "wrapper": wrapper,
                "outcome": outcome,
                "thread_id": thread.GetThreadID(),
                "holder": holder,
                "image": image,
                "config_hex": config.hex() if config is not None else None,
                "config_sha256": digest,
                "bit_exact_linear_prophoto_target": config == EXPECTED_CONFIG,
                "decoded_config": _decode_config(config) if config is not None else None,
                "stack": _stack(thread),
            }
        )

    if state["one_shot_equal"] and outcome == "equal_copy":
        bp_loc.GetBreakpoint().SetEnabled(False)

    total = sum(sum(outcomes.values()) for outcomes in state["counts"].values())
    if total >= state["hit_cap"]:
        for breakpoint_id in state["breakpoints"].values():
            breakpoint = target.FindBreakpointByID(breakpoint_id)
            if breakpoint and breakpoint.IsValid():
                breakpoint.SetEnabled(False)
    return False


def _add(debugger, name, address):
    state = _state()
    target = debugger.GetSelectedTarget()
    before = target.GetNumBreakpoints()
    debugger.HandleCommand(
        f"breakpoint set --shlib libcp.dylib --address 0x{address:x}"
    )
    if target.GetNumBreakpoints() <= before:
        state["errors"].append({"error": "breakpoint creation", "site": name})
        return
    breakpoint = target.GetBreakpointAtIndex(target.GetNumBreakpoints() - 1)
    breakpoint.SetScriptCallbackFunction(
        "slot15_branch_incidence_probe.branch_hit"
    )
    state["breakpoints"][name] = breakpoint.GetID()


def install(debugger):
    for address, (wrapper, outcome) in SITES.items():
        _add(debugger, f"{wrapper}_{outcome}", address)
    print("SLOT15_BRANCH_INCIDENCE_INSTALLED", _state()["breakpoints"])


def install_tele(debugger):
    for address, (wrapper, outcome) in SITES.items():
        if wrapper in ("Bayer", "BayerFloat"):
            _add(debugger, f"{wrapper}_{outcome}", address)
    print("SLOT15_BRANCH_INCIDENCE_INSTALLED_TELE", _state()["breakpoints"])


def install_tele_mismatch(debugger):
    for address, (wrapper, outcome) in SITES.items():
        if wrapper in ("Bayer", "BayerFloat") and outcome == "unequal_convert":
            _add(debugger, f"{wrapper}_{outcome}", address)
    print("SLOT15_BRANCH_INCIDENCE_INSTALLED_TELE_MISMATCH", _state()["breakpoints"])


def report_to_file(debugger, path):
    state = dict(_state())
    process = debugger.GetSelectedTarget().GetProcess()
    if process and process.IsValid():
        state["process_exit_status"] = process.GetExitStatus()
        state["process_state"] = int(process.GetState())
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("SLOT15_BRANCH_INCIDENCE_WROTE", path)
