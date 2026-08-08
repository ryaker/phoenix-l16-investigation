#!/usr/bin/env python3
"""Verify index-5 depth custody into the mm-labeled GDepth export path."""

from __future__ import annotations

import hashlib
import json
import math
import re
import struct
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86_const import X86_INS_CALL, X86_INS_JMP, X86_OP_IMM


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
RUN_DIR = ROOT / "runs/index5_gdepth_export_bridge"
CASES = (
    "unit1_28mm",
    "unit1_35mm",
    "unit1_70mm",
    "unit1_150mm",
    "unit2_28mm",
)
INDEX_DIMS = (
    (65, 49),
    (130, 98),
    (260, 195),
    (520, 390),
    (1040, 780),
    (2080, 1560),
)


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


def direct_target(data: bytes, mapping, va: int, instruction_id: int) -> int:
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    instruction = next(decoder.disasm(bytes_at(data, mapping, va, 16), va))
    require(
        instruction.id == instruction_id,
        f"0x{va:x} has unexpected control instruction {instruction.mnemonic}",
    )
    require(
        len(instruction.operands) == 1
        and instruction.operands[0].type == X86_OP_IMM,
        f"0x{va:x} is not a direct control transfer",
    )
    return instruction.operands[0].imm


def verify_static() -> str:
    data = LIBCP.read_bytes()
    mapping = segments(data)
    digest = hashlib.sha256(data).hexdigest()
    require(
        digest == "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9",
        f"libcp digest changed: {digest}",
    )
    calls = {
        0x26AC13: 0xF340,
        0x3B3207: 0x3D8B70,
        0x3D907F: 0x2673A0,
        0x3D90A2: 0x38C380,
        0x3D90B7: 0x2674D0,
        0x3D90C4: 0xF340,
        0x3DC2DD: 0x3F7A40,
        0x3DC2E8: 0x3D9050,
        0x41AC13: 0x3DAF50,
        0x41F1B4: 0x5562DE,
        0x41F1D7: 0x5562DE,
    }
    for call_va, expected in calls.items():
        actual = direct_target(data, mapping, call_va, X86_INS_CALL)
        require(
            actual == expected,
            f"call 0x{call_va:x} -> 0x{actual:x}, expected 0x{expected:x}",
        )
    jumps = {
        0x3D8B75: 0x3D8780,
        0x38C6EB: 0x38C720,
    }
    for jump_va, expected in jumps.items():
        actual = direct_target(data, mapping, jump_va, X86_INS_JMP)
        require(
            actual == expected,
            f"jump 0x{jump_va:x} -> 0x{actual:x}, expected 0x{expected:x}",
        )
    for slot, expected in {
        0x658DD8: 0x267890,
        0x658E58: 0x267B30,
        0x66AD60: 0x38C6E0,
    }.items():
        actual = u64(bytes_at(data, mapping, slot, 8))
        require(
            actual == expected,
            f"vtable slot 0x{slot:x} -> 0x{actual:x}, expected 0x{expected:x}",
        )
    constant = struct.unpack("<f", bytes_at(data, mapping, 0x5D7FF4, 4))[0]
    require(constant == 100000.0, f"depth cap changed: {constant}")
    hashes = {
        (0x2673A0, 0x2674D0): "9e651b88a8d1666918cf38e3ea4ab4f01078f76408450fc232efd63d494871ae",
        (0x267890, 0x267A60): "3da44915ea0722f2ddebcd3db6e5027867157493bcc1a9a23c946ef3d8d1b952",
        (0x2674D0, 0x267640): "b94e40f036489f15c54a75b770e1fb93226961e429649e2b7df0fddc34e3ccec",
        (0x267B30, 0x267D00): "d2f6f47b21fcf341edf426d28470bf10d8221b80c77466f597f60cdf7d4e463d",
        (0x38C380, 0x38C510): "e013a8ca657ceabc0a1acef0a119edae6841ee50c365eb333ff0b182fb770767",
        (0x38C720, 0x38CE90): "4a8266fc0a651d860ad97a123c985454240a20c81c5411b03dd0fbc4e2fa0432",
        (0x3D8FE0, 0x3D9050): "7d52f6114cc415624da053064bd8348f5b764c7b11374eb0b513581822f6b3c6",
        (0x3D9050, 0x3D91A0): "9584944acdb2569eeb09c0d3b8d28d58aff21262d592ec1a856d09ac5996cda7",
        (0x3DAF50, 0x3DB3E0): "92c885416882db533ea0fb3ef123c0cecbb834746533fb2973bd876cec6df285",
        (0x41ABA0, 0x41AC40): "eeb6dc24e52abf06c7ca7eee6e3f11c948175d20a59021654f222d01e01b2e98",
        (0x41EB5A, 0x41EC91): "099dc7e8dcdb5c1afbbadea1765fa493eaf3195c493bc96229634d17ee85fff7",
    }
    for (start, end), expected in hashes.items():
        actual = hashlib.sha256(
            bytes_at(data, mapping, start, end - start)
        ).hexdigest()
        require(
            actual == expected,
            f"static range 0x{start:x}..0x{end:x} changed: {actual}",
        )
    reciprocal_a = list(
        Cs(CS_ARCH_X86, CS_MODE_64).disasm(
            bytes_at(data, mapping, 0x267890, 0x1D0), 0x267890
        )
    )
    reciprocal_b = list(
        Cs(CS_ARCH_X86, CS_MODE_64).disasm(
            bytes_at(data, mapping, 0x267B30, 0x1D0), 0x267B30
        )
    )
    require(
        {"rcpps", "rcpss"} <= {item.mnemonic for item in reciprocal_a},
        "first reciprocal worker no longer has packed/scalar reciprocal",
    )
    require(
        {"rcpps", "rcpss", "minps", "minss"}
        <= {item.mnemonic for item in reciprocal_b},
        "second reciprocal/cap worker changed",
    )
    for marker in (
        b'GDepth:Format="RangeInverse"',
        b'GDepth:Units="mm"',
        b'GDepth:Near="',
        b'GDepth:Far="',
    ):
        require(marker in data, f"missing GDepth marker {marker!r}")
    return digest


def one(packet: dict, site: str) -> dict:
    rows = [item for item in packet["samples"] if item["site"] == site]
    require(len(rows) == 1, f"{site}: expected one sample, got {len(rows)}")
    return rows[0]


def verify_case(case: str) -> dict:
    packet = json.loads((RUN_DIR / f"{case}.json").read_text())
    require(packet["process_exit_status"] == 0, f"{case}: process exit")
    require(not packet["drive_hit_step_cap"], f"{case}: step cap")
    require(not packet["errors"], f"{case}: errors {packet['errors']}")
    index_rows = [
        item for item in packet["samples"] if item["site"] == "index5_descriptor_ready"
    ]
    require(len(index_rows) == 6, f"{case}: index descriptor count")
    index_by_number = {item["object_index"]: item["descriptor"] for item in index_rows}
    require(set(index_by_number) == set(range(6)), f"{case}: index object numbers")
    for number, dims in enumerate(INDEX_DIMS):
        desc = index_by_number[number]
        require((desc["width"], desc["height"]) == dims, f"{case}: index dims")
        require(desc["stride"] == dims[0], f"{case}: index stride")
    selected = [
        item
        for item in packet["samples"]
        if item["site"] == "depth_cache_selected_input"
    ]
    require(len(selected) == 7, f"{case}: selected depth-cache inputs")
    for number in range(6):
        desc = selected[number]["selected_descriptor"]
        source = index_by_number[number]
        require(
            selected[number]["selected_input"] == source["address"],
            f"{case}: index-{number} descriptor identity",
        )
        require(
            desc["data_ptr"] == source["data_ptr"],
            f"{case}: index-{number} data identity",
        )
    upsample = one(packet, "upsample_depth_descriptor_ready")["descriptor"]
    selected_full = selected[6]["selected_descriptor"]
    require(
        (upsample["width"], upsample["height"], upsample["stride"])
        == (4160, 3120, 4160),
        f"{case}: upsample dimensions",
    )
    require(
        upsample["address"] == selected[6]["selected_input"]
        and upsample["data_ptr"] == selected_full["data_ptr"],
        f"{case}: UpsampleLayer descriptor identity",
    )
    watches = packet["cache_watch_samples"]
    promote = next(
        (item for item in watches if item["libcp_va"] == 0x3D902B), None
    )
    swap_old = next(
        (item for item in watches if item["libcp_va"] == 0x3D902F), None
    )
    require(promote is not None and swap_old is not None, f"{case}: cache swap")
    require(
        promote["cache_descriptor_0x18"]["data_ptr"]
        == promote["cache_descriptor_0x48"]["data_ptr"],
        f"{case}: working descriptor not promoted at swap",
    )
    provider = one(packet, "depth_provider_pre")
    require(provider["provider_target_va"] == 0x41ABA0, f"{case}: provider target")
    require(
        provider["source_descriptor_pointer"] == promote["cache_descriptor_0x18"]["address"]
        - 0x18,
        f"{case}: provider cache identity",
    )
    require(
        provider["source_image"]["data_ptr"]
        == promote["cache_descriptor_0x18"]["data_ptr"],
        f"{case}: provider promoted-data identity",
    )
    provider_out = one(packet, "depth_provider_post")["provider_descriptor"]
    require(
        provider_out["width"] > 0
        and provider_out["height"] > 0
        and provider_out["stride"] == provider_out["width"]
        and provider_out["width"] * 3 == provider_out["height"] * 4,
        f"{case}: provider output geometry",
    )
    gdepth_ready = one(packet, "gdepth_descriptor_ready")["gdepth_descriptor"]
    require(
        (gdepth_ready["width"], gdepth_ready["height"], gdepth_ready["stride"])
        == (10432, 7824, 10432),
        f"{case}: final GDepth descriptor dimensions",
    )
    extrema = one(packet, "gdepth_extrema_ready")
    near = extrema["near"]
    far = extrema["far"]
    require(
        math.isfinite(near) and math.isfinite(far) and 0 < near <= far,
        f"{case}: invalid extrema",
    )
    require(
        one(packet, "gdepth_near_stream")["streamed_near"] == near,
        f"{case}: streamed near",
    )
    require(
        one(packet, "gdepth_far_stream")["streamed_far"] == far,
        f"{case}: streamed far",
    )
    output = (RUN_DIR / f"{case}.dng").read_bytes()
    require(output.startswith(b"\xff\xd8\xff"), f"{case}: expected format-4 JPEG")
    text = output.decode("latin1", errors="ignore")
    require('GDepth:Format="RangeInverse"' in text, f"{case}: RangeInverse XMP")
    require('GDepth:Units="mm"' in text, f"{case}: mm XMP")
    near_match = re.search(r'GDepth:Near="([^"]+)"', text)
    far_match = re.search(r'GDepth:Far="([^"]+)"', text)
    require(near_match is not None and far_match is not None, f"{case}: XMP extrema")
    require(
        math.isclose(float(near_match.group(1)), near, abs_tol=0.051),
        f"{case}: XMP near value",
    )
    require(
        math.isclose(float(far_match.group(1)), far, abs_tol=0.051),
        f"{case}: XMP far value",
    )
    return {"near": near, "far": far}


def main() -> int:
    digest = verify_static()
    print(f"static_index5_gdepth_export_bridge={digest}")
    for case in CASES:
        summary = verify_case(case)
        print(
            f"{case}=OK GDepth:Near={summary['near']} "
            f"GDepth:Far={summary['far']} GDepth:Units=mm"
        )
    print("index5_gdepth_export_bridge=OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
