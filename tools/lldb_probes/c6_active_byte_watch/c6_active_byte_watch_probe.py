import builtins
import json
import os
import struct


F2770_RETURN = 0xE59A9


def reset(label="", hit_cap=16):
    builtins.l16_c6_active_byte_watch = {
        "label": label,
        "hit_cap": hit_cap,
        "armed": [],
        "hits": [],
        "errors": [],
        "counts": {"f2770_return": 0, "armed": 0, "watch_hits": 0},
    }


def _state():
    if not hasattr(builtins, "l16_c6_active_byte_watch"):
        reset()
    return builtins.l16_c6_active_byte_watch


def install_callbacks(debugger, ids):
    bp_id = ids.get("f2770_return")
    if not bp_id:
        return
    bp = debugger.GetSelectedTarget().FindBreakpointByID(bp_id)
    if bp and bp.IsValid():
        bp.SetScriptCallbackFunction("c6_active_byte_watch_probe.f2770_return")


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
    if data is None:
        return None
    return data[0]


def _u32(process, addr):
    data = _read(process, addr, 4)
    if data is None:
        return None
    return struct.unpack_from("<I", data, 0)[0]


def _i32(process, addr):
    data = _read(process, addr, 4)
    if data is None:
        return None
    return struct.unpack_from("<i", data, 0)[0]


def _libcp_base(target):
    for module in target.module_iter():
        if str(module.GetFileSpec().GetFilename()) == "libcp.dylib":
            base = module.GetObjectFileHeaderAddress().GetLoadAddress(target)
            if base != 0xFFFFFFFFFFFFFFFF:
                return base
    return None


def _module_va(target, pc):
    base = _libcp_base(target)
    if base is not None and pc >= base:
        return pc - base
    return None


def _stack(thread, max_frames=12):
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


def _registers(frame):
    return {
        name: _u(frame, name)
        for name in [
            "rax",
            "rbx",
            "rcx",
            "rdx",
            "rsi",
            "rdi",
            "rsp",
            "rbp",
            "r12",
            "r13",
            "r14",
            "r15",
            "rip",
        ]
    }


def f2770_return(frame, bp_loc, _dict):
    lldb = builtins.__import__("lldb")
    state = _state()
    state["counts"]["f2770_return"] += 1
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    item = _u(frame, "rbx")
    cam = _u32(process, item + 0x60)
    if cam != 15:
        return False

    active_addr = item + 0x30
    packet = {
        "site": "f2770_return_0xe59a9",
        "item_ptr": item,
        "camera_id_item_0x60": cam,
        "active_addr_item_0x30": active_addr,
        "active_byte_initial": _u8(process, active_addr),
        "pair_initial": [_i32(process, item + 0x58), _i32(process, item + 0x5C)],
        "type_item_0x100": _u32(process, item + 0x100),
        "stack": _stack(frame.GetThread(), 10),
    }

    error = lldb.SBError()
    wp = target.WatchAddress(active_addr, 1, False, True, error)
    if error.Success() and wp.IsValid():
        packet["watchpoint_id"] = wp.GetID()
        packet["watchpoint_error"] = None
        state["counts"]["armed"] += 1
        bp_loc.GetBreakpoint().SetEnabled(False)
    else:
        packet["watchpoint_id"] = None
        packet["watchpoint_error"] = error.GetCString()
        state["errors"].append(packet)
        return False

    state["armed"].append(packet)
    return False

def _record_watch_stop(debugger):
    lldb = builtins.__import__("lldb")
    state = _state()
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    if not process or not process.IsValid():
        return
    thread = process.GetSelectedThread()
    if not thread or not thread.IsValid():
        return
    if thread.GetStopReason() != lldb.eStopReasonWatchpoint:
        return
    frame = thread.GetSelectedFrame()
    if not frame or not frame.IsValid():
        return
    if state["hits"]:
        return

    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    meta = state["armed"][-1] if state["armed"] else {}
    addr = meta.get("active_addr_item_0x30")
    item = meta.get("item_ptr")
    hit = {
        "watchpoint_id": thread.GetStopReasonDataAtIndex(0) if thread.GetStopReasonDataCount() else None,
        "rip": _u(frame, "rip"),
        "libcp_va": _module_va(target, _u(frame, "rip")),
        "thread_id": frame.GetThread().GetThreadID(),
        "active_addr": addr,
        "active_byte_now": _u8(process, addr) if addr else None,
        "camera_id_now": _u32(process, item + 0x60) if item else None,
        "pair_now": [_i32(process, item + 0x58), _i32(process, item + 0x5C)] if item else None,
        "registers": _registers(frame),
        "stack": _stack(frame.GetThread(), 12),
    }
    state["hits"].append(hit)
    state["counts"]["watch_hits"] += 1


def report_to_file(path):
    lldb = builtins.__import__("lldb")
    _record_watch_stop(lldb.debugger)
    state = _state()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(state, f, indent=2, sort_keys=True)
    print("WROTE", path, "counts", state["counts"], "hits", len(state["hits"]))
