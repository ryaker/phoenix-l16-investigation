import builtins
import hashlib
import json
import struct
from pathlib import Path


HELPER_ENTRY = 0x2E8680
HELPER_DONE = 0x2E87D6
WORKER_ENTRY = 0x2E8CC0
CLIPPED_VIEW_RETURN = 0x2E8D07
LEAKAGE_ENTRY = 0x10ACD0
DECISION = 0x2E9AFD
WIDTH = 4160
HEIGHT = 3120
TARGETS = {(1108, 0)}
EDGE_VIEW_TARGETS = {(1108, 0), (1021, 3119), (0, 241), (4159, 2086)}


def reset(label="", output_dir="", capture_decision=True):
    builtins.l16_monofusion_hotpixel = {
        "label": label,
        "output_dir": output_dir,
        "capture_decision": capture_decision,
        "active_thread": None,
        "helper": None,
        "worker": None,
        "worker_entries": [],
        "clipped_views": [],
        "target_decisions": [],
        "decision_breakpoint_id": None,
        "leakage_entries": [],
        "complete": False,
        "errors": [],
    }


def _state():
    if not hasattr(builtins, "l16_monofusion_hotpixel"):
        reset()
    return builtins.l16_monofusion_hotpixel


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


def _descriptor(process, address):
    raw = _read(process, address, 0x30)
    if raw is None:
        return {"address": address, "read_ok": False}
    words = struct.unpack("<8iQQ", raw)
    return {
        "address": address,
        "read_ok": True,
        "origin": list(words[0:2]),
        "bounds": list(words[2:4]),
        "size": list(words[4:6]),
        "stride": words[6],
        "reserved": words[7],
        "data": words[8],
        "allocation": words[9],
    }


def _dump_image(process, descriptor, name):
    state = _state()
    if not descriptor.get("read_ok") or descriptor.get("size") != [WIDTH, HEIGHT]:
        return None
    stride = descriptor["stride"]
    if stride < WIDTH:
        state["errors"].append(f"{name}: short stride {stride}")
        return None
    output = Path(state["output_dir"]) / name
    digest = hashlib.sha256()
    with output.open("wb") as handle:
        for y in range(HEIGHT):
            raw = _read(process, descriptor["data"] + 2 * y * stride, 2 * WIDTH)
            if raw is None:
                state["errors"].append(f"{name}: row {y} read failed")
                return None
            handle.write(raw)
            digest.update(raw)
    return {"path": str(output), "bytes": 2 * WIDTH * HEIGHT, "sha256": digest.hexdigest()}


def _dump_view(process, descriptor, name):
    if not descriptor.get("read_ok"):
        return None
    origin_x, origin_y = descriptor.get("origin", [0, 0])
    upper_x, upper_y = descriptor.get("bounds", [0, 0])
    width, height = upper_x - origin_x, upper_y - origin_y
    stride = descriptor.get("stride", 0)
    if width <= 0 or height <= 0 or stride < width or width * height > WIDTH * HEIGHT:
        return None
    output = Path(_state()["output_dir"]) / name
    digest = hashlib.sha256()
    with output.open("wb") as handle:
        for y in range(height):
            raw = _read(process, descriptor["allocation"] + 2 * y * stride, 2 * width)
            if raw is None:
                return None
            handle.write(raw)
            digest.update(raw)
    return {
        "path": str(output),
        "bytes": 2 * width * height,
        "sha256": digest.hexdigest(),
        "storage": "row-packed little-endian uint16 full descriptor bounds from allocation",
        "logical_origin": [origin_x, origin_y],
        "logical_upper_bound": [upper_x, upper_y],
        "allocation_extent": [width, height],
    }


def _base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            address = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if address != 0xFFFFFFFFFFFFFFFF:
                return address
    return None


def _rectangle_contains(rectangle, x, y):
    if rectangle is None:
        return False
    x0, y0, x1, y1 = rectangle
    return x0 <= x < x1 and y0 <= y < y1


def _set_enabled(target, breakpoint_id, enabled):
    breakpoint = target.FindBreakpointByID(breakpoint_id)
    if breakpoint and breakpoint.IsValid():
        breakpoint.SetEnabled(enabled)


def hit(frame, bp_loc, internal_dict):
    state = _state()
    thread = frame.GetThread()
    process = thread.GetProcess()
    base = _base(process.GetTarget())
    site = frame.GetPC() - base if base is not None else None

    if site == LEAKAGE_ENTRY:
        source = _descriptor(process, _u(frame, "rdx"))
        if source.get("size") == [WIDTH, HEIGHT]:
            state["leakage_entries"].append(
                {"thread_id": thread.GetThreadID(), "source": source}
            )
        return False

    if site == HELPER_ENTRY:
        phase_raw = _read(process, _u(frame, "rdx"), 8)
        phase = list(struct.unpack("<2i", phase_raw)) if phase_raw else None
        source = _descriptor(process, _u(frame, "rsi"))
        if phase != [-1, -1] or source.get("size") != [WIDTH, HEIGHT]:
            return False
        destination = _descriptor(process, _u(frame, "rdi"))
        state["active_thread"] = thread.GetThreadID()
        state["helper"] = {
            "thread_id": thread.GetThreadID(),
            "phase": phase,
            "sensor": _u(frame, "rcx"),
            "sensor_raw_0x110": (_read(process, _u(frame, "rcx"), 0x110) or b"").hex(),
            "source": source,
            "destination": destination,
            "source_dump": _dump_image(process, source, "a2_hotpixel_input.u16le"),
        }
        target = process.GetTarget()
        for name in (
            "worker_breakpoint_id",
            "clipped_view_breakpoint_id",
            "done_breakpoint_id",
            "leakage_breakpoint_id",
        ):
            _set_enabled(target, state[name], True)
        return False

    if site == WORKER_ENTRY:
        closure = _u(frame, "rdi")
        raw = _read(process, closure, 0x38)
        if raw is None:
            state["errors"].append("worker closure read failed")
            return False
        pointers = struct.unpack_from("<6Q", raw, 8)
        phase_raw = _read(process, pointers[1], 8)
        phase = list(struct.unpack("<2i", phase_raw)) if phase_raw else None
        source = _descriptor(process, pointers[0])
        if phase != [-1, -1] or source.get("size") != [WIDTH, HEIGHT]:
            return False
        if state["helper"] is None or source.get("data") != state["helper"]["source"].get("data"):
            return False
        rectangle_raw = _read(process, _u(frame, "rsi"), 16)
        rectangle = list(struct.unpack("<4i", rectangle_raw)) if rectangle_raw else None
        state["worker_entries"].append(
            {
                "thread_id": thread.GetThreadID(),
                "phase": phase,
                "source_origin": source.get("origin"),
                "source_bounds": source.get("bounds"),
                "rectangle": rectangle,
            }
        )
        if state["capture_decision"] and not state["target_decisions"] and any(
            _rectangle_contains(rectangle, x, y) for x, y in TARGETS
        ):
            breakpoint = process.GetTarget().FindBreakpointByID(state["decision_breakpoint_id"])
            breakpoint.SetThreadID(thread.GetThreadID())
            breakpoint.SetEnabled(True)
        if state["worker"] is not None:
            return False
        pointer_block = _read(process, pointers[2], 32)
        lut_pointers = list(struct.unpack("<4Q", pointer_block)) if pointer_block else []
        luts = []
        for lane, pointer in enumerate(lut_pointers):
            lut = _read(process, pointer, 4096)
            lut_path = Path(state["output_dir"]) / f"hotpixel_lut_lane{lane}.f32le"
            if lut:
                lut_path.write_bytes(lut)
            luts.append(
                {
                    "pointer": pointer,
                    "sha256": hashlib.sha256(lut).hexdigest() if lut else None,
                    "first_8": list(struct.unpack("<8f", lut[:32])) if lut else None,
                    "path": str(lut_path) if lut else None,
                    "bytes": len(lut) if lut else 0,
                }
            )
        threshold_raw = _read(process, pointers[3], 4)
        state["worker"] = {
            "thread_id": thread.GetThreadID(),
            "phase": phase,
            "source": source,
            "destination": _descriptor(process, pointers[4]),
            "luts": luts,
            "threshold_multiplier": struct.unpack("<f", threshold_raw)[0]
            if threshold_raw
            else None,
        }
        return False

    if site == CLIPPED_VIEW_RETURN:
        active = next(
            (
                item
                for item in reversed(state["worker_entries"])
                if item["thread_id"] == thread.GetThreadID()
            ),
            None,
        )
        if active is None or not any(
            _rectangle_contains(active["rectangle"], x, y)
            for x, y in EDGE_VIEW_TARGETS
        ):
            return False
        rectangle = active["rectangle"]
        if any(item["rectangle"] == rectangle for item in state["clipped_views"]):
            return False
        descriptor = _descriptor(process, _u(frame, "rbp") - 0xE0)
        name = "clipped_view_%d_%d_%d_%d.u16le" % tuple(rectangle)
        state["clipped_views"].append(
            {
                "thread_id": thread.GetThreadID(),
                "rectangle": rectangle,
                "descriptor": descriptor,
                "dump": _dump_view(process, descriptor, name),
                "stack_raw_0x1c0": (
                    _read(process, _u(frame, "rbp") - 0x1C0, 0x1C0) or b""
                ).hex(),
            }
        )
        return False

    if site == DECISION:
        rbp = _u(frame, "rbp")
        closure_pointer_raw = _read(process, rbp - 0x1F8, 8)
        if closure_pointer_raw is None:
            return False
        closure = struct.unpack("<Q", closure_pointer_raw)[0]
        closure_raw = _read(process, closure, 0x38)
        if closure_raw is None:
            return False
        pointers = struct.unpack_from("<6Q", closure_raw, 8)
        phase_raw = _read(process, pointers[1], 8)
        phase = list(struct.unpack("<2i", phase_raw)) if phase_raw else None
        destination = _descriptor(process, pointers[4])
        if phase != [-1, -1] or destination.get("size") != [WIDTH, HEIGHT]:
            return False
        local_x = _u(frame, "r12")
        row_pointer = _u(frame, "rsi")
        pixel_offset = (row_pointer + 2 * local_x - destination["data"]) // 2
        y = pixel_offset // destination["stride"]
        x = pixel_offset % destination["stride"]
        if (x, y) not in TARGETS:
            return False
        rows = {
            -4: struct.unpack("<Q", _read(process, rbp - 0x150, 8))[0],
            -2: struct.unpack("<Q", _read(process, rbp - 0x0F0, 8))[0],
            -1: struct.unpack("<Q", _read(process, rbp - 0x100, 8))[0],
            0: _u(frame, "r13"),
            1: struct.unpack("<Q", _read(process, rbp - 0x108, 8))[0],
            2: struct.unpack("<Q", _read(process, rbp - 0x0F8, 8))[0],
            4: struct.unpack("<Q", _read(process, rbp - 0x158, 8))[0],
        }
        windows = {}
        for dy, pointer in rows.items():
            raw = _read(process, pointer + 2 * (local_x - 5), 22)
            windows[str(dy)] = list(struct.unpack("<11H", raw)) if raw else None
        state["target_decisions"].append(
            {
                "xy": [x, y],
                "thread_id": thread.GetThreadID(),
                "local_x": local_x,
                "phase_selector_register": _u(frame, "rdx") & 1,
                "phase_selector_stack": struct.unpack(
                    "<i", _read(process, rbp - 0x17C, 4)
                )[0]
                & 1,
                "closure_phase": phase,
                "worker_source_data": pointers[0],
                "accept": _u(frame, "rax") & 0xFF,
                "windows": windows,
            }
        )
        process.GetTarget().FindBreakpointByID(
            state["decision_breakpoint_id"]
        ).SetEnabled(False)
        return False

    if site == HELPER_DONE and state["active_thread"] == thread.GetThreadID():
        destination = _descriptor(process, _u(frame, "r15"))
        state["helper"]["destination_after"] = destination
        state["helper"]["destination_dump"] = _dump_image(
            process, destination, "a2_hotpixel_output.u16le"
        )
        state["complete"] = state["helper"]["destination_dump"] is not None
        error = process.Kill()
        if not error.Success():
            state["errors"].append("kill after capture failed: " + str(error.GetCString()))
        return False

    return False


def attach(debugger):
    target = debugger.GetSelectedTarget()
    expected = {
        HELPER_ENTRY,
        HELPER_DONE,
        WORKER_ENTRY,
        CLIPPED_VIEW_RETURN,
        LEAKAGE_ENTRY,
    }
    if _state()["capture_decision"]:
        expected.add(DECISION)
    found = set()
    for index in range(target.GetNumBreakpoints()):
        bp = target.GetBreakpointAtIndex(index)
        if not bp or not bp.IsValid() or bp.GetNumLocations() < 1:
            continue
        site = bp.GetLocationAtIndex(0).GetAddress().GetFileAddress()
        if site in expected:
            bp.SetScriptCallbackFunction("monofusion_hotpixel_preprocess_probe.hit")
            bp.SetAutoContinue(True)
            if site == DECISION:
                _state()["decision_breakpoint_id"] = bp.GetID()
                bp.SetEnabled(False)
            elif site == WORKER_ENTRY:
                _state()["worker_breakpoint_id"] = bp.GetID()
                bp.SetEnabled(False)
            elif site == CLIPPED_VIEW_RETURN:
                _state()["clipped_view_breakpoint_id"] = bp.GetID()
                bp.SetEnabled(False)
            elif site == HELPER_DONE:
                _state()["done_breakpoint_id"] = bp.GetID()
                bp.SetEnabled(False)
            elif site == LEAKAGE_ENTRY:
                _state()["leakage_breakpoint_id"] = bp.GetID()
                bp.SetEnabled(False)
            found.add(site)
    if found != expected:
        _state()["errors"].append("missing sites: " + repr(sorted(expected - found)))
    print("L16_MONOFUSION_HOTPIXEL_ATTACHED", [hex(value) for value in sorted(found)])


def drive(debugger, limit=512):
    lldb = builtins.__import__("lldb")
    process = debugger.GetSelectedTarget().GetProcess()
    stopped = {lldb.eStateStopped, lldb.eStateCrashed, lldb.eStateSuspended}
    iterations = 0
    while not _state()["complete"] and process.GetState() in stopped:
        if iterations >= limit:
            _state()["errors"].append(f"continue limit reached: {limit}")
            break
        error = process.Continue()
        iterations += 1
        if not error.Success():
            _state()["errors"].append("continue failed: " + str(error.GetCString()))
            break
    print("L16_MONOFUSION_HOTPIXEL_DRIVE", iterations, process.GetState())


def write_report(debugger, path):
    process = debugger.GetSelectedTarget().GetProcess()
    report = dict(_state())
    report["process"] = {
        "state": process.GetState(),
        "exit_status": process.GetExitStatus(),
    }
    with open(path, "w", encoding="ascii") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
        handle.write("\n")
    print("L16_MONOFUSION_HOTPIXEL_REPORT", path)
