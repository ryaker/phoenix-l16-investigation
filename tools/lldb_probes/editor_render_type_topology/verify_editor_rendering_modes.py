#!/usr/bin/env python3
"""Verify public editor rendering modes and retained Unit-1 28mm captures."""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
LUMEN = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/MacOS/Lumen"
)
RUN = ROOT / "runs/editor_render_type_topology"

LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
LUMEN_SHA256 = "1cd727486f9b21c4eacab4a99cff4a85f3c1c3f5e4f3a78b76617ec12438065d"

MODE_NAMES = ["Normal", "RefocusPoint", "RefocusSlider", "DebugView", "QuickSelect"]
MODE_TARGETS = [0x3BB524, 0x3BB588, 0x3BB5FA, 0x3BB718, 0x3BB76D]
DEBUG_TARGETS = {
    0x300C: 0x42C140,
    0x300D: 0x42C140,
    0x300E: 0x42C140,
    0x3017: 0x42FB40,
    0x3018: 0x42D8D0,
    0x3019: 0x42C8F0,
    0x301A: 0x42FD30,
    0x301B: 0x42C8F0,
    0x301C: 0x42C8F0,
    0x301D: 0x42C8F0,
    0x301E: 0x42ECB0,
}
RAW_SHA256 = {
    "mode0_blur9_f2": "4c0441433388fa4f3364319e2d22ea1970e964837fb1055264e0d69c657816c0",
    "mode1_blur9_f2": "4c0441433388fa4f3364319e2d22ea1970e964837fb1055264e0d69c657816c0",
    "mode2_blur9_f2": "a726066884c63f86efc177a954418d98010ba87136f7d95ff7d6ce2334907628",
    "mode3_blur9_f2": "0e9b834fc7bc5c5854fe83ed4c87f9688c74991917647a90da078d00872f9c8a",
    "mode4_blur9_f2": "4c0441433388fa4f3364319e2d22ea1970e964837fb1055264e0d69c657816c0",
    "mode3_blur9_f2_debug300c": "a958af3506d0c138ea8f120df45bd520e38e8ea82c91dcdfa7fc5e2c5139104a",
    "mode3_blur9_f2_debug300d": "361d92bc68dce5a74cbfd510e730cecd7a44a4fb311f2081e2a801542dc5ebf7",
    "mode3_blur9_f2_debug300e": "332a786c69b1dfa50e13b736549f667ea1eb20c1d6369330f148f7509082df06",
    "mode3_blur9_f2_debug3017": "c97c3c7f3e8f38d1f0eb057802ef056cdb4b31a987ce8895836d943cbd1dc104",
    "mode3_blur9_f2_debug3018": "e273c72c326975d9e2f54bd00ee8720acd94383b72d150cb49e9e5bb1c429b83",
    "mode3_blur9_f2_debug3019": "14af19c08431e41fbab91751193897c68d7f74f4e6d6988af70a43077bae6c47",
    "mode3_blur9_f2_debug301a": "1e56efc8e93b4499506280918ff5b27d554ffce1395b72b9f459409fcdee867a",
    "mode3_blur9_f2_debug301b": "d6e8590444315141d040499a0a32a7de2623af6bf7dc3c557f6464579d887078",
    "mode3_blur9_f2_debug301c": "f7683607264ed3660ad896a9840a7b01f01c8671554b163fbbc5e78e168f88fe",
    "mode3_blur9_f2_debug301d": "92b9400fc4fabc4b0e69176fa6ab3b3f5222bd1d248291a502d3d7e598e52e87",
    "mode3_blur9_f2_debug301e": "7dc934f6587762499f63df1445888fce8683c5d15cf4e51ab975eee9550b452a",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def range_hash(data: bytes, start: int, end: int) -> str:
    return sha256(data[start:end])


def qt_strings(data: bytes, base: int, count: int) -> list[str]:
    result = []
    for index in range(count):
        record = base + 24 * index
        refcount, size = struct.unpack_from("<ii", data, record)
        allocation, offset = struct.unpack_from("<Qq", data, record + 8)
        require(refcount == -1 and allocation == 0,
                f"unexpected Qt string record {index}")
        start = record + offset
        raw = data[start:start + size]
        require(data[start + size] == 0, f"Qt string {index} lacks terminator")
        result.append(raw.decode("ascii"))
    return result


def parse_info(path: Path) -> dict[str, int]:
    info = {}
    for line in path.read_text().splitlines():
        key, value = line.split("=", 1)
        info[key] = int(value)
    return info


def request_state(report: dict, mode: int) -> dict:
    matches = [item for item in report.get("request_state", [])
               if item["mode"] == mode]
    require(len(matches) == 1, f"missing request state for mode {mode}")
    return matches[0]


def verify_installed() -> None:
    libcp = LIBCP.read_bytes()
    lumen = LUMEN.read_bytes()
    require(sha256(libcp) == LIBCP_SHA256, "libcp SHA drift")
    require(sha256(lumen) == LUMEN_SHA256, "Lumen SHA drift")

    ranges = {
        (libcp, 0x3BB4F2, 0x3BC13D):
            "2028df3497459309c77869701f83f46b41b71c16a0d4677aa53fdda3243fa55f",
        (libcp, 0x3B0DD0, 0x3B155E):
            "da283ba71a2c4d55d987489a261ec88aa5fb38b6349f8facc7dbd1b43d7ecace",
        (libcp, 0x3B8970, 0x3B8A99):
            "3dade3831d235eb2a3e83d24171712a6b27d4a809a53057443ee506f55872d56",
        (libcp, 0x3C5ED0, 0x3C5FC4):
            "0127af1688f0bbb09045753b09d497bdeebc9ee7aaaaa3e4021ac7069055319b",
        (libcp, 0x396120, 0x396130):
            "66c80e744188f5938e96db3d4c84120bf48369172dfb40a3e81f59092cec7687",
        (libcp, 0x3A7150, 0x3A7820):
            "9cf0cb46996ec9f7e7e6b23833b7fca4f1816c5768da55179d96ebf824582c8a",
        (libcp, 0x3BBF37, 0x3BC0E6):
            "9f83060846505e08f5a9adb3cbcc45b0925f893b86e374897e08558a93b8b3ed",
        (lumen, 0x2C670, 0x2C6B4):
            "586cbc33c3cfbe0ac9d0bd8d68cd4e43d534437069bca393be7ffbfe639640bd",
        (lumen, 0x68C80, 0x68C9C):
            "23bd284c8ea1e2e0c3d28f1b97650d8a3cdf38ee975cbea1befa2320caf2a56c",
        (lumen, 0x31350, 0x315FE):
            "7fb63907a8e80c5d2105440b177affecf5e22464d0effaca4951e5f602af7291",
        (lumen, 0xCC52F0, 0xCC53D8):
            "825c126e69e99011e3b360a6c63477067fe0464044e30a46bc895255a5166897",
    }
    for (data, start, end), expected in ranges.items():
        require(range_hash(data, start, end) == expected,
                f"installed range drift at 0x{start:x}..0x{end:x}")

    # Qt 5 enum metadata: each enum record is name, flags, count, pair offset.
    strings = qt_strings(lumen, 0xD59828, 20)
    metadata = struct.unpack_from("<58I", lumen, 0xCC52F0)
    require(metadata[8:10] == (3, 14), "ImageEdit enum table moved")
    enum_records = [metadata[14 + 4 * index:18 + 4 * index]
                    for index in range(3)]
    render = enum_records[1]
    require(strings[render[0]] == "RenderMode" and render[2] == 5,
            "RenderMode metadata drift")
    pairs = [(strings[metadata[render[3] + 2 * index]],
              metadata[render[3] + 2 * index + 1])
             for index in range(render[2])]
    require(pairs == list(zip(MODE_NAMES, range(5))),
            f"public RenderMode enum drift: {pairs}")

    jump_base = 0x3BC480
    targets = [jump_base + struct.unpack_from("<i", libcp, jump_base + 4 * mode)[0]
               for mode in range(5)]
    require(targets == MODE_TARGETS, f"mode jump-table drift: {targets}")

    # ParamInt(20): subtract 10, table index 10, then store at request state +0x80.
    require(libcp[0x3C5EF4:0x3C5EFB] == bytes.fromhex("83c3f683fb0a77"),
            "ParamInt range gate drift")
    param_table = 0x3C5FC4
    param_target = param_table + struct.unpack_from("<i", libcp, param_table + 40)[0]
    require(param_target == 0x3C5F48, f"ParamInt(20) target drift: 0x{param_target:x}")
    require(libcp[0x3C5F48:0x3C5F50] == bytes.fromhex("4589bc2480000000"),
            "ParamInt(20) state+0x80 store drift")


def verify_runtime() -> None:
    expected_routes = {
        0: {"mode0_dof": 388, "mode0_pipeline": 388},
        1: {"mode1_dof": 388, "mode0_pipeline": 388},
        2: {"mode2_pipeline": 388, "mode0_pipeline": 388},
        3: {"mode0_pipeline": 388},
        4: {"mode4_dof": 388, "mode0_pipeline": 388},
    }
    route_fields = ["mode0_dof", "mode1_dof", "mode2_pipeline", "mode4_dof",
                    "mode0_pipeline", "mode1_pipeline", "mode4_pipeline"]
    reports = {}
    for mode in range(5):
        stem = f"mode{mode}_blur9_f2"
        report = json.loads((RUN / f"editor_cache_route_{stem}.json").read_text())
        reports[mode] = report
        for field in route_fields:
            require(report.get(field, 0) == expected_routes[mode].get(field, 0),
                    f"mode {mode} route drift at {field}")
        if mode in (0, 1, 4):
            require(report["dof_threshold_calls"] == 786,
                    f"mode {mode} DOF threshold count drift")
        else:
            require(report["dof_threshold_calls"] == 398,
                    f"mode {mode} preparation threshold count drift")

        raw = RUN / f"editor_cache_output_{stem}_level4.raw"
        info = parse_info(RUN / f"editor_cache_output_{stem}_level4.info")
        require(info == {"width": 652, "height": 489, "stride": 2608,
                         "pixelformat_int": 0, "bytes": 1275312},
                f"mode {mode} output geometry drift: {info}")
        require(raw.stat().st_size == info["bytes"], f"mode {mode} raw size drift")
        require(sha256(raw.read_bytes()) == RAW_SHA256[stem],
                f"mode {mode} raw hash drift")

    require(RAW_SHA256["mode0_blur9_f2"] == RAW_SHA256["mode1_blur9_f2"] ==
            RAW_SHA256["mode4_blur9_f2"],
            "retained default Normal/RefocusPoint/QuickSelect outputs differ")
    mode2 = (RUN / "editor_cache_output_mode2_blur9_f2_level4.raw").read_bytes()
    require(mode2 != (RUN / "editor_cache_output_mode0_blur9_f2_level4.raw").read_bytes(),
            "RefocusSlider output unexpectedly equals Normal")

    unset = reports[3]
    state3 = request_state(unset, 3)
    require(unset["mode3_first_request_key"] == -1 and
            unset["mode3_matched_calls"] == 0 and
            unset["mode3_selected_target_va"] == "0x0",
            "unset DebugView fallback drift")
    require(state3["calls"] == 388 and state3["debug_size"] == 11,
            "unset DebugView request/tree count drift")
    raw3 = (RUN / "editor_cache_output_mode3_blur9_f2_level4.raw").read_bytes()
    require(not any(raw3), "unset DebugView output is not zero-filled")

    observed_keys = set()
    observed_hashes = set()
    for key, target in DEBUG_TARGETS.items():
        suffix = f"mode3_blur9_f2_debug{key:04x}"
        report = json.loads((RUN / f"editor_cache_route_{suffix}.json").read_text())
        state = request_state(report, 3)
        require(report["mode3_first_request_key"] == key,
                f"DebugView 0x{key:x} request-key drift")
        require(report["mode3_matched_calls"] == 388 and state["calls"] == 388,
                f"DebugView 0x{key:x} match-count drift")
        require(int(report["mode3_selected_target_va"], 16) == target,
                f"DebugView 0x{key:x} target drift")
        require(state["debug_size"] == len(DEBUG_TARGETS),
                f"DebugView 0x{key:x} tree-size drift")
        raw = RUN / f"editor_cache_output_{suffix}_level4.raw"
        require(sha256(raw.read_bytes()) == RAW_SHA256[suffix],
                f"DebugView 0x{key:x} raw hash drift")
        observed_keys.add(report["mode3_first_request_key"])
        observed_hashes.add(RAW_SHA256[suffix])
    require(observed_keys == set(DEBUG_TARGETS), "incomplete DebugView key set")
    require(len(observed_hashes) == len(DEBUG_TARGETS),
            "DebugView keys did not produce distinct retained outputs")

    quick = reports[4]
    state4 = request_state(quick, 4)
    mask = quick["quick_select_mask"]
    require(mask == {"calls": 388, "width": 5216, "height": 3912,
                     "stride": 5216, "pixels": 20404992, "nonzero": 0,
                     "min": 0, "max": 0},
            f"default QuickSelect mask drift: {mask}")
    require(state4["color_8c0"] ==
            ["3f800000", "00000000", "3f800000", "3e800000"],
            "QuickSelect overlay color drift")
    require(state4["slider_8e0"] == "41100000" and state4["debug_size"] == 11,
            "QuickSelect renderer defaults drift")

    active_stem = "mode4_blur9_f2_quick"
    active_report = json.loads(
        (RUN / f"editor_cache_route_{active_stem}.json").read_text())
    active_mask_meta = active_report["quick_select_mask"]
    require(active_mask_meta == {
        "calls": 388, "width": 5216, "height": 3912, "stride": 5216,
        "pixels": 20404992, "nonzero": 32268, "min": 0, "max": 1,
    }, f"active QuickSelect mask drift: {active_mask_meta}")
    require(active_report["mode4_dof"] == 388 and
            active_report["mode0_pipeline"] == 388,
            "active QuickSelect route drift")

    mask_path = RUN / f"editor_quick_select_mask_{active_stem}.raw"
    active_path = RUN / f"editor_cache_output_{active_stem}_level4.raw"
    mask = mask_path.read_bytes()
    active = active_path.read_bytes()
    baseline = (RUN / "editor_cache_output_mode4_blur9_f2_level4.raw").read_bytes()
    require(len(mask) == 5216 * 3912 and
            sha256(mask) == "557a4e37597217455b0d77a7e20e9d1f19e64ff4b3de8b73eeaa939d4390633e",
            "active QuickSelect raw mask drift")
    require(len(active) == 652 * 489 * 4 and
            sha256(active) == "6cbaa0eaf9f2709f50705091f3a18a451e56e308338e1fcc3ce4ebf859d7eaef",
            "active QuickSelect packed output drift")
    require(set(mask) == {0, 1} and sum(mask) == 32268,
            "active QuickSelect mask is not exact binary incidence")

    mask_points = [(index % 5216, index // 5216)
                   for index, value in enumerate(mask) if value]
    require((min(x for x, _ in mask_points), min(y for _, y in mask_points),
             max(x for x, _ in mask_points), max(y for _, y in mask_points)) ==
            (2489, 1873, 2733, 2036), "active QuickSelect mask bbox drift")

    selected = set()
    changed = set()
    changed_bytes = 0
    maximum_delta = 0
    for y in range(489):
        for x in range(652):
            pixel = 4 * (y * 652 + x)
            if mask[(8 * y) * 5216 + 8 * x]:
                selected.add((x, y))
            if active[pixel:pixel + 4] != baseline[pixel:pixel + 4]:
                changed.add((x, y))
            for lane in range(4):
                delta = abs(active[pixel + lane] - baseline[pixel + lane])
                changed_bytes += delta != 0
                maximum_delta = max(maximum_delta, delta)
    require(selected == changed and len(selected) == 501,
            "active QuickSelect output support does not equal sampled mask support")
    require(changed_bytes == 1498 and maximum_delta == 64,
            "active QuickSelect packed-difference incidence drift")
    require(all(active[4 * (y * 652 + x) + 3] ==
                baseline[4 * (y * 652 + x) + 3] for x, y in changed),
            "active QuickSelect changed alpha")


def main() -> None:
    verify_installed()
    verify_runtime()
    print("PASS editor RenderingMode: public enum, exact dispatch, five-mode runtime routes")
    print("PASS DebugView: unset zero fallback plus complete 11-key tree/target/output census")
    print("PASS QuickSelect: 388 reads of 5216x3912 all-zero default mask; exact no-op output")
    print("PASS active QuickSelect: binary mask and 501/501 sampled-pixel output support")


if __name__ == "__main__":
    main()
