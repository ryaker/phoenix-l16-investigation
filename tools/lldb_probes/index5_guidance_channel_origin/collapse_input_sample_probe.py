import builtins
import json
import struct


CAMERA_KEY_COMPARE_VA = 0x3F5035
CREATE_STEREO_ENTRY_VA = 0x27B7A0
SOFTISP_TILE_ENTRY_VA = 0x27D5B0
LOADS = {
    0xA4CED: ((1, 0), (0, 0), (0, 1), (1, 1)),
    0xA52FD: ((1, 0), (0, 0), (1, 1), (0, 1)),
    0xA590D: ((0, 1), (0, 0), (1, 1), (1, 0)),
    0xA5F1D: ((1, 1), (1, 0), (0, 1), (0, 0)),
}


def reset(label, wanted_key=0, source_lri=None, packet_limit=64):
    builtins.l16_collapse_input_sample = {
        "label": label,
        "wanted_key": int(wanted_key),
        "source_lri": source_lri,
        "packet_limit": int(packet_limit),
        "last_key_by_thread": {},
        "entries_by_key": {},
        "softisp_tiles": [],
        "softisp_breakpoint_id": None,
        "entry": None,
        "packet": None,
        "packets": [],
        "errors": [],
        "terminated_after_capture": False,
    }


def _state():
    if not hasattr(builtins, "l16_collapse_input_sample"):
        reset("")
    return builtins.l16_collapse_input_sample


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _i32(value):
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def _read(process, address, size):
    if not address or size <= 0:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    raw = process.ReadMemory(address, size, error)
    return raw if error.Success() and len(raw) == size else None


def _u64(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<Q", raw)[0] if raw is not None else None


def _base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            address = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if address != 0xFFFFFFFFFFFFFFFF:
                return address
    return None


def _enable_breakpoint(process, breakpoint_id):
    if breakpoint_id is None:
        return
    breakpoint = process.GetTarget().FindBreakpointByID(breakpoint_id)
    if breakpoint and breakpoint.IsValid():
        breakpoint.SetEnabled(True)


def _descriptor(process, address):
    raw = _read(process, address, 0x30)
    if raw is None:
        return None
    words = struct.unpack("<8iQQ", raw)
    return {
        "address": address,
        "origin": list(words[0:2]),
        "bounds": list(words[2:4]),
        "size": list(words[4:6]),
        "stride": words[6],
        "reserved": words[7],
        "data": words[8],
        "allocation": words[9],
        "raw": raw.hex(),
    }


def hit(frame, bp_loc, internal_dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    base = _base(process.GetTarget())
    site = frame.GetPC() - base if base is not None else None
    thread_id = thread.GetThreadID()
    if site == CAMERA_KEY_COMPARE_VA:
        state["last_key_by_thread"][str(thread_id)] = _u(frame, "rsi") & 0xFFFFFFFF
        return False
    if site == CREATE_STEREO_ENTRY_VA:
        key = state["last_key_by_thread"].get(str(thread_id))
        descriptor = _descriptor(process, _u(frame, "rsi"))
        if key is not None and descriptor is not None:
            state["entries_by_key"][str(key)] = descriptor
        if state["entry"] is None and key == state["wanted_key"]:
            state["entry"] = {
                "thread_id": thread_id,
                "source_key": key,
                "input_u16_descriptor": descriptor,
            }
            _enable_breakpoint(process, state["softisp_breakpoint_id"])
        return False
    if site == SOFTISP_TILE_ENTRY_VA:
        if state["entry"] is None or len(state["softisp_tiles"]) >= 512:
            return False
        closure = _u(frame, "rdi")
        rectangle_raw = _read(process, _u(frame, "rsi"), 16)
        output_descriptor = _descriptor(process, _u64(process, closure + 0x08))
        input_descriptor = _descriptor(process, _u64(process, closure + 0x20))
        if rectangle_raw is not None:
            state["softisp_tiles"].append(
                {
                    "thread_id": thread_id,
                    "closure": closure,
                    "rectangle": list(struct.unpack("<4i", rectangle_raw)),
                    "output_descriptor": output_descriptor,
                    "input_descriptor": input_descriptor,
                }
            )
        return False
    if (
        site not in LOADS
        or state["entry"] is None
        or state["terminated_after_capture"]
    ):
        return False

    x0 = _i32(_u(frame, "r14")) + (_u(frame, "rcx") & 0xFFFFFFFF)
    y0 = _i32(_u(frame, "r13"))
    coordinates = [(x0 + dx, y0 + dy) for dx, dy in LOADS[site]]
    source = state["entry"]["input_u16_descriptor"]
    if source is None or any(
        x < 0 or y < 0 or x >= source["size"][0] or y >= source["size"][1]
        for x, y in coordinates
    ):
        return False

    rbp = _u(frame, "rbp")
    closure = _u64(process, rbp - 0xC8)
    demosaic_object = _u64(process, closure + 0x08)
    float_descriptor = _descriptor(process, _u64(process, demosaic_object + 0x08))
    collapse_descriptor = _descriptor(process, _u64(process, demosaic_object + 0x10))
    rectangle_raw = _read(process, _u(frame, "r12"), 16)
    if float_descriptor is None or rectangle_raw is None:
        state["errors"].append("descriptor/rectangle read failed")
        return False

    lanes = []
    for (x, y), (register, displacement) in zip(
        coordinates,
        {
            0xA4CED: (("rax", -4), ("rax", 0), ("rdi", 0), ("rdi", 4)),
            0xA52FD: (("rax", 0), ("rax", -4), ("rdi", 4), ("rdi", 0)),
            0xA590D: (("rdi", 0), ("rax", -4), ("rdi", 4), ("rax", 0)),
            0xA5F1D: (("rdi", 4), ("rax", 0), ("rdi", 0), ("rax", -4)),
        }[site],
    ):
        float_address = _u(frame, register) + _u(frame, "rcx") * 4 + displacement
        float_raw = _read(process, float_address, 4)
        raw_by_key = {}
        for key, descriptor in state["entries_by_key"].items():
            if x >= descriptor["size"][0] or y >= descriptor["size"][1]:
                continue
            address = descriptor["data"] + (y * descriptor["stride"] + x) * 2
            value_raw = _read(process, address, 2)
            if value_raw is not None:
                raw_by_key[key] = struct.unpack("<H", value_raw)[0]
        raw_address = source["data"] + (y * source["stride"] + x) * 2
        sensor_raw = _read(process, raw_address, 2)
        if float_raw is None or sensor_raw is None:
            state["errors"].append("lane read failed")
            return False
        lanes.append(
            {
                "xy": [x, y],
                "float_address": float_address,
                "float_value": struct.unpack("<f", float_raw)[0],
                "float_bits": struct.unpack("<I", float_raw)[0],
                "raw_u16_address": raw_address,
                "raw_u16": struct.unpack("<H", sensor_raw)[0],
                "raw_u16_by_key": raw_by_key,
            }
        )
    packet = {
        "site": site,
        "thread_id": thread_id,
        "rectangle": list(struct.unpack("<4i", rectangle_raw)),
        "float_descriptor": float_descriptor,
        "collapse_descriptor": collapse_descriptor,
        "known_input_keys": sorted(int(key) for key in state["entries_by_key"]),
        "lanes_rg1g2b": lanes,
    }
    state["packets"].append(packet)
    if state["packet"] is None:
        state["packet"] = packet
    if len(state["packets"]) >= state["packet_limit"]:
        error = process.Kill()
        state["terminated_after_capture"] = error.Success()
        if not error.Success():
            state["errors"].append(f"kill failed: {error.GetCString()}")
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    expected = {
        CAMERA_KEY_COMPARE_VA,
        CREATE_STEREO_ENTRY_VA,
        SOFTISP_TILE_ENTRY_VA,
    } | set(LOADS)
    found = set()
    for index in range(target.GetNumBreakpoints()):
        breakpoint = target.GetBreakpointAtIndex(index)
        if not breakpoint or not breakpoint.IsValid() or breakpoint.GetNumLocations() < 1:
            continue
        site = breakpoint.GetLocationAtIndex(0).GetAddress().GetFileAddress()
        if site in expected:
            breakpoint.SetScriptCallbackFunction("collapse_input_sample_probe.hit")
            if site == SOFTISP_TILE_ENTRY_VA:
                breakpoint.SetEnabled(False)
                _state()["softisp_breakpoint_id"] = breakpoint.GetID()
            found.add(site)
    if found != expected:
        _state()["errors"].append(f"missing sites {sorted(expected - found)}")
    print("COLLAPSE_INPUT_SAMPLE_ATTACHED", [hex(site) for site in sorted(found)])


def write_report(debugger, path):
    process = debugger.GetSelectedTarget().GetProcess()
    state = dict(_state())
    state["process"] = {
        "state": process.GetState(),
        "exit_status": process.GetExitStatus(),
    }
    with open(path, "w", encoding="ascii") as output:
        json.dump(state, output, indent=2, sort_keys=True)
        output.write("\n")
    print("COLLAPSE_INPUT_SAMPLE_REPORT", path)
