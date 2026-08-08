#!/usr/bin/env python3
"""Verify the selected Bayer cross-talk amount from public RAW and libcp tables."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import struct
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
STATIC_PATH = (
    ROOT
    / "tools/lldb_probes/index5_public_field_names"
    / "verify_index5_public_field_names.py"
)
RAW_PATH = ROOT / "tools/lldb_probes/raw_sensor_layout/verify_raw_sensor_layout.py"
LIBCP_SHA256 = "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9"
WIDTH = 4160
HEIGHT = 3120
FIT_WIDTH = 17
FIT_HEIGHT = 13
TABLE_BYTES = FIT_WIDTH * FIT_HEIGHT * 16

DEFAULT_RUNS = (
    (
        ROOT / "runs/correction_liveness/amount_fit_unit1_28mm_a1",
        Path("/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"),
        0,
    ),
    (
        ROOT / "runs/correction_liveness/amount_fit_unit1_28mm_b2_direct",
        Path("/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri"),
        6,
    ),
    (
        ROOT / "runs/correction_liveness/amount_fit_unit2_28mm_a1",
        Path("/Volumes/Base Photos/Light/2018-07-04/L16_02130.lri"),
        0,
    ),
)

BODY_HASHES = {
    (0xF4170, 0xF4D27): "7614080616e7b92f5e181a71e94811ade3b10a5e17123ff131b54f1626b7d7fa",
    (0xFCD90, 0xFCF90): "cc220a22f58909bd5a0221dec1245da707f299c0738aa990e491edcf462199c9",
    (0xFCF90, 0xFD940): "82091fc6cf17274813eac525c8b488d52a4e1e7b7fabf9285ee9ba6cd4158fc1",
    (0xFD940, 0xFE019): "63d7435837dca672db39fa139878c86b3d8c98fbfc6ee517ce0a40b51c862f95",
    (0xFE1B0, 0xFE2E6): "18367c18f15562f275847cbae791adf07a8ceee7de983c5865a1e5425d24ff58",
    (0xFE2F0, 0xFE429): "a2c63f7d7855b56c0b2a06d8278c7c18a0307deb1fed684ae92e0b9bef189e4b",
    (0xFE430, 0xFE569): "cc24735351b5e94539714187a5f2e14b7ab04a74717fba5e53c12f0f3a88530a",
    (0x102AB0, 0x102E91): "963ce5cc171524091499778ead50a7b4b169224381b0f33984766fd25432d030",
    (0x351760, 0x351A23): "d2c76ddc141c24f77ccbf3e9a9de706d8468b70b8e7d80dcdb546f2129513bac",
    (0x351BA0, 0x351C6A): "371bc4f3241f15e62e2265373a7c494964de5dce622cd2deb11eb29f72c1fad9",
}

TABLES = {
    "A_true": (0x5B0540, (
        "2a1637770b1ee36fa8a07823f82c68c9f775f146e750159a82097ba2d12eb8c1",
        "4ed615b18aa8510d31ebf2eabbba3920b17bce51fe9bb336a0a5c59ab52836e2",
        "3a3ad347cc7649eb981bc2f9f9521879d66d266c7d3c5dd5179ce51f658d78a4",
    )),
    "A_false": (0x5B2EB0, (
        "1079288f1c03f593bab826ce01001461b298175f36464425e36fd28794c7f86b",
        "8a5d0313ceb19940c004607406611729c9d4355421c10200a2e82641071d859c",
        "f98a07a18514b3637fa48bd645465ed9238a4a087f2bb42bd4e2741966901576",
    )),
    "B_true": (0x5B65F0, (
        "dbc4d5e935a1cae7694414140a921426eeca8646a37fe12ed5bc6aab8a10b129",
        "89b3425d1e8c962ba337bda076516cea9d4c3af4cc14a05f52ad103ca8949f30",
        "476e14f2a2e6f7b4bd310e61932c98f6f5d30bad9fa68261a6691c31e807c025",
    )),
    "B_false": (0x5B8F60, (
        "b3c48764e4298bf387ff1bc9688cb445659fccf9e5518b42f0d34044b199ecb7",
        "be74d9d3b5f24b0b37adfab4a08a2960edd1ab778d0f72fa520bb49754dfe261",
        "34b58764e5893218fc52fbe7409a9c0814f1172d85f39cf511f8f4021bfcd5fa",
    )),
    "C_true": (0x5BC6A0, (
        "6e8d49b68bf983317fdb3b613a99b059b6b5c14dc9b6a92e1496c35f61e67ffe",
        "346d0350bd0acc4fdbdbd01b29105026c46824360520e1c177f1a3fd540160c2",
        "e2fe7b0aac5fa407834f94336bbf277cdcb321f76cba2254ab7148c35ee38a6c",
    )),
    "C_false": (0x5BF010, (
        "6745d332c0f6b00c224a39a19ef40d665b5381c97e4b4bdd15d26373125aa800",
        "620b0e52f840167c874c3164ea8c81eb8dc724d8c4b6a720ed55029975d8579d",
        "8cf061eec1ccfb42834b3acb99f6db448839607e966feba59fd8e66f7eb9f9ed",
    )),
}

SENSOR4_TABLES = {
    "A": (0x5AF770, "fec3116bad2c7102ca42bfc38beb0fc136492c8ed235a3facb7b8b55c281f765"),
    "B": (0x5B5820, "e85f77aed89a03571a8a458ff849c0ea514f1b576019eee03f7debd5f87b5425"),
    "C": (0x5BB8D0, "4a4ae1bded16a5c1bf8c2f8daa522795d04fee228679b93ee18d6e350b2a7e45"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


STATIC = load_module("crosstalk_amount_static", STATIC_PATH)
RAW = load_module("crosstalk_amount_raw", RAW_PATH)


def f32(value):
    return np.asarray(value, dtype=np.float32)


def bits(value) -> int:
    return struct.unpack("<I", struct.pack("<f", float(value)))[0]


def same_f32(actual, expected) -> bool:
    return bits(actual) == bits(expected)


def verify_static() -> tuple[bytes, list[tuple[int, int]]]:
    data = STATIC.LIBCP.read_bytes()
    require(hashlib.sha256(data).hexdigest() == LIBCP_SHA256, "libcp SHA-256 drift")
    mapping = STATIC.segments(data)
    for (start, end), expected in BODY_HASHES.items():
        body = STATIC.bytes_at(data, mapping, start, end - start)
        require(hashlib.sha256(body).hexdigest() == expected, f"body 0x{start:x} drift")
    for name, (base, hashes) in TABLES.items():
        for group, expected in enumerate(hashes):
            table = STATIC.bytes_at(data, mapping, base + group * TABLE_BYTES, TABLE_BYTES)
            require(hashlib.sha256(table).hexdigest() == expected, f"{name}[{group}] drift")
    for name, (address, expected) in SENSOR4_TABLES.items():
        table = STATIC.bytes_at(data, mapping, address, TABLE_BYTES)
        require(hashlib.sha256(table).hexdigest() == expected, f"{name}_sensor4 drift")
    constants = {
        0x5AF2D8: 1_000_000_000.0,
        0x5AF2DC: np.float32(1.0 / 19.0),
        0x5AF2E0: 6_504_070.0,
        0x5AF2E4: 3_000.0,
        0x5AF2E8: 5_000.0,
        0x5AF2EC: 2_504_070.0,
        0x5A886C: 0.5,
    }
    for address, expected in constants.items():
        actual = struct.unpack("<f", STATIC.bytes_at(data, mapping, address, 4))[0]
        require(same_f32(actual, expected), f"constant 0x{address:x}: {actual}")
    return data, mapping


def module_fields(message: bytes, number: int, wire_type: int) -> list[bytes]:
    return [value for observed, value in RAW.fields(message).get(number, []) if observed == wire_type]


def public_raw(path: Path, camera_key: int) -> np.ndarray:
    matches = []
    for block in RAW.lri.scan_lri_blocks(str(path)):
        for module in module_fields(block["payload"], 12, 2):
            if RAW.one(module, 2, 0) != camera_key:
                continue
            surface = RAW.one(module, 9, 2)
            size = RAW.one(surface, 2, 2)
            matches.append((
                block,
                RAW.one(size, 1, 0),
                RAW.one(size, 2, 0),
                RAW.one(surface, 4, 0),
                RAW.one(surface, 5, 0),
            ))
    require(len(matches) == 1, f"{path}: camera {camera_key} RAW matches={len(matches)}")
    block, width, height, stride, data_offset = matches[0]
    require((width, height, stride) == (WIDTH, HEIGHT, WIDTH * 5 // 4), "RAW layout")
    with path.open("rb") as handle:
        handle.seek(block["block_offset"] + data_offset)
        packed = handle.read(stride * height)
    require(len(packed) == stride * height, f"{path}: truncated RAW")
    source = np.frombuffer(packed, dtype=np.uint8).reshape(height, stride // 5, 5)
    words = source.astype(np.uint16)
    output = np.empty((height, width), dtype=np.uint16)
    output[:, 0::4] = words[:, :, 0] | ((words[:, :, 1] & 0x03) << 8)
    output[:, 1::4] = (words[:, :, 1] >> 2) | ((words[:, :, 2] & 0x0F) << 6)
    output[:, 2::4] = (words[:, :, 2] >> 4) | ((words[:, :, 3] & 0x3F) << 4)
    output[:, 3::4] = (words[:, :, 3] >> 6) | (words[:, :, 4] << 2)
    return output


def ratio_maps(raw: np.ndarray, red_x: int, red_y: int) -> tuple[np.ndarray, np.ndarray]:
    red = raw[red_y::2, red_x::2]
    blue = raw[1 - red_y::2, 1 - red_x::2]
    green_horizontal = raw[red_y::2, 1 - red_x::2]
    green_vertical = raw[1 - red_y::2, red_x::2]
    green_sum = f32(f32(green_horizontal) + f32(green_vertical))
    green_average = f32(green_sum * np.float32(0.5))
    reciprocal = f32(np.float32(1.0) / green_average)
    return f32(f32(red) * reciprocal), f32(f32(blue) * reciprocal)


def sequential_sum(values: np.ndarray):
    accumulator = np.float32(0.0)
    for value in values:
        accumulator = np.float32(accumulator + value)
    return accumulator


def fit_lanes(red_ratio: np.ndarray, blue_ratio: np.ndarray) -> np.ndarray:
    ar_x = np.zeros_like(red_ratio)
    ar_y = np.zeros_like(red_ratio)
    ab_x = np.zeros_like(blue_ratio)
    ab_y = np.zeros_like(blue_ratio)
    ar_x[1:, 1:] = f32(red_ratio[1:, 1:] - red_ratio[1:, :-1])
    ar_y[1:, 1:] = f32(red_ratio[1:, 1:] - red_ratio[:-1, 1:])
    ab_x[1:, 1:] = f32(blue_ratio[1:, 1:] - blue_ratio[1:, :-1])
    ab_y[1:, 1:] = f32(blue_ratio[1:, 1:] - blue_ratio[:-1, 1:])

    red_energy = f32(f32(ar_x * ar_x) + f32(ar_y * ar_y))
    blue_x_energy = f32(ab_x * ab_x)
    blue_y_energy = f32(ab_y * ab_y)
    blue_energy = f32(blue_x_energy + blue_y_energy)
    total = f32(f32(red_energy + blue_x_energy) + blue_y_energy)
    accepted = total <= np.float32(0.02)
    red_mask = accepted & (np.sqrt(red_energy, dtype=np.float32) > np.float32(0.0))
    blue_mask = accepted & (np.sqrt(blue_energy, dtype=np.float32) > np.float32(0.0))

    output = np.ones((FIT_HEIGHT, FIT_WIDTH, 4), dtype=np.float32)
    scale_x = np.float32(red_ratio.shape[1] / np.float32(FIT_WIDTH))
    scale_y = np.float32(red_ratio.shape[0] / np.float32(FIT_HEIGHT))
    for y in range(FIT_HEIGHT):
        y0 = int(np.trunc(np.float32(y) * scale_y))
        y1 = int(np.trunc(np.float32(y + 1) * scale_y))
        for x in range(FIT_WIDTH):
            x0 = int(np.trunc(np.float32(x) * scale_x))
            x1 = int(np.trunc(np.float32(x + 1) * scale_x))
            for lane, image, mask in (
                (0, red_ratio, red_mask),
                (2, blue_ratio, blue_mask),
            ):
                values = image[y0:y1, x0:x1][mask[y0:y1, x0:x1]].ravel()
                if values.size:
                    output[y, x, lane] = np.float32(
                        sequential_sum(values) / np.float32(values.size)
                    )
    return output


def group_for_camera(camera_key: int) -> int:
    require(0 <= camera_key <= 15, f"camera key {camera_key}")
    return 0 if camera_key <= 4 else (1 if camera_key <= 9 else 2)


def table(data: bytes, mapping, letter: str, sensor: int, variant: bool, group: int):
    if sensor == 4:
        address = SENSOR4_TABLES[letter][0]
    else:
        require(sensor in (1, 2), f"unsupported sensor selector {sensor}")
        address = TABLES[f"{letter}_{str(variant).lower()}"][0] + group * TABLE_BYTES
    raw = STATIC.bytes_at(data, mapping, address, TABLE_BYTES)
    return np.frombuffer(raw, dtype="<f4").reshape(FIT_HEIGHT * FIT_WIDTH, 4)


def score(candidate: np.ndarray, fit: np.ndarray):
    product = f32(candidate * fit.reshape(-1, 4))
    total = np.zeros(4, dtype=np.float32)
    for pixel in product:
        total = f32(total + pixel)
    mean = f32(total / np.float32(product.shape[0]))
    squared = np.zeros(4, dtype=np.float32)
    for pixel in product:
        delta = f32(mean - pixel)
        squared = f32(squared + f32(delta * delta))
    variance = f32(squared / np.float32(product.shape[0]))
    return np.float32(variance[0] + variance[2])


def verify_histograms(run_dir: Path, report: dict, raw: np.ndarray) -> dict | None:
    producer = report["producer"]
    outer = producer.get("histograms_0x1d8")
    if not isinstance(outer, dict) or "vectors" not in outer:
        return None
    red_x, red_y = producer["bayer_override_0x58"]
    phases = (
        (red_x, red_y),
        (1 - red_x, red_y),
        (red_x, 1 - red_y),
        (1 - red_x, 1 - red_y),
    )
    require(outer["count"] == 4 and len(outer["vectors"]) == 4, "histogram outer vector")
    histograms = []
    for index, (x, y) in enumerate(phases):
        expected = np.bincount(raw[y::8, x::8].ravel(), minlength=1024).astype(np.uint64)
        observed = np.fromfile(run_dir / f"histogram_{index}_u64.bin", dtype="<u8")
        require(np.array_equal(expected, observed), f"{run_dir.name}: histogram {index}")
        histograms.append(observed)

    selected = histograms[1]
    cumulative = np.cumsum(selected, dtype=np.uint64)
    target = np.float32(np.float32(cumulative[-1]) * np.float32(0.5))
    median_bin = int(np.argmax(cumulative >= int(target)))
    black, white = producer["black_white_0xac"]
    normalized = np.float32(
        np.float32(np.float32(median_bin) - np.float32(black))
        / np.float32(np.float32(white) - np.float32(black))
    )
    gain = np.float32(producer["sensor_analog_gain_0x40_f32"][0])
    exposure = np.float32(producer["sensor_exposure_0x38_u64"])
    energy = np.float32(np.float32(normalized * gain) * exposure)
    live = producer["fit_exposure_energy_xmm1"][0]
    require(same_f32(energy, live), f"{run_dir.name}: exposure energy {energy} != {live}")
    return {
        "histogram_samples_each": int(selected.sum()),
        "selected_histogram": 1,
        "median_bin": median_bin,
        "normalized_median": float(normalized),
        "exposure_energy": float(energy),
    }


def verify_run(run_dir: Path, source_lri: Path, camera_key: int, data: bytes, mapping) -> dict:
    report = json.loads((run_dir / "report.json").read_text(encoding="ascii"))
    require(report["complete"] and not report["errors"], f"{run_dir}: incomplete capture")
    require(report["desired_camera_id"] == camera_key, f"{run_dir}: camera key")
    producer = report["producer"]
    fit_report = report["fit"]
    red_x, red_y = producer["bayer_override_0x58"]
    raw = public_raw(source_lri, camera_key)
    red_ratio, blue_ratio = ratio_maps(raw, red_x, red_y)

    observed_red = np.fromfile(run_dir / "fit_numerator_f32.bin", dtype="<f4").reshape(1560, 2080)
    observed_blue = np.fromfile(run_dir / "fit_denominator_f32.bin", dtype="<f4").reshape(1560, 2080)
    require(np.array_equal(red_ratio.view("<u4"), observed_red.view("<u4")), f"{run_dir.name}: red ratio")
    require(np.array_equal(blue_ratio.view("<u4"), observed_blue.view("<u4")), f"{run_dir.name}: blue ratio")

    rebuilt_fit = fit_lanes(red_ratio, blue_ratio)
    observed_fit = np.fromfile(run_dir / "fit_input_vec4_f32.bin", dtype="<f4").reshape(13, 17, 4)
    for lane in (0, 2):
        require(
            np.array_equal(rebuilt_fit[:, :, lane].view("<u4"), observed_fit[:, :, lane].view("<u4")),
            f"{run_dir.name}: fit lane {lane}",
        )

    sensor = fit_report["sensor_type"]
    variant = bool(fit_report["variant_flag"])
    group = group_for_camera(camera_key)
    table_a = table(data, mapping, "A", sensor, variant, group)
    table_b = table(data, mapping, "B", sensor, variant, group)
    scores = []
    amounts = []
    best = np.float32(1_000_000_000.0)
    selected = np.float32(0.0)
    for index, packet in enumerate(fit_report["candidates"]):
        amount = np.float32(np.float32(index) * np.float32(1.0 / 19.0))
        candidate = f32(
            f32(table_a * amount)
            + f32(table_b * np.float32(np.float32(1.0) - amount))
        )
        value = score(candidate, observed_fit)
        if value < best:
            best = value
            selected = amount
        require(packet["index"] == index, f"{run_dir.name}: candidate index")
        require(same_f32(packet["amount"], amount), f"{run_dir.name}: amount {index}")
        require(same_f32(packet["score"], value), f"{run_dir.name}: score {index}")
        require(same_f32(packet["best_after"], best), f"{run_dir.name}: best {index}")
        require(same_f32(packet["selected_after"], selected), f"{run_dir.name}: selected {index}")
        scores.append(float(value))
        amounts.append(float(amount))

    cct = np.float32(fit_report["cct_xmm0"][0])
    exposure_energy = np.float32(fit_report["exposure_energy_xmm1"][0])
    c_gate = (
        exposure_energy < np.float32(6_504_070.0)
        and cct >= np.float32(3_000.0)
        and cct < np.float32(5_000.0)
        and exposure_energy >= np.float32(2_504_070.0)
    )
    require((fit_report["c_table"] is not None) == c_gate, f"{run_dir.name}: C gate")
    c_score = None
    if c_gate:
        c_score = score(table(data, mapping, "C", sensor, variant, group), observed_fit)
        packet = fit_report["c_table"]
        require(same_f32(packet["score"], c_score), f"{run_dir.name}: C score")
        require(same_f32(packet["best_ab_score"], best), f"{run_dir.name}: C best A/B")
        if c_score < best:
            selected = np.float32(-1.0)
            best = c_score

    require(same_f32(fit_report["return_xmm0"][0], selected), f"{run_dir.name}: return")
    require(same_f32(producer["stored_amount_xmm0"][0], selected), f"{run_dir.name}: stored amount")
    histogram = verify_histograms(run_dir, report, raw)
    return {
        "run": run_dir.name,
        "source_lri": str(source_lri),
        "camera_key": camera_key,
        "bayer_red": [red_x, red_y],
        "ratio_samples_exact": int(red_ratio.size * 2),
        "fit_lane_samples_exact": FIT_WIDTH * FIT_HEIGHT * 2,
        "candidate_scores_exact": len(scores),
        "selected_index": amounts.index(float(selected)) if selected >= 0 else -1,
        "selected_amount": float(selected),
        "best_score": float(best),
        "c_gate": bool(c_gate),
        "c_score": float(c_score) if c_score is not None else None,
        "histogram": histogram,
        "ignored_fit_lanes": [1, 3],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="append", nargs=3, metavar=("DIR", "LRI", "CAMERA_KEY"))
    args = parser.parse_args()
    data, mapping = verify_static()
    runs = (
        tuple((Path(directory), Path(lri), int(key)) for directory, lri, key in args.run)
        if args.run
        else DEFAULT_RUNS
    )
    print(f"crosstalk_amount_static=OK libcp={LIBCP_SHA256} bodies={len(BODY_HASHES)} tables=21")
    for run_dir, source_lri, camera_key in runs:
        print("crosstalk_amount=OK " + json.dumps(
            verify_run(run_dir, source_lri, camera_key, data, mapping), sort_keys=True
        ))


if __name__ == "__main__":
    main()
