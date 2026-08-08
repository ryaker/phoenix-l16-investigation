import builtins
import json


WORKERS = {
    0x9E360: {"filter_enum": 2, "phase_bits": [0, 0]},
    0x9F360: {"filter_enum": 2, "phase_bits": [1, 0]},
    0xA0380: {"filter_enum": 2, "phase_bits": [0, 1]},
    0xA13C0: {"filter_enum": 2, "phase_bits": [1, 1]},
    0xA23C0: {"filter_enum": 0, "phase_bits": [0, 0]},
    0xA2D90: {"filter_enum": 0, "phase_bits": [1, 0]},
    0xA3740: {"filter_enum": 0, "phase_bits": [0, 1]},
    0xA4100: {"filter_enum": 0, "phase_bits": [1, 1]},
    0xA4AC0: {"filter_enum": 3, "phase_bits": [0, 0]},
    0xA50D0: {"filter_enum": 3, "phase_bits": [1, 0]},
    0xA56E0: {"filter_enum": 3, "phase_bits": [0, 1]},
    0xA5CF0: {"filter_enum": 3, "phase_bits": [1, 1]},
}
CREATE_STEREO_ENTRY = 0x27B7A0
HOT_PIXEL_STAGE_ENTRY = 0x341770
HOT_PIXEL_STAGE_AFTER_PATCH = 0x341885
HOT_PIXEL_PATCH_WORKER = 0x2E8CC0


def reset(label=""):
    builtins.l16_guidance_collapse2_worker = {
        "label": label,
        "hits": [],
        "create_entries": [],
        "hot_pixel_stage_entries": [],
        "hot_pixel_patch_returns": [],
        "hot_pixel_worker_hits": [],
        "capture_complete": False,
        "terminated_after_capture": False,
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_guidance_collapse2_worker"):
        reset()
    return builtins.l16_guidance_collapse2_worker


def _libcp_base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                return base
    return None


def hit(frame, bp_loc, internal_dict):
    state = _state()
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    base = _libcp_base(target)
    site = frame.GetPC() - base if base is not None else None
    if site == CREATE_STEREO_ENTRY:
        state["create_entries"].append(
            {"thread_id": frame.GetThread().GetThreadID()}
        )
        return False
    if not state["create_entries"]:
        return False
    if site == HOT_PIXEL_STAGE_ENTRY:
        state["hot_pixel_stage_entries"].append(
            {
                "thread_id": frame.GetThread().GetThreadID(),
                "closure_rdi": frame.FindRegister("rdi").GetValueAsUnsigned(),
                "payload_rsi": frame.FindRegister("rsi").GetValueAsUnsigned(),
            }
        )
        return False
    if site == HOT_PIXEL_STAGE_AFTER_PATCH:
        state["hot_pixel_patch_returns"].append(
            {
                "thread_id": frame.GetThread().GetThreadID(),
                "patched_count_eax": frame.FindRegister("rax").GetValueAsUnsigned()
                & 0xFFFFFFFF,
            }
        )
        return False
    if site == HOT_PIXEL_PATCH_WORKER:
        state["hot_pixel_worker_hits"].append(
            {"thread_id": frame.GetThread().GetThreadID()}
        )
        return False
    item = dict(WORKERS.get(site, {}))
    item.update(
        {
            "site": site,
            "thread_id": frame.GetThread().GetThreadID(),
            "closure_rdi": frame.FindRegister("rdi").GetValueAsUnsigned(),
            "rectangle_rsi": frame.FindRegister("rsi").GetValueAsUnsigned(),
        }
    )
    state["hits"].append(item)
    state["capture_complete"] = True
    error = process.Kill()
    state["terminated_after_capture"] = error.Success()
    if not error.Success():
        state["errors"].append(f"kill failed: {error.GetCString()}")
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    found = set()
    for index in range(target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(index)
        if not bp or not bp.IsValid() or bp.GetNumLocations() < 1:
            continue
        site = bp.GetLocationAtIndex(0).GetAddress().GetFileAddress()
        if site in WORKERS or site in {
            CREATE_STEREO_ENTRY,
            HOT_PIXEL_STAGE_ENTRY,
            HOT_PIXEL_STAGE_AFTER_PATCH,
            HOT_PIXEL_PATCH_WORKER,
        }:
            bp.SetScriptCallbackFunction("collapse2_worker_probe.hit")
            found.add(site)
    expected = set(WORKERS) | {
        CREATE_STEREO_ENTRY,
        HOT_PIXEL_STAGE_ENTRY,
        HOT_PIXEL_STAGE_AFTER_PATCH,
        HOT_PIXEL_PATCH_WORKER,
    }
    if found != expected:
        _state()["errors"].append("missing sites: " + repr(sorted(expected - found)))
    print("L16_GUIDANCE_COLLAPSE2_WORKERS_ATTACHED", len(found))


def write_report(debugger, path):
    process = debugger.GetSelectedTarget().GetProcess()
    state = dict(_state())
    state["process"] = {
        "state": process.GetState(),
        "exit_status": process.GetExitStatus(),
    }
    with open(path, "w", encoding="ascii") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_GUIDANCE_COLLAPSE2_WORKER_REPORT", path)
