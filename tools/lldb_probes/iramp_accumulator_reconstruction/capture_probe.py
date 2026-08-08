import builtins
import json
import os
import struct


SCRATCH_BYTES = 0x2800


def reset(output_dir, require_nonbaseline=False):
    builtins.l16_iramp_reconstruction = {
        "output_dir": output_dir,
        "require_nonbaseline": require_nonbaseline,
        "pending": {},
        "captured": False,
        "pairs_seen": 0,
        "errors": [],
    }


def _state():
    return builtins.l16_iramp_reconstruction


def _reg(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    lldb = builtins.__import__("lldb")
    error = lldb.SBError()
    raw = process.ReadMemory(address, size, error)
    return raw if error.Success() and len(raw) == size else None


def capture_before(frame, bp_loc, internal_dict):
    state = _state()
    if state["captured"]:
        return False
    process = frame.GetThread().GetProcess()
    thread_id = frame.GetThread().GetThreadID()
    scratch_address = _reg(frame, "rdi")
    before = _read(process, scratch_address, SCRATCH_BYTES)
    if before is None:
        state["errors"].append("failed to read pre-call scratch")
        process.Kill()
        return False
    state["pending"][thread_id] = {
        "scratch_address": scratch_address,
        "before": before,
    }
    return False


def capture_after(frame, bp_loc, internal_dict):
    state = _state()
    if state["captured"]:
        return False
    process = frame.GetThread().GetProcess()
    thread_id = frame.GetThread().GetThreadID()
    packet = state["pending"].pop(thread_id, None)
    if packet is None:
        return False
    after = _read(process, packet["scratch_address"], SCRATCH_BYTES)
    if after is None:
        state["errors"].append("failed to read post-call scratch")
        process.Kill()
        return False

    state["pairs_seen"] += 1
    normalizers = struct.unpack_from("<20f", packet["before"], 0x2580)
    if state["require_nonbaseline"] and all(
        value == 0.20000000298023224 for value in normalizers
    ):
        return False

    output_dir = state["output_dir"]
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "before.bin"), "wb") as handle:
        handle.write(packet["before"])
    with open(os.path.join(output_dir, "after.bin"), "wb") as handle:
        handle.write(after)

    changed = [
        index
        for index, (old, new) in enumerate(zip(packet["before"], after))
        if old != new
    ]
    metadata = {
        "site": "libcp+0x369f34",
        "target": "libcp+0x36e530",
        "thread_id": thread_id,
        "scratch_address": packet["scratch_address"],
        "scratch_size": SCRATCH_BYTES,
        "return_offset": _reg(frame, "rax") - packet["scratch_address"],
        "pairs_seen": state["pairs_seen"],
        "changed_byte_count": len(changed),
        "first_changed_offset": min(changed) if changed else None,
        "last_changed_offset": max(changed) if changed else None,
        "selectors_25d0": list(packet["before"][0x25D0:0x26D0]),
        "normalizers_2580": list(normalizers),
        "output_first_vec4": list(struct.unpack_from("<4f", after, 0x1580)),
    }
    with open(os.path.join(output_dir, "capture.json"), "w") as handle:
        json.dump(metadata, handle, indent=2, sort_keys=True)
        handle.write("\n")

    state["captured"] = True
    state["metadata"] = metadata
    process.Kill()
    return False


def report():
    state = _state().copy()
    state["pending"] = sorted(state["pending"])
    print("L16_IRAMP_RECONSTRUCTION", json.dumps(state, sort_keys=True))
