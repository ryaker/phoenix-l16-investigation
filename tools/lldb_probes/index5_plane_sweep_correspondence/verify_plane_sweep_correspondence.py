#!/usr/bin/env python3
"""Verify and replay the index-5 plane-sweep correspondence transform."""

from __future__ import annotations

import hashlib
import json
import math
import struct
from pathlib import Path

from capstone import CS_ARCH_X86, CS_MODE_64, Cs
from capstone.x86_const import X86_INS_CALL, X86_INS_JMP, X86_OP_IMM
import numpy as np


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
REPORT = ROOT / "runs/index5_plane_sweep_correspondence/unit1_28mm/report.json"
EXAMPLES = (
    ROOT
    / "runs/index5_plane_sweep_correspondence/unit1_28mm/correspondence_examples.json"
)
COMPOSED_REPORT = ROOT / "runs/index5_composed_geometry_origin/composed_geometry_28mm.json"
LOOKUP_REPORT = (
    ROOT
    / "runs/codex_index5_lookup_vector_public_origin/lookup_vector_public_28mm.json"
)
WINNER_MAP = ROOT / "runs/reference_stage_maps/unit1_28mm/index5_hypothesis_index.u16le"

SOURCE_NAMES = ("A5", "A2", "A3", "A4")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def f32(value):
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def add(a, b):
    return f32(f32(a) + f32(b))


def mul(a, b):
    return f32(f32(a) * f32(b))


def div(a, b):
    return f32(f32(a) / f32(b))


def instruction(data, address):
    decoder = Cs(CS_ARCH_X86, CS_MODE_64)
    decoder.detail = True
    return next(decoder.disasm(data[address : address + 16], address))


def direct_target(insn):
    require(insn.id in (X86_INS_CALL, X86_INS_JMP), f"0x{insn.address:x}: not call/jmp")
    require(len(insn.operands) == 1 and insn.operands[0].type == X86_OP_IMM, "direct target")
    return insn.operands[0].imm


def verify_static():
    data = LIBCP.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    require(digest == LIBCP_SHA256, f"installed libcp digest {digest}")
    windows = {
        (0x25E0C0, 0x25E4A8): "a2f016d2329cbf72e4fac334e8795ef7312614dc123304de4b8cb71086a9dd76",
        (0x25E4B0, 0x25E4FA): "ad316edfe91f6b6a2966c2603cf354482da4520ecf6e31968f333ef810add354",
        (0x26A790, 0x26A83E): "4cc606ba3d1c378af1ff579c802e4b792d6de86d5df159552e55a8b3d7741da9",
        (0x2728F0, 0x2729B0): "a636e78fcd92684c5c3ee1ecfc35c820bfc67eb1c4676f3d4636204f598076ca",
        (0x2732F0, 0x273AC3): "43584a1fab797ad5f8ca4770fc3b2885f95ad93e79f0bcfbda12abaae5155a00",
        (0x276F76, 0x2773E1): "94ddf5c386c558561c3e04b32282b2d6dbe241ebda6e63c40e9a20c7a07d242d",
    }
    for (start, end), expected in windows.items():
        observed = hashlib.sha256(data[start:end]).hexdigest()
        require(observed == expected, f"window 0x{start:x}..0x{end:x}")

    calls = {
        0x25E32B: 0x25EC70,
        0x25E348: 0x25EC70,
        0x25E35A: 0x9DB20,
        0x25E36C: 0x25EC70,
        0x25E4F5: 0x25E0C0,
        0x26A7FF: 0x25E4B0,
        0x272976: 0x26A790,
        0x2769FC: 0x26A790,
        0x2773DC: 0x2732F0,
    }
    for address, target in calls.items():
        require(direct_target(instruction(data, address)) == target, f"target 0x{address:x}")

    expected = {
        0x25E4E6: ("movabs", "rax, 0x3f8000003f800000"),
        0x26A7C8: ("mov", "ebx, 1"),
        0x26A7CF: ("mov", "r12d, 0xa8"),
        0x26A7E0: ("add", "r12, 0xa8"),
        0x2733D8: ("mulss", "xmm0, xmm5"),
        0x2733DC: ("mulss", "xmm0, dword ptr [r14 + r8 + 0x48]"),
        0x2733E8: ("mulss", "xmm1, xmm5"),
        0x2733EC: ("mulss", "xmm1, dword ptr [r14 + r8 + 0x4c]"),
        0x2733F7: ("mulps", "xmm0, xmmword ptr [r14 + r8]"),
        0x273400: ("mulps", "xmm1, xmmword ptr [r14 + r8 + 0x10]"),
        0x27340A: ("mulps", "xmm5, xmmword ptr [r14 + r8 + 0x20]"),
        0x273410: ("addps", "xmm5, xmmword ptr [r14 + r8 + 0x30]"),
        0x273416: ("addps", "xmm5, xmm0"),
        0x273419: ("addps", "xmm5, xmm1"),
        0x27342C: ("divss", "xmm0, xmm2"),
        0x273430: ("mulss", "xmm5, xmm0"),
        0x273434: ("mulss", "xmm0, xmm1"),
        0x273438: ("addss", "xmm5, xmm11"),
        0x27343D: ("addss", "xmm0, xmm11"),
        0x27346D: ("maxss", "xmm5, xmm1"),
        0x273471: ("maxss", "xmm0, xmm2"),
        0x273475: ("minss", "xmm5, xmm3"),
        0x273479: ("minss", "xmm0, xmm4"),
        0x27347D: ("cvttss2si", "r11d, xmm5"),
        0x273482: ("cvttss2si", "eax, xmm0"),
        0x273524: ("pavgb", "xmm6, xmm7"),
        0x273539: ("pavgb", "xmm3, xmm6"),
    }
    for address, wanted in expected.items():
        insn = instruction(data, address)
        observed = (insn.mnemonic, insn.op_str)
        require(observed == wanted, f"0x{address:x}: {observed} != {wanted}")

    # The result matrix is loaded row-major as doubles, but stored as float32 columns.
    transpose_stores = {
        0x25E441: "dword ptr [rbx], xmm14",       # H[0]
        0x25E446: "dword ptr [rbx + 4], xmm4",   # H[4]
        0x25E44B: "dword ptr [rbx + 8], xmm3",   # H[8]
        0x25E450: "dword ptr [rbx + 0xc], xmm1", # H[12]
        0x25E455: "dword ptr [rbx + 0x10], xmm12", # H[1]
        0x25E46A: "dword ptr [rbx + 0x20], xmm9",  # H[2]
        0x25E480: "dword ptr [rbx + 0x30], xmm8",  # H[3]
    }
    for address, operands in transpose_stores.items():
        insn = instruction(data, address)
        require((insn.mnemonic, insn.op_str) == ("movss", operands), f"transpose 0x{address:x}")

    require(struct.unpack("<f", data[0x5A8200 : 0x5A8204])[0] == 0.25, "+0.25")
    create_name = data[0x5DBA20 : data.index(b"\0", 0x5DBA20)].decode("ascii")
    warp_name = data[0x5DBF90 : data.index(b"\0", 0x5DBF90)].decode("ascii")
    require("StereoISP17CreateStereoImage" in create_name, "CreateStereoImage RTTI")
    require("ImageWarp" in warp_name and "LensUndistortCRA" in warp_name, "undistort warp RTTI")
    return digest


def project(record, u, v, depth, descriptor):
    values = [f32(value) for value in record["matrix_0x00"]]
    columns = [values[index : index + 4] for index in range(0, 16, 4)]
    scale_x, scale_y = [f32(value) for value in record["scale_0x48"]]
    qx = mul(mul(f32(u), depth), scale_x)
    qy = mul(mul(f32(v), depth), scale_y)
    p = []
    for lane in range(4):
        value = mul(depth, columns[2][lane])
        value = add(value, columns[3][lane])
        value = add(value, mul(qx, columns[0][lane]))
        value = add(value, mul(qy, columns[1][lane]))
        p.append(value)
    require(math.isfinite(p[2]) and p[2] != 0.0, "finite projection denominator")
    inverse_z = div(1.0, p[2])
    continuous_x = add(mul(p[0], inverse_z), 0.25)
    continuous_y = add(mul(p[1], inverse_z), 0.25)
    x0, y0 = descriptor["origin"]
    x1, y1 = descriptor["bounds"]
    sampled_x = min(max(continuous_x, f32(x0 + 1)), f32(x1 - 3))
    sampled_y = min(max(continuous_y, f32(y0 + 1)), f32(y1 - 3))
    base_x = int(sampled_x)
    base_y = int(sampled_y)
    return {
        "projective_p_f32": p,
        "continuous_before_clamp": [continuous_x, continuous_y],
        "sample_coordinate": [sampled_x, sampled_y],
        "integer_base_trunc": [base_x, base_y],
        "half_phase": [int(f32(sampled_x + sampled_x)) & 1, int(f32(sampled_y + sampled_y)) & 1],
        "clamped": [sampled_x != continuous_x, sampled_y != continuous_y],
    }


def build_result(packet, index_map, scope):
    require((packet["index"], packet["mode"]) == (5, 8), "index/mode")
    require(packet["projection_vector"]["count"] == 4, "four projected sources")
    require(packet["images_vector"]["count"] == 5, "five Images")
    descriptors = [item["descriptor"] for item in packet["images"]]
    require(all(item and item["size"] == [2080, 1560] for item in descriptors), "Images dimensions")
    require(all(item["stride"] == 2080 for item in descriptors), "Images stride")
    require(packet["guidance"]["size"] == [2080, 1560], "Guidance dimensions")
    records = packet["projection_vector"]["records"]
    require(all(item and item["scale_0x48"] == [1.0, 1.0] for item in records), "unit scales")

    require(index_map["source_descriptor"]["size"] == [2080, 1560], "winner-map dimensions")
    lookup = index_map["lookup"]
    require(lookup["count"] == 752 and lookup["byte_size"] == 3008, "wide lookup")
    lookup_values = struct.unpack("<752f", bytes.fromhex(lookup["raw_hex"]))

    samples = []
    for selected in index_map["samples"]:
        u = selected["u"]
        v = selected["v"]
        hypothesis = selected["hypothesis_index"]
        require(hypothesis < len(lookup_values), f"hypothesis {hypothesis}")
        depth = lookup_values[hypothesis]
        sources = []
        for ordinal, (name, record, descriptor) in enumerate(
            zip(SOURCE_NAMES, records, descriptors[1:])
        ):
            sources.append(
                {
                    "source_ordinal": ordinal + 1,
                    "camera": name,
                    **project(record, u, v, depth, descriptor),
                }
            )
        samples.append(
            {
                "reference_camera": "A1",
                "reference_pixel": [u, v],
                "winning_hypothesis_index": hypothesis,
                "ray_depth_mm": depth,
                "sources": sources,
            }
        )

    result = {
        "scope": scope,
        "coordinate_frame": "StereoLayer 2080x1560 level coordinates",
        "camera_order": ["A1", *SOURCE_NAMES],
        "samples": samples,
    }
    EXAMPLES.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    return result


def verify_same_run():
    report = json.loads(REPORT.read_text())
    require(report.get("capture_complete"), "runtime capture incomplete")
    require(not report.get("errors"), f"runtime errors: {report.get('errors')}")
    return build_result(
        report["projection_packet"],
        report["index_map"],
        "Unit-1 canonical 28mm, index 5, mode 8; same-run capture",
    )


def composed_matrices(record):
    k = np.eye(4, dtype=np.float64)
    k[:3, :3] = np.asarray(struct.unpack_from("<9f", record, 0)).reshape(3, 3)
    extrinsic = np.eye(4, dtype=np.float64)
    extrinsic[:3, :3] = np.asarray(
        struct.unpack_from("<9f", record, 0x30)
    ).reshape(3, 3)
    extrinsic[:3, 3] = struct.unpack_from("<3f", record, 0x24)
    return k, extrinsic


def verify_retained_join():
    expected_hashes = {
        COMPOSED_REPORT: "8bad9066618c8e72ba5dbb0e710ab05c9b527e8eeadd235e4c8d2b7fd3d336ec",
        LOOKUP_REPORT: "87c2f04b91db12ded99f6d4b0e18152ba7dc06cea464c2b94dcb1a872f3769a6",
        WINNER_MAP: "e6c207fad12807546b9e9f9f4c0e0722c5bef8b3fb933da512b0f4ab1c111bd4",
    }
    for path, expected in expected_hashes.items():
        require(hashlib.sha256(path.read_bytes()).hexdigest() == expected, f"artifact {path}")

    composed = json.loads(COMPOSED_REPORT.read_text())
    event = next(
        item
        for item in composed["events"]
        if item.get("site_name") == "before_stereolayer_install"
    )
    packet0 = event["packet"]
    raw = bytes.fromhex(packet0["composed_geometry_vector"]["raw_hex"])
    require(len(raw) == 5 * 0xA8, "five composed 0xa8 records")
    camera_records = [raw[index * 0xA8 : (index + 1) * 0xA8] for index in range(5)]
    k_reference, e_reference = composed_matrices(camera_records[0])
    reference_camera = k_reference @ e_reference
    projection_records = []
    for record in camera_records[1:]:
        k_source, e_source = composed_matrices(record)
        h = (k_source @ e_source) @ np.linalg.inv(reference_camera)
        stored = h.T.astype(np.float32).reshape(-1).tolist()
        projection_records.append(
            {"matrix_0x00": stored, "map_0x40": 0, "scale_0x48": [1.0, 1.0]}
        )

    lookup_report = json.loads(LOOKUP_REPORT.read_text())
    lookup_sample = next(
        item
        for item in lookup_report["target_samples"]
        if item.get("site") == "lookup_vector_after_copy_f043e"
    )
    lookup_hex = lookup_sample["source_span_copied_by_f02d0"]["raw_hex"]
    lookup_raw = bytes.fromhex(lookup_hex)
    require(len(lookup_raw) == 752 * 4, "retained lookup size")
    map_raw = WINNER_MAP.read_bytes()
    require(len(map_raw) == 2080 * 1560 * 2, "retained winner-map size")
    samples = []
    for u, v in ((1040, 780), (520, 390), (1560, 1170)):
        hypothesis = struct.unpack_from("<H", map_raw, 2 * (v * 2080 + u))[0]
        samples.append({"u": u, "v": v, "hypothesis_index": hypothesis})

    descriptor = {
        "origin": [0, 0],
        "bounds": [2080, 1560],
        "size": [2080, 1560],
        "stride": 2080,
    }
    packet = {
        "index": 5,
        "mode": 8,
        "guidance": descriptor,
        "images_vector": {"count": 5},
        "images": [
            {"ordinal": ordinal, "descriptor": descriptor} for ordinal in range(5)
        ],
        "projection_vector": {"count": 4, "records": projection_records},
    }
    index_map = {
        "source_descriptor": descriptor,
        "lookup": {"count": 752, "byte_size": 3008, "raw_hex": lookup_hex},
        "samples": samples,
    }
    result = build_result(
        packet,
        index_map,
        "Unit-1 canonical 28mm retained-runtime deterministic join; composed records, lookup, and winner map are from separate completed captures",
    )
    result["artifact_sha256"] = {
        str(path.relative_to(ROOT)): value for path, value in expected_hashes.items()
    }
    EXAMPLES.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    return result


def verify_runtime():
    if REPORT.exists():
        try:
            report = json.loads(REPORT.read_text())
            if report.get("capture_complete") and not report.get("errors"):
                return verify_same_run()
        except (OSError, ValueError):
            pass
    return verify_retained_join()


def main():
    digest = verify_static()
    result = verify_runtime()
    print(f"index5_plane_sweep_static=OK libcp={digest}")
    print("matrix=H=(Ksrc*Esrc)*inverse(Kref*Eref); stored=float32(transpose(H))")
    print("projection=P=H*[u*d,v*d,d,1]; sample=(Px/Pz+0.25,Py/Pz+0.25)")
    for sample in result["samples"]:
        source_text = ", ".join(
            f"{source['camera']}=({source['sample_coordinate'][0]:.6f},{source['sample_coordinate'][1]:.6f})"
            for source in sample["sources"]
        )
        print(
            f"pixel={tuple(sample['reference_pixel'])} h={sample['winning_hypothesis_index']} "
            f"d_mm={sample['ray_depth_mm']:.9g} {source_text}"
        )
    print(f"index5_plane_sweep_correspondence=OK examples={EXAMPLES}")


if __name__ == "__main__":
    main()
