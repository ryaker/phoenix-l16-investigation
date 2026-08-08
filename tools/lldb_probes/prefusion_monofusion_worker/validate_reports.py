#!/usr/bin/env python3
import json
import math
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "runs" / "prefusion_monofusion_worker"
NAMES = ("unit1_28mm", "unit1_35mm", "unit2_28mm")
DETAILED = ("unit1_28mm", "unit2_28mm")
EXPECTED_CAPTURE = {
    "unit1_28mm": {
        "sensor_analog_gain": 1.5,
        "sensor_digital_gain": 1.015625,
        "sensor_exposure": 14639008,
    },
    "unit2_28mm": {
        "sensor_analog_gain": 7.75,
        "sensor_digital_gain": 1.0,
        "sensor_exposure": 42005140,
    },
}
EXPECTED_TARGET = {
    "unit1_28mm": {
        "sensor_analog_gain": 1.0,
        "sensor_exposure": 11238709,
    },
    "unit1_35mm": {
        "sensor_analog_gain": 1.0,
        "sensor_exposure": 1301331,
    },
    "unit2_28mm": {
        "sensor_analog_gain": 3.875,
        "sensor_exposure": 42009320,
    },
}
EXPECTED_SOURCE = {
    name: {
        "sensor_analog_gain": values["sensor_analog_gain"],
        "sensor_exposure": values["sensor_exposure"],
    }
    for name, values in EXPECTED_CAPTURE.items()
}
EXPECTED_SOURCE["unit1_35mm"] = {
    "sensor_analog_gain": 1.0,
    "sensor_exposure": 2606820,
}
LIBCP = Path(
    "/Users/ryaker/Documents/Light_Work/Lumen/Lumen.app/Contents/Frameworks/libcp.dylib"
)
PANCHROMATIC_TABLE_VA = 0x5AD7C0


def installed_rows():
    data = LIBCP.read_bytes()
    rows = {}
    for index in range(28):
        raw = data[
            PANCHROMATIC_TABLE_VA
            + index * 0x20 : PANCHROMATIC_TABLE_VA
            + (index + 1) * 0x20
        ]
        gain, scale, threshold, cliff, black, white, a, b = struct.unpack("<I7f", raw)
        rows[gain] = {
            "gain": gain,
            "scale": scale,
            "threshold": threshold,
            "cliff_slope": cliff,
            "black_level": black,
            "white_level": white,
            "panchromatic_a": a,
            "panchromatic_b": b,
            "raw_hex": raw.hex(),
        }
    return rows


def require(condition, message):
    if not condition:
        raise SystemExit("FAIL: " + message)


def close(actual, expected, message, *, rel_tol=2e-6, abs_tol=1e-9):
    require(
        actual is not None
        and math.isclose(actual, expected, rel_tol=rel_tol, abs_tol=abs_tol),
        f"{message}: got {actual!r}, expected {expected!r}",
    )


def f32(value):
    return struct.unpack("<f", struct.pack("<f", value))[0]


reports = {}
installed = installed_rows()
for name in NAMES:
    path = RUN / f"{name}.json"
    require(path.exists(), f"missing {path}")
    reports[name] = json.loads(path.read_text())

for name, report in reports.items():
    subtracts = report["initializer_subtract_calls"]
    affines = report["initializer_affine_calls"]
    workers = report["worker_entries"]
    mode1 = report["mode1_calls_0x19f790"]
    mode0 = report["mode0_calls_0x1a3c00"]
    require(subtracts, f"{name}: no initializer subtract")
    require(affines, f"{name}: no initializer affine")
    require(workers, f"{name}: no worker entry")
    require(bool(mode1) != bool(mode0), f"{name}: expected exactly one live branch")
    for sample in subtracts:
        require(sample["source"]["read_ok"], f"{name}: unreadable subtract source")
    for sample in affines:
        require(sample["source"]["read_ok"], f"{name}: unreadable affine source")
    for worker in workers:
        require(worker["source_records_0x08"]["count"] == 1, f"{name}: source count")
        require(worker["flow_records_0xd8"]["count"] == 1, f"{name}: flow count")
        source = worker["source_records_0x08"]["records"][0]["descriptor"]
        flow = worker["flow_records_0xd8"]["records"][0]["descriptor"]
        require(source["size"] == [4160, 3120], f"{name}: full-resolution source size")
        require(flow["size"] == [519, 389], f"{name}: reduced flow size")

        fields = worker["kernel_fields_0x38_0x50"]
        close(fields["black_level_0x60"], 42.0, f"{name}: worker black level")
        close(fields["white_level_0x64"], 1023.0, f"{name}: worker white level")
        close(worker["normalization_0xf8"], 981.0, f"{name}: white-black range")
        expected_rgb = [0.2155500054359436, 0.43230700492858887, 0.35214298963546753]
        for index, expected in enumerate(expected_rgb):
            close(
                worker["normalization_0x100"][index],
                expected,
                f"{name}: normalization weight {index}",
            )

    for sample in subtracts:
        close(sample["subtract"], 42.0, f"{name}: initializer black subtraction")
    for sample in affines:
        close(sample["add"], 42.0, f"{name}: initializer black restoration")
        target = EXPECTED_TARGET[name]
        source = EXPECTED_SOURCE[name]
        target_energy = f32(
            f32(float(target["sensor_exposure"]))
            * f32(target["sensor_analog_gain"])
        )
        source_energy = f32(
            f32(float(source["sensor_exposure"]))
            * f32(source["sensor_analog_gain"])
        )
        exposure_ratio = f32(target_energy / source_energy)
        expected_multiply = f32(exposure_ratio / f32(2.3183400630950928))
        close(
            sample["multiply"],
            expected_multiply,
            f"{name}: public exposure/analog source affine",
            rel_tol=0.0,
            abs_tol=0.0,
        )

    output = RUN / f"{name}.hdr"
    require(output.is_file(), f"{name}: missing completed HDR")
    require(output.stat().st_size > 300_000_000, f"{name}: short HDR output")
    require(output.read_bytes()[:10] == b"#?RADIANCE", f"{name}: not Radiance HDR")

for name in DETAILED:
    report = reports[name]
    require(len(report["initializer_weight_inputs"]) == 1, f"{name}: weight callback")
    require(len(report["initializer_vst_scaling"]) == 1, f"{name}: VST callback")
    require(len(report["initializer_source_captures"]) == 1, f"{name}: source callback")

    weight = report["initializer_weight_inputs"][0]
    vst = report["initializer_vst_scaling"][0]
    capture = report["initializer_source_captures"][0]
    worker = report["worker_entries"][0]
    fields = worker["kernel_fields_0x38_0x50"]

    count = weight["same_group_nonmono_count"]
    response = weight["sensor_response"]
    require(count == 4, f"{name}: same-group non-mono count")
    close(response, 2.3183400630950928, f"{name}: sensor response")
    require(vst["same_group_nonmono_count"] == float(count), f"{name}: VST count")
    close(vst["sensor_response"], response, f"{name}: VST response")

    expected_alpha = f32(count / (response + count))
    expected_scale = f32(1.0 + count / response)
    close(fields["float_0x50"], expected_alpha, f"{name}: target blend alpha")
    close(fields["float_0x54"], expected_scale, f"{name}: noise scale")
    close(worker["normalization_0x110"], response, f"{name}: copied response")

    denominator = f32(response * count)
    expected_a = f32(vst["selected_panchromatic_a"] / denominator)
    expected_b = f32(vst["selected_panchromatic_b"] / denominator)
    close(vst["scaled_a_xmm0"], expected_a, f"{name}: scaled panchromatic a")
    close(vst["scaled_b_xmm1"], expected_b, f"{name}: scaled panchromatic b")
    close(fields["vst_a_0x58"], expected_a, f"{name}: stored VST a")
    close(fields["vst_b_0x5c"], expected_b, f"{name}: stored VST b")

    require(capture["camera_key"] == 1, f"{name}: source is not A2/key 1")
    require(capture["sensor_type"] == 3, f"{name}: internal source sensor type")
    close(capture["black_level"], 42.0, f"{name}: source black level")
    close(capture["white_level"], 1023.0, f"{name}: source white level")
    for field, expected in EXPECTED_CAPTURE[name].items():
        if isinstance(expected, float):
            close(capture[field], expected, f"{name}: public capture {field}")
        else:
            require(capture[field] == expected, f"{name}: public capture {field}")

    gain_key = int(capture["sensor_analog_gain"] * 100.0)
    row = installed[gain_key]
    close(
        vst["selected_panchromatic_a"],
        row["panchromatic_a"],
        f"{name}: installed selected panchromatic a",
    )
    close(
        vst["selected_panchromatic_b"],
        row["panchromatic_b"],
        f"{name}: installed selected panchromatic b",
    )

constructors = reports["unit1_28mm"]["sensor_characterization_constructors"]
require(len(constructors) == 1, "unit1_28mm: characterization constructor count")
constructor = constructors[0]
require(constructor["sensor_type"] == 3, "unit1_28mm: constructor sensor type")
require(len(constructor["rows"]) == 28, "unit1_28mm: constructor row count")
for actual, expected in zip(constructor["rows"], installed.values()):
    require(actual == expected, f"unit1_28mm: installed constructor row {expected['gain']}")

unit1_35_fields = reports["unit1_35mm"]["worker_entries"][0]["kernel_fields_0x38_0x50"]
unit1_35_denominator = f32(2.3183400630950928 * 4.0)
close(
    unit1_35_fields["vst_a_0x58"],
    f32(installed[100]["panchromatic_a"] / unit1_35_denominator),
    "unit1_35mm: installed selected panchromatic a",
)
close(
    unit1_35_fields["vst_b_0x5c"],
    f32(installed[100]["panchromatic_b"] / unit1_35_denominator),
    "unit1_35mm: installed selected panchromatic b",
)

require(
    reports["unit1_28mm"]["initializer_weight_inputs"][0]["sensor_response"]
    == reports["unit2_28mm"]["initializer_weight_inputs"][0]["sensor_response"],
    "two-body sensor-response mismatch",
)
require(
    reports["unit1_28mm"]["worker_entries"][0]["kernel_fields_0x38_0x50"]["float_0x50"]
    == reports["unit2_28mm"]["worker_entries"][0]["kernel_fields_0x38_0x50"]["float_0x50"],
    "two-body alpha mismatch",
)

branches = {
    name: "0x19f790" if report["mode1_calls_0x19f790"] else "0x1a3c00"
    for name, report in reports.items()
}
print("prefusion_monofusion_worker=OK")
for name in NAMES:
    first_sub = reports[name]["initializer_subtract_calls"][0]
    first_aff = reports[name]["initializer_affine_calls"][0]
    mode = reports[name]["worker_entries"][0]["mode_0x00"]
    print(
        f"{name}: mode={mode} branch={branches[name]} "
        f"subtract={first_sub['subtract']:.9g} "
        f"multiply={first_aff['multiply']:.9g} add={first_aff['add']:.9g}"
    )
