"""Bounded pipeline-route census for supported focal/topology variants."""

import builtins
import json
import struct


SITES = {
    0x22F0F0: "calib_state_dispatcher",
    0x24C320: "prefusion_scorer_a",
    0x24D610: "prefusion_scorer_b",
    0x276790: "stereo_runpass_dispatch",
    0x276860: "stereo_runpass_primary",
    0x277E70: "stereo_runpass_sibling",
    0x275630: "stereo_tile_state_builder",
    0x2730C0: "stereo_cost_sibling",
    0x2732F0: "stereo_cost_primary",
    0x26D750: "range_map_builder",
    0x29ED90: "guided_upsample",
    0x3F7040: "warp_record_builder",
    0x3F72F0: "cross_category_warp",
    0x3C90A5: "c6_clear",
    0x3ECC10: "iramp_src1_wrapper",
    0x3ECD80: "iramp_src2_wrapper",
    0x3ECED0: "iramp_direct_wrapper",
    0x365960: "iramp_entry",
    0x3661B0: "iramp_inner",
    0x369FA1: "iramp_accumulator",
    0x19F790: "monofusion_mode1",
    0x1A3C00: "monofusion_mode0",
}

CAP = 8


def reset(label=""):
    builtins.l16_variant_pipeline = {
        "label": label,
        "cap": CAP,
        "counts": {name: 0 for name in SITES.values()},
        "iramp_entries": [],
        "errors": [],
    }


def state():
    if not hasattr(builtins, "l16_variant_pipeline"):
        reset()
    return builtins.l16_variant_pipeline


def libcp_base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            value = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if value != 0xFFFFFFFFFFFFFFFF:
                return value
    return None


def reg(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error) if address else None
    return data if error.Success() and data is not None and len(data) == size else None


def u64(process, address):
    data = read(process, address, 8)
    return struct.unpack("<Q", data)[0] if data else None


def i64(process, address):
    data = read(process, address, 8)
    return struct.unpack("<q", data)[0] if data else None


def i32x4(process, address):
    data = read(process, address, 16)
    return list(struct.unpack("<4i", data)) if data else None


def xmm_low(frame, name):
    data = frame.FindRegister(name).GetData()
    error = builtins.__import__("lldb").SBError()
    value = data.GetFloat(error, 0) if data.IsValid() else None
    return value if error.Success() else None


def iramp_entry(frame):
    process = frame.GetThread().GetProcess()
    vector = reg(frame, "rcx")
    begin = u64(process, vector)
    end = u64(process, vector + 8)
    items = []
    if begin is not None and end is not None and end >= begin:
        count = (end - begin) // 0x10
        for index in range(min(count, 16)):
            ptr0 = u64(process, begin + index * 0x10)
            ptr1 = u64(process, begin + index * 0x10 + 8)
            candidates = []
            if ptr0:
                for offset in range(0, 0x100, 8):
                    nested = u64(process, ptr0 + offset)
                    camera_id = i64(process, nested + 0x90) if nested and nested > 0x100000000 else None
                    if camera_id is not None and 0 <= camera_id <= 15:
                        candidates.append(
                            {
                                "object_offset": offset,
                                "nested_pointer": nested,
                                "camera_id": camera_id,
                            }
                        )
            items.append(
                {
                    "index": index,
                    "ptr0": ptr0,
                    "ptr1": ptr1,
                    "candidate_funcdata_fields": candidates,
                }
            )
    return {
        "source_vector_begin": begin,
        "source_vector_end": end,
        "source_count": len(items),
        "contributors": items,
        "warp_vector_begin": u64(process, reg(frame, "r8")),
        "warp_vector_end": u64(process, reg(frame, "r8") + 8),
        "roi": i32x4(process, reg(frame, "r9")),
        "scale": xmm_low(frame, "xmm0"),
    }


def hit(frame, bp_loc, _dict):
    out = state()
    target = frame.GetThread().GetProcess().GetTarget()
    base = libcp_base(target)
    va = frame.GetPC() - base if base is not None else None
    name = SITES.get(va)
    if name is None:
        out["errors"].append({"pc": frame.GetPC(), "error": "unknown site"})
        return False
    out["counts"][name] += 1
    if va == 0x365960 and not out["iramp_entries"]:
        out["iramp_entries"].append(iramp_entry(frame))
    if out["counts"][name] >= CAP:
        bp_loc.GetBreakpoint().SetEnabled(False)
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    for index in range(target.GetNumBreakpoints()):
        target.GetBreakpointAtIndex(index).SetScriptCallbackFunction(
            "variant_pipeline_probe.hit"
        )


def drive_until_exit_or_step_cap(debugger, max_steps=20000):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    steps = 0
    while process.IsValid() and process.GetState() == lldb.eStateStopped and steps < max_steps:
        steps += 1
        process.Continue()
    state()["drive_steps"] = steps
    state()["drive_hit_step_cap"] = (
        process.IsValid()
        and process.GetState() == lldb.eStateStopped
        and steps >= max_steps
    )


def write_report(debugger, path):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    out = dict(state())
    out["process"] = {
        "state": lldb.SBDebugger.StateAsCString(process.GetState()),
        "exit_status": process.GetExitStatus(),
    }
    with open(path, "w", encoding="utf-8") as stream:
        json.dump(out, stream, indent=2, sort_keys=True)
        stream.write("\n")
    print("L16_VARIANT_PIPELINE_WROTE", path)
