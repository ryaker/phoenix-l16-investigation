#!/usr/bin/env python3
"""Copy an LRI while disabling every public CameraModule except one key."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import struct
from pathlib import Path


def read_varint(data: bytes | bytearray, offset: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while offset < len(data) and shift < 70:
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7F) << shift
        if byte < 0x80:
            return value, offset
        shift += 7
    raise ValueError("invalid varint")


def fields(data: bytes | bytearray):
    offset = 0
    while offset < len(data):
        tag, after_tag = read_varint(data, offset)
        number, wire_type = tag >> 3, tag & 7
        if number == 0:
            raise ValueError("invalid field zero")
        if wire_type == 0:
            value, end = read_varint(data, after_tag)
            yield number, wire_type, value, after_tag, end
        elif wire_type == 1:
            end = after_tag + 8
            yield number, wire_type, None, after_tag, end
        elif wire_type == 2:
            length, content = read_varint(data, after_tag)
            end = content + length
            yield number, wire_type, data[content:end], content, end
        elif wire_type == 5:
            end = after_tag + 4
            yield number, wire_type, None, after_tag, end
        else:
            raise ValueError(f"unsupported wire type {wire_type}")
        if end > len(data):
            raise ValueError("truncated field")
        offset = end


def patch_payload(payload: bytearray, selected_key: int) -> list[dict]:
    patches = []
    for number, wire_type, module_raw, module_start, _module_end in fields(payload):
        if (number, wire_type) != (12, 2):
            continue
        module = bytearray(module_raw)
        module_id = None
        enabled_field = None
        for child_number, child_wire, value, value_start, value_end in fields(module):
            if (child_number, child_wire) == (2, 0):
                module_id = value
            elif (child_number, child_wire) == (3, 0):
                enabled_field = (value, value_start, value_end)
        if module_id is None or enabled_field is None:
            continue
        value, value_start, value_end = enabled_field
        if value not in (0, 1) or value_end - value_start != 1:
            raise AssertionError(f"camera {module_id}: is_enabled is not one-byte bool")
        replacement = 1 if module_id == selected_key else 0
        absolute = module_start + value_start
        payload[absolute] = replacement
        patches.append(
            {
                "camera_key": module_id,
                "old_is_enabled": value,
                "new_is_enabled": replacement,
                "payload_offset": absolute,
            }
        )
    return patches


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--camera-key", type=int, required=True)
    args = parser.parse_args()

    if args.source.resolve() == args.destination.resolve():
        raise SystemExit("source and destination must differ")
    shutil.copyfile(args.source, args.destination)
    original_size = args.destination.stat().st_size
    patches = []
    with args.destination.open("r+b") as handle:
        block_offset = 0
        block_index = 0
        while block_offset < original_size:
            handle.seek(block_offset)
            header = handle.read(32)
            if len(header) != 32 or header[:4] != b"LELR":
                raise AssertionError(f"invalid LELR block at {block_offset}")
            total_size = struct.unpack_from("<Q", header, 4)[0]
            message_offset = struct.unpack_from("<Q", header, 12)[0]
            message_size = struct.unpack_from("<I", header, 20)[0]
            handle.seek(block_offset + message_offset)
            payload = bytearray(handle.read(message_size))
            block_patches = patch_payload(payload, args.camera_key)
            if block_patches:
                handle.seek(block_offset + message_offset)
                handle.write(payload)
                for item in block_patches:
                    item["block_index"] = block_index
                    item["file_offset"] = (
                        block_offset + message_offset + item["payload_offset"]
                    )
                patches.extend(block_patches)
            if total_size <= 0:
                raise AssertionError("zero-sized LELR block")
            block_offset += total_size
            block_index += 1
        handle.flush()
        os.fsync(handle.fileno())

    keys = sorted({item["camera_key"] for item in patches})
    if args.camera_key not in keys or len(keys) < 5:
        raise AssertionError(f"incomplete CameraModule patch set: {keys}")
    if args.destination.stat().st_size != original_size:
        raise AssertionError("staged LRI size changed")
    print(
        json.dumps(
            {
                "source": str(args.source),
                "destination": str(args.destination),
                "camera_key": args.camera_key,
                "camera_keys": keys,
                "patch_count": len(patches),
                "disabled_count": sum(
                    item["new_is_enabled"] == 0 for item in patches
                ),
                "file_size": original_size,
                "patches": patches,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
