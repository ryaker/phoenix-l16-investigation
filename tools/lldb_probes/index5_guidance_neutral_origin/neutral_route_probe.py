import builtins
import json
import struct


SITES = {
    0xE5720: "selector_source_test",
    0xE574D: "selector_copy_call",
    0xE5752: "selector_copy_done",
    0x144560: "selector_temp_entry",
    0x1BD270: "entry",
    0x1BD597: "gains_optional",
    0x1BD5A5: "mode_optional",
    0x1BD5CA: "default_route",
    0x1BD675: "default_result",
    0x1BD6A8: "stored_route",
    0x1BD715: "neutral_ready",
    0x318218: "default_output_ready",
    0x33E430: "stats_entry",
    0x33E5F1: "stage1_call",
    0x33E5F3: "stage1_done",
    0x33E611: "stage2_call",
    0x33E613: "stage2_done",
    0x342730: "awb_worker_entry",
    0x342752: "awb_candidates_ready",
    0x3427B7: "awb_solve_call",
    0x3427BC: "awb_solve_done",
    0x2D36BA: "solver_live_entry",
    0x2D39D7: "solver_bounds_ready",
    0x2D3CC8: "solver_points_ready",
    0x2D3F54: "solver_scene_weight_ready",
    0x2D3F86: "solver_table1_call",
    0x2D3FA0: "solver_table2_call",
    0x2D3FA5: "solver_table_results",
    0x2D3FD9: "solver_table1_scale",
    0x2D4004: "solver_table2_scale",
    0x2D424D: "solver_neutral_ready",
    0x2D4276: "solver_xy_ready",
}


def reset(output_path, source_lri):
    builtins.l16_guidance_neutral = {
        "output_path": output_path,
        "source_lri": source_lri,
        "events": [],
        "selector_merge": [],
        "active": {},
        "stats_owner_by_thread": {},
        "solver_active": {},
        "solver_traces": [],
        "completed": [],
        "errors": [],
    }


def _state():
    return builtins.l16_guidance_neutral


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    import lldb

    error = lldb.SBError()
    raw = process.ReadMemory(address, size, error)
    if not error.Success() or len(raw) != size:
        return None
    return raw


def _base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            address = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if address != 0xFFFFFFFFFFFFFFFF:
                return address
    return None


def _optional_vec3(process, address):
    raw = _read(process, address, 0x10)
    if raw is None:
        return None
    return {
        "address": address,
        "value": list(struct.unpack("<3f", raw[:12])),
        "present": raw[12] != 0,
        "raw": raw.hex(),
    }


def _optional_i32(process, address):
    raw = _read(process, address, 0x28)
    if raw is None:
        return None
    return {
        "address": address,
        "value": struct.unpack("<i", raw[:4])[0],
        "present": raw[0x24] != 0,
        "raw": raw.hex(),
    }


def _vec3(process, address):
    raw = _read(process, address, 12)
    return list(struct.unpack("<3f", raw)) if raw is not None else None


def _u64(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<Q", raw)[0] if raw is not None else None


def _cstring(process, address, limit=256):
    if not address:
        return None
    data = bytearray()
    for offset in range(limit):
        raw = _read(process, address + offset, 1)
        if raw is None or raw == b"\x00":
            break
        data.extend(raw)
    return data.decode("ascii", errors="replace") if data else None


def _rtti(process, address, base):
    vtable = _u64(process, address)
    typeinfo = _u64(process, vtable - 8) if vtable else None
    name_pointer = _u64(process, typeinfo + 8) if typeinfo else None
    return {
        "vtable": vtable,
        "vtable_va": vtable - base if vtable and base is not None else None,
        "typeinfo": typeinfo,
        "typeinfo_va": typeinfo - base if typeinfo and base is not None else None,
        "name_pointer": name_pointer,
        "name": _cstring(process, name_pointer),
    }


def _snapshot(process, address, size=0x80):
    raw = _read(process, address, size)
    if raw is None:
        return None
    return {
        "address": address,
        "raw": raw.hex(),
        "f32": list(struct.unpack("<%df" % (size // 4), raw)),
    }


def _vector(process, address, element_size, max_elements=20000):
    raw = _read(process, address, 24)
    if raw is None:
        return None
    begin, end, capacity = struct.unpack("<3Q", raw)
    valid = begin <= end <= capacity and element_size > 0
    count = (end - begin) // element_size if valid else None
    payload = None
    if valid and count is not None and count <= max_elements:
        payload = _read(process, begin, count * element_size)
    return {
        "address": address,
        "begin": begin,
        "end": end,
        "capacity": capacity,
        "element_size": element_size,
        "count": count,
        "raw": raw.hex(),
        "payload": payload.hex() if payload is not None else None,
    }


def _float_image(process, address, max_elements=20000, read_payload=True):
    raw = _read(process, address, 0x28)
    if raw is None:
        return None
    width, height = struct.unpack_from("<II", raw, 0x10)
    begin, end = struct.unpack_from("<QQ", raw, 0x18)
    count = (end - begin) // 4 if begin <= end else None
    payload = None
    if read_payload and count is not None and count <= max_elements:
        payload = _read(process, begin, count * 4)
    return {
        "address": address,
        "width": width,
        "height": height,
        "begin": begin,
        "end": end,
        "count": count,
        "header_raw": raw.hex(),
        "payload": payload.hex() if payload is not None else None,
    }


def hit(frame, bp_loc, internal_dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    base = _base(target)
    site = frame.GetPC() - base if base is not None else None
    name = SITES.get(site)
    thread_id = str(thread.GetThreadID())
    if name is None:
        return False

    try:
        if name == "selector_source_test":
            source = _u(frame, "rbx")
            selector = _u64(process, source + 0xF0)
            state["selector_merge"].append({
                "phase": name,
                "source_header": source,
                "destination_stack": _u(frame, "r13"),
                "source_has_selector": bool((_read(process, source + 0x11, 1) or b"\0")[0] & 2),
                "source_selector_pointer": selector,
                "source_selector_rtti": _rtti(process, selector, base) if selector else None,
                "source_selector_snapshot": _snapshot(process, selector, 0x30) if selector else None,
            })
        elif name == "selector_temp_entry":
            source = _u(frame, "rsi")
            state["selector_merge"].append({
                "phase": name,
                "temporary_destination": _u(frame, "rdi"),
                "source": source,
                "source_rtti": _rtti(process, source, base),
                "source_snapshot": _snapshot(process, source, 0x30),
            })
        elif name == "selector_copy_call":
            source = _u(frame, "rsi")
            state["selector_merge"].append({
                "phase": name,
                "destination": _u(frame, "rdi"),
                "source": source,
                "source_rtti": _rtti(process, source, base),
                "source_snapshot": _snapshot(process, source, 0x30),
            })
        elif name == "selector_copy_done":
            destination = _u(frame, "rdi")
            state["selector_merge"].append({
                "phase": name,
                "destination": destination,
                "destination_snapshot": _snapshot(process, destination, 0x28),
            })
        elif name.startswith("solver_"):
            bp_loc.SetEnabled(False)
            rbp = _u(frame, "rbp")
            trace = state["solver_active"].setdefault(
                thread_id,
                {"thread_id": int(thread_id), "source_lri": state["source_lri"]},
            )
            if name == "solver_live_entry":
                trace[name] = {
                    "candidate_pair": _u(frame, "r13"),
                    "output": _u(frame, "r15"),
                    "stack": _snapshot(process, rbp - 0x210, 0x1F0),
                }
            elif name == "solver_bounds_ready":
                trace[name] = {"stack": _snapshot(process, rbp - 0x1B0, 0x130)}
            elif name == "solver_points_ready":
                trace[name] = {
                    "points": _vector(process, rbp - 0x100, 8),
                    "stack": _snapshot(process, rbp - 0x1B0, 0x130),
                }
            elif name == "solver_scene_weight_ready":
                trace[name] = {
                    "scene_weight": _snapshot(process, rbp - 0x164, 4),
                    "stack": _snapshot(process, rbp - 0x1B0, 0x130),
                }
            elif name in ("solver_table1_call", "solver_table2_call"):
                trace[name] = {
                    "output": _u(frame, "rdi"),
                    "points": _vector(process, _u(frame, "rsi"), 8),
                    "table": _float_image(process, _u(frame, "rdx")),
                }
            elif name == "solver_table_results":
                trace[name] = {
                    "table1_result": _snapshot(process, rbp - 0x108, 8),
                    "table2_result": _snapshot(process, rbp - 0x110, 8),
                    "stack": _snapshot(process, rbp - 0x1B0, 0x130),
                }
            elif name == "solver_table1_scale":
                trace[name] = {
                    "table1_result": _snapshot(process, rbp - 0x108, 8),
                    "scale": _snapshot(process, rbp - 0x188, 4),
                }
            elif name == "solver_table2_scale":
                trace[name] = {
                    "table2_result": _snapshot(process, rbp - 0x110, 8),
                    "scale": _snapshot(process, rbp - 0x180, 4),
                }
            elif name == "solver_neutral_ready":
                trace[name] = {
                    "neutral": _snapshot(process, rbp - 0x120, 12),
                    "stack": _snapshot(process, rbp - 0x1B0, 0x130),
                }
            elif name == "solver_xy_ready":
                trace[name] = {
                    "neutral": _snapshot(process, rbp - 0x120, 12),
                    "xyz": _snapshot(process, rbp - 0x130, 12),
                    "xy": _snapshot(process, rbp - 0x128, 8),
                }
                state["solver_traces"].append(trace)
                del state["solver_active"][thread_id]
        elif name == "entry":
            current = {
                "thread_id": int(thread_id),
                "factory": _u(frame, "rdi"),
                "capture_stack": _u(frame, "rsi"),
                "camera_index": _u(frame, "rdx") & 0xFFFFFFFF,
                "route": None,
            }
            state["active"][thread_id] = current
        else:
            current = state["active"].get(thread_id)
            if name == "stats_entry":
                output = _u(frame, "rsi")
                owner = next(
                    (
                        key
                        for key, item in state["active"].items()
                        if item.get("default_output") == output
                    ),
                    None,
                )
                if owner is None:
                    return False
                current = state["active"][owner]
                state["stats_owner_by_thread"][thread_id] = owner
            elif name.startswith("stage"):
                owner = state["stats_owner_by_thread"].get(thread_id)
                if owner is None or owner not in state["active"]:
                    return False
                current = state["active"][owner]
            elif current is None:
                return False

            if name == "gains_optional":
                current["gains_optional"] = _optional_vec3(process, _u(frame, "rax"))
            elif name == "mode_optional":
                current["mode_optional"] = _optional_i32(process, _u(frame, "rax"))
            elif name == "default_route":
                current["route"] = "default_awb"
            elif name == "default_result":
                current["default_result"] = _vec3(process, _u(frame, "rax"))
            elif name == "default_output_ready":
                current["default_output"] = _u64(process, _u(frame, "r14"))
            elif name == "stored_route":
                current["route"] = "stored_gains"
            elif name == "neutral_ready":
                current["neutral"] = _vec3(process, current["factory"] + 0x74)
                state["completed"].append(current)
                del state["active"][thread_id]
            elif name == "stats_entry":
                current["stats"] = {
                    "pipeline": _u(frame, "rdi"),
                    "output": _u(frame, "rsi"),
                    "image_descriptor": _u(frame, "rdx"),
                    "roi": _u(frame, "rcx"),
                    "output_entry": _snapshot(process, _u(frame, "rsi")),
                }
            elif name in ("stage1_call", "stage2_call"):
                stats = current.setdefault("stats", {})
                callback = _u(frame, "rax")
                stats[name] = {
                    "worker": callback,
                    "worker_va": callback - base if base is not None else None,
                    "object": _u(frame, "rdi"),
                    "object_snapshot": _snapshot(process, _u(frame, "rdi")),
                    "output_before": _snapshot(process, _u(frame, "rsi")),
                }
            elif name in ("stage1_done", "stage2_done"):
                stats = current.setdefault("stats", {})
                stats[name] = {
                    "output_after": _snapshot(process, stats.get("output", 0)),
                }
            elif name == "awb_worker_entry":
                stats = current.setdefault("stats", {})
                stats["awb_worker"] = {
                    "stage_object": _u(frame, "rdi"),
                    "output": _u(frame, "rsi"),
                    "prepared_image": _u(frame, "rdx"),
                    "source_image": _u(frame, "rcx"),
                }
            elif name == "awb_candidates_ready":
                stats = current.setdefault("stats", {})
                stats.setdefault("awb_worker", {})["candidates"] = {
                    "vec4": _vector(process, _u(frame, "rbp") - 0x48, 16),
                    "aux": _vector(process, _u(frame, "rbp") - 0x30, 8),
                }
            elif name == "awb_solve_call":
                stats = current.setdefault("stats", {})
                stats.setdefault("awb_worker", {})["solve_call"] = {
                    "output": _u(frame, "rdi"),
                    "candidate_pair": _u(frame, "rsi"),
                    "source_image": _u(frame, "rdx"),
                    "calibration": _u(frame, "rcx"),
                    "calibration_snapshot": _snapshot(process, _u(frame, "rcx"), 0x80),
                    "table1": _float_image(
                        process, base + 0x6708F0
                    ),
                    "table2": _float_image(
                        process, base + 0x6708C0
                    ),
                }
            elif name == "awb_solve_done":
                stats = current.setdefault("stats", {})
                output = _u(frame, "rbp") - 0x78
                stats.setdefault("awb_worker", {})["solve_result"] = _snapshot(
                    process, output, 0x10
                )
        state["events"].append(
            {"site": name, "thread_id": int(thread_id), "pc_va": site}
        )
    except Exception as error:
        state["errors"].append("%s:%s" % (name, error))
    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    for breakpoint in target.breakpoint_iter():
        breakpoint.SetScriptCallbackFunction("neutral_route_probe.hit")


def write_report(debugger):
    state = _state()
    with open(state["output_path"], "w", encoding="ascii") as output:
        json.dump(state, output, indent=1, sort_keys=True)
        output.write("\n")
    print(
        "GUIDANCE_NEUTRAL_REPORT",
        state["output_path"],
        "completed",
        len(state["completed"]),
        "errors",
        len(state["errors"]),
    )
