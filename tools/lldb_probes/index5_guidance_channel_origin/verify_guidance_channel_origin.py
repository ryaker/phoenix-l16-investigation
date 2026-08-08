#!/usr/bin/env python3
"""Verify the public producer and custody chain for index-5 Guidance."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import struct
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)
REPORT = ROOT / "runs/index5_guidance_channel_origin/guidance_origin_28mm.json"

CREATE_FUNC_TYPE_VA = 0x5DBA20
CREATE_LAMBDA_TYPE_VA = 0x5DBB30
CREATE_LAMBDA_VTABLE = 0x6591A8
CREATE_LAMBDA_WORKER = 0x27D950
CREATE2_LAMBDA_VTABLE = 0x659228
CREATE2_LAMBDA_WORKER = 0x27DC80
CONVERT_FUNC_TYPE_VA = 0x5DB7E0
CONVERT_LAMBDA_TYPE_VA = 0x5DB890
CONVERT_LAMBDA_VTABLE = 0x6590A8
CONVERT_LAMBDA_WORKER = 0x27D1A0
CREATE_CONVERT_VTABLE = 0x659020
CREATE_CONVERT_WORKER = 0x27CE60

RAW_CREATE_FUNC_TYPE = (
    "NSt3__110__function6__funcIZN2lt9StereoISP17CreateStereoImageERNS2_5Image"
    "INS2_8vec4x8uiEEERKNS4_ItEERKNS2_13CapturedImageERKNS2_9CalibDataESG_"
    "RKNS2_4Vec2IiEERKNS2_7SoftISPESN_RKNS2_4Vec3IfEERNS4_INS2_8vec4x32fEEE"
    "SG_bbE3$_2NS_9allocatorISV_EEFvRKNS2_9RectangleIiEEiEEE"
)
RAW_CREATE_LAMBDA_TYPE = (
    "ZN2lt9StereoISP17CreateStereoImageERNS_5ImageINS_8vec4x8uiEEERKNS1_ItEE"
    "RKNS_13CapturedImageERKNS_9CalibDataESD_RKNS_4Vec2IiEERKNS_7SoftISPESK_"
    "RKNS_4Vec3IfEERNS1_INS_8vec4x32fEEESD_bbE3$_2"
)
PUBLIC_SIGNATURE = (
    "lt::StereoISP::CreateStereoImage(lt::Image<lt::vec4x8ui>&, "
    "lt::Image<unsigned short> const&, lt::CapturedImage const&, "
    "lt::CalibData const&, lt::CalibData const&, lt::Vec2<int> const&, "
    "lt::SoftISP const&, lt::SoftISP const&, lt::Vec3<float> const&, "
    "lt::Image<lt::vec4x32f>&, lt::CalibData const&, bool, bool)"
)
RAW_CONVERT_FUNC_TYPE = (
    "NSt3__110__function6__funcIZN2lt9StereoISP12ConvertToYUVERKNS2_5Image"
    "INS2_8vec4x32fEEERKNS2_6MatrixIfLi4ELi4ELb1EEEE3$_0NS_9allocatorISD_EE"
    "FvRKNS2_9RectangleIiEEiEEE"
)
RAW_CONVERT_LAMBDA_TYPE = (
    "ZN2lt9StereoISP12ConvertToYUVERKNS_5ImageINS_8vec4x32fEEERKNS_6Matrix"
    "IfLi4ELi4ELb1EEEE3$_0"
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


STATIC = load_module("index5_guidance_origin_static", STATIC_PATH)


def verify_static() -> tuple[str, str]:
    digest = STATIC.verify_static()
    data = STATIC.LIBCP.read_bytes()
    mapping = STATIC.segments(data)

    require(
        STATIC.cstring(data, mapping, CREATE_FUNC_TYPE_VA).decode("ascii")
        == RAW_CREATE_FUNC_TYPE,
        "CreateStereoImage function-object type drift",
    )
    require(
        STATIC.cstring(data, mapping, CREATE_LAMBDA_TYPE_VA).decode("ascii")
        == RAW_CREATE_LAMBDA_TYPE,
        "CreateStereoImage lambda type drift",
    )
    demangled = subprocess.run(
        ["c++filt", "-t", RAW_CREATE_FUNC_TYPE],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    require(PUBLIC_SIGNATURE in demangled, "CreateStereoImage public signature drift")
    require(
        STATIC.cstring(data, mapping, CONVERT_FUNC_TYPE_VA).decode("ascii")
        == RAW_CONVERT_FUNC_TYPE,
        "ConvertToYUV function-object type drift",
    )
    require(
        STATIC.cstring(data, mapping, CONVERT_LAMBDA_TYPE_VA).decode("ascii")
        == RAW_CONVERT_LAMBDA_TYPE,
        "ConvertToYUV lambda type drift",
    )

    for lea_va, target in (
        (0x27BBBC, CREATE_LAMBDA_VTABLE),
        (0x27C276, CREATE2_LAMBDA_VTABLE),
    ):
        require(
            STATIC.rip_target(STATIC.instruction(data, mapping, lea_va)) == target,
            f"CreateStereoImage callback vtable LEA 0x{lea_va:x} changed",
        )
    require(
        STATIC.u64(
            STATIC.bytes_at(data, mapping, CREATE_LAMBDA_VTABLE + 0x30, 8)
        )
        == CREATE_LAMBDA_WORKER,
        "CreateStereoImage callback worker drift",
    )
    require(
        STATIC.u64(
            STATIC.bytes_at(data, mapping, CREATE2_LAMBDA_VTABLE + 0x30, 8)
        )
        == CREATE2_LAMBDA_WORKER,
        "CreateStereoImage second callback worker drift",
    )
    require(
        STATIC.rip_target(STATIC.instruction(data, mapping, 0x27B4D4))
        == CONVERT_LAMBDA_VTABLE,
        "ConvertToYUV callback vtable LEA changed",
    )
    require(
        STATIC.u64(
            STATIC.bytes_at(data, mapping, CONVERT_LAMBDA_VTABLE + 0x30, 8)
        )
        == CONVERT_LAMBDA_WORKER,
        "ConvertToYUV callback worker drift",
    )
    require(
        STATIC.rip_target(STATIC.instruction(data, mapping, 0x27AE49))
        == CREATE_CONVERT_VTABLE,
        "CreateStereoImage ConvertToYUV callback vtable drift",
    )
    require(
        STATIC.u64(
            STATIC.bytes_at(data, mapping, CREATE_CONVERT_VTABLE + 0x30, 8)
        )
        == CREATE_CONVERT_WORKER,
        "CreateStereoImage ConvertToYUV callback worker drift",
    )
    require(
        STATIC.direct_call_target(STATIC.instruction(data, mapping, 0x27BFF0))
        == 0x27ADC0,
        "CreateStereoImage ConvertToYUV call drift",
    )

    calls = (
        (0x3F47F8, 0x27AEF0),
        (0x3F5086, 0x27B7A0),
        (0x3FC798, 0x3F4B90),
        (0x3FC7E3, 0xF340),
        (0x3FC807, 0x224F30),
        (0x3FF0EA, 0x226410),
        (0x3FF43C, 0x2681B0),
        (0x268268, 0x26BA90),
        (0x26BAEB, 0x274160),
    )
    for call_va, target in calls:
        require(
            STATIC.direct_call_target(STATIC.instruction(data, mapping, call_va))
            == target,
            f"custody call 0x{call_va:x} changed",
        )

    require(
        STATIC.memory_displacement(STATIC.instruction(data, mapping, 0x22641A), 1)
        == 0x78,
        "keyed image-tree root offset changed",
    )
    require(
        STATIC.memory_displacement(STATIC.instruction(data, mapping, 0x226454), 1)
        == 0x28,
        "keyed image-tree payload offset changed",
    )
    require(
        STATIC.memory_displacement(STATIC.instruction(data, mapping, 0x26BAD4), 1)
        == 0x240,
        "StereoLayer Images destination changed",
    )
    require(
        STATIC.memory_displacement(STATIC.instruction(data, mapping, 0x3F4845), 0)
        == 0x270,
        "ConvertToYUV shared-descriptor destination changed",
    )
    require(
        STATIC.instruction(data, mapping, 0x3FF426).op_str == "r14, 0x270",
        "ConvertToYUV handoff offset changed",
    )
    require(
        STATIC.instruction(data, mapping, 0x2681E2).op_str == "rbx, rdx",
        "layer dispatcher optional-image capture changed",
    )
    require(
        STATIC.instruction(data, mapping, 0x26821A).mnemonic == "test"
        and STATIC.direct_call_target(
            STATIC.instruction(data, mapping, 0x268268)
        )
        == 0x26BA90,
        "StereoLayer branch changed",
    )

    windows = {
        (0x27B7A0, 0x27CDC0): "4bdb42332ca7b6cf240cdc1f224b1f4af0e0de01c93e6362f4542725caff0aca",
        (0x3F500D, 0x3F5096): "d5200d312ccd98ba1f5f63c6bc983a2a782e9b20687f8ed5e2c073b4ba6fc29f",
        (0x3FC750, 0x3FC857): "f4929a18f56305d86ae4d4097fe10578a664f3100cdbbda67f2c7f7219acdf56",
        (0x226410, 0x2264F0): "e996e4aa0b75f3a89cbfd96795fe31daf87a5c4ffe1bbe8e35ccbd2b6de1fd49",
    }
    for (start, end), expected in windows.items():
        actual = hashlib.sha256(
            STATIC.bytes_at(data, mapping, start, end - start)
        ).hexdigest()
        require(actual == expected, f"static range 0x{start:x}..0x{end:x} changed")
    return digest, demangled


def verify_runtime() -> str:
    report = json.loads(REPORT.read_text())
    require(report["process"]["state"] == "exited", "runtime process state")
    require(report["process"]["exit_status"] == 9, "runtime early-kill status")
    require(report["capture_complete"], "runtime capture incomplete")
    require(report["terminated_after_capture"], "runtime did not terminate after capture")
    require(not report["errors"], f"runtime errors: {report['errors']}")
    require(not report["drive_hit_step_cap"], "runtime drive hit step cap")
    require(report["watchpoint_stops"] == 2, "unexpected watchpoint stop count")
    require(
        report["watchpoint_hit_counts"]
        == {"payload_watchpoint_id": 1, "root_watchpoint_id": 1},
        "unexpected watchpoint hit counts",
    )

    events = report["create_stereo_events"]
    require(len(events) == 1, "expected one completed CreateStereoImage event")
    create = events[0]
    require(create["call_site"] == 0x3F5086, "CreateStereoImage call site")
    require(create["return_site"] == 0x3F508B, "CreateStereoImage return site")
    require(
        create["before_raw_0x00_0x30"] == "00" * 0x30,
        "CreateStereoImage output was not initially empty",
    )
    stack_vas = [row["libcp_va"] for row in create["stack"][:4]]
    require(
        stack_vas == [0x3F5086, 0x3FC79D, 0x3FEB2F, 0x3FBCB3],
        f"CreateStereoImage stack changed: {stack_vas}",
    )

    event = report["event"]
    require(event["libcp_va"] == 0x22504A, "cache payload writer changed")
    require(event["node"]["key_0x20"] == 0, "captured cache key is not zero")
    require(event["create_stereo_completed_count"] == 1, "producer count mismatch")
    require(event["matches_latest_create_stereo_output"], "cached descriptor mismatch")
    require(event["matching_create_stereo_event_indexes"] == [0], "producer match set")
    require(
        create["after_raw_0x00_0x30"]
        == event["cached_descriptor_raw_0x00_0x30"],
        "CreateStereoImage output bytes differ from cached payload",
    )
    payload = bytes.fromhex(event["cached_descriptor_raw_0x00_0x30"])
    words = list(struct.unpack("<12I", payload))
    require(
        words[:8] == [0, 0, 2080, 1560, 2080, 1560, 2080, 1560],
        f"unexpected cached descriptor geometry: {words[:8]}",
    )
    pointers = struct.unpack_from("<QQ", payload, 0x20)
    require(pointers[0] != 0 and pointers[0] == pointers[1], "descriptor data pointers")
    cache_stack = [row["libcp_va"] for row in event["stack"][:4]]
    require(
        cache_stack == [0x22504A, 0x3FC80C, 0x3FEB2F, 0x3FBCB3],
        f"cache insertion stack changed: {cache_stack}",
    )
    return (
        "Unit-1 28mm key=0 descriptor=2080x1560 "
        "CreateStereoImage_output==cached_payload"
    )


def main() -> None:
    digest, demangled = verify_static()
    print(f"static_index5_guidance_channel_origin=OK libcp={digest}")
    print(f"public_producer={PUBLIC_SIGNATURE}")
    print(
        "convert_to_yuv_route=CreateStereoImage calls 0x27adc0 with callback "
        "worker 0x27ce60 before key-0 pack; state+0x270 is an additional "
        "optional Upsample-route product"
    )
    print(f"runtime={verify_runtime()}")
    print("index5_guidance_channel_origin=OK")


if __name__ == "__main__":
    main()
