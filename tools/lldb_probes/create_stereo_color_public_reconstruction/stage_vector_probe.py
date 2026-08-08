import builtins
import hashlib
import json
import os
import struct


CREATE_ENTRY = 0x27B7A0
COLOR_CLOSURE_WORKER = 0x27D5B0
STAGE_EXECUTOR_ENTRY = 0x33F180
STAGE_CALL = 0x33F3E8
STAGE_RETURN = 0x33F3EB
STAGE_EXECUTOR_RETURN = 0x33F477

# Internal lineage sites for resolving the lazy stage-5 descriptor route.
STAGE5_WRAPPER = 0x341B30
STAGE5_FALSE_FACTORY = 0xF9EF0
STAGE5_TRUE_FACTORY = 0xFB6A0
STAGE5_VEC4_FALSE_CALLBACK = 0xFEBF0
STAGE5_FLOAT_FALSE_CALLBACK = 0x100680
STAGE5_VEC4_TRUE_CALLBACK = 0x103120
STAGE5_FLOAT_TRUE_CALLBACK = 0x1054D0
STAGE5_VEC4_FALSE_SECONDARY = 0x100560
STAGE5_FLOAT_FALSE_SECONDARY = 0x1019A0
STAGE5_VEC4_TRUE_SECONDARY = 0x1053B0
STAGE5_FLOAT_TRUE_SECONDARY = 0x106C80
DEMOSAIC_CALL = 0x342D99
DEMOSAIC_ADAPTER = 0x342B80
DEMOSAIC_ENTRY = 0x2EB560
LINEAGE_SITES = {
    STAGE5_WRAPPER: "stage5_wrapper",
    STAGE5_FALSE_FACTORY: "stage5_false_factory",
    STAGE5_TRUE_FACTORY: "stage5_true_factory",
    STAGE5_VEC4_FALSE_CALLBACK: "stage5_vec4_false_callback",
    STAGE5_FLOAT_FALSE_CALLBACK: "stage5_float_false_callback",
    STAGE5_VEC4_TRUE_CALLBACK: "stage5_vec4_true_callback",
    STAGE5_FLOAT_TRUE_CALLBACK: "stage5_float_true_callback",
    STAGE5_VEC4_FALSE_SECONDARY: "stage5_vec4_false_secondary",
    STAGE5_FLOAT_FALSE_SECONDARY: "stage5_float_false_secondary",
    STAGE5_VEC4_TRUE_SECONDARY: "stage5_vec4_true_secondary",
    STAGE5_FLOAT_TRUE_SECONDARY: "stage5_float_true_secondary",
    DEMOSAIC_CALL: "demosaic_call",
    DEMOSAIC_ADAPTER: "demosaic_adapter",
    DEMOSAIC_ENTRY: "demosaic_entry",
}


def reset(label="", output_dir="", camera_key=None, terminate_on_complete=False):
    builtins.l16_color_stage_vector = {
        "label": label,
        "output_dir": output_dir,
        "camera_key": camera_key,
        "terminate_on_complete": terminate_on_complete,
        "create_input": None,
        "create_inputs": [],
        "site_hits": {},
        "lineage_hits": {name: 0 for name in LINEAGE_SITES.values()},
        "lineage_samples": [],
        "active_thread": None,
        "closure": None,
        "executors": [],
        "selected_executor": None,
        "executor_stack": [],
        "calls": [],
        "pending_calls": [],
        "breakpoints": {},
        "complete": False,
        "terminated_after_capture": False,
        "breakpoints_disabled_after_capture": False,
        "launch_error": None,
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_color_stage_vector"):
        reset()
    return builtins.l16_color_stage_vector


def _u(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    if not address or size <= 0:
        return None
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    raw = process.ReadMemory(address, size, error)
    if not error.Success() or len(raw) != size:
        return None
    return raw


def _u64(process, address):
    raw = _read(process, address, 8)
    return struct.unpack("<Q", raw)[0] if raw is not None else None


def _u32(process, address):
    raw = _read(process, address, 4)
    return struct.unpack("<I", raw)[0] if raw is not None else None


def _base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            value = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if value != 0xFFFFFFFFFFFFFFFF:
                return value
    return None


def _cstring(process, address, limit=2048):
    raw = _read(process, address, limit)
    if raw is None:
        return None
    raw = raw.split(b"\0", 1)[0]
    try:
        return raw.decode("ascii")
    except UnicodeDecodeError:
        return None


def _descriptor(process, address):
    raw = _read(process, address, 0x30)
    if raw is None:
        return None
    words = struct.unpack("<8iQQ", raw)
    origin = list(words[0:2])
    bounds = list(words[2:4])
    size = list(words[4:6])
    stride = words[6]
    data = words[8]
    allocation = words[9]
    if not (
        -16384 <= origin[0] <= 16384
        and -16384 <= origin[1] <= 16384
        and -16384 <= bounds[0] <= 32768
        and -16384 <= bounds[1] <= 32768
        and 0 <= size[0] <= 16384
        and 0 <= size[1] <= 16384
        and 0 <= stride <= 65536
        and (size[0] == 0 or stride >= size[0])
        and (data == 0 or data > 0x10000)
        and (allocation == 0 or allocation > 0x10000)
    ):
        return None
    return {
        "address": address,
        "origin": origin,
        "bounds": bounds,
        "size": size,
        "stride": stride,
        "reserved": words[7],
        "data": data,
        "allocation": allocation,
        "raw": raw.hex(),
    }


def _rtti(process, object_address, base):
    vtable = _u64(process, object_address)
    typeinfo = _u64(process, vtable - 8) if vtable else None
    name_pointer = _u64(process, typeinfo + 8) if typeinfo else None
    worker = _u64(process, vtable + 0x30) if vtable else None
    return {
        "object": object_address,
        "vtable": vtable,
        "vtable_va": vtable - base if vtable and base else None,
        "typeinfo": typeinfo,
        "type_name": _cstring(process, name_pointer) if name_pointer else None,
        "worker": worker,
        "worker_va": worker - base if worker and base else None,
    }


def _sample_data(process, descriptor, limit=256):
    if descriptor is None or not descriptor["data"]:
        return None
    raw = _read(process, descriptor["data"], limit)
    if raw is None:
        return None
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "raw": raw.hex()}


def _descriptor_candidates(process, object_address, object_raw):
    candidates = []
    seen = set()
    for offset in range(0, len(object_raw) - 7, 8):
        pointer = struct.unpack_from("<Q", object_raw, offset)[0]
        for source, address in (("inline", object_address + offset), ("pointer", pointer)):
            if not address or address in seen:
                continue
            descriptor = _descriptor(process, address)
            if descriptor is None:
                continue
            seen.add(address)
            candidates.append(
                {
                    "object_offset": offset,
                    "source": source,
                    "descriptor": descriptor,
                    "data_sample": _sample_data(process, descriptor),
                }
            )
    return candidates


def _payload_slots(process, tile_address):
    slots = {}
    for offset in (0x40, 0x70, 0xA0, 0xD0, 0x100):
        descriptor = _descriptor(process, tile_address + offset)
        if (
            descriptor is None
            or descriptor["size"][0] <= 0
            or descriptor["size"][1] <= 0
            or not descriptor["data"]
        ):
            continue
        slots[hex(offset)] = {
            "descriptor": descriptor,
            "data_sample": _sample_data(process, descriptor),
        }
    return slots


def _dump_payload_slots(process, snapshot, label):
    state = _state()
    output_dir = state["output_dir"]
    if not output_dir:
        return
    bytes_per_pixel = {"0x70": 16, "0xd0": 4, "0x100": 2}
    for slot, item in snapshot["payload_slots"].items():
        element_size = bytes_per_pixel.get(slot)
        if element_size is None:
            continue
        descriptor = item["descriptor"]
        byte_count = descriptor["stride"] * descriptor["size"][1] * element_size
        if byte_count <= 0 or byte_count > 32 * 1024 * 1024:
            continue
        raw = _read(process, descriptor["data"], byte_count)
        if raw is None:
            continue
        filename = f"{label}_slot_{slot[2:]}.bin"
        path = os.path.join(output_dir, filename)
        with open(path, "wb") as handle:
            handle.write(raw)
        item["artifact"] = {
            "path": path,
            "bytes": len(raw),
            "bytes_per_pixel": element_size,
            "sha256": hashlib.sha256(raw).hexdigest(),
        }


def _snapshot(process, object_address, tile_address, base):
    object_raw = _read(process, object_address, 0x180) or b""
    tile_raw = _read(process, tile_address, 0x140) or b""
    identity = _rtti(process, object_address, base)
    snapshot = {
        "rtti": identity,
        "object_raw": object_raw.hex(),
        "tile_address": tile_address,
        "tile_raw": tile_raw.hex(),
        "payload_slots": _payload_slots(process, tile_address),
    }
    if identity["worker_va"] == 0x345D50:
        pipeline = _u64(process, object_address + 8)
        settings_raw = _read(process, pipeline + 0x1618, 8) if pipeline else None
        snapshot["lens_context"] = {
            "pipeline": pipeline,
            "settings_raw": settings_raw.hex() if settings_raw else None,
            "multiplier": struct.unpack("<f", settings_raw[:4])[0]
            if settings_raw
            else None,
            "inverse": settings_raw[4] if settings_raw else None,
            "payload_profile_pointer": _u64(process, tile_address + 8),
        }
    return snapshot


def _stage_vector(process, vector_address, base):
    begin = _u64(process, vector_address)
    end = _u64(process, vector_address + 8)
    if not begin or not end or end < begin or (end - begin) % 8:
        return {"address": vector_address, "begin": begin, "end": end, "stages": []}
    count = (end - begin) // 8
    if count > 256:
        return {"address": vector_address, "begin": begin, "end": end, "stages": []}
    stages = []
    for index in range(count):
        record = _u64(process, begin + 8 * index)
        function = _u64(process, record + 0x20) if record else None
        stages.append(
            {
                "index": index,
                "record": record,
                "record_raw": (_read(process, record, 0x40) or b"").hex() if record else None,
                "function": function,
                "rtti": _rtti(process, function, base) if function else None,
            }
        )
    return {
        "address": vector_address,
        "begin": begin,
        "end": end,
        "stage_count": count,
        "stages": stages,
    }


def hit(frame, bp_loc, internal_dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    target = process.GetTarget()
    base = _base(target)
    site = frame.GetPC() - base if base is not None else None
    thread_id = thread.GetThreadID()
    site_key = hex(site) if site is not None else "unknown"
    state["site_hits"][site_key] = state["site_hits"].get(site_key, 0) + 1

    if site in LINEAGE_SITES:
        name = LINEAGE_SITES[site]
        state["lineage_hits"][name] += 1
        # Keep every factory/demosaic edge. Wrapper snapshots are larger, so
        # retain only the first eight while preserving their total hit count.
        keep_sample = site != STAGE5_WRAPPER or state["lineage_hits"][name] <= 8
        if keep_sample and len(state["lineage_samples"]) < 4096:
            registers = {
                name: _u(frame, name)
                for name in ("rdi", "rsi", "rdx", "rcx", "r8", "r9")
            }
            sample = {
                "site": name,
                "site_va": site,
                "thread_id": thread_id,
                "registers": registers,
            }
            for register in ("rdi", "rsi", "rdx", "rcx"):
                descriptor = _descriptor(process, registers[register])
                if descriptor is not None:
                    sample[f"{register}_descriptor"] = descriptor
            if site == STAGE5_WRAPPER:
                sample["pipeline_cross_talk_type_0x1514"] = _u32(
                    process, registers["rdi"] + 0x1514
                )
                sample["payload_slots"] = _payload_slots(process, registers["rsi"])
            elif site == DEMOSAIC_CALL:
                # 0x342d99 calls owner+0x1560/+0x30. Its adapter remaps
                # payload+0x70 to output and this local clipped descriptor to
                # the DemosaickLightV1 input.
                payload = _u(frame, "rbx")
                local_input = _u(frame, "rbp") - 0x50
                sample["payload"] = payload
                sample["payload_d0_descriptor"] = _descriptor(process, payload + 0xD0)
                sample["payload_output_descriptor"] = _descriptor(process, payload + 0x70)
                sample["local_input_descriptor"] = _descriptor(process, local_input)
                sample["target_rtti"] = _rtti(process, registers["rdi"], base)
            state["lineage_samples"].append(sample)

        # Internal sites are diagnostic peers of the selected callback trace;
        # they must not enter the stage-order state machine below.
        return False

    if state["complete"]:
        return False

    if site == CREATE_ENTRY:
        descriptor = _descriptor(process, _u(frame, "rsi"))
        if descriptor:
            state["create_inputs"].append(descriptor)
            if state["create_input"] is None and descriptor["size"] == [4160, 3120]:
                state["create_input"] = descriptor
        return False

    if site == COLOR_CLOSURE_WORKER:
        closure = _u(frame, "rdi")
        input_pointer = _u64(process, closure + 0x20)
        input_descriptor = _descriptor(process, input_pointer) if input_pointer else None
        captured_image = _u64(process, closure + 0x28)
        camera_key = _u32(process, captured_image + 0x60) if captured_image else None
        expected = state["create_input"]
        requested_key = state["camera_key"]
        if (
            state["active_thread"] is None
            and input_descriptor is not None
            and (
                (requested_key is not None and camera_key == requested_key)
                or (
                    requested_key is None
                    and expected is not None
                    and input_descriptor["allocation"] == expected["allocation"]
                )
            )
        ):
            state["active_thread"] = thread_id
            state["closure"] = {
                "address": closure,
                "raw": (_read(process, closure, 0x30) or b"").hex(),
                "output_descriptor": _descriptor(process, _u64(process, closure + 0x08)),
                "softisp": _u64(process, closure + 0x18),
                "input_descriptor": input_descriptor,
                "captured_image": captured_image,
                "camera_key_0x60": camera_key,
            }
        return False

    if thread_id != state["active_thread"]:
        return False

    if site == STAGE_EXECUTOR_ENTRY:
        if state["selected_executor"] is not None:
            return False
        executor_id = len(state["executors"])
        payload = _u(frame, "rdi")
        executor = {
            "id": executor_id,
            "thread_id": thread_id,
            "payload": payload,
            "payload_before": (_read(process, payload, 0x140) or b"").hex(),
            "vector": _stage_vector(process, _u(frame, "rsi"), base),
            "input_descriptor": _descriptor(process, _u(frame, "rdx")),
            "mapped_rectangle_raw": (_read(process, _u(frame, "rcx"), 16) or b"").hex(),
        }
        executor["expected_stage_indices"] = [
            stage["index"] for stage in executor["vector"]["stages"] if stage["function"]
        ]
        state["executors"].append(executor)
        state["selected_executor"] = executor_id
        return False

    if site == STAGE_EXECUTOR_RETURN:
        if not state["executor_stack"]:
            state["errors"].append("executor return without active executor")
            return False
        executor_id = state["executor_stack"].pop()
        executor = state["executors"][executor_id]
        executor["payload_after"] = (_read(process, executor["payload"], 0x140) or b"").hex()
        if not state["executor_stack"]:
            state["complete"] = True
        return False

    if site == STAGE_CALL:
        executor_id = state["selected_executor"]
        if executor_id is None:
            return False
        executor = state["executors"][executor_id]
        executor_calls = [
            item for item in state["calls"] if item["executor_id"] == executor_id
        ]
        expected_indices = executor["expected_stage_indices"]
        if len(executor_calls) >= len(expected_indices):
            return False
        stage_index = _u(frame, "rbx")
        expected_index = expected_indices[len(executor_calls)]
        if stage_index != expected_index:
            state["errors"].append(
                f"stage order mismatch: expected {expected_index}, observed {stage_index}"
            )
            return False
        object_address = _u(frame, "rdi")
        tile_address = _u(frame, "rsi")
        before = _snapshot(process, object_address, tile_address, base)
        _dump_payload_slots(process, before, f"stage_{stage_index:02d}_before")
        if executor_calls:
            executor_calls[-1]["after"] = before
            executor_calls[-1]["after_source"] = "next_stage_before"
        item = {
            "stage_index": stage_index,
            "executor_id": executor_id,
            "thread_id": thread_id,
            "before": before,
        }
        state["calls"].append(item)
        if len(executor_calls) + 1 == len(expected_indices):
            state["complete"] = True
            if state["terminate_on_complete"]:
                state["terminated_after_capture"] = True
                report_path = os.path.join(state["output_dir"], "report.json")
                write_report(None, report_path)
                error = process.Kill()
                if not error.Success():
                    state["terminated_after_capture"] = False
                    state["errors"].append(f"kill failed: {error.GetCString()}")
                    write_report(None, report_path)
        return False

    if site == STAGE_RETURN:
        if not state["pending_calls"]:
            state["errors"].append("stage return without pending call")
            return False
        index = state["pending_calls"].pop()
        before = state["calls"][index]["before"]
        state["calls"][index]["after"] = _snapshot(
            process,
            before["rtti"]["object"],
            before["tile_address"],
            base,
        )
        executor_id = state["calls"][index]["executor_id"]
        executor = state["executors"][executor_id]
        expected_calls = sum(
            1 for stage in executor["vector"]["stages"] if stage["function"]
        )
        executor_calls = [
            item for item in state["calls"] if item["executor_id"] == executor_id
        ]
        if (
            expected_calls > 0
            and len(executor_calls) == expected_calls
            and all("after" in item for item in executor_calls)
        ):
            state["complete"] = True
        return False

    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    expected = {
        CREATE_ENTRY,
        COLOR_CLOSURE_WORKER,
        STAGE_EXECUTOR_ENTRY,
        STAGE_CALL,
    }
    diagnostic = set(LINEAGE_SITES)
    found = set()
    for index in range(target.GetNumBreakpoints()):
        breakpoint = target.GetBreakpointAtIndex(index)
        if not breakpoint or not breakpoint.IsValid() or breakpoint.GetNumLocations() < 1:
            continue
        site = breakpoint.GetLocationAtIndex(0).GetAddress().GetFileAddress()
        if site in expected or site in diagnostic:
            breakpoint.SetScriptCallbackFunction("stage_vector_probe.hit")
            _state()["breakpoints"][str(site)] = breakpoint.GetID()
            if site in expected:
                found.add(site)
    missing = sorted(expected - found)
    if missing:
        _state()["errors"].append("missing breakpoints: " + ",".join(hex(item) for item in missing))


def launch_and_write(debugger, arguments, path):
    lldb = builtins.__import__("lldb")
    debugger.SetAsync(False)
    target = debugger.GetSelectedTarget()
    launch_info = lldb.SBLaunchInfo(arguments)
    environment = lldb.SBEnvironment()
    framework_path = "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks"
    environment.Set("DYLD_FRAMEWORK_PATH", framework_path, True)
    environment.Set("DYLD_LIBRARY_PATH", framework_path, True)
    launch_info.SetEnvironment(environment, True)
    launch_info.SetWorkingDirectory("/Users/ryaker/Dev/L16_Lumen_ReverseEngineering")
    error = lldb.SBError()
    target.Launch(launch_info, error)
    if not error.Success():
        _state()["launch_error"] = error.GetCString()
    write_report(debugger, path)


def write_report(debugger, path):
    state = dict(_state())
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="ascii") as handle:
        json.dump(state, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print(
        "COLOR_STAGE_VECTOR_REPORT "
        + json.dumps(
            {
                "label": state["label"],
                "complete": state["complete"],
                "executors": len(state["executors"]),
                "calls": len(state["calls"]),
                "errors": state["errors"],
            },
            sort_keys=True,
        )
    )


def assert_complete():
    state = _state()
    if state["errors"]:
        raise RuntimeError("; ".join(state["errors"]))
    if not state["complete"] or len(state["calls"]) != 7:
        raise RuntimeError(
            f"capture incomplete: complete={state['complete']} calls={len(state['calls'])}"
        )
    print(
        "create_stereo_color_stage_vector=OK "
        + state["label"]
        + " stages="
        + ",".join(str(item["stage_index"]) for item in state["calls"])
    )
