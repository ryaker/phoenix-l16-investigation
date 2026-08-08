#!/usr/bin/env python3
"""Verify accepted-bank assembly output reaches 0x23faf0 across four zooms."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import struct
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
RUN_DIR = ROOT / "runs" / "prefusion_264270_output_watch"
TIERS = ("28mm", "35mm", "70mm", "150mm")

LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
ASSEMBLY_BEGIN = 0x264270
ASSEMBLY_END = 0x2643C7
ASSEMBLY_SHA256 = "acde803cf7789e4ccf0c61450feb6e83d827f7c95d2a4312724b0f35e22b2cda"
COMPOSER_BEGIN = 0x23FAF0
COMPOSER_END = 0x23FBD0
COMPOSER_SHA256 = "d07dbe6d5b04ffae62e114283c13a04e0c2b14d85741c0ab7932c105aeba6472"
COMPOSER_RETURN_BEGIN = 0x2404B5
COMPOSER_RETURN_END = 0x2404CA
COMPOSER_RETURN_SHA256 = "a8a20e67d96580280c22e561dc258f94c748d870032125bc8e62b5546c43f7d8"
WIDE_CONSUMER_BEGIN = 0x23A179
WIDE_CONSUMER_END = 0x23A220
WIDE_CONSUMER_SHA256 = "a78734cbbabf871e40b1e936125aeb4cb74a4546c116105121ea441ce734b3c4"
TELE_CONSUMER_BEGIN = 0x20DBE0
TELE_CONSUMER_END = 0x20DC80
TELE_CONSUMER_SHA256 = "d68d9fb771afc90b17938576ac1774fc2b45c06dd308bb27341584d71d9c8e28"
WIDE_FORMULA_BEGIN = 0x23A200
WIDE_FORMULA_END = 0x23A388
WIDE_FORMULA_SHA256 = "3087c7f73073d1215cf08eadbbfb833b51b7f1dfe64d882ed84501b6e83fd355"
WIDE_CALL_RETURN_BEGIN = 0x239C34
WIDE_CALL_RETURN_END = 0x239C44
WIDE_CALL_RETURN_SHA256 = "b3cf90d5151ea0669037e3c609e8e648d10c04b1af591736180226a1237bbf85"
WIDE_STORE_BEGIN = 0x239D2D
WIDE_STORE_END = 0x239D47
WIDE_STORE_SHA256 = "a0f27e3e6b9fbe4069f2569b358f18eb9ca06e6a7153cc6a7d131d020b4efdf7"
TELE_FORMULA_BEGIN = 0x20DBE0
TELE_FORMULA_END = 0x20DC92
TELE_FORMULA_SHA256 = "810a7349b4891bb9ede9ba0cd1e8bc32e57b0eadff3f1dc288775f682cc13907"
TELE_STORE_BEGIN = 0x20B234
TELE_STORE_END = 0x20B273
TELE_STORE_SHA256 = "f6376af0870446c7cf20cb74cd5c4b69f671531cb0833828f570bab321a76d9f"
WIDE_COUNT_BIAS_ADDRESS = 0x5D2C98
WIDE_SCORE_ACCESSOR_BEGIN = 0x23A530
WIDE_SCORE_ACCESSOR_END = 0x23A5BD
WIDE_SCORE_ACCESSOR_SHA256 = "e073ce3833a2d3d75de1e3e6b930406034c7b6d786a9f3ce927a6773c9241396"
TELE_TREE_CLEANUP_BEGIN = 0x230920
TELE_TREE_CLEANUP_END = 0x230970
TELE_TREE_CLEANUP_SHA256 = "a2f1b6f6758af3b5589700771b2f29f68bf8df3198cd0c05ee1f13ce049ef57f"
WIDE_DECISION_BEGIN = 0x22D8ED
WIDE_DECISION_END = 0x22D908
WIDE_DECISION_SHA256 = "f0cce948c7dad3ae0ac8b30306fe98c104134854ffd632153ee19d5794b9f027"
WIDE_LOCAL_REUSE_BEGIN = 0x22DE81
WIDE_LOCAL_REUSE_END = 0x22DEBD
WIDE_LOCAL_REUSE_SHA256 = "2fdfaa641ff7d96c1488c3451b2897ef535ea3f022c40364a0f65b7d6cfb35f3"
WIDE_EXISTING_ENTRY_BEGIN = 0x22DCC3
WIDE_EXISTING_ENTRY_END = 0x22DCE6
WIDE_EXISTING_ENTRY_SHA256 = "ca5a6e8c78767badfc4840e21404f5539f1898747d7311ee4acfd269a169e8f8"
WIDE_CALIB_TRANSFER_BEGIN = 0x22DF1F
WIDE_CALIB_TRANSFER_END = 0x22DF4A
WIDE_CALIB_TRANSFER_SHA256 = "b783fb62719b519efc618e2d34fe520b57458eb5381b066bb7ef8317dc3d1cf8"
WIDE_CANDIDATE_MATERIALIZE_BEGIN = 0x22D9A0
WIDE_CANDIDATE_MATERIALIZE_END = 0x22DCAB
WIDE_CANDIDATE_MATERIALIZE_SHA256 = "e44ff56e342b10fd7788ec9507df8ae42a197258960c2d88c1df27313619cfa5"
F33D0_BEGIN = 0x0F33D0
F33D0_END = 0x0F349D
F33D0_SHA256 = "ce947e1ecadeca1e37461eee9394c61e948ae7a86a84b71c6e39e557ae1656a8"
TERMINAL_FIRST_HELPER_BEGIN = 0x22E20E
TERMINAL_FIRST_HELPER_END = 0x22E249
TERMINAL_FIRST_HELPER_SHA256 = "1178507220f11f9bdfbcea5b663abec0ce5077a1681e2fb79745644b4c99aba7"
TERMINAL_RECORD_CHAIN_BEGIN = 0x23CB9C
TERMINAL_RECORD_CHAIN_END = 0x23CBC1
TERMINAL_RECORD_CHAIN_SHA256 = "b0d7bc07d6abe62c70c2004b51faaddd5d46fa62003bead9e100759db72980b3"
SELECTOR_ONE_WRAPPER_BEGIN = 0x264440
SELECTOR_ONE_WRAPPER_END = 0x26444F
SELECTOR_ONE_WRAPPER_SHA256 = "1659eacdd472b9ce2c4bbb38d5bcd3090012898f8a7f5b288847bb5e6b6f43a5"
TERMINAL_NODE_FIELDS_BEGIN = 0x23CE20
TERMINAL_NODE_FIELDS_END = 0x23CE68
TERMINAL_NODE_FIELDS_SHA256 = "bb6caf4daeda93105f4c596a09930e4c54f40f248566e4f2fdd028b540db1cf1"
TERMINAL_TREE_COPY_CALLS_BEGIN = 0x23D128
TERMINAL_TREE_COPY_CALLS_END = 0x23D15D
TERMINAL_TREE_COPY_CALLS_SHA256 = "7698830b20a521539025b4964d0ce26bd57211827299c41101e45c51fb467f0b"
NODE_TREE_COPY_BEGIN = 0x1FE8A0
NODE_TREE_COPY_END = 0x1FE96F
NODE_TREE_COPY_SHA256 = "cade479bc0117877cddf8371090f2fc4b0c319b9e393ea181204e1fcfe4be4a4"
NODE_INSERT_COPY_BEGIN = 0x2008D0
NODE_INSERT_COPY_END = 0x2009D3
NODE_INSERT_COPY_SHA256 = "6dce5ffe6d6928cdd5b4d6aeb2876f5ab79949cb446c4841a4ac3335fe0f14f5"
TRANSFORM_FIELD_CALL_BEGIN = 0x1FF60C
TRANSFORM_FIELD_CALL_END = 0x1FF619
TRANSFORM_FIELD_CALL_SHA256 = "725d89e5afce1086b3d6ba7c6552b00e2793f27ee3f116e2c1a341e984ebe996"
FIELD_CONVERT_BEGIN = 0x200FB0
FIELD_CONVERT_END = 0x200FFA
FIELD_CONVERT_SHA256 = "d6dc2e2521985f8c8dedc66f0329052891fc018dfbfbdf79473b0c57768323bf"
BA_MIN_CAMERA_CHECK_BEGIN = 0x1FE965
BA_MIN_CAMERA_CHECK_END = 0x1FEA20
BA_MIN_CAMERA_CHECK_SHA256 = "2970e368b95710fcfc997af014b78a6f34d7511e49b84fb4ad09a04c12c205a3"
CAMERA_MAP_NORMALIZE_BEGIN = 0x1FF460
CAMERA_MAP_NORMALIZE_END = 0x200220
CAMERA_MAP_NORMALIZE_SHA256 = "2447eb1998a2fbef33466cc53897dddbec3cae9f9c01347936a91a27c3ae5497"
CAMERA_MAP_SUMMARY_BEGIN = 0x200690
CAMERA_MAP_SUMMARY_END = 0x200850
CAMERA_MAP_SUMMARY_SHA256 = "36359b851faf751649382d584c74bc1f744b66f38d0cc0cc0280a31bdc45e5ed"
TERMINAL_NORMALIZED_PIPELINE_BEGIN = 0x23D26A
TERMINAL_NORMALIZED_PIPELINE_END = 0x23D393
TERMINAL_NORMALIZED_PIPELINE_SHA256 = "363af6d8950101f08da861c438b9a8ef08f1c5ff0653584b61fb1687def19681"
NORMALIZED_CONVERT_BEGIN = 0x23C0F0
NORMALIZED_CONVERT_END = 0x23C5AD
NORMALIZED_CONVERT_SHA256 = "81fc95be366dbe405fecfdb5d0dbc94d88bceb87940c240a7a9d6c3f3f79b248"
NORMALIZED_COMPOSE_PREFIX_BEGIN = 0x2406A0
NORMALIZED_COMPOSE_PREFIX_END = 0x240700
NORMALIZED_COMPOSE_PREFIX_SHA256 = "e7b2892511455950aebed9a967db0149ed19a21aa388f586312ddf1c19256d66"

ASSEMBLY_ANCHORS = {
    0x264282: ("mov", "r15, rsi"),
    0x264285: ("mov", "rbx, rdi"),
    0x26428E: ("call", "0xf34e0"),
    0x264299: ("movups", "xmm0, xmmword ptr [rax]"),
    0x2642A4: ("movups", "xmmword ptr [rbx], xmm0"),
    0x2642AD: ("call", "0xf34e0"),
    0x2642CA: ("call", "0xf34e0"),
    0x264306: ("call", "0xf3360"),
    0x26433E: ("call", "0xf3350"),
    0x2643C6: ("ret", ""),
}
COMPOSER_ANCHORS = {
    0x23FB04: ("mov", "rbx, rdx"),
    0x23FB0E: ("mov", "r12, rdi"),
    0x23FB23: ("movups", "xmm0, xmmword ptr [rbx]"),
    0x23FB26: ("movups", "xmm1, xmmword ptr [rbx + 0x10]"),
    0x23FB2A: ("movups", "xmmword ptr [r12 + 0x10], xmm1"),
    0x23FB30: ("movups", "xmmword ptr [r12], xmm0"),
    0x23FB35: ("mov", "eax, dword ptr [rbx + 0x24]"),
    0x23FB50: ("mov", "dword ptr [r12 + 0x50], eax"),
    0x23FB55: ("movups", "xmm0, xmmword ptr [rbx + 0x30]"),
    0x23FB63: ("movups", "xmmword ptr [r12 + 0x30], xmm0"),
}
COMPOSER_RETURN_ANCHORS = {
    0x2404B5: ("mov", "rax, r12"),
    0x2404B8: ("add", "rsp, 0x4f8"),
    0x2404C9: ("ret", ""),
}
WIDE_CONSUMER_ANCHORS = {
    0x23A179: ("movss", "xmm0, dword ptr [rbp - 0x110]"),
    0x23A181: ("movss", "dword ptr [rbp - 0x200], xmm0"),
    0x23A189: ("movss", "xmm0, dword ptr [rbp - 0x10c]"),
    0x23A199: ("movss", "xmm0, dword ptr [rbp - 0x108]"),
    0x23A200: ("movss", "xmm15, dword ptr [rcx + rdi*8]"),
    0x23A206: ("ucomiss", "xmm14, xmm15"),
}
TELE_CONSUMER_ANCHORS = {
    0x20DBE4: ("movups", "xmm2, xmmword ptr [rdx]"),
    0x20DBEF: ("movss", "xmm3, dword ptr [rsi]"),
    0x20DBF3: ("shufps", "xmm3, xmm3, 0"),
    0x20DBF7: ("mulps", "xmm3, xmm2"),
    0x20DBFA: ("movups", "xmmword ptr [rdi], xmm3"),
    0x20DC09: ("addps", "xmm4, xmm3"),
}
WIDE_FORMULA_ANCHORS = {
    0x23A200: ("movss", "xmm15, dword ptr [rcx + rdi*8]"),
    0x23A206: ("ucomiss", "xmm14, xmm15"),
    0x23A220: ("movss", "xmm1, dword ptr [rax]"),
    0x23A2C6: ("movss", "xmm4, dword ptr [rbp - 0x200]"),
    0x23A330: ("divss", "xmm2, xmm1"),
    0x23A33C: ("subss", "xmm5, xmm15"),
    0x23A341: ("subss", "xmm2, xmm0"),
    0x23A351: ("sqrtss", "xmm0, xmm2"),
    0x23A355: ("addss", "xmm8, xmm0"),
    0x23A35A: ("inc", "esi"),
    0x23A36F: ("cvtss2sd", "xmm1, xmm8"),
    0x23A377: ("cvtsi2sd", "xmm0, esi"),
    0x23A383: ("divsd", "xmm1, xmm0"),
}
WIDE_CALL_RETURN_ANCHORS = {
    0x239C3A: ("call", "0x239e00"),
    0x239C3F: ("movss", "dword ptr [rbp - 0x5c], xmm0"),
}
WIDE_STORE_ANCHORS = {
    0x239D38: ("call", "0x23a5d0"),
    0x239D3D: ("movss", "xmm0, dword ptr [rbp - 0x5c]"),
    0x239D42: ("movss", "dword ptr [rax], xmm0"),
}
TELE_FORMULA_ANCHORS = {
    0x20DBE4: ("movups", "xmm2, xmmword ptr [rdx]"),
    0x20DBEF: ("movss", "xmm3, dword ptr [rsi]"),
    0x20DC1E: ("movups", "xmmword ptr [rdi], xmm3"),
    0x20DC53: ("movups", "xmmword ptr [rdi + 0x10], xmm3"),
    0x20DC89: ("movups", "xmmword ptr [rdi + 0x20], xmm1"),
    0x20DC8D: ("mov", "rax, rdi"),
    0x20DC91: ("ret", ""),
}
TELE_STORE_ANCHORS = {
    0x20B234: ("lea", "rdi, [rbp - 0x1e0]"),
    0x20B23B: ("lea", "rsi, [rbp - 0xd8]"),
    0x20B242: ("lea", "rdx, [rbp - 0x1b0]"),
    0x20B249: ("call", "0x20dbe0"),
    0x20B24E: ("movups", "xmm0, xmmword ptr [rbp - 0x1e0]"),
    0x20B263: ("movups", "xmmword ptr [r14 + 0x40], xmm2"),
    0x20B268: ("movups", "xmmword ptr [r14 + 0x30], xmm1"),
    0x20B26D: ("movups", "xmmword ptr [r14 + 0x20], xmm0"),
}
WIDE_SCORE_ACCESSOR_ANCHORS = {
    0x23A536: ("mov", "rcx, qword ptr [rdi + 0x48]"),
    0x23A560: ("cmp", "dword ptr [rbx + 0x20], esi"),
    0x23A594: ("lea", "rdi, [rbx + 0x28]"),
    0x23A59B: ("call", "0x23a7b0"),
    0x23A5B1: ("movss", "xmm0, dword ptr [rax + 0x38]"),
    0x23A5BC: ("ret", ""),
}
TELE_TREE_CLEANUP_ANCHORS = {
    0x23092D: ("test", "rbx, rbx"),
    0x230938: ("call", "0x230920"),
    0x230944: ("call", "0x230920"),
    0x230949: ("mov", "rdi, rbx"),
    0x230950: ("jmp", "0x55638c"),
}
WIDE_DECISION_ANCHORS = {
    0x22D8ED: ("movss", "xmm0, dword ptr [rbp - 0x2a0]"),
    0x22D8F5: ("ucomiss", "xmm0, dword ptr [r12 + 0x28]"),
    0x22D8FB: ("jbe", "0x22d9a0"),
    0x22D901: ("mov", "rax, qword ptr [rbp - 0x2a8]"),
}
WIDE_LOCAL_REUSE_ANCHORS = {
    0x22DE81: ("mov", "qword ptr [rbp - 0x2a0], rdx"),
    0x22DE98: ("mov", "qword ptr [rbp - 0x2a0], rdx"),
    0x22DEAB: ("mov", "qword ptr [rbp - 0x2a0], rdx"),
}
WIDE_EXISTING_ENTRY_ANCHORS = {
    0x22DCC3: ("mov", "qword ptr [rbp - 0x2b8], rsi"),
    0x22DCCA: ("mov", "qword ptr [rbp - 0xe8], rbx"),
    0x22DCD1: ("test", "rbx, rbx"),
    0x22DCDB: ("je", "0x22dcf0"),
    0x22DCDD: ("mov", "qword ptr [rbp - 0x2c0], rbx"),
    0x22DCE4: ("jmp", "0x22dd4f"),
}
WIDE_CALIB_TRANSFER_ANCHORS = {
    0x22DF1F: ("mov", "rsi, qword ptr [rbp - 0x2c0]"),
    0x22DF26: ("add", "rsi, 0x30"),
    0x22DF2A: ("add", "r15, 0x60"),
    0x22DF2E: ("add", "rbx, 0x54"),
    0x22DF32: ("mov", "r8d, 1"),
    0x22DF38: ("mov", "rdi, qword ptr [rbp - 0x2b8]"),
    0x22DF3F: ("mov", "rdx, r15"),
    0x22DF42: ("mov", "rcx, rbx"),
    0x22DF45: ("call", "0xf33d0"),
}
WIDE_CANDIDATE_MATERIALIZE_ANCHORS = {
    0x22D9A0: ("mov", "rax, qword ptr [rbp - 0x288]"),
    0x22DAAF: ("lea", "rdi, [rbp - 0x280]"),
    0x22DAB6: ("call", "0xe6ba0"),
    0x22DAC9: ("call", "0x264440"),
    0x22DB6E: ("movss", "xmm1, dword ptr [rbp - 0x2a0]"),
    0x22DB76: ("movss", "dword ptr [r15 + 0x28], xmm1"),
    0x22DB90: ("movups", "xmmword ptr [r15 + 0x30], xmm1"),
    0x22DBB7: ("movups", "xmmword ptr [r15 + 0x60], xmm1"),
    0x22DC49: ("movups", "xmmword ptr [r15 + 0xb0], xmm0"),
}
F33D0_ANCHORS = {
    0x0F33D9: ("cmp", "r8d, 1"),
    0x0F33DD: ("je", "0xf3440"),
    0x0F3440: ("mov", "eax, dword ptr [rsi + 0x20]"),
    0x0F3443: ("mov", "dword ptr [rdi + 0x14c], eax"),
    0x0F3457: ("movups", "xmmword ptr [rdi + 0x12c], xmm0"),
    0x0F345E: ("mov", "eax, dword ptr [rdx + 0x20]"),
    0x0F3461: ("mov", "dword ptr [rdi + 0x170], eax"),
    0x0F3475: ("movups", "xmmword ptr [rdi + 0x150], xmm0"),
    0x0F347C: ("mov", "eax, dword ptr [rcx]"),
    0x0F347E: ("mov", "dword ptr [rdi + 0x174], eax"),
    0x0F3490: ("mov", "dword ptr [rdi + 0x17c], eax"),
}
TERMINAL_FIRST_HELPER_ANCHORS = {
    0x22E20E: ("mov", "rdi, qword ptr [r15 + 0x40]"),
    0x22E212: ("mov", "rsi, qword ptr [r15 + 0x50]"),
    0x22E216: ("mov", "rcx, qword ptr [r15 + 0xa0]"),
    0x22E235: ("mov", "r8d, 1"),
    0x22E23B: ("mov", "r9d, 0xb"),
    0x22E244: ("call", "0x23c5f0"),
}
TERMINAL_RECORD_CHAIN_ANCHORS = {
    0x23CB9C: ("mov", "rsi, qword ptr [rbp - 0x430]"),
    0x23CBA3: ("mov", "rdi, r15"),
    0x23CBA6: ("call", "0x264440"),
    0x23CBAB: ("add", "rbx, 0x20"),
    0x23CBAF: ("lea", "rdi, [rbp - 0x378]"),
    0x23CBB6: ("mov", "rsi, rbx"),
    0x23CBB9: ("mov", "rdx, r15"),
    0x23CBBC: ("call", "0x23faf0"),
}
SELECTOR_ONE_WRAPPER_ANCHORS = {
    0x264440: ("push", "rbp"),
    0x264441: ("mov", "rbp, rsp"),
    0x264444: ("mov", "edx, 1"),
    0x264449: ("pop", "rbp"),
    0x26444A: ("jmp", "0x264270"),
}
TERMINAL_NODE_FIELDS_ANCHORS = {
    0x23CE20: ("cvtps2pd", "xmm5, xmm5"),
    0x23CE23: ("cvtps2pd", "xmm7, qword ptr [rbp - 0x354]"),
    0x23CE2E: ("movups", "xmmword ptr [rbx + 0x28], xmm1"),
    0x23CE32: ("movups", "xmmword ptr [rbx + 0x38], xmm2"),
    0x23CE36: ("movups", "xmmword ptr [rbx + 0x48], xmm3"),
    0x23CE3A: ("movupd", "xmmword ptr [rbx + 0x58], xmm4"),
    0x23CE5E: ("mov", "dword ptr [rbx + 0xa0], 0"),
}
TERMINAL_TREE_COPY_CALLS_ANCHORS = {
    0x23D132: ("lea", "rdi, [rbp - 0x4c0]"),
    0x23D139: ("lea", "rsi, [rbp - 0x150]"),
    0x23D147: ("mov", "ecx, 1"),
    0x23D14C: ("call", "0x1fea20"),
    0x23D151: ("lea", "rdi, [rbp - 0x4c0]"),
    0x23D158: ("call", "0x1ff460"),
}
NODE_TREE_COPY_ANCHORS = {
    0x1FE8F0: ("lea", "rdx, [rbx + 0x20]"),
    0x1FE8FA: ("call", "0x2008d0"),
}
NODE_INSERT_COPY_ANCHORS = {
    0x2008E8: ("mov", "edi, 0xa8"),
    0x2008ED: ("call", "0x556398"),
    0x2008FA: ("mov", "rax, qword ptr [rbx]"),
    0x20090B: ("movups", "xmm0, xmmword ptr [rbx + 8]"),
    0x20092D: ("movups", "xmmword ptr [r12 + 0x28], xmm0"),
    0x2009C3: ("mov", "rax, r15"),
}
TRANSFORM_FIELD_CALL_ANCHORS = {
    0x1FF60C: ("lea", "rsi, [rbx + 0x28]"),
    0x1FF610: ("mov", "rdi, r15"),
    0x1FF613: ("call", "0x200fb0"),
}
FIELD_CONVERT_ANCHORS = {
    0x200FB4: ("mov", "rax, qword ptr [rsi]"),
    0x200FB7: ("mov", "qword ptr [rdi], rax"),
    0x200FBA: ("movsd", "xmm0, qword ptr [rsi + 0x20]"),
    0x200FC4: ("divsd", "xmm0, xmm1"),
    0x200FC8: ("movsd", "qword ptr [rdi + 8], xmm0"),
    0x200FF9: ("ret", ""),
}
BA_MIN_CAMERA_CHECK_ANCHORS = {
    0x1FE965: ("cmp", "qword ptr [r13 + 0x10], 2"),
    0x1FE96A: ("ja", "0x1fe9fd"),
    0x1FE97F: ("lea", "rsi, [rip + 0x433aca]"),
    0x1FE98A: ("mov", "edx, 0x27"),
}
CAMERA_MAP_NORMALIZE_ANCHORS = {
    0x1FF613: ("call", "0x200fb0"),
    0x1FF84D: ("call", "0x1fea40"),
    0x1FF869: ("call", "0x1fec40"),
    0x1FFD70: ("movsd", "xmm0, qword ptr [rcx - 0x10]"),
    0x1FFDAF: ("call", "0x200690"),
}
CAMERA_MAP_SUMMARY_ANCHORS = {
    0x2006A7: ("cmp", "qword ptr [r13 + 0x10], 0"),
    0x20073A: ("call", "0x201000"),
    0x200816: ("lea", "rsi, [rip + 0x431c5b]"),
    0x200821: ("mov", "edx, 0x11"),
}
TERMINAL_NORMALIZED_PIPELINE_ANCHORS = {
    0x23D27E: ("movups", "xmm0, xmmword ptr [rax + 0x28]"),
    0x23D2AA: ("movups", "xmm0, xmmword ptr [rax + 0x70]"),
    0x23D2EE: ("call", "0x23c0f0"),
    0x23D34D: ("call", "0x2406a0"),
    0x23D372: ("mov", "r8d, 1"),
    0x23D38D: ("call", "0xf33d0"),
}
NORMALIZED_CONVERT_ANCHORS = {
    0x23C104: ("mov", "r15, rdx"),
    0x23C107: ("mov", "r14, rsi"),
    0x23C10A: ("mov", "rbx, rdi"),
    0x23C49D: ("movss", "dword ptr [rbx], xmm0"),
    0x23C560: ("movss", "dword ptr [rbx + 0x50], xmm0"),
    0x23C598: ("mov", "rax, rbx"),
}
NORMALIZED_COMPOSE_PREFIX_ANCHORS = {
    0x2406B4: ("mov", "rbx, rdx"),
    0x2406B7: ("mov", "r15, rsi"),
    0x2406BA: ("mov", "r13, rdi"),
    0x2406C4: ("movups", "xmm0, xmmword ptr [rbx]"),
    0x2406D0: ("movups", "xmmword ptr [r13], xmm0"),
    0x2406F9: ("movups", "xmmword ptr [r13 + 0x40], xmm1"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_lane_b_audit():
    path = ROOT / "tools" / "lane_b_index5_public_meaning_audit.py"
    spec = importlib.util.spec_from_file_location("lane_b_audit", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LANE_B_AUDIT = load_lane_b_audit()


def snapshot_words(snapshot: dict) -> tuple[int, ...]:
    raw = bytes.fromhex(snapshot["hex"])
    require(len(raw) % 4 == 0, "snapshot is not fixed32-aligned")
    return struct.unpack("<" + "I" * (len(raw) // 4), raw)


def decode(blob: bytes, begin: int, end: int) -> dict[int, tuple[str, str]]:
    disassembler = Cs(CS_ARCH_X86, CS_MODE_64)
    return {
        instruction.address: (instruction.mnemonic, instruction.op_str)
        for instruction in disassembler.disasm(blob[begin:end], begin)
    }


def verify_static() -> None:
    blob = LIBCP.read_bytes()
    require(hashlib.sha256(blob).hexdigest() == LIBCP_SHA256, "libcp SHA drift")
    require(
        blob[WIDE_COUNT_BIAS_ADDRESS : WIDE_COUNT_BIAS_ADDRESS + 8] == b"\0" * 8,
        "wide score count-bias constant drift",
    )
    require(
        hashlib.sha256(blob[ASSEMBLY_BEGIN:ASSEMBLY_END]).hexdigest()
        == ASSEMBLY_SHA256,
        "0x264270 SHA drift",
    )
    require(
        hashlib.sha256(blob[COMPOSER_BEGIN:COMPOSER_END]).hexdigest()
        == COMPOSER_SHA256,
        "0x23faf0 SHA drift",
    )
    require(
        hashlib.sha256(blob[COMPOSER_RETURN_BEGIN:COMPOSER_RETURN_END]).hexdigest()
        == COMPOSER_RETURN_SHA256,
        "0x23faf0 return SHA drift",
    )
    require(
        hashlib.sha256(blob[WIDE_CONSUMER_BEGIN:WIDE_CONSUMER_END]).hexdigest()
        == WIDE_CONSUMER_SHA256,
        "wide consumer SHA drift",
    )
    require(
        hashlib.sha256(blob[TELE_CONSUMER_BEGIN:TELE_CONSUMER_END]).hexdigest()
        == TELE_CONSUMER_SHA256,
        "tele consumer SHA drift",
    )
    for begin, end, expected, label in (
        (WIDE_FORMULA_BEGIN, WIDE_FORMULA_END, WIDE_FORMULA_SHA256, "wide formula"),
        (
            WIDE_CALL_RETURN_BEGIN,
            WIDE_CALL_RETURN_END,
            WIDE_CALL_RETURN_SHA256,
            "wide call return",
        ),
        (WIDE_STORE_BEGIN, WIDE_STORE_END, WIDE_STORE_SHA256, "wide store"),
        (TELE_FORMULA_BEGIN, TELE_FORMULA_END, TELE_FORMULA_SHA256, "tele formula"),
        (TELE_STORE_BEGIN, TELE_STORE_END, TELE_STORE_SHA256, "tele store"),
        (
            WIDE_SCORE_ACCESSOR_BEGIN,
            WIDE_SCORE_ACCESSOR_END,
            WIDE_SCORE_ACCESSOR_SHA256,
            "wide score accessor",
        ),
        (
            TELE_TREE_CLEANUP_BEGIN,
            TELE_TREE_CLEANUP_END,
            TELE_TREE_CLEANUP_SHA256,
            "tele tree cleanup",
        ),
        (
            WIDE_DECISION_BEGIN,
            WIDE_DECISION_END,
            WIDE_DECISION_SHA256,
            "wide decision",
        ),
        (
            WIDE_LOCAL_REUSE_BEGIN,
            WIDE_LOCAL_REUSE_END,
            WIDE_LOCAL_REUSE_SHA256,
            "wide local reuse",
        ),
        (
            WIDE_EXISTING_ENTRY_BEGIN,
            WIDE_EXISTING_ENTRY_END,
            WIDE_EXISTING_ENTRY_SHA256,
            "wide existing entry",
        ),
        (
            WIDE_CALIB_TRANSFER_BEGIN,
            WIDE_CALIB_TRANSFER_END,
            WIDE_CALIB_TRANSFER_SHA256,
            "wide calibration transfer",
        ),
        (
            WIDE_CANDIDATE_MATERIALIZE_BEGIN,
            WIDE_CANDIDATE_MATERIALIZE_END,
            WIDE_CANDIDATE_MATERIALIZE_SHA256,
            "wide candidate materialization",
        ),
        (F33D0_BEGIN, F33D0_END, F33D0_SHA256, "f33d0 selector copy"),
        (
            TERMINAL_FIRST_HELPER_BEGIN,
            TERMINAL_FIRST_HELPER_END,
            TERMINAL_FIRST_HELPER_SHA256,
            "terminal first helper",
        ),
        (
            TERMINAL_RECORD_CHAIN_BEGIN,
            TERMINAL_RECORD_CHAIN_END,
            TERMINAL_RECORD_CHAIN_SHA256,
            "terminal record chain",
        ),
        (
            SELECTOR_ONE_WRAPPER_BEGIN,
            SELECTOR_ONE_WRAPPER_END,
            SELECTOR_ONE_WRAPPER_SHA256,
            "selector-one wrapper",
        ),
        (
            TERMINAL_NODE_FIELDS_BEGIN,
            TERMINAL_NODE_FIELDS_END,
            TERMINAL_NODE_FIELDS_SHA256,
            "terminal node fields",
        ),
        (
            TERMINAL_TREE_COPY_CALLS_BEGIN,
            TERMINAL_TREE_COPY_CALLS_END,
            TERMINAL_TREE_COPY_CALLS_SHA256,
            "terminal tree-copy calls",
        ),
        (
            NODE_TREE_COPY_BEGIN,
            NODE_TREE_COPY_END,
            NODE_TREE_COPY_SHA256,
            "node tree copy",
        ),
        (
            NODE_INSERT_COPY_BEGIN,
            NODE_INSERT_COPY_END,
            NODE_INSERT_COPY_SHA256,
            "node insert copy",
        ),
        (
            TRANSFORM_FIELD_CALL_BEGIN,
            TRANSFORM_FIELD_CALL_END,
            TRANSFORM_FIELD_CALL_SHA256,
            "transform field call",
        ),
        (
            FIELD_CONVERT_BEGIN,
            FIELD_CONVERT_END,
            FIELD_CONVERT_SHA256,
            "field conversion",
        ),
        (
            BA_MIN_CAMERA_CHECK_BEGIN,
            BA_MIN_CAMERA_CHECK_END,
            BA_MIN_CAMERA_CHECK_SHA256,
            "BA minimum-camera check",
        ),
        (
            CAMERA_MAP_NORMALIZE_BEGIN,
            CAMERA_MAP_NORMALIZE_END,
            CAMERA_MAP_NORMALIZE_SHA256,
            "camera-map normalization",
        ),
        (
            CAMERA_MAP_SUMMARY_BEGIN,
            CAMERA_MAP_SUMMARY_END,
            CAMERA_MAP_SUMMARY_SHA256,
            "camera-map summary",
        ),
        (
            TERMINAL_NORMALIZED_PIPELINE_BEGIN,
            TERMINAL_NORMALIZED_PIPELINE_END,
            TERMINAL_NORMALIZED_PIPELINE_SHA256,
            "terminal normalized pipeline",
        ),
        (
            NORMALIZED_CONVERT_BEGIN,
            NORMALIZED_CONVERT_END,
            NORMALIZED_CONVERT_SHA256,
            "normalized record conversion",
        ),
        (
            NORMALIZED_COMPOSE_PREFIX_BEGIN,
            NORMALIZED_COMPOSE_PREFIX_END,
            NORMALIZED_COMPOSE_PREFIX_SHA256,
            "normalized compose prefix",
        ),
    ):
        require(
            hashlib.sha256(blob[begin:end]).hexdigest() == expected,
            f"{label} SHA drift",
        )
    assembly = decode(blob, ASSEMBLY_BEGIN, ASSEMBLY_END)
    composer = decode(blob, COMPOSER_BEGIN, COMPOSER_END)
    composer_return = decode(blob, COMPOSER_RETURN_BEGIN, COMPOSER_RETURN_END)
    wide_consumer = decode(blob, WIDE_CONSUMER_BEGIN, WIDE_CONSUMER_END)
    tele_consumer = decode(blob, TELE_CONSUMER_BEGIN, TELE_CONSUMER_END)
    post_windows = (
        (
            decode(blob, WIDE_FORMULA_BEGIN, WIDE_FORMULA_END),
            WIDE_FORMULA_ANCHORS,
            "wide formula",
        ),
        (
            decode(blob, WIDE_CALL_RETURN_BEGIN, WIDE_CALL_RETURN_END),
            WIDE_CALL_RETURN_ANCHORS,
            "wide call return",
        ),
        (
            decode(blob, WIDE_STORE_BEGIN, WIDE_STORE_END),
            WIDE_STORE_ANCHORS,
            "wide store",
        ),
        (
            decode(blob, TELE_FORMULA_BEGIN, TELE_FORMULA_END),
            TELE_FORMULA_ANCHORS,
            "tele formula",
        ),
        (
            decode(blob, TELE_STORE_BEGIN, TELE_STORE_END),
            TELE_STORE_ANCHORS,
            "tele store",
        ),
        (
            decode(blob, WIDE_SCORE_ACCESSOR_BEGIN, WIDE_SCORE_ACCESSOR_END),
            WIDE_SCORE_ACCESSOR_ANCHORS,
            "wide score accessor",
        ),
        (
            decode(blob, TELE_TREE_CLEANUP_BEGIN, TELE_TREE_CLEANUP_END),
            TELE_TREE_CLEANUP_ANCHORS,
            "tele tree cleanup",
        ),
        (
            decode(blob, WIDE_DECISION_BEGIN, WIDE_DECISION_END),
            WIDE_DECISION_ANCHORS,
            "wide decision",
        ),
        (
            decode(blob, WIDE_LOCAL_REUSE_BEGIN, WIDE_LOCAL_REUSE_END),
            WIDE_LOCAL_REUSE_ANCHORS,
            "wide local reuse",
        ),
        (
            decode(blob, WIDE_EXISTING_ENTRY_BEGIN, WIDE_EXISTING_ENTRY_END),
            WIDE_EXISTING_ENTRY_ANCHORS,
            "wide existing entry",
        ),
        (
            decode(blob, WIDE_CALIB_TRANSFER_BEGIN, WIDE_CALIB_TRANSFER_END),
            WIDE_CALIB_TRANSFER_ANCHORS,
            "wide calibration transfer",
        ),
        (
            decode(
                blob,
                WIDE_CANDIDATE_MATERIALIZE_BEGIN,
                WIDE_CANDIDATE_MATERIALIZE_END,
            ),
            WIDE_CANDIDATE_MATERIALIZE_ANCHORS,
            "wide candidate materialization",
        ),
        (
            decode(blob, F33D0_BEGIN, F33D0_END),
            F33D0_ANCHORS,
            "f33d0 selector copy",
        ),
        (
            decode(blob, TERMINAL_FIRST_HELPER_BEGIN, TERMINAL_FIRST_HELPER_END),
            TERMINAL_FIRST_HELPER_ANCHORS,
            "terminal first helper",
        ),
        (
            decode(blob, TERMINAL_RECORD_CHAIN_BEGIN, TERMINAL_RECORD_CHAIN_END),
            TERMINAL_RECORD_CHAIN_ANCHORS,
            "terminal record chain",
        ),
        (
            decode(blob, SELECTOR_ONE_WRAPPER_BEGIN, SELECTOR_ONE_WRAPPER_END),
            SELECTOR_ONE_WRAPPER_ANCHORS,
            "selector-one wrapper",
        ),
        (
            decode(blob, TERMINAL_NODE_FIELDS_BEGIN, TERMINAL_NODE_FIELDS_END),
            TERMINAL_NODE_FIELDS_ANCHORS,
            "terminal node fields",
        ),
        (
            decode(
                blob,
                TERMINAL_TREE_COPY_CALLS_BEGIN,
                TERMINAL_TREE_COPY_CALLS_END,
            ),
            TERMINAL_TREE_COPY_CALLS_ANCHORS,
            "terminal tree-copy calls",
        ),
        (
            decode(blob, NODE_TREE_COPY_BEGIN, NODE_TREE_COPY_END),
            NODE_TREE_COPY_ANCHORS,
            "node tree copy",
        ),
        (
            decode(blob, NODE_INSERT_COPY_BEGIN, NODE_INSERT_COPY_END),
            NODE_INSERT_COPY_ANCHORS,
            "node insert copy",
        ),
        (
            decode(blob, TRANSFORM_FIELD_CALL_BEGIN, TRANSFORM_FIELD_CALL_END),
            TRANSFORM_FIELD_CALL_ANCHORS,
            "transform field call",
        ),
        (
            decode(blob, FIELD_CONVERT_BEGIN, FIELD_CONVERT_END),
            FIELD_CONVERT_ANCHORS,
            "field conversion",
        ),
        (
            decode(blob, BA_MIN_CAMERA_CHECK_BEGIN, BA_MIN_CAMERA_CHECK_END),
            BA_MIN_CAMERA_CHECK_ANCHORS,
            "BA minimum-camera check",
        ),
        (
            decode(blob, CAMERA_MAP_NORMALIZE_BEGIN, CAMERA_MAP_NORMALIZE_END),
            CAMERA_MAP_NORMALIZE_ANCHORS,
            "camera-map normalization",
        ),
        (
            decode(blob, CAMERA_MAP_SUMMARY_BEGIN, CAMERA_MAP_SUMMARY_END),
            CAMERA_MAP_SUMMARY_ANCHORS,
            "camera-map summary",
        ),
        (
            decode(
                blob,
                TERMINAL_NORMALIZED_PIPELINE_BEGIN,
                TERMINAL_NORMALIZED_PIPELINE_END,
            ),
            TERMINAL_NORMALIZED_PIPELINE_ANCHORS,
            "terminal normalized pipeline",
        ),
        (
            decode(blob, NORMALIZED_CONVERT_BEGIN, NORMALIZED_CONVERT_END),
            NORMALIZED_CONVERT_ANCHORS,
            "normalized record conversion",
        ),
        (
            decode(
                blob,
                NORMALIZED_COMPOSE_PREFIX_BEGIN,
                NORMALIZED_COMPOSE_PREFIX_END,
            ),
            NORMALIZED_COMPOSE_PREFIX_ANCHORS,
            "normalized compose prefix",
        ),
    )
    require(
        blob[0x632450 : 0x632450 + 40]
        == b"Very few cameras for BA reconstruction.\0",
        "BA reconstruction string drift",
    )
    require(
        blob[0x632478 : 0x632478 + 18] == b"Empty camera map.\0",
        "camera-map string drift",
    )
    for address, expected in ASSEMBLY_ANCHORS.items():
        require(assembly.get(address) == expected, f"assembly drift at 0x{address:x}")
    for address, expected in COMPOSER_ANCHORS.items():
        require(composer.get(address) == expected, f"composer drift at 0x{address:x}")
    for address, expected in COMPOSER_RETURN_ANCHORS.items():
        require(
            composer_return.get(address) == expected,
            f"composer return drift at 0x{address:x}",
        )
    for address, expected in WIDE_CONSUMER_ANCHORS.items():
        require(
            wide_consumer.get(address) == expected,
            f"wide consumer drift at 0x{address:x}",
        )
    for address, expected in TELE_CONSUMER_ANCHORS.items():
        require(
            tele_consumer.get(address) == expected,
            f"tele consumer drift at 0x{address:x}",
        )
    for window, anchors, label in post_windows:
        for address, expected in anchors.items():
            require(window.get(address) == expected, f"{label} drift at 0x{address:x}")


def expected_output_prefix(source_bank_hex: str) -> str:
    bank = bytes.fromhex(source_bank_hex)
    return (bank[0x00:0x24] + bank[0x48:0x54] + bank[0x24:0x48]).hex()


def verify_runtime() -> dict:
    summaries = {}
    for tier in TIERS:
        report_path = RUN_DIR / f"output_watch_{tier}.json"
        output_path = RUN_DIR / f"output_watch_{tier}.hdr"
        report = json.loads(report_path.read_text())
        counts = report["counts"]
        require(report["process_exit_status"] == 0, f"{tier}: process exit")
        require(report["drive_hit_step_cap"] is False, f"{tier}: step cap")
        require(report["errors"] == [], f"{tier}: errors")
        require(report["pending_f33d0"] == [], f"{tier}: pending f33d0")
        require(report["active_assembly"] == [], f"{tier}: active assembly")
        require(output_path.stat().st_size > 0, f"{tier}: empty HDR")
        require(counts["assembly_matches"] == 1, f"{tier}: assembly match count")
        require(counts["assembly_return_matches"] == 1, f"{tier}: assembly return")
        require(counts["watchpoints_armed"] == 1, f"{tier}: watch arm")
        require(counts["watchpoint_hits"] == 1, f"{tier}: watch hit")
        require(counts["composer_returns"] == 1, f"{tier}: composer return")
        require(
            counts["composer_watchpoints_armed"] == 1,
            f"{tier}: composer watch arm",
        )
        require(
            counts["composer_watchpoint_hits"] == 1,
            f"{tier}: composer watch hit",
        )
        require(counts["post_transform_captures"] == 1, f"{tier}: post transform")
        require(counts["storage_watchpoints_armed"] == 1, f"{tier}: storage watch arm")
        require(counts["storage_watchpoint_hits"] == 1, f"{tier}: storage watch hit")

        entry = report["assembly_entries"][0]
        returned = report["assembly_returns"][0]
        sample = report["watch_samples"][0]
        composer_return = report["composer_return"]
        composer_sample = report["composer_watch_samples"][0]
        post = report["post_transform"]
        storage_sample = report["storage_watch_samples"][0]
        require(entry["selector"] == 1, f"{tier}: selector")
        require(entry["source_exact_copy_match"] is True, f"{tier}: source copy")
        require(returned["return_libcp_va"] == 0x2643C6, f"{tier}: return VA")
        require(
            returned["output_snapshot"]["hex"][: 0x54 * 2]
            == expected_output_prefix(entry["source_bank"]["hex"]),
            f"{tier}: output assembly prefix mismatch",
        )
        require(sample["libcp_va"] == 0x23FB26, f"{tier}: first consumer VA")
        require(sample["changed"] is False, f"{tier}: first consumer changed output")
        require(
            sample["registers"]["rbx"] == entry["output_record"],
            f"{tier}: 0x23faf0 rbx/output mismatch",
        )
        require(
            composer_return["return_libcp_va"] == 0x2404B8,
            f"{tier}: composer pre-return VA",
        )
        require(
            composer_return["returned_rax"] == composer_return["destination"],
            f"{tier}: composer returned destination mismatch",
        )
        require(composer_sample["changed"] is False, f"{tier}: composer output changed")
        stack_vas = {frame.get("libcp_va") for frame in sample["stack"]}
        if tier in {"28mm", "35mm"}:
            require(
                {0x23A055, 0x239C3F, 0x22D7AE}.issubset(stack_vas),
                f"{tier}: missing wide 0x239e00/0x239ac0/State ancestry",
            )
            route = "0x239e00->0x239ac0->State0x22d250"
            require(
                composer_sample["libcp_va"] == 0x23A181,
                f"{tier}: wide composer consumer VA",
            )
            require(post["kind"] == "wide", f"{tier}: wide post kind")
            wide_return = post["wide_return"]
            wide_store = post["wide_store"]
            score_bits = wide_return["score_xmm0"]["hex"][:8]
            score = struct.unpack("<f", bytes.fromhex(score_bits))[0]
            require(wide_return["libcp_va"] == 0x239C3F, f"{tier}: wide return VA")
            require(wide_store["libcp_va"] == 0x239D46, f"{tier}: wide store VA")
            require(
                wide_store["caller_score_local"]["hex"] == score_bits,
                f"{tier}: wide score local mismatch",
            )
            require(
                wide_store["stored_score"]["hex"] == score_bits,
                f"{tier}: wide stored score mismatch",
            )
            require(math.isfinite(score) and score >= 0.0, f"{tier}: wide score value")
            require(storage_sample["kind"] == "wide_score", f"{tier}: storage kind")
            require(
                storage_sample["libcp_va"] == 0x23A5B6,
                f"{tier}: wide score accessor VA",
            )
            require(storage_sample["changed"] is False, f"{tier}: wide score changed")
            require(
                storage_sample["value_now"]["hex"] == score_bits,
                f"{tier}: wide score accessor bits",
            )
            storage_stack = {row.get("libcp_va") for row in storage_sample["stack"]}
            require(0x22D7E6 in storage_stack, f"{tier}: wide State accessor ancestry")
            decision = post["wide_decision_compare"]
            decision_route = post["wide_decision_route"]["route"]
            require(decision["libcp_va"] == 0x22D8FB, f"{tier}: decision VA")
            require(decision["score"]["hex"] == score_bits, f"{tier}: decision score")
            expected_route = (
                "materialize_candidate"
                if decision["jbe_predicted"]
                else "retain_existing_and_transfer"
            )
            require(decision_route == expected_route, f"{tier}: decision route")
            existing_score = struct.unpack(
                "<f", bytes.fromhex(decision["existing_score"]["hex"])
            )[0]
            if decision_route == "materialize_candidate":
                require(
                    report["counts"].get("decision_local_watchpoints_armed", 0) == 0,
                    f"{tier}: materialize route local watch",
                )
                require(
                    report["counts"]["wide_decision_captures"] >= 1,
                    f"{tier}: candidate store count",
                )
                store = post["wide_decision_store"]
                require(
                    store["libcp_va"] == 0x22DB7C,
                    f"{tier}: candidate score store VA",
                )
                require(
                    store["stored_score"]["hex"] == score_bits,
                    f"{tier}: candidate stored score",
                )
                require(
                    store["local_score"]["hex"] == score_bits,
                    f"{tier}: candidate local score",
                )
                require(
                    store["destination_node"] == decision["existing_node"],
                    f"{tier}: candidate destination/compared node identity",
                )
                require(
                    store["candidate_source_object"] == entry["source_object"],
                    f"{tier}: candidate source/assembly object identity",
                )
            else:
                require(
                    report["counts"]["decision_local_watchpoints_armed"] == 1,
                    f"{tier}: retain local watch arm",
                )
                require(
                    report["counts"]["decision_local_watchpoint_hits"] == 1,
                    f"{tier}: retain local watch hit",
                )
                local_sample = report["decision_local_watch_samples"][0]
                require(local_sample["libcp_va"] == 0x22DEB2, f"{tier}: local reuse VA")
                require(local_sample["changed"] is True, f"{tier}: local reuse change")
                require(
                    local_sample["value_before"]["hex"] == score_bits,
                    f"{tier}: local reuse original bits",
                )
                require(
                    post["wide_update_path"]
                    == {"libcp_va": 0x22DCC3, "path": "existing_entry"},
                    f"{tier}: retain subpath",
                )
                transfer = report["wide_calib_transfer"]
                require(transfer is not None, f"{tier}: calibration transfer missing")
                require(
                    report["counts"]["wide_calib_transfer_calls"] == 1,
                    f"{tier}: calibration transfer call count",
                )
                require(
                    report["counts"]["wide_calib_transfer_returns"] == 1,
                    f"{tier}: calibration transfer return count",
                )
                require(
                    transfer["call_libcp_va"] == 0x22DF45,
                    f"{tier}: calibration transfer call VA",
                )
                require(
                    transfer["return_libcp_va"] == 0x22DF4A,
                    f"{tier}: calibration transfer return VA",
                )
                require(transfer["selector"] == 1, f"{tier}: transfer selector")
                node = transfer["node"]
                require(
                    transfer["source_addresses"]
                    == [node + 0x30, node + 0x60, node + 0x54],
                    f"{tier}: transfer source/node identity",
                )
                require(
                    transfer["node"]
                    == decision["existing_node"],
                    f"{tier}: transfer/compared node identity",
                )
                require(
                    transfer["destination_object"] == entry["source_object"],
                    f"{tier}: transfer/assembly object identity",
                )
                expected_bank = (
                    transfer["source_0"]["hex"]
                    + transfer["source_1"]["hex"]
                    + transfer["source_2"]["hex"]
                )
                require(
                    transfer["bank_after"]["hex"] == expected_bank,
                    f"{tier}: transfer bank exact copy",
                )
                require(
                    transfer["bank_before"]["hex"] != transfer["bank_after"]["hex"],
                    f"{tier}: transfer bank did not change",
                )
                public_sequences = (
                    LANE_B_AUDIT.public_calibration_fixed32_sequence_index(tier)
                )
                public_compact = LANE_B_AUDIT.public_intrinsics_compact_records(tier)
                transfer_words = [
                    snapshot_words(transfer[name])
                    for name in ("source_0", "source_1", "source_2")
                ]
                require(
                    all(words not in public_sequences for words in transfer_words),
                    f"{tier}: transfer source unexpectedly exact public sequence",
                )
                compact_fields = (
                    "k_matrix_raw",
                    "rotation_raw",
                    "translation_raw",
                )
                require(
                    all(
                        words != tuple(record[field])
                        for words in transfer_words
                        for record in public_compact.values()
                        for field in compact_fields
                    ),
                    f"{tier}: transfer source unexpectedly exact compact component",
                )
                if tier == "35mm":
                    require(
                        report["counts"]["calib_transfer_watchpoints_armed"] == 1,
                        f"{tier}: transfer consumer watch arm",
                    )
                    require(
                        report["counts"]["calib_transfer_watchpoint_hits"] == 1,
                        f"{tier}: transfer consumer watch hit",
                    )
                    consumer = report["calib_transfer_watch_samples"][0]
                    require(
                        consumer["libcp_va"] == 0x26429C,
                        f"{tier}: transfer first consumer VA",
                    )
                    require(
                        consumer["changed"] is False,
                        f"{tier}: transfer changed before first consumer",
                    )
                    require(
                        consumer["value_now"]["hex"]
                        == transfer["bank_after"]["hex"][:16],
                        f"{tier}: transfer first-consumer bits",
                    )
                    require(
                        consumer["registers"]["r15"]
                        == transfer["destination_object"],
                        f"{tier}: transfer first-consumer object identity",
                    )
                    consumer_stack = {
                        row.get("libcp_va") for row in consumer["stack"]
                    }
                    require(
                        {0x23CBAB, 0x22E249, 0x22F3FF}.issubset(consumer_stack),
                        f"{tier}: terminal transfer consumer ancestry",
                    )
                    require(
                        report["counts"]["terminal_composer_handoffs"] == 1,
                        f"{tier}: terminal composer handoff count",
                    )
                    handoff = report["terminal_selected_record_handoff"]
                    require(
                        handoff["call_libcp_va"] == 0x23CBBC,
                        f"{tier}: terminal composer call VA",
                    )
                    require(
                        handoff["source_object"]
                        == transfer["destination_object"],
                        f"{tier}: terminal handoff source object",
                    )
                    require(
                        handoff["right_record"] == handoff["assembly_output"],
                        f"{tier}: terminal assembly/right pointer identity",
                    )
                    require(
                        handoff["right_snapshot"]["hex"][: 0x54 * 2]
                        == expected_output_prefix(transfer["bank_after"]["hex"]),
                        f"{tier}: terminal right-record assembly bytes",
                    )
                    require(
                        report["counts"]["terminal_composer_returns"] == 1,
                        f"{tier}: terminal composer return count",
                    )
                    require(
                        handoff["return_libcp_va"] == 0x23CBC1,
                        f"{tier}: terminal composer return VA",
                    )
                    require(
                        handoff["destination_before"]["hex"]
                        != handoff["destination_after"]["hex"],
                        f"{tier}: terminal composition output unchanged",
                    )
                    require(
                        report["counts"]["terminal_node_materializations"] == 1,
                        f"{tier}: terminal node materialization count",
                    )
                    require(
                        handoff["node_fields_libcp_va"] == 0x23CE5E,
                        f"{tier}: terminal node fields VA",
                    )
                    require(
                        handoff["destination_at_node"]["hex"]
                        == handoff["destination_after"]["hex"],
                        f"{tier}: terminal composition output drift",
                    )
                    require(
                        handoff["node_key"]["hex"] == handoff["local_key"]["hex"],
                        f"{tier}: terminal node/local key",
                    )
                    output_floats = struct.unpack(
                        "<8f",
                        bytes.fromhex(handoff["destination_after"]["hex"][:64]),
                    )
                    expected_node_fields = struct.pack(
                        "<8d", *(float(value) for value in output_floats)
                    ).hex()
                    require(
                        handoff["node_mapped_fields"]["hex"]
                        == expected_node_fields,
                        f"{tier}: terminal node mapped fields",
                    )
                    require(
                        report["counts"]["terminal_node_watchpoints_armed"] == 1,
                        f"{tier}: terminal node watch arm",
                    )
                    require(
                        report["counts"]["terminal_node_watchpoint_hits"] == 1,
                        f"{tier}: terminal node watch hit",
                    )
                    node_consumer = report["terminal_node_watch_samples"][0]
                    require(
                        node_consumer["libcp_va"] == 0x20090F,
                        f"{tier}: terminal node first consumer VA",
                    )
                    require(
                        node_consumer["changed"] is False,
                        f"{tier}: terminal node changed before copy",
                    )
                    require(
                        node_consumer["value_now"]["hex"]
                        == handoff["node_mapped_fields"]["hex"][:16],
                        f"{tier}: terminal node first-consumer bits",
                    )
                    require(
                        node_consumer["registers"]["rbx"] == handoff["node"] + 0x20,
                        f"{tier}: terminal node copy source identity",
                    )
                    node_consumer_stack = {
                        row.get("libcp_va") for row in node_consumer["stack"]
                    }
                    require(
                        {0x1FE8FF, 0x23D151, 0x22E249}.issubset(
                            node_consumer_stack
                        ),
                        f"{tier}: terminal node copy ancestry",
                    )
                    require(
                        report["counts"]["terminal_node_copy_returns"] == 1,
                        f"{tier}: terminal node copy return",
                    )
                    node_copy = report["terminal_node_copy"]
                    require(
                        node_copy["return_libcp_va"] == 0x2009C3,
                        f"{tier}: terminal node copy return VA",
                    )
                    require(
                        node_copy["source_node"] == handoff["node"],
                        f"{tier}: terminal node copy source pointer",
                    )
                    require(
                        node_copy["copied_node"] == node_copy["allocated_node"],
                        f"{tier}: terminal node copy allocation identity",
                    )
                    require(
                        node_copy["source_payload"]["hex"]
                        == node_copy["copied_payload"]["hex"],
                        f"{tier}: terminal node copied payload",
                    )
                    require(
                        report["counts"]["terminal_node_copy_watchpoints_armed"]
                        == 1,
                        f"{tier}: copied-node watch arm",
                    )
                    require(
                        report["counts"]["terminal_node_copy_watchpoint_hits"]
                        == 1,
                        f"{tier}: copied-node watch hit",
                    )
                    copied_consumer = report["terminal_node_copy_watch_samples"][0]
                    require(
                        copied_consumer["libcp_va"] == 0x200FB7,
                        f"{tier}: copied-node first consumer VA",
                    )
                    require(
                        copied_consumer["changed"] is False,
                        f"{tier}: copied node changed before transform",
                    )
                    require(
                        copied_consumer["value_now"]["hex"]
                        == node_copy["copied_payload"]["hex"][16:32],
                        f"{tier}: copied-node first-consumer bits",
                    )
                    require(
                        copied_consumer["registers"]["rbx"]
                        == node_copy["copied_node"],
                        f"{tier}: transform copied-node identity",
                    )
                    require(
                        copied_consumer["registers"]["rsi"]
                        == node_copy["copied_node"] + 0x28,
                        f"{tier}: transform field input identity",
                    )
                    copied_consumer_stack = {
                        row.get("libcp_va") for row in copied_consumer["stack"]
                    }
                    require(
                        {0x1FF618, 0x23D15D, 0x22E249}.issubset(
                            copied_consumer_stack
                        ),
                        f"{tier}: copied-node transform ancestry",
                    )
                    require(
                        report["counts"]["terminal_transform_returns"] == 1,
                        f"{tier}: camera-map normalization return",
                    )
                    normalized = report["terminal_transform"]
                    require(
                        normalized["return_libcp_va"] == 0x23D15D,
                        f"{tier}: camera-map normalization return VA",
                    )
                    require(
                        normalized["source_payload_after"]["hex"]
                        == node_copy["source_payload"]["hex"],
                        f"{tier}: selected source node changed by normalization",
                    )
                    require(
                        normalized["copied_payload_before"]["hex"]
                        == node_copy["copied_payload"]["hex"],
                        f"{tier}: copied-node pre-normalization drift",
                    )
                    require(
                        normalized["copied_payload_after"]["hex"]
                        != normalized["copied_payload_before"]["hex"],
                        f"{tier}: copied node unchanged by normalization",
                    )
                    require(
                        normalized["copied_payload_after"]["hex"][: 0x50 * 2]
                        == normalized["copied_payload_before"]["hex"][: 0x50 * 2],
                        f"{tier}: normalization changed bounded prefix",
                    )
                    require(
                        report["counts"][
                            "terminal_post_transform_watchpoints_armed"
                        ]
                        == 1,
                        f"{tier}: normalized-field watch arm",
                    )
                    require(
                        report["counts"][
                            "terminal_post_transform_watchpoint_hits"
                        ]
                        == 1,
                        f"{tier}: normalized-field first consumer",
                    )
                    normalized_consumer = report[
                        "terminal_post_transform_watch_samples"
                    ][0]
                    require(
                        normalized_consumer["libcp_va"] == 0x23D2AE,
                        f"{tier}: normalized-field first consumer VA",
                    )
                    require(
                        normalized_consumer["changed"] is False,
                        f"{tier}: normalized field changed before consumer",
                    )
                    require(
                        normalized_consumer["registers"]["rax"]
                        == normalized["copied_node"],
                        f"{tier}: normalized consumer node identity",
                    )
                    require(
                        normalized_consumer["value_now"]["hex"]
                        == normalized["copied_payload_after"]["hex"][
                            0x50 * 2 : 0x58 * 2
                        ],
                        f"{tier}: normalized consumer field bits",
                    )
                    for count_name in (
                        "terminal_normalized_convert_calls",
                        "terminal_normalized_convert_returns",
                        "terminal_normalized_compose_calls",
                        "terminal_normalized_compose_returns",
                        "terminal_normalized_f33d0_calls",
                        "terminal_normalized_f33d0_returns",
                    ):
                        require(
                            report["counts"][count_name] == 1,
                            f"{tier}: {count_name}",
                        )
                    pipeline = report["terminal_normalized_pipeline"]
                    require(
                        pipeline["convert_call_libcp_va"] == 0x23D2EE
                        and pipeline["convert_return_libcp_va"] == 0x23D2F3,
                        f"{tier}: normalized conversion call/return",
                    )
                    require(
                        pipeline["local_key"]["hex"]
                        == normalized["copied_payload_after"]["hex"][:8],
                        f"{tier}: normalized local/node key",
                    )
                    require(
                        pipeline["convert_source_snapshot"]["hex"]
                        == normalized["copied_payload_after"]["hex"][16:],
                        f"{tier}: normalized node/local conversion bytes",
                    )
                    require(
                        pipeline["convert_returned_rax"]
                        == pipeline["convert_destination"],
                        f"{tier}: normalized conversion return identity",
                    )
                    require(
                        pipeline["convert_destination_before"]["hex"]
                        != pipeline["convert_destination_after"]["hex"],
                        f"{tier}: normalized conversion output unchanged",
                    )
                    require(
                        pipeline["compose_call_libcp_va"] == 0x23D34D
                        and pipeline["compose_return_libcp_va"] == 0x23D352,
                        f"{tier}: normalized composition call/return",
                    )
                    require(
                        pipeline["compose_right"]
                        == pipeline["convert_destination"],
                        f"{tier}: conversion/composition pointer identity",
                    )
                    require(
                        pipeline["compose_right_snapshot"]["hex"]
                        == pipeline["convert_destination_after"]["hex"],
                        f"{tier}: conversion/composition bytes",
                    )
                    require(
                        pipeline["compose_returned_rax"]
                        == pipeline["compose_destination"],
                        f"{tier}: normalized composition return identity",
                    )
                    require(
                        pipeline["compose_destination_before"]["hex"]
                        != pipeline["compose_destination_after"]["hex"],
                        f"{tier}: normalized composition output unchanged",
                    )
                    require(
                        pipeline["f33d0_call_libcp_va"] == 0x23D38D
                        and pipeline["f33d0_return_libcp_va"] == 0x23D392,
                        f"{tier}: normalized f33d0 call/return",
                    )
                    require(
                        pipeline["f33d0_selector"] == 1,
                        f"{tier}: normalized f33d0 selector",
                    )
                    require(
                        pipeline["f33d0_destination_key"]["hex"]
                        == pipeline["local_key"]["hex"],
                        f"{tier}: normalized destination/local key",
                    )
                    require(
                        pipeline["f33d0_source_1"]
                        == pipeline["compose_destination"]
                        and pipeline["f33d0_source_3"]
                        == pipeline["compose_destination"] + 0x24
                        and pipeline["f33d0_source_2"]
                        == pipeline["compose_destination"] + 0x30,
                        f"{tier}: normalized composition/f33d0 slices",
                    )
                    compose_bytes = pipeline["compose_destination_after"]["hex"]
                    require(
                        pipeline["f33d0_source_1_snapshot"]["hex"]
                        == compose_bytes[: 0x24 * 2],
                        f"{tier}: normalized f33d0 source 1",
                    )
                    require(
                        pipeline["f33d0_source_3_snapshot"]["hex"]
                        == compose_bytes[0x24 * 2 : 0x30 * 2],
                        f"{tier}: normalized f33d0 source 3",
                    )
                    require(
                        pipeline["f33d0_source_2_snapshot"]["hex"]
                        == compose_bytes[0x30 * 2 : 0x54 * 2],
                        f"{tier}: normalized f33d0 source 2",
                    )
                    expected_bank = (
                        pipeline["f33d0_source_1_snapshot"]["hex"]
                        + pipeline["f33d0_source_2_snapshot"]["hex"]
                        + pipeline["f33d0_source_3_snapshot"]["hex"]
                    )
                    require(
                        pipeline["f33d0_bank_after"]["hex"] == expected_bank,
                        f"{tier}: normalized f33d0 destination bytes",
                    )
                    require(
                        pipeline["f33d0_bank_before"]["hex"]
                        != pipeline["f33d0_bank_after"]["hex"],
                        f"{tier}: normalized f33d0 bank unchanged",
                    )
                    require(
                        pipeline["outer_caller_libcp_va"] == 0x22E249,
                        f"{tier}: normalized write is not in terminal pass 1",
                    )
                    require(
                        report["counts"]["terminal_second_helper_calls"] == 1,
                        f"{tier}: terminal second helper call count",
                    )
                    require(
                        report["counts"][
                            "terminal_second_exact_postwrite_reads"
                        ]
                        == 1,
                        f"{tier}: terminal second-pass exact postwrite read",
                    )
                    custody = report["terminal_normalized_postwrite_consumer"]
                    second_call = custody["second_helper_call"]
                    matched = custody["matched_read"]
                    require(
                        custody["destination_object"]
                        == pipeline["f33d0_destination_object"],
                        f"{tier}: postwrite custody object identity",
                    )
                    require(
                        second_call["libcp_va"] == 0x22E283,
                        f"{tier}: second helper callsite",
                    )
                    require(
                        second_call["bank_at_call"]["hex"]
                        == pipeline["f33d0_bank_after"]["hex"],
                        f"{tier}: normalized bank changed before pass 2",
                    )
                    require(
                        second_call["destination_key_at_call"]["hex"]
                        == pipeline["f33d0_destination_key"]["hex"],
                        f"{tier}: normalized destination key changed before pass 2",
                    )
                    require(matched is not None, f"{tier}: missing matched pass-2 read")
                    require(
                        matched["source_object"]
                        == pipeline["f33d0_destination_object"],
                        f"{tier}: pass-2 source object identity",
                    )
                    require(
                        matched["source_key"]["hex"]
                        == pipeline["f33d0_destination_key"]["hex"],
                        f"{tier}: pass-2 source key identity",
                    )
                    require(
                        matched["source_bank"]["hex"]
                        == pipeline["f33d0_bank_after"]["hex"],
                        f"{tier}: pass-2 source bank bytes",
                    )
                    require(
                        matched["libcp_va"] in (0x23C6C0, 0x23CBA6, 0x23D226),
                        f"{tier}: unexpected pass-2 assembly callsite",
                    )
                    require(
                        0x22E288
                        in {row.get("libcp_va") for row in matched["stack"]},
                        f"{tier}: pass-2 terminal ancestry",
                    )
            composer_route = (
                f"0x239e00 score={score:.9g} existing={existing_score:.9g} "
                f"decision={decision_route}"
                + (
                    f" subpath={post['wide_update_path']['path']}"
                    if decision_route == "update"
                    else ""
                )
            )
        else:
            require(
                {0x20B0B2, 0x20ADB9, 0x22AE73}.issubset(stack_vas),
                f"{tier}: missing tele 0x20afb0/0x20ada0/State ancestry",
            )
            route = "0x20afb0->0x20ada0->State0x22ae60"
            require(
                composer_sample["libcp_va"] == 0x20DBF3,
                f"{tier}: tele composer consumer VA",
            )
            require(
                composer_sample["registers"]["rsi"]
                == composer_return["destination"],
                f"{tier}: tele matrix input mismatch",
            )
            require(post["kind"] == "tele", f"{tier}: tele post kind")
            helper = post["tele_helper_done"]
            caller = post["tele_caller_post"]
            node = post["tele_node_store"]
            require(helper["libcp_va"] == 0x20DC8D, f"{tier}: tele helper VA")
            require(caller["libcp_va"] == 0x20B24E, f"{tier}: tele caller VA")
            require(node["libcp_va"] == 0x20B272, f"{tier}: tele node VA")
            require(
                helper["matrix"]["hex"] == caller["local_matrix"]["hex"],
                f"{tier}: tele helper/caller matrix mismatch",
            )
            require(caller["node"] == node["node"], f"{tier}: tele node mismatch")
            require(
                helper["matrix"]["hex"] == node["node_matrix"]["hex"],
                f"{tier}: tele node matrix mismatch",
            )
            composer_route = (
                f"0x20dbe0 matrix -> node+0x20 key="
                f"{int.from_bytes(bytes.fromhex(node['node_key']['hex']), 'little')}"
            )
            require(storage_sample["kind"] == "tele_matrix", f"{tier}: storage kind")
            require(storage_sample["changed"] is True, f"{tier}: tele cleanup change")
            require(
                storage_sample["value_before"]["hex"]
                == node["node_matrix"]["hex"][:16],
                f"{tier}: tele watched prefix mismatch",
            )
            require(
                storage_sample["value_now"]["hex"] == "0000000000000000",
                f"{tier}: tele cleanup zero",
            )
            storage_stack = {row.get("libcp_va") for row in storage_sample["stack"]}
            require(0x23093D in storage_stack, f"{tier}: tele cleanup ancestry")
            composer_route += " first-later-touch=cleanup"
        summaries[tier] = {
            "source_object": entry["source_object"],
            "output_record": entry["output_record"],
            "composer_destination": sample["registers"]["r12"],
            "route": route,
            "composer_consumer": composer_sample["libcp_va"],
            "composer_route": composer_route,
        }
    return summaries


def main() -> None:
    verify_static()
    summaries = verify_runtime()
    print(
        f"static_264270_output_watch=OK libcp_sha256={LIBCP_SHA256} "
        f"assembly_sha256={ASSEMBLY_SHA256} composer_sha256={COMPOSER_SHA256}"
    )
    for tier in TIERS:
        summary = summaries[tier]
        print(
            f"{tier}: source_object=0x{summary['source_object']:x} "
            f"output_record=0x{summary['output_record']:x} "
            f"composer_destination=0x{summary['composer_destination']:x} "
            f"first_consumer=0x23fb26 route={summary['route']} "
            f"composer_consumer=0x{summary['composer_consumer']:x} "
            f"composer_route={summary['composer_route']}"
        )


if __name__ == "__main__":
    main()
