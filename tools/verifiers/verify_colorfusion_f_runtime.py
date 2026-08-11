#!/usr/bin/env python3
"""Bit-replay a ColorFusionBayer 0x18eb00/0x19C790 runtime capture."""

import argparse
import json
import pathlib
import struct


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


def bits(value):
    return struct.unpack("<I", struct.pack("<f", value))[0]


def from_bits(value):
    return struct.unpack("<f", struct.pack("<I", value))[0]


def x86_rcp(value):
    value_bits = bits(value)
    sign = value_bits & 0x80000000
    exponent = (value_bits >> 23) & 0xFF
    fraction = value_bits & 0x007FFFFF
    if exponent == 0:
        return from_bits(sign | 0x7F800000)
    if exponent == 0xFF:
        if fraction == 0:
            return from_bits(sign)
        return from_bits(value_bits | 0x00400000)
    if exponent >= 253:
        return from_bits(sign)
    index = fraction >> 12
    denominator = 4097 + 2 * index
    quotient = ((1 << 25) + denominator // 2) // denominator
    output_exponent = 253 - exponent
    output_fraction = (quotient - 4096) << 11
    return from_bits(sign | (output_exponent << 23) | output_fraction)


def read_floats(path):
    raw = path.read_bytes()
    return struct.unpack("<%df" % (len(raw) // 4), raw)


def replay_module(source, reference, coeff, noise):
    accumulator = 0.0
    lane_wins = [0, 0, 0, 0]
    for index in range(256):
        weights = []
        for lane in range(4):
            at = 4 * index + lane
            delta = f32(source[at] - reference[at])
            delta2 = f32(delta * delta)
            lam = f32(coeff[at] * noise[lane])
            denominator = f32(delta2 + lam)
            weight = f32(x86_rcp(denominator) * delta2)
            weights.append(weight)
        selected_lane = max(range(4), key=lambda lane: weights[lane])
        lane_wins[selected_lane] += 1
        selected = weights[selected_lane]
        accumulator = f32(accumulator + f32(1.0 - selected))
    return f32(accumulator * f32(1.0 / 256.0)), lane_wins


def replay_combine(module_values):
    # Installed order: A starts at 1, then A += (1-m); B starts at 0.
    a = f32(1.0)
    b = f32(0.0)
    for value in module_values:
        b = f32(b + f32(value * value))
        a = f32(a + f32(1.0 - value))
    numerator = f32(f32(a * a) + b)
    divisor = f32(float((len(module_values) + 1) ** 2))
    return a, b, numerator, f32(numerator / divisor)


def expect_bits(label, got, expected_hex):
    expected = int(expected_hex, 16)
    got_bits = bits(got)
    ok = got_bits == expected
    print(
        "%s %s got=%.9g/0x%08x expected=0x%08x"
        % ("PASS" if ok else "FAIL", label, got, got_bits, expected)
    )
    return ok


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("capture", type=pathlib.Path)
    args = parser.parse_args()
    root = args.capture.parent
    capture = json.loads(args.capture.read_text())
    ok = True
    observed_m = []
    for record in capture["modules"]:
        source = read_floats(root / record["source_file"])
        reference = read_floats(root / record["reference_file"])
        coeff = read_floats(root / record["coeff_file"])
        replayed, lane_wins = replay_module(
            source, reference, coeff, record["noise"]["float"]
        )
        expected = record["m"]["bits"][0]
        ok &= expect_bits("module_%d m" % record["k_register"], replayed, expected)
        lanes_equal = len(set(record["m"]["bits"])) == 1
        print(
            "%s module_%d broadcast lanes; max-lane census=%s"
            % ("PASS" if lanes_equal else "FAIL", record["k_register"], lane_wins)
        )
        ok &= lanes_equal
        observed_m.append(from_bits(int(expected, 16)))

    a, b, numerator, f_value = replay_combine(observed_m)
    ok &= expect_bits("combine A", a, capture["numerator"]["A"]["bits"][0])
    ok &= expect_bits("combine B", b, capture["numerator"]["B"]["bits"][0])
    ok &= expect_bits(
        "combine A^2+B", numerator, capture["numerator"]["A2_plus_B"]["bits"][0]
    )
    print("INFO patch f=(A^2+B)/(N+1)^2 = %.9g/0x%08x" % (f_value, bits(f_value)))

    ref_descriptor = capture["entry"]["reference_descriptor"]
    vector_descriptor_addresses = {
        hex(int(capture["entry"]["module_begin"], 16) + 0x30 * row["k"])
        for row in capture["entry"]["modules"]
    }
    separate = ref_descriptor not in vector_descriptor_addresses
    print(
        "%s reference descriptor %s is separate from N=%d inline source descriptors"
        % ("PASS" if separate else "FAIL", ref_descriptor, capture["n"])
    )
    ok &= separate
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

