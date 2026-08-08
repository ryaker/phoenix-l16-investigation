#!/usr/bin/env python3
"""Verify the public mode-1 DOFCache activation and pixel-effect bundle."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
RUN = ROOT / "runs/editor_render_type_topology"
SCHEMA_VERIFIER = (
    ROOT
    / "tools/lldb_probes/prefusion_node_dest_sentinel_custody"
    / "verify_embedded_calibration_proto_schema.py"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_bytes(blob: bytes, offset: int, expected: bytes, label: str) -> None:
    actual = blob[offset : offset + len(expected)]
    assert actual == expected, (
        f"{label} at {offset:#x}: expected {expected.hex()}, got {actual.hex()}"
    )


def rel32_target(blob: bytes, callsite: int) -> int:
    assert blob[callsite] == 0xE8, hex(callsite)
    return callsite + 5 + struct.unpack_from("<i", blob, callsite + 1)[0]


def jump_target(blob: bytes, table: int, index: int) -> int:
    return table + struct.unpack_from("<i", blob, table + 4 * index)[0]


def load_schema_module():
    spec = importlib.util.spec_from_file_location("embedded_schema", SCHEMA_VERIFIER)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_static(libcp: bytes) -> None:
    assert sha256(LIBCP) == "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"

    schema = load_schema_module()
    descriptors = schema.locate_all_descriptors(libcp)
    renderer_state = next(d for d in descriptors if d["name"] == "renderer_state.proto")
    assert renderer_state["serialized_sha256"] == (
        "3ca9a552251894714200ea068359a2167b5e15a00e596e18ef5ca4a75b156588"
    )
    fields = schema.field_map([renderer_state])
    schema.require_field(fields, ".ltpb.Settings", 12, "dof", "message")
    schema.require_field(fields, ".ltpb.Settings.DOF", 1, "f_num", "float")
    schema.require_field(fields, ".ltpb.Settings.DOF", 2, "focus_depth", "float")

    exports = subprocess.check_output(
        ["objdump", "--macho", "--exports-trie", str(LIBCP)], text=True
    )
    assert "__ZN5CIAPI12RendererBase11setPropertyENS_10ParamFloatEf" in exports

    # ParamFloat 0/1 dispatch to the first two float slots in the 14-float state.
    assert jump_target(libcp, 0x3C6160, 0) == 0x3C602E
    assert jump_target(libcp, 0x3C6160, 1) == 0x3C603E
    require_bytes(libcp, 0x3C602E, bytes.fromhex("f30f1045ccf3410f114748"), "ParamFloat(0)")
    require_bytes(libcp, 0x3C603E, bytes.fromhex("f30f1045ccf3410f11474c"), "ParamFloat(1)")

    # The worker snapshots those slots, validates focus_depth > 0, and forwards
    # xmm0/xmm1 to DOFCache::setDOF.
    assert rel32_target(libcp, 0x3B07FF) == 0x3C6F80
    require_bytes(libcp, 0x3B083F, bytes.fromhex("f3410f108d38070000"), "prior f_num")
    require_bytes(libcp, 0x3B0848, bytes.fromhex("f30f104598"), "requested f_num")
    require_bytes(libcp, 0x3B0852, bytes.fromhex("f30f104d9c"), "requested focus_depth")
    require_bytes(libcp, 0x3B086F, bytes.fromhex("0f2eca761d"), "positive focus guard")
    assert rel32_target(libcp, 0x3B0889) == 0x3F07D0

    require_bytes(libcp, 0x3F07DF, bytes.fromhex("0f2ec27642"), "positive f_num guard")
    require_bytes(libcp, 0x3F07E4, bytes.fromhex("0f2eca7677"), "positive focus guard")
    require_bytes(libcp, 0x3F080F, bytes.fromhex("f30f118398000000"), "cache f_num store")
    require_bytes(libcp, 0x3F0817, bytes.fromhex("f30f118b9c000000"), "cache focus store")

    # Mode 1 requires depth readiness, then selects DOF iff f_num < threshold.
    require_bytes(libcp, 0x3BB588, bytes.fromhex("4489c34183be8808000000"), "mode-1 depth gate")
    assert rel32_target(libcp, 0x3BB5A3) == 0x3C6F80
    assert rel32_target(libcp, 0x3BB5BF) == 0x3F06D0
    require_bytes(libcp, 0x3BB5CC, bytes.fromhex("0f2ec80f8340030000"), "f_num threshold predicate")
    require_bytes(libcp, 0x3BB5D5, bytes.fromhex("498bbeb8060000"), "mode-1 DOF arm")
    require_bytes(libcp, 0x3BB915, bytes.fromhex("498bbe88060000"), "mode-1 Pipeline arm")
    assert rel32_target(libcp, 0x3BB5F0) == 0x3D0650
    assert rel32_target(libcp, 0x3BB930) == 0x3D0650

    require_bytes(
        libcp,
        0x3F06D4,
        bytes.fromhex("f30f108788000000f30f598784000000f30f5e8780000000"),
        "DOF threshold formula",
    )

    # Public ParamFloat(19) accepts [0.1, 10], but the optical helper requires
    # strict 0 < max_infocus_blur < 10.
    require_bytes(libcp, 0x3B86C1, bytes.fromhex("4183fe13"), "ParamFloat(19)")
    require_bytes(libcp, 0x3B86CC, bytes.fromhex("0f2e052dd12000"), "0.1 lower bound")
    require_bytes(libcp, 0x3B86D5, bytes.fromhex("0f2e0534141f00"), "10 upper bound")
    require_bytes(libcp, 0x3B86DE, bytes.fromhex("83bb7407000001"), "mode-1 setter exclusion")
    require_bytes(libcp, 0x3B86EB, bytes.fromhex("f30f1183e0080000"), "max blur store")
    require_bytes(libcp, 0x2C5719, bytes.fromhex("0f57ed0f2ee50f868f000000"), "strict positive blur")
    require_bytes(libcp, 0x2C5725, bytes.fromhex("0f2e25e4432e000f8382000000"), "strict less-than-10 blur")


def verify_runtime() -> None:
    control = json.loads((RUN / "editor_cache_route_mode1_blur9.json").read_text())
    treatment = json.loads((RUN / "editor_cache_route_mode1_blur9_f2.json").read_text())

    assert control["mode0_pipeline"] == control["mode1_pipeline"] == 388
    assert control["mode0_dof"] == control["mode1_dof"] == 0
    assert control["dof_threshold_bits"] == "41737a6f"
    assert control["mode1_request_min_bits"] == "41737a6f"
    assert control["mode1_request_max_bits"] == "41737a6f"
    assert control["dof_field_98_bits"] == "41737a6f"
    assert control["dof_field_9c_bits"] == "00000000"

    assert treatment["mode0_pipeline"] == treatment["mode1_dof"] == 388
    assert treatment["mode0_dof"] == treatment["mode1_pipeline"] == 0
    assert treatment["dof_field_80_bits"] == "406b851f"  # 3.6800000668
    assert treatment["dof_field_84_bits"] == "41e00000"  # 28.0
    assert treatment["dof_field_88_bits"] == "40000000"  # 2.0
    assert treatment["dof_threshold_bits"] == "41737a6f"  # 15.2173910141
    assert treatment["dof_field_98_bits"] == "40000000"  # f_num 2.0
    assert treatment["dof_field_9c_bits"] == "45bc271c"  # 6020.888671875 mm
    assert treatment["mode0_request_min_bits"] == "41737a6f"
    assert treatment["mode1_request_min_bits"] == "40000000"
    assert treatment["mode1_request_max_bits"] == "40000000"

    control_raw = RUN / "editor_cache_output_mode1_blur9_level4.raw"
    treatment_raw = RUN / "editor_cache_output_mode1_blur9_f2_level4.raw"
    assert control_raw.stat().st_size == treatment_raw.stat().st_size == 1_275_312
    assert sha256(control_raw) == "6e647328940c4a436760b2462677e89439211ebb101ab2bbbe7f0da8d023bcf1"
    assert sha256(treatment_raw) == "4c0441433388fa4f3364319e2d22ea1970e964837fb1055264e0d69c657816c0"
    control_bytes = control_raw.read_bytes()
    treatment_bytes = treatment_raw.read_bytes()
    assert sum(a != b for a, b in zip(control_bytes, treatment_bytes)) == 659_544
    assert sum(
        control_bytes[i : i + 4] != treatment_bytes[i : i + 4]
        for i in range(0, len(control_bytes), 4)
    ) == 264_514
    assert max(abs(a - b) for a, b in zip(control_bytes, treatment_bytes)) == 95


def main() -> None:
    verify_static(LIBCP.read_bytes())
    verify_runtime()
    print("editor DOF public route: static + runtime bundle verified")


if __name__ == "__main__":
    main()
