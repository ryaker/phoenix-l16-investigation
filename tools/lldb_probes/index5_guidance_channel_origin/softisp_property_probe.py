import builtins
import json
import struct


CREATE_STEREO_ENTRY = 0x27B7A0
PROPERTY_LOOKUP_ENTRY = 0x31B610
PROPERTY_LOOKUP_RETURN = 0x31B692
STRING_EXTRACT_ENTRY = 0x31BBD0
STRING_EXTRACT_RETURN = 0x31BBDC
DIRECT_PACK_SOURCE = 0x27C062


def reset(label=""):
    builtins.l16_guidance_softisp_properties = {
        "label": label,
        "create_entries": [],
        "queried_properties": [],
        "lookups": [],
        "string_extracts": [],
        "pending_lookup": {},
        "pending_extract": {},
        "capture_complete": False,
        "terminated_after_capture": False,
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_guidance_softisp_properties"):
        reset()
    return builtins.l16_guidance_softisp_properties


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    if not address or size <= 0:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u64(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<Q", raw)[0] if raw is not None else None


def _libcpp_string(process, address):
    header = _read(process, address, 24)
    if header is None:
        return None
    if header[0] & 1:
        size = struct.unpack_from("<Q", header, 8)[0]
        data_pointer = struct.unpack_from("<Q", header, 16)[0]
        raw = _read(process, data_pointer, size)
    else:
        size = header[0] >> 1
        raw = header[1 : 1 + size]
    if raw is None:
        return None
    return raw.decode("utf-8", errors="replace")


def _libcp_base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                return base
    return None


def _module_va(frame):
    target = frame.GetThread().GetProcess().GetTarget()
    base = _libcp_base(target)
    return frame.GetPC() - base if base is not None else None


def _softisp_role(state, address):
    for index in range(len(state["create_entries"]) - 1, -1, -1):
        entry = state["create_entries"][index]
        if address == entry["softisp_1"]:
            return index, "softisp_1"
        if address == entry["softisp_2"]:
            return index, "softisp_2"
    return None, None


def _query_string_property(frame, object_address, name):
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    base = _libcp_base(target)
    if base is None:
        return {"name": name, "error": "unsupported query setup"}
    encoded = name.encode("ascii")
    lookup = base + PROPERTY_LOOKUP_ENTRY
    extract = base + STRING_EXTRACT_ENTRY
    if len(encoded) > 22:
        return {"name": name, "error": "property name too long"}
    short_string = [len(encoded) << 1] + list(encoded)
    short_string.extend([0] * (24 - len(short_string)))
    initializer = ",".join(str(value) for value in short_string)
    expression = (
        "({ struct L16Pair { void *first; void *second; }; "
        f"unsigned char text[24] = {{{initializer}}}; "
        "struct L16Pair pair = "
        f"((struct L16Pair (*)(void *, const void *))0x{lookup:x}ULL)"
        f"((void *)0x{object_address:x}ULL, (const void *)text); "
        f"(unsigned long)((void *(*)(struct L16Pair *))0x{extract:x}ULL)"
        "(&pair); })"
    )
    lldb = builtins.__import__("lldb")
    options = lldb.SBExpressionOptions()
    options.SetIgnoreBreakpoints(True)
    options.SetUnwindOnError(True)
    options.SetTimeoutInMicroSeconds(5_000_000)
    value = frame.EvaluateExpression(expression, options)
    error = value.GetError()
    if not error.Success():
        return {"name": name, "error": error.GetCString(), "expression": expression}
    value_address = value.GetValueAsUnsigned()
    return {
        "name": name,
        "value_address": value_address,
        "value": _libcpp_string(process, value_address),
    }


def hit(frame, bp_loc, internal_dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    thread_id = thread.GetThreadID()
    site = _module_va(frame)

    if site == CREATE_STEREO_ENTRY:
        rsp = _u(frame, "rsp")
        entry = {
                "thread_id": thread_id,
                "softisp_1": _u64(process, rsp + 0x08),
                "softisp_2": _u64(process, rsp + 0x10),
                "bool_same_camera": (
                    (_read(process, rsp + 0x30, 1) or b"\0")[0]
                ),
                "bool_second": ((_read(process, rsp + 0x38, 1) or b"\0")[0]),
            }
        state["create_entries"].append(entry)
        if len(state["create_entries"]) == 1:
            for role in ("softisp_1", "softisp_2"):
                for name in (
                    "demosaicking.type",
                    "hot_pixel_removal.type",
                    "color_correction.type",
                    "bayer_phase_fix.type",
                    "highlight_restore.type",
                    "lens_shading.type",
                    "denoising.type",
                    "tone_adjust.type",
                    "contrast_adjust.type",
                    "tone_mapping.type",
                    "output.color_space",
                    "output.white_point",
                ):
                    result = _query_string_property(frame, entry[role], name)
                    result["softisp_role"] = role
                    result["softisp_address"] = entry[role]
                    state["queried_properties"].append(result)
        return False

    if site == PROPERTY_LOOKUP_ENTRY:
        object_address = _u(frame, "rdi")
        entry_index, role = _softisp_role(state, object_address)
        if role is None:
            return False
        name = _libcpp_string(process, _u(frame, "rsi"))
        item = {
            "thread_id": thread_id,
            "create_entry_index": entry_index,
            "softisp_role": role,
            "softisp_address": object_address,
            "name": name,
            "node": None,
            "owner": None,
        }
        state["lookups"].append(item)
        state["pending_lookup"][str(thread_id)] = len(state["lookups"]) - 1
        if name is None:
            state["errors"].append("failed to decode property string")
        return False

    if site == PROPERTY_LOOKUP_RETURN:
        key = str(thread_id)
        index = state["pending_lookup"].pop(key, None)
        if index is not None:
            state["lookups"][index]["node"] = _u(frame, "rax")
            state["lookups"][index]["owner"] = _u(frame, "rdx")
        return False

    if site == STRING_EXTRACT_ENTRY:
        pair = _u(frame, "rdi")
        node = _u64(process, pair)
        owner = _u64(process, pair + 8)
        matches = [
            index
            for index, item in enumerate(state["lookups"])
            if item["node"] == node and item["owner"] == owner
        ]
        if matches:
            state["pending_extract"][str(thread_id)] = {
                "lookup_index": matches[-1],
                "node": node,
                "owner": owner,
            }
        return False

    if site == STRING_EXTRACT_RETURN:
        pending = state["pending_extract"].pop(str(thread_id), None)
        if pending is not None:
            value_address = _u(frame, "rax")
            pending["value_address"] = value_address
            pending["value"] = _libcpp_string(process, value_address)
            state["string_extracts"].append(pending)
        return False

    if site == DIRECT_PACK_SOURCE:
        state["capture_complete"] = True
        error = process.Kill()
        state["terminated_after_capture"] = error.Success()
        if not error.Success():
            state["errors"].append(f"kill failed: {error.GetCString()}")
        return False

    state["errors"].append(f"unexpected site {site}")
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    expected = {
        CREATE_STEREO_ENTRY,
        PROPERTY_LOOKUP_ENTRY,
        PROPERTY_LOOKUP_RETURN,
        STRING_EXTRACT_ENTRY,
        STRING_EXTRACT_RETURN,
        DIRECT_PACK_SOURCE,
    }
    found = set()
    for index in range(target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(index)
        if not bp or not bp.IsValid() or bp.GetNumLocations() < 1:
            continue
        site = bp.GetLocationAtIndex(0).GetAddress().GetFileAddress()
        if site in expected:
            bp.SetScriptCallbackFunction("softisp_property_probe.hit")
            found.add(site)
    if found != expected:
        _state()["errors"].append(
            "missing breakpoints: " + repr(sorted(expected - found))
        )
    print("L16_GUIDANCE_SOFTISP_PROPERTIES_ATTACHED", [hex(x) for x in sorted(found)])


def write_report(debugger, path):
    process = debugger.GetSelectedTarget().GetProcess()
    state = dict(_state())
    state.pop("pending_lookup", None)
    state.pop("pending_extract", None)
    state["process"] = {
        "state": process.GetState(),
        "exit_status": process.GetExitStatus(),
    }
    with open(path, "w", encoding="ascii") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_GUIDANCE_SOFTISP_PROPERTIES_REPORT", path)
