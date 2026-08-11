"""Dump ColorFusionBayer reference, ordered source, and flow descriptors.

Run at libcp+0x1abc71, immediately after initialize has built every descriptor
and immediately before it sets the initialized flag. Raw payloads stay under
ignored runs/; capture.json authenticates dimensions, sizes, and hashes.
"""

import hashlib
import json
import os
import struct

import lldb


ROOT = "/Volumes/Dev/L16_Lumen_ReverseEngineering"
OUT_DIR = os.environ.get(
    "CF_SOURCE_PLANES_OUT", ROOT + "/runs/colorfusion_source_planes/default"
)


def _reg(frame, name):
    return frame.FindRegister(name).GetValueAsUnsigned()


def _read(process, address, size):
    error = lldb.SBError()
    data = bytes(process.ReadMemory(address, size, error))
    if not error.Success() or len(data) != size:
        raise RuntimeError("read 0x%x+0x%x failed: %s" % (address, size, error))
    return data


def _u64(process, address):
    return struct.unpack("<Q", _read(process, address, 8))[0]


def _write(name, data):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, name)
    with open(path, "wb") as handle:
        handle.write(data)
    return {
        "file": name,
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def _descriptor(process, address, element_bytes, name):
    raw = _read(process, address, 0x30)
    width, height, stride = struct.unpack("<iii", raw[0x10:0x1c])
    data_address = struct.unpack("<Q", raw[0x20:0x28])[0]
    if not (0 < width <= 10000 and 0 < height <= 10000 and width <= stride <= 20000):
        raise RuntimeError("invalid %s descriptor %dx%d stride=%d" % (name, width, height, stride))
    size = stride * height * element_bytes
    if not data_address or size > 512 * 1024 * 1024:
        raise RuntimeError("invalid %s payload address/size" % name)
    payload = _read(process, data_address, size)
    return {
        "address": "0x%x" % address,
        "raw_hex": raw.hex(),
        "width": width,
        "height": height,
        "stride": stride,
        "data": "0x%x" % data_address,
        "element_bytes": element_bytes,
        "payload": _write(name + ".bin", payload),
    }


def _descriptor_vector(process, object_address, offset, element_bytes, prefix):
    vector = object_address + offset
    begin = _u64(process, vector)
    end = _u64(process, vector + 8)
    if end < begin or (end - begin) % 0x30 or end - begin > 0x30 * 16:
        raise RuntimeError("invalid %s vector 0x%x..0x%x" % (prefix, begin, end))
    count = (end - begin) // 0x30
    return {
        "vector_address": "0x%x" % vector,
        "begin": "0x%x" % begin,
        "end": "0x%x" % end,
        "count": count,
        "descriptors": [
            _descriptor(process, begin + 0x30 * index, element_bytes, "%s_%02d" % (prefix, index))
            for index in range(count)
        ],
    }


def capture(debugger, frame):
    process = frame.GetThread().GetProcess()
    owner = _reg(frame, "r14")
    source_ids_begin = _u64(process, owner + 0x148)
    source_ids_end = _u64(process, owner + 0x150)
    if source_ids_end < source_ids_begin or (source_ids_end - source_ids_begin) % 4:
        raise RuntimeError("invalid source ID vector")
    source_count = (source_ids_end - source_ids_begin) // 4
    source_ids = list(
        struct.unpack(
            "<%di" % source_count,
            _read(process, source_ids_begin, source_count * 4),
        )
    )

    report = {
        "stop_relative": "0x1abc71",
        "owner": "0x%x" % owner,
        "target_camera_id": struct.unpack("<i", _read(process, owner + 0x140, 4))[0],
        "source_camera_ids": source_ids,
        "reference": _descriptor(process, owner + 0x70, 8, "reference_vec4_f16"),
        "sources": _descriptor_vector(process, owner, 0x100, 8, "source_vec4_f16"),
        "flows": _descriptor_vector(process, owner, 0x128, 8, "flow_vec2_f32"),
    }
    if report["sources"]["count"] != source_count or report["flows"]["count"] != source_count:
        raise RuntimeError("camera/source/flow vector counts disagree")

    os.makedirs(OUT_DIR, exist_ok=True)
    report_path = os.path.join(OUT_DIR, "capture.json")
    with open(report_path, "w") as handle:
        json.dump(report, handle, indent=2, sort_keys=True)
    print("CF_SOURCE_PLANES_CAPTURE " + report_path)
