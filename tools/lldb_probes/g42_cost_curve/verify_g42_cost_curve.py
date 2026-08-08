#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import struct
from pathlib import Path

ROOT = Path("/Volumes/Dev/L16_Lumen_ReverseEngineering")
PARSER = argparse.ArgumentParser(description="Replay one retained native G-42 cost curve")
PARSER.add_argument(
    "--run",
    default=str(ROOT / "runs/g42_cost_curve/unit1_28mm"),
    help="retained G-42 capture directory",
)
PARSER.add_argument(
    "--map-run",
    help="optional reference_stage_maps directory for final-winner custody",
)
ARGS = PARSER.parse_args()
RUN = Path(ARGS.run)
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
SKIP_VERIFIER = (
    ROOT
    / "tools/lldb_probes/index5_stereo_residual_policy/verify_skip_mask_policy.py"
)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def f32(value):
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def add(a, b):
    return f32(f32(a) + f32(b))


def mul(a, b):
    return f32(f32(a) * f32(b))


def div(a, b):
    return f32(f32(a) / f32(b))


def pavgb(a, b):
    return (a + b + 1) >> 1


def project(record, u, v, depth, image):
    values = struct.unpack_from("<16f", record, 0)
    columns = [values[index : index + 4] for index in range(0, 16, 4)]
    scale_x, scale_y = struct.unpack_from("<2f", record, 0x48)
    qx = mul(mul(f32(u), depth), scale_x)
    qy = mul(mul(f32(v), depth), scale_y)
    p = []
    for lane in range(4):
        value = mul(depth, columns[2][lane])
        value = add(value, columns[3][lane])
        value = add(value, mul(qx, columns[0][lane]))
        value = add(value, mul(qy, columns[1][lane]))
        p.append(value)
    require(math.isfinite(p[2]) and p[2] != 0.0, "finite projection")
    inverse_z = div(1.0, p[2])
    continuous_x = add(mul(p[0], inverse_z), 0.25)
    continuous_y = add(mul(p[1], inverse_z), 0.25)
    x0, y0 = image["origin"]
    x1, y1 = image["bounds"]
    sampled_x = min(max(continuous_x, f32(x0 + 1)), f32(x1 - 3))
    sampled_y = min(max(continuous_y, f32(y0 + 1)), f32(y1 - 3))
    return {
        "sample": [sampled_x, sampled_y],
        "base": [int(sampled_x), int(sampled_y)],
        "half": [
            int(f32(sampled_x + sampled_x)) & 1,
            int(f32(sampled_y + sampled_y)) & 1,
        ],
    }


def sampled_patch(raw, image, projection):
    width = image["size"][0]
    base_x, base_y = projection["base"]
    half_x, half_y = projection["half"]
    rows = []
    for patch_y in range(3):
        row = []
        for patch_x in range(4):
            x = base_x - 1 + patch_x
            y = base_y - 1 + patch_y
            lanes = []
            for channel in range(4):
                offset = 4 * (y * width + x) + channel
                left = raw[offset]
                if half_y:
                    left = pavgb(left, raw[offset + 4 * width])
                if half_x:
                    right = raw[offset + 4]
                    if half_y:
                        right = pavgb(right, raw[offset + 4 + 4 * width])
                    left = pavgb(left, right)
                lanes.append(left)
            row.extend(lanes)
        rows.append(bytes(row))
    return rows


def source_cost(rows, anchor_rows, cap, weight):
    sums = [0, 0, 0, 0]
    for source_row, anchor_row in zip(rows, anchor_rows):
        for pixel in range(3):
            for channel in range(4):
                index = 4 * pixel + channel
                delta = min(abs(source_row[index] - anchor_row[index]), cap[channel])
                sums[channel] += delta
    scaled = [((weight[c] * sums[c]) + 16) >> 5 for c in range(4)]
    return min(sum(scaled), 65535), sums, scaled


def load_skip_module():
    spec = importlib.util.spec_from_file_location("g42_skip", SKIP_VERIFIER)
    require(spec is not None and spec.loader is not None, "skip verifier import")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


binary = LIBCP.read_bytes()
require(
    sha256(binary) == "b38dc4b354e832024a11ad2718619c09351ca6cc0ce6ee9b2784763926e481e9",
    "installed libcp identity",
)
require(
    sha256(binary[0x2732F0:0x273AC3])
    == "43584a1fab797ad5f8ca4770fc3b2885f95ad93e79f0bcfbda12abaae5155a00",
    "G-42 worker body",
)

report = json.loads((RUN / "report.json").read_text())
require(report["capture_ok"], "runtime packet")
require(len(report["reference_pixel"]) == 2, "reference pixel")
require(report["lower_hypothesis"] >= 0, "lower hypothesis")
require(report["hypothesis_count"] > 0, "hypothesis count")
require(report["lookup_count"] == 752, "lookup count")
require(report["source_count"] == 4, "source count")
require(report["projection_record_count"] == 4, "record count")

expected_hashes = {
    "local_curve.u16le": "039da01dde27ec23e78ab9ef709e0a7fd5a7c308dc76f63e230fb3e0b559f762",
    "lookup.f32le": "e52206cbe601e978e9c211b971d24e233656c35466b504bc7a316dc9a4304b20",
    "projection_records.bin": "04dc9c91346802f3bc1665376e63f3cce82a323c17e985734807dc22ba80f7e9",
    "image0.rgba8": "1deeb4894f0ca6725a6799aa69f734fe089c173edcd49b151bd0b0e31601b119",
    "image1.rgba8": "faf84d46be1b1bde02e5fabc127a3870e5b7ee515c4e14d60a9be93d4bc24290",
    "image2.rgba8": "621fa1e39042fab28c14190ddb6a81168924809d56a0076914681b129bb69e9a",
    "image3.rgba8": "2f186c3e33fadf587e97a7fae6c14683c5d00e30f97d3e6e480a4ce4a0eef715",
    "image4.rgba8": "eb59f13c268929bac7959dbadba86c127fec571e6068ae953510fee7520764b3",
}
artifact_hashes = {
    name: sha256((RUN / name).read_bytes()) for name in expected_hashes
}
if RUN.name == "unit1_28mm":
    require(report["reference_pixel"] == [1035, 780], "active reference pixel")
    require(report["lower_hypothesis"] == 21, "lower hypothesis")
    require(report["hypothesis_count"] == 6, "hypothesis count")
    for name, expected in expected_hashes.items():
        require(artifact_hashes[name] == expected, f"artifact {name}")

curve = struct.unpack(
    "<" + "H" * report["hypothesis_count"],
    (RUN / "local_curve.u16le").read_bytes(),
)
lookup = struct.unpack(
    "<" + "f" * report["lookup_count"],
    (RUN / "lookup.f32le").read_bytes(),
)
records_raw = (RUN / "projection_records.bin").read_bytes()
records = [records_raw[0x50 * i : 0x50 * (i + 1)] for i in range(4)]
images_raw = [(RUN / f"image{i}.rgba8").read_bytes() for i in range(5)]
require(
    all(
        len(raw) == image["size"][0] * image["size"][1] * 4
        for raw, image in zip(images_raw, report["images"])
    ),
    "image sizes",
)

cap = bytes.fromhex(report["cap_hex"])[0:4]
require(cap == bytes((2, 6, 6, 0)), "channel caps")
weights_raw = bytes.fromhex(report["weights_hex"])
weights = [struct.unpack_from("<4H", weights_raw, 8 * i) for i in range(4)]
anchor_rows = [bytes.fromhex(value) for value in report["anchor_rows_hex"]]

u, v = report["reference_pixel"]
anchor = images_raw[0]
anchor_width = report["images"][0]["size"][0]
for row_index, row in enumerate(anchor_rows):
    offset = 4 * ((v - 1 + row_index) * anchor_width + (u - 1))
    require(row[:12] == anchor[offset : offset + 12], "anchor image custody")

per_source = [[] for _ in range(4)]
combined = []
coordinates = []
for local_index in range(report["hypothesis_count"]):
    hypothesis = report["lower_hypothesis"] + local_index
    depth = lookup[hypothesis]
    running = 0
    hypothesis_coordinates = []
    for source_index in range(4):
        projected = project(
            records[source_index], u, v, depth, report["images"][source_index + 1]
        )
        rows = sampled_patch(
            images_raw[source_index + 1],
            report["images"][source_index + 1],
            projected,
        )
        cost, sums, scaled = source_cost(
            rows, anchor_rows, cap, weights[source_index]
        )
        per_source[source_index].append(cost)
        running = (running + cost) & 0xFFFF
        hypothesis_coordinates.append(
            {
                "source": source_index + 1,
                **projected,
                "channel_sums": sums,
                "scaled_channels": scaled,
                "cost": cost,
            }
        )
    combined.append(running)
    coordinates.append(
        {
            "hypothesis": hypothesis,
            "depth_mm": depth,
            "sources": hypothesis_coordinates,
        }
    )

require(tuple(combined) == curve, f"curve replay {combined} != {list(curve)}")
minimum_local = min(range(len(curve)), key=curve.__getitem__)
minimum_hypothesis = report["lower_hypothesis"] + minimum_local
minimum_count = sum(value == curve[minimum_local] for value in curve)
if RUN.name == "unit1_28mm":
    require(minimum_hypothesis == 25, "local G-42 minimum")
    require(minimum_count == 1, "unique local minimum")

skip = load_skip_module()
mask = skip.reproduce_mask(skip.load_task_rectangles())
mask_width = report["images"][0]["size"][0]
require(mask[v * mask_width + u] == 0, "captured pixel is locally evaluated")

map_custody = None
if ARGS.map_run:
    map_run = Path(ARGS.map_run)
    map_report = json.loads((map_run / "report.json").read_text())
    index_item = next(
        item for item in map_report["captures"]
        if item["name"] == "index5_hypothesis_index"
    )
    depth_item = next(
        item for item in map_report["captures"] if item["name"] == "index5_depth"
    )
    require(index_item["descriptor"]["size"] == [mask_width, report["images"][0]["size"][1]], "map dimensions")
    pixel_index = v * mask_width + u
    map_index_raw = (map_run / "index5_hypothesis_index.u16le").read_bytes()
    map_depth_raw = (map_run / "index5_depth.f32le").read_bytes()
    map_custody = {
        "winner_hypothesis": struct.unpack_from("<H", map_index_raw, 2 * pixel_index)[0],
        "depth_mm": struct.unpack_from("<f", map_depth_raw, 4 * pixel_index)[0],
        "index_map_sha256": index_item["sha256"],
        "depth_map_sha256": depth_item["sha256"],
    }

analysis = {
    "reference_pixel": [u, v],
    "reference_pixel_skip_mask": 0,
    "hypotheses": list(
        range(
            report["lower_hypothesis"],
            report["lower_hypothesis"] + report["hypothesis_count"],
        )
    ),
    "depth_mm": [
        lookup[index]
        for index in range(
            report["lower_hypothesis"],
            report["lower_hypothesis"] + report["hypothesis_count"],
        )
    ],
    "captured_curve": list(curve),
    "replayed_curve": combined,
    "per_source_curves": per_source,
    "local_argmin_hypothesis": minimum_hypothesis,
    "local_argmin_is_unique": minimum_count == 1,
    "artifact_sha256": artifact_hashes,
    "final_map_custody": map_custody,
    "coordinates_and_costs": coordinates,
}
(RUN / "analysis.json").write_text(
    json.dumps(analysis, indent=2, sort_keys=True) + "\n", encoding="ascii"
)

print(f"PASS G-42 same-call combined curve: {combined}")
print(f"PASS G-42 per-source curves: {per_source}")
print(
    "PASS G-42 local argmin: "
    f"h={minimum_hypothesis} unique={minimum_count == 1}"
)
print(f"PASS skip policy: capture ({u},{v})=0")
if map_custody:
    print(
        "PASS final-map custody: "
        f"h={map_custody['winner_hypothesis']} "
        f"depth_mm={map_custody['depth_mm']}"
    )
