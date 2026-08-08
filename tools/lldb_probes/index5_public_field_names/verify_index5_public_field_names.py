#!/usr/bin/env python3
"""Verify installed StereoLayer field names against admitted index-5 custody."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86_const import (
    X86_INS_CALL,
    X86_OP_IMM,
    X86_OP_MEM,
    X86_REG_RIP,
)


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def u32(data: bytes, offset: int = 0) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def u64(data: bytes, offset: int = 0) -> int:
    return struct.unpack_from("<Q", data, offset)[0]


def segments(data: bytes):
    require(u32(data) == 0xFEEDFACF, "libcp is not the pinned Mach-O")
    result = []
    offset = 32
    for _ in range(u32(data, 16)):
        command = u32(data, offset)
        size = u32(data, offset + 4)
        if command == 0x19:
            result.append(
                (
                    u64(data, offset + 24),
                    u64(data, offset + 32),
                    u64(data, offset + 40),
                    u64(data, offset + 48),
                )
            )
        offset += size
    return result


def file_offset(mapping, va: int) -> int:
    for vmaddr, vmsize, fileoff, filesize in mapping:
        if vmaddr <= va < vmaddr + vmsize:
            delta = va - vmaddr
            require(delta < filesize, f"VA 0x{va:x} outside file bytes")
            return fileoff + delta
    raise AssertionError(f"unmapped VA 0x{va:x}")


def bytes_at(data: bytes, mapping, va: int, size: int) -> bytes:
    offset = file_offset(mapping, va)
    result = data[offset : offset + size]
    require(len(result) == size, f"short read at 0x{va:x}")
    return result


def cstring(data: bytes, mapping, va: int) -> bytes:
    offset = file_offset(mapping, va)
    end = data.index(b"\0", offset)
    return data[offset:end]


def instruction(data: bytes, mapping, va: int):
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    return next(decoder.disasm(bytes_at(data, mapping, va, 16), va))


def rip_target(item) -> int:
    require(len(item.operands) >= 2, f"0x{item.address:x}: missing source operand")
    source = item.operands[1]
    require(
        source.type == X86_OP_MEM and source.mem.base == X86_REG_RIP,
        f"0x{item.address:x}: expected RIP-relative source",
    )
    return item.address + item.size + source.mem.disp


def memory_displacement(item, operand_index: int) -> int:
    operand = item.operands[operand_index]
    require(
        operand.type == X86_OP_MEM,
        f"0x{item.address:x}: operand {operand_index} is not memory",
    )
    return operand.mem.disp


def direct_call_target(item) -> int:
    require(item.id == X86_INS_CALL, f"0x{item.address:x}: expected call")
    require(
        len(item.operands) == 1 and item.operands[0].type == X86_OP_IMM,
        f"0x{item.address:x}: expected direct call",
    )
    return item.operands[0].imm


def verify_static() -> str:
    data = LIBCP.read_bytes()
    mapping = segments(data)
    digest = hashlib.sha256(data).hexdigest()
    require(digest == LIBCP_SHA256, f"libcp digest changed: {digest}")

    labels = (
        ("Depth map", 0x632AD9, 0x26FE3F, 0x26FE54, 0x2A8),
        ("Images", 0x632AE7, 0x26FE83, 0x26FE9B, 0x240),
        ("Guidance", 0x632AF2, 0x26FED3, 0x26FEEB, 0x288),
        ("Skip mask", 0x632B00, 0x26FF23, 0x26FF3B, 0x208),
        ("Pixel buf", 0x632B0E, 0x26FF73, 0x26FF8B, 0x1E0),
        ("Range buf", 0x632B1C, 0x26FFC3, 0x26FFDB, 0x1B8),
        ("Min cost buf", 0x632B2A, 0x270013, 0x27002B, 0x188),
        ("Line buf", 0x632B38, 0x270063, 0x27007B, 0x148),
    )
    for name, string_va, xref_va, field_va, displacement in labels:
        actual = cstring(data, mapping, string_va).decode("ascii").rstrip()
        require(actual == name, f"0x{string_va:x}: {actual!r}, expected {name!r}")
        require(
            rip_target(instruction(data, mapping, xref_va)) == string_va,
            f"{name}: string xref changed",
        )
        require(
            memory_displacement(instruction(data, mapping, field_va), 1)
            == displacement,
            f"{name}: field displacement changed",
        )

    cost_string = cstring(data, mapping, 0x632B46).decode("ascii").rstrip()
    require(cost_string == "Cost volume", f"cost-volume label changed: {cost_string!r}")
    require(
        rip_target(instruction(data, mapping, 0x2700B3)) == 0x632B46,
        "Cost volume string xref changed",
    )
    cost_field = instruction(data, mapping, 0x2700CB)
    require(
        cost_field.mnemonic == "add"
        and len(cost_field.operands) == 2
        and cost_field.operands[1].type == X86_OP_IMM
        and cost_field.operands[1].imm == 0xF8,
        "Cost volume field adjustment changed",
    )

    range_map = b"Range map needs to be the same size as mask."
    require(cstring(data, mapping, 0x632E54) == range_map, "Range map label changed")
    for xref_va in (0x299F9C, 0x29A5AA):
        require(
            rip_target(instruction(data, mapping, xref_va)) == 0x632E54,
            f"Range map xref 0x{xref_va:x} changed",
        )

    for call_va, target in ((0x26BE35, 0x26D750), (0x26BE50, 0x29A140)):
        require(
            direct_call_target(instruction(data, mapping, call_va)) == target,
            f"call 0x{call_va:x} target changed",
        )
    for call_va, target in (
        (0x3FF0EA, 0x226410),
        (0x3FF14A, 0x1BE970),
        (0x3FF1B7, 0x264440),
        (0x3FF1D1, 0x23FAF0),
        (0x3FF43C, 0x2681B0),
        (0x268268, 0x26BA90),
        (0x26BB05, 0x274410),
    ):
        require(
            direct_call_target(instruction(data, mapping, call_va)) == target,
            f"geometry-record call 0x{call_va:x} target changed",
        )
    require(
        memory_displacement(instruction(data, mapping, 0x3FF152), 1) == 0x448,
        "same-key state+0x448 lookup changed",
    )
    require(
        memory_displacement(instruction(data, mapping, 0x26BAF0), 1) == 0x258,
        "geometry-record vector destination changed",
    )
    require(
        memory_displacement(instruction(data, mapping, 0x26BE07), 1) == 0x2A8,
        "range-map builder depth-map input changed",
    )
    require(
        memory_displacement(instruction(data, mapping, 0x26BE3A), 1) == 0x208,
        "cost-volume skip-mask input changed",
    )
    require(
        memory_displacement(instruction(data, mapping, 0x26BE5B), 0) == 0xF8,
        "cost-volume destination field changed",
    )

    hashes = {
        (0x26FE00, 0x270146): "272d8454018f8b664e313d3e1be51f94796001dcb647cc842045fc7c9d360e21",
        (0x26BDF0, 0x26BE9E): "0d18311c38f4b2c6dcee779814d55a3fc5020343b19428f2857e908086649c8c",
        (0x299F70, 0x299FC0): "5f2e72b303195f919241fb927c5f5bc9f1859804de6f4e582c503655a2507461",
        (0x29A570, 0x29A5D0): "122ad44a72c11f823bf4b7ddc8aecb06e59b304d6ea2be6d2cbe9e07688d52be",
        (0x3FF050, 0x3FF46E): "8612d894a6acfd01573cf917f9ae756abe1075f6f7298ba5d44bb5d232bd9807",
        (0x2681B0, 0x26826D): "a0e8ba4fff5fbc0a221b5bf559ce8ae09f70ced88fe1ea85685f54b6a0824e21",
        (0x26BA90, 0x26BB3C): "d83ce8d693cbfa4084e374d5a0f46e08f53650788519cc7b6a00c0f40f27ac50",
        (0x28F5A0, 0x28F827): "c072ca497f377dcd393fd21ca41e4e645ec3d18cb4bbb890cdae3b7a8624b372",
    }
    for (start, end), expected in hashes.items():
        actual = hashlib.sha256(bytes_at(data, mapping, start, end - start)).hexdigest()
        require(actual == expected, f"range 0x{start:x}..0x{end:x} changed")
    return digest


def one_sample(packet: dict, site: str) -> dict:
    rows = [row for row in packet["samples"] if row["site"] == site]
    require(len(rows) == 1, f"{packet['label']}: expected one {site} sample")
    return rows[0]


def verify_range_reports() -> None:
    run_dir = ROOT / "runs/codex_26d750_source_range_builder"
    names = (
        "source_range_28mm.json",
        "source_range_35mm.json",
        "source_range_70mm.json",
        "source_range_150mm.json",
        "source_range_unit2_28mm.json",
    )
    for name in names:
        packet = json.loads((run_dir / name).read_text())
        require(packet["process"]["exit_status"] == 0, f"{name}: process exit")
        require(not packet["drive_hit_step_cap"], f"{name}: step cap")
        require(not packet["errors"], f"{name}: errors")
        source = one_sample(packet, "caller_pre_26d750")["call_args"]
        require(source["rsi_is_source_plus_0x2a8"], f"{name}: depth-map input")
        require(source["rdx_is_source_plus_0x208"], f"{name}: skip-mask input")
        cost = one_sample(packet, "caller_pre_29a140")
        require(cost["rsi_is_output_descriptor"], f"{name}: range-map handoff")
        require(cost["rdx_is_target_plus_0x208"], f"{name}: skip-mask handoff")
        print(f"{name}=OK range_map_to_cost_volume")


def verify_index_reports() -> None:
    run_dir = ROOT / "runs/codex_299c70_source_index_producer"
    for focal in ("28mm", "35mm", "70mm", "150mm"):
        name = f"source_index_{focal}.json"
        packet = json.loads((run_dir / name).read_text())
        require(packet["process"]["exit_status"] == 0, f"{name}: process exit")
        require(not packet["drive_hit_step_cap"], f"{name}: step cap")
        require(not packet["errors"], f"{name}: errors")
        summary = packet["summary"]
        require(summary["chain_count"] == 6, f"{name}: chain count")
        require(summary["stereo_indices"] == list(range(6)), f"{name}: indices")
        require(
            summary["all_chains_pass_available_checks"],
            f"{name}: custody checks",
        )
        print(f"{name}=OK cost_volume_to_index_map")


def verify_worker_reports() -> None:
    run_dir = ROOT / "runs/codex_299c70_worker_formula"
    for focal in ("28mm", "35mm", "70mm", "150mm"):
        name = f"worker_formula_{focal}.json"
        packet = json.loads((run_dir / name).read_text())
        require(packet["process"]["exit_status"] == 0, f"{name}: process exit")
        require(not packet["drive_hit_step_cap"], f"{name}: step cap")
        require(not packet["errors"], f"{name}: errors")
        summary = packet["summary"]
        require(summary["dispatch_count"] == 6, f"{name}: dispatch count")
        require(
            summary["all_worker_samples_match_formula"],
            f"{name}: argmin formula",
        )
        require(
            summary["all_dispatches_have_worker_samples"],
            f"{name}: worker coverage",
        )
        print(f"{name}=OK minimum_cost_hypothesis_index")


def verify_geometry_record_reports() -> None:
    run_dir = ROOT / "runs/codex_lookup_endpoint_count_origin"
    for focal in ("28mm", "35mm", "70mm", "150mm"):
        name = f"endpoint_count_origin_{focal}.json"
        packet = json.loads((run_dir / name).read_text())
        require(packet["process"]["exit_status"] == 0, f"{name}: process exit")
        require(not packet["drive_hit_step_cap"], f"{name}: step cap")
        require(not packet["errors"], f"{name}: errors")
        key = f"0x{packet['target_object']:x}"
        fields = packet["objects"][key]["setup_after_endpoint_store"][
            "object_fields_after_setup"
        ]
        image_bytes = fields["source_vector_0x240"]["byte_size"]
        record_bytes = fields["source_record_vector_0x258"]["byte_size"]
        require(image_bytes % 0x10 == 0, f"{name}: Images stride")
        require(record_bytes % 0xA8 == 0, f"{name}: geometry-record stride")
        image_count = image_bytes // 0x10
        record_count = record_bytes // 0xA8
        require(image_count == 5, f"{name}: Images count {image_count}")
        require(record_count == image_count, f"{name}: paired record count")
        print(
            f"{name}=OK images={image_count} "
            f"composed_geometry_records={record_count}"
        )


def main() -> None:
    digest = verify_static()
    print(f"static_index5_public_field_names={digest}")
    verify_range_reports()
    verify_index_reports()
    verify_worker_reports()
    verify_geometry_record_reports()
    print("index5_public_field_names=OK")


if __name__ == "__main__":
    main()
