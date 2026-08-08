#!/usr/bin/env python3
"""Inspect static CNR worker constants/calls in the installed libcp.dylib."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_X86, CS_GRP_CALL, CS_GRP_JUMP, CS_MODE_64
from capstone.x86 import X86_OP_IMM, X86_OP_MEM, X86_REG_RIP


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)

RANGES = {
    "cnr_body_0x307ee0": (0x307EE0, 0x308459),
    "cnr_callback_0x308520": (0x308520, 0x308567),
    "cnr_worker_0x3085a0": (0x3085A0, 0x308F50),
    "descriptor_copy_0x308f50": (0x308F50, 0x309270),
    "matrix_helper_0x309270": (0x309270, 0x309D50),
    "rotation_helper_0x309d50": (0x309D50, 0x30A050),
}

EXPECTED_HASHES = {
    "cnr_body_0x307ee0": (
        "dfbaee4a6921cbac9c4d6da49e2306c19bb4e18710ab1f805dbddd6d64dcf254"
    ),
    "cnr_callback_0x308520": (
        "e464875586d0a4f45738567d87dec65fabf39935a8d248fc885ba9a3a54b58c6"
    ),
    "cnr_worker_0x3085a0": (
        "d09448d2d08047f49df27bb92c2a75fbed0e3b0ab190f900b42034155b48a18e"
    ),
    "descriptor_copy_0x308f50": (
        "0fdc42e8c541ec6c7777ab8abd2817ba660b63ea9529ba607ef707a87c670541"
    ),
    "matrix_helper_0x309270": (
        "8c00b98db2d08556b0e0a895ab62dee34c0742f33a76aec542f982232fe39277"
    ),
    "rotation_helper_0x309d50": (
        "639f9a91a700f7b4df6b26d373da25ebf471cfbf8bd6252ad7123b2a46b78415"
    ),
}


def u32(data: bytes, offset: int = 0) -> int:
    return struct.unpack_from("<I", data, offset)[0]


def u64(data: bytes, offset: int = 0) -> int:
    return struct.unpack_from("<Q", data, offset)[0]


def cstr(data: bytes, offset: int, limit: int = 16) -> str:
    chunk = data[offset : offset + limit]
    return "".join(chr(byte) if 32 <= byte < 127 else "." for byte in chunk)


def macho_sections(data: bytes) -> list[dict[str, int | str]]:
    if data[:4] != b"\xcf\xfa\xed\xfe":
        raise ValueError("expected little-endian Mach-O 64")
    ncmds = u32(data, 16)
    offset = 32
    out: list[dict[str, int | str]] = []
    for _ in range(ncmds):
        command = u32(data, offset)
        size = u32(data, offset + 4)
        if command == 0x19:  # LC_SEGMENT_64
            segname = data[offset + 8 : offset + 24].rstrip(b"\0").decode("ascii")
            nsects = u32(data, offset + 64)
            sect_off = offset + 72
            for index in range(nsects):
                base = sect_off + index * 80
                sectname = data[base : base + 16].rstrip(b"\0").decode("ascii")
                section_seg = data[base + 16 : base + 32].rstrip(b"\0").decode("ascii")
                out.append(
                    {
                        "segment": section_seg or segname,
                        "section": sectname,
                        "addr": u64(data, base + 32),
                        "size": u64(data, base + 40),
                        "offset": u32(data, base + 48),
                    }
                )
        offset += size
    return out


def va_to_fileoff(sections: list[dict[str, int | str]], va: int) -> int:
    for item in sections:
        start = int(item["addr"])
        end = start + int(item["size"])
        if start <= va < end:
            return int(item["offset"]) + (va - start)
    raise ValueError(f"VA 0x{va:x} not in mapped sections")


def section_for(sections: list[dict[str, int | str]], va: int) -> str | None:
    for item in sections:
        start = int(item["addr"])
        end = start + int(item["size"])
        if start <= va < end:
            return f"{item['segment']},{item['section']}"
    return None


def bytes_at(data: bytes, sections: list[dict[str, int | str]], va: int, size: int) -> bytes:
    off = va_to_fileoff(sections, va)
    result = data[off : off + size]
    if len(result) != size:
        raise ValueError(f"short read at 0x{va:x}")
    return result


def range_hash(data: bytes, sections: list[dict[str, int | str]], start: int, end: int) -> str:
    return hashlib.sha256(bytes_at(data, sections, start, end - start)).hexdigest()


def decoded_blob(raw: bytes) -> dict[str, object]:
    result: dict[str, object] = {
        "hex": raw.hex(),
        "ascii": cstr(raw, 0, len(raw)),
    }
    if len(raw) >= 4:
        result["f32"] = [
            struct.unpack_from("<f", raw, offset)[0]
            for offset in range(0, len(raw) - 3, 4)
        ]
        result["u32"] = [
            struct.unpack_from("<I", raw, offset)[0]
            for offset in range(0, len(raw) - 3, 4)
        ]
    if len(raw) >= 8:
        result["f64"] = [
            struct.unpack_from("<d", raw, offset)[0]
            for offset in range(0, len(raw) - 7, 8)
        ]
        result["u64"] = [
            struct.unpack_from("<Q", raw, offset)[0]
            for offset in range(0, len(raw) - 7, 8)
        ]
    return result


def inspect(data: bytes) -> dict[str, object]:
    sections = macho_sections(data)
    md = Cs(CS_ARCH_X86, CS_MODE_64)
    md.detail = True

    ranges: dict[str, object] = {}
    rip_reads: dict[int, dict[str, object]] = {}
    call_targets: list[dict[str, object]] = []
    branch_targets: list[dict[str, object]] = []

    for name, (start, end) in RANGES.items():
        body = bytes_at(data, sections, start, end - start)
        digest = hashlib.sha256(body).hexdigest()
        instructions = 0
        for insn in md.disasm(body, start):
            instructions += 1
            if insn.group(CS_GRP_JUMP):
                for op in insn.operands:
                    if op.type == X86_OP_IMM:
                        branch_targets.append(
                            {
                                "range": name,
                                "at": f"0x{insn.address:x}",
                                "mnemonic": insn.mnemonic,
                                "target": f"0x{op.imm:x}",
                            }
                        )
            if insn.group(CS_GRP_CALL):
                for op in insn.operands:
                    if op.type == X86_OP_IMM:
                        call_targets.append(
                            {
                                "range": name,
                                "at": f"0x{insn.address:x}",
                                "target": f"0x{op.imm:x}",
                            }
                        )
            for op in insn.operands:
                if op.type != X86_OP_MEM or op.mem.base != X86_REG_RIP:
                    continue
                target = insn.address + insn.size + op.mem.disp
                size = max(op.size, 16 if insn.mnemonic.endswith("ps") else op.size)
                size = max(4, min(32, size))
                aligned = target & ~0xF
                key = target
                raw = bytes_at(data, sections, target, size)
                aligned_raw = bytes_at(data, sections, aligned, 32)
                rip_reads[key] = {
                    "target": f"0x{target:x}",
                    "aligned_0x10": f"0x{aligned:x}",
                    "section": section_for(sections, target),
                    "size": op.size,
                    "used_by": f"0x{insn.address:x}: {insn.mnemonic} {insn.op_str}",
                    "bytes": decoded_blob(raw),
                    "aligned_32": decoded_blob(aligned_raw),
                }
        ranges[name] = {
            "start": f"0x{start:x}",
            "end": f"0x{end:x}",
            "bytes": end - start,
            "instructions": instructions,
            "sha256": digest,
            "expected_sha256": EXPECTED_HASHES.get(name),
            "hash_ok": EXPECTED_HASHES.get(name) in (None, digest),
        }

    return {
        "libcp": str(LIBCP),
        "libcp_sha256": hashlib.sha256(data).hexdigest(),
        "ranges": ranges,
        "rip_reads": [rip_reads[key] for key in sorted(rip_reads)],
        "call_targets": call_targets,
        "branch_targets": branch_targets,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "runs/denoise_route_census/cnr_static_inspect.json",
    )
    args = parser.parse_args()

    data = LIBCP.read_bytes()
    report = inspect(data)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")

    bad = [
        name
        for name, item in report["ranges"].items()
        if not item.get("hash_ok", False)
    ]
    if bad:
        raise SystemExit(f"hash mismatch: {bad}")
    print(f"cnr_static_inspect=OK {args.out}")


if __name__ == "__main__":
    main()
