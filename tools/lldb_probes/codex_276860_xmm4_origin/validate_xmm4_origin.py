#!/usr/bin/env python3
import json
import math
import pathlib
import struct


ROOT = pathlib.Path("runs/codex_276860_xmm4_origin")
TIERS = ("28mm", "35mm", "70mm", "150mm")
LRI_PATHS = {
    "28mm": "/Volumes/Base Photos/Light/2018-07-23/L16_02130.lri",
    "35mm": "/Volumes/Base Photos/Light/2018-12-26/L16_03041.lri",
    "70mm": "/Volumes/Base Photos/Light/2019-05-18/L16_03434.lri",
    "150mm": "/Volumes/Base Photos/Light/2018-07-29/L16_02285.lri",
}
REQUIRED_TARGET_COUNTS = {
    "caller_pre_29a140": 1,
    "maker_after_299fd0": 1,
}
STEP_KEYS = (
    "after_subps_27787e",
    "after_mulps_277889",
    "after_andps_27788d",
    "after_blendps_277894",
    "after_pair_sum_2778a9",
    "after_xorps_2778ad",
    "after_broadcast_2778b1",
    "after_minss_2778b6",
    "after_maxss_2778bb",
    "after_floor_i32_2778cb",
    "after_fraction_2778d2",
    "after_polynomial_2778fa",
    "after_exponent_shift_2778ff",
    "xmm4_ready_277903",
)


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def scan_lri_blocks(path):
    blocks = []
    lri = pathlib.Path(path)
    with lri.open("rb") as handle:
        offset = 0
        index = 0
        file_size = lri.stat().st_size
        while offset < file_size:
            handle.seek(offset)
            header = handle.read(32)
            if len(header) < 32 or header[:4] != b"LELR":
                break
            total_len = struct.unpack_from("<Q", header, 4)[0]
            msg_offset = struct.unpack_from("<Q", header, 12)[0]
            msg_len = struct.unpack_from("<I", header, 20)[0]
            if total_len == 0:
                break
            handle.seek(offset + msg_offset)
            payload = handle.read(msg_len)
            blocks.append({"index": index, "payload_size": msg_len, "payload": payload})
            offset += total_len
            index += 1
    return blocks


def tier_from_path(path):
    name = path.name
    require(name.startswith("xmm4_origin_") and name.endswith(".json"), f"bad report name {name}")
    return name[len("xmm4_origin_") : -len(".json")]


def f32(value):
    return struct.unpack("<f", struct.pack("<f", float(value)))[0]


def f32_bits(value):
    return struct.unpack("<I", struct.pack("<f", f32(value)))[0]


def bits_f32(value):
    return struct.unpack("<f", struct.pack("<I", value & 0xFFFFFFFF))[0]


def signed32(value):
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def cvtt_i32(value):
    if math.isnan(value):
        return 0x80000000
    truncated = int(value)
    if truncated < -(2**31) or truncated > (2**31 - 1):
        return 0x80000000
    return truncated & 0xFFFFFFFF


def hex_u32_lanes(hex_string):
    data = bytes.fromhex(hex_string)
    require(len(data) == 16, f"expected 16 bytes, got {len(data)}")
    return list(struct.unpack("<IIII", data))


def hex_f32_lanes(hex_string):
    data = bytes.fromhex(hex_string)
    require(len(data) == 16, f"expected 16 bytes, got {len(data)}")
    return list(struct.unpack("<ffff", data))


def lanes_hex(lanes):
    return struct.pack("<IIII", *[lane & 0xFFFFFFFF for lane in lanes]).hex()


def f32_lanes_hex(lanes):
    return lanes_hex([f32_bits(value) for value in lanes])


def xmm(sample, reg):
    return sample["xmm_hex"][reg]


def xmm_u32(sample, reg):
    return hex_u32_lanes(xmm(sample, reg))


def xmm_f32(sample, reg):
    return hex_f32_lanes(xmm(sample, reg))


def assert_hex(actual, expected, label):
    require(actual == expected, f"{label}: expected {expected}, got {actual}")


def assert_low_hex(actual_lanes, expected_lanes, label):
    require(
        (actual_lanes[0] & 0xFFFFFFFF) == (expected_lanes[0] & 0xFFFFFFFF),
        f"{label}: expected low {expected_lanes[0]:08x}, got {actual_lanes[0]:08x}",
    )


def validate_object_scale_lri_absence(tier, scale_hex):
    scale_bytes = bytes.fromhex(scale_hex)
    nonzero_words = [
        scale_bytes[offset : offset + 4]
        for offset in range(0, len(scale_bytes), 4)
        if scale_bytes[offset : offset + 4] != b"\x00\x00\x00\x00"
    ]
    blocks = scan_lri_blocks(LRI_PATHS[tier])
    full_hits = [
        (block["index"], block["payload_size"])
        for block in blocks
        if block["payload"].find(scale_bytes) >= 0
    ]
    scalar_hits = []
    for word_index, word in enumerate(nonzero_words):
        for block in blocks:
            if block["payload"].find(word) >= 0:
                scalar_hits.append((word_index, block["index"], block["payload_size"]))
    require(not full_hits, f"{tier}: object+0x60 full vector found in LRI payloads {full_hits}")
    require(not scalar_hits, f"{tier}: object+0x60 nonzero scalar found in LRI payloads {scalar_hits[:8]}")
    return {"full_hits": 0, "nonzero_scalar_hits": 0, "nonzero_scalar_count": len(nonzero_words)}


def minss_lanes(a_bits, b_bits):
    out = list(a_bits)
    a = bits_f32(a_bits[0])
    b = bits_f32(b_bits[0])
    out[0] = f32_bits(b if math.isnan(a) or math.isnan(b) else min(a, b))
    return out


def maxss_lanes(a_bits, b_bits):
    out = list(a_bits)
    a = bits_f32(a_bits[0])
    b = bits_f32(b_bits[0])
    out[0] = f32_bits(b if math.isnan(a) or math.isnan(b) else max(a, b))
    return out


def validate_packet(path):
    tier = tier_from_path(path)
    packet = json.loads(path.read_text())
    require(packet.get("capture_complete") is True, f"{path.name}: capture not complete")
    require(packet.get("terminated_after_capture") is True, f"{path.name}: not terminated")
    require(not packet.get("step_hit_cap"), f"{path.name}: step cap")
    require(not packet.get("errors"), f"{path.name}: errors {packet.get('errors')}")
    process = packet.get("process", {})
    require(process.get("valid") is True, f"{path.name}: invalid process packet")
    for site, expected in REQUIRED_TARGET_COUNTS.items():
        require(
            packet.get("target_counts", {}).get(site) == expected,
            f"{path.name}: target count {site}={packet.get('target_counts', {}).get(site)}",
        )

    samples = packet.get("packet", {})
    table = samples.get("table")
    require(table, f"{path.name}: missing table sample")
    for key in STEP_KEYS:
        require(samples.get(key), f"{path.name}: missing {key}")

    for key in STEP_KEYS:
        sample = samples[key]
        require(
            table.get("thread_id") == sample.get("thread_id"),
            f"{path.name}: thread mismatch {key}",
        )
        for reg in ("rbp", "r9"):
            require(
                table["registers"].get(reg) == sample["registers"].get(reg),
                f"{path.name}: {reg} mismatch {key}",
            )

    require(table.get("site_va") == 0x27786B, f"{path.name}: table site")
    require(samples["xmm4_ready_277903"].get("site_va") == 0x277903, f"{path.name}: final site")
    require(
        table.get("target_stack_context", {}).get("object_from_stack_rbp_minus_0x1c8")
        == table.get("target_object"),
        f"{path.name}: target object mismatch",
    )
    require(
        table.get("target_stack_context", {}).get("record_lookup_from_r9", {}).get("record_index")
        is not None,
        f"{path.name}: r9 record lookup",
    )
    require(
        table.get("table_load", {}).get("stack_minus_0x210_eq_table_base") is True,
        f"{path.name}: table base",
    )

    inputs = table["xmm4_inputs"]
    scale_absence = validate_object_scale_lri_absence(tier, inputs["object_plus_0x60_hex"])
    source_vec = hex_f32_lanes(inputs["vector16_hex"])
    object_scale = hex_f32_lanes(inputs["object_plus_0x60_hex"])
    xmm8 = hex_f32_lanes(table["xmm_hex"]["xmm8"])
    xmm10_bits = hex_u32_lanes(table["xmm_hex"]["xmm10"])
    xmm11_bits = hex_u32_lanes(table["xmm_hex"]["xmm11"])
    xmm12_bits = hex_u32_lanes(table["xmm_hex"]["xmm12"])
    xmm13_bits = hex_u32_lanes(table["xmm_hex"]["xmm13"])
    xmm14_bits = hex_u32_lanes(table["xmm_hex"]["xmm14"])
    xmm15_low = hex_f32_lanes(table["xmm_hex"]["xmm15"])[0]

    after_sub = [f32(f32(xmm8[i]) - f32(source_vec[i])) for i in range(4)]
    assert_hex(
        xmm(samples["after_subps_27787e"], "xmm2"),
        f32_lanes_hex(after_sub),
        f"{path.name}: after subps",
    )

    after_mul = [f32(f32(after_sub[i]) * f32(object_scale[i])) for i in range(4)]
    assert_hex(
        xmm(samples["after_mulps_277889"], "xmm2"),
        f32_lanes_hex(after_mul),
        f"{path.name}: after mulps",
    )

    after_and = [f32_bits(after_mul[i]) & xmm10_bits[i] for i in range(4)]
    assert_hex(
        xmm(samples["after_andps_27788d"], "xmm2"),
        lanes_hex(after_and),
        f"{path.name}: after andps",
    )

    after_blend = list(after_and)
    after_blend[3] = xmm11_bits[3]
    assert_hex(
        xmm(samples["after_blendps_277894"], "xmm2"),
        lanes_hex(after_blend),
        f"{path.name}: after blendps",
    )

    blend_f = [bits_f32(v) for v in after_blend]
    tmp3 = [blend_f[2], blend_f[3], blend_f[0], blend_f[1]]
    tmp3 = [f32(f32(tmp3[i]) + f32(blend_f[i])) for i in range(4)]
    tmp2_shuf = [tmp3[1], tmp3[0], tmp3[3], tmp3[2]]
    after_sum = [f32(f32(tmp2_shuf[i]) + f32(tmp3[i])) for i in range(4)]
    assert_hex(
        xmm(samples["after_pair_sum_2778a9"], "xmm2"),
        f32_lanes_hex(after_sum),
        f"{path.name}: after pair sum",
    )

    after_xor = [f32_bits(after_sum[i]) ^ xmm12_bits[i] for i in range(4)]
    assert_hex(
        xmm(samples["after_xorps_2778ad"], "xmm2"),
        lanes_hex(after_xor),
        f"{path.name}: after xorps",
    )

    after_broadcast = [after_xor[0]] * 4
    assert_hex(
        xmm(samples["after_broadcast_2778b1"], "xmm2"),
        lanes_hex(after_broadcast),
        f"{path.name}: after broadcast",
    )

    after_min = minss_lanes(after_broadcast, xmm13_bits)
    assert_hex(
        xmm(samples["after_minss_2778b6"], "xmm2"),
        lanes_hex(after_min),
        f"{path.name}: after minss",
    )

    after_max = maxss_lanes(after_min, xmm14_bits)
    assert_hex(
        xmm(samples["after_maxss_2778bb"], "xmm2"),
        lanes_hex(after_max),
        f"{path.name}: after maxss",
    )

    trunc = [cvtt_i32(bits_f32(v)) for v in after_max]
    signmask = [0xFFFFFFFF if (v & 0x80000000) else 0 for v in after_max]
    floorish = [(signmask[i] + trunc[i]) & 0xFFFFFFFF for i in range(4)]
    assert_hex(
        xmm(samples["after_floor_i32_2778cb"], "xmm4"),
        lanes_hex(floorish),
        f"{path.name}: after floor i32",
    )

    floor_as_f32 = [f32(signed32(v)) for v in floorish]
    after_fraction = list(after_max)
    after_fraction[0] = f32_bits(f32(bits_f32(after_max[0]) - floor_as_f32[0]))
    assert_hex(
        xmm(samples["after_fraction_2778d2"], "xmm2"),
        lanes_hex(after_fraction),
        f"{path.name}: after fraction",
    )

    c1, c2, c3 = (
        f32(inputs["poly_const_add1_0x5dae30"]),
        f32(inputs["poly_const_add2_0x5dae34"]),
        f32(inputs["poly_const_add3_0x5dae38"]),
    )
    frac = bits_f32(after_fraction[0])
    poly = f32(f32(frac) * f32(xmm15_low))
    poly = f32(f32(poly) + c1)
    poly = f32(f32(poly) * f32(frac))
    poly = f32(f32(poly) + c2)
    poly = f32(f32(poly) * f32(frac))
    poly = f32(f32(poly) + c3)
    expected_poly_lanes = list(after_fraction)
    expected_poly_lanes[0] = f32_bits(poly)
    actual_poly = xmm_u32(samples["after_polynomial_2778fa"], "xmm3")
    assert_low_hex(actual_poly, expected_poly_lanes, f"{path.name}: after polynomial")

    shifted = [(v << 23) & 0xFFFFFFFF for v in floorish]
    assert_hex(
        xmm(samples["after_exponent_shift_2778ff"], "xmm4"),
        lanes_hex(shifted),
        f"{path.name}: after exponent shift",
    )

    final = [(shifted[i] + expected_poly_lanes[i]) & 0xFFFFFFFF for i in range(4)]
    actual_final = xmm_u32(samples["xmm4_ready_277903"], "xmm4")
    assert_low_hex(actual_final, final, f"{path.name}: final xmm4")

    xmm4_low = bits_f32(actual_final[0])
    require(0.0 < xmm4_low < 2.0, f"{path.name}: unexpected xmm4 low {xmm4_low}")
    return {
        "packet": packet,
        "clamped_scalar": bits_f32(after_max[0]),
        "fraction": frac,
        "floor_i32": signed32(floorish[0]),
        "poly": poly,
        "xmm4_low": xmm4_low,
        "table": table["table_load"]["table_value_u16"],
        "scale_lri_absence": scale_absence,
    }


def main():
    for tier in TIERS:
        path = ROOT / f"xmm4_origin_{tier}.json"
        require(path.exists(), f"missing report {path}")
        result = validate_packet(path)
        print(
            f"{path.name}: OK table={result['table']} "
            f"clamped={result['clamped_scalar']:.6f} "
            f"floor={result['floor_i32']} fraction={result['fraction']:.6f} "
            f"xmm4_low={result['xmm4_low']:.9f} "
            f"object_0x60_lri_full_hits={result['scale_lri_absence']['full_hits']} "
            f"object_0x60_lri_nonzero_scalar_hits="
            f"{result['scale_lri_absence']['nonzero_scalar_hits']}/"
            f"{result['scale_lri_absence']['nonzero_scalar_count']}"
        )


if __name__ == "__main__":
    main()
