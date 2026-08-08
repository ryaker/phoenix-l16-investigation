#!/usr/bin/env python3

import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
REPORT = ROOT / "runs/prefusion_wide_minimum_selector/wide_minimum_selector_28mm.json"
HDR = ROOT / "runs/prefusion_wide_minimum_selector/wide_minimum_selector_28mm.hdr"


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def f32(snapshot):
    return struct.unpack("<f", bytes.fromhex(snapshot["hex"]))[0]


def main():
    packet = json.loads(REPORT.read_text())
    require(packet["process_exit_status"] == 0, "process exit")
    require(packet["errors"] == [], "probe errors")
    require(HDR.read_bytes().startswith(b"#?RADIANCE"), "HDR output")
    require(
        set(packet["completed_routes"])
        == {"materialize_candidate", "retain_existing_and_transfer"},
        "both routes not completed",
    )
    require(len(packet["events"]) >= 2, "expected completed events")
    materialize_events = [
        event for event in packet["events"]
        if event["route"] == "materialize_candidate"
    ]
    retain_events = [
        event for event in packet["events"]
        if event["route"] == "retain_existing_and_transfer"
    ]
    for materialize in materialize_events:
        require(materialize["jbe_predicted"] is True, "materialize flags")
        require(
            f32(materialize["candidate_score"]) <= f32(materialize["existing_score"]),
            "materialize ordering",
        )
        require(materialize["route_va"] == 0x22D9A0, "materialize route VA")
        require(materialize["effect_va"] == 0x22DB7C, "materialize effect VA")
        require(
            materialize["destination_node"] == materialize["existing_node"],
            "materialize node identity",
        )
        require(
            materialize["stored_score"]["hex"]
            == materialize["candidate_score"]["hex"],
            "materialize score copy",
        )
        require(
            materialize["candidate_source_object_id"]["hex"]
            == materialize["existing_node_key"]["hex"],
            "materialize camera/node key identity",
        )

    for retain in retain_events:
        require(retain["jbe_predicted"] is False, "retain flags")
        require(
            f32(retain["candidate_score"]) > f32(retain["existing_score"]),
            "retain ordering",
        )
        require(retain["route_va"] == 0x22D901, "retain route VA")
        require(retain["existing_entry_va"] == 0x22DCC3, "existing entry VA")
        require(retain["transfer_call_va"] == 0x22DF45, "transfer call VA")
        require(retain["effect_va"] == 0x22DF4A, "transfer return VA")
        require(retain["selector"] == 1, "transfer selector")
        require(
            retain["destination_object_id"]["hex"]
            == retain["existing_node_key"]["hex"],
            "retain camera/node key identity",
        )
        node = retain["existing_node"]
        require(retain["selected_node"] == node, "selected node identity")
        require(retain["selected_node_local"] == node, "selected local identity")
        require(
            retain["source_addresses"] == [node + 0x30, node + 0x60, node + 0x54],
            "transfer source identities",
        )
        expected = (
            retain["source_0"]["hex"]
            + retain["source_1"]["hex"]
            + retain["source_2"]["hex"]
        )
        require(retain["bank_after"]["hex"] == expected, "transfer exact copy")
        require(retain["bank_before"]["hex"] != expected, "transfer changed bank")

    materialize = next(
        (
            event for event in materialize_events
            if f32(event["candidate_score"]) < f32(event["existing_score"])
        ),
        materialize_events[0],
    )
    retain = retain_events[0]

    print(
        "wide_minimum_selector=OK "
        f"materialize={f32(materialize['candidate_score']):.9g}"
        f"<={f32(materialize['existing_score']):.9g} "
        f"retain={f32(retain['candidate_score']):.9g}"
        f">{f32(retain['existing_score']):.9g}"
    )


if __name__ == "__main__":
    main()
