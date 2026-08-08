#!/usr/bin/env python3
import hashlib
import json
import subprocess
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86_const import X86_INS_CALL, X86_OP_IMM


ROOT = Path(__file__).resolve().parents[3]
LUMEN = Path("/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/MacOS/Lumen")
LIBCP = Path("/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib")
REPORT = ROOT / "runs" / "editor_render_type_topology" / "static_gui_callgraph.json"
VM_BASE = 0x100000000

RANGES = {
    "image_writer_ctor": (0x100061190, 0x10006126C),
    "image_viewer_ctor_prefix": (0x100067BD0, 0x100067C20),
    "image_editor_ctor": (0x1000687A0, 0x1000687E1),
    "post_depth_edit": (0x100068CA0, 0x100068D21),
    "commit_depth_edit": (0x100031F80, 0x10003204A),
    "push_render_request_level": (0x100031D00, 0x100031F69),
    "image_viewer_render": (0x100068370, 0x10006839C),
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def slice_va(blob, start, end):
    return blob[start - VM_BASE : end - VM_BASE]


def instructions(blob, start, end):
    disassembler = Cs(CS_ARCH_X86, CS_MODE_64)
    disassembler.detail = True
    return list(disassembler.disasm(slice_va(blob, start, end), start))


def instruction_at(rows, address):
    row = next((item for item in rows if item.address == address), None)
    assert row is not None, hex(address)
    return row


def assert_call(rows, address, target):
    row = instruction_at(rows, address)
    assert row.id == X86_INS_CALL, (hex(address), row.mnemonic, row.op_str)
    assert row.operands[0].type == X86_OP_IMM
    assert row.operands[0].imm == target, (hex(address), hex(row.operands[0].imm), hex(target))


def assert_text(rows, address, mnemonic, operands):
    row = instruction_at(rows, address)
    assert row.mnemonic == mnemonic, (hex(address), row.mnemonic, mnemonic)
    assert row.op_str == operands, (hex(address), row.op_str, operands)


def main():
    blob = LUMEN.read_bytes()
    libcp_blob = LIBCP.read_bytes()
    assert blob[:4] == bytes.fromhex("cffaedfe")

    decoded = {name: instructions(blob, start, end) for name, (start, end) in RANGES.items()}

    writer = decoded["image_writer_ctor"]
    assert_text(writer, 0x1000611F7, "lea", "r13, [rbx + 0xf8]")
    assert_text(writer, 0x10006122A, "mov", "esi, 3")
    assert_call(writer, 0x100061232, 0x10016E692)

    viewer = decoded["image_viewer_ctor_prefix"]
    assert_text(viewer, 0x100067BFB, "lea", "r13, [rbx + 0x40]")
    assert_call(viewer, 0x100067C02, 0x100061190)

    editor = decoded["image_editor_ctor"]
    assert_call(editor, 0x1000687A8, 0x100067BD0)
    assert_text(editor, 0x1000687C5, "lea", "rdi, [rbx + 0x200]")
    assert_text(editor, 0x1000687CC, "lea", "r15, [rbx + 0x138]")
    assert_text(editor, 0x1000687D3, "mov", "rsi, r15")
    assert_call(editor, 0x1000687D6, 0x10016E59C)

    post = decoded["post_depth_edit"]
    assert_text(post, 0x100068CAA, "lea", "rdi, [rbx + 0x138]")
    assert_call(post, 0x100068CB1, 0x10016E674)
    assert_text(post, 0x100068D00, "lea", "rsi, [rbx + 0x200]")
    assert_text(post, 0x100068D10, "mov", "byte ptr [rbx + 0x130], 1")

    commit = decoded["commit_depth_edit"]
    assert_text(commit, 0x100031FA0, "mov", "r14, qword ptr [r15 + 0xe8]")
    assert_call(commit, 0x100031FE6, 0x100068CA0)
    assert_call(commit, 0x100032026, 0x10002FC60)

    push = decoded["push_render_request_level"]
    assert_text(push, 0x100031F22, "mov", "r8d, 1")
    assert_call(push, 0x100031F31, 0x100068370)

    render = decoded["image_viewer_render"]
    assert_text(render, 0x100068374, "mov", "eax, r8d")
    assert_text(render, 0x100068381, "add", "rdi, 0x138")
    assert_text(render, 0x10006838D, "xor", "r8d, r8d")
    assert_text(render, 0x100068390, "mov", "ecx, eax")
    assert_call(render, 0x100068392, 0x10016E698)

    symbols = subprocess.run(
        ["nm", "-nm", "-arch", "x86_64", str(LUMEN)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    for symbol in (
        "__ZN5CIAPI8Renderer6CreateENS_15RendererProfileE",
        "__ZN5CIAPI8Renderer6renderEiRKNS_3ROIENS_10RenderTypeEb",
        "__ZN5CIAPI11DepthEditorC1ERNS_8RendererE",
        "__ZN11ImageEditor13postDepthEdit",
        "__ZN13ImageEditItem15commitDepthEdit",
    ):
        assert symbol in symbols, symbol

    report = {
        "lumen_path": str(LUMEN),
        "lumen_sha256": sha256(blob),
        "libcp_path": str(LIBCP),
        "libcp_sha256": sha256(libcp_blob),
        "facts": {
            "image_writer_renderer_profile": 3,
            "image_editor_renderer_offset": "0x138",
            "image_editor_depth_editor_offset": "0x200",
            "image_edit_render_type": 1,
            "image_edit_render_async_flag": 0,
            "commit_schedules_pyramid_render": True,
        },
        "body_sha256": {
            name: sha256(slice_va(blob, start, end))
            for name, (start, end) in RANGES.items()
        },
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("lumen_editor_callgraph=OK")
    print(json.dumps(report["facts"], sort_keys=True))


if __name__ == "__main__":
    main()
