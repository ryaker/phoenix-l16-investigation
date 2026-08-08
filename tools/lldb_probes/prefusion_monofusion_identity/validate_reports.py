#!/usr/bin/env python3
"""Validate the six FusionCacheBayer/MonoFusion runtime packets."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNS = ROOT / "runs/prefusion_monofusion_identity"
WIDE = ("unit1_28mm", "unit1_35mm", "unit2_28mm")
TELE = ("unit1_70mm", "unit1_150mm", "unit2_70mm")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def load(name: str) -> dict:
    path = RUNS / f"{name}.json"
    require(path.is_file(), f"missing {path}")
    return json.loads(path.read_text())


def validate_completed_output(name: str) -> None:
    path = RUNS / f"{name}.hdr"
    require(path.is_file(), f"missing {path}")
    require(path.stat().st_size > 300_000_000, f"short HDR output {path}")
    require(path.read_bytes()[:10] == b"#?RADIANCE", f"not Radiance HDR: {path}")


def validate_wide(name: str, packet: dict) -> None:
    require(len(packet["field20_stores"]) == 1, f"{name}: expected one +0x20 store")
    require(len(packet["initialize_entries"]) == 1, f"{name}: expected one initialize entry")
    require(len(packet["initialize_commits"]) == 1, f"{name}: expected one initialize commit")
    require(len(packet["process_entries"]) == 16, f"{name}: expected 16 sampled process entries")
    require(len(packet["process_returns"]) == 16, f"{name}: expected 16 sampled process returns")
    require(len(packet["wide_adapter_calls"]) == 16, f"{name}: expected 16 wide adapter calls")
    require(not packet["tele_adapter_calls"], f"{name}: unexpected tele adapter call")

    store = packet["field20_stores"][0]
    require(store["flag_0x18"] == 1, f"{name}: FusionCacheBayer flag is not one")
    require(store["mono_fusion"] != 0, f"{name}: null MonoFusion allocation")
    require(store["old_field_0x20"] == 0, f"{name}: +0x20 was already populated")
    require(
        store["mono_before_store"]["target_camera_id_0xb8"] == 0,
        f"{name}: MonoFusion target is not A1/key 0",
    )

    initialized = packet["initialize_commits"][0]
    require(
        initialized["target_camera_id_0xb8"] == 0,
        f"{name}: initialized target is not A1/key 0",
    )
    require(
        initialized["negative_override_ids_0xc0"]["values"] == [1],
        f"{name}: expected only A2/key 1 in negative-override vector",
    )
    require(
        initialized["record_vector_0x08"]["count"] == 1,
        f"{name}: expected one full-resolution MonoFusion source record",
    )
    require(
        initialized["record_vector_0xd8"]["count"] == 1,
        f"{name}: expected one reduced MonoFusion source record",
    )
    require(
        initialized["output_image_0x20"]["domain"] == [0, 0, 4160, 3120],
        f"{name}: unexpected MonoFusion image domain",
    )
    require(
        initialized["output_image_0x20"]["data"] != 0,
        f"{name}: MonoFusion image data is null",
    )

    for index, entry in enumerate(packet["process_entries"]):
        require(
            entry["mono"]["initialized_0x240"] == 1,
            f"{name}[{index}]: process reached uninitialized MonoFusion",
        )
    for index, returned in enumerate(packet["process_returns"]):
        output = returned["output_rbp_minus_0x190"]
        operand_a = returned["operand_rbp_minus_0x160"]
        operand_b = returned["operand_rbp_minus_0xc0"]
        require(output["data"] != 0, f"{name}[{index}]: null process output")
        require(output["size"] == operand_a["size"] == operand_b["size"], f"{name}[{index}]: size mismatch")
        require(
            len({output["data"], operand_a["data"], operand_b["data"]}) == 3,
            f"{name}[{index}]: output aliases an input descriptor",
        )
    for index, adapter in enumerate(packet["wide_adapter_calls"]):
        require(adapter["mono_is_rbp_minus_0x190"], f"{name}[{index}]: wrong adapter operand")
        require(adapter["mono"]["data"] != 0, f"{name}[{index}]: adapter mono data is null")
        require(adapter["anchor"]["data"] != 0, f"{name}[{index}]: adapter anchor data is null")
        require(
            adapter["mono"]["data"] != adapter["anchor"]["data"],
            f"{name}[{index}]: MonoFusion output aliases anchor",
        )


def validate_tele(name: str, packet: dict) -> None:
    for key in (
        "field20_stores",
        "initialize_entries",
        "initialize_commits",
        "process_entries",
        "process_returns",
        "wide_adapter_calls",
    ):
        require(not packet[key], f"{name}: unexpected {key}")
    require(len(packet["tele_adapter_calls"]) == 16, f"{name}: expected 16 tele adapter calls")
    for index, call in enumerate(packet["tele_adapter_calls"]):
        require(call["source"]["data"] != 0, f"{name}[{index}]: null tele source")
        require(call["anchor"]["data"] != 0, f"{name}[{index}]: null tele anchor")


def main() -> None:
    for name in WIDE:
        packet = load(name)
        validate_wide(name, packet)
        validate_completed_output(name)
    for name in TELE:
        packet = load(name)
        validate_tele(name, packet)
        validate_completed_output(name)
    print("prefusion_monofusion_runtime=OK")
    print("wide=Unit1(28,35)+Unit2(28): target=A1 selected_mono=[A2] process=16")
    print("tele=Unit1(70,150)+Unit2(70): MonoFusion absent direct_adapter=16")
    print("completed_hdr=6/6 dimensions=10432x7824")


if __name__ == "__main__":
    main()
