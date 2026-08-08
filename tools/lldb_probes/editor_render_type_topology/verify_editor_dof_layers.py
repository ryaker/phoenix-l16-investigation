#!/usr/bin/env python3
"""Verify the installed mode-1 DOF layer constructor against runtime tables."""

from __future__ import annotations

import hashlib
import json
import math
import struct
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
REPORT = ROOT / "runs/editor_render_type_topology/editor_dof_math_mode1_blur9_f2.json"
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def bits_to_f32(value: str) -> float:
    return struct.unpack("<f", struct.pack("<I", int(value, 16)))[0]


def f32_bits(value: float) -> str:
    return f"{struct.unpack('<I', struct.pack('<f', value))[0]:08x}"


def f32(value: float) -> float:
    return struct.unpack("<f", struct.pack("<f", value))[0]


def bits_to_f64(value: str) -> float:
    return struct.unpack(">d", bytes.fromhex(value))[0]


def range_hash(blob: bytes, start: int, end: int) -> str:
    return hashlib.sha256(blob[start:end]).hexdigest()


def radius_for(lower: float, upper: float) -> int:
    del lower
    return 2 * math.ceil(abs(upper)) + 1


def replay_table(low: float, high: float) -> list[tuple[str, str, int]]:
    low_limit = float(math.floor(low))
    high_limit = float(math.ceil(high))
    records: list[tuple[float, float, int]] = []

    # The selected 0x2c1ad0 branch receives start=0, unit span=1,
    # and geometric factor=2 from 0x2ce6d0 for both supported depth types.
    lower = 0.0
    upper = 1.0
    if high_limit >= lower and upper >= low_limit:
        records.append((lower, upper, radius_for(lower, upper)))

    lower = 1.0
    while lower < high_limit:
        upper = lower * 2.0
        if high_limit >= lower and upper >= low_limit:
            records.append((lower, upper, radius_for(lower, upper)))
        lower = upper

    upper = -0.0
    lower = -1.0
    if upper >= low_limit and high_limit >= lower:
        records.append((lower, upper, radius_for(lower, upper)))

    upper = -1.0
    while low_limit < upper:
        lower = upper * 2.0
        if upper >= low_limit and high_limit >= lower:
            records.append((lower, upper, radius_for(lower, upper)))
        upper = lower

    records.sort(key=lambda record: record[0])
    require(records, f"empty replay for range {low},{high}")
    first_lower = records[0][0]
    sentinel = (first_lower - 1.0, first_lower,
                2 * math.ceil(abs(first_lower)) + 1)
    records.insert(0, sentinel)
    return [(f32_bits(lower), f32_bits(upper), radius)
            for lower, upper, radius in records]


def main() -> None:
    blob = LIBCP.read_bytes()
    require(hashlib.sha256(blob).hexdigest() == LIBCP_SHA256, "libcp SHA drift")
    require(blob[0x2A414C:0x2A415C] == bytes.fromhex(
        "ba010000004c89ff4c89f6e814d20100"),
        "selected layer-constructor dispatch drift")
    require(blob[0x2C1B24:0x2C1B45] == bytes.fromhex(
        "f30f104580660f3a0ad009f30f119560fffffff30f108570ffffff"
        "660f3a0ad80a"),
        "range floor/ceil sequence drift")
    require(blob[0x2C1B5D:0x2C1B6E] == bytes.fromhex(
        "01c00f57c0f30f2ac0f30f5905fe6c2e00"),
        "layer start calculation drift")
    require(blob[0x2C1BE6:0x2C1C0E] == bytes.fromhex(
        "0f540503662e00e8fa442900f30f10ad40ffffff"
        "f30f58c0f30f100d22652e00f30f58c1f30f2cc0"),
        "odd-diameter calculation drift")
    require(blob[0x2C2275:0x2C22E6].find(bytes.fromhex("0f2e0439")) >= 0,
            "depth-bin upper-bound comparison drift")
    require(blob[0x2A4834:0x2A4886] == bytes.fromhex(
        "0f57c0f20f2a4308e8bb172b00f30f1075a0f30f106da4f2480f2cc0"
        "89c0f3480f2ac8f30f594dc4f30f1005c43830000f28d0f30f5cd1"
        "f30f5f158d0f32000f28cef30f5ccdf30f59caf30f5ec1f30f58cd"),
        "neighbor transition-width formula drift")
    require(blob[0x2A445F:0x2A44C6] == bytes.fromhex(
        "488b5590480395f0feffff4c01ea4c89f7488db530ffffff4c89f9"
        "e8710300004d85e47e20488b5590480395c8feffff4c01ea4c89f7"
        "488db530ffffff4c89f9e84c030000488b4590480385f0feffff"
        "498d5405c04c89f7488db530ffffff4c89f9e82a030000"),
        "three-neighbor layer gather drift")
    require(blob[0x2A55D0:0x2A55EA] == bytes.fromhex(
        "0f28c8f3410f5c4c240c0fc6c900410f594d000f5808410f2909"),
        "premultiplied source-over formula drift")
    installed_ranges = {
        (0x2B2450, 0x2B2B45):
            "f41588d481f954f69bad525a4dd8fe032aabe262ea08494589ee0cc258d09f2a",
        (0x2B2BE0, 0x2B2F2B):
            "0248b4fc351ff7e642f13e2684439e2fd63c137413a2d76fa55f40986f97bba2",
        (0x2B31C0, 0x2B3497):
            "0cceb9f5158de01dd67c0fc2f7afd5761a724369b6b966680a4489756bfff46a",
        (0x2B34B0, 0x2B39AE):
            "dd79ed26417db9dfe0add536de05f2c2ee4d87ee8e145278cea2d97a6ff5a17d",
        (0x2B39B0, 0x2B3B97):
            "2b08848b3f8995d689bf336108dd48e82f53fb969dcd972a94d2813a84d22300",
        (0x2ACD50, 0x2AD5D0):
            "3f51e87a2af4ba50f31b281551c8b93da9cb7da06d93185f60cabc31ad51e6d6",
    }
    for (start, end), expected in installed_ranges.items():
        require(range_hash(blob, start, end) == expected,
                f"installed body drift at 0x{start:x}..0x{end:x}")
    require(struct.unpack_from("<f", blob, 0x5ABED4)[0] == f32(1.0 / 64.0),
            "cubic phase step drift")
    require(struct.unpack_from("<d", blob, 0x5ABED8)[0] == 65536.0,
            "16.16 conversion constant drift")

    report = json.loads(REPORT.read_text())
    samples = report["layer_table_samples"]
    require(len(samples) >= 16, "insufficient distinct runtime layer tables")
    observed_radii: set[int] = set()
    observed_b5: set[int] = set()
    total_records = 0
    for index, sample in enumerate(samples):
        low, high = map(bits_to_f32, sample["range_bits"])
        expected = replay_table(low, high)
        actual = [(record["lower_bits"], record["upper_bits"], record["radius"])
                  for record in sample["records"]]
        require(actual == expected,
                f"table {index} mismatch for range {low},{high}: {actual} != {expected}")
        require(sample["depth_type"] == sample["b0"] == 0,
                f"unexpected depth type in table {index}")
        primary_pixels = sample["primary_dims"][0] * sample["primary_dims"][1]
        require(sum(record["primary_count"] for record in sample["records"])
                == primary_pixels, f"primary membership gap in table {index}")
        if not sample["secondary_present"]:
            require(all(record["secondary_count"] == 0
                        for record in sample["records"]),
                    f"secondary coordinates without an image in table {index}")
        observed_b5.add(sample["b5"])
        observed_radii.update(record["radius"] for record in sample["records"])
        total_records += len(actual)

    incidence = {item["radius"] for item in report["layer_radius_incidence"]}
    require(incidence == {1, 3, 5, 9, 17, 33, 65, 129},
            f"runtime radius incidence drift: {incidence}")
    require(observed_b5 == {0, 1}, f"missing b5 branch coverage: {observed_b5}")

    transitions = report["layer_transition_samples"]
    require(len(transitions) == 64, "incomplete transition sample set")
    transition_b5: set[int] = set()
    ramped = 0
    copied = 0
    for index, sample in enumerate(transitions):
        require(sample["b4"] == 0, f"unexpected b4 runtime branch at sample {index}")
        source_upper = bits_to_f32(sample["source_upper_bits"])
        boundary_upper = bits_to_f32(sample["boundary_upper_bits"])
        color = [bits_to_f32(value) for value in sample["color_bits"]]
        if source_upper > boundary_upper:
            config = f32(0.1 if sample["b0"] == 0 else 0.2)
            exponent = int(math.log2(sample["boundary_radius"]))
            width = max(
                f32(f32(1.0) - f32(f32(float(exponent)) * config)),
                f32(0.1),
            )
            span = f32(f32(source_upper - boundary_upper) * width)
            inverse_span = f32(f32(1.0) / span)
            threshold = f32(span + boundary_upper)
            depth = bits_to_f32(sample["depth_bits"])
            weight = f32(max(f32(0.0), f32(threshold - depth)) * inverse_span)
            expected_output = [f32_bits(f32(value * weight)) for value in color]
            expected_output.append(f32_bits(weight))
            ramped += 1
        else:
            expected_output = sample["color_bits"] + ["3f800000"]
            copied += 1
        require(sample["output_bits"] == expected_output,
                f"transition replay mismatch at sample {index}")
        transition_b5.add(sample["b5"])
    require(transition_b5 == {0, 1},
            f"missing transition b5 branch incidence: {transition_b5}")
    relations = report["layer_transition_relation_calls"]
    require(relations["less"] == relations["greater"] > 0 and
            relations["equal"] > 0,
            f"unexpected transition relation census: {relations}")

    require(report["gaussian5_captured"] == 1,
            "missing live five-tap DOF Gaussian")
    gaussian5 = ["3d5f2f87", "3e7a0feb", "3ece2434",
                 "3e7a0feb", "3d5f2f87"]
    require(report["gaussian5_bits"] == gaussian5,
            f"five-tap Gaussian drift: {report['gaussian5_bits']}")

    branch_calls = report["layer_filter_branch_calls"]
    require(branch_calls == {"copy": 278, "small": 1435, "large": 900},
            f"layer-filter branch incidence drift: {branch_calls}")
    require(sum(branch_calls.values()) == report["layer_filter_calls"] == 2613,
            "layer-filter call total mismatch")
    require(report["layer_filter_rect_calls"] == {"equal": 2613, "distinct": 0},
            f"layer-filter rectangle incidence drift: {report['layer_filter_rect_calls']}")
    require(report["layer_filter_resample_calls"] == 2 * branch_calls["large"],
            "large layers did not make exactly two resample passes")
    for index, sample in enumerate(report["layer_filter_samples"]):
        maximum = 13 if sample["depth_type"] == 0 else 65
        diameter = sample["diameter"]
        expected_branch = 0 if diameter <= 2 else (1 if maximum > diameter else 2)
        require(sample["branch"] == expected_branch,
                f"layer-filter branch mismatch at sample {index}")

    directions: Counter[str] = Counter()
    diameter_directions: Counter[tuple[int, str]] = Counter()
    resamples = report["layer_resample_samples"]
    require(len(resamples) == 256, "insufficient tagged resample samples")
    for index, sample in enumerate(resamples):
        observed_scale = bits_to_f64(sample["scale_bits"][0])
        direction = "down" if observed_scale > 1.0 else "up"
        directions[direction] += 1
        diameter = sample["diameter"]
        diameter_directions[(diameter, direction)] += 1
        output_width, output_height = sample["output_dims"]
        input_width, input_height = sample["input_dims"]
        if direction == "down":
            width, height = input_width, input_height
        else:
            width, height = output_width, output_height
        maximum = 13 if sample["depth_type"] == 0 else 65
        scale = f32(max(
            f32(f32(maximum) / f32(diameter)),
            f32(f32(min(width, 10)) / f32(width)),
            f32(f32(min(height, 10)) / f32(height)),
        ))
        inverse = f32(f32(1.0) / scale)
        expected_scale = inverse if direction == "down" else scale
        require([bits_to_f64(value) for value in sample["scale_bits"]]
                == [float(expected_scale), float(expected_scale)],
                f"resample scale mismatch at sample {index}")

        first = sample["first_rect"]
        scaled_x = math.trunc(f32(f32(float(first[0])) * scale))
        scaled_y = math.trunc(f32(f32(float(first[1])) * scale))
        if direction == "down":
            expected_dims = [
                math.trunc(f32(float(first[2] - first[0])) * scale),
                math.trunc(f32(float(first[3] - first[1])) * scale),
            ]
            require(sample["output_dims"] == expected_dims,
                    f"downsample dimension mismatch at sample {index}")
            offsets = [
                f32(f32(f32(float(scaled_x)) * inverse) - f32(float(first[0]))),
                f32(f32(f32(float(scaled_y)) * inverse) - f32(float(first[1]))),
            ]
        else:
            offsets = [
                f32(f32(f32(float(first[0])) * scale) - f32(float(scaled_x))),
                f32(f32(f32(float(first[1])) * scale) - f32(float(scaled_y))),
            ]
        require([bits_to_f64(value) for value in sample["offset_bits"]]
                == [float(value) for value in offsets],
                f"resample offset mismatch at sample {index}")

    require(directions == {"down": 128, "up": 128},
            f"resample direction coverage drift: {directions}")
    require({diameter for diameter, _ in diameter_directions}
            == {17, 33, 65, 129},
            f"large-diameter coverage drift: {diameter_directions}")
    for diameter in (17, 33, 65, 129):
        require(diameter_directions[(diameter, "down")]
                == diameter_directions[(diameter, "up")] > 0,
                f"unpaired resample coverage for diameter {diameter}")
    print(f"static_layer_constructor=OK tables={len(samples)}")
    print(f"runtime_layer_replay=OK records={total_records} radii={sorted(incidence)}")
    print("primary_membership=OK all captured depth pixels assigned exactly once")
    print(f"runtime_transition_replay=OK samples={len(transitions)} "
          f"ramped={ramped} copied={copied} calls={report['layer_transition_calls']}")
    print("runtime_layer_filter=OK copy=278 small=1435 large=900 resamples=1800")
    print("runtime_resample_replay=OK retained=256 diameters=17,33,65,129")
    print("static_compositor=OK cubic_B_spline_64_phase clamp disk gaussian source-over")


if __name__ == "__main__":
    main()
