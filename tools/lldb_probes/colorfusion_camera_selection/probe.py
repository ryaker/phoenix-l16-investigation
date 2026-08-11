"""Capture ColorFusionBayer's finalized target/source camera-ID selection."""

import json
import os
import struct

import lldb


OUT_PATH = os.environ.get(
    "CF_SELECTION_OUT",
    "/Volumes/Dev/L16_Lumen_ReverseEngineering/runs/"
    "colorfusion_camera_selection/capture.json",
)


def _reg(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    error = lldb.SBError()
    data = process.ReadMemory(address, size, error)
    if not error.Success() or len(data) != size:
        raise RuntimeError(
            "read 0x%x+0x%x failed: %s" % (address, size, error)
        )
    return bytes(data)


def _u64(process, address):
    return struct.unpack("<Q", _read(process, address, 8))[0]


def _libcp_base(target):
    module = target.FindModule(lldb.SBFileSpec("libcp.dylib"))
    if not module.IsValid():
        raise RuntimeError("libcp.dylib module not found")
    return module.GetObjectFileHeaderAddress().GetLoadAddress(target)


def capture(frame):
    """Recover ColorFusionBayer `this` from the stable worker-stop unwind."""
    process = frame.GetThread().GetProcess()
    target = process.GetTarget()
    base = _libcp_base(target)
    stack = []
    this = 0
    relative = 0
    for index in range(frame.GetThread().GetNumFrames()):
        candidate = frame.GetThread().GetFrameAtIndex(index)
        pc = candidate.GetPCAddress().GetLoadAddress(target)
        relative = pc - base
        stack.append({"index": index, "libcp_offset": "0x%x" % relative})
        if 0x1AAB40 <= relative < 0x1AAF90:
            this = _reg(candidate, "r12")
            break
    if not this:
        raise RuntimeError("ColorFusionBayer::process caller not found in stack")
    begin = _u64(process, this + 0x148)
    end = _u64(process, this + 0x150)
    capacity = _u64(process, this + 0x158)
    if end < begin or (end - begin) % 4:
        raise RuntimeError("invalid camera vector 0x%x..0x%x" % (begin, end))
    count = (end - begin) // 4
    camera_ids = []
    if count:
        camera_ids = list(struct.unpack("<%di" % count, _read(process, begin, 4 * count)))

    raw = _read(process, this + 0x140, 0x60)
    record = {
        "breakpoint": "libcp+0x18eb00",
        "process_caller": "libcp+0x%x" % relative,
        "stack_prefix": stack,
        "object": "0x%x" % this,
        "target_camera_id": struct.unpack_from("<i", raw, 0)[0],
        "source_vector": {
            "begin": "0x%x" % begin,
            "end": "0x%x" % end,
            "capacity": "0x%x" % capacity,
            "count": count,
            "camera_ids": camera_ids,
        },
        "mode_0x198": raw[0x58],
        "initialized_0x199": raw[0x59],
        "object_0x140_0x19f_hex": raw.hex(),
    }
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as output:
        json.dump(record, output, indent=2, sort_keys=True)
    print("CF_SELECTION_SUMMARY " + OUT_PATH)
    print(
        "CF_SELECTION target=%d sources=%s initialized=%d"
        % (
            record["target_camera_id"],
            camera_ids,
            record["initialized_0x199"],
        )
    )
    return record


def on_wiener(frame, bp_loc, internal_dict):
    capture(frame)
    bp_loc.GetBreakpoint().SetEnabled(False)
    frame.GetThread().GetProcess().Kill()
    return False
