import builtins
import json
import struct


ENTRY_VA = 0x27B7A0
CAMERA_KEY_COMPARE_VA = 0x3F5035
POST_SOFTISP_BRANCH_VA = 0x27C2D6
POST_GUIDANCE_TRANSFORM_VA = 0x27C6D2
DIRECT_PACK_SOURCE_VA = 0x27C062


def reset(label=""):
    builtins.l16_guidance_component_branch = {
        "label": label,
        "camera_key_pairs": [],
        "entries": [],
        "direct_pack_sources": [],
        "post_softisp": None,
        "post_guidance_transform": None,
        "capture_complete": False,
        "terminated_after_capture": False,
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_guidance_component_branch"):
        reset()
    return builtins.l16_guidance_component_branch


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, addr, size):
    if not addr or size <= 0:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    data = process.ReadMemory(addr, size, error)
    if not error.Success() or len(data) != size:
        return None
    return data


def _u8(process, addr):
    raw = _read(process, addr, 1)
    return raw[0] if raw is not None else None


def _u64(process, addr):
    raw = _read(process, addr, 8)
    return struct.unpack("<Q", raw)[0] if raw is not None else None


def _image_vec4f(process, addr):
    raw = _read(process, addr, 0x30)
    if raw is None:
        return {"addr": addr, "read_ok": False}
    words = struct.unpack("<8iQQ", raw)
    width = words[4]
    height = words[5]
    stride = words[6]
    data = words[8]

    def pixel(x, y):
        if not data or x < 0 or y < 0 or x >= width or y >= height:
            return None
        value = _read(process, data + (y * stride + x) * 16, 16)
        return list(struct.unpack("<4f", value)) if value is not None else None

    positions = {
        "top_left": (0, 0),
        "quarter": (width // 4, height // 4),
        "center": (width // 2, height // 2),
        "three_quarter": (3 * width // 4, 3 * height // 4),
        "bottom_right": (max(width - 1, 0), max(height - 1, 0)),
    }
    return {
        "addr": addr,
        "read_ok": True,
        "raw_0x00_0x30": raw.hex(),
        "origin": list(words[0:2]),
        "bounds": list(words[2:4]),
        "size": [width, height],
        "stride": stride,
        "reserved": words[7],
        "data": data,
        "allocation": words[9],
        "samples": {
            name: {"xy": list(xy), "vec4f": pixel(*xy)}
            for name, xy in positions.items()
        },
    }


def _libcp_base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                return base
    return None


def _module_va(target, pc):
    base = _libcp_base(target)
    return pc - base if base is not None and pc >= base else None


def hit(frame, bp_loc, internal_dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    site = _module_va(target, frame.GetPC())
    if site == CAMERA_KEY_COMPARE_VA:
        state["camera_key_pairs"].append({
            "thread_id": thread.GetThreadID(),
            "source_camera_key_esi": _u(frame, "rsi") & 0xFFFFFFFF,
            "anchor_camera_key_rdi_pointee": (
                struct.unpack("<I", _read(process, _u(frame, "rdi"), 4))[0]
                if _read(process, _u(frame, "rdi"), 4) is not None
                else None
            ),
        })
        return False
    if site == ENTRY_VA:
        rsp = _u(frame, "rsp")
        state["entries"].append({
            "thread_id": thread.GetThreadID(),
            "output_vec4u8_rdi": _u(frame, "rdi"),
            "input_u16_rsi": _u(frame, "rsi"),
            "captured_image_rdx": _u(frame, "rdx"),
            "calib_data_1_rcx": _u(frame, "rcx"),
            "calib_data_2_r8": _u(frame, "r8"),
            "size_r9": _u(frame, "r9"),
            "softisp_1_stack": _u64(process, rsp + 0x08),
            "softisp_2_stack": _u64(process, rsp + 0x10),
            "vec3_stack": _u64(process, rsp + 0x18),
            "output_vec4f_stack": _u64(process, rsp + 0x20),
            "calib_data_3_stack": _u64(process, rsp + 0x28),
            "bool_1_stack": _u8(process, rsp + 0x30),
            "bool_2_stack": _u8(process, rsp + 0x38),
        })
        return False
    if site == DIRECT_PACK_SOURCE_VA:
        matching_entries = [
            (index, entry)
            for index, entry in enumerate(state["entries"])
            if entry["thread_id"] == thread.GetThreadID()
        ]
        state["direct_pack_sources"].append(
            {
                "thread_id": thread.GetThreadID(),
                "matched_entry_index": (
                    matching_entries[-1][0] if matching_entries else None
                ),
                "source_vec4f_rbx": _image_vec4f(process, _u(frame, "rbx")),
            }
        )
        if not matching_entries:
            state["errors"].append("direct pack source reached without entry")
        return False
    if site == POST_SOFTISP_BRANCH_VA:
        rbp = _u(frame, "rbp")
        source = _u(frame, "rbx")
        state["post_softisp"] = {
            "thread_id": thread.GetThreadID(),
            "bool_1_rbp_0x38": _u8(process, rbp + 0x38),
            "bool_2_rbp_0x40": _u8(process, rbp + 0x40),
            "source_vec4f_rbx": _image_vec4f(process, source),
        }
        matching_entries = [
            (index, entry)
            for index, entry in enumerate(state["entries"])
            if entry["thread_id"] == thread.GetThreadID()
        ]
        if not matching_entries:
            state["errors"].append("post-SoftISP branch reached without entry")
        else:
            entry_index, entry = matching_entries[-1]
            state["post_softisp"]["matched_entry_index"] = entry_index
            if entry["output_vec4f_stack"] != source:
                state["errors"].append(
                    "matched public output Image<vec4x32f> is not rbx source"
                )
        return False
    if site == POST_GUIDANCE_TRANSFORM_VA:
        rbp = _u(frame, "rbp")
        state["post_guidance_transform"] = {
            "thread_id": thread.GetThreadID(),
            "input_vec4f_rbp_minus_0x2a0": _image_vec4f(
                process, rbp - 0x2A0
            ),
            "transformed_vec4f_rbp_minus_0x5d0": _image_vec4f(
                process, rbp - 0x5D0
            ),
            "transform_object_raw_0x00_0x110": (
                _read(process, rbp - 0x1A0, 0x110) or b""
            ).hex(),
        }
        if state.get("post_softisp") is None:
            state["errors"].append("transform reached without post-SoftISP packet")
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
    found = []
    for index in range(target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(index)
        if not bp or not bp.IsValid() or bp.GetNumLocations() < 1:
            continue
        site = bp.GetLocationAtIndex(0).GetAddress().GetFileAddress()
        if site in (
            CAMERA_KEY_COMPARE_VA,
            ENTRY_VA,
            DIRECT_PACK_SOURCE_VA,
            POST_SOFTISP_BRANCH_VA,
            POST_GUIDANCE_TRANSFORM_VA,
        ):
            bp.SetScriptCallbackFunction("guidance_component_branch_probe.hit")
            found.append(site)
    expected = sorted(
        (
            CAMERA_KEY_COMPARE_VA,
            ENTRY_VA,
            DIRECT_PACK_SOURCE_VA,
            POST_SOFTISP_BRANCH_VA,
            POST_GUIDANCE_TRANSFORM_VA,
        )
    )
    if sorted(found) != expected:
        _state()["errors"].append(f"missing breakpoints: {found}")
    print("L16_GUIDANCE_COMPONENT_BRANCH_ATTACHED", [hex(x) for x in found])


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
    print("L16_GUIDANCE_COMPONENT_BRANCH_REPORT", path)
