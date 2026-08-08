#!/usr/bin/env python3
"""Replay the installed 0x2d4410/0x2d4540 AWB table-fit helpers."""

import argparse
import hashlib
import json
import struct
from pathlib import Path

import numpy as np


EXPECTED_SHA256 = {
    "table1": "b52a2038cacf6b66e6cbb3610cfbfbc7e681d2754c85ce057d2f04f49e0afa85",
    "table2": "7eebd34fbfe7e4e8c0144db61ecdc48297a2a7efd95993629174f8c69460c848",
}

ILLUMINANT_A_XY_BITS = (0x3EE5283F, 0x3ED09BF5)
ILLUMINANT_D65_XY_BITS = (0x3EA01DB4, 0x3EA875B8)
ILLUMINANT_A_RECONSTRUCTED_XY_BITS = (0x3EE52841, 0x3ED09BF8)
ILLUMINANT_D65_RECONSTRUCTED_XY_BITS = (0x3EA01DB0, 0x3EA875B5)
ILLUMINANT_A_CCT_BITS = 0x45327A1E
ILLUMINANT_D65_CCT_BITS = 0x45CB30A7


def f32(value):
    return np.float32(value)


def from_bits(value):
    return np.array(value, dtype=np.uint32).view(np.float32)


def fast_log2(value):
    """Installed scalar polynomial used by 0x2d36ba..0x2d3cbf."""
    x = f32(value)
    bits = int(x.view(np.uint32))
    mantissa = from_bits((bits & 0x007FFFFF) | 0x3F800000)
    result = f32(mantissa * f32(0.20420436561107635))
    result = f32(result + f32(-1.2525469064712524))
    result = f32(result * mantissa)
    result = f32(result + f32(3.331021547317505))
    result = f32(result * mantissa)
    adjusted = (bits + 0xC0800000) & 0xFFFFFFFF
    if adjusted & 0x80000000:
        adjusted -= 0x100000000
    exponent = f32(adjusted >> 23)
    return f32(f32(exponent + f32(-2.2826788425445557)) + result)


def normalized_log_ratios(neutral):
    r_log = min(max(fast_log2(f32(neutral[0] / neutral[1])), f32(-2)), f32(2))
    b_log = min(max(fast_log2(f32(neutral[2] / neutral[1])), f32(-2)), f32(2))
    return np.array(
        [f32(f32(r_log * f32(0.25)) + f32(0.5)),
         f32(f32(b_log * f32(0.25)) + f32(0.5))],
        dtype=np.float32,
    )


def endpoint_neutral(matrix, xy):
    x, y = map(f32, xy)
    xyz = np.array(
        [
            f32(f32(f32(1.0) / y) * x),
            f32(1.0),
            f32(f32(f32(f32(1.0) - y) - x) / y),
        ],
        dtype=np.float32,
    )
    response = np.empty(3, dtype=np.float32)
    for row in range(3):
        value = f32(f32(matrix[row, 0] * xyz[0]) + matrix[row, 1])
        response[row] = f32(value + f32(matrix[row, 2] * xyz[2]))
    reciprocal = f32(f32(1.0) / response[1])
    return np.array(
        [f32(response[0] * reciprocal), f32(1.0), f32(response[2] * reciprocal)],
        dtype=np.float32,
    )


def interpolate_matrix(calibration, target_cct):
    cct_a, cct_d65 = calibration[:2]
    matrix_a = calibration[4:13].reshape((3, 3))
    matrix_d65 = calibration[13:22].reshape((3, 3))
    target_mired = f32(f32(1.0) / f32(target_cct))
    a_mired = f32(f32(1.0) / cct_a)
    d65_mired = f32(f32(1.0) / cct_d65)
    clamped = f32(min(max(target_mired, d65_mired), a_mired))
    alpha = f32(f32(clamped - d65_mired) / f32(a_mired - d65_mired))
    result = np.empty((3, 3), dtype=np.float32)
    for index, (a_value, d65_value) in enumerate(
        zip(matrix_a.flat, matrix_d65.flat)
    ):
        result.flat[index] = f32(
            d65_value + f32(alpha * f32(a_value - d65_value))
        )
    return result


def generated_points(solve, candidate_record):
    calibration = np.frombuffer(
        bytes.fromhex(solve["calibration_snapshot"]["raw"]), dtype="<f4"
    )
    xy_a = np.array(
        [from_bits(word) for word in ILLUMINANT_A_RECONSTRUCTED_XY_BITS]
    )
    xy_d65 = np.array(
        [from_bits(word) for word in ILLUMINANT_D65_RECONSTRUCTED_XY_BITS]
    )
    matrix_a = interpolate_matrix(calibration, from_bits(ILLUMINANT_A_CCT_BITS))
    matrix_d65 = interpolate_matrix(
        calibration, from_bits(ILLUMINANT_D65_CCT_BITS)
    )
    basis_a = normalized_log_ratios(endpoint_neutral(matrix_a, xy_a))
    basis_d65 = normalized_log_ratios(endpoint_neutral(matrix_d65, xy_d65))
    # The installed solver stores coefficients as [D65, A]. Its 2x2 system
    # is ordered [blue, red], so det = A_b * D_r - D_b * A_r.
    determinant = f32(
        f32(basis_a[1] * basis_d65[0]) - f32(basis_d65[1] * basis_a[0])
    )
    reciprocal = f32(f32(1.0) / determinant)

    candidates = np.frombuffer(
        bytes.fromhex(candidate_record["payload"]), dtype="<f4"
    ).reshape((-1, 4))
    points = np.empty((candidates.shape[0], 2), dtype=np.float32)
    for index, (red, green, blue, _) in enumerate(candidates):
        ratios = normalized_log_ratios(
            np.array(
                [f32(red / green), f32(1.0), f32(blue / green)],
                dtype=np.float32,
            )
        )
        first = f32(
            f32(basis_a[1] * ratios[0]) - f32(basis_a[0] * ratios[1])
        )
        second = f32(
            f32(basis_d65[0] * ratios[1]) - f32(basis_d65[1] * ratios[0])
        )
        points[index] = (f32(first * reciprocal), f32(second * reciprocal))
    return points, basis_a, basis_d65


def fast_exp2(value):
    x = min(max(f32(value), f32(-126.0)), f32(128.0))
    exponent = int(np.trunc(x))
    if int(x.view(np.uint32)) & 0x80000000:
        exponent -= 1
    fraction = f32(x - f32(exponent))
    result = f32(fraction * f32(0.07802452147006989))
    result = f32(result + f32(0.22606715559959412))
    result = f32(result * fraction)
    result = f32(result + f32(0.6958335638046265))
    result = f32(result * fraction)
    result = f32(result + f32(0.9999251961708069))
    bits = (int(result.view(np.uint32)) + ((exponent << 23) & 0xFFFFFFFF))
    return from_bits(bits & 0xFFFFFFFF)


def combine_centroids(table1, table2, centroid1, centroid2, scene_weight, basis_a, basis_d65):
    support1 = bilinear(table1, centroid1[0], centroid1[1])
    support2 = bilinear(table2, centroid2[0], centroid2[1])
    second_weight = f32(support2 * f32(scene_weight))
    first_weight = f32(support1 * f32(f32(1.0) - f32(scene_weight)))
    denominator = f32(first_weight + second_weight)
    x = f32(
        f32(f32(centroid1[0] * first_weight) + f32(centroid2[0] * second_weight))
        / denominator
    )
    y = f32(
        f32(f32(centroid1[1] * first_weight) + f32(centroid2[1] * second_weight))
        / denominator
    )
    q_blue = f32(f32(x * basis_d65[1]) + f32(y * basis_a[1]))
    q_red = f32(f32(x * basis_d65[0]) + f32(y * basis_a[0]))
    return np.array(
        [
            fast_exp2(f32(f32(q_red + f32(-0.5)) * f32(4.0))),
            f32(1.0),
            fast_exp2(f32(f32(q_blue + f32(-0.5)) * f32(4.0))),
        ],
        dtype=np.float32,
    )


def load_float_image(raw):
    header = bytes.fromhex(raw["header_raw"])
    origin_x, origin_y, step_x, step_y, width, height = struct.unpack_from(
        "<4f2I", header
    )
    payload = bytes.fromhex(raw["payload"])
    values = np.frombuffer(payload, dtype="<f4").copy()
    assert values.size == width * height
    return {
        "origin_x": f32(origin_x),
        "origin_y": f32(origin_y),
        "step_x": f32(step_x),
        "step_y": f32(step_y),
        "width": width,
        "height": height,
        "values": values,
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def bilinear(table, x_value, y_value):
    """Installed 0x2d4540, including its 0.01 out-of-domain value."""
    x = f32(x_value)
    y = f32(y_value)
    width = table["width"]
    height = table["height"]
    max_x = f32(table["origin_x"] + f32(table["step_x"] * f32(width - 1)))
    max_y = f32(table["origin_y"] + f32(table["step_y"] * f32(height - 1)))
    if x < table["origin_x"] or x > max_x:
        return f32(0.01)
    if y < table["origin_y"] or y > max_y:
        return f32(0.01)

    scaled_x = f32(
        f32(f32(x - table["origin_x"]) * f32(width - 1))
        / f32(table["step_x"] * f32(width - 1))
    )
    scaled_y = f32(
        f32(f32(y - table["origin_y"]) * f32(height - 1))
        / f32(table["step_y"] * f32(height - 1))
    )
    ix = int(np.trunc(scaled_x))
    iy = int(np.trunc(scaled_y))
    fx = f32(min(max(f32(scaled_x - f32(ix)), f32(0.0)), f32(1.0)))
    fy = f32(min(max(f32(scaled_y - f32(iy)), f32(0.0)), f32(1.0)))
    ix1 = min(ix + 1, width - 1)
    iy1 = min(iy + 1, height - 1)
    one_minus_x = f32(abs(f32(1.0) - fx))
    one_minus_y = f32(abs(f32(1.0) - fy))
    values = table["values"]

    # The installed image is x-major: index = x * height + y.
    result = f32(
        f32(0.01)
        + f32(one_minus_x * one_minus_y) * values[ix * height + iy]
    )
    result = f32(
        result + f32(one_minus_x * fy) * values[ix * height + iy1]
    )
    result = f32(
        result + f32(fx * one_minus_y) * values[ix1 * height + iy]
    )
    result = f32(result + f32(fx * fy) * values[ix1 * height + iy1])
    return result


def weighted_centroid(table, points):
    """Installed 0x2d4410 over an Nx2 float32 point vector."""
    weighted_x = f32(0.0)
    weighted_y = f32(0.0)
    total = f32(0.0)
    for x, y in points:
        weight = bilinear(table, x, y)
        weighted_x = f32(weighted_x + f32(weight * f32(x)))
        weighted_y = f32(weighted_y + f32(weight * f32(y)))
        total = f32(total + weight)
    if total < f32(10.0):
        return np.array([-1.0, -1.0], dtype=np.float32), total
    reciprocal = f32(f32(1.0) / total)
    return np.array(
        [f32(weighted_x * reciprocal), f32(weighted_y * reciprocal)],
        dtype=np.float32,
    ), total


def find_solve_call(report):
    for item in report.get("completed", []):
        solve = item.get("stats", {}).get("awb_worker", {}).get("solve_call")
        if solve and solve.get("table1", {}).get("payload"):
            return solve
    raise AssertionError("report has no AWB solve call with table payloads")


def find_points(report):
    for trace in report.get("solver_traces", []):
        point_record = trace.get("solver_points_ready", {}).get("points")
        if point_record and point_record.get("payload"):
            payload = bytes.fromhex(point_record["payload"])
            return np.frombuffer(payload, dtype="<f4").reshape((-1, 2)).copy(), trace
    return None, None


def self_test(table):
    values = table["values"]
    width = table["width"]
    height = table["height"]
    probes = [(0, 0), (0, height - 1), (width - 1, 0), (width - 1, height - 1)]
    for x_index, y_index in probes:
        x = f32(table["origin_x"] + f32(table["step_x"] * f32(x_index)))
        y = f32(table["origin_y"] + f32(table["step_y"] * f32(y_index)))
        actual = bilinear(table, x, y)
        expected = f32(f32(0.01) + values[x_index * height + y_index])
        assert actual.view(np.uint32) == expected.view(np.uint32), (
            x_index,
            y_index,
            actual,
            expected,
        )
    assert bilinear(table, f32(table["origin_x"] - 1), table["origin_y"]) == f32(
        0.01
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("table_report")
    parser.add_argument("--points-report")
    parser.add_argument("--candidate-payload", type=Path)
    args = parser.parse_args()

    report = json.load(open(args.table_report, encoding="ascii"))
    solve = find_solve_call(report)
    tables = {name: load_float_image(solve[name]) for name in ("table1", "table2")}
    for name, table in tables.items():
        assert table["sha256"] == EXPECTED_SHA256[name]
        assert (table["width"], table["height"]) == (40, 40)
        self_test(table)
        print(
            name,
            "sha256=" + table["sha256"],
            "origin=(%.9g,%.9g)" % (table["origin_x"], table["origin_y"]),
            "step=(%.9g,%.9g)" % (table["step_x"], table["step_y"]),
        )

    points_report = report
    if args.points_report:
        points_report = json.load(open(args.points_report, encoding="ascii"))
    candidate_record = None
    for item in report.get("completed", []):
        candidate_record = (
            item.get("stats", {})
            .get("awb_worker", {})
            .get("candidates", {})
            .get("vec4")
        )
        if candidate_record and candidate_record.get("payload"):
            break
    assert candidate_record is not None
    if args.candidate_payload:
        candidate_record = {"payload": args.candidate_payload.read_bytes().hex()}

    points, trace = find_points(points_report)
    if points is None:
        points, basis_a, basis_d65 = generated_points(solve, candidate_record)
        print(
            "generated_points=STATIC_REPLAY",
            "count=" + str(points.shape[0]),
            "basis_a=" + repr(basis_a.tolist()),
            "basis_d65=" + repr(basis_d65.tolist()),
        )
    else:
        _, basis_a, basis_d65 = generated_points(
            solve,
            candidate_record,
        )

    centroids = {}
    for name, table in tables.items():
        result, support = weighted_centroid(table, points)
        centroids[name] = result
        print(name, "centroid", result.tolist(), "support", float(support))
        recorded = (trace or {}).get("solver_table_results", {}).get(name + "_result")
        if recorded:
            expected = np.array(recorded["f32"], dtype=np.float32)
            assert np.array_equal(result.view(np.uint32), expected.view(np.uint32))
    if trace:
        print("solver_table_helpers=PASS points_replay=BIT_EXACT")
        return

    expected = np.array(
        next(
            item["stats"]["awb_worker"]["solve_result"]["f32"][:3]
            for item in report["completed"]
            if item.get("stats", {}).get("awb_worker", {}).get("solve_result")
        ),
        dtype=np.float32,
    )
    best = None
    for scene_weight in np.linspace(0.0, 1.0, 100001, dtype=np.float32):
        actual = combine_centroids(
            tables["table1"], tables["table2"], centroids["table1"],
            centroids["table2"], scene_weight, basis_a, basis_d65
        )
        error = float(np.abs(actual - expected).sum())
        if best is None or error < best[0]:
            best = (error, float(scene_weight), actual)
    print(
        "solver_table_helpers=PASS points_replay=STATIC_PENDING_RUNTIME_CHECK",
        "best_scene_weight=%.8g" % best[1],
        "best_output=" + repr(best[2].tolist()),
        "expected=" + repr(expected.tolist()),
        "l1=%.9g" % best[0],
    )


if __name__ == "__main__":
    main()
